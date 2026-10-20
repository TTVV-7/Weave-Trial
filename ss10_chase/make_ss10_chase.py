#!/usr/bin/env python3
"""A 1:1 model of the SS10 Chase light bar, from its dimension drawing.

    python ss10_chase/make_ss10_chase.py

writes ``ss10_chase/out/``:

* ``ss10_housing.stl`` -- the light itself, lying on its back, lens up
* ``ss10_bracket_inward.stl`` / ``ss10_bracket_outward.stl`` -- one L bracket;
  print two of whichever style you want (they are mirror-symmetric, so the
  same part goes on both ends, just turned round)
* ``ss10_assembly_<style>.stl`` -- everything in place, for checking fit
* ``*_preview.png``

Every number below is from the drawing (inches, converted to mm). The
drawing does not give the lens outline, the bracket thickness or the hole
sizes, so those are estimates, marked ``# est.``.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

import manifold3d as mf  # noqa: E402

from phonecase.solid import mesh_to_stl  # noqa: E402

IN = 25.4
SEG = 48

# drawing dimensions
LENGTH = 11.63 * IN           # overall, end cap to end cap
BODY_LEN = 10.85 * IN         # housing between the end caps
HEIGHT = 2.01 * IN
DEPTH = 1.60 * IN
HOLE_FROM_BACK = 0.93 * IN    # bracket bolt line, measured from the back
ADJUST = 0.67 * IN            # height adjustment slot travel
FOOT_DROP = 0.53 * IN         # bracket foot below the housing
INWARD_SPAN = (10.10 * IN, 12.43 * IN)   # foot inner / outer edges
OUTWARD_SPAN = (12.43 * IN, 13.44 * IN)

# estimates
CAP = (LENGTH - BODY_LEN) / 2  # 9.9 mm each end
R_EDGE = 4.0                   # est. housing corner radius
LENS_INSET = 6.0               # est. lens border
LENS_CHAMFER = 9.0             # est. lens corner chamfer
LENS_RECESS = 1.2              # est.
BOLT = 6.5                     # est. M6 clearance
BRACKET_T = 3.0                # est. steel is ~2.5, printed wants a bit more
BRACKET_W = 22.0               # est. bracket width (front-to-back)
FOOT_HOLE = 6.5                # est.
BOLT_GAP = 14.0                # est. spacing of the two end-cap bolts
UPRIGHT_X = INWARD_SPAN[1] / 2 - BRACKET_T   # inner face of the bracket upright


def rounded_box(x, y, z, r):
    """Box from (0,0,0) to (x,y,z) with all edges rounded to r."""
    s = mf.Manifold.sphere(r, SEG)
    pts = [s.translate((px, py, pz))
           for px in (r, x - r) for py in (r, y - r) for pz in (r, z - r)]
    return mf.Manifold.batch_hull(pts)


def prism(poly, h):
    return mf.Manifold.extrude(mf.CrossSection([poly]), h)


def lens_outline(w, h, c, notch):
    """Long octagon with the small V notches top and bottom at the centre."""
    cx = w / 2
    return [
        (c, 0), (cx - notch, 0), (cx, notch * 0.8), (cx + notch, 0),
        (w - c, 0), (w, c), (w, h - c), (w - c, h),
        (cx + notch, h), (cx, h - notch * 0.8), (cx - notch, h),
        (c, h), (0, h - c), (0, c),
    ]


def housing():
    """X along the bar, Y up the face, Z out of the lens. Back on z = 0."""
    body = rounded_box(BODY_LEN, HEIGHT, DEPTH, R_EDGE).translate((CAP, 0, 0))

    # end caps: a touch proud of the body all round, like the real die-cast caps
    cap = rounded_box(CAP + 1.0, HEIGHT, DEPTH, R_EDGE * 0.6)
    caps = [cap.translate((0, 0, 0)), cap.translate((LENGTH - CAP - 1.0, 0, 0))]
    solid = mf.Manifold.batch_boolean([body, *caps], mf.OpType.Add)

    # recessed lens window, with a raised lens face inside it
    lw = BODY_LEN - 2 * LENS_INSET
    lh = HEIGHT - 2 * LENS_INSET
    outline = lens_outline(lw, lh, LENS_CHAMFER, 5.0)
    pocket = prism(outline, LENS_RECESS + 1).translate(
        (CAP + LENS_INSET, LENS_INSET, DEPTH - LENS_RECESS))
    solid = solid - pocket
    inner = mf.CrossSection([outline]).offset(-1.2, mf.JoinType.Miter)
    lens = mf.Manifold.extrude(inner, 0.6).translate(
        (CAP + LENS_INSET, LENS_INSET, DEPTH - LENS_RECESS))
    solid = solid + lens

    # bracket bolt bosses on each end cap, out to the bracket upright, which
    # the drawing puts at 12.43" over the outside faces
    z_bolt = HOLE_FROM_BACK
    boss_len = UPRIGHT_X - LENGTH / 2
    for y in (HEIGHT / 2 - BOLT_GAP / 2, HEIGHT / 2 + BOLT_GAP / 2):
        boss = mf.Manifold.cylinder(boss_len + 1, 5.5, 5.5, SEG).rotate((0, 90, 0))
        solid = solid + boss.translate((-boss_len, y, z_bolt))
        solid = solid + boss.translate((LENGTH - 1, y, z_bolt))
    for y in (HEIGHT / 2 - BOLT_GAP / 2, HEIGHT / 2 + BOLT_GAP / 2):
        hole = mf.Manifold.cylinder(boss_len + 16, 5.0 / 2, 5.0 / 2, SEG)  # M6 tap / heat-set
        hole = hole.rotate((0, 90, 0))
        solid = solid - hole.translate((-boss_len - 1, y, z_bolt))
        solid = solid - hole.translate((LENGTH - 15, y, z_bolt))

    return solid


def bracket(style):
    """One L bracket, laid out in assembly coordinates for the +X end.

    The upright bolts to the end cap, the foot runs under the bar (inward)
    or away from it (outward) FOOT_DROP below the housing.
    """
    span = INWARD_SPAN if style == "inward" else OUTWARD_SPAN
    x_up = UPRIGHT_X
    if style == "inward":
        x0, x1 = span[0] / 2, x_up + BRACKET_T
    else:
        x0, x1 = x_up, span[1] / 2
    y_top = HEIGHT / 2 + BOLT_GAP / 2 + ADJUST / 2 + 8
    y_foot = -FOOT_DROP
    z0 = HOLE_FROM_BACK - BRACKET_W / 2

    upright = mf.Manifold.cube((BRACKET_T, y_top - y_foot, BRACKET_W)).translate(
        (x_up, y_foot, z0))
    foot = mf.Manifold.cube((x1 - x0, BRACKET_T, BRACKET_W)).translate(
        (x0, y_foot, z0))
    b = upright + foot

    # adjustment slot in the upright: both bolts ride in it, ADJUST of travel
    slot_len = BOLT_GAP + ADJUST + BOLT
    slot = (mf.Manifold.cylinder(BRACKET_T + 2, BOLT / 2, BOLT / 2, SEG)
            .translate((0, 0, -1)))
    slot = mf.Manifold.hull(slot + slot.translate((0, slot_len - BOLT, 0)))
    slot = slot.rotate((0, 90, 0)).translate(
        (x_up, HEIGHT / 2 - (slot_len - BOLT) / 2, HOLE_FROM_BACK))
    b = b - slot

    # mounting hole in the foot
    fx = (x0 + x_up) / 2 if style == "inward" else (x_up + BRACKET_T + x1) / 2
    hole = mf.Manifold.cylinder(BRACKET_T + 2, FOOT_HOLE / 2, FOOT_HOLE / 2, SEG)
    hole = hole.rotate((-90, 0, 0)).translate((fx, y_foot - 1, HOLE_FROM_BACK))
    return b - hole


def assembly(style):
    h = housing().translate((-LENGTH / 2, 0, 0))
    b = bracket(style)
    return mf.Manifold.batch_boolean([h, b, b.mirror((1, 0, 0))], mf.OpType.Add)


def bracket_for_print(style):
    """The bracket on its side: the L profile (X-Y) flat on the bed, so it
    prints as stacked L layers with no supports and the bend at full strength."""
    b = bracket(style)
    lo = b.bounding_box()
    return b.translate((-lo[0], -lo[1], -lo[2]))


def housing_halves():
    """The housing cut in two at the centre notch, for beds under 310 mm.

    Two 5 mm holes, 15 mm deep, in each cut face take 30 mm lengths of 5 mm
    dowel or rod; glue and press together.
    Each half prints lens-up like the whole one.
    """
    h = housing_for_print()
    lo = h.bounding_box()
    mid = (lo[0] + lo[3]) / 2
    big = 1000
    left = h ^ mf.Manifold.cube((mid - lo[0] + 1, big, big)).translate((lo[0] - 1, -1, -1))
    right = h - mf.Manifold.cube((mid - lo[0] + 1, big, big)).translate((lo[0] - 1, -1, -1))
    pin = mf.Manifold.cylinder(30, 5.2 / 2, 5.2 / 2, SEG).rotate((0, 90, 0))
    for y in (HEIGHT * 0.3, HEIGHT * 0.7):
        p_ = pin.translate((mid - 15, y, DEPTH * 0.45))
        left, right = left - p_, right - p_
    right = right.translate((-mid, 0, 0))
    return left, right


def housing_for_print():
    h = housing()
    lo = h.bounding_box()
    return h.translate((-lo[0], -lo[1], -lo[2]))


def preview(solid, path, elev=25, azim=-30, width=1400):
    """Shaded orthographic render with a depth buffer (matplotlib's own 3D
    sorts whole faces and gets long thin parts like this wrong)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    m = solid.to_mesh()
    tris = np.asarray(m.vert_properties)[:, :3][np.asarray(m.tri_verts)]
    el, az = math.radians(elev), math.radians(azim)
    ry = np.array([[math.cos(az), 0, math.sin(az)], [0, 1, 0],
                   [-math.sin(az), 0, math.cos(az)]])
    rx = np.array([[1, 0, 0], [0, math.cos(el), -math.sin(el)],
                   [0, math.sin(el), math.cos(el)]])
    t = tris @ (rx @ ry).T
    lo, hi = t.reshape(-1, 3).min(0), t.reshape(-1, 3).max(0)
    k = (width - 40) / (hi[0] - lo[0])
    height = int((hi[1] - lo[1]) * k) + 40
    p = (t - lo) * k + 20
    n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    light = np.array([-0.3, 0.5, 0.8]) / np.linalg.norm([-0.3, 0.5, 0.8])
    shade = 0.25 + 0.75 * np.abs(n @ light)
    depth = np.full((height, width), -np.inf)
    img = np.ones((height, width))
    for (a, b, c), sh in zip(p, shade):
        x0, x1 = int(max(min(a[0], b[0], c[0]), 0)), int(min(max(a[0], b[0], c[0]) + 1, width - 1))
        y0, y1 = int(max(min(a[1], b[1], c[1]), 0)), int(min(max(a[1], b[1], c[1]) + 1, height - 1))
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if x1 < x0 or y1 < y0 or abs(d) < 1e-12:
            continue
        X, Y = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        w0 = ((b[1] - c[1]) * (X - c[0]) + (c[0] - b[0]) * (Y - c[1])) / d
        w1 = ((c[1] - a[1]) * (X - c[0]) + (a[0] - c[0]) * (Y - c[1])) / d
        w2 = 1 - w0 - w1
        z = w0 * a[2] + w1 * b[2] + w2 * c[2]
        win = depth[y0:y1 + 1, x0:x1 + 1]
        hit = (w0 >= 0) & (w1 >= 0) & (w2 >= 0) & (z > win)
        win[hit] = z[hit]
        img[y0:y1 + 1, x0:x1 + 1][hit] = sh
    plt.imsave(path, img[::-1], cmap="gray", vmin=0, vmax=1)


