"""Turn the hi3D tree GLBs into two-part printable STLs that hide a magnet in the base.

Each tree is split CAP mm above its bottom. The tree gets a magnet pocket opening
on its new underside; the cap is the slice cut away, with two locating pins, and
is glued on after the magnet goes in.

Run: python3 make_magnets.py   (needs trimesh, manifold3d, shapely, fast-simplification)
All dimensions are in millimetres; tweak the constants below and re-run.
"""
import pathlib
import numpy as np
import trimesh
import manifold3d
from shapely.geometry import Polygon
from shapely import contains_xy
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
CAP = 1.0              # thickness of the glue-on cap (plastic between magnet and fridge)
PIN_D = 2.0            # locating pins on the cap
PIN_H = 1.5
PIN_CLEARANCE = 0.3    # added to the pin hole diameter
PIN_MARGIN = 0.8       # plastic required around each pin hole
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


def place_pins(solid, pocket):
    """Two pin positions, away from the pocket and not opposite each other so the cap
    only fits one way round. None if the base has no room for them."""
    hole_r = (PIN_D + PIN_CLEARANCE) / 2
    keep = hole_r + PIN_MARGIN
    region = _common(solid, np.linspace(0.05, PIN_H + 0.3 + CEILING, 4)).buffer(-keep)
    region = region.difference(pocket.buffer(POCKET_R + keep))
    xs, ys = np.meshgrid(*(np.arange(lo, hi, 0.25) for lo, hi in
                           zip(region.bounds[:2], region.bounds[2:])))
    pts = np.column_stack([xs.ravel(), ys.ravel()])
    pts = pts[contains_xy(region, pts[:, 0], pts[:, 1])]
    if len(pts) == 0:
        return None
    rel = pts - [pocket.x, pocket.y]
    a = pts[np.argmax(np.hypot(*rel.T))]
    ang = np.degrees(np.arctan2(*rel[:, ::-1].T) - np.arctan2(*(a - [pocket.x, pocket.y])[::-1]))
    turn = np.abs((ang + 180) % 360 - 180)
    ok = (turn > 90) & (turn < 150)
    if not ok.any():
        return None
    b = pts[ok][np.argmax(np.hypot(*(pts[ok] - a).T))]
    return a, b


def pins(points, d, h, z=0.0):
    return sum((manifold3d.Manifold.cylinder(h, d / 2, d / 2, 48).translate([x, y, z])
                for x, y in points), manifold3d.Manifold())


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

    # Thicken the base from below, a millimetre at a time, until the part above
    # the cap line can hold the pocket.
    for plinth in range(MAX_PLINTH + 1):
        thick = add_plinth(solid, plinth)
        tree = thick.trim_by_plane([0, 0, 1], CAP).translate([0, 0, -CAP])
        placed = place_pocket(tree)
        if placed:
            break
    else:
        raise SystemExit(f"{name}: base too small for a {MAGNET_D:g} mm magnet")
    c, wall = placed
    cap = thick.trim_by_plane([0, 0, -1], -CAP)

    pin_xy = place_pins(tree, c)
    if pin_xy is None:
        raise SystemExit(f"{name}: no room for the locating pins")
    tree -= manifold3d.Manifold.cylinder(POCKET_DEPTH + 1, POCKET_R, POCKET_R, RES).translate([c.x, c.y, -1])
    tree -= pins(pin_xy, PIN_D + PIN_CLEARANCE, PIN_H + 0.3 + 1, -1)
    cap += pins(pin_xy, PIN_D, PIN_H + 0.05, CAP - 0.05)

    for part, solid_part in (("tree", tree), ("cap", cap)):
        trimesh.Trimesh(**_arrays(solid_part)).export(OUT / f"{name}-{part}.stl")
    w, d, h = trimesh.Trimesh(**_arrays(tree)).extents
    return (f"| `stl/{name}-tree.stl` + `-cap.stl` | {w:.0f} × {d:.0f} × {h + CAP:.0f} "
            f"| {wall:.1f} mm | {plinth or '—'} |")

if __name__ == "__main__":
    for t in TREES:
        print(make(t), flush=True)
