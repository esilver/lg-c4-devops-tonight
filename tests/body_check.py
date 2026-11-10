"""body_check.py <dir> : how far the body and the hair really move, measured on the frames body_check.js wrote.

For every moment there are three pictures: body and hair off (r), body on but the hair's spring and the wind off (h),
and everything on (f). Dense optical flow from r to h is what the body adds to the picture; from h to f what the hair
adds on top. The flow is read at a few points (shoulders, chest, the freest hair, the bridge of the nose) and set
against what the engine asked for at that moment, worked out here with the same formula as the mesh's shader. So this
checks the whole chain: the timeline of breaths and postures, the maps, the mesh, the picture.

Also checked: the bottom edge of the picture never moves up or down (it is pinned there; it may slide sideways), and
nothing moves implausibly far or fast.
Writes <dir>/measured.json (the series, for body_plot.py) and prints a summary.   Run with gen/venv6/bin/python."""
import sys, json, numpy as np, cv2
d = sys.argv[1]; D = json.load(open(f"{d}/body.json")); R = D["rows"]; n = len(R); fps = D["fps"]; F = D["face"]; iod = F["iod"]; B = D["body"]
pts = {k: v for k, v in D["pts"].items() if v}; W, H = 1024, 576
dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
gray = lambda pre, i: cv2.cvtColor(cv2.imread(f"{d}/{pre}{i:04d}.jpg"), cv2.COLOR_BGR2GRAY)
def at(flow, p, r=6):
    x, y = int(round(p["x"])), int(round(p["y"])); return np.median(flow[max(0, y - r):y + r + 1, max(0, x - r):x + r + 1].reshape(-1, 2), axis=0)
ease = lambda t: (lambda u: u * u * (3 - 2 * u))(min(1.0, max(0.0, t)))
def asked(p, r, hair=True, body=True):
    """The mesh's own arithmetic (src/news.js, vertex shader) for one point at one moment: returns (dx, dy) in pixels."""
    x, y = p["x"], p["y"]; pinx = ease(x / (0.45 * iod)) * ease((W - x) / (0.45 * iod)); piny = ease((H - y) / (0.5 * iod)); dx = dy = 0.0
    if body:
        wy = B["sy"] + 2.6 * iod; qx, qy = x - F["cx"], y - F["cy"]; u = (x - B["cx"]) / B["r"]
        tx = r["sx"] - r["rot"] * (F["cy"] - wy) - r["rot"] * qy + r["lean"] * qx; ty = r["sy"] + r["rot"] * (F["cx"] - B["cx"]) + r["rot"] * qx + r["lean"] * qy
        ty -= r["lift"] * (0.25 + 0.75 * p["body"]); tx += p["body"] * (r["wide"] * (x - B["cx"]) + r["tw"] * max(0.0, 1 - u * u) * (0.35 + 0.65 * ease((y - B["sy"]) / (1.4 * iod))))
        dx += pinx * tx; dy += piny * ty
    if hair:
        t = r["t"]; ph = x * 0.05 + y * 0.035
        dx += pinx * p["hair"] * r["hx"] + pinx * p["wind"] * (r["wx"] * (0.75 + 0.25 * np.sin(ph * 0.7 - r["ts"] * 3.1)) + r["wa"] * np.sin(ph - r["ts"] * 8.3))
        dy += piny * p["hair"] * r["hy"] + piny * p["wind"] * (r["wy"] * (0.75 + 0.25 * np.sin(ph * 0.7 - r["ts"] * 3.1)) + r["wa"] * 0.5 * np.sin(ph * 1.31 - r["ts"] * 6.1))
    return dx, dy
mb = {k: [] for k in pts}; mh = {k: [] for k in pts}; far = []
for i in range(n):
    r, h, f = gray("r", i), gray("h", i), gray("f", i); fb = dis.calc(r, h, None); fh = dis.calc(h, f, None)
    for k, p in pts.items(): mb[k].append(at(fb, p)); mh[k].append(at(fh, p))
    far.append(float(np.percentile(np.hypot(fb[..., 0] + fh[..., 0], fb[..., 1] + fh[..., 1]), 99.9)))
out = dict(who=D["who"], fps=fps, t=[r["t"] for r in R], air=[r["air"] for r in R], lines=D["lines"], pts=pts, series={})
print(f"{D['who']}: {n} frames at {fps:.0f} a second, eye distance {iod:.0f} px")
print(f"  {'point':10s} {'what':5s}  moved (measured)        asked for             agreement")
for k, p in pts.items():
    for name, m, kw in (("body", np.array(mb[k]), dict(hair=False)), ("hair", np.array(mh[k]), dict(body=False))):
        a = np.array([asked(p, r, **kw) for r in R])
        if np.ptp(a, axis=0).max() < 0.4: continue                 # nothing was asked of this point
        err = np.sqrt(np.mean((m - a) ** 2)); cx = np.corrcoef(m[:, 0], a[:, 0])[0, 1] if np.ptp(a[:, 0]) > 0.4 else float("nan"); cy = np.corrcoef(m[:, 1], a[:, 1])[0, 1] if np.ptp(a[:, 1]) > 0.4 else float("nan")
        print(f"  {k:10s} {name:5s}  x {np.ptp(m[:, 0]):4.1f} px, y {np.ptp(m[:, 1]):4.1f} px    x {np.ptp(a[:, 0]):4.1f} px, y {np.ptp(a[:, 1]):4.1f} px    rms error {err:.2f} px, correlation x {cx:.2f} y {cy:.2f}")
        out["series"][f"{k}.{name}"] = dict(measured=np.round(m, 3).tolist(), asked=np.round(a, 3).tolist())
sh = -(np.array(mb["shoulderL"])[:, 1] + np.array(mb["shoulderR"])[:, 1]) / 2; tt = np.array([r["t"] for r in R])
line = np.searchsorted([l["start"] for l in D["lines"]], tt, side="right"); v = (np.abs(np.diff(sh)) * fps)[np.diff(line) == 0]       # speed within a line; from one line to the next the demo cuts
print(f"  shoulders rise and fall over {np.ptp(sh):.1f} px ({np.ptp(sh) / iod:.3f} eye distances); fastest {v.max():.0f} px a second, typical (median) {np.median(v):.1f}")
hd = np.array(mb["head"]); print(f"  head carried by the body over {np.ptp(hd[:, 0]):.1f} px sideways ({np.ptp(hd[:, 0]) / iod:.2f} eye distances) and {np.ptp(hd[:, 1]):.1f} px up and down")
bt = D["bottom"]; cov = np.array(bt["f"]) / np.maximum(1, np.array(bt["r"]))
print(f"  bottom edge: the figure covers {int(np.median(bt['r']))} px of the picture's bottom row when still, and between {100 * cov.min():.1f}% and {100 * cov.max():.1f}% of that while it moves (it would drop towards 0 if the figure lifted off the edge); furthest any part of the picture is moved: {np.max(far):.1f} px")
json.dump(out, open(f"{d}/measured.json", "w"))
