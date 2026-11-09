"""Every joint swept on its own at a fine step, both ways, without stopping at the first hit.
Usage: python3 fine_sweep.py [step_deg]"""
import sys
import numpy as np
from common import cb
STEP = float(sys.argv[1]) if len(sys.argv) > 1 else 2.5

def run(title, maker):
    parts, joints, info = maker()
    print(f"=== {title}: step {STEP} deg ===")
    for j in joints:
        A = cb.union(parts[n] for n in j["moving"])
        B = cb.union(p for n, p in parts.items() if n not in j["moving"])
        g0 = A.min_gap(B, 2.0)
        res = {}
        for sign in (1, -1):
            first_hit, tight, tight_at, hits = None, 9.0, 0, []
            for a in np.arange(STEP, j["limit"] + 1e-6, STEP):
                T = cb.turn(A, j["axis"], j["point"], sign * a)
                vol = (T ^ B).volume()
                gap = T.min_gap(B, 2.0)
                if vol > 1e-6:
                    hits.append((a, vol))
                    if first_hit is None:
                        first_hit = a
                if a <= j["want"] + 1e-6 and gap < tight:
                    tight, tight_at = gap, a
            res[sign] = (first_hit, tight, tight_at, hits)
        for sign in (1, -1):
            fh, tight, ta, hits = res[sign]
            free = (fh - STEP) if fh is not None else j["limit"]
            worst = max(hits, key=lambda h: h[1]) if hits else None
            print(f"  {j['name']:<16} {'+' if sign>0 else '-'}: free to {free:6.1f} (want {j['want']:g}, limit {j['limit']:g}); "
                  f"first hit {fh}; tightest gap within want {tight:.3f} at {ta:g} deg (as printed {g0:.3f}); "
                  f"hits {len(hits)}" + (f", worst {worst[1]:.3f} mm3 at {worst[0]:g}" if worst else ""))
    print()

run("test strip", cb.make_test)
run("pocket capybara", cb.make_capybara)
