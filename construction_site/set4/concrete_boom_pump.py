"""Truck-mounted concrete boom pump, 38 m four-section boom, stowed, outriggers set on pads.

A generic, brand-neutral pump with the typical proportions of the 36-38 m class (the pumps that
place the deck and pile-cap concrete on wharf, berth and conveyor-trestle works):

* chassis: 8x4 with a flat-fronted cab-over day cab, two steer axles 1,850 mm apart, tandem drive
  bogie at 1,350 mm, 315/80R22.5 tyres (~1.05 m OD), singles in front and duals behind, 2.5 m
  over the tyres, frame rails ~0.87 m wide with the top at ~1.06 m; leaf-sprung axles, bogie,
  prop shafts, fuel tank, battery box, air tanks, toolbox, mudguards, mud flaps, rear under-run
  bar with lamps; cab with plain slatted grille (no badge), windscreen, door glass, wipers, visor
  with marker lamps, beacon, mirrors, grab handles, entry steps and an air-intake snorkel;
* pump body: a box-section subframe on the rails, the front outrigger box (X-frame) behind the
  cab carrying the slewing ring and a cast turret ~1.1 m across, with the boom's base pivot at
  ~3.0 m; front X-type outriggers telescoped out diagonally forwards to a ~7.2 m spread, rear
  swing legs swung out to ~6.6 m, every leg on a jack with a foot plate on a 700 mm composite
  outrigger pad; an outrigger control station (levers, red knobs) on each side of the outrigger
  box; boom rests at the front (behind the cab) and over the pump;
* boom: four tapered welded box sections in a two-high, two-wide Z/R-fold package (sections
  of ~7.9 / 8.0 / 7.5 / 9.5 m, ~33 m of arm plus the turret, ~38 m vertical reach): section 1
  back from the turret, section 2 folded forward on top of it, section 3 rolled beside section 1
  back to the rear, section 4 folded forward on top of section 3 and out over the cab roof;
  knuckle yokes with pins at each fold, the big lift cylinder at the turret and a fold cylinder
  at every knuckle, hydraulic hoses; an orange stripe along every section;
* concrete system: the DN125 delivery line (133 mm OD) from the S-valve up over the hopper, along
  the right of the body, up the turret and along every section with clamp collars, elbows round
  every knuckle, the tip elbow with a work lamp and a ~3 m end hose hanging in front of the cab; the rear hopper
  (~600 l) with its grille, agitator shaft and motors, S-valve outlet housing with its shift
  cylinders and lever, twin material cylinders, water box and drive cylinders under the body;
  ~600 l water tank (left), hydraulic oil tank and oil cooler (right), rear control box with its
  panel and emergency stop.

Overall ~11.7 m long (outlet elbow to the end hose; 11.5 m bumper to under-run bar), 2.5 m wide over
the tyres (7.2 m front pad centres, 7.9 m over the front pads), ~3.95 m high over the folded boom.

Colours: white cab, body and boom, black chassis and trim, steel delivery line, safety-orange
accents (boom stripes, leg warning bands, composite pads): it prints in White, Black, Silver grey
and Safety orange. Round parts of the display model (tyres, axles, pipeline, rams) are fine
polygon prisms to keep the GLB light; the print model uses true cylinders.

Millimetres, X forward, Y left, Z up, ground at Z = 0, footprint roughly centred on the origin.
"""

from __future__ import annotations

import math

import cadquery as cq
import numpy as np

from cadkit import (V, Finish, arc_pts, band, bar, box, clip_poly, cone, cut, cyl, frustum, mv, place, prism,
                    rgb, sphere)
from finishes import AMBER, BLACK, CHROME, DARK, GALV, GLASS, LED, RED, RUBBER, SIGN_ORANGE, STEEL, WHITE

ASSET = dict(key="concrete_boom_pump", stem="Concrete_Boom_Pump_38m",
             title="Concrete Boom Pump Truck (38 m, stowed)", az=40, el=20, size="1200x900")

BODY = WHITE                                               # cab, body and boom
ACCENT = SIGN_ORANGE                                       # boom stripe, pads, leg warning tips
WHEEL = Finish(rgb("#c9cdd1"), metal=0.6, rough=0.4)       # painted steel disc wheels (silver)
GREY = Finish(rgb("#6c7177"), metal=0.6, rough=0.5)        # bumper, grille slats, hopper steel
PIPE = Finish(rgb("#b4b8bc"), metal=0.8, rough=0.35)       # delivery line
PAD = Finish(rgb("#f26a0d"), rough=0.6)                    # composite outrigger pads

# ---- running gear
R = 525.0                       # 315/80R22.5, ~1,050 mm OD
ZC = R * (1 - 0.015)            # axle height: tyres sunk 1.5 % for a flat print contact
XF1, XF2 = 4000.0, 2150.0       # steer axles
XR1, XR2 = -1500.0, -2850.0     # tandem drive axles
XRB = (XR1 + XR2) / 2
F_IN, F_OUT = 935.0, 1250.0
DI, DO = (630.0, 925.0), (955.0, 1250.0)

# ---- frame
RY0, RY1, RZ0, RZ1 = 345.0, 435.0, 760.0, 1060.0
XFR, XRR = XF1 + 1300.0, -5150.0
SZ0, SZ1 = 1040.0, 1330.0       # pump subframe
SY0, SY1 = 330.0, 530.0

# ---- cab (local: X = 0 at the first steer axle): plan sections (z, front x, half width, r, rear x, r)
CAB = [(880, 1450, 1200, 170, -380, 50), (1700, 1432, 1200, 170, -380, 50), (2650, 1322, 1190, 160, -380, 50),
       (2880, 1290, 1170, 150, -375, 50), (3000, 1220, 1110, 110, -340, 50), (3030, 1120, 1020, 60, -270, 40)]
CAB_IN = [(1130, 1385, 1150, 130, -330, 20), (1700, 1382, 1150, 130, -330, 20), (2650, 1272, 1140, 120, -330, 20),
          (2900, 1222, 1110, 100, -320, 20)]
WS_Z0, WS_Z1, WS_Y = 1740.0, 2610.0, 1010.0

# ---- turret and boom
X_T = 2850.0                    # slewing axis
Z_PIV = 3000.0                  # boom base pivot
ZA, ZB = 2760.0, 3400.0         # bottoms of the lower and upper layers of the folded boom
Y3 = 480.0                      # sections 3 and 4 lie beside 1 and 2, to the left
# section: (x root, x tip, y centre, z bottom, root width, root depth, tip width, tip depth)
SEC = {1: (3100.0, -4750.0, 0.0, ZA, 460.0, 620.0, 380.0, 480.0),
       2: (-4750.0, 3200.0, 0.0, ZB, 420.0, 480.0, 330.0, 350.0),
       3: (3200.0, -4250.0, Y3, ZA, 340.0, 560.0, 270.0, 430.0),
       4: (-4250.0, 5250.0, Y3, ZB, 310.0, 440.0, 210.0, 250.0)}
RP = 66.5                       # delivery line, 133 mm OD

# ---- outriggers: (pivot / root in plan, pad centre in plan)
FRONT_S, FRONT_E = (2300.0, -700.0), (4757.0, 3600.0)
REAR_S, REAR_E = (-3800.0, 600.0), (-4500.0, 3300.0)


