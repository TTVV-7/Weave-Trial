"""Dust-suppression fog cannon (mist cannon) on a single-axle trailer, set up for work: barrel
elevated 30 deg and slewed to blow forward over the drawbar, four corner stands wound down onto their pads,
drawbar resting on the jockey wheel.

A generic, brand-neutral unit with the typical proportions of the ~60 m-throw trailer class
(the self-powered mist cannons used on stockpiles, ship-loading berths and demolition sites):

* trailer: a 2.6 m x 1.2 m channel frame with a galvanised deck plate, one braked axle on leaf
  springs, 195/70R15C-size tyres (~660 mm OD) on galvanised wheels, round fenders, ~1.97 m wide
  over the fenders; an A-frame drawbar with an overrun coupling, 50 mm ball coupler, handbrake,
  breakaway cable, safety chains, 13-pin lead and a side-mounted swivel jockey wheel; four
  drop-leg corner stands (screw jacks) on outrigger arms with steel foot plates; ~3.7 m long
  overall (coupler to the barrel intake);
* power pack: a ~0.8 x 1.4 x 1.25 m soundproofed (50-70 kVA class) generator / booster-pump enclosure on the front
  deck with louvred air intakes both sides, a control door with screen and e-stop on the front,
  exhaust stack, lifting eye, beacon and two LED work floods on the roof, fuel filler and a
  camlock water inlet on the side; a hose from the pump to a rotary union in the slewing base;
* cannon: the usual ~1.2 m (1,200 mm OD) fan barrel, 1.8 m long, with a guarded intake grille
  and the axial fan behind it, flow-straightener vanes in the outlet, and a ring of 24 fine
  nozzles on a feed manifold round the outlet lip, fed by a steel pipe along the barrel; carried
  on trunnions in a tilting yoke on a slewing ring and pedestal (slewed 180 deg here so the outlet
  faces forward over the power pack and drawbar), elevated by a hydraulic ram;
  trunnions ~2.3 m up, top of the nozzle ring ~3.3 m with the barrel at 30 deg;
* lighting: combination tail lamps, side markers, reflectors and a rear number plate.

Millimetres, X forward (drawbar at +X), Y left, Z up, ground at Z = 0.
"""

from __future__ import annotations

import math

import cadquery as cq
import numpy as np

from cadkit import Finish, arc_pts, band, bar, box, cone, cut, cyl, mirror_y, mv, pipe, prism, rgb, rot, sphere, text
from finishes import AMBER, BLACK, CHROME, DARK, GALV, LED, ORANGE, RED, RUBBER, STEEL, WHITE

ASSET = dict(key="fog_cannon", stem="Dust_Fog_Cannon", title="Dust Suppression Fog Cannon (trailer)",
             az=35, el=18, size="1200x900")

CABINET = Finish(rgb("#9aa0a6"), metal=0.6, rough=0.45)       # stainless control door
TAIL = Finish(rgb("#d81b1b"), rough=0.25, glow=(0.35, 0.0, 0.0))

# ---- trailer
XR, XF = -1550.0, 1020.0          # frame rear / front
RY0, RY1 = 520.0, 600.0           # frame rail inner / outer y
ZF0, ZF1 = 430.0, 540.0           # frame rail bottom / top
ZD = ZF1 + 10                     # deck top
XA = -300.0                       # axle
RT = 330.0                        # tyre radius
ZC = RT * (1 - 0.015)             # wheel centre: tyres sink 1.5 % for a flat print contact patch
XC = 1720.0                       # drawbar nose

# ---- power pack
BX0, BX1, BY, BZ1 = 150.0, 960.0, 700.0, 1800.0

# ---- cannon
XT, ZT = -600.0, 2300.0           # trunnion axis
TH = 30.0                         # elevation
SLEW = 180.0                      # slew: the outlet points forward (+X), over the drawbar
CT, ST = math.cos(math.radians(TH)), math.sin(math.radians(TH))
CS, SS = math.cos(math.radians(SLEW)), math.sin(math.radians(SLEW))
RB = 600.0                        # barrel outer radius
HL = 900.0                        # barrel half length


def bp(x, y, z):
    """Barrel coordinates (x along the axis, +x to the intake, -x to the nozzles) to the model's."""
    u = x * CT + z * ST
    return (XT + u * CS - y * SS, u * SS + y * CS, ZT - x * ST + z * CT)


def sp(x, y, z):
    """A point on the slewing (upper) structure, given unslewed, into place."""
    u = x - XT
    return (XT + u * CS - y * SS, u * SS + y * CS, z)


def SL(*shapes):
    """Upper-structure shapes (yoke, ram, union...) given unslewed, rotated about the slew axis."""
    out = []
    for s in shapes:
        if isinstance(s, (list, tuple)):
            out += SL(*s)
        elif s is not None:
            out.append(rot(s, SLEW, (0, 0, 1), (XT, 0, 0)))
    return out


