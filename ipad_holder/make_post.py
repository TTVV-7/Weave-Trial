"""A stand-in for the post the holder hangs on: a 10 x 10 mm square bar with
flat, square-cut ends, 400 mm long, to check the hook's fit without the real
one.

    python ipad_holder/make_post.py

400 mm is longer than the bed, so the bar is printed as two 200 mm halves
that join with a square peg: the male half carries the peg on its inner end,
the female half a socket to take it. Square, so the halves cannot turn. A
drop of glue in the socket makes it permanent.

The top face carries a centimetre scale, 0 to 40 along the joined bar, as a
black inlay: the top 0.4 mm, in its own part and filament. The two side faces
carry the same tick marks engraved 0.4 mm deep, without numbers.

Writes ``test_post.3mf`` (both halves, with the scale) and
``test_post_male.stl`` / ``test_post_female.stl`` (plain, one colour). Print
both lying on the unmarked long face: no supports.
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
TICK_W = 0.8                    # two nozzle widths
TICK_LEN = {1: 3.5, 5: 5.0, 10: 5.0}    # by what the cm is a multiple of
TICK_W10 = 1.6                  # every 10 cm, a heavier tick
NUM_H = 3.2                     # numeral height
BODY_RGB = (225, 225, 228)
MARK_RGB = (0, 0, 0)


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
    male = bar(half) + peg.translate([half - 0.01, 0, 0])
    socket = centred_square(PEG_SIDE + 2 * FIT, PEG_LEN + SOCKET_EXTRA + 0.01)
    female = bar(half) - socket.translate([-0.01, 0, 0])
    return male, female


def ticks(start_cm: int, end_cm: int, x0: float) -> list[tuple[int, float]]:
    """(cm, local x) for each centimetre from start_cm to end_cm, where the
    half's local x = 0 sits at x0 mm along the joined bar. (Ticks on the very
    ends are pulled in by half their width, in tick_marks, to stay whole.)"""
    out = []
    for cm in range(start_cm, end_cm + 1):
        x = cm * 10.0 - x0
        out.append((cm, x))
    return out


def tick_marks(marks, with_numbers: bool) -> m3.CrossSection:
    """Ticks rising from the y = 0 edge of a 10 mm wide face: 3.5 mm every cm,
    5 mm every 5 cm, 5 mm and twice as heavy every 10 cm. With numbers, each
    cm's number sits above its tick, except on the bar's ends (0, 20, 40)."""
    from matplotlib.font_manager import FontProperties
    from matplotlib.textpath import TextPath
    font = FontProperties(family="DejaVu Sans", weight="bold")
    shapes = []
    for cm, x in marks:
        L = TICK_LEN[10 if cm % 10 == 0 else 5 if cm % 5 == 0 else 1]
        w = TICK_W10 if cm % 10 == 0 else TICK_W
        x = min(max(x, w / 2), POST_LEN / 2 - w / 2)
        shapes.append(m3.CrossSection.square([w, L]).translate([x - w / 2, 0]))
        if with_numbers and cm % int(POST_LEN / 20) != 0:
            tp = TextPath((0, 0), str(cm), size=NUM_H * 1.37, prop=font)
            loops = [q for q in tp.to_polygons() if len(q) >= 3]
            text = m3.CrossSection(loops, m3.FillRule.EvenOdd)
            tx0, ty0, tx1, ty1 = text.bounds()
            text = text.scale([NUM_H / (ty1 - ty0)] * 2)
            tx0, ty0, tx1, ty1 = text.bounds()
            top = TICK_LEN[5] + 0.8             # clear of the 5 cm ticks
            shapes.append(text.translate([x - (tx0 + tx1) / 2, top - ty0]))
    return m3.CrossSection.batch_boolean(shapes, m3.OpType.Add)


def scale_parts(solid: m3.Manifold, marks):
    """The half with its scale: (body, black inlay on top). The side faces'
    ticks are engraved into the body."""
    S, d = POST_SIDE, MARK_DEPTH
    top = tick_marks(marks, True).extrude(d + 0.01).translate([0, 0, S - d])
    inlay = solid ^ top
    side = tick_marks(marks, False).extrude(d + 0.01)
    # Ticks rise from the top edge down each side face: x along the bar, the
    # 2-D y running down from z = S.
    front = side.rotate([90, 0, 0]).mirror([0, 0, 1]).translate([0, d, S])
    back = side.rotate([90, 0, 0]).mirror([0, 0, 1]).translate([0, S + 0.01, S])
    body = solid - inlay - front - back
    return body, inlay


def main():
    male, female = build_halves()
    half_cm = int(POST_LEN / 20)
    m_body, m_ink = scale_parts(male, ticks(0, half_cm, 0.0))
    f_body, f_ink = scale_parts(female, ticks(half_cm, 2 * half_cm, POST_LEN / 2))
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


if __name__ == "__main__":
    main()
