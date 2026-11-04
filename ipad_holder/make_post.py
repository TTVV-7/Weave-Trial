"""A copy of the bar the holder slides along: 10 x 10 mm square, 500 mm long,
with the real bar's cut-down tip at one end and a millimetre scale.

    python ipad_holder/make_post.py

500 mm is longer than the bed, so the bar is printed as two 250 mm halves
that butt end to end on an M8 threaded rod run down the middle (see "steel
core" below), which stiffens them and holds them together.

The tip: over the last TIP_LEN mm at the 0 end, one corner is cut off, the
cut face square to the bar's diagonal, with a step down where the cut
starts. Measured from the cut face across to the opposite corner, the bar is
TIP_BASE thick just past the step, widening to TIP_END at the very end (the
full bar is 14.1 mm corner to corner). A round dimple and a groove are cut
into the cut face. The cut corner is the top back one as printed, so the
cut face looks up at 45 degrees and needs no supports.

The scale runs 0 to 50 cm from the tip along the bed face, as a black inlay
(the first 0.4 mm, in its own part and filament), mirrored so it reads from
below: a tick every mm, longer every 5 mm, longest every cm, and each cm
numbered. The other faces are plain.

Writes ``test_post.3mf`` (both halves, with the scale) and
``test_post_male.stl`` / ``test_post_female.stl`` (one colour, no scale).
Print both as they lie, scale on the bed: no supports. A half is 250 mm,
longer than a P1S's 256 mm bed, so both lie along the bed's diagonal
(362 mm), side by side and centred; the STLs are turned the same way.
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
from phonecase.threemf import Part, parts_to_3mf               # noqa: E402

POST_SIDE = 10.0                # the real post's section, by calipers
POST_LEN = 500.0                # joined length

# --- steel core --------------------------------------------------------------
# An M8 threaded rod runs down the middle of both halves to stiffen them. The
# bore is a plain sliding fit except for CORE_THREAD_LEN mm at each outer end
# (the bottom of the tip half's blind bore, and the far end of the other
# half), threaded M8 x 1.25. Push the rod into the tip half through the joint
# end and screw the last turns in; slide the other half over the rod's free
# end and screw it on until it butts up. Both threads sit on one helix (each
# starts a whole number of pitches from the tip), so when the halves butt
# their squares line up. The bore stops CORE_START mm from the tip, short of
# the cut corner, which would break into it; cut the rod to POST_LEN -
# CORE_START (470 mm), or a millimetre or two under.
CORE_D = 8.0
CORE_PITCH = 1.25
CORE_BORE = 8.3                 # plain bore: 0.85 mm of wall at the flats
CORE_MINOR, CORE_MAJOR = 6.85, 8.3   # the threaded bore's limits (ISO minor 6.65)
CORE_THREAD_LEN = 12.5          # ten turns
CORE_START = 30.0

# --- scale ------------------------------------------------------------------
MARK_DEPTH = 0.4                # two 0.2 mm layers, inlaid or engraved
TICK_W = 0.45                   # one nozzle width: the mm ticks are 1 mm apart
TICK_LEN = {1: 2.5, 5: 3.8, 10: 5.0}    # mm, by what the mm is a multiple of
NUM_H = 2.8                     # numeral height
NUM_Y = 5.8                     # numerals start this far from the ticks' edge
SIDE_TICK_W = 0.8               # the engraved side ticks: cm and 5 mm only
BODY_RGB = (225, 225, 228)
MARK_RGB = (0, 0, 0)


# --- the tip ---------------------------------------------------------------
TIP_LEN = 24.0                  # how far back from the end the cut runs
TIP_BASE = 7.8                   # thickness where the cut starts, after the step
TIP_END = 9.3                    # thickness at the very end
# On the cut face of the real bar: a round dimple (a cut-out, where a ball
# detent drops in) with a groove running from it out to the end. Read off a
# photo, so the sizes are estimates: measure the real bar and set these.
DIMPLE_X = 16.0                 # dimple centre, from the end of the bar
DIMPLE_D = 3.2
DIMPLE_DEPTH = 1.0
GROOVE_W = 0.8
GROOVE_D = 0.4


# The cut takes off one corner, square to the bar's diagonal: the bar hangs
# turned 45 degrees in the diamond loop, cut corner up. The tip's pieces are
# drawn in a frame turned with it, where x runs along the bar, the second
# axis is the distance from the opposite corner (the one left on the bed
# edge, at y = z = 0) along the diagonal, and the third runs across the cut
# face; diag() turns that frame back onto the bar.


def diag(solid: m3.Manifold) -> m3.Manifold:
    return solid.rotate([45, 0, 0])


def tip_cutter() -> m3.Manifold:
    """What comes off the corner over the last TIP_LEN mm at x = 0: a wedge
    leaving TIP_END from the opposite corner at the end and TIP_BASE at
    x = TIP_LEN, then a straight step up to the full bar."""
    e = 1.0
    slab = lambda x, t: m3.Manifold.cube([0.01, 20.0, 30.0]).translate([x, t, -15.0])
    return diag(m3.Manifold.batch_hull([slab(-e, tip_face_z(-e)),
                                        slab(TIP_LEN, TIP_BASE)]))


def tip_face_z(x: float) -> float:
    """How far the cut face is from the opposite corner at ``x`` mm from the
    end: the bar's thickness there, measured across the diagonal."""
    return TIP_END + (TIP_BASE - TIP_END) * x / TIP_LEN


