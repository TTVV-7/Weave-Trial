"""Road-rail railcar mover (shunting vehicle) on a short length of standard-gauge track.

A generic, brand-neutral machine with the typical proportions of the mid-size road-rail
railcar movers used to spot wagons under loading and unloading stations at bulk terminals:
it drives on four large rubber tyres on the road, and on the track it lowers a set of
flanged steel guide wheels at each end so that the tyres ride on the rail heads for traction
while the steel wheels keep it on the rails. Shown on the track, rail gear deployed.

Dimensions are typical figures for the class, not any one machine:
  body 4.70 m long x 2.90 m wide over the deck, ~5.6 m over the coupler knuckles,
      ~3.2 m above the ground to the top of the beacons (3.1 m to the cab roof)
  tyres ~1.20 m OD x 420 mm, on a 2.40 m wheelbase, their centre planes on the rail heads
      (1,509 mm apart), sunk 9 mm (1.5 % of the radius) into the rail heads
  rail gear: 460 mm tread / 510 mm flange steel wheels at 4.24 m centres, flanges inside
      the gauge, treads sunk 3.5 mm (1.5 %) into the rail heads
  couplers: standard knuckle couplers, centreline 870 mm (34.5 in) above the rail top, each
      on a vertical weight-transfer carriage lifted by two hydraulic cylinders
  track: two 6.8 m lengths of ~136 lb/yd flat-bottom rail (186 mm high, 74 mm head, 152 mm
      base) at 1,435 mm gauge on tie plates, twelve 2.59 m x 230 x 178 mm timber ties at
      570 mm centres, sunk 2 mm into the ground; rail top 376 mm above the ground.

Layout: central chassis between the tyres, a full-width deck with walkways on both sides,
a low front hood (hydraulics and air compressor, cooler grille on top), a centre cab with
glazing all round, sliding doors on both sides, a side-facing seat and consoles, roof work
lights and two beacons, and a taller rear engine hood with louvres, radiator grille, exhaust
stack and air pre-cleaner. Under the deck: fuel tank (left), two air reservoirs on a back
plate (right), access ladders on both sides. Each end: yellow/black chevron plates, head,
tail and indicator lamps, stirrup steps and grab irons, the coupler carriage with its guides
and lift cylinders, an uncoupling lever, a brake-pipe hose with a glad hand, and the rail
gear (pivot arms, axle beam, lift cylinder) under the end box. Deck handrails, mirrors,
wipers, fleet number.

Millimetres, X forward, Y left, Z up, ground at Z = 0, footprint centred on the origin.
"""

from __future__ import annotations

import math

import cadquery as cq
import numpy as np

from cadkit import bar, box, clip_poly, cone, cut, cyl, place, prism, rot, rounded_box, text
from finishes import (AMBER, BLACK, CHROME, DARK, GALV, GLASS, LED, MILL, RED, RUBBER, STEEL, TIMBER_DARK,
                      YELLOW)

ASSET = dict(key="railcar_mover", stem="Road_Rail_Railcar_Mover", title="Road-Rail Railcar Mover",
             az=40, el=18, size="1200x900")

# ---- track
GAUGE = 1435.0
HEAD_W = 74.0
RC = GAUGE / 2 + HEAD_W / 2       # rail centre line, |y|
Z_TIE = 176.0                     # tie top (ties sunk 2 mm)
Z_PLATE = 192.0                   # tie-plate top
RT = 376.0                        # rail top
TRACK_X = 3400.0                  # rails run -TRACK_X .. TRACK_X

# ---- road wheels
R = 600.0                         # tyre radius (~1.20 m OD)
ZA = RT + R - 0.015 * R           # axle height: tyres sunk 1.5 % into the rail heads
XW = 1200.0                       # axle |x| (2.40 m wheelbase)

# ---- rail gear
RG, RF = 230.0, 255.0             # tread / flange radius
ZG = RT + RG - 0.015 * RG         # rail-wheel axle height
XG = 2120.0                       # rail-wheel axle |x|

# ---- body
XE = 2350.0                       # end face |x|
YB = 1450.0                       # half width over the deck
ZD0, ZD = 1640.0, 1720.0          # deck underside / top
XEB = 1850.0                      # inner face of the end boxes
ZEB = 1000.0                      # underside of the end boxes
ZK = RT + 870.0                   # coupler centreline

