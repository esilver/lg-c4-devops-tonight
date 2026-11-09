import sys
from PIL import Image
idx = [int(a) for a in sys.argv[2:]]; cols = 2; tw = 512
ims = [Image.open(f'n{i}.jpg').resize((tw, 288), Image.LANCZOS) for i in idx]
m = Image.new('RGB', (cols * tw, 288 * ((len(ims) + 1) // 2)))
for k, im in enumerate(ims): m.paste(im, ((k % cols) * tw, (k // cols) * 288))
m.save(sys.argv[1], quality=90)
