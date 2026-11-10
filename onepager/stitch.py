"""stitch.py : joins the slices export.js wrote into pictures that can be posted.

  devops-tonight-how-it-was-made.jpg         the whole page at twice the pixel density (2400 px wide, about 17,000 tall)
  devops-tonight-how-it-was-made-8000.jpg    the whole page scaled to 8000 px tall, for places that refuse taller pictures
  devops-tonight-how-it-was-made-part1..3.jpg  the page cut at section boundaries into three crisp pictures, for a gallery
Run from the repository root:  gen/venv6/bin/python onepager/stitch.py"""
import glob, json, os, numpy as np, cv2
d = os.path.dirname(os.path.abspath(__file__)); im = np.vstack([cv2.imread(f) for f in sorted(glob.glob(f"{d}/slices/slice_*.png"))]); S = json.load(open(f"{d}/slices/sections.json"))
out = {"devops-tonight-how-it-was-made.jpg": im, "devops-tonight-how-it-was-made-8000.jpg": cv2.resize(im, (round(im.shape[1] * 8000 / im.shape[0]), 8000), interpolation=cv2.INTER_AREA)}
tops = [t * S["scale"] - 44 for t in S["tops"]]; third = im.shape[0] / 3                      # cut just above the strap of the section nearest each third
cuts = [0] + [min(tops, key=lambda t: abs(t - k * third)) for k in (1, 2)] + [im.shape[0]]
for i in range(3): out[f"devops-tonight-how-it-was-made-part{i + 1}.jpg"] = im[cuts[i]:cuts[i + 1]]
for f in glob.glob(f"{d}/devops-tonight-how-it-was-made*.jpg"): os.remove(f)
for name, a in out.items(): cv2.imwrite(f"{d}/{name}", a, [cv2.IMWRITE_JPEG_QUALITY, 90]); print(name, a.shape[1::-1], round(os.path.getsize(f"{d}/{name}") / 1e6, 2), "MB")