# ---- cab
CX, CY = 900.0, 950.0
ZB, ZR = 2180.0, 3000.0           # belt line, roof


def ys(a, b, s=1):
    """The |y| range a..b on side s, sorted."""
    return tuple(sorted((s * a, s * b)))


def rod(a, b, r, n=12):
    """A straight rod from a to b as an n-sided prism: reads round at this size, and keeps the
    web model light (a true cylinder this long is tessellated finely)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    L = float(np.linalg.norm(d))
    z = d / L
    x = np.cross(z, [0.0, 0, 1.0] if abs(z[2]) < 0.9 else [1.0, 0, 0])
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    pts = [(r * math.cos(2 * math.pi * (k + 0.5) / n), r * math.sin(2 * math.pi * (k + 0.5) / n)) for k in range(n)]
    return place(prism(pts, "z", 0, L), tuple(x), tuple(y), tuple(z), tuple(a))


def tube(points, r):
    """A bent rod through points: straight rods, each lengthened by r into its neighbours at
    the bends so the corners close without the (triangle-heavy) balls of cadkit.pipe."""
    pts = [np.asarray(p, float) for p in points]
    out = []
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        u = (b - a) / np.linalg.norm(b - a)
        a2 = a - u * r if i > 0 else a
        b2 = b + u * r if i < len(pts) - 2 else b
        out.append(rod(a2, b2, r))
    return out


def tank(x0, x1, y, z, rad, head=0.45):
    """Horizontal air reservoir along X with shallow dished heads (a revolved profile)."""
    h = rad * head
    prof = [(0.0, x0)] + [(rad * math.sin(math.radians(a)), x0 + h - h * math.cos(math.radians(a)))
                          for a in (25, 50, 70, 90)]
    prof += [(rr, x1 - (xx - x0)) for rr, xx in reversed(prof)]
    w = cq.Workplane("XY").polyline([(rr, xx) for rr, xx in prof]).close().revolve(360, (0, 0, 0), (0, 1, 0)).val()
    # revolved about local Y: map local (x=r, y=axis) so the axis lies along global X
    return rot(w, -90, (0, 0, 1)).translate(cq.Vector(0, y, z))


def jack(a, b, rb, rr, frac, eye_axis):
    """Hydraulic cylinder from a (base) to b (rod end): barrel, gland ring, rod, and a cross-pin
    eye boss at each end along eye_axis (no balls). Returns (barrel parts, rod parts)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    u = (b - a) / np.linalg.norm(b - a)
    j = a + (b - a) * frac
    e = np.asarray(eye_axis, float)
    T = lambda p: tuple(map(float, p))      # noqa: E731
    barrel = [cyl(rb, T(a), T(j)), cyl(rb * 1.12, T(j - u * 40), T(j + u * 5)),
              cyl(rb * 0.85, T(a - e * rb * 0.9), T(a + e * rb * 0.9))]
    rod = [cyl(rr, T(j - u * 20), T(b)), cyl(rr * 1.25, T(b - e * rr * 1.3), T(b + e * rr * 1.3))]
    return barrel, rod


def tyre_at_origin():
    """Rubber tyre, axis along Y through the origin, outer face towards +y: rounded carcass with
    two circumferential grooves and alternating shoulder slots (centre rib rides the rail head)."""
    prof = [(310, -200), (420, -212), (520, -210), (565, -200), (590, -180), (R, -150),
            (R, 150), (590, 180), (565, 200), (520, 210), (420, 212), (310, 200)]
    tyre = cq.Workplane("XY").polyline(prof).close().revolve(360, (0, 0, 0), (0, 1, 0)).val()
    cuts = []
    for y0 in (-118.0, 96.0):
        cuts.append(cut(cyl(R + 10, (0, y0, 0), (0, y0 + 22, 0)), cyl(R - 18, (0, y0 - 1, 0), (0, y0 + 23, 0))))
    n = 30
    for k in range(n):
        lo, hi = (130.0, 230.0) if k % 2 else (-230.0, -130.0)
        slot = box(-17, 17, lo, hi, R - 20, R + 30)
        cuts.append(rot(slot, 360.0 * k / n, (0, 1, 0)))
    return cut(tyre, *cuts)