class Acc:
    """Shapes gathered by part name, so both sides and all wheels share one part each."""

    def __init__(self):
        self.d: dict[str, tuple[Finish, list]] = {}

    def add(self, name, fin, *shapes):
        if name not in self.d:
            self.d[name] = (fin, [])
        out = self.d[name][1]

        def walk(items):
            for s in items:
                if isinstance(s, (list, tuple)):
                    walk(s)
                elif s is not None:
                    out.append(s)
        walk(shapes)

    def merge(self, other, dx):
        for name, (fin, ss) in other.d.items():
            self.add(name, fin, [mv(s, dx) for s in ss])

    def flush(self, m):
        for name, (fin, ss) in self.d.items():
            m.add(name, fin, ss)


# =============================================================================== helpers

def xfr(z):
    zs, xs = zip(*[(c[0], c[1]) for c in CAB])
    return float(np.interp(z, zs, xs))


def hw(z):
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
    return bar((x0, s * hw(z0), z0), (x1, s * hw(z1), z1), w, h, up=(0, s, 0))


def xbeam(x0, x1, yc, za0, zb0, za1, zb1, w0, w1, grow=0.0):
    """Tapered box section from x0 (w0 wide, za0..zb0) to x1 (w1 wide, za1..zb1), centred on yc."""
    def wire(x, w, za, zb):
        w = w / 2 + grow
        return cq.Wire.makePolygon([V(x, yc - w, za), V(x, yc + w, za), V(x, yc + w, zb),
                                    V(x, yc - w, zb)], close=True)
    return cq.Solid.makeLoft([wire(x0, w0, za0, zb0), wire(x1, w1, za1, zb1)], ruled=True)


def sec_at(k, x):
    """Width and depth of boom section k at x."""
    x0, x1, yc, zb, w0, h0, w1, h1 = SEC[k]
    f = (x - x0) / (x1 - x0)
    return w0 + (w1 - w0) * f, h0 + (h1 - h0) * f


def sec_pipe(k, x, s):
    """Centre of the delivery line on the s side (+1 left, -1 right) of section k at x."""
    x0, x1, yc, zb, *_ = SEC[k]
    w, h = sec_at(k, x)
    return (x, yc + s * (w / 2 + 110.0), zb + h / 2)


def along(a, b, f):
    return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)


def cbox(x0, x1, y0, y1, z0, z1, c, axis="x"):
    """Box with its long edges along `axis` chamfered by c: a light stand-in for a rounded box."""
    if axis == "x":
        u0, u1, v0, v1, a0, a1 = y0, y1, z0, z1, x0, x1
    else:
        u0, u1, v0, v1, a0, a1 = x0, x1, z0, z1, y0, y1
    pts = [(u0 + c, v0), (u1 - c, v0), (u1, v0 + c), (u1, v1 - c), (u1 - c, v1), (u0 + c, v1), (u0, v1 - c), (u0, v0 + c)]
    return prism(pts, axis, a0, a1)


LIGHT = False          # set by build(): True for the display model (GLB), False for the print


def rod(r, a, b, chord=32.0):
    """A round bar from a to b: a true cylinder for the print, a polygon prism (facets ~chord mm)
    for the display model, which keeps the GLB light without changing the silhouette."""
    if not LIGHT:
        return cyl(r, a, b)
    n = int(min(48, max(12, round(2 * math.pi * r / chord))))
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    L = float(np.linalg.norm(d))
    z = d / L
    x = np.cross(z, (1.0, 0, 0) if abs(z[0]) < 0.9 else (0, 1.0, 0))
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    return place(prism(ngon(0, 0, r, n), "z", 0, L), tuple(x), tuple(y), tuple(z), tuple(a))


def fillet_path(points, rad, step=30.0):
    """The polyline with every corner rounded to radius rad, as short chords of at most `step` deg."""
    pts = [np.asarray(p, float) for p in points]
    out = [pts[0]]
    for p0, p1, p2 in zip(pts, pts[1:], pts[2:]):
        l0, l1 = np.linalg.norm(p1 - p0), np.linalg.norm(p2 - p1)
        d0, d1 = (p1 - p0) / l0, (p2 - p1) / l1
        th = math.acos(max(-1.0, min(1.0, float(d0 @ d1))))
        if th < 1e-3:
            continue
        t = min(rad * math.tan(th / 2), 0.49 * l0, 0.49 * l1)
        re = t / math.tan(th / 2)
        a_, b_ = p1 - d0 * t, p1 + d1 * t
        nrm = d1 - (d1 @ d0) * d0
        c = a_ + nrm / np.linalg.norm(nrm) * re
        u, w = a_ - c, b_ - c
        n = max(1, math.ceil(math.degrees(th) / step))
        out += [c + (math.sin((1 - f) * th) * u + math.sin(f * th) * w) / math.sin(th)
                for f in np.linspace(0, 1, n + 1)]
    out.append(pts[-1])
    return [tuple(map(float, p)) for p in out]


def tube(points, r, rad=None):
    """A bent pipe: straight cylinders, each run on past the bend by just enough to close the joint
    (light: no balls at the bends). With rad, the corners are first rounded to that radius."""
    pts = [np.asarray(p, float) for p in (fillet_path(points, rad) if rad else points)]
    pts = [p for i, p in enumerate(pts) if i == 0 or np.linalg.norm(p - pts[i - 1]) > 1.0]
    ext = [0.0] * len(pts)
    for i in range(1, len(pts) - 1):
        d0, d1 = pts[i] - pts[i - 1], pts[i + 1] - pts[i]
        cosang = float(d0 @ d1 / (np.linalg.norm(d0) * np.linalg.norm(d1)))
        ext[i] = r * math.tan(math.acos(max(-1.0, min(1.0, cosang))) / 2) + 1.0
    out = []
    for i in range(len(pts) - 1):
        a_, b_ = pts[i], pts[i + 1]
        d = (b_ - a_) / np.linalg.norm(b_ - a_)
        out.append(rod(r, tuple(a_ - d * ext[i]), tuple(b_ + d * ext[i + 1])))
    return out


