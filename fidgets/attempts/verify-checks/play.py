"""Free play of each part along the six axes: how far it travels before it first touches a neighbour,
and the overlap the design's own 1 mm push sees (its pass mark is 0.001 mm3)."""
import numpy as np
from common import cb
parts, joints, info = cb.make_capybara()
AX = {"+x": (1, 0, 0), "-x": (-1, 0, 0), "+y": (0, 1, 0), "-y": (0, -1, 0), "+z": (0, 0, 1), "-z": (0, 0, -1)}
for n, p in parts.items():
    rest = cb.union(q for k, q in parts.items() if k != n)
    row = []
    for lab, d in AX.items():
        d = np.array(d, float)
        hi = None
        for t in np.arange(0.02, 3.0, 0.02):
            if (p.translate(list(t * d)) ^ rest).volume() > 1e-6:
                hi = t
                break
        if hi is None:
            row.append(f"{lab}: >3"); continue
        bite = (p.translate(list(d)) ^ rest).volume()
        row.append(f"{lab}: {hi:.2f} (bite@1mm {bite:.3f})")
    print(f"{n:<16} " + "  ".join(row))
