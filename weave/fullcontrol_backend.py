"""Optional FullControl backend.

The built-in writer in :mod:`weave.gcode` is the one used by default: it has no
dependencies and it knows about the per-bead extrusion heights the weave needs.
This module exists so the same geometry can be handed to FullControl instead,
for its viewer and its printer library.

Install with ``pip install fullcontrol``; nothing else in the project imports
it, so the toolpath still generates without it.
"""

from __future__ import annotations

from .geometry import LampSpec, Toolpath
from .profiles import Material, Printer


class FullControlUnavailable(RuntimeError):
    pass


def _fc():
    try:
        import fullcontrol as fc
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise FullControlUnavailable(
            "fullcontrol is not installed; run `pip install fullcontrol`, or "
            "use the built-in writer (the default)"
        ) from exc
    return fc


def to_steps(spec: LampSpec, path: Toolpath, printer: Printer,
             material: Material, *, centre: tuple[float, float] | None = None):
    """Convert the toolpath to a FullControl design (a list of steps).

    Bead geometry is emitted as ``ExtrusionGeometry`` steps wherever it changes,
    which is what keeps the solid foot from being over-extruded at the same
    flow as the free-air weave.
    """
    fc = _fc()
    cx, cy = centre if centre else (printer.bed_x / 2, printer.bed_y / 2)

    steps: list = [
        fc.Extruder(relative_gcode=not printer.absolute_e),
        fc.Printer(print_speed=material.weave_speed * 60,
                   travel_speed=material.travel_speed * 60),
        fc.Hotend(temp=material.nozzle_temp),
        fc.Buildplate(temp=material.bed_temp, wait=True),
        fc.Fan(speed_percent=0),
    ]

    speeds = {"foot": material.foot_speed, "weave": material.weave_speed,
              "fade": material.fade_speed, "rim": material.rim_speed}
    bead = None
    kind = None
    fan = None

    for i, s in enumerate(path.segments):
        if i in path.breaks and i:
            steps.append(fc.Extruder(on=False))
            steps.append(fc.Point(x=s.x + cx, y=s.y + cy, z=s.z + 2.0))
            steps.append(fc.Point(x=s.x + cx, y=s.y + cy, z=s.z))
            steps.append(fc.Extruder(on=True))
        if (s.bead_w, s.bead_h) != bead:
            bead = (s.bead_w, s.bead_h)
            steps.append(fc.ExtrusionGeometry(area_model="rectangle",
                                             width=s.bead_w, height=s.bead_h))
        if s.kind != kind:
            kind = s.kind
            steps.append(fc.Printer(print_speed=speeds.get(kind,
                                                           material.weave_speed) * 60))
        want_fan = 0 if s.z <= spec.layer_height + 1e-6 else (
            material.fan_foot if s.kind == "foot" else material.fan_weave)
        if want_fan != fan:
            fan = want_fan
            steps.append(fc.Fan(speed_percent=want_fan))
        steps.append(fc.Point(x=s.x + cx, y=s.y + cy, z=s.z))

    return steps


def write(spec: LampSpec, path: Toolpath, printer: Printer, material: Material,
          *, centre: tuple[float, float] | None = None,
          printer_name: str = "generic") -> str:
    """Render g-code through FullControl."""
    fc = _fc()
    steps = to_steps(spec, path, printer, material, centre=centre)
    controls = fc.GcodeControls(
        printer_name=printer_name,
        initialization_data={
            "primer": "front_lines_then_y",
            "print_speed": material.weave_speed * 60,
            "travel_speed": material.travel_speed * 60,
            "nozzle_temp": material.nozzle_temp,
            "bed_temp": material.bed_temp,
            "extrusion_width": spec.mesh_bead_width,
            "extrusion_height": spec.mesh_bead_height,
        },
    )
    return fc.transform(steps, "gcode", controls)
