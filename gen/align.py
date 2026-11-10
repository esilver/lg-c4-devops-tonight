"""align.py : find out when every sound happens in a recording whose words are known (request 9).

The first voices (tts.py) came from a model that reports its own timing. The second voices (tts2.py) do not, so the
timing is measured from the audio: a phoneme recogniser (wav2vec 2.0 trained to write speech as phonetic symbols) says,
for every 20 ms of sound, how likely each phoneme is, and the known phoneme sequence of the line is laid over that in the
most likely way (forced alignment, a Viterbi search written here).

  ./venv4/bin/python align.py check        align the FIRST voices and compare with the timing their model reported
  ./venv4/bin/python align.py              choose the best take of each line in work/tts2/, align it, write work/tts2/lines.json

Take choice: each take is aligned and transcribed by a speech recogniser. A take whose worst word matches its phonemes
poorly, or whose transcript drops or adds words, loses to the other one."""
import sys, os, re, json, glob, subprocess, numpy as np, soundfile as sf, torch
torch.set_num_threads(int(os.environ.get("ALIGN_THREADS", "4")))
HOP = 0.02                                     # the recogniser hears in 25 ms windows, 20 ms apart
# which of the recogniser's symbols count as each phoneme of the script (its alphabet is finer and writes r-coloured vowels as one symbol)
CLS = {
 'ɑ': 'ɑː ɑ ɑːɹ ɒ a aː', 'æ': 'æ a', 'a': 'a æ aː ɑː', 'ʌ': 'ʌ ɐ ə', 'ɔ': 'ɔː ɔ ɔːɹ ɑː ɒ oː oːɹ', 'ɒ': 'ɒ ɑː ɔ ɔː', 'ɛ': 'ɛ e ɛɹ',
 'ɜ': 'ɜː ɜ ɚ', 'ɪ': 'ɪ ᵻ i ɪɹ', 'i': 'iː i ɪ', 'ʊ': 'ʊ ʊɹ uː', 'u': 'uː u ʊ', 'ə': 'ə ɚ ɐ ᵻ əl', 'ɐ': 'ɐ ə ʌ', 'ᵊ': 'ə ᵻ ɐ əl n̩', 'ᵻ': 'ᵻ ɪ ə',
 'A': 'eɪ e eː ɛ', 'I': 'aɪ aɪɚ aɪə a', 'W': 'aʊ a', 'Y': 'ɔɪ oɪ', 'O': 'oʊ o oː əʊ', 'Q': 'əʊ oʊ o',
 'l': 'l əl ɫ l̩', 'n': 'n n̩', 't': 't ɾ ʔ', 'd': 'd ɾ', 'T': 'ɾ t d', 'ʔ': 'ʔ t', 'ɹ': 'ɹ ɚ ɑːɹ ɔːɹ ɛɹ ɪɹ ʊɹ ɜː oːɹ aɪɚ', 'ʤ': 'dʒ', 'ʧ': 'tʃ',
}
for c in 'bfhjkmpsvwzɡŋʃʒðθ': CLS[c] = c
VOWELS = "AIOWYQaiuæɐɑɒɔəɛɜɪʊʌᵻᵊ"
_m = {}
def model():
    if not _m:
        from transformers import Wav2Vec2ForCTC
        from huggingface_hub import snapshot_download
        p = snapshot_download("facebook/wav2vec2-lv-60-espeak-cv-ft", allow_patterns=["config.json", "vocab.json", "pytorch_model.bin"])
        _m["v"] = json.load(open(p + "/vocab.json")); _m["m"] = Wav2Vec2ForCTC.from_pretrained(p).eval()
    return _m["m"], _m["v"]
def read16k(path):
    a, sr = sf.read(path, dtype="float32")
    if a.ndim > 1: a = a.mean(axis=1)
    import librosa
    return a, sr, librosa.resample(a, orig_sr=sr, target_sr=16000)
def posteriors(a16):
    m, v = model(); x = torch.tensor((a16 - a16.mean()) / (a16.std() + 1e-7))[None]
    with torch.no_grad(): return torch.log_softmax(m(x).logits[0], dim=-1).numpy()          # [frames, symbols]