def BW(*shapes):
    """Barrel-frame shapes into place."""
    out = []
    for s in shapes:
        if isinstance(s, (list, tuple)):
            out += BW(*s)
        elif s is not None:
            out.append(mv(rot(rot(s, TH, (0, 1, 0)), SLEW, (0, 0, 1)), XT, 0, ZT))
    return out


def cx(r, x0, x1, y=0.0, z=0.0):
    return cyl(r, (x0, y, z), (x1, y, z))


def ringx(r0, r1, x0, x1):
    return cut(cx(r1, x0, x1), cx(r0, x0 - 1, x1 + 1))


def eye_plate(x, y, z0, r, hole, t, along):
    """A lifting-eye plate standing on z0: round top of radius r with a hole, in the plane of
    `along` ('x' or 'y') and Z, t thick."""
    zc = z0 + r + 25
    if along == "x":
        pl = cut(prism(arc_pts(x, zc, r, 0, 180, 12) + [(x - r, z0), (x + r, z0)], "y", y - t / 2, y + t / 2),
                 cyl(hole, (x, y - t, zc), (x, y + t, zc)))
    else:
        pl = cut(prism(arc_pts(y, zc, r, 0, 180, 12) + [(y - r, z0), (y + r, z0)], "x", x - t / 2, x + t / 2),
                 cyl(hole, (x - t, y, zc), (x + t, y, zc)))
    return pl


def revolve_y(profile, xc, zc):
    """Solid of revolution about the line through (xc, ., zc) parallel to Y; profile in (r, y)."""
    s = cq.Workplane("XY").polyline(profile).close().revolve(360, (0, 0, 0), (0, 1, 0)).val()
    return mv(s, xc, 0, zc)


# =========================================================================== build

def build(m):
    trailer(m)
    wheels(m)
    outriggers(m)
    drawbar(m)
    power_pack(m)
    slew_base(m)
    barrel(m)
    plumbing(m)
    hose_reel(m)
    lights(m)


# --------------------------------------------------------------------------- frame, axle

def trailer(m):
    rails = [box(XR, XF, s * RY0, s * RY1, ZF0, ZF1) for s in (1, -1)]
    cross = [box(XR - 5, XR + 75, -RY1 + 5, RY1 - 5, ZF0 + 8, ZF1 - 3),
             box(XF - 75, XF + 5, -RY1 + 5, RY1 - 5, ZF0 + 8, ZF1 - 3)]
    cross += [box(x - 35, x + 35, -RY0 - 4, RY0 + 4, ZF0 + 15, ZF1 - 5) for x in (-1050, XT, XA + 250, 560)]
    m.add("frame", ORANGE, rails, cross)
    m.add("deck", GALV, box(XR + 40, XF - 40, -RY1 - 8, RY1 + 8, ZD - m.t(10), ZD))

    # axle, leaf springs, hangers, U-bolts
    m.add("axle", BLACK, cyl(40, (XA, -790, ZC), (XA, 790, ZC)))
    hz = max(18.0, m.t(36) / 2)
    for s in (1, -1):
        yc = s * 562
        path = [(XA + d, 381 + 46 * (d / 330) ** 2) for d in np.linspace(-330, 330, 15)]
        m.add("leaf_spring", DARK, prism(band(path, hz), "y", yc - 26, yc + 26),
              [cyl(24, (XA + d, yc - 30, 427), (XA + d, yc + 30, 427)) for d in (-330, 330)])
        m.add("spring_hangers", ORANGE, [box(XA + d - 32, XA + d + 32, yc - 34, yc + 34, 400, ZF0 + 5)
                                         for d in (-330, 330)])
        ub = m.t(14)
        m.add("u_bolts", STEEL, [box(XA + dx - ub / 2, XA + dx + ub / 2, yc - 30, yc + 30, ZC - 50, 405)
                                 for dx in (-52, 52)],
              box(XA - 65, XA + 65, yc - 38, yc + 38, ZC - 62, ZC - 38))
    m.add("brake_drums", DARK, [cyl(110, (XA, s * 700, ZC), (XA, s * 785, ZC)) for s in (1, -1)])

    # side step on the left rail
    m.add("side_step", DARK, box(-1180, -940, 590, 780, 330, 352),
          [box(x - 20, x + 20, 560, 610, 340, ZF0 + 20) for x in (-1150, -970)],
          [box(x - 20, x + 20, 590, 620, 340, 380) for x in (-1150, -970)])


