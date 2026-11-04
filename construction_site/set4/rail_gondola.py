"""Rotary-dump coal gondola (aluminium tub-bottom body), loaded with a heaped coal topping.

A generic, brand-neutral North American unit-train coal car with the typical dimensions of the
modern aluminium rotary-dump gondola (the cars that shuttle between the mines and a coal export
terminal's rotary car dumper):

* body: 53 ft 1 in (16,180 mm) over the coupler pulling faces, 50 ft 6 in (15.4 m) over the
  strikers, end sheets 15.1 m apart; 3.04 m outside the side sheets, ~3.19 m over the top chords
  (~3.27 m over the corner grab irons), 3.9 m from the top of rail to the top chord. A "tub"
  (bathtub) body: between the trucks the floor drops to ~0.6 m above the rail, over the trucks it
  sits at 1.15 m on the body bolsters and short stub centre sills; ~4,700 cu ft (132 m3) level
  full, about 112 t of coal at 0.85 t/m3, a 286,000 lb gross-rail-load car's payload.
  Extruded top chords, 17 external hat-section side posts a side, a side sill following the tub,
  end sheets with vertical end posts and horizontal stiffeners, corner posts;
* trucks: two 3-piece (cast side frame + bolster) freight trucks at 40 ft 6 in (12,344 mm)
  centres, 70 in (1,778 mm) wheelbase, 36 in (914 mm) wheels on standard gauge (1,435 mm; 1,360
  mm back-to-back), roller-bearing journals ~2.0 m apart with adapters and end caps, spring nests
  and friction wedges in the side frame windows, side bearings and centre plates, brake beams
  with shoes on the treads. The wheels stand on Z = 0 = top of rail (no rail modelled): the
  flanges reach below it, as they would inside the rails of the digital twin's track;
* ends: the B end (+X, the hand-brake end) carries the ROTARY coupler (swivel collar) and is
  identified by red-painted end top chord and corner-post caps; a vertical hand-brake wheel on its
  geared housing with the brake staff/chain down to the end sill; the air-brake reservoir and
  control valve on the end sheet; the A end (-X) has a standard fixed coupler. Both ends have
  E-type couplers on 34.5 in (876 mm) centreline height, strikers, uncoupling levers, air hoses
  with glad hands and the train line, end-ladder rungs on one corner, sill steps and side grab
  irons at all four corners;
* markings: a black reporting-mark panel on each side with a generic mark "XXXX 104526" (not a
  real railroad's mark) and capacity data, white retro-reflective strips on the side sills;
* load: a coal fill heaped ~0.2 m above the top chords in a long ridge, sloping off at the ends.

At 1:50 the print is ~324 mm long (~66 x 82 mm in section). Colours: bare aluminium body, black
trucks / underframe details / coal, red rotary-end marks, white lettering and reflectors.

Millimetres, X forward (B end at +X), Y left, Z up, Z = 0 at the top of rail, centred on the car.
"""

from __future__ import annotations

import math

import cadquery as cq
import numpy as np

from cadkit import Finish, band, bar, box, cyl, mv, prism, rgb, rot, text
from finishes import BLACK, DARK, RED, STEEL, WHITE

ASSET = dict(key="rail_gondola", stem="Rail_Gondola_Coal", title="Coal Rail Car (rotary-dump gondola)",
             az=30, el=20, size="1200x900")

ALU = Finish(rgb("#c3c7cb"), metal=0.6, rough=0.38)        # bare aluminium body
TRUCK = Finish(rgb("#202224"), rough=0.7)                   # black cast trucks
WHEEL = Finish(rgb("#2b2725"), metal=0.3, rough=0.6)        # dark, rust-tinged rolled-steel wheels
COAL = Finish(rgb("#141516"), rough=0.95)                   # bituminous coal
PANEL = Finish(rgb("#1b1c1e"), rough=0.8)                   # black lettering panel
ROTARY_RED = RED

# ---- body
E = 7550.0                  # end sheet outer face, |x|
YS = 1520.0                 # side sheet outer face, |y|
YP = YS + 42                # side posts outer face
ZE = 1150.0                 # body bottom over the trucks
ZT = 600.0                  # tub bottom between the trucks
X_TUB, X_RISE = 4250.0, 4700.0      # tub flat ends / top of the tub slope
ZTOP = 3900.0               # top of the top chord
ZCOAL = 3775.0              # level fill

