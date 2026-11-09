"""Render preview images from the painted 3MFs, in their filament colours.

    python3 preview.py        (needs trimesh, matplotlib)

Writes stl/basketball-gyro.png, stl/basketball-spinner.png and preview.png
(both fidgets side by side, plus the gyro opened up to show it spins).
"""
import re
import zipfile
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import make_fidgets as mk

LIGHT = np.array([-0.3, -0.5, 0.8]) / np.linalg.norm([-0.3, -0.5, 0.8])


def read_3mf(path):
    """[(vertices, faces, filament index per face)] for each object, placed."""
    xml = zipfile.ZipFile(path).read("3D/3dmodel.model").decode()
    colours = [c[:7] for c in re.findall(r'<m:color color="([^"]+)"', xml)]
    items = dict(re.findall(r'<item objectid="(\d+)" transform="[^"]*? ([-\d.]+ [-\d.]+) 0"', xml))
    objs = []
    for oid, body in re.findall(r'<object id="(\d+)" type="model"><mesh>(.*?)</mesh>', xml):
        v = np.array(re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', body), float)
        t = re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)" paint_color="([^"]+)"', body)
        fc = np.array([x[:3] for x in t], int)
        k = np.array([mk.PAINT_CODE.index(x[3]) for x in t])
        ox, oy = map(float, items.get(oid, "0 0").split())
        objs.append((v + [ox, oy, 0], fc, k))
    return objs, colours


def view(elev, azim):
    """Rotation taking world coords to (screen x, screen y, depth towards viewer)."""
    e, a = np.radians(elev), np.radians(azim)
    rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    rx = np.array([[1, 0, 0], [0, np.cos(e - np.pi / 2), -np.sin(e - np.pi / 2)],
                   [0, np.sin(e - np.pi / 2), np.cos(e - np.pi / 2)]])
    return rx @ rz


def draw(ax, meshes, colours, elev=35, azim=-30):
    rgb = np.array([[int(c[j:j + 2], 16) / 255 for j in (1, 3, 5)] for c in colours])
    R = view(elev, azim)
    polys, cols, depth = [], [], []
    for v, f, k in meshes:
        m = trimesh.Trimesh(v, f, process=False)
        n = m.face_normals
        tri = m.triangles @ R.T
        nv = n @ R.T
        keep = nv[:, 2] > 0                       # back faces culled
        shade = 0.45 + 0.55 * np.clip(n[keep] @ LIGHT, 0, 1)
        polys.append(tri[keep][:, :, :2])
        cols.append(np.clip(rgb[k[keep]] * shade[:, None] + 0.04, 0, 1))
        depth.append(tri[keep][:, :, 2].mean(1))
    polys, cols, depth = np.concatenate(polys), np.concatenate(cols), np.concatenate(depth)
    o = np.argsort(depth)
    ax.add_collection(PolyCollection(polys[o], facecolors=cols[o], edgecolors=cols[o], linewidths=0.15))
    ax.autoscale()
    ax.set_aspect("equal")
    ax.axis("off")


def components(faces, n_verts):
    """Label each face with its connected body (union-find over shared vertices)."""
    parent = np.arange(n_verts)

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for a, b, c in faces:
        ra, rb, rc = root(a), root(b), root(c)
        parent[rb] = ra
        parent[root(rc)] = ra
    return np.array([root(a) for a in faces[:, 0]])


def gyro_opened(objs):
    """The gyro mid-spin: each pivot turned so the rings stand at angles."""
    v, f, k = objs[0]
    centre = np.array([0, 0, (v[:, 2].min() + v[:, 2].max()) / 2])
    body = components(f, len(v))
    ids = sorted(set(body), key=lambda b: np.abs(v[f[body == b]] - centre).max())
    angles = [70, 45, 35, 25]          # ball about x, ring 1 about y, ring 2 about x, ...
    vv = v - centre
    out = []
    for i, b in enumerate(ids):        # inside out: the ball, then each ring
        sel = body == b
        w = vv.copy()
        for p in range(i, len(angles)):   # part i turns with every pivot outside it
            axis = [1, 0, 0] if p % 2 == 0 else [0, 1, 0]
            w = w @ trimesh.transformations.rotation_matrix(np.radians(angles[p]), axis)[:3, :3].T
        out.append((w + centre, f[sel], k[sel]))
    return out


def main():
    gyro, colours = read_3mf(mk.OUT / "basketball-gyro.3mf")
    spinner, _ = read_3mf(mk.OUT / "basketball-spinner.3mf")
    opened = gyro_opened(gyro)

    for name, meshes, kw in [("basketball-gyro", gyro, {}), ("basketball-spinner", spinner, {"elev": 50})]:
        fig, ax = plt.subplots(figsize=(6, 5))
        draw(ax, meshes, colours, **kw)
        fig.savefig(mk.OUT / f"{name}.png", dpi=110, bbox_inches="tight", facecolor="white")
        plt.close(fig)

    fig, ax = plt.subplots(1, 3, figsize=(16, 5.6))
    draw(ax[0], gyro, colours)
    ax[0].set_title("Basketball gyro: as printed", fontsize=13)
    draw(ax[1], opened, colours, elev=25, azim=-40)
    ax[1].set_title("…and mid-spin", fontsize=13)
    draw(ax[2], spinner, colours, elev=50)
    ax[2].set_title("Basketball spinner + 2 caps (608 bearing)", fontsize=13)
    fig.tight_layout()
    fig.savefig(mk.HERE / "preview.png", dpi=100, facecolor="white")


if __name__ == "__main__":
    main()
