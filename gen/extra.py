"""extra.py <key> : a few stronger open-mouth candidates"""
import sys, json
from sdlib import *
from facelib import *
from prompts import DESC
key = sys.argv[1]; d = f"work/{key}"; pipe = load("dpm")
meta = json.load(open(f"{d}/meta.json")); face0 = Image.open(f"{d}/face0.png").convert("RGB"); m = meta["mouth"]
mm = ellipse_mask((512, 512), m["cx"], m["cy"], m["rx"], m["ry"], blur=6)
pf = f"RAW photo, close-up portrait of {DESC[key]}, "; sf = ", detailed skin texture, sharp focus"
for name, v, s, st in [("mouth_wide_1", "mouth wide open, speaking loudly, saying ah, teeth and tongue visible", 5, 1.0),
                       ("mouth_wide_2", "mouth wide open, speaking loudly, saying ah, teeth and tongue visible", 6, 1.0),
                       ("mouth_wide_3", "jaw dropped, mouth open, speaking mid-word, upper teeth visible, neutral expression", 7, 1.0)]:
    inpaint(pipe, pf + v + sf, face0, mm, strength=st, steps=16, cfg=7.0, seed=100 + s, neg=NEG + ", smile, grin, laughing").save(f"{d}/{name}.png"); print(name, flush=True)
