"""video_check.py <video.mp4> : in a finished video of the avatar, do the lips meet when the sound track has a p, b or m?

Nothing here comes from the page. The sound track is taken out of the file and a forced aligner (gen/align.py) finds
where each sound is in it. The frames are taken out of the file and, in each, the open part of the mouth is measured as
the number of pixels in a box round the mouth that are neither skin nor lip (the dark of the mouth, and teeth). Then,
for every p, b and m the aligner hears: how far in time is the nearest frame in which the mouth is shut?
The video's .json (written by avatar/record.js) supplies only the words and sounds of each line, for the aligner.

Run from the repository root:  gen/venv4/bin/python tests/video_check.py demo/avatar-me.mp4 [mouth_x mouth_y half_w half_h]
(the default box is this face's mouth, from a face detector run on one frame: corners at x 334 and 422, y 325)"""
import sys, os, json, subprocess, tempfile, glob, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "gen"))
from PIL import Image
from align import read16k, align, CLS
V = sys.argv[1]; M = json.load(open(V[:-4] + ".json")); FPS = M["fps"]
box = [int(v) for v in sys.argv[2:6]] if len(sys.argv) >= 6 else [378, 328, 46, 24]          # the mouth on the canvas: its middle, half its width and height
with tempfile.TemporaryDirectory() as d:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", V, "-q:v", "2", f"{d}/f_%05d.png"], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", V, "-ar", "24000", "-ac", "1", f"{d}/a.wav"], check=True)
    a, sr, a16 = read16k(f"{d}/a.wav"); gap = []; files = sorted(glob.glob(f"{d}/f_*.png"))
    for f in files:
        im = np.asarray(Image.open(f).convert("HSV").crop((box[0] - box[2], box[1] - box[3], box[0] + box[2], box[1] + box[3]))).astype(int); s, v = im[..., 1], im[..., 2]
        gap.append(int(((v < 95) | ((s < 70) & (v > 150))).sum()))                                # the dark of an open mouth, or teeth
gap = np.array(gap, float); shut = np.percentile(gap, 10) + 0.06 * (np.percentile(gap, 98) - np.percentile(gap, 10))
print(f"{len(gap)} frames; open-mouth pixels: at rest {np.percentile(gap, 10):.0f}, widest {gap.max():.0f}; a frame counts as shut below {shut:.0f}")
off, n, miss = [], 0, []
for L in M["lines"]:
    seg = L["sp"]["seg"]; i0, i1 = int(L["at"] * 16000), int((L["at"] + L["secs"]) * 16000); idx = [q for q, s in enumerate(seg) if s[0] in CLS and s[2] > 0]
    spans, _, _ = align(a16[i0:i1], [seg[q][0] for q in idx])
    for k, q in enumerate(idx):
        if seg[q][0] not in "pbm": continue
        n += 1; mid = L["at"] + (spans[k][0] + spans[k][1]) / 2; fr = np.arange(max(0, int((mid - 0.15) * FPS)), min(len(gap), int((mid + 0.15) * FPS) + 1)); ok = fr[gap[fr] <= shut]
        if len(ok): off.append(float(ok[np.argmin(np.abs((ok + 0.5) / FPS - mid))] + 0.5) / FPS - mid)
        else: miss.append((seg[q][0], round(mid, 2)))
e = np.array(off) * 1000
print(f"the aligner hears {n} p, b and m sounds in the sound track. A frame with the mouth shut is within 150 ms of {len(off)} of them; the nearest such frame is {np.median(np.abs(e)):.0f} ms away (median), within one frame ({1000 / FPS:.0f} ms) for {int((np.abs(e) <= 1000 / FPS).sum())} and within two for {int((np.abs(e) <= 2000 / FPS).sum())}")
if miss: print("no shut frame near:", miss)
