"""Fuel and lube service truck: ~10.7 m3 (2,800 US gal) diesel tank and an enclosed lube module
on a 3-axle 6x4 conventional chassis.

A generic, brand-neutral truck with the typical proportions of the class (the field service
trucks that refuel and grease loaders, dozers, stackers and reclaimers on mines, quarries and
bulk terminals):

* chassis: conventional (long-hood) 6x4, ~6.1 m wheelbase to the bogie centre, 1,370 mm tandem
  spread, 315/80R22.5 tyres (~1.05 m OD) on 22.5 in steel disc wheels, singles in front, duals
  behind, 2.5 m over the tyres; frame rails ~0.87 m wide, top at ~1.06 m; leaf-sprung front
  axle, leaf-spring tandem bogie, prop shafts, the truck's own fuel tank (left), battery box
  (right), tool boxes, tandem mudguards with mud flaps, rear bumper with lamps;
* cab and hood: ~3.0 m bumper to back of cab, tilting hood with flared fenders, plain bar
  grille (no badge), steel bumper with tow eyes, day cab 2.3 m wide with the roof at 3.0 m,
  two-piece windscreen, wipers, roof ID lamps, beacon, west-coast mirrors, grab handles, entry
  steps, exhaust stack behind the cab, a generic fleet number on the doors;
* body (2.5 m wide, on a 155 mm red body sub-frame skirt): a 2.0 m enclosed lube module behind
  the cab, its left roll-up door open to show five hose reels (fuel, engine oil, hydraulic oil,
  gear oil, grease) on a shelf with roller guides, hoses and nozzles, a filter manifold with four
  spin-on filters, air-operated pumps and a gauge panel below, a drip tray; the right door shut
  (ribbed aluminium roll-up door); a fire extinguisher on the left front corner;
* fuel tank: a rectangular, round-cornered tank 2.44 m wide x 1.43 m high x 3.12 m long
  (~10.7 m3), two compartments (bulkhead ring), each with a manlid and vent; top catwalk with
  a crossing landing over the gap to the module, handrails round it, a side ladder up the gap;
  plumbing (outlets, emergency valve) across the gap; generic hazard placards (red flammable
  diamonds with a UN 1202 panel on the sides, "FLAMMABLE" on the rear) and "DIESEL" lettering;
* rear deck: a ~1,000 kg / 2.5 t-m class knuckle-boom service crane on the left rear corner,
  folded for transit (main boom up, outer boom folded down beside it, hook stowed), with its
  rams, slewing column, controls and a stowed outrigger leg; a dispensing cabinet with meter and
  nozzle on the right rear corner; rear work lamps, rear beacon.

Overall ~9.6 m long (tow eyes to rear bumper), 2.5 m over the body and tyres (~3.1 m over the mirrors), ~3.45 m to the
top of the catwalk handrails (2.8 m to the body roof).

Millimetres, X forward, Y left, Z up, ground at Z = 0, footprint roughly centred on the origin.
"""

from __future__ import annotations

import math

import cadquery as cq
import numpy as np

from cadkit import V, Finish, arc_pts, band, bar, box, cone, cut, cyl, pipe, place, prism, rgb, text
from finishes import AMBER, BLACK, CHROME, DARK, GALV, GLASS, LED, RED, RUBBER, STEEL, WHITE

ASSET = dict(key="fuel_lube_truck", stem="Fuel_Lube_Service_Truck",
             title="Fuel and Lube Service Truck", az=40, el=18, size="1200x900")

CAB_RED = Finish(rgb("#b3201a"), rough=0.4)          # fleet red cab, body skirt and crane
BODY = WHITE
WHEEL = Finish(rgb("#ecece6"), rough=0.5)                  # white painted steel disc wheels
MOUTH = Finish(rgb("#232528"), rough=0.85)                 # shadowed holes
ALU = Finish(rgb("#c3c7cb"), metal=0.6, rough=0.38)        # aluminium roll-up doors, grating
BAY = Finish(rgb("#3a3d42"), rough=0.7)                    # inside of the lube bay
TAIL = Finish(rgb("#d81b1b"), rough=0.25, glow=(0.35, 0.0, 0.0))
TAG = {"fuel": Finish(rgb("#c62828"), rough=0.4), "engine": Finish(rgb("#f0ad00"), rough=0.45),
       "hydraulic": Finish(rgb("#1f5fa8"), rough=0.5), "gear": Finish(rgb("#2e7d32"), rough=0.45),
       "grease": Finish(rgb("#1d1f22"), rough=0.55)}

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
XFR, XRR = 4600.0, -4700.0

# ---- cab: plan sections (z, front x, half width, front corner r, rear x, rear corner r)
CAB = [(1040, 3010, 1150, 120, 1700, 60), (2100, 3010, 1150, 120, 1700, 60), (2880, 2790, 1135, 110, 1710, 60),
       (2960, 2720, 1100, 90, 1730, 50), (3000, 2660, 1050, 60, 1760, 40)]
CAB_IN = [(1110, 2960, 1100, 80, 1750, 30), (2100, 2960, 1100, 80, 1750, 30), (2860, 2750, 1085, 70, 1760, 30),
          (2930, 2690, 1050, 60, 1780, 30)]
WS_Z0, WS_Z1, WS_Y = 2150.0, 2840.0, 1020.0

# ---- hood: sections (x, bottom z, fender top z, fender half width, hood half width, hood top z)
HOOD = [(2990, 950, 1400, 1240, 560, 2100), (4380, 950, 1265, 1240, 540, 2010), (4540, 1000, 1185, 1180, 520, 1990)]

