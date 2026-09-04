"""Draw the part before printing it: plan, both sections, and the clip.

Everything is drawn from the same functions the mesh is built from, so if the
drawing and the STL disagree, the drawing is wrong and it is one bug, not two.
Scale is 1 mm = 1 unit, then the whole thing is scaled up once at the end, so
the printed dimensions can be checked against the drawing with a ruler.
"""

from __future__ import annotations

import math

from .check import check_fit
from .geom import ray
from .parts import _half_gap, _ring, clip_geometry, inner_section, outer_stations
from .spec import NozzleSpec

SCALE = 9.0
INK = "#1b1c1e"
FAINT = "#9aa0a6"
PANEL = "#c9ced4"
FLUID = "#2f7dd1"
CLIP = "#d1682f"


def _poly(pts, close=True) -> str:
    d = "M " + " L ".join(f"{x:.3f},{y:.3f}" for x, y in pts)
    return d + (" Z" if close else "")


def _outline(sdf, offset, n=180):
    return [(r * math.cos(t), r * math.sin(t))
            for t, r in ((2 * math.pi * i / n,
                          ray(sdf, 2 * math.pi * i / n, offset)) for i in range(n))]


def _profile(s: NozzleSpec, theta: float):
    """Half the body silhouette in the plane at angle theta: [(w, z), ...]."""
    return [(ray(sdf, theta, off), z) for z, sdf, off in outer_stations(s)]


def _channel(s: NozzleSpec, theta: float, sign: float):
    out = []
    zs = [s.z_bottom, s.plenum_z]
    for i in range(1, 13):
        zs.append(s.plenum_z + (s.head_height - s.plenum_z) * i / 12)
    az = math.radians(s.aim_az)
    for z in zs:
        sdf, shift, _ = inner_section(s, z)
        cx, cy = shift * -math.sin(az), shift * math.cos(az)
        c = cy if abs(math.cos(theta)) < 0.5 else cx
        out.append((c + sign * ray(sdf, theta), z))
    return out


def _section(s: NozzleSpec, theta: float, title: str, show_clip: bool) -> str:
    """One elevation. theta picks the cutting plane: 0 is the long axis."""
    right = _profile(s, theta)
    left = _profile(s, theta + math.pi)
    body = [(w, -z) for w, z in right] + [(-w, -z) for w, z in reversed(left)]
    ch = [(w, -z) for w, z in _channel(s, theta, 1.0)]
    ch += [(w, -z) for w, z in reversed(_channel(s, theta + math.pi, -1.0))]

    g = [f'<text x="0" y="{-s.head_height * SCALE - 10:.1f}" class="ttl">{title}</text>']
    g.append(f'<rect x="-70" y="0" width="140" height="{s.panel * SCALE:.2f}" '
             f'fill="{PANEL}" stroke="none"/>')
    g.append(f'<path d="{_poly([(x * SCALE, y * SCALE) for x, y in body])}" '
             f'fill="#f4f5f7" stroke="{INK}" stroke-width="1.1"/>')
    g.append(f'<path d="{_poly([(x * SCALE, y * SCALE) for x, y in ch])}" '
             f'fill="{FLUID}" fill-opacity="0.16" stroke="{FLUID}" stroke-width="0.9"/>')

    if show_clip:
        cg = clip_geometry(s)
        w = _half_gap(cg, cg["y_contact"])
        for sign in (-1, 1):
            prong = [(sign * w, -cg["z_bot"]), (sign * 8.0, -cg["z_bot"]),
                     (sign * 8.0, -cg["z_top"]), (sign * (w - cg["bevel"]),
                                                  -cg["z_top"])]
            rim = [(sign * 7.5, -cg["z_bot"]), (sign * (7.5 + s.clip_wing),
                                                -cg["z_bot"]),
                   (sign * (7.5 + s.clip_wing), -cg["z_rim_top"]),
                   (sign * 7.5, -cg["z_rim_top"])]
            for pts in (prong, rim):
                g.append(f'<path d="{_poly([(x * SCALE, y * SCALE) for x, y in pts])}"'
                         f' fill="{CLIP}" fill-opacity="0.30" stroke="{CLIP}" '
                         f'stroke-width="0.9"/>')
        g.append(f'<text x="0" y="{-s.z_bottom * SCALE + 16:.1f}" class="key">'
                 f'the clip wedges up the flare as it goes in</text>')
    else:
        tilt = math.radians(s.aim_deg)
        x0, y0 = 0.0, -s.head_height
        dx, dy = math.sin(tilt), -math.cos(tilt)
        shift = (s.head_height - s.plenum_z) * math.tan(tilt)
        g.append(f'<path d="M {shift * SCALE:.1f},{y0 * SCALE:.1f} '
                 f'l {dx * 7 * SCALE:.1f},{dy * 7 * SCALE:.1f}" stroke="{FLUID}" '
                 f'stroke-width="1.2" stroke-dasharray="4 3" marker-end="url(#ar)"/>')
        g.append(f'<text x="{(shift + dx * 7) * SCALE + 8:.1f}" '
                 f'y="{(y0 + dy * 7) * SCALE:.1f}" class="lbl">'
                 f'{s.aim_deg:.0f}&#176;</text>')
    return "\n".join(g)


