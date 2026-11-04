"""Truck-mounted vacuum road sweeper, ~6 m3 hopper, on a 2-axle 4x2 cab-over chassis.

A generic, brand-neutral sweeper with the typical proportions of the class (the 16-18 t
truck sweepers that keep quays, stockyard roads and rail sidings clean at bulk terminals):

* chassis: 4x2 cab-over, 4.2 m wheelbase, 315/80R22.5 tyres (~1.05 m OD) on 22.5 in steel
  disc wheels, singles in front, duals behind, 2.5 m over the tyres; frame rails ~0.87 m wide
  with the top at ~1.06 m and a body subframe on top; leaf-sprung front and rear axles, prop
  shaft, differential, rear mudguards with flaps, fuel tank, hydraulic oil tank, battery and
  tool boxes behind the rear axle, rear under-run bar with lamps;
* cab: flat-fronted cab-over day cab, 2.4 m wide, ~1.85 m long, roof at ~3.03 m, plain slatted
  grille (no badge), steel bumper with lamps, windscreen, door windows and a kerb-view window
  low in the nearside (left) door, wipers, sun visor with marker lamps, roof beacon and work
  lamps, main and kerb mirrors, entry steps, grab handles, air-intake snorkel, fleet numbers;
* body (all white, ~6.2 m long): auxiliary engine housing behind the cab with louvred side
  panels, roof radiator grille and exhaust stack; ~2.5 m3 clean-water tank with fill hatch,
  hydrant inlet and sight gauge, plus two saddle tanks under the body between the axles;
  a ~3.8 m long tipping debris hopper (pivots at the rear sill, ~6 m3 usable) with side
  ribs, inspection doors and an orange stripe, the suction fan housing with its outlet grille
  on the hopper roof, and a top-hinged rear door with seal, hydraulic door rams, lock clamps,
  drain valve and an orange/white chevron panel (stripes as separate coloured parts);
* sweeping gear: a ~1.1 m wide suction nozzle (pick-up head) under the body between the axles,
  with rubber flaps, castor wheels, drag arms and a 250 mm suction hose rising into the hopper;
  two ~0.9 m gutter brooms at the front corners behind the front wheels, tilted out and
  forward, each a steel hub plate with a flared bristle ring, hydraulic motor, swing arm,
  hoses and a water jet; a front spray bar under the bumper;
* rear: a ~200 mm wander hose (manual suction hose) on a swivelling boom at the top right of
  the rear, hanging down to its parking cradle on the under-run bar; LED directional arrow bar
  and work lamps over the door, two rear beacons.

Overall ~8.6 m long (bumper to the wander hose), 2.5 m wide over the body and tyres (~2.9 m
over the gutter brooms, ~3.07 m over the mirrors), ~3.2 m high to the top of the beacons.

Millimetres, X forward, Y left, Z up, ground at Z = 0, footprint roughly centred on the origin.
"""

from __future__ import annotations

import math

import cadquery as cq
import numpy as np

from cadkit import (V, Finish, arc_pts, band, bar, box, clip_poly, cone, cut, cyl, mv, pipe, place, prism, rgb, rot,
                    sphere, text)
from finishes import AMBER, BLACK, CHROME, DARK, GALV, GLASS, LED, ORANGE, RED, RUBBER, STEEL, WHITE

ASSET = dict(key="road_sweeper", stem="Vacuum_Road_Sweeper", title="Vacuum Road Sweeper Truck",
             az=40, el=18, size="1200x900")

BODY = WHITE
STRIPE = Finish(rgb("#f26a0d"), rough=0.4)                  # safety orange chevrons and stripe
WHEEL = Finish(rgb("#c9cdd1"), metal=0.6, rough=0.4)        # painted steel disc wheels
GREY = Finish(rgb("#6c7177"), metal=0.6, rough=0.5)         # bumper, grille slats
MOUTH = Finish(rgb("#232528"), rough=0.85)
BRISTLE = Finish(rgb("#e8661a"), rough=0.9)                 # orange poly broom bristles

# ---- running gear
R = 525.0                       # 315/80R22.5, ~1,050 mm OD
ZC = R * (1 - 0.015)            # axle height: tyres sunk 1.5 % for a flat print contact
XF, XR = 2700.0, -1500.0        # front axle, rear axle (4.2 m wheelbase)
F_IN, F_OUT = 935.0, 1250.0     # front tyre faces, |y|
DI, DO = (630.0, 925.0), (955.0, 1250.0)   # rear duals, inner / outer tyre faces, |y|

# ---- frame
RY0, RY1, RZ0, RZ1 = 345.0, 435.0, 760.0, 1060.0
SZ1 = 1220.0                    # top of the body subframe
XFR, XRR = 4000.0, -3930.0      # frame ends

# ---- body
XH = -3900.0                    # hopper rear face
XDO = XH - 65.0                 # rear door outer face
ZH0, ZH1 = 1200.0, 2950.0       # hopper bottom / top
HY = 1230.0                     # hopper half width
ZT1 = 2900.0                    # top of the water tank and engine housing

# ---- gutter brooms
XB, YB = 1560.0, 990.0          # broom centres
TILT_OUT, TILT_FWD = 6.0, 3.0   # degrees

# ---- cab, in the chassis frame with the front axle at x = 0 (shifted by XF):
# plan sections (z, front x, half width, front corner r, rear x, rear corner r)
CAB = [(880, 1450, 1200, 170, -380, 50), (1700, 1432, 1200, 170, -380, 50), (2650, 1322, 1190, 160, -380, 50),
       (2880, 1290, 1170, 150, -375, 50), (3000, 1220, 1110, 110, -340, 50), (3030, 1120, 1020, 60, -270, 40)]
CAB_IN = [(1130, 1385, 1150, 130, -330, 20), (1700, 1382, 1150, 130, -330, 20), (2650, 1272, 1140, 120, -330, 20),
          (2900, 1222, 1110, 100, -320, 20)]
WS_Z0, WS_Z1, WS_Y = 1740.0, 2610.0, 1010.0          # windscreen opening


def xfr(z):
    """Cab front face (on the centre line, cab frame) at height z."""
    zs, xs = zip(*[(c[0], c[1]) for c in CAB])
    return float(np.interp(z, zs, xs))


def hw(z):
    """Cab half width at height z."""
    zs, ys = zip(*[(c[0], c[2]) for c in CAB])
    return float(np.interp(z, zs, ys))


def rrect(x0, x1, hy, rf, rr, z, n=6):
    pts = (arc_pts(x1 - rf, hy - rf, rf, 0, 90, n) + arc_pts(x0 + rr, hy - rr, rr, 90, 180, n)
           + arc_pts(x0 + rr, -hy + rr, rr, 180, 270, n) + arc_pts(x1 - rf, -hy + rf, rf, 270, 360, n))
    return [V(x, y, z) for x, y in pts]


def loft_sections(secs):
    wires = [cq.Wire.makePolygon(rrect(x0, x1, hy, rf, rr, z), close=True) for z, x1, hy, rf, x0, rr in secs]
    return cq.Solid.makeLoft(wires, ruled=True)


