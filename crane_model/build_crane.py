"""Parametric STEP model of the Mammoet 1824 carry deck crane (Broderson IC-80 class).

Dimensions are estimated from a site photo and are approximate. Units: mm.
Axes: X forward (cab end), Y left, Z up. Run: python3 build_crane.py
"""
import math
import cadquery as cq

# ---- pose parameters ----
SLEW_DEG = 0.0       # turret slew, about Z
BOOM_DEG = 40.0      # boom luff angle above horizontal
TELE = 0.25          # telescope extension, 0..1
OUTRIGGERS = 1.0     # 0 stowed .. 1 set on pads
HOOK_LINE = 2.5      # m of line below tip sheave

MAX_EXT = 8.0        # m, total telescope stroke
S = 1000.0           # m -> mm
DECK = 1.35

YELLOW = cq.Color(0.91, 0.71, 0.09)
YELLOW_DK = cq.Color(0.79, 0.59, 0.06)
BLACK = cq.Color(0.10, 0.11, 0.12)
RED = cq.Color(0.78, 0.06, 0.18)
STEEL = cq.Color(0.73, 0.75, 0.77)
CHROME = cq.Color(0.90, 0.91, 0.92)
GLASS = cq.Color(0.20, 0.30, 0.36, 0.5)
TIMBER = cq.Color(0.30, 0.21, 0.15)
BLUE = cq.Color(0.18, 0.50, 0.84)
WEIGHT = cq.Color(0.42, 0.23, 0.15)


def box(lx, ly, lz, cx, cy, cz):
    """Box sized (lx, ly, lz) m centred on (cx, cy, cz) m."""
    return cq.Solid.makeBox(lx * S, ly * S, lz * S,
                            cq.Vector((cx - lx / 2) * S, (cy - ly / 2) * S, (cz - lz / 2) * S))


def cyl(r, a, b):
    """Cylinder of radius r (m) from point a to point b (m)."""
    va, vb = cq.Vector(*a) * S, cq.Vector(*b) * S
    d = vb - va
    return cq.Solid.makeCylinder(r * S, d.Length, va, d.normalized())


def merge(*solids):
    return cq.Compound.makeCompound(list(solids))


def text_plate(txt, size, depth, pnt, normal, xdir):
    try:
        wp = cq.Workplane(cq.Plane(origin=cq.Vector(*pnt) * S, xDir=xdir, normal=normal))
        return wp.text(txt, size * S, depth * S, halign="center", valign="center", kind="bold").val()
    except Exception:  # no usable system font
        return None


# =================== carrier ===================
carrier = cq.Assembly(name="carrier")
carrier.add(box(5.6, 2.3, 0.85, 0, 0, 0.925), name="chassis", color=YELLOW)
carrier.add(box(5.62, 2.32, 0.10, 0, 0, 1.12), name="body_stripe", color=BLACK)
carrier.add(box(5.62, 2.32, 0.04, 0, 0, 1.04), name="pin_stripe", color=RED)
carrier.add(box(5.4, 2.2, 0.08, 0, 0, DECK + 0.04), name="deck_plate", color=YELLOW_DK)
grilles = [box(0.22, 0.02, 0.18, -1.6 + i * 0.32, s * 1.16, 1.25) for s in (-1, 1) for i in range(6)]
carrier.add(merge(*grilles), name="engine_grilles", color=BLACK)
for s, side in ((1, "L"), (-1, "R")):
    t = text_plate("1824", 0.22, 0.004, (1.7 * s, s * 1.151, 0.78),
                   cq.Vector(0, s, 0), cq.Vector(-s, 0, 0))
    if t:
        carrier.add(t, name=f"fleet_no_{side}", color=cq.Color(1, 1, 1))

# wheels
for x, xn in ((1.85, "F"), (-1.85, "R")):
    for y, yn in ((1.05, "L"), (-1.05, "R")):
        c = (x, y, 0.62)
        tyre = cyl(0.62, (x, y - 0.275, 0.62), (x, y + 0.275, 0.62))
        lugs = []
        for i in range(14):
            a = 2 * math.pi * i / 14
            lug = box(0.10, 0.56, 0.05, 0, 0, 0).rotate(cq.Vector(), cq.Vector(0, 1, 0), -math.degrees(a) + 90)
            lugs.append(lug.translate(cq.Vector(x + 0.63 * math.cos(a), y, 0.62 + 0.63 * math.sin(a)) * S))
        wheel = cq.Assembly(name=f"wheel_{xn}{yn}")
        wheel.add(merge(tyre, *lugs), name="tyre", color=BLACK)
        wheel.add(cyl(0.34, (x, y - 0.285, 0.62), (x, y + 0.285, 0.62)), name="rim", color=YELLOW)
        wheel.add(cyl(0.12, (x, y - 0.30, 0.62), (x, y + 0.30, 0.62)), name="hub", color=STEEL)
        carrier.add(wheel)