# ---- body
SK0, SK1, SKY = 1225.0, 1380.0, 1250.0       # body sub-frame skirt: bottom, top, half width
BZ1 = 2800.0                                 # body roof / tank top
MX0, MX1, MY = -560.0, 1480.0, 1245.0        # lube module
BX0, BX1, BY0 = -420.0, 1290.0, 620.0        # lube bay (left side), back wall at y = BY0
BZ0, BZT = 1450.0, 2620.0                    # bay floor / ceiling
TX0, TX1, TY, TR = -4200.0, -1080.0, 1220.0, 280.0   # fuel tank: rear, front, half width, corner r
TZ0 = 1370.0                                 # tank bottom
XBH = -2640.0                                # compartment bulkhead
XC, YC = -4470.0, 880.0                      # crane slewing column


def rr_pts(hy, z0, z1, r, n=6):
    """(y, z) outline of a rounded rectangle."""
    return (arc_pts(hy - r, z1 - r, r, 0, 90, n) + arc_pts(-hy + r, z1 - r, r, 90, 180, n)
            + arc_pts(-hy + r, z0 + r, r, 180, 270, n) + arc_pts(hy - r, z0 + r, r, 270, 360, n))


def tank_prism(x0, x1, grow=0.0):
    return prism(rr_pts(TY + grow, TZ0 - grow, BZ1 + grow, TR + grow), "x", x0, x1)


def tank_ring(xm, w, grow, wall):
    """A raised frame round the tank at xm: the outline grown by `grow`, `wall` deep inwards."""
    outer = tank_prism(xm - w / 2, xm + w / 2, grow)
    inner = prism(rr_pts(TY - wall, TZ0 + wall, BZ1 - wall, TR - wall), "x", xm - w, xm + w)
    return cut(outer, inner)


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


def ngon(cx, cz, r, n):
    return [(cx + r * math.cos(2 * math.pi * (k + 0.5) / n), cz + r * math.sin(2 * math.pi * (k + 0.5) / n))
            for k in range(n)]


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


def gear(xc, zc, ro, ri, n, phase, frac=0.45):
    """(x, z) outline of a lug ring: n teeth out to ro, valleys at ri."""
    pts, p = [], 360.0 / n
    for k in range(n):
        a0 = phase + k * p
        for a, r in ((a0, ri), (a0, ro), (a0 + frac * p, ro), (a0 + frac * p, ri)):
            pts.append((xc + r * math.cos(math.radians(a)), zc + r * math.sin(math.radians(a))))
    return pts


def diamond(c, h):
    """(u, v) points of a diamond of half diagonal h round c."""
    u, v = c
    return [(u + h, v), (u, v + h), (u - h, v), (u, v - h)]


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

# small parts of one finish that are merged into one named part, to keep the part count down
ALIAS = {n: "amber_lamps" for n in ("side_markers", "front_indicators", "fender_marker", "door_mirror_light",
                                    "roof_id_lamps", "skirt_markers", "module_marker_lamps", "tank_markers",
                                    "rear_indicators")}
ALIAS.update({"beacon": "beacons", "rear_beacon": "beacons", "beacon_base": "beacon_bases",
              "rear_beacon_base": "beacon_bases", "reversing_lamps": "work_lamp_lenses", "bay_lamp": "work_lamp_lenses",
              "rear_work_lamp_lens": "work_lamp_lenses", "rear_markers": "tail_lamps",
              "extinguisher_bracket": "extinguisher_fittings", "extinguisher_valve": "extinguisher_fittings",
              "manlid_hinges": "manlid_hardware", "manlid_clamps": "manlid_hardware",
              "roll_door_handle": "roll_door_handles", "door_pull_strap": "roll_door_handles",
              "cowl": "window_rubbers", "rear_window_rubber": "window_rubbers", "door_rubber": "window_rubbers",
              "windscreen_rubber": "window_rubbers", "mud_flap_hanger": "chassis_brackets",
              "mudguard_brackets": "chassis_brackets", "spring_hangers": "chassis_brackets",
              "fuel_meter_face": "gauge_faces", "gauges": "gauge_faces", "extinguisher_gauge": "gauge_faces",
              "door_handle": "grab_handles", "cabinet_handle": "grab_handles", "bay_grab_handle": "grab_handles",
              "crane_ram_eyes": "crane_brackets", "crane_controls": "crane_brackets",
              "step_frame": "step_frames", "bay_step_frame": "step_frames", "bay_step_treads": "step_treads",
              "crane_lever_knobs": "red_handles", "emergency_valve_handles": "red_handles",
              "fuel_cap": "fuel_tank_fittings", "fuel_tank_straps": "fuel_tank_fittings",
              "battery_bracket": "battery_box", "reel_nozzles": "nozzles", "fuel_nozzle": "nozzles",
              "crane_slew_ring": "crane_bearings", "crane_knuckle": "crane_bearings"})


class Parts:
    """Collects shapes by part name, so each left/right pair ends up as one part."""

    def __init__(self, m):
        self.m, self.order = m, {}
        self.print_mode = m.print_mode
        self.t, self.r = m.t, m.r

    def add(self, name, finish, *shapes):
        name = ALIAS.get(name, name)
        self.order.setdefault(name, (finish, []))[1].append(shapes)

    def flush(self):
        for name, (finish, shapes) in self.order.items():
            self.m.add(name, finish, shapes)


def build(model):
    m = Parts(model)
    _chassis(m)
    _cab(m)
    _body(m)
    _lube_bay(m)
    _tank(m)
    _rear(m)
    m.flush()


# =============================================================================== chassis

