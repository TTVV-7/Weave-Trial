"""Turn the hi3D tree GLBs into half-tree fridge magnets.

Each tree is cut in half down the middle, front to back. The front half lies flat
against the fridge on its cut face, which gets up to MAX_MAGNETS pockets for disc
magnets. Each pocket is closed by a thin glue-in lid that sits flush with the
back, so the magnets are hidden.

Run: python3 make_magnets.py   (needs trimesh, manifold3d, shapely, fast-simplification)
All dimensions are in millimetres; tweak the constants below and re-run.
"""
import pathlib
import numpy as np
import trimesh
import manifold3d
from shapely import contains_xy
from shapely.geometry import Polygon
from shapely.ops import unary_union

HERE = pathlib.Path(__file__).parent
OUT = HERE / "stl"
OUT.mkdir(exist_ok=True)

HEIGHT = 75.0          # finished height of each tree, base to tip
MAGNETS = [(6.0, 3.0), (5.0, 2.0)]   # disc magnets (diameter, thickness), largest first;
                                     # each tree gets the largest that fits its back
CLEARANCE = 0.3        # added to the pocket diameter for a press/glue fit
LID = 1.0              # glue-in lid over each magnet, flush with the back
LID_CLEARANCE = 0.15   # taken off the lid diameter so it drops in
DEPTH_EXTRA = 0.2      # room for glue between magnet and lid
MIN_WALL = 1.2         # plastic required around each pocket
CEILING = 1.2          # solid plastic required in front of each pocket
MAX_MAGNETS = 3
CUT_BACK = [0.0, 1.0, 2.0, 3.0, 4.0]  # how far behind the middle the cut may move to
                                     # leave more plastic in front of the magnets
MIN_SPACING = 10.0     # centre to centre, so the magnets spread the load
FACES = 400_000        # decimate the 2M-face scans to this
RES = 64               # pocket circle smoothness

TREES = ["douglas-fir", "western-red-cedar", "sitka-spruce",
         "western-hemlock", "pacific-madrone", "bigleaf-maple"]



def load(name):
    """GLB (Y up, front +Z, 1 unit tall) -> merged Z-up mesh, front facing -Y,
    scaled to HEIGHT with its base at z=0."""
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


def section(solid, z):
    """Cross-section of the solid at height z, as shapely (multi)polygons."""
    rings = [Polygon(r) for r in solid.slice(z).to_polygons() if len(r) >= 3]
    return unary_union([r for r in rings if r.exterior.is_ccw]).difference(
        unary_union([r for r in rings if not r.exterior.is_ccw]))


def _common(solid, zs):
    """Region solid at every one of the heights zs."""
    region = section(solid, zs[0])
    for z in zs[1:]:
        region = region.intersection(section(solid, z))
    return region


def _arrays(solid):
    mesh = solid.to_mesh()
    return dict(vertices=mesh.vert_properties[:, :3], faces=mesh.tri_verts)


def half(solid, back=0.0):
    """Front half of the tree, cut `back` mm behind the middle of its base and
    laid on its cut face: back at z=0, front facing +z, top of the tree at +y."""
    yc = section(solid, 1.0).centroid.y + back
    front = solid.trim_by_plane([0, -1, 0], -yc).translate([0, -yc, 0])
    return front.rotate([-90, 0, 0])


def pocket_size(magnet):
    """Pocket radius and depth (lid + magnet + glue room) for a (diameter, thickness) magnet."""
    d, t = magnet
    return (d + CLEARANCE) / 2, LID + t + DEPTH_EXTRA


def place_pockets(solid, magnet):
    """Up to MAX_MAGNETS pocket centres on the back face. The first sits nearest
    the middle of the back (for balance), the rest as far from the others as
    possible but at least MIN_SPACING apart."""
    r, depth = pocket_size(magnet)
    sides = _common(solid, np.linspace(0.05, depth, 5))
    cover = _common(solid, np.linspace(depth, depth + CEILING, 3))
    ok = sides.buffer(-(r + MIN_WALL)).intersection(cover.buffer(-r))
    if ok.is_empty:
        return []
    xs, ys = np.meshgrid(*(np.arange(lo, hi, 0.25) for lo, hi in
                           zip(ok.bounds[:2], ok.bounds[2:])))
    pts = np.column_stack([xs.ravel(), ys.ravel()])
    pts = pts[contains_xy(ok, pts[:, 0], pts[:, 1])]
    if len(pts) == 0:
        return []
    middle = np.array(section(solid, 0.05).centroid.coords[0])
    chosen = [pts[np.argmin(np.hypot(*(pts - middle).T))]]
    while len(chosen) < MAX_MAGNETS:
        gap = np.min([np.hypot(*(pts - c).T) for c in chosen], axis=0)
        if gap.max() < MIN_SPACING:
            break
        chosen.append(pts[np.argmax(gap)])
    return chosen


def cylinders(points, r, h, z=0.0):
    return sum((manifold3d.Manifold.cylinder(h, r, r, RES).translate([x, y, z])
                for x, y in points), manifold3d.Manifold())


def lids(n, pocket_r):
    r = pocket_r - LID_CLEARANCE / 2
    return cylinders([(i * (2 * r + 3), 0) for i in range(n)], r, LID)


def make(name):
    m = load(name)
    if not m.is_watertight:
        raise SystemExit(f"{name}: mesh is not watertight after merging")
    if len(m.faces) > FACES:
        m = decimate(m)
    solid = to_manifold(m)
    if solid.status() != manifold3d.Error.NoError:
        raise SystemExit(f"{name}: not a valid manifold ({solid.status()})")

    # Prefer two or more magnets (one alone lets the tree spin on the fridge), then
    # the larger magnet, then the cut nearest the middle.
    tried = [(magnet, back) for magnet in MAGNETS for back in CUT_BACK]
    best = None
    for magnet, back in tried:
        tree = half(solid, back)
        pockets = place_pockets(tree, magnet)
        if len(pockets) >= 2:
            best = magnet, back, tree, pockets
            break
        if pockets and best is None:
            best = magnet, back, tree, pockets
    if best is None:
        raise SystemExit(f"{name}: no room on the back for any of the magnets")
    magnet, back, tree, pockets = best
    r, depth = pocket_size(magnet)
    tree -= cylinders(pockets, r, depth + 1, -1)

    trimesh.Trimesh(**_arrays(tree)).export(OUT / f"{name}-half.stl")
    trimesh.Trimesh(**_arrays(lids(len(pockets), r))).export(OUT / f"{name}-lids.stl")
    w, h, d = trimesh.Trimesh(**_arrays(tree)).extents
    return (f"| `stl/{name}-half.stl` + `-lids.stl` | {w:.0f} × {h:.0f} | {d:.0f} mm "
            f"| {len(pockets)} × {magnet[0]:g}×{magnet[1]:g} mm | {back:g} mm "
            f"| {tree.volume() / 1000:.1f} cm³ |")


if __name__ == "__main__":
    for t in TREES:
        print(make(t), flush=True)
