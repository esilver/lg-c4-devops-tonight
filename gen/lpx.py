"""lpx.py <key>... : render the pose set for each presenter -> work/<key>/lp/f_*.png (512 crops) + affine.json"""
import sys, json, os, time, numpy as np
from PIL import Image
from lp import Source
LV = [0, .14, .3, .5, .72, 1]; AMAX = 68; EEE = 7; WOO = 12
for key in sys.argv[1:]:
    d = f"work/{key}"; meta = json.load(open(f"{d}/meta.json")); out = f"{d}/lp"; os.makedirs(out, exist_ok=True)
    src = Source(np.asarray(Image.open(f"{d}/frame.png").convert("RGB")), meta["lm"])
    poses = {"n": {}}
    for i, l in enumerate(LV[1:], 1): poses[f"n{i}"] = dict(aaa=AMAX * l)
    for i, l in enumerate(LV[:5]): poses[f"e{i}"] = dict(aaa=AMAX * l, eee=EEE); poses[f"w{i}"] = dict(aaa=AMAX * l, woo=WOO)
    poses["p"] = dict(aaa=-8); poses["half"] = dict(blink=-9); poses["closed"] = dict(blink=-17); poses["brow"] = dict(brow=9)
    t = time.time()
    for n, kw in poses.items(): Image.fromarray(src.render(comp=0, **kw)).save(f"{out}/f_{n}.png")
    json.dump(dict(A=src.A.tolist(), levels=LV), open(f"{out}/affine.json", "w")); print(key, len(poses), "poses", round(time.time() - t), "s", flush=True)
