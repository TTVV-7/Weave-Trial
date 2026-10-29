#!/usr/bin/env python3
"""Turn the full-size construction site models into printable scale models.

    python listings/make_scale_models.py                  # 1:50, into listings/construction-site-1-50/
    python listings/make_scale_models.py --scale 87       # HO scale
    python listings/make_scale_models.py --only Traffic_Cone_28in

The models in construction_site/ are drawn at real size for site planning, so a
handrail is a 48 mm tube and a fence wire is 4 mm. Shrunk to 1:50 those become
a 1 mm rail and a wire a twelfth of a millimetre across, which no printer can
make. Scale model makers solve this the same way every time: they exaggerate
the thin parts. So does this.

Each model is read from its .glb as its named parts, every part is split into
its separate pieces, and each piece is measured along its own oriented box. Any
side thinner than --min-feature is stretched about the piece's centre to that
size, so a wire becomes a printable rod in place and a plate a printable sheet,
while anything already thick enough is not touched. The pieces are then joined
into one closed solid (manifold3d). A part drawn a little clear of what holds
it up (a cab over the frame) is joined to it, since a printer would otherwise
print it in mid air. The solid is stood on the bed and written as an STL.

Then it measures what it made rather than trusting the recipe: rays fired
inward from points all over the surface give the wall thickness there, so a
curved sheet the box test cannot see (a mixer pan, a cab roof) still shows up
in the report. report.json records, per model, its size, how many loose pieces
it prints as, and how much of its surface is thinner than --min-feature.

And it paints them. Every part's colour in the .glb is snapped to the nearest
of FILAMENTS, ordinary PLA colours you can buy, and each model keeps the four
it uses most (a 4-slot AMS, or the Snapmaker U1's four toolheads); a colour
past the fourth is folded into the nearest one kept. Each triangle of the
finished solid takes the filament of the part it came from, and the model is
written as a painted 3MF beside the plain STL.
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
import zipfile
from pathlib import Path

import manifold3d
import numpy as np
import trimesh
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "construction_site"
OVERLAP = 0.05  # mm each piece grows by, so parts that touch fuse
BRIDGE = 3.0     # mm: a floating piece closer than this to the body is joined to it
Y_UP_TO_Z_UP = trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])
TOOLHEADS = 4
CUBE_CORNERS = np.array([[x, y, z] for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)])

# Stock PLA colours the models are painted in. Each model uses up to four.
FILAMENTS = {
    "Black": "#1A1A1A",
    "Silver grey": "#8C8F92",
    "Light grey": "#C8CACC",
    "White": "#F2F2F0",
    "Construction yellow": "#FFC200",
    "Safety orange": "#F26A0D",
    "Signal red": "#BF160D",
    "Blue": "#0066C0",
    "Dark green": "#22582F",
    "Sand": "#D8C8A4",
    "Wood brown": "#A07848",
}

# OrcaSlicer / Bambu Studio / Snapmaker Orca per-triangle codes for T1-T4.
PAINT_CODE = ["4", "8", "0C", "1C"]

# What each model is called in a listing, and the ones left out: the 50 ft
# fence run is five of the panels, and at 1:50 it is longer than most beds.
MODELS = {
    "Telehandler_10000lb_56ft": "Telehandler (10,000 lb class)",
    "Carry_Deck_Crane": "Carry deck crane",
    "Trailer_Concrete_Line_Pump": "Trailer concrete line pump",
    "Towable_Air_Compressor": "Towable air compressor",
    "Roll_Off_Dumpster_20yd": "Roll-off dumpster (20 yd)",
    "Planetary_Mixer_on_Stand": "Planetary concrete mixer on stand",
    "Planetary_Concrete_Mixer_500L": "Planetary concrete mixer (500 L)",
    "Mixer_Stand": "Mixer stand",
    "Pallet_of_Concrete_Bags": "Pallet of concrete bags",
    "Bulk_Bag_Concrete_on_Pallet": "Bulk bag of concrete mix (1 t) on pallet",
    "Industrial_Steel_Stair_12ft": "Industrial steel stair (12 ft)",
    "Rail_Crossover_Gantry": "Rail crossover gantry",
    "Temporary_Fence_Panel_6x10ft": "Temporary fence panel (6 x 10 ft)",
    "Traffic_Cone_28in": "Traffic cone (28 in)",
}


def srgb(linear_rgba) -> np.ndarray:
    """A glTF baseColorFactor (linear, 0-255) as an sRGB colour, 0-255."""
    c = np.asarray(linear_rgba[:3], dtype=float) / 255
    return 255 * np.where(c <= 0.0031308, 12.92 * c, 1.055 * c ** (1 / 2.4) - 0.055)


def lab(rgb) -> np.ndarray:
    """sRGB 0-255 to CIELAB, so 'nearest colour' means nearest to the eye."""
    c = np.atleast_2d(np.asarray(rgb, dtype=float)) / 255
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    xyz = c @ np.array([[0.4124, 0.3576, 0.1805],
                        [0.2126, 0.7152, 0.0722],
                        [0.0193, 0.1192, 0.9505]]).T / [0.9505, 1.0, 1.089]
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[:, 1] - 16, 500 * (f[:, 0] - f[:, 1]),
                     200 * (f[:, 1] - f[:, 2])], axis=1)


FILAMENT_NAMES = list(FILAMENTS)
FILAMENT_RGB = np.array([[int(h[i:i + 2], 16) for i in (1, 3, 5)] for h in FILAMENTS.values()])
FILAMENT_LAB = lab(FILAMENT_RGB)


def nearest_filament(rgb) -> int:
    return int(np.argmin(np.linalg.norm(FILAMENT_LAB - lab(rgb), axis=1)))


def named_parts(glb: Path) -> dict[str, tuple[trimesh.Trimesh, int]]:
    """The model's named parts, each one closed mesh in metres with Z up, and
    the filament (an index into FILAMENTS) nearest its colour.

    The .glb stores every face of a part as its own mesh under the part's node,
    so faces are gathered by parent node and welded back together."""
    scene = trimesh.load(glb)
    faces = collections.defaultdict(list)
    for node in scene.graph.nodes_geometry:
        transform, geometry = scene.graph[node]
        parent = scene.graph.transforms.parents.get(node, node)
        faces[parent].append(scene.geometry[geometry].copy().apply_transform(transform))
    parts = {}
    for name, meshes in faces.items():
        votes = collections.Counter()
        for m in meshes:
            votes[nearest_filament(srgb(m.visual.material.baseColorFactor))] += m.area
        mesh = trimesh.util.concatenate(meshes)
        mesh = trimesh.Trimesh(mesh.vertices, mesh.faces)  # drop colour and UVs
        mesh.merge_vertices(digits_vertex=6)  # to the micron: weld seams left by tessellation
        parts[name] = (mesh.apply_transform(Y_UP_TO_Z_UP), votes.most_common(1)[0][0])
    return parts


def closed(piece: trimesh.Trimesh) -> tuple[trimesh.Trimesh | None, bool]:
    """The piece as a closed solid, and whether that took its convex hull.
    None for a sliver too flat to be a solid at all."""
    if len(piece.faces) < 4 or np.linalg.matrix_rank(piece.vertices - piece.vertices[0]) < 3:
        return None, False
    if piece.is_watertight:
        return piece, False
    piece = piece.copy()
    piece.fill_holes()
    if piece.is_watertight:
        return piece, False
    return piece.convex_hull, True


def thicken(piece: trimesh.Trimesh, minimum: float) -> tuple[trimesh.Trimesh, bool]:
    """Stretch the piece about its centre along any side of its oriented box
    thinner than minimum. Returns the piece and whether it was thin.

    A piece thin both ways (a wire, a rail, a rod) becomes a square bar the
    size of its stretched box: at 0.8 mm nobody can see that it was round,
    and a fence panel of round wires crossing each other unions into a
    million triangles where square bars make a few thousand.

    Every piece also grows by OVERLAP on each side. The model's parts sit face
    to face, and two solids that only touch stay two solids in a union, so
    without it a cab or a wheel prints as a separate loose piece."""
    box = piece.bounding_box_oriented
    extents = np.maximum(box.primitive.extents, 1e-9)
    target = np.maximum(extents, minimum) + 2 * OVERLAP
    to_world = box.primitive.transform
    if (extents < minimum).sum() >= 2:
        return trimesh.creation.box(extents=target, transform=to_world), True
    stretch = np.diag(np.append(target / extents, 1.0))
    return (piece.copy().apply_transform(to_world @ stretch @ np.linalg.inv(to_world)),
            bool(extents.min() < minimum))


def to_manifold(mesh: trimesh.Trimesh) -> manifold3d.Manifold:
    return manifold3d.Manifold(manifold3d.Mesh(
        vert_properties=np.asarray(mesh.vertices, dtype=np.float32),
        tri_verts=np.asarray(mesh.faces, dtype=np.uint32)))


def union(pieces: list[trimesh.Trimesh], labels: list[int]) -> tuple[trimesh.Trimesh, np.ndarray]:
    """The pieces as one solid, and for each of its triangles the label of the
    piece it came from. manifold3d records that provenance itself, so the
    painting is exact rather than a nearest-surface guess."""
    solids, owner = [], {}
    for piece, label in zip(pieces, labels):
        m = to_manifold(piece)
        if m.status() == manifold3d.Error.NoError and not m.is_empty():
            m = m.as_original()
            owner[m.original_id()] = label
            solids.append(m)
    whole = manifold3d.Manifold.batch_boolean(solids, manifold3d.OpType.Add).to_mesh()
    runs = np.asarray(whole.run_index) // 3
    face_label = np.repeat([owner[i] for i in whole.run_original_id], np.diff(runs))
    # process=False keeps manifold's topology as it is. Letting trimesh weld
    # vertices by position joins every place two pieces meet at a single
    # point, and the result no longer splits into its true pieces.
    mesh = trimesh.Trimesh(whole.vert_properties[:, :3], whole.tri_verts, process=False)
    # A closed pocket inside the solid (the inside of the mixer pan) comes out
    # as a shell of its own, facing inward. Dropping it fills the pocket, which
    # a slicer would fill with infill anyway, and stops it counting as a part.
    shells = trimesh.graph.connected_components(mesh.face_adjacency,
                                                nodes=np.arange(len(mesh.faces)))
    keep = np.concatenate([f for f in shells if mesh.submesh([f], append=True).volume > 0])
    if len(keep) < len(mesh.faces):
        keep.sort()
        mesh, face_label = mesh.submesh([keep], append=True), face_label[keep]
        mesh.remove_unreferenced_vertices()
    return mesh, face_label


def gap_fillers(model: trimesh.Trimesh, face_label: np.ndarray,
                widest: float) -> list[tuple[trimesh.Trimesh, int]]:
    """Solids that join pieces floating near the main body to it.

    Some parts are drawn a few centimetres clear of what carries them (a cab
    above the frame, a stabiliser beside it). That is invisible on screen and
    fatal on a printer, where the part is printed in mid air. For each piece
    within widest of the body, the patch of it that faces the body and the
    patch of body it faces are wrapped in one convex hull, which fills the gap
    locally and nowhere else, painted like the piece. Pieces further off are
    left loose. Distances come from a k-d tree of points spread over the body,
    which is fast and light where an exact closest-point query on a large
    model takes gigabytes."""
    components = trimesh.graph.connected_components(model.face_adjacency,
                                                    nodes=np.arange(len(model.faces)))
    if len(components) < 2:
        return []
    volume = lambda faces: abs(model.submesh([faces], append=True).volume)
    components = sorted(components, key=volume, reverse=True)
    main = model.submesh([components[0]], append=True)
    body_points, _ = trimesh.sample.sample_surface_even(main, 200_000, seed=2)
    tree = cKDTree(body_points)
    fillers = []
    for faces in components[1:]:
        piece = model.submesh([faces], append=True)
        points, _ = trimesh.sample.sample_surface_even(piece, 4000, seed=3)
        gap, nearest = tree.query(points)
        if gap.min() > widest:
            continue
        near = gap < gap.min() + 0.6
        patch = np.vstack([points[near], body_points[nearest[near]]])
        # A corner of each point's 0.3 mm cube too: when the two patches are
        # flat and face to face, the hull of the points alone has no volume.
        patch = (patch[:, None, :] + CUBE_CORNERS * 0.15).reshape(-1, 3)
        label = collections.Counter(face_label[faces]).most_common(1)[0][0]
        fillers.append((trimesh.convex.convex_hull(patch), label))
    return fillers


def wall_thickness(mesh: trimesh.Trimesh, samples: int = 6000, seed: int = 1) -> np.ndarray:
    """Thickness at points spread evenly over the surface: the distance from
    each point, inward along its normal, to the next surface."""
    points, faces = trimesh.sample.sample_surface_even(mesh, samples, seed=seed)
    inward = -mesh.face_normals[faces]
    start = points + inward * 1e-4
    hits, rays, _ = mesh.ray.intersects_location(start, inward, multiple_hits=False)
    thickness = np.full(len(points), np.inf)
    thickness[rays] = np.linalg.norm(hits - start, axis=1)
    return thickness[np.isfinite(thickness)]


def slots(model: trimesh.Trimesh, face_label: np.ndarray) -> tuple[np.ndarray, list[int]]:
    """Fit the model's filaments to the printer: keep its TOOLHEADS most-used,
    by painted area, and fold any other into the nearest kept one. Returns the
    slot of each triangle and the kept filaments in slot order T1, T2, ..."""
    area = collections.Counter()
    for f, a in zip(face_label, model.area_faces):
        area[f] += a
    kept = [f for f, _ in area.most_common(TOOLHEADS)]
    slot_of = {}
    for f in area:
        nearest = min(kept, key=lambda k: np.linalg.norm(FILAMENT_LAB[k] - FILAMENT_LAB[f]))
        slot_of[f] = kept.index(nearest)
    return np.array([slot_of[f] for f in face_label]), kept


def write_3mf(path: Path, mesh: trimesh.Trimesh, slots: np.ndarray, kept: list[int]) -> None:
    """One object, every triangle painted with its slot, in the per-triangle
    format Bambu Studio, OrcaSlicer and Snapmaker Orca read (the writer in
    pnw-tree-magnets/make_magnets.py, which is proven on the U1 and the P1S)."""
    hexes = [FILAMENTS[FILAMENT_NAMES[k]] + "FF" for k in kept]
    verts = "".join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in mesh.vertices)
    tris = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}" paint_color="{PAINT_CODE[k]}"/>'
                   for (a, b, c), k in zip(mesh.faces, slots))
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


def fix_compressor_doors(parts: dict) -> None:
    """The compressor's three pairs of side doors are 1 m wide and start at
    x = -1.8, -0.7 and +0.35 m, so the last pair runs 0.25 m past the front of
    the 3.05 m canopy and stands out in the air. Re-space them: 0.95 m wide,
    0.05 m apart, centred on the canopy, each door's louvres moving with it."""
    for old, new in ((-1.8, -1.9), (-0.7, -0.9), (0.35, 0.1)):
        tag = f"_{round(old * 1000)}_"
        for name, (mesh, filament) in parts.items():
            if name.startswith(("door" + tag, "louvre" + tag)):
                x = mesh.vertices[:, 0]
                mesh.vertices[:, 0] = new + (x - old) * 0.95


