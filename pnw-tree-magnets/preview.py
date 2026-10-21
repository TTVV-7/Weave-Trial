"""Render magnet-preview.png from the painted 3MFs: each half-tree from the front in
its filament colours, its filaments, and its flat back with the magnet pockets."""
import re, zipfile
import numpy as np, trimesh, manifold3d, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Polygon, Rectangle
import make_magnets as mm


def read_3mf(path):
    """Vertices, triangles, filament index per triangle and filament colours."""
    xml = zipfile.ZipFile(path).read("3D/3dmodel.model").decode()
    v = np.array(re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', xml), float)
    t = re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)" paint_color="([^"]+)"', xml)
    f = np.array([x[:3] for x in t], int)
    k = np.array([mm.PAINT_CODE.index(x[3]) for x in t])
    colours = [c[:7] for c in re.findall(r'<m:color color="([^"]+)"', xml)]
    return v, f, k, colours


fig, ax = plt.subplots(2, 6, figsize=(18, 9), gridspec_kw={"height_ratios": [1.5, 1]})
light = np.array([0.35, 0.45, 0.82])
for i, n in enumerate(mm.TREES):
    v, f, k, colours = read_3mf(mm.OUT / f"{n}-half.3mf")
    mesh = trimesh.Trimesh(v, f, process=False)
    rgb = np.array([[int(c[j:j + 2], 16) / 255 for j in (1, 3, 5)] for c in colours])
    order = np.argsort(mesh.triangles[:, :, 2].mean(1))
    shade = 0.55 + 0.45 * np.clip(mesh.face_normals[order] @ light, 0, 1)
    ax[0, i].add_collection(PolyCollection(mesh.triangles[order][:, :, :2],
                                           facecolors=rgb[k[order]] * shade[:, None], linewidths=0))
    ax[0, i].set_title(n.replace("-", " ").title())
    for j, c in enumerate(colours):    # filament swatches under the tree
        ax[0, i].add_patch(Rectangle((mesh.bounds[0][0] + j * 9, -12), 8, 6, fc=c, ec="k", lw=0.5))
        ax[0, i].text(mesh.bounds[0][0] + j * 9 + 4, -14, f"T{j + 1}", ha="center", va="top", fontsize=7)
    solid = manifold3d.Manifold(manifold3d.Mesh(vert_properties=v.astype(np.float32),
                                                tri_verts=f.astype(np.uint32)))
    for r in solid.slice(0.3).to_polygons():   # back, mirrored as seen from behind
        ax[1, i].add_patch(Polygon(np.c_[-r[:, 0], r[:, 1]], closed=True, fc="#dddddd", ec="k", lw=0.8))
    ax[1, i].set_title("back: magnet pockets", fontsize=9)
    for a in ax[:, i]:
        a.autoscale(); a.set_aspect("equal"); a.axis("off")
fig.tight_layout()
fig.savefig(mm.HERE / "magnet-preview.png", dpi=90)
