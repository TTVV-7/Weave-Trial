"""Southwest Contracting gyro, as a painted 3MF and a plain STL.

The print-in-place gyro from make_fidgets.py (a ball pivoting inside four nested
rings on cone pins), branded: SOUTHWEST round the front of the outer ring and
CONTRACTING round the back, and an SWC monogram on both flat faces of the ball.
All the lettering is cut 0.6 mm in, so it shows in one colour and prints in the
accent colour on a multi-material printer.

Run: python3 make_swc_gyro.py   (needs numpy, trimesh, manifold3d, fonttools, qrcode)
Change the words, colours or letter sizes below and re-run.
"""
import sys
import numpy as np
import manifold3d as mf
import make_fidgets as mk

sys.path.insert(0, str(mk.HERE.parent / "reviewstand"))
from make_review_stand import text  # noqa: E402  (Inter Bold, outlines to a CrossSection)

OUT = mk.OUT
NAME = "southwest-contracting-gyro"

FRONT = "SOUTHWEST"       # round the front of the outer ring
BACK = "CONTRACTING"      # round the back
MONOGRAM = "SWC"          # on both faces of the ball

FILAMENTS = np.array([
    [0x1A, 0x1A, 0x1A],   # T1 black
    [0xFF, 0x6A, 0x13],   # T2 safety orange: the lettering
    [0xF2, 0xF2, 0xF2],   # T3 white
])
BLACK, ORANGE, WHITE = range(3)
BALL_COLOUR = WHITE
RING_COLOURS = [BLACK, ORANGE, WHITE, BLACK]   # inner to outer
LETTERS = ORANGE          # all the lettering (black instead on a part that is already orange)

CAP_H = 6.5               # letter height round the ring
MONO_H = 5.0              # monogram letter height
ENGRAVE = 0.6             # how deep the letters are cut


def ring_text(words, r, centre_deg):
    """`words` cut into a sphere of radius r, centred on angle centre_deg (from +x,
    anticlockwise seen from above), upright and reading left to right from outside."""
    flat = text(words, CAP_H, np.pi * r * 0.82)          # at most ~150 degrees of arc
    flat = flat.translate((0, -CAP_H / 2))               # centre the caps on the equator
    solid = mf.Manifold.extrude(flat, ENGRAVE + 1.0).refine_to_length(0.6)
    c0 = np.radians(centre_deg)

    def wrap(p):
        u, v, w = p[:, 0], p[:, 1], p[:, 2]
        rho = np.sqrt(r * r - v * v) - ENGRAVE + w       # w = 0 is the floor of the cut
        a = c0 + u / r
        return np.c_[rho * np.cos(a), rho * np.sin(a), v]

    return solid.warp_batch(wrap)


def monogram():
    """The monogram cut into the ball's flat top, and the same turned over about
    the spin axis for the bottom, so it reads the same whichever face is up."""
    flat = text(MONOGRAM, MONO_H, 2 * np.sqrt(mk.BALL_R ** 2 - mk.HALF_H ** 2) - 3.5)
    # turned to read left to right when you're looking at FRONT on the ring
    flat = flat.translate((0, -MONO_H / 2)).rotate(90)
    top = mf.Manifold.extrude(flat, ENGRAVE + 1.0).translate([0, 0, mk.HALF_H - ENGRAVE])
    return top + top.rotate([180, 0, 0])


def make():
    ball = mk.sphere(mk.BALL_R) ^ mk.slab() - monogram()
    parts = mk.make_gyro(ball)
    r_out = mk.ring_radii()[-1][1]
    words = ring_text(FRONT, r_out, 0) + ring_text(BACK, r_out, 180)
    parts[-1] = parts[-1] - words
    return parts


def paint(parts):
    r_out = mk.ring_radii()[-1][1]
    meshes, labels = [], []
    colours = [BALL_COLOUR] + RING_COLOURS
    for k, p in enumerate(parts):
        m = mk.to_mesh(p)
        c = m.triangles_center
        r = np.linalg.norm(c, axis=1)
        z = np.abs(c[:, 2])
        lab = np.full(len(m.faces), colours[k])
        ink = LETTERS if colours[k] != LETTERS else BLACK
        if k == 0:      # monogram: below the flat faces, outside the pin sockets
            cut = (z < mk.HALF_H - 1e-3) & (z > mk.HALF_H - ENGRAVE - 0.05) & (r < mk.BALL_R - 0.05)
            lab[cut] = ink
        elif k == len(parts) - 1:   # ring lettering: just under the outer skin
            cut = (r < r_out - 0.03) & (r > r_out - ENGRAVE - 0.15) & (z < mk.HALF_H - 1e-3)
            lab[cut] = ink
        meshes.append(m)
        labels.append(lab)
    return meshes, labels


def main():
    parts = make()
    print(f"gyro: every pivot turns a full circle, tightest gap {mk.check_gyro(parts):.2f} mm")
    meshes, labels = paint(parts)
    gyro, lab = mk.merged(meshes, labels)
    gyro = mk.on_bed(gyro)
    gyro.export(OUT / f"{NAME}.stl")
    mk.write_3mf(OUT / f"{NAME}.3mf", [(NAME, gyro, lab, (0, 0))], FILAMENTS)
    e = gyro.extents
    print(f"{NAME}  {e[0]:.1f} x {e[1]:.1f} x {e[2]:.1f} mm  {gyro.volume / 1000:.1f} cm3  "
          f"{len(gyro.faces)} tris")


if __name__ == "__main__":
    main()
