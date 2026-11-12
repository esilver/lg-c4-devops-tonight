"""dog_export.py [key] : a face that is not a person's, straight from pose pictures -> cast_<key>.json (read by avatar/faces/pack.py)

The other faces are made by finding a person's landmarks, re-posing the face with a model trained on people and
labelling hair and clothes with a face parser (prep_photo.py, lpx4.py, bodymap.py, lpexport3.py). None of that knows a
dog. Here the poses arrive ready-made: pictures of the same animal, the same size, on a plain white backdrop, each
differing from the resting one only around the mouth or around the eyes. This script lays them out as the same cast
entry the page's engine reads (src/news.js), so nothing in the engine has to know what kind of face it is:

  frame   the animal scaled into the 1024 x 576 frame: the eyes on the middle line, the ear tips a little below the top
          edge, the chest running off the bottom edge as a presenter's does.
  cut-out the matte is how far each pixel is from white, measured against the colour of the fur next to it, and the
          colours are un-mixed from white (as lpexport3.py does for see-through hair): laid over the plain plate the
          cut-out gives back the picture exactly, and a fur edge stays fur-coloured when it moves.
  mouth   speech moves the jaw only (an animal has no lip shapes): one run of pictures from shut to wide open, each
          with how far open it is. The engine cross-fades between neighbouring steps, and a cross-fade between two
          poses that are far apart is two mouths seen through each other. So in-between steps are made here: the
          opening (dark lips, tongue, teeth) is found in both neighbours, its upper and lower edge are matched from
          corner to corner, and the nearer picture is warped to the in-between outline (`between`).
          Every row the engine has for lip shapes and smiles gets this same run; p, b and m get the shut mouth.
  eyes    half and fully shut lids, and the gaze poses there are (left, right, down); the rest are the open eyes.
          (The engine's gaze goes sideways and down only, so a pose looking up has no slot to go in.)
  motion  nothing was measured, so the six fields are drawn: a turn and a nod move the muzzle (it is nearest the
          camera), the whole head only a little and the ears least, fading out down the ruff; "brows up" lifts the ears a little,
          since that is where an animal shows attention. All of it smooth, on the grid the page's mesh uses.
  body    no torso and no free hair: fur that breathes and turns like a shirt slides about under the chin (see export).

The pictures, and everything made from them, stay out of the repository (gen/work/<key>/ and the cast file are ignored).
Run from gen/:  ./venv2/bin/python dog_export.py            -> cast_dog.json, and sheets to look at in work/dog/
then, from the repository root:  python3 avatar/faces/pack.py dog 1.1 0.4 4 0.5 0 && python3 avatar/build.py dog"""
import sys, json, os, base64, math
import cv2, numpy as np
from PIL import Image
from scipy.interpolate import RBFInterpolator
from lpexport3 import uri
W, H, JAW = 1024, 576, 46                                   # the frame; jaw units at an opening of 1 (src/news.js)
# What the poses of a face are called (files in work/<key>/poses/, without .png). mouth: from nearly shut to wide open,
# each with the opening of the engine's jaw at which it is shown; more poses can be added anywhere along it. On that
# scale a quick vowel between two consonants is about 0.2, a clear one 0.5, a stressed "ah" 1, and nothing is over 1.3.
# The values are not the poses' measured openings (the four here measure about 0, 0.4, 0.65 and 1 of the widest): the
# engine's rules are a person's, and between an m and a b half a syllable apart they open the jaw by a fifth, which on
# a person parts the lips and shows teeth and on a muzzle would be a thin dark line. So the small openings sit low on
# the scale. Two poses of nearly one opening do not both belong in the run: mouth_3 and mouth_4 are 5 pixels apart in
# height, but one has the tongue forward over the lower teeth and no pale tuft on the chin, the other the tongue back
# and the tuft, so with both the tongue jumped and the chin changed colour each time the jaw passed between them.
# mouth_4 is the one kept: the poses on either side of it have the tuft too.
# shut: the mouth for p, b, m.
# eyes: the engine's slots (gl / gr look to the viewer's left / right, gd down); a slot left out shows the open eyes.
# A gaze pose that looks further than is wanted is given as [name, how much of it to keep] (see `partway`).
# travel: how far (pixels in the frame) the outline of the mouth may move between two stored steps; in-betweens are
# made until no step is longer. The page cross-fades between steps, and what moves further than this shows double.
# reach: how far round the opening itself (pixels of the pose pictures) a mouth pose is taken from; see `kept`.
# turn, nod: how far a full turn / nod carries the whole head, the muzzle on top of that, and the ears less, in eye
# distances (see "motion" above).
# A file work/<key>/poses.json with the same fields replaces this entry, so a new set of poses needs no edit here.
SETS = dict(dog=dict(rest="resting", mouth=[["mouth_1", 0.06], ["mouth_2", 0.22], ["mouth_4", 0.5], ["mouth_5", 0.95]], shut="mouth_6",
                     eyes=dict(half="eyes_half", closed="eyes_closed", gl="eyes_right", gr=["eyes_left", 0.55], gd="eyes_down"),
                     travel=7, reach=24, turn=(0.05, 0.14, 0.02), nod=(0.04, 0.10, 0.02), headroom=32, gain=1.0, seed=9.5))
