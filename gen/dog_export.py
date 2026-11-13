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
  mouth   speech moves the jaw (an animal has no lip shapes): a run of pictures from shut to open, made from the
          resting picture and ONE open pose as a jaw that drops (`jaw_run`): the upper lip stays, the chin goes
          down as one piece over the fur of the throat, and the open pose's lips, teeth and tongue show in the gap,
          held to the lower lip. The rows the engine has for lip shapes and smiles are the same drawing opened a
          little differently (the corners sooner or later, the tongue lifted or let down); p, b and m get the
          resting mouth. What is inside the open pose goes down with the jaw as one piece, so it has to be the lower
          jaw's own, each thing in its place: the tongue lying on the lower lip, the lower canines at the front
          corners either side of its tip, leaning apart (gen/dog_teeth.py sets them there; gen/dog_inside.py lays an editing
          model's redraw of the inside into a pose). Tried, and looked at by the dog's owner: canines drawn far
          back beside the root of the tongue (the tongue then lies ahead of the front teeth without hanging out);
          the tongue drawn behind a row of lower teeth (half open, the upper lip hides the upper part of the
          inside, and what is left is a pink band lying on top of the teeth).
  eyes    half and fully shut lids, and the gaze poses there are (left, right, down); the rest are the open eyes.
          (The engine's gaze goes sideways and down only, so a pose looking up has no slot to go in.)
  motion  nothing was measured, so the six fields are drawn: a turn and a nod move the muzzle (it is nearest the
          camera), the whole head only a little and the ears least, fading out down the ruff; "brows up" lifts the ears a little,
          since that is where an animal shows attention. All of it smooth, on the grid the page's mesh uses.
  body    no torso and no free hair: fur that breathes and turns like a shirt slides about under the chin (see export).

The pictures, and everything made from them, stay out of the repository (gen/work/<key>/ and the cast file are ignored).
Run from gen/:  ./venv2/bin/python dog_export.py            -> cast_dog.json, and sheets to look at in work/dog/
then, from the repository root:  python3 avatar/faces/pack.py dog 1.1 0.4 4 0.5 0 jaw=0.045 tilt=0.1 pant=0.32 perk=0.65 && python3 avatar/build.py dog
(jaw: the heavy jaw, see speechAt in src/news.js; tilt, pant, perk: the head tilted now and then, the mouth hanging
open while the animal is left alone, the ears lifted while it is spoken to: see faceAt)"""
import sys, json, os, base64, math
import cv2, numpy as np
from PIL import Image
from lpexport3 import uri
W, H, JAW = 1024, 576, 46                                   # the frame; jaw units at an opening of 1 (src/news.js)
# What the poses of a face are called (files in work/<key>/poses/, without .png).
# jaw: [pose, opening, lift, most]: the open mouth the run is made from (see `jaw_run`); where on the engine's scale
# the mouth is at its widest; how far the middle openings are brought forward (0 to 1; see `export`); and how much of
# the pose's own opening that widest is (1 if left out). On that scale a quick vowel between two consonants is about
# 0.2, a clear one 0.5, a stressed "ah" 1.
# shut: the mouth for p, b, m: the resting picture. The run starts from that picture, so the lips meet in it exactly;
# a separately drawn shut mouth (mouth_6 is one) would swap the fur round the mouth for other fur at every p, b and m.
# eyes: the engine's slots (gl / gr look to the viewer's left / right, gd down); a slot left out shows the open eyes.
# A gaze pose that looks further than is wanted is given as [name, how much of it to keep] (see `partway`).
# travel: how far (pixels in the frame) the lower lip may move between two stored steps. The page cross-fades between
# steps, and what moves further than this shows double.
# turn, nod: how far a full turn / nod carries the whole head, the muzzle on top of that, and the ears less, in eye
# distances (see "motion" above); spread: how far round the nose the muzzle's extra travel reaches, sideways and up and
# down, in eye distances. Fur shows every stretch: a coat is all fine lines, and where one part of the picture travels
# further than its neighbour the lines between them are pulled or pushed together. So the muzzle's travel is kept
# small and falls off slowly, over the cheeks: with 0.14 of an eye distance falling off within 0.6 the cheeks, the
# narrower one most, could be seen to squeeze and stretch at every turn of the head.
# A file work/<key>/poses.json with the same fields replaces this entry, so a new set of poses needs no edit here.
SETS = dict(dog=dict(rest="resting", jaw=["mouth_5i", 0.68, 0.6, 1.0], shut="resting",
                     eyes=dict(half="eyes_half", closed="eyes_closed", gl="eyes_right", gr=["eyes_left", 0.55], gd="eyes_down"),
                     travel=1.6, turn=(0.03, 0.09, 0.02), nod=(0.03, 0.07, 0.02), spread=(0.9, 0.9), headroom=32, gain=1.0, seed=9.5))
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
def jaw_run(P, R, nose, travel, most=1.0, shapes=None, fine=("n",), coarser=1.7, margin=16, fringe=22, shade=11):
    """The run of mouths as a jaw that drops: ONE open pose P (lips, teeth and tongue as drawn) and the resting
    picture R, put together the way a mouth opens. Returns, for each of `shapes`, [how far open, picture] for each
    step, the lower lip no further than `travel` pixels from one to the next (`coarser` times that in the shapes
    not named in `fine`: those are only seen in passing, mixed with the plain one). How far open is a fraction of the
    pose's own opening; the last step is at `most` (1: as far open as the pose).
    shapes: {name: (side, tongue)}. An animal has no lip shapes, but its mouth is not one flap either: the corners
    draw back for a grin and stay shut round a small opening, and the tongue is not fixed to the jaw. side > 0: the
    corners open sooner than the middle asks: the wide mouth of an "ee". side < 0: the sides stay shut longer, so
    the opening is a narrower one in the middle: an "oo". tongue: how far (pixels of the pose) the lit part of the
    tongue is lifted towards the upper teeth (as for t, d, n, l, s) or, negative, let down and back. All shapes are
    the same drawing; they differ in how far each column of the mouth is open and in where the tongue's soft upper
    edge lies, and by little enough that the page can mix two of them.
    Three things are in front of one another, as on the animal:
    - the upper lip and all the rest of the picture: R, which does not move. The mouth divides where the lips meet,
      at the middle of the resting mouth's dark line (divided at the line's lower edge, the pale fur of the lower lip
      stayed up under the upper lip as a light, ragged outline round the open mouth);
    - the inside of the mouth: P's, held to the LOWER lip. Its lower lip sits on the chin and as much of it shows as
      the gap has room for: a little way open the lower teeth show under the upper lip, then the tongue comes up
      from behind them. Nothing is squeezed, mixed or exchanged on the way, every step is as sharp as the pose, and
      with the jaw shut the picture is R itself. Under the upper lip it is in shadow, deepest right at the lip and
      gone `shade` pixels below, and the lip's own rim darkens with it, so that teeth and tongue come up out of the
      dark and are not sliced off along a line. As the gap grows P's black lower lip comes down over the lower half
      of the resting line, which it replaces (`tuck`): fully open, the lip sits on the pale fur as it does in P;
    - the chin: R's own fur from the lip down to a little under the pale tuft, as one piece that goes down with the
      lower lip: all the way in the middle of the mouth, less to either side and not at all towards the corners
      (a jaw turns on its hinge, and the corners of the mouth are next to it; the fur there, and the whiskers in
      it, stay as they are and the black of the lower lip comes down over them). It lies OVER the fur of the throat, which stays
      where it is: that fur is neither pushed together nor carried along. The piece's lower edge is not a line: over
      `fringe` pixels it ends hair by hair (its lighter hairs reach further), and towards that edge its broad
      shading goes over into that of the fur it lies on, so that no step of brightness travels with it.
    What was there before, and why not (each was looked at in motion by the dog's owner):
    - the poses' own pictures with steps made between each two: each pose was drawn separately and no two agree
      about what is inside the mouth, so somewhere between two of them one mouth has to turn into the other: done
      at once it popped at the corner, done by degrees the steps half way were soft;
    - every step from the slightly open pose, opened and closed by degrees: one mouth and sharp, but a dark gap
      with no tongue, not far open, and stretched: not a dog's mouth;
    - this jaw with the chin as a patch slid down, its edges straight cuts, and the inside sliced off along the
      upper lip: "cut out with scissors";
    - the fur under the lip giving way by degrees over a hundred pixels instead: no cut, but the coat under the chin
      was pushed together to half its height and let out again with every syllable."""
    ys, xs = np.where(np.abs(P - R).max(axis=2) > 0); X0, X1, Y0, Y1 = max(0, xs.min() - 2), min(R.shape[1], xs.max() + 3), max(0, ys.min() - 2), min(R.shape[0], ys.max() + 3)
    Op, Or = opening(P, nose, (X0, X1, Y0, Y1)), opening(R, nose, (X0, X1, Y0, Y1)); cols = np.where(Op.any(axis=0))[0]; xl, xr = int(cols.min()), int(cols.max()); x = np.arange(xl, xr + 1)
    sm = lambda v, sg=2.5: cv2.GaussianBlur(cv2.medianBlur(v.astype(np.float32).reshape(1, -1), 5), (0, 0), sg, borderType=cv2.BORDER_REPLICATE).ravel()
    env = lambda v, k: cv2.erode(v.astype(np.float32).reshape(1, -1), np.ones((1, k), np.uint8), borderType=cv2.BORDER_REPLICATE).ravel()      # the lowest value within k columns
    U, L = sm(env(np.argmax(Op[:, xl:xr + 1], axis=0), 25), 5), sm(Op.shape[0] - 1 - np.argmax(Op[::-1, xl:xr + 1], axis=0)) - 3  # (the upper edge is the upper LIP's: a white tooth standing in it is not part of what was found, and left a notch that the mouth then opened along)  # P's opening: its upper and lower edge, column by column (the lower one taken a little inside the lip: at the very edge its black is already mixed with the fur under it, and that showed as a light thread along the lower lip)
    has = Or[:, xl:xr + 1].any(axis=0); rx = x[has]; r0, r1 = int(rx.min()), int(rx.max())                             # the columns the resting mouth's line covers
    lt, lb = np.argmax(Or[:, xl:xr + 1], axis=0), Or.shape[0] - 1 - np.argmax(Or[::-1, xl:xr + 1], axis=0)             # that line's upper and lower edge
    # Where the lips meet: the middle of the line's darkness in each column, and smooth along the mouth. (The line's two
    # edges as the mask has them were used first: pale hairs lie across the line here and there, the edges jump at each,
    # and the mouth then opened along a ragged tear with bits of pale hair on either side of it.)
    lumR = cv2.GaussianBlur(R.mean(axis=2), (0, 0), 1.5); rows = np.arange(R.shape[0], dtype=np.float32); mid = np.zeros(len(x), np.float32)
    for i, c in enumerate(x):
        if has[i]: a, e = max(0, lt[i] - 3), lb[i] + 4; wgt = np.clip(120 - lumR[a:e, c], 0, None) + 1e-3; mid[i] = (wgt * rows[a:e]).sum() / wgt.sum()
    fill = lambda v: np.interp(x, x[has], v[has]); mid = cv2.GaussianBlur(cv2.medianBlur(fill(mid).astype(np.float32).reshape(1, -1), 5), (0, 0), 7, borderType=cv2.BORDER_REPLICATE).ravel()
    thick = np.clip(cv2.GaussianBlur(fill((lb - lt) / 2).astype(np.float32).reshape(1, -1), (0, 0), 10, borderType=cv2.BORDER_REPLICATE).ravel(), 4, 12)
    inl = cv2.GaussianBlur(has.astype(np.float32).reshape(1, -1), (0, 0), 4).ravel(); half = thick * inl; top = U + inl * np.clip(mid - U, 0, None)      # (P's own upper edge beyond the line's ends)
    full = np.clip(L - top, 0, None) * np.clip(np.minimum(x - xl, xr - x) / 5.0, 0, 1)
    out_by = np.clip(np.maximum(r0 - x, x - r1), 0, None).astype(np.float32); late = 0.55 * out_by / max(1.0, out_by.max())
    # how far down the chin piece reaches: to under the pale tuft (fur that has little colour), and a margin
    sat = cv2.GaussianBlur(cv2.cvtColor(np.clip(R, 0, 255).astype(np.uint8), cv2.COLOR_RGB2HSV)[..., 1].astype(np.float32) / 255, (0, 0), 3); under = np.round(top + half + 2).astype(int)
    tuft = np.array([u + (int(np.argmax(sat[u:u + 60, c] > 0.45)) if (sat[u:u + 60, c] > 0.45).any() else 60) for u, c in zip(under, x)], np.float32)
    foot = sm(np.maximum(tuft, top + half + 14) + margin, 8)
    pad = 44; xa, xb = max(0, xl - pad), min(R.shape[1] - 1, xr + pad); ya, yb = Y0, int(min(R.shape[0], L.max() + (foot - top).max() + fringe + 8))
    wide = lambda v, zero=False: np.concatenate([np.full(xl - xa, 0 if zero else v[0], np.float32), v.astype(np.float32), np.full(xb - xr, 0 if zero else v[-1], np.float32)])
    T, Lw, Fw, Hw = wide(top), wide(L), wide(foot), wide(half, True); yy, xx = np.mgrid[ya:yb, xa:xb + 1].astype(np.float32); ly, lx = yy - ya, xx - xa
    Rp = R[ya:yb, xa:xb + 1]; lum = Rp.mean(axis=2); hp = lum - cv2.GaussianBlur(lum, (0, 0), 2); hair = np.clip(hp / (2 * np.sqrt(cv2.GaussianBlur(hp * hp, (0, 0), 8)) + 2), -1, 1)
    edge = np.clip(0.5 - (yy - Fw[None, :]) / fringe, 0, 1); A = np.clip((edge + 0.32 * hair - 0.5) / 0.22 + 0.5, 0, 1) * (yy >= T[None, :] - 1)      # the piece, hair by hair at its lower edge
    Wm = step(-fringe / 2 - 14, -fringe / 2, yy - Fw[None, :]).astype(np.float32); low = cv2.GaussianBlur(Rp, (0, 0), 7)                              # where its broad shading goes over into the fur's below (under the tuft, which keeps its own)
    mid, hw = (r0 + r1) / 2, (r1 - r0) / 2; chin = wide(1 - step(0.5 * hw, 0.95 * hw, np.abs(x - mid)), True)                                         # the chin is the middle of the lower lip; at the corners nothing goes down
    at = lambda im, sy: cv2.remap(im, lx, (sy - ya).astype(np.float32), cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    runs = {}; dark = np.array([20, 13, 13], np.float32)
    away = np.abs(x - (xl + xr) / 2) / max(1.0, (xr - xl) / 2)                                    # 0 in the middle of the mouth, 1 at the pose's corners
    r_, g_, b_ = P[..., 0], P[..., 1], P[..., 2]; lit = ((r_ > 120) & (r_ - g_ > 45) & (b_ > g_ - 12) & (Op > 0)).astype(np.uint8)       # the tongue where the light falls on it
    fy, fx = np.mgrid[0:P.shape[0], 0:P.shape[1]].astype(np.float32); P0 = P
    if lit.sum() > 200:                                                                            # it lifts from its upper edge; where it lies on the lower lip it stays
        lit = largest(cv2.morphologyEx(lit, cv2.MORPH_OPEN, ell(2)))[0]; tc = np.where(lit.any(axis=0))[0]; ty0 = np.argmax(lit[:, tc], axis=0).astype(np.float32); ty1 = (lit.shape[0] - 1 - np.argmax(lit[::-1, tc], axis=0)).astype(np.float32)
        t0, t1 = (np.interp(np.arange(P.shape[1]), tc, sm(v, 4)) for v in (ty0, ty1)); lit = cv2.GaussianBlur(lit.astype(np.float32), (0, 0), 4) * np.clip((t1[None, :] - 4 - fy) / np.maximum(t1 - t0 - 4, 1)[None, :], 0, 1)
        teeth = ((P.min(axis=2) > 115) & (r_ - b_ < 95) & (r_ - g_ < 45) & (cv2.dilate(Op, ell(4)) > 0)).astype(np.uint8)                 # pale and colourless inside the mouth: they stand in the jaw
        lit *= 1 - np.clip(cv2.GaussianBlur(cv2.dilate(teeth, ell(2)).astype(np.float32), (0, 0), 1.5) * 1.5, 0, 1)                      # and do not go up and down with the tongue beside them
    else: lit = np.zeros(P.shape[:2], np.float32)
    # the lower lip's own colour, column by column (its rim is drawn in it: drawn in black it stood round a brown lip like a pen line)
    lipc = np.stack([wide(cv2.GaussianBlur(np.array([P0[int(l) - 6:int(l) - 1, c, k].mean() for l, c in zip(L, x)], np.float32).reshape(1, -1), (0, 0), 4).ravel()) for k in range(3)], axis=1)
    for name, (side, tongue) in (shapes or {"n": (0, 0)}).items():
        lag = late * (1 - 0.75 * side) if side >= 0 else np.clip(late + 0.48 * -side * step(0.3, 0.9, away), 0, 0.92); run = runs[name] = []
        P = P0 if not tongue else cv2.remap(P0, fx, (fy + tongue * lit).astype(np.float32), cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)                          # the pose with its tongue lifted or let down
        n = max(2, math.ceil(most * full.max() / (travel if name in fine else travel * coarser)))      # (most shapes are only seen mixed with the plain row: they can do with fewer steps)
        for o in [most * (q + 1) / n for q in range(n)]:
            g = wide(cv2.GaussianBlur((np.clip((o - lag) / (1 - lag), 0, 1) * full).reshape(1, -1), (0, 0), 3).ravel(), True)        # the gap, column by column
            d = (g - Hw * step(0, 2.5 * Hw + 1e-3, g)) * chin; t, b, sy = T[None, :], (T + g)[None, :], yy - d[None, :]                       # how far the chin goes down (the lip comes over the line's lower half)
            a, wm = np.clip(at(A, sy), 0, 1)[..., None], np.clip(at(Wm, sy), 0, 1)[..., None]
            fur = Rp + a * (at(Rp, sy) + wm * (low - at(low, sy)) - Rp)
            inside = cv2.remap(P, xx, (yy + (Lw[None, :] - b)).astype(np.float32), cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            w = (np.clip(yy - t + 0.5, 0, 1) * np.clip(b - yy + 0.5, 0, 1) * np.clip(g[None, :], 0, 1))[..., None]; both = fur * (1 - w) + inside * w
            dim = 0.9 * np.where(yy < t, np.clip(1 - (t - yy) / 6, 0, 1) ** 1.2, np.clip(1 - (yy - t) / shade, 0, 1) ** 1.5) * np.clip(g[None, :] / 5, 0, 1)                  # the upper lip's rim, and its shadow on what is under it
            tucked = np.clip((g - d) / np.maximum(Hw, 1), 0, 1)[None, :] * (Hw[None, :] > 0.5)                                                                                # 0: the line's lower half is still the lower lip's rim, 1: P's lip has come down over it
            rim = ((0.85 - 0.3 * tucked) * np.clip(1 - (yy - b) / ((Hw[None, :] + 3) * (1 - tucked) + 4 * tucked), 0, 1) * np.clip(yy - b + 1, 0, 1) * np.clip(g[None, :] / 4, 0, 1))[..., None]      # the lower lip's rim (the line's lower half with its stray pale hairs; later the soft edge of P's lip on the fur)
            both = both * (1 - dim[..., None]) + dark * dim[..., None]; im = R.copy(); im[ya:yb, xa:xb + 1] = both * (1 - rim) + lipc[None] * rim; run.append([o, np.clip(im, 0, 255)])
    return runs
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
    R = load(S["rest"]); Hs, Ws = R.shape[:2]; E = {k: load(v) if isinstance(v, str) else partway(R, load(v[0]), v[1]) for k, v in S["eyes"].items()}; wide_open, shut = load(S["jaw"][0]), load(S["shut"])
    for im in list(E.values()) + [wide_open, shut]: assert im.shape == R.shape, "the poses are not all one size"
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
    # ── the run of mouths, and where on the engine's scale each step is shown. Evenly, a quick vowel (a fifth to a third
    # of the scale) parted the lips and no more: the animal mumbled. `lift` bends the scale so that the middle openings
    # come sooner (at 0.5 a jaw a third open shows the mouth a little over half open), the ends staying where they are.
    k = S["jaw"][2] if len(S["jaw"]) > 2 else 0; most = S["jaw"][3] if len(S["jaw"]) > 3 else 1; where = lambda o: o if not k else ((1 + k) - math.sqrt((1 + k) ** 2 - 4 * k * o)) / (2 * k)
    # The engine keeps a row of jaw steps for each lip shape (half and fully spread: e1, e2; half and fully rounded: w1,
    # w2) and for a smile (sg), and mixes rows as the sounds ask. Here the rows are the shapes of `jaw_run`.
    SHAPES = dict(n=(0, 0), e1=(0.5, 3), e2=(1, 6), w1=(-0.5, -2.5), w2=(-1, -5), sg=(1, 0))
    # The smile's row is also the mouth that hangs open while the animal pants (BODY.pant in src/news.js): it is held
    # for seconds and rocks by a step or two, so it is made as fine as the plain row and gets its own list of steps (jg).
    runs = {k: [[JAW * S["jaw"][1] * where(o / most), im] for o, im in v] for k, v in jaw_run(wide_open, R, nose, S["travel"] / s, most, SHAPES, fine=("n", "sg")).items()}; run = runs["n"]      # [jaw, picture]
    os.makedirs(f"{d}/steps", exist_ok=True)                                                           # every step as made, to look at (and none left over from a run before)
    for f in os.listdir(f"{d}/steps"):
        if f.endswith(".png"): os.remove(f"{d}/steps/{f}")
    for k, v in runs.items():
        for j, im in v: Image.fromarray(np.clip(im, 0, 255).round().astype(np.uint8)).save(f"{d}/steps/{k}_{j:04.1f}.png")
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
    rows = {k: [pose(im) for _, im in v] for k, v in runs.items()}; seq = rows["n"]; jn = [0] + [round(float(j), 1) for j, _ in run]; pshut = pose(shut); Mm = softmask([im for v in rows.values() for im in v] + [pshut])
    m = region(Mm, dict(n=seq, p=pshut, sh=rest, **{k: [rest] + rows[k] for k in ("e1", "e2", "w1", "w2", "sg")})); m["jn"] = jn; m["js"] = [0] + [round(float(j), 1) for j, _ in runs["e1"]]; m["jg"] = [0] + [round(float(j), 1) for j, _ in runs["sg"]]
    eyes = {k: pose(v) for k, v in E.items()}; Me = softmask(list(eyes.values()), grow=3, feather=1.5)
    e = region(Me, {k: eyes.get(k, rest) for k in ("half", "closed", "gl", "gr", "gd", "smile")})
    # ── motion: six fields, drawn. yy / xx in eye distances from the middle of the eyes.
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); u, v = (xx - ex) / iod, (yy - ey) / iod; my = (ny_ - ey) / iod      # the nose, in eye distances below the eyes
    # The fields are the same inside the figure's outline and outside it: what the mesh moves is the cut-out, and its
    # outline goes with the head. (They were first made to fade out across the outline, "because the plate does not
    # move". The plate is another picture and never did; what the fade did was hold the outline back while the face
    # went on, so that in every turn the outer finger's width of fur was pushed together on one side of the head and
    # pulled out on the other, by a sixth, and most plainly on the narrower cheek.)
    body = np.ones((H, W), np.float32)
    # the head: everything down to the mouth, fading out over the whole ruff below it, as far as the frame's lower edge
    # (nothing moves on that edge). The ruff is all there is between the chin and the edge, a fifth of the frame, and
    # whatever the head travels as a whole that strip of fur has to take up by stretching. First the head slid a ninth
    # of an eye distance in a turn and the strip took it up in its upper half: the coat under the chin pulled like
    # cloth. A head that turns hardly moves its outline; what moves is what stands out towards the camera. So most of
    # a turn or a nod is the muzzle's travel now, and the little the whole head moves is spread over the whole strip.
    head = cv2.GaussianBlur(body * (1 - step(my + 0.45, (H - 6 - ey) / iod, v)), (0, 0), 0.12 * iod) * (1 - step(H - 0.2 * iod, H - 2, yy))
    su, sv = S.get("spread", (0.9, 0.9)); muzzle = np.exp(-(u / su) ** 2 - ((v - my - 0.1) / sv) ** 2)      # nearest the camera: it travels furthest when the head turns or nods
    ear = cv2.GaussianBlur(body * step(-0.85, -1.85, v), (0, 0), 0.08 * iod)                          # furthest from it: the tips travel least
    (t0, t1, t2), (n0, n1, n2) = S.get("turn", (0.03, 0.09, 0.02)), S.get("nod", (0.03, 0.07, 0.02))
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
    # ── sheets to look at: the run of mouths, the eye poses, the cut-out over a dark ground, what moves
    box = lambda r, pad=6: (slice(max(0, r["y"] - pad), r["y"] + r["h"] + pad), slice(max(0, r["x"] - pad), r["x"] + r["w"] + pad)); u8 = lambda im: np.clip(im, 0, 255).round().astype(np.uint8)
    tiles = [u8(rest[box(m)])] + [u8(im[box(m)]) for im in seq]
    n = math.ceil(len(tiles) / 2); tiles += [np.full_like(tiles[0], 255)] * (2 * n - len(tiles)); Image.fromarray(np.vstack([np.hstack(tiles[:n]), np.hstack(tiles[n:])])).resize((tiles[0].shape[1] * n * 2, tiles[0].shape[0] * 4), Image.LANCZOS).save(f"{d}/mouth_run.png")
    strip = np.hstack([u8(rest[box(e)])] + [u8(eyes[k][box(e)]) for k in eyes]); Image.fromarray(strip).resize((strip.shape[1] * 2, strip.shape[0] * 2), Image.LANCZOS).save(f"{d}/eyes_run.png")
    Image.fromarray(u8(cut * A3 + np.array([40, 60, 90], np.float32) * (1 - A3))).save(f"{d}/cutout_dark.png")
    vis = frame * 0.4; vis[..., 0] += 150 * head * (0.3 + 0.7 * muzzle); vis[..., 1] += 150 * tor * alpha; vis[..., 2] += 250 * np.maximum(ear, brow); vis = u8(vis)
    cv2.line(vis, (0, int(ysh)), (W, int(ysh)), (255, 255, 255), 1); cv2.circle(vis, (int(ex), int(ey + 0.45 * iod)), 4, (255, 255, 0), -1); cv2.line(vis, (int(bcx - br), H - 8), (int(bcx + br), H - 8), (255, 255, 0), 2); Image.fromarray(vis).save(f"{d}/motion.jpg", quality=88)
    kb = lambda o: sum(len(q) if isinstance(q, str) else sum(len(w) for w in q) for q in o.values() if isinstance(q, (str, list)) and q and isinstance(q if isinstance(q, str) else q[0], str)) // 1024
    print(f"{key}: scale {s:.3f}, eyes {iod:.0f} px apart at ({ex:.0f}, {ey:.0f}), nose ({nx_:.0f}, {ny_:.0f}); cut-out over plate differs from the picture by at most {np.abs(back - frame).max():.1f}; "
          f"mouth {m['w']}x{m['h']} {kb(m)} kB, {len(seq)} steps at jaw {jn[1:]}, eyes {e['w']}x{e['h']} {kb(e)} kB; "
          f"motion grid {cols}x{rows} step {st}, turn up to {np.abs(turn).max():.0f} px, nod {np.abs(nod).max():.0f} px, ears {0.05 * iod:.0f} px; chest from {ysh:.0f}, middle {bcx:.0f}, half width {br:.0f}", flush=True)
    return ent
if __name__ == "__main__":
    key = sys.argv[1] if len(sys.argv) > 1 else "dog"; json.dump({key: export(key)}, open(f"cast_{key}.json", "w"))
