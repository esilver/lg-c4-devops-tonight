"""voice_quality.py : an estimate of how natural and how clean each voice set sounds (request 9).

Nobody listened to these voices while they were made, so two published estimators stand in for an ear. Both ship with
torchaudio ("SQUIM"):
  subjective  predicts the mean opinion score (1 = bad, 5 = excellent) listeners would give a clip, judged against a
              recording of a real person speaking (a different sentence; torchaudio's own sample clip)
  objective   predicts three standard measures without any reference: STOI (intelligibility, 0-1), PESQ (quality, 1-4.5)
              and SI-SDR (how far the voice stands above noise and distortion, dB)
They are estimates from a model, good for comparing two sets of the same lines, not a verdict.

  ./venv4/bin/python voice_quality.py      compares work/bundle_first (first voices) with work/bundle (second voices)"""
import json, glob, numpy as np, soundfile as sf, torch, torchaudio, librosa
from torchaudio.pipelines import SQUIM_SUBJECTIVE, SQUIM_OBJECTIVE
torch.set_num_threads(4)
subj, obj = SQUIM_SUBJECTIVE.get_model(), SQUIM_OBJECTIVE.get_model()
ref_path = torchaudio.utils.download_asset("tutorial-assets/Lab41-SRI-VOiCES-src-sp0307-ch127535-sg0042.wav")
ref, sr = sf.read(ref_path, dtype="float32"); ref = torch.tensor(librosa.resample(ref, orig_sr=sr, target_sr=16000))[None]
def score(path):
    a, sr = sf.read(path, dtype="float32"); x = torch.tensor(librosa.resample(a, orig_sr=sr, target_sr=16000))[None]
    with torch.no_grad(): mos = float(subj(x, ref)[0]); stoi, pesq, sdr = (float(v[0]) for v in obj(x))
    return mos, stoi, pesq, sdr
rows = {}
for name, d in (("first", "work/bundle_first"), ("second", "work/bundle")):
    for f in sorted(glob.glob(d + "/[0-9][0-9]_*.wav")):
        n, who = f.split("/")[-1][:-4].split("_"); rows.setdefault((int(n), who), {})[name] = score(f)
print("line  who     opinion score      intelligibility     quality (PESQ)     above noise (dB)")
print("              first  second       first  second       first  second       first  second")
for (n, who), r in sorted(rows.items()):
    a, b = r["first"], r["second"]; print(f"{n:3d}  {who:6s}  {a[0]:5.2f}  {b[0]:5.2f}        {a[1]:5.3f}  {b[1]:5.3f}        {a[2]:5.2f}  {b[2]:5.2f}        {a[3]:5.1f}  {b[3]:5.1f}")
out = {}
for who in ["paige", "cy", "dee", "sunny", "mel", "all"]:
    sel = [r for (n, w), r in rows.items() if who in (w, "all")]
    m = {k: [round(float(np.mean([r[k][i] for r in sel])), 3) for i in range(4)] for k in ("first", "second")}; out[who] = m
    print(f"mean {who:6s}  {m['first'][0]:5.2f}  {m['second'][0]:5.2f}        {m['first'][1]:5.3f}  {m['second'][1]:5.3f}        {m['first'][2]:5.2f}  {m['second'][2]:5.2f}        {m['first'][3]:5.1f}  {m['second'][3]:5.1f}")
json.dump(out, open("work/voice_quality.json", "w"), indent=1)
