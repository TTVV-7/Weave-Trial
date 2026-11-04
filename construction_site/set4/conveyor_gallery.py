"""One 12 m module of an elevated, hoop-covered belt-conveyor gallery on its trestle bent.

A generic, brand-neutral overland / yard conveyor gallery of the kind that carries coal or potash
from the stockyard to the shiploader across a bulk export terminal. Every module is the same, so
modules placed end to end every 12 m (the next one 12 m along +X) make a continuous gallery: each
module's -X end sits on its own trestle bent and its +X end bears on the bent of the next module.
Dimensions are those of a typical 48 in (1,200 mm) belt conveyor gallery of the class:

* gallery: two 12.0 m long, 3.0 m deep Pratt side trusses at 3.0 m centres (3.2 m over the chord
  flanges), six 2.0 m panels; W200 (200 x 200) chords, 150 x 120 verticals and 150 x 120
  diagonals sloping down to mid-span, I-section floor beams at every panel point, X-bracing in
  plan under the floor and over the top chords, top struts and knee braces at every panel point;
  the underside of the bottom chords is 6.0 m above the ground, the top chords 9.0 m;
* conveyor (centre line 480 mm off the gallery axis): C200 stringers on short stools 400 mm above
  the floor, 35 deg three-roll troughing idlers (152 mm / 6 in rolls) at 1.2 m centres, flat
  return idlers at 3.0 m centres hung under the stringers, the 1,200 mm belt troughed on the
  carry side and flat on the return; a chequer-plate spill deck under the conveyor;
* hoop covers: 1.8 m diameter half-round white covers of corrugated sheet (the corrugations run
  round the arc) over the carry strand, held by galvanised hoops every 1.5 m on brackets off the
  stringers; the belt is open at the sides under the cover edges, as usual for hoop covers;
* walkway: ~950 mm clear, galvanised grating with longitudinal bearing bars on the +Y side,
  yellow handrail (top rail 1.1 m, mid rail, 100 mm toe board) along the truss side; an
  emergency-stop pull-wire lanyard with two pull-wire switches along the conveyor side; three
  LED walkway luminaires under the top struts; a galvanised cable ladder with three power /
  control cables on brackets off the -Y truss verticals;
* trestle bent at the -X end (x = -6 m): two splayed H-section columns (400 x 360, 4.8 m apart at
  the base, 3.5 m at the top) with a mid-height H strut and X-bracing in two tiers, an H cap
  beam (400 deep) carrying the bottom chords on bearing plates (shared with the previous
  module's chords), base plates with four anchor bolts on grout pads on 1.1 m square concrete
  pedestals; a bent / conveyor number plate on the strut.

Print (1:50): truss members, sheets, rails and the lanyard go through m.t() / m.r(), the grating
prints as a plain slab and, because a lone module would tip about its single bent, the print
alone carries two slim galvanised display props under the free (+X) end of the bottom chords
(placed clear of the next module's bent, so printed modules can still be lined up end to end).

Overall 12.55 m long (12.0 m gallery + the bent's pedestals), 5.9 m wide over the pedestals
(3.2 m over the gallery) and 9.0 m high.

Millimetres, X along the conveyor (bent at -X, free end at +X), Y left, Z up, ground at Z = 0.
"""

from __future__ import annotations

import math

import cadquery as cq
import numpy as np

from cadkit import Finish, arc_pts, band, bar, box, cyl, frustum, mv, place, prism, rgb, rot, text
from finishes import BLACK, CONCRETE, DARK, GALV, LED, RUBBER, STEEL, YELLOW

ASSET = dict(key="conveyor_gallery", stem="Conveyor_Gallery_Module",
             title="Conveyor Gallery Module on Trestle Bent", az=35, el=18, size="1200x900")

