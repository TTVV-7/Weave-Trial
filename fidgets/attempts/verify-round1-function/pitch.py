"""Deterministic confirmation of the body joint's up-and-down fold found by slop.py: turn the rear segment
about a crosswise (y) axis by theta and look, on a grid of shifts in x and z, for any place it fits."""
import sys
import numpy as np
from common import cb
parts, joints, info = cb.make_capybara()
at = cb.AXES[0]
ref = [at, 0, 4.0]
M = parts["body 2"] ^ cb.box(at - 14, at + 14, -30, 30, -5, 40)
F = parts["body 1"] ^ cb.box(at - 17, at + 17, -30, 30, -5, 40)
thetas = [float(a) for a in sys.argv[1:]]
for th in thetas:
    T = cb.turn(M, "y", ref, th)
    found = None
    for dz in np.arange(-0.6, 3.61, 0.1):
        for dx in np.arange(-0.6, 2.21, 0.1):
            if (T.translate([dx, 0, dz]) ^ F).volume() < 1e-6:
                found = (round(float(dx), 2), round(float(dz), 2)); break
        if found: break
    # where does the next joint's axis foot (9 mm behind, on the bed) go: + is below the bed plane
    if found:
        x, z = 9.0, -4.0
        a = np.radians(th)
        zz = -x * np.sin(a) + z * np.cos(a) + 4.0 + found[1]
        top = T.translate([found[0], 0, found[1]])
        print(f"theta {th:+.0f} deg about y: fits with shift dx, dz = {found}; the next joint's foot ends at z = {zz:+.2f}; gap to body 1 {top.min_gap(F, 3.0):.3f}", flush=True)
    else:
        print(f"theta {th:+.0f} deg about y: does not fit anywhere on the grid", flush=True)
