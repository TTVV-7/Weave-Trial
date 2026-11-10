"""Round 2: how far a body joint goes the wrong way, measured independently of the design's tilt_limit().
The rear segment is first yawed (the joint's own wiggle, 0 / 12.5 / 25 deg), then turned about the front
segment's crosswise (y) or lengthwise (x) axis through the joint at z = 4, and at every angle is free to shift
in ALL THREE directions (the design's search holds y at 0 for folds and x at 0 / 0.3 for twists).
Usage: r2_tilt.py joint(1-3) yaw axis sign [max]"""
import sys, itertools
import numpy as np
from common import cb
parts, joints, info = cb.make_capybara()
i, yaw, axis, sign = int(sys.argv[1]), float(sys.argv[2]), sys.argv[3], float(sys.argv[4])
top = float(sys.argv[5]) if len(sys.argv) > 5 else 16.0
at = cb.AXES[i - 1]
ref = [at, 0, 4.0]
F = parts[f"body {i}"] ^ cb.box(at - 17, at + 17, -30, 30, -5, 40)
M = cb.turn(parts[f"body {i + 1}"] ^ cb.box(at - 14, at + 14, -30, 30, -5, 40), "z", [at, 0, 0], yaw)
gx, gy, gz = np.arange(-1.0, 2.61, 0.2), np.arange(-1.0, 1.01, 0.2), np.arange(-1.0, 3.61, 0.2)
last, best, how = (0.0, 0.0, 0.0), 0.0, None
for deg in np.arange(0.5, top + 1e-6, 0.5):
    T = cb.turn(M, axis, ref, sign * deg)
    vol = lambda d: (T.translate([float(c) for c in d]) ^ F).volume()
    near = itertools.product(*[[last[k] + e for e in (0, -0.1, 0.1, -0.2, 0.2)] for k in range(3)])
    found = next((d for d in near if vol(d) < 1e-6), None)
    if found is None:
        vols = sorted((vol(d), d) for d in itertools.product(gx, gy, gz))
        if vols[0][0] < 1e-6:
            found = vols[0][1]
        else:
            fine = np.arange(-0.15, 0.151, 0.05)
            for _, d0 in vols[:6]:
                found = next((tuple(a + b for a, b in zip(d0, e)) for e in itertools.product(fine, fine, fine)
                              if vol(tuple(a + b for a, b in zip(d0, e))) < 1e-6), None)
                if found:
                    break
    if found is None:
        break
    last, best, how = tuple(float(c) for c in found), float(deg), tuple(round(float(c), 2) for c in found)
print(f"joint {i}, yawed {yaw:+g}: turned about {'+' if sign > 0 else '-'}{axis} it still fits at {best:g} deg (shift {how}); "
      f"{'still free at the top of the search' if best >= top else 'nothing fits at ' + format(best + 0.5, 'g')}", flush=True)
