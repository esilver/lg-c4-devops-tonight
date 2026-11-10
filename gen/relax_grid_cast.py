"""relax_grid_cast.py <out dir> <key>... : does a relaxed mouth help the other faces too? Per face a grid of renders: rows
are settings of the smile and of lip rounding, columns are jaw openings. Results: out/relax_grid_<key>.jpg.
Run from gen/:  ./venv2/bin/python relax_grid_cast.py out cy dee paige sunny"""
import sys, json, time, numpy as np, cv2
sys.path.insert(0, '.')
from PIL import Image
from lp import Source
out = sys.argv[1]
rows = [("smile 0", dict()), ("smile -0.15", dict(smile=-0.15)), ("smile -0.3", dict(smile=-0.3)), ("smile -0.2 woo 3", dict(smile=-0.2, woo=3))]
cols = [0, 16, 32, 48]
for key in sys.argv[2:]:
    d = f"work/{key}"; meta = json.load(open(f"{d}/meta.json")); t = time.time()
    src = Source(np.asarray(Image.open(f"{d}/frame.png").convert("RGB")), meta["lm"]); tiles = []
    for rn, kw in rows:
        r = []
        for a in cols:
            im = np.ascontiguousarray(src.render(comp=0, aaa=a, **kw)[200:470, 96:416])
            cv2.putText(im, f"{rn} jaw {a}", (6, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0), 1, cv2.LINE_AA); r.append(im)
        tiles.append(np.hstack(r))
    Image.fromarray(np.vstack(tiles)).save(f"{out}/relax_grid_{key}.jpg", quality=88); print(key, "done", round(time.time() - t), "s", flush=True)
