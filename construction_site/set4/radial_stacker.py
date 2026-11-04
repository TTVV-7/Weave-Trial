"""Portable radial stacking conveyor, 36 in belt x 100 ft, raised to its working angle with the
undercarriage wheels swung out for radial travel.

A generic, brand-neutral stacker with the typical proportions of the 36 in x 100 ft class used to
build open stockpiles of coal, potash, aggregate and other dry bulk:

* conveyor: 30.48 m (100 ft) between the tail and head pulley centres, raised at 19 deg, so the
  discharge (top of the belt over the head pulley) is ~11.1 m above the ground; 914 mm (36 in)
  belt on 35 deg three-roll troughing idlers (5 in rolls) at 1.2 m centres, closer-spaced impact
  idlers under the feed boot, the return belt flat on 4.5 in return rolls hung inside the truss
  at 3 m centres; flat-to-trough transitions at both ends;
* truss: a box lattice truss 1.2 m wide between the chords (110 mm angle chords), 12 panels of
  ~2.2 m with verticals and Warren diagonals in the side faces and lateral bracing in the bottom
  plane; 1.7 m deep in the middle, tapering to ~0.65 m at the tail and ~0.75 m at the head;
* tail: a deep channel tail section on a swivelling pivot base (ground pan, pedestal and turntable)
  with a 20 in tail pulley on screw take-ups and red pinch-point guards; a ~3.6 m x 2.8 m feed
  hopper (top ~3.15 m above the ground) over a skirted feed boot with rubber skirt seals; a
  control cabinet with a beacon and a cable conduit running up the truss to the drive; a fleet
  number stencilled on the tail channel;
* head: side plates carrying pillow-block bearings, a 24 in lagged head pulley, a primary belt
  scraper, a curved discharge hood with two floodlights; a shaft-mounted reducer with a ~30 kW
  motor, V-belt drive under a red guard and a torque arm; a service platform with handrails
  under the drive;
* undercarriage at ~2/3 of the length from the tail: a 4.2 m axle beam on two swivel bogies,
  each with dual 11R22.5 tyres (1.05 m OD) turned 90 deg for radial travel round the pivot;
  two telescoping struts (pinned), two hydraulic lift rams and two drag braces up to saddles
  on the truss bottom chords.

Overall ~30.7 m long, ~5.0 m wide over the radially set tyres (3.7 m over the hopper flange) and
~11.5 m high over the floodlights; the belt over the head pulley is ~11.1 m above the ground.

Colours: yellow truss, hopper, hood and undercarriage; black belt, tyres and drive; galvanised
idlers, pulleys and running gear; red guards. It prints in Construction yellow, Black, Silver
grey and Signal red.

PRINT NOTE: at 1:50 the model is ~610 mm long and ~235 mm high, larger than most print beds;
print it at 1:100 or smaller, or split the truss at a panel point. Truss members, plates and
rods go through m.t()/m.r(), so nothing is under 0.8 mm at 1:50.

Millimetres, X forward (the head and discharge face +X), Y left, Z up, ground at Z = 0,
footprint roughly centred on the origin.
"""

from __future__ import annotations

import math

import cadquery as cq
import numpy as np

from cadkit import Finish, arc_pts, band, bar, box, cut, cyl, frustum, mv, place, prism, rgb, rot, sphere, text
from finishes import AMBER, BLACK, CHROME, DARK, GALV, LED, RED, RUBBER, STEEL, YELLOW

ASSET = dict(key="radial_stacker", stem="Radial_Stacking_Conveyor",
             title="Radial Stacking Conveyor (36 in x 100 ft)", az=40, el=15, size="1200x900")

PAINT = YELLOW
GUARD = RED
CABINET = Finish(rgb("#8f969d"), metal=0.3, rough=0.5)

# ---------------------------------------------------------------- conveyor geometry (mm)
A = 19.0                                  # working angle, degrees
CA, SA = math.cos(math.radians(A)), math.sin(math.radians(A))
L = 30480.0                               # tail to head pulley centres, 100 ft
X0, Z0 = -14450.0, 900.0                  # local origin: top-chord line over the tail pulley
YC = 600.0                                # chord centre lines, |Y|
WB = 260.0                                # belt mid-surface above the top-chord line
RT, RH = 250.0, 320.0                     # tail / head pulley radii (20 in, 24 in lagged)
RR, RRET = 64.0, 57.0                     # carry / return idler roll radii
FLAT, WING = 190.0, 267.0                 # belt flat half-width and wing length (914 mm belt)
C35, S35 = math.cos(math.radians(35)), math.sin(math.radians(35))

N = 12                                    # truss panels
S0, S1 = 3600.0, L - 900.0                # first / last panel point
NODES = [S0 + i * (S1 - S0) / N for i in range(N + 1)]
DEPTH = [min(1700.0, 650.0 + 500.0 * i, 750.0 + 480.0 * (N - i)) for i in range(N + 1)]
IU, ID = 8, 5                             # undercarriage strut node / drag-brace node


