import json, io, base64, glob, os
from PIL import Image
def uri(im, fmt="JPEG", **kw):
    b = io.BytesIO(); im.save(b, fmt, **kw); return f"data:image/{fmt.lower()};base64," + base64.b64encode(b.getvalue()).decode()
A = json.load(open("../assets_fake.json")) if os.path.exists("../assets_fake.json") and "--final" not in __import__("sys").argv else dict(img={}, cast={})
A["cast"].update(json.load(open("cast_assets.json")))
for k in ("studio", "servers", "dcext", "office", "paged", "sat"):
    f = f"out/still_{k}.png"
    if os.path.exists(f): A["img"][k] = uri(Image.open(f).convert("RGB"), quality=84)
json.dump(A, open("../assets.json", "w")); print({k: len(v) // 1024 for k, v in A["img"].items()}, "cast", list(A["cast"]), "total MB", round(os.path.getsize("../assets.json") / 1e6, 2))
