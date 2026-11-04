"""Water truck, 4,000 US gal (15 m3) dust-control tank on a 3-axle 6x4 conventional chassis.

A generic, brand-neutral truck with the typical proportions of the class (the 4,000 gal
water trucks that keep haul roads and stockyards damp on mines, quarries and bulk terminals):

* chassis: conventional (long-hood) 6x4, ~6.1 m wheelbase to the bogie centre, 1,370 mm
  tandem spread, 315/80R22.5 tyres (~1.05 m OD) on 22.5 in steel disc wheels, singles in front,
  duals behind, 2.5 m over the tyres; frame rails ~0.87 m wide, top at ~1.06 m; leaf-sprung
  front axle, leaf-spring tandem bogie, prop shafts, fuel tank (left), battery box (right),
  tool boxes under the tank, tandem mudguards and mud flaps, rear bumper with lamps;
* cab and hood: ~3.0 m bumper-to-back-of-cab, a tilting hood with integral flared fenders
  (2.48 m wide), plain bar grille (no badge), steel bumper with tow eyes, headlamps and
  indicators in the fender fronts, external air cleaner on the right fender, day cab 2.3 m
  wide with the roof at 3.0 m, two-piece windscreen, door windows, rear window, wipers,
  roof ID lamps, beacon, west-coast mirrors with spot mirrors, grab handles, entry steps,
  exhaust stack behind the cab, fleet number on the doors;
* water system: an elliptical steel tank 2.4 m wide x 1.5 m high x 5.5 m long over the dished
  heads (~15.3 m3, 4,000 US gal), its baffles showing as external ribs; centrifugal pump driven
  by a PTO shaft on a deck behind the cab with suction valve, discharge manifold and air-valve
  actuators, a riser to a cab-top water cannon (monitor) with handle, hose reel with hose and
  nozzle, hydrant fill pipe, vertical ladder up the front head to a top catwalk with
  handrails both sides, fill hatch (manway) with hinge and clamps, vent; distribution pipes
  along the frame to the rear spray bar with fan nozzles, spray heads at the rear corners and
  side spray nozzles, all on air valves; rear work lamps and a rear beacon.

Overall ~9.6 m long (bumper to the side spray heads), ~2.5 m over the tyres and tank (~3.1 m
over the mirrors), ~3.4 m to the top of the cannon and handrails.

Millimetres, X forward, Y left, Z up, ground at Z = 0, footprint roughly centred on the origin.
"""

from __future__ import annotations

import math

import cadquery as cq
import numpy as np

from cadkit import V, Finish, arc_pts, band, bar, box, boxc, cone, cut, cyl, pipe, place, prism, rgb, rot, rounded_box, sphere, text
from finishes import AMBER, BLACK, CHROME, DARK, GALV, GLASS, LED, RED, RUBBER, STEEL, WHITE, YELLOW

ASSET = dict(key="water_truck", stem="Water_Truck_4000gal",
             title="Water Truck (4,000 gal dust control)", az=40, el=18, size="1200x900")

CAB_WHITE = WHITE
TANK = YELLOW
WHEEL = Finish(rgb("#ecece6"), rough=0.5)                  # white painted steel disc wheels
MOUTH = Finish(rgb("#232528"), rough=0.85)

# ---- running gear
R = 525.0                       # 315/80R22.5, ~1,050 mm OD
ZC = R * (1 - 0.015)            # axle height: tyres sunk 1.5 % for a flat print contact
XF = 3700.0                     # steer axle
XR1, XR2 = -1700.0, -3070.0     # tandem drive axles
XRB = (XR1 + XR2) / 2           # bogie trunnion
F_IN, F_OUT = 935.0, 1250.0     # front tyre faces, |y|
DI, DO = (630.0, 925.0), (955.0, 1250.0)   # rear duals, inner / outer tyre faces, |y|

# ---- frame
RY0, RY1, RZ0, RZ1 = 345.0, 435.0, 760.0, 1060.0
XFR, XRR = 4600.0, -4620.0

# ---- cab: plan sections (z, front x, half width, front corner r, rear x, rear corner r)
CAB = [(1040, 3010, 1150, 120, 1700, 60), (2100, 3010, 1150, 120, 1700, 60), (2880, 2790, 1135, 110, 1710, 60),
       (2960, 2720, 1100, 90, 1730, 50), (3000, 2660, 1050, 60, 1760, 40)]
CAB_IN = [(1110, 2960, 1100, 80, 1750, 30), (2100, 2960, 1100, 80, 1750, 30), (2860, 2750, 1085, 70, 1760, 30),
          (2930, 2690, 1050, 60, 1780, 30)]
WS_Z0, WS_Z1, WS_Y = 2150.0, 2840.0, 1020.0

# ---- hood: sections (x, bottom z, fender top z, fender half width, hood half width, hood top z)
HOOD = [(2990, 950, 1400, 1240, 560, 2100), (4380, 950, 1265, 1240, 540, 2010), (4540, 1000, 1185, 1180, 520, 1990)]

# ---- tank: elliptical, axis along x
TA, TB, TZ = 1200.0, 750.0, 1940.0       # half width, half height, axis height
TX0, TX1 = -4400.0, 900.0                # cylindrical shell; dished heads 100 mm beyond each end
HEAD = 100.0
DECK_Z = 1200.0                          # pump deck top


