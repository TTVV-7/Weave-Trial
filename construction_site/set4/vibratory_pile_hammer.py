"""Vibratory pile driver/extractor resting on timber cribbing, with its diesel hydraulic power pack.

A generic, brand-neutral crane-suspended vibro hammer of the medium class used for steel sheet
piles on quay walls and berth works (~50-60 kg.m eccentric moment, ~1,000-1,200 kN centrifugal
force, driven by a ~400-450 kW diesel hydraulic power unit), as it sits on site between lifts:

* hammer, ~2.4 m wide x ~0.9 m deep (1.2 m over the hose manifold and clamp cylinder) x ~3.6 m
  to the top of the shackle, standing on two timber cribbing stacks (five crossed layers of
  200 x 150 mm timbers, 0.75 m high) so the clamp hangs clear of the ground:
  - vibrator gearbox (eccentric housing), 2.3 m wide x 0.76 m deep x 1.05 m tall, chamfered
    underneath, with four bolted eccentric-bearing covers on each face, stiffening ribs and a
    top flange; two hydraulic drive motors standing on its top, with their pressure hoses;
  - suspension housing (0.68 m deep, 1.6 m wide, tapering to 0.9 m) sitting on twelve black
    rubber isolators on a yoke plate over the gearbox, with isolator end caps showing on both
    faces; a lifting eye plate with gussets on top and a ~25 t bow shackle in it;
  - hydraulic clamp under the gearbox for sheet piles: clamp body, horizontal clamp cylinder
    with its two hoses, a fixed and a moving serrated jaw;
  - hose manifold on the back face, with four bulkhead fittings for the hose bundle;
* power pack, skid-mounted sound-attenuated enclosure 5.0 m long x 2.0 m wide x 2.4 m to the
  top of the lifting eyes (2.8 m over the exhaust stack): channel-section skid with forklift
  pockets and the fuel tank built into it (filler neck and cap on the side), louvred doors
  with hinges and handles both sides, radiator grille at the rear end, roof with rain drip,
  four lifting eyes, exhaust stack with a rain flap, air intake, beacon; control panel with
  gauges, display and emergency stop under a rain hood on the front end, work light;
  hose quick-coupler panel low on the left side;
* colours: hammer yellow, power pack safety orange, black skid, hoses, louvres and isolators,
  steel clamp and fittings, weathered (grey) timber cribbing: four filaments in the print;
* hose bundle: four hydraulic hoses (two 3 in pressure/return lines, a 2 1/2 in boost line and
  a 1 3/4 in case drain, ~50-80 mm OD) looping down from the hammer manifold and lying on the
  ground (sunk 2 mm) along the power pack to its coupler panel.

Overall ~7.3 m x 2.6 m on plan. Dimensions are typical figures for the class, not any one
machine; no names, logos or maker-specific styling, only a generic fleet number.

Millimetres, X forward (the hammer at the +X end, the power pack's control end facing it),
Y left, Z up, ground at Z = 0, footprint roughly centred on the origin.
"""

from __future__ import annotations

import math

import cadquery as cq
import numpy as np

from cadkit import V, Finish, arc_pts, box, cut, cyl, frustum, mv, pipe, prism, rgb, rot, sphere, text, torus
from finishes import AMBER, BLACK, GALV, LED, ORANGE, RED, RUBBER, STEEL, WHITE, YELLOW

ASSET = dict(key="vibratory_pile_hammer", stem="Vibratory_Pile_Hammer",
             title="Vibratory Pile Hammer with Power Pack", az=35, el=22, size="1200x900")

HAMMER = YELLOW
PACK = ORANGE
CRIB = Finish(rgb("#9c8a72"), rough=0.9)        # weathered timber cribbing
SKID = BLACK
HOSE = RUBBER

# ---------------------------------------------------------------- hammer layout
HX, HY = 2900.0, -400.0         # hammer centre on plan (world)
XH, YH = 0.0, 0.0               # the hammer is drawn about its own centre, its broad faces
                                # towards local +-X, then turned 90 deg so they face +-Y
GW = 1150.0                     # gearbox half width (Y)
GD = 380.0                      # gearbox half depth (X)
ZG0, ZG1 = 748.0, 1800.0        # gearbox bottom (on the cribbing) and top
ZS0, ZS1 = 1960.0, 2900.0       # suspension housing bottom and top
SD = 340.0                      # suspension half depth (X)
Z_EYE = 3300.0                  # lifting eye hole centre

