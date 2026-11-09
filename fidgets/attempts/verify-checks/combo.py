"""Combined poses the design's own check never tries.
 A. each leg swept a full circle (2.5 deg) while the body joints are bent (all 27 combos of -25/0/+25, plus head nod +-15).
 B. all body-joint combos on a 12.5 deg grid (125 poses), pairwise overlap + smallest gap.
"""
import itertools
import numpy as np
from common import cb
parts, joints, info = cb.make_capybara()
J = {j["name"]: j for j in joints}
names = list(parts)
legs = [n for n in names if "leg" in n]

def pair_hits(p):
    out = []
    ks = list(p)
    for i, a in enumerate(ks):
        for b in ks[i + 1:]:
            v = (p[a] ^ p[b]).volume()
            if v > 1e-6:
                out.append((a, b, v))
    return out

print("A. legs through a full circle with the body bent")
worst = {}
for combo in itertools.product((-25, 0, 25), repeat=3):
    base = {f"body joint {i+1}": c for i, c in enumerate(combo)}
    bent = cb.posed(parts, joints, base)
    rest = {n: bent[n] for n in names if n not in legs}
    R = cb.union(rest.values())
    for leg in legs:
        j = J[leg]
        # the leg's own pivot moves with the body: find it by posing a tiny marker
        marker = cb.ball(0.01, *j["point"])
        mk_parts = dict(parts); mk_parts[leg] = marker
        mp = cb.posed(mk_parts, joints, base)[leg]
        bb = mp.bounding_box(); piv = [(bb[0]+bb[3])/2, (bb[1]+bb[4])/2, (bb[2]+bb[5])/2]
        # which body segment carries it, and so the yaw of its axis
        yaw = sum(c for i, c in enumerate(combo)) if leg.startswith("hind") else 0.0
        L0 = parts[leg]
        for a in np.arange(-180, 180, 2.5):
            L = cb.turn(L0, "y", j["point"], a)
            L = cb.posed({**parts, leg: L}, joints, base)[leg]
            v = (L ^ R).volume()
            if v > 1e-6:
                key = (leg, combo)
                worst.setdefault(key, []).append((a, v))
for (leg, combo), hits in sorted(worst.items()):
    angs = [h[0] for h in hits]
    inside = [h for h in hits if abs(h[0]) <= 45 + 1e-6]
    print(f"  {leg:<16} body joints {combo}: hits at leg angles {min(angs):g}..{max(angs):g} ({len(hits)} steps), "
          f"worst {max(h[1] for h in hits):.3f} mm3; inside +-45: {[(a, round(v,4)) for a, v in inside]}")
if not worst:
    print("  no hits")

print("B. body joints on a 12.5 deg grid, head nod and legs at rest")
bad, tight = [], (9.0, None)
for combo in itertools.product((-25, -12.5, 0, 12.5, 25), repeat=3):
    p = cb.posed(parts, joints, {f"body joint {i+1}": c for i, c in enumerate(combo)})
    h = pair_hits(p)
    if h:
        bad.append((combo, h))
    segs = [p[f"body {i+1}"] for i in range(4)]
    for i in range(3):
        g = segs[i].min_gap(segs[i+1], 2.0)
        if g < tight[0]:
            tight = (g, (combo, i + 1))
    for i in range(4):
        for k in range(i + 2, 4):
            g = segs[i].min_gap(segs[k], 2.0)
            if g < tight[0]:
                tight = (g, (combo, f"{i+1}-{k+1}"))
print("  poses with overlap:", len(bad))
for combo, h in bad[:20]:
    print("   ", combo, [(a, b, round(v, 4)) for a, b, v in h])
print(f"  tightest gap between body segments over the grid: {tight[0]:.3f} at {tight[1]}")
