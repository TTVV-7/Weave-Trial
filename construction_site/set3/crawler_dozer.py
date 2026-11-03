"""Crawler dozer, 20 t class, semi-U blade on the ground, single-shank ripper raised.

A generic, brand-neutral machine with the typical proportions of the ~20 t (150-200 hp)
crawler-dozer class, on a conventional oval (low-drive) undercarriage: the drive sprocket
sits at the rear on the same level as the front idler, inside the track loop.

Undercarriage: two oval track loops of single-grouser shoes (560 mm wide, 65 mm grousers,
~203 mm pitch) over a sealed link chain with visible pin bosses; rear drive sprocket with
bolted segments on a final-drive housing; front idler on a sliding yoke; six double-flange
track rollers and two carrier rollers per side on a box-section track roller frame; rear
pivot shaft and a front equalizer bar tying the track frames to the main frame.
Blade: semi-U moldboard (straight centre section, wings angled forward 25 deg) with end
plates, a bolted cutting edge and end bits, back ribs and beams; push arms outboard of the
tracks on trunnions at mid-track; a tilt cylinder on the left and an adjustable brace on
the right; two lift cylinders on trunnion brackets on the radiator-guard sides, with hoses.
Body: main frame and belly guard, front crankcase guard and pull hook, radiator guard with
a recessed grille and headlights, long engine hood with side louvres, exhaust stack and an
air pre-cleaner, fenders over the tracks with anti-slip treads, handrails and stirrup steps,
rear fuel tank with cap, gauge and work lights, tail lights.
Cab: ROPS cab at the rear centre with large glazing, doors, wiper, mirrors, grab handles,
seat and joystick consoles, roof work lights front and rear and a beacon.
Ripper: parallelogram single-shank ripper on a rear mounting frame, two lift cylinders,
shank with a replaceable tip, carried raised about 0.3 m clear of the ground.

Dimensions are typical figures for the class, not any one machine:
  track gauge 2.00 m, shoes 560 mm -> 2.56 m over the tracks; sprocket-idler centres 3.13 m,
      six rollers 2.38 m apart end to end (~2.4 m of track flat on the ground), track height ~1.1 m;
      grousers sunk 8 mm (~1.5 % of the idler radius) for a flat print contact patch
  blade 3.38 m wide over the end plates, 1.30 m high, cutting edge resting on the ground
  length ~5.7 m over the blade and fuel tank, ~6.6 m with the ripper raised
  hood top ~1.95 m, cab floor ~1.35 m, cab roof ~3.18 m (beacon ~3.27 m)
Millimetres, X forward, Y left, Z up, ground at Z = 0, X = 0 at mid-track.
"""

from __future__ import annotations

import math

import cadquery as cq
import numpy as np

from cadkit import (Finish, bar, box, clip_poly, cone, cut, cyl, mirror_y, pipe, prism, rgb, rot,
                    rounded_box, sphere, torus, band)
from finishes import AMBER, BLACK, CHROME, DARK, GLASS, LED, MILL, RED, STEEL, YELLOW

ASSET = dict(key="crawler_dozer", stem="Crawler_Dozer_20t", title="Crawler Dozer (20 t class)",
             az=40, el=20, size="1200x900")

SHOES = Finish(rgb("#2d2e30"), metal=0.45, rough=0.7)       # track shoes
LINKS = Finish(rgb("#4a4c4f"), metal=0.6, rough=0.5)        # sealed link chain
WEAR = Finish(rgb("#6f7174"), metal=0.7, rough=0.45)        # sprocket segments, ripper tip

# ---------------------------------------------------------------- undercarriage (mm)
TY = 1000.0                     # track centre line, |Y|  (2.0 m gauge)
SW = 560.0                      # shoe width
LWH = 130.0                     # half width of the link chain
G, SINK = 65.0, 8.0             # grouser height, sink below the ground
SHOE_T, LINK_H = 22.0, 160.0
BAND = SHOE_T + LINK_H          # shoe surface to the roller path
ZS = G - SINK                   # shoe outer surface on the bottom run (57)
SPR = (-1550.0, 560.0, 470.0)   # sprocket centre x, z and shoe-surface radius round it
IDL = (1580.0, 560.0, 462.0)    # idler centre x, z and shoe-surface radius round it
ROLL_X = (-1180.0, -705.0, -230.0, 245.0, 720.0, 1195.0)
RR = 120.0                      # track roller tread radius
ZR = ZS + BAND + RR - 5.0       # roller axle height (rollers sit 5 mm into the chain)
PITCH = 203.0

# ---------------------------------------------------------------- blade (side profile, x z)
XB = 2800.0                     # back plane of the moldboard
YJ = 1200.0                     # centre section / wing junction, |Y|
YE = 1660.0                     # wing end, |Y|
WING = 25.0                     # wing angle, degrees forward
BP0, BC, BP2 = np.array([3150.0, 0.0]), np.array([2760.0, 640.0]), np.array([3070.0, 1240.0])


