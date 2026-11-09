import sys, glob
from PIL import Image, ImageDraw
pat, out = sys.argv[1], sys.argv[2]; cols = int(sys.argv[3]) if len(sys.argv) > 3 else 2; tw = int(sys.argv[4]) if len(sys.argv) > 4 else 512
fs = sorted(glob.glob(pat)); ims = [Image.open(f).convert("RGB") for f in fs]
th = int(tw * ims[0].height / ims[0].width); rows = (len(ims) + cols - 1) // cols
m = Image.new("RGB", (cols * tw, rows * th))
for k, (f, im) in enumerate(zip(fs, ims)):
    x, y = (k % cols) * tw, (k // cols) * th; m.paste(im.resize((tw, th), Image.LANCZOS), (x, y))
    d = ImageDraw.Draw(m); label = f.split('/')[-1].replace('.png', ''); d.rectangle([x, y, x + 8 * len(label) + 6, y + 14], fill=(0, 0, 0)); d.text((x + 3, y + 1), label, fill=(255, 255, 0))
m.save(out, quality=88); print(len(fs))