def _chassis(m):
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

    # frame
    rails = [box(XRR, XFR, s * RY0, s * RY1, RZ0, RZ1) for s in (1, -1)]
    rails += [box(x - 40, x + 40, -RY1, RY1, RZ0 + 40, RZ1 - 40) for x in (XFR - 60, 2200, 0, XRB, -4000)]
    rails.append(box(XRR, XRR + 60, -RY1, RY1, RZ0, RZ1))
    m.add("frame_rails", BLACK, rails)
    m.add("engine", DARK, box(3000, 4450, -420, 420, 500, 1350), box(2250, 3020, -300, 300, 560, 1000))

    # truck fuel tank (left), battery box (right)
    m.add("fuel_tank", CHROME, cyl(290, (1200, 820, 770), (2300, 820, 770)))
    m.add("fuel_tank_straps", BLACK, [cyl(300, (x, 820, 770), (x + 50, 820, 770)) for x in (1400, 2050)],
          [box(x - 10, x + 60, 420, 560, 700, 860) for x in (1400, 2050)])
    m.add("fuel_cap", BLACK, cyl(65, (2150, 820, 1040), (2150, 820, 1100)))
    m.add("battery_box", BLACK, box(1250, 2250, -1100, -500, 600, 1000), box(1230, 2270, -1115, -485, 990, 1030))
    m.add("battery_bracket", BLACK, [box(x - 40, x + 40, -560, -420, 700, 900) for x in (1400, 2100)])

    # tandem mudguards, flaps
    path = arc_pts(XR1, ZC, 615, 14, 90, 10) + arc_pts(XR2, ZC, 615, 90, 166, 10)
    for s in (1, -1):
        m.add("rear_mudguard", BLACK, prism(band(path, m.t(12) / 2), "y", *sorted((s * 600, s * 1275))))
        m.add("mudguard_brackets", DARK, [box(x - 40, x + 40, *sorted((s * 425, s * 720)), 1050, ZC + 618)
                                          for x in (XR1 - 450, XR2 + 450)])
        xe = XR2 + 615 * math.cos(math.radians(166))
        m.add("rear_mud_flap", RUBBER, box(xe - m.t(22), xe + 5, *sorted((s * 640, s * 1265)), 280, ZC + 175))
        m.add("mud_flap_hanger", DARK, box(xe - 60, xe + 10, *sorted((s * 420, s * 1265)), ZC + 150, ZC + 210))
        m.add("side_markers", AMBER, [box(x - 45, x + 45, *sorted((s * 1272, s * 1284)), ZC + 560, ZC + 600)
                                      for x in (XR1 + 200, XR2 - 200)])

    # rear bumper and lamps
    m.add("rear_bumper", BLACK, box(-4800, -4690, -1220, 1220, 690, 820),
          [box(-4760, -4650, s * 300, s * 400, 800, 1230) for s in (1, -1)])
    for s in (1, -1):
        m.add("tail_lamps", TAIL, box(-4812, -4790, *sorted((s * 820, s * 1060)), 710, 800))
        m.add("rear_indicators", AMBER, box(-4812, -4790, *sorted((s * 620, s * 780)), 710, 800))
    m.add("reversing_lamps", LED, [box(-4812, -4790, *sorted((s * 420, s * 560)), 725, 785) for s in (1, -1)])


# =============================================================================== cab

