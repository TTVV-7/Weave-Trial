#!/usr/bin/env python3
"""1:50 print files for the hi3D construction equipment: a plain STL and a
painted 3MF for multi-colour printers, for each machine.

    python construction_equipment/make_prints.py                    # all ten
    python construction_equipment/make_prints.py Crawler_Excavator_20t

Needs trimesh, manifold3d, fast-simplification, scipy and scikit-image.
Writes construction_equipment/print_1-50/.

Each machine goes from the real-size GLB (scale_models.py) to a print that
stands on the bed in one solid piece:

1. 1:50, Z up, front toward +X; simplified from hi3D's 2 million triangles
   to FACES, which is still far finer than a printer can show at this size.
2. Parts thinner than MIN_THICKNESS (handrails, mirrors, hoses, track
   grousers, bucket side plates) are found on a PITCH voxel grid, as whatever
   a ball of that diameter can't fit inside, and given a skin of
   MIN_THICKNESS / 2 around them, so nothing prints thinner than that.
   Thick parts are left exactly as they were.
3. The bottom FLATTEN mm is cut off so tracks and tyres sit flat on the bed.
4. hi3D leaves a few loose pieces floating just off the body. Crumbs are
   dropped; anything bigger is pegged to the body with a short rod.
5. Every triangle takes the filament most of the texture around it maps to,
   out of the machine's three or four (the same stock colours as Construction
   Site Packs 1-4), then lone triangles are voted away so the printer isn't
   changing filament for single specks. Long edges are split first, so paint
   borders follow the texture.
"""

from __future__ import annotations

import sys
import time
import zipfile
from pathlib import Path

import fast_simplification
import manifold3d
import numpy as np
import trimesh
from scipy import ndimage
from scipy.spatial import cKDTree
from skimage.draw import polygon as rasterize
from skimage.measure import marching_cubes

HERE = Path(__file__).resolve().parent
OUT = HERE / "print_1-50"

SCALE = 1 / 50
FACES = 150_000          # triangles kept from hi3D's ~2 million
PITCH = 0.2              # mm, voxel size for finding thin parts
SLAB = 48                # voxels per slab when measuring distances on that grid
MIN_THICKNESS = 0.8      # mm, thinnest anything prints (two 0.4 mm lines)
RIM = 0.3                # mm; thin voxels this close to a thick part are its rounded edge, not a thin part
MIN_PIECE = 25           # voxels; smaller thin specks are surface noise, left alone
SKIN_TOLERANCE = 0.1    # mm the thickening skin may move when simplified
SKIN_BLUR = 1.2         # voxels of Gaussian blur on the skin's distance field
TOLERANCE = 0.05         # mm the finished surface may move when simplified
CRUMB = 1.0              # mm3; loose pieces smaller than this are dropped
PEG = 0.5                # mm, radius of the rod that pegs a loose piece to the body
FLATTEN = 0.3            # mm cut off the bottom
PAINT_EDGE = 4.0         # mm; longer edges are split so paint borders (the mixer's
                         # stripes) follow the texture rather than big flat triangles
SAMPLES = 3_000_000      # texture samples spread over the surface for painting
NEIGHBOURS = 32          # nearest samples that vote on each triangle's filament
COLOURED_C = 12          # CIELAB chroma above which a sample counts as coloured...
COLOURED_RATIO = 0.15    # ...if also at least this fraction of its lightness
L_BLACK = 30             # neutral samples darker than this are black
L_WHITE = 58             # and lighter than this white (the texture is darker than the paint)
SMOOTHING = 3            # passes removing lone triangles (all three neighbours another filament)

# The stock filaments of Construction Site Packs 1-4.
FILAMENTS = {
    "Construction yellow": (0xFF, 0xC2, 0x00),
    "Black": (0x1A, 0x1A, 0x1A),
    "Silver grey": (0x8C, 0x8F, 0x92),
    "White": (0xF2, 0xF2, 0xF0),
    "Safety orange": (0xF2, 0x6A, 0x0D),
    "Signal red": (0xBF, 0x16, 0x0D),
    "Wood brown": (0xA0, 0x78, 0x48),
}
YELLOW = ["Construction yellow", "Black", "Silver grey"]