def W(s, y, w):
    """Conveyor coordinates (s along the belt from the tail pulley, y, w up off the truss) to world."""
    return (X0 + s * CA - w * SA, float(y), Z0 + s * SA + w * CA)


def tilt(sh):
    return mv(rot(sh, -A, (0, 1, 0)), X0, 0, Z0)


def lbox(s0, s1, y0, y1, w0, w1):
    return tilt(box(s0, s1, y0, y1, w0, w1))


def lcyl(r, s, w, y0, y1):
    """Cylinder across the conveyor (along Y) at (s, w)."""
    return cyl(r, W(s, y0, w), W(s, y1, w))


def lprism_sw(pts, y0, y1):
    return tilt(prism(pts, "y", y0, y1))


def lprism_yw(pts, s0, s1):
    return tilt(prism(pts, "x", s0, s1))


def ys(s, a, b):
    return tuple(sorted((s * a, s * b)))


def arc_band(cx, cz, r0, r1, a0, a1, n=24):
    return arc_pts(cx, cz, r1, a0, a1, n) + arc_pts(cx, cz, r0, a1, a0, n)


def rod(m, r, a, b, n=12):
    """A round bar from a to b: a true cylinder in the print, an n-sided prism in the display model
    (keeps the GLB light; there are a few hundred rolls, rails and nuts)."""
    if m.print_mode:
        return cyl(r, a, b)
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    ln = float(np.linalg.norm(d))
    z = d / ln
    x = np.cross(z, [1.0, 0, 0] if abs(z[0]) < 0.9 else [0, 1.0, 0])
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    pts = [(r * math.cos(2 * math.pi * (k + 0.5) / n), r * math.sin(2 * math.pi * (k + 0.5) / n)) for k in range(n)]
    return place(prism(pts, "z", 0, ln), tuple(x), tuple(y), tuple(z), tuple(a))


def tube(m, pts, r, n=12):
    """A bent pipe through pts: balls at the bends in the print, plain prisms in the display model."""
    out = [rod(m, r, a, b, n) for a, b in zip(pts, pts[1:])]
    if m.print_mode:
        out += [sphere(r, p) for p in pts[1:-1]]
    return out


def revolve_y(profile):
    return cq.Workplane("XY").polyline(profile).close().revolve(360, (0, 0, 0), (0, 1, 0)).val()


# ---------------------------------------------------------------- the belt line

def belt_th(m):
    return m.t(15)


def pulley_w(m, r):
    """Pulley centre (w) so its face just overlaps the underside of the flat belt."""
    return WB - belt_th(m) / 2 - r + 3


def ret_w(m, s):
    """Return-belt mid-surface (w) at s: straight under the two pulleys."""
    th = belt_th(m)
    wt = pulley_w(m, RT) - RT - th / 2 + 3
    wh = pulley_w(m, RH) - RH - th / 2 + 3
    return wt + (wh - wt) * s / L


def belt_section(m, troughed):
    th = belt_th(m)
    if troughed:
        ye, we = FLAT + WING * C35, WB + WING * S35
        path = [(-ye, we), (-FLAT, WB), (FLAT, WB), (ye, we)]
    else:
        path = [(-FLAT - WING, WB), (-FLAT, WB), (FLAT, WB), (FLAT + WING, WB)]
    return band(path, th / 2)


def wing_top(m, y):
    """Top surface (w) of the troughed belt at |y| on a wing."""
    a = (abs(y) - FLAT) / C35
    return WB + a * S35 + belt_th(m) / 2 / C35


# ================================================================ build

def build(m):
    pivot_base(m)
    tail(m)
    hopper(m)
    truss(m)
    belt(m)
    idlers(m)
    head(m)
    drive(m)
    platform(m)
    undercarriage(m)
    electrics(m)


# ---------------------------------------------------------------- pivot base

def pivot_base(m):
    xp = W(0, 0, -450)[0]
    m.add("ground_pan", GALV, box(xp - 1200, xp + 1200, -1200, 1200, -2, 45),
          [box(xp - 1150, xp + 1150, y - 40, y + 40, 30, 150) for y in (-700, 700)],
          [box(x - 40, x + 40, -1150, 1150, 30, 140) for x in (xp - 700, xp + 700)])
    m.add("ground_anchors", DARK, [cyl(55, (xp + sx * 1080, sy * 1080, 30), (xp + sx * 1080, sy * 1080, 110))
                                   for sx in (1, -1) for sy in (1, -1)])
    m.add("pivot_pedestal", PAINT, cyl(300, (xp, 0, 30), (xp, 0, 250)),
          [box(xp - 30, xp + 30, -560, 560, 40, 230), box(xp - 560, xp + 560, -30, 30, 40, 230)])
    m.add("turntable", DARK, cyl(520, (xp, 0, 230), (xp, 0, 300)), cyl(120, (xp, 0, 290), (xp, 0, 330)))

    # saddle between the turntable and the tail channels (top follows the channel slope)
    def zc(x):                                  # channel bottom line at world x
        s = (x - X0 - 450 * SA) / CA
        return Z0 + s * SA - 450 * CA
    xs0, xs1 = xp - 480, xp + 480
    m.add("pivot_saddle", PAINT, prism([(xs0, 285), (xs1, 285), (xs1, zc(xs1) + 70), (xs0, zc(xs0) + 70)],
                                       "y", -680, 680))


