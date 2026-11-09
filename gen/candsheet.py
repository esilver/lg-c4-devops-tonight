import sys, glob, json
from PIL import Image, ImageDraw
key = sys.argv[1]; d = f"work/{key}"; meta = json.load(open(f"{d}/meta.json")); m = meta["mouth"]
fs = sorted(glob.glob(f"{d}/mouth_*.png"))
box = (int(m["cx"] - 150), int(m["cy"] - 120), int(m["cx"] + 150), int(m["cy"] + 120))
tiles = [("base", Image.open(f"{d}/face0r.png").crop(box))] + [(f.split('/')[-1][6:-4], Image.open(f).crop(box)) for f in fs]
cols = 4; rows = (len(tiles) + cols - 1) // cols; S = Image.new("RGB", (cols * 300, rows * 240))
for k, (n, im) in enumerate(tiles):
    x, y = (k % cols) * 300, (k // cols) * 240; S.paste(im, (x, y)); dr = ImageDraw.Draw(S); dr.rectangle([x, y, x + 90, y + 14], fill=(0, 0, 0)); dr.text((x + 3, y + 1), n, fill=(255, 255, 0))
S.save(f"out/cand_{key}_mouth.jpg", quality=90)
e = meta["eyes"]; bx = (int(min(v["cx"] - v["rx"] for v in e) - 30), int(min(v["cy"] - v["ry"] for v in e) - 40), int(max(v["cx"] + v["rx"] for v in e) + 30), int(max(v["cy"] + v["ry"] for v in e) + 40))
fs = [f"{d}/face0r.png"] + sorted(glob.glob(f"{d}/blink_*.png")); ims = [Image.open(f).crop(bx) for f in fs]
S = Image.new("RGB", (ims[0].width, ims[0].height * len(ims)))
for k, im in enumerate(ims): S.paste(im, (0, k * im.height))
S.save(f"out/cand_{key}_blink.jpg", quality=90)
