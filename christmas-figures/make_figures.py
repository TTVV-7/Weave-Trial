"""Turn the hi3D Christmas GLBs into printable figurines, ornaments and magnets.

Each figure comes three ways, all painted for a 4-filament printer:

    stl/<name>.stl, .3mf            the figurine as hi3D made it, HEIGHT tall
    stl/<name>-ornament.stl, .3mf   the same with a hanging loop on top
    stl/<name>-half.stl, .3mf       the front half with magnet pockets, as the
    stl/<name>-lids.stl             tree magnets in ../pnw-tree-magnets

The cutting, pockets, lids, texture sampling and painting are
pnw-tree-magnets/make_magnets.py's; this script only adds the loop and the
per-figure filaments. Five figures share red, white, dark green and golden
brown; the penguin swaps green for black, in the same slot.

Run: python3 make_figures.py   (needs trimesh, manifold3d, shapely, scipy, fast-simplification)
"""
import pathlib
import sys

import manifold3d
import numpy as np
import trimesh

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "pnw-tree-magnets"))
import make_magnets as mm  # noqa: E402

OUT = HERE / "stl"
OUT.mkdir(exist_ok=True)
CACHE = HERE / "cache"   # repaired meshes, 60 MB each, not committed

HEIGHT = 70.0        # figurine height, base to top, before the loop
LOOP_HOLE = 3.0      # hanging loop: hole diameter
LOOP_WIRE = 1.8      # and the thickness of its ring
LOOP_SINK = 1.5      # how far the ring is sunk into the top of the figure
LOOP_RADIUS = 10.0   # the loop goes on the highest surface within this of the figure's
                     # centre line, leaning towards the line, so it hangs straight

# Stock filaments. Every figure prints from four of them, in the slot order given
# in FIGURES, so five of the six load the same way and can share a plate.
RED = (0xB8, 0x2E, 0x2E)       # suits, hats, scarves, collar, buttons
WHITE = (0xF2, 0xF0, 0xEB)     # beards, trim, snow, icing, faces
GREEN = (0x2E, 0x4F, 0x3A)     # hats, bow tie, blanket
BROWN = (0xB0, 0x7A, 0x2A)     # golden brown: gingerbread, reindeer, beaks, bases
BLACK = (0x2A, 0x2A, 0x2A)     # the penguin

FIGURES = {
    "santa": dict(filaments=[RED, WHITE, GREEN, BROWN]),
    "snowman": dict(filaments=[RED, WHITE, GREEN, BROWN]),
    "reindeer": dict(filaments=[RED, WHITE, GREEN, BROWN]),
    "gingerbread": dict(filaments=[RED, WHITE, GREEN, BROWN]),
    "nutcracker": dict(filaments=[RED, WHITE, GREEN, BROWN]),
    # The penguin's body is black, which the shadow filter would throw away as
    # baked-in shadow: keep only the darkest samples out.
    "penguin": dict(filaments=[RED, WHITE, BLACK, BROWN], shadow_l=4),
}
# Decimation leaves long thin triangles on the gingerbread man's flat front, and
# a triangle is painted one colour, so a sliver touching a button went red
# across the cookie: split its triangles to at most 1 mm before painting.
FIGURES["gingerbread"]["max_edge"] = 1.0


def refined(mesh, spec):
    """mesh with no edge longer than the figure's max_edge, if it has one."""
    if "max_edge" not in spec:
        return mesh
    return mesh.subdivide_to_size(spec["max_edge"], max_iter=12)


