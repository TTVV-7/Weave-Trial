"""The iPad holder with an M5 thread in its clamp, a wing screw for it, and
two logos inlaid in the back.

    python ipad_holder/make_holder.py

Reads ``source_ipad_holder.3mf`` and the two logo SVGs next to this file and
writes ``ipad_holder.3mf``, ``wing_screw.3mf`` / ``.stl`` and ``preview.png``.

The pocket is stretched 5 mm taller and 1.5 mm deeper than the source's.
The diamond loop at the top is rebuilt as a true diamond with a 12 mm
opening, point to point, in 5 mm walls; the source's 5.2 mm hole (at
9 o'clock) goes with the old loop. An ISO-60 degree M5 x 0.8
thread is cut square through the upper-right wall instead, as near 2 o'clock
as the screw can sit and still pass into the opening without scraping the
lower-right wall. It is opened up for printing so a printed screw or a real
steel M5 both go in.

A slot in the top wall, open to the front, clears the iPad mini's top
(power) button in the top-right corner. The case's corners are rounded in
plan (the pocket's two closed corners with them, so the wall stays 3 mm),
and its front and back perimeter edges are rounded over. The source's
front-camera keyhole in the top lip is filled in. The home-button opening is
moved to where an iPad mini's button actually sits, made bigger, and
sloped. White accent lines run round the four corners of the front face.

The VanEye logo is cut 0.4 mm into the back face (the face on the bed) and
kept as its own part, so a slicer opens the file with two filaments to
assign. The printyours.ca logo is etched: the same 0.4 mm recess, left
empty. On the back both are mirrored, so they read correctly from behind.
"""

from __future__ import annotations

import math
import os
import sys

import manifold3d as m3
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from phonecase import svgart                                    # noqa: E402
from phonecase.threemf import Part, parts_to_3mf               # noqa: E402

# --- thread ---------------------------------------------------------------
PITCH = 0.8
# Extra neck length under the loop. With the screw at 9 o'clock this had to
# be 8 mm for the wings to clear the frame; at 2 o'clock they point up and
# away, so the source's neck is enough (checked in check_screw).
LOOP_RAISE = 0.0
# The loop is a true diamond: an opening DIAMOND mm point to point, across
# and up, in walls LOOP_WALL thick. Its outside is cut flat where it meets
# the neck.
DIAMOND = 12.0
LOOP_WALL = 5.0
HOLE_CLOCK = 2.0                # where the screw goes in, seen from the front
SCREW_GAP = 0.5                 # least gap between the screw and the walls
                                # of the opening as it passes through
# Radial limits of the two threads. ISO M5: internal minor 4.134, external
# major 5.0, external minor 4.019. The hole is opened and the screw shrunk
# so the two clear by about 0.12 mm on each flank.
HOLE_MINOR, HOLE_MAJOR = 4.35, 5.30
SCREW_MINOR, SCREW_MAJOR = 3.95, 4.80
FLANK_CLEAR = 0.12

# --- logos ----------------------------------------------------------------
INLAY_DEPTH = 0.4               # two 0.2 mm layers: enough to hide the base colour
ETCH_DEPTH = 0.4                # an etched logo is the same recess, left empty
# Where each logo goes, in model coordinates, and how wide its artwork is.
# An "inlay" is its own part in its own filament; an "etch" is just a recess.
LOGOS = [
    # file, keep-dark?, centre x, centre y, width, part name, display colour, kind
    ("logo_vaneye.svg", False, 189.6, -87.5, 105.0, "VanEye logo", (255, 255, 255), "inlay"),
    ("logo_printyours.svg", True, 189.6, -177.0, 42.0, "printyours.ca logo", None, "etch"),
]

# --- pocket size ----------------------------------------------------------
# Taller and deeper than the source, for a looser fit. The bottom half of the
# frame moves down POCKET_LONGER (through the plain walls at y = -100, where
# nothing is cut), and the lip and front face move up POCKET_DEEPER (from
# z = 9.6, just under the lip). The loop and the top stay where they were.
POCKET_LONGER = 5.0
POCKET_DEEPER = 1.5
STRETCH_Y = -100.0
STRETCH_Z = 9.6

