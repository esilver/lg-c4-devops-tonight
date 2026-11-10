"""prep_photo.py <key> [iod] [eye y] [eye x] : a real photograph as a presenter's frame. No image model touches it.

The five presenters' frames were generated at 1024x576 (prep.py). A photograph of a real person has to stay that
photograph, so here it is only scaled and placed, and the plain backdrop is carried on to the left and right:

  1. landmarks on work/<key>/source.png (YuNet, facelib.landmarks);
  2. the photograph is scaled (Lanczos) so that the eyes are `iod` pixels apart, and placed so that the point between
     the eyes is at (eye x, eye y) of the 1024x576 frame;
  3. the frame left and right of the photograph is backdrop that was never photographed. For every row the backdrop's
     colour at the photograph's edge and its sideways slope there are measured: a straight line through the backdrop
     pixels next to the edge (as many columns as are backdrop in that row, 72 at most). The colour is carried
     outwards, and the slope with it, dying away over about a hundred pixels, so the picture and its slope are both
     continuous at the edge: no seam, no kink. Two things keep rows from leaving streaks: the slope is smoothed
     heavily along the edge (it is a property of the lighting, which changes slowly), and the colour is smoothed along
     the edge more and more the further out it is carried (3 rows at the edge, 45 from 85 pixels out). The backdrop's
     own fine noise (what is left when a blurred copy is subtracted, from a patch of real backdrop) is laid over the
     new part, so it is not flatter than the real part and does not band when it is stored in 8 bits;
  4. landmarks again on the finished frame -> meta.json (iod, lm: what lp.py, bodymap.py, lpexport3.py and lipteach.py
     read; `photo` records the placement).

It refuses to run if backdrop would have to be invented above or below the photograph, or if the outermost columns
of the photograph are not backdrop in every row.

Run from gen/:  ./venv2/bin/python prep_photo.py me 98 228       -> work/me/frame.png, meta.json, frame_check.jpg"""
import sys, json, numpy as np, cv2
from PIL import Image
from facelib import landmarks
W, H = 1024, 576
REACH = 110        # pixels over which the backdrop's slope dies away outside the photograph
key = sys.argv[1]; IOD = float(sys.argv[2]) if len(sys.argv) > 2 else 98.0; EY = float(sys.argv[3]) if len(sys.argv) > 3 else 228.0; EX = float(sys.argv[4]) if len(sys.argv) > 4 else W / 2
d = f"work/{key}"; src = Image.open(f"{d}/source.png").convert("RGB"); lm0 = landmarks(src); assert lm0, "no face in the photograph"
eL, eR = np.array(lm0["eyeL"]), np.array(lm0["eyeR"]); s = IOD / float(np.linalg.norm(eR - eL)); em = (eL + eR) / 2
ws, hs = int(round(src.width * s)), int(round(src.height * s)); small = np.asarray(src.resize((ws, hs), Image.LANCZOS)).astype(np.float32)
x0, y0 = int(round(EX - em[0] * s)), int(round(EY - em[1] * s))
assert y0 <= 0 and y0 + hs >= H, f"the photograph does not cover the frame's height (rows {y0}..{y0 + hs})"
assert x0 >= 0 and x0 + ws <= W, "the photograph is wider than the frame at this size"
ph = small[-y0:-y0 + H]                                        # the rows of the photograph that are in the frame
blur_rows = lambda v, sg: cv2.GaussianBlur(np.ascontiguousarray(v, np.float32).reshape(H, 1, -1), (0, 0), sigmaX=0.01, sigmaY=sg, borderType=cv2.BORDER_REFLECT).reshape(v.shape)
def edge(strip, name):
    """strip[row, k]: the photograph from its edge column (k = 0) inwards. Per row: the backdrop's colour at the edge, the
    slope outwards, and how many columns were backdrop."""
    a = np.zeros((H, 3), np.float32); b = np.zeros((H, 3), np.float32); n = np.zeros(H, np.float32)
    for y in range(H):
        p = strip[y]; off = np.abs(p - np.median(p[:8], axis=0)).max(axis=1) > 7; run = int(off.argmax()) if off.any() else len(p)
        assert run >= 20, f"the {name} edge of the photograph is not plain backdrop at row {y} (only {run} columns)"
        k = int(np.clip(run - 8, 12, 72)); A = np.stack([np.ones(k, np.float32), -np.arange(k, dtype=np.float32)], 1)
        a[y], b[y] = np.linalg.lstsq(A, p[:k], rcond=None)[0]; n[y] = k
    w = n[:, None]; slope = blur_rows(b * w, 60) / blur_rows(w, 60)                               # rows with more backdrop count for more
    return np.stack([strip[:, :3].mean(axis=1), a]).mean(axis=0), slope, n                         # the edge colour: the outermost pixels and the line's value there, averaged
