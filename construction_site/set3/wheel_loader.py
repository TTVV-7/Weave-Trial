"""Medium wheel loader, 3 yd3 (2.3-2.5 m3) general-purpose bucket, about 16 t operating weight.

Articulated frame with a visible centre hinge (upper and lower pins) and a steering cylinder
each side; front frame with a Z-bar loader linkage: two lift arms, two lift cylinders, a
single tilt cylinder working a bell crank on a cross tube and a tilt link to the bucket.
General-purpose bucket with a base edge and bolt-on cutting edge, resting flat on the
ground; machine straight. Rear frame with the engine hood (side and rear grilles, exhaust
stack, air pre-cleaner), side pods, a rounded rear counterweight with tail lights and a tow
pin, fenders over all four wheels (the front ones on struts from the front frame), rubber mud
flaps behind the rear wheels, ROPS cab with large glazing, access ladder with a landing
and handrails, mirrors, roof work lights and a beacon.

Dimensions are typical figures for the class, not any one machine:
  wheelbase 3.30 m with the articulation hinge midway
  tyres 23.5R25 with a deep loader (L3-type) tread: OD ~1.61 m, ~0.62 m wide,
      sunk 12 mm (1.5 % of the radius) for a flat print contact patch
  track ~2.12 m, width over tyres ~2.74 m, bucket 2.90 m wide
  length with the bucket on the ground ~8.2 m, height to the cab roof ~3.44 m
  lift-arm pivot ~2.08 m up, bucket hinge pin ~0.47 m up with the bucket down
Generic and brand-neutral: no names, logos or maker-specific styling.
"""

import math

import cadquery as cq
import numpy as np

from cadkit import (Finish, arc_pts, band, bar, box, cone, cut, cyl, mirror_y, mv, pipe, prism, rgb, rot,
                    rounded_box, sphere, torus)
from finishes import AMBER, BLACK, CHROME, DARK, GLASS, LED, RED, RUBBER, STEEL, YELLOW

ASSET = dict(key="wheel_loader", stem="Wheel_Loader_3yd", title="Wheel Loader (3 yd³ class)",
             az=40, el=20, size="1200x900")

WORN = Finish(rgb("#7c7d7b"), metal=0.55, rough=0.5)      # bucket floor polished by the material

# ---------------------------------------------------------------- main dimensions (mm)
XF, XR = 1650.0, -1650.0          # front / rear axle, hinge at X = 0
R, SINK = 807.0, 12.0             # 23.5R25 tyre radius, sunk for the print contact patch
ZA = R - SINK                     # axle height
TYC = 1060.0                      # tyre centre plane, |Y|

# Z-bar linkage, points in the (X, Z) side plane, bucket on the ground
A = np.array([1000.0, 2080.0])    # lift-arm pivot on the front-frame tower
M = np.array([2350.0, 1100.0])    # bend in the lift arm
B = np.array([3060.0, 470.0])     # bucket hinge pin
CT = A + (M - A) * (950.0 / 1350.0)   # cross tube between the arms
C = np.array([2200.0, 1600.0])    # bell-crank pivot
D = np.array([2050.0, 2300.0])    # bell crank, tilt-cylinder end
E = np.array([2330.0, 1150.0])    # bell crank, tilt-link end
F = np.array([3130.0, 1150.0])    # tilt link to the bucket
T0 = np.array([880.0, 2330.0])    # tilt-cylinder base pin on the tower
L0 = np.array([760.0, 1080.0])    # lift-cylinder base pin on the front frame
L1 = np.array([1900.0, 1130.0])   # lift-cylinder rod pin under the arm
ARM_Y = (520.0, 640.0)            # lift-arm plate, |Y|
LIFT_Y = 575.0                    # lift-cylinder plane, |Y|


def P(p, y=0.0):
    """(x, z) side-plane point to a 3-D point at y."""
    return (float(p[0]), float(y), float(p[1]))


def ys(s, a, b):
    """The |Y| range a..b on side s (+1 left, -1 right), as sorted (y0, y1)."""
    return tuple(sorted((s * a, s * b)))


def arc_band(cx, cz, r0, r1, a0, a1, n=28):
    """Side-plane polygon of a curved strip between radii r0 and r1, angles in degrees."""
    return arc_pts(cx, cz, r1, a0, a1, n) + arc_pts(cx, cz, r0, a1, a0, n)


def loft_x(sections):
    """Ruled loft through cross sections [(x, [(y, z), ...]), ...] with matching point counts."""
    wires = [cq.Wire.makePolygon([cq.Vector(x, y, z) for y, z in pts], close=True) for x, pts in sections]
    return cq.Solid.makeLoft(wires, ruled=True)


