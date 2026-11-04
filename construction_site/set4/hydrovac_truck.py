"""Hydrovac (hydro-excavation / vacuum excavation) truck, ~12 m3 debris tank, tridem 8x4 chassis.

A generic, brand-neutral truck with the typical proportions of the North American hydrovac class
(12 m3 / ~15 yd3 debris body on a conventional-cab tri-drive or tandem-plus-pusher chassis):

* chassis: conventional (long-nose) day cab, front steer axle 1.1 m behind the bumper, tridem
  rear bogie at 1,370 mm spacing with a ~6.5 m wheelbase to the bogie centre, 315/80R22.5 tyres
  (~1.05 m OD) on steel disc wheels, singles in front and duals behind, 2.5 m over the tyres,
  frame rails ~0.96 m wide with the top at ~1.08 m;
* cab: long hood with a plain mesh grille in a steel surround (no badge), set-back front fenders
  with headlamps, marker lamps and arch trim, heavy steel bumper, day cab with windscreen, door
  glass, wipers, sun visor and roof marker lamps, amber light bar, west-coast mirrors, grab
  handles, steps over the fuel tank (left) and battery box (right), exhaust stack and air cleaner
  behind the cab;
* blower module: a ~1.25 m long enclosure 350 mm behind the cab (the stack and air cleaner stand
  in the gap) for the positive-displacement vacuum blower and water pump, with louvred side panels and access doors, the blower silencer across
  its roof with its outlet stack, an inlet filter housing, the vacuum line from the tank, a roof
  walkway with handrails and a side ladder, and toolboxes underneath;
* debris tank: a 2.0 m diameter x 4.0 m cylinder with a dished front head (~12.5 m3), stiffening
  rings, sitting on a subframe with a hydraulic tipping hinge at the rear and a telescopic tip ram
  under the front; a full-diameter dished rear door hinged at the top with two opening cylinders,
  eight clamp lugs around the rim, a drain valve at the bottom and a rear beacon; a manway, and
  fold-up handrails along the top;
* water: two ~1.5 m3 saddle water tanks along the sides under the debris tank (3,000 l total),
  with fillers, level gauges and conspicuity strips, mudguards and mud flaps under them; a wash
  hose reel each side between the blower module and the tank, with a wash wand on the left;
* boom: a turret on the front of the tank top carrying a two-stage telescopic box boom laid
  forward over the cab on a boom rest, with its lift cylinder; the 8 in (203 mm) rigid vacuum tube
  clamped along the boom, an elbow at the tip and the corrugated flexible suction hose hanging in
  front of the bumper and lying on the ground to the left with its digging tube; boom work light.

Overall ~11.1 m long (rear door to the hose on the ground; ~10.3 m bumper to door), 2.55 m wide
over the body (~3.0 m over the mirrors), ~3.8 m high to the top of the boom and rear beacon.

Millimetres, X forward, Y left, Z up, ground at Z = 0.
"""

from __future__ import annotations

import math

import numpy as np

from cadkit import (Finish, arc_pts, band, bar, box, cone, cut, cyl, pipe, place, prism, ram, rgb, rot, sphere,
                    wheel_lugs)
from finishes import AMBER, BLACK, CHROME, DARK, GALV, GLASS, LED, REFLECTOR, RUBBER, STEEL

ASSET = dict(key="hydrovac_truck", stem="Hydrovac_Truck", title="Hydrovac Excavation Truck",
             az=40, el=18, size="1200x900")

BODY = Finish(rgb("#b3191b"), rough=0.4)   # deep red truck and body
TAIL = Finish(rgb("#d81b1b"), rough=0.25, glow=(0.35, 0.0, 0.0))   # tail lamps
SAFETY = REFLECTOR              # yellow handrails, ladder, conspicuity strips

# ---- running gear
R = 525.0                       # 315/80R22.5, ~1,050 mm OD
ZC = R * (1 - 0.015)            # axle height: tyres sunk 1.5 % for a flat print contact
XF = 4350.0                     # front axle
XR = (-780.0, -2150.0, -3520.0)  # tridem axles
F_IN, F_OUT = 935.0, 1250.0
DI, DO = (630.0, 925.0), (955.0, 1250.0)

# ---- frame
RY0, RY1, RZ0, RZ1 = 390.0, 480.0, 780.0, 1080.0
XRR, XFR = -4560.0, 5300.0

# ---- cab
CAB_X0, CAB_X1, CAB_Y = 2150.0, 3620.0, 1180.0
CAB_PROFILE = [(2150, 1250), (3620, 1250), (3620, 2080), (3470, 2920), (3390, 3020), (2230, 3020), (2150, 2940)]

# ---- debris tank
TR, TZ = 1000.0, 2500.0          # radius, axis height
XT0, XT1 = -395.0, -4365.0       # cylinder front / rear
FH_C, FH_R = -1897.0, 1800.0     # dished front head: sphere centre x, radius
DR_C, DR_R = -2540.0, 2200.0     # dished rear door
# ---- blower module
MX0, MX1, MY, MZ0, MZ1 = 550.0, 1800.0, 1230.0, 1060.0, 2850.0
# ---- boom
BZ0, BZ1 = 3480.0, 3760.0        # boom base section bottom / top
VY, VZ, VR = 300.0, 3610.0, 110.0  # vacuum tube along the boom: y, z, radius


def xws(z):
    """Cab front (windscreen) face x at height z."""
    return float(np.interp(z, (2080.0, 2920.0), (3620.0, 3470.0)))