ell = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
step = lambda a, b, x: (lambda t: t * t * (3 - 2 * t))(np.clip((x - a) / (b - a), 0, 1))
def largest(m): n, lab, st, cen = cv2.connectedComponentsWithStats(m.astype(np.uint8)); k = 1 + int(np.argmax(st[1:, 4])); return (lab == k).astype(np.uint8), cen[k]
def filled(m): ff = m.astype(np.uint8).copy(); cv2.floodFill(ff, np.zeros((m.shape[0] + 2, m.shape[1] + 2), np.uint8), (0, 0), 2); return (ff != 2).astype(np.uint8)
def carried(col, known, sigmas, default):
    """Colours carried outwards from where they are known: every other pixel takes the average of the known ones near it (nearest first)."""
    out = col.copy(); done = known.copy(); k = known.astype(np.float32); out[~known] = default
    for sg in sigmas:
        den = cv2.GaussianBlur(k, (0, 0), sg); ok = (den > 0.05) & ~done; out[ok] = (cv2.GaussianBlur(col * k[..., None], (0, 0), sg) / np.maximum(den, 1e-6)[..., None])[ok]; done |= ok
    return out, done
def matte(R):
    """How much of each pixel is the animal, from a picture on pure white. Well inside the outline it is all animal
    (white fur and teeth too). In the band along the outline a pixel is fur mixed with white, and how much fur is read
    off against the colour of the fur just inside: a pale wisp is thin orange fur, not thick white fur. (Taking the
    outline band as solid left a white rim on every edge as soon as the cut-out was laid over anything but white.)"""
    far = 255 - R.min(axis=2); sil = filled(largest(far > 20)[0]); core = cv2.erode(sil, ell(max(3, round(R.shape[0] / 128))), borderValue=1) > 0
    fur, known = carried(R, core, (3, 6, 12, 24, 48), 255); d1, d2 = 255 - R, 255 - fur
    a = np.clip((d1 * d2).sum(axis=2) / np.maximum((d2 * d2).sum(axis=2), 1), 0, 1); a[core] = 1
    a[(far <= 3) | ~known | (cv2.dilate(sil, ell(30)) == 0)] = 0                                  # the backdrop's own faint unevenness is not fur
    return a.astype(np.float32)
def opening(P, nose, box, dark=95):
    """Where the mouth is open in a pose: lips and cavity (dark), tongue (pink: red with as much blue as green, which
    fur never has), and whatever they enclose (teeth). The nose is as dark as the lips and sits just above: left out."""
    r, g, b = P[..., 0], P[..., 1], P[..., 2]; m = ((P.max(axis=2) < dark) | ((r - g > 40) & (b > g - 12))).astype(np.uint8)
    keep = np.zeros_like(m); keep[box[2]:box[3], box[0]:box[1]] = 1; m[cv2.dilate(nose, ell(5)) > 0] = 0; m &= keep
    return filled(largest(cv2.morphologyEx(cv2.morphologyEx(m, cv2.MORPH_OPEN, ell(1)), cv2.MORPH_CLOSE, ell(4)))[0])