frame = np.zeros((H, W, 3), np.float32); frame[:, x0:x0 + ws] = ph; info = {}
for name, lo, hi, strip in (("left", 0, x0, ph[:, :80]), ("right", x0 + ws, W, ph[:, ::-1][:, :80])):
    if hi <= lo: continue
    c0, g, n = edge(strip, name); info[name] = (float(n.min()), float(np.abs(g).max()))
    for x in range(lo, hi):
        dist = float(x0 - x if name == "left" else x - (x0 + ws - 1))
        frame[:, x] = blur_rows(c0, 3 + 42 * min(1, dist / 85)) + g * (REACH * (1 - np.exp(-dist / REACH)))
# the backdrop's own fine noise, from a patch of the photograph that is plain backdrop (the left and right strips are
# scanned for the flattest 96-pixel window), laid over the new parts in tiles that are flipped at random
best = None
for ty in range(0, H - 96, 16):
    for tx in list(range(0, 97, 16)) + list(range(ws - 192, ws - 95, 16)):
        p = ph[ty:ty + 96, tx:tx + 96]; v = float(np.abs(p - p.mean(axis=(0, 1))).max())
        if v < 12 and (best is None or v < best[0]): best = (v, p - cv2.GaussianBlur(p, (0, 0), 3))
assert best is not None, "no plain patch of backdrop found for the noise"
r = best[1]; rng = np.random.default_rng(7); noise = np.zeros((H, W, 3), np.float32)
for ty in range(0, H, 96):
    for tx in range(0, W, 96):
        q = r if rng.random() < 0.5 else r[::-1]; q = q if rng.random() < 0.5 else q[:, ::-1]; q = q if rng.random() < 0.5 else q.transpose(1, 0, 2)
        hh, ww = min(96, H - ty), min(96, W - tx); noise[ty:ty + hh, tx:tx + ww] = q[:hh, :ww]
new = np.ones((H, W), bool); new[:, x0:x0 + ws] = False; frame[new] += noise[new]
out = Image.fromarray(np.clip(frame.round(), 0, 255).astype(np.uint8)); out.save(f"{d}/frame.png")
lm = landmarks(out); assert lm, "no face in the frame"
iod = float(np.linalg.norm(np.array(lm["eyeR"]) - np.array(lm["eyeL"])))
json.dump(dict(iod=iod, lm=lm, photo=dict(source="source.png", scale=s, x0=x0, y0=y0, w=ws, h=hs, extended=[[0, x0], [x0 + ws, W]])), open(f"{d}/meta.json", "w"), indent=1)
# to look at: the frame, and the frame with its contrast stretched six times about the backdrop's level (a seam, a
# streak or banding would show), with red ticks at the top and bottom where the photograph ends
f8 = np.asarray(out).astype(np.float32); chk = np.clip(128 + 6 * (f8 - np.median(ph[:, :60].reshape(-1, 3), axis=0)), 0, 255).astype(np.uint8)
for x in (x0, x0 + ws): chk[:6, max(0, x - 1):x + 1] = (255, 0, 0); chk[-6:, max(0, x - 1):x + 1] = (255, 0, 0)
Image.fromarray(np.vstack([np.asarray(out), chk])).save(f"{d}/frame_check.jpg", quality=92)
print(f"{key}: scale {s:.4f}, photograph at x {x0}..{x0 + ws}, rows {-y0}..{-y0 + H} of {hs}; eye distance {iod:.1f} px, eyes at ({(lm['eyeL'][0] + lm['eyeR'][0]) / 2:.1f}, {(lm['eyeL'][1] + lm['eyeR'][1]) / 2:.1f}); "
      + "; ".join(f"{k} edge: at least {v[0]:.0f} backdrop columns, steepest slope {v[1]:.3f} a pixel" for k, v in info.items()) + f"; noise patch spread {best[0]:.1f}, noise sd {r.std():.2f}")
