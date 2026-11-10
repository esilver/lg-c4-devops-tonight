"""mux.py <frames dir> <out.mp4> [--engine rec.wav sound_check.json] [--scale WxH] [--fps N] [--crf N]
Lay a sound track under rendered frames and encode a video.
Default track: each line's recording placed where the timeline says it starts (plus the title music when present).
With --engine: the recording of what the page actually played, shifted so its first line sits where the timeline puts it.
Run with the speech environment (numpy, soundfile):  ../../gen/venv3/bin/python ../mux.py rec_show show.mp4"""
import sys, json, glob, subprocess, numpy as np, soundfile as sf
a = sys.argv[1:]; frames, out = a[0], a[1]; SR = 24000
opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
fps = float(opt('--fps', '30')); T = json.load(open(f'{frames}/timing.json')); n = int(T['len'] * SR); mix = np.zeros(n + SR, dtype=np.float32)
ref = lambda ai: sf.read(sorted(glob.glob(f'../../gen/work/bundle/{ai:02d}_*.wav'))[0], dtype='float32')[0]      # the lines as bundled into the page
if '--engine' in a:
    i = a.index('--engine'); rec, sr = sf.read(a[i + 1], dtype='float32'); assert sr == SR; d = json.load(open(a[i + 2]))
    # Where do the first and the last line sit in the recording? The recorder runs on the sound card's clock and the page
    # on the computer's, which differ by a few hundredths of a percent, so the recording is shifted AND stretched to fit.
    def find(b):
        r = ref(b['ai']); exp = b['start'] + b['lead']; a0 = int(max(0, exp - 1.5) * SR); seg = rec[a0:a0 + int(3 * SR) + len(r)]; m = 1 << int(np.ceil(np.log2(len(seg) + len(r))))
        return exp, (a0 + int(np.argmax(np.fft.irfft(np.fft.rfft(seg, m) * np.conj(np.fft.rfft(r, m)), m)[:len(seg) - len(r)]))) / SR
    said = [b for b in T['beats'] if b['ai'] >= 0 and b['start'] + b['dur'] < len(rec) / SR - 1]; (e0, f0), (e1, f1) = find(said[0]), find(said[-1])
    rate = (f1 - f0) / (e1 - e0) if e1 > e0 else 1.0
    print(f'engine recording: first line {1000 * (f0 - e0):+.0f} ms from the timeline, last line {1000 * (f1 - e1):+.0f} ms; clocks differ by {100 * (rate - 1):+.3f}%; fitting it')
    t = f0 + (np.arange(len(mix)) / SR - e0) * rate; mix[:] = np.interp(t * SR, np.arange(len(rec)), rec, left=0, right=0)
else:
    for b in T['beats']:
        if b['ai'] < 0: continue
        r = ref(b['ai']); k = int((b['start'] + b['lead']) * SR); mix[k:k + len(r)] += r[:max(0, len(mix) - k)]
    for kind, f in (('intro', 'sting_intro.f32'), ('outro', 'sting_outro.f32')):
        bb = [b for b in T['beats'] if b.get('kind') == kind]
        if bb and glob.glob(f):
            x = np.fromfile(f, dtype=np.float32); x = x[::1]; idx = (np.arange(int(len(x) * SR / 44100)) * 44100 / SR).astype(int); x = x[idx] * 0.5
            k = int(bb[0]['start'] * SR); mix[k:k + len(x)] += x[:max(0, len(mix) - k)]
mix = mix[:n]; peak = float(np.abs(mix).max()); print('track', round(len(mix) / SR, 1), 's, peak', round(peak, 2)); sf.write(f'{frames}/track.wav', mix, SR, subtype='PCM_16')
vf = ['-vf', 'scale=' + opt('--scale').replace('x', ':') + ':flags=lanczos'] if opt('--scale') else []
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(fps), '-i', f'{frames}/f%0{len(glob.glob(frames + "/f*.jpg")[0].split("/f")[-1]) - 4}d.jpg', '-i', f'{frames}/track.wav', *vf,
                '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', opt('--crf', '20'), '-c:a', 'aac', '-b:a', '128k', '-shortest', '-movflags', '+faststart', out], check=True)
print('wrote', out)
