"""2D outlines, as signed distance fields sampled along rays.

Every cross-section in this part -- the hole, the plug, the waist, the flare,
the barb, the jet slot -- is star-shaped about the nozzle axis, so a section is
fully described by one radius per angle. That is what makes the whole solid a
stack of rings with a shared parameterisation, and a stack of rings is trivially
watertight.

Working in distance fields rather than polygons buys the offset for free:
`offset` is the contour of sdf == d, so the plug is the hole at d = -clearance
and the head is the hole at d = +margin. No polygon offsetting, no self-
intersecting corners.
"""

from __future__ import annotations

import math
from typing import Callable

Sdf = Callable[[float, float], float]


def sdf_round_rect(x: float, y: float, hx: float, hy: float, rc: float) -> float:
    """Exact signed distance to a rounded rectangle centred on the origin."""
    rc = min(rc, hx, hy)
    qx = abs(x) - (hx - rc)
    qy = abs(y) - (hy - rc)
    outside = math.hypot(max(qx, 0.0), max(qy, 0.0))
    inside = min(max(qx, qy), 0.0)
    return outside + inside - rc


def circle(r: float) -> Sdf:
    return lambda x, y: math.hypot(x, y) - r


def round_rect(hx: float, hy: float, rc: float) -> Sdf:
    return lambda x, y: sdf_round_rect(x, y, hx, hy, rc)


def union(*fields: Sdf) -> Sdf:
    return lambda x, y: min(f(x, y) for f in fields)


def intersect(*fields: Sdf) -> Sdf:
    return lambda x, y: max(f(x, y) for f in fields)


def ray(sdf: Sdf, theta: float, offset: float = 0.0, rmax: float = 60.0) -> float:
    """Distance from the origin to the contour sdf == offset, along theta.

    Bisection, not marching: the sections are star-shaped so there is exactly
    one crossing, and 48 halvings of a 60 mm interval land inside 3e-13 mm.
    """
    ux, uy = math.cos(theta), math.sin(theta)
    lo, hi = 0.0, rmax
    if sdf(0.0, 0.0) - offset >= 0.0:
        raise ValueError("offset eats the whole section (origin is outside it)")
    if sdf(ux * hi, uy * hi) - offset <= 0.0:
        raise ValueError("section is bigger than rmax")
    for _ in range(48):
        mid = 0.5 * (lo + hi)
        if sdf(ux * mid, uy * mid) - offset < 0.0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def ring(sdf: Sdf, z: float, n: int, offset: float = 0.0,
         cx: float = 0.0, cy: float = 0.0) -> list[tuple[float, float, float]]:
    """One closed section as n points, counter-clockwise, at height z."""
    pts = []
    for i in range(n):
        th = 2.0 * math.pi * i / n
        r = ray(sdf, th, offset)
        pts.append((cx + r * math.cos(th), cy + r * math.sin(th), z))
    return pts


def hole_sdf(length: float, neck: float, lobe_width: float, lobe_span: float,
             corner_r: float) -> Sdf:
    """The hole in the panel: two rounded rectangles crossed.

    A long thin one for the slot, and a short fat one -- corner radius equal to
    its own half width, so it is a stadium -- for the lobes. Measured off the
    photograph as ratios of the length (neck 0.44, lobes 0.81, lobe span 0.75)
    and scaled by the caliper readings.

    Both parts have an exact distance function, which is what makes the plug
    (offset -clearance) and the head (offset +margin) exact offsets rather than
    approximations of one.
    """
    slot = round_rect(length / 2.0, neck / 2.0, corner_r)
    lobes = round_rect(lobe_span / 2.0, lobe_width / 2.0, lobe_span / 2.0)
    return union(slot, lobes)


def widths(sdf: Sdf, offset: float = 0.0, n: int = 720) -> tuple[float, float]:
    """(x extent, y extent) of a section, for the fit checks."""
    hx = hy = 0.0
    for i in range(n):
        th = 2.0 * math.pi * i / n
        r = ray(sdf, th, offset)
        hx = max(hx, abs(r * math.cos(th)))
        hy = max(hy, abs(r * math.sin(th)))
    return 2.0 * hx, 2.0 * hy
