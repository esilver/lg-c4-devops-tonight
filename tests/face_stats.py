"""face_stats.py : numbers about how the faces move, from the tracks strip.js writes (tests/output/curves.json).
Lip closures and how long they last, how fast and how often the jaw moves, and how many nods, brow lifts and blinks the
bulletin has. Run from tests/output:   node ../strip.js 5 0.5 1 zz && python3 ../face_stats.py"""
import json, numpy as np
C = json.load(open('curves.json')); durs = []; step = []; rev = []; blinks = 0; total = 0; jmax = []; jtyp = []
for c in C:
    o = np.array(c['o']); p = o < -0.06; i = 0
    while i < len(p):                                   # runs of pressed lips
        if p[i]:
            j = i
            while j < len(p) and p[j]: j += 1
            durs.append((j - i) / 60 * 1000); i = j
        else: i += 1
    sp = o[int(c['t0'] * 60):int(c['t1'] * 60)]; d = np.diff(sp)
    step.append(float(np.abs(sp[2:] - sp[:-2]).max())); rev.append(int(((d[1:] * d[:-1]) < 0).sum()) / max(1e-3, c['t1'] - c['t0']))
    jmax.append(float(o.max())); jtyp.append(float(np.median(sp[sp > 0.03])))
    bl = np.array(c['blink']); blinks += int(((bl[1:] > 0.5) & (bl[:-1] <= 0.5)).sum()); total += c['dur']
durs = np.array(durs)
print(f"lip closures: {len(durs)}; shortest {durs.min():.0f} ms, median {np.median(durs):.0f} ms, longest {durs.max():.0f} ms")
print(f"jaw: widest opening per line {min(jmax):.2f} to {max(jmax):.2f}; typical opening while speaking {min(jtyp):.2f} to {max(jtyp):.2f} (1 = 46 jaw units; the widest pose is 60)")
print(f"jaw: direction changes per second {min(rev):.1f} to {max(rev):.1f}; largest change within one 30 fps frame {max(step):.2f}")
print(f"nods per line {min(len(c['nods']) for c in C)} to {max(len(c['nods']) for c in C)}, {sum(len(c['nods']) for c in C)} in all; brow lifts {sum(len(c['brows']) for c in C)}, peak strength per line {min(max(c['bu']) for c in C):.2f} to {max(max(c['bu']) for c in C):.2f}; brow lowerings {sum(len(c['frowns']) for c in C)}")
print(f"head: turn {min(min(c['yaw']) for c in C):+.2f} to {max(max(c['yaw']) for c in C):+.2f} (1 = 6 degrees), nod {min(min(c['pit']) for c in C):+.2f} to {max(max(c['pit']) for c in C):+.2f} (1 = 5 degrees down), tilt up to {np.degrees(max(max(abs(v) for v in c['roll']) for c in C)):.1f} degrees")
print(f"blinks while speaking: {blinks} in {total:.0f} s = {blinks / total * 60:.0f} a minute; phrases {sum(len(c['phr']) for c in C)}")