# --- rounding -------------------------------------------------------------
CORNER_R = 8.0                  # the case's corners, seen from the front
EDGE_R = 1.5                    # front and back perimeter edges
# The pocket's two closed corners (the right side is open below the lip, so
# only the left ones are corners at all). Rounded concentric with the
# outside so the wall stays 3 mm; an iPad mini's corners are rounder still.
POCKET_LEFT, POCKET_BOTTOM, POCKET_TOP = 121.0, -205.1 - POCKET_LONGER, -1.1
POCKET_R = 5.0

# --- wing screw -----------------------------------------------------------
SHANK_LEN = 13.0                # threaded length: 5 mm of wall, then 8 of the
                                # 8.4 mm it can reach into the opening

# The head is drawn at a 30 mm span and scaled to WING_SPAN, so lobes, waist
# and hub keep their proportions.
WING_SPAN = 40.0
WING_K = WING_SPAN / 30.0
WING_THICK = 4.0
HUB_D, HUB_H = 10.0 * WING_K, 9.0 * WING_K


def to_manifold(mesh: trimesh.Trimesh) -> m3.Manifold:
    return m3.Manifold(m3.Mesh(vert_properties=np.asarray(mesh.vertices, np.float32),
                               tri_verts=np.asarray(mesh.faces, np.uint32)))


def to_trimesh(solid: m3.Manifold) -> trimesh.Trimesh:
    m = solid.to_mesh()
    return trimesh.Trimesh(m.vert_properties[:, :3], m.tri_verts, process=False)


# --------------------------------------------------------------------------
# threads
# --------------------------------------------------------------------------

def threaded_rod(length: float, d_minor: float, d_major: float,
                 offset: float, *, segs: int = 72, steps: int = 20) -> m3.Manifold:
    """A rod along +z from 0 to ``length`` carrying a right-hand 60 degree thread.

    The surface is a radius that depends on angle and height: the sharp ISO
    triangle wave, moved out by ``offset`` (negative shrinks it), clipped to
    the minor and major radii. Moving along the helix keeps the same radius,
    which is what makes it a thread rather than a stack of rings.
    """
    H = PITCH * math.sqrt(3) / 2
    r_pitch = (5.0 - 0.6495 * PITCH) / 2          # basic M5 pitch radius
    r_lo = r_pitch - H / 2 + offset
    nz = max(2, int(math.ceil(length / PITCH * steps)))
    th = np.linspace(0, 2 * math.pi, segs, endpoint=False)
    z = np.linspace(0, length, nz + 1)
    T, Z = np.meshgrid(th, z)
    u = np.mod(Z - PITCH * T / (2 * math.pi), PITCH) / PITCH
    tri = 1 - np.abs(2 * u - 1)
    R = np.clip(r_lo + H * tri, d_minor / 2, d_major / 2)
    verts = np.c_[(R * np.cos(T)).ravel(), (R * np.sin(T)).ravel(), Z.ravel()]
    verts = np.vstack([verts, [0, 0, 0], [0, 0, length]])
    bot, top = len(verts) - 2, len(verts) - 1
    idx = np.arange((nz + 1) * segs).reshape(nz + 1, segs)
    a, b = idx[:-1], np.roll(idx[:-1], -1, axis=1)
    c, d = idx[1:], np.roll(idx[1:], -1, axis=1)
    faces = np.vstack([np.c_[a.ravel(), b.ravel(), d.ravel()],
                       np.c_[a.ravel(), d.ravel(), c.ravel()]])
    r0, r1 = idx[0], idx[-1]
    faces = np.vstack([faces,
                       np.c_[np.full(segs, bot), np.roll(r0, -1), r0],
                       np.c_[np.full(segs, top), r1, np.roll(r1, -1)]])
    mesh = trimesh.Trimesh(verts, faces, process=False)
    if mesh.volume < 0:
        mesh.invert()
    return to_manifold(mesh)


