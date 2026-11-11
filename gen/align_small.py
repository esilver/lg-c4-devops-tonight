"""align_small.py : when does each sound happen, found with a recogniser small enough for a browser.

align.py does this with a 1.2 GB phoneme recogniser. A voice that does not report its own timing (Pocket TTS, the
copied voice of docs/21) needs the same thing done in the page, so here it is done with ZIPA small (a Zipformer CTC
phone recogniser, 71 MB as 8-bit ONNX, CC BY 4.0, anyspeech/zipa-small-crctc-500k; weights only). Everything around
the network is written here so that it can be carried to the browser as it is:

  features   80 log mel energies every 10 ms, the Kaldi way (25 ms povey window, pre-emphasis 0.97, 20 to 7600 Hz)
  network    -> for every 40 ms (it hears at a quarter of the feature rate), how likely each of 127 IPA symbols is
  alignment  the line's known sounds are laid over that in the most likely way (a Viterbi search), and each boundary
             is then moved to where the next sound becomes the likelier of the two

  ./venv6/bin/python align_small.py check      score it against lines whose timing is known exactly (tests/output/voice/)
  ./venv6/bin/python align_small.py <wav> "<phonemes in the engine's alphabet>"     print the times"""
import sys, os, json, glob, numpy as np, onnxruntime as ort, soundfile as sf, librosa
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "avatar", "voice", "src", "zipa")
# which of the recogniser's symbols count as each sound of the engine's alphabet (it writes diphthongs and affricates as two symbols)
CLS = {
 'ɑ': 'ɑ a ɒ', 'æ': 'æ a ɛ', 'a': 'a æ ɑ', 'ʌ': 'ʌ ɐ ə', 'ɔ': 'ɔ ɒ o ɑ', 'ɒ': 'ɒ ɑ ɔ', 'ɛ': 'ɛ e', 'ɜ': 'ɜ ɝ ə ɹ ˞ ɚ', 'ɪ': 'ɪ i ɨ', 'i': 'i ɪ', 'ʊ': 'ʊ u', 'u': 'u ʊ ʉ',
 'ə': 'ə ɐ ɨ ɪ ʌ', 'ɐ': 'ɐ ə ʌ', 'ᵊ': 'ə ɨ ̩', 'ᵻ': 'ɨ ɪ ə', 'A': 'e ɪ ɛ', 'I': 'a ɪ ɑ', 'W': 'a ʊ ɑ', 'Y': 'ɔ ɪ o', 'O': 'o ʊ ɔ', 'Q': 'ə ʊ o',
 'l': 'l ɫ ̩', 'n': 'n ̩', 't': 't ɾ ʔ ʰ', 'd': 'd ɾ', 'T': 'ɾ t d', 'ʔ': 'ʔ t', 'ɹ': 'ɹ ɻ ˞ r', 'ʤ': 'd ʒ', 'ʧ': 't ʃ', 'ɡ': 'ɡ g', 'p': 'p ʰ', 'k': 'k ʰ',
}
for c in 'bfhjmsvwzŋʃʒðθ': CLS[c] = c
_m = {}
def model():
    if not _m:
        so = ort.SessionOptions(); so.intra_op_num_threads = int(os.environ.get("ALIGN_THREADS", "4"))
        _m["s"] = ort.InferenceSession(os.path.join(D, "model.int8.onnx"), so, providers=["CPUExecutionProvider"])
        _m["v"] = {l.rstrip("\n").rsplit(" ", 1)[0]: int(l.rstrip("\n").rsplit(" ", 1)[1]) for l in open(os.path.join(D, "tokens.txt"), encoding="utf-8")}
    return _m["s"], _m["v"]
