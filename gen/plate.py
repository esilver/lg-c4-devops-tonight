"""plate.py [key...] : what is BEHIND each presenter, painted by the image model (request 11). TRIED, NOT USED.

The page uses the simpler plate made in lpexport3.py. This script is kept because the attempt is part of the record:
the three plates it painted are in out/plates_tried/, and docs/15 says why they were set aside (in short: the model
does not reliably carry what is beside the outline across it, and where it does not, the outline of the person shows).

The page draws a presenter as a cut-out over a "plate": the photograph with the person removed. Until now the hole was
closed by smearing the surroundings inwards and blurring the result, which was fine while the figure moved by two or
three pixels. Body and hair now move by a centimetre or two; that uncovers a strip of plate along the outline, and a
smear there shows (worst behind the reporter, whose building has hard edges that stopped dead at his ear).

Here the same Stable Diffusion checkpoint that made the photographs fills the hole: the picture is encoded, the hole
is filled with noise, and the model denoises it while everything outside the hole is held to the original at every
step (the masked DDIM loop in sdlib.py, written for the first lip-sync). The prompt describes only the room or street.
The original pixels outside the hole are kept exactly.

The model does not always carry a line across the edge of the hole (a dark window outside met pale concrete inside,
along the exact outline of the head: a ghost of the person). So just inside the outline the plate is still the old
smear, which does continue whatever is next to it, and it gives way to the painted room over the next 16 pixels.
Only the first few dozen pixels inside the outline are ever seen. Whatever the model invents deeper in is never shown.

Run from gen/:  ./venv/bin/python plate.py            -> work/<key>/plate_gen.png (what the model painted; kept, so the
                                                         blend can be changed without painting again), plate.png and
                                                         plate_cmp.jpg. PLATE_STRENGTH=0.97 lets the model paint freely."""
import sys, os, json, time, numpy as np, cv2
from PIL import Image
from sdlib import load, inpaint
W, H = 1024, 576
SCENE = dict(
    paige="empty television news studio at night, a wide video wall of softly glowing blue and white screens, dark ceiling with a soft light strip, shallow depth of field, out of focus background, nobody there, photograph",
    cy="empty dark network operations room, several monitors with blue and green dashboards glowing in the background, shallow depth of field, out of focus, nobody there, photograph",
    dee="exterior of a modern concrete and glass office building, rows of dark windows between pale concrete bands, overcast daylight, shallow depth of field, out of focus background, nobody there, photograph",
    sunny="empty television studio corner, a plain grey wall with a large dark flat screen mounted on it, soft even light, out of focus background, nobody there, photograph",
    mel="empty home office, wooden bookshelves full of books beside a bright window, an office chair, soft daylight, shallow depth of field, out of focus background, nobody there, photograph")
STRENGTH = float(os.environ.get("PLATE_STRENGTH", "0.65"))       # how far the model may depart from the smear it starts from (see docs/15: at 0.97 it invented a bright panel beside the anchor's hair)
NEG = "person, people, man, woman, face, head, hair, portrait, body, hands, figure, silhouette, mannequin, statue, text, watermark, logo, letters, cartoon, illustration, painting, 3d render"
if __name__ == "__main__":
    keys = sys.argv[1:] or ["paige", "cy", "dee", "sunny", "mel"]; pipe = None
    for key in keys:
        d = f"work/{key}"; t = time.time(); frame = cv2.imread(f"{d}/frame.png"); alpha = cv2.imread(f"{d}/alpha.png", 0)
        hole = cv2.dilate(((alpha > 6) * 255).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)))        # the person and five pixels of safety, as in lpexport3.py
        rough = cv2.inpaint(frame, hole, 7, cv2.INPAINT_TELEA); depth = cv2.distanceTransform(hole, cv2.DIST_L2, 5)
        start = rough.copy(); far = np.clip((depth - 6) / 24, 0, 1)[..., None]; start = (rough * (1 - far) + cv2.GaussianBlur(rough, (0, 0), 14) * far).astype(np.uint8)    # the model starts from the smear, blurred deeper in
        wide = cv2.dilate(hole, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))                                             # repaint a little beyond the hole so the seam is the model's own
        if not os.path.exists(f"{d}/plate_gen.png"):
            pipe = pipe or load("base")
            inpaint(pipe, SCENE[key], Image.fromarray(cv2.cvtColor(start, cv2.COLOR_BGR2RGB)), Image.fromarray(wide), strength=STRENGTH, steps=24, cfg=5.5, seed=11, neg=NEG).save(f"{d}/plate_gen.png")
        gen = cv2.imread(f"{d}/plate_gen.png").astype(np.float32)
        # the model's colours drift a little through its encoder: match them to the photograph in a band just outside the hole
        band = (cv2.dilate(hole, np.ones((41, 41), np.uint8)) > 0) & (hole == 0)
        gen += (frame[band].astype(np.float32).mean(axis=0) - gen[band].mean(axis=0))
        w = np.clip((depth - 4) / 16, 0, 1); w = (w * w * (3 - 2 * w))[..., None]                  # the first pixels inside the outline continue the photograph; the painted room takes over by 20 px in
        plate = np.clip(np.where(hole[..., None] > 0, rough * (1 - w) + gen * w, frame), 0, 255).astype(np.uint8)
        cv2.imwrite(f"{d}/plate.png", plate)
        cnt, _ = cv2.findContours(hole, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); vis = plate.copy(); cv2.drawContours(vis, cnt, -1, (0, 255, 255), 1)
        cv2.imwrite(f"{d}/plate_cmp.jpg", np.hstack([cv2.resize(x, (W // 2, H // 2), interpolation=cv2.INTER_AREA) for x in (frame, rough, plate, vis)]), [cv2.IMWRITE_JPEG_QUALITY, 88])
        print(key, "plate", round(time.time() - t), "s", flush=True)
