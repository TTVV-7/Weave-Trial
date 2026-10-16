"""Renolux logo in 3D: the building as a slab cube on a block carrying the text.

    python3 mirror_hanger/make_cube.py [logo.jpg] [--out mirror_hanger/out3d]

The cube is built from horizontal slabs with recessed black grooves between
them, turned 45 degrees so a corner points at the viewer like the logo: the
face on the left is white, the face on the right red. The back carries the
same pair, so it reads the same from behind. A doorway is cut into the white
face. RENOLUX (white) and CONTRACTING (red) are raised on the block's front
(and back), reusing the 2-D outlines, minimum-width thickening included,
from make_hanger.py.

Prints upright, block on the bed, without supports: the block is at least as
deep as the cube's diagonal, so nothing overhangs except the 1 mm groove
ledges, the doorway lintel and the hanging hole -- all short bridges.

Writes black_part.stl, white_part.stl, red_part.stl, cube.3mf (one object,
three parts on extruders 1/2/3) and preview.png, all in one coordinate
system: x across, y front-to-back (front at -y), z up, bed at z=0.
"""
import argparse
import os
import sys

import manifold3d as mf
import numpy as np
import trimesh
from shapely import affinity
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_hanger as flat  # noqa: E402

# ============================ dimensions (mm) ==============================
CUBE_SIZE = 20.0           # cube edge length (it is this tall, too)
SLABS = 9                  # number of horizontal slabs
SLAB_FRACTION = 0.6        # slab share of each slab+groove pitch
GROOVE_DEPTH = 1.0         # how far the black core sits behind the slabs
SKIN = 1.6                 # depth of colour on each face (4 perimeters)

DOOR = True                # doorway in the white (front-left) face
DOOR_CENTRE = 0.35         # along the face, 0 = back edge, 1 = front corner
DOOR_WIDTH = 0.28          # fraction of the face
DOOR_HEIGHT = 0.42         # fraction of the cube height
DOOR_DEPTH = 3.5           # recess depth; its back wall is red
DOOR_BACK = 1.0            # thickness of that red back wall

TEXT_WIDTH = 70.0          # width of RENOLUX on the block; below
                           # ~70 the O of CONTRACTING fills in
TEXT_MARGIN = 2.5          # block edge to text, top and bottom
SIDE_MARGIN = 3.0          # block edge to text, left and right
BLOCK_DEPTH = None         # None = just deep enough for the turned cube
BLOCK_CORNER = 2.0         # rounding of the block's vertical edges
RAISE = 0.8                # text height above the block faces
BACK_TEXT = True           # mirror the text onto the back face too

HANG_TAB = True            # tab with a hole on top of the cube
HOLE_DIAMETER = 4.0
HOLE_WALL = 2.5
TAB_THICKNESS = 3.0
TAB_GAP = 1.0              # hole edge to cube top

ARC_SEGMENTS = 16
COLOURS = flat.COLOURS     # black/white/red display colour + extruder
# ===========================================================================


# ------------------------------------------------------------ mesh helpers
def to_manifold(tm):
    mesh = mf.Mesh(vert_properties=np.asarray(tm.vertices, np.float32),
                   tri_verts=np.asarray(tm.faces, np.uint32))
    m = mf.Manifold(mesh)
    assert m.status() == mf.Error.NoError, m.status()
    return m


def to_trimesh(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(mesh.vert_properties[:, :3], mesh.tri_verts,
                           process=True)


def prism(g, h, z0=0.0):
    """Shapely region -> Manifold prism from z0 to z0+h."""
    parts = [to_manifold(trimesh.creation.extrude_polygon(p, h))
             for p in flat.as_polys(g)]
    if not parts:
        return mf.Manifold()
    return mf.Manifold.batch_boolean(parts, mf.OpType.Add).translate((0, 0, z0))


def box3(x0, x1, y0, y1, z0, z1):
    return mf.Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))


def place(m, matrix, offset):
    """Apply a 3x3 rotation (proper, det +1) and a translation."""
    t = np.zeros((3, 4))
    t[:, :3] = matrix
    t[:, 3] = offset
    return m.transform(t)


