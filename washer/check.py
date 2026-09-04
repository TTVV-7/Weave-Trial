"""Does this part go in the hole, hold, flow, and print?

The generator will not write an STL that fails this. The lamp in this repo
refuses to write g-code whose weave does not weld; the same rule applies here,
because every failure mode of this part is a dimension that can be measured
before anything is printed:

  insertion   the whole shank goes in through the hole from above, or the part
              cannot be fitted at all -- the barb is the usual offender.
  wall        the fluid channel is inside the body with plastic left around it.
  clip        the wedge reaches the flare for the sheet it is being fitted to.
  print       nothing overhangs past 45 degrees with the head face down.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .geom import ray
from .mesh import Mesh
from .parts import _half_gap, _ring, clip_geometry, inner_ring, outer_stations
from .spec import NozzleSpec

#: PETG. Close enough to PLA and PP for a part this small.
DENSITY_G_MM3 = 1.27e-3


@dataclass
class FitReport:
    insertion: float = 0.0
    plug_clearance: float = 0.0
    head_margin: float = 0.0
    min_wall: float = 0.0
    wall_at: float = 0.0
    jet_area: float = 0.0
    jet_min: float = 0.0
    max_overhang: float = 0.0
    tip_wall: float = 0.0
    max_ledge: float = 0.0
    panel_range: tuple[float, float] = (0.0, 0.0)
    clip_travel: float = 0.0
    mass_g: float = 0.0
    problems: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems


def _seg_dist(p, a, b) -> float:
    vx, vy = b[0] - a[0], b[1] - a[1]
    wx, wy = p[0] - a[0], p[1] - a[1]
    ln = vx * vx + vy * vy
    t = 0.0 if ln == 0 else max(0.0, min(1.0, (wx * vx + wy * vy) / ln))
    return math.hypot(wx - t * vx, wy - t * vy)


def _poly_dist(p, poly) -> float:
    return min(_seg_dist(p, poly[i], poly[(i + 1) % len(poly)])
               for i in range(len(poly)))


#: The lead-in chamfer on the barb tip is thin on purpose and carries nothing.
LEAD_IN = 0.6


def check_fit(s: NozzleSpec, nozzle: Mesh | None = None) -> FitReport:
    r = FitReport()
    n = s.facets
    hole = s.hole()
    stations = outer_stations(s)

    # -- does the shank pass through the hole? -------------------------------
    r.insertion = 1e9
    for z, sdf, off in stations:
        if z >= 0.0:
            continue
        for i in range(n):
            th = 2.0 * math.pi * i / n
            r.insertion = min(r.insertion, ray(hole, th) - ray(sdf, th, off))
    r.plug_clearance = s.clearance
    r.head_margin = s.head_margin
    if r.insertion < 0.15:
        worst = "barb" if s.barb_ridge_r * 2 > s.W - 0.6 else "shank"
        r.problems.append(
            f"{worst} is {abs(r.insertion):.2f} mm too big to go through the hole"
            if r.insertion < 0 else
            f"only {r.insertion:.2f} mm of room getting the shank through the hole")

    # -- wall between the channel and the outside ----------------------------
    rings = [(z, _ring(sdf, z, n, off)) for z, sdf, off in stations]
    r.min_wall = 1e9
    z = s.z_bottom
    while z <= s.head_height + 1e-9:
        for (z0, r0), (z1, r1) in zip(rings, rings[1:]):
            if z0 - 1e-9 <= z <= z1 + 1e-9 and z1 > z0:
                t = (z - z0) / (z1 - z0)
                outer = [(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
                         for a, b in zip(r0, r1)]
                inner = inner_ring(s, z, n)
                d = min(_poly_dist(p, outer) for p in inner[::2])
                if z <= s.z_bottom + LEAD_IN:
                    r.tip_wall = d if r.tip_wall == 0.0 else min(r.tip_wall, d)
                elif d < r.min_wall:
                    r.min_wall, r.wall_at = d, z
                break
        z += 0.25
    if r.min_wall < 0.8:
        r.problems.append(
            f"only {r.min_wall:.2f} mm of wall beside the channel at z={r.wall_at:.1f}")

    # -- the jet -------------------------------------------------------------
    r.jet_area = s.jet_w * s.jet_h
    r.jet_min = min(s.jet_w, s.jet_h)
    if r.jet_min < 0.45:
        r.problems.append(f"jet is {r.jet_min:.2f} mm across; a 0.4 nozzle cannot print it")

    # -- overhangs, with the head face down on the bed -----------------------
    # Measured off the triangles that get written, not off the radius change:
    # where the section is not round, a radial step is not the surface slope.
    # Printed head down, a face that points along +z here points at the bed.
    if nozzle is not None:
        for a, b, c in nozzle.tris:
            ux, uy, uz = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
            vx, vy, vz = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
            nx, ny, nz = (uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx)
            ln = math.sqrt(nx * nx + ny * ny + nz * nz)
            if ln < 1e-12 or nz <= 0.0:
                continue
            angle = math.degrees(math.asin(min(1.0, nz / ln)))
            if angle < 85.0:                   # 85+ is a flat ledge, sized below
                r.max_overhang = max(r.max_overhang, angle)
    for (z0, s0, o0), (z1, s1, o1) in zip(stations, stations[1:]):
        if z1 - z0 >= 1e-9:
            continue
        for i in range(n):
            th = 2.0 * math.pi * i / n
            d = ray(s1, th, o1) - ray(s0, th, o0)
            if d < 0:
                r.max_ledge = max(r.max_ledge, -d)
    r.max_overhang = max(r.max_overhang, s.aim_deg)
    if r.max_overhang > 45.0:
        r.problems.append(f"{r.max_overhang:.0f} deg overhang; 45 is the limit")
    if r.max_ledge > 1.0:
        r.problems.append(f"{r.max_ledge:.2f} mm unsupported ledge")

    # -- what the clip can clamp --------------------------------------------
    g = clip_geometry(s)
    lo_gap, hi_gap = _half_gap(g, g["y_root"]), _half_gap(g, g["y_tip"])
    r.clip_travel = g["y_tip"] - g["y_root"]
    covered = []
    t = 0.3
    while t <= 8.0:
        z_top = -(t + s.clip_rim)
        contact = s.flare_hx_at(z_top - s.clip_thick)
        if z_top <= s.z_waist_bot + 1e-9 and lo_gap <= contact <= hi_gap:
            covered.append(t)
        t += 0.05
    r.panel_range = (min(covered), max(covered)) if covered else (0.0, 0.0)
    if not covered:
        r.problems.append("clip cannot reach the flare on any sheet thickness")
    elif not (r.panel_range[0] - 1e-9 <= s.panel <= r.panel_range[1] + 1e-9):
        r.problems.append(
            f"clip grips {r.panel_range[0]:.1f}-{r.panel_range[1]:.1f} mm sheet, "
            f"not the {s.panel:.1f} mm it is set up for")

    if nozzle is not None:
        r.mass_g = nozzle.volume() * DENSITY_G_MM3
    return r