def wheels(m):
    tyre = [(205, 778), (250, 770), (300, 770), (318, 777), (327, 792), (RT, 815), (RT, 915),
            (327, 938), (318, 953), (300, 960), (250, 960), (205, 952)]
    rim = [(0, 780), (213, 780), (213, 792), (209, 798), (209, 938), (213, 944), (213, 954),
           (191, 954), (181, 942), (123, 926), (0, 926)]
    for s, side in ((1, "L"), (-1, "R")):
        t = revolve_y(tyre, XA, ZC)
        r = revolve_y(rim, XA, ZC)
        lugs = [cyl(m.r(13), (XA + 75 * math.cos(a), 920, ZC + 75 * math.sin(a)),
                    (XA + 75 * math.cos(a), 946, ZC + 75 * math.sin(a)))
                for a in np.linspace(0, 2 * math.pi, 5, endpoint=False) + 0.3]
        cap = [cyl(50, (XA, 920, ZC), (XA, 948, ZC)), cone(50, 28, (XA, 948, ZC), (XA, 966, ZC))]
        if s < 0:
            t, r = mirror_y(t), mirror_y(r)
            lugs, cap = [mirror_y(x) for x in lugs], [mirror_y(x) for x in cap]
        m.add(f"tyre_{side}", RUBBER, t)
        m.add(f"rim_{side}", GALV, r, cap)
        m.add(f"lug_nuts_{side}", STEEL, lugs)

    # round fenders with a rolled outer edge, on brackets from the rails
    ri, ft = 375.0, m.t(6)
    for s in (1, -1):
        y0, y1 = sorted((s * 735, s * 985))
        arch = arc_pts(XA, ZC, ri + ft, 6, 174, 30) + arc_pts(XA, ZC, ri, 174, 6, 30)
        lip = arc_pts(XA, ZC, ri + ft + 14, 8, 172, 30) + arc_pts(XA, ZC, ri, 172, 8, 30)
        yl0, yl1 = sorted((s * 965, s * 985))
        m.add("fender", ORANGE, prism(arch, "y", y0, y1), prism(lip, "y", yl0, yl1),
              [box(XA + d - 30, XA + d + 30, s * 590, s * 745, ZF0, ZF1 - 8) for d in (-345, 345)])


# --------------------------------------------------------------------------- corner stands

def outriggers(m):
    YJ = 900.0
    arms, jacks, inner, pads, cranks = [], [], [], [], []
    for x in (-1420.0, 900.0):
        arms.append(box(x - 40, x + 40, -YJ - 40, YJ + 40, ZF0 + 12, ZF0 + 92))
        for s in (1, -1):
            y = s * YJ
            arms.append(box(x - 52, x + 52, s * (RY1 - 4), s * (RY1 + 50), ZF0 - 6, ZF1 + 6))     # receiver
            arms.append(cyl(m.r(11), (x, s * (RY1 + 25), ZF0 - 30), (x, s * (RY1 + 25), ZF1 + 50)))
            jacks += [box(x - 46, x + 46, y - 46, y + 46, 300, 940),
                      box(x - 58, x + 58, y - 58, y + 58, ZF0, ZF0 + 110),
                      box(x - 52, x + 52, y - 52, y + 52, 935, 962)]
            inner += [box(x - 35, x + 35, y - 35, y + 35, 60, 320), cyl(48, (x, y, 22), (x, y, 70))]
            pads.append(box(x - 140, x + 140, y - 140, y + 140, -2, 26))
            cranks += [cyl(m.r(16), (x, y, 955), (x, y, 1020)),
                       pipe([(x, y, 1010), (x, y, 1030), (x + 160, y, 1030), (x + 160, y, 1100)], m.r(12)),
                       cyl(m.r(18), (x + 160, y, 1070), (x + 160, y, 1130))]
    m.add("outrigger_arms", ORANGE, arms)
    m.add("jack_tubes", ORANGE, jacks)
    m.add("jack_legs", GALV, inner)
    m.add("jack_cranks", BLACK, cranks)
    m.add("jack_feet", STEEL, pads)


# --------------------------------------------------------------------------- drawbar

