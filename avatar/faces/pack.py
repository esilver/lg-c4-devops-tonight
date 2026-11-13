"""pack.py <face> <style> <sway> <hz> <damp> <hair> [jaw=<s>] [tilt=<rad>] [pant=<opening>] [perk=<lift>] : gen/cast_<face>.json -> avatar/faces/<face>.json

The hand-off file for a face that is not one of the bulletin's five:
  {"cast":  the presenter's entry exactly as gen/lpexport3.py wrote it (the shape of assets.json["cast"][name]),
   "style": how much this presenter moves (the engine's STYLE table: 0.85 to 1.25 for the five),
   "body":  {"sway", "hz", "damp", "hair"} (the engine's BODY table: how far the torso drifts, the spring free hair
            hangs on in cycles a second, its damping, and how far it swings; 0 = hair fixed to the head; and, only
            if they are given by name, "jaw": the seconds a heavy jaw's movement is smoothed over, for a muzzle, and
            "tilt": how far, in radians, the head tilts to one side now and then while its owner is not speaking,
            "pant": how far the mouth hangs open, on the scale of speech, while an animal left alone pants, and
            "perk": how far its ears lift, on the scale of the brows, while it is spoken to; see faceAt in src/news.js)}

Run from the repository root:  python3 avatar/faces/pack.py me 1 1 4 0.5 0        (the dog: ... dog 1.1 0.4 4 0.5 0 jaw=0.045 tilt=0.1 pant=0.32 perk=0.65)"""
import json, os, sys
who = sys.argv[1]; style, sway, hz, damp, hair = (float(v) for v in sys.argv[2:7]); more = dict(v.split("=") for v in sys.argv[7:]); assert set(more) <= {"jaw", "tilt", "pant", "perk"}, more; d = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(os.path.dirname(d))
num = lambda v: int(v) if v == int(v) else v
cast = json.load(open(f"{root}/gen/cast_{who}.json"))[who]; ref = json.load(open(f"{root}/assets.json"))["cast"]["paige"]
same = lambda a, b: type(a) is type(b) and (set(a) - {"jg"} == set(b) and all(same(a[k], b[k]) for k in b) if isinstance(a, dict) else True)      # (jg: a mouth may list its smile row's own jaw steps)
assert same(cast, ref), "the entry does not have the shape of assets.json['cast']['paige']"
out = f"{d}/{who}.json"; body = dict(sway=num(sway), hz=num(hz), damp=num(damp), hair=num(hair))
body.update({k: float(v) for k, v in more.items()})
json.dump(dict(cast=cast, style=num(style), body=body), open(out, "w"))
print(f"wrote {os.path.relpath(out, root)}: {os.path.getsize(out) / 1e6:.2f} MB; gain {cast['gain']}, face {cast['face']}, style {num(style)}, body sway {num(sway)} hz {num(hz)} damp {num(damp)} hair {num(hair)}")
