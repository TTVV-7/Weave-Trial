"""Backhoe loader, 14 ft (4.3 m) dig depth class, rigid frame, 4WD, centre-mount backhoe.

Front: loader with two box-section lift arms pivoting on towers ahead of the cab, a lift
cylinder under each arm, a tilt cylinder on top of each arm working a tipping lever and a
bucket link, a torque tube between the arms, and a ~1 m3 general-purpose bucket with a
bolted cutting edge resting flat on the ground. Sloping engine hood with grille, headlights,
indicators and side louvres, exhaust stack and air pre-cleaner, front counterweight/bumper
with a tow jaw, oscillating front axle with steering cylinder and front mudguards.
Middle: rigid main frame, rear axle, rear fenders, ROPS/FOPS cab centred between the
wheels with full glazing, door, wiper, mirrors, grab handles, steps both sides on the
fuel and hydraulic tanks, seat, steering wheel, loader and backhoe controls, roof with
front and rear work lights and a beacon, tail lamps.
Rear: backhoe tower carrying the swing casting (kingpost) on upper and lower swing pins with
two swing cylinders; curved (banana) boom with its boom cylinder underneath, dipper with
the dipper (crowd) cylinder on top of the boom, bucket cylinder on the back of the dipper
working side links and an H-link; a 24 in trenching bucket with four teeth resting on the
ground behind the machine; two stabiliser legs down on pads, each with its cylinder.

Dimensions are typical figures for the class, not any one machine:
  wheelbase 2.20 m; rear tyres 19.5L-24 R4 tractor tread (~1.35 m OD, ~0.5 m wide) at a
      ~1.75 m track; front tyres 12.5/80-18 (~0.95 m OD, ~0.32 m wide) at ~1.81 m;
      both sunk 1.5 % of their radius for a flat print contact patch
  width over the rear tyres ~2.25 m, loader bucket 2.30 m wide (~1.0 m3), ~3.4 m over the
      stabiliser pads
  height to the cab roof ~3.68 m (~3.8 m to the beacon); loader arm pivot ~2.0 m up
  backhoe: swing pivot 1.48 m behind the rear axle, boom ~2.78 m pin to pin (curved),
      dipper ~2.0 m, 610 mm (24 in) bucket, ~0.95 m tip radius, which gives the class's
      ~4.3 m (14 ft) dig depth; stabiliser pads ~2.9 m apart (centres)
  cab floor 1.65 m up; seat cushion ~0.5 m, dash ~0.68 m, steering wheel ~0.9 m above it
  length in this pose (backhoe bucket on the ground behind) ~8.9 m; the folded transport
      length of the class is ~7.0-7.3 m
Generic and brand-neutral: no names, logos or maker-specific styling.

Millimetres, X forward (loader end), Y left, Z up, ground at Z = 0, X = 0 at the rear axle.
"""

import math

import cadquery as cq
import numpy as np

from cadkit import (arc_pts, band, bar, box, cone, cut, cyl, mirror_y, mv, pipe, prism, rot, rounded_box,
                    sphere, torus)
from finishes import AMBER, BLACK, CHROME, DARK, GLASS, LED, RED, RUBBER, STEEL, YELLOW

ASSET = dict(key="backhoe_loader", stem="Backhoe_Loader", title="Backhoe Loader (14 ft dig depth class)",
             az=40, el=20, size="1200x900")

# ---------------------------------------------------------------- main dimensions (mm)
XRA, XFA = 0.0, 2200.0              # rear / front axle
RR = 675.0                          # 19.5L-24 rear tyre radius
ZRA = RR - 0.015 * RR               # rear axle height, tyre sunk 1.5 %
RTY = 875.0                         # rear tyre centre plane, |Y|
RF = 475.0                          # 12.5/80-18 front tyre radius
ZFA = RF - 0.015 * RF               # front axle height
FTY = 905.0                         # front tyre centre plane, |Y|

# loader arm, side plane points (x, z)
A = np.array([1300.0, 2000.0])      # arm pivot on the loader tower
M = np.array([3150.0, 1450.0])      # bend in front of the hood
B = np.array([3420.0, 330.0])       # bucket hinge pin
ARM_Y = (520.0, 660.0)              # arm plates, |Y|
L0 = np.array([1450.0, 1000.0])     # lift cylinder base
L1 = np.array([2500.0, 1420.0])     # lift cylinder rod end, under the arm
T0 = np.array([1700.0, 2120.0])     # tilt cylinder base, on top of the arm
G = np.array([3210.0, 1490.0])      # tipping-lever pivot on the arm
C1 = np.array([3100.0, 1770.0])     # tipping lever, tilt-cylinder end
C2 = np.array([3320.0, 1170.0])     # tipping lever, bucket-link end
Q = np.array([3460.0, 900.0])       # bucket link to the bucket
LINK_IN, LINK_OUT = 522.0, 658.0   # |Y| of the lever/link plates' faces that overlap the arm sides by 2 mm

# cab
CX0, CX1, CW = -750.0, 1050.0, 900.0
CZ0, CZ1 = 1650.0, 3420.0           # glazing from / to


def P(p, y=0.0):
    """(x, z) side-plane point to a 3-D point at y."""
    return (float(p[0]), float(y), float(p[1]))


def ys(s, a, b):
    """The |Y| range a..b on side s (+1 left, -1 right), as sorted (y0, y1)."""
    return tuple(sorted((s * a, s * b)))


def e2(deg):
    return np.array([math.cos(math.radians(deg)), math.sin(math.radians(deg))])


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def rot2(p, deg):
    """Rotate a 2-D (x, z) point anticlockwise by deg."""
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array([p[0] * c - p[1] * s, p[0] * s + p[1] * c])


def bez(ctrl, n):
    """n+1 points on a cubic Bezier curve through four (x, z) control points."""
    p = [np.asarray(c, float) for c in ctrl]
    out = []
    for i in range(n + 1):
        u = i / n
        q = (1 - u) ** 3 * p[0] + 3 * (1 - u) ** 2 * u * p[1] + 3 * (1 - u) * u ** 2 * p[2] + u ** 3 * p[3]
        out.append((float(q[0]), float(q[1])))
    return out


