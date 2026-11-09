"""export.py <key> ... : work/<key>/{frame.png, alpha.png, meta.json, candidates} + picks.json -> work/<key>/export/* and assets entry"""
import sys, json, os, math, io, base64
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFilter
picks = json.load(open("picks.json"))
def uri(im, fmt="JPEG", **kw):
    b = io.BytesIO(); im.save(b, fmt, **kw); return f"data:image/{fmt.lower()};base64," + base64.b64encode(b.getvalue()).decode()
def export(key, idx):
    d = f"work/{key}"; meta = json.load(open(f"{d}/meta.json")); pk = picks[key]
    frame = Image.open(f"{d}/frame.png").convert("RGB"); alpha = Image.open(f"{d}/alpha.png").convert("L")
    x0, y0, side, f = meta["x0"], meta["y0"], meta["side"], meta["f"]
    # foreground cut-out and a background plate with the person painted out (only its rim is ever seen)
    a = np.asarray(alpha); mask = cv2.dilate(((a > 6) * 255).astype(np.uint8), np.ones((9, 9), np.uint8), iterations=2)
    bgr = cv2.cvtColor(np.asarray(frame), cv2.COLOR_RGB2BGR)
    # tighten the matte a little and replace edge colours with colours grown out from the solid interior,
    # so no fringe of the old background shows when the person is placed over something else
    a2 = np.clip((a.astype(np.float32) / 255 - 0.25) / 0.7, 0, 1)
    grown = cv2.inpaint(bgr, ((a2 <= 0.98) * 255).astype(np.uint8), 4, cv2.INPAINT_TELEA)
    fg = Image.fromarray(cv2.cvtColor(grown, cv2.COLOR_BGR2RGB)).convert("RGBA"); fg.putalpha(Image.fromarray((a2 * 255).astype(np.uint8)))
    plate = cv2.inpaint(bgr, mask, 7, cv2.INPAINT_TELEA); soft = cv2.GaussianBlur(plate, (0, 0), 9)
    w = cv2.GaussianBlur(mask, (0, 0), 4).astype(np.float32)[..., None] / 255
    plate = (plate * (1 - w) + soft * w).astype(np.uint8); bg = Image.fromarray(cv2.cvtColor(plate, cv2.COLOR_BGR2RGB))
    def sprite(name, ells, blur):
        cand = Image.open(f"{d}/{name}.png").convert("RGB")
        m = Image.new("L", (512, 512), 0); dr = ImageDraw.Draw(m)
        for e in ells: dr.ellipse([e["cx"] - e["rx"], e["cy"] - e["ry"], e["cx"] + e["rx"], e["cy"] + e["ry"]], fill=255)
        m = m.filter(ImageFilter.GaussianBlur(blur)); pad = 3 * blur
        bx0 = max(0, math.floor((min(e["cx"] - e["rx"] for e in ells) - pad) / f)); by0 = max(0, math.floor((min(e["cy"] - e["ry"] for e in ells) - pad) / f))
        bx1 = min(side, math.ceil((max(e["cx"] + e["rx"] for e in ells) + pad) / f)); by1 = min(side, math.ceil((max(e["cy"] + e["ry"] for e in ells) + pad) / f))
        small = cand.resize((side, side), Image.LANCZOS).crop((bx0, by0, bx1, by1)).convert("RGBA")
        small.putalpha(m.resize((side, side), Image.BILINEAR).crop((bx0, by0, bx1, by1)))
        return small, x0 + bx0, y0 + by0
    names = []; vmap = [-1, -1, -1, -1, -1, -1]; frames = []; mx = my = 0
    for v in ("1", "2", "3", "4", "5"):
        n = pk["mouth"].get(v)
        if n is None: continue
        if n not in names:
            names.append(n); spr, mx, my = sprite(n, [meta["mouth"]], 7); frames.append(uri(spr, "WEBP", quality=92, method=6))
        vmap[int(v)] = names.index(n)
    for v in (1, 2, 3, 4):                      # fall back to a neighbouring shape (5, lips pressed, falls back to the rest pose)
        if vmap[v] < 0: vmap[v] = next((vmap[o] for o in (1, 3, 2, 4) if vmap[o] >= 0), -1)
    bl, bx, by = sprite(pk["blink"], meta["eyes"], 5)
    lm = meta["lm"]; ex = (lm["eyeL"][0] + lm["eyeR"][0]) / 2; ey = (lm["eyeL"][1] + lm["eyeR"][1]) / 2
    ent = dict(bg=uri(bg, quality=86), fg=uri(fg, "WEBP", quality=88, method=6), seed=round(1.0 + idx * 1.7, 2),
               face=dict(cx=round(ex, 1), cy=round(ey + 0.45 * meta["iod"], 1), iod=round(meta["iod"], 1)),
               mouth=dict(x=mx, y=my, map=vmap, frames=frames), blink=dict(x=bx, y=by, src=uri(bl, "WEBP", quality=92, method=6)))
    if "wxScale" in pk: ent["wxScale"] = pk["wxScale"]
    os.makedirs(f"{d}/export", exist_ok=True); bg.save(f"{d}/export/bg.jpg", quality=90); fg.save(f"{d}/export/fg.png")
    return ent
if __name__ == "__main__":
    out = {}
    for i, key in enumerate(["paige", "cy", "dee", "sunny", "mel"]):
        if key in sys.argv[1:] or len(sys.argv) == 1:
            if os.path.exists(f"work/{key}/alpha.png") and key in picks: out[key] = export(key, i); print("exported", key, {k: len(v) // 1024 for k, v in out[key].items() if isinstance(v, str)})
    json.dump(out, open("cast_assets.json", "w"))
