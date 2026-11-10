"""asr_engine.py : transcribe what the set actually played. Cuts each line out of the recording of the page's sound
output (rec.wav, made by sound_check.js) and gives it to a speech recogniser, so the words are checked after the
microphone chains, the echoes and the beds. Run from tests/output:   ../../gen/venv4/bin/python ../asr_engine.py"""
import json, glob, numpy as np, soundfile as sf, torch, librosa
from transformers import pipeline
torch.set_num_threads(4)
asr = pipeline("automatic-speech-recognition", model="openai/whisper-base.en", device="cpu")
d = json.load(open('sound_check.json')); a, sr = sf.read('rec.wav', dtype='float32'); S = json.load(open('../../src/speech.json'))
for ai, st, lead in d['beats']:
    if ai < 0: continue
    ref, _ = sf.read(sorted(glob.glob(f'../../gen/work/bundle/{ai:02d}_*.wav'))[0], dtype='float32'); exp = st + lead
    a0 = int(max(0, exp - 1.0) * sr); seg = a[a0:a0 + 2 * sr + len(ref)]; n = 1 << int(np.ceil(np.log2(len(seg) + len(ref))))        # find the line by correlation
    k = int(np.argmax(np.fft.irfft(np.fft.rfft(seg, n) * np.conj(np.fft.rfft(ref, n)), n)[:len(seg) - len(ref)])); t0 = (a0 + k) / sr - 0.1
    x = librosa.resample(a[int(t0 * sr):int((t0 + S[ai]['len'] + 0.25) * sr)], orig_sr=sr, target_sr=16000)
    print(f"{ai:2d} {S[ai]['who']:5s} | {asr({'raw': x, 'sampling_rate': 16000})['text'].strip()}", flush=True)
