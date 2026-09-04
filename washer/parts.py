"""The three printed parts.

  nozzle   head above the panel, plug through it, wedge flare and barb below.
           One closed solid: the fluid channel is the inner wall of a tube, so
           there is no boolean subtraction anywhere and nothing to leak.
  clip     slides in underneath and wedges up the flare. This is what holds the
           nozzle in, and it is a separate part because a rigid printed snap
           arm short enough to fit under a hood is a rigid printed snap arm
           that snaps.
  gauge    five tabs at 0.4 mm steps. The hole is only known to about half a
           millimetre, so the last measurement is taken by the printer.
"""

from __future__ import annotations

import math

from dataclasses import replace

from .geom import Sdf, circle, ray, round_rect
from .mesh import Mesh, Ring
from .spec import NozzleSpec


# --------------------------------------------------------------------------
# rings
# --------------------------------------------------------------------------
def _ring(sdf: Sdf, z: float, n: int, offset: float = 0.0,
          cx: float = 0.0, cy: float = 0.0, az: float = 0.0) -> Ring:
    """A section, sampled at n angles, then rotated by az and moved to (cx, cy).

    The rotation is applied after sampling so every ring keeps the same index
    order and any two rings can be lofted together.
    """
    ca, sa = math.cos(az), math.sin(az)
    out: Ring = []
    for i in range(n):
        th = 2.0 * math.pi * i / n
        r = ray(sdf, th, offset)
        x, y = r * math.cos(th), r * math.sin(th)
        out.append((cx + x * ca - y * sa, cy + x * sa + y * ca, z))
    return out


def outer_stations(s: NozzleSpec) -> list[tuple[float, Sdf, float]]:
    """(z, section, offset) from the barb tip up to the top of the head.

    Repeated z values are steps, and a step is just a quad strip with zero
    height difference -- a flat face, correctly wound, for free.
    """
    hole = s.hole()
    stem, ridge = s.barb_stem_r, s.barb_ridge_r
    st: list[tuple[float, Sdf, float]] = []

    # Barb, tip first. Each ridge is a cone up to the peak and a step back in,
    # so the hose slides on going up and bites going down.
    z = s.z_bottom
    st.append((z, circle(stem - 0.35), 0.0))   # lead-in for the hose
    pitch = (s.barb_len - 1.2) / max(1, s.barb_ridges)
    for k in range(s.barb_ridges):
        z0 = s.z_bottom + 0.2 + k * pitch
        st.append((z0, circle(stem), 0.0))
        st.append((z0 + pitch * 0.62, circle(ridge), 0.0))
        st.append((z0 + pitch * 0.62, circle(stem), 0.0))
    st.append((s.z_barb_top, circle(stem), 0.0))

    # Cone out to the flare, then the flare itself: the clip's ramp.
    st.append((s.z_flare_bot, s.shank(s.flare_hx), 0.0))
    st.append((s.z_waist_bot, s.shank(s.waist_hx), 0.0))
    st.append((s.z_waist_top, s.shank(s.waist_hx), 0.0))

    # Plug through the panel, then the head sitting on top of it.
    st.append((s.z_plug, hole, -s.clearance))
    st.append((0.0, hole, -s.clearance))
    st.append((0.0, hole, s.head_margin))
    st.append((s.head_height - s.head_chamfer_h, hole, s.head_margin))
    st.append((s.head_height, hole, s.head_margin - s.head_chamfer))
    return st


def inner_section(s: NozzleSpec, z: float) -> tuple[Sdf, float, float]:
    """The channel at height z: section, and where its centre has moved to.

    Below the plenum it is a plain vertical bore. Above it the centre walks
    sideways at the aim angle while the round bore squashes into the jet slot,
    so the exit is an oblique cut through a tilted tube -- and because the rings
    stay horizontal, that oblique cut is exactly the top face of the head.
    """
    r = s.bore / 2.0
    if z <= s.plenum_z:
        return round_rect(r, r, r), 0.0, 0.0
    span = s.head_height - s.plenum_z
    t = min(1.0, (z - s.plenum_z) / span)
    smooth = t * t * (3.0 - 2.0 * t)
    tilt = math.radians(s.aim_deg)
    hx = r + (s.jet_w / 2.0 - r) * smooth
    hy = r + ((s.jet_h / 2.0) / math.cos(tilt) - r) * smooth
    shift = (z - s.plenum_z) * math.tan(tilt)          # linear: a straight jet
    return round_rect(hx, hy, min(hx, hy)), shift, 0.0


