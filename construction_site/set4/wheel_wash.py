"""Drive-through wheel wash station for track-out control at a site or terminal gate: a raised
drive-over wash bath between splash screens, with its recycling / settlement tank, sludge auger
and skip, pump set and control cabinet, and a GO / STOP light at the exit.

A generic, brand-neutral unit with the typical layout and proportions of the modular
"drive-through" wheel washes used at the gates of bulk terminals, quarries and large sites
(sized for 3-, 4- and 5-axle trucks, up to ~45 t, 2.55 m wide over the wheels):

* wash bay: ~12 m long overall (3 m entry ramp, 6 m wash bath, 3 m exit ramp) and 4.3 m wide over
  the splash-screen posts; the vehicle runs on a 3.6 m wide grated deck 600 mm above the ground
  between 160 mm high wheel-guide kerbs (yellow kerb caps, black / yellow hazard bands on the
  bath sides); the deck is five galvanised grating panels with transverse bars, which flex the
  tyre treads open, on blue bearers across the bath; the ramps are steel wedges at ~1:5
  (11 deg) with galvanised cleat treads and raised side kerbs;
* spray: two galvanised spray bars per side (at ~0.9 m and ~1.13 m above the ground, i.e. low,
  at wheel and axle height) on uprights standing on the kerbs, each with a row of black nozzles
  angled in and down at the wheels, fed by risers at the entry end from a supply main that
  passes under the entry ramp;
* splash screens: 2.6 m high galvanised profiled-sheet walls along both sides of the bath on
  five blue posts per side with a top rail, raking back-struts on foot plates, and two
  floodlights per side lighting the bath at night;
* recycling / settlement tank: a 6.0 x 2.4 x 2.4 m container-style steel tank (corrugated sides
  and ends, corner posts and castings, top and bottom rails) beside the bay, its drain hoses
  from the bath side; a roof with two inspection hatches, a vent, a grated walkway and yellow
  handrails all round; a 45 deg stair with handrails on the long side up to a landing at the
  roof; a fleet-number plate;
* sludge auger: a 400 mm screw-conveyor tube sloping up at ~32 deg out of the far end of the
  tank on an A-frame support, with flanged joints, a gearbox and motor on its head and a
  discharge chute with a rubber sock dropping into a ~5 m3 yellow sludge skip (2.5 m long at
  the top, 1.35 m deep) holding a heap of settled sludge;
* pump set: a skid on the long side with an end-suction wash pump on a black motor (yellow
  coupling guard), suction from the tank, the discharge main with a gate valve running round
  the tank end to the bay; a stainless control cabinet on the skid with a rain hood, indicator
  lamps, isolator and an amber beacon;
* a GO / STOP traffic light (red over green, faces both ways) on a post at the exit, with a
  double-sided "WAIT FOR GREEN" sign hanging outboard of the post; silver bezels ring the lamps
  so both still read in the 4-filament painted print.

Overall ~12.0 m long (the bay; the skip and auger head reach X ~6.2 m on the tank side),
~10.1 m wide over the exit sign, bay, tank and pump skid, and ~3.9 m high over the auger
motor. Colours: blue steelwork, galvanised grating, screens and pipework, yellow
handrails, kerb caps and skip, black hoses, nozzles, motor and hazard bands. It prints in Blue,
Silver grey, Construction yellow and Black.

PRINT NOTE: at 1:50 the model is ~245 x 202 x 72 mm. The roof and stair handrails are ~1 mm
rods: print with the rails parallel to the bed. Plates, nozzles, rails and pipes go through
m.t() / m.r(), so nothing is under 0.8 mm at 1:50.

Millimetres, X forward (vehicles drive through towards +X, the exit), Y left, Z up, ground at
Z = 0, the wash bay centred on the origin.
"""

from __future__ import annotations

import numpy as np

from cadkit import Finish, bar, box, clip_poly, cone, corrugated_plan, cut, cyl, pipe, prism, rgb, sphere, text
from finishes import AMBER, BLACK, BLUE, GALV, LED, RUBBER, YELLOW

ASSET = dict(key="wheel_wash", stem="Drive_Through_Wheel_Wash", title="Drive-Through Wheel Wash Station",
             az=35, el=25, size="1200x900")

PAINT = BLUE
STAINLESS = Finish(rgb("#c9ced2"), metal=0.7, rough=0.3)
SLUDGE = Finish(rgb("#3a3226"), rough=0.95)
LAMP_RED = Finish(rgb("#e0201a"), rough=0.2, glow=(0.9, 0.05, 0.02))
LAMP_GREEN = Finish(rgb("#1fc24a"), rough=0.2, glow=(0.05, 0.8, 0.2))
SIGN_TEXT = BLACK

