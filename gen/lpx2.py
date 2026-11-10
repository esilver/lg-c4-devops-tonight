"""lpx2.py <key>... : the dense pose set (request 9). The first set had six jaw openings; blending between such widely
spaced poses shows two faint mouths at once. This set has twelve along the neutral row and eight along each of four
shaped rows (half and full spread, half and full round), so neighbouring poses differ by only a pixel or two.
Also stronger brow poses (raised and lowered). Writes work/<key>/lp/d_*.png (512 crops) and dense.json."""
import sys, json, os, time, numpy as np
from PIL import Image
from lp import Source
JN = [0, 4, 8, 12, 16, 21, 26, 32, 38, 45, 52, 60]          # jaw values along the neutral row
JS = [0, 5, 10, 16, 22, 30, 38, 48]                          # jaw values along each shaped row
ROWS = dict(e1=dict(eee=3.5), e2=dict(eee=7), w1=dict(woo=6), w2=dict(woo=12))
for key in sys.argv[1:]:
    d = f"work/{key}"; meta = json.load(open(f"{d}/meta.json")); out = f"{d}/lp"
    src = Source(np.asarray(Image.open(f"{d}/frame.png").convert("RGB")), meta["lm"]); t = time.time()
    poses = {f"n{i:02d}": dict(aaa=a) for i, a in enumerate(JN) if i}
    for r, kw in ROWS.items(): poses.update({f"{r}_{i}": dict(aaa=a, **kw) for i, a in enumerate(JS)})
    poses.update(browup=dict(brow=13), browdn=dict(brow=-12))
    for n, kw in poses.items():
        if not os.path.exists(f"{out}/d_{n}.png"): Image.fromarray(src.render(comp=0, **kw)).save(f"{out}/d_{n}.png")
    json.dump(dict(jn=JN, js=JS, rows=list(ROWS)), open(f"{out}/dense.json", "w")); print(key, len(poses), "poses", round(time.time() - t), "s", flush=True)
