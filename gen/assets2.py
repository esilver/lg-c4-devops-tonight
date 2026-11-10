import json, io, base64, os
from PIL import Image
def uri(im, fmt="JPEG", **kw):
    b = io.BytesIO(); im.save(b, fmt, **kw); return f"data:image/{fmt.lower()};base64," + base64.b64encode(b.getvalue()).decode()
A = dict(img={}, cast=json.load(open("cast_lp.json")))
# three stills were regenerated in the second round (see docs/12): the establishing shot now matches the reporter's backdrop,
# the paged engineer holds a phone, and the office is at dusk
SRC = dict(studio="studio", servers="servers", dcext="dcext2", office="office2", paged="paged2", sat="sat")
for k, f in SRC.items():
    f = f if os.path.exists(f"out/still_{f}.png") else k
    A["img"][k] = uri(Image.open(f"out/still_{f}.png").convert("RGB"), quality=84)
json.dump(A, open("../assets.json", "w")); print("cast", list(A["cast"]), "total MB", round(os.path.getsize("../assets.json") / 1e6, 2))