def hull2d(pts):
    """Convex hull, counter-clockwise (monotone chain)."""
    pts = sorted(set((round(float(x), 3), round(float(y), 3)) for x, y in pts))

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, hi = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], p) <= 0:
            hi.pop()
        hi.append(p)
    return lo[:-1] + hi[:-1]


def contour(off, n=120):
    """Track loop in the side plane (x, z), offset `off` from the shoe outer surface
    (negative = inwards): hull of the sprocket, idler and end-roller circles."""
    rv = RR - 5.0 + BAND
    circles = [SPR, IDL, (ROLL_X[0], ZR, rv), (ROLL_X[-1], ZR, rv)]
    pts = []
    for cx, cz, r in circles:
        pts += [(cx + (r + off) * math.cos(a), cz + (r + off) * math.sin(a))
                for a in np.linspace(0, 2 * math.pi, n, endpoint=False)]
    return hull2d(pts)


def walk(poly, n, phase=0.0):
    """n points evenly spaced round a closed polygon, with unit tangents."""
    P = np.array(poly + poly[:1], float)
    seg = np.diff(P, axis=0)
    L = np.linalg.norm(seg, axis=1)
    cum = np.concatenate([[0.0], np.cumsum(L)])
    out = []
    for k in range(n):
        s = (k + phase) * cum[-1] / n
        i = min(int(np.searchsorted(cum, s, side="right")) - 1, len(L) - 1)
        f = (s - cum[i]) / L[i]
        out.append((P[i] + f * seg[i], seg[i] / L[i]))
    return out, cum[-1]


def ring(outer, inner, y0, y1):
    return cut(prism(outer, "y", y0, y1), prism(inner, "y", y0 - 1, y1 + 1))


def P3(p, y):
    return (float(p[0]), float(y), float(p[1]))


def loft_x(sections):
    """Ruled loft through cross sections [(x, [(y, z), ...]), ...] with matching point counts."""
    wires = [cq.Wire.makePolygon([cq.Vector(x, y, z) for y, z in pts], close=True) for x, pts in sections]
    return cq.Solid.makeLoft(wires, ruled=True)


