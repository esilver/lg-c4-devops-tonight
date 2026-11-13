"""dog_teeth.py <key> <pose> <factor> <in> <down> <out> [sheet.jpg] : the two lower canines of an open-mouth pose set where a dog's stand

work/<key>/poses/<pose>.png -> work/<key>/poses/<out>.png. In the run of mouths (dog_export.py, `jaw_run`) everything inside the open
mouth goes down with the lower jaw as one piece. So the pose should hold what belongs to the lower jaw, where it belongs:
the tongue lying on the lower lip, and the lower canines at the front corners of the jaw, either side of the tip of the
tongue, coming up from behind the lip. (A pose came with them drawn far back, beside the root of the tongue: the tongue
then lay well ahead of the front teeth without hanging out of the mouth, which no dog's does, and the teeth came into
view last, from under the upper lip, as upper teeth would.)
Each canine is found as a pale, colourless patch inside the mouth beside the tongue. Both are taken out (what is round
them carried across); the better drawn one (the larger), `factor` times its size, is set with the middle of its root
`in` pixels nearer the middle of the mouth and `down` pixels lower than it was, and the same tooth, mirrored, on the
other side: two canines of one size, level, the same distance either side of the middle.
Run from gen/:  ./venv2/bin/python dog_teeth.py dog mouth_5n 1.3 9 31 mouth_5h"""
import sys, os, numpy as np, cv2
from PIL import Image
import dog_export as D
key, pose, k, din, down, out = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]), sys.argv[6]; src, rest, out = f"work/{key}/poses/{pose}.png", f"work/{key}/poses/resting.png", f"work/{key}/poses/{out}.png"
P = np.asarray(Image.open(src).convert("RGB")).astype(np.float32); R = np.asarray(Image.open(rest).convert("RGB")).astype(np.float32)
E = np.asarray(Image.open(os.path.join(os.path.dirname(src), "eyes_closed.png")).convert("RGB")).astype(np.float32)
lids = cv2.morphologyEx((np.abs(E - R).max(axis=2) > 24).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)); n, lab, st, cen = cv2.connectedComponentsWithStats(lids)
eL, eR = sorted((cen[q] for q in 1 + np.argsort(-st[1:, 4])[:2]), key=lambda c: c[0]); exs, eys, iods = (eL[0] + eR[0]) / 2, (eL[1] + eR[1]) / 2, eR[0] - eL[0]
dk = R.max(axis=2) < 60; dk[:int(eys + 0.2 * iods)] = False; dk[:, :int(exs - iods)] = False; dk[:, int(exs + iods):] = False; nose, nc = D.largest(dk)
Op = cv2.erode(D.opening(P, nose, (int(exs - iods), int(exs + iods), int(nc[1]), P.shape[0])), np.ones((3, 3), np.uint8))          # inside the mouth (the pale fur of the muzzle is not)
r, g, b = P[..., 0], P[..., 1], P[..., 2]; pale = ((P.min(axis=2) > 115) & (r - b < 95) & (r - g < 45) & (Op > 0)).astype(np.uint8)
n, lab, st, cen = cv2.connectedComponentsWithStats(pale); found = [i for i in range(1, n) if 25 <= st[i][4] <= 600 and st[i][3] >= 8 and st[i][3] > 1.1 * st[i][2] and 25 < abs(cen[i][0] - exs) < 110]
found = sorted(sorted(found, key=lambda i: -st[i][4])[:2], key=lambda i: cen[i][0]); assert len(found) == 2 and cen[found[0]][0] < exs < cen[found[1]][0], "two canines, one either side, were not found"
mid = (cen[found[0]][0] + cen[found[1]][0]) / 2; m_ = found[0] if st[found[0]][4] >= st[found[1]][4] else found[1]; side = -1 if cen[m_][0] < mid else 1
# the master, grown about the middle of its root, on a canvas of its own; its last rows fade (it comes up from behind the lip)
x, y, w, h, a = st[m_]; pad = 8; X0, Y0, X1, Y1 = x - pad, y - pad, x + w + pad, y + h + pad
m = cv2.GaussianBlur(cv2.dilate((lab[Y0:Y1, X0:X1] == m_).astype(np.float32), np.ones((3, 3), np.uint8)), (0, 0), 0.7); patch = P[Y0:Y1, X0:X1]
bx, by = cen[m_][0] - X0, float(y + h - Y0); big = (int(np.ceil(k * (X1 - X0))) + 4, int(np.ceil(k * (Y1 - Y0))) + 4); rx, ry = big[0] / 2, big[1] - 4.0 - k * (Y1 - Y0 - by)       # where the root lies on the canvas
M2 = np.float32([[k, 0, rx - k * bx], [0, k, ry - k * by]])
pm = cv2.warpAffine(patch, M2, big, flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE); mm = np.clip(cv2.warpAffine(m, M2, big, flags=cv2.INTER_CUBIC), 0, 1)
mm *= np.clip((ry + 1 - np.arange(big[1], dtype=np.float32)) / 3, 0, 1)[:, None]; mm = mm[..., None]
# both taken out (the root of one is in shadow and dimmer than the rest of it: taken with it)
loose = ((P.min(axis=2) > 70) & (r - b < 100) & (r - g < 50)).astype(np.uint8); n3, lab3 = cv2.connectedComponents(loose); gone = np.zeros_like(loose)
for i in found:
    near = np.zeros_like(loose); near[st[i][1] - 6:st[i][1] + st[i][3] + 12, st[i][0] - 8:st[i][0] + st[i][2] + 8] = 1; ids = np.unique(lab3[lab == i]); gone |= (np.isin(lab3, ids[ids > 0]) & (near > 0)).astype(np.uint8)
O = cv2.inpaint(np.clip(P, 0, 255).round().astype(np.uint8), cv2.dilate(gone, np.ones((5, 5), np.uint8)), 3, cv2.INPAINT_TELEA).astype(np.float32)
# and set at the front corners
off = abs(cen[m_][0] - mid) - din; rooty = st[m_][1] + st[m_][3] + down
for sgn in (side, -side):
    sprite, mask = (pm, mm) if sgn == side else (pm[:, ::-1], mm[:, ::-1]); cx = mid + sgn * off; rxx = rx if sgn == side else big[0] - 1 - rx
    ox, oy = int(round(cx - rxx)), int(round(rooty - ry)); O[oy:oy + big[1], ox:ox + big[0]] = O[oy:oy + big[1], ox:ox + big[0]] * (1 - mask) + sprite * mask
    print(f"  canine: root at ({cx:.1f}, {rooty:.0f}), {sgn * off:+.1f} px from the middle of the mouth ({mid:.1f}); {k * st[m_][2]:.0f}x{k * st[m_][3]:.0f}")
Image.fromarray(np.clip(O, 0, 255).round().astype(np.uint8)).save(out)
if len(sys.argv) > 7:
    ys, xs = np.where(Op > 0); x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    c = lambda im: cv2.resize(np.clip(im[y0 - 14:y1 + 14, x0 - 14:x1 + 14], 0, 255).astype(np.uint8), None, fx=3, fy=3, interpolation=cv2.INTER_LANCZOS4)
    cv2.imwrite(sys.argv[7], cv2.cvtColor(np.vstack([c(P), c(O)]), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 92])