# ---------------------------------------------------------------- tail section

def tail(m):
    th = belt_th(m)
    m.add("tail_frame", PAINT, [lbox(-700, S0 + 300, *ys(s, 555, 645), -450, 120) for s in (1, -1)],
          lbox(-650, -500, -645, 645, -450, -300), lbox(S0 + 120, S0 + 280, -645, 645, -450, -300))
    wt = pulley_w(m, RT)
    m.add("tail_pulley", GALV, lcyl(RT, 0, wt, -520, 520),
          [lcyl(RT * 0.55, 0, wt, *ys(s, 515, 545)) for s in (1, -1)])
    m.add("tail_pulley_wrap", RUBBER, lcyl(RT + th - 6, 0, wt, -457, 457))
    m.add("tail_shaft", STEEL, lcyl(m.r(60), 0, wt, -820, 820))
    # screw take-ups on the channel faces, pillow blocks riding in them
    tk, scr = [], []
    for s in (1, -1):
        y0, y1 = ys(s, 640, 720)
        tk += [lbox(-650, 650, y0, y1, wt - 110, wt - 60), lbox(-650, 650, y0, y1, wt + 60, wt + 110)]
        tk.append(lbox(560, 640, y0, y1, wt - 110, wt + 110))
        scr.append(cyl(m.r(22), W(120, s * 680, wt), W(900, s * 680, wt)))
        scr.append(cyl(45, W(880, s * 680, wt), W(940, s * 680, wt)))
    m.add("take_up_frames", PAINT, tk)
    m.add("take_up_screws", STEEL, scr)
    m.add("tail_bearings", DARK, [lbox(-150, 150, *ys(s, 630, 790), wt - 70, wt + 70) for s in (1, -1)],
          [lcyl(105, 0, wt, *ys(s, 640, 800)) for s in (1, -1)])
    # pinch-point guards over the tail pulley ends, on stand-offs
    gt = m.t(10)
    gd = []
    for s in (1, -1):
        gd.append(lbox(-720, 520, *ys(s, 830, 830 + gt), wt - 330, wt + 260))
        gd += [lbox(sc - 40, sc + 40, *ys(s, 640, 840), wt + 150, wt + 230) for sc in (-560, 380)]
        gd += [lbox(sc - 40, sc + 40, *ys(s, 640, 840), wt - 300, wt - 220) for sc in (-560, 380)]
    m.add("tail_guards", GUARD, gd)


# ---------------------------------------------------------------- feed hopper and boot

SK0, SK1, HB1 = 900.0, 4300.0, 2400.0          # skirt start / end, hopper bottom end (along s)
HH, HW = 900.0, 1800.0                         # hopper height, top half-width


def hopper_levels(m):
    """World z of the hopper bottom, and the skirt-top line w(s) that meets it."""
    wsk = wing_top(m, 330) - 5
    zhb = Z0 + HB1 * SA + (wsk + 300) * CA - 60
    return zhb, (lambda s: (zhb + 60 - Z0 - s * SA) / CA), wsk