def hyd(a, b, rb, rr, frac, eye_a, eye_b, axis=(0.0, 1.0, 0.0)):
    """Hydraulic cylinder from a (base) to b (rod end); eyes are (radius, half width) bosses
    across `axis`. Returns (barrel parts, rod parts, base eye, rod eye)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    u = d / np.linalg.norm(d)
    j = a + d * frac
    s0 = a + u * eye_a[0] * 0.55
    t = lambda p: tuple(map(float, p))    # noqa: E731
    barrel = [cyl(rb, t(s0), t(j)), cyl(rb * 1.12, t(j - u * 80), t(j + u * 6)),
              cyl(rb * 1.1, t(s0 + u * 10), t(s0 + u * 70))]
    rod = [cyl(rr, t(j - u * 30), t(b))]
    ax = np.asarray(axis, float)
    base_eye = cyl(eye_a[0], t(a - ax * eye_a[1]), t(a + ax * eye_a[1]))
    rod_eye = cyl(eye_b[0], t(b - ax * eye_b[1]), t(b + ax * eye_b[1]))
    return barrel, rod, base_eye, rod_eye


def blade_face(u):
    """Point on the moldboard front face (quadratic curve, u = 0 at the cutting edge) and its
    outward (forward) normal."""
    p = (1 - u) ** 2 * BP0 + 2 * u * (1 - u) * BC + u ** 2 * BP2
    d = 2 * (1 - u) * (BC - BP0) + 2 * u * (BP2 - BC)
    d = d / np.linalg.norm(d)
    return p, np.array([d[1], -d[0]])


def blade_profile():
    front = [tuple(blade_face(u)[0]) for u in np.linspace(0, 1, 20)]
    lip = [(3095.0, 1280.0), (3112.0, 1300.0)]
    back = [(2990.0, 1300.0), (2850.0, 1195.0), (XB, 1000.0), (XB, 300.0), (2870.0, 130.0),
            (2990.0, 40.0), (3090.0, 0.0)]
    return front + lip + back


def wing(shape):
    """Turn a left-hand blade piece drawn straight (from y = YJ outwards) into the wing:
    swung forward about the back plane at the junction."""
    return rot(shape, -WING, (0, 0, 1), (XB, YJ, 0))


def wing_section(x):
    """x of a blade-profile point where the wing crosses a plane y = YE."""
    return XB + (YE - YJ) * math.tan(math.radians(WING)) + (x - XB) / math.cos(math.radians(WING))


# ---------------------------------------------------------------- the machine

def build(m):
    t, r = m.t, m.r

    # ================================================================ undercarriage (left, then mirrored)
    outer = contour(0.0)
    left = []                                    # (name, finish, shapes) for the left track

    left.append(("track_shoes", SHOES, ring(outer, contour(-t(SHOE_T)), TY - SW / 2, TY + SW / 2)))
    left.append(("track_links", LINKS, ring(contour(-20.0), contour(-BAND), TY - LWH, TY + LWH)))
    _, perim = walk(outer, 1)
    n_sh = int(round(perim / PITCH))
    grousers = []
    for p, tg in walk(outer, n_sh)[0]:
        nrm = np.array([tg[1], -tg[0]])          # outward for a counter-clockwise loop
        a, b = p - 6 * nrm, p + G * nrm
        grousers.append(bar(P3(a, TY), P3(b, TY), SW, t(34), up=(tg[0], 0, tg[1])))
    left.append(("grousers", SHOES, grousers))
    pins = [cyl(30, P3(p, TY + LWH - 6), P3(p, TY + LWH + 14)) for p, _ in walk(contour(-100.0), n_sh, 0.5)[0]]
    left.append(("link_pins", DARK, pins))

    # track roller frame
    tf = [(-1250, 430), (1320, 430), (1440, 510), (1440, 640), (1330, 705), (-1190, 705), (-1250, 650)]
    frame = [prism(tf, "y", TY - 150, TY + 150)]
    frame += [box(x - 55, x + 55, TY + 140, TY + 160, ZR - 40, 470) for x in ROLL_X]       # roller caps
    frame.append(box(-900, 1100, TY + 148, TY + 162, 540, 600))                           # stiffener strip
    left.append(("track_frame", YELLOW, frame))
    rollers = []
    for x in ROLL_X:
        # double-flange roller: a tread on each link rail, a slim hub between them (clears the
        # sprocket teeth at the rear roller)
        rollers += [cyl(RR, (x, TY + 50, ZR), (x, TY + 105, ZR)), cyl(RR, (x, TY - 105, ZR), (x, TY - 50, ZR)),
                    cyl(RR - 60, (x, TY - 55, ZR), (x, TY + 55, ZR)),
                    cyl(RR + 18, (x, TY + 88, ZR), (x, TY + 112, ZR)),
                    cyl(RR + 18, (x, TY - 112, ZR), (x, TY - 88, ZR)),
                    cyl(62, (x, TY + 105, ZR), (x, TY + 148, ZR))]
    left.append(("track_rollers", BLACK, rollers))
    carriers, posts = [], []
    for x in (-420.0, 560.0):
        zc = 845.0 - 75.0 + 6.0
        carriers += [cyl(75, (x, TY - 95, zc), (x, TY + 95, zc)), cyl(40, (x, TY - 150, zc), (x, TY + 120, zc))]
        posts.append(box(x - 45, x + 45, TY - 170, TY - 90, 690, zc + 20))
    left.append(("carrier_rollers", BLACK, carriers))
    left.append(("carrier_brackets", YELLOW, posts))

    # front idler on its yoke
    xi, zi, ri = IDL
    rt = ri - BAND + 5.0
    idler = [cyl(rt, (xi, TY - 110, zi), (xi, TY + 110, zi)),
             cyl(rt - 30, (xi, TY + 105, zi), (xi, TY + 124, zi)), cyl(rt - 30, (xi, TY - 124, zi), (xi, TY - 105, zi)),
             torus(195, 14, (xi, TY + 124, zi), (0, 1, 0)),
             cyl(115, (xi, TY + 120, zi), (xi, TY + 150, zi))]
    left.append(("idler", BLACK, idler))
    left.append(("idler_bolts", STEEL, [cyl(16, (xi + 78 * math.cos(a), TY + 145, zi + 78 * math.sin(a)),
                                            (xi + 78 * math.cos(a), TY + 162, zi + 78 * math.sin(a)))
                                        for a in np.linspace(0, 2 * math.pi, 6, endpoint=False)]))
    left.append(("idler_yoke", YELLOW, box(1380, xi - 20, TY + 128, TY + 168, zi - 50, zi + 50),
                 box(1380, xi - 20, TY - 168, TY - 128, zi - 50, zi + 50)))

    # rear drive sprocket on the final drive
    xs, zs, rs = SPR
    rim = rs - BAND + 4.0
    teeth, nt = [], 23
    for k in range(nt):
        a = 2 * math.pi * k / nt
        st = 2 * math.pi / nt
        for da, rad in ((-0.5, 282), (-0.18, 352), (0.18, 352), (0.5, 282)):
            teeth.append((xs + rad * math.cos(a + da * st), zs + rad * math.sin(a + da * st)))
    left.append(("sprocket_segments", WEAR, prism(teeth, "y", TY - 42, TY + 42)))
    left.append(("sprocket", DARK, cyl(rim, (xs, TY - 70, zs), (xs, TY + 70, zs)),
                 cyl(205, (xs, TY + 66, zs), (xs, TY + 92, zs)), cyl(115, (xs, TY + 90, zs), (xs, TY + 118, zs))))
    sb = [cyl(16, (xs + 250 * math.cos(a), TY + 66, zs + 250 * math.sin(a)),
              (xs + 250 * math.cos(a), TY + 82, zs + 250 * math.sin(a)))
          for a in np.linspace(0, 2 * math.pi, 18, endpoint=False)]
    sb += [cyl(15, (xs + 165 * math.cos(a), TY + 90, zs + 165 * math.sin(a)),
               (xs + 165 * math.cos(a), TY + 104, zs + 165 * math.sin(a)))
           for a in np.linspace(0, 2 * math.pi, 10, endpoint=False) + 0.3]
    left.append(("sprocket_bolts", STEEL, sb))
    left.append(("final_drive", DARK, cyl(330, (xs, 560, zs), (xs, 790, zs)),
                 cone(330, 250, (xs, 790, zs), (xs, TY - 66, zs))))
    left.append(("pivot_shaft", DARK, cyl(110, (-1050, 560, 590), (-1050, TY - 140, 590))))

    for name, fin, *shapes in left:
        flat = []
        for sh in shapes:
            flat += sh if isinstance(sh, list) else [sh]
        m.add(f"{name}_L", fin, flat)
        m.add(f"{name}_R", fin, [mirror_y(sh) for sh in flat])

    m.add("equalizer_bar", DARK, box(700, 880, -(TY + 20), TY + 20, 600, 720),
          cyl(95, (660, 0, 640), (920, 0, 640)))

    # ================================================================ main frame and body
    m.add("main_frame", YELLOW, box(-2120, 1700, -600, 600, 400, 960), box(-2120, -300, -600, 600, 900, 1180))
    m.add("belly_guard", DARK, box(-1750, 1680, -560, 560, 340, 410),
          prism([(1650, 340), (1700, 340), (1985, 640), (1985, 720), (1650, 720)], "y", -560, 560))
    m.add("pull_hook", DARK, box(1975, 2080, -95, 95, 500, 680))
    m.add("pull_pin", STEEL, cyl(42, (2035, 0, 470), (2035, 0, 720)))

    # fenders over the tracks
    fender = [(-2260, 1120), (-2260, 1200), (100, 1200), (260, 1120)]
    for s in (1, -1):
        y0, y1 = sorted((s * 560, s * 1320))
        m.add("fender", YELLOW, prism(fender, "y", y0, y1),
              prism([(-2260, 1080), (-2260, 1200), (100, 1200), (260, 1120), (240, 1080)], "y",
                    *sorted((s * 1296, s * (1296 + t(26))))))
        m.add("fender_treads", DARK, box(-2200, -1900, *sorted((s * 900, s * 1260)), 1195, 1200 + t(6)),
              box(-280, 60, *sorted((s * 900, s * 1260)), 1195, 1200 + t(6)))

    # ---- radiator guard, grille, headlights
    guard = prism([(1600, 700), (1960, 700), (1960, 1850), (1890, 1960), (1600, 1960)], "y", -650, 650)
    guard = cut(guard, box(1945, 1975, -540, -30, 860, 1780), box(1945, 1975, 30, 540, 860, 1780))
    m.add("radiator_guard", YELLOW, guard)
    m.add("grille_backing", BLACK, box(1938, 1950, -540, 540, 860, 1780))
    gp = 90 if m.print_mode else 60          # 1 mm gaps between 0.8 mm bars in the print
    m.add("grille_bars", DARK, [box(1946, 1946 + t(12), -540, 540, z, z + t(26)) for z in range(880, 1770, gp)])
    lamps, lenses = [], []
    for s in (1, -1):
        lamps.append(box(1760, 1880, *sorted((s * 380, s * 540)), 1950, 2060))
        lenses.append(box(1876, 1880 + t(8), *sorted((s * 395, s * 525)), 1965, 2045))
    m.add("headlamp_housings", BLACK, lamps)
    m.add("headlights", LED, lenses)

    # ---- engine hood
    def hood_sec(top, w=580.0, ch=110.0, z0=950.0):
        return [(-w, z0), (w, z0), (w, top - ch), (w - ch, top), (-(w - ch), top), (-w, top - ch)]
    m.add("hood", YELLOW, loft_x([(-350.0, hood_sec(1950.0)), (1620.0, hood_sec(1890.0))]))
    lv = t(10)
    panels, louvres = [], []
    for s in (1, -1):
        panels.append(box(320, 1420, *sorted((s * 572, s * 590)), 1260, 1760))
        louvres += [box(340, 1400, *sorted((s * 586, s * (590 + lv))), z, z + 22) for z in range(1280, 1745, 46)]
    m.add("hood_side_panels", BLACK, panels)
    m.add("hood_louvres", DARK, louvres)
    if not m.print_mode:
        seams = []
        for s in (1, -1):
            seams += [box(x - 5, x + 5, *sorted((s * 578, s * 584)), 990, 1820) for x in (-150, 260, 1480)]
        m.add("hood_seams", BLACK, seams)

    def hood_top(x):
        return 1950.0 - (x + 350.0) / 1970.0 * 60.0
    ex, ey = 650.0, -410.0
    m.add("exhaust_stack", BLACK, cyl(72, (ex, ey, hood_top(ex) - 30), (ex, ey, 2800)),
          cyl(110, (ex, ey, hood_top(ex) - 10), (ex, ey, hood_top(ex) + 50)))
    m.add("exhaust_tip", STEEL, cyl(78, (ex, ey, 2770), (ex, ey, 2860)))
    px, py = 1100.0, 400.0
    m.add("air_intake", BLACK, cyl(65, (px, py, hood_top(px) - 30), (px, py, 2230)),
          cyl(140, (px, py, 2210), (px, py, 2370)))
    m.add("precleaner_cap", DARK, cyl(155, (px, py, 2360), (px, py, 2395)), cone(150, 50, (px, py, 2395), (px, py, 2450)))
    m.add("hood_grab_rail", BLACK, pipe([(1450, 280, hood_top(1450) - 10), (1450, 280, hood_top(1450) + 90),
                                         (1450, -280, hood_top(1450) + 90), (1450, -280, hood_top(1450) - 10)], r(16)))

    # ---- lift-cylinder brackets on the radiator-guard sides
    LB = np.array([1660.0, 1740.0])          # base trunnion (x, z)
    LE = np.array([2730.0, 1060.0])          # rod end on the blade
    LY = 800.0
    brk = []
    for s in (1, -1):
        brk += [box(1560, 1760, *sorted((s * 640, s * 708)), 1630, 1850),
                box(1580, 1740, *sorted((s * 892, s * 940)), 1650, 1830),
                box(1560, 1760, *sorted((s * 640, s * 940)), 1830, 1880)]
    m.add("lift_cylinder_brackets", YELLOW, brk)

    # ---- rear: fuel tank, lights
    m.add("fuel_tank", YELLOW, rounded_box(-2250, -1840, -700, 700, 950, 1720, 35))
    m.add("fuel_cap", BLACK, cyl(70, (-2050, 450, 1710), (-2050, 450, 1770)))
    m.add("fuel_gauge", DARK, box(-2258, -2246, -90, 90, 1400, 1620))
    rl, rlens = [], []
    for s in (1, -1):
        rl.append(box(-2270, -2170, *sorted((s * 480, s * 640)), 1712, 1810))
        rlens.append(box(-2270 - t(8) + 4, -2266, *sorted((s * 495, s * 625)), 1726, 1797))
    m.add("rear_lamp_housings", BLACK, rl, [box(-2292, -2250, *sorted((s * 1100, s * 1262)), 1105, 1200)
                                            for s in (1, -1)])
    m.add("rear_work_lights", LED, rlens)
    m.add("tail_lights", RED, [box(-2292 - t(8) + 4, -2288, *sorted((s * 1115, s * 1247)), 1120, 1185)
                               for s in (1, -1)])

    # ================================================================ cab (ROPS)
    CX0, CX1, CW = -1800.0, -360.0, 760.0
    CZ0, CZB, CZF, CZ1 = 1350.0, 1560.0, 1960.0, 3030.0
    pp = 90.0
    m.add("cab_base", YELLOW, box(-1860, -300, -800, 800, 1150, CZ0 + 5))
    m.add("cab_lower", YELLOW, box(CX0, CX1, -CW, CW, CZ0, CZB - 10),
          box(CX1 - 90, CX1 - 3, -CW + 3, CW - 3, CZ0, CZF - 10))
    frame = [box(x0, x0 + pp, y0, y0 + pp, CZB, CZ1) for x0 in (CX0, CX1 - pp) for y0 in (-CW, CW - pp)]
    frame += [box(-1195, -1105, *sorted((s * CW, s * (CW - pp))), CZB, CZ1) for s in (1, -1)]       # door posts
    frame += [box(CX0, CX1, *sorted((s * CW, s * (CW - pp))), CZ1 - 80, CZ1) for s in (1, -1)]
    frame += [box(x0, x0 + pp, -CW, CW, CZ1 - 80, CZ1) for x0 in (CX0, CX1 - pp)]
    frame += [box(CX0, CX1, *sorted((s * CW, s * (CW - 60))), CZB - 10, CZB + 40) for s in (1, -1)]
    frame.append(box(CX0, CX0 + 60, -CW, CW, CZB - 10, CZB + 40))
    frame.append(box(CX1 - 60, CX1, -CW, CW, CZF - 10, CZF + 40))
    m.add("cab_frame", BLACK, frame)
    g = t(12)
    glass = [box(CX1 - 45 - g / 2, CX1 - 45 + g / 2, -CW + pp / 2, CW - pp / 2, CZF + 30, CZ1 - 70),
             box(CX0 + 45 - g / 2, CX0 + 45 + g / 2, -CW + pp / 2, CW - pp / 2, CZB + 30, CZ1 - 70)]
    glass += [box(CX0 + pp / 2, CX1 - pp / 2, *sorted((s * (CW - 45 - g / 2), s * (CW - 45 + g / 2))), CZB + 30, CZ1 - 70)
              for s in (1, -1)]
    m.add("cab_glass", GLASS, glass)
    m.add("cab_roof", YELLOW, rounded_box(CX0 - 80, CX1 + 90, -CW - 60, CW + 60, CZ1 - 20, CZ1 + 150, 40))
    m.add("roof_panel", DARK, box(-1650, -520, -560, 560, CZ1 + 140, CZ1 + 140 + t(14)))
    if m.print_mode:     # solid interior, so the glazed cab is not a sealed hollow
        m.add("cab_core", DARK, box(CX0 + 40, CX1 - 40, -CW + 40, CW - 40, CZ0 - 10, CZ1 + 10))
    m.add("seat", BLACK, box(-1500, -1080, -250, 250, CZ0, 1800),
          bar((-1470, 0, 1780), (-1560, 0, 2450), 500, 140, up=(1, 0, 0)),
          [box(-1420, -1100, *sorted((s * 250, s * 320)), 1900, 1960) for s in (1, -1)])
    m.add("consoles", DARK, [box(-1350, -950, *sorted((s * 330, s * 470)), CZ0, 1880) for s in (1, -1)],
          box(-560, -420, -560, 560, CZ0, CZF - 40),
          [cyl(18, (-1050, s * 400, 1870), (-1040, s * 400, 2030)) for s in (1, -1)])
    m.add("joystick_knobs", BLACK, [sphere(34, (-1040, s * 400, 2040)) for s in (1, -1)])

    # cab details
    wt = t(10)
    xw = CX1 - 45 + g / 2 + wt / 2 - 3
    m.add("wiper", BLACK, bar((xw, 250, CZF + 80), (xw, -150, CZ1 - 160), t(30), wt, up=(1, 0, 0)),
          cyl(30, (xw - 15, 250, CZF + 80), (xw + 20, 250, CZF + 80)))
    handles = []
    for s in (1, -1):
        yo = s * (CW + 70)
        yi = s * (CW - 10)
        for x in (-1150.0, CX1 - pp / 2):
            handles.append(pipe([(x, yi, 1750), (x, yo, 1750), (x, yo, 2650), (x, yi, 2650)], r(16)))
    m.add("cab_grab_handles", YELLOW, handles)
    m.add("door_handles", BLACK, [box(-1080, -980, *sorted((s * (CW - 55), s * (CW + 30))), 2150, 2195) for s in (1, -1)])
    for s in (1, -1):
        xa = CX1 - pp / 2
        m.add("mirror_arm", BLACK, pipe([(xa, s * (CW - 30), 2700), (xa + 40, s * (CW + 160), 2740),
                                         (xa + 70, s * (CW + 250), 2660)], r(15)))
        m.add("mirror_housing", BLACK, box(xa + 50, xa + 110, *sorted((s * (CW + 210), s * (CW + 380))), 2440, 2730))
        m.add("mirror_glass", CHROME, box(xa + 52 - t(6), xa + 54, *sorted((s * (CW + 222), s * (CW + 368))), 2452, 2718))
    fl, fll = [], []
    lt = t(8)
    for s in (1, -1):
        for x0, x1, lx0, lx1 in ((CX1 + 70, CX1 + 170, CX1 + 166, CX1 + 170 + lt),
                                 (CX0 - 160, CX0 - 60, CX0 - 160 - lt, CX0 - 156)):
            fl.append(box(x0, x1, *sorted((s * 380, s * 560)), CZ1 + 10, CZ1 + 110))
            fll.append(box(lx0, lx1, *sorted((s * 395, s * 545)), CZ1 + 22, CZ1 + 98))
    m.add("roof_lamp_housings", BLACK, fl)
    m.add("roof_work_lights", LED, fll)
    m.add("beacon_base", BLACK, cyl(70, (-1650, -520, CZ1 + 140), (-1650, -520, CZ1 + 170)))
    m.add("beacon", AMBER, cyl(55, (-1650, -520, CZ1 + 165), (-1650, -520, CZ1 + 245)))

    # ---- handrails and steps on the fenders
    rails, steps, straps = [], [], []
    for s in (1, -1):
        y = s * 1272
        rails += pipe([(-2180, y, 1190), (-2180, y, 1720), (-480, y, 1720), (-480, y, 1190)], r(18))
        rails.append(cyl(r(18), (-1330, y, 1190), (-1330, y, 1720)))
        ys0, ys1 = sorted((s * 1300, s * 1450))
        sw = t(40)
        straps += [box(x - sw / 2, x + sw / 2, *sorted((s * 1296, s * 1450)), 760, 820) for x in (-330, -110)]
        straps += [box(x - sw / 2, x + sw / 2, *sorted((s * 1296, s * (1296 + t(26)))), 760, 1130)
                   for x in (-330, -110)]
        steps.append(box(-330, -110, ys0, ys1, 780, 780 + t(30)))
    m.add("handrails", YELLOW, rails)
    m.add("step_straps", YELLOW, straps)
    m.add("steps", DARK, steps)

    # ================================================================ blade
    prof = blade_profile()
    blade = [prism(prof, "y", -YJ, YJ)]
    clipL = box(0, 6000, YJ - 50, YE, -100, 2000)
    wingL = wing(prism(prof, "y", YJ, YJ + 900)).intersect(clipL)
    # end plate: the wing's section at y = YE, standing proud of the moldboard face
    endp = [(wing_section(3178.0), -5.0)]
    for u in np.linspace(0, 1, 20):
        q, n = blade_face(u)
        q = q + (30 + 85 * math.sin(math.pi * u)) * n
        endp.append((wing_section(q[0]), q[1]))
    endp += [(wing_section(3140.0), 1318.0), (wing_section(2975.0), 1318.0)]
    endp += [(wing_section(x) - 12, z) for x, z in ((2840.0, 1205.0), (XB, 1000.0), (XB, 300.0), (2870.0, 130.0),
                                                     (2990.0, 30.0), (3000.0, -5.0))]
    endp = clip_poly(endp, 0, 6000, -5, 2000)
    endL = prism(endp, "y", YE - 10, YE + t(30))
    ribs = [prism([(2650, 240), (2815, 240), (2815, 1150), (2720, 1150), (2650, 1050)], "y", y - t(40) / 2, y + t(40) / 2)
            for y in (-1050, -420, 0, 420, 1050)]
    beams = [box(2660, 2830, -YJ, YJ, 220, 340), box(2720, 2850, -YJ, YJ, 1080, 1180)]
    m.add("blade", YELLOW, blade, ribs, beams, wingL, mirror_y(wingL), endL, mirror_y(endL))

    # cutting edge (centre) and end bits (wings), with plow bolts
    us = np.linspace(0.0, 0.14, 6)
    ce = [tuple(blade_face(u)[0] + 14 * blade_face(u)[1]) for u in us]
    ce += [tuple(blade_face(u)[0] - 45 * blade_face(u)[1]) for u in us[::-1]]
    ce = clip_poly(ce, 0, 6000, -5, 2000)
    m.add("cutting_edge", DARK, prism(ce, "y", -YJ, YJ))
    bitL = wing(prism(ce, "y", YJ, YJ + 900)).intersect(clipL)
    m.add("end_bits", DARK, bitL, mirror_y(bitL))
    pb, nb = blade_face(0.075)
    bolts = [cyl(22, P3(pb + 8 * nb, y), P3(pb + 28 * nb, y)) for y in np.linspace(-1080, 1080, 10)]
    wb = [wing(cyl(22, P3(pb + 8 * nb, y), P3(pb + 28 * nb, y))) for y in (YJ + 120, YJ + 300)]
    m.add("edge_bolts", STEEL, bolts, wb, [mirror_y(b) for b in wb])

    # ---- push arms on trunnions at mid-track, outboard of the tracks
    PA0, PA1, PY = np.array([150.0, 580.0]), np.array([2940.0, 420.0]), 1380.0
    for s in (1, -1):
        y = s * PY
        m.add("push_arm", YELLOW, bar(P3(PA0, y), P3(PA1, y), 170, 300),
              cyl(150, (PA0[0], s * 1290, PA0[1]), (PA0[0], s * 1470, PA0[1])),
              box(2850, 2960, *sorted((s * 1290, s * 1470)), 280, 580))
        m.add("trunnion_cap", DARK, cyl(110, (PA0[0], s * 1465, PA0[1]), (PA0[0], s * 1495, PA0[1])))
        m.add("trunnion", STEEL, cyl(90, (PA0[0], s * (TY + 140), PA0[1]), (PA0[0], s * 1300, PA0[1])),
              [cyl(15, (PA0[0] + 75 * math.cos(a), s * 1490, PA0[1] + 75 * math.sin(a)),
                   (PA0[0] + 75 * math.cos(a), s * 1508, PA0[1] + 75 * math.sin(a)))
               for a in np.linspace(0, 2 * math.pi, 6, endpoint=False)])
        m.add("push_arm_pin", STEEL, cyl(55, (2900, s * 1270, 420), (2900, s * 1490, 420)))

    # ---- tilt cylinder (left) and brace (right), push arm to blade top
    TB, TE = np.array([2060.0, 720.0]), np.array([2800.0, 1185.0])
    for s in (1, -1):
        m.add("tilt_brackets", YELLOW, box(1980, 2140, *sorted((s * 1320, s * 1440)), 600, 740),
              box(2760, 2870, *sorted((s * 1090, s * 1210)), 1120, 1240))
    a3, b3 = P3(TB, PY), P3(TE, 1150.0)
    barrel, rod, e0, e1 = hyd(a3, b3, 85, 50, 0.56, (85, 55), (65, 50))
    m.add("tilt_cylinder", BLACK, barrel, e0)
    m.add("tilt_cylinder_rod", CHROME, rod, e1)
    a3, b3 = np.array(P3(TB, -PY)), np.array(P3(TE, -1150.0))
    mid = (a3 + b3) / 2
    du = (b3 - a3) / np.linalg.norm(b3 - a3)
    m.add("tilt_brace", YELLOW, bar(tuple(a3), tuple(b3), 110, 110),
          cyl(70, tuple(a3 + (0, -55, 0)), tuple(a3 + (0, 55, 0))), cyl(60, tuple(b3 + (0, -50, 0)), tuple(b3 + (0, 50, 0))))
    m.add("brace_adjuster", DARK, cyl(78, tuple(mid - du * 160), tuple(mid + du * 160)))
    m.add("tilt_hoses", BLACK, pipe([(260, 1330, 738), (1960, 1330, 636), (2010, 1345, 700)], r(18)),
          pipe([(260, 1430, 738), (1960, 1430, 636), (2010, 1415, 700)], r(18)))

    # ---- lift cylinders, radiator guard to blade back
    lift_pins = []
    for s in (1, -1):
        y = s * LY
        barrel, rod, e0, e1 = hyd(P3(LB, y), P3(LE, y), 85, 50, 0.58, (90, 80), (65, 70))
        m.add("lift_cylinder", BLACK, barrel, e0)
        m.add("lift_cylinder_rod", CHROME, rod, e1)
        m.add("lift_cylinder_clevis", YELLOW, [box(2690, 2845, *sorted((s * a, s * b)), 990, 1140)
                                                 for a, b in ((730 - t(30), 730), (870, 870 + t(30)))])
        lift_pins += [cyl(r(40), P3(LB, s * 630), P3(LB, s * 955)), cyl(r(35), P3(LE, s * 690), P3(LE, s * 910))]
        u = (LE - LB) / np.linalg.norm(LE - LB)
        w = np.array([-u[1], u[0]])                   # up, square to the cylinder
        L = np.linalg.norm(LE - LB)
        hose = [np.array([1600.0, 1600.0]), LB + 0.12 * L * u + 112 * w, LB + 0.5 * L * u + 112 * w,
                LB + 0.55 * L * u + 80 * w]
        m.add("lift_hoses", BLACK, pipe([P3(p, y + s * 20) for p in hose[1:]], r(16)),
              pipe([P3(hose[0], s * 650), P3(hose[1], y + s * 20)], r(16)))
    m.add("lift_pins", STEEL, lift_pins)

    # ================================================================ ripper (single shank, raised)
    Ml, Mu = np.array([-2330.0, 560.0]), np.array([-2330.0, 1060.0])
    Bl, Bu = np.array([-3020.0, 820.0]), np.array([-3020.0, 1320.0])
    mount = []
    mp = [(-2440, 430), (-2390, 380), (-2090, 380), (-2090, 950), (-2255, 950), (-2255, 1330), (-2390, 1330), (-2440, 1270)]
    for s in (1, -1):
        mount.append(prism(mp, "y", *sorted((s * 470, s * 590))))
        mount += [box(-2520, -2420, *sorted((s * a, s * b)), 1220, 1340) for a, b in ((205, 245), (355, 395))]
    mount += [box(-2440, -2300, -590, 590, 380, 500), box(-2440, -2300, -420, 420, 1230, 1330)]
    m.add("ripper_mount", YELLOW, mount)
    links = []
    for s in (1, -1):
        links += [bar(P3(Ml, s * 530), P3(Bl, s * 530), t(70), 170), bar(P3(Mu, s * 530), P3(Bu, s * 530), t(70), 150)]
    m.add("ripper_links", YELLOW, links)
    beam = [box(-3150, -2945, -600, 600, 780, 1000),                       # cross beam
            box(-3110, -2950, -360, 360, 1250, 1390),                      # top tube
            box(-3190, -2960, -115, 115, 740, 1470)]                       # shank pocket
    beam += [prism([(-3110, 760), (-2940, 760), (-2940, 1000), (-2990, 1400), (-3110, 1400)], "y", *sorted((s * 520, s * 580)))
             for s in (1, -1)]
    beam += [box(-3040, -2940, *sorted((s * 230, s * 370)), 700, 800) for s in (1, -1)]
    m.add("ripper_beam", YELLOW, beam)
    shank_path = [(-3080, 1680), (-3080, 920), (-3045, 700), (-2970, 560), (-2890, 480)]
    m.add("ripper_shank", MILL, prism(band(shank_path, [130, 130, 115, 95, 75]), "y", -t(90) / 2, t(90) / 2))
    E = np.array(shank_path[-1], float)
    du = E - np.array(shank_path[-2], float)
    du /= np.linalg.norm(du)
    nn = np.array([-du[1], du[0]])
    tip = [E - 60 * du + 80 * nn, E + 110 * du + 55 * nn, E + 225 * du, E + 110 * du - 50 * nn, E - 60 * du - 80 * nn]
    m.add("ripper_tip", WEAR, prism([tuple(p) for p in tip], "y", -t(100) / 2, t(100) / 2))
    m.add("shank_holes", DARK, [cyl(r(32), (-3080 + dx, -t(90) / 2 - 6, z), (-3080 + dx, t(90) / 2 + 6, z))
                                for dx, z in ((0, 1610), (0, 1525))])
    rp = [cyl(r(40), P3(p, -610), P3(p, 610)) for p in (Ml, Mu, Bl, Bu)]
    rp.append(cyl(r(40), (-3100, -150, 1300), (-3100, 150, 1300)))
    m.add("ripper_pins", STEEL, rp)
    for s in (1, -1):
        barrel, rod, e0, e1 = hyd((-2470, s * 300, 1280), (-2990, s * 300, 750), 80, 48, 0.55, (75, 55), (60, 55))
        m.add("ripper_cylinder", BLACK, barrel, e0)
        m.add("ripper_cylinder_rod", CHROME, rod, e1)
