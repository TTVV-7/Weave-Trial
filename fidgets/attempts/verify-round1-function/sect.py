"""Sections through the neck hinge (planes y = const) as printed and at both nod stops."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import cb
parts, joints, info = cb.make_capybara()
cols = {"head": "#c97", "body 1": "#69c", "orange": "#f90", "body 2": "#9c6"}
fig, ax = plt.subplots(3, 3, figsize=(21, 15))
for r, nod in enumerate((0, 18, -18)):
    p = cb.posed(parts, joints, {"head nod": nod})
    for c, y in enumerate((0.0, 1.8, 2.5)):
        a = ax[r, c]
        for n in ("head", "body 1", "orange", "body 2"):
            cs = cb.section_y(p[n], y)
            for poly in cs.to_polygons():
                poly = np.asarray(poly)
                a.fill(poly[:, 0], -poly[:, 1], color=cols[n], alpha=0.75, ec="k", lw=0.5)
        a.plot([cb.NECK_X], [cb.NECK_Z], "k+")
        a.set_xlim(8, 34); a.set_ylim(-1.5, 16.5); a.set_aspect("equal"); a.grid(True, lw=0.3)
        a.set_xticks(np.arange(8, 35, 2)); a.set_yticks(np.arange(0, 17, 2))
        a.set_title(f"nod {nod:+d}, section y = {y}")
fig.tight_layout(); fig.savefig("sect_neck.png", dpi=70)
