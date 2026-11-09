"""matte_onnx.py <model: modnet|birefnet> <in.png> <alpha_out.png> [more pairs]  -- weights-only ONNX inference"""
import sys, numpy as np, onnxruntime as ort
from PIL import Image
which = sys.argv[1]
so = ort.SessionOptions(); so.intra_op_num_threads = 4; so.enable_cpu_mem_arena = False
if which == "modnet":
    s = ort.InferenceSession("models/modnet/onnx/model.onnx", so, providers=["CPUExecutionProvider"])
    def matte(im):
        w, h = im.size; sc = 672 / min(w, h); W, H = int(round(w * sc / 32)) * 32, int(round(h * sc / 32)) * 32
        x = (np.asarray(im.resize((W, H), Image.BILINEAR)).astype("float32") / 255 - 0.5) / 0.5
        p = s.run(None, {s.get_inputs()[0].name: x.transpose(2, 0, 1)[None]})[0][0, 0]
        return Image.fromarray((p.clip(0, 1) * 255).astype("uint8")).resize((w, h), Image.BILINEAR)
else:
    s = ort.InferenceSession("models/birefnet_onnx/onnx/model.onnx", so, providers=["CPUExecutionProvider"])
    def matte(im):
        w, h = im.size
        x = np.asarray(im.resize((1024, 1024), Image.BILINEAR)).astype("float32") / 255
        x = (x - np.array([0.485, 0.456, 0.406], dtype="float32")) / np.array([0.229, 0.224, 0.225], dtype="float32")
        p = s.run(None, {s.get_inputs()[0].name: x.transpose(2, 0, 1)[None]})[-1][0, 0]
        p = 1 / (1 + np.exp(-p)) if (p.min() < -0.01 or p.max() > 1.01) else p
        return Image.fromarray((p.clip(0, 1) * 255).astype("uint8")).resize((w, h), Image.BILINEAR)
a = sys.argv[2:]
for i in range(0, len(a), 2):
    matte(Image.open(a[i]).convert("RGB")).save(a[i + 1]); print("matte", a[i], flush=True)