def side_bar(x0, z0, x1, z1, s, w, h):
    """A strip lying on the cab side between (x0, z0) and (x1, z1), standing h/2 proud of it."""
    return bar((x0, s * hw(z0), z0), (x1, s * hw(z1), z1), w, h, up=(0, s, 0))


def ngon(cx, cz, r, n):
    return [(cx + r * math.cos(2 * math.pi * (k + 0.5) / n), cz + r * math.sin(2 * math.pi * (k + 0.5) / n))
            for k in range(n)]


def gear(xc, zc, ro, ri, n, phase, frac=0.45):
    """(x, z) outline of a lug ring: n teeth out to ro, valleys at ri."""
    pts, p = [], 360.0 / n
    for k in range(n):
        a0 = phase + k * p
        for a, r in ((a0, ri), (a0, ro), (a0 + frac * p, ro), (a0 + frac * p, ri)):
            pts.append((xc + r * math.cos(math.radians(a)), zc + r * math.sin(math.radians(a))))
    return pts


def rbox(x0, x1, y0, y1, z0, z1, r, axis="x", n=3):
    """A box with the four edges along `axis` rounded (radius r), as a light extruded profile."""
    if axis == "x":
        u0, u1, v0, v1, a0, a1 = y0, y1, z0, z1, x0, x1
    else:
        u0, u1, v0, v1, a0, a1 = x0, x1, z0, z1, y0, y1
    pts = (arc_pts(u1 - r, v0 + r, r, -90, 0, n) + arc_pts(u1 - r, v1 - r, r, 0, 90, n)
           + arc_pts(u0 + r, v1 - r, r, 90, 180, n) + arc_pts(u0 + r, v0 + r, r, 180, 270, n))
    return prism(pts, axis, a0, a1)


def rot_pt(p, deg, axis):
    """Rotate a point about an axis through the origin (right hand), as Shape.rotate does."""
    a = math.radians(deg)
    k = np.asarray(axis, float) / np.linalg.norm(axis)
    p = np.asarray(p, float)
    return p * math.cos(a) + np.cross(k, p) * math.sin(a) + k * np.dot(k, p) * (1 - math.cos(a))


class Parts:
    """Collects shapes by part name (so left/right pairs end up as one part), optionally shifted in x."""

    def __init__(self, m, dx=0.0, store=None):
        self.m, self.dx = m, dx
        self.order = {} if store is None else store
        self.print_mode = m.print_mode
        self.t, self.r = m.t, m.r

    def shifted(self, dx):
        return Parts(self.m, self.dx + dx, self.order)

    def add(self, name, finish, *shapes):
        flat = []

        def walk(items):
            for s in items:
                if isinstance(s, (list, tuple)):
                    walk(s)
                elif s is not None:
                    flat.append(mv(s, self.dx) if self.dx else s)
        walk(shapes)
        self.order.setdefault(name, (finish, []))[1].extend(flat)

    def flush(self):
        for name, (finish, shapes) in self.order.items():
            if shapes:
                self.m.add(name, finish, shapes)


# =============================================================================== wheels

def wheel(m, parts, xc, s, y_in, y_out, kind):
    """kind 'steer' (rib tread, rim), 'outer' (lug tread, rim) or 'inner' (lug tread, no rim)."""
    def c(y):
        return (xc, s * y, ZC)
    D = 6.0 if kind == "inner" else 18.0
    body = cyl(R - D, c(y_in + 30), c(y_out - 30)).fuse(
        cone(R - D - 50, R - D, c(y_in), c(y_in + 30)), cone(R - D, R - D - 50, c(y_out - 30), c(y_out)))
    if kind != "inner":
        body = cut(body, cyl(292, c(y_out + 5), c(y_out - 130)))
    bore = cyl(R - D - 12, c(y_in - 5), c(y_out + 5))
    tread = []
    if kind == "steer":
        w = (y_out - y_in - 60 - 3 * 14) / 4
        for k in range(4):
            a = y_in + 30 + k * (w + 14)
            rib = cyl(R, c(a), c(a + w))
            tread.append(cut(rib, bore) if k == 3 else rib)
    elif kind == "outer":
        n = 24
        p = 360.0 / n
        ym, half = (y_in + y_out) / 2, (y_out - y_in) / 2
        for (a, b), ph in (((y_in + 26, ym + 0.12 * half), 270 - 0.225 * p),
                           ((ym - 0.12 * half, y_out - 26), 270 + 0.275 * p)):
            y0, y1 = sorted((s * a, s * b))
            ring = prism(gear(xc, ZC, R, R - D - 4, n, ph), "y", y0, y1)
            tread.append(cut(ring, bore) if b > y_out - 140 else ring)
    parts["tyres"] += [body] + tread
    if kind == "inner":
        return
    yf = y_out
    parts["rims"].append(cut(cyl(300, c(yf - 135), c(yf - 8)), cyl(300 - m.t(24), c(yf - 100), c(yf + 1))))
    y0, y1 = sorted((s * (yf - 97), s * (yf - 104)))
    parts["rim_holes"] += [prism(ngon(xc + 205 * math.cos(a), ZC + 205 * math.sin(a), 34, 8), "y", y0, y1)
                           for a in np.linspace(0.3, 2 * math.pi + 0.3, 8, endpoint=False)]
    hub = 70.0 if kind == "steer" else 45.0
    parts["hubs"] += [cyl(130, c(yf - 104), c(yf - 101 + hub)), cone(118, 60, c(yf - 101 + hub), c(yf - 101 + hub + 35))]
    for a in np.linspace(0, 2 * math.pi, 10, endpoint=False):
        x, z = xc + 168 * math.cos(a), ZC + 168 * math.sin(a)
        parts["nuts"].append(prism(ngon(x, z, m.r(21), 6), "y", *sorted((s * (yf - 112), s * (yf - 70)))))


# =============================================================================== build

def build(model):
    m = Parts(model)
    running_gear(m)
    cab(m.shifted(XF))
    body(m)
    hopper(m)
    sweeping_gear(m)
    rear(m)
    m.flush()


