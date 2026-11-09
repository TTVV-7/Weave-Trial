"""Render preview images from the painted 3MFs, in their filament colours.

    python3 preview.py        (needs trimesh, matplotlib)

Writes stl/basketball-gyro.png, stl/basketball-spinner.png and preview.png
(both fidgets side by side, plus the gyro opened up to show it spins), and
stl/construction-nut-bolt.png and construction-preview.png (the nut & bolt
screwed together, and laid out as printed), and
stl/southwest-contracting-gyro.png and southwest-contracting-preview.png, and
stl/pocket-gear-fidget.png and pocket-gear-preview.png (before and after a turn), and
stl/pocket-capybara.png and pocket-capybara-preview.png (straight and wiggled).
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
import make_nut_bolt as nb

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


def construction():
    objs, colours = read_3mf(mk.OUT / "construction-nut-bolt.3mf")
    bolt, nuts = objs[0], objs[1:]
    built = [bolt]
    for (v, f, k), z in zip(nuts, [44.0, 28.0, 12.0]):
        v = v - [v[:, 0].mean(), v[:, 1].mean(), 0]      # back to the bolt's axis
        a = np.radians(360 * (z - nb.HEAD_H) / nb.PITCH)
        rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
        built.append((v @ rz.T + [0, 0, z], f, k))
    fig, ax = plt.subplots(figsize=(5, 6))
    draw(ax, built, colours, elev=15, azim=-25)
    fig.savefig(mk.OUT / "construction-nut-bolt.png", dpi=110, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    fig, ax = plt.subplots(1, 3, figsize=(16, 6), gridspec_kw={"width_ratios": [1, 1.4, 1.1]})
    draw(ax[0], built, colours, elev=15, azim=-25)
    ax[0].set_title("Construction nut & bolt", fontsize=13)
    draw(ax[1], objs, colours, elev=40, azim=-30)
    ax[1].set_title("…as printed: bolt standing, nuts flat", fontsize=13)
    draw(ax[2], [nuts[0]], colours, elev=70, azim=-20)
    ax[2].set_title("hazard stripes run on round every face", fontsize=13)
    fig.tight_layout()
    fig.savefig(mk.HERE / "construction-preview.png", dpi=100, facecolor="white")


def southwest():
    gyro, colours = read_3mf(mk.OUT / "southwest-contracting-gyro.3mf")
    fig, ax = plt.subplots(figsize=(6, 4.5))
    draw(ax, gyro, colours, elev=20, azim=-90)
    fig.savefig(mk.OUT / "southwest-contracting-gyro.png", dpi=110, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    fig, ax = plt.subplots(1, 3, figsize=(16, 5))
    draw(ax[0], gyro, colours, elev=20, azim=-90)
    ax[0].set_title("Southwest Contracting gyro: front", fontsize=13)
    draw(ax[1], gyro, colours, elev=20, azim=90)
    ax[1].set_title("back", fontsize=13)
    draw(ax[2], gyro_opened(gyro), colours, elev=30, azim=-60)
    ax[2].set_title("mid-spin", fontsize=13)
    fig.tight_layout()
    fig.savefig(mk.HERE / "southwest-contracting-preview.png", dpi=100, facecolor="white")


def gears():
    import make_gear_fidget as gf
    colours = [f"#{r:02X}{g:02X}{b:02X}" for r, g, b in gf.FILAMENTS]
    parts, base = gf.make_parts()

    def as_draw(ps):
        mesh, lab = gf.paint(ps, gf.GEAR_H)
        return [(mesh.vertices, mesh.faces, lab)]

    before = as_draw(parts)
    after = as_draw(gf.turned(parts, base, 60))
    fig, ax = plt.subplots(figsize=(5.5, 5))
    draw(ax, before, colours, elev=55, azim=-30)
    fig.savefig(mk.OUT / "pocket-gear-fidget.png", dpi=110, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    fig, ax = plt.subplots(1, 3, figsize=(16, 5.4))
    draw(ax[0], before, colours, elev=55, azim=-30)
    ax[0].set_title("Pocket gear fidget, as printed", fontsize=13)
    draw(ax[1], after, colours, elev=89, azim=0)
    ax[1].set_title("sun turned 60°: planets rolled round", fontsize=13)
    draw(ax[2], after, colours, elev=30, azim=40)
    ax[2].set_title("herringbone teeth hold it together", fontsize=13)
    fig.tight_layout()
    fig.savefig(mk.HERE / "pocket-gear-preview.png", dpi=100, bbox_inches="tight", facecolor="white")


def capybara():
    import make_capybara as cb
    colours = [f"#{r:02X}{g:02X}{b:02X}" for r, g, b in cb.FILAMENTS]
    parts, joints, info = cb.make_capybara()

    def as_draw(ps):
        mesh, lab = cb.paint(parts, info, ps)
        return [(mesh.vertices, mesh.faces, lab)]

    pose = {"body joint 1": 25, "body joint 2": -25, "body joint 3": 25, "head nod": 12, "orange": 90,
            "front left leg": 35, "front right leg": -30, "hind left leg": -40, "hind right leg": 30}
    straight = as_draw(parts)
    wiggled = as_draw(cb.posed(parts, joints, pose))
    fig, ax = plt.subplots(figsize=(7, 4.5))
    draw(ax, straight, colours, elev=25, azim=60)
    fig.savefig(mk.OUT / "pocket-capybara.png", dpi=110, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    fig, ax = plt.subplots(2, 2, figsize=(14, 9))
    draw(ax[0, 0], straight, colours, elev=25, azim=60)
    ax[0, 0].set_title("Pocket capybara, straight (as printed)", fontsize=13)
    draw(ax[0, 1], wiggled, colours, elev=25, azim=60)
    ax[0, 1].set_title("wiggled: body bent, head up, legs swung", fontsize=13)
    draw(ax[1, 0], straight, colours, elev=89, azim=180)
    ax[1, 0].set_title("from above, straight", fontsize=13)
    draw(ax[1, 1], wiggled, colours, elev=89, azim=180)
    ax[1, 1].set_title("from above, wiggled", fontsize=13)
    fig.tight_layout()
    fig.savefig(mk.HERE / "pocket-capybara-preview.png", dpi=100, bbox_inches="tight", facecolor="white")
    plt.close(fig)


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
    construction()
    southwest()
    gears()
    capybara()


if __name__ == "__main__":
    main()