def orient(solid: m3.Manifold, start, direction) -> m3.Manifold:
    """Turn a solid built along +z to run along ``direction`` (in the xy
    plane) from ``start``."""
    deg = math.degrees(math.atan2(direction[1], direction[0]))
    return solid.rotate([0, 90, 0]).rotate([0, 0, deg]).translate(list(start))


def hole_cutter(axis) -> m3.Manifold:
    flank = FLANK_CLEAR * 2 / math.sqrt(3)        # radial shift for that flank gap
    length = axis["wall"] + 6.0
    rod = threaded_rod(length, HOLE_MINOR, HOLE_MAJOR, +flank)
    return orient(rod, axis["inner"] - 0.5 * axis["n"], axis["n"])


# --------------------------------------------------------------------------
# holder
# --------------------------------------------------------------------------

def load_source():
    scene = trimesh.load(os.path.join(HERE, "source_ipad_holder.3mf"))
    return {name: g for name, g in scene.geometry.items()}


def stretch_frame(frame: trimesh.Trimesh) -> trimesh.Trimesh:
    """The frame made POCKET_LONGER taller and POCKET_DEEPER deeper.

    No vertex lies near either cut, so moving everything past it stretches
    only the plain walls that cross it.
    """
    v = frame.vertices.copy()
    v[v[:, 1] < STRETCH_Y, 1] -= POCKET_LONGER
    v[v[:, 2] > STRETCH_Z, 2] += POCKET_DEEPER
    return trimesh.Trimesh(v, frame.faces, process=False)


def loop_section(neck: trimesh.Trimesh) -> m3.CrossSection:
    """The diamond loop's cross-section, centred over the neck.

    The opening is a square on its point, DIAMOND across; the outside is the
    opening grown LOOP_WALL (mitred, so the corners stay sharp). Below the
    opening the outside's point is filled out to the neck's full width, so
    the loop does not hang from a narrow waist.
    """
    (nx0, _, _), (nx1, ny1, _) = neck.bounds
    h = DIAMOND / 2
    hole = m3.CrossSection([[[h, 0], [0, h], [-h, 0], [0, -h]]])
    outer = hole.offset(LOOP_WALL, m3.JoinType.Miter, 2.0)
    flat = -h - LOOP_WALL
    w = nx1 - nx0
    foot = m3.CrossSection.batch_hull([
        outer ^ m3.CrossSection.square([60, 60]).translate([-30, -h - 60]),
        m3.CrossSection.square([w, 0.01]).translate([-w / 2, flat])])
    ring = ((outer ^ m3.CrossSection.square([60, 60]).translate([-30, flat]))
            + foot) - hole
    # The flat sits 1 mm into the neck so the two fuse.
    return ring.translate([(nx0 + nx1) / 2, ny1 - 1.0 - flat + LOOP_RAISE])


def hole_axis(cs: m3.CrossSection, zc: float) -> dict:
    """Where the screw goes through the upper-right wall.

    The thread runs square to the wall so the wings seat flat. Along the wall
    it sits where a line from the opening's centre at HOLE_CLOCK meets the
    inside face, but no further toward the right corner than lets the screw
    clear the lower-right wall by SCREW_GAP as it passes into the opening.
    """
    polys = sorted((np.asarray(p) for p in cs.to_polygons()),
                   key=lambda p: -abs(_area(p)))
    outer, inner = polys[0], polys[1]
    top_i, right_i, left_i = (inner[inner[:, 1].argmax()], inner[inner[:, 0].argmax()],
                              inner[inner[:, 0].argmin()])
    top_o = outer[outer[:, 1].argmax()]
    centre = np.array([(left_i[0] + right_i[0]) / 2, (left_i[1] + right_i[1]) / 2])
    along = (right_i - top_i) / np.linalg.norm(right_i - top_i)
    n = np.array([along[1], -along[0]])          # out of the opening
    if np.dot(n, top_i - centre) < 0:
        n = -n
    mid = (top_i + right_i) / 2
    half = np.linalg.norm(right_i - top_i) / 2
    a = math.radians(HOLE_CLOCK * 30)
    ray = np.array([math.sin(a), math.cos(a)])   # clockwise from 12
    t = np.dot(mid - centre, n) / np.dot(ray, n)
    wanted = float(np.dot(centre + t * ray - mid, along))
    s = min(wanted, half - SCREW_MAJOR / 2 - SCREW_GAP)
    inner_pt = mid + s * along
    wall = float(np.dot(top_o - top_i, n))
    return {"inner": np.r_[inner_pt, zc], "n": np.r_[n, 0.0], "wall": wall,
            "shift": s, "wanted": wanted, "face": 2 * half,
            "clock": 3 + math.degrees(math.atan2(-(inner_pt - centre)[1],
                                                 (inner_pt - centre)[0])) / 30}


