"""parse_test.py <out.jpg> : first look at the face parser: its labels at two crop sizes for each presenter (the tight crop
it was trained on, and one of the whole frame height, which is what finds long hair lying on the chest).
Result: out/face_parse_two_crops.jpg.   Run from gen/:  ./venv6/bin/python parse_test.py out/face_parse_two_crops.jpg"""
import sys, json, numpy as np, cv2, onnxruntime as ort
W, H = 1024, 576
s = ort.InferenceSession("models/parse/bisenet_resnet_34.onnx", providers=["CPUExecutionProvider"])
PAL = np.array([[0,0,0],[255,200,170],[120,80,0],[120,80,0],[0,255,255],[0,255,255],[255,255,0],[200,120,120],[200,120,120],[255,0,255],[255,170,130],[255,0,0],[200,0,0],[200,0,0],[90,160,255],[255,255,255],[0,160,0],[160,0,200],[80,80,80]], np.uint8)[:, ::-1]
def parse(frame, cx, cy, side):
    M = np.array([[512 / side, 0, 256 - cx * 512 / side], [0, 512 / side, 256 - cy * 512 / side]])
    crop = cv2.warpAffine(frame, M, (512, 512), flags=cv2.INTER_AREA if side > 512 else cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    x = (crop[:, :, ::-1].astype(np.float32) / 255 - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
    out = s.run(None, {"input": x.transpose(2, 0, 1)[None].astype(np.float32)})[0][0]
    lab = out.argmax(0).astype(np.uint8)
    full = cv2.warpAffine(lab, cv2.invertAffineTransform(M), (W, H), flags=cv2.INTER_NEAREST, borderValue=255)
    return full
tiles = []
for k in ["paige", "cy", "dee", "sunny", "mel"]:
    f = cv2.imread(f"work/{k}/frame_lp2.png"); m = json.load(open(f"work/{k}/meta.json")); lm = m["lm"]; iod = m["iod"]
    ex = (lm["eyeL"][0] + lm["eyeR"][0]) / 2; ey = (lm["eyeL"][1] + lm["eyeR"][1]) / 2; my = (lm["mouthL"][1] + lm["mouthR"][1]) / 2
    row = []
    for side, cyy in ((4.0 * iod, ey + 0.1 * (my - ey)), (max(576, 6.0 * iod), max(ey, 288 if 6 * iod <= 576 else ey + 0.6 * iod))):
        lab = parse(f, ex, cyy, side); col = PAL[np.minimum(lab, 18)]; col[lab == 255] = (40, 40, 40)
        vis = cv2.addWeighted(f, 0.45, col, 0.55, 0); cv2.putText(vis, f"{k} side {side:.0f}  classes {sorted(set(np.unique(lab).tolist()) - {255})}", (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
        row.append(cv2.resize(vis, (512, 288), interpolation=cv2.INTER_AREA))
    tiles.append(np.hstack(row))
cv2.imwrite(sys.argv[1], np.vstack(tiles), [cv2.IMWRITE_JPEG_QUALITY, 85])
