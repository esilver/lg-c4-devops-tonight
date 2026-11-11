"""lpexport3.py [key...] : everything the page needs to animate a presenter (request 11), from the re-posed renders.
This is lpexport2.py reading the poses built around a relaxed mouth (lpx4.py, work/<key>/lp4/) and adding the body and
hair maps (bodymap.py). What each part is:

  mouth   a dense grid of poses: 12 jaw openings with neutral lips, 8 each with lips half / fully spread and half / fully
          rounded, 8 while smiling, lips pressed, a half smile (now the photograph's own expression, since "neutral"
          is the relaxed mouth). Stored opaque; one soft mask is shared by all of them.
  eyes    half and fully closed lids, three gaze directions, and the eyes of a smile. One shared mask.
          (The eyes that the model draws under raised brows were tried and dropped: on two faces they drooped.)
  motion  six displacement fields on a grid over the head: turned right / left, nodded down / up (true head rotation,
          so the nose travels further than the ears), brows raised / lowered. The page moves the live picture by a
          weighted sum of them, so brows and head MOVE instead of cross-fading between two pictures.
  body    three maps on an 8-pixel grid: torso, free hair, wind (see bodymap.py), and the torso's middle, shoulder line and width.
  plus the cut-out, the background plate and a base frame that agrees with the neutral render.

Run from gen/:  ./venv2/bin/python lpexport3.py            -> cast3.json (read by assets4.py)
                ./venv2/bin/python lpexport3.py me --out cast_me.json     a sixth face, in a file of its own"""
import sys, json, os, io, base64, math
import cv2, numpy as np
from PIL import Image
W, H = 1024, 576; LP = "lp4"
GAIN = dict(paige=1.05, cy=1.0, dee=1.12, sunny=1.05, mel=0.95)
GAIN.update(me=1.25)                                         # a face from a photograph; judged on the live avatar page (lipcal_photo.py, avatar/faces/check.js)
EXTRA = dict(sunny=dict(wxScale=1.08))
ROWS = ["e1", "e2", "w1", "w2", "sg"]
OUTLINE = {"me"}                                             # the jaw is seen against the backdrop: the mouth region stops short of the cut-out's outline (see export)
PLAIN = {"me"}                                               # photographed against a plain backdrop: the plate is that backdrop, continued smoothly (plain_plate)
def plain_plate(bgr, alpha, reach=12):
    """The plate for a face photographed against a plain backdrop. Carrying the surroundings inwards (what the other
    plates do) leaves a faint figure in a plain backdrop: streaks where stray hairs and the soft shadow next to the
    outline are dragged in, and a seam down the middle where the lighter side meets the darker one. Here the hole
    (the person and `reach` pixels around, which takes the stray hairs with it) is filled by the smoothest surface
    that meets the real backdrop all round it: every filled pixel is the average of its four neighbours (worked out
    from a coarse copy of the picture to the full one). The backdrop's own fine noise, from a patch of real backdrop,
    is laid over the filled part so that it is not flatter than the rest."""
    hole = cv2.dilate((alpha > 6).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * reach + 1, 2 * reach + 1))) > 0
    pyr = [(bgr.astype(np.float32), hole)]
    while min(pyr[-1][0].shape[:2]) > 24:                                                           # coarser copies: a pixel is the mean of what is known in its 2x2 block
        im, h = pyr[-1]; H2, W2 = (im.shape[0] + 1) // 2, (im.shape[1] + 1) // 2; k = (~h).astype(np.float32)
        den = cv2.resize(k, (W2, H2), interpolation=cv2.INTER_AREA); num = cv2.resize(im * k[..., None], (W2, H2), interpolation=cv2.INTER_AREA)
        pyr.append((num / np.maximum(den, 1e-6)[..., None], den < 1e-6))
    ker = np.array([[0, 0.25, 0], [0.25, 0, 0.25], [0, 0.25, 0]], np.float32); cur = None
    for im, h in reversed(pyr):
        im = im.copy(); im[h] = cv2.resize(cur, (im.shape[1], im.shape[0]), interpolation=cv2.INTER_LINEAR)[h] if cur is not None else im[~h].mean(axis=0)
        for _ in range(300): im[h] = cv2.filter2D(im, -1, ker, borderType=cv2.BORDER_REFLECT)[h]
        cur = im
    best = None                                                                                    # the flattest window of real backdrop, for its noise
    for y in range(0, bgr.shape[0] - 96, 32):
        for x in range(0, bgr.shape[1] - 96, 32):
            if hole[y:y + 96, x:x + 96].any(): continue
            q = bgr[y:y + 96, x:x + 96].astype(np.float32); v = float(np.abs(q - q.mean(axis=(0, 1))).max())
            if best is None or v < best[0]: best = (v, q - cv2.GaussianBlur(q, (0, 0), 3))
    if best is not None:
        rng = np.random.default_rng(11); noise = np.zeros_like(cur)
        for y in range(0, cur.shape[0], 96):
            for x in range(0, cur.shape[1], 96):
                q = best[1] if rng.random() < 0.5 else best[1][::-1]; q = q if rng.random() < 0.5 else q[:, ::-1]; hh, ww = min(96, cur.shape[0] - y), min(96, cur.shape[1] - x); noise[y:y + hh, x:x + ww] = q[:hh, :ww]
        cur[hole] += noise[hole]
    return np.clip(cur, 0, 255)