# --------------------------------------------------------------------- cube
def cube_parts():
    """Black/white/red solids of the slab cube, axis-aligned, centred on
    the origin at z = 0..CUBE_SIZE. The -x face is the front-left one."""
    s, n, f = CUBE_SIZE, SLABS, SLAB_FRACTION
    pitch = s / (n * f + (n - 1) * (1 - f))
    t, g = f * pitch, (1 - f) * pitch
    h = s / 2
    inner = h - GROOVE_DEPTH - SKIN               # half-size of black at slabs
    core = h - GROOVE_DEPTH                       # half-size of the core
    assert inner > 0, "GROOVE_DEPTH + SKIN leave no core"

    ring = box(-h, -h, h, h).difference(box(-inner, -inner, inner, inner))
    big = 2 * s                                   # diagonal split: x faces
    x_tris = unary_union([Polygon([(0, 0), (-big, -big), (-big, big)]),
                          Polygon([(0, 0), (big, big), (big, -big)])])
    white_ring, red_ring = ring.intersection(x_tris), ring.difference(x_tris)

    zs = [i * pitch for i in range(n)]
    white = mf.Manifold.batch_boolean([prism(white_ring, t, z) for z in zs],
                                      mf.OpType.Add)
    red = mf.Manifold.batch_boolean([prism(red_ring, t, z) for z in zs],
                                    mf.OpType.Add)
    black = prism(box(-core, -core, core, core), s)
    black = black - white - red

    if DOOR:
        # on the -x face; its y runs from +h (back edge) to -h (front corner)
        yc = h - DOOR_CENTRE * s
        w = DOOR_WIDTH * s / 2
        dz = DOOR_HEIGHT * s
        hole = box3(-h - 1, -h + DOOR_DEPTH, yc - w, yc + w, -1, dz)
        back = box3(-h + DOOR_DEPTH - 1e-3, -h + DOOR_DEPTH + DOOR_BACK,
                    yc - w, yc + w, 0, dz)
        white, red = white - hole, red - hole
        black = black - hole - back
        red = red + (back - hole)
    return black, white, red, t, g


# ------------------------------------------------------------------- text
def text_regions():
    """RENOLUX / CONTRACTING outlines from the flat pipeline, thickened at
    the size they will be printed, centred on x = 0, bottom at v = 0."""
    flat.OVERALL_WIDTH = TEXT_WIDTH + 2 * flat.MARGIN
    _, white, red, _, report, info = flat.build(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "logo.jpg")
        if LOGO is None else LOGO)
    building_bottom = info["band_y"][0][0]
    pick = lambda g: unary_union([p for p in flat.as_polys(g)
                                  if p.centroid.y < building_bottom - 0.5])
    tw, tr = pick(white), pick(red)
    minx, miny, maxx, maxy = unary_union([tw, tr]).bounds
    move = lambda g: affinity.translate(g, -(minx + maxx) / 2, -miny)
    text_report = [r for r in report if r[1] != "building"]
    # holes lost anywhere: the building has none, so these are letters
    filled = {c: n for c, n in info["counters_filled"].items() if n > 0}
    return move(tw), move(tr), maxx - minx, maxy - miny, (text_report, filled)


def on_face(region, front, y_face, z0):
    """2-D text (u across, v up) -> raised solid on the block's front or
    back face. Mirrored on the back so it reads correctly from behind."""
    m = prism(region, RAISE)                       # (u, v, w)
    if front:   # (u, v, w) -> (u, y_face - w, v + z0)
        rot = [[1, 0, 0], [0, 0, -1], [0, 1, 0]]
    else:       # (u, v, w) -> (-u, y_face + w, v + z0)
        rot = [[-1, 0, 0], [0, 0, 1], [0, 1, 0]]
    return place(m, rot, (0, y_face, z0))


