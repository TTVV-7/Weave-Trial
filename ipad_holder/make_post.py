"""A stand-in for the post the holder hangs on: a 12 x 12 mm square bar with
flat, square-cut ends, to check the hook's fit without the real one.

    python ipad_holder/make_post.py

Writes ``test_post.3mf`` and ``test_post.stl``. Print it lying on one of its
long faces: it needs no supports.
"""

from __future__ import annotations

import os
import sys

import manifold3d as m3

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from phonecase.threemf import Part, parts_to_3mf               # noqa: E402

POST_SIDE = 12.0                # the real post's section
POST_LEN = 200.0                # fits a 256 mm bed with room to spare


def build_post() -> m3.Manifold:
    """Lying along x, one long face on the bed."""
    return m3.Manifold.cube([POST_LEN, POST_SIDE, POST_SIDE])


def main():
    post = build_post()
    with open(os.path.join(HERE, "test_post.3mf"), "wb") as f:
        f.write(parts_to_3mf([Part("Post", 0, (200, 200, 205), post)],
                             origin=(20, 20), name="12 mm test post"))
    m = post.to_mesh()
    import trimesh
    trimesh.Trimesh(m.vert_properties[:, :3], m.tri_verts).export(
        os.path.join(HERE, "test_post.stl"))
    print(f"post {POST_SIDE:g} x {POST_SIDE:g} x {POST_LEN:g} mm, "
          f"volume {post.volume():.0f} mm3")


if __name__ == "__main__":
    main()