def tip_dimple() -> m3.Manifold:
    """The round cut-out in the cut face, on its centre line: a sphere
    flattened to DIMPLE_DEPTH, centred on the face."""
    r = DIMPLE_D / 2
    return diag(m3.Manifold.sphere(r, 48).scale([1, DIMPLE_DEPTH / r, 1])
                .translate([DIMPLE_X, tip_face_z(DIMPLE_X), 0]))


def tip_groove() -> m3.Manifold:
    """The groove from the dimple out to the end, following the face's slope."""
    w, d, e = GROOVE_W, GROOVE_D, 1.0
    strip = lambda x: (m3.Manifold.cube([0.01, d + e, w])
                       .translate([x, tip_face_z(x) - d, -w / 2]))
    return diag(m3.Manifold.batch_hull([strip(-e), strip(DIMPLE_X)]))


def bar(length: float) -> m3.Manifold:
    """Lying along +x from 0, one long face on the bed."""
    return m3.Manifold.cube([length, POST_SIDE, POST_SIDE])


def centred_square(side: float, length: float) -> m3.Manifold:
    """A square rod along +x from 0, on the bar's axis."""
    off = (POST_SIDE - side) / 2
    return m3.Manifold.cube([length, side, side]).translate([0, off, off])


def threaded_bore(length: float, segs: int = 72, steps: int = 16) -> m3.Manifold:
    """An internal M8 thread's cutter along +z from 0 to ``length``: the ISO
    60 degree triangle wave clipped to CORE_MINOR and CORE_MAJOR, moving along
    the helix at a constant radius."""
    P = CORE_PITCH
    H = P * math.sqrt(3) / 2
    r_pitch = (CORE_D - 0.6495 * P) / 2 + 0.1    # 0.1 mm of clearance
    r_lo = r_pitch - H / 2
    nz = int(math.ceil(length / P * steps))
    th = np.linspace(0, 2 * math.pi, segs, endpoint=False)
    z = np.linspace(0, length, nz + 1)
    T, Z = np.meshgrid(th, z)
    u = np.mod(Z - P * T / (2 * math.pi), P) / P
    R = np.clip(r_lo + H * (1 - np.abs(2 * u - 1)), CORE_MINOR / 2, CORE_MAJOR / 2)
    verts = np.c_[(R * np.cos(T)).ravel(), (R * np.sin(T)).ravel(), Z.ravel()]
    verts = np.vstack([verts, [0, 0, 0], [0, 0, length]])
    bot, top = len(verts) - 2, len(verts) - 1
    idx = np.arange((nz + 1) * segs).reshape(nz + 1, segs)
    a, b = idx[:-1], np.roll(idx[:-1], -1, axis=1)
    c, d = idx[1:], np.roll(idx[1:], -1, axis=1)
    faces = np.vstack([np.c_[a.ravel(), b.ravel(), d.ravel()],
                       np.c_[a.ravel(), d.ravel(), c.ravel()],
                       np.c_[np.full(segs, bot), np.roll(idx[0], -1), idx[0]],
                       np.c_[np.full(segs, top), idx[-1], np.roll(idx[-1], -1)]])
    mesh = trimesh.Trimesh(verts, faces, process=False)
    if mesh.volume < 0:
        mesh.invert()
    return m3.Manifold(m3.Mesh(vert_properties=np.asarray(mesh.vertices, np.float32),
                               tri_verts=np.asarray(mesh.faces, np.uint32)))


def along_axis(solid: m3.Manifold, x0: float) -> m3.Manifold:
    """A solid built along +z, turned to run along the bar's axis from x0."""
    S = POST_SIDE / 2
    return solid.rotate([0, 90, 0]).translate([x0, S, S])


def build_halves() -> tuple[m3.Manifold, m3.Manifold]:
    half, t, P = POST_LEN / 2, CORE_THREAD_LEN, CORE_PITCH
    plain = lambda x0, x1: along_axis(
        m3.Manifold.cylinder(x1 - x0, CORE_BORE / 2, CORE_BORE / 2, 64), x0)
    # Each thread starts a whole number of pitches from the tip, in joined
    # coordinates, so both are on the rod's one helix.
    m0 = math.ceil(CORE_START / P) * P
    f0 = math.floor((POST_LEN - t) / P) * P
    male = (bar(half) - tip_cutter() - tip_groove() - tip_dimple()
            - along_axis(threaded_bore(t), m0) - plain(m0 + t - 0.01, half + 1))
    female = (bar(half) - plain(-1, f0 - half + 0.01)
              - along_axis(threaded_bore(POST_LEN - f0 + 1), f0).translate([-half, 0, 0]))
    return male, female