FIXES = {"Towable_Air_Compressor": fix_compressor_doors}


def fence_panel(scale: float, minimum: float) -> dict[str, tuple[trimesh.Trimesh, int, float]]:
    """A 6 x 10 ft temporary construction fence panel, in metres with Z up:
    a round-tube frame with a middle rail, welded wire mesh with close
    vertical wires and wider-spaced horizontal ones, standing on two flat
    stands with a joining pin each.

    The construction_site model is a chain-link panel, which at 1:50 prints as
    a diagonal grid. This is the welded-mesh panel seen on most sites. Its
    wires keep their real spacing and are drawn at their printed size, 0.5 mm
    across the panel (one line from a 0.4 mm nozzle) and 0.8 mm deep, rather
    than thickened to the usual minimum, which closes the mesh up into a
    pegboard. The frame is drawn bolder than real so it still reads as one.
    The third item of each part is the minimum it is thickened to."""
    light, steel = FILAMENT_NAMES.index("Light grey"), FILAMENT_NAMES.index("Silver grey")
    width, top = 3.048, 1.829                       # 10 ft wide, 6 ft tall
    mm = scale / 1000                               # one printed millimetre, in metres
    tube = max(0.042, 1.75 * minimum * mm)
    wire_across, wire_deep = 0.5 * mm, 0.8 * mm
    z_bottom, z_top = 0.17, top - tube / 2
    z_middle = (z_bottom + z_top) / 2
    post_x = width / 2 - tube / 2

    def rod(a, b, diameter):
        return trimesh.creation.cylinder(radius=diameter / 2, segment=[a, b], sections=20)

    def wire(a, b):
        """A straight wire along x or z, wire_across wide in the panel's plane."""
        a, b = np.asarray(a, float), np.asarray(b, float)
        size = np.array([wire_across, wire_deep, wire_across])
        axis = int(np.argmax(np.abs(b - a)))
        size[axis] = abs(b[axis] - a[axis])
        return trimesh.creation.box(extents=size,
                                    transform=trimesh.transformations.translation_matrix((a + b) / 2))

    frame, mesh_wires, stands = [], [], []
    for side in (-1, 1):
        frame.append(rod((side * post_x, 0, 0.02), (side * post_x, 0, top + 0.03), tube))
    for z in (z_bottom, z_middle, z_top):
        frame.append(rod((-post_x, 0, z), (post_x, 0, z), tube))

    inner = post_x - tube / 2
    count = round(2 * inner / 0.095)                # verticals about 95 mm apart
    for x in np.linspace(-inner, inner, count + 1)[1:-1]:
        mesh_wires.append(wire((x, 0, z_bottom), (x, 0, z_top)))
    for low, high in ((z_bottom, z_middle), (z_middle, z_top)):
        for z in np.linspace(low, high, 6)[1:-1]:   # four wires, five rows of mesh
            mesh_wires.append(wire((-inner - tube / 4, 0, z), (inner + tube / 4, 0, z)))

    for side in (-1, 1):
        x = side * post_x
        stands.append(trimesh.creation.box(              # flat stand across the fence line
            extents=(0.15, 0.61, 0.025),
            transform=trimesh.transformations.translation_matrix((x + side * 0.04, 0, 0.0125))))
        stands.append(rod((x + side * 0.1, 0, 0.02), (x + side * 0.1, 0, 0.22), 0.032))

    return {"frame": (trimesh.util.concatenate(frame), light, minimum),
            "mesh": (trimesh.util.concatenate(mesh_wires), light, 0.0),
            "stands": (trimesh.util.concatenate(stands), steel, minimum)}


