import sys, json, numpy as np
from PIL import Image, ImageDraw
from lp import Source
key = sys.argv[1]; d = f"work/{key}"; meta = json.load(open(f"{d}/meta.json"))
src = Source(np.asarray(Image.open(f"{d}/frame.png").convert("RGB")), meta["lm"])
P = [("n", {}), ("a10", dict(aaa=10)), ("a22", dict(aaa=22)), ("a36", dict(aaa=36)), ("a52", dict(aaa=52)), ("a75", dict(aaa=75)),
     ("e6", dict(eee=6)), ("e10", dict(eee=10)), ("e6a22", dict(eee=6, aaa=22)), ("e10a22", dict(eee=10, aaa=22)), ("e10a45", dict(eee=10, aaa=45)), ("am8", dict(aaa=-8)),
     ("w8", dict(woo=8)), ("w14", dict(woo=14)), ("w8a22", dict(woo=8, aaa=22)), ("w14a22", dict(woo=14, aaa=22)), ("w14a45", dict(woo=14, aaa=45)), ("s3", dict(smile=0.3)),
     ("b10", dict(blink=-10)), ("b20", dict(blink=-20)), ("br8", dict(brow=8)), ("br15", dict(brow=15)), ("px8", dict(px=8)), ("pxm8", dict(px=-8))]
S = Image.new("RGB", (6 * 240, 4 * 240))
for k, (n, kw) in enumerate(P):
    im = Image.fromarray(src.render(comp=0, **kw)); im.save(f"{d}/lp/s_{n}.png")
    box = (136, 110, 376, 350) if k >= 18 else (136, 250, 376, 490)
    x, y = (k % 6) * 240, (k // 6) * 240; S.paste(im.crop(box), (x, y)); dr = ImageDraw.Draw(S); dr.rectangle([x, y, x + 60, y + 14], fill=(0, 0, 0)); dr.text((x + 3, y + 1), n, fill=(255, 255, 0))
S.save(f"out/lp_sweep_{key}.jpg", quality=90); print("done")
