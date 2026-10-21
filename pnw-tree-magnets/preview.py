"""Render magnet-preview.png: each tree from the side, its underside, and its cap."""
import numpy as np, trimesh, manifold3d, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Polygon
import make_magnets as mm


def manifold(m):
    return manifold3d.Manifold(manifold3d.Mesh(vert_properties=m.vertices.astype(np.float32),
                                               tri_verts=m.faces.astype(np.uint32)))


def outline(ax, solid, z, title, fill):
    for r in solid.slice(z).to_polygons():
        ax.add_patch(Polygon(r, closed=True, fc=fill, ec="k", lw=1.2))
    ax.autoscale(); ax.set_aspect("equal"); ax.set_title(title, fontsize=9); ax.tick_params(labelsize=7)


fig, ax = plt.subplots(3, 6, figsize=(18, 10), gridspec_kw={"height_ratios": [1.6, 1, 1]})
for i, n in enumerate(mm.TREES):
    tree = trimesh.load(mm.OUT / f"{n}-tree.stl")
    t = tree.triangles[:, :, [0, 2]]
    shade = np.clip(tree.face_normals @ np.array([0.4, -0.8, 0.45]), 0.15, 1)
    order = np.argsort(tree.triangles[:, :, 1].mean(1))[::-1]
    ax[0, i].add_collection(PolyCollection(t[order], facecolors=plt.cm.Greens(0.35 + 0.6 * shade[order]), linewidths=0))
    ax[0, i].autoscale(); ax[0, i].set_aspect("equal"); ax[0, i].axis("off")
    ax[0, i].set_title(n.replace("-", " ").title())
    outline(ax[1, i], manifold(tree), 0.3, "tree underside: pocket + pin holes", "#cfe8cf")
    cap = manifold(trimesh.load(mm.OUT / f"{n}-cap.stl"))
    outline(ax[2, i], cap, 0.5, "cap", "#e8dccf")
    for r in cap.slice(mm.CAP + 0.5).to_polygons():
        ax[2, i].add_patch(Polygon(r, closed=True, fc="#8b5a2b", ec="k", lw=1))
fig.tight_layout()
fig.savefig(mm.HERE / "magnet-preview.png", dpi=90)
