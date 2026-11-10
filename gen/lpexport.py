"""lpexport.py [key...] : re-posed face crops -> frame-space sprites that share one soft mask per region, a base frame that
   matches them, the cut-out / background plate, and the cast entry for the page."""
import sys, json, os, io, base64, math
import cv2, numpy as np
from PIL import Image
W, H = 1024, 576
GAIN = dict(paige=1.05, cy=1.0, dee=1.12, sunny=1.05, mel=0.95)
EXTRA = dict(sunny=dict(wxScale=1.08))
def uri(im, fmt="JPEG", **kw):
    b = io.BytesIO(); im.save(b, fmt, **kw); return f"data:image/{fmt.lower()};base64," + base64.b64encode(b.getvalue()).decode()
def export(key, idx):
    d = f"work/{key}"; meta = json.load(open(f"{d}/meta.json")); aff = json.load(open(f"{d}/lp/affine.json")); A = np.array(aff["A"])
    frame = np.asarray(Image.open(f"{d}/frame.png").convert("RGB")).astype(np.float32); alpha = Image.open(f"{d}/alpha.png").convert("L")
    lm = meta["lm"]; iod = meta["iod"]; ex = (lm["eyeL"][0] + lm["eyeR"][0]) / 2; ey = (lm["eyeL"][1] + lm["eyeR"][1]) / 2
    sc = math.sqrt(abs(np.linalg.det(A[:, :2])))
    def toframe(name):
        im = np.asarray(Image.open(f"{d}/lp/f_{name}.png").convert("RGB")); M = A.copy()
        if sc < 0.92:                                   # shrink with area averaging first, then place
            im = cv2.resize(im, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA); M[:, :2] /= sc
        return cv2.warpAffine(im, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
    valid = cv2.warpAffine(np.full((512, 512), 255, np.uint8), A, (W, H), flags=cv2.INTER_NEAREST) > 0
    valid = cv2.erode(valid.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
    n = toframe("n"); L = aff["levels"]
    mouth = [f"n{i}" for i in range(1, 6)] + [f"e{i}" for i in range(5)] + [f"w{i}" for i in range(5)] + ["p", "smile"]; eyes = ["half", "closed", "brow"]
    F = {k: toframe(k) for k in mouth + eyes}; yy = np.arange(H)[:, None] * np.ones((1, W)); xx = np.ones((H, 1)) * np.arange(W)[None]
    ell = lambda cy, rx, ry: ((xx - ex) / (rx * iod)) ** 2 + ((yy - ey - cy * iod) / (ry * iod)) ** 2 < 1      # where a region may live, in face units
    def softmask(names, region):
        diff = np.max([np.abs(F[k] - n).mean(axis=2) for k in names], axis=0)
        b = ((diff > 5) & valid & region).astype(np.uint8)
        b = cv2.morphologyEx(b, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        r = max(3, int(round(0.11 * iod))); sg = max(2.0, 0.05 * iod)
        b = cv2.dilate(b, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1)))
        b = cv2.morphologyEx(b, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (4 * r + 1, 4 * r + 1)))
        b = cv2.erode(b, np.ones((3, 3), np.uint8), iterations=int(round(1.2 * sg)))            # keep the feather inside the dilated area
        b = cv2.dilate(b, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * int(2 * sg) + 1, 2 * int(2 * sg) + 1)))
        m = cv2.GaussianBlur(b.astype(np.float32), (0, 0), sg) * valid
        return np.clip(m, 0, 1)
    Mm = softmask(mouth, (yy > ey + 0.32 * iod) & ell(1.25, 1.3, 1.2)); Me = softmask(eyes, (yy < ey + 0.42 * iod) & ell(-0.14, 1.4, 0.78))
    U = np.maximum(Mm, Me)[..., None]; base = frame * (1 - U) + n * U                              # the photo now agrees with the sprites
    Image.fromarray(base.round().astype(np.uint8)).save(f"{d}/frame_lp.png")
    def sprites(names, M):
        ys, xs = np.where(M > 1 / 255); x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1; out = []
        for k in names:
            rgba = np.dstack([F[k][y0:y1, x0:x1], M[y0:y1, x0:x1, None] * 255]).round().astype(np.uint8)
            out.append(uri(Image.fromarray(rgba, "RGBA"), "WEBP", quality=82, method=6))
        return out, int(x0), int(y0), (int(x1 - x0), int(y1 - y0))
    ms, mx, my, msz = sprites(mouth, Mm); es, exx, eyy, esz = sprites(eyes, Me)
    # cut-out with decontaminated edges, and a plate with the person painted out
    a = np.asarray(alpha); mask = cv2.dilate(((a > 6) * 255).astype(np.uint8), np.ones((9, 9), np.uint8), iterations=2)
    bgr = cv2.cvtColor(base.round().astype(np.uint8), cv2.COLOR_RGB2BGR)
    a2 = np.clip((a.astype(np.float32) / 255 - 0.25) / 0.7, 0, 1)
    grown = cv2.inpaint(bgr, ((a2 <= 0.98) * 255).astype(np.uint8), 4, cv2.INPAINT_TELEA)
    fg = Image.fromarray(cv2.cvtColor(grown, cv2.COLOR_BGR2RGB)).convert("RGBA"); fg.putalpha(Image.fromarray((a2 * 255).astype(np.uint8)))
    plate = cv2.inpaint(bgr, mask, 7, cv2.INPAINT_TELEA); soft = cv2.GaussianBlur(plate, (0, 0), 9)
    w = cv2.GaussianBlur(mask, (0, 0), 4).astype(np.float32)[..., None] / 255
    bg = Image.fromarray(cv2.cvtColor((plate * (1 - w) + soft * w).astype(np.uint8), cv2.COLOR_BGR2RGB))
    ent = dict(bg=uri(bg, quality=86), fg=uri(fg, "WEBP", quality=88, method=6), seed=round(1.0 + idx * 1.7, 2), gain=GAIN[key],
               face=dict(cx=round(ex, 1), cy=round(ey + 0.45 * iod, 1), iod=round(iod, 1)),
               mouth=dict(x=mx, y=my, L=L, n=ms[0:5], e=ms[5:10], w=ms[10:15], p=ms[15], s=ms[16]), eyes=dict(x=exx, y=eyy, half=es[0], closed=es[1], brow=es[2]))
    ent.update(EXTRA.get(key, {}))
    Image.fromarray((np.dstack([Mm, Me, np.zeros_like(Mm)]) * 255).astype(np.uint8)).save(f"{d}/lp/masks.png")
    print(key, "mouth", msz, "eyes", esz, "kB", sum(len(s) for s in ms + es) // 1024, flush=True)
    return ent
if __name__ == "__main__":
    keys = ["paige", "cy", "dee", "sunny", "mel"]; out = json.load(open("cast_lp.json")) if os.path.exists("cast_lp.json") else {}
    for i, key in enumerate(keys):
        if (key in sys.argv[1:] or len(sys.argv) == 1) and os.path.exists(f"work/{key}/lp/f_brow.png"): out[key] = export(key, i)
    json.dump(out, open("cast_lp.json", "w"))