# ---------------------------------------------------------------- assembly
def build():
    tw, tr, text_w, text_h, report = text_regions()
    block_w = text_w + 2 * SIDE_MARGIN
    block_h = text_h + 2 * TEXT_MARGIN
    diag = CUBE_SIZE * np.sqrt(2)
    depth = BLOCK_DEPTH or np.ceil(diag + 2 * BLOCK_CORNER)
    assert depth >= diag, "BLOCK_DEPTH too small: the cube would overhang"
    assert block_w >= diag, "block narrower than the cube's diagonal"

    plan = box(-block_w / 2, -depth / 2, block_w / 2, depth / 2)
    r = BLOCK_CORNER
    plan = plan.buffer(-r, quad_segs=ARC_SEGMENTS).buffer(r, quad_segs=ARC_SEGMENTS)
    black = prism(plan, block_h)
    white = on_face(tw, True, -depth / 2, TEXT_MARGIN)
    red = on_face(tr, True, -depth / 2, TEXT_MARGIN)
    if BACK_TEXT:
        white = white + on_face(tw, False, depth / 2, TEXT_MARGIN)
        red = red + on_face(tr, False, depth / 2, TEXT_MARGIN)

    cb, cw, cr, slab_t, groove_t = cube_parts()
    # turn 45 degrees so the (-x, -y) corner points at the viewer (-y):
    # -x becomes the front-left face (white), -y the front-right (red)
    turn = lambda m: m.rotate((0, 0, 45)).translate((0, 0, block_h))
    black = black + turn(cb)
    white = white + turn(cw)
    red = red + turn(cr)
    top = block_h + CUBE_SIZE

    if HANG_TAB:
        hr = HOLE_DIAMETER / 2
        tab_r = (hr + HOLE_WALL) / np.cos(np.pi / (4 * ARC_SEGMENTS))
        hz = TAB_GAP + hr + 0.0                     # hole centre above cube top
        prof = unary_union([Point(0, hz).buffer(tab_r, quad_segs=ARC_SEGMENTS),
                            box(-tab_r, -0.5, tab_r, hz)])
        prof = prof.difference(Point(0, hz).buffer(hr, quad_segs=ARC_SEGMENTS))
        # profile in the x-z plane, TAB_THICKNESS along y, sunk 0.5 mm into
        # the black centre of the cube's top slab
        tab = place(prism(prof, TAB_THICKNESS),
                    [[1, 0, 0], [0, 0, -1], [0, 1, 0]],
                    (0, TAB_THICKNESS / 2, top))
        black = black + tab
        top = top + hz + tab_r

    info = dict(block=(block_w, depth, block_h), top=top, slab=slab_t,
                groove=groove_t, text=(text_w, text_h), report=report[0],
                filled=report[1])
    return black, white, red, info


# ----------------------------------------------------------------- preview
def render(meshes, azim, elev, px=900, pad=0.06):
    """Orthographic z-buffer render -> RGB image. azim 0 looks from the
    front (-y), 90 from the right (+x), 180 from the back."""
    a, e = np.radians(azim), np.radians(elev)
    # camera basis: `fwd` points from the viewer into the scene
    fwd = np.array([-np.sin(a) * np.cos(e), np.cos(a) * np.cos(e), -np.sin(e)])
    right = np.array([np.cos(a), np.sin(a), 0.0])
    up = np.cross(right, fwd)
    light = -fwd + np.array([0, 0, 0.6]) - right * 0.4
    light /= np.linalg.norm(light)

    allv = np.vstack([m.vertices for m in meshes.values()])
    sx, sy = allv @ right, allv @ up
    span = max(np.ptp(sx), np.ptp(sy)) * (1 + 2 * pad)
    k = px / span
    w = int(np.ceil(np.ptp(sx) * (1 + 2 * pad) * k))
    h = int(np.ceil(np.ptp(sy) * (1 + 2 * pad) * k))
    ox, oy = sx.min() - np.ptp(sx) * pad, sy.max() + np.ptp(sy) * pad
    img = np.full((h, w, 3), 0.82)
    depth = np.full((h, w), np.inf)
    for name, m in meshes.items():
        base = np.array(COLOURS[name][0]) / 255
        v = m.vertices
        X, Y, Z = (v @ right - ox) * k, (oy - v @ up) * k, v @ fwd
        for f, n in zip(m.faces, m.face_normals):
            if n @ fwd >= 0:
                continue                                  # back face
            x, y, z = X[f], Y[f], Z[f]
            x0, x1 = max(int(x.min()), 0), min(int(x.max()) + 1, w - 1)
            y0, y1 = max(int(y.min()), 0), min(int(y.max()) + 1, h - 1)
            if x1 < x0 or y1 < y0:
                continue
            gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5,
                                 np.arange(y0, y1 + 1) + 0.5)
            d = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
            if abs(d) < 1e-12:
                continue
            l0 = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / d
            l1 = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / d
            l2 = 1 - l0 - l1
            inside = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
            zz = l0 * z[0] + l1 * z[1] + l2 * z[2]
            sub = depth[y0:y1 + 1, x0:x1 + 1]
            hit = inside & (zz < sub)
            sub[hit] = zz[hit]
            shade = 0.35 + 0.65 * max(n @ light, 0)
            img[y0:y1 + 1, x0:x1 + 1][hit] = np.clip(base * shade + 0.03, 0, 1)
    return img