# ---- running gear
XT = 6172.0                 # truck centres (40 ft 6 in)
WB = 889.0                  # half wheelbase (70 in)
R = 457.0                   # 36 in wheel, tread radius
ZC = R * (1 - 0.015)        # axle height: wheels sunk 1.5 % for a flat print contact
YJ = 1003.0                 # journal / side-frame centre line, |y|
ZK = 876.0                  # coupler centreline (34.5 in)
XCPL = 8090.0               # coupler pulling face (53 ft 1 in over couplers)


def rounded(poly, r, n=4):
    """Polyline with its interior corners rounded off (quadratic, r mm back from each corner)."""
    p = [np.asarray(q, float) for q in poly]
    out = [tuple(p[0])]
    for a, b, c in zip(p, p[1:], p[2:]):
        u, v = (a - b) / np.linalg.norm(a - b), (c - b) / np.linalg.norm(c - b)
        p0, p2 = b + u * r, b + v * r
        for t in np.linspace(0, 1, n + 1):
            out.append(tuple((1 - t) ** 2 * p0 + 2 * t * (1 - t) * b + t ** 2 * p2))
    out.append(tuple(p[-1]))
    return out


BOTTOM = rounded([(-E, ZE), (-X_RISE, ZE), (-X_TUB, ZT), (X_TUB, ZT), (X_RISE, ZE), (E, ZE)], 160)


def bottom_z(x):
    xs, zs = zip(*BOTTOM)
    return float(np.interp(x, xs, zs))


def revolve_y(profile, xc, zc):
    """Solid of revolution about the line through (xc, ., zc) parallel to Y; profile in (r, y)."""
    s = cq.Workplane("XY").polyline(profile).close().revolve(360, (0, 0, 0), (0, 1, 0)).val()
    return mv(s, xc, 0, zc)


def rod(points, r, square=False):
    """A bent rod through points: cylinders (or square bars, lighter for the web) run on by r past
    each end, so the bends close square."""
    out = []
    for a, b in zip(points, points[1:]):
        a, b = np.asarray(a, float), np.asarray(b, float)
        d = (b - a) / np.linalg.norm(b - a)
        if square:
            out.append(bar(tuple(a - d * r), tuple(b + d * r), 2 * r, 2 * r))
        else:
            out.append(cyl(r, tuple(a - d * r), tuple(b + d * r)))
    return out


def build(m):
    body(m)
    ends(m)
    coal(m)
    markings(m)
    for xt in (XT, -XT):
        truck(m, xt)
    for s in (1, -1):
        coupler(m, s)
    hand_brake(m)
    air_brake(m)
    ladders_and_grabs(m)


# --------------------------------------------------------------------------- body

def body(m):
    te = m.t(8)
    side = BOTTOM + [(E, 3810.0), (-E, 3810.0)]
    m.add("side_sheets", ALU, [prism(side, "y", s * (YS - te), s * YS) for s in (1, -1)])
    # floor plate following the tub, a little inside the side sheets
    floor = [(x, z + 36) for x, z in BOTTOM]
    m.add("floor", ALU, prism(band(floor, 36), "y", -(YS - 4), YS - 4))
    # side sill (bottom chord) along the tub edge
    sill = [(x, z + 10) for x, z in BOTTOM]
    m.add("side_sills", ALU, [prism(band(sill, 60), "y", s * (YS - 20), s * (YS + 48)) for s in (1, -1)])
    # extruded top chords
    chord = [(YS - 50, 3750), (YS + 75, 3750), (YS + 75, 3872), (YS + 50, ZTOP), (YS - 50, ZTOP)]
    m.add("top_chords", ALU, [prism([(s * y, z) for y, z in chord], "x", -E - 30, E + 30) for s in (1, -1)])
    # hat-section side posts
    posts = []
    for x in np.linspace(-E + 420, E - 420, 17):
        zb = max(bottom_z(x - 55), bottom_z(x + 55)) + 40            # ends inside the side sill
        for s in (1, -1):
            y0, y1 = sorted((s * (YS - 5), s * YP))
            posts.append(box(x - 55, x + 55, y0, y1, zb, 3770))
            y0, y1 = sorted((s * (YS - 5), s * (YP + 10)))
            posts.append(box(x - 30, x + 30, y0, y1, zb + 30, 3760))        # hat crown
    m.add("side_posts", ALU, posts)

    # body bolsters and stub centre sills over the trucks
    bol = [(-YS + 10, 1170), (YS - 10, 1170), (YS - 10, 1060), (420, 725), (-420, 725), (-YS + 10, 1060)]
    under = []
    for s in (1, -1):
        under.append(prism(bol, "x", s * XT - 210, s * XT + 210))
        x0, x1 = sorted((s * (XT - 700), s * (E + 10)))
        under.append(box(x0, x1, -210, 210, 735, 1165))
        x0, x1 = sorted((s * (E - 30), s * (E + 160)))
        under.append(box(x0, x1, -(YS + 25), YS + 25, 940, 1180))                # end sill
        under.append(cyl(190, (s * XT, 0, 690), (s * XT, 0, 745)))              # centre plate
        under += [box(s * XT - 95, s * XT + 95, y - 80, y + 80, 695, 800) for y in (-635, 635)]  # side bearings
    m.add("underframe", BLACK, under)


