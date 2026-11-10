"""lipteach.py : a learned reference for how the mouth should move (request 10).

Two rounds of hand-written rules (which sound opens the jaw how far) still left the lips looking wrong. This script
asks a network that was trained on real talking faces instead. Wav2Lip takes a face and a stretch of sound and paints
the mouth that goes with the sound. Its picture is small and soft, so it is not shown; it is MEASURED. For every
1/50 s of every line, a landmark network finds the lips in Wav2Lip's picture, giving how far the mouth is open and how
wide it is. The same measurement on each presenter's own pose renders says which pose shows that opening on that
face. The page then plays those curves with the sharp poses.

That also settles how much each face should move: a presenter whose mouth opens little at a given setting (the guest)
is driven further, until the measured opening matches.

  ./venv6/bin/python lipteach.py calib            measure every presenter's poses -> work/lipcal.json
  ./venv6/bin/python lipteach.py teach [set]      measure Wav2Lip on every line of a voice set (bundle, bundle_first,
                                                  bundle_second) -> work/<set>/lip_raw.json   (add line numbers to redo only those)
  ./venv6/bin/python lipteach.py map [set]        turn the measurements into jaw and lip-shape curves in the set's speech file

Weights only (ONNX files from facefusion/models-3.0.0 on the Hugging Face Hub); the glue is written here."""
import sys, json, os, glob, math, numpy as np, cv2, onnxruntime as ort, librosa, soundfile as sf
from scipy.signal import lfilter
W, H, FPS = 1024, 576, int(os.environ.get('LIP_FPS', '50'))      # measurements a second; LIP_FPS=25 halves the work for a set that matters less
so = ort.SessionOptions(); so.intra_op_num_threads = 4
_s = {}
def sess(n):
    if n not in _s: _s[n] = ort.InferenceSession(f"models/w2l/{n}.onnx", so, providers=["CPUExecutionProvider"])
    return _s[n]
def mel(a16):
    """Wav2Lip's own spectrogram: 80 bands, 80 frames a second, scaled to -4..4."""
    D = librosa.stft(lfilter([1, -0.97], [1], a16), n_fft=800, hop_length=200, win_length=800)
    S = librosa.filters.mel(sr=16000, n_fft=800, n_mels=80, fmin=55, fmax=7600) @ np.abs(D)
    return np.clip(8 * ((20 * np.log10(np.maximum(1e-5, S)) - 20 + 100) / 100) - 4, -4, 4).astype(np.float32)
def facebox(meta):
    x, y, w, h = meta["lm"]["box"]; return int(round(x)), int(round(y)), int(round(x + w)), int(round(min(H, y + h * 1.04)))       # a little chin room, as Wav2Lip's own cropping has
def landmarks(frame_bgr, box):
    """68 face landmarks in frame coordinates (2DFAN4): the face box is scaled to 195 px inside a 256 px crop."""
    x1, y1, x2, y2 = box; sc = 195 / max(x2 - x1, y2 - y1); M = np.array([[sc, 0, (256 - (x1 + x2) * sc) / 2], [0, sc, (256 - (y1 + y2) * sc) / 2]])
    crop = cv2.warpAffine(frame_bgr, M, (256, 256), flags=cv2.INTER_AREA if sc < 1 else cv2.INTER_LINEAR)
    lm = sess("2dfan4").run(None, {"input": crop.transpose(2, 0, 1)[None].astype(np.float32) / 255})[0][0, :, :2] / 64 * 256
    return (lm - M[:, 2]) / sc
def measure(lm, iod):
    """Mouth opening (gap between the inner lips), outer lip height and mouth width, in eye distances."""
    return [float(np.linalg.norm(lm[66] - lm[62]) / iod), float(np.linalg.norm(lm[57] - lm[51]) / iod), float(np.linalg.norm(lm[54] - lm[48]) / iod)]