STRUCT = Finish(rgb("#8e969d"), metal=0.25, rough=0.55)     # painted structural steel -> Silver grey
HOOD = Finish(rgb("#eff1ef"), rough=0.5)                    # prepainted white hood sheet -> White
CHEQUER = Finish(rgb("#6f767c"), metal=0.5, rough=0.5)      # chequer-plate spill deck
GROUT = Finish(rgb("#9d9b95"), rough=0.97)
PLATE_WHITE = Finish(rgb("#f4f4ef"), rough=0.5)

# ---------------------------------------------------------------- gallery
E = 6000.0                          # half length of the module
YT = 1500.0                         # side-truss centre planes, |Y|
ZB = 6100.0                         # bottom chord centre (underside 6000)
ZT = 8900.0                         # top chord centre (top 9000)
XS = [-5925.0, -4000.0, -2000.0, 0.0, 2000.0, 4000.0, 5925.0]     # panel points
# longitudinal parts stop a few mm short of the module ends, each at its own x, so nothing
# shares an end face with the chords (the gap between two modules is invisible)
END = dict(deck=5997.0, grating=5994.0, stringer=5998.0, belt=5992.0, ret=5995.0, hood=5990.0,
           rail=5993.0, mid=5996.0, toe=5991.0, tray=5989.0, cable=5987.0, lanyard=5986.0)

# ---------------------------------------------------------------- conveyor
YC = -480.0                         # conveyor centre line
ZS = 6800.0                         # top of the stringers
ZR = 6960.0                         # centre-roll axis
RR = 76.0                           # 152 mm rolls
TR = math.radians(35.0)             # trough angle
ZRR = 6440.0                        # return-roll axis
RRR = 64.0
XI = [-5400.0 + 1200.0 * k for k in range(10)]        # carrying idlers
XRI = [-4500.0, -1500.0, 1500.0, 4500.0]              # return idlers
RH = 900.0                          # hood inside radius
XH = [-5250.0 + 1500.0 * k for k in range(8)]         # hoops

# ---------------------------------------------------------------- walkway
YW0, YW1 = 470.0, 1425.0            # grating
ZW = 6235.0                         # top of the grating
YH = 1340.0                         # handrail line

# ---------------------------------------------------------------- bent
XB = -E
YB0, ZB0 = 2400.0, 620.0            # column axis at the base plate
YB1, ZB1 = 1750.0, 5640.0           # column axis at the cap beam


def ycol(z):
    return YB0 + (YB1 - YB0) * (z - ZB0) / (ZB1 - ZB0)


# =========================================================================== helpers

def ipts(cu, cv, d, bf, tf, tw):
    """I-section outline: u across the flanges, v along the depth."""
    u, v = bf / 2, d / 2
    pts = [(-u, -v), (u, -v), (u, -v + tf), (tw / 2, -v + tf), (tw / 2, v - tf), (u, v - tf),
           (u, v), (-u, v), (-u, v - tf), (-tw / 2, v - tf), (-tw / 2, -v + tf), (-u, -v + tf)]
    return [(cu + a, cv + b) for a, b in pts]


def i_x(m, x0, x1, yc, zc, d, bf, tf, tw):
    """I-beam along X, web vertical."""
    return prism(ipts(yc, zc, d, bf, m.t(tf), m.t(tw)), "x", x0, x1)


def i_y(m, y0, y1, xc, zc, d, bf, tf, tw):
    """I-beam along Y, web vertical."""
    return prism(ipts(xc, zc, d, bf, m.t(tf), m.t(tw)), "y", y0, y1)


