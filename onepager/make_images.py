"""make_images.py : gathers, crops and resizes the pictures the one-pager shows -> onepager/img/

Everything comes from files already in the repository (four frames of the video, the presenters' frames, mattes and
plates, the pose renders as they are drawn, the lip-sync network's own picture, the body maps, the measurement chart),
plus three captures:
  node onepager/capture.js                                              -> src/chart.png
  cd tests/output && node ../poses.js paige ../../onepager/src/poses_paige.jpg
  cd tests/output && node ../phoneme_strip.js paige 0 0.3 30 20 ../../onepager/src/phon_paige.jpg
One picture is drawn here: the measured displacement field of a head turn and of a nod, as arrows.
Run from the repository root:  gen/venv6/bin/python onepager/make_images.py"""
import json, base64, numpy as np, cv2
O = "onepager/img/"; KEYS = ["paige", "cy", "dee", "sunny", "mel"]
def save(name, im, q=84): cv2.imwrite(O + name, im, [cv2.IMWRITE_JPEG_QUALITY, q]); return im.shape[1], im.shape[0]
def fit(im, w): return cv2.resize(im, (w, round(im.shape[0] * w / im.shape[1])), interpolation=cv2.INTER_AREA if w < im.shape[1] else cv2.INTER_CUBIC)
out = {}
# four moments of the video itself: the anchor, the reporter, the forecast, the interview
import subprocess
fr4 = []
for t in (8, 36, 62, 84):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(t), "-i", "demo/devops-tonight.mp4", "-frames:v", "1", f"onepager/src/frame_{t}.png"], check=True); fr4.append(cv2.imread(f"onepager/src/frame_{t}.png"))
out["hero.jpg"] = save("hero.jpg", fit(np.vstack([np.hstack(fr4[:2]), np.hstack(fr4[2:])]), 1500), 86)
# the five presenters, as photographed (with the relaxed mouth laid in)
for k in KEYS: out[f"cast_{k}.jpg"] = save(f"cast_{k}.jpg", fit(cv2.imread(f"gen/work/{k}/frame_lp3.png"), 520))
# cutting a person out: photograph, matte, cut-out on a checkerboard, plate
k = "dee"; fr = cv2.imread(f"gen/work/{k}/frame.png"); al = cv2.imread(f"gen/work/{k}/alpha.png", 0); pl = cv2.imread(f"gen/work/{k}/plate3.jpg")
yy, xx = np.mgrid[0:576, 0:1024]; chk = np.where(((xx // 24 + yy // 24) % 2)[..., None] == 0, 52, 78).astype(np.float32) * np.ones((1, 1, 3), np.float32); a = al[..., None].astype(np.float32) / 255
for name, im in (("matte_photo.jpg", fr), ("matte_alpha.jpg", cv2.cvtColor(al, cv2.COLOR_GRAY2BGR)), ("matte_cut.jpg", (fr * a + chk * (1 - a)).astype(np.uint8)), ("matte_plate.jpg", pl)): out[name] = save(name, fit(im, 520))
# every kind of pose the page can make, the lip-sync network's own picture, the mouth frame by frame
out["poses.jpg"] = save("poses.jpg", fit(cv2.imread("onepager/src/poses_paige.jpg"), 1650), 82)
out["w2l.jpg"] = save("w2l.jpg", cv2.imread("gen/out/w2l_proto_paige.jpg"), 86)
out["phon.jpg"] = save("phon.jpg", cv2.imread("onepager/src/phon_paige.jpg"), 86)
# the measured displacement fields as arrows (drawn two and a half times their length so they can be seen)
c = json.load(open("gen/cast3.json"))["paige"]; F = c["flow"]; base = cv2.imread("gen/work/paige/frame_lp3.png")
x0, y0, st, cols, rows = F["x"], F["y"], F["step"], F["cols"], F["rows"]; x1, y1 = min(1024, x0 + cols * st), min(576, y0 + rows * st)
for name, idx, label in (("flow_turn.jpg", 0, "head turned 6 degrees"), ("flow_nod.jpg", 2, "head nodded 5 degrees")):
    s, b64 = F["f"][idx]; v = np.frombuffer(base64.b64decode(b64), np.int8).astype(np.float32).reshape(rows, cols, 2) / s
    im = (base[y0:y1, x0:x1] * 0.5).astype(np.uint8); im = cv2.resize(im, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    for j in range(1, rows, 3):
        for i in range(1, cols, 3):
            dx, dy = v[j, i]
            if dx * dx + dy * dy < 0.36: continue
            p = (int(2 * i * st), int(2 * j * st)); q = (int(p[0] + 5 * dx), int(p[1] + 5 * dy)); cv2.arrowedLine(im, p, q, (166, 230, 46), 2, cv2.LINE_AA, tipLength=0.28)
    out[name] = save(name, fit(im, 640), 86)
# where the body and the loose hair are; one breath; what moves while a line is spoken
for k in ("paige", "dee"):                                    # the maps as the page holds them (8-pixel grid), tinted over the photograph
    B = json.load(open(f"gen/work/{k}/body.json")); fr = cv2.imread(f"gen/work/{k}/frame.png").astype(np.float32) * 0.35; A = cv2.imread(f"gen/work/{k}/alpha.png", 0).astype(np.float32)[..., None] / 255
    m = lambda key: cv2.resize(np.frombuffer(base64.b64decode(B[key]), np.uint8).reshape(B["rows"], B["cols"]).astype(np.float32) / 255, (1024, 576), interpolation=cv2.INTER_CUBIC)[..., None] if key in B else 0
    im = fr + A * (m("b") * np.float32([0, 150, 0]) + m("h") * np.float32([0, 0, 200]) + m("w") * np.float32([200, 0, 0]))
    out[f"body_{k}.jpg"] = save(f"body_{k}.jpg", fit(np.clip(im, 0, 255).astype(np.uint8), 760), 86)
out["breath.jpg"] = save("breath.jpg", fit(cv2.imread("tests/output/body/stills_paige_breath.jpg"), 1650), 86)
for src, name in (("onepager/src/chart.png", "chart.png"), ("tests/output/body/body_paige.png", "motion.png")):
    im = cv2.imread(src); im = fit(im, 1650) if im.shape[1] > 1650 else im; cv2.imwrite(O + name, im, [cv2.IMWRITE_PNG_COMPRESSION, 9]); out[name] = (im.shape[1], im.shape[0])
json.dump(out, open(O + "sizes.json", "w"), indent=1); print({k: v for k, v in out.items()})