def fbank(a16):
    """Kaldi-style log mel filterbank energies: [frames, 80], one frame every 10 ms (samples in -1..1, as the training features were)"""
    N, S, NFFT, NMEL = 400, 160, 512, 80; n = len(a16); T = (n + S // 2) // S
    pad = np.concatenate([a16[1:N // 2 - S // 2 + 1][::-1], a16, a16[-(N // 2 + S // 2 + 1):-1][::-1]]) if n > N else np.pad(a16, (N, N))      # reflected ends: frame t is centred on sample t*160 + 80
    fr = np.lib.stride_tricks.sliding_window_view(pad, N)[::S][:T].astype(np.float64).copy()
    fr -= fr.mean(axis=1, keepdims=True); fr = np.concatenate([fr[:, :1] * (1 - 0.97), fr[:, 1:] - 0.97 * fr[:, :-1]], axis=1)
    fr *= (0.5 - 0.5 * np.cos(2 * np.pi * np.arange(N) / (N - 1))) ** 0.85
    P = np.abs(np.fft.rfft(fr, NFFT, axis=1)) ** 2
    mel = lambda f: 1127.0 * np.log(1 + f / 700.0); lo, hi = mel(20.0), mel(8000.0 - 400.0); edges = lo + (hi - lo) * np.arange(NMEL + 2) / (NMEL + 1)
    fm = mel(np.arange(NFFT // 2 + 1) * 16000.0 / NFFT); W = np.zeros((NMEL, NFFT // 2 + 1))
    for m in range(NMEL):
        l, c, r = edges[m], edges[m + 1], edges[m + 2]; W[m] = np.maximum(0, np.minimum((fm - l) / (c - l), (r - fm) / (r - c)))
    return np.log(np.maximum(P @ W.T, 1.1920929e-07)).astype(np.float32)
def posteriors(a16):
    s, v = model(); x = fbank(a16)[None]; lp, n = s.run(None, {"x": x, "x_lens": np.array([x.shape[1]], np.int64)})
    return lp[0, :int(n[0])], x.shape[1] / max(1, int(n[0])) * 0.01           # log probabilities per output frame, and seconds per output frame
def align(a16, phones):
    """phones: the line's sounds in order (engine alphabet). -> [(start, end)] in seconds, and how well each matched"""
    lp, hop = posteriors(a16); _, v = model(); T = len(lp); N = len(phones)
    tok = np.stack([np.logaddexp.reduce(lp[:, [v[s] for s in CLS[p].split() if s in v]], axis=1) for p in phones], axis=1)       # [T, N]
    S = 2 * N + 1; E = np.empty((T, S)); E[:, 0::2] = lp[:, :1]; E[:, 1::2] = tok; NEG = -1e30
    skip = np.ones(S, bool); skip[:3] = False; skip[0::2] = False                # any two sounds may touch (the sets overlap, so equal neighbours cannot be told apart anyway)
    dp = np.full(S, NEG); dp[0] = E[0, 0]; dp[1] = E[0, 1]; bp = np.zeros((T, S), np.int8); ar = np.arange(S)
    for t in range(1, T):
        b = np.concatenate([[NEG], dp[:-1]]); c = np.concatenate([[NEG, NEG], dp[:-2]]); c[~skip] = NEG
        m = np.stack([dp, b, c]); k = m.argmax(0); dp = m[k, ar] + E[t]; bp[t] = k
    s = S - 1 if dp[S - 1] >= dp[S - 2] else S - 2; path = [s]
    for t in range(T - 1, 0, -1): s -= int(bp[t, s]); path.append(s)
    path = np.array(path[::-1]); spans = []
    for i in range(N):
        w = np.where(path == 2 * i + 1)[0]
        spans.append((w[0], w[-1]) if len(w) else None)
    for i in range(N):                                                           # a sound the path gave no frame of its own sits between its neighbours
        if spans[i] is None:
            a = next((spans[j][1] for j in range(i - 1, -1, -1) if spans[j]), 0); spans[i] = (a, a)
    score = [float(tok[a:b + 1, i].max()) for i, (a, b) in enumerate(spans)]
    # the boundary between two neighbours: where, between the frames each is surest of, the second becomes likelier than the first
    rel = tok - np.log1p(-np.minimum(np.exp(lp[:, 0]), 1 - 1e-6))[:, None]; bounds = [0.0]
    for i in range(N - 1):
        a, b = spans[i][1], spans[i + 1][0]
        if b - a <= 1: cut = float(b)
        else:
            d = rel[a:b + 1, i + 1] - rel[a:b + 1, i]; pos = np.where(d > 0)[0]; cut = a + (float(pos[0]) if len(pos) else (b - a + 1) / 2); cut = 0.5 * cut + 0.5 * (a + b + 1) / 2
        bounds.append(cut * hop)
    bounds.append(len(a16) / 16000)
    return [(bounds[i], bounds[i + 1]) for i in range(N)], score, hop
def read16k(path):
    a, sr = sf.read(path, dtype="float32"); a = a.mean(axis=1) if a.ndim > 1 else a
    return a, sr, librosa.resample(a, orig_sr=sr, target_sr=16000)
if __name__ == "__main__":
    if sys.argv[1:] == ["check"]:
        # lines made by the voice that reports its own timing (corrected, and confirmed against the large aligner: docs/18)
        es, ec, lips = [], [], []; s, v = model()
        for f in sorted(glob.glob("../tests/output/voice/line_*.json")):
            L = json.load(open(f)); a, sr, a16 = read16k(f[:-5] + ".wav"); seg = L["sp"]["seg"]; idx = [i for i, s_ in enumerate(seg) if s_[0] in CLS and s_[2] > 0]
            import time; t0 = time.time(); spans, score, hop = align(a16, [seg[i][0] for i in idx]); took = time.time() - t0
            lp, _ = posteriors(a16); inv = {i: t for t, i in v.items()}; said = "".join(inv[k] for k, p in zip(lp.argmax(1), [None] + list(lp.argmax(1)[:-1])) if k != 0 and k != p)
            print(f"{os.path.basename(f)[:-5]}: {len(a) / sr:.1f} s aligned in {took:.2f} s; it writes: {said[:90]}")
            for k, i in enumerate(idx):
                sg = seg[i]; nxt = seg[i + 1][0] if i + 1 < len(seg) else "."; prv = seg[i - 1][0] if i else "."
                if sg[0] in "pbm": lips.append((spans[k][0] + spans[k][1]) / 2 - (sg[1] + sg[2] / 2))
                if nxt in ",.:;?!—…" or prv in ",.:;?!—…" or sg[2] > 0.2 or k == 0: continue
                es.append(spans[k][0] - sg[1]); ec.append((spans[k][0] + spans[k][1]) / 2 - (sg[1] + sg[2] / 2))
        es, ec, lips = np.array(es) * 1000, np.array(ec) * 1000, np.array(lips) * 1000
        print(f"\noutput frames are {hop * 1000:.0f} ms apart")
        for name, e in (("starts", es), ("centres", ec), ("centres of p, b, m", lips)):
            m = np.median(e); print(f"{len(e)} {name}: small aligner minus truth {m:+.0f} ms (median); around that, half within {np.median(np.abs(e - m)):.0f} ms, 90% within {np.percentile(np.abs(e - m), 90):.0f} ms; without removing the median, 90% within {np.percentile(np.abs(e), 90):.0f} ms")
    else:
        a, sr, a16 = read16k(sys.argv[1]); ph = [c for c in sys.argv[2] if c in CLS]; spans, score, hop = align(a16, ph)
        for p, (t0, t1), sc in zip(ph, spans, score): print(f"{p}  {t0:6.3f}  {t1:6.3f}  {sc:6.2f}")
