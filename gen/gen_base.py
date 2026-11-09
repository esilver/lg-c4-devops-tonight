import sys, time, os
from sdlib import *
from prompts import P
keys = sys.argv[1].split(","); seeds = [int(s) for s in sys.argv[2].split(",")]
pipe = load("dpm"); os.makedirs("out", exist_ok=True)
for seed in seeds:
    for k in keys:
        f = f"out/base_{k}_{seed}.png"
        if os.path.exists(f): continue
        t = time.time(); im = t2i(pipe, P[k], seed, steps=25, cfg=5.0); im.save(f); print(k, seed, round(time.time() - t, 1), flush=True)