def hopper(m):
    ts = m.t(12)
    zhb, wtop, wsk = hopper_levels(m)
    zht = zhb + HH
    # skirt boards: bottom on the belt wings, top level with the hopper bottom, then down along the belt
    sk = [(SK0, wsk), (SK1, wsk), (SK1, wsk + 420), (HB1, wtop(HB1)), (SK0, wtop(SK0))]
    m.add("skirt_boards", PAINT, [lprism_sw(sk, *ys(s, 330, 330 + ts)) for s in (1, -1)],
          lbox(SK0 - ts, SK0 + 5, -330 - ts, 330 + ts, WB - 10, wtop(SK0)),
          [lbox(sc - 30, sc + 30, *ys(s, 330 + ts - 5, 330 + ts + 50), wsk + 60, wsk + 290)
           for s in (1, -1) for sc in (2900, 3600)])
    m.add("skirt_seals", RUBBER, [lbox(SK0 + 5, SK1, *ys(s, 330 - m.t(14), 333), wsk - 2, wsk + 140) for s in (1, -1)])

    # the hopper: a hollow pyramid frustum, level top, sloped walls
    xa, xb = W(SK0, 0, wtop(SK0))[0], W(HB1, 0, wtop(HB1))[0]
    hb = 340.0 + ts

    def rect(z, g):
        f = (z - zhb) / HH
        return (xa - 900 * f - g, xb + 450 * f + g, -(hb + (HW - hb) * f) - g, hb + (HW - hb) * f + g, z)
    shell = cut(frustum(rect(zhb, 0), rect(zht, 0)), frustum(rect(zhb - 2, -ts), rect(zht + 2, -ts)))
    bands = [cut(frustum(rect(z, 45), rect(z + 110, 45)), frustum(rect(z - 1, -5), rect(z + 111, -5)))
             for z in (zhb + 330,)]
    rim = cut(frustum(rect(zht - 110, 60), rect(zht + 15, 60)), frustum(rect(zht - 111, 3 - ts), rect(zht + 16, 3 - ts)))
    m.add("hopper", PAINT, shell, bands, rim)

    # posts from the tail channels up under the sloped side walls
    posts = []
    for s in (1, -1):
        for sc in (SK0 + 250, HB1 - 250):
            x = W(sc, 0, 120)[0]
            yc = 640.0
            zo = zhb + (yc - hb) / (HW - hb) * HH         # outer wall surface over the post centre
            zp = zo + 0.5 * ts * HH / (HW - hb)
            zbot = W(sc, 0, 60)[2]                         # inside the channel
            posts.append(box(x - 50, x + 50, *ys(s, yc - 45, yc + 45), zbot, zp))
    m.add("hopper_posts", PAINT, posts)

    # fleet number stencilled on the left (+Y) tail channel, under the hopper
    m.add("fleet_number", BLACK, text("RS 04", 280, m.t(10) + 3, W(1650, 645 - 3, -170), (-CA, 0, -SA), (0, 1, 0)))


# ---------------------------------------------------------------- truss

def truss(m):
    m.add("top_chords", PAINT, [lbox(S0 - 300, L + 150, *ys(s, 545, 655), -55, 55) for s in (1, -1)])
    bottom, joints, verts, diags, lats = [], [], [], [], []
    for s in (1, -1):
        y = s * YC
        for i in range(N):
            bottom.append(bar(W(NODES[i], y, -DEPTH[i]), W(NODES[i + 1], y, -DEPTH[i + 1]), 110, 110))
        for i in range(N + 1):
            joints.append(lbox(NODES[i] - 75, NODES[i] + 75, *ys(s, 540, 660), -DEPTH[i] - 62, -DEPTH[i] + 62))
            verts.append(bar(W(NODES[i], y, 0), W(NODES[i], y, -DEPTH[i]), 80, 80))
        for i in range(N):
            a, b = (W(NODES[i], y, 0), W(NODES[i + 1], y, -DEPTH[i + 1])) if i % 2 == 0 else \
                   (W(NODES[i], y, -DEPTH[i]), W(NODES[i + 1], y, 0))
            diags.append(bar(a, b, 60 if i % 2 else 66, 70))
    for i in range(N + 1):
        lats.append(lbox(NODES[i] - 35, NODES[i] + 35, -YC, YC, -DEPTH[i] - 35, -DEPTH[i] + 35))
        lats.append(lbox(NODES[i] - 30, NODES[i] + 30, -YC, YC, -30, 30))
    nrm = (-SA, 0, CA)
    for i in range(N):
        sg = 1 if i % 2 else -1
        lats.append(bar(W(NODES[i], -sg * YC, -DEPTH[i]), W(NODES[i + 1], sg * YC, -DEPTH[i + 1]), 56, 56, up=nrm))
    m.add("bottom_chords", PAINT, bottom, joints)
    m.add("truss_verticals", PAINT, verts)
    m.add("truss_diagonals", PAINT, diags)
    m.add("truss_bracing", PAINT, lats)


# ---------------------------------------------------------------- belt

def belt(m):
    th = belt_th(m)
    flat, trough = belt_section(m, False), belt_section(m, True)
    secs = [(0.0, flat), (300.0, flat), (1000.0, trough), (L - 1700, trough), (L - 700, flat), (L, flat)]
    wires = [cq.Wire.makePolygon([cq.Vector(s, y, w) for y, w in pts], close=True) for s, pts in secs]
    m.add("carry_belt", RUBBER, tilt(cq.Solid.makeLoft(wires, ruled=True)))
    wt, wh = ret_w(m, 0), ret_w(m, L)
    m.add("return_belt", RUBBER, lprism_sw([(0, wt - th / 2), (L, wh - th / 2), (L, wh + th / 2), (0, wt + th / 2)],
                                           -457, 457))


