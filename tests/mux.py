"""mux.py <frames dir> <out.mp4> [--engine rec.wav sound_check.json] [--scale WxH] [--fps N]
Lay a sound track under rendered frames and encode a video.
Default track: each line's recording placed where the timeline says it starts (plus the title music when present).
With --engine: the recording of what the page actually played, shifted so its first line sits where the timeline puts it.
Run with the speech environment (numpy, soundfile):  ../../gen/venv3/bin/python ../mux.py rec_show show.mp4"""
import sys, json, glob, subprocess, numpy as np, soundfile as sf
a = sys.argv[1:]; frames, out = a[0], a[1]; SR = 24000
opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
fps = float(opt('--fps', '30')); T = json.load(open(f'{frames}/timing.json')); n = int(T['len'] * SR); mix = np.zeros(n + SR, dtype=np.float32)
ref = lambda ai: sf.read(sorted(glob.glob(f'../../gen/work/tts/mp3/{ai:02d}_*.wav'))[0], dtype='float32')[0]
if '--engine' in a:
    i = a.index('--engine'); rec, sr = sf.read(a[i + 1], dtype='float32'); assert sr == SR; d = json.load(open(a[i + 2]))
    first = next(b for b in T['beats'] if b['ai'] >= 0); r = ref(first['ai']); exp = first['start'] + T['lead']
    a0 = int(max(0, exp - 1.5) * SR); seg = rec[a0:a0 + int(3 * SR) + len(r)]; m = 1 << int(np.ceil(np.log2(len(seg) + len(r))))
    k = int(np.argmax(np.fft.irfft(np.fft.rfft(seg, m) * np.conj(np.fft.rfft(r, m)), m)[:len(seg) - len(r)])); shift = (a0 + k) / SR - exp
    print(f'engine recording is {1000 * shift:+.0f} ms from the timeline; shifting it'); s = int(round(shift * SR))
    src = rec[s:] if s >= 0 else np.concatenate([np.zeros(-s, dtype=np.float32), rec]); L = min(len(src), len(mix)); mix[:L] = src[:L]
else:
    for b in T['beats']:
        if b['ai'] < 0: continue
        r = ref(b['ai']); k = int((b['start'] + T['lead']) * SR); mix[k:k + len(r)] += r[:max(0, len(mix) - k)]
    for kind, f in (('intro', 'sting_intro.f32'), ('outro', 'sting_outro.f32')):
        bb = [b for b in T['beats'] if b.get('kind') == kind]
        if bb and glob.glob(f):
            x = np.fromfile(f, dtype=np.float32); x = x[::1]; idx = (np.arange(int(len(x) * SR / 44100)) * 44100 / SR).astype(int); x = x[idx] * 0.5
            k = int(bb[0]['start'] * SR); mix[k:k + len(x)] += x[:max(0, len(mix) - k)]
mix = mix[:n]; peak = float(np.abs(mix).max()); print('track', round(len(mix) / SR, 1), 's, peak', round(peak, 2)); sf.write(f'{frames}/track.wav', mix, SR, subtype='PCM_16')
vf = ['-vf', 'scale=' + opt('--scale').replace('x', ':') + ':flags=lanczos'] if opt('--scale') else []
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(fps), '-i', f'{frames}/f%0{len(glob.glob(frames + "/f*.jpg")[0].split("/f")[-1]) - 4}d.jpg', '-i', f'{frames}/track.wav', *vf,
                '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-c:a', 'aac', '-b:a', '128k', '-shortest', '-movflags', '+faststart', out], check=True)
print('wrote', out)
