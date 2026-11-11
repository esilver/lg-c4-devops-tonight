"""lpx4.py <key>... : the whole pose set again, around a RELAXED mouth (request 11: "his lips are too tight").

Every presenter was photographed with a closed-lip smile, and until now every mouth pose was that smile plus a jaw
opening: they all talked through a held smile, lips stretched sideways and thin. Worst on the guest, whose smile is
the tightest and whose mouth opened least.

Here the neutral pose is a relaxed mouth: the smile taken partly out and the lips let a little forward. All speech
poses are built on it. The photograph's own expression is kept as the "half smile" pose, so a presenter who is
listening looks exactly as before; the smile lets go when they start to speak and comes back afterwards.
The guest's jaw also travels further for the same setting (his poses went to 60 units; at 90 he is still a believable
open mouth, see docs/15).

Writes work/<key>/lp4/*.png (512 crops, the names lpexport3.py expects), affine.json and dense.json.
Run from gen/:  ./venv2/bin/python lpx4.py mel cy dee sunny paige"""
import sys, json, os, time, numpy as np
from PIL import Image
from lp import Source
JN = [0, 4, 8, 12, 16, 21, 26, 32, 38, 45, 52, 60]          # jaw values along the neutral row (page units)
JS = [0, 5, 10, 16, 22, 30, 38, 48]                          # jaw values along each shaped row
SMILE = 0.38                                                 # the broad smile, measured from the photograph's expression
REST = dict(paige=dict(smile=-0.10, woo=2), cy=dict(smile=-0.20, woo=3), dee=dict(smile=-0.20, woo=3), sunny=dict(smile=-0.20, woo=3), mel=dict(smile=-0.25, woo=4))
REST.update(me=dict(smile=-0.15, woo=3))                     # a face from a photograph (prep_photo.py); chosen from relax_grid_photo.py's sheet
REST.update(paige2=dict(smile=-0.10, woo=2))                 # another photograph (AI-generated): its own expression is barely a smile, so less is taken out; corners turned down from -0.15
JAWK = dict(mel=1.5)                                         # model jaw units per page jaw unit
# The first pose of each shaped row is meant to have the lips together. On some faces spreading the lips, or smiling,
# parts them at jaw 0, so a closure (m, b, p) next to an "ee" or in a smile showed the teeth. For such a face that one
# pose is drawn at a negative jaw value (model units) that presses the lips shut while keeping the row's lip shape.
SHUT = dict(paige2=dict(e1=-14, e2=-18, w1=-6, w2=-6, sg=-14))
for key in sys.argv[1:]:
    d = f"work/{key}"; meta = json.load(open(f"{d}/meta.json")); out = f"{d}/lp4"; os.makedirs(out, exist_ok=True)
    src = Source(np.asarray(Image.open(f"{d}/frame.png").convert("RGB")), meta["lm"]); t = time.time()
    rs, rw = REST[key]["smile"], REST[key]["woo"]; k = JAWK.get(key, 1.0); rest = dict(smile=rs, woo=rw)
    poses = {"f_n": dict(rest), "d_sh": {}}                                                    # relaxed; and the photograph's own expression
    poses.update({f"d_n{i:02d}": dict(rest, aaa=k * a) for i, a in enumerate(JN) if i})
    for i, a in enumerate(JS):
        aj = lambda r: SHUT[key][r] if i == 0 and r in SHUT.get(key, {}) else k * a
        poses[f"d_e1_{i}"] = dict(aaa=aj("e1"), eee=3.5, smile=rs); poses[f"d_e2_{i}"] = dict(aaa=aj("e2"), eee=7, smile=rs)       # spread lips are not pushed forward
        poses[f"d_w1_{i}"] = dict(aaa=aj("w1"), woo=min(15, rw + 6), smile=rs); poses[f"d_w2_{i}"] = dict(aaa=aj("w2"), woo=min(15, rw + 12), smile=rs)
        poses[f"d_sg_{i}"] = dict(aaa=aj("sg"), smile=SMILE)
    poses.update(f_p=dict(rest, aaa=-8), f_half=dict(rest, blink=-9), f_closed=dict(rest, blink=-17), f_gl=dict(rest, px=-7), f_gr=dict(rest, px=7), f_gd=dict(rest, py=-7),
                 f_yawp=dict(rest, yaw=6.0), f_yawn=dict(rest, yaw=-6.0), f_pitp=dict(rest, pitch=5.0), f_pitn=dict(rest, pitch=-5.0), d_browup=dict(rest, brow=13), d_browdn=dict(rest, brow=-12))
    for n, kw in poses.items():
        if not os.path.exists(f"{out}/{n}.png"): Image.fromarray(src.render(comp=0, **kw)).save(f"{out}/{n}.png")
    json.dump(dict(A=src.A.tolist()), open(f"{out}/affine.json", "w"))
    json.dump(dict(jn=JN, js=JS, rows=["e1", "e2", "w1", "w2"], rest=rest, jawk=k, smile=SMILE, shut=SHUT.get(key, {})), open(f"{out}/dense.json", "w")); print(key, len(poses), "poses", round(time.time() - t), "s", flush=True)
