"""prep.py <key> <seed> : work/<key>/ frame.png (final 1024x576), face0.png (512 crop), meta.json, then mouth/blink candidates.
Re-running skips whatever already exists."""
import sys, json, os
from sdlib import *
from facelib import *
from prompts import P, DESC
key, seed = sys.argv[1], sys.argv[2]
W, H = 1024, 576
d = f"work/{key}"; os.makedirs(d, exist_ok=True)
pipe = load("dpm"); t0 = time.time()
pf = f"RAW photo, close-up portrait of {DESC[key]}, "; sf = ", detailed skin texture, sharp focus"
if not os.path.exists(f"{d}/meta.json"):
    base = Image.open(f"out/base_{key}_{seed}.png").convert("RGB")
    frame = img2img(pipe, P[key], base.resize((W, H), Image.LANCZOS), strength=0.3, steps=20, cfg=5.0, seed=1)
    frame.save(f"{d}/hires.png"); print("hires", round(time.time() - t0), flush=True)
    lm = landmarks(frame); assert lm, "no face"
    eL, eR, mL, mR = (np.array(lm[k]) for k in ("eyeL", "eyeR", "mouthL", "mouthR"))
    iod = float(np.linalg.norm(eR - eL)); ec = (eL + eR) / 2; mc = (mL + mR) / 2
    side = min(int(round(3.6 * iod / 8)) * 8, H)
    x0 = int(round(ec[0] - side / 2)); y0 = int(round(ec[1] + 0.45 * iod - side / 2))
    x0 = min(max(x0, 0), W - side); y0 = min(max(y0, 0), H - side); f = 512 / side
    crop = frame.crop((x0, y0, x0 + side, y0 + side)).resize((512, 512), Image.LANCZOS)
    face0 = img2img(pipe, pf + "lips closed, looking at the camera" + sf, crop, strength=0.35, steps=20, cfg=5.0, seed=2)
    face0.save(f"{d}/face0.png"); print("face", round(time.time() - t0), flush=True)
    face0r = decode(pipe, encode(pipe, face0)); face0r.save(f"{d}/face0r.png")   # same VAE round trip as every variant
    out = frame.copy(); out.paste(face0r.resize((side, side), Image.LANCZOS), (x0, y0), ellipse_mask((512, 512), 256, 256, 212, 232, blur=16).resize((side, side), Image.BILINEAR))
    out.save(f"{d}/frame.png")
    c = lambda p: ((p[0] - x0) * f, (p[1] - y0) * f)
    mcc = c(mc); mw = float(np.linalg.norm(mR - mL)) * f; iodc = iod * f
    mouth = dict(cx=mcc[0], cy=mcc[1] + 0.20 * mw, rx=0.78 * mw, ry=0.58 * mw)
    eyes = [dict(cx=c(e)[0], cy=c(e)[1], rx=0.36 * iodc, ry=0.22 * iodc) for e in (eL, eR)]
    json.dump(dict(x0=x0, y0=y0, side=side, f=f, iod=iod, lm=lm, mouth=mouth, eyes=eyes), open(f"{d}/meta.json", "w"), indent=1)
meta = json.load(open(f"{d}/meta.json")); face0 = Image.open(f"{d}/face0.png").convert("RGB"); mouth, eyes = meta["mouth"], meta["eyes"]
mm = ellipse_mask((512, 512), mouth["cx"], mouth["cy"], mouth["rx"], mouth["ry"], blur=6)
em = Image.new("L", (512, 512), 0)
for e in eyes: em.paste(255, mask=ellipse_mask((512, 512), e["cx"], e["cy"], e["rx"], e["ry"]))
em = em.filter(ImageFilter.GaussianBlur(5))
NS = NEG + ", smile, grin, laughing"
jobs = [
 ("mouth_closed_1", "lips pressed together, mouth closed, neutral expression", mm, 1, NS),
 ("mouth_sm_1", "lips parted, mouth slightly open, mid-sentence, neutral expression", mm, 1, NS),
 ("mouth_sm_2", "lips parted, mouth slightly open, mid-sentence, neutral expression", mm, 2, NS),
 ("mouth_open_1", "mouth open, talking, teeth visible, saying ah", mm, 1, NEG),
 ("mouth_open_2", "mouth open, talking, teeth visible, saying ah", mm, 2, NEG),
 ("mouth_oh_1", "mouth open in a small round O shape, saying oh, surprised", mm, 1, NS + ", teeth"),
 ("mouth_oh_2", "mouth open in a small round O shape, saying oh, surprised", mm, 2, NS + ", teeth"),
 ("mouth_ee_1", "mouth wide, talking, showing upper teeth, saying ee", mm, 1, NEG),
 ("mouth_ah_1", "jaw dropped, mouth open, speaking mid-word, neutral expression", mm, 3, NS),
 ("mouth_ah_2", "jaw dropped, mouth open, speaking mid-word, neutral expression", mm, 4, NS),
 ("mouth_oh_3", "mouth open in a small round O shape, saying oh, surprised", mm, 3, NS + ", teeth"),
 ("blink_1", "eyes closed, eyelids shut, eyelashes", em, 1, NEG),
 ("blink_2", "eyes closed, eyelids shut, eyelashes", em, 2, NEG),
]
for name, v, mask, s, neg in jobs:
    if os.path.exists(f"{d}/{name}.png"): continue
    inpaint(pipe, pf + v + sf, face0, mask, strength=0.92, steps=16, cfg=6.0, seed=100 + s, neg=neg).save(f"{d}/{name}.png"); print(name, round(time.time() - t0), flush=True)
print("done", flush=True)
