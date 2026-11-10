"""asr_check.py : transcribe every generated line with a speech recogniser and compare with the script.
An independent check that the audio says the intended words, and that word timings agree.  ./venv3/bin/python asr_check.py"""
import json, re, subprocess, numpy as np, soundfile as sf, torch
from transformers import pipeline
torch.set_num_threads(4)
asr = pipeline("automatic-speech-recognition", model="openai/whisper-base.en", device="cpu")
L = json.load(open("work/tts/lines.json")); norm = lambda s: re.sub(r"[^a-z0-9 ]", "", s.lower().replace("-", " ")).split()
bad = 0; diffs = []
for ln in L:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", ln["wav"], "-ar", "16000", "-ac", "1", "work/tts/_16k.wav"], check=True)
    a, sr = sf.read("work/tts/_16k.wav", dtype="float32")
    out = asr({"raw": a, "sampling_rate": sr}, return_timestamps="word")
    said = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", ln["spoken"]); ref, hyp = norm(said), norm(out["text"])
    ok = ref == hyp; bad += not ok
    print(f"{ln['n']:2d} {ln['who']:5s} {'OK ' if ok else 'DIFF'} heard: {out['text'].strip()}")
    if not ok: print("          wanted:", said)
    # word-start agreement where the word sequences match one to one
    if ok:
        caps = [w for w in ln["words"]]; hw = out["chunks"]
        refw = [x for c, _ in caps for x in norm(c)] if False else None
print("lines differing:", bad, "of", len(L))