def tick_marks(x0: float, every: int, with_numbers: bool) -> m3.CrossSection:
    """The scale on one half, on a POST_SIDE-wide face: x along the half,
    y from the ticks' edge. ``x0`` is where the half's x = 0 falls along the
    joined bar; ``every`` the tick spacing in mm (1, or 5 for the sides).
    Ticks on a half's ends are pulled in to stay whole; numbers go on every
    cm except the bar's two ends and the joint."""
    from matplotlib.font_manager import FontProperties
    from matplotlib.textpath import TextPath
    font = FontProperties(family="DejaVu Sans", weight="bold")
    half = POST_LEN / 2
    w = TICK_W if every == 1 else SIDE_TICK_W
    shapes = []
    for mm in range(int(x0), int(x0 + half) + 1, every):
        x = min(max(mm - x0, w / 2), half - w / 2)
        L = TICK_LEN[10 if mm % 10 == 0 else 5 if mm % 5 == 0 else 1]
        shapes.append(m3.CrossSection.square([w, L]).translate([x - w / 2, 0]))
        if with_numbers and mm % 10 == 0 and mm % int(half) != 0:
            tp = TextPath((0, 0), str(mm // 10), size=10, prop=font)
            text = m3.CrossSection([q for q in tp.to_polygons() if len(q) >= 3],
                                   m3.FillRule.EvenOdd)
            tx0, ty0, tx1, ty1 = text.bounds()
            text = text.scale([NUM_H / (ty1 - ty0)] * 2)
            tx0, ty0, tx1, ty1 = text.bounds()
            shapes.append(text.translate([x - (tx0 + tx1) / 2, NUM_Y - ty0]))
    return m3.CrossSection.batch_boolean(shapes, m3.OpType.Add)


def scale_parts(solid: m3.Manifold, x0: float):
    """The half with its scale: (body, black inlay). The inlay is in the bed
    face, mirrored across the bar (y -> S - y) so it reads from below. (The
    side faces had cm ticks engraved 0.4 mm deep; with the steel core the
    walls are only 0.85 mm, so they are gone.)"""
    S, d = POST_SIDE, MARK_DEPTH
    bed = (tick_marks(x0, 1, True).mirror([0, 1]).translate([0, S])
           .extrude(d + 0.01).translate([0, 0, -0.01]))
    inlay = solid ^ bed
    return solid - inlay, inlay


BED = 256.0                     # Bambu Lab P1S, square
GAP = 10.0                      # between the halves on the bed


def diagonal(solid: m3.Manifold) -> m3.Manifold:
    """Turned 45 degrees about the pair's middle and centred on the bed."""
    S, L = POST_SIDE, POST_LEN / 2
    mid = [L / 2, S + GAP / 2, 0]
    return (solid.translate([-mid[0], -mid[1], 0]).rotate([0, 0, 45])
            .translate([BED / 2, BED / 2, 0]))


def main():
    male, female = build_halves()
    half = POST_LEN / 2
    m_body, m_ink = scale_parts(male, 0.0)
    f_body, f_ink = scale_parts(female, half)
    # Side by side, 10 mm apart, then turned onto the bed's diagonal.
    gap = POST_SIDE + GAP
    f_body, f_ink = f_body.translate([0, gap, 0]), f_ink.translate([0, gap, 0])
    m_body, m_ink, f_body, f_ink = (diagonal(p) for p in (m_body, m_ink, f_body, f_ink))
    male, female = diagonal(male), diagonal(female)
    parts = [Part("Male half", 0, BODY_RGB, m_body),
             Part("Male half scale", 1, MARK_RGB, m_ink),
             Part("Female half", 0, BODY_RGB, f_body),
             Part("Female half scale", 1, MARK_RGB, f_ink)]
    with open(os.path.join(HERE, "test_post.3mf"), "wb") as f:
        f.write(parts_to_3mf(parts, origin=(0, 0), name="10 mm test post, 500 mm",
                             slicer_config=True))
    for name, solid in (("male", male), ("female", female)):
        m = solid.to_mesh()
        trimesh.Trimesh(m.vert_properties[:, :3], m.tri_verts).export(
            os.path.join(HERE, f"test_post_{name}.stl"))
    for name, solid in (("male", male), ("female", female)):
        b = solid.bounding_box()
        print(f"{name:6s} on the bed x {b[0]:.1f}..{b[3]:.1f}, y {b[1]:.1f}..{b[4]:.1f}, "
              f"up to {b[5]:.1f} mm, "
              f"genus {solid.genus()}, {len(solid.decompose())} piece")
    print(f"scale inlay {m_ink.volume() + f_ink.volume():.0f} mm3, "
          f"{len(m_ink.decompose()) + len(f_ink.decompose())} pieces")


if __name__ == "__main__":
    main()