def ends(m):
    te = m.t(8)
    for s in (1, -1):
        x0, x1 = sorted((s * (E - te), s * E))
        parts = [box(x0, x1, -(YS - 2), YS - 2, 1100, 3810)]
        # vertical end posts and horizontal end stiffeners
        xa, xb = sorted((s * (E - 5), s * (E + 80)))
        parts += [box(xa, xb, y - 60, y + 60, 1120, 3760) for y in (-520, 520)]
        xa, xb = sorted((s * (E - 5), s * (E + 70)))
        parts += [box(xa, xb, -(YS - 60), YS - 60, z - 50, z + 50) for z in (1750, 2450, 3150)]
        # corner posts
        xa, xb = sorted((s * (E - 90), s * (E + 50)))
        for sy in (1, -1):
            ya, yb = sorted((sy * (YS - 90), sy * (YS + 45)))
            parts.append(box(xa, xb, ya, yb, 1000, 3800))
        m.add("end_walls", ALU, parts)
        # end top chord: red at the rotary (B, +X) end
        xa, xb = sorted((s * (E - 60), s * (E + 45)))
        chord = box(xa, xb, -(YS + 40), YS + 40, 3760, ZTOP - 5)
        if s > 0:
            m.add("rotary_end_chord", ROTARY_RED, chord)
            xa, xb = sorted((s * (E - 96), s * (E + 56)))
            m.add("rotary_end_post_caps", ROTARY_RED,
                  [box(xa, xb, *sorted((sy * (YS - 96), sy * (YS + 51))), 3350, 3755) for sy in (1, -1)])
        else:
            m.add("end_chords", ALU, chord)


# --------------------------------------------------------------------------- coal

def coal(m):
    te = m.t(8)
    xl, yl = E - te + 5, YS - te + 5
    fill = [(max(-xl, min(xl, x)), z + 60) for x, z in BOTTOM]
    fill = [(-xl, ZE + 60)] + fill[1:-1] + [(xl, ZE + 60), (xl, ZCOAL), (-xl, ZCOAL)]
    body = prism(fill, "y", -yl, yl)
    H = 320.0
    cross = [(-yl, 3740.0)] + [(y, ZCOAL + H * (1 - abs(y / yl) ** 1.5)) for y in np.linspace(-yl, yl, 21)] \
        + [(yl, 3740.0)]
    longi = [(-xl, 3700), (xl, 3700), (xl, 3790), (xl - 1300, 4400), (-(xl - 1300), 4400), (-xl, 3790)]
    heap = prism(cross, "x", -xl, xl).intersect(prism(longi, "y", -yl - 10, yl + 10))
    m.add("coal_load", COAL, body, heap)
    if not m.print_mode:          # lumps on the heap
        rng = np.random.default_rng(7)
        lumps = []
        for _ in range(70):
            x = rng.uniform(-xl + 400, xl - 400)
            y = rng.uniform(-yl + 150, yl - 150)
            z = min(ZCOAL + H * (1 - abs(y / yl) ** 1.5),
                    3790 + (xl - abs(x)) * (610 / 1300))
            r = rng.uniform(50, 105)
            lump = box(-r, r, -0.8 * r, 0.8 * r, -0.7 * r, 0.7 * r)
            lump = rot(rot(lump, rng.uniform(-30, 30), (1, 0, 0)), rng.uniform(-30, 30), (0, 1, 0))
            lumps.append(mv(rot(lump, rng.uniform(0, 180)), x, y, z - 0.35 * r))
        m.add("coal_lumps", COAL, lumps)