# name -> (title for the guide, the four filaments it may use)
MACHINES = {
    "Crawler_Excavator_20t": ("Crawler excavator (20 t class)", YELLOW),
    "Mini_Excavator_3.5t": ("Mini excavator (3.5 t class)", YELLOW),
    "Wheel_Loader_18t": ("Wheel loader (18 t class)", YELLOW),
    "Crawler_Dozer_20t": ("Crawler dozer with ripper (20 t class)", YELLOW),
    "Backhoe_Loader": ("Backhoe loader", YELLOW),
    "Skid_Steer_Loader": ("Skid steer loader", YELLOW),
    "Articulated_Dump_Truck_30t": ("Articulated dump truck (30 t class)", YELLOW),
    "Concrete_Mixer_Truck": ("Concrete mixer truck",
                             ["White", "Safety orange", "Black", "Silver grey"]),
    "Vibratory_Soil_Compactor_12t": ("Single-drum vibratory soil compactor (12 t class)", YELLOW),
    "Scissor_Lift_26ft": ("Electric scissor lift (26 ft), stowed",
                          ["Safety orange", "Construction yellow", "Black", "Silver grey"]),
}

# glTF (X width, Y up, Z forward, metres) -> print (X forward, Y width, Z up, mm)
TO_PRINT = np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]], float) * 1000 * SCALE


def log(t0: float, msg: str) -> None:
    print(f"  {time.time() - t0:6.1f}s  {msg}", flush=True)


def load(name: str):
    """The scaled GLB as one watertight mesh in print coordinates, plus
    SAMPLES points spread evenly over its surface with their texture colours,
    for painting. (Sampling only the vertices would miss whatever the texture
    paints across big flat triangles, like the stripes on the mixer drum.)"""
    g = trimesh.load(HERE / f"{name}.glb").to_geometry()   # applies scale_models.py's root
    points, face = trimesh.sample.sample_surface(g, SAMPLES, seed=1)
    bary = trimesh.triangles.points_to_barycentric(g.triangles[face], points)
    uv = np.clip((bary[:, :, None] * g.visual.uv[g.faces[face]]).sum(1), 0, 1)
    tex = np.asarray(g.visual.material.baseColorTexture.convert("RGB"))
    colours = tex[((1 - uv[:, 1]) * (tex.shape[0] - 1)).round().astype(int),
                  (uv[:, 0] * (tex.shape[1] - 1)).round().astype(int)]
    where = points @ TO_PRINT.T
    m = trimesh.Trimesh(g.vertices @ TO_PRINT.T, g.faces, process=True)   # drops UVs, so seams merge
    m.merge_vertices(digits_vertex=6)
    if not m.is_watertight:
        raise SystemExit(f"{name}: hi3D mesh is not watertight after merging")
    return m, where, colours


def to_manifold(vertices, faces) -> manifold3d.Manifold:
    s = manifold3d.Manifold(manifold3d.Mesh(
        vert_properties=np.asarray(vertices, np.float32),
        tri_verts=np.asarray(faces, np.uint32)))
    if s.status() != manifold3d.Error.NoError:
        raise SystemExit(f"not a valid solid: {s.status()}")
    return s


def from_manifold(s: manifold3d.Manifold) -> trimesh.Trimesh:
    mesh = s.to_mesh()
    return trimesh.Trimesh(mesh.vert_properties[:, :3], mesh.tri_verts, process=False)


def decimate(vertices, faces, target):
    if len(faces) <= target:
        return vertices, faces
    return fast_simplification.simplify(vertices, faces, 1 - target / len(faces))


