"""Every joint swept on its own at a fine step both ways to its limit, WITHOUT stopping at the first hit,
optionally with a neighbouring pose. Usage: python3 fine_sweep.py step which [pose-json]"""
import sys, json
import numpy as np
from common import cb
STEP = float(sys.argv[1]) if len(sys.argv) > 1 else 2.5
WHICH = sys.argv[2] if len(sys.argv) > 2 else "full"
POSE = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
ONLY = sys.argv[4].split(",") if len(sys.argv) > 4 else None
maker = {"full": cb.make_capybara, "test": cb.make_test, "nolug": lambda: cb.make_capybara(loop=False)}[WHICH]
parts, joints, info = maker()
print(f"=== {WHICH}: step {STEP} deg, other joints {POSE} ===", flush=True)
for j in joints:
    if ONLY and not any(o in j["name"] for o in ONLY):
        continue
    if j["name"] in POSE:
        continue
    rest = cb.union(cb.posed({n: p for n, p in parts.items() if n not in j["moving"]}, joints, POSE).values())
    mine = {n: parts[n] for n in j["moving"]}
    g0 = cb.union(cb.posed(mine, joints, POSE).values()).min_gap(rest, 2.0)
    lim = 180 if j["axis"] == "y" else 90
    for sign in (1, -1):
        first, tight, tight_at, hits, free_after = None, 9.0, 0, [], []
        for a in np.arange(STEP, lim + 1e-6, STEP):
            T = cb.union(cb.posed(mine, joints, dict(POSE, **{j["name"]: sign * a})).values())
            vol = (T ^ rest).volume()
            if vol > 1e-6:
                hits.append((a, vol))
                if first is None:
                    first = a
            else:
                if first is not None:
                    free_after.append(a)
                if a <= j["want"] + 1e-6:
                    gap = T.min_gap(rest, 2.0)
                    if gap < tight:
                        tight, tight_at = gap, a
        free = (first - STEP) if first is not None else lim
        worst = max(hits, key=lambda h: h[1]) if hits else None
        print(f"  {j['name']:<16} {'+' if sign>0 else '-'}: free to {free:6.1f} (want {j['want']:g}); first hit {first}; "
              f"tightest gap within want {tight:.3f} at {tight_at:g} (start {g0:.3f}); hits {len(hits)}"
              + (f", worst {worst[1]:.2f} mm3 at {worst[0]:g}" if worst else "")
              + (f"; FREE AGAIN after first hit at {free_after[:6]}{'...' if len(free_after) > 6 else ''} ({len(free_after)} steps)" if free_after else ""), flush=True)