def inner_ring(s: NozzleSpec, z: float, n: int) -> Ring:
    sdf, shift, _ = inner_section(s, z)
    az = math.radians(s.aim_az)
    return _ring(sdf, z, n, 0.0, shift * -math.sin(az), shift * math.cos(az), az)


# --------------------------------------------------------------------------
# the nozzle
# --------------------------------------------------------------------------
def build_nozzle(s: NozzleSpec) -> Mesh:
    n = s.facets
    outer = [_ring(sdf, z, n, off) for z, sdf, off in outer_stations(s)]

    zs = [s.z_bottom, s.plenum_z]
    steps = 12
    for i in range(1, steps + 1):
        zs.append(s.plenum_z + (s.head_height - s.plenum_z) * i / steps)
    inner = [inner_ring(s, z, n) for z in zs]

    m = Mesh()
    m.tube(outer, inner)
    return m


# --------------------------------------------------------------------------
# the clip
# --------------------------------------------------------------------------
def clip_geometry(s: NozzleSpec) -> dict:
    """Where the clip meets the panel and where it meets the flare.

    Built in the assembly frame -- origin on the nozzle axis, z = 0 at the top
    face of the panel -- because every dimension here is a relationship with
    something else, and stating them in the same frame is the only way to check
    them. `build_clip` moves the result onto the bed afterwards.
    """
    z_rim_top = -s.panel                       # against the underside of the sheet
    z_top = z_rim_top - s.clip_rim             # prong top: must clear the waist
    z_bot = z_top - s.clip_thick
    contact = s.flare_hx_at(z_bot)             # half width of the flare it grips
    # The prong's inner edge is straight in plan and the shank is a rounded
    # rectangle, so the two first touch at the back of the shank's flat side,
    # not on its centreline. That is where the design fit is reckoned from.
    y_contact = -(s.W / 2.0 - s.clearance - 0.8)
    taper = math.tan(math.radians(s.clip_taper_deg))
    return {
        "z_rim_top": z_rim_top, "z_top": z_top, "z_bot": z_bot,
        "contact": contact, "y_contact": y_contact, "taper": taper,
        "bevel": math.tan(math.radians(s.flare_angle)) * s.clip_thick,
        "y_root": -3.5, "y_tip": s.clip_reach,
        "y_bar0": -3.5 - s.clip_back, "y_bar1": -3.5,
        "x_out": 7.5 + s.clip_wing,
    }


def _half_gap(g: dict, y: float) -> float:
    """Half the notch width at depth y, on the clip's lower face."""
    return g["contact"] + (y - g["y_contact"]) * g["taper"]


def build_clip(s: NozzleSpec, assembly: bool = False) -> Mesh:
    g = clip_geometry(s)
    m = Mesh()
    z_top, z_bot, z_rim = g["z_top"], g["z_bot"], g["z_rim_top"]
    y0, y1 = g["y_root"], g["y_tip"]
    bevel = g["bevel"]

    # Two prongs. The inner face lies on the flare cone, so the clip meets the
    # ramp face to face instead of digging an edge into it.
    for sign in (-1.0, 1.0):
        wi0, wi1 = _half_gap(g, y0), _half_gap(g, y1)
        xo = 8.0
        bottom = [(sign * wi0, y0, z_bot), (sign * xo, y0, z_bot),
                  (sign * xo, y1, z_bot), (sign * wi1, y1, z_bot)]
        top = [(sign * (wi0 - bevel), y0, z_top), (sign * xo, y0, z_top),
               (sign * xo, y1, z_top), (sign * (wi1 - bevel), y1, z_top)]
        if sign < 0:                    # keep both prongs wound the same way
            bottom = bottom[::-1]
            top = top[::-1]
        m.hexahedron(bottom, top)

    # Back bar and side wings: full height, so these are what touch the sheet.
    m.box(-g["x_out"], g["x_out"], g["y_bar0"], g["y_bar1"], z_bot, z_rim)
    for sign in (-1.0, 1.0):
        x0, x1 = sorted((sign * 7.5, sign * g["x_out"]))
        m.box(x0, x1, g["y_bar1"], y1 - 1.0, z_bot, z_rim)

    if assembly:
        return m
    return m.translated(0.0, -g["y_bar0"], -z_bot)