# ---------------------------------------------------------------- wash bay
XB = 3000.0                 # bath half length (6 m bath)
XT = 2990.0                 # ramp top, |X|
XR = 6000.0                 # ramp toe, |X|
YK0, YK1 = 1800.0, 2000.0   # bath side beams (wheel-guide kerbs), |Y|
ZD = 600.0                  # deck bearers top
ZK = 760.0                  # kerb top
ZG = 615.0                  # top of the grating bars
POSTS = list(np.linspace(-2910.0, 2910.0, 5))
YP0, YP1 = 1995.0, 2145.0   # splash-screen posts, |Y|
ZW0, ZW1 = 740.0, 2600.0    # splash screens
YS = 1885.0                 # spray bars, |Y|
ZS = (900.0, 1130.0)        # spray bar heights
XF = -3150.0                # spray risers / supply crossing, under the entry ramp top

# ---------------------------------------------------------------- recycling tank
X0, X1 = -3300.0, 2700.0    # 6.0 m
Y0, Y1 = 2850.0, 5250.0     # 2.4 m
HT = 2400.0
YC = (Y0 + Y1) / 2

# ---------------------------------------------------------------- sludge auger
AUG_A = np.array([X1 - 900.0, YC, 1000.0])
AUG_B = np.array([X1 + 2500.0, YC, 3100.0])
AUG_D = (AUG_B - AUG_A) / np.linalg.norm(AUG_B - AUG_A)
AUG_L = float(np.linalg.norm(AUG_B - AUG_A))
AUG_R = 200.0
SKIP_X = 4950.0


def P(v):
    return tuple(float(c) for c in v)


def aug(s):
    """Point on the auger axis s mm up from its foot."""
    return AUG_A + AUG_D * s