def idlers(m):
    th = belt_th(m)
    wc = WB - th / 2 + 3 - RR                      # centre-roll axis
    off = th / 2 - 3 + RR                          # wing-roll axis below the wing mid-line
    rs = m.r(12)
    bt = m.t(12)
    stations = [1150 + 360 * k for k in range(5)]                       # impact idlers under the boot
    stations += list(np.arange(3300, L - 1750, 1200))
    frames, rolls, impact = [], [], []
    for k, s in enumerate(stations):
        tgt = impact if k < 5 else rolls
        frames.append(lbox(s - 40, s + 40, -640, 640, 40, 100))
        tgt.append(rod(m, RR, W(s, -FLAT, wc), W(s, FLAT, wc), 14))
        if m.print_mode:
            tgt.append(lcyl(rs, s, wc, -FLAT - 25, FLAT + 25))
        for sg in (1, -1):
            frames.append(lbox(s - 30, s + 30, *ys(sg, 176, 176 + bt), 60, wc + 40))
            frames.append(lbox(s - 30, s + 30, *ys(sg, 540, 540 + bt), 60, 470))

            def wp(a):
                y = FLAT + a * C35 + off * S35
                w = WB + a * S35 - off * C35
                return W(s, sg * y, w)
            tgt.append(rod(m, RR, wp(10), wp(380), 14))
            tgt.append(rod(m, rs, wp(-60) if m.print_mode else wp(370), wp(440), 8))
    m.add("idler_frames", PAINT, frames)
    m.add("carry_idlers", GALV, rolls)
    m.add("impact_idlers", RUBBER, impact)

    # return rolls hung from the top chords
    ret, hang = [], []
    for s in np.arange(1800, L - 900, 3000):
        wr = ret_w(m, s) - th / 2 + 3 - RRET
        ret.append(rod(m, RRET, W(s, -515, wr), W(s, 515, wr), 14))
        ret.append(rod(m, rs, W(s, -570, wr), W(s, 570, wr), 8))
        for sg in (1, -1):
            hang.append(lbox(s - 30, s + 30, *ys(sg, 528, 528 + m.t(10)), wr - 40, -20))
    m.add("return_idlers", GALV, ret)
    m.add("return_hangers", PAINT, hang)


# ---------------------------------------------------------------- head

def head(m):
    th = belt_th(m)
    wh = pulley_w(m, RH)
    ht = m.t(8)
    r0 = RH + 330
    # head frame: deep side plates continuing the top chords out to the bearings
    plate = [(L - 1900, -110), (L + 250, -110), (L + 420, 0), (L + 420, 150), (L - 1900, 150)]
    m.add("head_plates", PAINT, [lprism_sw(plate, *ys(s, 608, 608 + m.t(16))) for s in (1, -1)],
          lbox(L - 1650, L - 1550, -620, 620, -110, -40),
          [bar(W(S1, s * YC, -DEPTH[N]), W(L - 300, s * 616, -80), 80, 80) for s in (1, -1)])
    m.add("head_pulley", GALV, lcyl(RH, L, wh, -525, 525),
          [lcyl(RH * 0.55, L, wh, *ys(s, 520, 560)) for s in (1, -1)])
    m.add("head_lagging", RUBBER, lcyl(RH + th - 6, L, wh, -457, 457))
    m.add("head_shaft", STEEL, lcyl(m.r(80), L, wh, -820, 1180))
    m.add("head_bearings", DARK, [lbox(L - 190, L + 190, *ys(s, 618, 760), wh - 120, wh + 60) for s in (1, -1)],
          [lcyl(125, L, wh, *ys(s, 625, 770)) for s in (1, -1)])

    # discharge hood: curved shell over the pulley, flat cover back over the transition
    a_top = math.degrees(math.asin(min(1.0, (540 - wh) / r0)))
    a_back = 180 - a_top
    shell = lprism_sw(arc_band(L, wh, r0, r0 + ht, -30, a_back, 28), -650, 650)
    sb = lprism_sw(arc_band(L, wh, RH + 70, r0 + ht, -30, a_back, 28), 604, 650)
    sb2 = mirror(sb)
    sback = [L - 1500, L + r0 * math.cos(math.radians(a_back)) + 30]
    rear = lbox(sback[0], sback[1], -650, 650, 540, 540 + ht)
    rear_sides = [lbox(sback[0], sback[1], *ys(s, 604, 650), 130, 545) for s in (1, -1)]
    m.add("hood", PAINT, shell, sb, sb2, rear, rear_sides)
    # rubber dust curtain at the hood mouth
    a = math.radians(-30)
    ce = (L + (r0 + ht / 2) * math.cos(a), wh + (r0 + ht / 2) * math.sin(a))
    m.add("dust_curtain", RUBBER, lprism_sw([(ce[0] - 25, ce[1] + 30), (ce[0] + m.t(12) - 25, ce[1] + 30),
                                             (ce[0] + m.t(12) + 60, ce[1] - 380), (ce[0] + 60, ce[1] - 380)],
                                            -630, 630))

    # primary belt scraper under the pulley
    a = math.radians(-55)
    rc = RH + 230
    sc = (L + rc * math.cos(a), wh + rc * math.sin(a))
    tip = (L + (RH + th - 10) * math.cos(math.radians(-35)), wh + (RH + th - 10) * math.sin(math.radians(-35)))
    m.add("belt_scraper", DARK, lcyl(60, sc[0], sc[1], -640, 640),
          lprism_sw(band([sc, tip], m.t(16) / 2), -440, 440))
    m.add("scraper_tensioners", RED, [lbox(sc[0] - 80, sc[0] + 80, *ys(s, 630, 700), sc[1] - 120, sc[1] + 80)
                                      for s in (1, -1)])
    m.add("scraper_arms", PAINT, [bar(W(L + 200, s * 616, -80), W(sc[0], s * 616, sc[1]), 70, 60) for s in (1, -1)])

    # floodlights on the hood, aimed down at the pile
    lamps, lens = [], []
    for y in (-420, 420):
        for ang in (55,):
            r = r0 + ht + 40
            c = W(L + r * math.cos(math.radians(ang)), y, wh + r * math.sin(math.radians(ang)))
            lamps.append(box(c[0] - 140, c[0] + 140, y - 160, y + 160, c[2] - 110, c[2] + 110))
            lens.append(box(c[0] + 136, c[0] + 140 + m.t(10), y - 135, y + 135, c[2] - 85, c[2] + 85))
    m.add("floodlights", DARK, lamps)
    m.add("floodlight_lenses", LED, lens)