def drawbar(m):
    xa = XF - 70
    m.add("a_frame", ORANGE, [bar((xa, s * 560, 485), (XC, s * 50, 485), 75, 100) for s in (1, -1)],
          box(XC - 160, XC + 60, -52, 52, 435, 535), box(1300, 1380, -330, 330, 445, 525),
          box(xa - 10, xa + 40, -RY1 + 10, RY1 - 10, ZF0 + 4, ZF1 - 6))
    # overrun coupling with a ball coupler head, handbrake and breakaway cable
    m.add("overrun_coupling", GALV, box(XC + 20, XC + 200, -58, 58, 450, 548),
          sphere(56, (XC + 205, 0, 492)), cyl(56, (XC + 205, 0, 440), (XC + 205, 0, 492)),
          box(XC + 140, XC + 215, -50, 50, 440, 500))
    m.add("coupler_handle", BLACK, bar((XC + 120, 0, 556), (XC + 235, 0, 570), 46, m.t(22)),
          cyl(m.r(14), (XC + 125, -45, 552), (XC + 125, 45, 552)))
    m.add("bellows", RUBBER, cyl(48, (XC - 20, 0, 499), (XC + 30, 0, 499)))
    m.add("handbrake", BLACK, box(XC - 60, XC + 40, 55, 85, 470, 560),
          bar((XC - 10, 70, 540), (XC - 230, 75, 800), 34, m.t(26), up=(0, 1, 0)),
          cyl(m.r(22), (XC - 230, 55, 800), (XC - 230, 110, 800)))
    m.add("breakaway_cable", STEEL, pipe([(XC - 120, 78, 760), (XC - 80, 140, 620), (XC + 60, 150, 520),
                                          (XC + 150, 70, 470)], m.r(6)))
    for s in (1, -1):
        m.add("safety_chain", STEEL, pipe([(XC - 120, s * 50, 450), (XC - 60, s * 85, 340), (XC + 40, s * 90, 300),
                                           (XC + 120, s * 70, 350), (XC + 160, s * 50, 452)], m.r(9)))
    lead = [(XF - 40, 548, ZF1 + 4), (XC - 140, 60, ZF1 + 4), (XC - 60, 70, 548), (XC + 20, 120, 520),
            (XC + 40, 150, 440)]
    m.add("wiring_lead", BLACK, pipe(lead, m.r(9)), box(XC + 15, XC + 65, 125, 175, 390, 445))

    # side-wind swivel jockey wheel on the -Y bar
    xj, yj = 1560.0, -330.0
    y_bar = -(560 - (xj - xa) / (XC - xa) * (560 - 50))
    m.add("jack_clamp", ORANGE, box(xj - 50, xj + 50, yj + 30, y_bar + 20, 440, 520))
    m.add("jockey_jack", BLACK, cyl(38, (xj, yj, 300), (xj, yj, 900)), cyl(46, (xj, yj, 860), (xj, yj, 920)),
          box(xj - 55, xj + 55, yj - 50, yj + 50, 420, 540))
    m.add("jockey_crank", BLACK, cyl(m.r(12), (xj, yj, 880), (xj + 120, yj, 880)),
          bar((xj + 110, yj, 880), (xj + 110, yj - 20, 1040), 26, m.t(14), up=(1, 0, 0)),
          cyl(m.r(16), (xj + 110, yj - 20, 1030), (xj + 200, yj - 20, 1030)))
    zw = 100 * (1 - 0.015)
    m.add("jockey_leg", GALV, cyl(30, (xj, yj, 190), (xj, yj, 320)),
          box(xj - 80, xj + 30, yj - 45, yj + 45, 190, 205),
          [box(xj - 80, xj - 55, yj + s * 38 - m.t(6) / 2, yj + s * 38 + m.t(6) / 2, zw - 10, 200) for s in (1, -1)],
          cyl(m.r(12), (xj - 68, yj - 46, zw), (xj - 68, yj + 46, zw)))
    m.add("jockey_wheel", RUBBER, cyl(100, (xj - 68, yj - 30, zw), (xj - 68, yj + 30, zw)))
    m.add("jockey_hub", GALV, cyl(45, (xj - 68, yj - 33, zw), (xj - 68, yj + 33, zw)))


# --------------------------------------------------------------------------- generator / pump box

