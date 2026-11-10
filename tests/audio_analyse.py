"""audio_analyse.py : checks on what the sound engine actually played (run from tests/output after sound_check.js).
  - where each spoken line starts in the recording of the set's output, against where the show's timeline puts it
  - level of the title music and of each line
  - the two pieces of music: peak, loudness over time, strongest pitches
Use the speech environment:  ../../gen/venv3/bin/python ../audio_analyse.py"""
import json, glob, numpy as np, soundfile as sf
d = json.load(open('sound_check.json')); rec, sr = sf.read('rec.wav', dtype='float32'); assert sr == 24000
beats = {ai: st for ai, st in d['beats'] if ai >= 0}; lead = d['lead']; lat = d['lat']
print(f"recording {len(rec) / sr:.1f} s, peak {np.abs(rec).max():.2f}")
def db(x): return 20 * np.log10(max(1e-9, float(np.sqrt(np.mean(x ** 2)))))
print(f"titles 0.3-4.8 s: {db(rec[int(0.3 * sr):int(4.8 * sr)]):.1f} dBFS rms")
offs = []
for ai in sorted(beats):
    f = sorted(glob.glob(f'../../gen/work/tts/mp3/{ai:02d}_*.wav'))[0]; ref, _ = sf.read(f, dtype='float32')
    exp = beats[ai] + lead - lat                       # the engine starts each recording early by the output latency
    a0 = int(max(0, exp - 1.0) * sr); a1 = int((exp + 1.0) * sr) + len(ref)
    if a1 > len(rec): continue
    seg = rec[a0:a1]; n = 1 << int(np.ceil(np.log2(len(seg) + len(ref))))
    xc = np.fft.irfft(np.fft.rfft(seg, n) * np.conj(np.fft.rfft(ref, n)), n)[:len(seg) - len(ref)]
    k = int(np.argmax(xc)); found = (a0 + k) / sr; offs.append(found - exp)
    print(f"line {ai:2d}: expected at {exp:7.3f} s, found at {found:7.3f} s, difference {1000 * (found - exp):+6.1f} ms, level {db(rec[a0 + k:a0 + k + len(ref)]):.1f} dBFS")
if offs: print(f"start-of-recording offset (common to all lines): {1000 * np.mean(offs):+.1f} ms; spread between lines: {1000 * (max(offs) - min(offs)):.1f} ms")
for k in ('intro', 'outro'):
    x = np.fromfile(f'sting_{k}.f32', dtype=np.float32); s = 44100
    print(f"music '{k}': {len(x) / s:.2f} s, peak {np.abs(x).max():.2f}, rms {db(x):.1f} dBFS")
    for t0 in np.arange(0, len(x) / s - 0.5, 0.75):
        w = x[int(t0 * s):int((t0 + 0.75) * s)]; w = w * np.hanning(len(w)); sp = np.abs(np.fft.rfft(w)); fr = np.fft.rfftfreq(len(w), 1 / s)
        top = sorted(((sp[i], fr[i]) for i in range(1, len(sp) - 1) if sp[i] > sp[i - 1] and sp[i] > sp[i + 1] and 60 < fr[i] < 1300), reverse=True)[:4]
        print(f"   {t0:4.2f}-{t0 + 0.75:4.2f} s  rms {db(x[int(t0 * s):int((t0 + 0.75) * s)]):6.1f} dB   strongest: " + ", ".join(f"{f:.0f} Hz" for _, f in sorted(top, key=lambda q: q[1])))