def mirror(sh):
    return sh.mirror("XZ")


# ---------------------------------------------------------------- drive

def drive(m):
    wh = pulley_w(m, RH)
    m.add("reducer", DARK, lbox(L - 290, L + 270, 790, 1050, wh - 330, wh + 250),
          lcyl(200, L, wh, 780, 1060))
    sm, wm = L - 860, wh + 260
    m.add("motor", DARK, lcyl(225, sm, wm, 700, 1030), lcyl(205, sm, wm, 660, 705),
          [lbox(sm - 240, sm + 240, 720, 1010, wm + d - 18, wm + d + 18) for d in (-120, 0, 120)],
          lbox(sm - 120, sm + 120, 780, 950, wm + 200, wm + 310))
    m.add("motor_base", PAINT, lbox(sm - 300, sm + 300, 612, 1040, wm - 270, wm - 200),
          [lbox(sm + d - 40, sm + d + 40, 700, 1000, wm - 210, wm - 150) for d in (-170, 170)])
    # V-belt guard over the motor and reducer input pulleys
    gp = arc_pts(sm, wm, 200, 90, 270, 12) + arc_pts(L - 150, wh + 170, 170, -90, 90, 12)
    m.add("vbelt_guard", GUARD, lprism_sw(gp, 1025, 1025 + m.t(110)))
    # torque arm from the reducer back to a bracket on the head plate
    m.add("torque_arm", DARK, bar(W(L - 240, 900, wh - 290), W(L - 560, 680, -60), 70, 70),
          lbox(L - 640, L - 480, 612, 720, -110, -10))


# ---------------------------------------------------------------- head service platform

def platform(m):
    wh = pulley_w(m, RH)
    hz = W(L, 0, wh)[2]
    zp = hz - 1000
    xa, xb = W(L - 2300, 0, 0)[0], W(L + 150, 0, 0)[0]
    y0, y1 = 600.0, 1650.0
    m.add("platform_deck", GALV, box(xa, xb, y0, y1, zp - m.t(40), zp))
    if not m.print_mode:
        m.add("platform_grating", DARK, [box(x - 6, x + 6, y0 + 40, y1 - 40, zp - 1, zp + 3)
                                         for x in np.arange(xa + 80, xb - 40, 100)])
    # hangers down from the head plate, knee braces under the deck
    br = []
    for sc in (L - 1800, L - 250):
        top = W(sc, 0, 20)
        x = min(max(top[0], xa + 60), xb - 60)
        br.append(box(x - 45, x + 45, 612, 700, zp - 400, top[2]))
        br.append(bar((x, 660, zp - 370), (x, 1550, zp - 30), 70, 70))
        br.append(box(x - 40, x + 40, 610, 1600, zp - 120, zp - 20))
    m.add("platform_brackets", PAINT, br)
    # handrail round the outer edges, toe boards
    hr = m.r(24)
    zr1, zr2 = zp + 1070, zp + 550
    xe0, xe1, ye = xa + 40, xb - 40, y1 - 40
    rails = tube(m, [(xe0, y0 + 60, zr1), (xe0, ye, zr1), (xe1, ye, zr1), (xe1, y0 + 60, zr1)], hr)
    rails += tube(m, [(xe0, y0 + 60, zr2), (xe0, ye, zr2), (xe1, ye, zr2), (xe1, y0 + 60, zr2)], hr)
    posts = [(xe0, ye), (xe1, ye), (xe0, y0 + 60), (xe1, y0 + 60)] + \
        [(x, ye) for x in np.linspace(xe0, xe1, 4)[1:-1]]
    rails += [rod(m, hr, (x, y, zp - 10), (x, y, zr1 + (hr if m.print_mode else 0))) for x, y in posts]
    m.add("platform_handrail", PAINT, rails)
    tb = m.t(8)
    m.add("toe_boards", PAINT, box(xa, xb, y1 - tb, y1, zp - 10, zp + 120),
          box(xa, xa + tb, y0, y1, zp - 10, zp + 120), box(xb - tb, xb, y0, y1, zp - 10, zp + 120))


