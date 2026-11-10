"""lipsync_check.py <lipsync.json> <dir of the lines' WAVs> : is the mouth in time with the voice?
For each line, the mouth-opening curve the page draws is compared with the loudness of the recording it plays. A mouth
opens for vowels, which are the loud part of speech, so the two rise and fall together; sliding one against the other
shows whether the mouth runs early or late. Prints, per line and overall, the shift (ms) at which they agree best
(negative = the mouth moves first) and how well they agree there.
Run from tests/output:  node ../lipsync.js ../../lg-c4/index.html lipsync.json && ../../gen/venv4/bin/python ../lipsync_check.py lipsync.json ../../gen/work/bundle"""
import sys, json, glob, numpy as np, soundfile as sf
D = json.load(open(sys.argv[1])); wavs = sys.argv[2]; lags = []; cs = []
def smooth(x, n): return np.convolve(x, np.hanning(n) / np.hanning(n).sum(), mode="same")
for d in D:
    a, sr = sf.read(sorted(glob.glob(f"{wavs}/{d['ai']:02d}_*.wav"))[0], dtype="float32"); n = sr // 100; k = len(a) // n
    env = np.sqrt((a[:k * n].reshape(k, n) ** 2).mean(axis=1)); env = smooth(env / (env.max() + 1e-9), 7)      # loudness, 100 a second, about 40 ms of smoothing
    o = smooth(np.clip(np.array(d["o"]), 0, None), 7); m = min(len(o), len(env)); o, env = o[:m], env[:m]
    best = (-9, 0)
    for lag in range(-15, 16):                              # mouth shifted by lag * 10 ms (positive = mouth later than the sound)
        x = o[max(0, lag):m + min(0, lag)]; y = env[max(0, -lag):m - max(0, lag)]; c = float(np.corrcoef(x, y)[0, 1])
        if c > best[0]: best = (c, lag)
    # refine to the nearest ms with a parabola through the three points around the peak
    def corr(lag): x = o[max(0, lag):m + min(0, lag)]; y = env[max(0, -lag):m - max(0, lag)]; return float(np.corrcoef(x, y)[0, 1])
    if abs(best[1]) == 15:                                  # no peak inside the window: this line cannot say
        print(f"line {d['ai']:2d} {d['who']:5s}: no clear best shift within 150 ms (agreement unshifted {corr(0):.2f})"); continue
    c0, cm, cp = best[0], corr(best[1] - 1), corr(best[1] + 1); frac = float(np.clip(0.5 * (cm - cp) / (cm - 2 * c0 + cp), -0.5, 0.5)) if (cm - 2 * c0 + cp) != 0 else 0
    lag_ms = -(best[1] + frac) * 10; lags.append(lag_ms); cs.append(c0)
    print(f"line {d['ai']:2d} {d['who']:5s}: mouth agrees best with the sound when shifted {lag_ms:+5.0f} ms (agreement {c0:.2f}; unshifted {corr(0):.2f})")
print(f"{len(lags)} of {len(D)} lines with a clear answer: median shift {np.median(lags):+.0f} ms (negative = the mouth is late by that much, positive = early), range {min(lags):+.0f} to {max(lags):+.0f}; median agreement {np.median(cs):.2f}")
