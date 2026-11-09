"""matte.py <in.png> <alpha_out.png> ...pairs : person matte with BiRefNet"""
import sys, torch, numpy as np
from PIL import Image
from transformers import AutoModelForImageSegmentation
torch.set_num_threads(4)
m = AutoModelForImageSegmentation.from_pretrained("models/birefnet", trust_remote_code=True).eval()
def matte(pil):
    im = pil.convert("RGB"); w, h = im.size
    x = np.asarray(im.resize((1024, 1024), Image.BILINEAR)).astype("float32") / 255
    x = (x - np.array([0.485, 0.456, 0.406], dtype="float32")) / np.array([0.229, 0.224, 0.225], dtype="float32")
    x = torch.from_numpy(x).permute(2, 0, 1)[None]
    with torch.no_grad(): p = m(x)[-1].sigmoid()[0, 0].numpy()
    return Image.fromarray((p * 255).astype("uint8")).resize((w, h), Image.BILINEAR)
a = sys.argv[1:]
for i in range(0, len(a), 2):
    matte(Image.open(a[i])).save(a[i + 1]); print("matte", a[i], flush=True)
