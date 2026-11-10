"""relax_grid_photo.py <key> <out.jpg> [full] : choosing REST and JAWK (lpx4.py) for a face that came from a photograph
(prep_photo.py). The same look as relax_grid_mel.py / relax_grid_cast.py, with more settings: rows are how far the
smile is taken out and the lips let forward ("woo"), columns are jaw openings, in the re-posing model's own units, up
to 90 (the widest pose is 60 units times JAWK). The lower face of each 512 render, labelled.
With `full` the whole 512 renders are tiled instead (to see what the model does to the rest of the face).
Also prints the head angles the model reads from the photograph.
Run from gen/:  ./venv2/bin/python relax_grid_photo.py me ../avatar/faces/check/me_relax_grid.jpg     (42 renders, about five minutes)"""
import sys, json, time, numpy as np, cv2
sys.path.insert(0, '.')
from PIL import Image
from lp import Source
key, out = sys.argv[1], sys.argv[2]; full = len(sys.argv) > 3 and sys.argv[3] == "full"
d = f"work/{key}"; meta = json.load(open(f"{d}/meta.json"))
src = Source(np.asarray(Image.open(f"{d}/frame.png").convert("RGB")), meta["lm"])
print("head angles read by the model: pitch", round(src.pitch, 1), "yaw", round(src.yaw, 1), "roll", round(src.roll, 1), "scale", round(float(src.scale[0, 0]), 3), flush=True)
rows = [("photo", dict()), ("sm -.10 woo 2", dict(smile=-0.10, woo=2)), ("sm -.15 woo 3", dict(smile=-0.15, woo=3)), ("sm -.20 woo 3", dict(smile=-0.20, woo=3)),
        ("sm -.25 woo 4", dict(smile=-0.25, woo=4)), ("sm -.30 woo 4", dict(smile=-0.30, woo=4)), ("sm -.20 woo 0", dict(smile=-0.20))]
cols = [0, 12, 26, 45, 60, 90]
t = time.time(); tiles = []
for rn, kw in rows:
    r = []
    for a in cols:
        im = src.render(comp=0, aaa=a, **kw); im = np.ascontiguousarray(im if full else im[215:455, 126:386])          # the lower face of the 512 crop
        cv2.putText(im, f"{rn} jaw {a}", (5, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 0), 1, cv2.LINE_AA); r.append(im)
    tiles.append(np.hstack(r)); print(rn, round(time.time() - t), "s", flush=True)
Image.fromarray(np.vstack(tiles)).save(out, quality=92); print("done", round(time.time() - t), "s")