def edges(m, xc, K=25):
    """K points along the upper edge of the opening and K along the lower, from one corner to the other, the middle
    one on the face's centre line; smoothed, so that a tooth standing out of the outline does not put a kink in the warp."""
    cols = np.where(m.any(axis=0))[0]; xl, xr = cols.min(), cols.max(); xs = np.arange(xl, xr + 1); assert xl < xc < xr, "what was found is not the mouth: it does not cross the middle of the face"
    sm = lambda v: cv2.GaussianBlur(cv2.medianBlur(v.astype(np.float32).reshape(1, -1), 5), (0, 0), 3, borderType=cv2.BORDER_REPLICATE).ravel()
    yu, yl = sm(np.argmax(m[:, xl:xr + 1], axis=0)), sm(m.shape[0] - 1 - np.argmax(m[::-1, xl:xr + 1], axis=0))
    mid = (yu + yl) / 2; e = np.clip(np.minimum(xs - xl, xr - xs) / 6.0, 0, 1); yu, yl = mid + (yu - mid) * e, mid + (yl - mid) * e      # the two edges meet at the corners
    u = np.linspace(0, 1, K); x = np.where(u < 0.5, xl + (xc - xl) * u * 2, xc + (xr - xc) * (u * 2 - 1))
    return np.stack([x, np.interp(x, xs, yu)], 1), np.stack([x, np.interp(x, xs, yl)], 1)