# cab (fixed on carrier, front left)
cx, cy, cz = 1.75, -0.62, DECK
W, D, H = 1.3, 0.95, 1.55
cab = cq.Assembly(name="cab")
posts = [box(0.07, 0.07, H, cx + sx * (W / 2 - 0.035), cy + sy * (D / 2 - 0.035), cz + H / 2)
         for sx in (-1, 1) for sy in (-1, 1)]
cab.add(merge(box(W, D, 0.12, cx, cy, cz + H), *posts), name="frame", color=YELLOW)
cab.add(merge(box(W - 0.1, 0.02, H - 0.1, cx, cy + D / 2 - 0.02, cz + H / 2),
              box(W - 0.1, 0.02, H - 0.1, cx, cy - D / 2 + 0.02, cz + H / 2),
              box(0.02, D - 0.1, H - 0.1, cx + W / 2 - 0.02, cy, cz + H / 2),
              box(0.02, D - 0.1, H - 0.1, cx - W / 2 + 0.02, cy, cz + H / 2)), name="glazing", color=GLASS)
cab.add(merge(box(0.5, 0.5, 0.5, cx - 0.2, cy, cz + 0.25),
              box(0.04, 0.2, 0.3, cx + W / 2 + 0.15, cy - D / 2 - 0.1, cz + H * 0.7),
              box(0.25, 0.03, 0.03, cx + W / 2 + 0.05, cy - D / 2 - 0.05, cz + H * 0.7)),
        name="seat_and_mirror", color=BLACK)
cab.add(cyl(0.09, (cx - W / 2 + 0.2, cy + D / 2 - 0.15, cz + H + 0.06),
            (cx - W / 2 + 0.2, cy + D / 2 - 0.15, cz + H + 0.26)), name="beacon", color=cq.Color(1, 0.55, 0))
carrier.add(cab)

# outriggers
ext = min(OUTRIGGERS * 2, 1) * 1.55
drop = max(min(OUTRIGGERS * 2 - 1, 1), 0)
for x, xn in ((2.45, "F"), (-2.45, "R")):
    carrier.add(box(0.42, 2.34, 0.42, x, 0, 0.85), name=f"outrigger_box_{xn}", color=BLACK)
    for s, sn in ((1, "L"), (-1, "R")):
        yend = s * (1.17 + ext + 0.18)
        pad_z = 0.85 + (-0.2 + (-0.79 + 0.2) * drop)
        o = cq.Assembly(name=f"outrigger_{xn}{sn}")
        o.add(merge(box(0.34, 1.9, 0.34, x, s * (0.2 + ext + 0.18), 0.85),
                    box(0.36, 0.36, 0.95, x, yend, 0.85 + 0.18)), name="beam_and_leg", color=YELLOW)
        o.add(cyl(0.12, (x, yend, 0.55), (x, yend, pad_z)), name="jack_ram", color=STEEL)
        o.add(box(0.75, 0.75, 0.10, x, yend, pad_z - 0.05), name="pad", color=TIMBER)
        carrier.add(o)

# =================== turret (slews about Z) ===================
TX, TZ = -0.7, DECK + 0.08
PIV = (-0.55, -0.55, 1.75)            # boom foot pin, turret-local
CYL_BASE = (1.05, -0.55, 0.5)
turret = cq.Assembly(name="turret")
turret.add(cyl(0.85, (0, 0, 0), (0, 0, 0.18)), name="slew_ring", color=BLACK)
turret.add(merge(box(2.6, 1.6, 0.35, -0.35, 0.15, 0.35),
                 box(0.08, 0.08, 0.08, 0, 0, 0)), name="frame", color=YELLOW)
turret.add(box(1.75, 1.45, 1.1, -1.55, 0.15, 1.75), name="counterweight", color=YELLOW)
for s, sn in ((1, "L"), (-1, "R")):
    yface = 0.15 + s * 0.726
    turret.add(box(1.5, 0.006, 0.27, -1.55, yface, 1.8), name=f"livery_{sn}", color=RED)
    t = text_plate("MAMMOET", 0.17, 0.004, (-1.55, yface + s * 0.003, 1.8),
                   cq.Vector(0, s, 0), cq.Vector(-s, 0, 0))
    if t:
        turret.add(t, name=f"livery_text_{sn}", color=cq.Color(1, 1, 1))
turret.add(box(1.6, 0.04, 0.9, -1.55, 0.85, 0.95), name="engine_screen", color=BLACK)
turret.add(merge(*[box(0.9, 0.08, 1.4, PIV[0], PIV[1] + dy, 1.05) for dy in (-0.33, 0.33)]),
           name="boom_foot_plates", color=YELLOW)