def rrect(x0, x1, y0, y1, r, n=6):
    """Plan of a rounded rectangle, (x, y) points."""
    return (arc_pts(x1 - r, y1 - r, r, 0, 90, n) + arc_pts(x0 + r, y1 - r, r, 90, 180, n)
            + arc_pts(x0 + r, y0 + r, r, 180, 270, n) + arc_pts(x1 - r, y0 + r, r, 270, 360, n))


def rod(a, b, r, n=8):
    """A thin round rod from a to b as an n-sided prism: light in the GLB, round enough to read."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    L = float(np.linalg.norm(d))
    z = d / L
    x = np.cross(z, [1.0, 0, 0] if abs(z[0]) < 0.9 else [0, 1.0, 0])
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    poly = [(r * math.cos(2 * math.pi * (k + 0.5) / n), r * math.sin(2 * math.pi * (k + 0.5) / n)) for k in range(n)]
    return place(prism(poly, "z", 0, L), tuple(x), tuple(y), tuple(z), tuple(a))


def rods(points, r, n=8):
    """A bent rod through points: prisms, each run a little past the bend so the corners close."""
    pts = [np.asarray(p, float) for p in points]
    out = []
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        t = (b - a) / np.linalg.norm(b - a)
        out.append(rod(a - t * (r if i else 0), b + t * (r if i < len(pts) - 2 else 0), r, n))
    return out


def ysp(s, a, b):
    """The y interval |y| from a to b on side s, sorted."""
    return tuple(sorted((s * a, s * b)))


MERGE = {}
for _target, _names in {
    "black_trim": ("door_seams", "module_door_seams", "toolbox_seams", "toolbox_handles", "water_tank_trim",
                   "headlamp_housing", "bumper_valance", "windscreen_rubber", "door_rubber", "arch_trim",
                   "hood_vents", "fuel_tank_straps", "fuel_cap", "light_bar_base", "silencer_saddles", "filter_lid",
                   "vacuum_line_flanges", "manway_clamps", "wash_wand_holder", "rear_work_lamps", "boom_work_light",
                   "hose_cuff", "dig_tube_collar", "vacuum_tube_clamps", "mirror_heads", "wipers",
                   "exhaust_shield", "boom_collar", "door_gasket", "stack_brackets", "ladder_brackets",
                   "step_hangers", "drain_valve"),
    "amber_lamps": ("front_indicators", "fender_markers", "roof_markers", "light_bar", "rear_indicators",
                    "rear_beacon"),
    "white_lamps": ("headlamps", "fog_lamps", "rear_work_lamp_lens", "boom_work_light_lens"),
    "axles_driveline": ("front_axle", "drive_axles", "prop_shafts"),
    "hinges_and_lugs": ("module_hinges", "door_hinge", "door_ram_lugs", "rear_beacon_mount", "tip_hinge",
                        "boom_ram_lug", "turret_base", "boom_tip"),
    "ram_rods": ("door_ram_rods", "tip_ram_rod", "boom_ram_rod"),
    "rams": ("door_rams", "boom_ram", "tip_ram"),
    "cab_chrome": ("door_handle", "grab_handles", "mirror_arms", "mirror_glass"),
    "handrails": ("roof_handrails", "tank_handrails"),
    "conspicuity_strips": ("water_tank_strip", "rear_reflector_strip"),
    "pins": ("hinge_pin", "tip_pin", "boom_pivot"),
    "water_fittings": ("water_fillers", "water_valves", "drain_pipe"),
    "cab": ("sun_visor",),
    "debris_tank": ("tank_flange",),
    "boom": ("boom_fly",),
    "silencer": ("silencer_outlet",),
    "front_suspension": ("front_springs", "tie_rod"),
}.items():
    MERGE.update(dict.fromkeys(_names, _target))


# =============================================================================== wheels

def wheel(m, parts, xc, s, y_in, y_out, kind):
    """kind 'steer' (rib tread, rim), 'outer' (drive tread, rim) or 'inner' (drive tread, no rim)."""
    def c(y):
        return (xc, s * y, ZC)
    D = 16.0
    body = cyl(R - D, c(y_in + 30), c(y_out - 30)).fuse(
        cone(R - D - 50, R - D, c(y_in), c(y_in + 30)), cone(R - D, R - D - 50, c(y_out - 30), c(y_out)))
    if kind != "inner":
        body = cut(body, cyl(292, c(y_out + 5), c(y_out - 130)))
    parts["tyres"].append(body)
    if kind == "steer":
        w = (y_out - y_in - 60 - 2 * 14) / 3          # three ribs, two grooves
        for k in range(3):
            a = y_in + 30 + k * (w + 14)
            parts["tyres"].append(cyl(R, c(a), c(a + w)))
    else:
        y0, y1 = sorted((s * (y_in + 28), s * (y_out - 28)))
        parts["tyres"] += wheel_lugs(xc, ZC, R, D + 4, y0, y1, 16 if kind == "inner" else 28,
                                     90 if kind == "inner" else 80, 0.12)
    if kind == "inner":
        return
    yf = y_out
    rim = cut(cyl(300, c(yf - 135), c(yf - 8)), cyl(300 - m.t(24), c(yf - 100), c(yf + 1)))
    parts["rims"].append(rim)
    hub = 70.0 if kind == "steer" else 45.0
    parts["hubs"] += [cyl(130, c(yf - 101), c(yf - 101 + hub)),
                      cone(118, 60, c(yf - 101 + hub), c(yf - 101 + hub + 35))]
    for a in np.linspace(0, 2 * math.pi, 10, endpoint=False):
        x, z = xc + 168 * math.cos(a), ZC + 168 * math.sin(a)
        hexa = [(x + m.r(21) * math.cos(k * math.pi / 3), z + m.r(21) * math.sin(k * math.pi / 3)) for k in range(6)]
        parts["nuts"].append(prism(hexa, "y", s * (yf - 102), s * (yf - 68)))


# =============================================================================== hose

def bezier(p0, p1, p2, p3, n):
    p0, p1, p2, p3 = (np.asarray(p, float) for p in (p0, p1, p2, p3))
    t = np.linspace(0, 1, n)[:, None]
    return list((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3)


def hose_path():
    """Centre line of the flexible suction hose: down from the boom-tip elbow, round onto the
    ground and away to the left."""
    rg = 120.0 - 6.0                                   # ring radius 120 (16-gon), sunk into the ground
    a = [np.array((5765.0, VY, 3450.0)), np.array((5770.0, VY, 1500.0))]
    b = bezier((5770.0, VY, 1500.0), (5775.0, VY, 500.0), (5830.0, 420.0, rg), (6080.0, 760.0, rg), 9)
    c = bezier((6080.0, 760.0, rg), (6260.0, 1000.0, rg), (6230.0, 1350.0, rg), (6130.0, 1650.0, rg), 6)
    return a + b[1:] + c[1:]


def resample(pts, step):
    """Points every `step` mm along a polyline, with their unit tangents."""
    pts = np.asarray(pts, float)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    cum = np.concatenate([[0], np.cumsum(seg)])
    out = []
    for d in np.arange(step / 2, cum[-1] - step / 4, step):
        i = min(int(np.searchsorted(cum, d)) - 1, len(seg) - 1)
        i = max(i, 0)
        f = (d - cum[i]) / seg[i]
        p = pts[i] + f * (pts[i + 1] - pts[i])
        t = (pts[i + 1] - pts[i]) / seg[i]
        out.append((p, t))
    return out


# =============================================================================== build

def build(m):
    hr = m.r(20)                 # handrail radius
    acc = {}

    def add(name, fin, *shapes):
        """Collect shapes by part name, so the two sides of the truck make one part each."""
        acc.setdefault(name, (fin, []))[1].extend(shapes)
    g = {"tyres": [], "rims": [], "hubs": [], "nuts": []}

    # =========================================================== running gear
    for s in (1, -1):
        wheel(m, g, XF, s, F_IN, F_OUT, "steer")
        for xc in XR:
            wheel(m, g, xc, s, *DI, "inner")
            wheel(m, g, xc, s, *DO, "outer")
    add("tyres", RUBBER, g["tyres"])
    add("rims", STEEL, g["rims"])
    add("hubs", DARK, g["hubs"])
    add("wheel_nuts", CHROME, g["nuts"])

    # front axle, springs
    fa = [box(XF - 70, XF + 70, -880, 880, 430, 560)]
    fa += [cyl(90, (XF, s * 860, 410), (XF, s * 860, 640)) for s in (1, -1)]
    fa += [cyl(165, (XF, s * 830, ZC), (XF, s * 950, ZC)) for s in (1, -1)]
    fa += [box(XF - 110, XF + 110, *ysp(s, 395, 515), 540, 600) for s in (1, -1)]
    add("front_axle", DARK, fa)
    springs = []
    for s in (1, -1):
        springs.append(prism(band([(XF - 700, 765), (XF - 350, 640), (XF, 610), (XF + 350, 640), (XF + 700, 765)], 35),
                             "y", *ysp(s, 405, 495)))
    add("front_springs", BLACK, springs)
    add("tie_rod", BLACK, rod((XF - 280, -800, 480), (XF - 280, 800, 480), m.r(28)),
        [bar((XF, s * 850, 480), (XF - 300, s * 790, 480), 50, 50) for s in (1, -1)])

    # tridem drive axles, equaliser beams, air springs
    ax = []
    for x in XR:
        # mostly hidden under the body and inside the wheels: light 16-sided prisms
        ax += [rod((x, -620, ZC), (x, 620, ZC), 140, 16), rod((x - 160, 0, ZC), (x + 160, 0, ZC), 250, 16),
               rod((x, -300, ZC), (x, 300, ZC), 230, 16)]
        ax += [rod((x, s * 560, ZC), (x, s * 1140, ZC), 230, 16) for s in (1, -1)]
    ax.append(cyl(150, (XR[0], 0, ZC), (XR[0] + 380, 0, ZC + 40)))
    add("drive_axles", DARK, ax)
    susp = []
    for s in (1, -1):
        susp.append(box(XR[2] - 260, XR[0] + 260, *ysp(s, 470, 580), ZC + 90, ZC + 220))
        susp += [cyl(135, (x, s * 525, ZC + 200), (x, s * 525, RZ0 + 20)) for x in XR]
        susp += [bar((x + 120, s * 520, ZC + 150), (x + 520, s * 435, RZ0 + 10), 80, 80, up=(0, s, 0)) for x in XR]
    add("suspension", BLACK, susp)
    add("prop_shafts", DARK, cyl(m.r(55), (2300, 0, 760), (XR[0] + 380, 0, ZC + 40)),
          [cyl(m.r(75), (x - 50, 0, z), (x + 50, 0, z)) for x, z in ((2300, 760), (XR[0] + 380, ZC + 40))],
          cyl(m.r(50), (XR[0] - 150, 0, ZC + 60), (XR[1] + 300, 0, ZC + 40)),
          cyl(m.r(50), (XR[1] - 150, 0, ZC + 60), (XR[2] + 300, 0, ZC + 40)))

    # =========================================================== frame
    rails = [box(XRR, XFR, s * RY0, s * RY1, RZ0, RZ1) for s in (1, -1)]
    rails += [box(x - 40, x + 40, -RY1 + 5, RY1 - 5, RZ0 + 40, RZ1 - 40) for x in (XFR - 60, 3300, 1200, -1450, -2850, -4400)]
    add("frame_rails", BLACK, rails)
    add("engine", DARK, box(3560, 5150, -450, 450, 600, 1700), box(2250, 3600, -330, 330, 650, 1100))
    add("cab_mounts", BLACK, box(2200, 3560, -500, 500, 1060, 1270))

    # =========================================================== hood and fenders
    hood = prism([(3580, 1000), (5260, 1000), (5260, 1800), (5180, 1870), (3580, 1980)], "y", -720, 720)
    hood = hood.intersect(prism([(3560, -705), (5280, -615), (5280, 615), (3560, 705)], "z", 900, 2100))
    hood = hood.intersect(prism([(-760, 900), (760, 900), (760, 1760), (590, 2060), (-590, 2060), (-760, 1760)],
                                "x", 3500, 5300))
    add("hood", BODY, hood)
    fender_pf = [(3590, 900), (3590, 1460), (3800, 1540), (4600, 1560), (5000, 1480), (5250, 1250), (5265, 900)]
    arch = [cyl(640, (XF, s * 500, ZC), (XF, s * 1400, ZC)) for s in (1, -1)]
    add("fenders", BODY, [cut(prism(fender_pf, "y", *ysp(s, 560, 1260)), arch[i]) for i, s in enumerate((1, -1))])
    add("arch_trim", BLACK, [prism(band(arc_pts(XF, ZC, 655, 22, 158, 24), 28), "y", *ysp(s, 1225, 1280))
                               for s in (1, -1)],
          [prism(band(arc_pts(XF, ZC, 645, 25, 155, 24), m.t(14) / 2), "y", *ysp(s, 560, 1240)) for s in (1, -1)])
    add("hood_vents", BLACK, [box(3800, 4300, *ysp(s, 640, 712), 1450, 1750) for s in (1, -1)])
    add("hood_vent_slats", STEEL, [box(3820, 4280, *ysp(s, 700, 700 + m.t(20)), z, z + 30)
                                     for s in (1, -1) for z in (1500, 1580, 1660)])

    # grille, surround, bumper, lamps
    add("grille", BLACK, box(5245, 5285, -540, 540, 1060, 1760))
    sur = cut(box(5250, 5300, -590, 590, 1015, 1805), box(5240, 5310, -545, 545, 1065, 1755))
    add("grille_surround", STEEL, sur, [box(5255, 5292, -545, 545, z - 14, z + 14) for z in range(1160, 1700, 110)])
    add("bumper", STEEL, prism([(5250, 470), (5420, 470), (5470, 520), (5470, 780), (5420, 830), (5250, 830)],
                               "y", -1250, 1250))
    add("bumper_valance", BLACK, box(5260, 5455, -1100, 1100, 400, 480))
    add("tow_hooks", SAFETY, [box(5440, 5520, *ysp(s, 520, 600), 560, 640) for s in (1, -1)])
    for s in (1, -1):
        add("headlamp_housing", BLACK, box(5225, 5272, *ysp(s, 790, 1150), 1010, 1200))
        add("headlamps", LED, [cyl(68, (5265, s * y, 1105), (5282, s * y, 1105)) for y in (880.0, 1060.0)])
        add("front_indicators", AMBER, box(5230, 5268, *ysp(s, 1165, 1235), 1040, 1170))
        add("fender_markers", AMBER, box(5050, 5130, *ysp(s, 1140, 1220), 1380, 1470))
        add("fog_lamps", LED, cyl(55, (5455, s * 950, 650), (5478, s * 950, 650)))

    # =========================================================== cab
    shell = prism(CAB_PROFILE, "y", -CAB_Y, CAB_Y).intersect(
        prism(rrect(CAB_X0, CAB_X1 + 10, -CAB_Y, CAB_Y, 150), "z", 1200, 3100))
    if not m.print_mode:
        inner = prism([(2200, 1300), (3570, 1300), (3570, 2080), (3425, 2900), (3360, 2970), (2250, 2970), (2200, 2900)],
                      "y", -1130, 1130)
        side_win = box(2450, 3380, -1300, 1300, 2150, 2850)
        ws = prism([(xws(2150) - 120, 2150), (xws(2150) + 120, 2150), (xws(2850) + 120, 2850), (xws(2850) - 120, 2850)],
                   "y", -980, 980)
        shell = cut(shell, inner, side_win, ws)
        add("dash", DARK, box(3300, 3570, -1120, 1120, 1300, 2050))
        add("seats", BLACK, [box(2500, 2950, y - 250, y + 250, 1300, 1750) for y in (600.0, -600.0)],
              [box(2300, 2450, y - 250, y + 250, 1700, 2500) for y in (600.0, -600.0)])
        add("steering_wheel", BLACK, cyl(210, (3200, 600, 2050), (3240, 600, 1985)),
              cyl(35, (3220, 600, 2020), (3420, 600, 1750)))
    add("cab", BODY, shell)

    # windscreen (sloped), its rubber, wipers
    d = np.array([xws(2920) - xws(2080), 0.0, 840.0])
    d /= np.linalg.norm(d)
    nrm = np.array([d[2], 0.0, -d[0]])
    gl = m.t(14)

    def on_ws(z, off):
        return np.array((xws(z), 0.0, z)) + nrm * off
    add("windscreen", GLASS, bar(on_ws(2125, 6), on_ws(2875, 6), 2010, gl, up=tuple(nrm)))
    add("windscreen_rubber", BLACK, bar(on_ws(2105, 2), on_ws(2895, 2), 2090, gl, up=tuple(nrm)),
          bar(on_ws(2470, 4), on_ws(2530, 4), 30, gl + 6, up=tuple(nrm)))
    wo = 6 + gl / 2 + m.t(18) / 2 - 6
    add("wipers", BLACK, [bar(on_ws(2160, wo), on_ws(2190, wo) + np.array((0, dy, 0)), m.t(25), m.t(18),
                                up=tuple(nrm)) for dy in (-780.0, 780.0)])
    add("sun_visor", BODY, box(3380, 3565, -1060, 1060, 2950, 2995))
    add("roof_markers", AMBER, [box(3548, 3578, y - 40, y + 40, 2955, 2988) for y in (-800, -400, 0, 400, 800)])
    add("light_bar_base", BLACK, box(2700, 2900, -520, 520, 3000, 3045))
    add("light_bar", AMBER, prism([(2715, 3035), (2885, 3035), (2885, 3090), (2850, 3120), (2750, 3120), (2715, 3090)],
                                  "y", -500, 500))

    for s in (1, -1):
        # door glass in its rubber, door seams, handle, grab handles
        add("door_rubber", BLACK, box(2420, 3410, *ysp(s, 1160, 1160 + m.t(15)), 2120, 2880))
        add("door_glass", GLASS, box(2450, 3380, *ysp(s, 1168, 1168 + m.t(15) + 5), 2150, 2850))
        sw = m.t(14)
        add("door_seams", BLACK, box(2350, 2370, *ysp(s, 1170, 1170 + sw), 1300, 2960),
              box(3440, 3460, *ysp(s, 1170, 1170 + sw), 1300, 2120),
              box(2355, 3455, *ysp(s, 1170, 1170 + sw), 1310, 1330))
        add("door_handle", CHROME, box(2460, 2580, *ysp(s, 1172, 1172 + m.t(25)), 2000, 2040))
        add("grab_handles", CHROME, rods([(2280, s * 1170, 1450), (2280, s * 1235, 1450),
                                            (2280, s * 1235, 2450), (2280, s * 1170, 2450)], hr))
        # west-coast mirrors
        xm, ym = 3480.0, s * 1430
        add("mirror_arms", CHROME, rods([(3420, s * 1160, 2250), (xm, ym, 2250)], hr),
              rods([(3420, s * 1160, 2700), (xm, ym, 2700)], hr), rod((xm, ym, 2150), (xm, ym, 2800), hr))
        add("mirror_heads", BLACK, box(xm - 30, xm + 60, *ysp(s, 1360, 1505), 2200, 2760))
        add("mirror_glass", CHROME, box(xm - 42, xm - 25, *ysp(s, 1372, 1493), 2215, 2745))
        # steps under the door
        add("step_hangers", BLACK, [box(x, x + 40, *ysp(s, 1100, 1250), 450, 1270) for x in (2640, 3260)])
        add("step_treads", GALV, [box(2650, 3290, *ysp(s, 1110, 1262), z, z + 40) for z in (480, 830)])
    # fuel tank (left), battery box (right)
    add("fuel_tank", CHROME, cyl(300, (2250, 850, 760), (3450, 850, 760)))
    add("fuel_tank_straps", BLACK, [cyl(312, (x, 850, 760), (x + 50, 850, 760)) for x in (2450, 3200)],
          box(2240, 3460, 470, 600, 700, 900))
    add("fuel_cap", BLACK, cyl(60, (3300, 850, 1050), (3300, 850, 1090)))
    add("battery_box", BLACK, box(2260, 3440, -1100, -470, 480, 1060))
    add("battery_lid", DARK, box(2280, 3420, -1112, -1090, 520, 1020))

    # exhaust stack (right) and air cleaner (left) between the cab and the module
    XS = 1975.0                  # in the 350 mm gap between the blower module (MX1) and the cab back
    add("exhaust_stack", CHROME, cyl(90, (XS, -1000, 1300), (XS, -1000, 3420)),
          cone(90, 70, (XS, -1000, 3420), (XS, -1000, 3520)))
    add("exhaust_shield", BLACK, cyl(110, (XS, -1000, 2300), (XS, -1000, 3000)))
    add("air_cleaner", BLACK, cyl(150, (XS, 1000, 1500), (XS, 1000, 2550)),
          cone(150, 90, (XS, 1000, 2550), (XS, 1000, 2650)),
          cyl(70, (XS, 1000, 1420), (XS, 1000, 1510)))
    # stand-off brackets to the cab back wall
    add("stack_brackets", BLACK, [box(XS, CAB_X0 + 30, *ysp(s, 970, 1030), z, z + 60)
                                  for s in (1, -1) for z in (1450, 2150)],
          [box(XS, CAB_X0 + 30, -1030, -970, 2750, 2810)])

    # =========================================================== blower module
    mod = box(MX0, MX1, -MY, MY, MZ0, MZ1)
    add("blower_module", BODY, mod)
    add("module_roof", BLACK, box(MX0 - 20, MX1 + 20, -MY - 20, MY + 20, MZ1 - 20, MZ1 + 30))
    for s in (1, -1):
        lx0 = 800.0 if s > 0 else 1100.0
        lt = m.t(30)
        add("module_louvres", BLACK, box(lx0, MX1 - 120, *ysp(s, MY - 15, MY - 15 + lt), 1420, 2650))
        add("louvre_slats", STEEL, [box(lx0 + 20, MX1 - 140, *ysp(s, MY, MY + lt + 10), z, z + 40)
                                      for z in np.arange(1470, 2620, 105)])
        add("module_door_seams", BLACK, [box(x, x + 20, *ysp(s, MY - 10, MY + m.t(12)), MZ0 + 60, MZ1 - 60)
                                           for x in (lx0 - 60, MX1 - 60)])
        add("module_hinges", DARK, [box(MX1 - 50, MX1 - 10, *ysp(s, MY - 10, MY + m.t(25)), z, z + 120) for z in (1300, 2500)])
    # silencer across the roof, its outlet; inlet filter housing; vacuum line from the tank
    add("silencer", CHROME, cyl(270, (850, -950, 3110), (850, 950, 3110)),
          [cone(270, 120, (850, s * 950, 3110), (850, s * 1050, 3110)) for s in (1, -1)])
    add("silencer_saddles", BLACK, [box(700, 1000, y - 30, y + 30, 2860, 2980) for y in (-500, 500)])
    add("silencer_outlet", CHROME, cyl(110, (850, -650, 3300), (850, -650, 3540)))
    add("filter_housing", STEEL, cyl(230, (1500, 850, 2860), (1500, 850, 3220)))
    add("filter_lid", BLACK, cyl(245, (1500, 850, 3210), (1500, 850, 3270)),
          [box(1490 + 200 * math.cos(a) - 20, 1510 + 200 * math.cos(a), 850 + 245 * math.sin(a) - 20,
               850 + 245 * math.sin(a) + 20, 3150, 3260) for a in (0.5, 2.6, 4.7)])
    add("vacuum_line", STEEL, rods([(-520, -450, 3300), (250, -450, 3300), (650, -450, 3000), (650, -450, 2800)], 110, 20))
    add("vacuum_line_flanges", BLACK, cyl(135, (100, -450, 3300), (150, -450, 3300)))
    # roof walkway handrails and the ladder on the right-hand side
    xe = MX1 - 50
    rails_ = []
    for s in (1, -1):
        for x in (620.0, 1150.0, xe):
            rails_.append(rod((x, s * 1180, MZ1 - 10), (x, s * 1180, 3400), hr))
        rails_ += rods([(620, s * 1180, 3400), (xe, s * 1180, 3400)], hr)
        rails_ += rods([(620, s * 1180, 3130), (xe, s * 1180, 3130)], hr)
    add("roof_handrails", SAFETY, rails_)
    sw_ = m.t(50)                                      # ladder stiles, printable
    stiles = (640.0, 950.0)
    lad = [box(x - sw_ / 2, x + sw_ / 2, -1310, -1310 + sw_, 400, 3400) for x in stiles]
    lad += [rod((stiles[0], -1290, z), (stiles[1], -1290, z), m.r(18)) for z in np.arange(560, 3300, 280)]
    # stile tops tied into the roof handrail
    lad += [rod((x, -1290, z), (x, -1180, z), hr) for x in stiles for z in (3130.0, 3390.0)]
    add("ladder", SAFETY, lad)
    add("ladder_brackets", BLACK, [box(600, 990, -1300, -MY + 30, z, z + 60) for z in (1300, 2500, 2755)],
          box(600, 990, -1300, -RY1 + 10, 880, 940),
          box(600, 1100, -1300, -1180, 445, 505))

    # toolboxes under the module
    for s, x0 in ((1, 650.0), (-1, 1050.0)):
        add("toolbox", GALV, box(x0, MX1 - 50, *ysp(s, 560, 1240), 430, MZ0 + 10))
        st = m.t(14)
        xt = MX1 - 50
        add("toolbox_seams", BLACK, box(x0 + 20, xt - 20, *ysp(s, 1230, 1230 + st), 985, 1000),
              box((x0 + xt) / 2 - 10, (x0 + xt) / 2 + 10, *ysp(s, 1230, 1230 + st), 450, 985))
        add("toolbox_handles", BLACK, [box(x - 70, x + 70, *ysp(s, 1235, 1235 + m.t(30)), 930, 960)
                                         for x in ((x0 * 3 + xt) / 4, (x0 + xt * 3) / 4)])

    # =========================================================== debris tank
    tank = [cyl(TR, (XT1, 0, TZ), (XT0, 0, TZ)),
            sphere(FH_R, (FH_C, 0, TZ)).intersect(cyl(TR, (-410, 0, TZ), (-80, 0, TZ)))]
    tank += [cyl(TR + 25, (x - 40, 0, TZ), (x + 40, 0, TZ)) for x in (-1350, -2600, -3750)]
    add("debris_tank", BODY, tank)
    add("tank_flange", BODY, cyl(1050, (-4360, 0, TZ), (-4405, 0, TZ)))
    add("door_gasket", BLACK, cyl(1035, (-4400, 0, TZ), (-4430, 0, TZ)))
    door = [cyl(1050, (-4425, 0, TZ), (-4500, 0, TZ)),
            sphere(DR_R, (DR_C, 0, TZ)).intersect(cyl(TR, (-4495, 0, TZ), (-4760, 0, TZ)))]
    add("rear_door", BODY, door)
    add("door_stripe", SAFETY, cut(cyl(1062, (-4440, 0, TZ), (-4485, 0, TZ)), cyl(1040, (-4430, 0, TZ), (-4495, 0, TZ))))
    clamps = []
    for a in (65, 100, 135, 170, 190, 225, 260, 295):
        c = box(-4470, -4385, -55, 55, TZ + 1035, TZ + 1110)
        clamps.append(rot(c, -a, (1, 0, 0), (0, 0, TZ)))
        h = box(-4520, -4460, -25, 25, TZ + 1070, TZ + 1140)
        clamps.append(rot(h, -a, (1, 0, 0), (0, 0, TZ)))
    add("door_clamps", BLACK, clamps)
    # hinge at the top, opening cylinders
    add("door_hinge", DARK, [box(-4410, -4300, *ysp(s, 380, 470), 3440, 3650) for s in (1, -1)],
          [box(-4510, -4400, *ysp(s, 270, 370), 3480, 3650) for s in (1, -1)],
          [bar((-4450, s * 320, 3590), (-4600, s * 320, 3180), 90, 70, up=(0, s, 0)) for s in (1, -1)])
    add("hinge_pin", STEEL, cyl(45, (-4420, -520, 3590), (-4420, 520, 3590)))
    for s in (1, -1):
        (barrel, rd), eyes = ram((-3750, s * 650, 3420), (-4500, s * 650, 3420), 60, 35, 0.6)
        add("door_rams", BLACK, barrel)
        add("door_ram_rods", CHROME, rd)
        add("door_ram_lugs", DARK, box(-3820, -3680, *ysp(s, 610, 690), 3220, 3460),
              box(-4560, -4440, *ysp(s, 610, 690), 3250, 3460))
    add("rear_beacon_mount", DARK, box(-4410, -4310, -120, 120, 3440, 3640))
    add("rear_beacon_base", BLACK, cyl(90, (-4360, 0, 3630), (-4360, 0, 3670)))
    add("rear_beacon", AMBER, cyl(75, (-4360, 0, 3665), (-4360, 0, 3740)), sphere(75, (-4360, 0, 3740)))
    # drain valve at the bottom of the door
    add("drain_pipe", STEEL, cyl(95, (-4520, 0, 1680), (-4790, 0, 1680)))
    add("drain_valve", BLACK, box(-4720, -4640, -160, 160, 1550, 1810))
    add("drain_handle", SAFETY, bar((-4680, 0, 1800), (-4680, 0, 2050), m.t(30), m.t(30), up=(1, 0, 0)),
          box(-4700, -4660, -150, 150, 2030, 2070))
    # manway and handrails on top
    add("manway", STEEL, cyl(300, (-2050, 0, 3440), (-2050, 0, 3540)))
    add("manway_clamps", BLACK, [box(-2050 + 290 * math.cos(a) - 30, -2050 + 290 * math.cos(a) + 30,
                                       290 * math.sin(a) - 30, 290 * math.sin(a) + 30, 3480, 3570)
                                   for a in np.linspace(0, 2 * math.pi, 6, endpoint=False)])
    top = []
    for s in (1, -1):
        ys = s * 560
        zb = TZ + math.sqrt(TR ** 2 - 560 ** 2) - 40
        for x in (-1500, -2600, -3500, -4150):
            top.append(rod((x, ys, zb), (x, ys, 3700), hr))
        top += rods([(-1500, ys, 3700), (-4150, ys, 3700)], hr)
        top += rods([(-1500, ys, 3500), (-4150, ys, 3500)], hr)
    add("tank_handrails", SAFETY, top)

    # subframe, saddles, tipping hinge and ram
    add("subframe", BLACK, [box(-4420, -300, s * RY0, s * RY1, RZ1 - 10, 1320) for s in (1, -1)],
          [box(x - 60, x + 60, -700, 700, 1300, 1720) for x in (-900, -2150, -3450)])
    add("tip_hinge", DARK, [box(-4420, -4200, *ysp(s, 450, 620), RZ1 - 20, 1780) for s in (1, -1)])
    add("tip_pin", STEEL, cyl(70, (-4310, -680, 1300), (-4310, 680, 1300)))
    add("tip_ram", BLACK, cyl(150, (-230, 0, 1040), (-330, 0, 1400)))
    add("tip_ram_rod", CHROME, cyl(100, (-320, 0, 1380), (-400, 0, 1620)))

    # =========================================================== water tanks, guards, lights
    for s in (1, -1):
        add("water_tank", BODY, box(-4300, -350, *ysp(s, 740, 1270), 1180, 1880))
        add("water_tank_strip", SAFETY, box(-4280, -370, *ysp(s, 1262, 1262 + m.t(12)), 1250, 1300))
        add("water_tank_trim", BLACK, box(-4310, -340, *ysp(s, 1255, 1255 + m.t(20)), 1820, 1885))
        add("water_fillers", STEEL, [cyl(90, (x, s * 1080, 1860), (x, s * 1080, 1950)) for x in (-900, -3700)])
        add("water_gauge", GLASS, box(-1300, -1240, *ysp(s, 1262, 1262 + m.t(14)), 1350, 1800))
        add("water_valves", STEEL, cyl(60, (-600, s * 1150, 1180), (-600, s * 1150, 1080)),
              rod((-600, s * 1150, 1100), (-450, s * 1150, 1100), m.r(18)))
        add("mudguards", BLACK, box(-4250, -320, *ysp(s, 600, 1285), 1130, 1190))
        add("mud_flaps", RUBBER, box(-4170, -4170 + m.t(20), *ysp(s, 640, 1255), 300, 1150))
        add("rear_work_lamps", BLACK, box(-4335, -4290, *ysp(s, 1050, 1220), 1700, 1800))
        add("rear_work_lamp_lens", LED, box(-4345, -4320, *ysp(s, 1070, 1200), 1715, 1785))

    # rear under-run bumper, lamps
    add("rear_bumper", BLACK, box(-4600, -4500, -1240, 1240, 420, 600),
          [box(-4560, -4480, *ysp(s, RY0, RY1), 560, RZ0 + 20) for s in (1, -1)])
    for s in (1, -1):
        add("tail_lamps", TAIL, box(-4615, -4590, *ysp(s, 800, 1100), 450, 570))
        add("rear_indicators", AMBER, box(-4615, -4590, *ysp(s, 600, 780), 450, 570))
    add("rear_reflector_strip", SAFETY, box(-4612, -4592, -560, 560, 470, 550))

    # =========================================================== hose reels and wash wand
    for s in (1, -1):
        xc, zc = 100.0, 1550.0
        ft = m.t(25)
        add("hose_reel_flanges", STEEL, cyl(380, (xc, s * 770, zc), (xc, s * (770 + ft), zc)),
              cyl(380, (xc, s * (1180 - ft), zc), (xc, s * 1180, zc)))
        add("hose_reel_hose", BLACK, cyl(320, (xc, s * (770 + ft / 2), zc), (xc, s * (1180 - ft / 2), zc)),
              [cyl(338, (xc, s * y, zc), (xc, s * (y + 45), zc)) for y in (830.0, 925.0, 1020.0)])
        add("hose_reel_stand", DARK, box(xc - 50, xc + 50, *ysp(s, RY0 + 20, 790), RZ1 - 20, zc + 40),
              cyl(m.r(40), (xc, s * 700, zc), (xc, s * 1230, zc)))
    add("wash_wand", STEEL, rod((640, 1300, 1250), (640, 1300, 2300), m.r(16)))
    add("wash_wand_grip", SAFETY, box(610, 670, 1270, 1330, 1350, 1500))
    add("wash_wand_holder", BLACK, [box(600, 680, MY - 20, 1330, z, z + 50) for z in (1300, 2200)])
    add("wash_hose", BLACK, rods([(300, 1150, 1850), (520, 1200, 1500), (640, 1300, 1260)], m.r(20)))

    # =========================================================== boom
    add("turret_base", DARK, cyl(420, (-750, 0, 3380), (-750, 0, 3480)))
    add("slew_ring", STEEL, cyl(400, (-750, 0, 3470), (-750, 0, 3520)))
    add("turret", BODY, box(-1060, -440, -260, 260, 3510, 3660))
    add("boom", BODY, box(-1050, 2700, -170, 170, BZ0, BZ1))
    add("boom_fly", BODY, box(2600, 5650, -140, 140, BZ0 + 25, BZ1 - 25))
    add("boom_collar", BLACK, box(2600, 2720, -185, 185, BZ0 - 15, BZ1 + 15))
    add("boom_tip", DARK, box(5560, 5700, -160, 160, BZ0 + 5, BZ1 - 5))
    add("boom_pivot", STEEL, cyl(60, (-950, -300, 3640), (-950, 300, 3640)))
    (barrel, rd), eyes = ram((-500, -235, 3540), (700, -235, 3660), 55, 32, 0.55)
    add("boom_ram", BLACK, barrel)
    add("boom_ram_rod", CHROME, rd, eyes)
    add("boom_ram_lug", DARK, box(640, 760, -275, -150, 3600, 3720))
    add("boom_rest", BLACK, box(1500, 1600, -90, 90, MZ1 - 10, 3420),
          box(1470, 1630, -220, 220, 3400, BZ0 + 10),
          [box(1470, 1630, *ysp(s, 180, 215), BZ0, 3600) for s in (1, -1)])
    add("boom_work_light", BLACK, box(5690, 5740, -130, -20, 3600, 3700))
    add("boom_work_light_lens", LED, box(5735, 5750, -120, -30, 3610, 3690))
    add("boom_hydraulic_hoses", BLACK, rods([(-700, -260, 3600), (-200, -200, 3790), (2600, -200, 3790)], m.r(22)))

    # 8 in rigid vacuum tube along the boom, elbow at the tip, clamps
    add("vacuum_tube", STEEL, rods([(-1350, VY, 3420), (-1350, VY, VZ), (5550, VY, VZ), (5690, VY, 3580),
                                      (5755, VY, 3500), (5765, VY, 3420)], VR, 20))
    add("vacuum_tube_clamps", BLACK, [cyl(VR + 15, (x - 35, VY, VZ), (x + 35, VY, VZ)) for x in (-600, 1200, 3000, 4800)],
          [box(x - 35, x + 35, 130, VY - 40, VZ - 60, VZ + 40) for x in (-600, 1200, 3000, 4800)])
    add("hose_cuff", BLACK, cyl(140, (5765, VY, 3360), (5765, VY, 3460)))

    # flexible corrugated suction hose: a smooth core with steel-wire corrugation rings
    path = hose_path()
    core = []
    for a, b in zip(path, path[1:]):
        t = (b - a) / np.linalg.norm(b - a)
        core.append(rod(a - t * 12, b + t * 12, 100, 16))
    rings = [rod(p - t * 22, p + t * 22, 120, 16) for p, t in resample(path, 95)[1:]]
    add("suction_hose", RUBBER, core)
    add("suction_hose_rings", STEEL, rings)
    # the digging tube on the end of the hose
    p_end = np.array(path[-1])
    t_end = (p_end - np.array(path[-2]))
    t_end /= np.linalg.norm(t_end)
    tip = p_end + t_end * 650
    tip[2] = 95 - 2
    add("dig_tube", STEEL, cyl(95, tuple(p_end - t_end * 60 + np.array((0, 0, -25))), tuple(tip)))
    up = np.array((0.0, 0.0, 1.0))
    h0, h1 = p_end + t_end * 120, p_end + t_end * 470          # D-grip over the tube
    h0[2] = h1[2] = 93.0
    add("dig_tube_handle", SAFETY, rods([h0 + up * 60, h0 + up * 260, h1 + up * 260, h1 + up * 60], m.r(24)))
    add("dig_tube_collar", BLACK, rod(p_end + t_end * 20 + np.array((0, 0, -25)), p_end + t_end * 110 + np.array((0, 0, -25)), 112, 16))

    # merge the many small same-finish details into a few parts, to keep the web twin light
    out = {}
    for name, (fin, shapes) in acc.items():
        target = MERGE.get(name, name)
        if target in out:
            assert out[target][0] is fin, (name, target)
        out.setdefault(target, (fin, []))[1].extend(shapes)
    for name, (fin, shapes) in out.items():
        m.add(name, fin, shapes)
