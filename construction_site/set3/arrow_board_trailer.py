"""Solar-powered flashing arrow board (traffic advisor) on a single-axle trailer, set up for work:
sign raised, outriggers down on pads, tongue resting on its jockey wheel.

A generic, brand-neutral unit with the typical proportions of the class:

* trailer: a 2.4 m long x 1.2 m wide rectangular-tube frame (rails 3 x 4 in) with a checker-plate
  deck, one axle on leaf springs just behind the middle, 15 in trailer wheels (~660 mm tyres),
  round fenders, ~1.82 m wide over the fenders; an A-frame tongue with a 2 in ball coupler, safety
  chains, a wiring lead and a side-mounted swivel jockey jack, ~3.8 m long overall (2.25 m wide
  over the outrigger jacks);
* arrow panel: the standard 96 x 48 in (2,440 x 1,220 mm) Type C board, black face in an aluminium
  edge frame, raised on a telescoping square mast (6 in outer, 5 in inner) so its bottom is
  ~2.1 m and its top ~3.3 m above the ground, facing the rear (-X) where traffic approaches;
  25 amber lamp heads (~5.7 in hooded LED lamps, lens, bezel and sun visor) laid out as a
  right-pointing arrow (as the approaching driver sees it): a 13-lamp shaft and a two-row chevron
  head; a photocell for night dimming on the top edge; back stiffeners and a clamp bracket on the
  inner mast;
* mast: hand winch with crank on the front face, lift cable over a sheave on the outer-tube
  collar, lock pin, side braces down to the frame rails, a controller cabinet on the rear face
  with a coiled cord (hung beside the mast) up to the sign;
* power: two ~100 W solar modules (1,150 x 660 mm) on a rack over the rear deck, tilted 25 deg
  towards the rear, with adjustable front struts and junction boxes, the leads cable-tied down the
  rack and along the deck to the controller (display only; left out of the print); a lidded aluminium
  battery box (sized for a bank of deep-cycle batteries) on the front deck with hinges, hasp,
  padlock, handles and louvres;
* stabilisers: four telescoping outrigger arms with top-wind screw jacks on timber pads, the
  usual set-up for a 2.4 m sign in wind;
* lighting: round red stop/tail lamps, red and amber reflectors and side markers, a 12 x 6 in
  licence plate on a bracket with its lamp above, red/white conspicuity tape on the rear.

Millimetres, X forward (tongue at +X), Y left, Z up, ground at Z = 0.
"""

from __future__ import annotations

import math

import cadquery as cq
import numpy as np

from cadkit import Finish, arc_pts, band, bar, box, cone, cyl, mirror_y, mv, pipe, prism, rgb, rot, sphere, torus
from finishes import AMBER, BLACK, DARK, GALV, LED, ORANGE, RED, REFLECTOR, RUBBER, STEEL, TIMBER_DARK, WHITE

ASSET = dict(key="arrow_board_trailer", stem="Solar_Arrow_Board_Trailer", title="Solar Arrow Board Trailer",
             az=215, el=15, size="1200x900")

ALU = Finish(rgb("#c3c7cb"), metal=0.6, rough=0.38)           # aluminium battery box, panel frames
SIGN_FACE = Finish(rgb("#161718"), rough=0.85)                # flat black sign face
HOOD = Finish(rgb("#0e0f10"), rough=0.4)                      # glossy black lamp hoods
CELL = Finish(rgb("#1c2c52"), metal=0.35, rough=0.15)         # mono solar cells
BACKSHEET = Finish(rgb("#dfe3e8"), rough=0.5)                 # white backsheet between cells
CABINET = Finish(rgb("#8f969d"), metal=0.3, rough=0.5)        # controller cabinet
CHECKER = Finish(rgb("#5d6268"), metal=0.5, rough=0.5)        # checker-plate deck
TAIL = Finish(rgb("#d81b1b"), rough=0.25, glow=(0.35, 0.0, 0.0))

# ---- trailer
XR, XF = -1320.0, 1080.0          # frame rear / front
RY0, RY1 = 525.0, 600.0           # frame rail inner / outer y
ZF0, ZF1 = 430.0, 530.0           # frame rail bottom / top
XA = -250.0                       # axle
RT = 330.0                        # tyre radius
ZC = RT * (1 - 0.015)             # wheel centre: tyres sink 1.5 % for a flat print contact patch
YT0, YT1 = 690.0, 880.0           # tyre inner / outer face