def running_gear(m):
    parts = {k: [] for k in ("tyres", "rims", "rim_holes", "hubs", "nuts")}
    for s in (1, -1):
        wheel(m, parts, XF, s, F_IN, F_OUT, "steer")
        wheel(m, parts, XR, s, *DI, "inner")
        wheel(m, parts, XR, s, *DO, "outer")
    m.add("tyres", RUBBER, parts["tyres"])
    m.add("wheel_rims", WHEEL, parts["rims"])
    m.add("rim_hand_holes", MOUTH, parts["rim_holes"])
    m.add("wheel_hubs", DARK, parts["hubs"])
    m.add("wheel_nuts", STEEL, parts["nuts"])

    # front axle: dropped beam, kingpins, tie rod, leaf springs
    fa = [box(XF - 70, XF + 70, -880, 880, 430, 560)]
    fa += [cyl(90, (XF, s * 860, 410), (XF, s * 860, 640)) for s in (1, -1)]
    fa += [cyl(165, (XF, s * 830, ZC), (XF, s * 950, ZC)) for s in (1, -1)]
    fa += [bar((XF, s * 850, 470), (XF - 280, s * 790, 470), 50, 50) for s in (1, -1)]
    m.add("axles", DARK, fa)
    m.add("tie_rod", BLACK, cyl(m.r(28), (XF - 280, -800, 470), (XF - 280, 800, 470)))
    springs, hangers = [], []
    for s in (1, -1):
        y0, y1 = sorted((s * 440, s * 530))
        springs.append(prism(band([(XF - 760, 720), (XF - 380, 625), (XF, 595), (XF + 380, 625), (XF + 760, 720)], 38),
                             "y", y0, y1))
        hangers += [box(x - 55, x + 55, s * 425, s * 545, 680, 790) for x in (XF - 760, XF + 760)]
        hangers.append(box(XF - 110, XF + 110, s * 425, s * 545, 545, 580))
        # rear axle springs: under-slung beside the rails
        y0, y1 = sorted((s * 465, s * 575))
        springs.append(prism(band([(XR - 760, 765), (XR - 380, 700), (XR, 680), (XR + 380, 700), (XR + 760, 765)],
                                  [34, 44, 50, 44, 34]), "y", y0, y1))
        hangers += [box(x - 60, x + 60, s * 425, s * 590, 700, 800) for x in (XR - 760, XR + 760)]
        hangers.append(box(XR - 120, XR + 120, s * 455, s * 585, ZC + 100, ZC + 180))
    m.add("springs", BLACK, springs)
    m.add("spring_hangers", DARK, hangers)

    # rear axle, differential, prop shaft
    axle = [cyl(140, (XR, -600, ZC), (XR, 600, ZC)), cyl(255, (XR, -170, ZC), (XR, 170, ZC)),
            cyl(200, (XR - 60, 0, ZC), (XR + 200, 0, ZC + 20)),
            cyl(150, (XR, 0, ZC), (XR + 360, 0, ZC + 40))]
    axle += [cyl(230, (XR, s * 560, ZC), (XR, s * 1140, ZC)) for s in (1, -1)]
    m.add("axles", DARK, axle)
    m.add("prop_shaft", DARK, cyl(m.r(55), (XF - 950, 0, 720), (XR + 360, 0, ZC + 40)),
          [cyl(m.r(70), (p[0] - 50, 0, p[2]), (p[0] + 50, 0, p[2])) for p in ((XF - 950, 0, 720), (XR + 360, 0, ZC + 40))],
          box(150, 300, -110, 110, 620, RZ0 + 20))

    # frame and body subframe
    rails = [box(XRR, XFR, s * RY0, s * RY1, RZ0, RZ1) for s in (1, -1)]
    rails += [box(x - 40, x + 40, -RY1, RY1, RZ0 + 40, RZ1 - 40) for x in (XFR - 40, 1500, 200, XR, -3000)]
    rails.append(box(XRR, XRR + 60, -RY1, RY1, RZ0, RZ1))
    m.add("frame_rails", BLACK, rails)
    sub = [box(XRR + 20, 2200, s * RY0, s * RY1, RZ1 - 5, SZ1) for s in (1, -1)]
    sub += [box(x - 50, x + 50, -RY1 - 60, RY1 + 60, RZ1 + 20, SZ1 - 10) for x in (2100, 900, -400, -2000, -3600)]
    m.add("subframe", BLACK, sub)
    m.add("engine", DARK, box(XF - 380, XF + 950, -360, 360, 480, 1100), box(XF - 960, XF - 370, -260, 260, 560, 960))

    # rear mudguards and flaps
    path = arc_pts(XR, ZC, 615, 12, 168, 18)
    for s in (1, -1):
        y0, y1 = sorted((s * 600, s * 1275))
        m.add("rear_mudguards", BLACK, prism(band(path, m.t(12) / 2), "y", y0, y1))
        m.add("mudguard_brackets", DARK, [box(x - 40, x + 40, *sorted((s * 425, s * 720)), 1050, ZC + 618)
                                          for x in (XR - 330, XR + 330)])
        xe = XR + 615 * math.cos(math.radians(168))
        m.add("mud_flaps", RUBBER, box(xe - m.t(22), xe + 5, *sorted((s * 640, s * 1265)), 280, ZC + 150),
              box(XF - 695 - m.t(20), XF - 695, *sorted((s * 960, s * 1230)), 300, 1000))
        m.add("mud_flap_hangers", DARK, box(xe - 60, xe + 10, *sorted((s * 420, s * 1265)), ZC + 120, ZC + 200),
              box(XF - 735, XF - 680, *sorted((s * 425, s * 1230)), 960, 1010))
        m.add("side_markers", AMBER, [box(x - 45, x + 45, *sorted((s * 1272, s * 1284)), ZC + 560, ZC + 600)
                                      for x in (XR + 250, XR - 250)])

    # tanks and boxes behind the rear axle
    m.add("fuel_tank", CHROME, rbox(-3300, -2250, 480, 1080, 560, 1040, 80))
    m.add("tank_straps", BLACK, [box(x, x + 50, 470, 1090, 550, 1050) for x in (-3100, -2500)],
          [box(x - 10, x + 60, 425, 490, 880, 1000) for x in (-3100, -2500)],
          [box(x, x + 50, -1090, -470, 590, 1160) for x in (-3000, -2500)])
    m.add("fuel_cap", BLACK, cyl(65, (-2400, 950, 1030), (-2400, 950, 1090)))
    m.add("tool_box", GALV, box(-3900, -3400, 470, 1150, 640, 1150))
    m.add("tool_box_lid", BLACK, box(-3880, -3420, 1140, 1160, 1080, 1110),
          box(-3700, -3600, 1140, 1165, 980, 1060))
    m.add("hydraulic_tank", DARK, box(-3050, -2200, -1080, -480, 600, 1150))
    m.add("hydraulic_tank_gauge", GLASS, box(-2900, -2700, -1092, -1075, 750, 1050))
    m.add("hydraulic_tank_cap", GALV, cyl(60, (-2400, -800, 1140), (-2400, -800, 1185)))
    m.add("battery_box", BLACK, box(-3900, -3250, -1100, -470, 640, 1020), box(-3920, -3230, -1115, -460, 1010, 1045))
    m.add("box_brackets", DARK, [box(x - 40, x + 40, *sorted((s * 425, s * 500)), 700, 900)
                                 for x in (-3700, -3500, -2850, -2400) for s in (1, -1)])