def power_pack(m):
    m.add("enclosure", WHITE, box(BX0, BX1, -BY, BY, ZD + 20, BZ1),
          box(BX0 - 15, BX1 + 15, -BY - 15, BY + 15, BZ1 - 6, BZ1 + 32))
    m.add("enclosure_skid", DARK, box(BX0 - 12, BX1 + 12, -BY - 12, BY + 12, ZD - 4, ZD + 90),
          [box(x - 60, x + 60, -BY - 16, BY + 16, ZD + 20, ZD + 70) for x in (300, 810)])

    # louvred air intakes / outlets, both sides
    panels, slats = [], []
    for s in (1, -1):
        for xp0, xp1 in ((230.0, 520.0), (590.0, 880.0)):
            panels.append(box(xp0, xp1, s * (BY - 20), s * (BY + 6), 740, 1610))
            for z in range(770, 1570, 65):
                tri = [(s * (BY + 2), z), (s * (BY + 30), z), (s * (BY + 2), z + 44)]
                slats.append(prism(tri, "x", xp0 + 14, xp1 - 14))
    # exhaust outlet louvre on the back face
    panels.append(box(BX0 - 6, BX0 + 20, -520, -120, 1180, 1460))
    for z in range(1205, 1440, 65):
        slats.append(prism([(BX0 - 2, z), (BX0 - 30, z), (BX0 - 2, z + 44)], "y", -505, -135))
    m.add("louvre_panels", DARK, panels)
    m.add("louvres", BLACK, slats)

    # side doors: seams (display only), hinges and handles
    if not m.print_mode:
        seams = []
        for s in (1, -1):
            for x in (BX0 + 40, 555, BX1 - 40):
                seams.append(box(x - 4, x + 4, s * (BY - 2), s * (BY + 3), 700, 1690))
            seams += [box(BX0 + 40, BX1 - 40, s * (BY - 2), s * (BY + 3), z - 4, z + 4) for z in (700, 1690)]
        m.add("door_seams", DARK, seams)
        m.add("fleet_number", BLACK, text("FC 07", 110, 6, (380, BY + 4, BZ1 - 85), (-1, 0, 0), (0, 1, 0)),
              text("FC 07", 110, 6, (730, -BY - 4, BZ1 - 85), (1, 0, 0), (0, -1, 0)))
    hw = []
    for s in (1, -1):
        for x in (BX0 + 60, BX1 - 60):
            hw += [box(x - 14, x + 14, s * (BY - 4), s * (BY + 16), z, z + 90) for z in (760, 1520)]
        hw += [box(x - 20, x + 20, s * (BY - 4), s * (BY + 22), 1080, 1180) for x in (520, 590)]
        zh = BZ1 - 120
        hw.append(pipe([(BX0 + 100, s * (BY - 5), zh), (BX0 + 100, s * (BY + 55), zh),
                        (BX1 - 100, s * (BY + 55), zh), (BX1 - 100, s * (BY - 5), zh)], m.r(14)))
    m.add("door_hardware", STEEL, hw)

    # control door on the front face: screen, buttons, e-stop
    m.add("control_door", CABINET, box(BX1 - 6, BX1 + 14, -300, 200, 820, 1440))
    m.add("control_panel", BLACK, box(BX1 + 10, BX1 + 22, -250, -30, 1180, 1360),
          box(BX1 + 10, BX1 + 20, -250, -30, 1050, 1140),
          box(BX1 + 12, BX1 + 40, 150, 185, 1020, 1160))                                   # door handle
    m.add("panel_buttons", LED, [cyl(m.r(14), (BX1 + 15, y, 1095), (BX1 + 30, y, 1095)) for y in (-210, -140, -70)])
    m.add("e_stop_collar", AMBER, cyl(46, (BX1 + 10, 80, 1300), (BX1 + 28, 80, 1300)))
    m.add("e_stop", RED, cyl(30, (BX1 + 26, 80, 1300), (BX1 + 58, 80, 1300)))
    m.add("door_hinges_front", DARK, [cyl(m.r(16), (BX1 + 14, -300, z), (BX1 + 14, -300, z + 90)) for z in (880, 1300)])

    # roof: exhaust stack with rain cap, lifting eye, beacon, work floods
    xe, ye = 820.0, -430.0
    ze = BZ1 + 330
    m.add("exhaust", DARK, cyl(45, (xe, ye, BZ1 + 20), (xe, ye, ze)), cyl(70, (xe, ye, BZ1 + 20), (xe, ye, BZ1 + 160)))
    m.add("rain_cap", BLACK, bar((xe - 50, ye, ze + 10), (xe + 60, ye, ze + 45), 100, m.t(10)),
          box(xe - 55, xe - 30, ye - 20, ye + 20, ze - 25, ze + 20))
    m.add("lifting_eye", STEEL, box(500, 610, -45, 45, BZ1 + 20, BZ1 + 50),
          eye_plate(555, 0, BZ1 + 30, 55, 28, m.t(25), "y"))
    xb, yb = 880.0, 300.0
    m.add("beacon_base", BLACK, cyl(70, (xb, yb, BZ1 + 20), (xb, yb, BZ1 + 62)))
    m.add("beacon", AMBER, cyl(52, (xb, yb, BZ1 + 60), (xb, yb, BZ1 + 150)), sphere(52, (xb, yb, BZ1 + 150)))
    fl, lens = [], []
    for s in (1, -1):
        y = s * 560
        fl += [box(BX1 - 110, BX1 - 50, y - 30, y + 30, BZ1 + 20, BZ1 + 180),
               box(BX1 - 150, BX1 - 10, y - 75, y + 75, BZ1 + 170, BZ1 + 300)]
        lens.append(box(BX1 - 140, BX1 - 20, s * 560 + s * 70, s * 560 + s * (75 + m.t(6)), BZ1 + 182, BZ1 + 288))
    m.add("work_flood_housings", BLACK, fl)
    m.add("work_floods", LED, lens)

    # fuel filler and the camlock water inlet on the left side
    m.add("fuel_filler", BLACK, cyl(42, (880, BY - 10, 1660), (880, BY + 40, 1660)),
          cyl(52, (880, BY + 38, 1660), (880, BY + 62, 1660)))
    m.add("water_inlet", STEEL, cyl(48, (BX0 + 120, BY - 10, 640), (BX0 + 120, BY + 90, 640)),
          box(BX0 + 50, BX0 + 190, BY - 10, BY + 20, 570, 710))
    m.add("inlet_cap", BLACK, cyl(60, (BX0 + 120, BY + 88, 640), (BX0 + 120, BY + 125, 640)),
          [bar((BX0 + 120, BY + 108, 640), (BX0 + 120 + 90 * c, BY + 108, 640 + 90 * sn), 24, m.t(14), up=(0, 1, 0))
           for c, sn in ((1, 0), (-1, 0))])
    if not m.print_mode:
        m.add("warning_label", AMBER, box(BX1 + 13, BX1 + 16, 60, 200, 900, 980))


