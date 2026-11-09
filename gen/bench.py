import sys, time, torch
from sdlib import *
mode = sys.argv[1]; dt = torch.bfloat16 if sys.argv[2] == "bf16" else torch.float32
steps = int(sys.argv[3]); cfg = float(sys.argv[4])
t = time.time(); pipe = load(mode, dt); print("load", round(time.time() - t, 1), flush=True)
P = ("RAW photo, television news anchor, a woman in her mid 30s with long dark brown hair, wearing a red blazer, sitting at a news desk, "
     "looking at the camera, lips closed, calm friendly expression, medium close-up, modern television news studio with dark blue video walls "
     "out of focus in the background, broadcast television footage, studio lighting, natural skin texture, sharp focus, 8k")
os.makedirs("out", exist_ok=True)
for seed in (11, 12):
    t = time.time(); im = t2i(pipe, P, seed, steps=steps, cfg=cfg); print(mode, sys.argv[2], seed, round(time.time() - t, 1), flush=True)
    im.save(f"out/bench_{mode}_{sys.argv[2]}_{steps}_{seed}.jpg", quality=92)
