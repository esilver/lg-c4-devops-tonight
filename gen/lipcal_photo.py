"""lipcal_photo.py <key> : how far a new face's mouth opens, pose by pose, measured the way lipteach.py measures the five.

lipteach.py's "calib" step, for one face outside the five (one made from a photograph, prep_photo.py), written to
work/<key>/lipcal.json. work/lipcal.json, which the bulletin's lip curves were made from, is read and not touched.
The same landmark network looks at the same softened picture of each pose, so the numbers compare directly: the gap
between the inner lips, the height of the outer lips and the width of the mouth, in eye distances.

Prints the new face next to the five: the opening above "shut" at three jaw settings, and the widths. That is what
JAWK (lpx4.py) and the page's `gain` (lpexport3.py) are judged against.
Run from gen/ after lpexport3.py:  ./venv6/bin/python lipcal_photo.py me"""
import sys, json
from lipteach import Face, measure, landmarks, LP
key = sys.argv[1]; F = Face(key); dense = json.load(open(f"work/{key}/{LP}/dense.json")); JN, JS = dense["jn"], dense["js"]
m = lambda name: measure(landmarks(F.soften(F.pose(name)), F.box), F.iod)
cal = dict(jn=JN, js=JS, n=[measure(landmarks(F.soften(F.base), F.box), F.iod)] + [m(f"d_n{i:02d}") for i in range(1, len(JN))])
for r in ("e1", "e2", "w1", "w2", "sg"): cal[r] = [m(f"d_{r}_{i}") for i in range(len(JS))]
cal["p"] = m("f_p"); cal["sh"] = m("d_sh"); json.dump(cal, open(f"work/{key}/lipcal.json", "w"))
ref = dict(json.load(open("work/lipcal.json"))); ref[key] = cal
print("          opening above shut at jaw 16 / 32 / 60    shut   pressed   width: relaxed  photo  spread  round  smile")
for k, c in ref.items():
    o = [c["n"][i][0] - c["n"][0][0] for i in (4, 7, 11)]
    print(f"{k:8s}  {o[0]:.3f} / {o[1]:.3f} / {o[2]:.3f}                      {c['n'][0][0]:.3f}  {c['p'][0]:.3f}     {c['n'][0][2]:.3f}          {c['sh'][2]:.3f}  {c['e2'][0][2]:.3f}   {c['w2'][0][2]:.3f}  {c['sg'][0][2]:.3f}")
print(f"{key}: opening along the relaxed row (jaw {JN}):", " ".join(f"{v[0]:.3f}" for v in cal["n"]))