# --------------------------------------------------------------------------
# the gauge
# --------------------------------------------------------------------------
_SEGMENTS = {
    "0": "abcdef", "1": "bc", "2": "abdeg", "3": "abcdg", "4": "bcfg",
    "5": "acdfg", "6": "acdefg", "7": "abc", "8": "abcdefg", "9": "abcdfg",
}
#: (x0, y0, x1, y1) in units of one digit box, 1 wide by 2 tall.
_SEG_BOX = {
    "a": (0.0, 1.8, 1.0, 2.0), "b": (0.8, 1.0, 1.0, 1.8),
    "c": (0.8, 0.2, 1.0, 1.0), "d": (0.0, 0.0, 1.0, 0.2),
    "e": (0.0, 0.2, 0.2, 1.0), "f": (0.0, 1.0, 0.2, 1.8),
    "g": (0.0, 0.9, 1.0, 1.1),
}


def label(m: Mesh, text: str, x: float, y: float, z: float,
          size: float = 1.6, height: float = 0.6) -> float:
    """Raised seven-segment text. Returns the x it ended at."""
    for ch in text:
        if ch == ".":
            m.box(x, x + 0.2 * size, y, y + 0.2 * size, z, z + height)
            x += 0.45 * size
            continue
        for seg in _SEGMENTS.get(ch, ""):
            x0, y0, x1, y1 = _SEG_BOX[seg]
            m.box(x + x0 * size, x + x1 * size,
                  y + y0 * size, y + y1 * size, z, z + height)
        x += 1.35 * size
    return x


def build_gauge(s: NozzleSpec, steps: tuple[float, ...] = (-0.8, -0.4, 0.0, 0.4, 0.8),
                thickness: float = 1.2) -> Mesh:
    """Flat tabs cut to the hole outline, in 0.4 mm steps of overall length.

    Push each one into the hole. The largest that drops in without forcing is
    the hole; feed its number back as --length and the whole part re-cuts.
    """
    m = Mesh()
    n = max(48, s.facets // 2)
    pitch = 14.0
    bar_y0, bar_y1 = -9.0, 0.0
    span = pitch * len(steps)
    m.box(-span / 2.0, span / 2.0, bar_y0, bar_y1, 0.0, 3.0)

    for k, delta in enumerate(steps):
        cx = -span / 2.0 + pitch * (k + 0.5)
        scale = (s.hole_length + delta) / s.hole_length
        sdf = replace(s, fit_scale=s.fit_scale * scale).hole()
        # Tab lies flat, long axis across the bar, so five of them fit on one
        # handle without touching.
        rings = [[(cx - p[1], 6.0 + p[0], z) for p in _ring(sdf, 0.0, n)]
                 for z in (0.0, thickness)]
        m.loft(rings)
        m.box(cx - 2.5, cx + 2.5, bar_y1 - 0.1, 6.5, 0.0, thickness)
        text = f"{(s.hole_length + delta) * s.fit_scale:.1f}"
        label(m, text, cx - 2.6, bar_y0 + 2.4, 3.0)
    return m


# --------------------------------------------------------------------------
def printable_nozzle(s: NozzleSpec) -> Mesh:
    """Turned over and dropped onto the bed: head face down, barb in the air.

    That orientation is not a preference. It puts the visible face against the
    glass plate, leaves the jet as a hole in the first layer rather than a
    bridge, and turns every downward face on the shank into an upward one --
    which is why the flare and the head chamfer are the only overhangs left.
    """
    return build_nozzle(s).flipped().translated(0.0, 0.0, s.head_height)


def build(s: NozzleSpec, part: str) -> Mesh:
    if part == "nozzle":
        return printable_nozzle(s)
    if part == "clip":
        return build_clip(s)
    if part == "gauge":
        return build_gauge(s)
    if part == "all":
        m = Mesh()
        m.add(printable_nozzle(s).translated(-14.0, 0.0, 0.0))
        m.add(build_clip(s).translated(14.0, -6.0, 0.0))
        m.add(build_gauge(s).translated(0.0, -24.0, 0.0))
        return m
    raise ValueError(f"unknown part {part!r}")
