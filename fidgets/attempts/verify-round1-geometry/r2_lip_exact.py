"""Round 2: the lip of each socket, exact: empty space under it against open air above it (manifold min_gap),
taken behind the lip's blunt front face so that the two spaces are separate bodies."""
import numpy as np, manifold3d as mf
from lib import *
def bx(x0, x1, y0, y1, z0, z1):
    return mf.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])
for label, maker in (("full", cb.make_capybara), ("strip", cb.make_test), ("full, no keyring", lambda: cb.make_capybara(loop=False))):
    parts, joints, info = maker()
    for i, at in enumerate(info["axes"]):
        rear = parts[f"body {i + 2}"]
        top = rear.bounding_box()[5]
        for x0 in (cb.X_CUT + 1e-4, cb.X_CUT + 0.05):
            rows = []
            for y0, y1 in ((-8.4, 8.4), (-8.4, -3.0), (-3.0, 3.0), (3.0, 8.4)):
                void = bx(at + x0, at + 10.5, y0, y1, cb.Z_C + 1.0, top + 2) - rear
                ps = void.decompose()
                over = [p for p in ps if p.bounding_box()[5] > top + 1.9]
                under = [p for p in ps if p.bounding_box()[5] <= top + 1.9 and p.volume() > 1e-5]
                if not over or not under:
                    rows.append(f"y {y0:+.1f}..{y1:+.1f}: not separate ({len(under)}/{len(over)})")
                    continue
                g = min(u.min_gap(cb.union(over), 6.0) for u in under)
                rows.append(f"y {y0:+.1f}..{y1:+.1f}: {g:.4f}")
            print(f"{label} joint {i + 1}, from {x0:.4f} behind the axis: " + "; ".join(rows), flush=True)