def between(A, B, R, nose, xc, travel):
    """Pictures part of the way from pose A to pose B: as many as it takes for the outline of the mouth to move no
    further than `travel` pixels from one to the next. Returns [fraction of the way, picture] for each.
    Optical flow between the two was tried first and did no better than a cross-fade: it cannot follow a jaw that
    drops by a fifth of the muzzle while a tongue appears. What does work is to say where the mouth is. The outline of the opening in A and in B is matched point for point;
    for a step in between, the outline is that far along; A and B are each warped so that their outline lands on it (a
    thin-plate spline through the outline's points, held still on the nose and round the box the poses differ in).
    The step is the warped picture of whichever pose is nearer. (Mixing the two warped pictures was tried: lips, corners
    and chin do land in one place, but fur and teeth do not line up hair for hair, so every made step came out softer
    than the poses around it, and the mouth went soft and sharp again as it moved.) Between a step made from A and the
    next one made from B the page cross-fades as it does everywhere, now between two pictures with one outline."""
    ys, xs = np.where(np.abs(np.stack([A, B]) - R).max(axis=(0, 3)) > 0); X0, X1, Y0, Y1 = max(0, xs.min() - 2), min(R.shape[1], xs.max() + 3), max(0, ys.min() - 2), min(R.shape[0], ys.max() + 3)
    (UA, LA), (UB, LB) = edges(opening(A, nose, (X0, X1, Y0, Y1)), xc), edges(opening(B, nose, (X0, X1, Y0, Y1)), xc)
    still = [(x, y) for x in np.linspace(X0, X1, 14) for y in (Y0, Y1)] + [(x, y) for y in np.linspace(Y0, Y1, 10)[1:-1] for x in (X0, X1)]
    ny, nx = np.where(cv2.morphologyEx(nose, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0); still = np.array(still + [(nx[i], ny[i]) for i in np.linspace(0, len(nx) - 1, 16).astype(int)], np.float32)
    gy, gx = np.mgrid[Y0:Y1:4, X0:X1:4].astype(np.float32); yy, xx = np.mgrid[Y0:Y1, X0:X1].astype(np.float32)
    win = step(0, 10, np.minimum(np.minimum(xx - X0, X1 - 1 - xx), np.minimum(yy - Y0, Y1 - 1 - yy))).astype(np.float32)[..., None]      # nothing moves on the border of the box
    def warped(P, src, dst):
        pts, val = np.concatenate([dst, still]), np.concatenate([src - dst, np.zeros_like(still)]); _, i = np.unique(np.round(pts).astype(int), axis=0, return_index=True)
        f = RBFInterpolator(pts[i], val[i], kernel="thin_plate_spline", smoothing=0.5)(np.stack([gx.ravel(), gy.ravel()], 1)).reshape(gy.shape + (2,)).astype(np.float32)
        f = cv2.resize(f, (X1 - X0, Y1 - Y0), interpolation=cv2.INTER_CUBIC) * win
        return cv2.remap(P, xx + f[..., 0], yy + f[..., 1], cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    far = max(np.hypot(*(UB - UA).T).max(), np.hypot(*(LB - LA).T).max()); k = max(0, math.ceil(far / travel) - 1); out = []
    for t in [(q + 1) / (k + 1) for q in range(k)]:
        dst = np.concatenate([(1 - t) * UA + t * UB, (1 - t) * LA + t * LB]); im = R.copy()
        im[Y0:Y1, X0:X1] = warped(A, np.concatenate([UA, LA]), dst) if t < 0.5 else warped(B, np.concatenate([UB, LB]), dst); out.append([t, np.clip(im, 0, 255)])
    return out
def kept(P, R, nose, reach):
    """A mouth pose as it is used: the pose round its opening, the resting picture everywhere else.
    Each pose was drawn again inside a patch that reaches well below the mouth, and the fur in that patch is new fur:
    the same coat, but not the same hairs. The page cross-fades from pose to pose, so with every syllable the fur under
    the chin dissolved into other fur and back, as far down as the widest pose's patch (a third of the way to the
    frame's edge). What has to change with the jaw is the opening, the lips round it and the tuft on the chin under
    them; `reach` pixels round the opening takes those in, and beyond it the hairs are the resting picture's own."""
    ys, xs = np.where(np.abs(P - R).max(axis=2) > 0)
    if not len(ys): return P
    op = opening(P, nose, (xs.min(), xs.max() + 1, ys.min(), ys.max() + 1))
    if op.sum() < 40: return P                                                                     # no opening to speak of (the shut mouth): its patch is small as it is
    w = np.clip(cv2.GaussianBlur(cv2.dilate(op, ell(int(reach))).astype(np.float32), (0, 0), reach / 3), 0, 1)[..., None]
    return R + (P - R) * w
def partway(R, P, k):
    """A gaze pose that looks less far than it was drawn: the pose itself, with every point moved back towards where it
    is in the open eyes R until only k of the way is left. (Mixing the pose with the open eyes instead shows both at
    once: two glints in each eye and a white seen through the iris.) Where each point belongs in R is dense optical
    flow, smoothed over a few pixels so that the iris moves as one piece; an iris that slides a few pixels is something
    flow can follow, which a jaw that drops is not."""
    ys, xs = np.where(np.abs(P - R).max(axis=2) > 0); X0, X1, Y0, Y1 = max(0, xs.min() - 2), min(R.shape[1], xs.max() + 3), max(0, ys.min() - 2), min(R.shape[0], ys.max() + 3)
    gray = lambda im: cv2.cvtColor(im[Y0:Y1, X0:X1].round().astype(np.uint8), cv2.COLOR_RGB2GRAY); yy, xx = np.mgrid[0:Y1 - Y0, 0:X1 - X0].astype(np.float32)
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM); dis.setFinestScale(0); f = cv2.GaussianBlur(dis.calc(gray(P), gray(R), None), (0, 0), 4)
    f *= step(0, 6, np.minimum(np.minimum(xx, X1 - X0 - 1 - xx), np.minimum(yy, Y1 - Y0 - 1 - yy))).astype(np.float32)[..., None]; px, py = xx, yy
    for _ in range(6): px, py = (xx - (1 - k) * cv2.remap(f[..., 0], px, py, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE), yy - (1 - k) * cv2.remap(f[..., 1], px, py, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE))
    out = R.copy(); out[Y0:Y1, X0:X1] = np.clip(cv2.remap(P[Y0:Y1, X0:X1], px, py, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE), 0, 255); return out
def export(key):
    d = f"work/{key}"; S = dict(SETS.get(key, {})); S.update(json.load(open(f"{d}/poses.json")) if os.path.exists(f"{d}/poses.json") else {})
    load = lambda n: np.asarray(Image.open(f"{d}/poses/{n}.png").convert("RGB")).astype(np.float32)
    R = load(S["rest"]); Hs, Ws = R.shape[:2]; E = {k: load(v) if isinstance(v, str) else partway(R, load(v[0]), v[1]) for k, v in S["eyes"].items()}; mouths = [(load(n), o) for n, o in S["mouth"]]; shut = load(S["shut"])
    for im in list(E.values()) + [m for m, _ in mouths] + [shut]: assert im.shape == R.shape, "the poses are not all one size"
    # ── where things are, in the pictures as they came: the eyes (what a blink changes), the nose (the largest dark thing below them)
    lids = cv2.morphologyEx((np.abs(E["closed"] - R).max(axis=2) > 24).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)); n, lab, st, cen = cv2.connectedComponentsWithStats(lids)
    eyeL, eyeR = sorted((cen[k] for k in 1 + np.argsort(-st[1:, 4])[:2]), key=lambda c: c[0]); exs, eys, iods = (eyeL[0] + eyeR[0]) / 2, (eyeL[1] + eyeR[1]) / 2, eyeR[0] - eyeL[0]
    dk = R.max(axis=2) < 60; dk[:int(eys + 0.2 * iods)] = False; dk[:, :int(exs - iods)] = False; dk[:, int(exs + iods):] = False; nose, nc = largest(dk)
    # ── the frame: scaled so that the ear tips have S["headroom"] pixels above them and the picture's lower edge falls
    # just below the frame's (the chest runs off it), the eyes on the middle line; then every picture goes through `fit`
    a_src = matte(R); top = int(np.where(a_src.max(axis=1) > 0.5)[0][0]); s = (H + 4 - S["headroom"]) / (Hs - top); size = (round(Ws * s), round(Hs * s))
    ox, oy = round(W / 2 - exs * s), S["headroom"] - round(top * s); sx0, sy0 = max(0, -ox), max(0, -oy)
    def fit(im, fill):
        small = np.dstack([np.asarray(Image.fromarray(im[..., c]).resize(size, Image.LANCZOS)) for c in range(im.shape[2])]) if im.ndim == 3 else np.asarray(Image.fromarray(im).resize(size, Image.LANCZOS))
        out = np.full((H, W) + im.shape[2:], fill, np.float32); part = small[sy0:sy0 + H - max(0, oy), sx0:sx0 + W - max(0, ox)]; out[max(0, oy):max(0, oy) + part.shape[0], max(0, ox):max(0, ox) + part.shape[1]] = part; return out
    # ── the run of mouths, in jaw units, with in-betweens wherever the outline travels further than S["travel"] in one step
    run = []                                                                                       # [jaw, picture, made here?]
    near = lambda im: kept(im, R, nose, S.get("reach", 24))
    for i, (im, o) in enumerate(mouths):
        if i: run += [[JAW * (mouths[i - 1][1] + t * (o - mouths[i - 1][1])), b, True] for t, b in between(mouths[i - 1][0], im, R, nose, float(nc[0]), S["travel"] / s)]
        run.append([JAW * o, im, False])
    run = [[j, near(im), made] for j, im, made in run]
    P = lambda x, y: (x * s + ox, y * s + oy)                                                         # a point of the pictures, in the frame
    alpha = np.clip(fit(a_src, 0), 0, 1); alpha[alpha < 0.01] = 0; frame = np.clip(fit(R, 255), 0, 255); A3 = alpha[..., None]
    ex, ey = P(exs, eys); iod = iods * s; nx_, ny_ = P(*nc)
    # ── the cut-out: colours un-mixed from white, so that cut-out over plate is the picture again. Where almost nothing
    # of a pixel is fur its un-mixed colour is mostly noise: there it leans on the fur colour carried out from inside.
    fur, _ = carried(frame, alpha > 0.98, (2, 4, 8, 16), 255)
    def unmixed(im): col = np.clip((im - (1 - A3) * 255) / np.maximum(A3, 1e-3), 0, 255); return fur + (col - fur) * np.clip(A3 / 0.15, 0, 1)
    cut = unmixed(frame); fg = Image.fromarray(np.dstack([cut, alpha * 255]).round().astype(np.uint8), "RGBA"); plate = Image.new("RGB", (W, H), (255, 255, 255))
    back = cut * A3 + 255 * (1 - A3); fg.save(f"{d}/cutout.png"); Image.fromarray((alpha * 255).round().astype(np.uint8)).save(f"{d}/alpha.png"); Image.fromarray(frame.round().astype(np.uint8)).save(f"{d}/frame.png")
    # ── mouth and eyes: every pose in the frame, un-mixed like the cut-out, cropped to one soft mask per region
    rest = unmixed(frame); pose = lambda im: unmixed(np.clip(fit(im, 255), 0, 255))
    def softmask(ims, grow=5, feather=2.5):
        b = cv2.morphologyEx((np.max([np.abs(im - rest).mean(axis=2) for im in ims], axis=0) > 3).astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        b = cv2.morphologyEx(cv2.dilate(b, ell(grow)), cv2.MORPH_CLOSE, ell(2 * grow)); return np.clip(cv2.GaussianBlur(cv2.dilate(b, ell(int(2 * feather))).astype(np.float32), (0, 0), feather), 0, 1)
    def region(M, groups):
        ys, xs = np.where(M > 1 / 255); x0, x1, y0, y1 = int(xs.min()), int(xs.max()) + 1, int(ys.min()), int(ys.max()) + 1
        rgb = lambda im: uri(Image.fromarray(im[y0:y1, x0:x1].round().astype(np.uint8)), quality=86, method=6)
        mk = np.zeros((y1 - y0, x1 - x0, 4), np.uint8); mk[..., :3] = 255; mk[..., 3] = (M[y0:y1, x0:x1] * 255).round()
        out = dict(x=x0, y=y0, w=x1 - x0, h=y1 - y0, mask=uri(Image.fromarray(mk, "RGBA"), "PNG", optimize=True))
        out.update({g: ([rgb(im) for im in v] if isinstance(v, list) else rgb(v)) for g, v in groups.items()}); return out
    seq = [pose(im) for _, im, _ in run]; jn = [0] + [round(float(j), 1) for j, _, _ in run]; pshut = pose(shut); Mm = softmask(seq + [pshut])
    # The engine keeps a row of jaw steps for each lip shape and for a smile, and mixes rows as the sounds ask. An animal's
    # mouth has one row. Every row is given the same pictures at the same jaw steps, so whatever the mix it is one picture.
    m = region(Mm, dict(n=seq, e1=[rest] + seq, e2=[rest] + seq, w1=[rest] + seq, w2=[rest] + seq, sg=[rest] + seq, p=pshut, sh=rest)); m["jn"] = jn; m["js"] = jn
    eyes = {k: pose(v) for k, v in E.items()}; Me = softmask(list(eyes.values()), grow=3, feather=1.5)
    e = region(Me, {k: eyes.get(k, rest) for k in ("half", "closed", "gl", "gr", "gd", "smile")})
    # ── motion: six fields, drawn. yy / xx in eye distances from the middle of the eyes.
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); u, v = (xx - ex) / iod, (yy - ey) / iod; my = (ny_ - ey) / iod      # the nose, in eye distances below the eyes
    body = cv2.dilate((alpha > 0.1).astype(np.uint8), np.ones((9, 9), np.uint8)).astype(np.float32)   # the plate does not move
    # the head: everything down to the mouth, fading out over the whole ruff below it, as far as the frame's lower edge
    # (nothing moves on that edge). The ruff is all there is between the chin and the edge, a fifth of the frame, and
    # whatever the head travels as a whole that strip of fur has to take up by stretching. First the head slid a ninth
    # of an eye distance in a turn and the strip took it up in its upper half: the coat under the chin pulled like
    # cloth. A head that turns hardly moves its outline; what moves is what stands out towards the camera. So most of
    # a turn or a nod is the muzzle's travel now, and the little the whole head moves is spread over the whole strip.
    head = cv2.GaussianBlur(body * (1 - step(my + 0.45, (H - 6 - ey) / iod, v)), (0, 0), 0.12 * iod) * (1 - step(H - 0.2 * iod, H - 2, yy))
    muzzle = np.exp(-(u / 0.6) ** 2 - ((v - my - 0.1) / 0.65) ** 2)                                   # nearest the camera: it travels furthest when the head turns or nods
    ear = cv2.GaussianBlur(body * step(-0.85, -1.85, v), (0, 0), 0.08 * iod)                          # furthest from it: the tips travel least
    (t0, t1, t2), (n0, n1, n2) = S.get("turn", (0.05, 0.14, 0.02)), S.get("nod", (0.04, 0.10, 0.02))
    turn = head * (t0 + t1 * muzzle - t2 * ear) * iod; nod = head * (n0 + n1 * muzzle - n2 * ear) * iod; z = np.zeros_like(turn)
    # "brows up" is attention: the ears lift from their base to their tips (and lean in a touch), the fur over the eyes
    # lifts a little; "brows down" lets the ears sink and spread. The eyes themselves stay put: their poses are pictures.
    brow = cv2.GaussianBlur(body * step(-0.18, -0.42, v) * (1 - step(-0.6, -1.0, v)) * (1 - step(0.8, 1.25, np.abs(u))), (0, 0), 0.04 * iod)
    fields = [np.dstack([turn, z]), np.dstack([-turn, z]), np.dstack([z, nod]), np.dstack([z, -nod]),
              np.dstack([-0.012 * iod * ear * np.sign(u), -(0.05 * ear + 0.022 * brow) * iod]), np.dstack([0.016 * iod * ear * np.sign(u), (0.025 * ear + 0.012 * brow) * iod])]
    mag = np.max([np.hypot(f[..., 0], f[..., 1]) for f in fields], axis=0); ys, xs = np.where(mag > 0.04)
    st = int(np.clip(round(iod * 0.11), 6, 14)); x0 = max(0, int(xs.min()) - st); y0 = max(0, int(ys.min()) - st)
    cols = min(W - x0, int(xs.max()) + st - x0) // st + 2; rows = min(H - y0, int(ys.max()) + st - y0) // st + 2
    gx = np.clip(x0 + np.arange(cols) * st, 0, W - 1); gy = np.clip(y0 + np.arange(rows) * st, 0, H - 1); enc = []
    for f in fields:
        g = f[gy][:, gx].copy(); g[0] = g[-1] = 0; g[:, 0] = g[:, -1] = 0; k = 127 / max(1e-3, np.abs(g).max()); enc.append([round(float(k), 4), base64.b64encode(np.round(g * k).astype(np.int8).tobytes()).decode()])
    # ── body: none. The engine lets a torso breathe (its upper edge rises and falls a tenth of an eye distance), widen
    # and turn under the head, which is what a chest in a shirt does. The strip of ruff at the frame's edge was first
    # given as the torso, and the fur pumped up and down against the pinned edge and slid sideways under the chin. With
    # no torso the whole figure takes a quarter of the breath and sways as one piece, which is all a sitting dog shows.
    tor = step(my + 0.95, my + 1.5, v); A = alpha; blur = lambda mm, sg: cv2.GaussianBlur((mm * A).astype(np.float32), (0, 0), sg * iod) / np.maximum(cv2.GaussianBlur(A, (0, 0), sg * iod), 1e-3)
    tor = 0 * blur(tor, 0.12); ysh = ey + (my + 1.22) * iod; low = np.where(alpha[H - 12:].max(axis=0) > 0.5)[0]; bcx, br = (low.min() + low.max()) / 2, float(np.clip((low.max() - low.min()) / 2, 1.2 * iod, 4 * iod))
    by = np.minimum(np.arange(0, H + 1, 8), H - 1); bx = np.minimum(np.arange(0, W + 1, 8), W - 1)
    b64 = lambda mm: base64.b64encode(np.round(np.clip(cv2.GaussianBlur(mm.astype(np.float32), (0, 0), 8 / 3)[by][:, bx], 0, 1) * 255).astype(np.uint8).tobytes()).decode()
    chin = float(np.where(opening(R, nose, (int(exs - iods), int(exs + iods), int(nc[1]), Hs)).any(axis=1))[0].max() * s + oy + 0.3 * iod)      # under the shut lips
    ent = dict(bg=uri(plate, "JPEG", quality=86), fg=uri(fg, quality=96, method=6), seed=float(S["seed"]), gain=float(S["gain"]),
               face=dict(cx=round(float(ex), 1), cy=round(float(ey + 0.45 * iod), 1), iod=round(float(iod), 1)), mouth=m, eyes=e,
               flow=dict(x=x0, y=y0, step=st, cols=int(cols), rows=int(rows), f=enc),
               body=dict(step=8, cols=len(bx), rows=len(by), cx=round(float(bcx), 1), sy=round(float(ysh), 1), r=round(br, 1), chin=round(chin, 1), b=b64(tor), h=b64(np.zeros((H, W)))))
    # ── sheets to look at: the run of mouths (made steps marked), the eye poses, the cut-out over a dark ground, what moves
    box = lambda r, pad=6: (slice(max(0, r["y"] - pad), r["y"] + r["h"] + pad), slice(max(0, r["x"] - pad), r["x"] + r["w"] + pad)); u8 = lambda im: np.clip(im, 0, 255).round().astype(np.uint8)
    tiles = [u8(rest[box(m)])] + [u8(im[box(m)]) for im in seq]
    for t, (_, _, made) in zip(tiles[1:], run): t[:5, :] = (60, 120, 255) if made else (40, 200, 60)        # blue: made here; green: a pose as it came
    n = math.ceil(len(tiles) / 2); tiles += [np.full_like(tiles[0], 255)] * (2 * n - len(tiles)); Image.fromarray(np.vstack([np.hstack(tiles[:n]), np.hstack(tiles[n:])])).resize((tiles[0].shape[1] * n * 2, tiles[0].shape[0] * 4), Image.LANCZOS).save(f"{d}/mouth_run.png")
    strip = np.hstack([u8(rest[box(e)])] + [u8(eyes[k][box(e)]) for k in eyes]); Image.fromarray(strip).resize((strip.shape[1] * 2, strip.shape[0] * 2), Image.LANCZOS).save(f"{d}/eyes_run.png")
    Image.fromarray(u8(cut * A3 + np.array([40, 60, 90], np.float32) * (1 - A3))).save(f"{d}/cutout_dark.png")
    vis = frame * 0.4; vis[..., 0] += 150 * head * (0.3 + 0.7 * muzzle); vis[..., 1] += 150 * tor * alpha; vis[..., 2] += 250 * np.maximum(ear, brow); vis = u8(vis)
    cv2.line(vis, (0, int(ysh)), (W, int(ysh)), (255, 255, 255), 1); cv2.circle(vis, (int(ex), int(ey + 0.45 * iod)), 4, (255, 255, 0), -1); cv2.line(vis, (int(bcx - br), H - 8), (int(bcx + br), H - 8), (255, 255, 0), 2); Image.fromarray(vis).save(f"{d}/motion.jpg", quality=88)
    kb = lambda o: sum(len(q) if isinstance(q, str) else sum(len(w) for w in q) for q in o.values() if isinstance(q, (str, list)) and q and isinstance(q if isinstance(q, str) else q[0], str)) // 1024
    print(f"{key}: scale {s:.3f}, eyes {iod:.0f} px apart at ({ex:.0f}, {ey:.0f}), nose ({nx_:.0f}, {ny_:.0f}); cut-out over plate differs from the picture by at most {np.abs(back - frame).max():.1f}; "
          f"mouth {m['w']}x{m['h']} {kb(m)} kB, {len(seq)} steps at jaw {jn[1:]} ({sum(1 for q in run if q[2])} made here), eyes {e['w']}x{e['h']} {kb(e)} kB; "
          f"motion grid {cols}x{rows} step {st}, turn up to {np.abs(turn).max():.0f} px, nod {np.abs(nod).max():.0f} px, ears {0.05 * iod:.0f} px; chest from {ysh:.0f}, middle {bcx:.0f}, half width {br:.0f}", flush=True)
    return ent
if __name__ == "__main__":
    key = sys.argv[1] if len(sys.argv) > 1 else "dog"; json.dump({key: export(key)}, open(f"cast_{key}.json", "w"))