def _plan(s: NozzleSpec) -> str:
    hole = s.hole()
    g = ['<text x="0" y="-84" class="ttl">plan, looking down</text>']
    g.append(f'<rect x="-95" y="-72" width="190" height="144" fill="{PANEL}"/>')
    for off, fill, stroke, dash in ((0.0, "#ffffff", INK, ""),):
        pts = [(x * SCALE, y * SCALE) for x, y in _outline(hole, off)]
        g.append(f'<path d="{_poly(pts)}" fill="{fill}" stroke="{stroke}" '
                 f'stroke-width="1.2"/>')
    for off, col, dash in ((s.head_margin, INK, "5 3"),
                           (-s.clearance, FAINT, "2 2")):
        pts = [(x * SCALE, y * SCALE) for x, y in _outline(hole, off)]
        g.append(f'<path d="{_poly(pts)}" fill="none" stroke="{col}" '
                 f'stroke-width="0.9" stroke-dasharray="{dash}"/>')
    L, W = s.L, s.W
    g.append(f'<path d="M {-L / 2 * SCALE:.1f},0 L {L / 2 * SCALE:.1f},0" '
             f'stroke="{INK}" stroke-width="0.6" stroke-dasharray="3 2"/>')
    g.append(f'<text x="0" y="-6" class="dim">{L:.1f}</text>')
    g.append(f'<text x="6" y="{W / 2 * SCALE - 3:.1f}" class="dim">{W:.1f}</text>')
    g.append(f'<path d="M -99,{-s.lobe_width * s.fit_scale / 2 * SCALE:.1f} '
             f'l 0,{s.lobe_width * s.fit_scale * SCALE:.1f}" stroke="{FAINT}" '
             f'stroke-width="0.7"/>')
    g.append(f'<text x="-104" y="4" class="dim" text-anchor="end">'
             f'{s.lobe_width * s.fit_scale:.1f}</text>')
    g.append('<text x="0" y="92" class="key">solid: the hole &#183; dashed: '
             'the head &#183; dotted: the plug</text>')
    return "\n".join(g)


