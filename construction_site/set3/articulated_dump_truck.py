"""Articulated dump truck (ADT), 6x6, 28-30 t payload class, body lowered.

A generic, brand-neutral machine with the typical proportions of the 30 t ADT class:
overall length ~10.6 m, width ~3.0 m over the body and tyres, ~3.6 m to the cab roof
(~3.7 m to the top of the beacon), 23.5R25 tyres (~1.62 m OD, ~0.6 m section) on all six
wheels at a ~2.35 m track, front axle 2.1 m ahead of the articulation joint, tandem bogie
axles 1.75 m apart with the walking-beam pivot ~3.7 m behind the joint, dump body ~6.2 m
long and ~3.0 m wide (about 17 m3 heaped) with a loading height of ~3.0 m.

Tractor unit: long engine hood with grille, headlights and side louvres, front bumper with
tow jaw, front fenders and mud flaps, centred ROPS/FOPS cab with glazing, door, wiper,
interior, mirrors, roof work lights and beacon, exhaust stack and air pre-cleaner out at
the rear corners of the hood beside the A-pillars, left-hand access ladder and platform
with handrails, fuel tank (left), hydraulic tank and battery box (right).
Hitch: articulation pins, oscillation tube and flange, two steering cylinders, hoses.
Trailer unit: box frame, walking-beam tandem bogie, mudguards on L-brackets with a rear lip
carrying mud flaps behind the tyres, two hoist cylinders, tail lights; dump body with curved
floor and flared sides, side ribs and top rails, a raised headboard and a cab-protector lip
(~350 mm, chamfered corners) over the hitch that stops well short of the cab, open tail with
an upswept floor, lowered onto its rear pivot. Tyres carry a directional lug tread that
wraps over the shoulders.

Millimetres, X forward, Y left, Z up, ground at Z = 0, X = 0 at the articulation joint.
"""

from __future__ import annotations

import math

import numpy as np

from cadkit import (arc_pts, band, bar, box, cone, cut, cyl, pin, pipe, prism, ram, rot, rounded_box,
                    sphere, torus)
from finishes import AMBER, BLACK, CHROME, DARK, GALV, GLASS, LED, RED, RUBBER, STEEL, YELLOW

ASSET = dict(key="articulated_dump_truck", stem="Articulated_Dump_Truck_30t",
             title="Articulated Dump Truck (30 t class)", az=40, el=18, size="1200x900")

# ---- running gear
R = 808.0                     # 23.5R25, ~1,616 mm OD
ZC = R - 0.015 * R            # axle height: tyres sunk 1.5 % for a flat print contact
YI, YO = 875.0, 1475.0        # tyre inner / outer face, |y|
XF = 2100.0                   # front axle
XB1, XB2 = -2850.0, -4600.0   # tandem bogie axles
XBP = (XB1 + XB2) / 2         # walking-beam pivot

# ---- dump body
ZFL = 1800.0                  # floor underside
XT, XFW = -6350.0, -200.0     # tail, headboard front face
BCY, BCZ, BR, FL = 680.0, ZFL + 600.0, 600.0, 12.0     # floor-to-side corner arc, side flare (deg)
TOP = [(XT, 2900.0), (-1000.0, 3080.0), (-450.0, 3330.0), (XFW, 3330.0)]   # side top edge (x, z)

# ---- cab
CX0, CX1, CY = 650.0, 2600.0, 1000.0
ZF, ZB, ZR = 1850.0, 2300.0, 3450.0      # cab floor, belt line, roof
LEAN = 140.0


def xf(z):
    """Cab front (windscreen line) at height z."""
    return CX1 - (z - ZB) / (ZR - ZB) * LEAN


def body_y(z, w=0.0):
    """Half-width of the body side (outer face, or w in from it) at height z."""
    a = math.radians(-FL)
    ye, ze = BCY + (BR - w) * math.cos(a), BCZ + (BR - w) * math.sin(a)
    return ye + math.tan(math.radians(FL)) * (z - ze)


def top_z(x):
    """Height of the body side's top edge at x."""
    xs, zs = zip(*TOP)
    return float(np.interp(x, xs, zs))


def body_section(w, top):
    """Cross-section (y, z): flat floor, round corners, flared sides; w in from the outside."""
    half = arc_pts(BCY, BCZ, BR - w, -90, -FL, 10) + [(body_y(top, w), top)]
    return half + [(-y, z) for y, z in reversed(half)]