def _cab(m):
    hr = m.r(18)
    hood = cq.Solid.makeLoft([hood_section(*h) for h in HOOD], ruled=True)
    arches = [cyl(650, (XF, s * 575, ZC), (XF, s * 1400, ZC)) for s in (1, -1)]
    m.add("hood", CAB_RED, cut(hood, *arches))
    m.add("fender_liners", BLACK, [prism(band(arc_pts(XF, ZC, 652, 6, 174, 24), 16), "y", *sorted((s * 580, s * 1238)))
                                   for s in (1, -1)])
    m.add("grille", BLACK, box(4520, 4565, -470, 470, 1080, 1940))
    m.add("grille_bars", CHROME, [box(4560, 4580, -440, 440, z - 22, z + 22) for z in np.linspace(1160, 1860, 7)],
          box(4560, 4582, -25, 25, 1100, 1920))
    louv = []
    for s in (1, -1):
        for z in np.arange(1560, 1860, 60):
            louv.append(bar((3450, s * hood_hw(3450), z), (4050, s * hood_hw(4050), z), 30, m.t(14), up=(0, s, 0)))
    m.add("hood_louvres", BLACK, louv)
    for s in (1, -1):
        m.add("headlamp_housing", BLACK, box(4528, 4552, *sorted((s * 620, s * 1000)), 1025, 1155))
        m.add("headlamps", LED, box(4545, 4558, *sorted((s * 640, s * 790)), 1040, 1140),
              box(4545, 4558, *sorted((s * 830, s * 980)), 1040, 1140))
        m.add("front_indicators", AMBER, box(4530, 4556, *sorted((s * 1020, s * 1150)), 1040, 1140))
        m.add("fender_marker", AMBER, box(4380, 4460, *sorted((s * 1225, s * 1250)), 1150, 1200))
    m.add("bumper", STEEL, prism([(4540, 600), (4690, 600), (4720, 630), (4720, 850), (4690, 880), (4540, 880)],
                                 "y", -1240, 1240))
    m.add("bumper_end_caps", BLACK, [box(4545, 4715, *sorted((s * 1225, s * 1250)), 620, 860) for s in (1, -1)])
    m.add("tow_eyes", DARK, [prism([(4700, 560), (4800, 600), (4800, 680), (4700, 720)], "y", *sorted((s * 600, s * 640)))
                             for s in (1, -1)],
          [cyl(m.r(25), (4760, s * 560, 640), (4760, s * 680, 640)) for s in (1, -1)])
    m.add("air_cleaner", BLACK, cyl(180, (3250, -950, 1380), (3250, -950, 2000)),
          cone(180, 100, (3250, -950, 2000), (3250, -950, 2060)))
    m.add("air_cleaner_bands", STEEL, [cyl(188, (3250, -950, z), (3250, -950, z + 40)) for z in (1500, 1850)])
    m.add("air_intake_pipe", BLACK, rods([(3250, -950, 1550), (3250, -650, 1550), (3250, -500, 1600)], m.r(70)))

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
    m.add("cab", CAB_RED, shell)

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

        def xd(z):
            return xfr(z) - 70 if z > 2100 else 2940.0
        zk = (1110.0, 2100.0, 2880.0)
        seams = [side_bar(1830, z0, 1830, z1, s, sw, sh) for z0, z1 in zip(zk, zk[1:])]
        seams += [side_bar(xd(z0), z0, xd(z1), z1, s, sw, sh) for z0, z1 in zip(zk, zk[1:])]
        seams.append(side_bar(1830 - sw / 2, 1110, xd(1110) + sw / 2, 1110, s, sw, sh))
        m.add("door_seams", BLACK, seams)
        m.add("door_handle", CHROME, side_bar(1950, 1950, 2110, 1950, s, 40, m.t(24)))
        m.add("door_number", WHITE, text("FL-12", 210, m.t(10) + 6, (2400, s * 1146, 1600), (-s, 0, 0), (0, s, 0)))
        m.add("door_mirror_light", AMBER, side_bar(2950, 1300, 2990, 1300, s, 90, m.t(16)))
        ya, yb = s * 1140, s * 1205
        m.add("grab_handles", CHROME, rods([(1770, ya, 1250), (1770, yb, 1250), (1770, yb, 2450), (1770, ya, 2450)], hr, 10))
        m.add("step_frame", DARK, box(2400, 2400 + m.t(35), *sorted((s * 960, s * 1190)), 380, 1060),
              box(2950 - m.t(35), 2950, *sorted((s * 960, s * 1190)), 380, 1060),
              box(2400, 2950, *sorted((s * 940, s * (960 + m.t(35)))), 380, 1060))
        m.add("step_treads", GALV, box(2420, 2930, *sorted((s * 980, s * 1210)), 400, 440),
              box(2420, 2930, *sorted((s * 980, s * 1210)), 720, 760))
        m.add("front_mud_flap", RUBBER, box(2985, 2985 + m.t(20), *sorted((s * 960, s * 1230)), 300, 1000))
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
    m.add("roof_id_lamps", AMBER, [box(2550, 2620, y - 45, y + 45, 2985, 3030) for y in (-250, 0, 250)],
          [box(2500, 2580, y - 40, y + 40, 2985, 3025) for y in (-900, 900)])
    m.add("beacon_base", BLACK, cyl(95, (1980, 550, 2985), (1980, 550, 3045)))
    m.add("beacon", AMBER, cyl(75, (1980, 550, 3040), (1980, 550, 3150)), cone(75, 30, (1980, 550, 3148), (1980, 550, 3200)))
    m.add("exhaust_stack", CHROME, cyl(75, (1610, -1000, 1150), (1610, -1000, 3250)),
          cone(75, 60, (1610, -1000, 3250), (1610, -1000, 3330)))
    m.add("exhaust_shield", BLACK, cyl(92, (1610, -1000, 1900), (1610, -1000, 2600)),
          box(1610, 1720, -1030, -970, 2450, 2520), pipe([(1610, -1000, 1180), (1900, -700, 900)], m.r(60)))


# =============================================================================== body: skirt, module

