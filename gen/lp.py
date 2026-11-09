"""Face re-posing with the LivePortrait ONNX weights (inference glue written here; weights only, no third-party code).
   A source photo is encoded once; expression offsets on its implicit keypoints give new mouth / eye poses of the same face."""
import json, os, sys, numpy as np, cv2, onnxruntime as ort
from PIL import Image

so = ort.SessionOptions(); so.intra_op_num_threads = 4; so.enable_cpu_mem_arena = False
D = "models/lp/liveportrait_onnx/"
_s = {}
def sess(n):
    if n not in _s: _s[n] = ort.InferenceSession(D + n + ".onnx", so, providers=["CPUExecutionProvider"])
    return _s[n]

def _deg(p):
    e = np.exp(p - p.max(axis=1, keepdims=True)); sm = e / e.sum(axis=1, keepdims=True)
    return float((sm * np.arange(66)).sum(axis=1)[0] * 3 - 97.5)

def _rot(pitch, yaw, roll):
    x, y, z = np.deg2rad([pitch, yaw, roll]); c, s = np.cos, np.sin
    rx = np.array([[1, 0, 0], [0, c(x), -s(x)], [0, s(x), c(x)]]); ry = np.array([[c(y), 0, s(y)], [0, 1, 0], [-s(y), 0, c(y)]])
    rz = np.array([[c(z), -s(z), 0], [s(z), c(z), 0], [0, 0, 1]])
    return (rz @ ry @ rx).T.astype(np.float32)

def crop_affine(lm, scale=5.06, lift=0.07):
    """Square crop around the face, rotated upright: returns crop->frame 2x3 matrix for a 512 crop."""
    eL, eR, mL, mR = (np.array(lm[k], dtype=np.float64) for k in ("eyeL", "eyeR", "mouthL", "mouthR"))
    ec, mc = (eL + eR) / 2, (mL + mR) / 2; iod = np.linalg.norm(eR - eL)
    uy = (mc - ec) / np.linalg.norm(mc - ec); ux = np.array([uy[1], -uy[0]])
    S = scale * iod; ctr = ec + uy * lift * iod; s = S / 512
    return np.array([[ux[0] * s, uy[0] * s, ctr[0] - 256 * s * (ux[0] + uy[0])], [ux[1] * s, uy[1] * s, ctr[1] - 256 * s * (ux[1] + uy[1])]], dtype=np.float64)

class Source:
    def __init__(self, frame_rgb, lm):
        self.frame = frame_rgb; self.A = crop_affine(lm); self.Ainv = cv2.invertAffineTransform(self.A)
        self.crop = cv2.warpAffine(frame_rgb, self.Ainv, (512, 512), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        x = cv2.resize(self.crop, (256, 256), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
        x = x.transpose(2, 0, 1)[None]
        self.f = sess("appearance_feature_extractor").run(None, {"img": x})[0]
        pitch, yaw, roll, t, exp, scale, kp = sess("motion_extractor").run(None, {"img": x})
        self.pitch, self.yaw, self.roll = _deg(pitch), _deg(yaw), _deg(roll)
        self.t, self.exp, self.scale, self.kp = t, exp.reshape(1, 21, 3), scale, kp.reshape(1, 21, 3)
        self.xs = self._kp(self.exp, 0, 0, 0)
    def _kp(self, exp, dp, dy, dr):
        x = (self.kp @ _rot(self.pitch + dp, self.yaw + dy, self.roll + dr) + exp) * self.scale[..., None]
        x[:, :, :2] += self.t[:, None, :2]; return x.astype(np.float32)
    def render(self, aaa=0, eee=0, woo=0, smile=0, blink=0, brow=0, px=0, py=0, pitch=0, yaw=0, roll=0, comp=0.05):
        e = self.exp.copy()
        e[0, 20, 1] += smile * -0.01; e[0, 14, 1] += smile * -0.02; e[0, 17, 1] += smile * 0.0065; e[0, 17, 2] += smile * 0.003
        e[0, 13, 1] += smile * -0.00275; e[0, 16, 1] += smile * -0.00275; e[0, 3, 1] += smile * -0.0035; e[0, 7, 1] += smile * -0.0035
        e[0, 19, 1] += aaa * 0.001; e[0, 19, 2] += aaa * 0.0001; e[0, 17, 1] += aaa * -0.0001
        e[0, 20, 2] += eee * -0.001; e[0, 20, 1] += eee * -0.001; e[0, 14, 1] += eee * -0.001
        e[0, 14, 1] += woo * 0.001; e[0, 3, 1] += woo * -0.0005; e[0, 7, 1] += woo * -0.0005; e[0, 17, 2] += woo * -0.0005
        e[0, 11, 1] += blink * -0.001; e[0, 13, 1] += blink * 0.0003; e[0, 15, 1] += blink * -0.001; e[0, 16, 1] += blink * 0.0003
        if px > 0: e[0, 11, 0] += px * 0.0007; e[0, 15, 0] += px * 0.001
        else: e[0, 11, 0] += px * 0.001; e[0, 15, 0] += px * 0.0007
        e[0, 11, 1] += py * -0.001; e[0, 15, 1] += py * -0.001; brow = brow - py / 2
        if brow > 0: e[0, 1, 1] += brow * 0.001; e[0, 2, 1] += brow * -0.001
        else: e[0, 1, 0] += brow * -0.001; e[0, 2, 0] += brow * 0.001; e[0, 1, 1] += brow * 0.0003; e[0, 2, 1] += brow * -0.0003
        xd = self._kp(e, pitch - aaa * comp, yaw, roll)
        d = sess("stitching").run(None, {"input": np.concatenate([self.xs.reshape(1, 63), xd.reshape(1, 63)], axis=1)})[0]
        xd = xd + d[:, :63].reshape(1, 21, 3); xd[:, :, :2] += d[:, 63:65].reshape(1, 1, 2)
        out = sess("warping_spade").run(None, {"feature_3d": self.f, "kp_driving": xd.astype(np.float32), "kp_source": self.xs})[0]
        return (out[0].transpose(1, 2, 0).clip(0, 1) * 255).round().astype(np.uint8)

if __name__ == "__main__":
    import time
    key = sys.argv[1]; d = f"work/{key}"; meta = json.load(open(f"{d}/meta.json"))
    src = Source(np.asarray(Image.open(f"{d}/frame.png").convert("RGB")), meta["lm"]); os.makedirs(f"{d}/lp", exist_ok=True)
    print("pose", round(src.pitch, 1), round(src.yaw, 1), round(src.roll, 1), "scale", float(src.scale[0, 0]), flush=True)
    Image.fromarray(src.crop).save(f"{d}/lp/src.png")
    tests = [("n", {}), ("a30", dict(aaa=30)), ("a60", dict(aaa=60)), ("a100", dict(aaa=100)), ("e15", dict(eee=15, aaa=20)), ("w15", dict(woo=15, aaa=20)), ("blink", dict(blink=-20)), ("a60nc", dict(aaa=60, comp=0))]
    for n, kw in tests:
        t = time.time(); Image.fromarray(src.render(**kw)).save(f"{d}/lp/t_{n}.png"); print(n, round(time.time() - t, 1), flush=True)
