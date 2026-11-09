import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFilter

def landmarks(pil):
    """Largest face: dict with eye centres, nose, mouth corners (image coords) and box."""
    img = cv2.cvtColor(np.asarray(pil.convert("RGB")), cv2.COLOR_RGB2BGR); h, w = img.shape[:2]
    det = cv2.FaceDetectorYN.create("models/yunet/face_detection_yunet_2023mar.onnx", "", (w, h), 0.5, 0.3, 50)
    _, faces = det.detect(img)
    if faces is None: return None
    f = max(faces, key=lambda f: f[2] * f[3]); p = f[4:14].reshape(5, 2)
    return dict(box=[float(v) for v in f[:4]], eyeL=p[0].tolist(), eyeR=p[1].tolist(), nose=p[2].tolist(), mouthL=p[3].tolist(), mouthR=p[4].tolist(), score=float(f[14]))

def ellipse_mask(size, cx, cy, rx, ry, blur=0):
    m = Image.new("L", size, 0); ImageDraw.Draw(m).ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255)
    return m.filter(ImageFilter.GaussianBlur(blur)) if blur else m
