"""check_stills.py [face] : the pictures behind a face, to look at, from gen/work/<face>/ -> avatar/faces/check/.

  <face>_frame.jpg     the framed 16:9 picture; under it the same picture with its contrast stretched six times about
                       the backdrop's level at each place where the photograph ends and the continued backdrop begins
                       (red ticks; a seam, a streak or banding would show there)
  <face>_matte.jpg     the matte; the cut-out over dark blue and over green; and its outline drawn on the frame
  <face>_matte_edges.jpg   five stretches of the outline, three times enlarged, over dark blue and over the plate
  <face>_plate.jpg     the plate (the backdrop with the person taken out); stretched six times; and with the outline
                       of the person drawn in, to see whether anything of the person is left
  <face>_regions.jpg   where the page swaps or moves pixels: mouth region red, eye region green, brow band blue;
                       and the body map (green torso, red free hair), as gen/bodymap.py drew it

Run from the repository root:  gen/venv2/bin/python avatar/faces/check_stills.py me"""
import sys, os, json, io, base64, numpy as np, cv2
from PIL import Image
who = sys.argv[1] if len(sys.argv) > 1 else "me"; d = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(os.path.dirname(d)); w = f"{root}/gen/work/{who}"; out = f"{d}/check"; os.makedirs(out, exist_ok=True)
ent = json.load(open(f"{d}/{who}.json"))["cast"]; dec = lambda u: Image.open(io.BytesIO(base64.b64decode(u.split(",")[1])))
frame = np.asarray(Image.open(f"{w}/frame.png").convert("RGB")).astype(np.float32); alpha = np.asarray(Image.open(f"{w}/alpha.png").convert("L"))
fg = np.asarray(dec(ent["fg"]).convert("RGBA")).astype(np.float32); plate = np.asarray(dec(ent["bg"]).convert("RGB")).astype(np.float32); meta = json.load(open(f"{w}/meta.json"))
H, W = alpha.shape; ref = np.median(frame[:, :160].reshape(-1, 3), axis=0); stretch = lambda im: np.clip(128 + 6 * (im - ref), 0, 255)
edge = cv2.Canny(alpha, 50, 150) > 0; over = lambda rgb: fg[..., :3] * fg[..., 3:] / 255 + np.array(rgb, np.float32) * (1 - fg[..., 3:] / 255)
def label(im, text):
    im = np.ascontiguousarray(np.clip(im, 0, 255).astype(np.uint8)); cv2.rectangle(im, (0, 0), (9 + 8 * len(text), 20), (0, 0, 0), -1); cv2.putText(im, text, (5, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1, cv2.LINE_AA); return im
def save(name, im, q=92): Image.fromarray(im).save(f"{out}/{who}_{name}", quality=q); print("wrote", f"check/{who}_{name}")
# the frame, and one stretched copy for each place where the photograph ends (stretched about the backdrop's level there)
seams = [x for pair in meta.get("photo", {}).get("extended", []) for x in pair if 0 < x < W]; tiles = [label(frame, "the frame, 1024 x 576")]
for x in seams or [W // 8]:
    band = frame[:, max(0, x - 30):x + 30][alpha[:, max(0, x - 30):x + 30] == 0]; s = np.clip(128 + 6 * (frame - np.median(band, axis=0)), 0, 255)
    for q in seams: s[26:40, q - 1:q + 1] = (255, 0, 0); s[-14:, q - 1:q + 1] = (255, 0, 0)
    tiles.append(label(s, f"contrast x 6 about the backdrop's level at x = {x}; red ticks: where the photograph ends"))
save("frame.jpg", np.vstack(tiles), 95)
# the matte
on = frame.copy(); on[edge] = (255, 40, 40)
save("matte.jpg", np.vstack([np.hstack([label(np.dstack([alpha] * 3), "matte (BiRefNet-portrait)"), label(over((32, 64, 106)), "the cut-out over dark blue")]), np.hstack([label(over((0, 200, 0)), "over green"), label(on, "the matte's outline on the frame")])]))
ex = (meta["lm"]["eyeL"][0] + meta["lm"]["eyeR"][0]) / 2; ey = (meta["lm"]["eyeL"][1] + meta["lm"]["eyeR"][1]) / 2; I = meta["iod"]; ys, xs = np.where(alpha > 127)
wins = [("top of the hair", ex - 0.2 * I, ys.min() + 0.25 * I), ("left ear and cheek", xs[(ys > ey - 20) & (ys < ey + 60)].min() + 0.35 * I, ey + 0.55 * I), ("right ear and cheek", xs[(ys > ey - 20) & (ys < ey + 60)].max() - 0.35 * I, ey + 0.55 * I),
        ("jaw and neck, left", ex - 0.85 * I, ey + 1.45 * I), ("shoulder, right", ex + 2.2 * I, H - 0.75 * I)]
rows = []
for name, cx, cy in wins:
    x = int(np.clip(cx - 80, 0, W - 160)); y = int(np.clip(cy - 55, 0, H - 110)); big = lambda im: cv2.resize(np.clip(im, 0, 255).astype(np.uint8)[y:y + 110, x:x + 160], (480, 330), interpolation=cv2.INTER_NEAREST)
    rows.append(np.hstack([label(big(over((32, 64, 106))), name + ", over dark blue, x 3"), label(big(fg[..., :3] * fg[..., 3:] / 255 + plate * (1 - fg[..., 3:] / 255)), "over the plate"), label(big(frame), "the frame")]))
save("matte_edges.jpg", np.vstack(rows))
# the plate
po = stretch(plate); po[edge] = (255, 0, 0)
save("plate.jpg", np.vstack([label(plate, "the plate: the backdrop with the person taken out"), label(stretch(plate), "contrast x 6"), label(po, "contrast x 6, with the person's outline drawn in")]), 95)
# the regions and the body map
m = np.asarray(Image.open(f"{w}/lp4/masks.png")).astype(np.float32); vis = frame * 0.55 + m * 0.45; vis[edge] = (255, 255, 0)
save("regions.jpg", np.hstack([label(vis, "mouth region red, eye region green, brow band blue"), label(np.asarray(Image.open(f"{w}/body.jpg").convert("RGB")), "body map: torso green, free hair red; lines: chin, shoulders")]))