# --------------------------------------------------------------------------- markings

def markings(m):
    xs = np.linspace(-E + 420, E - 420, 17)
    bay = (xs[14] + xs[15]) / 2          # last-but-one bay at the left end of each side
    panels, big, small, strips = [], [], [], []
    for s in (1, -1):
        xc = s * bay                     # +Y side: left end is +X; -Y side: left end is -X
        y0, y1 = sorted((s * (YS - 30), s * (YS + 10)))
        panels.append(box(xc - 360, xc + 360, y0, y1, 2150, 3420))
        yt = s * (YS + 7)
        xd, nd = (-s, 0, 0), (0, s, 0)
        big.append(text("XXXX", 190, 9, (xc, yt, 3170), xd, nd))
        big.append(text("104526", 150, 9, (xc, yt, 2840), xd, nd))
        if not m.print_mode:
            for line, z in (("CAPY 245000", 2480), ("LT WT 36400", 2370)):
                small.append(text(line, 64, 7, (xc, yt, z), xd, nd))
        # retro-reflective strips on the side sill, between posts
        for x in (-6685.0, -2227.0, 2227.0, 6685.0):
            zb = bottom_z(x)
            ya, yb = sorted((s * (YS + 20), s * (YS + 54)))
            strips.append(box(x - 200, x + 200, ya, yb, zb - 30, zb + 50))
    m.add("mark_panels", PANEL, panels)
    m.add("reporting_marks", WHITE, big)
    if small:
        m.add("capacity_data", WHITE, small)
    m.add("reflective_strips", WHITE, strips)


# --------------------------------------------------------------------------- trucks

def side_frame_polygon():
    right = [(700, 790), (1000, 765), (1150, 720), (1150, 640), (1090, 640), (1090, 400), (1013, 400),
             (1013, 600), (765, 600), (765, 390), (430, 200)]
    return [(0, 800)] + right + [(0, 200)] + [(-x, z) for x, z in reversed(right)]


