"""relax_grid_mel.py <key> <out.jpg> : what loosens the lips? A grid of renders of one face: rows are settings of the
smile and of lip rounding ("woo"), columns are jaw openings up to twice the old maximum. The first look for request 11
("his lips are too tight"); the result for the guest is out/relax_grid_mel.jpg.
Run from gen/:  ./venv2/bin/python relax_grid_mel.py mel out/relax_grid_mel.jpg"""
import sys, json, time, numpy as np, cv2
sys.path.insert(0, '.')
from PIL import Image
from lp import Source
key = sys.argv[1]; out = sys.argv[2]
d = f"work/{key}"; meta = json.load(open(f"{d}/meta.json"))
src = Source(np.asarray(Image.open(f"{d}/frame.png").convert("RGB")), meta["lm"])
rows = [("smile 0", dict()), ("smile -0.25", dict(smile=-0.25)), ("smile -0.5", dict(smile=-0.5)), ("smile -0.25 woo 4", dict(smile=-0.25, woo=4))]
cols = [0, 30, 60, 90, 120]
t = time.time(); tiles = []
for rn, kw in rows:
    r = []
    for a in cols:
        im = src.render(comp=0, aaa=a, **kw)[230:470, 96:416]          # the lower face of the 512 crop
        im = np.ascontiguousarray(im); cv2.putText(im, f"{rn} jaw {a}", (6, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0), 1, cv2.LINE_AA); r.append(im)
    tiles.append(np.hstack(r))
Image.fromarray(np.vstack(tiles)).save(out, quality=90); print("done", round(time.time() - t), "s")