def arc_band(cx, cz, r0, r1, a0, a1, n=28):
    """Side-plane polygon of a curved strip between radii r0 and r1, angles in degrees."""
    return arc_pts(cx, cz, r1, a0, a1, n) + arc_pts(cx, cz, r0, a1, a0, n)


def loft_x(sections):
    """Ruled loft through cross sections [(x, [(y, z), ...]), ...] with matching point counts."""
    wires = [cq.Wire.makePolygon([cq.Vector(x, y, z) for y, z in pts], close=True) for x, pts in sections]
    return cq.Solid.makeLoft(wires, ruled=True)


def ram3(a, b, rb, rr, frac=0.55, axis=(0, 1, 0), eye=None, rod_eye=None):
    """Hydraulic cylinder from a (base) to b (rod end), 3-D points; eye bosses across `axis`,
    each (radius, half length). Returns (barrel parts, rod parts)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    u = d / np.linalg.norm(d)
    ax = np.asarray(axis, float)
    er, eh = eye or (rb, rb * 0.85)
    rer, reh = rod_eye or (rr * 1.45, rr * 1.2)
    j = a + d * frac
    s0 = a + u * er * 0.7
    T = lambda p: tuple(float(v) for v in p)    # noqa: E731
    barrel = [cyl(rb, T(s0), T(j)), cyl(rb * 1.12, T(j - u * 70), T(j + u * 4)),
              cyl(rb * 1.1, T(s0), T(s0 + u * 50)), cyl(er, T(a - ax * eh), T(a + ax * eh))]
    rod = [cyl(rr, T(j - u * 20), T(b - u * rer * 0.5)), cyl(rer, T(b - ax * reh), T(b + ax * reh))]
    return barrel, rod


def lug(c, r, base, side_deg, n=10):
    """Side-plane lug: a boss of radius r round c, joined to a straight base edge
    (two points) on the far side; side_deg is the direction from the base to the boss."""
    return [tuple(base[0]), tuple(base[1])] + arc_pts(c[0], c[1], r, side_deg - 90, side_deg + 90, n)


# ---------------------------------------------------------------- wheels

def tyre_at_origin(R, prof, half, n, w, sweep, y_in, depth):
    """Tractor-tread tyre, axis along Y through the origin: carcass plus alternating bars,
    chevrons pointing forward at the top."""
    carcass = cq.Workplane("XY").polyline(prof).close().revolve(360, (0, 0, 0), (0, 1, 0)).val()
    crown = cyl(R, (0, -half - 60, 0), (0, half + 60, 0))
    lugs = []
    for k in range(n):
        s = 1 if k % 2 == 0 else -1
        pts = [(-w / 2 - sweep / 2, s * half), (w / 2 - sweep / 2, s * half),
               (w / 2 + sweep / 2, -s * y_in), (-w / 2 + sweep / 2, -s * y_in)]
        lugs.append(rot(prism(pts, "z", R - depth - 30, R + 20).intersect(crown), 360.0 * k / n, (0, 1, 0)))
    return [carcass] + lugs


def rear_tyre():
    prof = [(318, -212), (345, -232), (400, -246), (470, -252), (540, -250), (595, -240), (625, -222),
            (636, -195), (636, 195), (625, 222), (595, 240), (540, 250), (470, 252), (400, 246), (345, 232),
            (318, 212)]
    return tyre_at_origin(RR, prof, 254, 34, 95, 200, 30, 42)


def front_tyre():
    prof = [(232, -138), (255, -152), (300, -160), (360, -162), (410, -157), (440, -142), (450, -120),
            (452, -100), (452, 100), (450, 120), (440, 142), (410, 157), (360, 162), (300, 160), (255, 152),
            (232, 138)]
    return tyre_at_origin(RF, prof, 164, 28, 62, 110, 22, 24)


def rear_wheel():
    """24 in rim (outer face towards +Y), hub, wheel nuts."""
    rim = [cyl(318, (0, -226, 0), (0, 110, 0)),
           cut(cyl(350, (0, 100, 0), (0, 218, 0)), cyl(302, (0, 90, 0), (0, 230, 0))),
           cut(cyl(346, (0, -236, 0), (0, -192, 0)), cyl(300, (0, -245, 0), (0, -180, 0)))]
    hub = [cyl(200, (0, 95, 0), (0, 172, 0)), cyl(128, (0, 165, 0), (0, 226, 0)), cyl(52, (0, 220, 0), (0, 246, 0))]
    nuts = []
    for k in range(10):
        a = 2 * math.pi * (k + 0.5) / 10
        nuts.append(cyl(19, (164 * math.cos(a), 165, 164 * math.sin(a)), (164 * math.cos(a), 192, 164 * math.sin(a))))
    return rim, hub, nuts


def front_wheel():
    """18 in rim (outer face towards +Y), hub, wheel nuts."""
    rim = [cyl(232, (0, -150, 0), (0, 70, 0)),
           cut(cyl(258, (0, 62, 0), (0, 140, 0)), cyl(220, (0, 50, 0), (0, 150, 0))),
           cut(cyl(255, (0, -160, 0), (0, -126, 0)), cyl(220, (0, -170, 0), (0, -115, 0)))]
    hub = [cyl(140, (0, 55, 0), (0, 118, 0)), cyl(86, (0, 112, 0), (0, 158, 0)), cyl(40, (0, 152, 0), (0, 174, 0))]
    nuts = []
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        nuts.append(cyl(15, (113 * math.cos(a), 112, 113 * math.sin(a)), (113 * math.cos(a), 134, 113 * math.sin(a))))
    return rim, hub, nuts


# ---------------------------------------------------------------- the machine

def build(m):
    t, r = m.t, m.r

    # ================================================================ running gear
    def place(shapes, x, z, yc, s):
        out = [mv(sh, x, yc, z) for sh in shapes]
        return out if s > 0 else [mirror_y(sh) for sh in out]

    rt, ft = rear_tyre(), front_tyre()
    rw, fw = rear_wheel(), front_wheel()
    for s, side in ((1, "L"), (-1, "R")):
        m.add(f"rear_tyre_{side}", RUBBER, place(rt, XRA, ZRA, RTY, s))
        m.add(f"rear_rim_{side}", YELLOW, place(rw[0], XRA, ZRA, RTY, s))
        m.add(f"rear_hub_{side}", DARK, place(rw[1], XRA, ZRA, RTY, s))
        m.add(f"rear_wheel_nuts_{side}", STEEL, place(rw[2], XRA, ZRA, RTY, s))
        m.add(f"front_tyre_{side}", RUBBER, place(ft, XFA, ZFA, FTY, s))
        m.add(f"front_rim_{side}", YELLOW, place(fw[0], XFA, ZFA, FTY, s))
        m.add(f"front_hub_{side}", DARK, place(fw[1], XFA, ZFA, FTY, s))
        m.add(f"front_wheel_nuts_{side}", STEEL, place(fw[2], XFA, ZFA, FTY, s))

    # rear axle: housing, differential, trumpets, planetary hubs
    rax = [cyl(150, (XRA, -720, ZRA), (XRA, 720, ZRA)), sphere(270, (XRA, 0, ZRA - 20)),
           cyl(120, (XRA, 0, ZRA - 10), (XRA + 420, 0, ZRA + 20))]
    for s in (1, -1):
        rax += [cone(150, 215, (XRA, s * 420, ZRA), (XRA, s * 600, ZRA)), cyl(215, (XRA, s * 600, ZRA), (XRA, s * 690, ZRA))]
    m.add("rear_axle", DARK, rax)

    # front axle: oscillating beam, centre pivot, knuckles, steering cylinder
    fax = [cyl(110, (XFA, -700, ZFA), (XFA, 700, ZFA)), sphere(205, (XFA, 0, ZFA)),
           box(XFA - 210, XFA + 210, -170, 170, ZFA + 60, 600), cyl(95, (XFA - 330, 0, ZFA + 30), (XFA + 330, 0, ZFA + 30))]
    for s in (1, -1):
        fax += [cyl(135, (XFA, s * 680, ZFA), (XFA, s * 770, ZFA)),
                cyl(72, (XFA, s * 725, ZFA - 175), (XFA, s * 725, ZFA + 175)),
                bar((XFA, s * 725, ZFA + 120), (XFA - 250, s * 690, ZFA + 120), 60, 70)]
    m.add("front_axle", DARK, fax)
    m.add("steering_cylinder", BLACK, cyl(66, (XFA - 250, -380, ZFA + 120), (XFA - 250, 380, ZFA + 120)),
          box(XFA - 300, XFA - 200, -60, 60, ZFA + 20, ZFA + 120))
    m.add("steering_cylinder_rods", CHROME, cyl(30, (XFA - 250, -705, ZFA + 120), (XFA - 250, 705, ZFA + 120)))
    m.add("driveshaft", DARK, cyl(52, (XRA + 380, 0, ZRA + 20), (XFA - 300, 0, ZFA + 30)))

    # front mudguards on brackets from the steering knuckles
    for s in (1, -1):
        m.add("front_mudguard", BLACK, prism(arc_band(XFA, ZFA, 510, 510 + t(24), 28, 152), "y", *ys(s, 725, 1085)),
              prism(arc_band(XFA, ZFA, 508, 556, 27, 153), "y", *ys(s, 1090 - t(30), 1090)))
        m.add("mudguard_bracket", DARK, box(XFA - 55, XFA + 55, *ys(s, 690, 735), ZFA + 120, ZFA + 538))

    # ================================================================ main frame and rear tower
    m.add("main_frame", DARK, box(-900, 3120, -440, 440, 560, 1000),
          box(1300, 2900, -340, 340, 450, 600),                     # engine sump / transmission
          box(-400, 900, -340, 340, 480, 860))
    m.add("backhoe_tower", YELLOW, box(-1380, -750, -480, 480, 750, 1700),
          [box(-1400, -1370, y - 30, y + 30, 760, 1690) for y in (-300.0, 300.0)],
          [box(-1380, -750, *ys(s, 470, 495), 800, 1650) for s in (1, -1)])
    m.add("tower_deck", DARK, box(-1360, -770, -460, 460, 1695, 1712))

    # ================================================================ rear fenders
    for s in (1, -1):
        m.add("rear_fender", YELLOW, prism(arc_band(XRA, ZRA, 705, 705 + t(36), 6, 174), "y", *ys(s, 590, 1160)),
              prism(arc_band(XRA, ZRA, 700, 760, 5, 175), "y", *ys(s, 1168 - t(36), 1168)))

    # ================================================================ cab
    m.add("cab_tub", DARK, box(CX0, CX1, -600, 600, 850, 1400))
    m.add("cab_base", YELLOW, box(CX0, CX1, -CW, CW, 1400, CZ0))
    pp = 80.0
    frame = []
    for s in (1, -1):
        frame += [box(CX1 - pp, CX1, *ys(s, CW - pp, CW), CZ0, CZ1),          # front posts
                  box(CX0, CX0 + pp, *ys(s, CW - pp, CW), CZ0, CZ1),          # rear posts
                  box(120, 190, *ys(s, CW - 60, CW), CZ0, CZ1),               # door / B posts
                  box(CX0, CX1, *ys(s, CW - 40, CW), CZ0 - 10, CZ0 + 30)]     # sills
    frame += [box(CX0, CX1, -CW, CW, CZ1, CZ1 + 80),                         # roof header
              box(CX1 - 45, CX1, -CW + pp, CW - pp, 2090, 2130),              # windscreen rail
              box(CX0, CX0 + 45, -CW + pp, CW - pp, 2290, 2330)]              # rear window rail
    m.add("cab_frame", BLACK, frame)

    g = t(12)
    xg_f, xg_r = CX1 - 40, CX0 + 40
    glass = [box(xg_f - g / 2, xg_f + g / 2, -CW + 70, CW - 70, CZ0, CZ1 + 5),
             box(xg_r - g / 2, xg_r + g / 2, -CW + 70, CW - 70, CZ0, CZ1 + 5)]
    for s in (1, -1):
        glass.append(box(CX0 + 70, CX1 - 70, *ys(s, CW - 40 - g / 2, CW - 40 + g / 2), CZ0, CZ1 + 5))
    m.add("cab_glass", GLASS, glass)

    m.add("cab_roof", YELLOW, rounded_box(CX0 - 70, CX1 + 70, -CW - 60, CW + 60, CZ1 + 70, CZ1 + 260, 45))
    m.add("roof_cap", DARK, box(-450, 750, -560, 560, CZ1 + 250, CZ1 + 268))

    # interior (solid in the print, so the glazed cab is not a sealed hollow)
    if m.print_mode:
        m.add("cab_core", DARK, box(CX0 + 30, CX1 - 30, -CW + 30, CW - 30, 1395, CZ1 + 10))
    # cab floor at z = CZ0 (1650): seat cushion ~0.5 m up, dash ~0.68 m, wheel ~0.9 m
    m.add("cab_floor_mat", BLACK, box(CX0 + 40, CX1 - 40, -CW + 40, CW - 40, CZ0 - 2, CZ0 + 12))
    m.add("seat", BLACK, box(-300, 200, -270, 270, 2040, 2160),
          bar((-290, 0, 2130), (-350, 0, 2800), 540, 130, up=(1, 0, 0)),
          [box(-260, 120, *ys(s, 270, 330), 2220, 2280) for s in (1, -1)],
          [box(-200, -140, *ys(s, 270, 330), 2140, 2230) for s in (1, -1)])
    m.add("seat_pedestal", DARK, box(-170, 130, -170, 170, CZ0 - 10, 2045))
    m.add("dash", DARK, box(820, 1005, -560, 560, CZ0 - 10, 2330),
          bar((850, 0, 2120), (690, 0, 2560), 110, 110, up=(1, 0, 0)))
    wa = unit((-160.0, 0.0, 440.0))
    wc = np.array([680.0, 0.0, 2590.0])
    e1 = np.array([0.0, 1.0, 0.0])
    ew = np.cross(wa, e1)
    spokes = [bar(tuple(wc), tuple(wc + 175 * (math.cos(a) * e1 + math.sin(a) * ew)), 30, t(15), up=tuple(wa))
              for a in (math.radians(-90), math.radians(30), math.radians(150))]
    m.add("steering_wheel", BLACK, torus(180, r(18), tuple(wc), tuple(wa)), cyl(40, tuple(wc - wa * 40), tuple(wc + wa * 20)),
          spokes)
    m.add("backhoe_console", DARK, [box(-690, -470, *ys(s, 330, 560), CZ0 - 10, 2200) for s in (1, -1)])
    levers = []
    for s in (1, -1):
        for y in (400.0, 500.0):
            levers += [cyl(r(16), (-560, s * y, 2190), (-520, s * y, 2480)), sphere(36, (-520, s * y, 2490))]
    levers += [cyl(r(14), (700, -620, 2310), (680, -620, 2550)), sphere(32, (680, -620, 2560))]
    m.add("control_levers", BLACK, levers, box(640, 820, -700, -560, CZ0 - 10, 2320))

    # exterior cab details
    wt = t(10)
    m.add("wiper", BLACK, bar((xg_f + g / 2 + wt / 2 - 3, 280, 2170), (xg_f + g / 2 + wt / 2 - 3, -60, 3200), t(30), wt,
                              up=(1, 0, 0)),
          cyl(32, (xg_f, 280, 2170), (xg_f + 40, 280, 2170)))
    for s in (1, -1):
        m.add("grab_handle", YELLOW, pipe([(CX1 - 40, s * (CW - 20), 1760), (CX1 - 40, s * (CW + 70), 1760),
                                           (CX1 - 40, s * (CW + 70), 3000), (CX1 - 40, s * (CW - 20), 3000)], r(16)),
              pipe([(155, s * (CW - 20), 1800), (155, s * (CW + 70), 1800), (155, s * (CW + 70), 2700),
                    (155, s * (CW - 20), 2700)], r(16)))
        m.add("door_handle", BLACK, box(240, 340, *ys(s, CW - 50, CW + 30), 2200, 2250))
        m.add("door_hinges", DARK, [box(CX1 - 110, CX1 - 60, *ys(s, CW - 10, CW + 30), z, z + 110) for z in (1900, 3050)])
        # mirrors on the front posts
        xa = CX1 - 40
        m.add("mirror_arm", BLACK, pipe([(xa, s * (CW - 30), 2950), (xa + 60, s * (CW + 140), 3000),
                                         (xa + 80, s * (CW + 250), 2930)], r(15)))
        m.add("mirror_housing", BLACK, box(xa + 60, xa + 115, *ys(s, CW + 200, CW + 370), 2660, 2960))
        m.add("mirror_glass", STEEL, box(xa + 60 - t(6), xa + 64, *ys(s, CW + 212, CW + 358), 2672, 2948))
        # steps ahead of the rear tyre
        m.add("step_stringers", BLACK, [box(x0, x0 + 40, *ys(s, CW - 60, CW - 10), 420, 1405) for x0 in (745, 1005)])
        m.add("step_treads", DARK, [box(750, 1040, *ys(s, 660, CW - 15), z, z + 40) for z in (440, 880)])
        # fuel tank (left) / hydraulic tank (right) under the cab, steps on their faces
        m.add("fuel_tank" if s > 0 else "hydraulic_tank", YELLOW,
              rounded_box(700, 1035, *ys(s, 590, 832), 520, 862, 30))
        m.add("tank_straps", BLACK, [box(x, x + 40, *ys(s, 585, 842), 510, 872) for x in (760, 960)])
        if s > 0:
            m.add("fuel_filler", BLACK, cyl(45, (870, 820, 700), (870, 870, 700)), cyl(60, (870, 862, 700), (870, 892, 700)))
        else:
            m.add("sight_gauge", GLASS, box(860, 920, -840, -828, 600, 800))
            m.add("sight_gauge_frame", BLACK, box(850, 930, -834, -826, 590, 810))
        # tail lamps on the cab corners
        m.add("tail_lamp_housing", BLACK, box(CX0 - 40, CX0 + 5, *ys(s, 690, 880), 1440, 1610))
        m.add("tail_light", RED, box(CX0 - 40 - t(10), CX0 - 36, *ys(s, 700, 775), 1455, 1595))
        m.add("rear_indicator", AMBER, box(CX0 - 40 - t(10), CX0 - 36, *ys(s, 790, 868), 1455, 1595))

    # roof lamps and beacon
    lt = t(10)
    zl0, zl1 = CZ1 + 110, CZ1 + 210
    fl = [box(CX1 + 30, CX1 + 110, *ys(s, 560, 760), zl0, zl1) for s in (1, -1)]
    rl = [box(CX0 - 110, CX0 - 30, *ys(s, y0, y1), zl0, zl1) for s in (1, -1) for y0, y1 in ((300, 480), (600, 780))]
    m.add("roof_lamp_housings", BLACK, fl, rl)
    m.add("work_lights", LED, [box(CX1 + 106, CX1 + 110 + lt, *ys(s, 575, 745), zl0 + 14, zl1 - 14) for s in (1, -1)],
          [box(CX0 - 110 - lt, CX0 - 106, *ys(s, y0 + 15, y1 - 15), zl0 + 14, zl1 - 14)
           for s in (1, -1) for y0, y1 in ((300, 480), (600, 780))])
    m.add("beacon_base", BLACK, cyl(85, (-350, 560, CZ1 + 255), (-350, 560, CZ1 + 290)))
    m.add("beacon", AMBER, cyl(66, (-350, 560, CZ1 + 285), (-350, 560, CZ1 + 375)))

    # ================================================================ engine hood
    front_sec = [(-470, 980), (470, 980), (470, 1640), (400, 1780), (-400, 1780), (-470, 1640)]
    rear_sec = [(-470, 980), (470, 980), (470, 1910), (400, 2050), (-400, 2050), (-470, 1910)]
    m.add("hood", YELLOW, loft_x([(3150, front_sec), (CX1 - 20, rear_sec)]))
    m.add("grille", BLACK, box(3135, 3162, -360, 360, 1060, 1520))
    lv = t(8)
    # ribs and gaps both >= 0.8 mm at 1:50 in the print (finer pitch as drawn)
    rib_h, pitch = (t(22), 85) if m.print_mode else (22, 46)
    m.add("grille_bars", DARK, [box(3160, 3162 + lv, -345, 345, z, z + rib_h) for z in range(1080, 1500, pitch)])
    m.add("headlight_housings", BLACK, [box(3135, 3178, *ys(s, 220, 430), 1555, 1700) for s in (1, -1)])
    m.add("headlights", LED, [box(3174, 3178 + lt, *ys(s, 235, 415), 1570, 1685) for s in (1, -1)])
    m.add("indicators_front", AMBER, [box(3140, 3166 + lt * 0.5, *ys(s, 380, 455), 1440, 1520) for s in (1, -1)])
    louv = []
    for s in (1, -1):
        louv.append(box(2450, 2950, *ys(s, 455, 478), 1180, 1540))
    m.add("hood_side_grilles", BLACK, louv)
    m.add("hood_louvres", DARK, [box(2465, 2935, *ys(s, 470, 478 + lv), z, z + rib_h) for s in (1, -1)
                                 for z in range(1200, 1530, pitch)])
    if not m.print_mode:
        m.add("hood_seams", BLACK, [box(x - 5, x + 5, -405, 405, 1500, 2060) for x in (1500,)])
    m.add("hood_handle", BLACK, pipe([(2900, -150, 1795), (2900, -150, 1850), (2900, 150, 1850), (2900, 150, 1795)], r(15)))
    m.add("exhaust_stack", BLACK, cyl(r(58), (1170, -330, 1950), (1170, -330, 3200)),
          cyl(80, (1170, -330, 2040), (1170, -330, 2500)))
    m.add("exhaust_tip", STEEL, cyl(66, (1170, -330, 3170), (1170, -330, 3290)))
    m.add("air_precleaner", BLACK, cyl(90, (1240, 330, 1950), (1240, 330, 2480)))
    m.add("precleaner_cap", DARK, cyl(125, (1240, 330, 2470), (1240, 330, 2540)),
          cone(125, 50, (1240, 330, 2540), (1240, 330, 2600)))

    # front counterweight / bumper with tow jaw
    cw_side = [(3080, 420), (3255, 420), (3300, 470), (3300, 770), (3260, 820), (3080, 820)]
    m.add("counterweight", YELLOW, prism(cw_side, "y", -470, 470))
    m.add("tow_jaw", DARK, cut(box(3280, 3370, -120, 120, 520, 690), box(3300, 3380, -70, 70, 548, 662)))
    m.add("tow_pin", STEEL, cyl(26, (3335, 0, 505), (3335, 0, 715)), cyl(40, (3335, 0, 700), (3335, 0, 725)))

    # ================================================================ loader
    tower = [(CX1 - 10, 720), (1540, 720), (1540, 1250), (1470, 1820), (CX1 - 10, 1820)]
    clevis = [(1110, 1700), (1500, 1700), (1470, 1950)] + arc_pts(A[0], A[1], 170, 20, 160, 10) + [(1110, 1950)]
    for s in (1, -1):
        m.add("loader_tower", YELLOW, prism(tower, "y", *ys(s, 440, 700)),
              prism(clevis, "y", *ys(s, 440, 515)), prism(clevis, "y", *ys(s, 662, 662 + t(38))))

    arm = band([A, M, B], [150, 170, 110])
    lift_lug = lug(L1, 75, [(2590, 1520), (2410, 1520)], -90)
    tilt_lug = lug(T0, 75, [(1610, 1990), (1790, 1990)], 90)
    for s in (1, -1):
        y0, y1 = ys(s, *ARM_Y)
        m.add("lift_arm", YELLOW, prism(arm, "y", y0, y1), cyl(150, P(A, y0), P(A, y1)), cyl(110, P(B, y0), P(B, y1)),
              prism(lift_lug, "y", *ys(s, 545, 635)), prism(tilt_lug, "y", *ys(s, 545, 635)))
    m.add("torque_tube", YELLOW, cyl(75, (3281, -ARM_Y[1], 905), (3281, ARM_Y[1], 905)))

    # tipping levers and bucket links, plates either side of each arm (each plate overlaps the arm side
    # by 2 mm so it fuses to the arm in the print, and is never thinner than a printable wall)
    link_y = ((LINK_IN - t(35), LINK_IN), (LINK_OUT, LINK_OUT + t(35)))
    lever = band([C1, G, C2], [62, 85, 62])
    for s in (1, -1):
        for a, b in link_y:
            yy = ys(s, a, b)
            m.add("tipping_lever", YELLOW, prism(lever, "y", *yy),
                  [cyl(rr_, P(p, yy[0]), P(p, yy[1])) for p, rr_ in ((C1, 62), (G, 85), (C2, 62))])
            m.add("bucket_link", DARK, bar(P(C2, (yy[0] + yy[1]) / 2), P(Q, (yy[0] + yy[1]) / 2), t(35), 100),
                  cyl(55, P(C2, yy[0]), P(C2, yy[1])), cyl(55, P(Q, yy[0]), P(Q, yy[1])))

    # lift and tilt cylinders
    for s in (1, -1):
        y = s * sum(ARM_Y) / 2
        barrel, rod = ram3(P(L0, y), P(L1, y), 82, 48, 0.58, eye=(85, 60), rod_eye=(68, 44))
        m.add("lift_cylinder", BLACK, barrel)
        m.add("lift_cylinder_rod", CHROME, rod)
        barrel, rod = ram3(P(T0, y), P(C1, y), 66, 38, 0.6, eye=(68, 44), rod_eye=(56, 75))
        m.add("tilt_cylinder", BLACK, barrel)
        m.add("tilt_cylinder_rod", CHROME, rod)
    hoses = []
    for s in (1, -1):
        hoses += pipe([(1150, s * 600, 1790), (1450, s * 610, 2110), (1640, s * 600, 2150)], r(16))
        hoses += pipe([(1530, s * 650, 1300), (1700, s * 665, 1235), (1950, s * 665, 1195)], r(16))
    m.add("loader_hoses", BLACK, hoses)
    pins = []
    for s in (1, -1):
        pins += [cyl(62, P(A, s * 430), P(A, s * 712)), cyl(55, P(B, s * 460), P(B, s * 720)),
                 cyl(45, P(L1, s * 530), P(L1, s * 650)), cyl(45, P(T0, s * 530), P(T0, s * 650)),
                 cyl(42, P(C1, s * 470), P(C1, s * 710)), cyl(48, P(G, s * 470), P(G, s * 710)),
                 cyl(40, P(C2, s * 470), P(C2, s * 710)), cyl(40, P(Q, s * 470), P(Q, s * 710))]
    m.add("loader_pins", STEEL, pins)

    # ~1 m3 general-purpose bucket, 2.30 m wide, flat on the ground
    BW = 1150.0
    sh = t(36) / 2
    shell = [(4360, -6 + sh), (3640, -6 + sh), (3568, 62), (3518, 200), (3505, 500), (3520, 790), (3565, 930),
             (3635, 1000), (3800, 1028)]
    side = [(4505, -6), (3640, -6), (3550, 52), (3498, 196), (3485, 500), (3500, 800), (3548, 950), (3622, 1022),
            (3800, 1052), (3845, 1012), (4510, 58)]
    sp = t(28)
    bucket = [prism(band(shell, sh), "y", -BW + 5, BW - 5),
              prism(side, "y", -BW, -BW + sp), prism(side, "y", BW - sp, BW),
              box(3640, 3830, -BW, BW, 1000, 1062)]                                # top edge bar
    for s in (1, -1):
        for a, b in ((470, 515), (665, 710)):
            bucket.append(prism(lug(B, 100, [(3505, 170), (3505, 520)], 180), "y", *ys(s, a, b)))
        for a, b in link_y:
            bucket.append(prism(lug(Q, 62, [(3546, 820), (3546, 980)], 180), "y", *ys(s, a, b)))
    rib = band([(x - 45, z) for x, z in shell[2:7]], 32)
    bucket += [prism(rib, "y", y - 40, y + 40) for y in (-300.0, 300.0)]           # ribs behind the back plate
    m.add("loader_bucket", YELLOW, bucket)
    m.add("cutting_edge", DARK, prism([(4280, -6), (4512, -6), (4512, 14), (4470, 40), (4280, 40)], "y", -BW + 4, BW - 4))
    m.add("edge_bolts", STEEL, [cyl(22, (4370, y, 32), (4370, y, 54)) for y in np.linspace(-1020, 1020, 12)])
    eye = [(3090, 790), (3190, 790), (3170, 885), (3110, 885)]
    m.add("lifting_eyes", YELLOW, [cut(prism(eye, "y", y - t(40) / 2, y + t(40) / 2),
                                        cyl(22, (3140, y - 40, 850), (3140, y + 40, 850))) for y in (-330.0, 330.0)])

    # ================================================================ backhoe
    # bucket outline, local frame: pin at the origin, mouth towards +X with the dipper hanging straight down
    OUT = [(70, 40), (-60, 112)] + bez([(-400, 96), (-505, -330), (-340, -862), (40, -856)], 16) + \
        [(240, -862), (390, -822)]
    SHELL = bez([(-395, 72), (-483, -328), (-326, -840), (40, -836)], 16) + [(240, -841), (385, -803)]
    HEEL, EDGE = np.array([240.0, -862.0]), np.array([390.0, -822.0])
    dv = unit(EDGE - HEEL)
    nv = np.array([-dv[1], dv[0]])
    LB_LOC = np.array([-330.0, 55.0])
    teeth_loc = [[EDGE - 70 * dv, EDGE + 170 * dv, EDGE + 170 * dv + 16 * nv, EDGE - 70 * dv + 72 * nv]]
    bsh = t(36) / 2
    PHI = -math.degrees(math.atan2(dv[1], dv[0]))          # bottom flat on the ground
    polys_loc = [OUT, band(SHELL, bsh)] + teeth_loc
    zmin = min(rot2(p, PHI)[1] for poly in polys_loc for p in poly)
    BZ = -zmin - 12.0                                        # sunk 12 mm into the ground

    F = np.array([-1760.0, 1360.0])                          # boom foot pin
    ud = e2(-85.0)                                           # down the dipper
    nb = np.array([ud[1], -ud[0]])                           # dipper back (away from the machine)
    if nb[0] > 0:
        nb = -nb
    LD, CH = 2000.0, 2775.0                                  # dipper length, boom chord (14 ft dig depth)
    TZ = BZ - LD * ud[1]
    TX = F[0] - math.sqrt(CH ** 2 - (TZ - F[1]) ** 2)
    T = np.array([TX, TZ])                                   # boom tip / dipper pivot
    BK = T + LD * ud                                         # bucket pin
    a1, a2 = e2(125.0), e2(170.0)                            # banana boom: two legs, 45 deg bend
    L1_, L2_ = np.linalg.solve(np.column_stack([a1, a2]), T - F)
    K = F + L1_ * a1                                         # boom knee
    n_up = unit(np.array([a1[1], -a1[0]]) + np.array([a2[1], -a2[0]]))   # convex (upper) side at the knee
    n_dn = -n_up

    def W(p):
        """Bucket local point to world (x, z)."""
        return BK + rot2(p, PHI)

    def Wpoly(poly):
        return [tuple(W(p)) for p in poly]

    Dtop = T - 470 * ud                                      # dipper top, crowd-cylinder pin
    Pl = BK - 300 * ud                                       # side links on the dipper
    Lb = W(LB_LOC)                                           # H-link on the bucket
    J = Pl + 330 * nb - 200 * ud                             # bucket-cylinder rod end
    Cb0 = T - 100 * ud + 230 * nb                            # bucket-cylinder base
    C0 = np.array([-1900.0, 720.0])                          # boom-cylinder base on the swing casting
    Cm1 = K + 275 * n_dn                                     # boom-cylinder rod end under the knee
    Db = K + 265 * n_up                                      # crowd-cylinder base on top of the boom

    # tower lugs and swing pins (kingpost)
    XS_P = -1480.0
    m.add("swing_tower_lugs", YELLOW,
          [cyl(140, (XS_P, 0, z0), (XS_P, 0, z1)) for z0, z1 in ((1500, 1600), (620, 710))],
          [box(XS_P, -1370, -140, 140, z0, z1) for z0, z1 in ((1500, 1600), (620, 710))])
    CAST = [(-1540, 600), (-1540, 1500), (-1650, 1530), (-1790, 1500), (-1890, 1330), (-1990, 980), (-2010, 700),
            (-1930, 590), (-1700, 560)]
    cast = [prism(CAST, "y", -200, 200).intersect(box(-2100, -1500, -210, 210, 500, 1150))]
    cast += [prism(CAST, "y", *ys(s, 128, 205)).intersect(box(-2100, -1500, -210, 210, 1100, 1600)) for s in (1, -1)]
    cast += [cyl(140, (XS_P, 0, z0), (XS_P, 0, z1)) for z0, z1 in ((1405, 1495), (715, 800))]
    cast += [box(-1580, XS_P, -140, 140, z0, z1) for z0, z1 in ((1405, 1495), (715, 800))]
    cast.append(box(-1780, -1540, -330, 330, 520, 612))                         # swing-cylinder ears
    m.add("swing_casting", YELLOW, cast)
    m.add("swing_pins", STEEL, cyl(55, (XS_P, 0, 1380), (XS_P, 0, 1625)), cyl(55, (XS_P, 0, 595), (XS_P, 0, 820)),
          cyl(75, (XS_P, 0, 1600), (XS_P, 0, 1635)), cyl(75, (XS_P, 0, 585), (XS_P, 0, 620)))

    # swing cylinders, frame to the casting ears
    for s in (1, -1):
        barrel, rod = ram3((-870, s * 585, 566), (-1690, s * 268, 566), 64, 36, 0.55, axis=(0, 0, 1),
                           eye=(70, 52), rod_eye=(55, 46))
        m.add("swing_cylinder", BLACK, barrel)
        m.add("swing_cylinder_rod", CHROME, rod)
        m.add("swing_cylinder_mount", DARK, box(-940, -800, *ys(s, 430, 655), 490, 640))

    # boom: curved, box section, foot in the casting clevis
    boom = prism(band([F, K, T], [170, 215, 128]), "y", -125, 125)
    if not m.print_mode:
        boom = cut(boom, cyl(235, P(T, -103), P(T, 103)))                    # clevis round the dipper
    m.add("boom", YELLOW, boom, cyl(165, P(F, -125), P(F, 125)), cyl(128, P(T, -125), P(T, 125)),
          prism(lug(Cm1, 80, [tuple(K - 160 * unit(K - F) + 120 * n_dn), tuple(K + 60 * unit(T - K) + 120 * n_dn)],
                    math.degrees(math.atan2(n_dn[1], n_dn[0]))), "y", -85, 85),
          prism(lug(Db, 78, [tuple(K + 120 * unit(T - K) + 150 * n_up), tuple(K - 180 * unit(K - F) + 150 * n_up)],
                    math.degrees(math.atan2(n_up[1], n_up[0]))), "y", -80, 80))

    # dipper
    dip = prism(band([Dtop, T, BK], [105, 165, 95]), "y", -100, 100)
    cb_lug = lug(Cb0, 70, [tuple(T - 40 * ud + 120 * nb), tuple(T - 200 * ud + 120 * nb)],
                 math.degrees(math.atan2(nb[1], nb[0])))
    m.add("dipper", YELLOW, dip, cyl(105, P(Dtop, -100), P(Dtop, 100)), cyl(98, P(BK, -100), P(BK, 100)),
          prism(cb_lug, "y", -60, 60))

    # backhoe bucket: side plates, wrapper, top plate with ears, teeth
    bw, st = 305.0, t(20)
    bkt = [prism(Wpoly(OUT), "y", -bw, -bw + st), prism(Wpoly(OUT), "y", bw - st, bw),
           prism(Wpoly(band(SHELL, bsh)), "y", -bw + 4, bw - 4),
           prism(Wpoly([(-400, 96), (-60, 112), (70, 40), (40, 10), (-60, 70), (-398, 60)]), "y", -bw + 4, bw - 4)]
    ear = band([LB_LOC, (0.0, 0.0)], 80)
    for s in (1, -1):
        yy = ys(s, 104, 148)
        bkt += [prism(Wpoly(ear), "y", *yy), cyl(98, P(BK, yy[0]), P(BK, yy[1])),
                cyl(80, P(Lb, yy[0]), P(Lb, yy[1]))]
    m.add("backhoe_bucket", DARK, bkt)
    tooth_y = np.linspace(-bw + 70, bw - 70, 4)
    m.add("bucket_teeth", STEEL, [prism(Wpoly(teeth_loc[0]), "y", y - 32, y + 32) for y in tooth_y])
    cutter = Wpoly(band([tuple(EDGE + 10 * dv), (300, -560), (150, -150)], 32))
    m.add("side_cutters", STEEL, [prism(cutter, "y", *ys(s_, bw - 6, bw + t(16))) for s_ in (1, -1)])
    m.add("bucket_edge", STEEL, prism(Wpoly([EDGE - 120 * dv, EDGE + 8 * dv, EDGE + 8 * dv + 28 * nv,
                                               EDGE - 120 * dv + 28 * nv]), "y", -bw, bw))

    # links between the bucket cylinder, dipper and bucket
    links = [bar(P(J, s * 125), P(Pl, s * 125), t(32), 85) for s in (1, -1)]       # side links
    links += [bar(P(J, s * 72), P(Lb, s * 72), t(32), 95) for s in (1, -1)]        # H-link
    links.append(cyl(55, P(J, -60), P(J, 60)))
    m.add("bucket_links", DARK, links)

    # cylinders
    rams = [ram3(P(C0), P(Cm1), 88, 52, 0.56, eye=(92, 80), rod_eye=(72, 70)),      # boom
            ram3(P(Db), P(Dtop), 78, 46, 0.55, eye=(80, 72), rod_eye=(66, 60)),     # dipper (crowd)
            ram3(P(Cb0), P(J), 66, 40, 0.55, eye=(70, 56), rod_eye=(58, 50))]       # bucket
    m.add("backhoe_cylinders", BLACK, [b_ for b_, _ in rams])
    m.add("backhoe_cylinder_rods", CHROME, [r_ for _, r_ in rams])

    bpins = [cyl(70, P(F, -225), P(F, 225)), cyl(62, P(T, -150), P(T, 150)), cyl(58, P(BK, -160), P(BK, 160)),
             cyl(50, P(Lb, -150), P(Lb, 150)), cyl(48, P(Pl, -150), P(Pl, 150)), cyl(45, P(J, -150), P(J, 150)),
             cyl(48, P(C0, -205), P(C0, 205)), cyl(45, P(Cm1, -100), P(Cm1, 100)), cyl(45, P(Db, -95), P(Db, 95)),
             cyl(45, P(Dtop, -105), P(Dtop, 105)), cyl(42, P(Cb0, -75), P(Cb0, 75))]
    m.add("backhoe_pins", STEEL, bpins)

    # hoses up the boom sides to the crowd and bucket cylinders
    hr = r(17)
    hy = 125 + hr - 6
    run = [F + 40 * unit(K - F) + 120 * n_up, K + 60 * n_up, K + 0.55 * (T - K) + 70 * n_up, T + 60 * unit(T - K) + 40 * n_up]
    bh = []
    for s in (1, -1):
        bh += pipe([P(p, s * hy) for p in run], hr)
    m.add("boom_hoses", BLACK, bh)

    # ================================================================ stabilisers
    XS = -1100.0
    S0 = np.array([650.0, 1150.0])                           # leg pivot (|y|, z)
    S1 = np.array([1450.0, 230.0])                           # pad pin
    S2 = np.array([380.0, 1960.0])                           # cylinder base
    du = unit(S1 - S0)
    nu = np.array([-du[1], du[0]])
    if nu[1] < 0:
        nu = -nu
    S3m = S0 + 0.62 * (S1 - S0)
    S3 = S3m + 135 * nu                                      # cylinder rod end
    for s in (1, -1):
        def Q3(p, x=XS):
            return (float(x), float(s * p[0]), float(p[1]))
        m.add("stabiliser_leg", YELLOW, bar(Q3(S0), Q3(S1), 210, 190, up=(1, 0, 0)),
              cyl(112, Q3(S0, XS - 110), Q3(S0, XS + 110)), cyl(95, Q3(S1, XS - 95), Q3(S1, XS + 95)),
              bar(Q3(S3m), Q3(S3), 100, 140, up=(1, 0, 0)))
        m.add("stabiliser_mounts", YELLOW, box(XS - 150, XS + 150, *ys(s, 470, 640), 1030, 1270),
              box(XS - 85, XS + 85, *ys(s, 300, 460), 1650, 2040))
        m.add("stabiliser_pad", DARK, box(XS - 270, XS + 270, *ys(s, S1[0] - 250, S1[0] + 250), -10, 70),
              box(XS - 90, XS + 90, *ys(s, S1[0] - 80, S1[0] + 80), 50, 300))
        m.add("stabiliser_pins", STEEL, cyl(48, Q3(S0, XS - 165), Q3(S0, XS + 165)),
              cyl(45, Q3(S1, XS - 130), Q3(S1, XS + 130)), cyl(40, Q3(S2, XS - 110), Q3(S2, XS + 110)),
              cyl(38, Q3(S3, XS - 95), Q3(S3, XS + 95)))
        barrel, rod = ram3(Q3(S2), Q3(S3), 74, 44, 0.55, axis=(1, 0, 0), eye=(76, 80), rod_eye=(62, 60))
        m.add("stabiliser_cylinder", BLACK, barrel)
        m.add("stabiliser_cylinder_rod", CHROME, rod)
