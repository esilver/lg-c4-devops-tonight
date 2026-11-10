"""bodymap.py [key...] : which part of each presenter's picture is body, and which is hair that can swing (request 11).

Until now only the head moved; shoulders and hair were a still photograph. To move them the page needs to know, for
every point of the picture, three things:

  body   0 on the head, 1 on the torso, with the neck in between: the torso breathes, shifts and turns; the head rides on it;
  hair   how free the hair is at that point: 0 on the scalp, rising towards loose ends that hang below the ears or
         stand away from the skull (less where it lies on the shoulders); free hair lags behind the head and swings back;
  wind   for the reporter outdoors: how exposed the hair is (most at the outline).

A face-parsing network (BiSeNet, trained on CelebAMask-HQ; weights only, from facefusion/models-3.0.0 on the Hugging
Face Hub; the glue is written here) labels every pixel as skin, hair, neck, cloth and so on. It is run twice per
presenter: on the usual tight crop of the face, and on a crop of the whole frame height, which is what finds long hair
lying on the chest. The three maps are then built from those labels and from where things are, smoothed, and sampled
on an 8-pixel grid.

Run from gen/:  ./venv6/bin/python bodymap.py          -> work/<key>/body.json and body.jpg (to look at)"""
import sys, json, base64, numpy as np, cv2, onnxruntime as ort
W, H, STEP = 1024, 576, 8
HAIR, CLOTH, NECK, FACE = (17,), (16,), (14, 15), (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13)
WIND = dict(dee=1.0)                                        # who stands outdoors
_s = None
def parse(frame, cx, cy, side):
    """Labels for a square crop of the frame (19 classes), put back in frame coordinates; 255 outside the crop."""
    global _s
    if _s is None: so = ort.SessionOptions(); so.intra_op_num_threads = 2; _s = ort.InferenceSession("models/parse/bisenet_resnet_34.onnx", so, providers=["CPUExecutionProvider"])
    k = 512 / side; M = np.array([[k, 0, 256 - cx * k], [0, k, 256 - cy * k]])
    crop = cv2.warpAffine(frame, M, (512, 512), flags=cv2.INTER_AREA if side > 512 else cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    x = (crop[:, :, ::-1].astype(np.float32) / 255 - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
    lab = _s.run(None, {"input": x.transpose(2, 0, 1)[None].astype(np.float32)})[0][0].argmax(0).astype(np.uint8)
    return cv2.warpAffine(lab, cv2.invertAffineTransform(M), (W, H), flags=cv2.INTER_NEAREST, borderValue=255)
def step(a, b, x): t = np.clip((x - a) / max(1e-6, b - a), 0, 1); return t * t * (3 - 2 * t)
def build(key):
    d = f"work/{key}"; frame = cv2.imread(f"{d}/frame.png"); A = cv2.imread(f"{d}/alpha.png", 0).astype(np.float32) / 255; meta = json.load(open(f"{d}/meta.json")); lm = meta["lm"]; iod = meta["iod"]
    ex = (lm["eyeL"][0] + lm["eyeR"][0]) / 2; ey = (lm["eyeL"][1] + lm["eyeR"][1]) / 2; my = (lm["mouthL"][1] + lm["mouthR"][1]) / 2
    tight = parse(frame, ex, ey + 0.1 * (my - ey), 4.0 * iod); side = max(H, 6.0 * iod); wide = parse(frame, ex, H / 2 if side <= H else ey + 0.6 * iod, side)
    inner = cv2.erode((tight != 255).astype(np.uint8), np.ones((17, 17), np.uint8)) > 0           # trust the tight crop except along its border
    lab = np.where(inner, tight, wide); person = A > 0.3
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); isin = lambda cls: np.isin(lab, cls) & person
    hair, face, neck = isin(HAIR), isin(FACE), isin(NECK)
    col = np.abs(xx - ex) < 0.35 * iod; ychin = float(yy[face & col].max()); below = yy > ychin
    cloth = (isin(CLOTH) & (yy > ey + 0.9 * iod)) | (person & below & ~hair & ~face & ~neck)       # anything of the person below the chin that is not hair or skin is body (arms, clothes outside both crops)
    # where the clothes begin beside the neck (a collar, or the top of the shoulders): with an open neckline the cloth in
    # the middle starts far lower than the shoulders do, so the middle column is not the place to look
    near = isin(CLOTH) & (np.abs(xx - ex) < 1.8 * iod); ycol = float(np.percentile(yy[near], 4)) if near.sum() > 50 else ychin + 0.4 * iod
    ycol = float(np.clip(ycol, ychin - 0.3 * iod, ychin + 0.9 * iod))
    # ── body: where a point is decides it (the neck is the hinge); cloth is body wherever it is, skin of the face never
    bpos = step(min(ychin, ycol) - 0.05 * iod, max(ychin, ycol) + 0.35 * iod, yy); body = np.where(face, 0, np.where(cloth, 1, bpos)).astype(np.float32)
    blur = lambda m, s: cv2.GaussianBlur((m * A).astype(np.float32), (0, 0), s * iod) / np.maximum(cv2.GaussianBlur(A, (0, 0), s * iod), 1e-3)        # smoothed inside the cut-out only
    body = blur(body, 0.12)
    # ── hair: free where it hangs below the ears, and (less) where it stands away from the skull
    skull = (((xx - ex) / (1.15 * iod)) ** 2 + ((yy - (ey - 0.3 * iod)) / (1.5 * iod)) ** 2 < 1) | cv2.dilate(face.astype(np.uint8), np.ones((3, 3), np.uint8), iterations=max(1, int(0.06 * iod))).astype(bool)
    away = cv2.distanceTransform((~skull).astype(np.uint8), cv2.DIST_L2, 5)
    hang = step(ey + 0.25 * iod, ey + 1.75 * iod, yy); puff = 0.45 * np.clip(away / (0.45 * iod), 0, 1)
    free = blur(np.where(hair, np.maximum(hang, puff) * (1 - 0.45 * bpos), 0).astype(np.float32), 0.07)      # hair that lies on the shoulders is held by them: it swings about half as far
    # ── wind: hair far from the face and near the outline catches it
    wind = np.zeros((H, W), np.float32)
    if WIND.get(key):
        fromface = cv2.distanceTransform((~face).astype(np.uint8), cv2.DIST_L2, 5); toedge = cv2.distanceTransform(person.astype(np.uint8), cv2.DIST_L2, 5)
        wind = blur(np.where(hair, np.clip(fromface / (0.5 * iod), 0.15, 1) * (0.55 + 0.45 * np.clip(1 - toedge / (0.3 * iod), 0, 1)), 0).astype(np.float32) * WIND[key], 0.06)
    # ── the torso's own measurements: its middle, the shoulder line, half the shoulder width
    ysh = ycol + 0.5 * iod; band = person & (np.abs(yy - (ysh + 0.4 * iod)) < 0.25 * iod); xs = xx[band]
    cx = float(np.clip(np.median(xs), ex - 0.8 * iod, ex + 0.8 * iod)) if len(xs) else ex; r = float(np.clip(np.percentile(np.abs(xs - cx), 92), 1.2 * iod, 4 * iod)) if len(xs) else 2 * iod
    gy = np.minimum(np.arange(0, H + 1, STEP), H - 1); gx = np.minimum(np.arange(0, W + 1, STEP), W - 1)
    enc = lambda m: base64.b64encode(np.round(np.clip(cv2.GaussianBlur(m, (0, 0), STEP / 3)[gy][:, gx], 0, 1) * 255).astype(np.uint8).tobytes()).decode()
    out = dict(step=STEP, cols=len(gx), rows=len(gy), cx=round(cx, 1), sy=round(ysh, 1), r=round(r, 1), chin=round(ychin, 1), b=enc(body), h=enc(free))
    if WIND.get(key): out["w"] = enc(wind)
    json.dump(out, open(f"{d}/body.json", "w"))
    vis = (frame * 0.35).astype(np.float32); vis[..., 1] += 150 * body * A; vis[..., 2] += 200 * free; vis[..., 0] += 200 * wind
    vis = np.clip(vis, 0, 255).astype(np.uint8); cv2.line(vis, (0, int(ysh)), (W, int(ysh)), (255, 255, 255), 1); cv2.line(vis, (0, int(ychin)), (W, int(ychin)), (0, 255, 255), 1)
    cv2.line(vis, (int(cx - r), int(ysh) + 20), (int(cx + r), int(ysh) + 20), (255, 255, 0), 2); cv2.circle(vis, (int(cx), int(ysh) + 20), 5, (255, 255, 0), -1)
    cv2.imwrite(f"{d}/body.jpg", vis, [cv2.IMWRITE_JPEG_QUALITY, 88])
    print(f"{key}: chin {ychin:.0f}, collar {ycol:.0f}, shoulders {ysh:.0f}, middle {cx:.0f} (eyes {ex:.0f}), half width {r:.0f} px = {r / iod:.2f} eye distances; hair {100 * hair.sum() / person.sum():.0f}% of the cut-out, free hair (>0.5) {100 * (free > 0.5).sum() / max(1, hair.sum()):.0f}% of the hair", flush=True)
if __name__ == "__main__":
    for key in (sys.argv[1:] or ["paige", "cy", "dee", "sunny", "mel"]): build(key)