class Face:
    def __init__(self, key):
        d = f"work/{key}"; self.key = key; self.meta = json.load(open(f"{d}/meta.json")); self.iod = self.meta["iod"]; self.box = facebox(self.meta)
        self.base = cv2.imread(f"{d}/frame_lp2.png"); self.A = np.array(json.load(open(f"{d}/lp/affine.json"))["A"])
        self.mask = cv2.imread(f"{d}/lp/masks2.png")[..., 2:3].astype(np.float32) / 255            # the mouth region (red channel)
        x1, y1, x2, y2 = self.box; self.small = cv2.resize(self.base[y1:y2, x1:x2], (96, 96), interpolation=cv2.INTER_AREA)
    def pose(self, name):
        """The frame as the page would show it with one pose render in the mouth region."""
        im = cv2.imread(f"work/{self.key}/lp/{name}.png"); M = self.A.copy(); sc = math.sqrt(abs(np.linalg.det(M[:, :2])))
        if sc < 0.92: im = cv2.resize(im, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA); M[:, :2] /= sc
        f = cv2.warpAffine(im, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
        return (self.base * (1 - self.mask) + f * self.mask).round().astype(np.uint8)
    def soften(self, frame):
        """Through the same keyhole as Wav2Lip's output: the face at 96 px and back, so both are measured alike."""
        x1, y1, x2, y2 = self.box; out = frame.copy()
        out[y1:y2, x1:x2] = cv2.resize(cv2.resize(frame[y1:y2, x1:x2], (96, 96), interpolation=cv2.INTER_AREA), (x2 - x1, y2 - y1), interpolation=cv2.INTER_CUBIC); return out
    def speak(self, a16, model="wav2lip_96"):
        """Wav2Lip's mouth for every 1/50 s of the sound, pasted into the frame; yields frames."""
        m = mel(a16); n = int(len(a16) / 16000 * FPS); x1, y1, x2, y2 = self.box
        tgt = np.concatenate([self.small, self.small], axis=2).astype(np.float32) / 255; tgt[48:, :, :3] = 0; tgt = tgt.transpose(2, 0, 1)
        for i0 in range(0, n, 32):
            idx = range(i0, min(n, i0 + 32)); src = []
            for i in idx:
                # The stock inference code starts the 0.2 s window of sound AT the frame's time. Measured here, that shows each
                # mouth about a tenth of a second early. The window is started 75 ms before the frame's time instead; what
                # offset remains is measured against the audio and removed in "map".
                k = int(round(i * 80 / FPS)) - 6; c = m[:, max(0, k):max(0, k + 16)]
                if k < 0: c = np.pad(c, ((0, 0), (min(16, -k), 0)), constant_values=-4)
                if c.shape[1] < 16: c = np.pad(c, ((0, 0), (0, 16 - c.shape[1])), constant_values=-4)
                src.append(c[None])
            out = sess(model).run(None, {"source": np.stack(src), "target": np.repeat(tgt[None], len(src), axis=0)})[0]
            for o in out:
                f = self.base.copy(); f[y1:y2, x1:x2] = cv2.resize((o.transpose(1, 2, 0).clip(0, 1) * 255).astype(np.uint8), (x2 - x1, y2 - y1), interpolation=cv2.INTER_CUBIC); yield f
KEYS = ["paige", "cy", "dee", "sunny", "mel"]
SPEECH = dict(bundle="../src/speech.json", bundle_first="../src/speech_first.json", bundle_second="../src/speech_second.json")
JAW = 46.0                                           # jaw units at an opening of 1 on the page (src/news.js)
def enc(v, lo, hi): return "".join(chr(40 + int(round(float(np.clip((x - lo) / (hi - lo), 0, 1)) * 85))) for x in v)
def smooth3(x):
    x = np.asarray(x, float); p = np.pad(x, 1, mode="edge"); m = np.median(np.stack([p[:-2], p[1:-1], p[2:]]), axis=0); p = np.pad(m, 1, mode="edge"); return (p[:-2] + 2 * p[1:-1] + p[2:]) / 4
if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "calib":
        out = {}
        for key in KEYS:
            F = Face(key); dense = json.load(open(f"work/{key}/lp/dense.json")); JN, JS = dense["jn"], dense["js"]
            m = lambda name: measure(landmarks(F.soften(F.pose(name)), F.box), F.iod)
            cal = dict(jn=JN, js=JS, n=[measure(landmarks(F.soften(F.base), F.box), F.iod)] + [m(f"d_n{i:02d}") for i in range(1, len(JN))])
            for r in ("e1", "e2", "w1", "w2", "sg"): cal[r] = [m(f"d_{r}_{i}") for i in range(len(JS))]
            cal["p"] = m("f_p"); cal["sh"] = m("d_sh"); out[key] = cal
            print(f"{key:5s} opening: shut {cal['n'][0][0]:.3f}, pressed {cal['p'][0]:.3f}, jaw 16 {cal['n'][4][0]:.3f}, jaw 32 {cal['n'][7][0]:.3f}, jaw 60 {cal['n'][11][0]:.3f} | width: neutral {cal['n'][0][2]:.3f}, spread {cal['e2'][0][2]:.3f}, round {cal['w2'][0][2]:.3f}, smile {cal['sg'][0][2]:.3f}", flush=True)
        json.dump(out, open("work/lipcal.json", "w"))
    elif mode == "teach":
        SET = sys.argv[2] if len(sys.argv) > 2 else "bundle"; faces = {}; lines = []; only = set(int(x) for x in sys.argv[3:])       # teach bundle 0 13: only those lines again
        old = {l["n"]: l for l in json.load(open(f"work/{SET}/lip_raw.json"))["lines"]} if only else {}
        for f in sorted(glob.glob(f"work/{SET}/[0-9][0-9]_*.wav")):
            n, who = os.path.basename(f)[:-4].split("_")
            if only and int(n) not in only: lines.append(old[int(n)]); continue
            F = faces.setdefault(who, Face(who)); a, sr = sf.read(f, dtype="float32"); a16 = librosa.resample(a, orig_sr=sr, target_sr=16000)
            v = [measure(landmarks(fr, F.box), F.iod) for fr in F.speak(a16)]; lines.append(dict(n=int(n), who=who, v=[[round(x, 4) for x in r] for r in v]))
            print(f"{n} {who:5s} {len(v)} frames, opening {min(r[0] for r in v):.3f} to {max(r[0] for r in v):.3f}", flush=True)
        json.dump(dict(fps=FPS, lines=lines), open(f"work/{SET}/lip_raw.json", "w"))
    elif mode == "map":
        SET = sys.argv[2] if len(sys.argv) > 2 else "bundle"; raw = json.load(open(f"work/{SET}/lip_raw.json")); cal = json.load(open("work/lipcal.json")); S = json.load(open(SPEECH[SET])); fps = raw["fps"]
        # 1. Is the reference early or late? The sound itself says when the lips are shut: a "p" has a stretch of silence while
        #    they are closed, and the reference's lips should be at their tightest in the middle of it. Even with its window of
        #    sound moved back (see speak), the reference is still a few hundredths of a second early; it is moved by the median.
        off = []
        for ln, sp in zip(raw["lines"], S):
            a, sr = sf.read(sorted(glob.glob(f"work/{SET}/{ln['n']:02d}_*.wav"))[0], dtype="float32"); h = sr // 200
            db = 20 * np.log10(np.maximum(np.array([np.sqrt(np.mean(a[i:i + h] ** 2)) for i in range(0, len(a) - h, h)]), 1e-6)); o = np.array(ln["v"])[:, 0]
            od = np.convolve(np.interp(np.arange(len(db)) / 200, np.arange(len(o)) / fps, o), np.hanning(7) / np.hanning(7).sum(), mode="same")
            for ch, t, dur, _ in sp["seg"]:
                if ch != "p" or dur <= 0: continue
                i0, i1 = int((t - 0.03) * 200), int((t + dur + 0.02) * 200); q = np.where(db[i0:i1] < np.percentile(db, 90) - 28)[0]
                if len(q) < 6: continue                                  # no clear silence in this one
                c = (i0 + (q[0] + q[-1]) / 2) / 200; j0, j1 = int((c - 0.07) * 200), int((c + 0.07) * 200); off.append((j0 + int(np.argmin(od[j0:j1]))) / 200 - c)
        med = float(np.median(off)) if len(off) >= 6 else -0.03
        glag = float(np.clip(med, -0.08, 0.08))                          # put the tightest moment in the middle of the silence
        print(f"{SET}: the reference's lips are tightest {1000 * med:+.0f} ms from the middle of the silence of a p (median of {len(off)}, half of them between {1000 * np.percentile(off, 25):+.0f} and {1000 * np.percentile(off, 75):+.0f}); moving it {-1000 * round(glag * fps) / fps:+.0f} ms")
        lags = {k: glag for k in KEYS}
        # 2. Where is "shut" in the reference, and how far does it open each face? Its picture of a shut mouth does not measure
        #    the same as the photograph's, in pauses it sometimes leaves the lips apart, and it opens some faces more timidly
        #    than others, which says something about the network and not about how those presenters speak. So each
        #    presenter's readings are put on a common footing: the 12th percentile while speaking is "shut" (that is where
        #    their m, b and p readings lie), and the 90th percentile is the same opening for all five, set 15% above the
        #    middle presenter's because the reference under-opens as a whole (its pictures are averages, and averages are timid).
        speak = {k: [] for k in KEYS}; quietw = {k: [] for k in KEYS}
        for ln, sp in zip(raw["lines"], S):
            v = np.array(ln["v"]); o = smooth3(v[:, 0]); lag = lags[ln["who"]]
            for ch, t, dur, _ in sp["seg"]:
                if dur <= 0 or ch in " ˈˌː": continue
                a, b = max(0, int((t + lag) * fps)), int((t + dur + lag) * fps) + 1
                if ch in ",.:?!;":
                    if dur > 0.25: quietw[ln["who"]] += v[int((t + 0.08 + lag) * fps):int((t + dur - 0.08 + lag) * fps), 2].tolist()
                else: speak[ln["who"]] += o[a:b].tolist()
        shut = {k: float(np.percentile(speak[k], 12)) for k in KEYS}; top = {k: float(np.percentile(speak[k], 90)) - shut[k] for k in KEYS}
        target = 1.15 * float(np.median(list(top.values()))); amp = {k: float(np.clip(target / top[k], 0.7, 2.0)) for k in KEYS}
        print("   shut reading:", {k: round(v, 3) for k, v in shut.items()}, "| loud-end opening above it:", {k: round(v, 3) for k, v in top.items()}, f"| common level {target:.3f} eye distances, so scaled by", {k: round(v, 2) for k, v in amp.items()})
        stats = []
        for ln, sp in zip(raw["lines"], S):
            c = cal[ln["who"]]; n = np.array(c["n"]); JN = np.array(c["jn"], float); JS = np.array(c["js"], float); v = np.array(ln["v"]); who = ln["who"]
            open_n = np.maximum.accumulate(n[:, 0]); d_wid = (float(np.median(quietw[who])) if len(quietw[who]) > 10 else float(np.median(v[:, 2]))) - n[0, 2]
            o_raw = open_n[0] + np.clip(smooth3(v[:, 0]) - shut[who], 0, None) * amp[who]; w_raw = smooth3(smooth3(v[:, 2])) - d_wid
            jaw = np.interp(o_raw, open_n, JN)                                            # which of this face's own poses shows that opening
            # Pressing the lips together for m, b and p is left to the page's closure track, which knows exactly when those sounds are.
            o = jaw / JAW; o = np.where(o > 0.9, 0.9 + (o - 0.9) * 0.5, o)                    # the very widest moments are eased back
            wn = np.interp(jaw, JN, n[:, 2]); re = np.interp(jaw, JS, np.array(c["e2"])[:, 2]) / np.interp(jaw, JN, n[:, 2]); rw = np.interp(jaw, JS, np.array(c["w2"])[:, 2]) / wn; q = w_raw / wn
            s = np.clip(np.where(q >= 1, (q - 1) / np.maximum(0.02, re - 1), -(1 - q) / np.maximum(0.02, 1 - rw)), -1, 1); s = smooth3(s)
            k = int(round(lags[ln["who"]] * fps)); sh = lambda x: np.concatenate([x[k:], np.repeat(x[-1:], k)]) if k >= 0 else np.concatenate([np.repeat(x[:1], -k), x[:k]])     # undo the lag
            o, s = sh(o), sh(s); sp["lip"] = dict(fps=fps, o=enc(o, -0.12, 1.3), s=enc(s, -1, 1)); stats.append((ln["n"], ln["who"], float(np.median(o[o > 0.03])) if (o > 0.03).any() else 0, float(o.max()), float(np.mean(o < 0.03)), float(s.min()), float(s.max())))
        json.dump(S, open(SPEECH[SET], "w"), ensure_ascii=False)
        for n, who, med, mx, pr, s0, s1 in stats: print(f"{n:2d} {who:5s} typical opening {med:.2f}, widest {mx:.2f}, shut {100 * pr:2.0f}% of the time, shape {s0:+.2f} to {s1:+.2f}")
    elif mode == "proto":                                  # a first look: one presenter's poses and one line
        F = Face(sys.argv[2]); dense = json.load(open(f"work/{F.key}/lp/dense.json"))
        print("neutral photo:", [round(v, 3) for v in measure(landmarks(F.base, F.box), F.iod)], "softened:", [round(v, 3) for v in measure(landmarks(F.soften(F.base), F.box), F.iod)])
        for i, j in enumerate(dense["jn"]):
            if i == 0: continue
            fr = F.pose(f"d_n{i:02d}"); print(f"jaw {j:2d}: sharp", [round(v, 3) for v in measure(landmarks(fr, F.box), F.iod)], "softened", [round(v, 3) for v in measure(landmarks(F.soften(fr), F.box), F.iod)])
        for r in ("e2", "w2", "sg"):
            for i in (0, 3, 7): fr = F.pose(f"d_{r}_{i}"); print(f"{r} step {i}: softened", [round(v, 3) for v in measure(landmarks(F.soften(fr), F.box), F.iod)])
        a, sr = sf.read(sys.argv[3], dtype="float32"); a16 = librosa.resample(a, orig_sr=sr, target_sr=16000); rows = []
        for mdl in ("wav2lip_96", "wav2lip_gan_96"):
            v = np.array([measure(landmarks(f, F.box), F.iod) for f in F.speak(a16, mdl)]); rows.append(v)
            print(mdl, "frames", len(v), "opening min/median/max", v[:, 0].min().round(3), np.median(v[:, 0]).round(3), v[:, 0].max().round(3), "| width min/max", v[:, 2].min().round(3), v[:, 2].max().round(3))
        np.save("work/_proto.npy", np.array(rows)); k = 0
        for f in F.speak(a16, "wav2lip_96"):
            if k in (30, 45, 60, 75, 90, 105): cv2.imwrite(f"out/_w2l_{k}.jpg", f[F.box[1] - 20:F.box[3] + 20, F.box[0] - 20:F.box[2] + 20])
            k += 1
