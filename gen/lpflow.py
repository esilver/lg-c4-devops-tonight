"""lpflow.py [key...] : does moving the neutral face by a measured displacement field reproduce a real head turn?
For each of the four head poses (turned right/left, nodded down/up) the dense optical flow from the neutral render to the
posed render says where every pixel of the face goes. This script warps the neutral render by that field and prints how
much of the difference to the posed render is left over, and saves a side-by-side preview (out/flow_<key>.jpg: neutral,
warped neutral, real render). It is the test that justified the approach; lpexport2.py computes the fields the page uses."""
import sys, json, os, math
import cv2, numpy as np
from PIL import Image
W, H = 1024, 576
POSES = ["yawp", "yawn", "pitp", "pitn"]
def run(key):
    d = f"work/{key}"; meta = json.load(open(f"{d}/meta.json")); aff = json.load(open(f"{d}/lp/affine.json")); A = np.array(aff["A"])
    iod = meta["iod"]; sc = math.sqrt(abs(np.linalg.det(A[:, :2]))); alpha = np.asarray(Image.open(f"{d}/alpha.png").convert("L")).astype(np.float32) / 255
    def toframe(name):
        im = np.asarray(Image.open(f"{d}/lp/f_{name}.png").convert("RGB")); M = A.copy()
        if sc < 0.92: im = cv2.resize(im, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA); M[:, :2] /= sc
        return cv2.warpAffine(im, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    valid = cv2.warpAffine(np.full((512, 512), 255, np.uint8), A, (W, H), flags=cv2.INTER_NEAREST) > 0
    k = max(3, int(0.25 * iod)) | 1
    inside = cv2.erode(valid.astype(np.uint8), np.ones((k, k), np.uint8)).astype(np.float32)          # fade to nothing before the crop's edge
    person = cv2.dilate((alpha > 0.1).astype(np.uint8), np.ones((9, 9), np.uint8)).astype(np.float32)   # the background plate does not move
    wgt = cv2.GaussianBlur(inside * person, (0, 0), 0.12 * iod)
    n = toframe("n"); gn = cv2.cvtColor(n, cv2.COLOR_RGB2GRAY); dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); nose = {}; face = (slice(int(meta["lm"]["eyeL"][1] - 0.9 * iod), int(meta["lm"]["eyeL"][1] + 2.0 * iod)), slice(int(meta["lm"]["eyeL"][0] - 0.7 * iod), int(meta["lm"]["eyeR"][0] + 0.7 * iod)))
    for p in POSES:
        r = toframe(p); F = dis.calc(gn, cv2.cvtColor(r, cv2.COLOR_RGB2GRAY), None)
        F = cv2.GaussianBlur(F, (0, 0), 0.06 * iod) * wgt[..., None]
        # how well does moving the neutral picture by this field reproduce the posed render? (backward map by fixed point)
        bx, by = xx - F[..., 0], yy - F[..., 1]
        for _ in range(3):
            fx = cv2.remap(F[..., 0], bx, by, cv2.INTER_LINEAR); fy = cv2.remap(F[..., 1], bx, by, cv2.INTER_LINEAR); bx, by = xx - fx, yy - fy
        w = cv2.remap(n, bx, by, cv2.INTER_LINEAR)
        before = np.abs(n.astype(np.float32) - r)[face].mean(); after = np.abs(w.astype(np.float32) - r)[face].mean()
        ex = (meta["lm"]["eyeL"][0] + meta["lm"]["eyeR"][0]) / 2; ey = (meta["lm"]["eyeL"][1] + meta["lm"]["eyeR"][1]) / 2
        c = F[int(ey + 0.2 * iod):int(ey + 0.8 * iod), int(ex - 0.3 * iod):int(ex + 0.3 * iod)]; nose[p] = (float(c[..., 0].mean()), float(c[..., 1].mean()))
        mag = np.hypot(F[..., 0], F[..., 1]); print(f"{key} {p}: largest movement {mag.max():.1f} px, face change {before:.1f} -> left over after warp {after:.1f}", flush=True)
        if p == "yawp": Image.fromarray(np.hstack([n, w, r])[face[0], :]).save(f"out/flow_{key}.jpg", quality=88)
    # name the fields by what they do on screen: which pose carries the nose right, which down
    right, left = ("yawp", "yawn") if nose["yawp"][0] > nose["yawn"][0] else ("yawn", "yawp")
    down, up = ("pitp", "pitn") if nose["pitp"][1] > nose["pitn"][1] else ("pitn", "pitp")
    print(f"{key}: right={right} ({nose[right][0]:+.1f} px at the nose), down={down} ({nose[down][1]:+.1f} px)", flush=True)
if __name__ == "__main__":
    for key in sys.argv[1:] or ["paige", "cy", "dee", "sunny", "mel"]:
        if os.path.exists(f"work/{key}/lp/f_pitn.png"): run(key)
