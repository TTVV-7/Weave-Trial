"""Render magnet-preview.png: each half-tree from the front, and its flat back with the magnet pockets."""
import numpy as np, trimesh, manifold3d, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Polygon
import make_magnets as mm


def manifold(m):
    return manifold3d.Manifold(manifold3d.Mesh(vert_properties=m.vertices.astype(np.float32),
                                               tri_verts=m.faces.astype(np.uint32)))


fig, ax = plt.subplots(2, 6, figsize=(18, 8.5))
light = np.array([0.35, 0.45, 0.82])
for i, n in enumerate(mm.TREES):
    half = trimesh.load(mm.OUT / f"{n}-half.stl")
    # Front: looking down onto the relief (+z), drawn back to front.
    order = np.argsort(half.triangles[:, :, 2].mean(1))
    shade = np.clip(half.face_normals[order] @ light, 0.15, 1)
    ax[0, i].add_collection(PolyCollection(half.triangles[order][:, :, :2],
                                           facecolors=plt.cm.Greens(0.35 + 0.6 * shade), linewidths=0))
    ax[0, i].set_title(n.replace("-", " ").title())
    # Back: the cut face that sits on the fridge, mirrored as you'd see it from behind.
    for r in manifold(half).slice(0.3).to_polygons():
        ax[1, i].add_patch(Polygon(np.c_[-r[:, 0], r[:, 1]], closed=True, fc="#cfe8cf", ec="k", lw=0.8))
    ax[1, i].set_title("back: magnet pockets", fontsize=9)
    for a in ax[:, i]:
        a.autoscale(); a.set_aspect("equal"); a.axis("off")
fig.tight_layout()
fig.savefig(mm.HERE / "magnet-preview.png", dpi=90)