def cab(m):
    """The cab-over cab, drawn with the front axle at x = 0 (m is shifted by XF)."""
    hr = m.r(18)
    arch = [cyl(650, (0, s * 700, ZC), (0, s * 1400, ZC)) for s in (1, -1)]
    shell = loft_sections(CAB)
    if m.print_mode:
        shell = cut(shell, *arch)
    else:
        win = [prism([(380, 1880), (xfr(1880) - 230, 1880), (xfr(2600) - 230, 2600), (380, 2600)], "y",
                     s * 1080, s * 1300) for s in (1, -1)]
        kerb = prism([(470, 1150), (930, 1150), (930, 1560), (470, 1560)], "y", 1080, 1300)
        ws = box(1150, 1600, -WS_Y, WS_Y, WS_Z0, WS_Z1)
        shell = cut(shell, loft_sections(CAB_IN), *arch, *win, kerb, ws)
        m.add("dash", DARK, box(1130, 1390, -1145, 1145, 1120, 1720), box(-340, 1150, -340, 340, 1120, 1420))
        m.add("seats", BLACK, [box(250, 760, y - 260, y + 260, 1120, 1580) for y in (600.0, -600.0)],
              [box(150, 300, y - 260, y + 260, 1550, 2300) for y in (600.0, -600.0)])
        m.add("steering_wheel", BLACK, cut(cyl(220, (1000, 600, 2000), (1022, 600, 2040)),
                                           cyl(190, (990, 600, 1990), (1032, 600, 2050))),
              cyl(35, (1000, 600, 2000), (1250, 600, 1700)))
    m.add("cab", BODY, shell)

    for s in (1, -1):
        y0, y1 = sorted((s * 1150, s * 1215))
        m.add("front_fenders", BLACK, prism(band(arc_pts(0, ZC, 680, 14, 166, 28), 30), "y", y0, y1))
        y0, y1 = sorted((s * 700, s * 1180))
        m.add("arch_liners", BLACK, prism(band(arc_pts(0, ZC, 650, 18, 162, 24), m.t(16) / 2), "y", y0, y1),
              prism(clip_poly(arc_pts(0, ZC, 655, 0, 180, 24), -700, 700, 880, 2000), "y", *sorted((s * 692, s * 712))))

    # windscreen, rubber, wipers
    d = np.array([xfr(WS_Z1) - xfr(WS_Z0), 0.0, WS_Z1 - WS_Z0])
    d /= np.linalg.norm(d)
    nrm = (float(d[2]), 0.0, float(-d[0]))
    g = m.t(12)
    zg0, zg1 = WS_Z0 - 15, WS_Z1 + 15
    m.add("windows", GLASS, bar((xfr(zg0), 0, zg0), (xfr(zg1), 0, zg1), 2 * (WS_Y + 25), g, up=nrm))
    fr = m.t(18)
    frame = [bar((xfr(z), -WS_Y - 40, z), (xfr(z), WS_Y + 40, z), 50, fr, up=nrm) for z in (WS_Z0 - 10, WS_Z1 + 10)]
    frame += [bar((xfr(WS_Z0 - 30), y, WS_Z0 - 30), (xfr(WS_Z1 + 30), y, WS_Z1 + 30), 50, fr, up=nrm)
              for y in (-WS_Y - 15, WS_Y + 15)]
    m.add("window_rubbers", BLACK, frame)
    wipers = []
    o = np.array(nrm) * (g / 2 + 6)
    for y0, y1 in ((960.0, 140.0), (-80.0, -900.0)):
        za, zb = WS_Z0 + 25, WS_Z0 + 55
        wipers.append(bar(np.array((xfr(za), y0, za)) + o, np.array((xfr(zb), y1, zb)) + o, m.t(22), m.t(16), up=nrm))
        wipers.append(cyl(m.r(22), np.array((xfr(za), y0, za)) - o, np.array((xfr(za), y0, za)) + 1.6 * o))
    m.add("wipers", BLACK, wipers)

    for s in (1, -1):
        def xw(z):
            return xfr(z) - 230
        pane = [(360, 1860), (xw(1860) + 20, 1860), (xw(2620) + 20, 2620), (360, 2620)]
        y0, y1 = sorted((s * 1182, s * (1182 + max(m.t(22), 22))))
        m.add("windows", GLASS, prism(pane, "y", y0, y1))
        fr = m.t(14)
        rub = [side_bar(360, 1880, xw(1880), 1880, s, 44, fr), side_bar(360, 2600, xw(2600), 2600, s, 44, fr),
               side_bar(380, 1860, 380, 2620, s, 44, fr), side_bar(xw(1860), 1860, xw(2620), 2620, s, 44, fr)]
        m.add("window_rubbers", BLACK, rub)
        if s > 0:   # kerb-view window low in the nearside door, so the driver can see the gutter broom
            m.add("windows", GLASS, prism([(450, 1130), (950, 1130), (950, 1580), (450, 1580)], "y",
                                          1182, 1182 + max(m.t(22), 22)))
            m.add("window_rubbers", BLACK, side_bar(450, 1140, 950, 1140, s, 40, fr), side_bar(450, 1570, 950, 1570, s, 40, fr),
                  side_bar(460, 1130, 460, 1580, s, 40, fr), side_bar(940, 1130, 940, 1580, s, 40, fr))
        sw, sh = m.t(14), m.t(20)
        zk = (1130.0, 1700.0, 2650.0, 2700.0)

        def xd(z):
            return float(np.interp(z, (1130.0, 2700.0), (xfr(1130) - 190, xfr(2700) - 180)))
        seams = [side_bar(330, z0, 330, z1, s, sw, sh) for z0, z1 in zip(zk, zk[1:])]
        seams += [side_bar(xd(z0), z0, xd(z1), z1, s, sw, sh) for z0, z1 in zip(zk, zk[1:])]
        seams.append(side_bar(330 - sw / 2, 1130, xd(1130) + sw / 2, 1130, s, sw, sh))
        m.add("door_seams", BLACK, seams)
        m.add("door_handles", CHROME, side_bar(420, 1700, 560, 1700, s, 40, m.t(24)))
        m.add("door_hinges", BLACK, [side_bar(xfr(z) - 200, z, xfr(z) - 160, z, s, 100, m.t(30)) for z in (1350, 2350)])
        ya, yb = s * (hw(1500) - 5), s * (hw(1500) + 55)
        m.add("grab_handles", CHROME, pipe([(xfr(1300) - 120, ya, 1300), (xfr(1300) - 120, yb, 1300),
                                            (xfr(2200) - 120, yb, 2200), (xfr(2200) - 120, ya, 2200)], hr, False),
              pipe([(250, ya, 1350), (250, yb, 1350), (250, yb, 2300), (250, ya, 2300)], hr, False))
        num = text("RS 14", 120, m.t(10) + 6, (790, s * (hw(1665) - 4), 1665), (-s, 0, 0), (0, s, 0))
        m.add("fleet_numbers", BLACK, num)
        m.add("side_repeaters", AMBER, side_bar(1180, 1250, 1290, 1250, s, 45, m.t(16)))
        # entry steps ahead of the front wheel
        y0, y1 = sorted((s * 960, s * 1205))
        m.add("step_frames", DARK, box(760, 760 + m.t(35), y0, y1, 400, 900), box(1300 - m.t(35), 1300, y0, y1, 400, 900),
              box(760, 1300, *sorted((s * 960, s * (960 + m.t(35)))), 400, 900))
        y0, y1 = sorted((s * 980, s * 1218))
        m.add("step_treads", GALV, box(790, 1270, y0, y1, 420, 460), box(790, 1270, y0, y1, 760, 800))

    # front: grille, bumper, lamps, visor, mirrors
    m.add("grille", BLACK, bar((xfr(1060), 0, 1060), (xfr(1620), 0, 1620), 1700, m.t(24), up=(1, 0, 0)))
    m.add("grille_slats", GREY, [box(xfr(z) + 6, xfr(z) + 6 + m.t(14), -800, 800, z - 20, z + 20)
                                 for z in np.arange(1120, 1600, 78)])
    m.add("bumper", GREY, rbox(1370, 1545, -1215, 1215, 440, 905, 40, "y"))
    m.add("bumper_valance", BLACK, rbox(1380, 1535, -1185, 1185, 360, 470, 25, "y"))
    for s in (1, -1):
        y0, y1 = sorted((s * 700, s * 1150))
        m.add("lamp_housings", BLACK, box(1540, 1554, y0, y1, 660, 860))
        m.add("headlights", LED, [cyl(70, (1548, s * y, 760), (1561, s * y, 760)) for y in (790.0, 950.0)])
        m.add("headlight_bezels", CHROME, [cyl(82, (1546, s * y, 760), (1556, s * y, 760)) for y in (790.0, 950.0)])
        m.add("indicators", AMBER, box(1549, 1560, *sorted((s * 1050, s * 1135)), 690, 830))
    m.add("tow_recess", BLACK, box(1538, 1549, -120, 120, 445, 600))

    zv = 2690.0
    xv = xfr(zv)
    m.add("sun_visor", BODY, prism([(xv - 40, 2650), (xv + 190, 2690), (xv + 190, 2690 + m.t(35)), (xfr(2790) - 40, 2790)],
                                   "y", -1120, 1120))
    m.add("marker_lamps", AMBER, [box(xv + 120, xv + 175, y - 40, y + 40, 2715, 2752) for y in (-900, -300, 300, 900)])
    # roof: beacon and a pair of forward work lamps
    m.add("beacon_bases", BLACK, cyl(95, (-80, 0, 3020), (-80, 0, 3075)))
    m.add("beacons", AMBER, cyl(78, (-80, 0, 3070), (-80, 0, 3150)), cone(78, 35, (-80, 0, 3149), (-80, 0, 3195)))
    for y in (650.0, -650.0):
        m.add("work_lamp_housings", BLACK, box(700, 820, y - 90, y + 90, 3015, 3130), box(720, 760, y - 20, y + 20, 3000, 3030))
        m.add("work_lamp_lenses", LED, box(815, 830, y - 75, y + 75, 3028, 3117))

    for s in (1, -1):
        xm, ym = 1300.0, s * 1440
        m.add("mirror_arms", BLACK, pipe([(1150, s * (hw(2450) - 25), 2450), (xm, ym, 2470)], hr),
              pipe([(1150, s * (hw(1850) - 25), 1850), (xm, ym, 1850)], hr),
              cyl(hr, (xm, ym, 1820), (xm, ym, 2500)))
        y0, y1 = sorted((s * 1365, s * 1535))
        m.add("mirror_heads", BLACK, box(xm - 35, xm + 60, y0, y1, 2060, 2470), box(xm - 35, xm + 60, y0, y1, 1830, 2020))
        y0, y1 = sorted((s * 1378, s * 1522))
        m.add("mirror_glass", CHROME, box(xm - 47, xm - 30, y0, y1, 2075, 2455), box(xm - 47, xm - 30, y0, y1, 1845, 2005))
    # kerb mirror over the nearside of the windscreen
    m.add("mirror_arms", BLACK, pipe([(1080, 950, 3005), (1340, 1000, 3090), (1480, 1000, 2990)], hr))
    m.add("mirror_heads", BLACK, box(1440, 1540, 880, 1120, 2850, 3010))
    m.add("mirror_glass", CHROME, box(1430, 1450, 895, 1105, 2865, 2995))

    # air intake snorkel and exhaust silencer behind the cab
    m.add("air_intake", BLACK, cyl(110, (-470, -900, 1300), (-470, -900, 3060)),
          cyl(140, (-470, -900, 3050), (-470, -900, 3120)), cone(140, 60, (-470, -900, 3120), (-470, -900, 3180)),
          [box(-500, -350, -930, -870, z - 30, z + 30) for z in (1700, 2700)])
    m.add("exhaust", BLACK, cyl(200, (-1500, -700, 760), (-750, -700, 760)),
          box(-1400, -850, -560, -430, 760, 840), cyl(m.r(60), (-1500, -700, 760), (-1700, -900, 520)))

    # front spray bar under the bumper
    m.add("spray_bar", GALV, cyl(m.r(32), (1500, -1150, 340), (1500, 1150, 340)),
          [box(1470, 1530, y - 25, y + 25, 330, 380) for y in (-900, 0, 900)])
    m.add("spray_nozzles", BLACK, [bar((1500, y, 340), (1590, y, 295), m.t(40), m.t(40)) for y in np.linspace(-1050, 1050, 8)])