def body_shell(w):
    side = [(XT, 2200.0), (-5500.0, ZFL), (XFW, ZFL)] + TOP[::-1]
    outer = prism(body_section(0, 3700), "x", XT, XFW).intersect(prism(side, "y", -1800, 1800))
    (px, pz), (qx, qz) = side[0], side[1]
    L = math.hypot(qx - px, qz - pz)
    ox, oz = qx + w * (pz - qz) / L, qz + w * (qx - px) / L     # a point on the inner ramp
    k = (qz - pz) / (qx - px)

    def ramp_z(x):
        return oz + k * (x - ox)

    xe = XT - 500
    x_corner = ox + (ZFL + w - oz) / k
    inner_side = [(xe, ramp_z(xe)), (x_corner, ZFL + w), (XFW - w, ZFL + w), (XFW - w, 4200), (xe, 4200)]
    inner = prism(body_section(w, 4000), "x", xe, XFW - w).intersect(prism(inner_side, "y", -1800, 1800))
    return cut(outer, inner)


SH, DROP = 70.0, 60.0          # tyre shoulder: width in from each face, and radius lost across it


def tread(xc, s, depth, n=26, width=120.0, yaw=22.0):
    """Directional bar tread: lugs from the crown out to alternate shoulders, swept back.

    Each lug is a profile (e = distance from the tyre's centre plane towards its shoulder,
    r = radius) that runs flat across the crown and then turns down over the shoulder,
    so it wraps the tyre like a moulded earthmover lug instead of overhanging it.
    """
    lugs = []
    ym, half = (YI + YO) / 2, (YO - YI) / 2
    rc = R - depth                                  # crown radius of the carcass
    e0, e1, e2 = -0.12 * (half - SH), half - SH - 5, half - 12

    def cone_r(e):                                  # carcass radius out on the shoulder
        return rc - DROP * (e - (half - SH)) / SH

    prof = [(e0, rc - 25), (e1, rc - 25), (e2, cone_r(e2) - 25),
            (e2, cone_r(e2) + 0.7 * depth), (e1, R), (e0, R)]
    for i in range(n):
        a = 270 + 360 * i / n
        k = 1 if i % 2 else -1                      # which shoulder: +1 outer, -1 inner
        pts = [(s * (ym + k * e), ZC + r) for e, r in prof]
        lug = prism(pts, "x", xc - width / 2, xc + width / 2)
        lug = rot(lug, k * s * yaw, (0, 0, 1), (xc, s * (ym + k * (e0 + e1) / 2), ZC + R))
        lugs.append(rot(lug, 90 - a, (0, 1, 0), (xc, 0, ZC)))
    return lugs


def wheel(m, xc, s, tag):
    """23.5R25 tyre with a bar tread, dished yellow rim, planetary hub and wheel nuts."""
    D = 42.0

    def c(d):                               # on the axle, d mm in from the outer face
        return (xc, s * (YO - d), ZC)
    wd = YO - YI
    tyre = cyl(R - D, c(wd - SH), c(SH)).fuse(cone(R - D - DROP, R - D, c(wd), c(wd - SH)),
                                              cone(R - D, R - D - DROP, c(SH), c(0)))
    tyre = cut(tyre, cyl(440, c(120), c(-5)))
    m.add(f"tyre_{tag}", RUBBER, tyre, tread(xc, s, D))
    m.add(f"rim_{tag}", YELLOW, cyl(440, c(150), c(110)), torus(415, m.r(24), c(100), (0, 1, 0)))
    m.add(f"hub_{tag}", DARK, cone(250, 175, c(125), c(30)), cyl(115, c(35), c(12)))
    nuts = []
    for a in np.linspace(0, 2 * math.pi, 12, endpoint=False):
        x, z = xc + 300 * math.cos(a), ZC + 300 * math.sin(a)
        nuts.append(cyl(m.r(24), (x, s * (YO - 125), z), (x, s * (YO - 85), z)))
    m.add(f"wheel_nuts_{tag}", STEEL, nuts)


