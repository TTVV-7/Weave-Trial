"""Turn a :class:`~weave.geometry.Toolpath` into g-code.

Deliberately a plain writer with no slicer involved. A slicer would try to
turn this into layers, and the whole point is that it is not layers -- one
bead climbs continuously and welds to itself on the way past.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone

from .geometry import LampSpec, Segment, Toolpath, check_support, stats
from .profiles import Material, Printer


def _speed_for(kind: str, mat: Material) -> float:
    return {
        "foot": mat.foot_speed,
        "weave": mat.weave_speed,
        "fade": mat.fade_speed,
        "rim": mat.rim_speed,
    }.get(kind, mat.weave_speed)


def _fan_for(kind: str, mat: Material) -> int:
    return mat.fan_foot if kind == "foot" else mat.fan_weave


def write(
    spec: LampSpec,
    path: Toolpath,
    printer: Printer,
    material: Material,
    *,
    centre: tuple[float, float] | None = None,
) -> str:
    """Render the toolpath as a g-code program."""
    cx, cy = centre if centre else (printer.bed_x / 2, printer.bed_y / 2)

    radius = max(spec.bottom_radius, spec.top_radius) + max(0.0, spec.belly)
    if 2 * radius + 10 > min(printer.bed_x, printer.bed_y):
        raise ValueError(
            f"shade is {2 * radius:.0f} mm across but the {printer.name} bed is "
            f"{printer.bed_x:.0f}x{printer.bed_y:.0f} mm"
        )
    report = check_support(spec, path)
    st = stats(spec, path)
    if st["actual_height_mm"] > printer.max_z:
        raise ValueError(
            f"shade is {st['actual_height_mm']:.0f} mm tall, over the "
            f"{printer.name} limit of {printer.max_z:.0f} mm"
        )

    fil_area = math.pi * (printer.filament_diameter / 2) ** 2
    out: list[str] = []
    w = out.append

    w(f"; woven see-through lamp shade")
    w(f"; generated {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    w(f"; printer {printer.name} / material {material.name}")
    w(f"; {st['actual_height_mm']:.1f} mm tall, {2 * radius:.0f} mm across")
    w(f"; open area {spec.open_area_fraction * 100:.0f}%  "
      f"({spec.nodes_per_turn} welds per turn, holes up to "
      f"{spec.max_hole_height:.1f} mm)")
    w(f"; longest unsupported bridge {report.max_free_span:.1f} mm, "
      f"deepest weld dip {report.max_dip:.2f} mm")
    w(f"; ~{st['filament_m']:.1f} m / {st['filament_g']:.0f} g of filament")
    w(f"; NOT SLICED -- one continuous non-planar bead. Do not re-slice.")
    w("")

    fmt = dict(
        bed=material.bed_temp,
        nozzle_temp=material.nozzle_temp,
        prime_x0=5.0, prime_x1=printer.bed_x - 5.0,
        prime_y=3.0, prime_y_2=6.0,
        bed_y_safe=printer.bed_y - 10.0,
    )
    w(printer.start_gcode.format(**fmt).rstrip())
    w("G21 ; mm")
    w("G90 ; absolute positions")
    w("M82 ; absolute extrusion" if printer.absolute_e else "M83 ; relative extrusion")
    w("G92 E0")
    w("")

    e = 0.0
    fan = -1
    speed = -1.0
    prev: Segment | None = None

    def move(x, y, z, f, ecmd="") -> None:
        w(f"G1 X{x:.3f} Y{y:.3f} Z{z:.3f}{ecmd} F{f:.0f}")

    for i, s in enumerate(path.segments):
        x, y, z = s.x + cx, s.y + cy, s.z
        start_of_path = i in path.breaks

        want_fan = 0 if s.z <= spec.layer_height + 1e-6 else _fan_for(s.kind, material)
        if want_fan != fan:
            w(f"M106 S{round(want_fan * 255 / 100)}" if want_fan else "M107")
            fan = want_fan

        if start_of_path or prev is None:
            if prev is not None:
                # Lift clear of the shade before crossing it, or the nozzle
                # will shear off whatever it passes over.
                w(f"G1 E{e - material.retract_mm:.4f} F{material.retract_speed}"
                  if printer.absolute_e else
                  f"G1 E-{material.retract_mm:.4f} F{material.retract_speed}")
                w(f"G1 Z{max(prev.z, z) + 2.0:.3f} F{material.travel_speed * 60:.0f}")
                w(f"G1 X{x:.3f} Y{y:.3f} F{material.travel_speed * 60:.0f}")
                w(f"G1 Z{z:.3f} F{material.travel_speed * 60:.0f}")
                w(f"G1 E{e:.4f} F{material.retract_speed}"
                  if printer.absolute_e else
                  f"G1 E{material.retract_mm:.4f} F{material.retract_speed}")
            else:
                w(f"G1 X{x:.3f} Y{y:.3f} F{material.travel_speed * 60:.0f}")
                w(f"G1 Z{z:.3f} F{material.travel_speed * 60:.0f}")
            prev = s
            continue

        d = math.dist((prev.x, prev.y, prev.z), (s.x, s.y, s.z))
        if d < 1e-9:
            continue
        vol = d * spec.bead_area(s.bead_w, s.bead_h) * material.flow
        de = vol / fil_area
        e += de

        mm_s = (material.first_layer_speed
                if s.z <= spec.layer_height + 1e-6
                else _speed_for(s.kind, material))
        f = mm_s * 60.0
        ecmd = f" E{e:.4f}" if printer.absolute_e else f" E{de:.4f}"
        if abs(f - speed) > 1:
            move(x, y, z, f, ecmd)
            speed = f
        else:
            w(f"G1 X{x:.3f} Y{y:.3f} Z{z:.3f}{ecmd}")
        prev = s

    w("")
    w(printer.end_gcode.format(**fmt).rstrip())
    w("")
    return "\n".join(out)