turret.add(cyl(0.09, (PIV[0], PIV[1] - 0.4, PIV[2]), (PIV[0], PIV[1] + 0.4, PIV[2])), name="foot_pin", color=STEEL)
turret.add(cyl(0.28, (0.55, 0.2, 0.85), (0.55, 0.7, 0.85)), name="hyd_tank", color=BLACK)
turret.add(box(0.4, 0.5, 0.4, *CYL_BASE), name="cylinder_foot", color=YELLOW)

# lift cylinder geometry follows the boom angle
a = math.radians(BOOM_DEG)
ON_BOOM = (2.4, -0.35)
anchor = (PIV[0] + ON_BOOM[0] * math.cos(a) - ON_BOOM[1] * math.sin(a), PIV[1],
          PIV[2] + ON_BOOM[0] * math.sin(a) + ON_BOOM[1] * math.cos(a))
d = [anchor[i] - CYL_BASE[i] for i in range(3)]
L = math.sqrt(sum(v * v for v in d))
turret.add(cyl(0.17, CYL_BASE, [CYL_BASE[i] + d[i] * 1.75 / L for i in range(3)]), name="lift_cyl_barrel", color=YELLOW_DK)
turret.add(cyl(0.085, CYL_BASE, anchor), name="lift_cyl_rod", color=CHROME)

# =================== boom (luffs about foot pin) ===================
e = TELE * MAX_EXT
boom = cq.Assembly(name="boom")
boom.add(box(5.4, 0.56, 0.62, 2.4, 0, 0), name="section_1_base", color=YELLOW)
boom.add(box(1.6, 0.006, 0.26, 1.2, -0.281, 0.05), name="livery", color=RED)
boom.add(box(5.0, 0.46, 0.50, 2.9 + e / 2, 0, 0), name="section_2", color=YELLOW)
boom.add(box(4.8, 0.36, 0.40, 3.2 + e, 0, 0), name="section_3_fly", color=YELLOW)
hx = 5.75 + e
boom.add(merge(*[box(0.6, 0.05, 0.5, hx, dy, 0.05) for dy in (-0.2, 0.2)]), name="boom_head", color=YELLOW)
boom.add(cyl(0.2, (hx + 0.18, -0.15, 0.05), (hx + 0.18, 0.15, 0.05)), name="tip_sheave", color=STEEL)
turret.add(boom, loc=cq.Location(cq.Vector(*PIV) * S, cq.Vector(0, 1, 0), -BOOM_DEG))

# =================== hook (hangs plumb, world frame) ===================
tl = (hx + 0.18, -0.15)  # tip point in boom x/z
tip_t = (PIV[0] + tl[0] * math.cos(a) - tl[1] * math.sin(a), PIV[1], PIV[2] + tl[0] * math.sin(a) + tl[1] * math.cos(a))
sl = math.radians(SLEW_DEG)
tip = (TX + tip_t[0] * math.cos(sl) - tip_t[1] * math.sin(sl),
       tip_t[0] * math.sin(sl) + tip_t[1] * math.cos(sl), TZ + tip_t[2])
line = min(HOOK_LINE, tip[2] - 0.95)
hz = tip[2] - line
hook = cq.Assembly(name="hook_block")
hook.add(cyl(0.018, tip, (tip[0], tip[1], hz)), name="wire_rope", color=BLACK)
hook.add(cyl(0.2, (tip[0], tip[1], hz), (tip[0], tip[1], hz - 0.42)), name="overhaul_ball", color=WEIGHT)
hook.add(cyl(0.05, (tip[0], tip[1], hz - 0.42), (tip[0], tip[1], hz - 0.6)), name="swivel", color=STEEL)
torus = cq.Solid.makeTorus(0.16 * S, 0.045 * S, cq.Vector(tip[0], tip[1], hz - 0.78) * S, cq.Vector(0, 1, 0))
gap = box(0.2, 0.2, 0.2, tip[0] + 0.12, tip[1], hz - 0.68)
hook.add(torus.cut(gap), name="crane_hook", color=BLUE)

# =================== top level ===================
crane = cq.Assembly(name="mammoet_1824_carry_deck_crane")
crane.add(carrier)
crane.add(turret, loc=cq.Location(cq.Vector(TX, 0, TZ) * S, cq.Vector(0, 0, 1), SLEW_DEG))
crane.add(hook)

if __name__ == "__main__":
    import os
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mammoet_1824_crane.step")
    crane.save(out, exportType="STEP")
    bb = cq.Compound.makeCompound([s for s in crane.toCompound()]).BoundingBox()
    print(f"wrote {out}")
    print(f"envelope: {bb.xlen:.0f} x {bb.ylen:.0f} x {bb.zlen:.0f} mm, tip {tip[2]:.2f} m high,"
          f" radius {math.hypot(tip[0] - TX, tip[1]):.2f} m")
