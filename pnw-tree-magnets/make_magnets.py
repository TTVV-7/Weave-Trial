"""Turn the hi3D tree GLBs into printable STLs with a magnet pocket in the base.

Run: python3 make_magnets.py   (needs trimesh, manifold3d, shapely, fast-simplification)
All dimensions are in millimetres; tweak the constants below and re-run.
"""
import pathlib
import numpy as np
import trimesh
import manifold3d
from shapely.geometry import Polygon
from shapely.ops import unary_union, polylabel

HERE = pathlib.Path(__file__).parent
OUT = HERE / "stl"
OUT.mkdir(exist_ok=True)

HEIGHT = 75.0          # finished height of each tree, base to tip
MAGNET_D = 10.0        # magnet diameter (10 x 3 mm neodymium disc)
MAGNET_T = 3.0         # magnet thickness
CLEARANCE = 0.3        # added to the pocket diameter for a press/glue fit
DEPTH_EXTRA = 0.2      # pocket is this much deeper than the magnet
FLATTEN = 0.4          # shave this off the bottom so the base is dead flat
MIN_WALL = 2.0         # plastic required around the pocket
CEILING = 1.2          # solid plastic required above the pocket
MAX_PLINTH = 4         # mm the base may be thickened to fit the pocket
FACES = 400_000        # decimate the 2M-face scans to this
RES = 96               # pocket circle smoothness

TREES = ["douglas-fir", "western-red-cedar", "sitka-spruce",
         "western-hemlock", "pacific-madrone", "bigleaf-maple"]


def load(name):
    """GLB (Y up, 1 unit tall) -> merged, Z-up mesh scaled to HEIGHT with its base at z=0."""
    m = trimesh.load(HERE / f"{name}.glb").to_geometry()
    m = trimesh.Trimesh(m.vertices, m.faces, process=True)   # drops UVs so seams merge
    m.merge_vertices(digits_vertex=6)
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    m.apply_scale(HEIGHT / m.extents[2])
    m.apply_translation(-np.array([*m.centroid[:2], m.bounds[0][2]]))
    return m


def decimate(m):
    import fast_simplification
    v, f = fast_simplification.simplify(m.vertices, m.faces, 1 - FACES / len(m.faces))
    return trimesh.Trimesh(v, f, process=True)


def to_manifold(m):
    return manifold3d.Manifold(manifold3d.Mesh(
        vert_properties=np.asarray(m.vertices, np.float32),
        tri_verts=np.asarray(m.faces, np.uint32)))


def footprint(solid, z):
    """Cross-section of the base at height z, as a shapely polygon."""
    rings = [Polygon(r) for r in solid.slice(z).to_polygons() if len(r) >= 3]
    shape = unary_union([r for r in rings if r.exterior.is_ccw]).difference(
        unary_union([r for r in rings if not r.exterior.is_ccw]))
    return max(getattr(shape, "geoms", [shape]), key=lambda g: g.area)


def _common(solid, zs):
    """Region solid at every one of the heights zs."""
    region = footprint(solid, zs[0])
    for z in zs[1:]:
        region = region.intersection(footprint(solid, z))
    return max(getattr(region, "geoms", [region]), key=lambda g: g.area)


def _arrays(solid):
    mesh = solid.to_mesh()
    return dict(vertices=mesh.vert_properties[:, :3], faces=mesh.tri_verts)


POCKET_R = (MAGNET_D + CLEARANCE) / 2
POCKET_DEPTH = MAGNET_T + DEPTH_EXTRA


def add_plinth(solid, h):
    """Extend the bottom face straight down by h mm, keeping the base at z=0."""
    if h == 0:
        return solid
    foot = manifold3d.Manifold.extrude(solid.slice(0.05), h + 0.05).translate([0, 0, -h])
    return (solid + foot).translate([0, 0, h])


def place_pocket(solid):
    """Best pocket centre and its side wall, or None if the base can't hold it.

    The pocket's sides need MIN_WALL of plastic all the way up, and its
    ceiling needs CEILING of solid directly above it (roots leave gaps).
    """
    sides = _common(solid, np.linspace(0.05, POCKET_DEPTH, 5))
    cover = _common(solid, np.linspace(POCKET_DEPTH, POCKET_DEPTH + CEILING, 4))
    ok = sides.buffer(-(POCKET_R + MIN_WALL)).intersection(cover.buffer(-POCKET_R))
    if ok.is_empty:
        return None
    ok = max(getattr(ok, "geoms", [ok]), key=lambda g: g.area)
    c = polylabel(ok, tolerance=0.05)
    return c, sides.boundary.distance(c) - POCKET_R


def make(name):
    m = load(name)
    if not m.is_watertight:
        raise SystemExit(f"{name}: mesh is not watertight after merging")
    if len(m.faces) > FACES:
        m = decimate(m)
    solid = to_manifold(m)
    if solid.status() != manifold3d.Error.NoError:
        raise SystemExit(f"{name}: not a valid manifold ({solid.status()})")

    # Shave the bottom flat, then drop it back onto z=0.
    solid = solid.trim_by_plane([0, 0, 1], FLATTEN).translate([0, 0, -FLATTEN])

    # Thicken the base from below, a millimetre at a time, until it can hold the pocket.
    for plinth in range(MAX_PLINTH + 1):
        thick = add_plinth(solid, plinth)
        placed = place_pocket(thick)
        if placed:
            break
    else:
        raise SystemExit(f"{name}: base too small for a {MAGNET_D:g} mm magnet")
    (c, wall), r, depth = placed, POCKET_R, POCKET_DEPTH

    pocket = (manifold3d.Manifold.cylinder(depth + 1, r, r, RES)
              .translate([c.x, c.y, -1]))
    solid = thick - pocket

    out = trimesh.Trimesh(**_arrays(solid))
    out.export(OUT / f"{name}-magnet.stl")
    w, d, h = out.extents
    return f"| `stl/{name}-magnet.stl` | {w:.0f} × {d:.0f} × {h:.0f} | {wall:.1f} mm | {plinth or '—'} |"


if __name__ == "__main__":
    for t in TREES:
        print(make(t), flush=True)