DETAIL = {"me"}                                              # a real photograph: its own fine detail is put back into every pose (photo_detail)
QUALITY = dict(me=(86, 96))                                  # WebP quality of the poses and of the cut-out, where detail was put back (80 and 88 otherwise)
def photo_detail(R, frame):
    """A re-posed render with the photograph's fine detail. The model that re-poses the face draws it a little soft:
    pores, stubble, single brow hairs and lashes and the rim of the iris are in the photograph and not in its renders,
    and the page is made of the renders wherever a mouth or an eye can change. Here the photograph is moved onto the
    render (dense optical flow from the render to the photograph), and what is finer than a few pixels is taken from
    the moved photograph instead of the render: detail from the camera, shape and shading from the render. Not where
    the two disagree about what is there (teeth and the inside of the mouth, a lid over the eye, an iris that has
    turned): there the render is kept as it is. Detail travels with the skin, so it does not stay behind when the jaw
    drops."""
    H, W = R.shape[:2]; bl = lambda im, s: cv2.GaussianBlur(im, (0, 0), s); gray = lambda im: cv2.cvtColor(np.clip(im, 0, 255).round().astype(np.uint8), cv2.COLOR_RGB2GRAY)
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM); dis.setFinestScale(0); f = bl(dis.calc(gray(R), gray(frame), None), 1.0)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); mx, my = xx + f[..., 0], yy + f[..., 1]
    lin = cv2.remap(frame, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE); wp = np.clip(cv2.remap(frame, mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE), lin - 12, lin + 12)
    band = lambda im: bl(im, 2.2) - bl(im, 8)                                                    # shapes a few pixels across: both pictures have them, if they show the same thing
    agree = bl(np.clip(1 - (bl(np.abs(band(wp) - band(R)).mean(axis=2), 2.5) - 2.0) / 3.0, 0, 1), 1.5)
    return np.clip(R + agree[..., None] * ((wp - bl(wp, 2.5)) - (R - bl(R, 2.5))), 0, 255)
def uri(im, fmt="WEBP", **kw):
    b = io.BytesIO(); im.save(b, fmt, **kw); return f"data:image/{fmt.lower()};base64," + base64.b64encode(b.getvalue()).decode()
