"""audio_bundle.py : level, trim and encode the spoken lines, and write ../src/speech.json for the page.
Run from gen/ after tts.py:   ./venv3/bin/python audio_bundle.py
Per line the page gets: the MP3 as a data: URI, its length, the time of its first loud sample (so the page can measure and
cancel any decoder delay), caption words with start times, and every phoneme with start, length and relative loudness."""
import json, re, subprocess, base64, os, numpy as np, soundfile as sf
SR = 24000; TARGET_LUFS = -19.0; LEAD, TAIL = 0.06, 0.16
L = json.load(open("work/tts/lines.json")); out = []; os.makedirs("work/tts/mp3", exist_ok=True)
def lufs(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1])
for ln in L:
    a, sr = sf.read(ln["wav"], dtype="float32"); assert sr == SR
    seg = ln["seg"]; first = seg[0][1]; last = max(s[1] + s[2] for s in seg if s[0] not in " ")
    cut0 = max(0.0, first - LEAD); cut1 = min(len(a) / SR, last + TAIL)
    a = a[int(cut0 * SR):int(cut1 * SR)].copy()
    a[:240] *= np.linspace(0, 1, 240); a[-480:] *= np.linspace(1, 0, 480)                       # 10 ms in, 20 ms out
    tmp = "work/tts/_trim.wav"; sf.write(tmp, a, SR); gain = 10 ** ((TARGET_LUFS - lufs(tmp)) / 20)
    a *= gain; knee = 0.6                                   # every line at the same loudness; the rare peak above the knee is rounded off, not scaled down
    over = np.abs(a) > knee; a[over] = np.sign(a[over]) * (knee + 0.29 * np.tanh((np.abs(a[over]) - knee) / 0.29)); wav = f"work/tts/mp3/{ln['n']:02d}_{ln['who']}.wav"; mp3 = wav[:-4] + ".mp3"; sf.write(wav, a, SR, subtype="PCM_16")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-ac", "1", "-ar", str(SR), "-c:a", "libmp3lame", "-b:a", "64k", mp3], check=True)
    onset = int(np.argmax(np.abs(a) > 0.02)) / SR
    vow = [s[3] for s in seg if s[0] in "AIOWYQaiuæɐɑɒɔəɛɜɪʊʌᵻ" and s[2] > 0]; med = float(np.median(vow)) if vow else 1.0
    segs = [[s[0], round(s[1] - cut0, 3), round(s[2], 3), round(min(2.0, s[3] / med), 2)] for s in seg]
    words = [[w, round(max(0.0, t - cut0), 3)] for w, t in ln["words"]]
    out.append(dict(who=ln["who"], len=round(len(a) / SR, 3), onset=round(onset, 4), words=words, seg=segs,
                    audio="data:audio/mpeg;base64," + base64.b64encode(open(mp3, "rb").read()).decode()))
    print(f"{ln['n']:2d} {ln['who']:5s} {len(a) / SR:5.2f}s gain {20 * np.log10(gain):+5.1f} dB peak {np.abs(a).max():.2f} onset {onset * 1000:4.0f} ms mp3 {os.path.getsize(mp3) // 1024} KB")
json.dump(out, open("../src/speech.json", "w"), ensure_ascii=False)
print("speech total", round(sum(o["len"] for o in out), 1), "s; speech.json", os.path.getsize("../src/speech.json") // 1024, "KB")
# A calibration clip: 0.1 s of silence, then a 20 ms tone burst. MP3 decoders differ in whether they remove the encoder's
# start-up delay; the page decodes this clip, sees where the burst lands, and shifts every line by the difference.
t = np.arange(int(0.3 * SR)) / SR; cal = np.where((t >= 0.1) & (t < 0.12), 0.8 * np.sin(2 * np.pi * 2000 * (t - 0.1)), 0).astype(np.float32)
sf.write("work/tts/mp3/calib.wav", cal, SR, subtype="PCM_16")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "work/tts/mp3/calib.wav", "-ac", "1", "-ar", str(SR), "-c:a", "libmp3lame", "-b:a", "64k", "work/tts/mp3/calib.mp3"], check=True)
open("../src/calib.txt", "w").write("data:audio/mpeg;base64," + base64.b64encode(open("work/tts/mp3/calib.mp3", "rb").read()).decode())
print("calibration clip", os.path.getsize("work/tts/mp3/calib.mp3"), "bytes")