def loop(mesh, sink=LOOP_SINK):
    """A ring sunk `sink` mm into the top of the figure, its plane facing the
    front so a hook goes through it front to back. The top surface is read off
    the vertices (they are dense): the highest within 0.6 mm of each point of
    a grid around the centre line, scored down a little with distance from it."""
    from scipy.spatial import cKDTree
    r_ring, r_wire = (LOOP_HOLE + LOOP_WIRE) / 2, LOOP_WIRE / 2
    v = mesh.vertices
    near = cKDTree(v[:, :2])
    cx, cy = mesh.center_mass[:2]
    steps = np.arange(-LOOP_RADIUS, LOOP_RADIUS + 0.5)
    grid = np.array([(cx + dx, cy + dy) for dx in steps for dy in steps
                     if np.hypot(dx, dy) <= LOOP_RADIUS])
    tops = np.array([max((v[i, 2] for i in near.query_ball_point(p, 0.6)), default=-np.inf)
                     for p in grid])
    best = np.argmax(tops - 0.2 * np.hypot(*(grid - (cx, cy)).T))
    (x, y), z = grid[best], tops[best]
    ring = manifold3d.Manifold.revolve(
        manifold3d.CrossSection.circle(r_wire, mm.RES // 2).translate([r_ring, 0]), mm.RES)
    return ring.rotate([90, 0, 0]).translate([x, y, z + r_ring - sink])


def repaired(m):
    """A mesh hi3D left with an edge shared by three faces (the gingerbread
    man's base) made watertight with pymeshfix. Slow on 2M faces, about 20
    minutes, but repairing after decimation instead loses most of the
    detail. The loose fragments it leaves go the way of hi3D's own."""
    import pymeshfix
    v, f = pymeshfix.clean_from_arrays(np.ascontiguousarray(m.vertices, dtype=np.float64),
                                       np.ascontiguousarray(m.faces, dtype=np.int32))
    out = trimesh.Trimesh(v, f, process=True)
    if not out.is_watertight:
        raise SystemExit("mesh is not watertight even after pymeshfix")
    return out


def whole(name):
    """The figure as a valid manifold at HEIGHT, plus what mm.load() gave
    (the watertight full mesh and the textured vertices) for mm.make().
    hi3D meshes carry a few microscopic loose fragments: only the biggest
    piece is kept."""
    m, painted = mm.load(HERE / f"{name}.glb", HEIGHT)
    if not m.is_watertight:
        cached = CACHE / f"{name}.repaired.ply"
        if cached.exists():
            m = trimesh.load(cached)
        else:
            print(f"{name}: not watertight after merging, repairing", flush=True)
            m = repaired(m)
            CACHE.mkdir(exist_ok=True)
            m.export(cached)
    loaded = (m, painted)
    if len(m.faces) > mm.FACES:
        m = mm.decimate(m)
    solid = mm.to_manifold(m)
    if solid.status() != manifold3d.Error.NoError:
        raise SystemExit(f"{name}: not a valid manifold ({solid.status()})")
    return max(solid.decompose(), key=lambda s: s.volume()), loaded


def biggest_piece(part):
    """The half mm.make() made, without those fragments: its biggest connected
    piece, with the colours of the triangles kept."""
    mesh = part["mesh"]
    pieces = trimesh.graph.connected_components(mesh.face_adjacency, nodes=np.arange(len(mesh.faces)))
    keep = max(pieces, key=lambda p: mesh.area_faces[p].sum())
    return dict(part, mesh=mesh.submesh([keep], append=True), rgb=part["rgb"][keep])


def write(name, mesh, painted, transform, spec, suffix=""):
    """STL and painted 3MF of one form of the figure; returns the filament shares."""
    mesh.export(OUT / f"{name}{suffix}.stl")
    part = dict(name=name, mesh=mesh, rgb=mm.texture_colours(
        mesh, painted, transform, shadow_l=spec.get("shadow_l", mm.SHADOW_L)))
    label = mm.paint(part, spec["filaments"])
    mm.write_3mf(OUT / f"{name}{suffix}.3mf", mesh, label, spec["filaments"])
    share = np.bincount(label, weights=mesh.area_faces, minlength=4)
    return (share / share.sum()).round(2).tolist()


def make(name):
    spec = FIGURES[name]
    solid, loaded = whole(name)
    painted = loaded[1]
    figure = trimesh.Trimesh(**mm._arrays(solid))
    w, d, h = figure.extents
    print(f"{name}: {w:.0f} × {d:.0f} × {h:.0f} mm, {solid.volume() / 1000:.1f} cm³,",
          "T1-T4", write(name, refined(figure, spec), painted, None, spec))

    for sink in (LOOP_SINK, LOOP_SINK + 1, LOOP_SINK + 2):
        hung = solid + loop(figure, sink)
        if len(hung.decompose()) == 1:
            break
    else:
        raise SystemExit(f"{name}: the loop does not join the figure")
    ornament = trimesh.Trimesh(**mm._arrays(hung))
    print(f"  ornament {ornament.extents[2]:.0f} mm tall, T1-T4",
          write(name, refined(ornament, spec), painted, None, spec, "-ornament"))

    # mm.make() cuts the half and writes name-half.stl and name-lids.stl itself,
    # from the mesh already loaded; the half is written again without its fragments.
    half = biggest_piece(mm.make(name, folder=HERE, out=OUT, height=HEIGHT, loaded=loaded))
    if "max_edge" in spec:
        half["mesh"] = refined(half["mesh"], spec)
        half["rgb"] = mm.texture_colours(half["mesh"], painted, half["lay"],
                                         shadow_l=spec.get("shadow_l", mm.SHADOW_L))
    half["mesh"].export(OUT / f"{name}-half.stl")
    label = mm.paint(half, spec["filaments"])
    mm.write_3mf(OUT / f"{name}-half.3mf", half["mesh"], label, spec["filaments"])
    print(f"  magnet {half['row']}")


if __name__ == "__main__":
    names = sys.argv[1:] or list(FIGURES)
    if len(names) == 1:
        make(names[0])
    else:  # one process per figure: a 2M-face model's memory is not all given back
        import subprocess
        for name in names:
            subprocess.run([sys.executable, __file__, name], check=True)
