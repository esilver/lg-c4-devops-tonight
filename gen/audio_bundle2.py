"""audio_bundle2.py [tts2|tts] : level, trim and encode the spoken lines, measure the pitch of each voice, and write
../src/speech.json for the page (request 9; replaces audio_bundle.py).

  ./venv4/bin/python audio_bundle2.py          the second voices (work/tts2/lines.json, timed by align.py) -> ../src/speech.json
  ./venv4/bin/python audio_bundle2.py tts      the first voices (work/tts/lines.json, timed by their own model) -> ../src/speech_first.json
                                               ("python3 build.py first" builds the pages with those instead)

Per line the page gets: the MP3 as a data: URI, its length, the time of its first loud sample, caption words with start
times, every phoneme with start, length and relative loudness, and the pitch contour: one character per 40 ms, in half
semitones above or below that speaker's median pitch ('-' where the voice is not sounding). Brows and head follow it.
The levelled 16-bit WAVs go to work/bundle/ (work/bundle_first/ for the first voices) for the tests."""
import sys, json, re, subprocess, base64, os, numpy as np, soundfile as sf, librosa
SRC = sys.argv[1] if len(sys.argv) > 1 else "tts2"
SR = 24000; TARGET_LUFS = -19.0; LEAD, TAIL = 0.08, 0.18
# the first voices' model reports each sound about three of its 25 ms frames late (measured in align.py check; its own
# word times already allow for it), so those phoneme times are moved back
SHIFT = -0.07 if SRC == "tts" else 0.0
VOICED = "AIOWYQaiuæɐɑɒɔəɛɜɪʊʌᵻᵊmnŋlɹwjvzðʒbdɡʤT"
BUNDLE = "work/bundle" if SRC == "tts2" else "work/bundle_first"; DEST = "../src/speech.json" if SRC == "tts2" else "../src/speech_first.json"
L = json.load(open(f"work/{SRC}/lines.json")); out = []; os.makedirs(BUNDLE, exist_ok=True)
def lufs(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1])
clips = []
for ln in L:
    a, sr = sf.read(ln["wav"], dtype="float32"); assert sr == SR
    seg = [[s[0], s[1] + SHIFT, s[2], s[3]] for s in ln["seg"]]; said = [s for s in seg if s[0] not in " ,.:?!;ˈˌː" and s[2] > 0]
    first = said[0][1]; last = said[-1][1] + said[-1][2]
    cut0 = max(0.0, first - LEAD); cut1 = min(len(a) / SR, last + TAIL)
    a = a[int(cut0 * SR):int(cut1 * SR)].copy()
    a[:360] *= np.linspace(0, 1, 360); a[-720:] *= np.linspace(1, 0, 720)                       # 15 ms in, 30 ms out
    tmp = f"{BUNDLE}/_trim.wav"; sf.write(tmp, a, SR); gain = 10 ** ((TARGET_LUFS - lufs(tmp)) / 20)
    a *= gain; knee = 0.6                                   # every line at the same loudness; the rare peak above the knee is rounded off, not scaled down
    over = np.abs(a) > knee; a[over] = np.sign(a[over]) * (knee + 0.29 * np.tanh((np.abs(a[over]) - knee) / 0.29))
    f0, voiced, prob = librosa.pyin(a.astype(np.float64), fmin=60, fmax=440, sr=SR, frame_length=1536, hop_length=240)          # a value every 10 ms
    # the tracker also reports "pitch" in hiss and in silence; keep it only inside sounds that are voiced
    sung = np.zeros(len(f0), bool)
    for ch, t, d, _ in seg:
        if d > 0 and ch in VOICED: sung[max(0, int(round((t - cut0) * 100)) - 2):int(round((t + d - cut0) * 100)) + 2] = True          # the boundaries are good to a few hundredths
    f0 = np.where(voiced & sung, f0, np.nan); clips.append((ln, a, seg, cut0, gain, f0))
