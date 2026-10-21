"""A stand-in for the post the holder hangs on: a 10 x 10 mm square bar with
flat, square-cut ends, 400 mm long, to check the hook's fit without the real
one.

    python ipad_holder/make_post.py

400 mm is longer than the bed, so the bar is printed as two 200 mm halves
that join with a square peg: the male half carries the peg on its inner end,
the female half a socket to take it. Square, so the halves cannot turn. A
drop of glue in the socket makes it permanent.

Writes ``test_post.3mf`` (both halves) and ``test_post_male.stl`` /
``test_post_female.stl``. Print both lying on a long face: no supports.
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


def main():
    male, female = build_halves()
    # Side by side on the bed, 10 mm apart.
    gap = POST_SIDE + 10.0
    parts = [Part("Post, male half", 0, (200, 200, 205), male),
             Part("Post, female half", 0, (200, 200, 205),
                  female.translate([0, gap, 0]))]
    with open(os.path.join(HERE, "test_post.3mf"), "wb") as f:
        f.write(parts_to_3mf(parts, origin=(20, 20), name="10 mm test post, 400 mm"))
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