def cad_parts(script: Path, assembly, drop: tuple[str, ...] = ()) -> dict:
    """The parts of a CadQuery model in this repo: run its build script, save
    the assembly as glTF (colours and part names kept) and read that back
    like the construction_site models. Parts whose names start with anything
    in drop are left out. The export is in millimetres, so it is put in metres."""
    import importlib.util
    import tempfile
    spec = importlib.util.spec_from_file_location(script.stem, script)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses look their module up here
    spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory() as scratch:
        glb = Path(scratch) / "model.glb"
        assembly(module).save(str(glb), exportType="GLTF")
        parts = named_parts(glb)
    return {name: (mesh.apply_scale(0.001), filament)
            for name, (mesh, filament) in parts.items() if not name.startswith(drop)}


BUILT = {
    "Temporary_Fence_Panel_6x10ft": fence_panel,
    # The crane was modelled on one company's machine; its name and fleet
    # number stay off a model that is for sale.
    "Carry_Deck_Crane": lambda scale, minimum: cad_parts(
        ROOT / "crane_model" / "build_crane.py", lambda m: m.crane,
        drop=("livery_text", "fleet_no")),
    "Bulk_Bag_Concrete_on_Pallet": lambda scale, minimum: cad_parts(
        ROOT / "bulkbag" / "bulk_bag.py", lambda m: m.build(m.Spec())),
}


