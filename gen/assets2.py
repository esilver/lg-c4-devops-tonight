import json, io, base64, os
from PIL import Image
def uri(im, fmt="JPEG", **kw):
    b = io.BytesIO(); im.save(b, fmt, **kw); return f"data:image/{fmt.lower()};base64," + base64.b64encode(b.getvalue()).decode()
A = dict(img={}, cast=json.load(open("cast_lp.json")))
for k in ("studio", "servers", "dcext", "office", "paged", "sat"):
    A["img"][k] = uri(Image.open(f"out/still_{k}.png").convert("RGB"), quality=84)
json.dump(A, open("../assets.json", "w")); print("cast", list(A["cast"]), "total MB", round(os.path.getsize("../assets.json") / 1e6, 2))