# ---------------------------------------------------------------- power pack layout
PX0, PX1 = -3800.0, 1200.0      # skid ends
PY0, PY1 = -1300.0, 700.0       # skid sides
EX0, EX1 = PX0 + 100, PX1 - 100     # enclosure ends
EY0, EY1 = PY0 + 50, PY1 - 50       # enclosure sides
EZ0, EZ1 = 225.0, 2180.0            # enclosure bottom / roof

# ---------------------------------------------------------------- hose bundle
HOSE_R = [24.0, 34.0, 40.0, 40.0]   # case drain, boost, return, pressure
HOSE_GAP = 20.0
Y_BUNDLE = 1100.0               # bundle centre line on the ground
XP = 0.0                        # where the bundle turns in towards the coupler panel
R_TURN = 300.0                  # turn radius of the bundle centre line
Z_CPL = 380.0                   # coupler height on the power pack
LY_MAN = 940.0                  # hose manifold centre along the hammer (local Y)
R_TURN1 = 250.0                 # first turn of the bundle, at the foot of the hammer


def world(lx, ly):
    """Hammer-local plan point to world: local +X -> world +Y, local +Y -> world -X."""
    return HX - ly, HY + lx


def hose_offsets():
    c = [0.0]
    for a, b in zip(HOSE_R, HOSE_R[1:]):
        c.append(c[-1] + a + b + HOSE_GAP)
    mid = (c[0] + c[-1]) / 2
    return [v - mid for v in c]


def hose(points, r):
    """A hose through points: a round tube swept along the polyline with rounded bends (one solid,
    far lighter than cylinders and joint balls); cylinders and balls if the sweep fails."""
    p = np.asarray(points, float)
    d0 = (p[1] - p[0]) / np.linalg.norm(p[1] - p[0])
    try:
        path = cq.Wire.makePolygon([V(*map(float, q)) for q in p])
        ring = cq.Wire.makeCircle(r, V(*map(float, p[0])), V(*map(float, d0)))
        tube = cq.Solid.sweep(ring, [], path, makeSolid=True, isFrenet=False, transitionMode="round")
        if tube.isValid() and len(tube.Solids()) == 1:
            return [tube]
    except Exception:
        pass
    return pipe(points, r)