def align(a16, phones):
    """phones: the line's phonemes in order. Returns per phoneme (start, end) in seconds, and how well each matched."""
    lp = posteriors(a16); _, v = model(); T = len(lp); N = len(phones)
    tok = np.stack([np.logaddexp.reduce(lp[:, [v[s] for s in CLS[p].split() if s in v]], axis=1) for p in phones], axis=1)       # [T, N]
    # pass 1: the usual alignment with "nothing new" frames (blanks) between phonemes; gives each phoneme's most certain frames
    S = 2 * N + 1; E = np.empty((T, S)); E[:, 0::2] = lp[:, :1]; E[:, 1::2] = tok; NEG = -1e30
    skip = np.zeros(S, bool); skip[3::2] = [phones[i] != phones[i - 1] for i in range(1, N)]            # two different phonemes may touch
    dp = np.full(S, NEG); dp[0] = E[0, 0]; dp[1] = E[0, 1]; bp = np.zeros((T, S), np.int8); ar = np.arange(S)
    for t in range(1, T):
        b = np.concatenate([[NEG], dp[:-1]]); c = np.concatenate([[NEG, NEG], dp[:-2]]); c[~skip] = NEG
        m = np.stack([dp, b, c]); k = m.argmax(0); dp = m[k, ar] + E[t]; bp[t] = k
    s = S - 1 if dp[S - 1] >= dp[S - 2] else S - 2; path = [s]
    for t in range(T - 1, 0, -1): s -= bp[t, s]; path.append(s)
    path = np.array(path[::-1]); spans = [(np.where(path == 2 * i + 1)[0][0], np.where(path == 2 * i + 1)[0][-1]) for i in range(N)]
    score = [float(tok[a:b + 1, i].max()) for i, (a, b) in enumerate(spans)]
    # pass 2: the boundary between two neighbours is where, ignoring blanks, the second becomes likelier than the first
    rel = tok - np.log1p(-np.minimum(np.exp(lp[:, 0]), 1 - 1e-6))[:, None]; bounds = [0.0]
    for i in range(N - 1):
        a, b = spans[i][1], spans[i + 1][0]
        if b - a <= 1: cut = b
        else:
            d = rel[a:b + 1, i + 1] - rel[a:b + 1, i]; pos = np.where(d > 0)[0]; cut = a + (int(pos[0]) if len(pos) else (b - a + 1) // 2)
            cut = int(round(0.5 * cut + 0.5 * (a + b + 1) / 2))                      # halfway between that crossing and the midpoint: steadier than either
        bounds.append(cut * HOP + 0.0025)
    bounds.append(len(a16) / 16000)
    return [(bounds[i], bounds[i + 1]) for i in range(N)], score, spans
def loud_frames(a, sr, hop=0.01):
    n = int(sr * hop); k = len(a) // n; r = np.sqrt((a[:k * n].reshape(k, n) ** 2).mean(axis=1) + 1e-12); return r
def retime(ref, a, sr, a16):
    """ref: a line of work/tts/lines.json (its phonemes and caption words). Returns the same line re-timed to the audio a."""
    seg = ref["seg"]; idx = [i for i, s in enumerate(seg) if s[0] in CLS and s[2] > 0]; phones = [seg[i][0] for i in idx]
    se, score, spans = align(a16, phones)
    # silence inside a phoneme's stretch is a pause, not part of the sound: pull the edges in to where there is signal
    r = loud_frames(a, sr); thr = max(np.percentile(r, 95) * 0.035, 1e-4); quiet = r < thr
    def trim(t0, t1, first, last):
        f0, f1 = int(t0 * 100), min(len(r), int(np.ceil(t1 * 100)))
        if f1 - f0 < 14: return t0, t1
        q = quiet[f0:f1]; lead = int(np.argmax(~q)) if (~q).any() else 0; trail = int(np.argmax(~q[::-1])) if (~q).any() else 0
        if first or lead >= 10: t0 = t0 + max(0, lead - 2) * 0.01          # keep 20 ms of the run-in
        if last or trail >= 10: t1 = t1 - max(0, trail - 3) * 0.01
        return t0, max(t1, t0 + 0.03)
    se = [trim(t0, t1, i == 0, i == len(se) - 1) for i, (t0, t1) in enumerate(se)]
    out = []; k = 0; t = se[0][0]
    for i, s in enumerate(seg):
        ch = s[0]
        if i in idx:
            t0, t1 = se[k]; f0, f1 = int(t0 * sr), max(int(t0 * sr) + 1, int(t1 * sr)); out.append([ch, round(t0, 3), round(t1 - t0, 3), round(float(np.sqrt((a[f0:f1] ** 2).mean())), 4)]); t = t1; k += 1
        elif ch in "ˈˌ ː" or ch in CLS: out.append([ch, round(se[k][0] if k < len(se) else t, 3), 0, 0])       # marks take no time of their own
        else:                                            # punctuation: the pause, if any, between the sounds either side
            nxt = se[k][0] if k < len(se) else len(a) / sr; out.append([ch, round(t, 3), round(max(0.0, nxt - t), 3), 0])
    # pauses the script did not ask for
    fixed = []
    for j, s in enumerate(out):
        if fixed and s[0] in CLS and s[2] > 0:
            p = next((q for q in reversed(fixed) if q[2] > 0), None)
            if p and p[0] in CLS and s[1] - (p[1] + p[2]) >= 0.12: fixed.append([",", round(p[1] + p[2], 3), round(s[1] - p[1] - p[2], 3), 0])
        fixed.append(s)
    # caption words: each appears with the first sound of its first spoken word. The reference gives word times on its
    # own clock (about 85 ms ahead of its phoneme times), so each word is matched to the nearest word-initial phoneme.
    cand = []; fresh = True; k = 0
    for i, sg in enumerate(seg):
        if sg[0] == " ": fresh = True
        elif fresh and (sg[0] in "ˈˌ" or i in idx): cand.append((sg[1], k)); fresh = False
        if i in idx: k += 1
    words = []; j = 0
    for w, t in ref["words"]:
        j = min(range(j, len(cand)), key=lambda q: abs(cand[q][0] - 0.085 - t)); words.append([w, round(se[min(cand[j][1], len(se) - 1)][0], 3)])
    wscore = []; k = 0; cur = []
    for i, s in enumerate(seg):                           # how well the worst word matched
        if i in idx: cur.append(score[k]); k += 1
        if s[0] == " " and cur: wscore.append(float(np.mean(cur))); cur = []
    if cur: wscore.append(float(np.mean(cur)))
    retime.words = [round(x, 1) for x in wscore]            # kept for the report
    return dict(seg=fixed, words=words, dur=round(len(a) / sr, 3)), float(np.mean(score)), float(min(wscore)), se
_asr = {}
def hear(a16):
    if not _asr:
        from transformers import pipeline
        _asr["p"] = pipeline("automatic-speech-recognition", model="openai/whisper-base.en", device="cpu")
    return _asr["p"]({"raw": a16, "sampling_rate": 16000})["text"].strip()
# what the recogniser writes for things the script spells out
SAME = [("twenty twenty six", "2026"), ("a i", "ai"), ("u s", "us"), ("d n s", "dns"), ("five oh threes", "503s"), ("nine thousand dollars", "9000"), ("why a mel", "ya mel"), ("y a mel", "ya mel"),
        ("sy", "cy"), ("sai", "cy"), ("sigh", "cy"), ("si", "cy"), ("psy", "cy"), ("dekkar", "dekar"), ("decar", "dekar"), ("de car", "dekar"), ("decker", "dekar"), ("side dekar", "cy dekar"), ("sidecar", "cy dekar"), ("side car", "cy dekar"),
        ("yammel", "yaml"), ("yamil", "yaml"), ("yamel", "yaml"), ("yamal", "yaml"), ("fin ops", "finops"), ("phenops", "finops"), ("auto scaler", "autoscaler"), ("one", "1"), ("four", "4"), ("forty", "40"), ("nine", "9"),
        ("four thousand", "4000"), ("4 thousand", "4000"), ("under way", "underway"), ("dee ploy", "deploy"), ("d ploy", "deploy"), ("d", "dee"), ("doody", "duty"), ("yml", "ya mel"), ("yaml staff", "ya mel staff"), ("riding", "writing"), ("9s", "nines"), ("4 nines", "4 nines"), ("had", "have")]
def norm(s):
    s = re.sub(r"[^a-z0-9 ]", "", s.lower().replace("-", " ").replace("$", "")); s = " " + " ".join(s.split()) + " "
    for a, b in SAME: s = s.replace(f" {a} ", f" {b} ")
    return s.split()
def wer(ref, hyp):
    d = np.arange(len(hyp) + 1)
    for i, r in enumerate(ref, 1):
        p = d.copy(); d[0] = i
        for j, h in enumerate(hyp, 1): d[j] = min(p[j] + 1, d[j - 1] + 1, p[j - 1] + (r != h))
    return int(d[-1])
if __name__ == "__main__":
    REF = json.load(open("work/tts/lines.json"))
    if sys.argv[1:] == ["check"]:
        # the first voices come with exact timing; how close does the aligner get?
        es, ec = [], []
        for ln in REF:
            a, sr, a16 = read16k(ln["wav"]); new, sc, ws, se = retime(ln, a, sr, a16)
            idx = [i for i, s in enumerate(ln["seg"]) if s[0] in CLS and s[2] > 0]
            for k, i in enumerate(idx):
                s = ln["seg"][i]; nxt = ln["seg"][i + 1][0] if i + 1 < len(ln["seg"]) else "."; prv = ln["seg"][i - 1][0] if i else "."
                if nxt in ",.:?" or prv in ",.:?" or s[2] > 0.2: continue          # the model's own timing folds pauses into these
                es.append(se[k][0] - s[1]); ec.append((se[k][0] + se[k][1]) / 2 - (s[1] + s[2] / 2))
            print(f"{ln['n']:2d} {ln['who']:5s} match {sc:6.2f} worst word {ws:6.2f}", flush=True)
        es, ec = np.array(es) * 1000, np.array(ec) * 1000
        # the model's own times turn out to run late by a constant (its authors subtract three 25 ms frames when they
        # time words); what matters for the aligner is the scatter around that constant
        for name, e in (("start", es), ("centre", ec)):
            m = np.median(e); print(f"{len(e)} phonemes, {name}: aligner minus model {m:+.0f} ms; scatter around that: median {np.median(np.abs(e - m)):.0f} ms, 90% within {np.percentile(np.abs(e - m), 90):.0f} ms")
        sys.exit()
    SCRIPT = json.load(open("work/tts2/script.json")); out = []; report = []
    PICK = json.load(open("work/tts2/pick.json")) if os.path.exists("work/tts2/pick.json") else {}       # takes chosen by hand after reading the report, e.g. {"3": 1}
    for ln, sc in zip(REF, SCRIPT):
        best = None
        for f in sorted(glob.glob(f"work/tts2/{ln['n']:02d}_{ln['who']}_t*.wav")):
            if str(ln["n"]) in PICK and int(f[-5]) != PICK[str(ln["n"])]: continue
            a, sr, a16 = read16k(f); new, score, worst, se = retime(ln, a, sr, a16); heard = hear(a16); e = wer(norm(sc["spoken"]), norm(heard))
            rate = len(se) / max(0.1, se[-1][1] - se[0][0]); rank = (-e, worst, score)                 # fewest wrong words first, then the best worst word
            row = dict(file=f, heard=heard, word_errors=e, match=round(score, 2), worst_word=round(worst, 2), phonemes_per_s=round(rate, 1), speech=round(se[-1][1] - se[0][0], 2), lead=round(se[0][0], 2), tail=round(len(a) / sr - se[-1][1], 2), word_scores=retime.words)
            print(f"{ln['n']:2d} {ln['who']:5s} {os.path.basename(f)[-6:-4]} errors {e} match {score:6.2f} worst {worst:6.2f} rate {rate:4.1f}/s lead {row['lead']:.2f} tail {row['tail']:.2f} | {heard}", flush=True)
            report.append(row)
            if best is None or rank > best[0]: best = (rank, f, new, row)
        _, f, new, row = best
        out.append(dict(n=ln["n"], who=ln["who"], voice="chatterbox:" + ln["voice"], caption=ln["caption"], spoken=sc["spoken"], phonemes=ln["phonemes"], wav=f, take=int(f[-5]), **new))
        print(f"   -> take {f[-5]}", flush=True)
    json.dump(out, open("work/tts2/lines.json", "w"), ensure_ascii=False); json.dump(report, open("work/tts2/takes.json", "w"), ensure_ascii=False, indent=1)
    print("total", round(sum(o["dur"] for o in out), 1), "s")