def body(m):
    # ---------------------------------------------------- auxiliary engine housing
    m.add("engine_housing", BODY, rbox(950, 2180, -1240, 1240, ZH0 - 5, ZT1, 60))
    for s in (1, -1):
        y0, y1 = sorted((s * 1234, s * 1247))
        m.add("louvre_panels", BLACK, box(1090, 2060, y0, y1, 1640, 2700))
        y0, y1 = sorted((s * 1243, s * 1258))
        m.add("louvre_slats", BODY, [box(1110, 2040, y0, y1, z, z + 34) for z in np.arange(1665, 2660, 64)])
        # access door seams and handles
        y0, y1 = sorted((s * 1236, s * 1250))
        m.add("body_seams", BLACK, box(1030, 1050, y0, y1, 1280, 2820), box(2090, 2110, y0, y1, 1280, 2820))
        y0, y1 = sorted((s * 1240, s * (1240 + max(m.t(30), 30))))
        m.add("body_handles", CHROME, box(1990, 2040, y0, y1, 1450, 1560))
    m.add("radiator_grille", BLACK, box(1300, 2030, -900, 900, ZT1 - 20, ZT1 + 15))
    m.add("radiator_slats", BODY, [box(1320, 2010, y - 22, y + 22, ZT1 + 5, ZT1 + 30) for y in np.arange(-840, 841, 105)])
    m.add("aux_exhaust", BLACK, cyl(65, (1150, -1000, ZT1 - 20), (1150, -1000, 3150)),
          cyl(80, (1150, -1000, 2930), (1150, -1000, 3020)))
    m.add("aux_exhaust_tip", CHROME, cone(65, 55, (1150, -1000, 3140), (1150, -1000, 3200)))

    # ---------------------------------------------------- water tank
    m.add("water_tank", BODY, rbox(-280, 990, -1235, 1235, ZH0 + 10, ZT1 - 10, 60))
    m.add("fill_hatch", GALV, cyl(220, (350, 550, ZT1 - 20), (350, 550, ZT1 + 45)),
          cyl(150, (350, 550, ZT1 + 40), (350, 550, ZT1 + 70)))
    m.add("fill_hatch_clamps", BLACK, [box(560, 610, y - 25, y + 25, ZT1 + 10, ZT1 + 60) for y in (480, 620)],
          box(70, 140, 450, 650, ZT1 - 10, ZT1 + 55))
    m.add("hydrant_inlet", GALV, cyl(m.r(55), (500, 1225, 1700), (500, 1330, 1700)),
          cyl(80, (500, 1300, 1700), (500, 1340, 1700)))
    m.add("hydrant_cap", BLACK, cyl(70, (500, 1335, 1700), (500, 1370, 1700)))
    m.add("sight_gauge", GLASS, box(870, 910, 1228, 1252, 1500, 2700))
    m.add("sight_gauge_guard", GALV, [box(850, 930, 1225, 1258, z - 25, z + 25) for z in (1480, 2100, 2720)])
    m.add("drain_valve", GALV, cyl(m.r(40), (350, -1100, ZH0 + 40), (350, -1100, 1050)))

    # orange stripe and side markers along the whole body
    for s in (1, -1):
        y0, y1 = sorted((s * 1224, s * 1237))
        stripe = [box(XH + 90, -310, y0, y1, 1360, 1500), box(-215, 925, *sorted((s * 1229, s * 1242)), 1360, 1500)]
        y0, y1 = sorted((s * 1234, s * 1247))
        stripe.append(box(1015, 2115, y0, y1, 1360, 1500))
        m.add("side_stripes", STRIPE, stripe)
        m.add("side_markers", AMBER, [box(x - 45, x + 45, *sorted((s * 1225, s * 1240)), 1290, 1335)
                                      for x in (XH + 200, -2000, 400, 1600)])
    # broom work lamps under the engine housing, aimed at the brooms
    for s in (1, -1):
        y0, y1 = sorted((s * 1080, s * 1200))
        m.add("work_lamp_housings", BLACK, box(1240, 1360, y0, y1, 1090, 1215))
        y0, y1 = sorted((s * 1095, s * 1185))
        m.add("work_lamp_lenses", LED, box(1355, 1370, y0, y1, 1105, 1195))

    # saddle tanks under the body between the axles (the right one shortened round the suction hose)
    for s, x0 in ((1, -800.0), (-1, 220.0)):
        y0, y1 = sorted((s * 640, s * 1235))
        m.add("saddle_tanks", BODY, rbox(x0, 980, y0, y1, 640, 1180, 50))
        m.add("tank_straps", BLACK, [box(x, x + 50, *sorted((s * 630, s * 1245)), 630, 1190)
                                     for x in ((x0 + 200, 780) if s > 0 else (420, 780))])
        m.add("box_brackets", DARK, [box(x - 40, x + 40, *sorted((s * 425, s * 660)), 900, 1080)
                                     for x in ((x0 + 300, 700) if s > 0 else (500, 800))])