def main():
    out = HERE / "out"
    out.mkdir(exist_ok=True)
    parts = {"ss10_housing": housing_for_print()}
    parts["ss10_housing_half_A"], parts["ss10_housing_half_B"] = housing_halves()
    for style in ("inward", "outward"):
        parts[f"ss10_bracket_{style}"] = bracket_for_print(style)
        parts[f"ss10_assembly_{style}"] = assembly(style)
    for name, solid in parts.items():
        assert solid.status() == mf.Error.NoError, name
        (out / f"{name}.stl").write_bytes(mesh_to_stl(solid, header=name))
        lo = solid.bounding_box()
        size = [lo[i + 3] - lo[i] for i in range(3)]
        print(f"{name:28s} {size[0]:7.1f} x {size[1]:6.1f} x {size[2]:6.1f} mm"
              f"  vol {solid.volume() / 1000:6.1f} cm3")
    preview(parts["ss10_assembly_inward"], out / "assembly_inward_preview.png")
    preview(parts["ss10_assembly_outward"], out / "assembly_outward_preview.png")
    preview(parts["ss10_bracket_inward"], out / "bracket_inward_preview.png", azim=-150)
    preview(parts["ss10_housing_half_A"], out / "housing_half_preview.png", elev=35, azim=-50)


if __name__ == "__main__":
    main()