# --------------------------------------------------------------------------- slewing base and yoke

def slew_base(m):
    ped = [cyl(300, (XT, 0, ZD - 3), (XT, 0, 1100)), cyl(420, (XT, 0, ZD - 3), (XT, 0, ZD + 25))]
    for a in (45, 135, 225, 315):
        g = prism([(290, ZD + 5), (405, ZD + 5), (290, ZD + 230)], "y", -m.t(20) / 2, m.t(20) / 2)
        ped.append(mv(rot(g, a, (0, 0, 1)), XT, 0, 0))
    m.add("pedestal", ORANGE, ped)
    m.add("pedestal_bolts", STEEL, [cyl(m.r(18), (XT + 375 * math.cos(a), 375 * math.sin(a), ZD + 20),
                                        (XT + 375 * math.cos(a), 375 * math.sin(a), ZD + 45))
                                    for a in np.linspace(0, 2 * math.pi, 12, endpoint=False) + 0.13])
    m.add("slewing_ring", DARK, cyl(425, (XT, 0, 1090), (XT, 0, 1155)))
    sx, sy = XT + 330, 330.0
    m.add("slew_drive", DARK, cyl(85, (sx, sy, 960), (sx, sy, 1160)), cyl(60, (sx, sy, 880), (sx, sy, 965)),
          box(sx - 40, sx + 40, sy - 110, sy - 70, 900, 1000))
    m.add("turntable", ORANGE, cyl(465, (XT, 0, 1150), (XT, 0, 1192)))

    # yoke: base beam and two tapered arms up to the trunnion bearings
    arm = [(XT - 200, 1250), (XT + 200, 1250)] + arc_pts(XT, ZT, 150, 0, 180, 14)
    yoke = [box(XT - 220, XT + 220, -760, 760, 1180, 1300)]
    for s in (1, -1):
        y0, y1 = sorted((s * 650, s * 730))
        yoke.append(prism(arm, "y", y0, y1))
        yoke.append(cyl(170, (XT, s * 715, ZT), (XT, s * 765, ZT)))                     # bearing housing
        yoke.append(prism([(XT - 220, 1295), (XT + 220, 1295), (XT + 150, 1560), (XT - 150, 1560)], "y",
                          *sorted((s * 640, s * 760))))
    yoke.append(box(XT - 210, XT - 120, -45, 45, 1290, 1420))                           # ram lug
    m.add("yoke", ORANGE, SL(yoke))
    m.add("trunnion_caps", STEEL, *SL([cyl(95, (XT, s * 760, ZT), (XT, s * 785, ZT)) for s in (1, -1)],
          [cyl(m.r(12), (XT + 60 * math.cos(a), s * 780, ZT + 60 * math.sin(a)),
               (XT + 60 * math.cos(a), s * 798, ZT + 60 * math.sin(a)))
           for s in (1, -1) for a in np.linspace(0, 2 * math.pi, 6, endpoint=False)]))

    # elevation ram, yoke lug to a lug under the barrel
    a = np.array(sp(XT - 165, 0, 1380.0))
    b = np.array(bp(-350, 0, -650))
    u = (b - a) / np.linalg.norm(b - a)
    ey = np.array(sp(XT, 1.0, 0.0)) - np.array(sp(XT, 0.0, 0.0))     # pin axis (the trunnion direction)
    j = a + (b - a) * 0.55
    t = lambda p: tuple(map(float, p))       # noqa: E731
    m.add("elevation_ram", BLACK, cyl(62, t(a + u * 30), t(j)), cyl(70, t(j - u * 60), t(j + u * 5)),
          cyl(55, t(a - ey * 60), t(a + ey * 60)))
    m.add("elevation_ram_rod", CHROME, cyl(32, t(j - u * 20), t(b - u * 30)),
          cyl(45, t(b - ey * 40), t(b + ey * 40)))
    m.add("ram_pins", STEEL, cyl(m.r(22), t(a - ey * 75), t(a + ey * 75)),
          cyl(m.r(22), t(b - ey * 70), t(b + ey * 70)))


# --------------------------------------------------------------------------- the barrel