def louvre(axis, wall, s, a0, a1, z0, z1, dep, pitch):
    """Louvre blades on a wall at u = wall (outward along s), sloping down and out, a0..a1 along
    the wall: a sawtooth section in (u, z) extruded along `axis`."""
    back = 20.0
    n = max(1, int((z1 - z0) // pitch))
    pts = [(wall - s * back, z0), (wall, z0)]
    for k in range(n):
        zt = z0 + (k + 1) * pitch
        pts.append((wall + s * dep, zt))
        if k < n - 1:
            pts.append((wall, zt))
    pts.append((wall - s * back, z0 + n * pitch))
    return prism(pts, axis, a0, a1)


def build(m):
    n = len(m.parts)
    hammer(m)
    cribbing(m)
    m.parts[n:] = [(name, fin, [mv(rot(sh, 90, (0, 0, 1)), HX, HY, 0) for sh in shapes])
                   for name, fin, shapes in m.parts[n:]]
    power_pack(m)
    hoses(m)


# ================================================================= hammer

def hammer(m):
    t, r = m.t, m.r

    # ---- vibrator gearbox (eccentric housing)
    prof = [(YH - 900, ZG0), (YH + 900, ZG0), (YH + GW, 980), (YH + GW, 1740), (YH + GW - 60, ZG1),
            (YH - GW + 60, ZG1), (YH - GW, 1740), (YH - GW, 980)]
    case = prism(prof, "x", XH - GD, XH + GD)
    flange = box(XH - GD - 30, XH + GD + 30, YH - GW - 25, YH + GW + 25, 1690, 1745)
    ribs = []
    for e in (1, -1):
        for yr in (-500.0, 0.0, 500.0):
            x0, x1 = (XH + GD - 10, XH + GD + 38) if e > 0 else (XH - GD - 38, XH - GD + 10)
            ribs.append(box(x0, x1, YH + yr - 20, YH + yr + 20, 800, 1700))
    m.add("gearbox", HAMMER, case, flange, ribs)

    covers, bolts, plugs = [], [], []
    for e in (1, -1):
        xf = XH + e * GD
        for yr in (-780.0, -260.0, 260.0, 780.0):
            y = YH + yr
            covers.append(cyl(200, (xf - e * 10, y, 1250), (xf + e * t(32), y, 1250)))
            plugs.append(cyl(62, (xf + e * 10, y, 1250), (xf + e * (t(32) + 22), y, 1250)))
            for k in range(6):
                a = 2 * math.pi * (k + 0.5) / 6
                yb, zb = y + 160 * math.cos(a), 1250 + 160 * math.sin(a)
                rb = r(22)
                hexa = [(yb + rb * math.cos(math.radians(60 * j)), zb + rb * math.sin(math.radians(60 * j)))
                        for j in range(6)]
                bolts.append(prism(hexa, "x", xf + e * 10, xf + e * (t(32) + 18)))
    m.add("eccentric_covers", HAMMER, covers)
    m.add("eccentric_cover_bolts", STEEL, bolts, plugs)

    # ---- hydraulic drive motors on the gearbox top
    motors, motor_caps = [], []
    for s in (1, -1):
        x, y = XH + 120, YH + s * 980
        motors += [cyl(130, (x, y, ZG1 - 12), (x, y, ZG1 + 32)), cyl(100, (x, y, ZG1 + 25), (x, y, 2060)),
                   box(x + 60, x + 150, y - 45, y + 45, 1900, 2010)]
        motor_caps += [cyl(84, (x, y, 2050), (x, y, 2095)), cyl(30, (x, y, 2090), (x, y, 2115))]
    m.add("drive_motors", BLACK, motors)
    m.add("motor_end_caps", STEEL, motor_caps)
    hr = r(22)
    m.add("motor_hoses", HOSE,
          hose([(XH + 120, YH + 980, 2080), (XH + 120, YH + 980, 2165), (XH + 330, YH + 980, 2165),
                (XH + 470, YH + 1000, 1930), (XH + 470, YH + 1000, 1760)], hr),
          hose([(XH + 210, YH + 980, 1955), (XH + 290, YH + 980, 1955), (XH + 290, YH + 1060, 1860),
                (XH + 290, YH + 1080, ZG1 - 30)], hr),
          hose([(XH + 120, YH - 980, 2080), (XH + 120, YH - 980, 2150), (XH - 160, YH - 980, 2150),
                (XH - 160, YH - 980, ZG1 - 20)], hr),
          hose([(XH + 210, YH - 980, 1955), (XH + 290, YH - 980, 1955), (XH + 290, YH - 1060, 1860),
                (XH + 290, YH - 1080, ZG1 - 30)], hr))

    # ---- suspension: yoke plate, rubber isolators, housing, lifting eye
    m.add("yoke_plate", HAMMER, box(XH - 330, XH + 330, YH - 820, YH + 820, ZG1 - 15, 1872))
    iso = [cyl(85, (XH + dx, YH + yr, 1862), (XH + dx, YH + yr, ZS0 + 12))
           for dx in (-170.0, 170.0) for yr in (-710.0, -440.0, -170.0, 170.0, 440.0, 710.0)]
    m.add("rubber_isolators", RUBBER, iso)

    sprof = [(YH - 800, ZS0), (YH + 800, ZS0), (YH + 800, 2600), (YH + 450, ZS1), (YH - 450, ZS1),
             (YH - 800, 2600)]
    housing = prism(sprof, "x", XH - SD, XH + SD)
    bands = [box(XH - SD - 25, XH + SD + 25, YH - 825, YH + 825, ZS0, ZS0 + 70)]
    m.add("suspension_housing", HAMMER, housing, bands)
    caps = []
    for e in (1, -1):
        for yr in (-580.0, -230.0, 230.0, 580.0):
            caps.append(cyl(105, (XH + e * (SD - 10), YH + yr, 2330), (XH + e * (SD + t(22)), YH + yr, 2330)))
    m.add("isolator_caps", RUBBER, caps)
    cap_bolts = [cyl(r(26), (XH + e * (SD - 10), YH + yr, 2330), (XH + e * (SD + t(22) + 16), YH + yr, 2330))
                 for e in (1, -1) for yr in (-580.0, -230.0, 230.0, 580.0)]
    m.add("isolator_cap_bolts", STEEL, cap_bolts)

    pt = t(100)
    eye_prof = [(YH - 330, ZS1 - 20), (YH + 330, ZS1 - 20)] + arc_pts(YH, Z_EYE, 260, -12, 192, 24)
    eye = cut(prism(eye_prof, "x", XH - pt / 2, XH + pt / 2), cyl(120, (XH - 200, YH, Z_EYE), (XH + 200, YH, Z_EYE)))
    gus = []
    gt = t(30)
    for e in (1, -1):
        for yr in (-190.0, 190.0):
            tri = [(XH + e * (pt / 2 - 5), ZS1 - 10), (XH + e * 240, ZS1 - 10), (XH + e * (pt / 2 - 5), 3110)]
            gus.append(prism(tri, "y", YH + yr - gt / 2, YH + yr + gt / 2))
    m.add("lifting_eye", HAMMER, eye, gus)

    # bow shackle in the eye, pin resting on the bottom of the hole
    rp, rl = r(34), r(28)
    zp = Z_EYE - 120 + rp - 5
    off = pt / 2 + rl + 4
    zb = zp + 230
    sh = [cyl(rp, (XH - off - 30, YH, zp), (XH + off + 26, YH, zp)),
          cyl(rp + 12, (XH - off - 30, YH, zp), (XH - off - 12, YH, zp))]
    for d in (1, -1):
        sh.append(cyl(rl, (XH + d * off, YH, zp - 10), (XH + d * off, YH, zb + 6)))
        sh.append(cyl(rl + 9, (XH + d * off, YH, zp - 30), (XH + d * off, YH, zp + 30)))
    sh.append(torus(off, rl, (XH, YH, zb), (0, 1, 0)).intersect(
        box(XH - off - 60, XH + off + 60, YH - 60, YH + 60, zb, zb + off + 60)))
    m.add("shackle", GALV, sh)

    # ---- hydraulic clamp (sheet-pile jaws) under the gearbox
    body = [box(XH - 300, XH + 300, YH - 280, YH + 280, 440, 770),
            box(XH - 345, XH + 345, YH - 325, YH + 325, 690, 775)]
    body += [box(XH - 210, XH + 210, YH + s * 230, YH + s * 300, 380, 450) for s in (1, -1)]
    cylc = [cyl(140, (XH + 250, YH, 590), (XH + 560, YH, 590)), cyl(155, (XH + 540, YH, 590), (XH + 585, YH, 590))]
    m.add("clamp_body", STEEL, body, cylc)
    jaw_f = [(XH - 175, 455), (XH - 30, 455), (XH - 30, 170), (XH - 105, 170), (XH - 175, 270)]
    jaw_m = [(2 * XH - x, z) for x, z in jaw_f]
    m.add("clamp_jaws", GALV, prism(jaw_f, "y", YH - 215, YH + 215), prism(jaw_m, "y", YH - 215, YH + 215))
    teeth = []
    for e in (1, -1):
        pts = [(XH + e * 36, 180)]
        z = 180.0
        while z + 40 <= 440:
            pts += [(XH + e * 16, z + 20), (XH + e * 36, z + 40)]
            z += 40
        pts += [(XH + e * 40, z), (XH + e * 40, 180)]
        teeth.append(prism(pts, "y", YH - 200, YH + 200))
    m.add("jaw_teeth", BLACK, teeth)
    m.add("clamp_hoses", HOSE,
          [hose([(XH + 565, YH + s * 80, 650), (XH + 645, YH + s * 80, 720), (XH + 645, YH + s * 80, 880),
                 (XH + 560, YH + s * 80, 955), (XH + GD - 15, YH + s * 80, 960)], r(20)) for s in (1, -1)])

    # ---- hose manifold on the front face, bulkhead fittings for the bundle
    lys = [LY_MAN - d for d in hose_offsets()]
    m.add("hose_manifold", HAMMER, box(XH + GD - 10, XH + GD + 190, lys[-1] - 75, lys[0] + 70, 1520, 1775))
    fits = []
    for y, hr_ in zip(lys, HOSE_R):
        fits.append(cyl(hr_ + 8, (XH + GD + 180, y, 1650), (XH + GD + 265, y, 1650)))
        fits.append(cyl(hr_ + 18, (XH + GD + 185, y, 1650), (XH + GD + 215, y, 1650)))
    m.add("manifold_fittings", STEEL, fits)

    # ---- fleet number on the suspension
    ef = max(2.0, 0.3 * m.scale) if m.print_mode else 2.0
    words = [text("VH-12", 170, ef, (XH + SD - 1, YH, 2700), (0, 1, 0), (1, 0, 0)),
             text("VH-12", 170, ef, (XH - SD + 1, YH, 2700), (0, -1, 0), (-1, 0, 0))]
    m.add("fleet_number", BLACK, [w for w in words if w is not None])


def cribbing(m):
    """Two stacks of crossed 200 x 150 timbers under the gearbox, 5 layers, 0.75 m high."""
    tb = []
    for s in (1, -1):
        yc = YH + s * 650
        for k in range(5):
            z0, z1 = 150.0 * k - 2, 150.0 * k + 150
            if k % 2 == 0:      # along X
                for dy in (-125.0, 125.0):
                    tb.append(box(XH - 550 + 15 * k, XH + 550 - 10 * k, yc + dy - 100, yc + dy + 100, z0, z1))
            else:               # along Y
                for dx in (-400.0, 0.0, 400.0):
                    tb.append(box(XH + dx - 100, XH + dx + 100, yc - 262, yc + 258, z0, z1))
    m.add("timber_cribbing", CRIB, tb)


# ================================================================= power pack

def power_pack(m):
    t, r = m.t, m.r

    # ---- skid base with the fuel tank, channel rails and forklift pockets
    rails = []
    for y0, y1 in ((PY0, PY0 + 150), (PY1 - 150, PY1)):
        rails.append(box(PX0, PX1, y0, y1, -2, 240))
    deck = box(PX0 + 60, PX1 - 60, PY0 + 100, PY1 - 100, 20, 250)
    ends = [box(PX0 - 20, PX0 + 140, PY0 + 30, PY1 - 30, 15, 230), box(PX1 - 140, PX1 + 20, PY0 + 30, PY1 - 30, 15, 230)]
    pockets = [box(xc - 220, xc + 220, PY0 - 50, PY1 + 50, 55, 185) for xc in (-2400.0, -200.0)]
    web = [box(PX0 + 160, PX1 - 160, y0, y1, 45, 195)
           for y0, y1 in ((PY0 - 10, PY0 + 50), (PY1 - 50, PY1 + 10))]       # channel recess
    m.add("skid", SKID, [cut(s_, *pockets, *web) for s_ in rails + [deck] + ends])
    pocket_lips = []
    for xc in (-2400.0, -200.0):
        for y0, y1 in ((PY0 - 8, PY0 + 40), (PY1 - 40, PY1 + 8)):
            pocket_lips.append(cut(box(xc - 250, xc + 250, y0, y1, 30, 210), box(xc - 220, xc + 220, y0 - 5, y1 + 5, 55, 185)))
    m.add("fork_pocket_frames", STEEL, pocket_lips)

    # ---- fuel filler on the left side of the skid
    m.add("fuel_filler_neck", STEEL, cyl(48, (-3250, PY1 - 30, 190), (-3250, PY1 + 75, 190)))
    m.add("fuel_cap", BLACK, cyl(68, (-3250, PY1 + 60, 190), (-3250, PY1 + 60 + t(40), 190)))
    m.add("fuel_cap_ring", RED, cut(cyl(80, (-3250, PY1 - 5, 190), (-3250, PY1 + 18, 190)),
                                    cyl(56, (-3250, PY1 - 10, 190), (-3250, PY1 + 30, 190))))

    # ---- enclosure, roof
    shell = box(EX0, EX1, EY0, EY1, EZ0, EZ1)
    roof = [box(EX0 - 25, EX1 + 25, EY0 - 25, EY1 + 25, EZ1 - 10, EZ1 + 35),
            frustum((EX0, EX1, EY0, EY1, EZ1 + 30), (EX0 + 100, EX1 - 100, EY0 + 100, EY1 - 100, EZ1 + 100))]
    m.add("enclosure", PACK, shell, roof)

    # ---- doors, both sides, with louvres, hinges and handles
    dt = t(14)
    doors = [(-3600.0, -2700.0, 330.0), (-2640.0, -1740.0, 330.0), (-1680.0, -780.0, 330.0), (-700.0, 960.0, 640.0)]
    panels, louv, hinges, handles = [], [], [], []
    for s in (1, -1):
        yw = EY1 if s > 0 else EY0
        yo = yw + s * dt
        for x0, x1, z0 in doors:
            z0 = z0 if s > 0 else 330.0          # no coupler panel on the right side
            z1 = 2080.0
            panels.append(box(x0, x1, yw - s * 5, yo, z0, z1))
            for g0, g1 in ((z1 - 520, z1 - 90), (z0 + 90, z0 + 430)):
                louv.append(louvre("x", yo, s, x0 + 110, x1 - 110, g0, g1, t(22), 66))
            hr_ = r(20)
            yh = yo + s * (hr_ - 6)
            for zh in (z0 + 180, z1 - 300):
                hinges.append(cyl(hr_, (x0 + 22, yh, zh), (x0 + 22, yh, zh + 130)))
            handles.append(box(x1 - 120, x1 - 60, yo - s * 4, yo + s * t(28), 1180, 1330))
            handles.append(box(x1 - 105, x1 - 75, yo - s * 4, yo + s * (t(28) + 20), 1210, 1250))
    m.add("doors", PACK, panels)
    m.add("door_louvres", BLACK, louv)
    m.add("door_hinges", STEEL, hinges)
    m.add("door_handles", STEEL, handles)

    # ---- radiator grille on the rear end, hydraulic cooler grille above
    m.add("radiator_grille", BLACK, louvre("y", EX0, -1, EY0 + 180, EY1 - 180, 520, 1900, t(24), 70))
    m.add("rear_grille_frame", PACK,
          cut(box(EX0 - t(40), EX0 + 10, EY0 + 120, EY1 - 120, 460, 1960),
              box(EX0 - 100, EX0 + 20, EY0 + 175, EY1 - 175, 515, 1905)))

    # ---- front end (facing the hammer): control panel under a rain hood, work light
    xf = EX1
    yc = 180.0                                  # control panel centre, left of the hammer
    cab = box(xf - 10, xf + 150, yc - 400, yc + 400, 880, 1720)
    hood = prism([(xf - 10, 1700), (xf + 260, 1760), (xf + 260, 1760 + t(16)), (xf - 10, 1800)], "y",
                 yc - 440, yc + 440)
    m.add("control_cabinet", PACK, cab, hood)
    face = box(xf + 140, xf + 150 + t(10), yc - 350, yc + 350, 930, 1660)
    m.add("control_face", STEEL, face)
    xg = xf + 150 + t(10)
    gauges = [cyl(58, (xg - 5, yc + dy, 1480), (xg + 20, yc + dy, 1480)) for dy in (-250.0, -100.0, 50.0)]
    m.add("gauges", WHITE, gauges)
    m.add("display", BLACK, box(xg - 5, xg + 15, yc + 120, yc + 300, 1400, 1560),
          [cyl(r(22), (xg - 5, yc + dy, 1180), (xg + 30, yc + dy, 1180)) for dy in (-270.0, -170.0, -70.0)])
    m.add("emergency_stop", RED, cyl(40, (xg - 5, yc + 210, 1150), (xg + 40, yc + 210, 1150)),
          sphere(52, (xg + 40, yc + 210, 1150)))
    m.add("estop_collar", AMBER, cyl(70, (xg - 5, yc + 210, 1150), (xg + 15, yc + 210, 1150)))
    m.add("work_light", BLACK, box(xf - 10, xf + 120, -650, -450, 1900, 2050))
    m.add("work_light_lens", LED, box(xf + 110, xf + 120 + t(10), -630, -470, 1920, 2030))
    # battery isolator and the hydraulic tank sight gauge on the front end
    m.add("sight_gauge", STEEL, box(xf - 10, xf + 40, -900, -820, 500, 900))
    m.add("sight_glass", AMBER, box(xf + 35, xf + 40 + t(8), -885, -835, 530, 870))
    m.add("isolator_switch", RED, box(xf - 10, xf + 60, -1100, -1040, 700, 800))

    # ---- hose coupler panel, low on the left side
    offs = hose_offsets()
    xs = [XP - (R_TURN + d) for d in offs]
    m.add("coupler_panel", STEEL, box(min(xs) - 90, max(xs) + 90, EY1 - 10, EY1 + t(16), 250, 520))
    cpl = []
    for x, hr_ in zip(xs, HOSE_R):
        cpl.append(cyl(hr_ + 5, (x, EY1, Z_CPL), (x, EY1 + 140, Z_CPL)))
        cpl.append(cyl(hr_ + 14, (x, EY1 + 40, Z_CPL), (x, EY1 + 75, Z_CPL)))
    m.add("quick_couplers", STEEL, cpl)

    # ---- roof: lifting eyes, exhaust stack with rain flap, air intake, beacon
    eyes = []
    et = t(40)
    for x in (EX0 + 160, EX1 - 160):
        for y in (EY0 + 160, EY1 - 160):
            prof = [(x - 120, EZ1 + 20), (x + 120, EZ1 + 20)] + arc_pts(x, EZ1 + 170, 110, 0, 180, 14)
            eyes.append(cut(prism(prof, "y", y - et / 2, y + et / 2),
                            cyl(48, (x, y - 80, EZ1 + 170), (x, y + 80, EZ1 + 170))))
    m.add("roof_lifting_eyes", PACK, eyes)

    xs_, ys_ = -3150.0, -850.0
    m.add("exhaust_stack", STEEL, cyl(110, (xs_, ys_, EZ1 + 60), (xs_, ys_, EZ1 + 150)),
          cyl(70, (xs_, ys_, EZ1 + 120), (xs_, ys_, 2800)))
    flap_t = t(10)
    flap = box(-85, 85, -85, 85, -flap_t / 2, flap_t / 2)
    flap = mv(rot(flap, -12, (0, 1, 0)), xs_, ys_, 2810)
    m.add("rain_flap", BLACK, flap, cyl(r(14), (xs_ - 95, ys_ - 90, 2790), (xs_ - 95, ys_ + 90, 2790)))
    m.add("air_intake", BLACK, box(-2700, -2350, -1000, -650, EZ1 + 60, EZ1 + 260),
          box(-2730, -2320, -1030, -620, EZ1 + 250, EZ1 + 300))
    m.add("beacon_base", BLACK, cyl(80, (850, 350, EZ1 + 80), (850, 350, EZ1 + 140)))
    m.add("beacon", AMBER, cyl(62, (850, 350, EZ1 + 135), (850, 350, EZ1 + 240)), sphere(62, (850, 350, EZ1 + 240)))

    # ---- fleet number and a hazard band on the doors
    ef = max(2.0, 0.3 * m.scale) if m.print_mode else 2.0
    yo = EY1 + dt
    words = [text("HPU-07", 150, ef, (-2260, yo - 1, 1250), (-1, 0, 0), (0, 1, 0)),
             text("HPU-07", 150, ef, (-2260, EY0 - dt + 1, 1250), (1, 0, 0), (0, -1, 0))]
    m.add("pack_number", BLACK, [w for w in words if w is not None])


# ================================================================= hose bundle

def hoses(m):
    offs = hose_offsets()
    xm, y0 = world(GD + 220, LY_MAN)          # manifold centre on plan, hose start
    yg = Y_BUNDLE - R_TURN1                    # where the bundle reaches the ground
    for i, (d, hr) in enumerate(zip(offs, HOSE_R)):
        x = xm + d
        zg = hr - 2
        # loop out of the manifold on the hammer's front face and down to the ground
        drop = [(0, 1650), (130, 1630), (250, 1550), (340, 1400), (400, 1180), (430, 900), (440, 620),
                (445, 400), (465, 230), (510, 110)]
        k = (yg - y0) / 650.0
        pts = [(x, y0 + dy * k, z) for dy, z in drop]
        pts.append((x, y0 + 570 * k, zg + 25))
        pts.append((x, yg, zg))
        # first turn on the ground, heading -X along the power pack
        rho = R_TURN1 + d
        for a in range(15, 91, 15):
            pts.append((xm - R_TURN1 + rho * math.cos(math.radians(a)), yg + rho * math.sin(math.radians(a)), zg))
        y = Y_BUNDLE + d
        # then a turn in towards the coupler panel, rising into the coupler
        rho = R_TURN + d
        cy = Y_BUNDLE - R_TURN
        pts.append((XP + 60, y, zg))
        for a in range(90, 181, 10):
            f = max(0.0, (a - 120) / 60)
            f = f * f * (3 - 2 * f)
            pts.append((XP + rho * math.cos(math.radians(a)), cy + rho * math.sin(math.radians(a)),
                        zg + (Z_CPL - zg) * f))
        pts.append((XP - rho, EY1 + 60, Z_CPL))
        m.add(f"hose_{i + 1}", HOSE, hose(pts, hr))