def truck(m, xt):
    tag = "B" if xt > 0 else "A"
    frames, springs, wedges, wheels, axles, bearings, brakes = [], [], [], [], [], [], []
    poly = [(xt + x, z) for x, z in side_frame_polygon()]
    win = [(370, 335), (370, 690), (690, 690), (690, 475), (440, 345)]
    for sy in (1, -1):
        y0, y1 = sorted((sy * (YJ - 63), sy * (YJ + 63)))
        f = prism(poly, "y", y0, y1)
        cuts = [box(xt - 280, xt + 280, y0 - 5, y1 + 5, 320, 690)]          # bolster opening
        for sx in (1, -1):
            cuts.append(prism([(xt + sx * x, z) for x, z in win], "y", y0 - 5, y1 + 5))
        f = f.cut(*cuts)
        # top flange of the compression member, and the spring seat
        fy0, fy1 = sorted((sy * (YJ - 80), sy * (YJ + 80)))
        f2 = [prism([(xt + x, z) for x, z in ((-1000, 765), (-700, 790), (700, 790), (1000, 765),
                                               (1000, 745), (700, 770), (-700, 770), (-1000, 745))],
                    "y", fy0, fy1),
              box(xt - 300, xt + 300, fy0, fy1, 290, 330)]
        frames += [f] + f2
        # spring nest and friction wedges
        for x in (-175.0, 0.0, 175.0):
            springs.append(cyl(58 if m.print_mode else 46, (xt + x, sy * YJ, 315), (xt + x, sy * YJ, 480)))   # filled in print
            springs += [cyl(60, (xt + x, sy * YJ, z - 9), (xt + x, sy * YJ, z + 9)) for z in (345, 380, 415, 450)]
        for sx in (1, -1):
            xa, xb = sorted((xt + sx * 222, xt + sx * 288))
            wedges.append(box(xa, xb, y0 + 8, y1 - 8, 540, 694))
    # bolster (with a raised bowl for the centre plate)
    m.add(f"truck_{tag}_side_frames", TRUCK, frames)
    m.add(f"truck_{tag}_bolster", TRUCK, box(xt - 230, xt + 230, -(YJ + 87), YJ + 87, 470, 700),
          cyl(220, (xt, 0, 680), (xt, 0, 708)))
    m.add(f"truck_{tag}_springs", DARK, springs)
    m.add(f"truck_{tag}_wedges", DARK, wedges)

    prof = [(0, 640), (130, 640), (300, 700), (410, 682), (R + 22, 682), (R + 28, 696), (R + 6, 718),
            (R, 735), (R - 6, 820), (390, 820), (300, 802), (135, 795), (0, 795)]
    for sx in (1, -1):
        xa = xt + sx * WB
        w = revolve_y(prof, xa, ZC)
        wheels += [w, w.mirror("XZ")]
        axles.append(cyl(95, (xa, -905, ZC), (xa, 905, ZC)))
        for sy in (1, -1):
            bearings.append(cyl(118, (xa, sy * 900, ZC), (xa, sy * 1082, ZC)))
            bearings.append(cyl(100, (xa, sy * 1078, ZC), (xa, sy * 1112, ZC)))
            y0, y1 = sorted((sy * (YJ - 58), sy * (YJ + 58)))
            bearings.append(box(xa - 122, xa + 122, y0, y1, 540, 612))           # adapter
            for k in range(3):
                a = math.radians(90 + 120 * k)
                p = (xa + 55 * math.cos(a), ZC + 55 * math.sin(a))
                bearings.append(cyl(m.r(17), (p[0], sy * 1108, p[1]), (p[0], sy * 1132, p[1])))
        # brake beam inboard of each wheelset, shoes on the treads
        xb = xt + sx * (WB - 509)
        brakes.append(bar((xb, -800, 440), (xb, 800, 440), 80, 80, up=(1, 0, 0)))
        brakes.append(box(xb - 25, xb + 25, -60, 60, 400, 520))                       # strut
        for sy in (1, -1):
            xs0, xs1 = sorted((xt + sx * (WB - 484), xt + sx * (WB - 432)))
            ya, yb = sorted((sy * 724, sy * 818))
            brakes.append(box(xs0, xs1, ya, yb, 340, 560))
            xh0, xh1 = sorted((xb - sx * 30, xt + sx * (WB - 470)))
            brakes.append(box(xh0, xh1, *sorted((sy * 735, sy * 810)), 395, 500))   # brake head
    # truck brake lever and connecting rod
    brakes.append(bar((xt - 380, 0, 500), (xt + 380, 0, 470), 60, m.t(30), up=(0, 1, 0)))
    m.add(f"truck_{tag}_wheels", WHEEL, wheels)
    m.add(f"truck_{tag}_axles", TRUCK, axles)
    m.add(f"truck_{tag}_bearings", STEEL, bearings)
    m.add(f"truck_{tag}_brake_rigging", TRUCK, brakes)


# --------------------------------------------------------------------------- couplers

def coupler(m, s):
    """E-type coupler, striker, uncoupling lever and air hose at the end s (+1 = B, rotary end)."""
    def X(x):
        return s * x

    def B(x0, x1, y0, y1, z0, z1):
        xa, xb = sorted((X(x0), X(x1)))
        ya, yb = sorted((s * y0, s * y1))
        return box(xa, xb, ya, yb, z0, z1)

    tag = "B" if s > 0 else "A"
    parts = [B(E + 150, E + 210, -240, 240, 730, 1030),                 # striker
             B(E + 100, E + 410, -105, 105, ZK - 90, ZK + 90),          # shank
             B(E + 390, E + 480, -190, 170, ZK - 160, ZK + 160),         # head
             B(E + 470, XCPL, 25, 175, ZK - 150, ZK + 150),              # knuckle
             B(E + 470, XCPL - 15, -195, -95, ZK - 150, ZK + 150),       # guard arm
             cyl(36, (X(E + 440), s * 125, ZK - 190), (X(E + 440), s * 125, ZK + 190))]   # knuckle pin
    m.add(f"coupler_{tag}", BLACK, parts)
    if s > 0:   # rotary coupler: swivel collar on the shank, painted red
        m.add("rotary_collar", ROTARY_RED, cyl(140, (X(E + 220), 0, ZK), (X(E + 330), 0, ZK)))
    # uncoupling lever: rod along the end sill to the corner, handle down at the side
    lv = m.r(18)
    xl = X(E + 260)
    m.add(f"uncoupling_lever_{tag}", BLACK,
          rod([(X(E + 420), s * 40, ZK + 165), (xl, s * 160, 1060), (xl, -s * 1380, 1060),
                (X(E + 320), -s * (YS + 30), 1060), (X(E + 320), -s * (YS + 30), 900)], lv),
          [B(E + 150, E + 280, y - 30, y + 30, 1020, 1090) for y in (-700, -1250)])
    # air hose: angle cock on the end sill, hose drooping to the glad hand
    hose = [(X(E + 180), s * 430, 990), (X(E + 280), s * 440, 860), (X(E + 360), s * 420, 720)]
    m.add(f"air_hose_{tag}", BLACK, rod(hose, m.r(30)), B(E + 330, E + 420, 380, 470, 680, 740),
          B(E + 150, E + 230, 390, 470, 960, 1040))