def thin_parts(solid: manifold3d.Manifold, surface_points: np.ndarray):
    """The skin that brings every thin part up to MIN_THICKNESS, as a mesh,
    or None if nothing is thin."""
    box = np.array(solid.bounding_box())
    pad = 4 + int(np.ceil(MIN_THICKNESS / PITCH))
    lo = box[:3] - pad * PITCH
    shape = np.ceil((box[3:] + pad * PITCH - lo) / PITCH).astype(int)

    # Voxelise slice by slice from exact cross-sections, then add every voxel
    # the full-resolution surface touches, so parts thinner than a voxel are
    # not lost between voxel centres.
    occ = np.zeros(shape, bool)
    for k in range(shape[2]):
        for ring in solid.slice(lo[2] + (k + 0.5) * PITCH).to_polygons():
            if len(ring) >= 3:
                rr, cc = rasterize((ring[:, 0] - lo[0]) / PITCH - 0.5,
                                   (ring[:, 1] - lo[1]) / PITCH - 0.5, shape[:2])
                occ[rr, cc, k] ^= True          # even-odd: holes cancel out
    idx = np.floor((surface_points - lo) / PITCH).astype(int)
    occ[idx[:, 0], idx[:, 1], idx[:, 2]] = True

    # Thin: inside the solid but not inside any ball of diameter MIN_THICKNESS
    # that fits in it (the morphological opening), and not merely the rounded
    # rim that the opening shaves off a thick part's edges.
    r = MIN_THICKNESS / 2
    core = edt(occ, r + PITCH) > r
    opened = edt(~core, r + PITCH) <= r
    del core
    thin = occ & ~opened & (edt(~opened, RIM + PITCH) > RIM)
    del occ, opened
    label, n = ndimage.label(thin, structure=np.ones((3, 3, 3)))
    del thin
    if n == 0:
        return None
    big = np.bincount(label.ravel())[1:] >= MIN_PIECE
    keep = np.concatenate([[False], big])[label]
    del label
    if not keep.any():
        return None

    # Only the box around the thin parts needs a surface.
    m = int(np.ceil(r / PITCH)) + 3
    nz = [np.flatnonzero(keep.any(axis=tuple(j for j in range(3) if j != i))) for i in range(3)]
    a = [max(0, ax[0] - m) for ax in nz]
    b = [min(keep.shape[i], nz[i][-1] + m + 1) for i in range(3)]
    keep = keep[a[0]:b[0], a[1]:b[1], a[2]:b[2]]
    # > 0 within r of a thin part. Voxel distances are multiples of PITCH, so
    # nudge the level off them, or grid points sit exactly on the surface and
    # marching cubes makes zero-area triangles.
    field = (r + 0.07 * PITCH) - edt(~keep, r + 2 * PITCH)
    # blurred a little, or the skin shows every voxel as a lump
    field = ndimage.gaussian_filter(field, SKIN_BLUR)
    verts, faces, _, _ = marching_cubes(np.pad(field, 1, constant_values=-1), 0.0)
    del field, keep
    origin = lo + np.array(a) * PITCH
    skin = trimesh.Trimesh((verts - 1 + 0.5) * PITCH + origin, faces[:, ::-1], process=True)
    skin.update_faces(skin.nondegenerate_faces())
    skin.remove_unreferenced_vertices()
    # simplified by manifold itself, which keeps it a valid solid (a generic
    # decimator can leave the marching-cubes surface non-manifold)
    return to_manifold(skin.vertices, skin.faces).simplify(SKIN_TOLERANCE)


def edt(mask: np.ndarray, cap: float) -> np.ndarray:
    """Distance in mm from each True voxel to the nearest False one, exact up
    to `cap` (anything further reads as `cap`). Worked in slabs along X so a
    20 cm truck's grid fits in memory: scipy's transform needs about 20 bytes
    per voxel, and only distances up to `cap` are ever compared."""
    margin = int(np.ceil(cap / PITCH)) + 2
    out = np.empty(mask.shape, np.float32)
    n = mask.shape[0]
    for a in range(0, n, SLAB):
        b = min(n, a + SLAB)
        lo, hi = max(0, a - margin), min(n, b + margin)
        d = ndimage.distance_transform_edt(mask[lo:hi]).astype(np.float32) * PITCH
        out[a:b] = np.minimum(d[a - lo:b - lo], cap)
    return out


