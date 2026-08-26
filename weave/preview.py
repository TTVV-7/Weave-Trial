"""Render the toolpath to a standalone SVG, so you can see it before you print it.

Orthographic front elevation. Beads are bucketed by depth and drawn back to
front, faint at the back and solid at the front, which is what makes the weave
read as a weave rather than a smear. The right-hand panel puts a warm disc
behind the same geometry to show roughly what gets through when it is lit.
"""

from __future__ import annotations

import math

from .geometry import LampSpec, Toolpath, check_support, stats


BANDS = 20


def _project(path: Toolpath, z_lo: float, z_hi: float):
    """Yield ``(depth_band, x0, y0, x1, y1)`` for beads within a height range."""
    segs = path.segments
    prev = None
    for i, s in enumerate(segs):
        if prev is not None and i not in path.breaks:
            if z_lo <= s.z <= z_hi and z_lo <= prev.z <= z_hi:
                depth = (s.y + prev.y) / 2
                yield depth, prev.x, -prev.z, s.x, -s.z
        prev = s


def _panel(path: Toolpath, spec: LampSpec, z_lo: float, z_hi: float,
           width: float, stroke: float, lit: bool) -> tuple[str, float, float]:
    """Return SVG body for one elevation, plus its drawing extents."""
    items = list(_project(path, z_lo, z_hi))
    if not items:
        return "", width, width
    depths = [d for d, *_ in items]
    d_lo, d_hi = min(depths), max(depths)
    span = (d_hi - d_lo) or 1.0

    buckets: list[list[str]] = [[] for _ in range(BANDS)]
    for d, x0, y0, x1, y1 in items:
        b = min(BANDS - 1, int((d - d_lo) / span * BANDS))
        buckets[b].append(f"M{x0:.2f} {y0:.2f}L{x1:.2f} {y1:.2f}")

    body: list[str] = []
    if lit:
        r = max(spec.bottom_radius, spec.top_radius) * 0.55
        cy = -(z_lo + z_hi) / 2
        body.append(
            f'<circle cx="0" cy="{cy:.1f}" r="{r:.1f}" fill="url(#bulb)"/>')
    for b, ds in enumerate(buckets):
        if not ds:
            continue
        t = b / (BANDS - 1)  # 0 = furthest away, 1 = nearest the viewer
        if lit:
            # Front beads block the light; back beads are washed out by it.
            col = f"rgb({int(30 + 40 * (1 - t))},{int(26 + 34 * (1 - t))},{int(22 + 30 * (1 - t))})"
            op = 0.25 + 0.75 * t
        else:
            g = int(205 - 165 * t)
            col = f"rgb({g},{g},{g + 6})"
            op = 0.35 + 0.65 * t
        body.append(
            f'<path d="{"".join(ds)}" fill="none" stroke="{col}" '
            f'stroke-opacity="{op:.2f}" stroke-width="{stroke:.2f}" '
            f'stroke-linecap="round"/>')
    return "\n".join(body), width, width


def render(spec: LampSpec, path: Toolpath, *, detail_turns: float = 4.0) -> str:
    """Build the full SVG document."""
    st = stats(spec, path)
    rep = check_support(spec, path)
    h = st["actual_height_mm"]
    r = max(spec.bottom_radius, spec.top_radius) + max(0.0, spec.belly)

    bead = spec.mesh_bead_width
    elev, _, _ = _panel(path, spec, 0, h + 1, 2 * r, bead, lit=False)
    lit, _, _ = _panel(path, spec, 0, h + 1, 2 * r, bead, lit=True)

    d_lo = h * 0.45
    d_hi = d_lo + detail_turns * spec.rise_per_turn
    det, _, _ = _panel(path, spec, d_lo, d_hi, 2 * r, bead, lit=False)

    pad = 14.0
    col_w = 2 * r + pad * 2
    det_scale = min(3.0, (h * 0.55) / max(d_hi - d_lo, 1e-6))
    total_w = col_w * 3
    total_h = h + pad * 2 + 58

    def label(x, y, text, size=7.5, col="#8a8a92", weight=400):
        return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{col}" '
                f'font-weight="{weight}" font-family="ui-monospace,SFMono-Regular,Menlo,monospace" '
                f'text-anchor="middle">{text}</text>')

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w:.0f}" '
        f'height="{total_h:.0f}" viewBox="0 0 {total_w:.1f} {total_h:.1f}">',
        '<defs>'
        '<radialGradient id="bulb">'
        '<stop offset="0%" stop-color="#fff6df"/>'
        '<stop offset="55%" stop-color="#ffdc9b"/>'
        '<stop offset="100%" stop-color="#f0b95c" stop-opacity="0"/>'
        '</radialGradient>'
        '</defs>',
        f'<rect width="{total_w:.1f}" height="{total_h:.1f}" fill="#fbfbfc"/>',
    ]

    # elevation
    parts.append(f'<g transform="translate({col_w / 2:.1f},{pad + h:.1f})">{elev}</g>')
    parts.append(label(col_w / 2, total_h - 32,
                       f"elevation &#183; {h:.0f} mm tall &#183; {2 * r:.0f} mm across", 9, "#2c2c33", 600))
    parts.append(label(col_w / 2, total_h - 19,
                       f"{st['path_length_m']:.0f} m of bead &#183; {st['filament_g']:.0f} g"))

    # detail
    parts.append(
        f'<g transform="translate({col_w * 1.5:.1f},{pad + h * 0.72:.1f}) '
        f'scale({det_scale:.3f}) translate(0,{(d_lo + d_hi) / 2:.1f})">{det}</g>')
    parts.append(label(col_w * 1.5, total_h - 32,
                       f"detail &#183; {detail_turns:.0f} turns at {det_scale:.1f}&#215;", 9, "#2c2c33", 600))
    parts.append(label(col_w * 1.5, total_h - 19,
                       f"{spec.nodes_per_turn} welds/turn &#183; holes to "
                       f"{spec.max_hole_height:.1f} mm &#183; bridge {rep.max_free_span:.1f} mm"))

    # lit
    parts.append(f'<g transform="translate({col_w * 2.5:.1f},{pad + h:.1f})">{lit}</g>')
    parts.append(label(col_w * 2.5, total_h - 32,
                       f"lit &#183; {spec.open_area_fraction * 100:.0f}% open air", 9, "#2c2c33", 600))
    parts.append(label(col_w * 2.5, total_h - 19,
                       "shown against a bulb at the centre"))

    parts.append('</svg>')
    return "\n".join(parts)