def tank_top(y, k=1.0):
    return TZ + k * TB * math.sqrt(max(0.0, 1 - (y / (k * TA)) ** 2))


def tank_bot(y, k=1.0):
    return TZ - k * TB * math.sqrt(max(0.0, 1 - (y / (k * TA)) ** 2))


def ell_wire(x, a, b):
    return cq.Wire.makeEllipse(a, b, V(x, 0, TZ), V(1, 0, 0), V(0, 1, 0))


def ell_prism(x0, x1, a, b):
    x0, x1 = sorted((x0, x1))
    return cq.Solid.extrudeLinear(cq.Face.makeFromWires(ell_wire(x0, a, b)), V(x1 - x0, 0, 0))


def tank_head(x, d):
    """A dished head lofted out from the shell end at x, d = +1 (front) or -1 (rear)."""
    ws = [ell_wire(x - d * 5, TA, TB)]
    for f, k in ((0.45, 0.965), (0.8, 0.89), (1.0, 0.74)):
        ws.append(ell_wire(x + d * f * HEAD, k * TA, k * TB))
    try:
        return cq.Solid.makeLoft(ws, ruled=False)
    except Exception:          # noqa: BLE001
        return cq.Solid.makeLoft(ws, ruled=True)


def rrect(x0, x1, hy, rf, rr, z, n=6):
    """Plan of a box with rounded corners at height z, as 3-D points, anticlockwise."""
    pts = (arc_pts(x1 - rf, hy - rf, rf, 0, 90, n) + arc_pts(x0 + rr, hy - rr, rr, 90, 180, n)
           + arc_pts(x0 + rr, -hy + rr, rr, 180, 270, n) + arc_pts(x1 - rf, -hy + rf, rf, 270, 360, n))
    return [V(x, y, z) for x, y in pts]


def loft_sections(secs):
    wires = [cq.Wire.makePolygon(rrect(x0, x1, hy, rf, rr, z), close=True) for z, x1, hy, rf, x0, rr in secs]
    return cq.Solid.makeLoft(wires, ruled=True)


def xfr(z):
    """Cab front face (centre line) at height z."""
    zs, xs = zip(*[(c[0], c[1]) for c in CAB])
    return float(np.interp(z, zs, xs))


def hw(z):
    zs, ys = zip(*[(c[0], c[2]) for c in CAB])
    return float(np.interp(z, zs, ys))


def hood_hw(x):
    xs, ys = zip(*[(h[0], h[4]) for h in HOOD])
    return float(np.interp(x, xs, ys))


def hood_section(x, bot, ft, fhw, hhw, top, r=140.0):
    half = [(fhw, bot)] + arc_pts(fhw - 120, ft - 120, 120, 0, 90, 4) + [(hhw + 25, ft), (hhw, ft + 35)]
    half += arc_pts(hhw - r, top - r, r, 0, 90, 5)
    full = half + [(-y, z) for y, z in reversed(half)]
    return cq.Wire.makePolygon([V(x, y, z) for y, z in full], close=True)


def side_bar(x0, z0, x1, z1, s, w, h):
    """A strip on the cab side between (x0, z0) and (x1, z1), standing h/2 proud of it."""
    return bar((x0, s * hw(z0), z0), (x1, s * hw(z1), z1), w, h, up=(0, s, 0))