def hopper(m):
    shell = rbox(XH, -200, -HY, HY, ZH0, ZH1, 80)
    m.add("hopper", BODY, shell)
    # side ribs, inspection doors
    for s in (1, -1):
        y0, y1 = sorted((s * (HY - 6), s * (HY + 22)))
        m.add("hopper_ribs", BODY, [box(x - 40, x + 40, y0, y1, 1540, ZH1 - 90) for x in (-3300, -2450, -900)],
              box(XH + 120, -320, y0, y1, 2780, 2840))
        y0, y1 = sorted((s * (HY - 4), s * (HY + 10)))
        m.add("body_seams", BLACK, box(-2150, -2130, y0, y1, 1580, 2560), box(-1270, -1250, y0, y1, 1580, 2560),
              box(-2150, -1250, y0, y1, 1580, 1600), box(-2150, -1250, y0, y1, 2540, 2560))
        y0, y1 = sorted((s * HY, s * (HY + max(m.t(30), 30))))
        m.add("body_handles", CHROME, [box(-1400, -1330, y0, y1, z - 50, z + 50) for z in (1800, 2300)])
        m.add("door_hinges", BLACK, [box(-2190, -2120, *sorted((s * (HY - 4), s * (HY + 26))), z - 60, z + 60)
                                     for z in (1750, 2380)])
    # rear pivot of the tipping hopper
    m.add("hopper_pivot", DARK, [box(XH + 20, XH + 200, *sorted((s * 330, s * 450)), RZ1 + 10, ZH0 + 70)
                                 for s in (1, -1)])
    m.add("pivot_pins", STEEL, cyl(48, (XH + 110, -520, ZH0 - 20), (XH + 110, 520, ZH0 - 20)))

    # suction fan housing on the hopper roof with its outlet grille
    fx, fy = -900.0, -480.0
    m.add("fan_housing", BODY, cyl(440, (fx, fy, ZH1 - 20), (fx, fy, 3060)))
    m.add("fan_outlet", BLACK, cyl(400, (fx, fy, 3040), (fx, fy, 3075)))
    m.add("fan_grille", GALV, [box(fx - math.sqrt(400 ** 2 - (abs(d) + 18) ** 2) + 12,
                                   fx + math.sqrt(400 ** 2 - (abs(d) + 18) ** 2) - 12,
                                   fy + d - 18, fy + d + 18, 3062, 3092) for d in np.arange(-315, 316, 90)])
    m.add("fan_drive_cover", BODY, rbox(-520, -230, -900, -100, ZH1 - 20, 3030, 30))
    # top handrail beside the fan for service access
    rr = m.r(18)
    m.add("roof_rail", GALV, pipe([(-2600, 1100, ZH1 - 10), (-2600, 1100, 3180), (-600, 1100, 3180),
                                   (-600, 1100, ZH1 - 10)], rr))


def chevron(c, half, w=1400.0):
    """(y, z) outline of an upward-pointing 45 deg chevron stripe with its apex on the centre line at z = c."""
    return band([(-w, c - w), (0.0, c), (w, c - w)], half)


