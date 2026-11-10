"""plot_curve.py [line index] : draw one line's jaw (green) and lip (orange) curves from curves.json, with word boundaries
and stressed syllables (bright dots nod, dim ones do not). Run from tests/output after strip.js; writes curve<N>.png."""
import json, sys
from PIL import Image, ImageDraw
k = int(sys.argv[1]) if len(sys.argv) > 1 else 0; d = json.load(open('curves.json'))[k]; W, H = 1500, 420
im = Image.new('RGB', (W, H), (18, 20, 26)); dr = ImageDraw.Draw(im); X = lambda t: 20 + t / d['dur'] * (W - 40)
for y, lab in [(200, 'open 0'), (40, 'open 1'), (310, 'shape 0')]: dr.line([(20, y), (W - 20, y)], fill=(60, 60, 70)); dr.text((22, y + 2), lab, fill=(120, 120, 130))
n = len(d['o'])
dr.line([(X(i / 60), 200 - d['o'][i] * 160) for i in range(n)], fill=(90, 230, 160), width=2)
dr.line([(X(i / 60), 310 - d['s'][i] * 80) for i in range(n)], fill=(240, 170, 80), width=2)
for t, w in zip(d['wt'], d['words']): dr.line([(X(t), 20), (X(t), 400)], fill=(50, 55, 70)); dr.text((X(t) + 2, 404), w, fill=(200, 200, 210))
for t, w in d['stress']: dr.ellipse([X(t) - 3, 212, X(t) + 3, 218], fill=(255, 80, 80) if w > 0.42 else (120, 60, 60))
im.save(f'curve{k + 1}.png'); print('wrote', f'curve{k + 1}.png')