def hyd(a, b, rb, rr, frac, eye_a, eye_b):
    """Hydraulic cylinder from a (base) to b (rod end), 3-D points; eyes are (radius, half width)
    cross bosses along Y. Returns (barrel parts, rod parts, base eye, rod eye)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    u = d / np.linalg.norm(d)
    j = a + d * frac
    s0 = a + u * eye_a[0] * 0.55
    t = lambda p: tuple(map(float, p))    # noqa: E731
    barrel = [cyl(rb, t(s0), t(j)), cyl(rb * 1.1, t(j - u * 70), t(j + u * 6)),
              cyl(rb * 1.08, t(s0 + u * 12), t(s0 + u * 65))]
    rod = [cyl(rr, t(j - u * 30), t(b))]
    ey = np.array([0.0, 1.0, 0.0])
    base_eye = cyl(eye_a[0], t(a - ey * eye_a[1]), t(a + ey * eye_a[1]))
    rod_eye = cyl(eye_b[0], t(b - ey * eye_b[1]), t(b + ey * eye_b[1]))
    return barrel, rod, base_eye, rod_eye


# ---------------------------------------------------------------- wheels

def tyre_at_origin():
    """23.5R25 loader tyre, axis along Y through the origin: carcass plus chevron lugs."""
    prof = [(330, -280), (355, -283), (400, -292), (470, -302), (560, -308), (640, -304), (690, -292),
            (725, -268), (745, -235), (752, -200), (752, 200), (745, 235), (725, 268), (690, 292),
            (640, 304), (560, 308), (470, 302), (400, 292), (355, 283), (330, 280)]
    carcass = cq.Workplane("XY").polyline(prof).close().revolve(360, (0, 0, 0), (0, 1, 0)).val()
    crown = cyl(R, (0, -400, 0), (0, 400, 0))
    n, w, sweep = 44, 118.0, 150.0
    lugs = []
    for k in range(n):
        s = 1 if k % 2 == 0 else -1
        pts = [(-w / 2 - sweep / 2, s * 314), (w / 2 - sweep / 2, s * 314),
               (w / 2 + sweep / 2, -s * 28), (-w / 2 + sweep / 2, -s * 28)]
        lug = prism(pts, "z", 690, R + 20).intersect(crown)
        lugs.append(rot(lug, 360.0 * k / n, (0, 1, 0)))
    return [carcass] + lugs


def wheel_at_origin(m):
    """Yellow 25 in rim with its outer face towards +Y, planetary hub, wheel nuts."""
    rim = [cyl(345, (0, -250, 0), (0, 175, 0)),
           cut(cyl(392, (0, 168, 0), (0, 262, 0)), cyl(328, (0, 160, 0), (0, 270, 0))),
           cut(cyl(372, (0, -268, 0), (0, -200, 0)), cyl(320, (0, -280, 0), (0, -190, 0)))]
    nuts = []
    for k in range(18):
        a = 2 * math.pi * k / 18
        x, z = 290 * math.cos(a), 290 * math.sin(a)
        nuts.append(cyl(24, (x, 165, z), (x, 200, z)))
    hub = [cyl(240, (0, 120, 0), (0, 232, 0)), cyl(176, (0, 225, 0), (0, 262, 0)),
           cyl(46, (0, 255, 0), (0, 276, 0))]
    bolts = []
    for k in range(10):
        a = 2 * math.pi * (k + 0.5) / 10
        x, z = 208 * math.cos(a), 208 * math.sin(a)
        bolts.append(cyl(16, (x, 225, z), (x, 246, z)))
    return rim, hub, nuts + bolts


# ---------------------------------------------------------------- the machine

def build(m):
    t = m.t
    tyre = tyre_at_origin()
    rim, hub, nuts = wheel_at_origin(m)

    def place(shapes, x, s):
        out = [mv(sh, x, TYC, ZA) for sh in shapes]
        return out if s > 0 else [mirror_y(sh) for sh in out]

    for x, end in ((XF, "front"), (XR, "rear")):
        for s, side in ((1, "L"), (-1, "R")):
            m.add(f"tyre_{end}_{side}", RUBBER, place(tyre, x, s))
            m.add(f"rim_{end}_{side}", YELLOW, place(rim, x, s))
            m.add(f"hub_{end}_{side}", DARK, place(hub, x, s))
            m.add(f"wheel_nuts_{end}_{side}", STEEL, place(nuts, x, s))

    # ---- axles and driveline
    for x, end, k in ((XF, "front", -1), (XR, "rear", 1)):
        housing = [cyl(165, (x, -840, ZA), (x, 840, ZA)), sphere(318, (x, 0, ZA - 20)),
                   cyl(150, (x, 0, ZA - 10), (x + k * 430, 0, ZA + 20))]
        for s in (1, -1):
            housing += [cone(165, 252, (x, s * 560, ZA), (x, s * 690, ZA)),
                        cyl(252, (x, s * 690, ZA), (x, s * 830, ZA))]
        m.add(f"{end}_axle", DARK, housing)
    m.add("driveshaft", DARK, cyl(55, (-700, 0, 1000), (XF - 400, 0, ZA + 30)),
          cyl(55, (XR + 400, 0, ZA + 30), (-1150, 0, 1000)))

    # ---- front frame: body, towers carrying the arm pivots and tilt-cylinder base
    body = [(320, 620), (1150, 620), (1250, 900), (2050, 900), (2150, 660), (2700, 660), (2760, 760),
            (2760, 920), (2350, 980), (2150, 1080), (1450, 1260), (650, 1420), (320, 1420)]
    tower = [(620, 1300), (1700, 1300), (1300, 2450), (680, 2450)]
    ff = [prism(body, "y", -450, 450)]
    ff += [prism(tower, "y", *ys(s, 360, 450)) for s in (1, -1)]
    ff.append(box(900, 1250, -360, 360, 1400, 2150))                     # web between the towers
    ff += [box(660, 860, *ys(s, 440, 540), 980, 1180) for s in (1, -1)]  # lift-cylinder base brackets
    ff += [box(530, 670, *ys(s, 430, 680), 700, 900) for s in (1, -1)]  # steering-cylinder lugs
    m.add("front_frame", YELLOW, ff)
    m.add("bucket_stops", DARK, [box(2720, 2800, *ys(s, 250, 440), 780, 900) for s in (1, -1)])

    # ---- rear frame
    rf = [box(-3440, -2150, -500, 500, 620, 1560), box(-2150, -1150, -500, 500, 940, 1560),
          box(-1150, -320, -500, 500, 620, 1560)]
    rf += [box(-920, -780, *ys(s, 480, 680), 700, 900) for s in (1, -1)]
    rf.append(box(-2000, -1300, -320, 320, 900, 1000))                     # axle trunnion
    m.add("rear_frame", YELLOW, rf)

    # ---- articulation hinge
    clevis = [(-450, -280)] + arc_pts(0, 0, 280, -90, 90, 14) + [(-450, 280)]
    tongue = [(450, 250)] + arc_pts(0, 0, 250, 90, 270, 14) + [(450, -250)]
    m.add("hinge_plates", YELLOW, [prism(clevis, "z", z0, z1) for z0, z1 in
                                   ((1150, 1220), (1350, 1420), (580, 650), (790, 860))],
          [prism(tongue, "z", z0, z1) for z0, z1 in ((1226, 1344), (656, 784))])
    caps = [cyl(122, (0, 0, 1418), (0, 0, 1448)), cyl(122, (0, 0, 552), (0, 0, 582))]
    caps += [cyl(16, (85 * math.cos(a), 85 * math.sin(a), 1440), (85 * math.cos(a), 85 * math.sin(a), 1462))
             for a in np.linspace(0, 2 * math.pi, 4, endpoint=False) + math.pi / 4]
    m.add("hinge_pins", STEEL, cyl(75, (0, 0, 1120), (0, 0, 1450)), cyl(75, (0, 0, 545), (0, 0, 890)), caps)

    # steering cylinders, one each side across the hinge
    for s in (1, -1):
        barrel, rod, e0, e1 = hyd((-850, s * 600, 800), (600, s * 600, 800), 70, 40, 0.56, (78, 60), (62, 50))
        m.add("steering_cylinder", BLACK, barrel, e0)
        m.add("steering_cylinder_rod", CHROME, rod, e1)

    # ---- fenders
    fth = t(16)
    for s in (1, -1):
        y0, y1 = ys(s, 735, 1420)
        m.add("front_fender", YELLOW, prism(arc_band(XF, ZA, 880, 880 + fth, 12, 125), "y", y0, y1),
              prism(arc_band(XF, ZA, 878, 935, 11, 126), "y", *ys(s, 1392, 1424)),
              prism([(1590, 900), (1710, 900)] + arc_pts(XF, ZA, 888, 86, 94, 2), "y", *ys(s, 680, 740)),
              bar((1450, s * 440, 1250), (1450, s * 760, 1650), 90, 90, up=(1, 0, 0)))
        m.add("rear_fender", YELLOW, prism(arc_band(XR, ZA, 880, 880 + fth, 40, 178), "y", y0, y1),
              prism(arc_band(XR, ZA, 878, 935, 39, 179), "y", *ys(s, 1392, 1424)))
        mf = t(32)
        m.add("mud_flap", RUBBER, box(-2530 - mf, -2530, *ys(s, 760, 1400), 330, 845))

    # ---- rear body: side pods, deck, counterweight
    pods = [box(-3430, -2540, *ys(s, 490, 1180), 640, 1560) for s in (1, -1)]
    m.add("rear_pods", YELLOW, pods, box(-3440, -2540, -1180, 1180, 1540, 1600))
    if not m.print_mode:
        seams = [box(x - 5, x + 5, 1178, 1184, 700, 1500) for x in (-3330, -2640)]
        seams += [box(-3330, -2640, 1178, 1184, z - 5, z + 5) for z in (700, 1500)]
        m.add("pod_door_seams", BLACK, seams)
    m.add("pod_door_handle", BLACK, box(-2760, -2700, 1170, 1200, 1080, 1180))
    m.add("fuel_cap", BLACK, cyl(70, (-3000, -900, 1580), (-3000, -900, 1640)))
    m.add("deck_treads", DARK, [box(-3400, -2580, *ys(s, 760, 1150), 1595, 1600 + t(6)) for s in (1, -1)])

    cw_plan = [(-3400, -1180), (-3400, 1180)] + arc_pts(-3430, 880, 300, 90, 180, 10) + \
        arc_pts(-3430, -880, 300, 180, 270, 10)
    cw_side = [(-3390, 480), (-3390, 1610), (-3590, 1610), (-3700, 1520), (-3735, 1420), (-3735, 700),
               (-3640, 480)]
    cw = prism(cw_plan, "z", 480, 1600).intersect(prism(cw_side, "y", -1200, 1200))
    cw = cut(cw, box(-3760, -3560, -170, 170, 560, 720))                  # tow-pin slot
    m.add("counterweight", YELLOW, cw)
    eyes = []
    for s in (1, -1):
        eye = prism([(-3590, 1592), (-3440, 1592), (-3480, 1700), (-3560, 1700)], "y", *ys(s, 880, 880 + t(40)))
        eyes.append(cut(eye, cyl(30, (-3518, s * 820, 1648), (-3518, s * 980, 1648))))
    m.add("lifting_eyes", YELLOW, eyes)
    m.add("tow_pin", STEEL, cyl(42, (-3640, 0, 520), (-3640, 0, 760)), cyl(70, (-3640, 0, 740), (-3640, 0, 770)))
    lamps, lens_r, lens_a, lens_w = [], [], [], []
    lt = t(10)
    for s in (1, -1):
        lamps.append(box(-3748, -3700, *ys(s, 600, 860), 1200, 1380))
        lens_r.append(box(-3748 - lt, -3744, *ys(s, 615, 705), 1215, 1365))
        lens_a.append(box(-3748 - lt, -3744, *ys(s, 715, 845), 1295, 1365))
        lens_w.append(box(-3748 - lt, -3744, *ys(s, 715, 845), 1215, 1285))
    m.add("tail_lamp_housings", BLACK, lamps)
    m.add("tail_lights", RED, lens_r)
    m.add("indicators_rear", AMBER, lens_a)
    m.add("reverse_lights", LED, lens_w)

    # ---- engine hood
    front_sec = [(-700, 1560), (700, 1560), (700, 2230), (580, 2420), (-580, 2420), (-700, 2230)]
    rear_sec = [(-700, 1560), (700, 1560), (700, 2120), (580, 2290), (-580, 2290), (-700, 2120)]
    m.add("hood", YELLOW, loft_x([(-1690, front_sec), (-3440, rear_sec)]))
    grille, louvres = [], []
    lv = t(8)
    lh, lh2 = t(22), t(24)                     # louvre heights; wider pitch in print so fins stay apart
    p1 = int(2 * lh)
    p2 = 50 if not m.print_mode else int(2 * lh2)
    for s in (1, -1):
        grille.append(box(-3250, -2450, *ys(s, 688, 712), 1690, 2090))
        louvres += [box(-3235, -2465, *ys(s, 700, 712 + lv), z, z + lh) for z in range(1712, 2070, p1)]
    grille.append(box(-3462, -3420, -580, 580, 1630, 2200))               # radiator grille, rear
    louvres += [box(-3462 - lv, -3450, -560, 560, z, z + lh2) for z in range(1650, 2190, p2)]
    m.add("hood_grilles", BLACK, grille)
    m.add("grille_louvres", DARK, louvres)
    if not m.print_mode:
        m.add("hood_seams", BLACK, [box(x - 5, x + 5, *ys(s, 698, 704), 1600, 2170)
                                     for x in (-2380, -1980) for s in (1, -1)])
    m.add("exhaust_stack", DARK, cyl(72, (-2150, -330, 2300), (-2150, -330, 3060)),
          cyl(95, (-2150, -330, 2380), (-2150, -330, 2700)))
    m.add("exhaust_tip", STEEL, cyl(78, (-2150, -330, 3040), (-2150, -330, 3170)))
    m.add("air_precleaner", BLACK, cyl(112, (-1950, 360, 2330), (-1950, 360, 2730)))
    m.add("precleaner_cap", DARK, cyl(150, (-1950, 360, 2720), (-1950, 360, 2790)),
          cone(150, 60, (-1950, 360, 2790), (-1950, 360, 2850)))
    hl = []
    for s in (1, -1):
        hl.append(box(-3478, -3380, *ys(s, 440, 600), 2235, 2335))
    m.add("rear_work_lamp_housings", BLACK, hl)
    m.add("rear_work_lights", LED, [box(-3478 - lt, -3474, *ys(s, 455, 585), 2250, 2320) for s in (1, -1)])
    m.add("rear_camera", BLACK, box(-3480, -3400, -45, 45, 2270, 2340))
    m.add("hood_grab_rail", BLACK, pipe([(-3300, 300, 2290), (-3300, 300, 2380), (-3300, -300, 2380),
                                         (-3300, -300, 2290)], m.r(16)))

    # ---- cab (ROPS) over the rear frame, door and ladder on the left
    CX0, CX1, CW, CZ0, CZ1, lean = -1700.0, -80.0, 760.0, 1700.0, 3290.0, 70.0

    def xf(z):
        return CX1 + lean * (z - CZ0) / (CZ1 - CZ0)

    m.add("cab_base", DARK, box(-1760, -40, -800, 800, 1560, CZ0))
    pp = 80.0
    frame = [bar((xf(CZ0) - pp / 2, s * (CW - pp / 2), CZ0), (xf(CZ1) - pp / 2, s * (CW - pp / 2), CZ1), pp, pp,
                 up=(1, 0, 0)) for s in (1, -1)]
    frame += [box(-990, -910, *ys(s, CW - pp, CW), CZ0, CZ1) for s in (1, -1)]
    frame += [box(CX0, CX0 + pp, *ys(s, CW - pp, CW), CZ0, CZ1) for s in (1, -1)]
    frame.append(box(xf(CZ0) - pp, xf(CZ0), -CW, CW, CZ0, 1770))
    frame += [box(CX0, xf(1820) - 10, *ys(s, CW - pp, CW), CZ0, 1820) for s in (1, -1)]
    frame.append(box(CX0, CX0 + pp, -CW, CW, CZ0, 2460))
    frame.append(box(CX0, xf(CZ1), -CW, CW, CZ1 - 60, CZ1))
    m.add("cab_frame", BLACK, frame)

    g = t(12)
    zt = CZ1 - 60
    glass = [bar((xf(1755) - pp / 2, 0, 1755), (xf(zt) - pp / 2, 0, zt), 2 * CW - pp, g, up=(1, 0, 0))]
    for s in (1, -1):
        yc = s * (CW - pp / 2)
        door = [(-950, 1820), (xf(1820) - pp / 2, 1820), (xf(zt) - pp / 2, zt), (-950, zt)]
        quarter = [(CX0 + pp / 2, 1820), (-950, 1820), (-950, zt), (CX0 + pp / 2, zt)]
        glass += [prism(door, "y", yc - g / 2, yc + g / 2), prism(quarter, "y", yc - g / 2, yc + g / 2)]
    glass.append(box(CX0 + pp / 2 - g / 2, CX0 + pp / 2 + g / 2, -(CW - pp / 2), CW - pp / 2, 2460, zt))
    m.add("cab_glass", GLASS, glass)

    m.add("cab_roof", YELLOW, rounded_box(CX0 - 70, xf(CZ1) + 70, -CW - 60, CW + 60, CZ1, CZ1 + 150, 40))
    m.add("roof_panel", DARK, box(-1450, -350, -480, 480, CZ1 + 140, CZ1 + 160))

    # interior (solid in the print, so the glazed cab is not a sealed hollow)
    if m.print_mode:
        core = [(CX0 + 40, CZ0 - 10), (xf(CZ0 - 10) - 40, CZ0 - 10), (xf(CZ1 + 10) - 40, CZ1 + 10), (CX0 + 40, CZ1 + 10)]
        m.add("cab_core", DARK, prism(core, "y", -CW + 40, CW - 40))
    m.add("seat", BLACK, box(-1300, -860, -260, 260, CZ0, 2120),
          bar((-1330, 0, 2080), (-1420, 0, 2760), 520, 150, up=(1, 0, 0)),
          [box(-1250, -900, *ys(s, 240, 320), 2100, 2220) for s in (1, -1)])
    m.add("controls", DARK, box(-380, -150, -420, 420, CZ0, 1980),
          bar((-420, 0, 1950), (-540, 0, 2300), 110, 110, up=(1, 0, 0)),
          box(-1150, -700, -580, -380, CZ0, 2180), cyl(18, (-800, -480, 2170), (-800, -480, 2330)))
    wheel_axis = np.array([-120.0, 0.0, 350.0]) / np.linalg.norm([-120.0, 0.0, 350.0])
    wc = np.array([-550.0, 0.0, 2320.0])
    e1 = np.array([0.0, 1.0, 0.0])
    e2 = np.cross(wheel_axis, e1)
    spokes = [bar(tuple(wc), tuple(wc + 172 * (math.cos(a) * e1 + math.sin(a) * e2)), 30, t(15), up=tuple(wheel_axis))
              for a in (math.radians(-90), math.radians(30), math.radians(150))]
    m.add("steering_wheel", BLACK, torus(170, m.r(18), tuple(wc), tuple(wheel_axis)),
          cyl(40, (-560, 0, 2270), (-545, 0, 2330)), spokes)

    # exterior cab details
    wt = t(10)
    off = g / 2 + wt / 2 - 4
    m.add("wiper", BLACK, bar((xf(1800) - pp / 2 + off, 260, 1800), (xf(2950) - pp / 2 + off, -120, 2950), t(30), wt,
                              up=(1, 0, 0)),
          cyl(t(30), (xf(1800) - pp / 2 + off - 5, 260, 1800), (xf(1800) - pp / 2 + off + 25, 260, 1800)))
    rr = m.r(15)
    m.add("cab_grab_handles", YELLOW,
          pipe([(xf(z) - pp / 2, CW - 10 if k in (0, 3) else CW + 70, z) for k, z in enumerate((1950, 1950, 2900, 2900))],
               rr),
          pipe([(-950, CW - 10, 1950), (-950, CW + 70, 1950), (-950, CW + 70, 2900), (-950, CW - 10, 2900)], rr))
    m.add("door_handle", BLACK, box(-290, xf(2200) - pp + 20, CW - 20, CW + 28, 2170, 2215))
    m.add("door_hinges", DARK, [cyl(22, (-960, CW + 18, z), (-960, CW + 18, z + 110)) for z in (1950, 2880)],
          [box(-990, -950, CW - 10, CW + 30, z, z + 110) for z in (1950, 2880)])
    ra = m.r(15) if not m.print_mode else 28        # mirror arm: sturdier in the print
    for s in (1, -1):
        xa = xf(2650) - pp / 2
        m.add("mirror_arm", BLACK, pipe([(xa, s * (CW - 30), 2650), (xa + 60, s * (CW + 150), 2700),
                                         (xa + 90, s * (CW + 250), 2620)], ra))
        m.add("mirror_housing", BLACK, box(xa + 70, xa + 130, *ys(s, CW + 210, CW + 390), 2420, 2720))
        m.add("mirror_glass", CHROME, box(xa + 72 - t(6), xa + 74, *ys(s, CW + 222, CW + 378), 2432, 2708))

    # roof lamps and beacon
    fl = [box(-20, 90, *ys(s, 470, 650), CZ1 + 110, CZ1 + 205) for s in (1, -1)]
    fl += [box(-1800, -1690, *ys(s, 470, 650), CZ1 + 110, CZ1 + 205) for s in (1, -1)]
    m.add("roof_lamp_housings", BLACK, fl)
    m.add("roof_work_lights", LED, [box(86, 90 + lt, *ys(s, 485, 635), CZ1 + 122, CZ1 + 193) for s in (1, -1)],
          [box(-1800 - lt, -1796, *ys(s, 485, 635), CZ1 + 122, CZ1 + 193) for s in (1, -1)])
    m.add("indicators_front", AMBER, [box(30, 75, *ys(s, 700, 790), CZ1 + 40, CZ1 + 95) for s in (1, -1)])
    m.add("beacon_base", BLACK, cyl(85, (-1450, 450, CZ1 + 140), (-1450, 450, CZ1 + 175)),
          cyl(45, (-1450, 450, CZ1 + 250), (-1450, 450, CZ1 + 272)))
    m.add("beacon", AMBER, cyl(68, (-1450, 450, CZ1 + 172), (-1450, 450, CZ1 + 252)))

    # ---- access ladder, landing and handrails (left side, ahead of the rear tyre)
    zb, zl = 400.0, 1640.0
    xb, xl = -500.0, -820.0

    def lx(z):
        return xb + (xl - xb) * (z - zb) / (zl - zb)

    st = t(20)
    m.add("ladder_stringers", BLACK, [bar((xb, y, zb - 20), (xl, y, zl), st, 90, up=(1, 0, 0)) for y in (895, 1295)])
    m.add("ladder_steps", DARK, [box(lx(z) - 70, lx(z) + 100, 885, 1305, z - 22, z + 22)
                                 for z in (zb + 20, 730, 1030, 1330)])
    m.add("landing", DARK, box(-1010, -460, 700, 1310, 1600, 1650))
    m.add("landing_brackets", YELLOW, [box(x - 40, x + 40, 480, 760, 1440, 1610) for x in (-900, -560)])
    hr = m.r(16) if not m.print_mode else 25
    m.add("handrail", YELLOW,
          pipe([(lx(650), 1300, 650), (lx(650), 1300, 1550), (lx(1640), 1300, 2540), (-1000, 1300, 2540),
                (-1000, 1300, 1645)], hr))

    # ---- lift arms, cross tube, bell crank, tilt link
    arm = band([A, M, B], [200, 228, 150])
    lift_lug = [(1780, 1250), (2020, 1250)] + arc_pts(L1[0], L1[1], 88, 0, -180, 10)
    for s in (1, -1):
        y0, y1 = ys(s, *ARM_Y)
        m.add("lift_arm", YELLOW, prism(arm, "y", y0, y1), cyl(205, P(A, y0), P(A, y1)),
              cyl(125, P(B, y0), P(B, y1)), prism(lift_lug, "y", *ys(s, 530, 630)))
    m.add("cross_tube", YELLOW, cyl(125, P(CT, -ARM_Y[1]), P(CT, ARM_Y[1])))
    m.add("crank_supports", YELLOW, [prism(band([CT, C], [110, 95]), "y", *ys(s, 105, 150)) for s in (1, -1)],
          [cyl(95, P(C, ys(s, 105, 150)[0]), P(C, ys(s, 105, 150)[1])) for s in (1, -1)])
    crank = band([D, C, E], [95, 125, 90])
    m.add("bell_crank", YELLOW, [prism(crank, "y", *ys(s, 52, 102)) for s in (1, -1)],
          [cyl(r, P(p, ys(s, 52, 102)[0]), P(p, ys(s, 52, 102)[1])) for s in (1, -1)
           for p, r in ((D, 95), (C, 125), (E, 90))])
    m.add("tilt_link", DARK, bar(P(E), P(F), 88, 140), cyl(78, P(E, -44), P(E, 44)), cyl(78, P(F, -44), P(F, 44)))

    # cylinders
    barrel, rod, e0, e1 = hyd(P(T0), P(D), 115, 62, 0.6, (108, 85), (82, 48))
    m.add("tilt_cylinder", BLACK, barrel, e0)
    m.add("tilt_cylinder_rod", CHROME, rod, e1)
    for s in (1, -1):
        y = s * LIFT_Y
        barrel, rod, e0, e1 = hyd(P(L0, y), P(L1, y), 95, 56, 0.62, (100, 55), (72, 45))
        m.add("lift_cylinder", BLACK, barrel, e0)
        m.add("lift_cylinder_rod", CHROME, rod, e1)

    hoses = []
    for s in (1, -1):
        hoses += pipe([(760, s * 400, 2440), (1100, s * 230, 2445), (1450, s * 60, 2390)], m.r(18))
        hoses += pipe([(700, s * 445, 1350), (980, s * 520, 1240), (1080, s * 575, 1135)], m.r(16))
    m.add("hoses", BLACK, hoses)

    pins = []
    for s in (1, -1):
        pins += [cyl(70, P(A, s * 330), P(A, s * 690)), cyl(118, P(A, s * 445), P(A, s * 525)),
                 cyl(60, P(B, s * 475), P(B, s * 712)), cyl(50, P(L0, s * 430), P(L0, s * 650)),
                 cyl(45, P(L1, s * 515), P(L1, s * 645))]
    pins += [cyl(55, P(C, -165), P(C, 165)), cyl(50, P(D, -118), P(D, 118)), cyl(50, P(E, -118), P(E, 118)),
             cyl(50, P(F, -118), P(F, 118)), cyl(55, P(T0, -470), P(T0, 470))]
    m.add("pins", STEEL, pins)

    # ---- 2.9 m general-purpose bucket with a bolt-on cutting edge
    BW = 1420.0
    sh = t(30) / 2
    shell = [(4200, -4 + sh), (3660, -4 + sh), (3450, 56), (3290, 186), (3200, 400), (3180, 700), (3205, 990),
             (3285, 1225), (3420, 1365), (3600, 1432), (3790, 1442)]
    side = [(4440, -4), (3660, -4), (3440, 40), (3272, 175), (3182, 395), (3162, 700), (3188, 1000),
            (3270, 1243), (3410, 1385), (3598, 1455), (3795, 1462), (3835, 1420), (4445, 70)]
    sp = t(30)

    def behind(z, d):
        """The point d behind the shell's mid-line at height z (on the back plate and curl)."""
        for (x0, z0), (x1, z1) in zip(shell[1:], shell[2:]):
            if z0 <= z <= z1:
                f = (z - z0) / (z1 - z0)
                L = math.hypot(x1 - x0, z1 - z0)
                return (x0 + f * (x1 - x0) - d * (z1 - z0) / L, z + d * (x1 - x0) / L)
        raise ValueError(z)

    # The lug outlines stop 10 mm behind the shell's mid-line, so they stay hidden inside the
    # bucket while still overlapping the back plate (5 mm shown, 10 mm in the print).
    hinge_lug = [behind(760, 10)] + arc_pts(B[0], B[1], 122, 100, 262, 12) + \
        [behind(z, 10) for z in (230, 400, 700)]
    tilt_lug = [behind(1300, 10)] + arc_pts(F[0], F[1], 95, 90, 270, 12) + \
        [behind(z, 10) for z in (960, 990, 1225)]
    bucket = []
    for s in (1, -1):
        for a, b in ((488, 528), (652, 692)):
            bucket.append(prism(hinge_lug, "y", *ys(s, a, b)))
        bucket.append(prism(tilt_lug, "y", *ys(s, 55, 102)))
    bucket += [prism(band(shell, sh), "y", -BW + 5, BW - 5),
               prism(side, "y", -BW, -BW + sp), prism(side, "y", BW - sp, BW),
               box(3640, 3800, -BW, BW, 1412, 1482)]                               # top edge bar
    m.add("bucket", YELLOW, bucket)
    m.add("bucket_floor_wear", WORN, box(3700, 4120, -BW + sp, BW - sp, -4 + 2 * sh - 2, -4 + 2 * sh + t(4)))
    edge = [(4080, -4), (4400, -4), (4400, 30), (4340, 62), (4080, 62)]
    m.add("base_edge", DARK, prism(edge, "y", -BW + 5, BW - 5))
    boce = [(4300, -4), (4512, -4), (4512, 14), (4472, 44), (4300, 44)]
    segs = ((-BW + 15, -488), (-472, 472), (488, BW - 15))
    m.add("bolt_on_edge", STEEL, [prism(boce, "y", a, b) for a, b in segs])
    m.add("edge_bolts", BLACK, [cyl(24, (4250, y, 55), (4250, y, 62 + t(16))) for y in np.linspace(-1300, 1300, 10)])
    u = np.array([3835 - 4445, 1420 - 70.0])
    u /= np.linalg.norm(u)
    nrm = np.array([-u[1], u[0]])                   # into the side plate, up and back
    if nrm[0] > 0:
        nrm = -nrm
    p0 = np.array([4462.0, -4.0])
    p1 = p0 + 520 * u
    cutter = [tuple(p0), tuple(p1), tuple(p1 + 120 * nrm), tuple(p0 + 120 * nrm + np.array([-60, 0]))]
    cutter = [(x, max(z, -4)) for x, z in cutter]
    sc = t(26)
    m.add("side_cutters", DARK, [prism(cutter, "y", *ys(s, BW - 6, BW + sc)) for s in (1, -1)])
    cb = []
    for s in (1, -1):
        for f in (0.3, 0.7):
            q = p0 + f * 520 * u + 60 * nrm
            cb.append(cyl(20, (q[0], s * (BW + sc - 4), q[1]), (q[0], s * (BW + sc + 12), q[1])))
    m.add("side_cutter_bolts", STEEL, cb)
