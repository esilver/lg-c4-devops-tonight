"""body_stills.py <dir> <out.jpg> [wind] : two moments of a recording made by body_check.js, side by side, and laid over each
other in red and cyan so that what moved between them shows as coloured fringes.

Default: the deepest breath in the recording. Left, just before the presenter breathes in; middle, at the top of that
breath; right, the first in red and the second in cyan. The shoulders and chest are fringed; where nothing moved the
overlay is grey.

With "wind" (the reporter): the strongest gust. Left, that moment with the wind switched off; middle, as shown; right,
the overlay. Enlarged on the hair.                                             Run with gen/venv6/bin/python."""
import sys, json, numpy as np, cv2
d, out = sys.argv[1], sys.argv[2]; wind = len(sys.argv) > 3 and sys.argv[3] == "wind"
D = json.load(open(f"{d}/body.json")); R = D["rows"]; fps = D["fps"]; t = np.array([r["t"] for r in R]); F = D["face"]
line = np.searchsorted([l["start"] for l in D["lines"]], t, side="right")
img = lambda pre, i: cv2.imread(f"{d}/{pre}{i:04d}.jpg")
def overlay(a, b):
    a, b = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY), cv2.cvtColor(b, cv2.COLOR_BGR2GRAY); return np.dstack([b, b, a])      # red = first, cyan = second
def label(im, text):
    cv2.rectangle(im, (0, im.shape[0] - 30), (im.shape[1], im.shape[0]), (0, 0, 0), -1); cv2.putText(im, text, (10, im.shape[0] - 9), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 1, cv2.LINE_AA); return im
if wind:
    i = int(np.argmin([r["wx"] for r in R])); iod = F["iod"]; x0, x1 = int(max(0, F["cx"] - 2.4 * iod)), int(min(1024, F["cx"] + 2.4 * iod)); y0, y1 = 0, int(min(576, F["cy"] + 0.6 * iod))
    crop = lambda im: cv2.resize(im[y0:y1, x0:x1], (640, int(640 * (y1 - y0) / (x1 - x0))), interpolation=cv2.INTER_CUBIC)
    a, b = img("h", i), img("f", i)
    tiles = [label(crop(a), f"{t[i]:.2f} s, wind off"), label(crop(b), f"the same moment, wind on ({-R[i]['wx']:.1f} px gust)"), label(crop(overlay(a, b)), "red: wind off   cyan: wind on")]
else:
    air = np.array([r["air"] for r in R]); best = (0, 0, 0)
    for i in range(len(R)):                                       # the largest rise of the breath within one second, inside one line
        j = min(len(R) - 1, i + int(fps)); k = i + int(np.argmax(air[i:j + 1]))
        if line[k] == line[i] and air[k] - air[i] > best[0]: best = (air[k] - air[i], i, k)
    _, i, k = best; a, b = img("f", i), img("f", k); sm = lambda im: cv2.resize(im, (640, 360), interpolation=cv2.INTER_AREA)
    tiles = [label(sm(a), f"{t[i]:.2f} s, before the breath (lungs {air[i]:.2f})"), label(sm(b), f"{t[k]:.2f} s, breath taken (lungs {air[k]:.2f}, shoulders {R[k]['lift'] - R[i]['lift']:+.1f} px)"), label(sm(overlay(a, b)), "red: before   cyan: after")]
cv2.imwrite(out, np.hstack(tiles), [cv2.IMWRITE_JPEG_QUALITY, 90]); print("wrote", out)
