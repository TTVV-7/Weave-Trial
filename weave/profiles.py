"""Printer, material and shade profiles.

Kept apart from the geometry on purpose: the toolpath is a shape, and how hot
and how fast to lay it down is a separate question that changes per machine.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from .geometry import LampSpec


@dataclass
class Printer:
    name: str = "generic-i3"
    bed_x: float = 220.0
    bed_y: float = 220.0
    max_z: float = 250.0
    nozzle: float = 0.4
    filament_diameter: float = 1.75
    #: Absolute E, G92-zeroed at the start. Set False for relative (M83).
    absolute_e: bool = True
    start_gcode: str = """\
M190 S{bed}
M104 S{nozzle_temp}
G28
G29 ; mesh bed levelling -- delete this line if your printer has no probe
M109 S{nozzle_temp}
G92 E0
; prime line, well clear of the shade
G1 Z0.3 F900
G1 X{prime_x0} Y{prime_y} F3000
G1 X{prime_x1} Y{prime_y} E14 F1000
G1 X{prime_x1} Y{prime_y_2} E15 F1000
G92 E0
G1 Z2 F900
"""
    end_gcode: str = """\
M107
G91
G1 Z5 E-3 F900
G90
G1 X5 Y{bed_y_safe} F4000
M104 S0
M140 S0
M84
"""


@dataclass
class Material:
    name: str = "petg-natural"
    nozzle_temp: int = 240
    bed_temp: int = 80
    #: Global flow trim.
    flow: float = 1.0
    retract_mm: float = 1.2
    retract_speed: int = 2400
    #: mm/s
    first_layer_speed: float = 14.0
    foot_speed: float = 28.0
    #: The weave is mostly unsupported. Slow is what makes it hold its shape.
    weave_speed: float = 16.0
    fade_speed: float = 18.0
    rim_speed: float = 22.0
    travel_speed: float = 120.0
    #: Percent, 0-100.
    fan_first_layer: int = 0
    fan_foot: int = 40
    #: Free-air beads need maximum cooling or they droop before they set.
    fan_weave: int = 100


PRINTERS: dict[str, Printer] = {
    "generic-i3": Printer(),
    "prusa-mk4": Printer(name="prusa-mk4", bed_x=250, bed_y=210, max_z=220),
    "bambu-p1s": Printer(name="bambu-p1s", bed_x=256, bed_y=256, max_z=256),
    "ender3": Printer(name="ender3", bed_x=220, bed_y=220, max_z=250),
    "voron-350": Printer(name="voron-350", bed_x=350, bed_y=350, max_z=330),
}

MATERIALS: dict[str, Material] = {
    "petg-natural": Material(),
    # Translucent PLA is the easiest to get a clean glow from, and PLA holds a
    # free-air bead better than PETG. It is also the least heat-tolerant, so
    # keep it to LED bulbs.
    "pla-translucent": Material(
        name="pla-translucent", nozzle_temp=210, bed_temp=60,
        weave_speed=18.0, fade_speed=20.0, foot_speed=32.0,
        retract_mm=0.8, fan_foot=60,
    ),
    "petg-clear": Material(
        name="petg-clear", nozzle_temp=245, bed_temp=80,
        weave_speed=14.0, flow=0.97,
    ),
}


def _spec(**kw) -> LampSpec:
    return replace(LampSpec(), **kw)


#: Named shades. ``rise_per_turn`` is the see-through dial; ``waves_per_turn``
#: trades hole size against how far each bead has to bridge unsupported.
LAMPS: dict[str, LampSpec] = {
    # ~80% open. The default: unmistakably see-through, still rigid.
    "open-weave": _spec(),
    # ~87% open. Wide diamonds, a real lattice. Longer bridges, print it slow.
    "airy": _spec(rise_per_turn=3.4, waves_per_turn=36.5, height=150.0),
    # ~64% open. Fine slits, a soft even glow rather than visible bulb.
    "frosted": _spec(rise_per_turn=1.25, waves_per_turn=24.5, height=150.0),
    # Short wide shade for a table lamp base.
    "table-shade": _spec(height=110.0, bottom_radius=60.0, top_radius=48.0,
                         waves_per_turn=36.5, rise_per_turn=2.4),
    # Tapered pendant with a waist.
    "pendant": _spec(height=180.0, bottom_radius=55.0, top_radius=30.0,
                     belly=6.0, waves_per_turn=32.5, rise_per_turn=2.4),
    # Small, fast, cheap. Print this one first.
    "test-ring": _spec(height=40.0, bottom_radius=30.0, top_radius=30.0,
                       waves_per_turn=20.5, ramp_turns=2, rim_height=1.2),
}
