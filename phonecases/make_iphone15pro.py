#!/usr/bin/env python3
"""iPhone 15 Pro cases in TPU, and a TPU + PETG hybrid with a swappable back.

    python phonecases/make_iphone15pro.py            # -> phonecases/iphone-15-pro/

Built on the repo's case generator (``phonecase``), so the body, cavity, lip
and cutouts are the same well-tested shapes; this adds what TPU and the hybrid
need on top. Needs ``manifold3d`` (pip install manifold3d).

Two cases:

* **TPU case** -- one piece, all TPU. Tighter fit than the PLA presets
  because TPU stretches over the phone, a taller lip that leans further in
  (TPU can, and it grips the screen edge), and vertical grip ribs cut into
  the lower half of both long sides, below the buttons.

* **Hybrid** -- the MakerWorld "flexible bumper, rigid back" idea: a TPU
  frame with a window in the back, and a PETG plate that drops in from the
  inside, sitting on the frame's ledge with the phone on top of it holding it
  there. Print as many plates as you like and swap them. The plate here is a
  two-colour PETG line dither: stripes whose width grows along the plate, so
  it reads as a gradient from one colour into the other -- colour mixing
  without mixing filament.

TPU and PETG are printed separately (no AMS for TPU), so each part is its
own file. ``hybrid_assembly.3mf`` is the two together, in place, to look at.
"""

from __future__ import annotations

import math
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import manifold3d as mf  # noqa: E402

from phonecase.profiles import case  # noqa: E402
from phonecase.solid import build_solid, mesh_to_stl  # noqa: E402
from phonecase.threemf import Part, parts_to_3mf  # noqa: E402

OUT = Path(__file__).resolve().parent / "iphone-15-pro"
PHONE = "iphone-15-pro"
SEG = 48  # points per rounded corner for the shapes added here

# TPU (95A) fit. TPU stretches, so the gap is about half the PLA one; the lip
# leans in further because a flexible lip can be pushed past and then grips.
TPU_FIT = dict(clearance=0.15, wall=1.8, back_thickness=1.2, lip=1.5,
               lip_inset=1.1)

# Hybrid
PLATE_T = 1.2          # PETG plate thickness (6 layers)
PLATE_GAP = 0.2        # plate to pocket, each side
LEDGE = 5.0            # frame ledge the plate sits on, around the window
CAMERA_MARGIN = 0.6    # plate's camera hole is this much bigger all round

COLOURS = {
    "tpu": (0x2B, 0x2F, 0x36),      # graphite TPU
    "petg_a": (0x1C, 0x7E, 0xD6),   # blue PETG
    "petg_b": (0xF7, 0x67, 0x07),   # orange PETG
}


# --------------------------------------------------------------------------
# shapes
# --------------------------------------------------------------------------

def rrect(hx: float, hy: float, r: float, cx: float = 0.0, cy: float = 0.0) -> mf.CrossSection:
    r = max(0.05, min(r, hx, hy))
    pts = []
    for qx, qy, a0 in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        ox, oy = cx + qx * (hx - r), cy + qy * (hy - r)
        for i in range(SEG + 1):
            a = math.radians(a0 + 90 * i / SEG)
            pts.append((ox + r * math.cos(a), oy + r * math.sin(a)))
    return mf.CrossSection([pts])


def slab(section: mf.CrossSection, z0: float, z1: float) -> mf.Manifold:
    return section.extrude(z1 - z0).translate((0, 0, z0))


def grip_ribs(spec) -> mf.Manifold:
    """Vertical grooves on the lower half of both long sides, under the buttons.

    Vertical rather than horizontal so a groove is never an overhang, and
    stopped short of the base chamfer and the lip so neither edge is weakened.
    """
    depth, width, pitch = 0.5, 1.0, 3.0
    z0, z1 = spec.back_thickness + 1.0, spec.height - spec.lip - 0.5
    y_top = -8.0                               # buttons start a little above centre
    y_bot = -(spec.outer_l / 2 - spec.outer_r - 2.0)
    cutters = []
    y = y_bot
    while y < y_top:
        for side in (-1, 1):
            x = side * (spec.outer_w / 2 - depth / 2 + 0.25)
            box = mf.Manifold.cube((depth + 0.5, width, z1 - z0), center=True)
            cutters.append(box.translate((x, y, (z0 + z1) / 2)))
        y += pitch
    return mf.Manifold.batch_boolean(cutters, mf.OpType.Add)


def camera(spec):
    return next(c for c in spec.cutouts if c.name == "camera")


# --------------------------------------------------------------------------
# the parts
# --------------------------------------------------------------------------

def tpu_case():
    spec = case(PHONE, **TPU_FIT)
    return spec, build_solid(spec) - grip_ribs(spec)