# --------------------------------------------------------------------------- brakes

def hand_brake(m):
    """Vertical hand-brake wheel on its geared housing at the B (+X) end, chain/staff to the sill."""
    yc, zc, xw = -730.0, 2130.0, E + 250
    m.add("brake_housing", BLACK, box(E - 5, E + 200, -900, -560, 1900, 2350),
          box(E - 5, E + 120, -930, -530, 2320, 2380))
    rw = m.t(30)
    rim = cyl(280 + rw / 2, (xw - 16, yc, zc), (xw + 16, yc, zc)).cut(
        cyl(280 - rw / 2, (xw - 20, yc, zc), (xw + 20, yc, zc)))
    spokes = [bar((xw, yc, zc), (xw, yc + 280 * math.cos(a), zc + 280 * math.sin(a)), 40, m.t(18),
                  up=(1, 0, 0)) for a in np.radians([45, 135, 225, 315])]
    m.add("brake_wheel", BLACK, rim, spokes, cyl(55, (E + 190, yc, zc), (xw + 25, yc, zc)))
    m.add("brake_staff", BLACK, cyl(m.r(20), (E + 120, -640, 1170), (E + 120, -640, 1910)),
          box(E + 90, E + 150, -670, -610, 1170, 1200))


def air_brake(m):
    """Air reservoir and control valve on the B end sheet, train line along the floor."""
    m.add("air_reservoir", BLACK, cyl(150, (E + 175, 80, 1480), (E + 175, 820, 1480)),
          [box(E - 5, E + 170, y - 30, y + 30, 1380, 1460) for y in (200, 700)])
    m.add("control_valve", BLACK, box(E - 5, E + 230, -330, -40, 1330, 1610),
          rod([(E + 140, -60, 1480), (E + 175, 80, 1480)], m.r(20)),
          rod([(E + 140, -200, 1330), (E + 140, -200, 1100), (E + 140, -40, 1000)], m.r(18)))
    line = [(x, -330, z - 40) for x, z in BOTTOM[1:-1]]
    line = [(-E - 180, -330, ZE - 40)] + line + [(E + 180, -330, ZE - 40)]
    m.add("train_line", BLACK, rod(line, m.r(24)))


# --------------------------------------------------------------------------- ladders, steps, grabs

def ladders_and_grabs(m):
    gr = m.r(14)
    rungs = []
    for s, ya, yb in ((1, 1000.0, 1400.0), (-1, -1400.0, -1000.0)):
        xa, xb = s * (E - 5), s * (E + 130)
        for z in (1400, 1820, 2240, 2660, 3080, 3500):
            rungs.append(rod([(xa, ya, z), (xb, ya, z), (xb, yb, z), (xa, yb, z)], gr, square=True))
    m.add("end_ladders", BLACK, rungs)
    steps, grabs = [], []
    for s in (1, -1):
        for sy in (1, -1):
            y = sy * (YS + 30)
            x0, x1 = s * (E - 330), s * (E - 90)
            steps.append(rod([(x0, y, 1180), (x0, y, 480), (x1, y, 480), (x1, y, 1180)], m.r(16), square=True))
            ya, yb = sy * (YS - 5), sy * (YP + 60)
            for z in (1400, 1800):
                grabs.append(rod([(s * (E - 470), ya, z), (s * (E - 470), yb, z),
                                   (s * (E - 130), yb, z), (s * (E - 130), ya, z)], gr, square=True))
    m.add("sill_steps", BLACK, steps)
    m.add("side_grabs", BLACK, grabs)