def _area(p) -> float:
    x, y = p[:, 0], p[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


# How far in from the frame's right-hand outside edge the slot for the top
# button runs. The iPad mini 5's button sits in this stretch; it is cut
# generously because Apple publishes no exact position.
POWER_SLOT = (9.0, 33.0)


def power_slot(frame: trimesh.Trimesh) -> m3.Manifold:
    """A slot through the top wall and its lip, from the pocket floor up and
    open to the front, so a finger reaches the button."""
    x_right = frame.bounds[1, 0]
    y_top = frame.bounds[1, 1]
    floor = 2.0                                  # back plate thickness
    x0, x1 = x_right - POWER_SLOT[1], x_right - POWER_SLOT[0]
    return (m3.Manifold.cube([x1 - x0, 12.0, 14.0])
            .translate([x0, y_top - 10.0, floor]))


def rounded_rect(x0, y0, x1, y1, r) -> m3.CrossSection:
    return (m3.CrossSection.square([x1 - x0 - 2 * r, y1 - y0 - 2 * r])
            .translate([x0 + r, y0 + r]).offset(r, m3.JoinType.Round, 2.0, 96))


def envelope(frame: trimesh.Trimesh, steps: int = 10) -> m3.Manifold:
    """The frame's outline with rounded corners and rounded-over edges.

    The outline is convex, so the rounded box is the hull of thin slices of
    it, each inset by how far the edge round has come in at that height.
    """
    (x0, y0, z0), (x1, y1, z1) = frame.bounds
    slabs = []
    for i in range(steps + 1):
        a = math.pi / 2 * i / steps
        inset = EDGE_R * (1 - math.cos(a))
        for z in (z0 + EDGE_R * (1 - math.sin(a)), z1 - EDGE_R * (1 - math.sin(a))):
            sl = rounded_rect(x0 + inset, y0 + inset, x1 - inset, y1 - inset,
                              CORNER_R - inset).extrude(1e-3)
            slabs.append(sl.translate([0, 0, min(max(z, z0), z1 - 1e-3)]))
    return m3.Manifold.batch_hull(slabs)


# The front-camera keyhole: a notch in the top wall's inside face and a hole
# through the lip above it, around x = 189. Filling it back to the wall face
# (y = -1.1) and the lip's edge (y = -5.4, from LIP_Z) leaves the top as
# plain as the rest of it.
CAMERA_X = (185.0, 193.0)


def camera_fill() -> m3.Manifold:
    x0, x1 = CAMERA_X
    wall = m3.Manifold.cube([x1 - x0, 1.2, LIP_Z + 0.05]).translate([x0, -1.1, 1.95])
    lip = m3.Manifold.cube([x1 - x0, 4.4, 2.0]).translate([x0, -5.4, LIP_Z])
    return wall + lip


# Where the iPad mini sits: slid in against the left wall, resting on the
# bottom wall as it hangs. Its 7.9" 4:3 screen leaves a 21 mm bottom bezel on
# the 203.2 mm body, and the home button (about 11 mm) is centred in it.
IPAD_W = 134.8
HOME_CENTRE = (POCKET_LEFT + IPAD_W / 2, POCKET_BOTTOM + 10.6)
HOME_HOLE_D = 15.0              # at the back of the lip, against the screen
HOME_HOLE_W = 19.0              # its width, side to side: a slot, rounded ends
HOME_SLOPE = 30.0               # degrees from the face: the gentle bevel out
LIP_Z = 9.8 + POCKET_DEEPER     # underside of the front lip


def home_fill() -> m3.Manifold:
    """Fill the source's home-button hole (10 mm, 4.7 mm too low) flush with
    the bottom lip, so the new one can be cut in the right place."""
    return (m3.Manifold.cube([14.0, 9.6, 2.0])
            .translate([181.6, -205.2 - POCKET_LONGER, LIP_Z]))


def home_cutter(z_top: float) -> m3.Manifold:
    """A slot HOME_HOLE_W wide and HOME_HOLE_D tall at the lip's underside,
    widening at HOME_SLOPE to the front face, so the lip slopes away all round
    the button. It is the hull of two cones, one at each rounded end."""
    r0 = HOME_HOLE_D / 2
    h = z_top - LIP_Z
    r1 = r0 + h / math.tan(math.radians(HOME_SLOPE))
    cone = m3.Manifold.cylinder(h + 0.02, r0, r1 + 0.02 / math.tan(math.radians(HOME_SLOPE)), 128)
    dx = (HOME_HOLE_W - HOME_HOLE_D) / 2
    slot = m3.Manifold.batch_hull([cone.translate([-dx, 0, 0]), cone.translate([dx, 0, 0])])
    return slot.translate([*HOME_CENTRE, LIP_Z - 0.01])


# --- colours --------------------------------------------------------------
BODY_RGB = (0, 0, 0)            # filament 1; the VanEye inlay is filament 2

# --- front accent lines ---------------------------------------------------
# Off: the front is plain body colour. On, the lines are their own part in
# another filament.
FRONT_LINES = False
LINE_DEPTH = 0.4                # the last two layers, in a second filament
LINE_W = 0.8                    # two nozzle widths
LINE_IN = 3.0                   # from the case's outer edge
LINE_LEN = 35.0                 # along each side from each corner
LINE_MARGIN = 0.7               # kept clear of every edge and opening


def front_lines(body: m3.Manifold, frame: trimesh.Trimesh) -> m3.CrossSection:
    """Corner accents: a line following the rounded outline LINE_IN from the
    edge, kept only within LINE_LEN of each corner, on the flat front face."""
    (x0, y0, _), (x1, y1, z1) = frame.bounds
    outer = rounded_rect(x0, y0, x1, y1, CORNER_R)
    ring = (outer.offset(-LINE_IN, m3.JoinType.Round)
            - outer.offset(-LINE_IN - LINE_W, m3.JoinType.Round))
    keep = body.slice(z1 - 0.05).offset(-LINE_MARGIN, m3.JoinType.Round)
    L = LINE_LEN
    boxes = [m3.CrossSection.square([L, L]).translate([x, y])
             for x, y in ((x0, y1 - L), (x1 - L, y1 - L), (x0, y0), (x1 - L, y0))]
    return ring ^ keep ^ m3.CrossSection.batch_boolean(boxes, m3.OpType.Add)


def pocket_fillets(frame: trimesh.Trimesh) -> m3.Manifold:
    """Material filling the pocket's two left corners out to POCKET_R."""
    z1 = frame.bounds[1, 2]
    r = POCKET_R
    # Reaching 0.1 mm into the walls so the fill fuses with them rather
    # than meeting them face to face.
    fill = (m3.CrossSection.square([r + 0.1, r + 0.1]).translate([-0.1, -0.1])
            - m3.CrossSection.circle(r, 96).translate([r, r]))
    corners = [fill.translate([POCKET_LEFT, POCKET_BOTTOM]),
               fill.mirror([0, 1]).translate([POCKET_LEFT, POCKET_TOP])]
    cs = m3.CrossSection.batch_boolean(corners, m3.OpType.Add)
    return cs.extrude(z1 - 2.0 + 1e-3).translate([0, 0, 2.0 - 1e-3])


def logo_region(path: str, keep_dark: bool, cx: float, cy: float,
                width: float) -> m3.CrossSection:
    """The logo's ink as a 2-D region, placed and mirrored for the back face.

    Painter's rule from the top of the stack down: each shape counts only
    where nothing drawn after it covers it, and only the ink colour is kept
    (dark on a light logo, light on a dark one).
    """
    art = svgart.load_file(path, flatness=0.02)
    covered, ink = m3.CrossSection(), []
    for shape in reversed(art.shapes):
        loops = [sp for sp in shape.subpaths if len(sp) >= 3]
        if not loops:
            continue
        rule = m3.FillRule.EvenOdd if shape.even_odd else m3.FillRule.NonZero
        poly = m3.CrossSection(loops, rule)
        visible = poly - covered
        covered = covered + poly
        r, g, b = shape.rgb
        dark = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255 < 0.45
        if dark == keep_dark and not visible.is_empty():
            ink.append(visible)
    region = m3.CrossSection.batch_boolean(ink, m3.OpType.Add)
    x0, y0, x1, y1 = region.bounds()
    s = width / (x1 - x0)
    # Seen from behind, the model's +x runs to the viewer's left; the SVG's
    # y runs down. Scaling both by -s reads the right way round from the back.
    region = (region.translate([-(x0 + x1) / 2, -(y0 + y1) / 2])
                    .scale([-s, -s]).translate([cx, cy]))
    # Drop specks no nozzle could lay down.
    return m3.CrossSection.batch_boolean(
        [p for p in region.decompose() if p.area() > 0.05], m3.OpType.Add)


def build_holder(info: dict | None = None):
    src = load_source()
    names = sorted(src, key=lambda n: -src[n].volume)
    frame, loop, neck = (src[n] for n in names)
    frame = stretch_frame(frame)
    # The neck is a plain box; stretch it upwards and carry the loop with it.
    (nx0, ny0, nz0), (nx1, ny1, nz1) = neck.bounds
    # It also starts 1 mm inside the frame wall: in the source it only touches
    # the frame face to face, which leaves it a separate solid.
    neck_box = (m3.Manifold.cube([nx1 - nx0, ny1 - ny0 + LOOP_RAISE + 1.0, nz1 - nz0])
                .translate([nx0, ny0 - 1.0, nz0]))
    z0, z1 = loop.bounds[:, 2]
    cs = loop_section(neck)
    axis = hole_axis(cs, (z0 + z1) / 2)
    case = ((to_manifold(frame) + pocket_fillets(frame) + camera_fill()
             + home_fill()) ^ envelope(frame)) - home_cutter(frame.bounds[1, 2])
    body = m3.Manifold.batch_boolean(
        [case, cs.extrude(z1 - z0).translate([0, 0, z0]), neck_box], m3.OpType.Add)
    body = body - hole_cutter(axis) - power_slot(frame)
    if info is not None:
        info["axis"] = axis

    inlays = []
    for fname, keep_dark, cx, cy, w, label, rgb, kind in LOGOS:
        region = logo_region(os.path.join(HERE, fname), keep_dark, cx, cy, w)
        if kind == "etch":
            body = body - region.extrude(ETCH_DEPTH)
            continue
        solid = body ^ region.extrude(INLAY_DEPTH)
        inlays.append((label, rgb, solid))
    z1 = frame.bounds[1, 2]
    if FRONT_LINES:
        lines = body ^ front_lines(body, frame).extrude(LINE_DEPTH).translate(
            [0, 0, z1 - LINE_DEPTH])
        inlays.append(("Front lines", (245, 245, 245), lines))
    for _, _, solid in inlays:
        body = body - solid

    parts = [Part("Holder", 0, BODY_RGB, body)]
    parts += [Part(label, i + 1, rgb, solid)
              for i, (label, rgb, solid) in enumerate(inlays)]
    return parts


# --------------------------------------------------------------------------
# wing screw
# --------------------------------------------------------------------------

def build_screw() -> m3.Manifold:
    """Printed head-down: wings flat on the bed, thread pointing up."""
    flank = FLANK_CLEAR * 2 / math.sqrt(3)
    # Wings: a bow-tie outline in the xz plane, extruded WING_THICK in y.
    k = WING_K
    lobe = m3.CrossSection.circle(4.5 * k, 64)
    wing = m3.CrossSection.batch_hull([
        m3.CrossSection.square([HUB_D, HUB_H]).translate([-HUB_D / 2, 0]),
        lobe.translate([-(WING_SPAN / 2 - 4.5 * k), 4.5 * k]),
        lobe.translate([+(WING_SPAN / 2 - 4.5 * k), 4.5 * k]),
    ])
    # Waist the outline between hub and lobes so it reads as two wings.
    waist = m3.CrossSection.circle(6.0 * k, 64)
    wing = (wing - waist.translate([-8.6 * k, HUB_H + 3.2 * k])
            - waist.translate([8.6 * k, HUB_H + 3.2 * k]))
    wings = (wing.extrude(WING_THICK).translate([0, 0, -WING_THICK / 2])
             .rotate([90, 0, 0]))
    hub = m3.Manifold.cylinder(HUB_H, HUB_D / 2, HUB_D / 2, 64)
    collar = m3.Manifold.cylinder(1.0, 4.5, 4.5, 64).translate([0, 0, HUB_H])
    rod = threaded_rod(SHANK_LEN, SCREW_MINOR, SCREW_MAJOR, -flank)
    # Chamfer the tip so the thread starts cleanly.
    tip = m3.Manifold.cylinder(SHANK_LEN, SCREW_MAJOR / 2 + SHANK_LEN - 0.6,
                               SCREW_MAJOR / 2 - 0.6, 64)
    rod = (rod ^ tip).translate([0, 0, HUB_H + 1.0])
    return m3.Manifold.batch_boolean([wings, hub, collar, rod], m3.OpType.Add)


def seat_screw(screw: m3.Manifold, axis: dict, spin: float = 0.0,
               backoff: float = 0.0) -> m3.Manifold:
    """The screw in the clamp, turned ``spin`` degrees, bearing face on the
    loop (or ``backoff`` mm short of it)."""
    face = axis["inner"] + axis["n"] * (axis["wall"] + backoff)
    s = screw.rotate([0, 0, spin]).translate([0, 0, -(HUB_H + 1.0)])
    return orient(s, face, -axis["n"])


def check_screw(body: m3.Manifold, screw: m3.Manifold, axis: dict) -> dict:
    """Does the screw turn, and does it go in?

    The head is turned a full revolution in 5 degree steps against the
    holder, 0.3 mm off its seat; then a rod the screw's full diameter is
    pushed from the inside face across the opening until it meets the loop,
    which is how far the screw can reach to clamp something.
    """
    head = screw ^ m3.Manifold.cube([80, 80, HUB_H + 1.0]).translate([-40, -40, 0])
    hits = [deg for deg in range(0, 360, 5)
            if (seat_screw(head, axis, deg, 0.3) ^ body).volume() > 1e-3]
    reach = 0.0
    while reach < axis["face"]:
        rod = m3.Manifold.cylinder(reach + 0.1, SCREW_MAJOR / 2, SCREW_MAJOR / 2, 48)
        if (orient(rod, axis["inner"] - 0.05 * axis["n"], -axis["n"]) ^ body).volume() > 1e-3:
            break
        reach += 0.1
    lowest = min(seat_screw(head, axis, deg, 0.3).bounding_box()[1]
                 for deg in range(0, 360, 5))
    return {"hits": hits, "reach": reach, "lowest_wing_y": lowest}


# --------------------------------------------------------------------------
# output
# --------------------------------------------------------------------------

def preview(parts, screw, axis, reach, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import PathPatch
    from matplotlib.path import Path
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    fig = plt.figure(figsize=(20, 7))
    light = np.array([0.3, -0.5, 0.8]) / np.linalg.norm([0.3, -0.5, 0.8])

    def draw(ax, meshes, view):
        for mesh, rgb in meshes:
            shade = np.clip(np.abs(mesh.face_normals @ light), 0.25, 1)[:, None]
            ax.add_collection3d(Poly3DCollection(
                mesh.triangles, facecolors=np.c_[np.array(rgb) / 255 * shade,
                                                 np.ones(len(shade))],
                edgecolor="none"))
        allv = np.vstack([m.vertices for m, _ in meshes])
        c, r = allv.mean(0), (allv.max(0) - allv.min(0)).max() / 2
        ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r)
        ax.set_zlim(c[2] - r, c[2] + r); ax.view_init(*view); ax.set_axis_off()

    def fill(ax, cs, colour):
        loops = cs.to_polygons()
        if not loops:
            return
        verts = np.vstack([np.vstack([lp, lp[:1]]) for lp in loops])
        codes = []
        for lp in loops:
            codes += [Path.MOVETO] + [Path.LINETO] * (len(lp) - 1) + [Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(verts, codes), fc=colour, ec="k", lw=0.4))

    meshes = [(to_trimesh(p.solid), p.rgb) for p in parts]
    ax = fig.add_subplot(1, 3, 1, projection="3d"); ax.set_title("Back (logos)")
    draw(ax, meshes, (-90, 90))              # from below: the back face

    # The screw as far in as it goes: through the wall and `reach` across.
    seated = seat_screw(screw, axis, 0, SHANK_LEN - axis["wall"] - reach)
    z = axis["inner"][2]
    ax = fig.add_subplot(1, 3, 2)
    ax.set_title("Front, cut through the thread: clamp at 2 o'clock, "
                 "button slot top right", fontsize=10)
    fill(ax, parts[0].solid.slice(z), "#%02x%02x%02x" % parts[0].rgb)
    fill(ax, seated.slice(z), "#c8c8c8")
    ax.set_xlim(165, 265); ax.set_ylim(-12, 42); ax.set_aspect("equal")
    ax.set_xlabel("mm"); ax.grid(True, lw=0.3)

    ax = fig.add_subplot(1, 3, 3, projection="3d"); ax.set_title("Wing screw")
    draw(ax, [(to_trimesh(screw), (200, 200, 200))], (15, -60))
    plt.savefig(path, dpi=110, bbox_inches="tight")