def hybrid():
    """The TPU frame and the PETG plate, in the same coordinates."""
    # The frame is a TPU case whose back is its own back plus the PETG plate,
    # so the cutouts land where the phone actually is (sitting on the plate).
    spec = case(PHONE, **{**TPU_FIT, "back_thickness": TPU_FIT["back_thickness"] + PLATE_T})
    back = TPU_FIT["back_thickness"]
    frame = build_solid(spec) - grip_ribs(spec)

    # Pocket for the plate: the cavity outline, from the frame's back up.
    pocket = rrect(spec.inner_w / 2, spec.inner_l / 2, spec.inner_r)
    frame = frame - slab(pocket, back, spec.back_thickness + 0.01)
    # Window through the back, leaving the ledge the plate rests on.
    window = rrect(spec.inner_w / 2 - LEDGE, spec.inner_l / 2 - LEDGE,
                   max(1.0, spec.inner_r - LEDGE))
    frame = frame - slab(window, -1.0, back + 0.02)

    # The plate: the pocket less a gap, with a camera hole a little larger
    # than the frame's so it never shows past the frame's own edge.
    cam = camera(spec)
    outline = (rrect(spec.inner_w / 2 - PLATE_GAP, spec.inner_l / 2 - PLATE_GAP,
                     spec.inner_r - PLATE_GAP)
               - rrect(cam.w / 2 + CAMERA_MARGIN, cam.h / 2 + CAMERA_MARGIN,
                       cam.r + CAMERA_MARGIN, cam.u, cam.v))
    plate = slab(outline, 0.0, PLATE_T)
    return spec, frame, outline, plate


def dither(outline: mf.CrossSection, *, pitch=2.4, angle=35.0, min_w=0.45,
           depth=0.44) -> mf.Manifold:
    """Colour B's stripes for the plate's face: a line-dither gradient.

    Stripes at ``angle`` with a fixed pitch, each one widening along the
    plate's length from ``min_w`` (about one 0.42 line) to ``pitch - min_w``,
    so the face goes from mostly colour A to mostly colour B. ``depth`` is
    the first two layers -- the face that sits on the bed, the glossy one.
    """
    bx0, by0, bx1, by1 = outline.bounds()
    span = max(bx1 - bx0, by1 - by0) * 1.6
    ca, sa = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    stripes = []
    n = int(span / pitch) + 2
    steps = 40
    for k in range(-n, n + 1):
        off = k * pitch
        left, right = [], []
        for i in range(steps + 1):
            t = -span / 2 + span * i / steps
            # Point on the stripe's centre line, in plate coordinates.
            x, y = t * ca - off * sa, t * sa + off * ca
            # Width from where that point is along the plate (bottom -> top).
            f = min(1.0, max(0.0, (y - by0) / (by1 - by0)))
            w = min_w + f * (pitch - 2 * min_w)
            left.append((x - sa * w / 2, y + ca * w / 2))
            right.append((x + sa * w / 2, y - ca * w / 2))
        stripes.append(mf.CrossSection([right + left[::-1]]))
    region = mf.CrossSection.batch_boolean(stripes, mf.OpType.Add) ^ outline
    return region.extrude(depth)


# --------------------------------------------------------------------------

def write(name: str, data: bytes) -> None:
    path = OUT / name
    path.write_bytes(data)
    print(f"  {path.relative_to(ROOT)}  ({len(data) / 1e3:.0f} kB)")


def grams(solid, density: float) -> float:
    return solid.volume() / 1000 * density


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    spec, tpu = tpu_case()
    print(f"TPU case: {spec.outer_w:.1f} x {spec.outer_l:.1f} x {spec.height:.1f} mm, "
          f"~{grams(tpu, 1.21):.0f} g TPU")
    write("tpu_case.stl", mesh_to_stl(tpu, header="iPhone 15 Pro TPU case"))
    write("tpu_case.3mf", parts_to_3mf([Part("tpu", 0, COLOURS["tpu"], tpu)],
                                       origin=(spec.outer_w / 2, spec.outer_l / 2),
                                       name="iPhone 15 Pro TPU case"))

    hspec, frame, outline, plate = hybrid()
    inlay = dither(outline)
    body = plate - inlay
    print(f"Hybrid: frame ~{grams(frame, 1.21):.0f} g TPU, "
          f"plate ~{grams(plate, 1.27):.0f} g PETG "
          f"({inlay.volume() / plate.volume() * 100:.0f}% of the plate face in colour B)")
    origin = (hspec.outer_w / 2, hspec.outer_l / 2)
    write("hybrid_tpu_frame.stl", mesh_to_stl(frame, header="iPhone 15 Pro hybrid TPU frame"))
    write("hybrid_tpu_frame.3mf", parts_to_3mf([Part("tpu", 0, COLOURS["tpu"], frame)],
                                               origin=origin, name="hybrid TPU frame"))
    write("hybrid_petg_plate.stl", mesh_to_stl(plate, header="iPhone 15 Pro hybrid PETG plate"))
    write("hybrid_petg_plate_gradient.3mf", parts_to_3mf(
        [Part("petg blue", 0, COLOURS["petg_a"], body),
         Part("petg orange", 1, COLOURS["petg_b"], inlay)],
        origin=origin, name="hybrid PETG plate"))

    # Both together, plate seated on the ledge, to look at rather than print.
    back = TPU_FIT["back_thickness"]
    seat = lambda s: s.translate((0, 0, back))  # noqa: E731
    write("hybrid_assembly.3mf", parts_to_3mf(
        [Part("tpu frame", 0, COLOURS["tpu"], frame),
         Part("petg blue", 1, COLOURS["petg_a"], seat(body)),
         Part("petg orange", 2, COLOURS["petg_b"], seat(inlay))],
        origin=origin, name="hybrid assembly (view only)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