# ---- mast and sign
XM = 450.0                        # mast centre
MO, MI = 76.0, 63.0               # half widths of the outer and inner mast tubes
ZS = 2710.0                       # sign centre: bottom 2100, top 3320
SW, SH, SD = 2440.0, 1220.0, 100.0
XB = XM - MO - 50                 # back of the sign panel, clear of the outer-mast collar
XS = XB - SD                      # sign face

# ---- solar rack
TILT = 25.0
P0X, P0Z = -1260.0, 1080.0        # lower edge of the modules' underside
PL, PW = 1150.0, 660.0            # module length up the slope, width
CT, ST = math.cos(math.radians(TILT)), math.sin(math.radians(TILT))


def T(u, y, w):
    """Solar-rack coordinates (u up the slope, y, w off the module back) to the model's."""
    return (P0X + u * CT - w * ST, y, P0Z + u * ST + w * CT)


def tilted(s):
    return mv(rot(s, -TILT, (0, 1, 0)), P0X, 0, P0Z)


def revolve_y(profile, xc, zc):
    """Solid of revolution about the line through (xc, ., zc) parallel to Y; profile in (r, y)."""
    s = cq.Workplane("XY").polyline(profile).close().revolve(360, (0, 0, 0), (0, 1, 0)).val()
    return mv(s, xc, 0, zc)


def ring_yz(yc, zc, r0, r1, a0, a1, x0, x1, n=18):
    """Part annulus in the YZ plane (angles from +Y towards +Z), extruded along X."""
    return prism(arc_pts(yc, zc, r1, a0, a1, n) + arc_pts(yc, zc, r0, a1, a0, n), "x", x0, x1)


def chain_links(points, m, r_link=20.0, wire=5.5):
    """A hanging chain through points: alternating round links; a plain rod in print."""
    if m.print_mode:
        return pipe(points, m.r(wire))
    pts = [np.asarray(p, float) for p in points]
    out, k = [], 0
    for a, b in zip(pts, pts[1:]):
        d = b - a
        L = float(np.linalg.norm(d))
        t = d / L
        n1 = np.cross(t, [0, 0, 1.0])
        n1 = n1 / np.linalg.norm(n1) if np.linalg.norm(n1) > 1e-6 else np.array([1.0, 0, 0])
        n2 = np.cross(t, n1)
        for s in np.arange(0, L, 1.55 * r_link):
            c = a + t * s
            out.append(torus(r_link, wire, tuple(c), tuple(n1 if k % 2 else n2)))
            k += 1
    return out


# =========================================================================== build

def build(m):
    trailer(m)
    wheels(m)
    outriggers(m)
    tongue(m)
    mast(m)
    sign(m)
    solar(m)
    battery_box(m)
    lights(m)


# --------------------------------------------------------------------------- frame, axle