def write_preview(path, meshes):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    views = (("front, three-quarter", -35, 22), ("front", 0, 8),
             ("back", 180, 8))
    fig, axs = plt.subplots(1, 3, figsize=(18, 6.5), facecolor="#d1d1d1")
    for ax, (title, azim, elev) in zip(axs, views):
        ax.imshow(render(meshes, azim, elev))
        ax.set_title(title)
        ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(path, dpi=130, facecolor=fig.get_facecolor())
    plt.close(fig)


# -------------------------------------------------------------------- main
LOGO = None


def main():
    global LOGO
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("logo", nargs="?", default=os.path.join(here, "logo.jpg"))
    ap.add_argument("--out", default=os.path.join(here, "out3d"))
    a = ap.parse_args()
    LOGO = a.logo
    os.makedirs(a.out, exist_ok=True)

    black, white, red, info = build()

    # the three parts must touch, never overlap
    for x, y, nx, ny in ((black, white, "black", "white"),
                         (black, red, "black", "red"),
                         (white, red, "white", "red")):
        v = (x ^ y).volume()
        assert v < 1e-3, f"{nx} and {ny} overlap by {v:.4f} mm3"

    if info["report"]:
        print(f"WARNING: text thinner than {flat.MIN_FEATURE} mm was thickened:")
        for colour, name, n, med, lo, area in info["report"]:
            print(f"  {colour:5s} {name:12s} {n:3d} shape(s): typical thin stroke "
                  f"{med:.2f} mm, thinnest {lo:.2f} mm, +{area:.1f} mm2 added")
    for colour, n in info["filled"].items():
        print(f"WARNING: {colour}: {n} hole(s) inside letters filled in; "
              "raise TEXT_WIDTH to keep them")
    if info["groove"] < 0.6:
        print(f"WARNING: grooves are only {info['groove']:.2f} mm tall")

    meshes = {"black": to_trimesh(black), "white": to_trimesh(white),
              "red": to_trimesh(red)}
    names = {"black": "black_part", "white": "white_part", "red": "red_part"}
    for k, m in meshes.items():
        m.export(os.path.join(a.out, names[k] + ".stl"))
        print(f"{names[k]}.stl  {len(m.faces):6d} tris  watertight={m.is_watertight}"
              f"  volume={m.volume / 1000:.2f} cm3")
    flat.write_3mf(os.path.join(a.out, "cube.3mf"),
                   [(names[k], meshes[k], *COLOURS[k])
                    for k in ("black", "white", "red")],
                   title="Renolux cube")
    write_preview(os.path.join(a.out, "preview.png"), meshes)

    bw, bd, bh = info["block"]
    allv = np.vstack([m.vertices for m in meshes.values()])
    size = allv.max(0) - allv.min(0)
    print(f"block {bw:.1f} x {bd:.1f} x {bh:.1f} mm; cube {CUBE_SIZE:.0f} mm, "
          f"{SLABS} slabs of {info['slab']:.2f} mm with {info['groove']:.2f} mm "
          f"grooves; overall {size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} mm")
    print(f"wrote {a.out}/: black_part.stl white_part.stl red_part.stl "
          "cube.3mf preview.png")


if __name__ == "__main__":
    main()
