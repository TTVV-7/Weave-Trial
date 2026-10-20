#!/usr/bin/env python3
"""A towable 3-phase diesel generator, as a STEP model.

    python generator/generator.py                    # write the STEP + preview
    python generator/generator.py --length 4800 --height 2000

A sound-attenuated 300 kVA / 240 kW prime, 3-phase, 480/600 V selectable
generator on a tandem-axle trailer - sized to run a concrete line pump
(~75 kW), a 185 cfm air compressor (~45 kW) and a small batch plant (~75 kW)
together with headroom for motor starting. Generic: no make or model.

The enclosure sits on a double-walled base fuel tank (110% containment) on
the trailer chassis. Gull-wing service doors run down both sides, with air
intake louvres at the front, the radiator discharge grille at the rear and
the exhaust stack and single lifting eye on the roof. The output panel on the
kerb side carries a main breaker, a voltage selector, five cam-lok
connectors (three phases, neutral, ground) and convenience receptacles.

All dimensions are in millimetres. X runs from the hitch (negative) to the
back of the trailer, Y across it, Z up, with the origin on the ground under
the front face of the enclosure.

Needs CadQuery (`pip install cadquery`).
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import cadquery as cq

HERE = Path(__file__).resolve().parent

BODY = cq.Color(0.96, 0.78, 0.10)       # enclosure
DARK = cq.Color(0.18, 0.18, 0.18)       # chassis, base tank, louvres
STEEL = cq.Color(0.55, 0.57, 0.60)
TYRE = cq.Color(0.08, 0.08, 0.08)
RIM = cq.Color(0.75, 0.75, 0.75)
PANEL = cq.Color(0.85, 0.86, 0.88)
RED = cq.Color(0.80, 0.10, 0.10)
CAMLOK = {"L1": cq.Color(0.10, 0.10, 0.10), "L2": cq.Color(0.80, 0.10, 0.10),
          "L3": cq.Color(0.10, 0.25, 0.80), "N": cq.Color(0.95, 0.95, 0.95),
          "G": cq.Color(0.10, 0.60, 0.20)}


@dataclass
class Spec:
    length: float = 4300        # enclosure, X
    width: float = 1900         # enclosure, Y
    height: float = 1650        # enclosure above the base tank
    tank_height: float = 350    # base fuel tank (~800 L)
    deck: float = 680           # top of the chassis rails
    wheel_dia: float = 760
    drawbar: float = 1700       # hitch eye ahead of the enclosure


def box(dx, dy, dz, x, y, z):
    """A box by size, placed by its min corner."""
    return cq.Workplane().box(dx, dy, dz, centered=False).translate((x, y, z)).val()


def cyl(r, h, base, axis=(0, 0, 1)):
    return cq.Solid.makeCylinder(r, h, cq.Vector(*base), cq.Vector(*axis))


def louvres(x0, x1, z0, z1, y_face, out, pitch=45):
    """Angled slats standing proud of a side face at y_face, facing `out`."""
    slats = []
    z = z0
    while z + 30 <= z1:
        s = (cq.Workplane().box(x1 - x0, 4, 40)
             .rotate((0, 0, 0), (1, 0, 0), -out * 40)
             .translate(((x0 + x1) / 2, y_face + out * 12, z + 20)).val())
        slats.append(s)
        z += pitch
    frame = box(x1 - x0 + 40, 10, z1 - z0 + 40, x0 - 20, y_face - (10 if out < 0 else 0), z0 - 20)
    return cq.Compound.makeCompound(slats), frame


def build(s: Spec) -> cq.Assembly:
    asm = cq.Assembly(name="Towable_Generator_300kVA")
    L, W, H = s.length, s.width, s.height
    yl, yr = -W / 2, W / 2                 # +Y is the kerb side
    z_tank = s.deck
    z_enc = z_tank + s.tank_height
    z_top = z_enc + H

    # ---- trailer --------------------------------------------------------
    rail_h, rail_w = 150, 75
    rail_y = W / 2 - 250
    chassis = []
    for y in (-rail_y, rail_y):
        chassis.append(box(L + 200, rail_w, rail_h, -100, y - rail_w / 2, s.deck - rail_h))
    for x in range(0, int(L) + 1, 700):
        chassis.append(box(75, 2 * rail_y, 100, x - 37, -rail_y, s.deck - rail_h + 25))
    # A-frame drawbar to the hitch eye
    hx, hz = -s.drawbar, s.deck - 200
    for y in (-rail_y, rail_y):
        chassis.append(cq.Workplane(cq.Plane(origin=(0, y, s.deck - rail_h / 2),
                                             xDir=(0, 0, 1),
                                             normal=cq.Vector(hx, -y, hz - s.deck + rail_h / 2).normalized()))
                       .rect(100, 75).extrude(cq.Vector(hx, -y, hz - s.deck + rail_h / 2).Length).val())
    asm.add(cq.Compound.makeCompound(chassis), name="trailer_chassis", color=DARK)
    eye = (cq.Workplane("XY").circle(55).circle(35).extrude(40)
           .translate((hx - 60, 0, hz - 20)).val())
    asm.add(eye.fuse(box(120, 60, 40, hx - 20, -30, hz - 20)), name="pintle_eye", color=STEEL)
    # jack stand at the front, stabiliser legs at the rear
    asm.add(cyl(40, s.deck, (hx + 450, 0, 0)).fuse(box(200, 200, 12, hx + 350, -100, 0)),
            name="front_jack", color=STEEL)
    asm.add(cyl(30, 180, (hx + 450, 0, s.deck)).fuse(cyl(15, 160, (hx + 450, 30, s.deck + 150), (0, 1, 0))),
            name="jack_handle", color=STEEL)
    for i, y in enumerate((-rail_y, rail_y)):
        asm.add(box(80, 80, s.deck - rail_h, L - 40, y - 40, 0).fuse(box(220, 220, 12, L - 110, y - 110, 0)),
                name=f"rear_stabiliser_{i}", color=STEEL)

    # tandem axle, wheels outboard of the enclosure under fenders
    r = s.wheel_dia / 2
    tyre_w = 225
    wy = W / 2 + 40 + tyre_w / 2
    ax = [L * 0.52 - 480, L * 0.52 + 480]
    for i, x in enumerate(ax):
        asm.add(cyl(45, 2 * wy, (x, -wy, r), (0, 1, 0)), name=f"axle_{i}", color=DARK)
        for j, sgn in enumerate((-1, 1)):
            y0 = sgn * wy - tyre_w / 2
            tyre = cyl(r, tyre_w, (x, y0, r), (0, 1, 0)).cut(cyl(r * 0.62, tyre_w, (x, y0, r), (0, 1, 0)))
            rim = cyl(r * 0.62, tyre_w - 30, (x, y0 + 15, r), (0, 1, 0))
            asm.add(tyre, name=f"tyre_{i}_{j}", color=TYRE)
            asm.add(rim, name=f"rim_{i}_{j}", color=RIM)
    for j, sgn in enumerate((-1, 1)):
        # one fender over both wheels: a flat top and two sloped ends
        fy0 = W / 2 if sgn > 0 else -W / 2 - tyre_w - 80
        x0, x1 = ax[0] - r - 60, ax[1] + r + 60
        top_z = 2 * r + 60
        prof = [(x0, s.deck - 60), (x0 + 200, top_z), (x1 - 200, top_z), (x1, s.deck - 60),
                (x1 - 4, s.deck - 60), (x1 - 203, top_z - 4), (x0 + 203, top_z - 4), (x0 + 4, s.deck - 60)]
        fender = cq.Workplane("XZ").polyline(prof).close().extrude(-(tyre_w + 80)).translate((0, fy0, 0)).val()
        asm.add(fender, name=f"fender_{j}", color=DARK)

    # ---- base tank and enclosure ----------------------------------------
    asm.add(box(L, W, s.tank_height, 0, yl, z_tank), name="base_fuel_tank", color=DARK)
    asm.add(cyl(45, 40, (L * 0.15, yr - 120, z_enc)), name="fuel_fill_cap", color=RED)
    enc = cq.Workplane().box(L, W, H, centered=False).translate((0, yl, z_enc)).edges("|X and >Z").fillet(40)
    asm.add(enc.val(), name="enclosure", color=BODY)

    # side doors: three per side, proud by 3 mm, with handles
    door_x = [(L * 0.22, L * 0.47), (L * 0.49, L * 0.74), (L * 0.76, L * 0.96)]
    for side, (y, out) in (("road", (yl, -1)), ("kerb", (yr, 1))):
        for k, (x0, x1) in enumerate(door_x):
            if side == "kerb" and k == 2:
                continue        # the output panel is here instead
            dz0, dz1 = z_enc + 120, z_top - 120
            yy = y if out > 0 else y - 3
            asm.add(box(x1 - x0, 3, dz1 - dz0, x0, yy, dz0), name=f"door_{side}_{k}", color=BODY)
            asm.add(box(120, 25, 40, x1 - 180, y + (3 if out > 0 else -28), (dz0 + dz1) / 2),
                    name=f"door_handle_{side}_{k}", color=DARK)
        slats, frame = louvres(150, L * 0.20, z_enc + 200, z_top - 200, y, out)
        asm.add(slats, name=f"intake_louvres_{side}", color=DARK)
        asm.add(frame, name=f"intake_frame_{side}", color=DARK)

    # radiator discharge grille on the rear face
    grille = [box(10, W - 300, 25, L, yl + 150, z) for z in range(int(z_enc + 200), int(z_top - 200), 55)]
    asm.add(cq.Compound.makeCompound(grille), name="radiator_discharge_grille", color=DARK)
    # control panel window on the front face
    asm.add(box(10, 700, 500, -10, -350, z_enc + 700), name="control_panel_door", color=PANEL)
    asm.add(box(6, 120, 120, -16, 150, z_enc + 1250), name="emergency_stop_housing", color=BODY)
    asm.add(cyl(35, 30, (-46, 210, z_enc + 1310), (1, 0, 0)), name="emergency_stop", color=RED)

    # output panel on the kerb side, rear door position
    x0, x1 = door_x[2]
    pz0, pz1 = z_enc + 150, z_top - 150
    asm.add(box(x1 - x0, 6, pz1 - pz0, x0, yr, pz0), name="output_panel_door_frame", color=PANEL)
    asm.add(box(220, 60, 300, x0 + 60, yr, pz1 - 380), name="main_breaker", color=DARK)
    asm.add(box(160, 50, 160, x0 + 340, yr, pz1 - 300), name="voltage_selector_480_600V", color=DARK)
    for k, (tag, col) in enumerate(CAMLOK.items()):
        cx = x0 + 90 + k * ((x1 - x0 - 180) / 4)
        asm.add(cyl(32, 70, (cx, yr, pz0 + 260), (0, 1, 0)), name=f"camlok_{tag}", color=col)
    for k in range(3):
        asm.add(box(110, 40, 110, x0 + 90 + k * 160, yr, pz0 + 60), name=f"receptacle_{k}", color=DARK)

    # roof: exhaust stack with a rain cap, single-point lifting eye
    ex, ey = L * 0.80, -W / 4
    asm.add(cyl(75, 330, (ex, ey, z_top)).cut(cyl(68, 330, (ex, ey, z_top))), name="exhaust_stack", color=STEEL)
    cap = cq.Workplane().circle(85).extrude(3).rotate((0, 0, 0), (0, 1, 0), 20).translate((ex, ey, z_top + 335)).val()
    asm.add(cap, name="exhaust_rain_cap", color=STEEL)
    lift = (box(300, 140, 60, L / 2 - 150, -70, z_top)
            .fuse(cq.Workplane("XZ").circle(90).circle(55).extrude(25).translate((L / 2, 12, z_top + 140)).val()))
    asm.add(lift, name="lifting_eye", color=STEEL)

    # rear lights
    for i, y in enumerate((yl + 150, yr - 300)):
        asm.add(box(20, 150, 70, L, y, s.deck - 130), name=f"tail_light_{i}", color=RED)
    return asm


def preview(asm: cq.Assembly, out: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LightSource
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    def split(tri, max_edge=250.0):
        a, b, c = tri
        e = [(a, b, c), (b, c, a), (c, a, b)]
        lens = [sum((p - q) ** 2 for p, q in zip(u, v)) for u, v, _ in e]
        i = lens.index(max(lens))
        if lens[i] <= max_edge ** 2:
            return [tri]
        u, v, w = e[i]
        m = tuple((p + q) / 2 for p, q in zip(u, v))
        return split((u, m, w), max_edge) + split((m, v, w), max_edge)

    fig = plt.figure(figsize=(12, 8), dpi=110)
    ax = fig.add_subplot(projection="3d")
    polys, cols = [], []
    for name in asm.objects:
        obj = asm.objects[name]
        if obj.obj is None:
            continue
        col = obj.color.toTuple()[:3] if obj.color else (0.5, 0.5, 0.5)
        verts, tris = obj.obj.tessellate(3, 0.4)
        for a, b, c in tris:
            for tri in split((verts[a].toTuple(), verts[b].toTuple(), verts[c].toTuple())):
                polys.append(tri)
                cols.append(col)
    ax.add_collection3d(Poly3DCollection(polys, facecolors=cols, edgecolor="none", linewidths=0,
                                         shade=True, lightsource=LightSource(azdeg=315, altdeg=45)))
    ax.set_xlim(-2000, 4800); ax.set_ylim(-3400, 3400); ax.set_zlim(0, 3400)
    ax.set_box_aspect((6800, 6800, 3400))
    ax.view_init(elev=18, azim=-125)
    ax.set_axis_off()
    ax.set_title("Towable 3-phase generator, 300 kVA / 240 kW prime, 480/600 V")
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for f, v in Spec.__dataclass_fields__.items():
        p.add_argument("--" + f.replace("_", "-"), type=type(v.default), default=v.default)
    p.add_argument("--out", type=Path, default=HERE / "Towable_Generator_300kVA.step")
    p.add_argument("--no-preview", action="store_true")
    a = p.parse_args()
    s = Spec(**{f: getattr(a, f) for f in Spec.__dataclass_fields__})
    asm = build(s)
    asm.export(str(a.out))
    print(f"wrote {a.out} ({len(asm.objects) - 1} parts)")
    if not a.no_preview:
        png = a.out.with_name(a.out.stem + "_preview.png")
        preview(asm, png)
        print(f"wrote {png}")


if __name__ == "__main__":
    main()