def chevrons(y0, y1, z0, z1, width, pitch, s):
    """(y, z) polygons of black chevron stripes on a rectangle, sloping down and outward (side s)."""
    polys = []
    vals = [s * y + z for y in (y0, y1) for z in (z0, z1)]
    for c in np.arange(min(vals) - width + 60, max(vals), pitch):
        # band between the lines s*y + z = c and s*y + z = c + width, in rectangle coordinates
        ya, yb = y0 - 2000, y1 + 2000
        band_ = [(ya, c - s * ya), (yb, c - s * yb), (yb, c + width - s * yb), (ya, c + width - s * ya)]
        p = clip_poly(band_, y0, y1, z0, z1)
        if len(p) >= 3:
            # drop slivers at the corners
            area = 0.5 * abs(sum(u0 * v1 - u1 * v0 for (u0, v0), (u1, v1) in zip(p, p[1:] + p[:1])))
            if area > 0.18 * width * width:
                polys.append(p)
    return polys


def end_parts(m):
    """Everything at the front (+x) end: end box, chevron plates, lamps, coupler carriage and
    weight-transfer cylinders, coupler, uncoupling lever, brake hose, steps, rail gear.
    Returns [(name, finish, shapes)]; the rear end is the same turned 180 deg about Z."""
    t, r = m.t, m.r
    out = {}

    def add(name, fin, *shapes):
        flat = []

        def walk(items):
            for s in items:
                if isinstance(s, (list, tuple)):
                    walk(s)
                elif s is not None:
                    flat.append(s)
        walk(shapes)
        if name in out:
            out[name][1].extend(flat)
        else:
            out[name] = (fin, flat)

    add("end_box", YELLOW, box(XEB, XE, -YB, YB, ZEB, ZD0 + 5))

    # chevron plates either side of the coupler carriage
    pz0, pz1 = 1020.0, 1500.0
    plates, stripes = [], []
    for s in (1, -1):
        y0, y1 = ys(640, 1420, s)
        plates.append(box(XE - 10, XE + 20, y0, y1, pz0, pz1))
        for p in chevrons(y0, y1, pz0, pz1, 130.0, 260.0, s):
            stripes.append(prism(p, "x", XE + 15, XE + 20 + t(6)))
    add("chevron_plates", YELLOW, plates)
    add("chevron_stripes", BLACK, stripes)

    # lamps: headlight, indicator, tail light each side, above the chevrons
    lt = t(10)
    add("end_lamp_housings", BLACK, [box(XE - 10, XE + 70, *ys(880, 1400, s), 1530, 1630) for s in (1, -1)])
    add("headlights", LED, [box(XE + 66, XE + 70 + lt, *ys(1240, 1385, s), 1545, 1615) for s in (1, -1)])
    add("indicators", AMBER, [box(XE + 66, XE + 70 + lt, *ys(1065, 1220, s), 1545, 1615) for s in (1, -1)])
    add("tail_lights", RED, [box(XE + 66, XE + 70 + lt, *ys(895, 1045, s), 1545, 1615) for s in (1, -1)])

    # weight-transfer coupler: carriage between two guides, lifted by two cylinders
    add("coupler_guides", DARK, [box(XE - 10, XE + 70, *ys(345, 425, s), ZEB + 10, 1700) for s in (1, -1)],
        [box(XE - 10, XE + 150, *ys(430, 610, s), ZEB + 10, ZEB + 70) for s in (1, -1)])
    add("coupler_carriage", BLACK, box(XE - 10, XE + 55, -335, 335, 1070, 1620),
        box(XE + 20, XE + 150, -610, 610, 1615, 1690))
    for s in (1, -1):
        a, b = (XE + 75, s * 520, ZEB + 60), (XE + 75, s * 520, 1625)
        barrel, rod = jack(a, b, 62, 34, 0.58, (1, 0, 0))
        add("weight_transfer_cylinder", BLACK, barrel)
        add("weight_transfer_rod", CHROME, rod)
    k0 = XE + 160
    shank = box(XE + 40, k0 + 20, -85, 85, ZK - 80, ZK + 80)
    head = [(k0, -150), (k0 + 150, -150), (k0 + 225, -125), (k0 + 250, -75), (k0 + 205, -50),
            (k0 + 172, -20), (k0 + 178, 40), (k0 + 240, 58), (k0 + 270, 100), (k0 + 252, 160),
            (k0 + 190, 186), (k0 + 60, 172), (k0, 120)]
    add("coupler", MILL, shank, prism(head, "z", ZK - 140, ZK + 140),
        box(XE + 30, XE + 70, -150, 150, ZK - 120, ZK + 120))          # yoke flange on the carriage
    add("knuckle_pin", STEEL, cyl(30, (k0 + 215, 110, ZK - 160), (k0 + 215, 110, ZK + 165)))
    # uncoupling lever across the end, handle at the right corner
    lx = XE + 135
    lever = tube([(k0 + 70, -60, ZK + 130), (k0 + 70, -60, 1470), (lx, -380, 1470), (lx, -1330, 1470),
                  (lx, -1330, 1380)], r(16))
    add("uncoupling_lever", RED, lever)
    add("lever_brackets", DARK, [box(XE - 10, lx + 25, y - 25, y + 25, 1445, 1495) for y in (-800.0, -1250.0)])

    # brake-pipe hose with angle cock and glad hand
    hose = tube([(XE - 10, -230, 1030), (XE + 110, -230, 1030), (XE + 160, -235, 920), (XE + 175, -250, 760)],
                r(28))
    add("brake_hose", BLACK, hose)
    add("angle_cock", RED, box(XE + 60, XE + 100, -270, -190, 1040, 1090 + t(10)))
    add("glad_hand", DARK, box(XE + 135, XE + 215, -300, -200, 700, 780))

    # stirrup steps and grab irons at the corners
    st = t(20)
    for s in (1, -1):
        y0 = s * 1390
        add("stirrup_step", GALV, box(XE - 120, XE - 120 + st, *ys(1330, 1440, s), 480, ZEB + 20),
            box(XE - 330, XE - 100, *ys(1320, 1450, s), 480, 510),
            box(XE - 330, XE - 330 + st, *ys(1330, 1440, s), 480, ZEB + 20))
        add("grab_iron", YELLOW, tube([(XE - 5, y0, 1080), (XE + 90, y0, 1080), (XE + 90, y0, 1480),
                                       (XE - 5, y0, 1480)], r(18)))

    # rail gear: pivot brackets, swing arms, axle beam, lift cylinder, flanged steel wheels
    piv = (1950.0, 960.0)
    gear, wheels, hubs = [], [], []
    for s in (1, -1):
        gear.append(box(piv[0] - 70, piv[0] + 70, *ys(540, 680, s), piv[1] - 60, ZEB + 15))
        gear.append(bar((piv[0], s * 610, piv[1]), (XG, s * 610, ZG), 130, 60, up=(0, 1, 0)))
        gear.append(cyl(75, (piv[0], s * 530, piv[1]), (piv[0], s * 690, piv[1])))
        hubs.append(cyl(100, (XG, s * 600, ZG), (XG, s * 712, ZG)))
        hubs.append(cyl(70, (XG, s * 820, ZG), (XG, s * 860, ZG)))
        wheels.append(cyl(RG, (XG, s * 710, ZG), (XG, s * 834, ZG)))
        wheels.append(cyl(RF, (XG, s * (716 - t(26)), ZG), (XG, s * 716, ZG)))
    gear.append(box(XG - 75, XG + 75, -650, 650, ZG - 60, ZG + 70))
    add("rail_gear_frame", BLACK, gear)
    add("rail_wheel_hubs", DARK, hubs)
    add("rail_wheels", STEEL, wheels)
    for s in (1, -1):
        a, b = (XG + 110, s * 380, ZEB + 10), (XG + 40, s * 380, ZG + 70)
        barrel, rod = jack(a, b, 55, 30, 0.55, (0, 1, 0))
        add("rail_gear_cylinder", BLACK, barrel)
        add("rail_gear_rod", CHROME, rod)
    add("rail_gear_hoses", BLACK, [tube([(XG + 40, s * 300, ZEB + 5), (XG + 60, s * 300, 860),
                                         (XG + 100, s * 330, 800)], r(14)) for s in (1, -1)])
    return out


