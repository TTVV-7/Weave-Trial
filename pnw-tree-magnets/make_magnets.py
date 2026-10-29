"""Turn the hi3D tree GLBs into half-tree fridge magnets.

Each tree is cut in half down the middle, front to back. The front half lies flat
against the fridge on its cut face, which gets up to MAX_MAGNETS pockets for disc
magnets. Each pocket is closed by a thin glue-in lid that sits flush with the
back, so the magnets are hidden.

The half is also written as a painted 3MF for a 4-toolhead printer: every
triangle takes the colour of the hi3D texture nearest it, snapped to the nearest
of FILAMENTS. Every tree uses the same four in the same slots, so the printer is
loaded once for the whole set and different trees can share a plate.

Run: python3 make_magnets.py   (needs trimesh, manifold3d, shapely, fast-simplification)
All dimensions are in millimetres; tweak the constants below and re-run.
"""
import pathlib
import zipfile
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
TOOLHEADS = 4          # filaments per print (Snapmaker U1)
SMOOTHING = 3          # passes of majority vote, so lone triangles don't cost a tool change
NEIGHBOURS = 32        # texture samples averaged for each triangle
SHADOW_L = 22          # samples darker than this (CIELAB lightness) are baked-in shadow

# The four filaments, T1-T4, for every tree.
FILAMENTS = np.array([
    [0x29, 0x43, 0x29],   # T1 dark forest green: needles, leaves
    [0x48, 0x68, 0x43],   # T2 moss green: lighter needles, moss
    [0x5D, 0x34, 0x1E],   # T3 dark brown: trunks, bark, bases
    [0xBA, 0x74, 0x26],   # T4 golden amber: maple leaves, madrone bark and berries
])
FOREST, MOSS, BROWN, AMBER = range(4)

TREES = ["douglas-fir", "western-red-cedar", "sitka-spruce",
         "western-hemlock", "pacific-madrone", "bigleaf-maple"]