def comb_y(x0, x1, zb, zt, zc, pitch, w):
    """Side profile (x, z) of a plate with transverse bars on top: base zb..zt, bars up to zc."""
    pts = [(x0, zb), (x1, zb), (x1, zt)]
    n = int((x1 - x0 - w) // pitch)
    start = x0 + (x1 - x0 - n * pitch) / 2
    for i in range(n, -1, -1):
        c = start + i * pitch
        pts += [(c + w / 2, zt), (c + w / 2, zc), (c - w / 2, zc), (c - w / 2, zt)]
    pts.append((x0, zt))
    return pts


def cleat_tread(xa, za, xb, zb, below, above, cleat, pitch, w):
    """Side profile (x, z) of a cleated tread plate laid on the slope line (xa, za)-(xb, zb)."""
    if xa > xb:
        xa, za, xb, zb = xb, zb, xa, za

    def f(x):
        return za + (zb - za) * (x - xa) / (xb - xa)

    pts = [(xa, f(xa) - below), (xb, f(xb) - below), (xb, f(xb) + above)]
    n = int((xb - xa - w) // pitch)
    start = xa + (xb - xa - n * pitch) / 2
    for i in range(n, -1, -1):
        c = start + i * pitch
        pts += [(c + w / 2, f(c + w / 2) + above), (c + w / 2, f(c + w / 2) + cleat),
                (c - w / 2, f(c - w / 2) + cleat), (c - w / 2, f(c - w / 2) + above)]
    pts.append((xa, f(xa) + above))
    return pts


# ================================================================ build

def build(m):
    bath(m)
    ramps(m)
    spray(m)
    screens(m)
    tank(m)
    tank_top(m)
    stair(m)
    auger(m)
    skip(m)
    pump_set(m)
    pipework(m)
    traffic_light(m)


# ---------------------------------------------------------------- wash bath

def bath(m):
    m.add("bath_sides", PAINT, [box(-XB, XB, s * YK0, s * YK1, -2, ZK) for s in (1, -1)],
          [box(e * (XB - 150), e * XB, -YK0 - 5, YK0 + 5, -2, ZD - 10) for e in (1, -1)],
          box(-XB + 5, XB - 5, -YK0 - 5, YK0 + 5, -2, 570))      # solid under the grating: no closed void
    joints = (-1770.0, -590.0, 590.0, 1770.0)
    m.add("deck_bearers", PAINT, [box(x - 60, x + 60, -YK0 - 5, YK0 + 5, 100, ZD) for x in joints])
    edges = [-2950.0] + [v for x in joints for v in (x - 20, x + 20)] + [2950.0]
    panels = []
    for x0, x1 in zip(edges[::2], edges[1::2]):
        panels.append(prism(comb_y(x0, x1, 560, 592, ZG, 110, m.t(30)), "y", -1790, 1790))
    m.add("deck_grating", GALV, panels)
    # yellow wheel-guide kerb caps
    m.add("kerb_caps", YELLOW, [box(-2990, 2990, s * (YK0 - 5), s * 1955, ZK - 5, ZK + 15) for s in (1, -1)])
    # hazard bands on the outer faces of the bath sides: yellow plate, black 45 deg stripes
    pt = m.t(4)
    m.add("hazard_plates", YELLOW, [box(-2985, 2985, s * (YK1 - 5), s * (YK1 + pt), 70, 690) for s in (1, -1)])
    stripes = []
    for s in (1, -1):
        for xk in np.arange(-3600.0, 3000.0, 420.0):
            poly = clip_poly([(xk, 70), (xk + 210, 70), (xk + 830, 690), (xk + 620, 690)], -2985, 2985, 70, 690)
            if len(poly) >= 3:
                stripes.append(prism(poly, "y", s * (YK1 - 3), s * (YK1 + pt + 4)))
    m.add("hazard_stripes", BLACK, stripes)


# ---------------------------------------------------------------- ramps

def kerb_top(x, e):
    """Top of a ramp side kerb at x on the entry (e = -1) or exit (e = 1) ramp."""
    return 130.0 + (ZK - 10 - 130.0) * (XR - abs(x)) / (XR - XT)


def ramps(m):
    for e, name in ((-1, "entry"), (1, "exit")):
        xt, xr = e * XT, e * XR
        core = [(xr, -2), (xt, -2), (xt, ZD), (xr, 10)]
        m.add(f"{name}_ramp", PAINT, prism(core, "y", -YK0 + 5, YK0 - 5),
              [prism([(xr, -2), (xt, -2), (xt, ZK - 10), (xr, 130)], "y", *sorted((s * 1790, s * 2010)))
               for s in (1, -1)])
        m.add(f"{name}_ramp_tread", GALV,
              prism(cleat_tread(xr - e * 150, 10 + 590 * 150 / (XR - XT), xt - e * 30, ZD - 590 * 30 / (XR - XT),
                                22, 6, 32, 200, m.t(50)), "y", -1780, 1780))
        # yellow cap along the top of each side kerb, stiffener ribs on the outside
        x_end = e * (XT + 20)
        m.add(f"{name}_kerb_caps", YELLOW,
              [prism([(xr, 120), (x_end, kerb_top(x_end, e) - 10), (x_end, kerb_top(x_end, e) + 14), (xr, 144)],
                     "y", *sorted((s * 1785, s * 2015))) for s in (1, -1)])
        ribs = []
        for s in (1, -1):
            for f in (0.25, 0.5, 0.75):
                x = xt + (xr - xt) * f
                ribs.append(box(x - 35, x + 35, *sorted((s * 2005, s * 2055)), -2, kerb_top(x, e) - 30))
            ribs.append(box(xr - e * 5, xr + e * 25, *sorted((s * 1790, s * 2055)), -2, 110))
        m.add(f"{name}_ramp_ribs", PAINT, ribs)


# ---------------------------------------------------------------- spray bars

def spray(m):
    rp = m.r(38)
    bars, ups, nozzles = [], [], []
    for s in (1, -1):
        y = s * YS
        for z in ZS:
            bars.append(cyl(rp, (XF, y, z), (2900, y, z)))
            bars.append(sphere(rp + 6, (2900, y, z)))
            for x in np.arange(-2820.0, 2850.0, 300.0):
                d = np.array([0.0, -s * 0.87, -0.5])
                a = np.array([x, y, z])
                nozzles.append(cyl(m.r(14), P(a), P(a + d * (rp + 70))))
        # riser from the supply crossing under the ramp, through the kerb
        bars.append(cyl(rp, (XF, y, 400), (XF, y, ZS[1])))
        bars += [sphere(rp, (XF, y, z)) for z in ZS]
        for x in (-2400.0, -1200.0, 0.0, 1200.0, 2400.0):
            ups.append(cyl(m.r(30), (x, y, ZK - 5), (x, y, ZS[1] + 60)))
            ups.append(box(x - 70, x + 70, y - 70, y + 70, ZK + 5, ZK + 25))
    m.add("spray_bars", GALV, bars)
    m.add("spray_uprights", GALV, ups)
    m.add("spray_nozzles", BLACK, nozzles)


# ---------------------------------------------------------------- splash screens

def screens(m):
    posts, struts, feet, rails, sheets = [], [], [], [], []
    for s in (1, -1):
        y0, y1 = sorted((s * YP0, s * YP1))
        for x in POSTS:
            posts.append(box(x - 75, x + 75, y0, y1, -2, 2650))
            struts.append(bar((x, s * 2110, 1750), (x, s * 2620, 5), 90, 90))
            feet.append(box(x - 110, x + 110, *sorted((s * 2480, s * 2740)), -2, 25))
        rails.append(box(-3010, 3010, *sorted((s * 1950, s * 2150)), 2590, 2680))
        plan = corrugated_plan(-2990, 2990, s * 1960, 30, s * 2010)
        sheets.append(prism(plan, "z", ZW0, ZW1))
        # the outer face of the profiled sheet, corrugated too (behind the posts)
        sheets.append(prism(corrugated_plan(-2990, 2990, s * 2040, 30, s * 2000), "z", ZW0 + 20, ZW1))
    m.add("screen_posts", PAINT, posts, rails)
    m.add("screen_struts", PAINT, struts, feet)
    m.add("splash_screens", GALV, sheets)
    # floodlights under the top rails, lighting the bath
    hous, lens = [], []
    for s in (1, -1):
        for x in (-1500.0, 1500.0):
            hous.append(box(x - 160, x + 160, *sorted((s * 1830, s * 1960)), 2540, 2640))
            hous.append(box(x - 30, x + 30, *sorted((s * 1900, s * 1960)), 2630, 2600 + 10))
            lens.append(box(x - 140, x + 140, *sorted((s * 1845, s * 1945)), 2525, 2545))
    m.add("floodlights", BLACK, hous)
    m.add("floodlight_lenses", LED, lens)


# ---------------------------------------------------------------- recycling tank

def tank(m):
    m.add("tank_body", PAINT, box(X0 + 60, X1 - 60, Y0 + 60, Y1 - 60, 80, 2340))
    walls = [prism(corrugated_plan(X0 + 160, X1 - 160, Y1 - 10, 40, Y1 - 90), "z", 140, 2270),
             prism(corrugated_plan(X0 + 160, X1 - 160, Y0 + 10, 40, Y0 + 90), "z", 140, 2270)]
    for xe, xb in ((X1 - 10, X1 - 90), (X0 + 10, X0 + 90)):
        plan = corrugated_plan(Y0 + 160, Y1 - 160, xe, 40, xb)
        walls.append(prism([(v, u) for u, v in plan], "z", 140, 2270))
    m.add("tank_walls", PAINT, walls)
    frame = []
    for x0, x1 in ((X0, X0 + 170), (X1 - 170, X1)):
        for y0, y1 in ((Y0, Y0 + 170), (Y1 - 170, Y1)):
            frame.append(box(x0, x1, y0, y1, -2, 2410))
    for z0, z1 in ((-2, 150), (2260, 2400)):
        frame += [box(X0 + 160, X1 - 160, Y0 + 5, Y0 + 130, z0, z1), box(X0 + 160, X1 - 160, Y1 - 130, Y1 - 5, z0, z1),
                  box(X0 + 5, X0 + 130, Y0 + 160, Y1 - 160, z0, z1), box(X1 - 130, X1 - 5, Y0 + 160, Y1 - 160, z0, z1)]
    m.add("tank_frame", PAINT, frame)
    cast = []
    for xc in (X0, X1 - 170):
        for yc in (Y0, Y1 - 170):
            for z0, z1 in ((-2, 120), (2300, 2425)):
                cast.append(box(xc - 6, xc + 176, yc - 6, yc + 176, z0, z1))
    m.add("corner_castings", BLACK, cast)
    # fleet-number plate on the long side
    pt = m.t(10) + 10
    yf = Y1 - 15 + pt
    m.add("fleet_plate", YELLOW, box(-1750, -450, Y1 - 15, yf, 1550, 2120))
    ef = max(2.0, 0.3 * m.scale) if m.print_mode else 2.0
    words = [text("WW-04", 300, ef, (-1100, yf - 1, 1880), (-1, 0, 0), (0, 1, 0)),
             text("WASH WATER", 110, ef, (-1100, yf - 1, 1640), (-1, 0, 0), (0, 1, 0))]
    m.add("fleet_number", SIGN_TEXT, [w for w in words if w is not None])
    # drain valves on the far end, near the bottom
    valves, wheels = [], []
    for y in (Y0 + 700, Y1 - 700):
        valves += [cyl(70, (X1 - 40, y, 320), (X1 + 260, y, 320)), cyl(105, (X1 + 120, y, 320), (X1 + 200, y, 320)),
                   cyl(m.r(18), (X1 + 160, y, 320), (X1 + 160, y, 520))]
        wheels.append(cyl(110, (X1 + 160, y, 510), (X1 + 160, y, 510 + m.t(25))))
    m.add("drain_valves", GALV, valves)
    m.add("valve_wheels", BLACK, wheels)


def tank_top(m):
    m.add("tank_roof", PAINT, box(X0 + 100, X1 - 100, Y0 + 100, Y1 - 100, 2320, 2390))
    m.add("roof_walkway", GALV, prism(comb_y(X0 + 260, X1 - 260, 2380, 2400, 2420, 120, m.t(30)),
                                      "y", Y1 - 1000, Y1 - 160))
    hatches, hinges = [], []
    for x in (-1800.0, 700.0):
        hatches.append(box(x - 450, x + 450, Y0 + 300, Y0 + 1150, 2380, 2450))
        hatches.append(box(x - 420, x + 420, Y0 + 330, Y0 + 1120, 2440, 2465))
        hinges += [cyl(m.r(22), (x + dx - 70, Y0 + 290, 2440), (x + dx + 70, Y0 + 290, 2440)) for dx in (-280, 280)]
        hinges.append(box(x - 60, x + 60, Y0 + 1140, Y0 + 1190, 2420, 2470))
    m.add("tank_hatches", PAINT, hatches)
    m.add("hatch_hinges", BLACK, hinges)
    xv, yv = X0 + 450, Y0 + 450
    m.add("tank_vent", GALV, cyl(60, (xv, yv, 2380), (xv, yv, 2950)), sphere(60, (xv, yv, 2950)),
          cyl(60, (xv, yv, 2950), (xv + 260, yv, 2950)), sphere(60, (xv + 260, yv, 2950)),
          cyl(60, (xv + 260, yv, 2950), (xv + 260, yv, 2800)))

    # handrails round the roof, open at the stair landing
    rr = m.r(24)
    za, zb, zc = 2380.0, 2950.0, 3500.0
    xi0, xi1, yi0, yi1 = X0 + 75, X1 - 75, Y0 + 75, Y1 - 75
    xg = 2120.0                            # the +Y side rail stops here, at the landing
    posts = [(x, yi0) for x in np.linspace(xi0, xi1, 5)] + [(x, yi1) for x in np.linspace(xi0, xg, 4)]
    posts += [(xi0, YC), (xi1, YC), (xi1, yi1)]
    rails = [cyl(rr, (x, y, za), (x, y, zc + 10)) for x, y in posts]
    for z in (zb, zc):
        rails += [cyl(rr, (xi0, yi0, z), (xi1, yi0, z)), cyl(rr, (xi0, yi1, z), (xg, yi1, z)),
                  cyl(rr, (xi0, yi0, z), (xi0, yi1, z)), cyl(rr, (xi1, yi0, z), (xi1, yi1, z))]
    rails += [sphere(rr, (x, y, zc)) for x, y in ((xi0, yi0), (xi1, yi0), (xi0, yi1), (xi1, yi1), (xg, yi1))]
    m.add("roof_handrails", YELLOW, rails)


# ---------------------------------------------------------------- stair

XS0, XS1 = -400.0, 2150.0          # stair foot / head (nosing line from the ground to the landing)
ZL = 2410.0                        # landing top


def stair_z(x):
    return (x - XS0) * ZL / (XS1 - XS0)


def stair(m):
    ya, yb = Y1 + 70, Y1 + 790
    st = m.t(20)
    # stringers, landing and its legs
    xa_, xb_ = XS0 - 400, XS1 - 20
    side = [(xa_, stair_z(xa_) - 300), (xb_, stair_z(xb_) - 300), (xb_, stair_z(xb_) + 10), (xa_, stair_z(xa_) + 10)]
    side = clip_poly(side, xa_, xb_, -2, 3000)
    strs = [prism(side, "y", y - st / 2, y + st / 2) for y in (ya, yb)]
    land = [box(XS1 - 40, X1 - 10, Y1 - 80, yb + 20, ZL - 160, ZL - 40)]
    legs = [box(x - 50, x + 50, yb - 50, yb + 50, -2, ZL - 100) for x in (XS1 + 20, X1 - 70)]
    legs.append(bar((XS1 + 20, yb, 300), (X1 - 70, yb, 1800), 60, 60))
    m.add("stair_stringers", PAINT, strs, land, legs)
    n = 13
    treads = []
    for i in range(1, n):
        z = ZL * i / n
        x = XS0 + (XS1 - XS0) * i / n
        treads.append(box(x - 140, x + 140, ya - 5, yb + 5, z - 40, z))
    treads.append(prism(comb_y(XS1 - 30, X1 - 20, ZL - 50, ZL - 20, ZL, 120, m.t(30)), "y", Y1 - 70, yb + 10))
    m.add("stair_treads", GALV, treads)
    # handrails: sloping rails on both stringers, round the landing
    rr = m.r(24)
    rails = []
    h = 1000.0
    for y in (ya, yb):
        xs = (XS0 + 100, XS0 + 1300, XS1)
        rails += [cyl(rr, (x, y, stair_z(x) - 20), (x, y, stair_z(x) + h + 10)) for x in xs]
        rails += [cyl(rr, (xs[0], y, stair_z(xs[0]) + h), (XS1, y, stair_z(XS1) + h)),
                  cyl(rr, (xs[0], y, stair_z(xs[0]) + h / 2), (XS1, y, stair_z(XS1) + h / 2))]
    zt = ZL + 1100
    rails += [cyl(rr, (XS1, yb, ZL - 30), (XS1, yb, zt + 10)), cyl(rr, (X1 - 40, yb, ZL - 30), (X1 - 40, yb, zt + 10)),
              cyl(rr, (X1 - 40, Y1 - 75, ZL - 30), (X1 - 40, Y1 - 75, zt + 10))]
    for z in (ZL + 550, zt):
        rails += [cyl(rr, (XS1, yb, z), (X1 - 40, yb, z)), cyl(rr, (X1 - 40, Y1 - 75, z), (X1 - 40, yb, z))]
    rails += [cyl(rr, (XS1, yb, stair_z(XS1) + h), (XS1, yb, zt))]
    m.add("stair_handrails", YELLOW, rails)


# ---------------------------------------------------------------- sludge auger

def auger(m):
    s_wall = (X1 - AUG_A[0]) / AUG_D[0]
    m.add("auger_tube", PAINT, cyl(AUG_R, P(AUG_A), P(AUG_B)),
          [cyl(AUG_R + 38, P(aug(s)), P(aug(s + 45))) for s in (s_wall + 30, 1900.0, 2800.0)],
          cyl(AUG_R + 38, P(aug(AUG_L - 45)), P(aug(AUG_L))))
    # inspection covers along the top of the tube
    up = np.array([-AUG_D[2], 0.0, AUG_D[0]])
    m.add("auger_covers", GALV, [bar(P(aug(s) + up * (AUG_R - 10)), P(aug(s + 420) + up * (AUG_R - 10)), 220, 70,
                                     up=P(up)) for s in (1350.0, 2300.0)])
    # drive head: gearbox and motor on the axis
    m.add("auger_drive", BLACK, bar(P(aug(AUG_L - 20)), P(aug(AUG_L + 230)), 380, 420, up=P(up)),
          cyl(140, P(aug(AUG_L + 220)), P(aug(AUG_L + 680))), cyl(150, P(aug(AUG_L + 670)), P(aug(AUG_L + 740))),
          bar(P(aug(AUG_L + 300) + up * 120), P(aug(AUG_L + 520) + up * 120), 140, 110, up=P(up)))
    # discharge chute and rubber sock into the skip
    pc = aug(AUG_L - 400)
    m.add("auger_chute", PAINT, box(pc[0] - 180, pc[0] + 180, YC - 180, YC + 180, 2530, pc[2]))
    # galvanised liner collar at the foot of the chute, then a short rubber sock
    m.add("chute_collar", GALV, box(pc[0] - 185, pc[0] + 185, YC - 185, YC + 185, 2300, 2560),
          box(pc[0] - 205, pc[0] + 205, YC - 205, YC + 205, 2280, 2340))
    m.add("discharge_sock", RUBBER, cyl(175, (pc[0], YC, 1700), (pc[0], YC, 2310)))
    # A-frame support
    xa = 3500.0
    za = float(AUG_A[2] + (xa - AUG_A[0]) * AUG_D[2] / AUG_D[0])
    zt = za - AUG_R / AUG_D[0] + 60
    m.add("auger_support", PAINT, [bar((xa, YC + s * 750, 10), (xa, YC + s * 110, zt - 80), 100, 100) for s in (1, -1)],
          box(xa - 90, xa + 90, YC - 260, YC + 260, zt - 120, zt), bar((xa, YC - 560, 600), (xa, YC + 560, 600), 70, 70),
          [box(xa - 130, xa + 130, YC + s * 750 - 130, YC + s * 750 + 130, -2, 25) for s in (1, -1)])


# ---------------------------------------------------------------- sludge skip

def skip(m):
    xc, hb, ht, h, w = SKIP_X, 850.0, 1250.0, 1350.0, 900.0
    tw = m.t(8)
    outer = prism([(xc - hb, -2), (xc + hb, -2), (xc + ht, h), (xc - ht, h)], "y", YC - w, YC + w)
    k = (ht - hb) / (h + 2)

    def xin(z, side):
        return xc + side * (hb + k * (z + 2) - tw * 1.3)
    inner = prism([(xin(tw, -1), tw), (xin(tw, 1), tw), (xin(h + 20, 1), h + 20), (xin(h + 20, -1), h + 20)],
                  "y", YC - w + tw, YC + w - tw)
    rim = [box(xc - ht - 30, xc + ht + 30, YC + s * w - 40, YC + s * w + 40, h - 80, h + 20) for s in (1, -1)]
    rim += [prism([(xc + e * (ht - 40), h - 90), (xc + e * (ht + 35), h - 90), (xc + e * (ht + 35), h + 20),
                   (xc + e * (ht - 40), h + 20)], "y", YC - w - 40, YC + w + 40) for e in (1, -1)]
    ribs = [box(x - 50, x + 50, *sorted((YC + s * (w - 5), YC + s * (w + 60))), -2, h - 70)
            for s in (1, -1) for x in (xc - 500, xc + 500)]
    m.add("sludge_skip", YELLOW, cut(outer, inner), rim, ribs)
    m.add("skip_trunnions", BLACK, [cyl(85, (xc, YC + s * (w - 10), 900), (xc, YC + s * (w + 180), 900)) for s in (1, -1)],
          [cyl(120, (xc, YC + s * (w + 150), 900), (xc, YC + s * (w + 190), 900)) for s in (1, -1)])
    # the heap of settled sludge, filling the skip to ~0.75 m with a cone under the sock
    zf = 760.0
    fill = prism([(xin(tw - 5, -1) - 8, tw - 5), (xin(tw - 5, 1) + 8, tw - 5), (xin(zf, 1) + 8, zf), (xin(zf, -1) - 8, zf)],
                 "y", YC - w + tw - 5, YC + w - tw + 5)
    pc = aug(AUG_L - 400)
    m.add("sludge", SLUDGE, fill, cone(760, 110, (pc[0], YC, zf - 20), (pc[0], YC, 1230)),
          cyl(70, (pc[0], YC, 1200), (pc[0], YC, 1720)))          # the stream falling from the sock


# ---------------------------------------------------------------- pump set and controls

XP0, XP1 = -3300.0, -1300.0         # pump skid
YP = Y1 + 650.0                     # pump axis
ZP = 450.0


def pump_set(m):
    m.add("pump_skid", PAINT, box(XP0, XP1, Y1 - 40, Y1 + 1300, -2, 60),
          [box(XP0, XP1, y - 60, y + 60, 40, 180) for y in (Y1 + 300, Y1 + 1000)],
          box(-2420, -1300, YP - 260, YP + 260, 40, 170))
    # end-suction pump on its motor, axis along X
    m.add("pump_motor", BLACK, cyl(210, (-2300, YP, ZP), (-1850, YP, ZP)), cyl(180, (-2380, YP, ZP), (-2290, YP, ZP)),
          box(-2280, -1870, YP - 160, YP + 160, 160, ZP - 120),
          [box(-2270, -1880, YP - 12, YP + 12, ZP + 150, ZP + 235)], box(-2150, -1990, YP + 150, YP + 290, ZP - 60, ZP + 80))
    m.add("coupling_guard", YELLOW, box(-1860, -1700, YP - 130, YP + 130, ZP - 130, ZP + 130))
    m.add("pump_casing", PAINT, cyl(280, (-1710, YP, ZP + 20), (-1500, YP, ZP + 20)),
          cyl(120, (-1520, YP, ZP), (-1340, YP, ZP)), cyl(95, (-1600, YP, ZP + 250), (-1600, YP, 950)),
          box(-1720, -1490, YP - 200, YP + 200, 160, 260))
    # control cabinet on its stand, door facing out
    cx0, cx1, cy0, cy1 = -3220.0, -2480.0, Y1 + 860, Y1 + 1220
    m.add("cabinet_stand", PAINT, [box(x - 40, x + 40, y - 40, y + 40, 40, 520) for x in (cx0 + 60, cx1 - 60)
                                   for y in (cy0 + 60, cy1 - 60)],
          box(cx0 - 60, cx1 + 60, cy0 - 70, cy1 + 120, 1880, 1920))
    m.add("control_cabinet", STAINLESS, box(cx0, cx1, cy0, cy1, 500, 1890))
    m.add("cabinet_fittings", BLACK, box(cx1 - 110, cx1 - 70, cy1 - 5, cy1 + 35, 1050, 1250),
          box(cx0 + 300, cx0 + 420, cy1 - 5, cy1 + 40, 1500, 1620),
          [cyl(m.r(14), (x, cy1 - 5, z), (x, cy1 + 25, z)) for x in (cx0 + 70, cx0 + 120) for z in (650, 1700)])
    m.add("cabinet_lamps", LAMP_GREEN, cyl(28, (cx0 + 160, cy1 - 5, 1700), (cx0 + 160, cy1 + 25, 1700)))
    m.add("cabinet_lamps_red", LAMP_RED, cyl(28, (cx0 + 230, cy1 - 5, 1700), (cx0 + 230, cy1 + 25, 1700)))
    m.add("cabinet_lamp_bezel", GALV, box(cx0 + 135, cx0 + 275, cy1 - 5, cy1 + 12, 1650, 1750))
    m.add("beacon", AMBER, cyl(80, (cx1 - 150, cy0 + 180, 1910), (cx1 - 150, cy0 + 180, 2080)),
          sphere(80, (cx1 - 150, cy0 + 180, 2080)))
    m.add("cable_conduit", BLACK, pipe([(cx1 - 120, cy0 + 120, 510), (cx1 - 120, cy0 + 120, 260),
                                        (-2050, cy0 + 120, 260), (-2050, YP + 220, 260), (-2050, YP + 220, 420)], m.r(25)))


def pipework(m):
    rp = 70.0
    # pump suction from the tank side
    suc = [(-1370, YP, ZP), (-1150, YP, ZP), (-1150, Y1 - 60, ZP)]
    m.add("suction_pipe", GALV, pipe(suc, 115), cyl(160, (-1150, Y1 - 15, ZP), (-1150, Y1 + 40, ZP)),
          cyl(160, (-1400, YP, ZP), (-1330, YP, ZP)))
    # discharge main: up from the pump, round the tank end, under the entry ramp to the spray risers
    yr = 2450.0
    main = [(-1600, YP, 940), (-1600, YP, 1150), (X0 - 350, YP, 1150), (X0 - 350, YP, 400),
            (X0 - 350, yr, 400), (XF, yr, 400), (XF, -YS, 400)]
    m.add("supply_main", GALV, pipe(main, rp), [sphere(rp, p) for p in (main[-1],)])
    m.add("gate_valve", BLACK, box(-1680, -1520, YP - 80, YP + 80, 1000, 1110),
          cyl(m.r(16), (-1600, YP, 1110), (-1600, YP, 1260)), cyl(110, (-1600, YP, 1250), (-1600, YP, 1250 + m.t(25))))
    m.add("pipe_stands", PAINT, [box(X0 - 420, X0 - 280, y - 70, y + 70, -2, 340) for y in (3300.0, 4300.0)],
          [box(x - 70, x + 70, yr - 70, yr + 70, -2, 340) for x in (-3600.0,)])
    # drain hoses from the bath side into the tank
    hoses, flanges = [], []
    for x in (-800.0, 700.0):
        hoses.append(cyl(115, (x, YK1 - 40, 330), (x, Y0 + 60, 330)))
        flanges += [cyl(165, (x, YK1 + 10, 330), (x, YK1 + 60, 330)), cyl(165, (x, Y0 - 50, 330), (x, Y0 + 20, 330))]
    m.add("drain_hoses", RUBBER, hoses)
    m.add("hose_flanges", GALV, flanges)


# ---------------------------------------------------------------- GO / STOP light at the exit

def traffic_light(m):
    xp, yp = 3500.0, -2500.0
    m.add("light_base", PAINT, box(xp - 200, xp + 200, yp - 200, -1960, -2, 30),
          cyl(110, (xp, yp, 20), (xp, yp, 60)))
    m.add("light_post", GALV, cyl(60, (xp, yp, 20), (xp, yp, 2760)))
    m.add("light_head", BLACK, box(xp - 140, xp + 140, yp - 180, yp + 180, 2700, 3520),
          [box(xp + e * 140 - (m.t(10) if e > 0 else 160), xp + e * 140 + (160 if e > 0 else m.t(10)),
               yp - 150, yp + 150, z + 140, z + 140 + m.t(10)) for e in (1, -1) for z in (2910.0, 3300.0)])
    m.add("lamp_red", LAMP_RED, [cyl(125, (xp + e * 130, yp, 3300), (xp + e * 160, yp, 3300)) for e in (1, -1)])
    m.add("lamp_green", LAMP_GREEN, [cyl(125, (xp + e * 130, yp, 2910), (xp + e * 160, yp, 2910)) for e in (1, -1)])
    # silver bezel rings so both lamps read even when the lamp colours fold in the painted print
    m.add("lamp_bezels", GALV, [cut(cyl(150, (xp + e * 125, yp, z), (xp + e * 175, yp, z)),
                                    cyl(118, (xp + e * 120, yp, z), (xp + e * 180, yp, z)))
                                for e in (1, -1) for z in (2910.0, 3300.0)])
    # double-sided sign on the post, hanging outboard (-Y), readable from the bath and from beyond the exit
    st = m.t(10)
    xs0, xs1 = xp - st / 2 - 20, xp + st / 2 + 20
    ys = yp - 480
    m.add("light_sign", YELLOW, box(xs0, xs1, yp - 1000, yp + 40, 1900, 2450))
    ef = max(2.0, 0.3 * m.scale) if m.print_mode else 2.0
    words = []
    for xf, nx in ((xs1 - 1, 1), (xs0 + 1, -1)):
        words += [text("WAIT FOR", 150, ef, (xf, ys, 2290), (0, nx, 0), (nx, 0, 0)),
                  text("GREEN", 190, ef, (xf, ys, 2050), (0, nx, 0), (nx, 0, 0))]
    m.add("sign_text", SIGN_TEXT, [w for w in words if w is not None])