def build(m):
    t, r = m.t, m.r

    # =============================================================== track
    xs = [-3135.0 + 570.0 * k for k in range(12)]
    m.add("ties", TIMBER_DARK, [box(x - 115, x + 115, -1295, 1295, -2, Z_TIE) for x in xs])
    m.add("tie_plates", MILL, [box(x - 100, x + 100, *ys(RC - 180, RC + 180, s), Z_TIE - 2, Z_PLATE)
                               for x in xs for s in (1, -1)])
    w = max(9.0, t(17.5) / 2)
    bt = t(14)
    prof = [(-76, 0), (76, 0), (76, bt), (w, max(34, bt + 14)), (w, 140), (37, 150), (37, 186),
            (-37, 186), (-37, 150), (-w, 140), (-w, max(34, bt + 14)), (-76, bt)]
    rails = []
    for s in (1, -1):
        pts = [(s * RC + y, Z_PLATE - 2 + z) for y, z in prof]
        rails.append(prism(pts, "x", -TRACK_X, TRACK_X))
    m.add("rails", STEEL, rails)
    spikes = []
    for x in xs:
        for s in (1, -1):
            for dy in (-95.0, 95.0):
                spikes.append(box(x - 40, x - 10, *ys(RC + dy - 15, RC + dy + 15, s), Z_PLATE - 4, Z_PLATE + t(22)))
                spikes.append(box(x + 10, x + 40, *ys(RC + dy - 15, RC + dy + 15, s), Z_PLATE - 4, Z_PLATE + t(22)))
    m.add("spikes", DARK, spikes)

    # =============================================================== road wheels
    tyre = tyre_at_origin()
    rim = [cut(cyl(312, (0, -195, 0), (0, 170, 0)), cyl(255, (0, 120, 0), (0, 175, 0)))]
    hub = [cyl(165, (0, 100, 0), (0, 195, 0)), cone(120, 70, (0, 190, 0), (0, 240, 0))]
    nuts = []
    for k in range(10):
        a = 2 * math.pi * k / 10
        nuts.append(rod((205 * math.cos(a), 115, 205 * math.sin(a)), (205 * math.cos(a), 148, 205 * math.sin(a)),
                        r(24), 6))

    def put(shapes, x, s):
        out = [sh.translate(cq.Vector(x, RC, ZA)) for sh in shapes]
        return out if s > 0 else [sh.mirror("XZ") for sh in out]

    corners = [(x, s) for x in (XW, -XW) for s in (1, -1)]
    m.add("tyres", RUBBER, [put([tyre], x, s) for x, s in corners])
    m.add("rims", YELLOW, [put(rim, x, s) for x, s in corners])
    m.add("hubs", BLACK, [put(hub, x, s) for x, s in corners])
    m.add("wheel_nuts", STEEL, [put(nuts, x, s) for x, s in corners])
    m.add("axles", DARK, [cyl(125, (x, -620, ZA), (x, 620, ZA)) for x in (XW, -XW)],
          [cyl(185, (x, s * 470, ZA), (x, s * 560, ZA)) for x in (XW, -XW) for s in (1, -1)])

    # =============================================================== chassis, deck, under-deck
    m.add("chassis", DARK, box(-2300, 2300, -520, 520, 760, ZD0 + 10))
    m.add("deck", YELLOW, box(-XE, XE, -YB, YB, ZD0, ZD),
          [box(-XE, XE, *ys(YB - 60, YB, s), 1560, ZD0 + 5) for s in (1, -1)])      # deck edge skirts
    m.add("walkway_treads", GALV, [box(-XE + 30, XE - 30, *ys(960, YB - 30, s), ZD - 3, ZD + t(8)) for s in (1, -1)])

    # left: fuel tank on straps
    m.add("fuel_tank", YELLOW, rounded_box(-520, 130, 1000, 1420, 860, 1600, 40))
    m.add("fuel_tank_straps", BLACK, [box(x, x + 50, 990, 1430, 850, ZD0 + 5) for x in (-420.0, -20.0)])
    m.add("fuel_filler", BLACK, cyl(60, (-300, 1410, 1480), (-300, 1470, 1480)),
          cyl(75, (-300, 1465, 1480), (-300, 1490, 1480)))
    m.add("fuel_gauge", GLASS, box(30, 70, 1415, 1428, 1050, 1450))

    # right: two air reservoirs on a back plate, battery box below
    m.add("air_tank_backplate", DARK, box(-540, 150, *ys(1000, 1075, -1), 820, ZD0 + 5))
    tanks, bands = [], []
    for zc in (1060.0, 1420.0):
        tanks.append(tank(-530.0, 130.0, -1235.0, zc, 170.0))
        bands += [cyl(178, (x, -1235.0, zc), (x + 45, -1235.0, zc)) for x in (-330.0, -110.0)]
    m.add("air_tanks", GALV, tanks)
    m.add("air_tank_bands", BLACK, bands)
    m.add("air_drain_valves", STEEL, [cyl(r(18), (-200, -1235, zc - 160), (-200, -1235, zc - 220))
                                      for zc in (1060.0, 1420.0)])
    m.add("air_pipes", BLACK, tube([(-30, -1235, 1420 + 150), (100, -1100, 1600), (100, -1040, 1600)], r(16)))

    # access ladders both sides, under the cab doors
    sw = t(25)
    m.add("ladder_stringers", BLACK, [box(x, x + sw, *ys(1360, 1450, s), 380, ZD0 + 10)
                                      for x in (185.0, 545.0 - sw) for s in (1, -1)])
    m.add("ladder_treads", GALV, [box(185, 545, *ys(1290, 1455, s), z, z + t(30))
                                  for z in (420.0, 760.0, 1100.0, 1420.0) for s in (1, -1)])

    # =============================================================== ends (front as built, rear turned)
    for name, (fin, shapes) in end_parts(m).items():
        m.add(name, fin, shapes, [rot(sh, 180) for sh in shapes])

    # =============================================================== front hood (hydraulics, compressor)
    hz = 2130.0
    sec = [(-900, ZD - 10), (900, ZD - 10), (900, hz - 70), (830, hz), (-830, hz), (-900, hz - 70)]
    m.add("front_hood", YELLOW, prism(sec, "x", CX + 15, XE - 30))
    m.add("cooler_grille", BLACK, box(1650, 2200, -620, 620, hz - 5, hz + t(14)))
    m.add("cooler_slats", DARK, [box(x, x + t(25), -600, 600, hz, hz + 32) for x in np.arange(1680, 2180, 70)])
    seams = []
    if not m.print_mode:
        for s in (1, -1):
            seams += [box(x - 5, x + 5, *ys(898, 905, s), ZD + 60, hz - 90) for x in (1100.0, 1650.0, 2200.0)]
    m.add("hood_door_seams", BLACK, seams)
    m.add("hood_handles", BLACK, [box(x - 60, x + 60, *ys(895, 925, s), 1950, 1985)
                                  for x in (1375.0, 1925.0) for s in (1, -1)])
    m.add("hydraulic_filler", BLACK, cyl(70, (1250, 450, hz - 10), (1250, 450, hz + 60)))
    m.add("front_hood_grille", BLACK, box(XE - 45, XE - 20, -520, 520, ZD + 110, hz - 110))
    m.add("front_hood_slats", YELLOW, [box(XE - 30, XE - 30 + t(20), -500, 500, z, z + t(25))
                                       for z in np.arange(ZD + 140, hz - 130, 55)])

    # =============================================================== rear hood (engine)
    rz = 2350.0
    sec = [(-900, ZD - 10), (900, ZD - 10), (900, rz - 100), (800, rz), (-800, rz), (-900, rz - 100)]
    m.add("engine_hood", YELLOW, prism(sec, "x", -XE + 30, -CX - 15))
    m.add("radiator_grille", BLACK, box(-XE + 15, -XE + 40, -720, 720, ZD + 50, rz - 90))
    m.add("radiator_slats", DARK, [box(-XE + 5, -XE + 20, -700, 700, z, z + t(25)) for z in np.arange(ZD + 80, rz - 110, 60)])
    louv = []
    for s in (1, -1):
        louv += [box(-2200, -1850, *ys(895, 900 + t(12), s), z, z + t(25)) for z in np.arange(1880, 2200, 60)]
    m.add("engine_louvres", BLACK, louv)
    m.add("exhaust_stack", BLACK, cyl(r(70), (-1150, -650, rz - 20), (-1150, -650, 2980)),
          cyl(95, (-1150, -650, rz - 10), (-1150, -650, rz + 60)))
    m.add("exhaust_tip", STEEL, cyl(78, (-1150, -650, 2960), (-1150, -650, 3030)))
    m.add("precleaner", BLACK, cyl(r(60), (-1150, 650, rz - 20), (-1150, 650, 2600)),
          cyl(130, (-1150, 650, 2580), (-1150, 650, 2760)))
    m.add("precleaner_cap", DARK, cone(140, 60, (-1150, 650, 2755), (-1150, 650, 2830)))
    m.add("engine_hood_handles", BLACK, [box(x - 60, x + 60, *ys(895, 925, s), 2100, 2135)
                                         for x in (-1600.0, -1250.0) for s in (1, -1)])
    nums = []
    for s in (1, -1):
        nums.append(text("RM 07", 170, t(6), (-1420, s * 898, 1900), (-s, 0, 0), (0, s, 0)))
    m.add("fleet_number", BLACK, nums)

    # =============================================================== cab
    m.add("cab_lower", YELLOW, box(-CX, CX, -CY, CY, ZD - 10, ZB))
    pp = 90.0
    frame = []
    for sx in (1, -1):
        for sy in (1, -1):
            frame.append(box(*sorted((sx * CX, sx * (CX - pp))), *ys(CY - pp, CY, sy), ZB - 20, ZR))
    for sy in (1, -1):
        frame += [box(x, x + 60, *ys(CY - 70, CY + 4, sy), ZB - 20, ZR) for x in (120.0, 760.0)]
        frame.append(box(-CX, CX, *ys(CY - 40, CY + 6, sy), ZB - 25, ZB + 15))         # belt-line trim
    for sx in (1, -1):
        frame.append(box(*sorted((sx * (CX - 40), sx * (CX + 6))), -CY, CY, ZB - 25, ZB + 15))
    m.add("cab_frame", BLACK, frame)
    g = t(12)
    glass = []
    for sx in (1, -1):
        xg = sx * (CX - 35)
        glass.append(box(xg - g / 2, xg + g / 2, -(CY - 45), CY - 45, ZB - 5, ZR + 5))
    for sy in (1, -1):
        yg = sy * (CY - 35)
        glass.append(box(-(CX - 45), CX - 45, yg - g / 2, yg + g / 2, ZB - 5, ZR + 5))
    m.add("cab_glass", GLASS, glass)
    m.add("roof_rim", BLACK, box(-CX - 45, CX + 45, -CY - 45, CY + 45, ZR - 15, ZR + 25))
    m.add("cab_roof", YELLOW, rounded_box(-CX - 60, CX + 60, -CY - 60, CY + 60, ZR + 15, ZR + 100, 30))
    if m.print_mode:   # solid core so the glazed cab is not a sealed hollow
        m.add("cab_core", DARK, box(-CX + 50, CX - 50, -CY + 50, CY - 50, ZD - 5, ZR + 20))
    # interior: side-facing seat and consoles
    m.add("seat", BLACK, box(-300, 200, -500, -50, ZD, 2200), box(-300, 200, -560, -420, 2150, 2750),
          [box(x, x + 60, -480, -100, 2150, 2300) for x in (-320.0, 180.0)])
    m.add("consoles", DARK, box(-650, -380, -550, 300, ZD, 2280), box(280, 550, -550, 300, ZD, 2280),
          box(-300, 200, 350, 700, ZD, 2250))
    m.add("control_levers", BLACK, [cyl(r(18), (x, y, 2270), (x, y, 2440)) for x in (-560.0, 380.0) for y in (-200.0, 100.0)])

    # doors: lower panel seams, handles, hinges
    dseams = []
    if not m.print_mode:
        for sy in (1, -1):
            dseams += [box(x, x + 12, *ys(CY - 4, CY + 4, sy), ZD + 40, ZB - 30) for x in (150.0, 760.0)]
    m.add("door_seams", BLACK, dseams)
    m.add("door_handles", CHROME, [box(200, 300, *ys(CY - 5, CY + 30, sy), 2050, 2095) for sy in (1, -1)])
    m.add("door_rails", DARK, [box(-50, 860, *ys(CY - 5, CY + 35, sy), z, z + 40) for sy in (1, -1) for z in (ZD + 20, ZR - 50)])
    # grab handles beside the doors
    m.add("cab_grab_handles", BLACK, [tube([(80, sy * (CY - 10), 2000), (80, sy * (CY + 70), 2000),
                                            (80, sy * (CY + 70), 2850), (80, sy * (CY - 10), 2850)], r(16))
                                      for sy in (1, -1)])
    # wipers on both end screens
    wt = t(10)
    wipers = []
    for sx in (1, -1):
        xo = sx * (CX - 35 + g / 2 + wt / 2 - 3)
        wipers.append(bar((xo, 300, ZB + 60), (xo, -100, ZB + 700), t(26), wt, up=(sx, 0, 0)))
        wipers.append(cyl(r(28), (xo - sx * 20, 300, ZB + 60), (xo + sx * 25, 300, ZB + 60)))
    m.add("wipers", BLACK, wipers)
    # mirrors on arms off the corner posts
    arms, heads, mglass = [], [], []
    for sx in (1, -1):
        for sy in (1, -1):
            x0 = sx * (CX - 45)
            arms += tube([(x0, sy * (CY - 30), 2650), (x0 + sx * 120, sy * (CY + 120), 2700),
                          (x0 + sx * 120, sy * 1250, 2700)], r(18) if not m.print_mode else 24)
            heads.append(box(*sorted((x0 + sx * 90, x0 + sx * 150)), *ys(1180, 1330, sy), 2520, 2780))
            mglass.append(box(*sorted((x0 + sx * 150 - sx * 4, x0 + sx * 150 + sx * t(6))),
                              *ys(1192, 1318, sy), 2532, 2768))
    m.add("mirror_arms", BLACK, arms)
    m.add("mirror_heads", BLACK, heads)
    m.add("mirror_glass", CHROME, mglass)
    # roof: work lights at both ends, two beacons on diagonal corners, horn
    lamps, lenses = [], []
    for sx in (1, -1):
        for sy in (1, -1):
            xa = sorted((sx * (CX - 10), sx * (CX + 80)))
            lamps.append(box(*xa, *ys(450, 650, sy), ZR + 80, ZR + 170))
            xl = sorted((sx * (CX + 76), sx * (CX + 80 + t(10))))
            lenses.append(box(*xl, *ys(465, 635, sy), ZR + 92, ZR + 158))
    m.add("roof_lamp_housings", BLACK, lamps)
    m.add("roof_work_lights", LED, lenses)
    spots = ((CX - 220, -(CY - 220)), (-(CX - 220), CY - 220))
    m.add("beacon_bases", BLACK, [cyl(95, (bx, by, ZR + 90), (bx, by, ZR + 125)) for bx, by in spots])
    m.add("beacons", AMBER, [cyl(72, (bx, by, ZR + 120), (bx, by, ZR + 205)) for bx, by in spots],
          [cone(72, 30, (bx, by, ZR + 200), (bx, by, ZR + 245)) for bx, by in spots])
    m.add("horn", BLACK, cyl(45, (0, 0, ZR + 90), (0, 0, ZR + 130)), cone(45, 70, (0, 0, ZR + 125), (0, 0, ZR + 180)))

    # =============================================================== deck handrails
    hr = r(22)
    zt, zm = ZD + 1000, ZD + 500
    rails_ = []
    for s in (1, -1):
        y = s * 1410
        yi = s * 990                      # end posts on the walkway, beside the hoods
        rails_ += tube([(-2300, yi, ZD - 15), (-2300, yi, zt), (-2300, y, zt), (160, y, zt), (160, y, ZD - 15)], hr)
        rails_ += tube([(580, y, ZD - 15), (580, y, zt), (2300, y, zt), (2300, yi, zt), (2300, yi, ZD - 15)], hr)
        rails_ += tube([(-2300, yi, zm), (-2300, y, zm), (160, y, zm)], hr)
        rails_ += tube([(580, y, zm), (2300, y, zm), (2300, yi, zm)], hr)
        rails_ += [rod((x, y, ZD - 15), (x, y, zt), hr) for x in (-2300.0, -1100.0, 1450.0, 2300.0)]
    m.add("handrails", YELLOW, rails_)
