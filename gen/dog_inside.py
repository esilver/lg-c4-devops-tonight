"""dog_inside.py <key> <pose> <edited.png> <x0> <y0> <side> <out> : a pose's mouth as an image editor redrew it, put back into the pose

An editing model was shown a square cut round a pose's open mouth (side x side pixels of the pose at x0, y0, enlarged)
and asked to change one thing in it: the teeth. What it gives back is the whole cut drawn again: the same picture to
the eye, but not the same pixels anywhere, and a fraction of a pixel off. What is wanted of it is the inside of the
mouth. So the cut is brought back to size, laid where it best fits the pose, and taken only inside the pose's own
opening and a few pixels round it; everywhere else the pose stays as it was, pixel for pixel. (gen/dog_export.py uses
of an open pose only what is inside its opening, so this is all of the edit that can show.)
Run from gen/:  ./venv2/bin/python dog_inside.py dog mouth_5 /path/to/edited.png 550 576 448 mouth_5s
-> work/dog/poses/mouth_5s.png, and work/dog/inside_mouth_5s.png to look at (the pose, the edit, the result)."""
import sys, numpy as np, cv2
from PIL import Image
from dog_export import opening, largest, ell
key, pose, edited, x0, y0, side, out = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6]), sys.argv[7]
d = f"work/{key}"; load = lambda n: np.asarray(Image.open(f"{d}/poses/{n}.png").convert("RGB")).astype(np.float32)
R, P = load("resting"), load(pose); E = np.asarray(Image.open(edited).convert("RGB").resize((side, side), Image.LANCZOS)).astype(np.float32)
dk = R.max(axis=2) < 60; dk[:int(0.6 * R.shape[0])] = False; nose, _ = largest(dk)                 # the nose: the largest dark thing in the lower part of the picture
ys, xs = np.where(np.abs(P - R).max(axis=2) > 0); box = (xs.min(), xs.max() + 1, ys.min(), ys.max() + 1); cut = (slice(y0, y0 + side), slice(x0, x0 + side))
gray = lambda im: cv2.cvtColor(np.clip(im, 0, 255).astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32)
(dx, dy), how = cv2.phaseCorrelate(gray(P[cut]), gray(E), cv2.createHanningWindow((side, side), cv2.CV_32F))      # where the edit lies against the pose
E = cv2.warpAffine(E, np.float32([[1, 0, -dx], [0, 1, -dy]]), (side, side), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
whole = P.copy(); whole[cut] = E; m = np.maximum(opening(P, nose, box), opening(whole, nose, box))  # the opening as it was, and as the edit has it
w = np.clip(cv2.GaussianBlur(cv2.dilate(m, ell(4)).astype(np.float32), (0, 0), 2), 0, 1)[..., None]; new = P + (whole - P) * w
Image.fromarray(np.clip(new, 0, 255).round().astype(np.uint8)).save(f"{d}/poses/{out}.png")
a, b = max(0, box[2] - 20), min(P.shape[0], box[3] + 20); l, r = max(0, box[0] - 20), min(P.shape[1], box[1] + 20)
Image.fromarray(np.clip(np.hstack([P[a:b, l:r], whole[a:b, l:r], new[a:b, l:r]]), 0, 255).round().astype(np.uint8)).save(f"{d}/inside_{out}.png")
far = cv2.dilate(m, ell(12)) == 0; inb = np.zeros(m.shape, bool); inb[cut] = True
print(f"{out}: the edit lay {dx:+.2f}, {dy:+.2f} pixels off (fit {how:.2f}); away from the mouth it differs from the pose by {np.abs(whole - P).mean(axis=2)[far & inb].mean():.1f} levels on average; "
      f"{int((w[..., 0] > 0.5).sum())} pixels taken; outside them the new pose is the old one: {bool(np.abs(new - P).max(axis=2)[w[..., 0] == 0].max() == 0)}")