def peg_loose_pieces(solid: manifold3d.Manifold):
    """Drop crumbs; join any bigger loose piece to the body with a short rod."""
    pieces = sorted(solid.decompose(), key=lambda p: -p.volume())
    body, dropped, pegged = pieces[0], 0, 0
    for p in pieces[1:]:
        if p.volume() < CRUMB:
            dropped += 1
            continue
        bv = body.to_mesh().vert_properties[:, :3]
        pv = p.to_mesh().vert_properties[:, :3]
        gap, j = cKDTree(bv).query(pv)
        i = int(np.argmin(gap))
        a, b = pv[i], bv[j[i]]
        axis = (b - a) / max(np.linalg.norm(b - a), 1e-6)
        a, b = a - axis * PEG, b + axis * PEG               # reach into both
        rod = manifold3d.Manifold.batch_hull([manifold3d.Manifold.sphere(PEG, 16).translate(a),
                                              manifold3d.Manifold.sphere(PEG, 16).translate(b)])
        body = body + p + rod
        pegged += 1
    return body, dropped, pegged


# ---------- colour ----------

def to_lab(rgb):
    """sRGB 0-255 -> CIELAB, so colour distances match what the eye sees."""
    c = np.asarray(rgb, float) / 255
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    xyz = c @ np.array([[0.4124, 0.2126, 0.0193], [0.3576, 0.7152, 0.1192],
                        [0.1805, 0.0722, 0.9505]]) / [0.9505, 1.0, 1.089]
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]),
                     200 * (f[..., 1] - f[..., 2])], -1)


def classify(rgb, names):
    """Filament index into `names` for each texture sample.

    hi3D bakes heavy shadow into the texture (hidden surfaces come out dark
    brown, shaded yellow comes out mustard), so plain nearest-colour matching
    paints half of a yellow machine black. Instead: a sample with real colour
    in it goes to the coloured filament nearest in hue, however dark it is;
    a neutral one goes to black, grey or white by how light it is."""
    lab = to_lab(rgb)
    light, chroma = lab[:, 0], np.hypot(lab[:, 1], lab[:, 2])
    hue = np.degrees(np.arctan2(lab[:, 2], lab[:, 1])) % 360
    pal = to_lab([FILAMENTS[n] for n in names])
    pal_chroma = np.hypot(pal[:, 1], pal[:, 2])
    pal_hue = np.degrees(np.arctan2(pal[:, 2], pal[:, 1])) % 360
    coloured = np.flatnonzero(pal_chroma > 20)
    neutral = np.flatnonzero(pal_chroma <= 20)

    out = np.empty(len(rgb), int)
    is_col = (chroma >= COLOURED_C) & (chroma >= COLOURED_RATIO * light) & (len(coloured) > 0)
    if is_col.any():
        gap = np.abs((hue[is_col, None] - pal_hue[None, coloured] + 180) % 360 - 180)
        out[is_col] = coloured[gap.argmin(1)]
    if (~is_col).any():
        # black below L_BLACK, white above L_WHITE, grey between; a machine
        # without one of those uses its nearest neutral filament instead
        level = np.digitize(light[~is_col], [L_BLACK, L_WHITE])
        targets = [FILAMENTS["Black"], FILAMENTS["Silver grey"], FILAMENTS["White"]]
        pool = neutral if len(neutral) else np.arange(len(names))
        choice = [pool[np.argmin(np.abs(pal[pool, 0] - to_lab([t])[0, 0]))] for t in targets]
        out[~is_col] = np.array(choice)[level]
    return out


def paint(mesh: trimesh.Trimesh, where, colours, names):
    """Filament index into `names` for every triangle of `mesh`: the majority
    of its nearest texture samples, then lone specks voted away."""
    k = len(names)
    sample = classify(colours, names)
    _, near = cKDTree(where).query(mesh.triangles_center, k=NEIGHBOURS)
    counts = np.zeros((len(mesh.faces), k))
    for j in range(NEIGHBOURS):
        np.add.at(counts, (np.arange(len(mesh.faces)), sample[near[:, j]]), 1)
    label = counts.argmax(1)

    pairs = mesh.face_adjacency
    for _ in range(SMOOTHING):
        votes = np.zeros((len(label), k))
        votes[np.arange(len(label)), label] += 2.5   # flips only if all three neighbours differ
        for a, b in (pairs.T, pairs[:, ::-1].T):
            np.add.at(votes, (a, label[b]), 1)
        label = votes.argmax(1)
    return label


# OrcaSlicer / Bambu Studio / Snapmaker Orca per-triangle filament codes, T1-T4.
PAINT_CODE = ["4", "8", "0C", "1C"]


