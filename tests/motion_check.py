"""motion_check.py <frame prefix> <count> : mean absolute change between consecutive frames, in the mouth region and in a
static background region (grain only). Written for this export; it is the tidied form of an inline check run in the session.
Typical use, from tests/output:   node ../strip.js 7.6 0.016667 100 q   &&   python3 ../motion_check.py q 100
The regions are for Paige's solo shot in the 1024x576 picture."""
import sys, numpy as np
from PIL import Image
pre, n = sys.argv[1], int(sys.argv[2])
def series(box):
    fr = [np.asarray(Image.open(f"{pre}{i}.jpg").crop(box)).astype(np.float32) for i in range(n)]
    return np.array([np.abs(fr[i + 1] - fr[i]).mean() for i in range(n - 1)])
m, g = series((395, 205, 625, 385)), series((40, 80, 270, 260))
print("mouth region      median %.2f  mean %.2f  max %.2f  95th pct %.2f" % (np.median(m), m.mean(), m.max(), np.percentile(m, 95)))
print("static background median %.2f  max %.2f   (film grain alone)" % (np.median(g), g.max()))
print("largest steps at frames", np.argsort(m)[-5:][::-1].tolist())