# ---------------------------------------------------------------- undercarriage

TR, TW = 527.0, 280.0                     # 11R22.5 tyre radius, width
ZW = TR * (1 - 0.015)                     # wheel centre: tyres sink 1.5 %
YB = 1950.0                               # bogie centres, |Y|
ZB0, ZB1 = 1250.0, 1520.0                 # axle-beam bottom / top


def tyre_shape(m):
    prof = [(282, -122), (300, -134), (380, -140), (470, -138), (505, -128), (520, -114), (TR, -100)]
    if m.print_mode:
        prof += [(TR, 100)]
    else:
        for y0, y1 in ((-72, -60), (-6, 6), (60, 72)):
            prof += [(TR, y0), (TR - 14, y0), (TR - 14, y1), (TR, y1)]
        prof += [(TR, 100)]
    prof += [(520, 114), (505, 128), (470, 138), (380, 140), (300, 134), (282, 122)]
    return rot(revolve_y(prof), 90, (0, 0, 1))          # axis along X


def undercarriage(m):
    xa = W(NODES[IU], 0, -DEPTH[IU])[0]
    # axle beam with strut and ram lugs
    m.add("axle_beam", PAINT, box(xa - 170, xa + 170, -YB - 150, YB + 150, ZB0, ZB1),
          [box(xa - 120, xa + 120, *ys(s, 1630, 1870), ZB1 - 20, ZB1 + 140) for s in (1, -1)],
          [box(xa + 150, xa + 520, *ys(s, 1490, 1610), ZB1 - 120, ZB1 + 90) for s in (1, -1)],
          [box(xa - 520, xa - 150, *ys(s, 1140, 1260), ZB1 - 120, ZB1 + 90) for s in (1, -1)])

    tyre = tyre_shape(m)
    tyres, rims, hubs, nuts, bogies, kp = [], [], [], [], [], []
    for s in (1, -1):
        yb = s * YB
        kp.append(cyl(210, (xa, yb, 1130), (xa, yb, ZB0 + 30)))
        kp.append(cyl(260, (xa, yb, 1180), (xa, yb, 1215)))
        bogies.append(box(xa - 640, xa + 640, yb - 150, yb + 150, 1080, 1160))
        ft = m.t(30)
        for sx in (1, -1):
            bogies.append(box(*sorted((xa + sx * 380, xa + sx * (380 + ft))), yb - 120, yb + 120, 420, 1100))
        hubs.append(cyl(60, (xa - 440, yb, ZW), (xa + 440, yb, ZW)))
        hubs.append(cyl(175, (xa - 80, yb, ZW), (xa + 80, yb, ZW)))
        for sx in (1, -1):
            xc = xa + sx * 185
            tyres.append(mv(tyre, xc, yb, ZW))
            rims.append(cyl(292, (xc - 118, yb, ZW), (xc + 118, yb, ZW)))
            xo = xc + sx * 118
            rims.append(cyl(130, (xo - sx * 2, yb, ZW), (xo + sx * 30, yb, ZW)))
            for k in range(10):
                a = 2 * math.pi * k / 10
                nuts.append(rod(m, m.r(20), (xo - sx * 3, yb + 200 * math.cos(a), ZW + 200 * math.sin(a)),
                                (xo + sx * 28, yb + 200 * math.cos(a), ZW + 200 * math.sin(a)), 6))
    m.add("kingpins", DARK, kp)
    m.add("bogie_frames", PAINT, bogies)
    m.add("tyres", RUBBER, tyres)
    m.add("rims", GALV, rims)
    m.add("wheel_hubs", DARK, hubs)
    m.add("wheel_nuts", STEEL, nuts)

    # saddles clamped round the bottom chords
    sad = []
    for i in (IU, ID):
        for s in (1, -1):
            sad.append(lbox(NODES[i] - 230, NODES[i] + 230, *ys(s, 515, 700), -DEPTH[i] - 190, -DEPTH[i] + 35))
    su = NODES[IU] + 600
    for s in (1, -1):
        sad.append(lbox(su - 150, su + 150, *ys(s, 560, 640), -DEPTH[IU] - 190, -DEPTH[IU]))
    m.add("strut_saddles", PAINT, sad)

    # telescoping struts: outer tube from the axle, inner tube up to the saddle, pinned
    outer, inner, pins, braces = [], [], [], []
    mids = []
    for s in (1, -1):
        a = np.array([xa, s * 1750, ZB1 + 60])
        b = np.array(W(NODES[IU], s * YC, -DEPTH[IU] - 120))
        d = b - a
        outer.append(bar(tuple(a), tuple(a + 0.58 * d), 260, 260, up=(1, 0, 0)))
        outer.append(bar(tuple(a + 0.555 * d), tuple(a + 0.585 * d), 320, 320, up=(1, 0, 0)))   # collar
        inner.append(bar(tuple(a + 0.45 * d), tuple(b), 200, 200, up=(1, 0, 0)))
        p = a + 0.57 * d
        pins.append(cyl(m.r(38), (p[0] - 230, p[1], p[2]), (p[0] + 230, p[1], p[2])))
        q = a + 0.85 * d
        pins.append(cyl(m.r(32), (q[0] - 150, q[1], q[2]), (q[0] + 150, q[1], q[2])))
        mids.append(a + 0.35 * d)
        # drag brace back to the node at the middle of the truss
        braces.append(bar((xa - 330, s * 1200, ZB1 + 10), W(NODES[ID], s * YC, -DEPTH[ID] - 120), 170, 170))
    braces.append(bar(tuple(mids[0]), tuple(mids[1]), 160, 160, up=(1, 0, 0)))
    braces.append(bar(tuple(mids[0]), (xa, -1700, ZB1 + 60), 120, 120, up=(1, 0, 0)))
    m.add("strut_outer_tubes", PAINT, outer, braces)
    m.add("strut_inner_tubes", GALV, inner)
    m.add("strut_pins", STEEL, pins)

    # hydraulic lift rams beside the struts
    barrels, rods = [], []
    for s in (1, -1):
        a = (xa + 340, s * 1550, ZB1 + 20)
        b = W(su, s * YC, -DEPTH[IU] - 120)
        a, b = np.asarray(a, float), np.asarray(b, float)
        j = a + 0.52 * (b - a)
        u = (b - a) / np.linalg.norm(b - a)
        barrels += [rod(m, 105, tuple(a), tuple(j), 16), rod(m, 118, tuple(j - 90 * u), tuple(j), 16),
                    rod(m, 85, tuple(a - [110, 0, 0]), tuple(a + [110, 0, 0]), 12)]
        rods += [rod(m, 62, tuple(j - 40 * u), tuple(b), 12),
                 rod(m, 70, tuple(b - [100, 0, 0]), tuple(b + [100, 0, 0]), 12)]
    m.add("lift_ram_barrels", BLACK, barrels)
    m.add("lift_ram_rods", CHROME, rods)
    # hoses from the beam to the rams
    hoses = []
    for s in (1, -1):
        hoses += tube(m, [(xa + 230, s * 1350, ZB1 - 10), (xa + 300, s * 1450, ZB1 + 400), (xa + 360, s * 1495, ZB1 + 700)],
                      m.r(18))
    m.add("ram_hoses", BLACK, hoses)


