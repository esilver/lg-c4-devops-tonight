"""body_plot.py <dir> <out.png> [seconds] : one picture of what moves while a presenter speaks, from the files that
body_check.js and body_check.py wrote in <dir>.

Six small charts on one time axis, because the measures have different scales (never two scales on one chart):
the mouth and the breath as the engine asks for them, then the shoulders, the chest and the loosest hair as MEASURED
on the rendered frames by optical flow. Stretches of speech are shaded. Colours follow what is moving: blue the mouth,
green the body, orange the hair (the three series colours of the demo page, checked there for colour-blind separation
and contrast on this surface). Run with gen/venv6/bin/python."""
import sys, json, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
d, out = sys.argv[1], sys.argv[2]; D = json.load(open(f"{d}/body.json")); M = json.load(open(f"{d}/measured.json")); R = D["rows"]; S = M["series"]
SURF, LINE, INK, MUTED, BLUE, ORANGE, GREEN = "#20262e", "#343d49", "#ece9e2", "#9aa4b0", "#3987e5", "#d95926", "#199e70"
NAMES = dict(paige="Paige Duty", cy="Cy Dekar", dee="Dee Ploy", sunny="Sunny Uptime", mel="Y. A. Mel")
t = np.array([r["t"] for r in R]); tmax = float(sys.argv[3]) if len(sys.argv) > 3 else float(t[-1]); keep = t <= tmax; t = t[keep]
ser = lambda name, k: np.array(S[name]["measured"])[keep][:, k]
lanes = [("Mouth opening (0 closed, 1 wide; below 0 the lips are pressed)", BLUE, np.array([r["o"] for r in R])[keep], [0, 1], "asked"),
         ("Breath: how full the lungs are (0 to 1)", GREEN, np.array([r["air"] for r in R])[keep], [0, 1], "asked"),
         ("Shoulders: how far up, in pixels", GREEN, -(ser("shoulderL.body", 1) + ser("shoulderR.body", 1)) / 2, None, "measured"),
         ("Chest: how far to the right, in pixels", GREEN, ser("chest.body", 0), None, "measured")]
hair = "gust.hair" if "gust.hair" in S else "tip.hair" if "tip.hair" in S else None
if hair:
    what = "Hair in the wind" if hair.startswith("gust") else "Loose hair against the head"
    lanes += [(f"{what}: how far to the right, in pixels", ORANGE, ser(hair, 0), None, "measured"), (f"{what}: how far down, in pixels", ORANGE, ser(hair, 1), None, "measured")]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9.5})
fig, axes = plt.subplots(len(lanes), 1, figsize=(11, 1.25 * len(lanes) + 1.5), sharex=True, facecolor=SURF, gridspec_kw=dict(hspace=0.62))
spans = [(l["start"] + p[0], l["start"] + p[1]) for l in D["lines"] for p in l["phr"] if l["start"] + p[0] < tmax]
cuts = [l["start"] for l in D["lines"][1:] if l["start"] < tmax]
for ax, (title, colour, y, fixed, kind) in zip(axes, lanes):
    ax.set_facecolor(SURF)
    for a, b in spans: ax.axvspan(a, min(b, tmax), color=INK, alpha=0.055, lw=0)                 # she is speaking
    for c in cuts: ax.axvline(c, color=MUTED, lw=1)
    ax.axhline(0, color=LINE, lw=1); ax.plot(t, y, color=colour, lw=2, solid_capstyle="round", solid_joinstyle="round")
    lo, hi = (fixed[0], fixed[1]) if fixed else (min(0, float(y.min())), max(0, float(y.max())))
    pad = 0.12 * (hi - lo or 1); ax.set_ylim(lo - pad - (0.16 if fixed and lo == 0 and y.min() < 0 else 0), hi + pad)
    ext = sorted((round(float(y.min())), round(float(y.max()))), key=abs)                         # label the larger extreme, and the other only where it is clear of zero
    ticks = [0, 1] if fixed else sorted({0, ext[1]} | ({ext[0]} if abs(ext[0]) >= 0.35 * (hi - lo) else set())); ax.set_yticks(ticks); ax.set_yticklabels([f"{v:g}" for v in ticks], color=MUTED)
    ax.set_title(title + ("" if kind == "asked" else "  (measured on the frames)"), loc="left", color=INK, fontsize=9.5, pad=4)
    for s in ax.spines.values(): s.set_visible(False)
    ax.tick_params(axis="both", length=0, colors=MUTED); ax.set_xlim(0, tmax)
axes[-1].set_xlabel("seconds", color=MUTED); axes[-1].set_xticks(np.arange(0, tmax + 0.01, 1 if tmax <= 16 else 2))
if cuts: axes[0].annotate("next line: a cut", (cuts[0], axes[0].get_ylim()[1]), xytext=(4, -2), textcoords="offset points", color=MUTED, fontsize=8.5, va="top")
if spans: axes[0].annotate("shaded: speaking", (spans[0][0], axes[0].get_ylim()[1]), xytext=(3, -2), textcoords="offset points", color=MUTED, fontsize=8.5, va="top")
fig.suptitle(f"{NAMES.get(D['who'], D['who'])}: what moves while the line is spoken", x=0.062, y=0.99, ha="left", color=INK, fontsize=13, fontweight="bold")
fig.text(0.062, 0.935, "Blue: the mouth.  Green: the body.  Orange: loose hair.  Mouth and breath are what the engine asks for; the rest is read off the rendered picture.", color=MUTED, fontsize=9)
fig.subplots_adjust(left=0.062, right=0.985, top=0.87, bottom=0.075)
fig.savefig(out, dpi=150, facecolor=SURF); print("wrote", out)