def rear(m):
    # rear door, top hinged, with seal, rams, clamps and drain
    m.add("rear_door", BODY, box(XDO, XH + 10, -1205, 1205, ZH0 + 90, ZH1 - 15))
    m.add("door_seal", BLACK, cut(box(XH - 5, XH + 8, -1222, 1222, ZH0 + 72, ZH1 - 5),
                                  box(XH - 10, XH + 20, -1190, 1190, ZH0 + 105, ZH1 - 35)))
    knuckles = [cyl(45, (XDO + 20, y0, ZH1 + 5), (XDO + 20, y1, ZH1 + 5))
                for y0, y1 in ((-1100, -880), (-320, -100), (100, 320), (880, 1100))]
    leaves = [box(XDO + 10, XH + 200, y0, y1, ZH1 - 25, ZH1 + 25)
              for y0, y1 in ((-1080, -900), (-300, -120), (120, 300), (900, 1080))]
    m.add("door_hinges", BLACK, knuckles, leaves)
    m.add("hinge_pin", STEEL, cyl(m.r(22), (XDO + 20, -1130, ZH1 + 5), (XDO + 20, 1130, ZH1 + 5)))
    for s in (1, -1):
        yr = s * 1300
        (barrel, rod), eyes = ram_parts((XH + 500, yr, 2700), (XDO + 40, yr, 2180))
        m.add("door_rams", BLACK, barrel)
        m.add("door_ram_rods", CHROME, rod, eyes)
        m.add("door_ram_lugs", DARK, box(XH + 430, XH + 570, *sorted((s * (HY - 10), s * 1320)), 2640, 2760),
              box(XDO + 5, XDO + 80, *sorted((s * 1195, s * 1320)), 2130, 2230))
        m.add("door_clamps", BLACK, box(XDO - 45, XDO + 20, *sorted((s * 960, s * 1180)), ZH0 + 105, ZH0 + 165),
              box(XDO - 70, XDO - 30, *sorted((s * 1010, s * 1060)), ZH0 + 95, ZH0 + 175))
    m.add("drain_valve", GALV, cyl(45, (XDO + 40, 0, ZH0 + 135), (XDO - 70, 0, ZH0 + 135)))
    m.add("drain_handle", RED, bar((XDO - 50, 0, ZH0 + 135), (XDO - 50, 230, ZH0 + 135), 40, m.t(20)))

    # chevron panel: white plate in a black frame, orange stripes laid on it
    y_p, z0, z1 = 1150.0, 1380.0, 2620.0
    m.add("chevron_plate", BODY, box(XDO - 15, XDO + 5, -y_p, y_p, z0, z1))
    fw = 35.0
    xa, xb = XDO - 18, XDO + 3
    m.add("chevron_frame", BLACK, box(xa, xb, -y_p, y_p, z0, z0 + fw), box(xa, xb, -y_p, y_p, z1 - fw, z1),
          box(xa, xb, -y_p, -y_p + fw, z0, z1), box(xa, xb, y_p - fw, y_p, z0, z1))
    win = box(XDO - 25, XDO, -y_p + 25, y_p - 25, z0 + 25, z1 - 25)
    stripes = []
    pitch = 300.0 * math.sqrt(2)
    c = z0 + 40
    while c < z1 + 1400:
        s_ = prism(chevron(c, 75.0), "x", XDO - 20, XDO - 5).intersect(win)
        if s_.Volume() > 1:
            stripes.append(s_)
        c += pitch
    m.add("chevrons", STRIPE, stripes)

    # LED directional arrow bar and work lamps over the door, rear beacons
    m.add("arrow_bar", BLACK, box(XDO - 60, XDO + 60, -640, 640, ZH1 + 60, ZH1 + 190),
          [box(XDO - 20, XH + 150, y - 30, y + 30, ZH1 - 20, ZH1 + 80) for y in (-450.0, 450.0)])
    m.add("arrow_lamps", AMBER, [cyl(40, (XDO - 50, y, ZH1 + 125), (XDO - 75, y, ZH1 + 125))
                                 for y in np.linspace(-560, 560, 9)])
    for s in (1, -1):
        y0, y1 = sorted((s * 740, s * 920))
        m.add("work_lamp_housings", BLACK, box(XDO - 40, XDO + 80, y0, y1, ZH1 + 60, ZH1 + 170),
              box(XDO + 40, XH + 200, s * 830 - 30, s * 830 + 30, ZH1 - 20, ZH1 + 80))
        y0, y1 = sorted((s * 755, s * 905))
        m.add("work_lamp_lenses", LED, box(XDO - 52, XDO - 30, y0, y1, ZH1 + 72, ZH1 + 158))
        m.add("beacon_bases", BLACK, cyl(95, (XH + 350, s * 1050, ZH1 - 20), (XH + 350, s * 1050, ZH1 + 60)))
        m.add("beacons", AMBER, cyl(78, (XH + 350, s * 1050, ZH1 + 55), (XH + 350, s * 1050, ZH1 + 160)),
              cone(78, 35, (XH + 350, s * 1050, ZH1 + 159), (XH + 350, s * 1050, ZH1 + 205)))

    # rear under-run bar and lamps
    xu = XRR - 220
    m.add("rear_underrun", GREY, box(xu - 50, xu + 50, -1150, 1150, 430, 560),
          [box(xu - 30, XRR + 30, s * RY0, s * RY1, 520, RZ0 + 20) for s in (1, -1)])
    for s in (1, -1):
        m.add("lamp_housings", BLACK, box(xu - 65, xu - 40, *sorted((s * 640, s * 1120)), 455, 545))
        m.add("tail_lights", RED, box(xu - 75, xu - 55, *sorted((s * 900, s * 1110)), 465, 535))
        m.add("indicators", AMBER, box(xu - 75, xu - 55, *sorted((s * 780, s * 890)), 465, 535))
        m.add("reversing_lights", LED, box(xu - 75, xu - 55, *sorted((s * 650, s * 770)), 465, 535))

    # wander hose: boom on a swivel post at the top right, hose hanging to its cradle
    yw = -1010.0
    xpost, xtip, zb = XH + 150, XDO - 250, 3110.0
    m.add("wander_boom", GALV, cyl(55, (xpost, yw, ZH1 - 20), (xpost, yw, zb + 40)),
          bar((xpost, yw, zb), (xtip - 40, yw, zb), 90, 90))
    m.add("wander_swivel", BLACK, cyl(80, (xpost, yw, zb - 50), (xpost, yw, zb + 60)),
          cyl(70, (xtip, yw, zb - 70), (xtip, yw, zb + 50)))
    hose = [(xtip, yw, zb - 40), (xtip - 20, yw, 2700), (xtip + 10, yw, 1900), (xtip + 40, yw, 1250)]
    hr = 100.0
    m.add("wander_hose", RUBBER, pipe(hose, hr, False))
    ribs = []
    for a, b in zip(hose, hose[1:]):
        a, b = np.asarray(a), np.asarray(b)
        L = np.linalg.norm(b - a)
        d = (b - a) / L
        for t in np.arange(120, L - 60, 160):
            p = a + d * t
            ribs.append(cyl(hr + 12, tuple(p - d * 18), tuple(p + d * 18)))
    ribs += bend_cuffs(hose, hr + 12, 30)
    m.add("wander_hose_cuffs", RUBBER, ribs)
    tip = np.array([xtip + 40, yw, 1250.0])
    m.add("wander_nozzle", GALV, cyl(85, tuple(tip + (0, 0, 40)), (xtip + 55, yw, 980)),
          pipe([(xtip + 45, yw - 85, 1150), (xtip + 45, yw - 200, 1150), (xtip + 45, yw - 200, 1350),
                (xtip + 42, yw - 90, 1350)], m.r(22)))
    m.add("wander_cradle", DARK, box(xtip - 40, xu + 30, yw - 60, yw + 60, 490, 550),
          cyl(m.r(40), (xtip + 55, yw, 520), (xtip + 55, yw, 960)),
          cut(cyl(110, (xtip + 55, yw, 930), (xtip + 55, yw, 1010)), cyl(80, (xtip + 55, yw, 950), (xtip + 55, yw, 1020))))


def bend_cuffs(points, r, half):
    """A collar over each bend of a hose drawn without joint balls, along the mean direction."""
    out = []
    for p0, p1, p2 in zip(points, points[1:], points[2:]):
        p0, p1, p2 = (np.asarray(q, float) for q in (p0, p1, p2))
        d = (p1 - p0) / np.linalg.norm(p1 - p0) + (p2 - p1) / np.linalg.norm(p2 - p1)
        d /= np.linalg.norm(d)
        out.append(cyl(r, tuple(p1 - d * half), tuple(p1 + d * half)))
    return out