def _body(m):
    hr = m.r(18)
    # red body sub-frame skirt the whole length of the body, on the frame rails
    m.add("body_skirt", CAB_RED, box(-4720, MX1, -SKY, SKY, SK0, SK1))
    m.add("body_sills", BLACK, [box(-4700, MX1 - 20, s * RY0, s * RY1, RZ1 - 5, SK0 + 10) for s in (1, -1)])
    for s in (1, -1):
        m.add("skirt_markers", AMBER, [box(x - 45, x + 45, *sorted((s * (SKY - 4), s * (SKY + 8))), 1280, 1325)
                                       for x in (1300.0, -2000.0, -4500.0)])

    # lube module: a white box with a left bay (cut here, fitted out in _lube_bay)
    mod = prism(arc_pts(MX1 - 40, MY - 40, 40, 0, 90, 3) + arc_pts(MX0 + 40, MY - 40, 40, 90, 180, 3)
                + arc_pts(MX0 + 40, -MY + 40, 40, 180, 270, 3) + arc_pts(MX1 - 40, -MY + 40, 40, 270, 360, 3),
                "z", SK1 - 10, BZ1)
    mod = cut(mod, box(BX0, BX1, BY0, MY + 60, BZ0, BZT))
    m.add("lube_module", BODY, mod)
    # roof: vents, marker lamps
    m.add("module_roof_vents", ALU, [box(x - 160, x + 160, -350, 350, BZ1 - 10, BZ1 + 70) for x in (1000.0, 200.0)])
    m.add("module_vent_louvres", DARK, [box(x - 150, x + 150, y - 12, y + 12, BZ1 + 60, BZ1 + 78)
                                        for x in (1000.0, 200.0) for y in (-240, -120, 0, 120, 240)])
    m.add("module_marker_lamps", AMBER, [box(MX1 - 60, MX1 + 6, y - 45, y + 45, BZ1 - 90, BZ1 - 30) for y in (-1100, 1100)])

    # right side: the shut ribbed roll-up door
    p, pts = 72.0, [(-MY + 10, BZ0)]
    z = BZ0
    while z + p <= BZT + 1:
        pts += [(-MY - 14, z + 4), (-MY - 14, z + p - 16), (-MY - 6, z + p - 10), (-MY - 6, z + p - 4)]
        z += p
    pts += [(-MY + 10, z)]
    m.add("roll_door_right", ALU, prism(pts, "x", BX0, BX1))
    rails = [box(x - 30, x + 30, -MY - 22, -MY + 10, BZ0 - 20, BZT + 20) for x in (BX0 - 25, BX1 + 25)]
    rails.append(box(BX0 - 50, BX1 + 50, -MY - 22, -MY + 10, BZT + 10, BZT + 70))
    m.add("door_rails", DARK, rails)
    m.add("roll_door_handle", BLACK, box((BX0 + BX1) / 2 - 160, (BX0 + BX1) / 2 + 160, -MY - 40, -MY - 5, BZ0 + 40, BZ0 + 90))
    m.add("module_lettering", BLACK, text("FUEL & LUBE", 170, 40, ((BX0 + BX1) / 2, -MY - 4, 2250), (1, 0, 0), (0, -1, 0)))

    # left side, ahead of the bay: fire extinguisher in a strap bracket
    xe, ye = 1385.0, MY + 65
    m.add("fire_extinguisher", RED, cyl(72, (xe, ye, 1560), (xe, ye, 2040)), cone(72, 30, (xe, ye, 2038), (xe, ye, 2100)))
    m.add("extinguisher_bracket", BLACK, [cyl(80, (xe, ye, z), (xe, ye, z + 40)) for z in (1640, 1920)],
          box(xe - 60, xe + 60, MY - 10, ye - 40, 1540, 1580))
    m.add("extinguisher_valve", BLACK, cyl(m.r(26), (xe, ye, 2090), (xe, ye, 2170)),
          bar((xe, ye, 2160), (xe - 120, ye, 2190), m.t(30), m.t(20), up=(0, 0, 1)),
          rods([(xe - 10, ye + 10, 2130), (xe - 40, ye + 90, 2080), (xe - 40, ye + 90, 1700)], m.r(14), 8))
    m.add("extinguisher_gauge", WHITE, cyl(m.r(18), (xe + 20, ye + 15, 2120), (xe + 20, ye + 45, 2120)))

    # step under the bay and grab handle
    y0, y1 = sorted((960.0, 1230.0))
    m.add("bay_step_frame", DARK, box(300, 300 + m.t(35), y0, y1, 560, SK0 + 20),
          box(800 - m.t(35), 800, y0, y1, 560, SK0 + 20), box(300, 800, 940, 960 + m.t(35), 560, SK0 + 20))
    m.add("bay_step_treads", GALV, box(320, 780, 980, 1240, 580, 620), box(320, 780, 980, 1240, 900, 940))
    xg = BX0 - 70
    m.add("bay_grab_handle", CHROME, rods([(xg, MY - 10, 1500), (xg, MY + 60, 1500),
                                           (xg, MY + 60, 2400), (xg, MY - 10, 2400)], hr, 10))

    # tool boxes under the body
    for s, (x0, x1) in ((1, (-480.0, 200.0)), (-1, (-1000.0, 800.0))):
        y0, y1 = sorted((s * 650, s * 1180))
        m.add("tool_box", ALU, box(x0, x1, y0, y1, 680, SK0 + 15))
        m.add("tool_box_lid", BLACK, box(x0 - 10, x1 + 10, *sorted((s * 1175, s * (1180 + m.t(12)))), 1150, 1180),
              [box(x - 60, x + 60, *sorted((s * 1175, s * (1180 + m.t(14)))), 1060, 1120) for x in (x0 + 150, x1 - 150)])


# =============================================================================== lube bay