def main():
    info = {}
    parts = build_holder(info)
    screw = build_screw()
    axis = info["axis"]
    lo = np.min([p.solid.bounding_box()[:3] for p in parts], axis=0)
    with open(os.path.join(HERE, "ipad_holder.3mf"), "wb") as f:
        f.write(parts_to_3mf(parts, origin=(10 - lo[0], 10 - lo[1]),
                             name="iPad holder", slicer_config=True))
    with open(os.path.join(HERE, "wing_screw.3mf"), "wb") as f:
        f.write(parts_to_3mf([Part("Wing screw", 0, (200, 200, 200), screw)],
                             origin=(20, 20), name="M5 wing screw"))
    to_trimesh(screw).export(os.path.join(HERE, "wing_screw.stl"))
    for p in parts:
        print(f"{p.name:20s} volume {p.solid.volume():9.1f} mm3  "
              f"genus {p.solid.genus()}")
    print(f"{'Wing screw':20s} volume {screw.volume():9.1f} mm3  "
          f"height {screw.bounding_box()[5]:.1f} mm")
    print(f"loop wall {axis['wall']:.2f} mm, inside face {axis['face']:.2f} mm; "
          f"screw at {axis['clock']:.2f} o'clock, {axis['shift']:.2f} mm off the "
          f"face's centre ({axis['wanted']:.2f} wanted for exactly {HOLE_CLOCK:g})")
    chk = check_screw(parts[0].solid, screw, axis)
    print(f"wings hit the holder at {len(chk['hits'])} of 72 turns {chk['hits'][:6]}; "
          f"screw reaches {chk['reach']:.1f} mm into the opening; lowest wing "
          f"{chk['lowest_wing_y'] - 1.9:.1f} mm above the frame")
    preview(parts, screw, axis, chk["reach"], os.path.join(HERE, "preview.png"))


if __name__ == "__main__":
    main()