def _clip_plan(s: NozzleSpec) -> str:
    """The clip from below, in the assembly frame, with the hole dashed in."""
    cg = clip_geometry(s)
    g = [f'<text x="0" y="{(cg["y_bar0"] - 6.6) * SCALE:.1f}" class="ttl">'
         f'the clip, from underneath</text>']
    pts = [(x * SCALE, y * SCALE) for x, y in _outline(s.hole(), 0.0)]
    g.append(f'<path d="{_poly(pts)}" fill="{PANEL}" stroke="{FAINT}" '
             f'stroke-width="0.8" stroke-dasharray="4 3"/>')
    y0, y1 = cg["y_root"], cg["y_tip"]
    for sign in (-1, 1):
        w0, w1 = _half_gap(cg, y0), _half_gap(cg, y1)
        prong = [(sign * w0, y0), (sign * 8.0, y0), (sign * 8.0, y1),
                 (sign * w1, y1)]
        g.append(f'<path d="{_poly([(x * SCALE, y * SCALE) for x, y in prong])}" '
                 f'fill="{CLIP}" fill-opacity="0.22" stroke="{CLIP}" '
                 f'stroke-width="0.9"/>')
        wing = [(sign * 7.5, cg["y_bar1"]), (sign * cg["x_out"], cg["y_bar1"]),
                (sign * cg["x_out"], y1 - 1.0), (sign * 7.5, y1 - 1.0)]
        g.append(f'<path d="{_poly([(x * SCALE, y * SCALE) for x, y in wing])}" '
                 f'fill="{CLIP}" fill-opacity="0.38" stroke="{CLIP}" '
                 f'stroke-width="0.9"/>')
    bar = [(-cg["x_out"], cg["y_bar0"]), (cg["x_out"], cg["y_bar0"]),
           (cg["x_out"], cg["y_bar1"]), (-cg["x_out"], cg["y_bar1"])]
    g.append(f'<path d="{_poly([(x * SCALE, y * SCALE) for x, y in bar])}" '
             f'fill="{CLIP}" fill-opacity="0.38" stroke="{CLIP}" stroke-width="0.9"/>')
    g.append(f'<path d="M {-cg["x_out"] * SCALE - 26:.1f},'
             f'{(cg["y_bar0"] - 3.0) * SCALE:.1f} l 0,{2.2 * SCALE:.1f}" '
             f'stroke="{INK}" stroke-width="1.1" marker-end="url(#ak)"/>')
    g.append(f'<text x="{-cg["x_out"] * SCALE - 26:.1f}" '
             f'y="{(cg["y_bar0"] - 3.8) * SCALE:.1f}" class="key">push</text>')
    g.append(f'<text x="0" y="{(y1 + 3.4) * SCALE:.1f}" class="key">'
             f'darker: bears on the sheet &#183; lighter: rides the flare</text>')
    return "\n".join(g)


def render(s: NozzleSpec, report=None) -> str:
    report = report or check_fit(s)
    w, h = 1120, 600
    css = ("text{font-family:ui-sans-serif,system-ui,'Helvetica Neue',sans-serif;"
           "fill:%s}.ttl{font-size:13px;font-weight:600;text-anchor:middle}"
           ".lbl{font-size:11px}.dim{font-size:11px;text-anchor:middle;fill:%s}"
           ".key{font-size:10.5px;text-anchor:middle;fill:%s}"
           ".note{font-size:11px}" % (INK, INK, FAINT))
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'width="{w}" height="{h}">',
        f'<style>{css}</style>',
        '<defs><marker id="ar" viewBox="0 0 10 10" refX="8" refY="5" '
        f'markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" '
        f'fill="{FLUID}"/></marker>'
        '<marker id="ak" viewBox="0 0 10 10" refX="8" refY="5" '
        f'markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" '
        f'fill="{INK}"/></marker></defs>',
        f'<rect width="{w}" height="{h}" fill="#ffffff"/>',
        f'<g transform="translate(190,150)">{_plan(s)}</g>',
        f'<g transform="translate(190,450)">{_clip_plan(s)}</g>',
        f'<g transform="translate(580,170)">'
        f'{_section(s, 0.0, "section on the long axis, with the clip", True)}</g>',
        f'<g transform="translate(900,170)">'
        f'{_section(s, math.pi / 2, "section across the neck", False)}</g>',
    ]
    lines = [
        f"hole {s.L:.1f} x {s.W:.1f} mm, sheet {s.panel:.1f} mm",
        f"plug clearance {s.clearance:.2f} mm/side, "
        f"tightest way in {report.insertion:.2f} mm",
        f"wall beside the channel {report.min_wall:.2f} mm, "
        f"jet {s.jet_w:.1f} x {s.jet_h:.2f} mm",
        f"clip grips {report.panel_range[0]:.1f}-{report.panel_range[1]:.1f} mm sheet",
    ]
    for i, line in enumerate(lines):
        parts.append(f'<text x="500" y="{h - 132 + i * 16}" class="note">{line}</text>')
    parts.append("</svg>")
    return "\n".join(parts)