def _lube_bay(m):
    # dark lining (back wall), drip tray floor
    m.add("bay_lining", BAY, box(BX0 - 20, BX1 + 20, BY0 - 20, BY0 + 12, BZ0 - 20, BZT + 20),
          box(BX0 - 20, BX1 + 20, BY0 - 20, MY + 13, BZ0 - 20, BZ0 + 12))
    # the left door rolled up into its drum under the ceiling, its bottom bar and pull strap
    m.add("roll_door_left", ALU, cyl(105, (BX0 - 20, MY - 115, BZT - 100), (BX1 + 20, MY - 115, BZT - 100)),
          box(BX0 - 10, BX1 + 10, MY - 70, MY - 20, BZT - 215, BZT - 170))
    m.add("door_pull_strap", BLACK, box((BX0 + BX1) / 2 - 30, (BX0 + BX1) / 2 + 30, MY - 60, MY - 40, BZT - 340, BZT - 200))
    m.add("door_rails", DARK, [box(x - 30, x + 30, MY - 10, MY + 22, BZ0 - 20, BZT + 20) for x in (BX0 - 25, BX1 + 25)])
    m.add("bay_lamp", LED, box(BX0 + 200, BX1 - 200, BY0 + 20, BY0 + 90, BZT - 30, BZT + 5))

    # five hose reels on a shelf, axes along x, hoses out over roller guides
    shelf_z = 1920.0
    m.add("reel_shelf", GALV, box(BX0 - 20, BX1 + 20, BY0 - 10, MY - 90, shelf_z - 35, shelf_z))
    rc, rz, rf, rd = 870.0, shelf_z + 245, 250.0, 150.0
    pitch = (BX1 - BX0) / 5
    flanges, drums, axles, guides, hoses, nozzles, stands = [], [], [], [], [], [], []
    tags = {}
    ft = m.t(20)
    for k, product in enumerate(("fuel", "engine", "hydraulic", "gear", "grease")):
        xc = BX0 + pitch * (k + 0.5)
        hwid = pitch / 2 - 25
        flanges += [rod((xc + sx * hwid, rc, rz), (xc + sx * (hwid - ft), rc, rz), rf, 20) for sx in (1, -1)]
        hr_ = rd + (30 if product == "fuel" else 0)
        drums.append(rod((xc - hwid + ft - 2, rc, rz), (xc + hwid - ft + 2, rc, rz), hr_, 20))
        axles.append(cyl(m.r(28), (xc - hwid - 20, rc, rz), (xc + hwid + 20, rc, rz)))
        stands += [box(xc + sx * (hwid + 5) - 15, xc + sx * (hwid + 5) + 15, rc - 40, rc + 40, shelf_z - 10, rz + 10)
                   for sx in (1, -1)]
        # roller guide on the shelf front edge, hose from the drum over it and down, nozzle
        gy = MY - 130
        guides.append(box(xc - 80, xc + 80, gy - 30, gy + 30, shelf_z - 20, shelf_z + 50))
        hose_r = m.r(24 if product == "fuel" else 16)
        hoses += rods([(xc, rc + 80, rz - 100), (xc, gy, shelf_z + 30), (xc, gy + 10, shelf_z - 300),
                       (xc + 40, gy + 10, shelf_z - 330)], hose_r, 8)
        nozzles.append(box(xc + 20, xc + 160, gy - 20, gy + 40, shelf_z - 380, shelf_z - 300))
        tags.setdefault(product, []).append(box(xc - 70, xc + 70, MY - 100, MY - 80, shelf_z - 32, shelf_z - 3))
    m.add("reel_flanges", STEEL, flanges)
    m.add("reel_hoses", RUBBER, drums, hoses)
    m.add("reel_axles", DARK, axles, stands)
    m.add("reel_guides", GALV, guides)
    m.add("reel_nozzles", BLACK, nozzles)
    for product, shapes in tags.items():
        m.add(f"product_tag_{product}", TAG[product], shapes)

    # lower tier: filter manifold with spin-on filters (front), air pumps and gauge panel (rear)
    fx = [BX1 - 140 - 190 * k for k in range(4)]
    m.add("filter_manifold", GALV, box(fx[-1] - 120, fx[0] + 120, BY0 - 10, BY0 + 140, 1720, 1800),
          [cyl(m.r(25), (x, BY0 + 70, 1800), (x, BY0 + 70, shelf_z - 25)) for x in fx])
    m.add("lube_filters", RED, [cyl(60, (x, BY0 + 80, 1500), (x, BY0 + 80, 1730)) for x in fx])
    pumps = [cyl(70, (x, BY0 + 90, BZ0), (x, BY0 + 90, 1640)) for x in (BX0 + 120, BX0 + 320)]
    m.add("air_pumps", DARK, pumps, [box(x - 80, x + 80, BY0 - 10, BY0 + 170, 1640, 1700) for x in (BX0 + 120, BX0 + 320)])
    m.add("air_regulators", GALV, [cyl(m.r(30), (x, BY0 + 90, 1700), (x, BY0 + 90, 1780)) for x in (BX0 + 120, BX0 + 320)])
    m.add("gauge_panel", BLACK, box(BX0 + 430, BX0 + 680, BY0 - 10, BY0 + 40, 1520, 1860))
    m.add("gauges", WHITE, [rod((x, BY0 + 30, z), (x, BY0 + 55, z), 42, 10)
                            for x in (BX0 + 495, BX0 + 615) for z in (1620, 1770)])


# =============================================================================== fuel tank