med = {}
for who in set(ln["who"] for ln in L):
    v = np.concatenate([c[5][~np.isnan(c[5])] for c in clips if c[0]["who"] == who]); med[who] = float(np.median(v))
for ln, a, seg, cut0, gain, f0 in clips:
    wav = f"{BUNDLE}/{ln['n']:02d}_{ln['who']}.wav"; mp3 = wav[:-4] + ".mp3"; sf.write(wav, a, SR, subtype="PCM_16")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-ac", "1", "-ar", str(SR), "-c:a", "libmp3lame", "-b:a", "64k", mp3], check=True)
    onset = int(np.argmax(np.abs(a) > 0.02)) / SR
    vow = [s[3] for s in seg if s[0] in "AIOWYQaiuæɐɑɒɔəɛɜɪʊʌᵻ" and s[2] > 0]; mv = float(np.median(vow)) if vow else 1.0
    segs = [[s[0], round(s[1] - cut0, 3), round(s[2], 3), round(min(2.0, s[3] / mv), 2)] for s in seg]
    words = [[w, round(max(0.0, t - cut0), 3)] for w, t in ln["words"]]
    st = 12 * np.log2(f0 / med[ln["who"]]); st[np.abs(st) > 10] = np.nan                    # an octave off is the tracker's mistake, not the voice
    for i in range(len(st)):                                # and so is a value far from its neighbours
        w = st[max(0, i - 7):i + 8]; w = w[~np.isnan(w)]
        if len(w) >= 3 and abs(st[i] - np.median(w)) > 4: st[i] = np.nan
    track = ""
    for i in range(0, len(st), 4):                           # 40 ms steps: the median of the voiced values in each
        w = st[i:i + 4]; w = w[~np.isnan(w)]; track += "-" if len(w) < 2 else chr(78 + int(np.clip(round(2 * float(np.median(w))), -24, 24)))
    out.append(dict(who=ln["who"], len=round(len(a) / SR, 3), onset=round(onset, 4), words=words, seg=segs, f0=track,
                    audio="data:audio/mpeg;base64," + base64.b64encode(open(mp3, "rb").read()).decode()))
    v = st[~np.isnan(st)]
    print(f"{ln['n']:2d} {ln['who']:5s} {len(a) / SR:5.2f}s gain {20 * np.log10(gain):+5.1f} dB peak {np.abs(a).max():.2f} onset {onset * 1000:4.0f} ms mp3 {os.path.getsize(mp3) // 1024} KB  pitch median {med[ln['who']]:.0f} Hz, this line {np.percentile(v, 5):+.1f} to {np.percentile(v, 95):+.1f} semitones")
json.dump(out, open(DEST, "w"), ensure_ascii=False); os.remove(f"{BUNDLE}/_trim.wav")
print("voices:", SRC, "| speech total", round(sum(o["len"] for o in out), 1), "s;", DEST, os.path.getsize(DEST) // 1024, "KB")
# A calibration clip: 0.1 s of silence, then a 20 ms tone burst. MP3 decoders differ in whether they remove the encoder's
# start-up delay; the page decodes this clip, sees where the burst lands, and shifts every line by the difference.
t = np.arange(int(0.3 * SR)) / SR; cal = np.where((t >= 0.1) & (t < 0.12), 0.8 * np.sin(2 * np.pi * 2000 * (t - 0.1)), 0).astype(np.float32)
os.makedirs("work/bundle", exist_ok=True); sf.write("work/bundle/calib.wav", cal, SR, subtype="PCM_16")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "work/bundle/calib.wav", "-ac", "1", "-ar", str(SR), "-c:a", "libmp3lame", "-b:a", "64k", "work/bundle/calib.mp3"], check=True)
open("../src/calib.txt", "w").write("data:audio/mpeg;base64," + base64.b64encode(open("work/bundle/calib.mp3", "rb").read()).decode())
