"""lpx3.py <key>... : smiling poses (request 9). A presenter who smiles should be able to keep the smile while talking, so
besides a half smile with the mouth closed there is a whole row of smiling mouths at eight jaw openings.
Writes work/<key>/lp/d_sh.png (half smile) and d_sg_0.png … d_sg_7.png (smile, jaw opening as in the shaped rows)."""
import sys, json, os, time, numpy as np
from PIL import Image
from lp import Source
JS = [0, 5, 10, 16, 22, 30, 38, 48]; SMILE = 0.38
for key in sys.argv[1:]:
    d = f"work/{key}"; meta = json.load(open(f"{d}/meta.json")); out = f"{d}/lp"
    src = Source(np.asarray(Image.open(f"{d}/frame.png").convert("RGB")), meta["lm"]); t = time.time()
    poses = dict(sh=dict(smile=SMILE / 2)); poses.update({f"sg_{i}": dict(smile=SMILE, aaa=a) for i, a in enumerate(JS)})
    for n, kw in poses.items():
        if not os.path.exists(f"{out}/d_{n}.png"): Image.fromarray(src.render(comp=0, **kw)).save(f"{out}/d_{n}.png")
    print(key, len(poses), "poses", round(time.time() - t), "s", flush=True)