def rod(a, b, r, n=12):
    """A faceted round bar from a to b (light in the GLB, round enough for rails and rungs)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    L = float(np.linalg.norm(d))
    z = d / L
    x = np.cross(z, [1.0, 0, 0] if abs(z[0]) < 0.9 else [0, 1.0, 0])
    x /= np.linalg.norm(x)
    return place(prism(ngon(0, 0, r, n), "z", 0, L), tuple(x), tuple(np.cross(z, x)), tuple(z), tuple(a))


def rods(points, r, n=12):
    return [rod(p, q, r, n) for p, q in zip(points, points[1:])]


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
    if kind == "inner":
        tread = []
    elif kind == "steer":
        w = (y_out - y_in - 60 - 3 * 14) / 4
        tread = []
        for k in range(4):
            a = y_in + 30 + k * (w + 14)
            rib = cyl(R, c(a), c(a + w))
            tread.append(cut(rib, bore) if k == 3 else rib)
    else:
        n = 24
        p = 360.0 / n
        ym, half = (y_in + y_out) / 2, (y_out - y_in) / 2
        tread = []
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

class Parts:
    """Collects shapes by part name, so each left/right pair ends up as one part."""

    def __init__(self, m):
        self.m, self.order = m, {}
        self.print_mode = m.print_mode
        self.t, self.r = m.t, m.r

    def add(self, name, finish, *shapes):
        self.order.setdefault(name, (finish, []))[1].append(shapes)

    def flush(self):
        for name, (finish, shapes) in self.order.items():
            self.m.add(name, finish, shapes)


def build(model):
    m = Parts(model)
    _build(m)
    m.flush()


def _build(m):
    hr = m.r(18)
    pr = m.r(20)

    # =========================================================== running gear
    parts = {k: [] for k in ("tyres", "rims", "rim_holes", "hubs", "nuts")}
    for s in (1, -1):
        wheel(m, parts, XF, s, F_IN, F_OUT, "steer")
        for xc in (XR1, XR2):
            wheel(m, parts, xc, s, *DI, "inner")
            wheel(m, parts, xc, s, *DO, "outer")
    m.add("tyres", RUBBER, parts["tyres"])
    m.add("wheel_rims", WHEEL, parts["rims"])
    m.add("rim_hand_holes", MOUTH, parts["rim_holes"])
    m.add("wheel_hubs", DARK, parts["hubs"])
    m.add("wheel_nuts", STEEL, parts["nuts"])

    # front axle, springs
    fa = [box(XF - 70, XF + 70, -880, 880, 430, 560)]
    fa += [cyl(90, (XF, s * 860, 410), (XF, s * 860, 640)) for s in (1, -1)]
    fa += [cyl(165, (XF, s * 830, ZC), (XF, s * 1000, ZC)) for s in (1, -1)]
    fa += [bar((XF, s * 850, 470), (XF - 280, s * 790, 470), 50, 50) for s in (1, -1)]
    m.add("front_axle", DARK, fa)
    m.add("tie_rod", BLACK, cyl(m.r(28), (XF - 280, -800, 470), (XF - 280, 800, 470)))
    springs, hangers = [], []
    for s in (1, -1):
        y0, y1 = sorted((s * 440, s * 530))
        springs.append(prism(band([(XF - 760, 720), (XF - 380, 625), (XF, 595), (XF + 380, 625), (XF + 760, 720)], 38),
                             "y", y0, y1))
        hangers += [box(x - 55, x + 55, s * 425, s * 545, 680, 790) for x in (XF - 760, XF + 760)]
        hangers.append(box(XF - 110, XF + 110, s * 425, s * 545, 545, 580))
    m.add("front_springs", BLACK, springs)
    m.add("spring_hangers", DARK, hangers)

    # tandem drive axles, bogie springs, prop shafts
    axles = []
    for x in (XR1, XR2):
        axles += [cyl(140, (x, -600, ZC), (x, 600, ZC)), cyl(255, (x, -170, ZC), (x, 170, ZC)),
                  cyl(200, (x - 60, 0, ZC), (x + 200, 0, ZC + 20)),
                  cyl(150, (x, 0, ZC), (x + 360, 0, ZC + 40))]
        axles += [cyl(230, (x, s * 560, ZC), (x, s * 1140, ZC)) for s in (1, -1)]
    m.add("drive_axles", DARK, axles)
    bogie = []
    for s in (1, -1):
        y0, y1 = sorted((s * 465, s * 575))
        bogie.append(prism(band([(XR1 + 60, ZC + 175), (XRB, 830), (XR2 - 60, ZC + 175)], [45, 70, 45]), "y", y0, y1))
        bogie += [box(x - 120, x + 120, s * 455, s * 585, ZC + 110, ZC + 165) for x in (XR1, XR2)]
        bogie.append(box(XRB - 170, XRB + 170, s * 425, s * 600, 700, 1060))
    m.add("bogie_springs", BLACK, bogie)
    m.add("bogie_trunnion", STEEL, cyl(95, (XRB, -640, 830), (XRB, 640, 830)))
    m.add("prop_shafts", DARK, cyl(m.r(55), (2300, 0, 760), (XR1 + 360, 0, ZC + 40)),
          cyl(m.r(50), (XR1 - 150, 0, ZC + 60), (XR2 + 360, 0, ZC + 40)),
          [cyl(m.r(70), (p[0] - 50, 0, p[2]), (p[0] + 50, 0, p[2])) for p in ((2300, 0, 760), (XR1 + 360, 0, ZC + 40), (XR2 + 360, 0, ZC + 40))],
          box(-200, 0, -110, 110, 660, RZ0 + 20))

    # =========================================================== frame
    rails = [box(XRR, XFR, s * RY0, s * RY1, RZ0, RZ1) for s in (1, -1)]
    rails += [box(x - 40, x + 40, -RY1, RY1, RZ0 + 40, RZ1 - 40) for x in (XFR - 60, 2200, 0, XRB, -4000)]
    rails.append(box(XRR, XRR + 60, -RY1, RY1, RZ0, RZ1))
    m.add("frame_rails", BLACK, rails)
    m.add("tank_sills", BLACK, [box(-4520, 1000, s * RY0, s * RY1, RZ1 - 5, 1240) for s in (1, -1)])
    m.add("engine", DARK, box(3000, 4450, -420, 420, 500, 1350), box(2250, 3020, -300, 300, 560, 1000))

    # =========================================================== hood with fenders
    hood = cq.Solid.makeLoft([hood_section(*h) for h in HOOD], ruled=True)
    arches = [cyl(650, (XF, s * 575, ZC), (XF, s * 1400, ZC)) for s in (1, -1)]
    m.add("hood", CAB_WHITE, cut(hood, *arches))
    m.add("fender_liners", BLACK, [prism(band(arc_pts(XF, ZC, 652, 6, 174, 24), 16), "y", *sorted((s * 580, s * 1238)))
                                   for s in (1, -1)])
    # grille: plain black panel with chrome bars, white hood surround
    m.add("grille", BLACK, box(4520, 4565, -470, 470, 1080, 1940))
    m.add("grille_bars", CHROME, [box(4560, 4580, -440, 440, z - 22, z + 22) for z in np.linspace(1160, 1860, 7)],
          box(4560, 4582, -25, 25, 1100, 1920))
    # hood side louvres
    louv = []
    for s in (1, -1):
        for z in np.arange(1560, 1860, 60):
            louv.append(bar((3450, s * hood_hw(3450), z), (4050, s * hood_hw(4050), z), 30, m.t(14), up=(0, s, 0)))
    m.add("hood_louvres", BLACK, louv)
    # head lamps and indicators in the fender fronts
    for s in (1, -1):
        m.add("headlamp_housing", BLACK, box(4528, 4552, *sorted((s * 620, s * 1000)), 1025, 1155))
        m.add("headlamps", LED, box(4545, 4558, *sorted((s * 640, s * 790)), 1040, 1140),
              box(4545, 4558, *sorted((s * 830, s * 980)), 1040, 1140))
        m.add("front_indicators", AMBER, box(4530, 4556, *sorted((s * 1020, s * 1150)), 1040, 1140))
        m.add("fender_marker", AMBER, box(4380, 4460, *sorted((s * 1225, s * 1250)), 1150, 1200))
    # bumper, tow eyes, licence plate blank
    m.add("bumper", STEEL, prism([(4540, 600), (4690, 600), (4720, 630), (4720, 850), (4690, 880), (4540, 880)],
                                 "y", -1240, 1240))
    m.add("bumper_end_caps", BLACK, [box(4545, 4715, *sorted((s * 1225, s * 1250)), 620, 860) for s in (1, -1)])
    m.add("tow_eyes", DARK, [prism([(4700, 560), (4800, 600), (4800, 680), (4700, 720)], "y", *sorted((s * 600, s * 640)))
                             for s in (1, -1)],
          [cyl(m.r(25), (4760, s * 560, 640), (4760, s * 680, 640)) for s in (1, -1)])
    m.add("front_spray_nozzles", BLACK, [cyl(m.r(30), (4630, s * 900, 610), (4700, s * 900, 540)) for s in (1, -1)],
          [box(4690, 4730, *sorted((s * 850, s * 950)), 520, 550) for s in (1, -1)])
    # air cleaner on the right fender
    m.add("air_cleaner", BLACK, cyl(180, (3250, -950, 1380), (3250, -950, 2000)),
          cone(180, 100, (3250, -950, 2000), (3250, -950, 2060)))
    m.add("air_cleaner_bands", STEEL, [cyl(188, (3250, -950, z), (3250, -950, z + 40)) for z in (1500, 1850)])
    m.add("air_intake_pipe", BLACK, rods([(3250, -950, 1550), (3250, -650, 1550), (3250, -500, 1600)], m.r(70)))

    # =========================================================== cab
    shell = loft_sections(CAB)
    if not m.print_mode:
        win = [prism([(1900, 2150), (xfr(2150) - 130, 2150), (xfr(2820) - 130, 2820), (1900, 2820)], "y",
                     *sorted((s * 1060, s * 1300))) for s in (1, -1)]
        ws = box(2650, 3100, -WS_Y, WS_Y, WS_Z0, WS_Z1)
        rw = box(1650, 1800, -650, 650, 2250, 2750)
        shell = cut(shell, loft_sections(CAB_IN), *win, ws, rw)
        m.add("dash", DARK, box(2700, 2990, -1100, 1100, 1110, 2050))
        m.add("seats", BLACK, [box(2050, 2500, y - 260, y + 260, 1110, 1650) for y in (550.0, -550.0)],
              [box(1950, 2100, y - 260, y + 260, 1600, 2450) for y in (550.0, -550.0)])
        m.add("steering_wheel", BLACK, cut(cyl(220, (2650, 550, 2050), (2672, 550, 2087)),
                                           cyl(190, (2640, 550, 2033), (2690, 550, 2117))),
              cyl(35, (2650, 550, 2050), (2900, 550, 1700)))
    m.add("cab", CAB_WHITE, shell)

    # windscreen, two-piece, rubber, centre post, wipers
    d = np.array([xfr(WS_Z1) - xfr(WS_Z0), 0.0, WS_Z1 - WS_Z0])
    d /= np.linalg.norm(d)
    nrm = (float(d[2]), 0.0, float(-d[0]))
    g = m.t(12)
    za, zb = WS_Z0 - 15, WS_Z1 + 15
    m.add("windscreen", GLASS, bar((xfr(za), 0, za), (xfr(zb), 0, zb), 2 * (WS_Y + 25), g, up=nrm))
    fr = m.t(18)
    frame = [bar((xfr(z), -WS_Y - 40, z), (xfr(z), WS_Y + 40, z), 50, fr, up=nrm) for z in (WS_Z0 - 10, WS_Z1 + 10)]
    frame += [bar((xfr(WS_Z0 - 30), y, WS_Z0 - 30), (xfr(WS_Z1 + 30), y, WS_Z1 + 30), 50, fr, up=nrm)
              for y in (-WS_Y - 15, 0.0, WS_Y + 15)]
    m.add("windscreen_rubber", BLACK, frame)
    o = np.array(nrm) * (g / 2 + 6)
    wipers = []
    for y0, y1 in ((900.0, 150.0), (-120.0, -870.0)):
        p0 = np.array((xfr(WS_Z0 + 30), y0, WS_Z0 + 30))
        p1 = np.array((xfr(WS_Z0 + 70), y1, WS_Z0 + 70))
        wipers.append(bar(p0 + o, p1 + o, m.t(22), m.t(16), up=nrm))
        wipers.append(cyl(m.r(22), p0 - o, p0 + 1.6 * o))
    m.add("wipers", BLACK, wipers)
    m.add("cowl", BLACK, box(2985, 3035, -1120, 1120, 2085, 2150))

    for s in (1, -1):
        def xw(z):
            return xfr(z) - 130
        pane = [(1900, 2150), (xw(2150) + 20, 2150), (xw(2820) + 20, 2820), (1900, 2820)]
        m.add("door_glass", GLASS, prism(pane, "y", *sorted((s * 1132, s * (1150 + max(m.t(14), 14))))))
        f2 = m.t(14)
        m.add("door_rubber", BLACK, side_bar(1900, 2150, xw(2150), 2150, s, 40, f2),
              side_bar(1900, 2820, xw(2820), 2820, s, 40, f2), side_bar(1900, 2150, 1900, 2820, s, 40, f2),
              side_bar(xw(2150), 2150, xw(2820), 2820, s, 40, f2))
        sw, sh = m.t(14), m.t(20)

        def xd(z):                       # door front edge
            return xfr(z) - 70 if z > 2100 else 2940.0
        zk = (1110.0, 2100.0, 2880.0)
        seams = [side_bar(1830, z0, 1830, z1, s, sw, sh) for z0, z1 in zip(zk, zk[1:])]
        seams += [side_bar(xd(z0), z0, xd(z1), z1, s, sw, sh) for z0, z1 in zip(zk, zk[1:])]
        seams.append(side_bar(1830 - sw / 2, 1110, xd(1110) + sw / 2, 1110, s, sw, sh))
        m.add("door_seams", BLACK, seams)
        m.add("door_handle", CHROME, side_bar(1950, 1950, 2110, 1950, s, 40, m.t(24)))
        m.add("door_number", BLACK, text("WT-07", 210, m.t(10) + 6, (2400, s * 1146, 1600),
                                         (-s, 0, 0), (0, s, 0)))
        m.add("door_mirror_light", AMBER, side_bar(2950, 1300, 2990, 1300, s, 90, m.t(16)))
        ya, yb = s * 1140, s * 1205
        m.add("grab_handles", CHROME, rods([(1770, ya, 1250), (1770, yb, 1250), (1770, yb, 2450), (1770, ya, 2450)], hr, 10))
        # entry steps
        m.add("step_frame", DARK, box(2400, 2400 + m.t(35), *sorted((s * 960, s * 1190)), 380, 1060),
              box(2950 - m.t(35), 2950, *sorted((s * 960, s * 1190)), 380, 1060),
              box(2400, 2950, *sorted((s * 940, s * (960 + m.t(35)))), 380, 1060))
        m.add("step_treads", GALV, box(2420, 2930, *sorted((s * 980, s * 1210)), 400, 440),
              box(2420, 2930, *sorted((s * 980, s * 1210)), 720, 760))
        # front mud flaps hung off the fender
        m.add("front_mud_flap", RUBBER, box(2985, 2985 + m.t(20), *sorted((s * 960, s * 1230)), 300, 1000))
        # west-coast mirror and spot mirror
        xm, ym = 3000.0, s * 1430
        m.add("mirror_arms", BLACK, rod((2860, s * 1130, 2250), (xm, ym, 2250), hr, 10),
              rod((2760, s * 1125, 2700), (xm, ym, 2700), hr, 10), rod((xm, ym, 2180), (xm, ym, 2760), hr, 10))
        m.add("mirror_heads", BLACK, box(xm - 40, xm + 45, *sorted((s * 1340, s * 1520)), 2280, 2680),
              cyl(95, (xm - 40, s * 1430, 2160), (xm + 30, s * 1430, 2160)))
        m.add("mirror_glass", CHROME, box(xm - 52, xm - 35, *sorted((s * 1352, s * 1508)), 2292, 2668),
              cyl(80, (xm - 52, s * 1430, 2160), (xm - 35, s * 1430, 2160)))

    m.add("rear_window", GLASS, box(1700 - m.t(12), 1712, -650, 650, 2250, 2750))
    m.add("rear_window_rubber", BLACK, [box(1690 - m.t(12), 1712, -680, 680, z - 20, z + 20) for z in (2240, 2760)],
          [box(1690 - m.t(12), 1712, y - 20, y + 20, 2230, 2770) for y in (-660, 660)])
    # roof: ID lamps, clearance lamps, beacon
    m.add("roof_id_lamps", AMBER, [box(2550, 2620, y - 45, y + 45, 2985, 3030) for y in (-250, 0, 250)],
          [box(2500, 2580, y - 40, y + 40, 2985, 3025) for y in (-900, 900)])
    m.add("beacon_base", BLACK, cyl(95, (1980, 550, 2985), (1980, 550, 3045)))
    m.add("beacon", AMBER, cyl(75, (1980, 550, 3040), (1980, 550, 3150)), sphere(75, (1980, 550, 3150)))
    # exhaust stack behind the cab, right
    m.add("exhaust_stack", CHROME, cyl(75, (1640, -1000, 1150), (1640, -1000, 3250)),
          cone(75, 60, (1640, -1000, 3250), (1640, -1000, 3330)))
    m.add("exhaust_shield", BLACK, cyl(92, (1640, -1000, 1900), (1640, -1000, 2600)),
          box(1640, 1720, -1030, -970, 2450, 2520), pipe([(1640, -1000, 1180), (1900, -700, 900)], m.r(60)))

    # =========================================================== under-cab and side gear
    m.add("fuel_tank", CHROME, cyl(290, (1200, 820, 770), (2300, 820, 770)))
    m.add("fuel_tank_straps", BLACK, [cyl(300, (x, 820, 770), (x + 50, 820, 770)) for x in (1400, 2050)],
          [box(x - 10, x + 60, 420, 560, 700, 860) for x in (1400, 2050)])
    m.add("fuel_cap", BLACK, cyl(65, (2150, 820, 1040), (2150, 820, 1100)))
    m.add("battery_box", BLACK, box(1250, 2250, -1100, -500, 600, 1000), box(1230, 2270, -1115, -485, 990, 1030))
    m.add("battery_bracket", DARK, [box(x - 40, x + 40, -560, -420, 700, 900) for x in (1400, 2100)])
    for s in (1, -1):
        y0, y1 = sorted((s * 650, s * 1160))
        m.add("tool_box", GALV, box(-1050, 150, y0, y1, 650, 1150))
        m.add("tool_box_lid", BLACK, box(-1060, 160, *sorted((s * 1155, s * (1160 + m.t(12)))), 1100, 1130),
              [box(x - 60, x + 60, *sorted((s * 1155, s * (1160 + m.t(14)))), 1020, 1080) for x in (-700, -200)])
        m.add("tool_box_brackets", DARK, [box(x - 40, x + 40, *sorted((s * 420, s * 670)), 900, 990) for x in (-900, 0)])

    # tandem mudguards, flaps
    path = arc_pts(XR1, ZC, 615, 14, 90, 10) + arc_pts(XR2, ZC, 615, 90, 166, 10)
    for s in (1, -1):
        m.add("rear_mudguard", BLACK, prism(band(path, m.t(12) / 2), "y", *sorted((s * 600, s * 1275))))
        m.add("mudguard_brackets", DARK, [box(x - 40, x + 40, *sorted((s * 425, s * 720)), 1050, ZC + 618)
                                          for x in (XR1 - 450, XR2 + 450)])
        xe = XR2 + 615 * math.cos(math.radians(166))
        m.add("rear_mud_flap", RUBBER, box(xe - m.t(22), xe + 5, *sorted((s * 640, s * 1265)), 280, ZC + 175))
        m.add("mud_flap_hanger", DARK, box(xe - 60, xe + 10, *sorted((s * 420, s * 1265)), ZC + 150, ZC + 210))
        m.add("mudguard_markers", AMBER, [box(x - 45, x + 45, *sorted((s * 1272, s * 1284)), ZC + 560, ZC + 600)
                                          for x in (XR1 + 200, XR2 - 200)])

    # rear bumper and lamps
    m.add("rear_bumper", BLACK, box(-4700, -4600, -1220, 1220, 690, 820))
    for s in (1, -1):
        m.add("tail_lamps", RED, box(-4712, -4690, *sorted((s * 820, s * 1060)), 710, 800))
        m.add("rear_indicators", AMBER, box(-4712, -4690, *sorted((s * 620, s * 780)), 710, 800))
    m.add("reversing_lamps", LED, [box(-4712, -4690, *sorted((s * 420, s * 560)), 725, 785) for s in (1, -1)])

    # =========================================================== tank
    shell = ell_prism(TX0, TX1, TA, TB)
    m.add("tank", TANK, shell, tank_head(TX1, 1), tank_head(TX0, -1))
    ribs = [ell_prism(x - 35, x + 35, TA + 18, TB + 18) for x in (TX1 - 10, 50.0, -1050.0, -3350.0, TX0 + 10)]
    m.add("tank_ribs", TANK, ribs)
    # cradles on the sills
    cradles = []
    k = 0.985
    for x in (820.0, -300.0, -1500.0, -2650.0, -3700.0, -4330.0):
        pts = [(950.0, 1110.0)] + [(y, tank_bot(y, k)) for y in np.linspace(950, -950, 21)] + [(-950.0, 1110.0)]
        cradles.append(prism(pts, "x", x - 55, x + 55))
    m.add("tank_cradles", BLACK, cradles)
    # lettering and side markers
    for s in (1, -1):
        m.add("tank_lettering", BLACK, text("WATER", 420, 85, (-2200, s * 1138, TZ), (-s, 0, 0), (0, s, 0)))
        m.add("tank_side_markers", AMBER, [box(x - 50, x + 50, *sorted((s * 1180, s * 1228)), TZ - 35, TZ + 35)
                                           for x in (700.0, -4200.0)])

    # catwalk on the tank top with handrails both sides
    pz = 2685.0
    pt = m.t(40)
    plank = [box(-4330, -560, -270, 270, pz, pz + pt), box(60, 1045, -270, 270, pz, pz + pt)]
    m.add("catwalk", GALV, plank)
    m.add("catwalk_tread", DARK, [box(x - 12, x + 12, -255, 255, pz + pt - 8, pz + pt + 8)
                                  for x in list(np.arange(-4250, -600, 250)) + list(np.arange(150, 1000, 250))])
    m.add("catwalk_brackets", BLACK, [box(x - 30, x + 30, -280, 280, 2610, pz + 10)
                                      for x in (900.0, 200.0, -700.0, -1700.0, -2700.0, -3700.0, -4250.0)])
    rails_ = []
    posts_x = (-4300.0, -3300.0, -2300.0, -1300.0, -560.0, 100.0, 850.0)
    ztop, zmid = 3300.0, 3000.0
    for y in (-280.0, 280.0):
        rails_ += [rod((x, y, pz + 10), (x, y, ztop + pr), pr) for x in posts_x]
        rails_ += [rod((posts_x[0] - pr, y, z), (posts_x[-1] + pr, y, z), pr) for z in (zmid, ztop)]
    m.add("handrails", TANK, rails_)

    # fill hatch (manway) with hinge and clamps, vent
    hx = -250.0
    m.add("fill_hatch_collar", TANK, cyl(270, (hx, 0, 2600), (hx, 0, 2770)))
    m.add("fill_hatch_lid", GALV, cyl(290, (hx, 0, 2765), (hx, 0, 2765 + m.t(30))),
          cyl(150, (hx, 0, 2790), (hx, 0, 2810)))
    m.add("fill_hatch_hinge", BLACK, box(hx - 360, hx - 260, -120, 120, 2730, 2800),
          cyl(m.r(25), (hx - 320, -150, 2790), (hx - 320, 150, 2790)))
    m.add("fill_hatch_clamps", BLACK, [box(hx + 250, hx + 330, y - 30, y + 30, 2700, 2810) for y in (-150, 150)])
    m.add("tank_vent", GALV, cyl(45, (-3900, 600, 2550), (-3900, 600, 2800)),
          cone(80, 40, (-3900, 600, 2790), (-3900, 600, 2850)))

    # ladder up the front head
    xl = 1055.0
    m.add("ladder_stringers", BLACK, [box(xl - 25, xl + 25, y - 25, y + 25, DECK_Z - 20, 3260) for y in (-200, 200)])
    m.add("ladder_rungs", GALV, [rod((xl, -210, z), (xl, 210, z), m.r(16), 8) for z in np.arange(1300, 2600, 300)])
    m.add("ladder_brackets", DARK, [box(950, xl, y - 20, y + 20, 2290, 2340) for y in (-200, 200)])
    m.add("ladder_grabs", TANK, [rod((xl, y, 3240), (850, y * 1.4, 3300), pr) for y in (-200, 200)])

    # =========================================================== pump deck and plumbing behind the cab
    m.add("pump_deck", GALV, box(1000, 1690, -1150, 1150, DECK_Z - m.t(30), DECK_Z))
    m.add("deck_bearers", BLACK, [box(x - 40, x + 40, -1150, 1150, RZ1 - 20, DECK_Z - 10) for x in (1060, 1620)],
          [box(1000, 1690, y - 40, y + 40, RZ1 - 20, DECK_Z - 10) for y in (-1100, 1100)])
    m.add("pump_volute", DARK, cyl(200, (1150, 0, 1420), (1330, 0, 1420)), box(1150, 1450, -200, 200, DECK_Z - 10, 1300))
    m.add("pump_gearbox", BLACK, box(1330, 1520, -150, 150, 1250, 1560))
    m.add("pto_shaft", DARK, rods([(1450, 0, 1300), (1600, 0, 1000), (2300, 0, 800)], m.r(40)))
    m.add("suction_pipe", GALV, cyl(85, (930, 0, 1420), (1160, 0, 1420)))
    m.add("suction_valve", BLACK, cyl(130, (1095, 0, 1420), (1125, 0, 1420)))
    m.add("valve_handles", YELLOW, bar((1110, 0, 1550), (1110, 280, 1600), 40, m.t(20)),
          bar((1240, 380, 1990), (1240, 380, 2180), 40, m.t(20), up=(1, 0, 0)))
    m.add("discharge_pipe", GALV, cyl(75, (1240, 0, 1560), (1240, 0, 1920)),
          cyl(80, (1240, -840, 1900), (1240, 540, 1900)))
    m.add("air_valve_actuators", BLACK, [cyl(65, (1240, y, 1950), (1240, y, 2080)) for y in (-600, -300, 300)],
          [cyl(m.r(14), (1240, y, 2080), (1240, y, 2130)) for y in (-600, -300, 300)])
    # feed pipes to the rear spray bar, along the frame
    for s, ys in ((1, 460.0), (-1, -760.0)):
        m.add("feed_pipe", GALV, rods([(1240, ys, 1900), (1240, ys, 1150), (1000, s * 520, 1150),
                                       (-4560, s * 520, 1150), (-4740, s * 520, 1100), (-4740, s * 520, 560)], m.r(45), 14))
    # riser and cab-top water cannon
    xc_, yc_ = 1240.0, -500.0
    m.add("monitor_riser", GALV, cyl(70, (xc_, yc_, 1900), (xc_, yc_, 3120)),
          bar((xc_, yc_, 2400), (950, yc_, 2400), 50, 50))
    m.add("monitor_swivel", BLACK, cyl(100, (xc_, yc_, 3100), (xc_, yc_, 3190)))
    tip = np.array([2000.0, yc_, 3340.0])
    base = np.array([xc_, yc_, 3180.0])
    dvec = (tip - base) / np.linalg.norm(tip - base)
    m.add("water_cannon", STEEL, sphere(85, tuple(base)), cone(75, 50, tuple(base), tuple(tip - 120 * dvec)))
    m.add("cannon_nozzle", BLACK, cone(62, 40, tuple(tip - 140 * dvec), tuple(tip)))
    m.add("cannon_handle", BLACK, pipe([tuple(base), (1000, yc_, 3260), (930, yc_, 3200)], m.r(22)))
    m.add("cannon_brace", DARK, bar((xc_, yc_, 2950), (1680, yc_, 2950), 60, 60))
    # hose reel on the left of the deck
    rx, rz = 1430.0, 1600.0
    m.add("hose_reel_flanges", GALV, [cyl(260, (rx, y, rz), (rx, y + m.t(15), rz)) for y in (600.0, 1035.0)])
    m.add("hose_reel_hose", RUBBER, cyl(205, (rx, 610, rz), (rx, 1040, rz)),
          pipe([(rx - 180, 1000, rz - 100), (rx - 260, 1100, 1450), (rx - 260, 1100, 1260)], m.r(28)))
    m.add("hose_nozzle", YELLOW, cyl(m.r(40), (rx - 260, 1100, 1270), (rx - 260, 1100, 1340)))
    m.add("hose_reel_frame", BLACK, [box(rx - 40, rx + 40, y - 20, y + 20, DECK_Z - 10, rz + 10) for y in (570.0, 1080.0)],
          cyl(m.r(30), (rx, 560, rz), (rx, 1090, rz)), box(rx - 260, rx + 260, 560, 1090, DECK_Z - 10, DECK_Z + 40))
    m.add("hose_reel_crank", BLACK, pipe([(rx, 1090, rz), (rx, 1120, rz), (rx + 130, 1120, rz + 60), (rx + 130, 1170, rz + 60)], m.r(16)))
    # hydrant fill pipe, front left
    m.add("fill_pipe", GALV, rods([(880, 1000, 2250), (1080, 1100, 2250), (1080, 1100, 1480)], m.r(60), 14),
          boxc(150, 150, 150, 1080, 1100, 2250))
    m.add("fill_cap", BLACK, cyl(78, (1080, 1100, 1420), (1080, 1100, 1490)))

    # =========================================================== rear: lamps, spray bar and heads
    for s in (1, -1):
        m.add("rear_work_lamps", BLACK, box(-4540, -4440, *sorted((s * 700, s * 900)), 2240, 2380))
        m.add("rear_work_lamp_lens", LED, box(-4552, -4535, *sorted((s * 715, s * 885)), 2255, 2365))
    m.add("rear_beacon_base", BLACK, cyl(90, (-4450, 0, 2540), (-4450, 0, 2620)))
    m.add("rear_beacon", AMBER, cyl(72, (-4450, 0, 2615), (-4450, 0, 2720)), sphere(72, (-4450, 0, 2720)))

    xb, zb = -4740.0, 560.0
    m.add("spray_bar", GALV, cyl(55, (xb, -1190, zb), (xb, 1190, zb)))
    m.add("spray_bar_brackets", BLACK, [box(-4775, -4680, y - 30, y + 30, zb, 720) for y in (-900, -300, 300, 900)])
    noz = []
    for y in (-760.0, -380.0, 0.0, 380.0, 760.0):
        noz.append(rod((xb, y, zb), (xb - 75, y, zb - 85), m.r(30), 8))
        noz.append(box(xb - 110, xb - 60, y - 70, y + 70, zb - 115, zb - 85))
    for s in (1, -1):
        # rear corner spray heads on air valves, aimed down and out
        noz.append(cyl(70, (xb, s * 1100, zb), (xb, s * 1100, zb + 170)))
        noz.append(cyl(m.r(35), (xb, s * 1100, zb), (xb - 120, s * 1250, zb - 90)))
        noz.append(rot(box(xb - 160, xb - 100, s * 1190, s * 1330, zb - 120, zb - 75), s * -35, (0, 0, 1),
                       (xb - 130, s * 1260, zb)))
        # side spray nozzles, aimed sideways off the bar ends
        noz.append(cyl(m.r(35), (xb + 40, s * 1150, zb), (xb + 40, s * 1300, zb + 40)))
        noz.append(box(xb - 10, xb + 90, *sorted((s * 1280, s * 1330)), zb - 10, zb + 90))
    m.add("spray_heads", BLACK, noz)
    m.add("valve_caps", YELLOW, [cyl(50, (xb, s * 1100, zb + 165), (xb, s * 1100, zb + 200)) for s in (1, -1)])
