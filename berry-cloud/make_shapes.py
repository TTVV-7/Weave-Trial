"""Mock-up models for Brittany's strawberry, cloud and raindrops.

Run: python3 make_shapes.py   (needs numpy, trimesh, shapely, manifold3d)
Writes stl/*.stl (one per printed part) and shapes.glb (coloured, for previews).
All sizes in millimetres. The models are closed solids: slice them with 0 %
infill and 3 walls (or vase mode for the raindrops) to get hollow prints.
"""
import math
from pathlib import Path
import numpy as np
import trimesh
from shapely.geometry import Polygon
import manifold3d as m3
from strawberry import strawberry

HERE = Path(__file__).parent
OUT = HERE / "stl"
OUT.mkdir(exist_ok=True)
SEG = 128

# ---- sizes from the request -------------------------------------------------
BERRY_H = 205.0      # body; with the leaves and stem the berry is ~9" (229 mm) tall
BERRY_W = 190.0      # 7.5"
CLOUD_W = 290.0      # 11.4"
DROP_L = 65.0        # 2.5"


def revolve(profile):
    """Closed solid of revolution about Z from a list of (r, z), r=0 at both ends."""
    p = np.asarray(profile, float)
    th = np.linspace(0, 2 * np.pi, SEG, endpoint=False)
    rings = [np.c_[r * np.cos(th), r * np.sin(th), np.full(SEG, z)] for r, z in p[1:-1]]
    v = np.vstack([[0, 0, p[0, 1]], *rings, [0, 0, p[-1, 1]]])
    f, n = [], len(rings)
    for j in range(SEG):
        k = (j + 1) % SEG
        f.append([0, 1 + k, 1 + j])
        for i in range(n - 1):
            a, b = 1 + i * SEG, 1 + (i + 1) * SEG
            f += [[a + j, a + k, b + k], [a + j, b + k, b + j]]
        last = 1 + (n - 1) * SEG
        f.append([last + j, last + k, len(v) - 1])
    mesh = trimesh.Trimesh(v, f)
    mesh.fix_normals()
    return mesh


def to_manifold(mesh):
    return m3.Manifold(m3.Mesh(vert_properties=mesh.vertices.astype(np.float32),
                               tri_verts=mesh.faces.astype(np.uint32)))


def from_manifold(man):
    m = man.to_mesh()
    return trimesh.Trimesh(m.vert_properties[:, :3], m.tri_verts)


# ---- cloud -----------------------------------------------------------------
PUFFS = [  # (x, z, r) in units of the cloud width
    (0.00, 0.22, 0.25), (-0.22, 0.13, 0.19), (0.22, 0.14, 0.20),
    (-0.37, 0.07, 0.13), (0.38, 0.07, 0.12), (-0.09, 0.36, 0.17),
    (0.12, 0.33, 0.16), (-0.27, 0.25, 0.12),
]
FRONT = [  # (x, y, z, r): smaller puffs bulging out of the front and back
    (-0.12, -0.10, 0.17, 0.14), (0.16, -0.10, 0.17, 0.13), (0.02, -0.12, 0.28, 0.11),
    (-0.12, 0.10, 0.17, 0.14), (0.16, 0.10, 0.17, 0.13), (0.02, 0.12, 0.28, 0.11),
]


def cloud():
    """Puffs unioned together, squashed front-to-back, flat underside."""
    puffs, front = PUFFS, FRONT
    W = CLOUD_W
    man = None
    for x, z, r in puffs:
        s = m3.Manifold.sphere(r * W, 96).translate((x * W, 0, z * W))
        man = s if man is None else man + s
    man = man.scale((1, 0.55, 1))
    for x, y, z, r in front:
        man = man + m3.Manifold.sphere(r * W, 96).scale((1, 0.8, 1)).translate((x * W, y * W, z * W))
    cut = m3.Manifold.cube((W * 2, W * 2, W), True).translate((0, 0, -W / 2 + 0.06 * W))
    man = (man - cut).translate((0, 0, -0.06 * W))
    mesh = from_manifold(man)
    return mesh


# ---- raindrop --------------------------------------------------------------
def raindrop():
    t = np.linspace(0, np.pi, 120)
    r = np.sin(t) * np.sin(t / 2) ** 2.2
    z = -np.cos(t)
    scale = DROP_L / (z.max() - z.min())
    r, z = r * scale, (z - z.min()) * scale
    r[0] = r[-1] = 0
    prof = list(zip(r, z))[::-1]            # round end at the bottom, point up
    return revolve([(a, DROP_L - b) for a, b in prof][::-1])


if __name__ == "__main__":
    berry, n_seeds = strawberry()
    print(f"strawberry: {n_seeds} seeds")
    parts = {
        "strawberry-body": (berry["strawberry-body"], "#c4142c"),
        "strawberry-seeds": (berry["strawberry-seeds"], "#f2c230"),
        "strawberry-leaves": (berry["strawberry-leaves"], "#2f8a2f"),
        "cloud": (cloud(), "#f4f6fa"),
        "raindrop": (raindrop(), "#2a86d0"),
    }
    scene = trimesh.Scene()
    for name, (mesh, col) in parts.items():
        mesh.export(OUT / f"{name}.stl")
        e = mesh.extents
        print(f"{name:18s} {e[0]:6.0f} x {e[1]:6.0f} x {e[2]:6.0f} mm  "
              f"({e[0]/25.4:.1f} x {e[1]/25.4:.1f} x {e[2]/25.4:.1f} in)  watertight={mesh.is_watertight}")
        m = mesh.copy()
        rgb = [int(col[i:i + 2], 16) for i in (1, 3, 5)]
        m.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(
            baseColorFactor=rgb + [255], roughnessFactor=0.55, metallicFactor=0.0))
        scene.add_geometry(m, geom_name=name, node_name=name)
    scene.export(HERE / "shapes.glb")
