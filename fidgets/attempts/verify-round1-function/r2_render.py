"""Round 2: close-ups drawn from the WRITTEN 3MF (read back with preview.read_3mf), to look at the paint edges."""
import sys
sys.path.insert(0, '/home/user/Weave-Trial/fidgets')
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import preview as pv
objs, colours = pv.read_3mf('/home/user/Weave-Trial/fidgets/attempts/joints/pocket-capybara.3mf')
views = [(12, 90, "face", ([0, 0, 8], 10)), (10, 125, "face 3/4", ([4, 0, 9], 12)), (5, 180, "left side: head", ([10, 0, 9], 13)),
         (5, 180, "left side: front paw", ([21, 0, 4], 8)), (5, 180, "left side: hind leg", ([57, 0, 7], 10)), (60, 150, "from above front", ([10, 0, 12], 13)),
         (5, 180, "whole side", None), (20, 150, "three-quarter", None)]
fig, ax = plt.subplots(2, 4, figsize=(28, 13))
for a, (elev, azim, title, close) in zip(ax.flat, views):
    pv.draw(a, objs, colours, elev=elev, azim=azim)
    if close:
        c = pv.view(elev, azim) @ np.array(close[0], float)
        a.set_xlim(c[0] - close[1], c[0] + close[1]); a.set_ylim(c[1] - close[1] * 0.7, c[1] + close[1] * 0.7)
    a.set_title(title, fontsize=13)
fig.tight_layout()
fig.savefig("r2/paint_closeups.png", dpi=70, bbox_inches="tight", facecolor="white")