def jack(a, b, rb, rr, frac=0.6):
    """Hydraulic cylinder from a to b with cylindrical eye bosses (lighter than ball ends)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = (b - a) / np.linalg.norm(b - a)
    ax = np.cross(d, (0.0, 0.0, 1.0))
    if np.linalg.norm(ax) < 0.2:
        ax = np.cross(d, (0.0, 1.0, 0.0))
    ax /= np.linalg.norm(ax)
    j = a + (b - a) * frac
    barrel = [rod(rb, a, j), rod(rb * 1.12, j - (b - a) * 0.05, j)]
    rods = [rod(rr, j - (b - a) * 0.02, b, 20.0)]
    eyes = [rod(rb * 0.85, a - ax * rb * 0.75, a + ax * rb * 0.75),
            rod(rr * 1.35, b - ax * rr * 1.1, b + ax * rr * 1.1)]
    return barrel, rods + eyes


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


def hollow_frustum(bot, top, t):
    x0, x1, y0, y1, z0 = bot
    X0, X1, Y0, Y1, Z1 = top
    inner = frustum((x0 + t, x1 - t, y0 + t, y1 - t, z0 - 1), (X0 + t, X1 - t, Y0 + t, Y1 - t, Z1 + 1))
    return cut(frustum(bot, top), inner)


# =============================================================================== wheels

def wheel(a, m, xc, s, y_in, y_out, kind):
    def c(y):
        return (xc, s * y, ZC)
    D = 16.0

    def disc(r, ya, yb, n=48):
        """A round disc across the wheel: exact for the print, a fine polygon for the light GLB."""
        if m.print_mode:
            return cyl(r, c(ya), c(yb))
        return prism(ngon(xc, ZC, r, n), "y", *sorted((s * ya, s * yb)))
    body = disc(R - D, y_in + 30, y_out - 30).fuse(disc(R - D - 45, y_in, y_out)) if m.print_mode \
        else disc(R - D, y_in + 8, y_out - 8)
    if kind != "inner":
        body = cut(body, disc(292, y_out + 5, y_out - 130, 36))
    bore = disc(R - D - 12, y_in - 5, y_out + 5)
    if kind == "steer":
        w = (y_out - y_in - 60 - 2 * 14) / 3
        tread = []
        for k in range(3):
            lo, hi = y_in + 30 + k * (w + 14), y_in + 30 + k * (w + 14) + w
            rib = disc(R, lo, hi)
            tread.append(cut(rib, bore) if k == 2 else rib)
    else:
        n = 20
        p = 360.0 / n
        ym, half = (y_in + y_out) / 2, (y_out - y_in) / 2
        tread = []
        halves = (((y_in + 26, ym + 0.12 * half), 270 - 0.225 * p), ((ym - 0.12 * half, y_out - 26), 270 + 0.275 * p))
        if not m.print_mode:
            halves = (((y_in + 26, y_out - 26), 270 - 0.225 * p),)
        for (lo, hi), ph in [] if kind == "inner" else halves:
            y0, y1 = sorted((s * lo, s * hi))
            ring = prism(gear(xc, ZC, R, R - D - 4, n, ph), "y", y0, y1)
            tread.append(cut(ring, bore) if hi > y_out - 140 else ring)
    a.add("tyres", RUBBER, body, tread)
    if kind == "inner":
        return
    yf = y_out
    a.add("wheel_rims", WHEEL, cut(rod(300, c(yf - 135), c(yf - 8)), rod(300 - m.t(24), c(yf - 100), c(yf + 1))))
    y0, y1 = sorted((s * (yf - 97), s * (yf - 104)))
    a.add("wheel_hubs", DARK, [prism(ngon(xc + 205 * math.cos(t), ZC + 205 * math.sin(t), 34, 6), "y", y0, y1)
                               for t in np.linspace(0.3, 2 * math.pi + 0.3, 8, endpoint=False)])
    hub = 70.0 if kind == "steer" else 45.0
    a.add("wheel_hubs", DARK, rod(130, c(yf - 104), c(yf - 101 + hub)),
          cone(118, 60, c(yf - 101 + hub), c(yf - 101 + hub + 35)))
    nuts = []
    for t in np.linspace(0, 2 * math.pi, 10, endpoint=False):
        x, z = xc + 168 * math.cos(t), ZC + 168 * math.sin(t)
        nuts.append(prism(ngon(x, z, m.r(21), 6), "y", *sorted((s * (yf - 112), s * (yf - 70)))))
    a.add("wheel_nuts", STEEL, nuts)


def steer_axle(a, m, x):
    a.add("axles", DARK, box(x - 70, x + 70, -880, 880, 430, 560),
          [rod(90, (x, s * 860, 410), (x, s * 860, 640)) for s in (1, -1)],
          [rod(165, (x, s * 830, ZC), (x, s * 950, ZC)) for s in (1, -1)],
          [bar((x, s * 850, 470), (x - 280, s * 790, 470), 50, 50) for s in (1, -1)])
    a.add("tie_rods", BLACK, cyl(m.r(28), (x - 280, -800, 470), (x - 280, 800, 470)))
    for s in (1, -1):
        y0, y1 = sorted((s * 440, s * 530))
        a.add("springs", BLACK, prism(band([(x - 760, 720), (x - 380, 625), (x, 595), (x + 380, 625),
                                            (x + 760, 720)], 38), "y", y0, y1))
        y0, y1 = sorted((s * 425, s * 545))
        a.add("spring_hangers", DARK, [box(xx - 55, xx + 55, y0, y1, 680, 790) for xx in (x - 760, x + 760)],
              box(x - 110, x + 110, y0, y1, 545, 580),
              [cyl(m.r(16), (xx, s * 485, 520), (xx, s * 485, 640)) for xx in (x - 85, x + 85)])


# =============================================================================== cab (local)

def cab(c, m):
    hr = m.r(18)
    shell = loft_sections(CAB)
    arch = [cyl(650, (0, s * 700, ZC), (0, s * 1400, ZC)) for s in (1, -1)]
    if m.print_mode:
        shell = cut(shell, *arch)
    else:
        win = [prism([(380, 1880), (xfr(1880) - 230, 1880), (xfr(2600) - 230, 2600), (380, 2600)], "y",
                     s * 1080, s * 1300) for s in (1, -1)]
        ws = box(1150, 1600, -WS_Y, WS_Y, WS_Z0, WS_Z1)
        shell = cut(shell, loft_sections(CAB_IN), *arch, *win, ws)
    c.add("cab", BODY, shell)

    for s in (1, -1):
        y0, y1 = sorted((s * 1150, s * 1215))
        c.add("fenders", BLACK, prism(band(arc_pts(0, ZC, 680, 14, 166, 28), 30), "y", y0, y1))
        y0, y1 = sorted((s * 700, s * 1180))
        c.add("fenders", BLACK, prism(band(arc_pts(0, ZC, 650, 18, 162, 24), m.t(16) / 2), "y", y0, y1))
        wall = clip_poly(arc_pts(0, ZC, 655, 0, 180, 24), -700, 700, 880, 2000)
        y0, y1 = sorted((s * 692, s * 712))
        c.add("fenders", BLACK, prism(wall, "y", y0, y1))

    # windscreen, rubber, wipers
    d = np.array([xfr(WS_Z1) - xfr(WS_Z0), 0.0, WS_Z1 - WS_Z0])
    d /= np.linalg.norm(d)
    nrm = (float(d[2]), 0.0, float(-d[0]))
    g = m.t(12)
    zg0, zg1 = WS_Z0 - 15, WS_Z1 + 15
    c.add("glass", GLASS, bar((xfr(zg0), 0, zg0), (xfr(zg1), 0, zg1), 2 * (WS_Y + 25), g, up=nrm))
    fr = m.t(18)
    frame = [bar((xfr(z), -WS_Y - 40, z), (xfr(z), WS_Y + 40, z), 50, fr, up=nrm) for z in (WS_Z0 - 10, WS_Z1 + 10)]
    frame += [bar((xfr(WS_Z0 - 30), y, WS_Z0 - 30), (xfr(WS_Z1 + 30), y, WS_Z1 + 30), 50, fr, up=nrm)
              for y in (-WS_Y - 15, WS_Y + 15)]
    c.add("cab_trim", BLACK, frame)
    for y0, y1 in ((960.0, 140.0), (-80.0, -900.0)):
        za, zb = WS_Z0 + 25, WS_Z0 + 55
        o = np.array(nrm) * (g / 2 + 6)
        c.add("cab_trim", BLACK, bar(np.array((xfr(za), y0, za)) + o, np.array((xfr(zb), y1, zb)) + o,
                                     m.t(22), m.t(16), up=nrm),
              cyl(m.r(22), np.array((xfr(za), y0, za)) - o, np.array((xfr(za), y0, za)) + 1.6 * o))

    for s in (1, -1):
        def xw(z):
            return xfr(z) - 230
        pane = [(360, 1860), (xw(1860) + 20, 1860), (xw(2620) + 20, 2620), (360, 2620)]
        y0, y1 = sorted((s * 1182, s * (1182 + max(m.t(22), 22))))
        c.add("glass", GLASS, prism(pane, "y", y0, y1))
        fr = m.t(14)
        c.add("cab_trim", BLACK, side_bar(360, 1880, xw(1880), 1880, s, 44, fr),
              side_bar(360, 2600, xw(2600), 2600, s, 44, fr),
              side_bar(380, 1860, 380, 2620, s, 44, fr), side_bar(xw(1860), 1860, xw(2620), 2620, s, 44, fr))
        sw, sh = m.t(14), m.t(20)
        zk = (1130.0, 1700.0, 2650.0, 2700.0)

        def xd(z):
            return float(np.interp(z, (1130.0, 2700.0), (xfr(1130) - 190, xfr(2700) - 180)))
        c.add("cab_trim", BLACK, [side_bar(330, z0, 330, z1, s, sw, sh) for z0, z1 in zip(zk, zk[1:])],
              [side_bar(xd(z0), z0, xd(z1), z1, s, sw, sh) for z0, z1 in zip(zk, zk[1:])],
              side_bar(330 - sw / 2, 1130, xd(1130) + sw / 2, 1130, s, sw, sh),
              [side_bar(xfr(z) - 200, z, xfr(z) - 160, z, s, 100, m.t(30)) for z in (1350, 2350)],
              side_bar(-200, 2050, 180, 2050, s, 520, m.t(10)))
        c.add("cab_chrome", CHROME, side_bar(420, 1700, 560, 1700, s, 40, m.t(24)))
        ya, yb = s * (hw(1500) - 5), s * (hw(1500) + 55)
        c.add("cab_chrome", CHROME, tube([(xfr(1300) - 120, ya, 1300), (xfr(1300) - 120, yb, 1300),
                                          (xfr(2200) - 120, yb, 2200), (xfr(2200) - 120, ya, 2200)], hr),
              tube([(250, ya, 1350), (250, yb, 1350), (250, yb, 2300), (250, ya, 2300)], hr))
        c.add("grey_trim", GREY, [side_bar(-170, z, 150, z, s, 26, m.t(18)) for z in range(1840, 2280, 62)])
        c.add("amber_lamps", AMBER, side_bar(1180, 1250, 1290, 1250, s, 45, m.t(16)))
        y0, y1 = sorted((s * 960, s * 1205))
        c.add("cab_steps", DARK, box(760, 760 + m.t(35), y0, y1, 400, 900), box(1300 - m.t(35), 1300, y0, y1, 400, 900),
              box(760, 1300, *sorted((s * 960, s * (960 + m.t(35)))), 400, 900))
        y0, y1 = sorted((s * 980, s * 1218))
        c.add("step_treads", GALV, box(790, 1270, y0, y1, 420, 460), box(790, 1270, y0, y1, 760, 800))

    if not m.print_mode:
        c.add("cab_interior", DARK, box(1130, 1390, -1145, 1145, 1120, 1720), box(-340, 1150, -340, 340, 1120, 1420),
              [box(250, 760, y - 260, y + 260, 1120, 1580) for y in (600.0, -600.0)],
              [box(150, 300, y - 260, y + 260, 1550, 2300) for y in (600.0, -600.0)],
              cyl(220, (1000, 600, 2000), (1015, 600, 1980)), cyl(35, (1000, 600, 2000), (1250, 600, 1700)))

    c.add("cab_trim", BLACK, bar((xfr(1060), 0, 1060), (xfr(1620), 0, 1620), 1700, m.t(24), up=(1, 0, 0)))
    c.add("grey_trim", GREY, [box(xfr(z) + 6, xfr(z) + 6 + m.t(14), -800, 800, z - 20, z + 20)
                              for z in np.arange(1120, 1600, 78)])
    c.add("bumper", GREY, cbox(1370, 1545, -1215, 1215, 440, 905, 40, axis="y"))
    c.add("cab_trim", BLACK, cbox(1380, 1535, -1185, 1185, 360, 470, 25, axis="y"))
    c.add("step_treads", GALV, [box(1455, 1548, *sorted((s * 250, s * 700)), 898, 916) for s in (1, -1)])
    for s in (1, -1):
        y0, y1 = sorted((s * 700, s * 1150))
        c.add("cab_trim", BLACK, box(1540, 1554, y0, y1, 660, 860), cyl(62, (1538, s * 950, 560), (1551, s * 950, 560)))
        c.add("lamps", LED, [cyl(70, (1548, s * y, 760), (1561, s * y, 760)) for y in (790.0, 950.0)],
              cyl(48, (1540, s * 950, 560), (1557, s * 950, 560)))
        c.add("cab_chrome", CHROME, [cyl(82, (1546, s * y, 760), (1556, s * y, 760)) for y in (790.0, 950.0)])
        y0, y1 = sorted((s * 1050, s * 1135))
        c.add("amber_lamps", AMBER, box(1549, 1560, y0, y1, 690, 830))

    zv = 2690.0
    xv = xfr(zv)
    c.add("cab", BODY, prism([(xv - 40, 2650), (xv + 190, 2690), (xv + 190, 2690 + m.t(35)), (xfr(2790) - 40, 2790)],
                             "y", -1120, 1120))
    c.add("amber_lamps", AMBER, [box(xv + 120, xv + 175, y - 40, y + 40, 2715, 2752) for y in (-900, -300, 300, 900)])
    c.add("cab", BODY, cbox(200, 560, -260, 260, 3010, 3068, 22))
    c.add("cab_trim", BLACK, box(190, 570, -270, 270, 3015, 3032), cyl(95, (-120, -500, 3020), (-120, -500, 3075)))
    c.add("amber_lamps", AMBER, cyl(78, (-120, -500, 3070), (-120, -500, 3195)), sphere(78, (-120, -500, 3195)))

    for s in (1, -1):
        xm, ym = 1300.0, s * 1440
        y0, y1 = sorted((s * 1365, s * 1535))
        c.add("cab_trim", BLACK, tube([(1150, s * (hw(2450) - 25), 2450), (xm, ym, 2470)], hr),
              tube([(1150, s * (hw(1850) - 25), 1850), (xm, ym, 1850)], hr),
              cyl(hr, (xm, ym, 1820), (xm, ym, 2500)),
              box(xm - 35, xm + 60, y0, y1, 2060, 2470), box(xm - 35, xm + 60, y0, y1, 1830, 2020))
        y0, y1 = sorted((s * 1378, s * 1522))
        c.add("cab_chrome", CHROME, box(xm - 47, xm - 30, y0, y1, 2075, 2455), box(xm - 47, xm - 30, y0, y1, 1845, 2005))
    c.add("cab_trim", BLACK, tube([(1080, -950, 3005), (1340, -1000, 3090), (1480, -1000, 2990)], hr),
          box(1440, 1540, -1120, -880, 2850, 3010))
    c.add("cab_chrome", CHROME, box(1430, 1450, -1105, -895, 2865, 2995))
    # air intake snorkel behind the cab
    c.add("cab_trim", BLACK, cyl(110, (-500, -900, 1560), (-500, -900, 3060)),
          cyl(140, (-500, -900, 3050), (-500, -900, 3120)), cone(140, 60, (-500, -900, 3120), (-500, -900, 3180)),
          [box(-520, -360, -930, -870, z - 30, z + 30) for z in (1900, 2700)])
    c.add("engine", DARK, box(-380, 950, -360, 360, 480, 1100))


# =============================================================================== build

def build(m):
    global LIGHT
    LIGHT = not m.print_mode
    a = Acc()

    # =========================================================== running gear
    for s in (1, -1):
        for x in (XF1, XF2):
            wheel(a, m, x, s, F_IN, F_OUT, "steer")
        for x in (XR1, XR2):
            wheel(a, m, x, s, *DI, "inner")
            wheel(a, m, x, s, *DO, "outer")
    steer_axle(a, m, XF1)
    steer_axle(a, m, XF2)
    axles = []
    for x in (XR1, XR2):
        axles += [rod(140, (x, -600, ZC), (x, 600, ZC)), rod(270, (x - 170, 0, ZC), (x + 170, 0, ZC)),
                  rod(150, (x, 0, ZC), (x + 360, 0, ZC + 40))]
        axles += [rod(230, (x, s * 560, ZC), (x, s * 1140, ZC)) for s in (1, -1)]
    a.add("axles", DARK, axles)
    for s in (1, -1):
        y0, y1 = sorted((s * 465, s * 575))
        a.add("springs", BLACK, prism(band([(XR1 + 60, ZC + 175), (XRB, 830), (XR2 - 60, ZC + 175)], [45, 70, 45]),
                                      "y", y0, y1),
              [box(x - 120, x + 120, s * 455, s * 585, ZC + 110, ZC + 165) for x in (XR1, XR2)],
              box(XRB - 170, XRB + 170, s * 425, s * 600, 700, 1060),
              [bar((XRB, s * 520, 690), (x, s * 520, ZC - 40), 70, 70, up=(0, 1, 0)) for x in (XR1 + 250, XR2 - 250)])
    a.add("axles", STEEL, cyl(95, (XRB, -640, 830), (XRB, 640, 830)))
    a.add("prop_shafts", DARK, cyl(m.r(55), (XF1 - 950, 0, 720), (XR1 + 360, 0, ZC + 40)),
          cyl(m.r(50), (XR1 - 150, 0, ZC + 60), (XR2 + 360, 0, ZC + 40)),
          [cyl(m.r(75), (p[0] - 50, p[1], p[2]), (p[0] + 50, p[1], p[2]))
           for p in ((XF1 - 950, 0, 720), (XR1 + 360, 0, ZC + 40), (XR2 + 360, 0, ZC + 40))],
          box(XF1 - 960, XF1 - 370, -260, 260, 560, 960))

    # =========================================================== frame and subframe
    a.add("frame", BLACK, [box(XRR, XFR, s * RY0, s * RY1, RZ0, RZ1) for s in (1, -1)],
          [box(x - 40, x + 40, -RY1, RY1, RZ0 + 40, RZ1 - 40) for x in (XFR - 40, 3000, 1000, XRB, -4300)],
          box(XRR, XRR + 60, -RY1, RY1, RZ0, RZ1))
    sub = [box(XRR, 2400, s * SY0, s * SY1, SZ0, SZ1) for s in (1, -1)]
    sub += [box(x - 50, x + 50, -SY1, SY1, SZ1 - 120, SZ1) for x in (-4700, -2400, -300, 1800)]
    a.add("body", BODY, sub)
    # front outrigger box (X-frame) behind the cab
    a.add("body", BODY, box(2250, 3500, -SY1, SY1, SZ0, 1220), cbox(2250, 3500, -1100, 1100, 1180, 1620, 40))
    a.add("black_trim", BLACK, [box(2240, 3510, *sorted((s * 1080, s * 1112)), 1250, 1280) for s in (1, -1)])

    # =========================================================== cab
    c = Acc()
    cab(c, m)
    a.merge(c, XF1)

    # mudguards over the second steer axle and the tandem, mud flaps
    for s in (1, -1):
        y0, y1 = sorted((s * 905, s * 1285))
        a.add("mudguards", BLACK, prism(band(arc_pts(XF2, ZC, 610, 25, 155, 16), m.t(12) / 2), "y", y0, y1))
        y0, y1 = sorted((s * 520, s * 920))
        a.add("mudguard_brackets", DARK, box(XF2 - 40, XF2 + 40, y0, y1, 1060, ZC + 616))
        path = arc_pts(XR1, ZC, 615, 14, 90, 10) + arc_pts(XR2, ZC, 615, 90, 166, 10)
        y0, y1 = sorted((s * 600, s * 1275))
        a.add("mudguards", BLACK, prism(band(path, m.t(12) / 2), "y", y0, y1))
        y0, y1 = sorted((s * 425, s * 720))
        a.add("mudguard_brackets", DARK, [box(x - 40, x + 40, y0, y1, 1050, ZC + 618) for x in (XR1 - 250, XR2 + 250)])
        xe = XR2 + 615 * math.cos(math.radians(166))
        y0, y1 = sorted((s * 640, s * 1265))
        a.add("mud_flaps", RUBBER, box(xe - m.t(22), xe, y0, y1, 280, ZC + 175))
        y0, y1 = sorted((s * 960, s * 1230))
        a.add("mud_flaps", RUBBER, box(XF2 - 610 - m.t(20), XF2 - 610, y0, y1, 300, 760))
        y0, y1 = sorted((s * 425, s * 1230))
        a.add("mudguard_brackets", DARK, box(XF2 - 650, XF2 - 590, y0, y1, 720, 775))
        a.add("amber_lamps", AMBER, [box(x - 45, x + 45, s * 1272, s * 1284, ZC + 560, ZC + 600)
                                     for x in (XR1 + 200, XR2 - 200)])

    # =========================================================== tanks and boxes on the chassis
    a.add("fuel_tank", CHROME, cbox(250, 1350, 480, 1090, 560, 1050, 90))
    a.add("black_trim", BLACK, [box(x, x + 50, 470, 1100, 550, 1060) for x in (450, 1100)],
          [box(x - 10, x + 60, 425, 490, 880, 1000) for x in (450, 1100)],
          cyl(65, (1250, 950, 1040), (1250, 950, 1100)))
    a.add("black_trim", BLACK, box(-900, 100, 470, 1150, 600, 1100), box(-910, 110, 455, 1160, 1090, 1120))
    a.add("toolbox_latches", GALV, [box(x - 40, x + 40, 1145, 1165, 1000, 1060) for x in (-650, -150)])
    a.add("black_trim", BLACK, box(200, 800, -1080, -470, 640, 1020), box(180, 820, -1095, -425, 1010, 1045))
    a.add("air_tanks", GALV, [cyl(130, (-900, -y, 760), (-100, -y, 760)) for y in (650, 930)],
          [box(x, x + 50, -1065, -425, 640, 900) for x in (-800, -250)])
    y0, y1 = -1160, -1160 + m.t(35)
    a.add("side_guards", GALV, [box(-900, 1550, y0, y1, z, z + 100) for z in (480, 760)],
          [box(x - 30, x + 30, -1160, -1100, 470, 870) for x in (-850, 1480)])
    a.add("mudguard_brackets", DARK, [box(x - 30, x + 30, -1150, -400, 780, 840) for x in (-850, 1480)])

    # water tank (left), on the subframe
    a.add("water_tank", STEEL, cbox(-1000, 1500, 500, 1200, 1340, 2000, 70))
    a.add("black_trim", BLACK, [box(x - 30, x + 30, 490, 1212, 1330, 2012) for x in (-600, 250, 1100)],
          cyl(90, (200, 900, 1990), (200, 900, 2060)), box(-1010, 1510, 490, 1212, 1320, 1370))
    a.add("water_tank_gauge", GLASS, box(-850, -790, 1195, 1212, 1450, 1900))
    # hydraulic oil tank and oil cooler (right)
    a.add("body", BODY, cbox(500, 1600, -1150, -500, 1240, 1680, 50))
    a.add("black_trim", BLACK, box(490, 1610, -1160, -490, 1230, 1280), cyl(70, (1300, -1000, 1670), (1300, -1000, 1710)))
    a.add("water_tank_gauge", GLASS, box(700, 760, -1162, -1145, 1320, 1600))
    a.add("body", BODY, box(-800, 300, -1150, -500, 1240, 1680))
    a.add("black_trim", BLACK, box(-740, 240, -1162, -1140, 1290, 1630))
    a.add("grey_trim", GREY, [box(-720, 220, -1172, -1155, z, z + 20) for z in range(1310, 1620, 45)])

    # =========================================================== turret
    a.add("slewing_ring", DARK, rod(640, (X_T, 0, 1600), (X_T, 0, 1760)))
    a.add("pins", STEEL, rod(665, (X_T, 0, 1640), (X_T, 0, 1700)))
    a.add("slew_drives", BLACK, [cyl(110, (X_T + dx, dy, 1600), (X_T + dx, dy, 2000)) for dx, dy in ((-450, 520), (-450, -520))],
          [cyl(130, (X_T + dx, dy, 1960), (X_T + dx, dy, 2010)) for dx, dy in ((-450, 520), (-450, -520))])
    a.add("turret", BODY, frustum((X_T - 560, X_T + 520, -520, 520, 1740), (X_T - 330, X_T + 330, -300, 300, 2860)))
    lug = [(X_T - 260, 2700), (X_T + 260, 2700)] + arc_pts(X_T, Z_PIV, 260, 0, 180, 12)
    a.add("turret", BODY, [prism(lug, "y", *sorted((s * 222, s * 300))) for s in (1, -1)])
    a.add("pins", STEEL, cyl(95, (X_T, -330, Z_PIV), (X_T, 330, Z_PIV)))

    # =========================================================== boom sections
    for k in (1, 2, 3, 4):
        x0, x1, yc, zb, w0, h0, w1, h1 = SEC[k]
        # the box girder, with top and bottom flanges standing a little proud of the webs
        c0, c1 = x0 + math.copysign(40, x1 - x0), x1 - math.copysign(40, x1 - x0)
        wc0, hc0 = sec_at(k, c0)
        wc1, hc1 = sec_at(k, c1)
        a.add(f"boom_section_{k}", BODY, xbeam(x0, x1, yc, zb, zb + h0, zb, zb + h1, w0, w1),
              xbeam(c0, c1, yc, zb + hc0 - 26, zb + hc0 + 5, zb + hc1 - 26, zb + hc1 + 5, wc0 + 26, wc1 + 26),
              xbeam(c0, c1, yc, zb - 5, zb + 26, zb - 5, zb + 26, wc0 + 26, wc1 + 26))
        # orange stripe along both sides, above the delivery line
        i0, i1 = x0 + math.copysign(260, x1 - x0), x1 - math.copysign(200, x1 - x0)
        w_0, h_0 = sec_at(k, i0)
        w_1, h_1 = sec_at(k, i1)
        hs = 0.075 * h_0 + 8
        a.add("boom_stripes", ACCENT, xbeam(i0, i1, yc, zb + 0.74 * h_0 - hs, zb + 0.74 * h_0 + hs,
                                            zb + 0.74 * h_1 - hs, zb + 0.74 * h_1 + hs, w_0, w_1, grow=7))

    # knuckle yokes: rear 1-2 and 3-4 (Z folds), front 2-3 (roll fold across to the left)
    def yoke(xa, xb, zlo, zhi, ys):
        """Side plates of a rear knuckle: from xa back to xb, its rear corners well rounded."""
        rr = 0.36 * (zhi - zlo)
        prof = ([(xa, zlo)] + arc_pts(xb + rr, zlo + rr, rr, 270, 180, 8)
                + arc_pts(xb + rr, zhi - rr, rr, 180, 90, 8) + [(xa, zhi)])
        return [prism(prof, "y", *sorted(y)) for y in ys]

    a.add("boom_knuckles", BODY, yoke(-4600, -5330, 2770, 3880, [(-245, -180), (180, 245)]),
          yoke(-4100, -4830, 2770, 3840, [(Y3 - 195, Y3 - 128), (Y3 + 128, Y3 + 195)]))
    a.add("pins", STEEL, [cyl(75, (-5080, -270, z), (-5080, 270, z)) for z in (3030, 3620)],
          [cyl(70, (-4580, Y3 - 220, z), (-4580, Y3 + 220, z)) for z in (3010, 3600)])
    # front knuckle 2-3: an L-shaped casting carrying section 2's tip (upper) and section 3's root (lower)
    a.add("boom_knuckles", BODY, cbox(3150, 3580, -250, Y3 + 190, ZA + 10, ZB + 12, 40, axis="y"),
          cbox(3150, 3580, -200, 200, ZB - 20, ZB + 360, 40, axis="y"))
    a.add("pins", STEEL, cyl(80, (3380, -280, ZA + 300), (3380, Y3 + 220, ZA + 300)),
          cyl(70, (3380, -230, ZB + 180), (3380, 230, ZB + 180)))
    # base of section 1 between the turret lugs, with the lift-cylinder bracket underneath
    a.add("boom_knuckles", BODY, box(450, 720, -140, 140, ZA - 150, ZA + 20))

    # hydraulic cylinders: lift (turret), fold 1-2 under section 1, fold 2-3 on top of section 2,
    # fold 3-4 under section 3
    def top2(x):
        return ZB + sec_at(2, x)[1]

    barrels, rods = [], []
    for (p, q, rb, rr, f) in (((X_T - 420, 0, 2050), (585, 0, ZA - 80), 140, 82, 0.6),
                              ((-2900, 0, ZA - 75), (-4560, 0, ZA - 60), 95, 55, 0.6),
                              ((1300, 0, top2(1300) + 70), (3200, 0, top2(3200) + 70), 85, 50, 0.6),
                              ((-2700, Y3, ZA - 70), (-4150, Y3, ZA - 60), 80, 48, 0.6)):
        b, r_ = jack(p, q, rb, rr, f)
        barrels.append(b)
        rods.append(r_)
    a.add("boom_rams", BLACK, barrels)
    a.add("boom_ram_rods", CHROME, rods)
    # ram anchors: lugs welded under and on the sections
    a.add("black_trim", BLACK, box(-3000, -2800, -70, 70, ZA - 150, ZA + 15), box(-4620, -4480, -70, 70, ZA - 130, ZA + 15),
          box(1200, 1400, -60, 60, top2(1300) - 20, top2(1300) + 90),
          box(3120, 3240, -60, 60, top2(3200) - 20, top2(3200) + 90),
          box(-2800, -2600, Y3 - 60, Y3 + 60, ZA - 140, ZA + 15), box(-4220, -4080, Y3 - 60, Y3 + 60, ZA - 120, ZA + 15))
    # hydraulic hoses along section 1 (left side) and section 2 (top)
    hoses = []
    for dz in (0, 90):
        hoses.append(tube([(X_T - 250, 300, 2600 + dz), (2600, sec_at(1, 2600)[0] / 2 + 12, ZA + 180 + dz),
                           (-2700, sec_at(1, -2700)[0] / 2 + 12, ZA + 180 + dz), (-2850, 50, ZA - 40)], m.r(22)))
    hoses.append(tube([(3150, 130, top2(3150) + 10), (1450, 130, top2(1450) + 10)], m.r(22)))
    a.add("hoses", BLACK, hoses)

    # =========================================================== delivery line
    def seg(k, s, xa, xb):
        return (sec_pipe(k, xa, s), sec_pipe(k, xb, s))

    p1a, p1b = seg(1, -1, 2700, -4600)
    p2a, p2b = seg(2, -1, -4600, 3150)
    p3a, p3b = seg(3, 1, 3150, -4150)
    p4a, p4b = seg(4, 1, -4150, 5250)
    line = []
    # from the S-valve up over the hopper, along the right of the body and up the turret
    line.append(tube([(-5700, -150, 1180), (-5920, -150, 1180), (-5920, -750, 1780), (2150, -750, 1780),
                      (2470, p1a[1], 2750), (2470, p1a[1], p1a[2]), p1a], RP, 200))
    # along the boom, with an elbow round every knuckle

    def elbow(pa, pb, xr):
        """Half-round elbow reaching back to xr behind pa and pb, which lie on the same side."""
        r = abs(pb[2] - pa[2]) / 2
        ys = (pa[1] + pb[1]) / 2
        return fillet_path([pa, (xr, ys, pa[2]), (xr, ys, pb[2]), pb], r)

    line.append(tube([p1a, p1b], RP))
    line.append(tube(elbow(p1b, p2a, -5330), RP))
    line.append(tube([p2a, p2b], RP))
    line.append(tube([p2b, (3700, p2b[1], p2b[2]), (3700, p2b[1], 3240), (3700, p3a[1], 3240), p3a], RP, 140))
    line.append(tube([p3a, p3b], RP))
    line.append(tube(elbow(p3b, p4a, -4820), RP))
    line.append(tube([p4a, p4b, (5440, p4b[1], p4b[2]), (5500, p4b[1] - 10, p4b[2] - 120)], RP, 120))
    a.add("delivery_line", PIPE, line)
    # clamp collars and brackets
    clamps = []
    for k, s, xs in ((1, -1, (2200, 600, -1000, -2600, -4200)), (2, -1, (-4200, -2600, -1000, 600, 2200)),
                     (3, 1, (2600, 1000, -600, -2200, -3800)), (4, 1, (-3800, -2200, -600, 1000, 2600, 4200))):
        x0, x1, yc, zb, *_ = SEC[k]
        for x in xs:
            p = sec_pipe(k, x, s)
            w, h = sec_at(k, x)
            clamps.append(prism(ngon(p[1], p[2], RP + 16, 10), "x", x - 30, x + 30))
            clamps.append(box(x - 35, x + 35, *sorted((yc + s * (w / 2 - 15), p[1])), p[2] - 30, p[2] + 30))
    for p in ((-5400, -750, 1780), (-2700, -750, 1780), (-1100, -750, 1780), (1900, -750, 1780)):
        clamps.append(prism(ngon(p[1], p[2], RP + 16, 10), "x", p[0] - 30, p[0] + 30))
        clamps.append(box(p[0] - 40, p[0] + 40, -760, -SY1 + 20, SZ1 - 20, 1750))
    # couplings at the knuckles
    for p in (p1a, p1b, p2a, p2b, p3a, p3b, p4a, p4b):
        clamps.append(prism(ngon(p[1], p[2], RP + 22, 10), "x", p[0] - 40, p[0] + 40))
    a.add("line_clamps", BLACK, clamps)
    # end hose hanging from the tip elbow in front of the cab
    eh = (5500, p4b[1] - 10, p4b[2] - 120)
    a.add("pins", STEEL, cyl(RP + 22, (eh[0], eh[1], eh[2] + 20), (eh[0] + 25, eh[1], eh[2] - 70)))
    a.add("end_hose", RUBBER, tube([(eh[0] + 10, eh[1], eh[2] - 40), (5590, eh[1] - 5, 3000), (5615, eh[1] - 20, 2400),
                                    (5630, eh[1] - 40, 1850)], 72, 600))
    a.add("pins", STEEL, cyl(85, (5630, eh[1] - 40, 1880), (5632, eh[1] - 40, 1800)))
    # work lamp on the tip of section 4, aimed at the end hose
    xt, yt = SEC[4][1], SEC[4][2]
    a.add("black_trim", BLACK, box(xt - 180, xt - 40, yt - 70, yt + 70, ZB + 240, ZB + 330))
    a.add("lamps", LED, box(xt - 45, xt - 30, yt - 55, yt + 55, ZB + 255, ZB + 315))

    # =========================================================== boom rests
    a.add("body", BODY, [box(3440, 3570, y - 70, y + 70, 1600, ZA + 15) for y in (-150.0, Y3)],
          box(3440, 3570, -230, Y3 + 90, 2350, 2460))
    a.add("body", BODY, [box(-2460, -2320, y - 70, y + 70, SZ1 - 10, ZA - 40) for y in (0.0, Y3)],
          box(-2460, -2320, -200, Y3 + 170, ZA - 120, ZA - 30))
    a.add("rest_pads", RUBBER, box(-2470, -2310, -190, Y3 + 160, ZA - 40, ZA + 6))

    # =========================================================== outriggers
    def leg(m_, e, tag):
        x, y = e
        a.add("outrigger_legs", BODY, box(x - 150, x + 150, y - 150, y + 150, 640, 1660))
        a.add("black_trim", BLACK, box(x - 160, x + 160, y - 160, y + 160, 1640, 1690),
              box(x - 160, x + 160, y - 160, y + 160, 640, 690))
        a.add("outrigger_jacks", CHROME, rod(85, (x, y, 110), (x, y, 660)))
        a.add("pins", STEEL, rod(200, (x, y, 66), (x, y, 132)), rod(120, (x, y, 125), (x, y, 190)))
        a.add("outrigger_pads", PAD, cbox(x - 350, x + 350, y - 350, y + 350, -2, 74, 20))
        a.add("black_trim", BLACK, [box(x + dx - 150, x + dx + 150, y - 25, y + 25, 70, 92) for dx in (-170, 170)])

    for s in (1, -1):
        # outrigger control station on the side of the outrigger box: levers and a gauge
        ys = s * 1100
        a.add("black_trim", BLACK, box(2380, 2780, *sorted((ys - s * 20, ys + s * 25)), 1300, 1560))
        a.add("cab_chrome", CHROME, [cyl(m.r(14), (x, ys, 1420), (x, ys + s * 170, 1520)) for x in (2450, 2530, 2610, 2690)])
        a.add("tail_lights", RED, [cyl(m.r(30), (x, ys + s * 160, 1510), (x, ys + s * 200, 1530)) for x in (2450, 2530, 2610, 2690)])
        # front: X-type telescopic legs, out diagonally forwards from the outrigger box
        S = (FRONT_S[0], s * FRONT_S[1])
        E = (FRONT_E[0], s * FRONT_E[1])
        d = np.subtract(E, S)
        L = float(np.linalg.norm(d))

        def at_y(yv):
            return (yv - S[1]) / (E[1] - S[1])
        zo = 1400.0
        o0, o1 = along(S, E, at_y(s * 900)), along(S, E, at_y(s * 1800))
        a.add("outrigger_beams", BODY, bar((*o0, zo), (*o1, zo), 330, 300))
        a.add("black_trim", BLACK, bar((*along(S, E, at_y(s * 1780)), zo), (*o1, zo), 350, 320))
        i0, i1 = along(S, E, at_y(s * 1700)), along(S, E, 1 + 120 / L)
        a.add("outrigger_beams", BODY, bar((*i0, zo), (*i1, zo), 250, 230))
        a.add("outrigger_tips", ACCENT, [bar((*along(S, E, f0), zo), (*along(S, E, f1), zo), 262, 242)
                                         for f0, f1 in ((1 - 900 / L, 1 - 700 / L), (1 - 500 / L, 1 - 300 / L))])
        leg(m, E, "front")
        # rear: swing legs on a pivot post on the subframe
        S = (REAR_S[0], s * REAR_S[1])
        E = (REAR_E[0], s * REAR_E[1])
        L = float(np.hypot(E[0] - S[0], E[1] - S[1]))
        a.add("body", BODY, box(S[0] - 200, S[0] + 200, *sorted((s * 420, s * 760)), 1150, 1460))
        a.add("pins", STEEL, cyl(105, (S[0], S[1], 1120), (S[0], S[1], 1500)))
        a.add("outrigger_beams", BODY, bar((*S, 1320), (*along(S, E, 1 + 120 / L), 1320), 300, 280))
        a.add("outrigger_tips", ACCENT, [bar((*along(S, E, f0), 1320), (*along(S, E, f1), 1320), 312, 292)
                                         for f0, f1 in ((1 - 900 / L, 1 - 700 / L), (1 - 500 / L, 1 - 300 / L))])
        leg(m, E, "rear")
        b, r_ = jack((-3150, s * 470, 1250), (*along(S, E, 0.42), 1250), 70, 40, 0.6)
        a.add("boom_rams", BLACK, b)
        a.add("boom_ram_rods", CHROME, r_)

    # =========================================================== pump: hopper, S-valve, cylinders
    hx0, hx1 = -5000.0, -5780.0
    outer = [(hx0 + 60, 1500), (hx1, 1500), (hx1, 1250), (-5600, 900), (-5150, 840), (hx0 + 60, 920)]
    inner = [(hx0 + 10, 1560), (hx1 + 50, 1560), (hx1 + 50, 1262), (-5578, 945), (-5165, 890), (hx0 + 10, 960)]
    hop = cut(prism(outer, "y", -880, 880), prism(inner, "y", -830, 830))
    a.add("hopper", GREY, hop, box(-4960, -4900, -880, 880, 880, 1500))
    gr = [box(x - 15, x + 15, -850, 850, 1460, 1515) for x in np.arange(-5110, -5730, -90)]
    gr += [box(-5770, -5010, y - 15, y + 15, 1470, 1525) for y in (-560, 0, 560)]
    gr += [box(hx1 - 15, hx0 - 30, -895, -860, 1490, 1530), box(hx1 - 15, hx0 - 30, 860, 895, 1490, 1530)]
    a.add("hopper_grille", BLACK, gr)
    if not m.print_mode:
        a.add("hopper_inside", Finish(rgb("#5d5f60"), rough=0.9), box(-5600, -5100, -820, 820, 930, 960))
    ag = [cyl(55, (-5360, -860, 1060), (-5360, 860, 1060))]
    ag += [bar((-5360, y, 1060), (-5360 + 190 * math.cos(t), y, 1060 + 190 * math.sin(t)), 40, 60)
           for y, t in zip(np.arange(-650, 700, 260), np.linspace(0, 5 * math.pi / 3, 6))]
    a.add("agitator", DARK, ag)
    a.add("agitator_motors", BLACK, [cyl(110, (-5360, s * 870, 1060), (-5360, s * 1010, 1060)) for s in (1, -1)])
    # S-valve outlet housing, lever and shift cylinders on the rear wall
    a.add("s_valve", DARK, cyl(150, (-5770, -150, 1180), (-5860, -150, 1180)),
          cyl(120, (-5770, 250, 1250), (-5850, 250, 1250)), box(-5800, -5760, -760, 760, 1050, 1400))
    a.add("s_valve_lever", BLACK, bar((-5880, 250, 1250), (-5880, 250, 980), 80, 60, up=(1, 0, 0)))
    for s in (1, -1):
        b, r_ = jack((-5830, s * 700, 1350), (-5880, 250 + s * 120, 990), 60, 35, 0.6)
        a.add("boom_rams", BLACK, b)
        a.add("boom_ram_rods", CHROME, r_)
    a.add("hopper_door", BODY, box(-5800, -5772, -420, 420, 1290, 1470))
    # material cylinders, water box, drive cylinders under the body
    a.add("pump_cylinders", CHROME, [rod(125, (-5010, y, 1120), (-3380, y, 1120)) for y in (-185.0, 185.0)])
    a.add("water_box", GALV, box(-3400, -2950, -340, 340, 920, 1310))
    a.add("black_trim", BLACK, box(-3420, -2930, -350, 350, 1300, 1345))
    a.add("pump_cylinders", CHROME, [rod(92, (-2960, y, 1120), (-1550, y, 1120)) for y in (-185.0, 185.0)])
    a.add("black_trim", BLACK, [box(-1600, -1450, y - 130, y + 130, 990, 1250) for y in (-185.0, 185.0)],
          box(-1600, -1450, -SY1, SY1, 1040, 1100))
    # rear frame extension, under-run bar, lamps, control box
    a.add("frame", BLACK, [box(-5850, XRR + 40, s * RY0, s * RY1, 540, 780) for s in (1, -1)])
    a.add("rear_underrun", GREY, box(-5900, -5800, -1150, 1150, 430, 560))
    for s in (1, -1):
        a.add("black_trim", BLACK, box(-5915, -5890, *sorted((s * 760, s * 1120)), 455, 545))
        a.add("tail_lights", RED, box(-5925, -5905, *sorted((s * 900, s * 1110)), 465, 535))
        a.add("amber_lamps", AMBER, box(-5925, -5905, *sorted((s * 780, s * 890)), 465, 535))
        a.add("lamps", LED, cyl(70, (-5780, s * 950, 1600), (-5812, s * 950, 1600)))
        a.add("black_trim", BLACK, box(-5790, -5700, *sorted((s * 820, s * 1040)), 1470, 1690))
    a.add("amber_lamps", AMBER, cyl(80, (-5300, 950, 1530), (-5300, 950, 1650)), sphere(80, (-5300, 950, 1650)))
    a.add("black_trim", BLACK, box(-5380, -5220, 860, 1030, 1470, 1540))
    a.add("control_box", BODY, box(-4950, -4500, -1180, -980, 950, 1560), box(-4950, -4500, -1000, -520, 1300, 1380))
    a.add("black_trim", BLACK, box(-4900, -4550, -1192, -1175, 1020, 1500))
    a.add("tail_lights", RED, cyl(32, (-4800, -1188, 1430), (-4800, -1215, 1430)))
    a.add("amber_lamps", AMBER, [box(x - 25, x + 25, -1200, -1185, 1250, 1300) for x in (-4700, -4620)])

    a.flush(m)
