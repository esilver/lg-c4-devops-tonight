"""lp_motion.py <key>... : poses for head movement and gaze -> work/<key>/lp/f_yawp.png, f_yawn.png, f_pitp.png, f_pitn.png
(head turned and nodded by a few degrees either way) and f_gl.png, f_gr.png, f_gd.png (eyes left, right, down)."""
import sys, json, numpy as np
from PIL import Image
from lp import Source
YAW, PITCH = 6.0, 5.0
for key in sys.argv[1:]:
    d = f"work/{key}"; meta = json.load(open(f"{d}/meta.json"))
    src = Source(np.asarray(Image.open(f"{d}/frame.png").convert("RGB")), meta["lm"])
    poses = dict(yawp=dict(yaw=YAW), yawn=dict(yaw=-YAW), pitp=dict(pitch=PITCH), pitn=dict(pitch=-PITCH), gl=dict(px=-7), gr=dict(px=7), gd=dict(py=-7))
    for n, kw in poses.items(): Image.fromarray(src.render(comp=0, **kw)).save(f"{d}/lp/f_{n}.png")
    print(key, len(poses), "poses", flush=True)