def build(stem: str, scale: float, minimum: float, out: Path) -> dict:
    if stem in BUILT:
        parts = BUILT[stem](scale, minimum)
    else:
        parts = named_parts(SOURCE / f"{stem}.glb")
        if stem in FIXES:
            FIXES[stem](parts)
    mm = 1000.0 / scale
    pieces, filaments, stretched, hulled = [], [], 0, 0
    for mesh, filament, *thinnest in parts.values():
        for piece in mesh.split(only_watertight=False):
            piece, was_hulled = closed(piece.apply_scale(mm))
            if piece is None:
                continue
            piece, was_stretched = thicken(piece, thinnest[0] if thinnest else minimum)
            pieces.append(piece)
            filaments.append(filament)
            stretched += was_stretched
            hulled += was_hulled
    drawn = len(pieces)
    model, face_label = union(pieces, filaments)
    for _ in range(4):  # a piece may hang off another floating piece
        fillers = gap_fillers(model, face_label, widest=BRIDGE)
        if not fillers:
            break
        loose = len(model.split(only_watertight=False))
        bridged, bridged_label = union(pieces + [f for f, _ in fillers],
                                       filaments + [label for _, label in fillers])
        if len(bridged.split(only_watertight=False)) >= loose:
            break
        pieces += [f for f, _ in fillers]
        filaments += [label for _, label in fillers]
        model, face_label = bridged, bridged_label
    slot, kept = slots(model, face_label)
    model.apply_translation([-model.centroid[0], -model.centroid[1], -model.bounds[0][2]])

    thickness = wall_thickness(model)
    thin = float(np.mean(thickness < minimum * 0.95))
    loose = len(model.split(only_watertight=False))
    path = out / f"{stem}_1-{scale:g}.stl"
    model.export(path)
    write_3mf(path.with_suffix(".3mf"), model, slot, kept)
    np.save(path.with_suffix(".slots.npy"), slot.astype(np.uint8))  # for the renders
    return {
        "name": MODELS[stem],
        "file": path.name,
        "painted": path.with_suffix(".3mf").name,
        "filaments": [f"T{i + 1} {FILAMENT_NAMES[k]} {FILAMENTS[FILAMENT_NAMES[k]]}"
                      for i, k in enumerate(kept)],
        "size_mm": [round(float(v), 1) for v in model.extents],
        "volume_cm3": round(model.volume / 1000, 2),
        "triangles": len(model.faces),
        "watertight": bool(model.is_watertight),
        "loose_pieces": loose,
        "pieces_thickened": stretched,
        "pieces_total": drawn,
        "pieces_closed_by_hull": hulled,
        "thinnest_wall_mm": round(float(np.percentile(thickness, 1)), 2),
        "surface_too_thin": round(thin, 3),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--scale", type=float, default=50, help="1:N, default 1:50")
    ap.add_argument("--min-feature", type=float, default=0.8,
                    help="thinnest wall or rod to allow, mm (0.8 suits a 0.4 mm nozzle)")
    ap.add_argument("--out", type=Path, help="listing folder (default listings/construction-site-1-<N>)")
    ap.add_argument("--only", nargs="*", help="model names to build, default all")
    args = ap.parse_args()

    out = args.out or ROOT / "listings" / f"construction-site-1-{args.scale:g}"
    (out / "files").mkdir(parents=True, exist_ok=True)
    report_path = out / "report.json"
    report = json.loads(report_path.read_text()) if report_path.exists() else {}
    report.update(scale=f"1:{args.scale:g}", min_feature_mm=args.min_feature)
    models = report.setdefault("models", {})

    for stem in args.only or MODELS:
        r = build(stem, args.scale, args.min_feature, out / "files")
        models[stem] = r
        x, y, z = r["size_mm"]
        print(f"{r['name']:36s} {x:5.0f} x {y:4.0f} x {z:4.0f} mm  "
              f"{r['pieces_thickened']:4d}/{r['pieces_total']:<4d} thickened  "
              f"{r['loose_pieces']} piece(s)  thin surface {r['surface_too_thin']:.1%}  "
              + ", ".join(f.split(" #")[0] for f in r["filaments"]))
        report_path.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
