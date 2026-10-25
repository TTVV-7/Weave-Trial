"""A copy of the bar the holder slides along: 10 x 10 mm square, 400 mm long,
with the real bar's cut-down tip at one end and a millimetre scale.

    python ipad_holder/make_post.py

400 mm is longer than the bed, so the bar is printed as two 200 mm halves
that join with a square peg: the male half carries the peg on its inner end,
the female half a socket to take it. Square, so the halves cannot turn. A
drop of glue in the socket makes it permanent.

The tip: over the last TIP_LEN mm at the 0 end, the top face is cut down
with a square step, leaving the bar TIP_BASE thick where the cut starts and
TIP_END at the very end -- both 7.8 mm now, so it is flat, 20.3 mm long
inside to inside, measured off the real bar. (Set them apart for a taper.)

The scale runs 0 to 40 cm from the tip along the bed face, as a black inlay
(the first 0.4 mm, in its own part and filament), mirrored so it reads from
below: a tick every mm, longer every 5 mm, longest every cm, and each cm
numbered. The two side faces carry the cm and 5 mm ticks engraved 0.4 mm
deep, without numbers. The top face is plain.

Writes ``test_post.3mf`` (both halves, with the scale) and
``test_post_male.stl`` / ``test_post_female.stl`` (one colour, no scale).
Print both as they lie, scale on the bed: no supports.
"""

from __future__ import annotations

import os
import sys

import manifold3d as m3
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from phonecase.threemf import Part, parts_to_3mf               # noqa: E402

POST_SIDE = 10.0                # the real post's section, by calipers
POST_LEN = 400.0                # joined length, peg hidden in the socket
PEG_SIDE = 5.0                  # leaves 2.5 mm of wall round the socket
PEG_LEN = 15.0
PEG_CHAMFER = 0.6               # on the peg's tip, so it finds the socket
FIT = 0.15                      # clearance each side, socket over peg
SOCKET_EXTRA = 0.5              # socket deeper than the peg, so the faces meet

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
TIP_LEN = 20.3                  # how far back from the end the cut runs
TIP_BASE = 7.8                  # thickness where the cut starts, after the step
TIP_END = 7.8                   # thickness at the very end


def tip_cutter() -> m3.Manifold:
    """What comes off the top face over the last TIP_LEN mm at x = 0: a wedge
    from TIP_END thick at the end to TIP_BASE at x = TIP_LEN, then a straight
    step up to the full bar."""
    S, e = POST_SIDE, 1.0
    at_end = (m3.Manifold.cube([0.01, S + 2 * e, S - TIP_END + e])
              .translate([-e, -e, TIP_END]))
    at_step = (m3.Manifold.cube([0.01, S + 2 * e, S - TIP_BASE + e])
               .translate([TIP_LEN, -e, TIP_BASE]))
    return m3.Manifold.batch_hull([at_end, at_step])


def bar(length: float) -> m3.Manifold:
    """Lying along +x from 0, one long face on the bed."""
    return m3.Manifold.cube([length, POST_SIDE, POST_SIDE])


def centred_square(side: float, length: float) -> m3.Manifold:
    """A square rod along +x from 0, on the bar's axis."""
    off = (POST_SIDE - side) / 2
    return m3.Manifold.cube([length, side, side]).translate([0, off, off])


def build_halves() -> tuple[m3.Manifold, m3.Manifold]:
    half = POST_LEN / 2
    # Peg: a square rod with its tip chamfered (the hull of the full square
    # and a smaller one at the end).
    c = PEG_CHAMFER
    body = centred_square(PEG_SIDE, PEG_LEN - c)
    tip = (centred_square(PEG_SIDE - 2 * c, 0.01)
           .translate([PEG_LEN - 0.01, 0, 0]))
    peg = m3.Manifold.batch_hull([body, tip])
    male = bar(half) + peg.translate([half - 0.01, 0, 0]) - tip_cutter()
    socket = centred_square(PEG_SIDE + 2 * FIT, PEG_LEN + SOCKET_EXTRA + 0.01)
    female = bar(half) - socket.translate([-0.01, 0, 0])
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
    face, mirrored across the bar (y -> S - y) so it reads from below; the
    side faces' ticks are engraved into the body."""
    S, d = POST_SIDE, MARK_DEPTH
    bed = (tick_marks(x0, 1, True).mirror([0, 1]).translate([0, S])
           .extrude(d + 0.01).translate([0, 0, -0.01]))
    inlay = solid ^ bed
    side = tick_marks(x0, 5, False).extrude(d + 0.01)
    # Ticks hang from the top edge down each side face: x along the bar, the
    # 2-D y running down from z = S.
    front = side.rotate([90, 0, 0]).mirror([0, 0, 1]).translate([0, d, S])
    back = side.rotate([90, 0, 0]).mirror([0, 0, 1]).translate([0, S + 0.01, S])
    body = solid - inlay - front - back
    return body, inlay


def main():
    male, female = build_halves()
    half = POST_LEN / 2
    m_body, m_ink = scale_parts(male, 0.0)
    f_body, f_ink = scale_parts(female, half)
    # Side by side on the bed, 10 mm apart.
    gap = POST_SIDE + 10.0
    f_body, f_ink = f_body.translate([0, gap, 0]), f_ink.translate([0, gap, 0])
    parts = [Part("Male half", 0, BODY_RGB, m_body),
             Part("Male half scale", 1, MARK_RGB, m_ink),
             Part("Female half", 0, BODY_RGB, f_body),
             Part("Female half scale", 1, MARK_RGB, f_ink)]
    with open(os.path.join(HERE, "test_post.3mf"), "wb") as f:
        f.write(parts_to_3mf(parts, origin=(20, 20), name="10 mm test post, 400 mm",
                             slicer_config=True))
    for name, solid in (("male", male), ("female", female)):
        m = solid.to_mesh()
        trimesh.Trimesh(m.vert_properties[:, :3], m.tri_verts).export(
            os.path.join(HERE, f"test_post_{name}.stl"))
    for name, solid in (("male", male), ("female", female)):
        b = solid.bounding_box()
        print(f"{name:6s} {b[3] - b[0]:.1f} x {b[4] - b[1]:.1f} x {b[5] - b[2]:.1f} mm, "
              f"genus {solid.genus()}, {len(solid.decompose())} piece")
    print(f"scale inlay {m_ink.volume() + f_ink.volume():.0f} mm3, "
          f"{len(m_ink.decompose()) + len(f_ink.decompose())} pieces")


if __name__ == "__main__":
    main()