def write_3mf(path: Path, mesh: trimesh.Trimesh, label, names) -> None:
    """One object, every triangle painted with its filament, filament colours listed."""
    hexes = [f"#{r:02X}{g:02X}{b:02X}FF" for r, g, b in (FILAMENTS[n] for n in names)]
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


def write_painted_glb(path: Path, mesh: trimesh.Trimesh, label, names) -> None:
    """The painted print as a GLB in filament colours (Y up), for preview renders."""
    back = np.array([[0, 1, 0], [0, 0, 1], [1, 0, 0]], float)   # print -> glTF axes
    pal = np.array([[*FILAMENTS[n], 255] for n in names], np.uint8)
    # every triangle gets its own corners, or the export would average colours
    # across shared vertices and smear narrow bands like the drum stripes
    tris = mesh.triangles.reshape(-1, 3) @ back.T
    out = trimesh.Trimesh(tris, np.arange(len(tris)).reshape(-1, 3), process=False)
    out.visual.vertex_colors = np.repeat(pal[label], 3, axis=0)
    out.export(path)


def make(name: str) -> dict:
    title, candidates = MACHINES[name]
    t0 = time.time()
    m, where, colours = load(name)
    v, f = decimate(m.vertices, m.faces, FACES)
    solid = to_manifold(v, f)
    log(t0, f"loaded and simplified to {len(f)} triangles")

    skin = thin_parts(solid, m.vertices)
    if skin is not None:
        solid = solid + skin
        log(t0, f"thin parts thickened ({skin.volume():.0f} mm3 added)")
    solid = solid.simplify(TOLERANCE)
    zmin = solid.bounding_box()[2]
    solid = solid.trim_by_plane([0, 0, 1], zmin + FLATTEN).translate([0, 0, -zmin - FLATTEN])
    where = where - [0, 0, zmin + FLATTEN]

    # after the cut, which can free a piece too; a peg must not poke through the bed
    dropped = pegged = 0
    for _ in range(3):
        solid, d, p = peg_loose_pieces(solid)
        solid = solid.trim_by_plane([0, 0, 1], 0)
        dropped, pegged = dropped + d, pegged + p
        if len(solid.decompose()) == 1:
            break
    log(t0, f"{dropped} crumbs dropped, {pegged} loose pieces pegged on")

    box = np.array(solid.bounding_box())
    solid = solid.translate([-(box[0] + box[3]) / 2, -(box[1] + box[4]) / 2, 0])
    where = where - [(box[0] + box[3]) / 2, (box[1] + box[4]) / 2, 0]
    before = solid.num_tri()
    solid = solid.refine_to_length(PAINT_EDGE)
    log(t0, f"{before} triangles, {solid.num_tri()} after splitting edges over {PAINT_EDGE} mm")
    mesh = from_manifold(solid)
    assert len(solid.decompose()) == 1 and mesh.is_watertight, "print is not one solid piece"

    label = paint(mesh, where, colours, candidates)
    # T1 is the filament with the most surface, and any that ended up unused are dropped
    share = np.bincount(label, weights=mesh.area_faces, minlength=len(candidates))
    order = [i for i in np.argsort(-share) if share[i] > 0]
    names = [candidates[i] for i in order]
    remap = np.zeros(len(candidates), int)
    remap[order] = np.arange(len(order))
    label = remap[label]
    log(t0, "painted: " + ", ".join(f"T{i + 1} {n} {share[o] / share.sum():.0%}"
                                    for i, (n, o) in enumerate(zip(names, order))))

    OUT.mkdir(exist_ok=True)
    mesh.export(OUT / f"{name}_1-50.stl")
    write_3mf(OUT / f"{name}_1-50_painted.3mf", mesh, label, names)
    write_painted_glb(OUT / f"{name}_1-50_painted.glb", mesh, label, names)
    size = mesh.extents
    log(t0, f"{size[0]:.0f} x {size[1]:.0f} x {size[2]:.0f} mm, {len(mesh.faces)} triangles, "
            f"{solid.volume() / 1000:.1f} cm3")
    return dict(name=name, title=title, size=size, filaments=names,
                volume=solid.volume(), triangles=len(mesh.faces))


def main(names: list[str]) -> int:
    for name in names or list(MACHINES):
        print(name, flush=True)
        make(name)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
