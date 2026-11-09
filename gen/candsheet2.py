import sys, json
from PIL import Image, ImageDraw
key = sys.argv[1]; names = sys.argv[2:]; d = f"work/{key}"; m = json.load(open(f"{d}/meta.json"))["mouth"]
box = (int(m["cx"] - 150), int(m["cy"] - 120), int(m["cx"] + 150), int(m["cy"] + 120))
S = Image.new("RGB", (len(names) * 300, 240))
for k, n in enumerate(names):
    S.paste(Image.open(f"{d}/mouth_{n}.png").crop(box), (k * 300, 0)); dr = ImageDraw.Draw(S); dr.rectangle([k * 300, 0, k * 300 + 60, 14], fill=(0, 0, 0)); dr.text((k * 300 + 3, 1), n, fill=(255, 255, 0))
S.save(f"out/cand2_{key}.jpg", quality=90)