def load(path, height=HEIGHT):
    """GLB (Y up, front +Z, 1 unit tall) -> merged Z-up mesh, front facing -Y,
    scaled to `height` with its base at z=0.

    Also returns the GLB's own vertices with their texture colour, already
    moved into the same frame, for painting the finished part."""
    g = trimesh.load(path).to_geometry()
    tex = np.asarray(g.visual.material.baseColorTexture.convert("RGB"))
    uv = np.clip(g.visual.uv, 0, 1)
    px = (uv[:, 0] * (tex.shape[1] - 1)).round().astype(int)
    py = ((1 - uv[:, 1]) * (tex.shape[0] - 1)).round().astype(int)
    colours = tex[py, px]

    m = trimesh.Trimesh(g.vertices, g.faces, process=True)   # drops UVs so seams merge
    m.merge_vertices(digits_vertex=6)
    frame = trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])
    m.apply_transform(frame)
    scale = trimesh.transformations.scale_matrix(height / m.extents[2])
    m.apply_transform(scale)
    shift = trimesh.transformations.translation_matrix(-np.array([*m.centroid[:2], m.bounds[0][2]]))
    m.apply_transform(shift)
    painted = trimesh.transform_points(g.vertices, shift @ scale @ frame)
    return m, (painted, colours)


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
    laid on its cut face: back at z=0, front facing +z, top of the tree at +y.
    Also returns the transform that takes the whole tree into that frame."""
    yc = section(solid, 1.0).centroid.y + back
    front = solid.trim_by_plane([0, -1, 0], -yc).translate([0, -yc, 0])
    lay = (trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0])
           @ trimesh.transformations.translation_matrix([0, -yc, 0]))
    return front.rotate([-90, 0, 0]), lay


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


def make(name, folder=HERE, out=OUT, height=HEIGHT):
    """The half of folder/name.glb with its magnet pockets, written to out/ as
    name-half.stl and name-lids.stl, plus what paint() needs to colour it."""
    m, painted = load(folder / f"{name}.glb", height)
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
        tree, lay = half(solid, back)
        pockets = place_pockets(tree, magnet)
        if len(pockets) >= 2:
            best = magnet, back, tree, lay, pockets
            break
        if pockets and best is None:
            best = magnet, back, tree, lay, pockets
    if best is None:
        raise SystemExit(f"{name}: no room on the back for any of the magnets")
    magnet, back, tree, lay, pockets = best
    r, depth = pocket_size(magnet)
    tree -= cylinders(pockets, r, depth + 1, -1)

    out_dir, out = out, trimesh.Trimesh(**_arrays(tree))
    out.export(out_dir / f"{name}-half.stl")
    trimesh.Trimesh(**_arrays(lids(len(pockets), r))).export(out_dir / f"{name}-lids.stl")

    rgb = texture_colours(out, painted, lay)
    w, h, d = out.extents
    row = (f"| `stl/{name}-half.stl` + `-lids.stl` | {w:.0f} × {h:.0f} | {d:.0f} mm "
           f"| {len(pockets)} × {magnet[0]:g}×{magnet[1]:g} mm | {back:g} mm "
           f"| {tree.volume() / 1000:.1f} cm³ |")
    return dict(name=name, mesh=out, rgb=rgb, row=row)


# ---------- colour: the same 4 filaments for every tree, painted 3MF ----------

def texture_colours(mesh, painted, transform=None, k=NEIGHBOURS, shadow_l=SHADOW_L):
    """Colour of the nearest textured hi3D vertices, for every triangle of mesh.
    The texture has shadows baked into its crevices, near black, which must not
    become a black filament: average only the neighbours that are out of shadow
    (lighter than shadow_l), and leave a triangle with none of those (NaN) for
    paint() to fill from around it. `transform` takes the GLB's vertices into
    the mesh's frame."""
    from scipy.spatial import cKDTree
    where, colours = painted
    if transform is not None:
        where = trimesh.transform_points(where, transform)
    _, near = cKDTree(where).query(mesh.triangles_center, k=k)
    rgb = colours[near].astype(float)
    lit = (to_lab(rgb)[..., 0] > shadow_l)[..., None]
    return np.where(lit.any(1), (rgb * lit).sum(1) / np.maximum(lit.sum(1), 1), np.nan)


def to_lab(rgb):
    """sRGB 0-255 -> CIELAB, so colour distances match what the eye sees."""
    c = np.asarray(rgb, float) / 255
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    xyz = c @ np.array([[0.4124, 0.2126, 0.0193], [0.3576, 0.7152, 0.1192],
                        [0.1805, 0.0722, 0.9505]]) / [0.9505, 1.0, 1.089]
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]),
                     200 * (f[..., 1] - f[..., 2])], -1)


def paint(part, filaments=FILAMENTS):
    """Filament index (0..len(filaments)-1) for every triangle. Shadowed triangles take
    the filament of the surface around them, then lone specks are voted away."""
    known = np.isfinite(part["rgb"][:, 0])
    pal = to_lab(filaments)
    label = np.full(len(known), -1)
    label[known] = np.argmin(((to_lab(part["rgb"][known])[:, None] - pal[None]) ** 2).sum(-1), 1)
    pairs = part["mesh"].face_adjacency

    def vote(label, self_weight):
        votes = np.zeros((len(label), len(filaments)))
        has = label >= 0
        votes[np.flatnonzero(has), label[has]] += self_weight
        for a, b in (pairs.T, pairs[:, ::-1].T):
            ok = label[b] >= 0
            np.add.at(votes, (a[ok], label[b[ok]]), 1)
        return np.where(votes.any(1), votes.argmax(1), -1)

    while (label < 0).any():
        filled = np.where(label < 0, vote(label, 0), label)
        if (filled == label).all():
            filled[filled < 0] = np.bincount(label[label >= 0]).argmax()
        label = filled
    for _ in range(SMOOTHING):
        label = vote(label, 1.5)
    return label


