"""lp_extra.py <key>... : extra poses added after the first set -> work/<key>/lp/f_smile.png (a closed-mouth smile for reactions)"""
import sys, json, numpy as np
from PIL import Image
from lp import Source
for key in sys.argv[1:]:
    d = f"work/{key}"; meta = json.load(open(f"{d}/meta.json"))
    src = Source(np.asarray(Image.open(f"{d}/frame.png").convert("RGB")), meta["lm"])
    Image.fromarray(src.render(comp=0, smile=0.5)).save(f"{d}/lp/f_smile.png"); print(key, "smile", flush=True)