# ---------------------------------------------------------------- electrics

def electrics(m):
    # control cabinet on the left tail channel, beacon on top
    s0 = S0 - 400
    x0 = W(s0, 0, 0)[0]
    zc0 = W(s0, 0, -300)[2] - 150
    m.add("cabinet_bracket", PAINT, box(x0 - 260, x0 + 260, 630, 760, zc0 + 120, zc0 + 360),
          bar(W(s0 + 200, 640, -380), (x0 + 200, 700, zc0 + 40), 60, 60))
    m.add("control_cabinet", CABINET, box(x0 - 350, x0 + 350, 740, 1160, zc0, zc0 + 1000),
          box(x0 - 380, x0 + 380, 720, 1180, zc0 + 1000, zc0 + 1040))
    m.add("cabinet_trim", BLACK, box(x0 - 330, x0 + 330, 1158, 1158 + m.t(6), zc0 + 980, zc0 + 990),
          [box(x0 + 260, x0 + 290, 1155, 1190, z, z + 120) for z in (zc0 + 420,)],
          box(x0 - 2, x0 + 2, 1155, 1162, zc0 + 20, zc0 + 960) if not m.print_mode else None)
    m.add("estop", RED, cyl(45, (x0 - 200, 1155, zc0 + 760), (x0 - 200, 1205, zc0 + 760)))
    m.add("beacon_base", BLACK, cyl(80, (x0 + 150, 950, zc0 + 1030), (x0 + 150, 950, zc0 + 1080)))
    m.add("beacon", AMBER, cyl(65, (x0 + 150, 950, zc0 + 1075), (x0 + 150, 950, zc0 + 1200)),
          sphere(65, (x0 + 150, 950, zc0 + 1200)))
    # conduit up the left top chord to the motor
    rc = m.r(35)
    wh = pulley_w(m, RH)
    run = [(x0 - 150, 950, zc0 + 1020), (x0 - 150, 950, zc0 + 1200), W(S0 - 150, 680, 60),
           W(L - 1250, 680, 60), W(L - 1000, 900, wh + 200)]
    m.add("conduit", BLACK, tube(m, run, rc))
    m.add("conduit_clips", DARK, [lbox(s - 40, s + 40, 640, 740, 20, 110) for s in np.arange(S0 + 600, L - 1500, 2400)])