def barrel(m):
    wall = m.t(35)
    ri = RB - wall
    shell = [ringx(ri, RB, -HL, HL), ringx(RB - 30, 628, HL - 60, HL + 5)]                # + intake flange
    boss = [cyl(130, (0, s * 520, 0), (0, s * 662, 0)) for s in (1, -1)]
    lugs = [box(-400, -300, -40, 40, -690, -560)]                                        # ram lug
    m.add("barrel", ORANGE, BW(shell, boss, lugs))
    m.add("barrel_core", DARK, BW(cx(ri + 10, -650, 650)))
    m.add("trunnion_band", DARK, BW(cx(RB + 18, -130, 130)))
    m.add("trunnion_pins", STEEL, SL([cyl(70, (XT, s * 640, ZT), (XT, s * 770, ZT)) for s in (1, -1)]))

    # axial fan behind the intake grille
    fan = [cx(150, 640, 775), cone(150, 70, (775, 0, 0), (830, 0, 0))]
    for k in range(7):
        blade = box(720 - 50, 720 + 50, -m.t(12) / 2, m.t(12) / 2, 130, ri - 25)
        blade = rot(blade, 32, (0, 0, 1), (720, 0, 0))
        fan.append(rot(blade, 360 * k / 7, (1, 0, 0)))
    m.add("fan", GALV, BW(fan))          # silver behind the black guard, so the two read apart

    # intake guard grille: rings and spokes
    gw = m.t(18)
    grille = [ringx(r - gw / 2, r + gw / 2, 868, 893) for r in (170, 290, 410, 530)]
    grille.append(cx(115, 862, 896))
    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        p0 = (880, 100 * math.cos(a), 100 * math.sin(a))
        p1 = (880, (ri + 12) * math.cos(a), (ri + 12) * math.sin(a))
        grille.append(bar(p0, p1, m.t(20), 28, up=(1, 0, 0)))
    m.add("intake_grille", BLACK, BW(grille))

    # flow-straightener vanes and nose cone in the outlet
    vanes = [cone(150, 55, (-640, 0, 0), (-790, 0, 0))]
    for k in range(8):
        v = box(-780, -640, -m.t(12) / 2, m.t(12) / 2, 120, ri + 10)
        vanes.append(rot(v, 360 * k / 8 + 22.5, (1, 0, 0)))
    m.add("straightener", ORANGE, BW(vanes))

    # nozzle ring: lip ring, feed manifold and 24 nozzles
    m.add("nozzle_ring", STEEL, BW(ringx(ri - 12, 642, -HL - 30, -HL + 12),
                                   ringx(588, 652, -HL + 5, -HL + 55)))            # + feed manifold
    noz = []
    for k in range(24):
        a = 2 * math.pi * (k + 0.5) / 24
        y, z = 605 * math.cos(a), 605 * math.sin(a)
        noz.append(cx(m.r(18), -HL - 20, -HL - 78, y, z))
        if not m.print_mode:
            noz.append(cone(18, 9, (-HL - 78, y, z), (-HL - 92, y, z)))
    m.add("nozzles", CHROME, BW(noz))

    # fan motor terminal box, lifting eyes and a stiffening band
    m.add("terminal_box", DARK, BW(box(260, 470, -130, 130, RB - 25, RB + 95)))
    m.add("barrel_eyes", STEEL, BW([eye_plate(x, 0, RB - 25, 50, 24, m.t(25), "x") for x in (-480, 380)]))
    m.add("barrel_band", DARK, BW(cx(RB + 14, -560, -500)))
    if not m.print_mode:
        m.add("barrel_stripe", WHITE, BW(cx(RB + 3, -440, -400)))


# --------------------------------------------------------------------------- water