def build(m):
    w = m.t(50)
    hr = m.r(20)

    # =============================================================== running gear
    for xc, tag in ((XF, "front"), (XB1, "bogie_front"), (XB2, "bogie_rear")):
        for s, side in ((1, "L"), (-1, "R")):
            wheel(m, xc, s, f"{tag}_{side}")
    m.add("front_axle", DARK, cyl(170, (XF, -950, ZC), (XF, 950, ZC)), sphere(300, (XF, 0, ZC)),
          [cyl(250, (XF, s * 700, ZC), (XF, s * 900, ZC)) for s in (1, -1)])
    m.add("rear_axles", DARK, [cyl(175, (x, -950, ZC), (x, 950, ZC)) for x in (XB1, XB2)],
          [sphere(290, (x, 0, ZC)) for x in (XB1, XB2)],
          [cyl(250, (x, s * 700, ZC), (x, s * 900, ZC)) for x in (XB1, XB2) for s in (1, -1)])
    beams = []
    for s in (1, -1):
        beams.append(prism(band([(XB1, ZC), (XBP, 1000.0), (XB2, ZC)], 170), "y", s * 600, s * 780))
        beams += [cyl(210, (x, s * 590, z), (x, s * 790, z)) for x, z in ((XB1, ZC), (XB2, ZC), (XBP, 1000.0))]
    m.add("bogie_beams", DARK, beams)
    m.add("bogie_pivot", STEEL, cyl(150, (XBP, -830, 1000), (XBP, 830, 1000)))

    # =============================================================== tractor frame and hitch
    rails = [box(150, 4000, s * 330, s * 480, 600, 1150) for s in (1, -1)]
    rails += [box(3880, 4000, -480, 480, 600, 1150), box(1500, 1600, -480, 480, 650, 1100)]
    m.add("front_frame", DARK, rails, box(100, 480, -430, 430, 650, 1560))
    m.add("cab_base", DARK, box(700, 2550, -820, 820, 1100, 1860))
    m.add("engine_belly", DARK, box(2500, 4000, -720, 720, 760, 1180))

    m.add("hitch_yoke", DARK, box(-350, 300, -360, 360, 560, 680), box(-350, 300, -360, 360, 1530, 1650),
          box(-380, -280, -360, 360, 560, 1650))
    m.add("hitch_pins", STEEL, cyl(110, (180, 0, 500), (180, 0, 565)), cyl(110, (180, 0, 1645), (180, 0, 1705)))
    flange_bolts = [cyl(m.r(22), (-300, 375 * math.cos(a), 1100 + 375 * math.sin(a)),
                        (-265, 375 * math.cos(a), 1100 + 375 * math.sin(a)))
                    for a in np.linspace(0, 2 * math.pi, 12, endpoint=False)]
    m.add("oscillation_joint", DARK, cyl(330, (-880, 0, 1100), (-300, 0, 1100)),
          cyl(420, (-340, 0, 1100), (-290, 0, 1100)))
    m.add("oscillation_bolts", STEEL, flange_bolts)
    for s in (1, -1):
        a, b = (720.0, s * 570.0, 1050.0), (-600.0, s * 570.0, 1050.0)
        (barrel, rod), eyes = ram(a, b, 75, 45, 0.55)
        m.add("steering_cylinder", BLACK, barrel)
        m.add("steering_rod", CHROME, rod, eyes)
        m.add("steering_mounts", DARK, box(640, 800, s * 470, s * 650, 960, 1140),
              box(-680, -520, s * 250, s * 650, 960, 1140))
    m.add("hitch_hoses", BLACK, [pipe([(350, y, 1500), (100, y, 1760), (-250, y, 1720), (-450, y, 1450)], hr * 1.3)
                                 for y in (180.0, 260.0)])

    # =============================================================== trailer frame
    rf = [box(-5450, -800, s * 380, s * 560, 950, 1500) for s in (1, -1)]
    rf += [box(-920, -700, -560, 560, 950, 1450)]
    rf += [box(x - 60, x + 60, -560, 560, 1050, 1450) for x in (-2000.0, XBP)]
    m.add("rear_frame", DARK, rf, box(-5500, -5380, -720, 720, 1050, 1400))
    m.add("tow_eye", STEEL, box(-5560, -5490, -110, 110, 1110, 1190), torus(75, m.r(26), (-5620, 0, 1150)))
    m.add("tail_lights", RED, [box(-5515, -5490, s * 540, s * 700, 1260, 1370) for s in (1, -1)])
    m.add("indicators_rear", AMBER, [box(-5515, -5490, s * 540, s * 700, 1110, 1220) for s in (1, -1)])

    # mudguards over the tandem, with a short rear lip that carries the mud flaps behind the tyres
    ze = ZC + 900 * math.sin(math.radians(145))
    path = arc_pts(XB1, ZC, 900, 35, 90, 8) + arc_pts(XB2, ZC, 900, 90, 145, 8) + [(-5470.0, ze)]
    guard = band(path, m.t(22))
    xr = -5475.0                               # flap clear of the rear tyre (back to x = -5410)
    for s in (1, -1):
        m.add("bogie_mudguard", BLACK, prism(guard, "y", s * 860, s * 1500))
        # L-brackets off the frame rail (below the tipping body's subframe) up to the guard
        m.add("mudguard_brackets", DARK, box(-3775, -3675, s * 540, s * 1000, 1400, 1470),
              box(-3775, -3675, s * 940, s * 1000, 1400, 1700),
              box(-3775, -3675, s * 940, s * 1480, 1640, 1700),
              box(-5250, -5150, s * 540, s * 880, 1380, 1480))
        m.add("rear_mud_flap", RUBBER, box(xr, xr + m.t(40), s * 870, s * 1480, 450, ze + 28))

    # hoist cylinders, retracted
    for s in (1, -1):
        a, b = (-850.0, s * 855.0, 1020.0), (-1550.0, s * 855.0, 1770.0)
        (barrel, rod), eyes = ram(a, b, 105, 65, 0.6)
        m.add("hoist_cylinder", BLACK, barrel)
        m.add("hoist_rod", CHROME, rod, eyes)
        m.add("hoist_mount", DARK, box(-950, -750, s * 540, s * 940, 930, 1100))
        m.add("hoist_body_lug", YELLOW, box(-1650, -1450, s * 790, s * 930, 1700, 1850))
        m.add("hoist_pins", STEEL, pin(a, 50, 115), pin(b, 50, 105))

    # =============================================================== dump body
    m.add("dump_body", YELLOW, body_shell(w))
    m.add("body_subframe", YELLOW, [box(-5100, -600, s * 380, s * 560, 1490, 1810) for s in (1, -1)])
    m.add("body_pivot_lugs", YELLOW, [box(-5330, -5170, s * 570, s * 690, 1560, 1810) for s in (1, -1)])
    m.add("frame_pivot_lugs", DARK, [box(-5330, -5170, s * 380, s * 560, 1450, 1720) for s in (1, -1)])
    m.add("body_pivot_pin", STEEL, cyl(70, (-5250, -730, 1640), (-5250, 730, 1640)))

    # cab-protector lip: ~350 mm out over the hitch, front corners chamfered in plan, well short
    # of the cab so the tractor/trailer break reads and the units can articulate
    canopy = prism([(XFW - 60, 3270), (130, 3350), (150, 3440), (XFW - 60, 3370)], "y", -1350, 1350)
    chamfer = [prism([(150, s * 800), (-150, s * 1350), (-150, s * 1500), (400, s * 1500), (400, s * 800)],
                     "z", 2600, 3600) for s in (1, -1)]
    gussets = [prism([(XFW - 30, 2700), (XFW - 30, 3300), (100, 3370)], "y", s * 1060, s * 1110) for s in (1, -1)]
    ribs = []
    for y in (-700.0, 0.0, 700.0):
        ribs.append(box(XFW - 30, XFW + 70, y - 30, y + 30, 1850, 3300))
        ribs.append(prism([(XFW - 30, 2950), (XFW - 30, 3300), (60, 3345)], "y", y - 30, y + 30))
    ribs.append(box(XFW - 30, XFW + 60, -1300, 1300, 2560, 2640))
    m.add("cab_protector", YELLOW, cut(canopy, *chamfer), [cut(g, *chamfer) for g in gussets], ribs)

    rails_b, stiff, vribs = [], [], []
    for s in (1, -1):
        for (x0, z0), (x1, z1) in zip(TOP, TOP[1:]):
            rails_b.append(bar((x0, s * (body_y(z0 - 50) - 25), z0 - 50), (x1, s * (body_y(z1 - 50) - 25), z1 - 50),
                               110, 120))
        yb = body_y(2330)
        stiff.append(box(XT + 40, XFW - 20, s * (yb - 30), s * (yb + 28), 2290, 2370))
        for x in (-1700.0, -3300.0, -4900.0):
            z1 = top_z(x) - 100
            sec = [(body_y(2370) - 20, 2350), (body_y(2370) + 30, 2350), (body_y(z1) + 30, z1), (body_y(z1) - 20, z1)]
            vribs.append(prism([(s * y, z) for y, z in sec], "x", x - 45, x + 45))
    m.add("body_top_rails", YELLOW, rails_b)
    m.add("body_side_stiffeners", YELLOW, stiff, vribs)
    for s in (1, -1):
        for x0, x1, fin in ((XT + 80, XT + 230, RED), (XFW - 520, XFW - 370, AMBER)):
            yb = body_y(2470)
            m.add("body_reflector", fin, box(x0, x1, s * (yb - 20), s * (yb + m.t(12)), 2420, 2490))
    m.add("body_tail_lip", YELLOW, box(XT - 10, XT + 140, -1200, 1200, 2160, 2300))

    # =============================================================== hood
    hood_side = [(2520, 1150), (2520, 2290), (3850, 2030), (4020, 1960), (4100, 1850), (4140, 1150)]
    hood_sec = [(-850, 1100), (850, 1100), (850, 1850), (640, 2400), (-640, 2400), (-850, 1850)]
    hood = prism(hood_side, "y", -900, 900).intersect(prism(hood_sec, "x", 2500, 4200))
    m.add("hood", YELLOW, hood)

    def hood_top(x):
        return float(np.interp(x, [2520, 3850], [2290, 2030]))

    m.add("hood_intake", BLACK, bar((3020, 0, hood_top(3020) + 2), (3560, 0, hood_top(3560) + 2), 760, m.t(36)))
    m.add("hood_intake_slats", DARK, [bar((x, -360, hood_top(x) + 16), (x, 360, hood_top(x) + 16), m.t(26), m.t(28))
                                      for x in np.arange(3062, 3540, 68)])
    x0 = 3600.0
    m.add("hood_handles", BLACK, [pipe([(x0, s * 420, hood_top(x0) - 20), (x0, s * 420, hood_top(x0) + 60),
                                        (x0 + 260, s * 420, hood_top(x0 + 260) + 60),
                                        (x0 + 260, s * 420, hood_top(x0 + 260) - 20)], hr) for s in (1, -1)])

    def xface(z):                           # hood front face
        return 4140 - 40 * (z - 1150) / 700

    m.add("grille", BLACK, prism([(xface(1280) - 40, 1280), (xface(1280) + 12, 1280),
                                  (xface(1800) + 12, 1800), (xface(1800) - 40, 1800)], "y", -620, 620))
    m.add("grille_bars", YELLOW, [box(xface(z) + 5, xface(z) + 5 + m.t(28), -600, 600, z - m.t(28) / 2, z + m.t(28) / 2)
                                  for z in np.arange(1330, 1780, 80)])
    lv = []
    for s in (1, -1):
        lv += [box(3200, 3850, s * 845, s * (850 + m.t(18)), z, z + m.t(28)) for z in range(1400, 1760, 70)]
    m.add("hood_louvres", BLACK, lv)
    for s in (1, -1):
        m.add("headlight_housing", BLACK, box(4000, 4140, s * 640, s * 840, 1640, 1830),
              box(4040, 4125, s * 650, s * 830, 1545, 1625))
        m.add("headlight", LED, box(4135, 4152, s * 660, s * 820, 1660, 1810))
        m.add("indicator_front", AMBER, box(4120, 4138, s * 665, s * 815, 1560, 1610))

    # bumper with a tow jaw, step plates and fog lights
    bumper = cut(box(3960, 4260, -1050, 1050, 680, 1110), box(4130, 4270, -110, 110, 850, 970))
    m.add("front_bumper", BLACK, bumper)
    m.add("tow_pin", STEEL, cyl(m.r(40), (4200, 0, 760), (4200, 0, 1140)), cyl(70, (4200, 0, 1105), (4200, 0, 1150)))
    m.add("bumper_steps", GALV, [box(4040, 4230, s * 250, s * 800, 1105, 1130) for s in (1, -1)])
    m.add("fog_lights", LED, [box(4255, 4272, s * 800, s * 950, 960, 1050) for s in (1, -1)])

    # front fenders and flaps
    for s, a1 in ((1, 160), (-1, 170)):
        arch = arc_pts(XF, ZC, 920, 6, a1, 24) + arc_pts(XF, ZC, 870, a1, 6, 24)
        m.add("front_fender", YELLOW, prism(arch, "y", s * 840, s * 1500))
        xe = XF + 900 * math.cos(math.radians(a1))
        ze = ZC + 900 * math.sin(math.radians(a1))
        m.add("front_mud_flap", RUBBER, box(xe - m.t(35) / 2, xe + m.t(35) / 2, s * 870, s * 1480, 520, ze + 40))

    # exhaust stack (right) and air pre-cleaner (left), out at the rear corners of the hood
    # chamfer beside the A-pillars, clear of the windscreen's centre
    ex, ey = 2700.0, -800.0
    m.add("exhaust", BLACK, cyl(m.r(65), (ex, ey, 1950), (ex, ey, 3380)),
          cyl(m.r(78), (ex, ey, 3330), (ex, ey, 3420)))
    m.add("exhaust_guard", GALV, cyl(95, (ex, ey, 2450), (ex, ey, 3050)),
          [box(ex - 100, ex + 100, ey - m.t(16) / 2, ey + m.t(16) / 2, z, z + 20) for z in (2500, 2980)])
    px, py = 2700.0, 800.0
    m.add("precleaner_pipe", BLACK, cyl(m.r(70), (px, py, 1950), (px, py, 2700)))
    m.add("precleaner", DARK, cyl(150, (px, py, 2680), (px, py, 2960)), cone(155, 70, (px, py, 2945), (px, py, 3030)))

    # =============================================================== cab
    m.add("cab_lower", YELLOW, box(CX0, CX1, -CY, CY, ZF, ZB))
    pp = 80.0
    posts = []
    for s in (1, -1):
        posts.append(box(CX0, CX0 + pp, s * CY, s * (CY - pp), ZB - 20, ZR))
        posts.append(bar((xf(ZB) - pp / 2, s * (CY - pp / 2), ZB - 20), (xf(ZR) - pp / 2, s * (CY - pp / 2), ZR),
                         pp, pp, up=(1, 0, 0)))
        posts.append(box(1700, 1770, s * CY, s * (CY - 60), ZB - 20, ZR))
        posts.append(box(CX0, CX1, s * (CY + 6), s * (CY - 40), ZB - 25, ZB + 15))   # belt-line trim
    m.add("cab_frame", BLACK, posts)
    g = m.t(12)
    side = [(CX0 + 40, ZB), (xf(ZB) - 40, ZB), (xf(ZR) - 40, ZR), (CX0 + 40, ZR)]
    glass = [prism(side, "y", s * (CY - 10), s * (CY - 10 - g)) for s in (1, -1)]
    glass.append(bar((xf(ZB) - 30, 0, ZB), (xf(ZR) - 30, 0, ZR), 2 * CY - 60, g, up=(1, 0, 0)))
    glass.append(box(CX0 + 15, CX0 + 15 + g, -CY + 40, CY - 40, ZB, ZR))
    m.add("cab_glass", GLASS, glass)
    m.add("roof_rim", BLACK, box(CX0 - 55, xf(ZR) + 115, -CY - 55, CY + 55, ZR - 10, ZR + 40))
    m.add("cab_roof", YELLOW, rounded_box(CX0 - 50, xf(ZR) + 110, -CY - 50, CY + 50, ZR + 20, ZR + 150, 30))
    m.add("roof_work_lights", LED, [box(xf(ZR) + 100, xf(ZR) + 122, s * 550, s * 800, ZR + 60, ZR + 120) for s in (1, -1)],
          [box(CX0 - 62, CX0 - 40, s * 450, s * 700, ZR + 60, ZR + 120) for s in (1, -1)])
    m.add("beacon_base", BLACK, cyl(105, (900, -650, ZR + 140), (900, -650, ZR + 180)))
    m.add("beacon", AMBER, cyl(80, (900, -650, ZR + 175), (900, -650, ZR + 290)))
    wy = [(xf(ZB + 70) - 18, 380, ZB + 70), (xf(ZB + 760) - 18, 160, ZB + 760)]
    m.add("wiper", BLACK, bar(wy[0], wy[1], m.t(22), m.t(20), up=(1, 0, 0)),
          cyl(m.r(30), (xf(ZB + 70) - 40, 380, ZB + 70), (xf(ZB + 70) - 5, 380, ZB + 70)))
    # interior
    m.add("dash", DARK, box(2250, 2500, -950, 950, ZB - 50, 2560))
    m.add("seat", BLACK, box(1250, 1700, -280, 280, ZB - 50, 2550), box(1120, 1270, -280, 280, 2500, 3150),
          [box(1200, 1650, s * 260, s * 340, 2650, 2710) for s in (1, -1)])
    m.add("steering", BLACK, torus(200, m.r(22), (2080, 0, 2850), (1, 0, 0.8)),
          cyl(m.r(40), (2080, 0, 2850), (2340, 0, 2520)))
    if m.print_mode:                        # no sealed void behind the glass in the print
        m.add("cab_core", DARK, prism(side, "y", -(CY - 10), CY - 10))
    # door (left), handle, hinges, grab handle
    seams = [box(x, x + 20, CY - 5, CY + m.t(6), ZF + 30, ZB - 25) for x in (760.0, 1690.0)]
    seams.append(box(760, 1710, CY - 5, CY + m.t(6), ZF + 30, ZF + 50))
    m.add("door_seams", BLACK, seams)
    m.add("door_handle", CHROME, box(850, 960, CY - 5, CY + 28, 2180, 2230))
    m.add("door_hinges", BLACK, [cyl(m.r(20), (1715, CY + 15, z), (1715, CY + 15, z + 110)) for z in (2000, 2900)])
    m.add("grab_handle", BLACK, pipe([(700, CY - 10, 2000), (700, CY + 60, 2000), (700, CY + 60, 2900),
                                      (700, CY - 10, 2900)], hr))
    # mirrors on arms from the A-pillars
    zm = 2950.0
    for s in (1, -1):
        x0 = xf(zm)
        m.add("mirror_arm", BLACK, pipe([(x0 - 40, s * (CY - 40), zm), (x0 + 80, s * (CY + 150), zm + 50),
                                         (x0 + 120, s * 1330, zm + 50)], hr))
        m.add("mirror_head", BLACK, box(x0 + 90, x0 + 170, s * 1260, s * 1470, 2730, 3080))
        m.add("mirror_glass", CHROME, box(x0 + 75, x0 + 95, s * 1275, s * 1455, 2745, 3065))

    # =============================================================== access, tanks
    m.add("fuel_tank", YELLOW, rounded_box(120, 720, 660, 1300, 800, 1620, 40))
    m.add("hydraulic_tank", YELLOW, rounded_box(120, 720, -1300, -660, 800, 1620, 40))
    m.add("tank_straps", BLACK, [box(x, x + 50, s * 650, s * 1310, 790, 1630) for x in (230.0, 560.0) for s in (1, -1)])
    m.add("tank_brackets", DARK, [box(x, x + 80, s * 470, s * 680, 820, 900) for x in (220.0, 560.0) for s in (1, -1)])
    m.add("fuel_filler", BLACK, cyl(70, (300, 1150, 1600), (300, 1150, 1690)), cyl(85, (300, 1150, 1690), (300, 1150, 1730)))
    m.add("sight_gauge", GLASS, box(380, 460, -1310, -1290, 1150, 1450))
    m.add("battery_box", BLACK, box(820, 1150, -1300, -800, 1120, 1500))

    m.add("platform", GALV, box(650, 1780, 980, 1480, 1800, 1870))
    m.add("platform_supports", DARK, box(700, 760, 1000, 1280, 1580, 1810),
          bar((1700, 800, 1350), (1700, 1350, 1805), 60, 60, up=(1, 0, 0)))
    m.add("ladder_stringers", BLACK, [box(x - m.t(30) / 2, x + m.t(30) / 2, 1300, 1460, 420, 1820)
                                      for x in (775.0, 1105.0)])
    m.add("ladder_treads", GALV, [box(775, 1105, 1300, 1460, z, z + 40) for z in (480, 820, 1160, 1480)])
    yr = 1475.0
    hrails = []
    for x in (775.0, 1105.0):
        hrails += pipe([(x, yr, 1000), (x, yr, 2850)], hr)
    hrails += pipe([(1105, yr, 2850), (1760, yr, 2850), (1760, yr, 1850)], hr)
    for z in (2850.0, 2350.0):
        hrails += pipe([(775, yr, z), (690, yr, z), (690, CY - 20, z)], hr)
    hrails += pipe([(1105, yr, 2350), (1760, yr, 2350)], hr)
    m.add("handrails", BLACK, hrails)