def ram_parts(a, b, rb=60.0, rr=35.0, frac=0.55):
    a, b = np.asarray(a, float), np.asarray(b, float)
    j = a + (b - a) * frac
    return (cyl(rb, tuple(a), tuple(j)), cyl(rr, tuple(j - (b - a) * 0.02), tuple(b))), \
        [cyl(rb * 0.9, tuple(a - (0, rb, 0)), tuple(a + (0, rb, 0))), cyl(rr * 1.4, tuple(b - (0, rr * 1.5, 0)), tuple(b + (0, rr * 1.5, 0)))]


def sweeping_gear(m):
    # ---------------------------------------------------- suction nozzle (pick-up head)
    nx0, nx1, ny0, ny1 = -450.0, 350.0, -760.0, 420.0
    m.add("nozzle", DARK, box(nx0, nx1, ny0, ny1, 70, 300),
          prism([(nx0, 300), (nx1, 300), (nx1 - 80, 360), (nx0 + 80, 360)], "y", ny0 + 40, ny1 - 40))
    m.add("nozzle_flaps", RUBBER, box(nx1 - 5, nx1 + m.t(20), ny0 + 10, ny1 - 10, 25, 120),
          box(nx0 - m.t(20), nx0 + 5, ny0 + 10, ny1 - 10, 25, 120))
    m.add("nozzle_skids", GALV, [box(nx0 + 40, nx1 - 40, y - 30, y + 30, 40, 90) for y in (ny0 + 30, ny1 - 30)])
    rw = 110.0
    xw_ = nx1 - 130
    m.add("nozzle_wheels", RUBBER, [cyl(rw, (xw_, y - 40, rw * 0.985), (xw_, y + 40, rw * 0.985))
                                    for y in (ny0 - 75, ny1 + 75)])
    m.add("nozzle_axles", STEEL, [cyl(m.r(30), (xw_, y0, rw * 0.985), (xw_, y1, rw * 0.985))
                                  for y0, y1 in ((ny0 + 40, ny0 - 120), (ny1 - 40, ny1 + 120))])
    m.add("nozzle_drag_arms", BLACK, [bar((nx1 - 60, y, 260), (1000, s * 390, 800), 70, 70)
                                      for s, y in ((1, 300.0), (-1, -300.0))])
    m.add("nozzle_lift_chain", GALV, [cyl(m.r(14), (nx0 + 60, y, 280), (nx0 + 60, y, RZ0 + 30)) for y in (-390.0, 390.0)])
    # suction hose up into the hopper
    hose = [(-120, -600, 280), (-280, -700, 700), (-520, -720, ZH0 + 60)]
    hr = 125.0
    m.add("suction_hose", RUBBER, pipe(hose, hr, False))
    cuffs = []
    for a, b in zip(hose, hose[1:]):
        a, b = np.asarray(a, float), np.asarray(b, float)
        L = np.linalg.norm(b - a)
        d = (b - a) / L
        for t in np.arange(90, L - 40, 150):
            p = a + d * t
            cuffs.append(cyl(hr + 12, tuple(p - d * 15), tuple(p + d * 15)))
    cuffs += bend_cuffs(hose, hr + 12, 30)
    m.add("suction_hose_cuffs", RUBBER, cuffs)
    m.add("hose_collars", GALV, cyl(150, (-120, -600, 290), (-120, -600, 380)),
          cyl(155, (-520, -720, ZH0 - 70), (-520, -720, ZH0 + 20)))

    # ---------------------------------------------------- gutter brooms
    for s in (1, -1):
        loc = []          # local frame: broom axis along z, ground at z = 0 before tilting
        ro, ri_, rt = 450.0, 360.0, 300.0
        n = 36
        star_b = [(r * math.cos(a), r * math.sin(a)) for k in range(n)
                  for a, r in ((2 * math.pi * k / n, ro), (2 * math.pi * (k + 0.5) / n, ro - 35))]
        star_t = [(r * math.cos(a), r * math.sin(a)) for k in range(n)
                  for a, r in ((2 * math.pi * k / n, rt), (2 * math.pi * (k + 0.5) / n, rt - 12))]
        wb = cq.Wire.makePolygon([V(x, y, 0) for x, y in star_b], close=True)
        wt = cq.Wire.makePolygon([V(x, y, 230) for x, y in star_t], close=True)
        bristles = cut(cq.Solid.makeLoft([wb, wt], ruled=True), cone(ri_ - 40, 200, (0, 0, -5), (0, 0, 235)))
        hub = cyl(330, (0, 0, 215), (0, 0, 255))
        boss = cyl(140, (0, 0, 240), (0, 0, 300))
        motor = [cyl(90, (0, 0, 290), (0, 0, 450)), cyl(110, (0, 0, 290), (0, 0, 320))]
        arm = [bar((0, 0, 380), (0, -s * (YB - 420), 380), 110, 110),
               box(-60, 60, -s * (YB - 400) - 60, -s * (YB - 400) + 60, 300, 470)]
        jet = pipe([(40, s * 30, 420), (300, s * 120, 420), (430, s * 160, 330)], m.r(16))
        hoses = pipe([(-60, 50 * s, 430), (-120, 40 * s, 560), (-200, -s * (YB - 450), 600)], m.r(20))

        def place_b(shape, dz=0.0):
            sh = rot(shape, -s * TILT_OUT, (1, 0, 0))
            sh = rot(sh, TILT_FWD, (0, 1, 0))
            return mv(sh, XB, s * YB, dz)

        dz = -3.0 - place_b(bristles).BoundingBox().zmin
        m.add("broom_bristles", BRISTLE, place_b(bristles, dz))
        m.add("broom_hubs", GALV, place_b(hub, dz), place_b(boss, dz))
        m.add("broom_motors", BLACK, [place_b(x, dz) for x in motor])
        m.add("broom_arms", DARK, [place_b(x, dz) for x in arm])
        m.add("broom_jets", BLACK, [place_b(x, dz) for x in jet])
        m.add("broom_hoses", RUBBER, [place_b(x, dz) for x in hoses])
        # pivot post from the inner end of the swing arm up into the frame rail
        p = rot_pt(rot_pt((0, -s * (YB - 400), 300), -s * TILT_OUT, (1, 0, 0)), TILT_FWD, (0, 1, 0)) + (XB, s * YB, dz)
        m.add("broom_posts", DARK, cyl(55, (p[0], p[1], p[2] + 10), (p[0], s * 390, RZ0 + 60)))
        q = rot_pt(rot_pt((-200, -s * (YB - 450), 600), -s * TILT_OUT, (1, 0, 0)), TILT_FWD, (0, 1, 0)) + (XB, s * YB, dz)
        m.add("broom_hoses", RUBBER, pipe([tuple(q), (q[0], s * 400, RZ0 + 40)], m.r(20)))
        # lift ram from the frame to the arm
        e = rot_pt(rot_pt((0, -s * (YB - 560), 380), -s * TILT_OUT, (1, 0, 0)), TILT_FWD, (0, 1, 0)) + (XB, s * YB, dz)
        (barrel, rod), eyes = ram_parts((XB + 300, s * 400, RZ0 + 40), tuple(e), 45, 25)
        m.add("broom_lift_rams", BLACK, barrel)
        m.add("broom_lift_rods", CHROME, rod, eyes)