def paint_sitka_spruce(part):
    """The spruce's texture is one blue-teal throughout, bark and needles alike, so
    colouring by texture can't separate them. Paint it by shape instead: a brown
    trunk and stone base, moss on the base and root flare, and needles in the two
    greens by how light the texture is there."""
    mesh = part["mesh"]
    x, y = mesh.triangles_center[:, 0], mesh.triangles_center[:, 1]
    up = mesh.face_normals[:, 1]
    BASE_TOP, FLARE_TOP, TRUNK_TOP = 6.0, 9.0, 21.5   # mm, measured off the model
    TRUNK_X, TRUNK_HALF = -0.3, 4.8                   # trunk centre line and half-width
    known = np.isfinite(part["rgb"][:, 0])
    light = np.full(len(y), np.nan)
    light[known] = to_lab(part["rgb"][known])[:, 0]
    label = np.full(len(y), FOREST)
    label[light > np.nanpercentile(light, 70)] = MOSS
    trunk = (y < TRUNK_TOP) & (np.abs(x - TRUNK_X) < TRUNK_HALF)
    label[trunk | (y < BASE_TOP)] = BROWN
    label[(y < FLARE_TOP) & (up > 0.3)] = MOSS          # moss on the base and root flare
    pairs = mesh.face_adjacency
    for _ in range(SMOOTHING):                # same speck removal as paint()
        votes = np.zeros((len(label), TOOLHEADS))
        votes[np.arange(len(label)), label] += 1.5
        for a, b in (pairs.T, pairs[:, ::-1].T):
            np.add.at(votes, (a, label[b]), 1)
        label = votes.argmax(1)
    return label


# Trees painted by shape rather than from their texture.
PAINT_BY_SHAPE = {"sitka-spruce": paint_sitka_spruce}


# OrcaSlicer / Bambu Studio / Snapmaker Orca per-triangle filament codes.
PAINT_CODE = ["4", "8", "0C", "1C"]


def write_3mf(path, mesh, label, colours):
    """One object, every triangle painted with its filament, filament colours listed."""
    hexes = [f"#{int(r):02X}{int(g):02X}{int(b):02X}FF" for r, g, b in colours]
    verts = "".join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in mesh.vertices)
    tris = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}" paint_color="{PAINT_CODE[k]}"/>'
                   for (a, b, c), k in zip(mesh.faces, label))
    model = ('<?xml version="1.0" encoding="UTF-8"?>'
             '<model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
             'xmlns:m="http://schemas.microsoft.com/3dmanufacturing/material/2015/02">'
             '<resources><m:colorgroup id="100">'
             + "".join(f'<m:color color="{h}"/>' for h in hexes) +
             f'</m:colorgroup><object id="1" type="model"><mesh><vertices>{verts}</vertices>'
             f'<triangles>{tris}</triangles></mesh></object></resources>'
             '<build><item objectid="1"/></build></model>')
    settings = ('<?xml version="1.0" encoding="UTF-8"?><config><object id="1">'
                f'<metadata key="name" value="{path.stem}"/><metadata key="extruder" value="1"/>'
                '</object></config>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.'
                   'openxmlformats.org/package/2006/content-types"><Default Extension="rels" '
                   'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="model" ContentType="application/vnd.ms-package.'
                   '3dmanufacturing-3dmodel+xml"/></Types>')
        z.writestr("_rels/.rels",
                   '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.'
                   'openxmlformats.org/package/2006/relationships"><Relationship '
                   'Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/'
                   '3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        z.writestr("3D/3dmodel.model", model)
        z.writestr("Metadata/model_settings.config", settings)


if __name__ == "__main__":
    for t in TREES:
        p = make(t)
        label = PAINT_BY_SHAPE.get(t, paint)(p)
        write_3mf(OUT / f"{t}-half.3mf", p["mesh"], label, FILAMENTS)
        share = np.bincount(label, weights=p["mesh"].area_faces, minlength=TOOLHEADS)
        print(p["row"], "T1-T4 share", (share / share.sum()).round(2).tolist(), flush=True)