def trailer(m):
    rails = [box(XR, XF, s * RY0, s * RY1, ZF0, ZF1) for s in (1, -1)]
    cross = [box(XR, XR + 75, -RY1, RY1, ZF0, ZF1), box(XF - 75, XF, -RY1, RY1, ZF0, ZF1)]
    cross += [box(x - 35, x + 35, -RY0 - 2, RY0 + 2, ZF0 + 15, ZF1 - 5) for x in (-760, XA + 10, 180, XM, 760)]
    m.add("frame", ORANGE, rails, cross)
    dt = m.t(6)
    m.add("deck", CHECKER, box(XR + 75, XF - 75, -RY0 - 2, RY0 + 2, ZF1 - 4, ZF1 + dt))
    if not m.print_mode:            # raised checker pattern, too fine to print
        studs = []
        for i, x in enumerate(np.arange(XR + 130, XF - 100, 90)):
            for y in np.arange(-480 + 45 * (i % 2), 480, 90):
                studs.append(rot(box(x - 18, x + 18, y - 5, y + 5, ZF1 + dt - 1, ZF1 + dt + 2),
                                 45 if (i + int(y // 90)) % 2 else -45, (0, 0, 1), (x, y, 0)))
        m.add("deck_tread", CHECKER, studs)
    # tie-down D rings on the rail sides
    m.add("tie_downs", STEEL, [torus(38, m.r(9), (x, s * (RY1 + 12), ZF1 - 20), (1, 0, 0))
                               for x in (-700, 640) for s in (1, -1)],
          [box(x - 30, x + 30, s * (RY1 - 2), s * (RY1 + 14), ZF1 - 45, ZF1 - 5) for x in (-700, 640) for s in (1, -1)])

    # axle, leaf springs, hangers, U-bolts
    m.add("axle", BLACK, cyl(38, (XA, -705, ZC), (XA, 705, ZC)))
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
              box(XA - 65, XA + 65, yc - 38, yc + 38, ZC - 62, ZC - 40))
    # brake-less hub drums
    m.add("hubs", DARK, [cyl(92, (XA, s * 640, ZC), (XA, s * 712, ZC)) for s in (1, -1)])


def wheels(m):
    tyre = [(200, 698), (245, 690), (300, 690), (318, 697), (327, 712), (RT, 740), (RT, 830),
            (327, 858), (318, 873), (300, 880), (245, 880), (200, 872)]
    rim = [(0, 700), (208, 700), (208, 712), (204, 718), (204, 858), (208, 864), (208, 874),
           (186, 874), (176, 862), (118, 846), (0, 846)]
    for s, side in ((1, "L"), (-1, "R")):
        t = revolve_y(tyre, XA, ZC)
        r = revolve_y(rim, XA, ZC)
        lugs = [cyl(m.r(13), (XA + 72 * math.cos(a), 840, ZC + 72 * math.sin(a)),
                    (XA + 72 * math.cos(a), 866, ZC + 72 * math.sin(a)))
                for a in np.linspace(0, 2 * math.pi, 5, endpoint=False) + 0.3]
        cap = [cyl(50, (XA, 840, ZC), (XA, 868, ZC)), cone(50, 28, (XA, 868, ZC), (XA, 886, ZC))]
        if s < 0:
            t, r = mirror_y(t), mirror_y(r)
            lugs, cap = [mirror_y(x) for x in lugs], [mirror_y(x) for x in cap]
        m.add(f"tyre_{side}", RUBBER, t)
        m.add(f"rim_{side}", GALV, r, cap)
        m.add(f"lug_nuts_{side}", STEEL, lugs)

    # round fenders with a rolled outer edge, on brackets from the rails
    ri, ft = 372.0, m.t(6)
    for s in (1, -1):
        y0, y1 = sorted((s * 648, s * 906))
        arch = arc_pts(XA, ZC, ri + ft, 6, 174, 30) + arc_pts(XA, ZC, ri, 174, 6, 30)
        lip = arc_pts(XA, ZC, ri + ft + 14, 8, 172, 30) + arc_pts(XA, ZC, ri, 172, 8, 30)
        yl0, yl1 = sorted((s * 888, s * 906))
        m.add("fender", ORANGE, prism(arch, "y", y0, y1), prism(lip, "y", yl0, yl1),
              [box(XA + d - 30, XA + d + 30, s * 590, s * 662, ZF0, ZF1) for d in (-345, 345)])


# --------------------------------------------------------------------------- outriggers

def outriggers(m):
    YJ = 1080.0
    arms, jacks, inner, pads, cranks = [], [], [], [], []
    for x in (-1180.0, 930.0):
        arms.append(box(x - 40, x + 40, -YJ - 40, YJ + 40, ZF0 + 12, ZF0 + 92))
        for s in (1, -1):
            y = s * YJ
            arms.append(box(x - 52, x + 52, s * (RY1 - 2), s * (RY1 + 50), ZF0, ZF1 + 6))     # receiver
            arms.append(cyl(m.r(11), (x, s * (RY1 + 25), ZF0 - 20), (x, s * (RY1 + 25), ZF1 + 50)))
            jacks += [box(x - 46, x + 46, y - 46, y + 46, 300, 980),
                      box(x - 58, x + 58, y - 58, y + 58, ZF0, ZF0 + 110),
                      box(x - 52, x + 52, y - 52, y + 52, 975, 1000)]
            inner += [box(x - 35, x + 35, y - 35, y + 35, 50, 320), sphere(40, (x, y, 52))]
            pads.append(box(x - 160, x + 160, y - 160, y + 160, 0, 32))
            inner.append(cyl(112, (x, y, 28), (x, y, 50)))
            cranks += [cyl(m.r(16), (x, y, 990), (x, y, 1060)),
                       pipe([(x, y, 1050), (x, y, 1070), (x + 170, y, 1070), (x + 170, y, 1150)], m.r(12)),
                       cyl(m.r(18), (x + 170, y, 1110), (x + 170, y, 1170))]
    m.add("outrigger_arms", ORANGE, arms)
    m.add("jack_tubes", ORANGE, jacks)
    m.add("jack_legs", GALV, inner)
    m.add("jack_cranks", BLACK, cranks)
    m.add("jack_pads", TIMBER_DARK, pads)


# --------------------------------------------------------------------------- tongue

def tongue(m):
    xa, xc = XF - 70, 2110.0
    m.add("a_frame", ORANGE, [bar((xa, s * 540, 480), (xc, s * 48, 480), 75, 100) for s in (1, -1)],
          box(1960, 2290, -50, 50, 430, 530), box(1600, 1680, -285, 285, 440, 520),
          box(xa - 10, xa + 40, -RY1, RY1, ZF0, ZF1))
    # ball coupler with latch
    m.add("coupler", GALV, box(2240, 2370, -58, 58, 455, 548), sphere(58, (2368, 0, 488)),
          cyl(58, (2368, 0, 430), (2368, 0, 488)), box(2240, 2370, -50, 50, 430, 470))
    m.add("coupler_latch", BLACK, bar((2270, 0, 556), (2390, 0, 572), 40, m.t(22)),
          cyl(m.r(14), (2275, -40, 550), (2275, 40, 550)))
    # safety chains hanging in loops off the tongue
    for s in (1, -1):
        pts = [(2010, s * 80, 445), (2050, s * 95, 350), (2120, s * 98, 290), (2190, s * 80, 330),
               (2230, s * 45, 440)]
        m.add("safety_chain", STEEL, chain_links(pts, m))
        m.add("chain_hook", STEEL, pipe([(2230, s * 45, 445), (2255, s * 62, 405), (2280, s * 52, 445)], m.r(9)))
    # wiring lead with a flat plug
    lead = [(XF - 40, 548, ZF1 + 6), (xc - 40, 60, ZF1 + 6), (2180, 62, 560), (2230, 95, 520), (2240, 120, 450)]
    m.add("wiring_lead", BLACK, pipe(lead, m.r(9)), box(2215, 2265, 100, 150, 400, 455))
    # document tube on the A-frame
    m.add("document_tube", BLACK, cyl(45, (1250, 433, 568), (1650, 254, 568)), cyl(50, (1235, 440, 568), (1270, 424, 568)),
          box(1420, 1460, 340, 400, ZF1 - 5, 545))

    # side-wind swivel jockey jack on the -Y rail
    xj, yj = 1760.0, -330.0
    y_rail = -(540 - (xj - xa) / (xc - xa) * (540 - 48))
    m.add("jack_mount", ORANGE, box(xj - 50, xj + 50, yj + 30, y_rail + 20, 440, 520))
    m.add("jockey_jack", BLACK, cyl(38, (xj, yj, 300), (xj, yj, 940)), cyl(46, (xj, yj, 900), (xj, yj, 960)),
          box(xj - 55, xj + 55, yj - 50, yj + 50, 420, 540))
    m.add("jockey_crank", BLACK, cyl(m.r(12), (xj, yj, 920), (xj + 120, yj, 920)),
          bar((xj + 110, yj, 920), (xj + 110, yj - 20, 1080), 26, m.t(14), up=(1, 0, 0)),
          cyl(m.r(16), (xj + 110, yj - 20, 1070), (xj + 200, yj - 20, 1070)))
    zw = 100 * (1 - 0.015)
    m.add("jockey_leg", GALV, cyl(30, (xj, yj, 190), (xj, yj, 320)),
          box(xj - 80, xj + 30, yj - 45, yj + 45, 190, 205),
          [box(xj - 80, xj - 55, yj + s * 38 - m.t(6) / 2, yj + s * 38 + m.t(6) / 2, zw - 10, 200) for s in (1, -1)],
          cyl(m.r(12), (xj - 68, yj - 46, zw), (xj - 68, yj + 46, zw)))
    m.add("jockey_wheel", RUBBER, cyl(100, (xj - 68, yj - 30, zw), (xj - 68, yj + 30, zw)))
    m.add("jockey_hub", GALV, cyl(45, (xj - 68, yj - 33, zw), (xj - 68, yj + 33, zw)))


# --------------------------------------------------------------------------- mast

def mast(m):
    m.add("mast_outer", ORANGE, box(XM - MO, XM + MO, -MO, MO, ZF1, 2350),
          box(XM - 170, XM + 170, -170, 170, ZF1, ZF1 + 22),
          [mv(rot(prism([(MO - 2, 0), (165, 0), (MO - 2, 340)], "y", -m.t(20) / 2, m.t(20) / 2), a, (0, 0, 1)),
              XM, 0, ZF1) for a in (0, 90, 180, 270)])
    m.add("mast_braces", ORANGE, [bar((XM, s * 562, ZF1 - 10), (XM, s * (MO - 10), 1560), 60, 60, up=(1, 0, 0))
                                  for s in (1, -1)],
          [box(XM - 50, XM + 50, s * 520, s * 600, ZF1 - 5, ZF1 + 15) for s in (1, -1)])
    m.add("mast_collar", DARK, box(XM - 92, XM + 92, -92, 92, 2290, 2390))
    m.add("mast_inner", GALV, box(XM - MI, XM + MI, -MI, MI, 2200, 3170))
    m.add("mast_cap", DARK, box(XM - 72, XM + 72, -72, 72, 3165, 3190),
          torus(45, m.r(12), (XM, 0, 3215), (1, 0, 0)))
    m.add("lock_pin", STEEL, cyl(m.r(13), (XM, -130, 2340), (XM, 130, 2340)),
          torus(32, m.r(5), (XM, -130, 2310), (0, 1, 0)))

    # hand winch on the front face, cable up over a sheave at the collar
    xw, zw = XM + MO + 64, 1180.0
    pt = m.t(8)
    m.add("winch_frame", DARK, [box(XM + MO - 4, xw + 50, s * 62 - pt / 2, s * 62 + pt / 2, zw - 90, zw + 90)
                                for s in (1, -1)],
          box(XM + MO - 4, XM + MO + 10, -70, 70, zw - 110, zw + 110))
    m.add("winch_drum", GALV, cyl(36, (xw, -58, zw), (xw, 58, zw)), cyl(60, (xw, -62, zw), (xw, -62 + m.t(10), zw)),
          cyl(60, (xw, 62 - m.t(10), zw), (xw, 62, zw)))
    m.add("winch_crank", BLACK, cyl(m.r(12), (xw, 50, zw), (xw, 120, zw)),
          bar((xw, 116, zw), (xw + 40, 116, zw + 170), 30, m.t(12), up=(0, 1, 0)),
          cyl(m.r(16), (xw + 40, 110, zw + 170), (xw + 40, 210, zw + 170)))
    m.add("winch_cable", STEEL, cyl(m.r(5), (xw - 28, 0, zw), (xw - 28, 0, 2350)))
    m.add("sheave", DARK, cyl(46, (xw - 2, -12, 2350), (xw - 2, 12, 2350)),
          [box(XM + 80, xw + 30, s * 18 - m.t(6) / 2, s * 18 + m.t(6) / 2, 2310, 2385) for s in (1, -1)])

    # controller cabinet on the rear face
    xc0 = XM - MO - 175
    m.add("controller", CABINET, box(xc0, XM - MO + 4, -160, 160, 1240, 1660),
          box(xc0 - 12, XM - MO, -172, 172, 1660, 1675))
    m.add("controller_trim", BLACK, [cyl(m.r(9), (xc0 - 6, 158, z - 40), (xc0 - 6, 158, z + 40)) for z in (1320, 1580)],
          box(xc0 - 14, xc0 + 2, -150, -125, 1420, 1500),
          box(xc0 - 5, xc0 + 2, -100, 100, 1550, 1610))
    m.add("controller_lamps", LED, [box(xc0 - 8, xc0 + 1, y - 10, y + 10, 1570, 1590) for y in (-60, -20, 20)])
    # coiled cord from the cabinet up to the sign, hung off to the side of the mast
    xcc, ycc, rc = XM - MO - 40, 118.0, 28.0
    coil = [torus(rc, m.r(7), (xcc, ycc, z), (0, 0, 1)) for z in np.arange(1720, 2060, 13)]
    if m.print_mode:                 # fill the coil, so it does not seal a void
        coil.append(cyl(rc, (xcc, ycc, 1720), (xcc, ycc, 2056)))
    m.add("sign_cord", BLACK, cyl(m.r(9), (xcc, ycc, 1660), (xcc, ycc + rc, 1725)), coil,
          cyl(m.r(9), (xcc, ycc + rc, 2050), (xcc, ycc, 2120)), cyl(m.r(9), (xcc, ycc, 2120), (xcc, ycc, ZS - 380)))
    m.add("cord_clip", DARK, box(xcc - 14, XM - MO + 6, 70, ycc + 14, 2160, 2190))
    # conduit down to the deck and forward to the battery box
    m.add("conduit", BLACK, pipe([(XM - MO - 30, -120, 1245), (XM - MO - 30, -120, ZF1 + 15),
                                  (XM - MO - 30, -300, ZF1 + 15), (690, -300, ZF1 + 15), (690, -300, 700)], m.r(14)))


# --------------------------------------------------------------------------- sign

LAMPS = [(i, 0) for i in range(-6, 7)] + [(6 - k - d, s * k) for k in (1, 2, 3) for d in (0, 1) for s in (1, -1)]


def sign(m):
    z0, z1 = ZS - SH / 2, ZS + SH / 2
    m.add("sign_face", SIGN_FACE, box(XS, XB, -SW / 2, SW / 2, z0, z1))
    e, rim = 42.0, 22.0
    m.add("sign_frame", DARK, box(XS - rim, XB + 6, -SW / 2, SW / 2, z0, z0 + e),
          box(XS - rim, XB + 6, -SW / 2, SW / 2, z1 - e, z1),
          box(XS - rim, XB + 6, -SW / 2, -SW / 2 + e, z0, z1), box(XS - rim, XB + 6, SW / 2 - e, SW / 2, z0, z1))
    # back stiffeners and the clamp bracket on the inner mast
    back = [box(XB - 3, XB + 26, -SW / 2 + 60, SW / 2 - 60, z - 30, z + 30) for z in (ZS - 380, ZS + 380)]
    back += [box(XB - 3, XB + 26, y - 25, y + 25, z0 + 60, z1 - 60) for y in (-760, 760)]
    back.append(box(XB - 3, XM - MI + 6, -120, 120, 2450, ZS + 440))
    back += [box(XM - 78, XM + 78, -78, 78, z - 45, z + 45) for z in (ZS - 150, ZS + 380)]
    m.add("sign_mount", DARK, back)
    if not m.print_mode:            # bolt heads round the edge frame
        heads = [cyl(9, (XS - rim + 1, y, z), (XS - rim - 5, y, z))
                 for y in np.linspace(-SW / 2 + 21, SW / 2 - 21, 9) for z in (z0 + 21, z1 - 21)]
        heads += [cyl(9, (XS - rim + 1, y, z), (XS - rim - 5, y, z))
                  for y in (-SW / 2 + 21, SW / 2 - 21) for z in np.linspace(z0 + 21, z1 - 21, 5)[1:-1]]
        m.add("sign_frame_bolts", STEEL, heads)
    m.add("sign_bolts", STEEL, [cyl(m.r(12), (XM + 78 - 4, y, z), (XM + 100, y, z))
                                for z in (ZS - 150, ZS + 380) for y in (-45, 45)])

    # 25 hooded amber lamp heads: right-pointing arrow as seen from -X (viewer's right is -Y)
    PU, PZ = 170.0, 155.0
    rh, rl = 72.0, 61.0
    vt = m.t(4)
    v_in, v_out = (rh - 6, rh - 6 + vt) if not m.print_mode else (78 - vt, 78)
    v_len = 60.0 if not m.print_mode else 70.0
    va0, va1 = (15, 165) if not m.print_mode else (-4, 184)    # hood over the top of the lens
    housings, lenses, visors = [], [], []
    for i, j in LAMPS:
        y, z = -i * PU, ZS + j * PZ
        housings.append(cyl(rh, (XS + 3, y, z), (XS - 30, y, z)))
        lenses.append(cyl(rl, (XS - 24, y, z), (XS - 34, y, z)))
        visors.append(ring_yz(y, z, v_in, v_out, va0, va1, XS - 28 - v_len, XS - 26))
    m.add("lamp_housings", HOOD, housings)
    m.add("lamp_visors", HOOD, visors)
    m.add("lamp_lenses", AMBER, lenses)

    # photocell on the top edge, and a lifting handle
    m.add("photocell", BLACK, cyl(28, (XS + 40, 900, z1 - 5), (XS + 40, 900, z1 + 45)))
    m.add("photocell_dome", WHITE, sphere(26, (XS + 40, 900, z1 + 45)))


# --------------------------------------------------------------------------- solar

def solar(m):
    for s in (1, -1):
        y0, y1 = sorted((s * 12, s * (12 + PW)))
        fr = 20.0
        m.add("solar_frame", ALU, tilted(box(0, PL, y0, y1, 0, 36)))
        if m.print_mode:
            m.add("solar_cells", CELL, tilted(box(fr, PL - fr, y0 + fr, y1 - fr, 30, 40)))
            continue
        m.add("solar_backsheet", BACKSHEET, tilted(box(fr, PL - fr, y0 + fr, y1 - fr, 30, 38)))
        nu, ny, g = 7, 4, 4.0
        cu = (PL - 2 * fr - (nu + 1) * g) / nu
        cw = (PW - 2 * fr - (ny + 1) * g) / ny
        cells = []
        for a in range(nu):
            for b in range(ny):
                u = fr + g + a * (cu + g)
                yy = y0 + fr + g + b * (cw + g)
                cells.append(tilted(box(u, u + cu, yy, yy + cw, 34, 39)))
        m.add("solar_cells", CELL, cells)
        # aluminium rim standing proud of the glass
        m.add("solar_rim", ALU, tilted(box(0, PL, y0, y0 + fr, 36, 42)), tilted(box(0, PL, y1 - fr, y1, 36, 42)),
              tilted(box(0, fr, y0, y1, 36, 42)), tilted(box(PL - fr, PL, y0, y1, 36, 42)))
    m.add("junction_boxes", BLACK, [tilted(box(880, 990, yc - 60, yc + 60, -32, 2)) for yc in (-340, 340)])

    # rack: two cross tubes under the modules, short rear legs, adjustable front struts
    rack = [tilted(box(u - 35, u + 35, -720, 720, -55, 2)) for u in (140, 1000)]
    lo, hi = T(140, 0, -28), T(1000, 0, -28)
    if not m.print_mode:            # module leads cable-tied along the rack and deck to the controller
        leads, ties = [], []
        xl, xd, zd = hi[0] + 30, XM - MO - 30, ZF1 + 6
        for s in (1, -1):
            yc, yr = s * 340, s * 562
            pts = [T(935, yc, -30), T(1000, yc, -58), T(1000, yr, -58), (xl, yr, T(1000, yr, -58)[2]),
                   (xl, yr, zd), (xd, yr, zd), (xd, s * 190, zd), (xd, s * 190, 558), (xd, s * 60, 558),
                   (xd, s * 60, 1250)]
            leads += pipe(pts, 8.0)
            ties += [cyl(11, (xl, yr, z - 6), (xl, yr, z + 6)) for z in (700, 1000, 1300)]
            ties += [cyl(11, (x - 6, yr, zd), (x + 6, yr, zd)) for x in (-150, 100)]
            ties += [cyl(11, (xd, s * 60, z - 6), (xd, s * 60, z + 6)) for z in (800, 1100)]
        m.add("solar_leads", BLACK, leads)
        m.add("cable_ties", DARK, ties)
    legs, struts = [], []
    for s in (1, -1):
        y = s * 562
        legs.append(box(lo[0] - 30, lo[0] + 30, y - 30, y + 30, ZF1 - 5, lo[2]))
        legs.append(box(hi[0] - 35, hi[0] + 35, y - 35, y + 35, ZF1 - 5, 1200))
        struts.append(box(hi[0] - 24, hi[0] + 24, y - 24, y + 24, 1150, hi[2]))
        struts += [cyl(m.r(10), (hi[0], y - 50, z), (hi[0], y + 50, z)) for z in (1170,)]
        legs.append(bar((lo[0] + 20, y, ZF1 + 20), (hi[0] - 20, y, 1150), 40, 40, up=(0, 1, 0)))
    m.add("solar_rack", DARK, rack, legs)
    m.add("tilt_struts", GALV, struts)


# --------------------------------------------------------------------------- battery box

def battery_box(m):
    x0, x1, yb, z1 = 690.0, 1050.0, 540.0, 1000.0
    m.add("battery_box", ALU, box(x0, x1, -yb, yb, ZF1 - 2, z1))
    lp = m.t(10)                     # front lip of the lid
    m.add("battery_lid", ALU, box(x0 - 12, x1 + lp, -yb - 12, yb + 12, z1, z1 + 34),
          box(x1 - 2, x1 + lp, -yb - 12, yb + 12, z1 - 40, z1 + 34))
    hw = []
    for y in (-330, 330):
        hw += [cyl(m.r(13), (x0 - 18, y - 70, z1 + 8), (x0 - 18, y + 70, z1 + 8)),
               box(x0 - 20, x0 + 2, y - 70, y + 70, z1 - 40, z1 + 10)]
    hw += [box(x1 + lp - 2, x1 + lp + 14, -40, 40, z1 - 90, z1 + 20),          # hasp
           box(x1 + lp + 10, x1 + lp + 38, -26, 26, z1 - 150, z1 - 85)]        # padlock body
    hw.append(torus(17, m.r(5), (x1 + lp + 24, 0, z1 - 80), (1, 0, 0)))
    for s in (1, -1):
        hw.append(pipe([(830, s * yb, 880), (830, s * (yb + 45), 880), (950, s * (yb + 45), 880),
                        (950, s * yb, 880)], m.r(10)))
    m.add("battery_hardware", STEEL, hw)
    if not m.print_mode:
        m.add("battery_louvres", DARK, [box(x, x + 26, s * yb - 1, s * (yb + 6), 640, 800)
                                        for x in np.arange(720, 1020, 42) for s in (1, -1)])
    if not m.print_mode:
        m.add("battery_label", REFLECTOR, box(x1 - 1, x1 + 3, -260, -60, 760, 860))


# --------------------------------------------------------------------------- lights

def lights(m):
    xr = XR
    # bumper/light bar on the rear cross member
    m.add("tail_light_housings", BLACK, [box(xr - 22, xr + 2, s * 470 - 72, s * 470 + 72, 440, 590) for s in (1, -1)])
    m.add("tail_lights", TAIL, [cyl(56, (xr - 20, s * 470, 515), (xr - 34, s * 470, 515)) for s in (1, -1)])
    m.add("rear_reflectors", RED, [box(xr - m.t(6), xr + 1, s * 320 - 35, s * 320 + 35, 455, 515) for s in (1, -1)])
    # 12 x 6 in licence plate on a bracket off the rear member, its lamp on top shining down
    bt, pt = m.t(18), m.t(3)
    xp = xr - 12 - bt                                   # rear face of the bracket post
    m.add("plate_bracket", BLACK, box(xp - 2, xr + 2, -260, -40, 450, 450 + m.t(20)),
          box(xp, xr - 12, -170, -130, 450, 712))
    m.add("licence_plate", WHITE, box(xp - pt + 2, xp + 2, -340, -35, 540, 692))
    if not m.print_mode:            # embossed border, display only
        m.add("plate_border", DARK, box(xp - pt, xp - pt + 3, -335, -40, 545, 551),
              box(xp - pt, xp - pt + 3, -335, -40, 681, 687),
              box(xp - pt, xp - pt + 3, -335, -329, 545, 687), box(xp - pt, xp - pt + 3, -46, -40, 545, 687))
    m.add("plate_lamp", BLACK, box(xp - 30, xr - 20, -175, -125, 700, 726))
    m.add("plate_lamp_lens", LED, box(xp - 28, xp + 2, -165, -135, 694, 702))
    # conspicuity tape along the rear member and the rail sides (decals, display only)
    if not m.print_mode:
        red, white = [], []
        for k, y in enumerate(np.arange(-275, 275, 78)):
            (red if k % 2 else white).append(box(xr - 2, xr + 1, y, y + 76, 485, 522))
        for s in (1, -1):
            for x0, x1 in ((-1110, -760), (140, 600), (690, 860)):
                for k, x in enumerate(np.arange(x0, x1 - 60, 152)):
                    (red if k % 2 else white).append(box(x, x + 150, s * (RY1 - 1), s * (RY1 + 2), 465, 505))
        m.add("tape_red", RED, red)
        m.add("tape_white", WHITE, white)
    # side markers: amber at the front, red at the rear
    m.add("marker_amber", AMBER, [box(XF - 70, XF - 20, s * (RY1 - 2), s * (RY1 + 18), 455, 495) for s in (1, -1)])
    m.add("marker_red", TAIL, [box(XR + 20, XR + 70, s * (RY1 - 2), s * (RY1 + 18), 455, 495) for s in (1, -1)])
