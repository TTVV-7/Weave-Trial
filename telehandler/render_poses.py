"""Side view of each pose from the cab side, one row, for a quick look."""
import sys, numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import gth1056 as g

poses = list(g.POSES.items())
fig, axs = plt.subplots(1, len(poses), figsize=(5*len(poses), 6))
L = np.array([0.3, 0.8, 0.5]); L /= np.linalg.norm(L)
for ax, (tag, (ang, ext)) in zip(axs, poses):
    polys, cols, depth = [], [], []
    for _, w, c in g.chassis() + g.boom(ang, ext) + g.lift_cylinder(ang):
        v, t = w.val().tessellate(25, 0.3)
        v = np.array([(p.x, p.y, p.z) for p in v]); t = np.array(t)
        tri = v[t]; n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
        keep = n[:, 1] > -0.05                       # faces toward the viewer at +Y
        rgb = np.array(c.toTuple()[:3])
        sh = 0.4 + 0.6*np.clip(n[keep] @ L, 0, 1)
        polys += list(tri[keep][:, :, [0, 2]]); cols += list(rgb*sh[:, None]); depth += list(tri[keep][:, :, 1].mean(1))
    o = np.argsort(depth)
    ax.add_collection(PolyCollection([polys[i] for i in o], facecolors=[cols[i] for i in o], edgecolors="none"))
    ax.set_xlim(-1000, 12000); ax.set_ylim(0, 17500); ax.set_aspect("equal"); ax.axis("off")
    ax.axhline(0, color="0.5", lw=1)
    ax.set_title(f"{tag}\nboom {ang}°, extended {ext/1000:g} m", fontsize=10)
plt.savefig(sys.argv[1], dpi=80, bbox_inches="tight")
