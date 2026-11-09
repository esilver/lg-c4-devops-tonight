"""stills.py key=seed ... : hires pass (1024x576) for chosen B-roll stills -> out/still_<key>.png"""
import sys
from sdlib import *
from prompts import P
pipe = load("dpm")
for a in sys.argv[1:]:
    k, s = a.split("="); im = Image.open(f"out/base_{k}_{s}.png").convert("RGB").resize((1024, 576), Image.LANCZOS)
    img2img(pipe, P[k], im, strength=0.3, steps=20, cfg=5.0, seed=1).save(f"out/still_{k}.png"); print("still", k, flush=True)