def plumbing(m):
    # pump outlet on the back of the enclosure, hose to the rotary union in the pedestal
    m.add("pump_outlet", STEEL, cyl(55, (BX0 - 45, -450, 950), (BX0 + 10, -450, 950)),
          cyl(70, (BX0 - 50, -450, 950), (BX0 - 30, -450, 950)))
    da = math.radians(-30)
    p_in = (XT + 270 * math.cos(da), 270 * math.sin(da), 760)
    p_out = (XT + 370 * math.cos(da), 370 * math.sin(da), 760)
    m.add("pedestal_inlet", STEEL, cyl(45, p_in, p_out), cyl(60, (p_out[0] - 15 * math.cos(da), p_out[1] - 15 * math.sin(da), 760),
                                                             (p_out[0] + 5 * math.cos(da), p_out[1] + 5 * math.sin(da), 760)))
    hose1 = [(BX0 - 45, -450, 950), (40, -455, 900), (-160, -360, 760), (p_out[0] + 30, p_out[1] - 15, 760)]
    # rotary union on the turntable and the flexible loop up to the barrel feed pipe
    xu, yu = XT + 160, -400.0
    m.add("rotary_union", STEEL, SL(cyl(48, (xu, yu, 1185), (xu, yu, 1270)), cyl(60, (xu, yu, 1230), (xu, yu, 1250))))
    p0 = bp(-120, -585, 250)
    hose2 = [sp(*p) for p in ((xu, yu, 1265), (xu + 20, -560, 1420), (XT + 170, -850, 1700), (XT + 150, -860, 2200),
                              (XT + 40, -800, 2560))] + [p0]
    m.add("hoses", BLACK, pipe(hose1, m.r(36)), pipe(hose2, m.r(34)))
    # steel feed pipe along the barrel into the nozzle manifold, with clamps
    pts = [bp(-100, -585, 250), bp(-HL + 30, -585, 250)]
    m.add("feed_pipe", STEEL, pipe(pts, m.r(30)), cyl(45, bp(-130, -585, 250), bp(-60, -585, 250)))
    m.add("pipe_clamps", DARK, BW([box(x - 20, x + 20, -630, -548, 200, 300) for x in (-350, -650)]))


# --------------------------------------------------------------------------- supply hose reel

def hose_reel(m):
    xr, zr, yr = -1230.0, ZD + 360, 420.0
    dt = m.t(10)
    frame = []
    for s in (1, -1):
        y0, y1 = sorted((s * (yr + 20), s * (yr + 70)))
        frame += [bar((xr - 230, s * (yr + 45), ZD + 10), (xr, s * (yr + 45), zr), 50, 50, up=(0, 1, 0)),
                  bar((xr + 230, s * (yr + 45), ZD + 10), (xr, s * (yr + 45), zr), 50, 50, up=(0, 1, 0)),
                  box(xr - 270, xr + 270, y0, y1, ZD - 6, ZD + 30)]
    m.add("reel_frame", ORANGE, frame)
    m.add("reel_flanges", GALV, [cyl(285, (xr, s * (yr - dt), zr), (xr, s * yr, zr)) for s in (1, -1)],
          cyl(40, (xr, -yr - 95, zr), (xr, yr + 95, zr)))
    m.add("reel_hose", BLACK, cyl(215, (xr, -yr + 2, zr), (xr, yr - 2, zr)))
    m.add("hose_coupling", STEEL, cyl(42, (xr + 150, 200, zr + 150), (xr + 150, 200, zr + 260)),
          cyl(55, (xr + 150, 200, zr + 230), (xr + 150, 200, zr + 270)))
    m.add("reel_crank", BLACK, bar((xr, yr + 95, zr), (xr + 160, yr + 95, zr + 120), 34, m.t(18), up=(0, 1, 0)),
          cyl(m.r(16), (xr + 160, yr + 80, zr + 120), (xr + 160, yr + 190, zr + 120)))


# --------------------------------------------------------------------------- lights

def lights(m):
    xr = XR - 5
    m.add("tail_light_housings", BLACK, [box(xr - 24, xr + 4, s * 470 - 75, s * 470 + 75, 440, 590) for s in (1, -1)])
    m.add("tail_lights", TAIL, [box(xr - 30, xr - 20, s * 470 - 65, s * 470 + 10, 452, 578) for s in (1, -1)])
    m.add("indicators_rear", AMBER, [box(xr - 30, xr - 20, s * 470 + 18, s * 470 + 65, 452, 578) for s in (1, -1)])
    m.add("rear_reflectors", RED, [box(xr - m.t(6), xr + 1, s * 300 - 40, s * 300 + 40, 455, 520) for s in (1, -1)])
    pt = m.t(4)
    m.add("plate_bracket", BLACK, box(xr - 25, xr + 20, -70, 70, 360, ZF0 + 15))
    m.add("number_plate", WHITE, box(xr - 25 - pt, xr - 23, -260, 260, 300, 412))
    if not m.print_mode:
        m.add("plate_border", BLACK, box(xr - 26 - pt, xr - 25 - pt + 3, -255, 255, 300, 306),
              box(xr - 26 - pt, xr - 25 - pt + 3, -255, 255, 406, 412))
    m.add("marker_amber", AMBER, [box(XF - 70, XF - 20, s * (RY1 - 2), s * (RY1 + 18), 455, 500) for s in (1, -1)])
    m.add("marker_red", TAIL, [box(XR + 20, XR + 70, s * (RY1 - 2), s * (RY1 + 18), 455, 500) for s in (1, -1)])
    if not m.print_mode:
        red, white = [], []
        for k, y in enumerate(np.arange(-400, 400, 100)):
            if abs(y + 50) < 120:
                continue
            (red if k % 2 else white).append(box(xr - 3, xr + 1, y, y + 98, 500, 532))
        m.add("tape_red", RED, red)
        m.add("tape_white", WHITE, white)
