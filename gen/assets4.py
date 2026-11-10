"""assets4.py : the picture bundle for the page (request 11): the six stills and, per presenter, the pose set built around
a relaxed mouth, the motion fields and the body and hair maps written by lpexport3.py.
Run from gen/ after lpexport3.py:   ./venv/bin/python assets4.py"""
import json, io, base64, os
from PIL import Image
def uri(im, fmt="JPEG", **kw):
    b = io.BytesIO(); im.save(b, fmt, **kw); return f"data:image/{fmt.lower()};base64," + base64.b64encode(b.getvalue()).decode()
A = dict(img={}, cast=json.load(open("cast3.json")))
SRC = dict(studio="studio", servers="servers", dcext="dcext2", office="office2", paged="paged2", sat="sat")       # three were regenerated in the second round (docs/12)
for k, f in SRC.items(): A["img"][k] = uri(Image.open(f"out/still_{f}.png").convert("RGB"), quality=84)
json.dump(A, open("../assets.json", "w")); print("cast", list(A["cast"]), "total MB", round(os.path.getsize("../assets.json") / 1e6, 2))