def _tank(m):
    hr = m.r(20)
    m.add("fuel_tank_body", BODY, tank_prism(TX0, TX1))
    # end frames and the compartment bulkhead ring
    m.add("tank_rings", ALU, [tank_ring(x, 70, 22, 70) for x in (TX0 - 10, XBH, TX1 + 10)])
    # lettering and placards both sides
    for s in (1, -1):
        m.add("tank_lettering", RED, text("DIESEL", 300, 48, ((TX1 + XBH) / 2, s * (TY - 12), 2150), (-s, 0, 0), (0, s, 0)))
        c = ((XBH + TX0) / 2, 2080.0)
        m.add("placard_border", BLACK, prism(diamond(c, 215), "y", *sorted((s * (TY - 10), s * (TY + 12)))))
        m.add("placard_red", RED, prism(diamond(c, 192), "y", *sorted((s * (TY - 10), s * (TY + 20)))))
        m.add("placard_un_panel", WHITE, box(c[0] - 128, c[0] + 128, *sorted((s * (TY - 10), s * (TY + 28))),
                                             c[1] - 50, c[1] + 50))
        if not m.print_mode:
            m.add("placard_text", BLACK, text("1202", 72, 8, (c[0], s * (TY + 26), c[1]), (-s, 0, 0), (0, s, 0)))
    # rear placard
    c = (0.0, 2050.0)
    xr = TX0 - 45
    m.add("placard_border", BLACK, prism(diamond(c, 215), "x", xr - 12, TX0 + 10))
    m.add("placard_red", RED, prism(diamond(c, 192), "x", xr - 20, TX0 + 10))
    m.add("placard_flammable", WHITE, box(xr - 26, TX0 + 10, -128, 128, c[1] - 45, c[1] + 45) if m.print_mode else
          text("FLAMMABLE", 44, 8, (xr - 18, 0, c[1]), (0, -1, 0), (-1, 0, 0)))

    # top: two manlids with vents
    for x in ((TX1 + XBH) / 2, (XBH + TX0) / 2):
        y = 640.0
        m.add("manlid_collars", ALU, cyl(240, (x, y, BZ1 - 20), (x, y, BZ1 + 60)))
        m.add("manlids", GALV, cyl(260, (x, y, BZ1 + 55), (x, y, BZ1 + 55 + m.t(30))),
              cyl(120, (x, y, BZ1 + 80), (x, y, BZ1 + 105)))
        m.add("manlid_hinges", BLACK, box(x - 60, x + 60, y - 330, y - 230, BZ1 + 30, BZ1 + 100))
        m.add("manlid_clamps", BLACK, [box(x + sx * 255 - 25, x + sx * 255 + 25, y + 120, y + 190, BZ1 + 30, BZ1 + 110)
                                       for sx in (1, -1)])
        m.add("tank_vents", GALV, cyl(45, (x - 380, y, BZ1 - 10), (x - 380, y, BZ1 + 160)),
              cone(85, 40, (x - 380, y, BZ1 + 150), (x - 380, y, BZ1 + 210)))

    # catwalk along the top, landing over the gap to the module
    pz, pt = BZ1 - 5, m.t(40)
    m.add("catwalk", ALU, box(TX0 + 60, TX1, -330, 330, pz, pz + pt),
          box(TX1 - 60, MX0 + 30, -1080, MY - 5, pz, pz + pt))
    ribs = []
    for x0, x1, y0, y1 in ((TX0 + 80, TX1 - 20, -310, 310), (TX1 - 40, MX0 + 10, -1060, MY - 25)):
        n = int((x1 - x0) // 120)
        ribs += [box(x0 + 120 * k + 50, x0 + 120 * k + 75, y0, y1, pz + pt - 8, pz + pt + 10) for k in range(n)]
    m.add("catwalk_tread", DARK, ribs)
    m.add("landing_beams", BLACK, [box(TX1 - 70, MX0 + 40, y - 40, y + 40, BZ1 - 120, pz + 10) for y in (-900, 0, 900)])

    # handrails round the top: both sides of the tank, across the rear and the front over the module
    posts_x = (TX0 + 60, -3440.0, XBH, -1860.0, TX1 - 40)
    ztop, zmid = 3450.0, 3120.0
    rails = []
    for y in (-1080.0, 1080.0):
        rails += [rod((x, y, BZ1 - 60), (x, y, ztop + hr), hr) for x in posts_x]
        rails += [rod((posts_x[0] - hr, y, z), (posts_x[-1] + hr, y, z), hr) for z in (zmid, ztop)]
    xf = MX0 - 80
    rails += [rod((xf, y, BZ1 - 10), (xf, y, ztop + hr), hr) for y in (-1080.0, 650.0)]
    rails += [rod((xf, -1080 - hr, z), (xf, 650 + hr, z), hr) for z in (zmid, ztop)]
    rails += [rod((posts_x[-1], -1080, z), (xf, -1080, z), hr) for z in (zmid, ztop)]
    rails += [rod((posts_x[0], -1080 - hr, z), (posts_x[0], 1080 + hr, z), hr) for z in (zmid, ztop)]
    m.add("handrails", GALV, rails)

    # side ladder up the gap between module and tank (left), grab rails above the landing
    xl0, xl1, yl = TX1 + 70, MX0 - 90, MY + 15
    m.add("ladder_stringers", BLACK, [box(x - 25, x + 25, yl - 25, yl + 25, 560, ztop) for x in (xl0, xl1)])
    m.add("ladder_rungs", GALV, [rod((xl0, yl, z), (xl1, yl, z), m.r(16), 8) for z in np.arange(720, 2800, 290)])
    m.add("ladder_brackets", DARK, [box(x - 20, x + 20, MY - 120, yl, SK1 - 40, SK1 + 20) for x in (xl0, xl1)],
          box(TX1 - 20, xl0 + 20, MY - 120, yl, BZ1 - 180, BZ1 - 120),
          box(xl1 - 20, MX0 + 20, MY - 120, yl, BZ1 - 180, BZ1 - 120),
          [box(xl0 - 20, xl1 + 20, yl - 20, yl + 20, ztop - 20, ztop + 20)])

    # plumbing across the gap: outlets, emergency valve, pump feed
    pipes, valves = [], []
    for y, z in ((-800.0, 1560.0), (-350.0, 1560.0), (250.0, 1700.0)):
        pipes.append(cyl(m.r(45), (TX1 - 40, y, z), (MX0 + 40, y, z)))
        valves.append(cyl(85, ((TX1 + MX0) / 2 - 25, y, z), ((TX1 + MX0) / 2 + 25, y, z)))
    m.add("gap_pipes", GALV, pipes)
    m.add("gap_valves", BLACK, valves)
    m.add("emergency_valve_handles", RED, [bar(((TX1 + MX0) / 2, y, z), ((TX1 + MX0) / 2, y + 220, z + 120), 40, m.t(20))
                                           for y, z in ((-800.0, 1560.0), (-350.0, 1560.0))])
    m.add("tank_markers", AMBER, [box(x - 50, x + 50, *sorted((s * (TY - 8), s * (TY + 14))), 2380, 2440)
                                  for s in (1, -1) for x in (TX1 - 150, TX0 + 150)])


# =============================================================================== rear deck: crane, cabinet, lamps

def _rear(m):
    hr = m.r(18)
    m.add("rear_deck", ALU, box(-4730, TX0 + 10, -SKY, SKY, SK1 - 10, SK1 + 45))

    # knuckle-boom crane, folded for transit on the left rear corner
    zb = SK1 + 45
    m.add("crane_base", CAB_RED, box(XC - 210, XC + 210, YC - 210, YC + 210, zb - 10, zb + 110))
    m.add("crane_slew_ring", BLACK, cyl(185, (XC, YC, zb + 100), (XC, YC, zb + 160)))
    zp = 2200.0
    m.add("crane_column", CAB_RED, cyl(170, (XC, YC, zb + 150), (XC, YC, zp)),
          box(XC - 150, XC + 160, YC - 145, YC + 145, zp - 170, zp + 90))
    top = (XC + 60, YC, 3200.0)
    m.add("crane_main_boom", CAB_RED, bar((XC, YC, zp - 40), top, 250, 220, up=(1, 0, 0)))
    # outer boom folded down beside the main boom, on its outboard side
    yo = YC + 245
    tip = (XC + 110, yo, 2380.0)
    m.add("crane_outer_boom", CAB_RED, bar((top[0], yo, top[2] + 40), tip, 200, 190, up=(1, 0, 0)))
    m.add("crane_extension", ALU, bar((tip[0] - 3, yo, tip[2] + 80), (tip[0] + 8, yo, 2200), 140, 130, up=(1, 0, 0)))
    m.add("crane_pins", STEEL, cyl(m.r(55), (top[0], YC - 150, top[2]), (top[0], yo + 120, top[2])),
          cyl(m.r(45), (XC, YC + 150, zp - 40), (XC, YC - 150, zp - 40)))
    m.add("crane_knuckle", BLACK, cyl(125, (top[0], YC + 100, top[2]), (top[0], yo - 80, top[2])))
    # hook block stowed under the extension
    m.add("crane_hook", BLACK, box(tip[0] - 55, tip[0] + 70, yo - 50, yo + 50, 2080, 2220),
          bar((tip[0] + 8, yo, 2090), (tip[0] + 8, yo, 1980), m.t(40), m.t(40), up=(1, 0, 0)),
          bar((tip[0] + 8, yo, 1990), (tip[0] - 70, yo, 2000), m.t(40), m.t(40)))
    # main boom ram behind the boom, knuckle ram on its inboard face
    a, b = np.array((XC - 185, YC, zb + 300)), np.array((XC - 70, YC, 2760.0))
    yk = YC - 185
    m.add("crane_rams", BLACK, cyl(75, tuple(a), tuple(a + 0.55 * (b - a))),
          cyl(70, (XC + 15, yk, 2380), (XC + 40, yk, 2850)))
    m.add("crane_ram_rods", CHROME, cyl(m.r(40), tuple(a + 0.5 * (b - a)), tuple(b)),
          cyl(m.r(34), (XC + 37, yk, 2800), (XC + 55, yk, 3110)))
    m.add("crane_ram_eyes", DARK, box(XC - 250, XC - 120, YC - 60, YC + 60, zb + 230, zb + 380),
          box(XC - 120, XC - 30, YC - 50, YC + 50, 2700, 2810),
          box(XC - 20, XC + 70, yk - 65, YC - 110, 2330, 2420), box(XC + 10, XC + 100, yk - 65, YC - 110, 3080, 3170))
    # controls on the base (inboard), outrigger leg stowed on the corner
    m.add("crane_controls", DARK, box(XC + 120, XC + 260, YC - 300, YC - 120, zb + 100, zb + 420))
    m.add("crane_levers", BLACK, [rod((XC + 190, y, zb + 410), (XC + 210, y, zb + 600), m.r(14), 8)
                                  for y in (YC - 150, YC - 210, YC - 270)])
    m.add("crane_lever_knobs", RED, [rod((XC + 211, y, zb + 580), (XC + 211, y, zb + 640), m.r(30), 8)
                                     for y in (YC - 150, YC - 210, YC - 270)])
    m.add("outrigger_leg", CAB_RED, box(XC - 70, XC + 70, SKY - 125, SKY - 5, 560, SK1 + 30),
          box(XC - 90, XC + 90, SKY - 145, SKY + 15, SK1 - 100, SK1 - 20))
    m.add("outrigger_pad", BLACK, box(XC - 140, XC + 140, SKY - 200, SKY + 60, 500, 570))

    # dispensing cabinet on the right rear corner: meter, nozzle holster
    cx0, cx1, cy0, cy1 = -4710.0, TX0 - 20, -SKY + 10, -350.0
    m.add("rear_cabinet", BODY, box(cx0, cx1, cy0, cy1, zb - 10, 2250))
    m.add("rear_cabinet_door", BLACK, [box(cx0 - 8, cx0 + 10, cy0 + 40, cy1 - 40, z - 10, z + 10) for z in (zb + 60, 2190)],
          [box(cx0 - 8, cx0 + 10, y - 10, y + 10, zb + 60, 2190) for y in (cy0 + 40, cy1 - 40)])
    m.add("cabinet_handle", CHROME, box(cx0 - 30, cx0 + 5, cy1 - 140, cy1 - 100, 1750, 1950))
    m.add("fuel_meter", GALV, cyl(130, (cx0 + 10, -720, 1950), (cx0 - 90, -720, 1950)))
    m.add("fuel_meter_face", WHITE, cyl(100, (cx0 - 85, -720, 1950), (cx0 - 100, -720, 1950)))
    m.add("fuel_nozzle", BLACK, box(cx0 - 120, cx0 + 5, -1100, -960, 1500, 1720),
          bar((cx0 - 60, -1030, 1720), (cx0 - 60, -1030, 1900), m.t(40), m.t(60), up=(1, 0, 0)),
          rods([(cx0 - 60, -1030, 1900), (cx0 - 120, -1030, 2050), (cx0 - 40, -900, 2150)], m.r(24), 8))

    # rear lamps: work lamps on the tank rear corners, beacon, marker lamps
    for s in (1, -1):
        m.add("rear_work_lamps", BLACK, box(TX0 - 110, TX0 + 10, *sorted((s * 600, s * 790)), 2560, 2700))
        m.add("rear_work_lamp_lens", LED, box(TX0 - 122, TX0 - 105, *sorted((s * 615, s * 775)), 2575, 2685))
        m.add("rear_markers", TAIL, box(TX0 - 70, TX0 - 20, *sorted((s * 1100, s * 1200)), 2720, 2770))
    m.add("rear_beacon_base", BLACK, cyl(90, (TX0 + 300, -700, BZ1 - 10), (TX0 + 300, -700, BZ1 + 70)))
    m.add("rear_beacon", AMBER, cyl(72, (TX0 + 300, -700, BZ1 + 65), (TX0 + 300, -700, BZ1 + 170)),
          cone(72, 28, (TX0 + 300, -700, BZ1 + 168), (TX0 + 300, -700, BZ1 + 215)))