def export(key, idx):
    d = f"work/{key}"; meta = json.load(open(f"{d}/meta.json")); aff = json.load(open(f"{d}/{LP}/affine.json")); A = np.array(aff["A"]); dense = json.load(open(f"{d}/{LP}/dense.json"))
    frame = np.asarray(Image.open(f"{d}/frame.png").convert("RGB")).astype(np.float32); alpha = np.asarray(Image.open(f"{d}/alpha.png").convert("L"))
    lm = meta["lm"]; iod = meta["iod"]; ex = (lm["eyeL"][0] + lm["eyeR"][0]) / 2; ey = (lm["eyeL"][1] + lm["eyeR"][1]) / 2
    sc = math.sqrt(abs(np.linalg.det(A[:, :2])))
    def toframe(name):
        im = np.asarray(Image.open(f"{d}/{LP}/{name}.png").convert("RGB")); M = A.copy()
        if sc < 0.92: im = cv2.resize(im, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA); M[:, :2] /= sc      # shrink with area averaging first, then place
        return cv2.warpAffine(im, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
    valid = cv2.warpAffine(np.full((512, 512), 255, np.uint8), A, (W, H), flags=cv2.INTER_NEAREST) > 0
    valid = cv2.erode(valid.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
    n = toframe("f_n"); JN, JS = dense["jn"], dense["js"]
    mouth = dict(n=[f"d_n{i:02d}" for i in range(1, len(JN))]); mouth.update({r: [f"d_{r}_{i}" for i in range(len(JS))] for r in ROWS}); mouth.update(p=["f_p"], sh=["d_sh"])
    eyes = dict(half="f_half", closed="f_closed", gl="f_gl", gr="f_gr", gd="f_gd", smile="d_sg_0")
    F = {k: toframe(k) for k in set(sum(mouth.values(), [])) | set(eyes.values()) | {"f_yawp", "f_yawn", "f_pitp", "f_pitn", "d_browup", "d_browdn"}}
    yy = np.arange(H, dtype=np.float32)[:, None] * np.ones((1, W), np.float32); xx = np.ones((H, 1), np.float32) * np.arange(W, dtype=np.float32)[None]
    ell = lambda cy, rx, ry: ((xx - ex) / (rx * iod)) ** 2 + ((yy - ey - cy * iod) / (ry * iod)) ** 2 < 1      # where a region may live, in face units
    def softmask(names, region, thr=5, grow=0.11, feather=0.05):
        diff = np.max([np.abs(F[k] - n).mean(axis=2) for k in names], axis=0)
        b = ((diff > thr) & valid & region).astype(np.uint8)
        b = cv2.morphologyEx(b, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        r = max(3, int(round(grow * iod))); sg = max(2.0, feather * iod)
        b = cv2.dilate(b, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1)))
        b = cv2.morphologyEx(b, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (4 * r + 1, 4 * r + 1)))
        b = cv2.erode(b, np.ones((3, 3), np.uint8), iterations=int(round(1.2 * sg)))            # keep the feather inside the dilated area
        b = cv2.dilate(b, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * int(2 * sg) + 1, 2 * int(2 * sg) + 1)))
        return np.clip(cv2.GaussianBlur(b.astype(np.float32), (0, 0), sg) * valid, 0, 1)
    Mm = softmask(sum(mouth.values(), []), (yy > ey + 0.34 * iod) & ell(1.25, 1.35, 1.2))
    if key in OUTLINE:
        # On this face the jaw and one side of the neck are seen against the backdrop, and the mouth region reaches across
        # that outline. The cut-out's edge is the photograph's, but a re-posed face is a pixel or two narrower or wider
        # there, so with the mouth shut a thin line of the render's backdrop stood inside the edge, and went as the mouth
        # opened. The region now fades out between 6 and 1.5 pixels inside the outline: the outline is always the photograph's.
        Mm = Mm * np.clip((cv2.distanceTransform((alpha > 127).astype(np.uint8), cv2.DIST_L2, 5) - 1.5) / 4.5, 0, 1)
    Me = softmask(list(eyes.values()), ell(0.05, 1.2, 0.25), grow=0.06, feather=0.035)          # lids and eyeballs only: the brows are moved, not swapped
    raw = F, n; qm, qf = QUALITY.get(key, (80, 88))
    if key in DETAIL: n = photo_detail(n, frame); F = {k: photo_detail(v, frame) for k, v in F.items()}      # after the masks, which are about where the poses differ
    if key in DETAIL:
        # The model lowers and softens the brows when it shuts the eyes, so a blink blurred the brows for a few pictures.
        # A blink does not move the brows: above a line a fifth of the eye distance over the eyes, the eye poses are the neutral picture.
        slope = (lm["eyeR"][1] - lm["eyeL"][1]) / (lm["eyeR"][0] - lm["eyeL"][0]); keep = np.clip((yy - (ey + slope * (xx - ex) - 0.2 * iod)) / (0.07 * iod), 0, 1)[..., None]
        for k in set(eyes.values()): F[k] = n + keep * (F[k] - n)
    U = np.maximum(Mm, Me)[..., None]; base = frame * (1 - U) + n * U                              # the photo now agrees with the renders
    Image.fromarray(base.round().astype(np.uint8)).save(f"{d}/frame_lp3.png")
    def region(M, groups):
        ys, xs = np.where(M > 1 / 255); x0, x1, y0, y1 = int(xs.min()), int(xs.max()) + 1, int(ys.min()), int(ys.max()) + 1
        rgb = lambda k: uri(Image.fromarray(F[k][y0:y1, x0:x1].round().astype(np.uint8)), quality=qm, method=6)
        mk = np.zeros((y1 - y0, x1 - x0, 4), np.uint8); mk[..., :3] = 255; mk[..., 3] = (M[y0:y1, x0:x1] * 255).round()
        out = dict(x=x0, y=y0, w=x1 - x0, h=y1 - y0, mask=uri(Image.fromarray(mk, "RGBA"), "PNG", optimize=True))
        out.update({g: ([rgb(k) for k in v] if isinstance(v, list) else rgb(v)) for g, v in groups.items()}); return out
    m = region(Mm, mouth); m["p"] = m["p"][0]; m["sh"] = m["sh"][0]; m["jn"] = JN; m["js"] = JS; e = region(Me, eyes)
    # ── motion fields: where each pixel of the neutral face goes in a posed render
    F, n = raw
    a01 = alpha.astype(np.float32) / 255; k = max(3, int(0.25 * iod)) | 1
    inside = cv2.erode(valid.astype(np.uint8), np.ones((k, k), np.uint8)).astype(np.float32)          # fade to nothing before the crop's edge
    person = cv2.dilate((a01 > 0.1).astype(np.uint8), np.ones((9, 9), np.uint8)).astype(np.float32)     # the background plate does not move
    whead = cv2.GaussianBlur(inside * person, (0, 0), 0.12 * iod)
    # brows: a band from just above the upper lid to the hairline, fading out sideways and upwards
    wbrow = np.clip((ey - 0.13 * iod - yy) / (0.12 * iod), 0, 1) * np.clip(1.6 - np.sqrt(((xx - ex) / (1.25 * iod)) ** 2 + ((yy - ey + 0.5 * iod) / (0.8 * iod)) ** 2) * 1.6 + 0.6, 0, 1)
    wbrow = cv2.GaussianBlur((wbrow * inside * person).astype(np.float32), (0, 0), 0.03 * iod)
    gn = cv2.cvtColor(n.round().astype(np.uint8), cv2.COLOR_RGB2GRAY); dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    def flow(name, w, sig):
        f = dis.calc(gn, cv2.cvtColor(F[name].round().astype(np.uint8), cv2.COLOR_RGB2GRAY), None); return cv2.GaussianBlur(f, (0, 0), sig * iod) * w[..., None]
    fl = {p: flow("f_" + p, whead, 0.06) for p in ("yawp", "yawn", "pitp", "pitn")}
    nose = lambda f: f[int(ey + 0.2 * iod):int(ey + 0.8 * iod), int(ex - 0.3 * iod):int(ex + 0.3 * iod)].reshape(-1, 2).mean(axis=0)
    right, left = ("yawp", "yawn") if nose(fl["yawp"])[0] > nose(fl["yawn"])[0] else ("yawn", "yawp")       # name the fields by what they do on screen
    down, up = ("pitp", "pitn") if nose(fl["pitp"])[1] > nose(fl["pitn"])[1] else ("pitn", "pitp")
    bu, bd = flow("d_browup", wbrow, 0.03), flow("d_browdn", wbrow, 0.03)
    fields = [fl[right], fl[left], fl[down], fl[up], bu, bd]
    mag = np.max([np.hypot(f[..., 0], f[..., 1]) for f in fields], axis=0); ys, xs = np.where(mag > 0.04)
    step = int(np.clip(round(iod * 0.11), 6, 14)); x0 = max(0, int(xs.min()) - step); y0 = max(0, int(ys.min()) - step)
    cols = min(W - x0, int(xs.max()) + step - x0) // step + 2; rows = min(H - y0, int(ys.max()) + step - y0) // step + 2
    gx = np.clip(x0 + np.arange(cols) * step, 0, W - 1); gy = np.clip(y0 + np.arange(rows) * step, 0, H - 1); enc = []
    for f in fields:
        g = f[gy][:, gx]; g[0] = g[-1] = 0; g[:, 0] = g[:, -1] = 0                                   # nothing moves on the border of the grid
        s = 127 / max(1e-3, np.abs(g).max()); enc.append([round(float(s), 4), base64.b64encode(np.round(g * s).astype(np.int8).tobytes()).decode()])
    browpx = [float(f[int(ey - 0.42 * iod):int(ey - 0.2 * iod), int(ex - 0.75 * iod):int(ex + 0.75 * iod), 1].mean()) for f in (bu, bd)]
    # ── cut-out with decontaminated edges, and a plate with the person painted out
    # The plate: the person painted out. Body and hair now move by a centimetre or two, which uncovers a strip of the
    # plate along the outline, so the real background is kept right up to the person (five pixels of safety). Inside, the
    # hole is closed by carrying the surroundings inwards (Telea), softened a little from 2 px in and heavily deeper,
    # where nothing is ever uncovered: the uncovered strip then looks like out-of-focus background, not like streaks.
    # (Before, the fill was blurred from eight pixels OUTSIDE the outline: a soft halo that stayed put when the figure
    # moved. Having the image model paint the room behind the person was tried too, see plate.py and docs/15.)
    mask = cv2.dilate(((alpha > 6) * 255).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)))
    bgr = cv2.cvtColor(base.round().astype(np.uint8), cv2.COLOR_RGB2BGR); a2 = np.clip((a01 - 0.25) / 0.7, 0, 1)
    grown = cv2.inpaint(bgr, ((a2 <= 0.98) * 255).astype(np.uint8), 4, cv2.INPAINT_TELEA)
    fg = Image.fromarray(cv2.cvtColor(grown, cv2.COLOR_BGR2RGB)).convert("RGBA"); fg.putalpha(Image.fromarray((a2 * 255).astype(np.uint8)))
    plate = cv2.inpaint(bgr, mask, 7, cv2.INPAINT_TELEA).astype(np.float32); depth = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
    w1 = np.clip((depth - 2) / 10, 0, 1)[..., None]; w2 = np.clip((depth - 14) / 26, 0, 1)[..., None]
    plate = plate * (1 - w1) + cv2.GaussianBlur(plate, (0, 0), 4) * w1; plate = plate * (1 - w2) + cv2.GaussianBlur(plate, (0, 0), 12) * w2
    if key in PLAIN: plate = plain_plate(cv2.cvtColor(frame.round().astype(np.uint8), cv2.COLOR_RGB2BGR), alpha)
    bg = Image.fromarray(cv2.cvtColor(plate.round().astype(np.uint8), cv2.COLOR_BGR2RGB)); bg.save(f"{d}/plate3.jpg", quality=90)      # kept to look at
    ent = dict(bg=uri(bg, "JPEG", quality=86), fg=uri(fg, quality=qf, method=6), seed=round(1.0 + idx * 1.7, 2), gain=GAIN[key],
               face=dict(cx=round(ex, 1), cy=round(ey + 0.45 * iod, 1), iod=round(iod, 1)), mouth=m, eyes=e,
               flow=dict(x=x0, y=y0, step=step, cols=int(cols), rows=int(rows), f=enc), body=json.load(open(f"{d}/body.json")))
    ent.update(EXTRA.get(key, {}))
    Image.fromarray((np.dstack([Mm, Me, np.clip(wbrow, 0, 1)]) * 255).astype(np.uint8)).save(f"{d}/{LP}/masks.png")
    kb = lambda o: sum(len(v) if isinstance(v, str) else sum(len(q) for q in v) for v in o.values() if isinstance(v, (str, list)) and v and isinstance(v if isinstance(v, str) else v[0], str)) // 1024
    print(f"{key}: mouth {m['w']}x{m['h']} {kb(m)} kB, eyes {e['w']}x{e['h']} {kb(e)} kB, motion grid {cols}x{rows} step {step} {sum(len(q[1]) for q in enc) // 1024} kB; right={right} {nose(fl[right])[0]:+.1f} px, down={down} {nose(fl[down])[1]:+.1f} px, brows up {browpx[0]:+.1f} px / down {browpx[1]:+.1f} px", flush=True)
    return ent
if __name__ == "__main__":
    # A face that is not one of the five (one made from a photograph, prep_photo.py) is named on the command line and
    # written to a file of its own, so cast3.json and the bulletin are left alone:  lpexport3.py me --out cast_me.json
    args = sys.argv[1:]; dest = args.pop(args.index("--out") + 1) if "--out" in args else "cast3.json"; args = [a for a in args if a != "--out"]
    five = ["paige", "cy", "dee", "sunny", "mel"]; keys = five + [a for a in args if a not in five]
    assert dest != "cast3.json" or keys == five, "a face outside the five needs --out <file>"
    out = json.load(open(dest)) if os.path.exists(dest) else {}
    for i, key in enumerate(keys):
        if (key in args or not args) and os.path.exists(f"work/{key}/{LP}/d_browdn.png"): out[key] = export(key, i)
    json.dump({k: out[k] for k in keys if k in out}, open(dest, "w"))