def member(m, a, b, d, bf, tf, tw, up):
    """I-section member from a to b, its depth towards `up`."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    dv = b - a
    L = float(np.linalg.norm(dv))
    x = dv / L
    y = np.cross(np.asarray(up, float), x)
    y /= np.linalg.norm(y)
    z = np.cross(x, y)
    s = prism(ipts(0, 0, d, bf, m.t(tf), m.t(tw)), "x", 0, L)
    return place(s, x, y, z, a)


def revolve_x(profile, yc, zc, a0, span):
    """Solid of revolution about the line (., yc, zc) parallel to X; profile in (x, r);
    angles from +Y towards +Z."""
    s = cq.Workplane("XY").polyline(profile).close().revolve(span, (0, 0, 0), (1, 0, 0)).val()
    return mv(rot(s, a0, (1, 0, 0)), 0, yc, zc)


def ring_x(yc, zc, r0, r1, a0, a1, x0, x1, n=28):
    """Part annulus round the X axis line (., yc, zc), extruded from x0 to x1."""
    return prism(arc_pts(yc, zc, r1, a0, a1, n) + arc_pts(yc, zc, r0, a1, a0, n), "x", x0, x1)


def hexnut(x, y, z0, z1, r):
    return prism([(x + r * math.cos(math.radians(30 + 60 * k)), y + r * math.sin(math.radians(30 + 60 * k)))
                  for k in range(6)], "z", z0, z1)


# =========================================================================== build

def build(m):
    truss(m)
    floor(m)
    conveyor(m)
    hood(m)
    walkway(m)
    services(m)
    bent(m)
    if m.print_mode:
        props(m)


# --------------------------------------------------------------------------- side trusses

def truss(m):
    chords = []
    for s in (1, -1):
        chords.append(i_x(m, -E, E, s * YT, ZB, 200, 200, 16, 10))
        chords.append(i_x(m, -E, E, s * YT, ZT, 200, 200, 16, 10))
    m.add("chords", STRUCT, chords)

    verts, diags = [], []
    for s in (1, -1):
        for x in XS:
            hw = 70.0 if abs(x) > 5000 else 75.0
            verts.append(box(x - hw, x + hw, s * (YT - 60), s * (YT + 60), ZB + 50, ZT - 50))
        for xa, xb in zip(XS, XS[1:]):
            if xa + xb < 0:             # Pratt: diagonals slope down towards mid-span
                a, b = (xa, s * YT, ZT - 50), (xb, s * YT, ZB + 50)
            else:
                a, b = (xa, s * YT, ZB + 50), (xb, s * YT, ZT - 50)
            diags.append(bar(a, b, 150, 120, up=(0, 1, 0)))
    m.add("truss_verticals", STRUCT, verts)
    m.add("truss_diagonals", STRUCT, diags)

    # top struts, plan bracing over the top chords, knee braces at every panel point
    struts, tops, knees = [], [], []
    for x in XS:
        hw = 70.0 if abs(x) > 5000 else 75.0
        struts.append(box(x - hw, x + hw, -YT, YT, ZT - 80, ZT + 80))
        for s in (1, -1):
            knees.append(bar((x, s * (YT - 30), ZT - 650), (x, s * (YT - 520), ZT - 60), 100, 90, up=(1, 0, 0)))
    for xa, xb in zip(XS, XS[1:]):
        for s in (1, -1):
            tops.append(bar((xa, -s * YT, ZT), (xb, s * YT, ZT), 90, 90))
    m.add("top_struts", STRUCT, struts)
    m.add("top_bracing", STRUCT, tops)
    m.add("knee_braces", STRUCT, knees)


# --------------------------------------------------------------------------- floor

def floor(m):
    beams = []
    for x in XS:
        bf = 140.0 if abs(x) > 5000 else 150.0
        beams.append(i_y(m, -YT, YT, x, 6107.5, 175, bf, 14, 9))
    m.add("floor_beams", STRUCT, beams)
    braces = []
    for xa, xb in zip(XS, XS[1:]):
        for s in (1, -1):
            braces.append(bar((xa, -s * YT, 6080), (xb, s * YT, 6080), 100, 90))
    m.add("floor_bracing", STRUCT, braces)
    e = END["deck"]
    m.add("spill_deck", CHEQUER, box(-e, e, -1420, YW0 + 10, 6190, 6190 + m.t(8)))


# --------------------------------------------------------------------------- conveyor

def conveyor(m):
    # stools from the floor beams up to the stringers
    stools = [box(x - 55, x + 55, YC + s * 630, YC + s * 695, 6185, 6612) for x in XS for s in (1, -1)]
    m.add("stools", STRUCT, stools)

    # C200 x 75 stringers, toes in
    tf, tw = m.t(11), m.t(8)
    e = END["stringer"]
    for s in (1, -1):
        o, i = YC + s * 700, YC + s * 625
        prof = [(o, ZS), (i, ZS), (i, ZS - tf), (o - s * tw, ZS - tf), (o - s * tw, ZS - 200 + tf),
                (i, ZS - 200 + tf), (i, ZS - 200), (o, ZS - 200)]
        m.add("stringer", STRUCT, prism(prof, "x", -e, e))

    # 35 deg troughing idlers: base angle, four stands, three rolls
    c, sn = math.cos(TR), math.sin(TR)
    w0, z0, wl = 255.0, ZR + 15, 465.0          # wing-roll axis: inner end and length
    frames, rolls = [], []
    for x in XI:
        frames.append(box(x - 45, x + 45, YC - 770, YC + 770, ZS - 10, ZS + 50))
        for s in (1, -1):
            st = m.t(10)
            frames.append(box(x - 40, x + 40, YC + s * 244 - st / 2, YC + s * 244 + st / 2, ZS + 45, ZR + 45))
            frames.append(box(x - 40, x + 40, YC + s * 660 - st / 2, YC + s * 660 + st / 2, ZS + 45,
                              z0 + wl * sn + 30))
            a = (x, YC + s * w0, z0)
            b = (x, YC + s * (w0 + wl * c), z0 + wl * sn)
            rolls.append(cyl(RR, a, b))
        rolls.append(cyl(RR, (x, YC - 232, ZR), (x, YC + 232, ZR)))
    # return idlers: drop brackets off the stringer webs and one flat roll
    for x in XRI:
        for s in (1, -1):
            bt = m.t(14)
            frames.append(box(x - 40, x + 40, YC + s * 698 - bt / 2, YC + s * 698 + bt / 2, ZRR - 50, ZS - 190))
        rolls.append(cyl(RRR, (x, YC - 705, ZRR), (x, YC + 705, ZRR)))
    m.add("idler_frames", GALV, frames)
    m.add("idler_rolls", STEEL, rolls)

    # belt: troughed carry strand on the rolls (bedded 6 mm), flat return strand
    bt = m.t(16)
    sink = 6.0
    flat = 210.5
    zc = ZR + RR - sink
    wing = (1200.0 - 2 * flat) / 2
    h = bt / 2
    path = [(-flat - wing * c - h * sn, zc + wing * sn + h * c), (-flat, zc + h), (flat, zc + h),
            (flat + wing * c + h * sn, zc + wing * sn + h * c)]
    path = [(YC + y, z) for y, z in path]
    e = END["belt"]
    m.add("belt_carry", RUBBER, prism(band(path, h), "x", -e, e))
    zr = ZRR + RRR - sink
    m.add("belt_return", RUBBER, box(-END["ret"], END["ret"], YC - 600, YC + 600, zr, zr + bt))


# --------------------------------------------------------------------------- hoop covers

def hood(m):
    ct = m.t(3)                     # sheet
    d = 20.0                        # corrugation depth
    rb = RH + ct
    e = END["hood"]
    n = 100                         # corrugations (ridges run round the arc)
    xs = np.linspace(-e, e, 2 * n + 1)
    prof = [(float(x), rb + (d if k % 2 else 0.0)) for k, x in enumerate(xs)]
    prof += [(e, RH), (-e, RH)]
    m.add("hood_sheets", HOOD, revolve_x(prof, YC, ZS, -5, 190))

    hoops, brackets = [], []
    r0 = rb - 2                     # hoop beds into the valleys too (no sealed pockets)
    r1 = rb + d + m.t(8)
    reach = rb + d + 30             # bracket reach from the conveyor centre
    for x in XH:
        hoops.append(ring_x(YC, ZS, r0, r1, -5, 185, x - 30, x + 30))
        for s in (1, -1):
            lo, hi = sorted((YC + s * 690, YC + s * reach))
            brackets.append(box(x - 40, x + 40, lo, hi, ZS - 110, ZS - 40))
    m.add("hood_hoops", GALV, hoops)
    m.add("hood_brackets", STRUCT, brackets)


# --------------------------------------------------------------------------- walkway

def walkway(m):
    e = END["grating"]
    if m.print_mode:
        m.add("grating", GALV, box(-e, e, YW0, YW1, 6190, ZW))
    else:
        # longitudinal bearing bars (5 mm at 30 mm) on a 10 mm deep band of cross bars
        pts = [(YW0, 6190)]
        y = YW0
        while y + 30 <= YW1:
            pts += [(y, ZW), (y + 5, ZW), (y + 5, 6200), (y + 30, 6200)]
            y += 30
        pts += [(y, ZW), (YW1, ZW), (YW1, 6190)]
        m.add("grating", GALV, prism(pts, "x", -e, e))

    m.add("toe_board", YELLOW, box(-END["toe"], END["toe"], YH + 18, YH + 18 + m.t(8), ZW - 10, ZW + 100))
    rp = m.r(24)
    posts = [cyl(rp, (x, YH, ZW - 10), (x, YH, ZW + 1125)) for x in (-5850, -4000, -2000, 0, 2000, 4000, 5850)]
    rails = [cyl(rp, (-END["rail"], YH, ZW + 1105), (END["rail"], YH, ZW + 1105)),
             cyl(m.r(20), (-END["mid"], YH, ZW + 560), (END["mid"], YH, ZW + 560))]
    m.add("handrail", YELLOW, posts, rails)


# --------------------------------------------------------------------------- services

def services(m):
    # cable ladder on brackets off the -Y truss verticals, with three cables
    tt = m.t(5)
    y0, y1, zt = -1420.0, -1120.0, 7600.0
    prof = [(y0, zt), (y1, zt), (y1, zt + 100), (y1 - tt, zt + 100), (y1 - tt, zt + tt),
            (y0 + tt, zt + tt), (y0 + tt, zt + 100), (y0, zt + 100)]
    m.add("cable_ladder", GALV, prism(prof, "x", -END["tray"], END["tray"]),
          [box(x - 30, x + 30, -YT + 50, y1 + 20, zt - 35, zt + 5) for x in XS])
    m.add("cables", BLACK, [cyl(r, (-END["cable"], y, zt + tt + r - 3), (END["cable"], y, zt + tt + r - 3))
                            for y, r in ((-1350, 32.0), (-1270, 26.0), (-1200, 22.0))])

    # walkway luminaires under the top struts over the walkway
    m.add("luminaires", GALV, [box(x - 300, x + 300, 860, 1040, ZT - 210, ZT - 75) for x in (-4000, 0, 4000)])
    m.add("luminaire_lenses", LED, [box(x - 270, x + 270, 890, 1010, ZT - 222, ZT - 205) for x in (-4000, 0, 4000)])

    # emergency-stop pull-wire: posts on the hood brackets, lanyard, two pull-wire switches
    ct = m.t(3)
    yp = YC + RH + ct + 20 + 30 - 22
    zl = 7280.0
    posts = [cyl(m.r(14), (x, yp, ZS - 100), (x, yp, zl + 40)) for x in XH]
    m.add("pullwire_posts", GALV, posts)
    m.add("pullwire_lanyard", YELLOW, cyl(m.r(5), (-END["lanyard"], yp, zl), (END["lanyard"], yp, zl)))
    for x in (XH[0], XH[5]):
        m.add("pullwire_switch", YELLOW, box(x - 90, x + 90, yp - 15, yp + 120, zl - 230, zl + 25))
        m.add("pullwire_lever", BLACK, box(x - 20, x + 20, yp + 100, yp + 150, zl - 120, zl + 60))


# --------------------------------------------------------------------------- trestle bent

def bent(m):
    ped, grout, plates, bolts, nuts = [], [], [], [], []
    for s in (1, -1):
        y = s * YB0
        ped.append(box(XB - 550, XB + 550, y - 550, y + 550, -2, 525))   # 2 mm into the ground, like every other base
        ped.append(frustum((XB - 550, XB + 550, y - 550, y + 550, 520), (XB - 500, XB + 500, y - 500, y + 500, 600)))
        grout.append(box(XB - 380, XB + 380, y - 380, y + 380, 595, 630))
        pt = m.t(40)
        plates.append(box(XB - 340, XB + 340, y - 340, y + 340, 625, 625 + pt))
        for dx in (-260, 260):
            for dy in (-260, 260):
                bolts.append(cyl(m.r(18), (XB + dx, y + dy, 600), (XB + dx, y + dy, 625 + pt + 70)))
                nuts.append(hexnut(XB + dx, y + dy, 625 + pt - 2, 625 + pt + 34, 34))
    m.add("pedestals", CONCRETE, ped)
    m.add("grout_pads", GROUT, grout)
    m.add("base_plates", STRUCT, plates)
    m.add("anchor_bolts", STEEL, bolts, nuts)

    # splayed H columns, flanges facing +-X
    cols = [member(m, (XB, s * YB0, ZB0), (XB, s * YB1, ZB1), 400, 360, 25, 16, (1, 0, 0)) for s in (1, -1)]
    m.add("bent_columns", STRUCT, cols)

    # cap beam with web stiffeners, bearing plates under the chords
    cap = [i_y(m, -2050, 2050, XB, 5800, 400, 440, 30, 18)]
    for y in (-YT, YT, -YB1, YB1):
        cap.append(box(XB - 210, XB + 210, y - m.t(15) / 2, y + m.t(15) / 2, 5615, 5985))
    m.add("cap_beam", STRUCT, cap)
    m.add("bearing_plates", DARK, [box(XB - 190, XB + 190, s * YT - 140, s * YT + 140, 5992, 5992 + m.t(25))
                                   for s in (1, -1)])

    # mid-height H strut and X-bracing in two tiers
    zs = 3200.0
    m.add("bent_strut", STRUCT, member(m, (XB, -ycol(zs), zs), (XB, ycol(zs), zs), 250, 250, 16, 10, (0, 0, 1)))
    xb = []
    for za, zb in ((950.0, 3050.0), (3350.0, 5450.0)):
        for s in (1, -1):
            xb.append(bar((XB, -s * ycol(za), za), (XB, s * ycol(zb), zb), 160, 160, up=(1, 0, 0)))
    m.add("bent_bracing", STRUCT, xb)

    # conveyor / bent number plate on the +X face of the strut
    px = XB + 120
    pt = m.t(20)
    m.add("bent_plate", PLATE_WHITE, box(px, px + pt, -470, 470, zs - 105, zs + 105))
    ef = max(2.0, 0.3 * m.scale) if m.print_mode else 3.0
    t = text("CV-03  B07", 125, ef, (px + pt - 1, 0, zs), (0, 1, 0), (1, 0, 0))
    if t is not None:
        m.add("bent_plate_text", BLACK, t)


# --------------------------------------------------------------------------- print-only display props

def props(m):
    """Two slim posts under the free end, so a lone printed module stands; clear of the next
    module's bent (its pedestals start at |y| 1850, its cap beam at x 5780)."""
    xp = 5600.0
    out = []
    for s in (1, -1):
        out.append(box(xp - 250, xp + 250, s * YT - 250, s * YT + 250, -2, -2 + m.t(40)))
        out.append(box(xp - 100, xp + 100, s * YT - 80, s * YT + 80, 20, 6030))
    m.add("display_props", GALV, out)
