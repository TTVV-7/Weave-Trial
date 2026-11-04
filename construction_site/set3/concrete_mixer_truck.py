"""Transit concrete mixer truck, 8 m3 (10 yd3) drum, on a 3-axle 6x4 cab-over chassis.

A generic, brand-neutral truck with the typical proportions of the class:

* chassis: 6x4, front steer axle under the cab, tandem drive bogie, 3900 + 1350 mm wheelbase,
  315/80R22.5 tyres (~1.05 m OD) on 22.5 in steel disc wheels, singles in front, duals behind,
  2.5 m over the tyres, frame rails ~0.86 m wide with the top at ~1.06 m;
* cab: flat-fronted cab-over day cab, 2.4 m wide, ~1.85 m long, roof at ~3.03 m, with a plain
  slatted grille (no badge), steel bumper with lamps, windscreen, door windows, wipers, sun
  visor with marker lamps, beacon, main/wide-angle and kerb mirrors, entry steps ahead of the
  front wheel, grab handles and an air-intake snorkel;
* mixer: a pear-shaped double-cone drum of ~14.8 m3 geometric volume (8 m3 / 10 yd3 rated),
  2.3 m in diameter and 5.0 m long, its axis tilted 13 deg (front low): a spline profile
  revolved about the axis, painted in diagonal orange/white bands; gearbox and hydraulic motor
  on the front pedestal, roller track ring on two support rollers on the rear pedestal, a recessed
  drum mouth showing the ends of the two spiral blades, charge hopper above it (top at ~4.0 m)
  with its spout running into the mouth, collection hopper and folding discharge chute (main
  chute hanging in the transit position with the extension folded back over it on its hinge,
  lift cylinder) below, access ladder with a platform and handrails, ~800 l water tank across the frame behind
  the cab with a supply pipe to the hopper, hydraulic oil tank, drum controls, two spare
  extension chutes on a rack above the left mudguards;
* running gear details: leaf-sprung front axle, leaf-spring tandem bogie with trunnion,
  differentials and prop shafts, rear mudguards and mud flaps, fuel tank (left), battery box and
  air tanks (right), side guards, rear under-run bar with lamps.

Overall ~9.45 m long (bumper to the stowed chute), 2.5 m wide over the tyres (~3.07 m over the
mirrors), ~4.0 m high to the top of the charge hopper.

Millimetres, X forward, Y left, Z up, ground at Z = 0, X = 0 at the front axle.
"""

from __future__ import annotations

import math

import cadquery as cq
import numpy as np

from cadkit import (V, Finish, arc_pts, band, bar, box, clip_poly, cone, cut, cyl, frustum, pipe, place, prism,
                    ram, rgb, rot, rounded_box, sphere, torus, wheel_lugs)
from finishes import AMBER, BLACK, CHROME, DARK, GALV, GLASS, LED, ORANGE, RED, RUBBER, STEEL, WHITE

ASSET = dict(key="concrete_mixer_truck", stem="Concrete_Mixer_Truck_8m3",
             title="Concrete Mixer Truck (8 m³ / 10 yd³)", az=40, el=18, size="1200x900")

WHEEL = Finish(rgb("#c9cdd1"), metal=0.5, rough=0.4)      # painted steel disc wheels
GREY = Finish(rgb("#6c7177"), metal=0.2, rough=0.5)       # bumper, grille slats
CHUTE = Finish(rgb("#6f757b"), metal=0.3, rough=0.6)      # worn grey steel chutes
MOUTH = Finish(rgb("#232528"), rough=0.85)                # the shadowed inside of the drum mouth
DRUM_A, DRUM_B = WHITE, ORANGE

# ---- running gear
R = 525.0                       # 315/80R22.5, ~1,050 mm OD
ZC = R * (1 - 0.015)            # axle height: tyres sunk 1.5 % for a flat print contact
XR1, XR2 = -3900.0, -5250.0     # tandem drive axles
XRB = (XR1 + XR2) / 2           # bogie trunnion
F_IN, F_OUT = 935.0, 1250.0     # front tyre faces, |y|
DI, DO = (630.0, 925.0), (955.0, 1250.0)   # rear duals, inner / outer tyre faces, |y|

# ---- frame
RY0, RY1, RZ0, RZ1 = 345.0, 435.0, 760.0, 1060.0     # frame rails
SZ1 = 1220.0                                          # top of the mixer subframe
XFR, XRR = 1300.0, -6760.0                            # frame ends

# ---- cab: plan sections (z, front x, half width, front corner r, rear x, rear corner r)
CAB = [(880, 1450, 1200, 170, -380, 50), (1700, 1432, 1200, 170, -380, 50), (2650, 1322, 1190, 160, -380, 50),
       (2880, 1290, 1170, 150, -375, 50), (3000, 1220, 1110, 110, -340, 50), (3030, 1120, 1020, 60, -270, 40)]
CAB_IN = [(1130, 1385, 1150, 130, -330, 20), (1700, 1382, 1150, 130, -330, 20), (2650, 1272, 1140, 120, -330, 20),
          (2900, 1222, 1110, 100, -320, 20)]
WS_Z0, WS_Z1, WS_Y = 1740.0, 2610.0, 1010.0          # windscreen opening

# ---- drum
TH = math.radians(13.0)
U = np.array([-math.cos(TH), 0.0, math.sin(TH)])     # along the drum axis, front (low) to rear (high)
N = np.array([math.sin(TH), 0.0, math.cos(TH)])      # square to it, upwards
Y = np.array([0.0, 1.0, 0.0])
DF = np.array([-1920.0, 0.0, 2170.0])                # centre of the drum's front head
PROFILE = [(0, 560), (230, 760), (650, 1010), (1150, 1145), (1800, 1160), (2450, 1145), (3100, 1040),
           (3800, 850), (4500, 610), (4860, 470), (5000, 440)]
S_RING, R_RING, R_ROLL = 3100.0, 1100.0, 170.0       # roller track and support rollers


def xfr(z):
    """Cab front face (on the centre line) at height z."""
    zs, xs = zip(*[(c[0], c[1]) for c in CAB])
    return float(np.interp(z, zs, xs))


def hw(z):
    """Cab half width at height z."""
    zs, ys = zip(*[(c[0], c[2]) for c in CAB])
    return float(np.interp(z, zs, ys))


def DP(s, dy=0.0, dn=0.0):
    """Point on the drum axis s mm from the front head, dy to the left, dn square to the axis (up)."""
    return tuple(float(v) for v in DF + s * U + dn * N + dy * Y)


def ring_pt(s, r, a):
    """Point at radius r round the drum axis, angle a (deg) from 'up' towards +Y."""
    a = math.radians(a)
    return DP(s, r * math.sin(a), r * math.cos(a))


S_MOUTH, R_MOUTH = 4860.0, 405.0                     # floor and radius of the recessed drum mouth


def drum_solid(cones=False):
    """The drum: a spline profile through PROFILE, revolved about the tilted axis, its mouth recessed.

    With cones=True it comes as a chain of short cones sampled off the same spline, which the
    print exporter tessellates into fine regular rings instead of a few coarse bands."""
    pts = [V(*DP(s, dn=r)) for s, r in PROFILE]
    spline = cq.Edge.makeSpline(pts)
    mouth = cyl(R_MOUTH, DP(S_MOUTH), DP(PROFILE[-1][0] + 100))
    if cones:
        sr = []
        for t in np.linspace(0, 1, 41):
            p = np.array(spline.positionAt(t).toTuple()) - DF
            sr.append((float(p @ U), float(p @ N)))
        return [cut(cone(r0, r1, DP(s0 - 1), DP(s1 + 1)), mouth) if s1 + 1 > S_MOUTH
                else cone(r0, r1, DP(s0 - 1), DP(s1 + 1)) for (s0, r0), (s1, r1) in zip(sr, sr[1:])]
    a0, a1 = V(*DP(0)), V(*DP(PROFILE[-1][0]))
    wire = cq.Wire.assembleEdges([cq.Edge.makeLine(a0, pts[0]), spline,
                                  cq.Edge.makeLine(pts[-1], a1), cq.Edge.makeLine(a1, a0)])
    return cut(cq.Solid.revolve(cq.Face.makeFromWires(wire), 360, a0, a1), mouth)


def rrect(x0, x1, hy, rf, rr, z, n=6):
    """Plan of a box with rounded corners at height z, as 3-D points, anticlockwise."""
    pts = (arc_pts(x1 - rf, hy - rf, rf, 0, 90, n) + arc_pts(x0 + rr, hy - rr, rr, 90, 180, n)
           + arc_pts(x0 + rr, -hy + rr, rr, 180, 270, n) + arc_pts(x1 - rf, -hy + rf, rf, 270, 360, n))
    return [V(x, y, z) for x, y in pts]


def loft_sections(secs):
    wires = [cq.Wire.makePolygon(rrect(x0, x1, hy, rf, rr, z), close=True) for z, x1, hy, rf, x0, rr in secs]
    return cq.Solid.makeLoft(wires, ruled=True)


def side_bar(m, x0, z0, x1, z1, s, w, h):
    """A strip lying on the cab side between (x0, z0) and (x1, z1), standing h/2 proud of it."""
    return bar((x0, s * hw(z0), z0), (x1, s * hw(z1), z1), w, h, up=(0, s, 0))


def hollow_frustum(bot, top, t):
    x0, x1, y0, y1, z0 = bot
    X0, X1, Y0, Y1, Z1 = top
    dz = 1.0 if Z1 > z0 else -1.0
    inner = frustum((x0 + t, x1 - t, y0 + t, y1 - t, z0 - dz), (X0 + t, X1 - t, Y0 + t, Y1 - t, Z1 + dz))
    return cut(frustum(bot, top), inner)


# =============================================================================== wheels

def wheel(m, xc, s, y_in, y_out, tag, kind):
    """kind 'steer' (rib tread, rim), 'outer' (drive tread, rim) or 'inner' (drive tread, no rim)."""
    def c(y):
        return (xc, s * y, ZC)
    D = 16.0
    body = cyl(R - D, c(y_in + 30), c(y_out - 30)).fuse(
        cone(R - D - 50, R - D, c(y_in), c(y_in + 30)), cone(R - D, R - D - 50, c(y_out - 30), c(y_out)))
    if kind != "inner":
        body = cut(body, cyl(292, c(y_out + 5), c(y_out - 130)))
    if kind == "steer":
        w = (y_out - y_in - 60 - 3 * 12) / 4
        tread = []
        for k in range(4):
            a, b = y_in + 30 + k * (w + 12), y_in + 30 + k * (w + 12) + w
            tread.append(cut(cyl(R, c(a), c(b)), cyl(R - D - 6, c(a - 1), c(b + 1))))
    else:
        y0, y1 = sorted((s * (y_in + 28), s * (y_out - 28)))
        tread = wheel_lugs(xc, ZC, R, D + 4, y0, y1, 40, 64, 0.12)
    m.add(f"tyre_{tag}", RUBBER, body, tread)
    if kind == "inner":
        return
    yf = y_out
    rim = cut(cyl(300, c(yf - 135), c(yf - 8)), cyl(300 - m.t(24), c(yf - 100), c(yf + 1)))
    if not m.print_mode:                      # hand holes, through to the dark tyre bore behind
        holes = []
        for a in np.linspace(0, 2 * math.pi, 10, endpoint=False):
            x, z = xc + 205 * math.cos(a), ZC + 205 * math.sin(a)
            holes.append(cyl(36, (x, s * (yf - 98), z), (x, s * (yf - 140), z)))
        rim = cut(rim, *holes)
    m.add(f"rim_{tag}", WHEEL, rim)
    hub = 70.0 if kind == "steer" else 45.0
    m.add(f"hub_{tag}", DARK, cyl(130, c(yf - 101), c(yf - 101 + hub)),
          cone(118, 60, c(yf - 101 + hub), c(yf - 101 + hub + 35)))
    nuts = []
    for a in np.linspace(0, 2 * math.pi, 10, endpoint=False):
        x, z = xc + 168 * math.cos(a), ZC + 168 * math.sin(a)
        nuts.append(cyl(m.r(19), (x, s * (yf - 102), z), (x, s * (yf - 68), z)))
    m.add(f"wheel_nuts_{tag}", STEEL, nuts)


# =============================================================================== build

def build(m):
    hr = m.r(18)

    # =========================================================== running gear
    for s, side in ((1, "L"), (-1, "R")):
        wheel(m, 0.0, s, F_IN, F_OUT, f"front_{side}", "steer")
        for xc, tag in ((XR1, "drive1"), (XR2, "drive2")):
            wheel(m, xc, s, *DI, f"{tag}_{side}_inner", "inner")
            wheel(m, xc, s, *DO, f"{tag}_{side}_outer", "outer")

    # front axle: dropped beam, kingpins, tie rod, leaf springs
    fa = [box(-70, 70, -880, 880, 430, 560)]
    fa += [cyl(90, (0, s * 860, 410), (0, s * 860, 640)) for s in (1, -1)]
    fa += [cyl(165, (0, s * 830, ZC), (0, s * 950, ZC)) for s in (1, -1)]
    fa += [bar((0, s * 850, 470), (-280, s * 790, 470), 50, 50) for s in (1, -1)]
    m.add("front_axle", DARK, fa)
    m.add("tie_rod", BLACK, cyl(m.r(28), (-280, -800, 470), (-280, 800, 470)))
    springs, hangers = [], []
    for s in (1, -1):
        y0, y1 = sorted((s * 440, s * 530))
        springs.append(prism(band([(-760, 720), (-380, 625), (0, 595), (380, 625), (760, 720)], 38), "y", y0, y1))
        hangers += [box(x - 55, x + 55, s * 425, s * 545, 680, 790) for x in (-760, 760)]
        hangers.append(box(-110, 110, s * 425, s * 545, 545, 580))
        hangers += [cyl(m.r(16), (x, s * 485, 520), (x, s * 485, 640)) for x in (-85, 85)]
    m.add("front_springs", BLACK, springs)
    m.add("spring_hangers", DARK, hangers)

    # tandem drive axles, bogie with leaf springs, prop shafts
    axles = []
    for x in (XR1, XR2):
        axles += [cyl(140, (x, -600, ZC), (x, 600, ZC)), sphere(270, (x, 0, ZC)),
                  cyl(150, (x, 0, ZC), (x + 360, 0, ZC + 40))]
        axles += [cyl(230, (x, s * 560, ZC), (x, s * 1140, ZC)) for s in (1, -1)]
    m.add("drive_axles", DARK, axles)
    bogie = []
    for s in (1, -1):
        y0, y1 = sorted((s * 465, s * 575))
        bogie.append(prism(band([(XR1 + 60, ZC + 175), (XRB, 830), (XR2 - 60, ZC + 175)], [45, 70, 45]), "y", y0, y1))
        bogie += [box(x - 120, x + 120, s * 455, s * 585, ZC + 110, ZC + 165) for x in (XR1, XR2)]
        bogie.append(box(XRB - 170, XRB + 170, s * 425, s * 600, 700, 1060))
        bogie += [bar((XRB, s * 520, 690), (x, s * 520, ZC - 40), 70, 70, up=(0, 1, 0)) for x in (XR1 + 250, XR2 - 250)]
    m.add("bogie_springs", BLACK, bogie)
    m.add("bogie_trunnion", STEEL, cyl(95, (XRB, -640, 830), (XRB, 640, 830)))
    m.add("prop_shafts", DARK, cyl(m.r(55), (-950, 0, 720), (XR1 + 360, 0, ZC + 40)),
          cyl(m.r(50), (XR1 - 150, 0, ZC + 60), (XR2 + 360, 0, ZC + 40)),
          [sphere(m.r(70), p) for p in ((-950, 0, 720), (XR1 + 360, 0, ZC + 40), (XR2 + 360, 0, ZC + 40))])

    # =========================================================== frame
    rails = [box(XRR, XFR, s * RY0, s * RY1, RZ0, RZ1) for s in (1, -1)]
    rails += [box(x - 40, x + 40, -RY1, RY1, RZ0 + 40, RZ1 - 40) for x in (XFR - 40, -1300, -2900, XRB, -6000)]
    rails.append(box(XRR, XRR + 60, -RY1, RY1, RZ0, RZ1))
    m.add("frame_rails", BLACK, rails)
    m.add("mixer_subframe", BLACK, [box(XRR, -1950, s * RY0, s * RY1, RZ1 - 5, SZ1) for s in (1, -1)])
    m.add("engine", DARK, box(-380, 950, -360, 360, 480, 1100), box(-960, -370, -260, 260, 560, 960))

    # =========================================================== cab
    shell = loft_sections(CAB)
    arch = [cyl(650, (0, s * 700, ZC), (0, s * 1400, ZC)) for s in (1, -1)]
    if m.print_mode:
        shell = cut(shell, *arch)
    else:
        win = [prism([(380, 1880), (xfr(1880) - 230, 1880), (xfr(2600) - 230, 2600), (380, 2600)], "y",
                     s * 1080, s * 1300) for s in (1, -1)]
        ws = box(1150, 1600, -WS_Y, WS_Y, WS_Z0, WS_Z1)
        shell = cut(shell, loft_sections(CAB_IN), *arch, *win, ws)
    m.add("cab", WHITE, shell)

    # arch trim and liners
    for s in (1, -1):
        y0, y1 = sorted((s * 1150, s * 1215))
        m.add("front_fender", BLACK, prism(band(arc_pts(0, ZC, 680, 14, 166, 28), 30), "y", y0, y1))
        y0, y1 = sorted((s * 700, s * 1180))
        m.add("arch_liner", BLACK, prism(band(arc_pts(0, ZC, 650, 18, 162, 24), m.t(16) / 2), "y", y0, y1))
        wall = clip_poly(arc_pts(0, ZC, 655, 0, 180, 24), -700, 700, 880, 2000)
        y0, y1 = sorted((s * 692, s * 712))
        m.add("arch_liner", BLACK, prism(wall, "y", y0, y1))

    # windscreen, its rubber, wipers
    d = np.array([xfr(WS_Z1) - xfr(WS_Z0), 0.0, WS_Z1 - WS_Z0])
    d /= np.linalg.norm(d)
    nrm = (float(d[2]), 0.0, float(-d[0]))                 # out of the windscreen
    g = m.t(12)
    zg0, zg1 = WS_Z0 - 15, WS_Z1 + 15
    m.add("windscreen", GLASS, bar((xfr(zg0), 0, zg0), (xfr(zg1), 0, zg1), 2 * (WS_Y + 25), g, up=nrm))
    fr = m.t(18)
    frame = [bar((xfr(z), -WS_Y - 40, z), (xfr(z), WS_Y + 40, z), 50, fr, up=nrm) for z in (WS_Z0 - 10, WS_Z1 + 10)]
    frame += [bar((xfr(WS_Z0 - 30), y, WS_Z0 - 30), (xfr(WS_Z1 + 30), y, WS_Z1 + 30), 50, fr, up=nrm)
              for y in (-WS_Y - 15, WS_Y + 15)]
    m.add("windscreen_rubber", BLACK, frame)
    wipers = []
    for y0, y1 in ((960.0, 140.0), (-80.0, -900.0)):
        za, zb = WS_Z0 + 25, WS_Z0 + 55
        o = np.array(nrm) * (g / 2 + 6)
        wipers.append(bar(np.array((xfr(za), y0, za)) + o, np.array((xfr(zb), y1, zb)) + o, m.t(22), m.t(16), up=nrm))
        wipers.append(cyl(m.r(22), np.array((xfr(za), y0, za)) - o, np.array((xfr(za), y0, za)) + 1.6 * o))
    m.add("wipers", BLACK, wipers)

    # door windows with rubbers, door seams, handles
    for s in (1, -1):
        def xw(z):
            return xfr(z) - 230
        pane = [(360, 1860), (xw(1860) + 20, 1860), (xw(2620) + 20, 2620), (360, 2620)]
        y0, y1 = sorted((s * 1182, s * (1182 + max(m.t(22), 22))))
        m.add("door_glass", GLASS, prism(pane, "y", y0, y1))
        fr = m.t(14)
        rub = [side_bar(m, 360, 1880, xw(1880), 1880, s, 44, fr), side_bar(m, 360, 2600, xw(2600), 2600, s, 44, fr),
               side_bar(m, 380, 1860, 380, 2620, s, 44, fr), side_bar(m, xw(1860), 1860, xw(2620), 2620, s, 44, fr)]
        m.add("door_rubber", BLACK, rub)
        # door seams, in pieces between the cab's loft sections so they follow the panel
        sw, sh = m.t(14), m.t(20)
        zk = (1130.0, 1700.0, 2650.0, 2700.0)

        def xd(z):                            # the door's front edge
            return float(np.interp(z, (1130.0, 2700.0), (xfr(1130) - 190, xfr(2700) - 180)))
        seams = [side_bar(m, 330, z0, 330, z1, s, sw, sh) for z0, z1 in zip(zk, zk[1:])]
        seams += [side_bar(m, xd(z0), z0, xd(z1), z1, s, sw, sh) for z0, z1 in zip(zk, zk[1:])]
        seams.append(side_bar(m, 330 - sw / 2, 1130, xd(1130) + sw / 2, 1130, s, sw, sh))
        m.add("door_seams", BLACK, seams)
        m.add("door_handle", CHROME, side_bar(m, 420, 1700, 560, 1700, s, 40, m.t(24)))
        m.add("door_hinges", BLACK, [side_bar(m, xfr(z) - 200, z, xfr(z) - 160, z, s, 100, m.t(30))
                                     for z in (1350, 2350)])
        # grab handles on the A-pillar and behind the door
        ya = s * (hw(1500) - 5)
        yb = s * (hw(1500) + 55)
        m.add("grab_handles", CHROME, pipe([(xfr(1300) - 120, ya, 1300), (xfr(1300) - 120, yb, 1300),
                                            (xfr(2200) - 120, yb, 2200), (xfr(2200) - 120, ya, 2200)], hr),
              pipe([(250, ya, 1350), (250, yb, 1350), (250, yb, 2300), (250, ya, 2300)], hr))
        m.add("cab_side_vent", BLACK, side_bar(m, -200, 2050, 180, 2050, s, 520, m.t(10)))
        m.add("cab_side_vent_slats", GREY, [side_bar(m, -170, z, 150, z, s, 26, m.t(18)) for z in range(1840, 2280, 62)])
        m.add("side_repeater", AMBER, side_bar(m, 1180, 1250, 1290, 1250, s, 45, m.t(16)))
        # entry steps ahead of the front wheel
        y0, y1 = sorted((s * 960, s * 1205))
        m.add("step_frame", DARK, box(760, 760 + m.t(35), y0, y1, 400, 900), box(1300 - m.t(35), 1300, y0, y1, 400, 900),
              box(760, 1300, *sorted((s * 960, s * (960 + m.t(35)))), 400, 900))
        y0, y1 = sorted((s * 980, s * 1218))
        m.add("step_treads", GALV, box(790, 1270, y0, y1, 420, 460), box(790, 1270, y0, y1, 760, 800))

    # interior
    if not m.print_mode:
        m.add("dash", DARK, box(1130, 1390, -1145, 1145, 1120, 1720), box(-340, 1150, -340, 340, 1120, 1420))
        m.add("seats", BLACK, [box(250, 760, y - 260, y + 260, 1120, 1580) for y in (600.0, -600.0)],
              [box(150, 300, y - 260, y + 260, 1550, 2300) for y in (600.0, -600.0)])
        m.add("steering_wheel", BLACK, torus(220, m.r(22), (1000, 600, 2000), (1, 0, 0.45)),
              cyl(m.r(35), (1000, 600, 2000), (1250, 600, 1700)))

    # front: grille, bumper, lamps, visor, mirrors
    m.add("grille", BLACK, bar((xfr(1060), 0, 1060), (xfr(1620), 0, 1620), 1700, m.t(24), up=(1, 0, 0)))
    m.add("grille_slats", GREY, [box(xfr(z) + 6, xfr(z) + 6 + m.t(14), -800, 800, z - 20, z + 20)
                                 for z in np.arange(1120, 1600, 78)])
    m.add("bumper", GREY, rounded_box(1370, 1545, -1215, 1215, 440, 905, 40))
    m.add("bumper_valance", BLACK, rounded_box(1380, 1535, -1185, 1185, 360, 470, 25))
    m.add("bumper_steps", GALV, [box(1455, 1548, *sorted((s * 250, s * 700)), 898, 916) for s in (1, -1)])
    for s in (1, -1):
        y0, y1 = sorted((s * 700, s * 1150))
        m.add("headlight_housing", BLACK, box(1540, 1554, y0, y1, 660, 860))
        m.add("headlight", LED, [cyl(70, (1548, s * y, 760), (1561, s * y, 760)) for y in (790.0, 950.0)])
        m.add("headlight_bezels", CHROME, [cyl(82, (1546, s * y, 760), (1556, s * y, 760)) for y in (790.0, 950.0)])
        y0, y1 = sorted((s * 1050, s * 1135))
        m.add("indicator_front", AMBER, box(1549, 1560, y0, y1, 690, 830))
        m.add("fog_light_ring", BLACK, cyl(62, (1538, s * 950, 560), (1551, s * 950, 560)))
        m.add("fog_light", LED, cyl(48, (1540, s * 950, 560), (1557, s * 950, 560)))
    m.add("tow_recess", BLACK, box(1538, 1549, -120, 120, 445, 600))
    m.add("tow_pin", STEEL, cyl(m.r(28), (1525, 0, 455), (1525, 0, 590)), box(1500, 1546, -45, 45, 500, 545))

    zv = 2690.0
    xv = xfr(zv)
    m.add("sun_visor", WHITE, prism([(xv - 40, 2650), (xv + 190, 2690), (xv + 190, 2690 + m.t(35)), (xfr(2790) - 40, 2790)],
                                    "y", -1120, 1120))
    m.add("marker_lamps", AMBER, [box(xv + 120, xv + 175, y - 40, y + 40, 2715, 2752) for y in (-900, -300, 300, 900)])
    m.add("roof_vent", WHITE, rounded_box(200, 560, -260, 260, 3010, 3068, 22))
    m.add("roof_vent_seam", BLACK, box(190, 570, -270, 270, 3015, 3032))
    m.add("beacon_base", BLACK, cyl(95, (-120, 0, 3020), (-120, 0, 3075)))
    m.add("beacon", AMBER, cyl(78, (-120, 0, 3070), (-120, 0, 3195)), sphere(78, (-120, 0, 3195)))

    for s in (1, -1):
        xm, ym = 1300.0, s * 1440
        m.add("mirror_arms", BLACK, pipe([(1150, s * (hw(2450) - 25), 2450), (xm, ym, 2470)], hr),
              pipe([(1150, s * (hw(1850) - 25), 1850), (xm, ym, 1850)], hr),
              cyl(hr, (xm, ym, 1820), (xm, ym, 2500)))
        y0, y1 = sorted((s * 1365, s * 1535))
        m.add("mirror_heads", BLACK, box(xm - 35, xm + 60, y0, y1, 2060, 2470),
              box(xm - 35, xm + 60, y0, y1, 1830, 2020))
        y0, y1 = sorted((s * 1378, s * 1522))
        m.add("mirror_glass", CHROME, box(xm - 47, xm - 30, y0, y1, 2075, 2455), box(xm - 47, xm - 30, y0, y1, 1845, 2005))
    # kerb mirror over the right of the windscreen
    m.add("kerb_mirror_arm", BLACK, pipe([(1080, -950, 3005), (1340, -1000, 3090), (1480, -1000, 2990)], hr))
    m.add("kerb_mirror", BLACK, box(1440, 1540, -1120, -880, 2850, 3010))
    m.add("kerb_mirror_glass", CHROME, box(1430, 1450, -1105, -895, 2865, 2995))

    # cab mounts and the air intake snorkel behind the cab
    m.add("air_intake", BLACK, cyl(110, (-500, -900, 1300), (-500, -900, 3060)),
          cyl(140, (-500, -900, 3050), (-500, -900, 3120)), cone(140, 60, (-500, -900, 3120), (-500, -900, 3180)),
          [box(-520, -360, -930, -870, z - 30, z + 30) for z in (1700, 2700)])
    m.add("exhaust", BLACK, cyl(210, (-1500, -700, 700), (-750, -700, 700)),
          box(-1400, -850, -560, -430, 760, 840), cyl(m.r(60), (-1500, -700, 700), (-1700, -1000, 560)))

    # =========================================================== tanks, boxes, guards
    tx, tz, tr = -960.0, 1530.0, 360.0
    m.add("water_tank", STEEL, cyl(tr, (tx, -930, tz), (tx, 930, tz)),
          [cone(tr, tr - 110, (tx, s * 930, tz), (tx, s * 1010, tz)) for s in (1, -1)])
    m.add("water_tank_bands", BLACK, [cyl(tr + 12, (tx, y - 40, tz), (tx, y + 40, tz)) for y in (-600, 0, 600)])
    m.add("water_tank_saddles", DARK, [box(tx - 300, tx + 300, y - 60, y + 60, RZ1 - 20, tz - 250) for y in (-390, 390)])
    m.add("water_tank_filler", GALV, cyl(70, (tx, 450, tz + 330), (tx, 450, tz + 400)),
          cyl(85, (tx, 450, tz + 395), (tx, 450, tz + 425)))
    m.add("water_pump_gauge", GALV, cyl(60, (tx + 50, 1000, tz), (tx + 50, 1050, tz)))

    m.add("fuel_tank", CHROME, rounded_box(-2700, -1550, 480, 1090, 560, 1050, 80))
    m.add("fuel_tank_straps", BLACK, [box(x, x + 50, 470, 1100, 550, 1060) for x in (-2500, -1800)],
          [box(x - 10, x + 60, 425, 490, 880, 1000) for x in (-2500, -1800)])
    m.add("fuel_filler", BLACK, cyl(65, (-1700, 950, 1040), (-1700, 950, 1100)))
    m.add("battery_box", BLACK, box(-2600, -2000, -1080, -470, 640, 1020), box(-2620, -1980, -1095, -425, 1010, 1045))
    m.add("air_tanks", GALV, [cyl(130, (-3300, -y, 760), (-2700, -y, 760)) for y in (650, 930)],
          [box(x, x + 50, -1065, -425, 640, 900) for x in (-3200, -2850)])
    for s in (1, -1):
        y0, y1 = sorted((s * (1160 - m.t(35)), s * 1160))
        m.add("side_guard", GALV, [box(-3330, -720, y0, y1, z, z + 100) for z in (480, 790)],
              [box(x - 30, x + 30, y0, y1, 470, 900) for x in (-3300, -760)])
        y0, y1 = sorted((s * 425, s * 1160))
        m.add("side_guard_brackets", DARK, [box(x - 30, x + 30, y0, y1, 820, 880) for x in (-3300, -760)])
        m.add("side_markers", AMBER, [box(x - 40, x + 40, s * 1158, s * 1170, 818, 862) for x in (-1500, -2900)])

    # rear mudguards, mud flaps, markers
    path = arc_pts(XR1, ZC, 615, 14, 90, 10) + arc_pts(XR2, ZC, 615, 90, 166, 10)
    for s in (1, -1):
        y0, y1 = sorted((s * 600, s * 1275))
        m.add("rear_mudguard", BLACK, prism(band(path, m.t(12) / 2), "y", y0, y1))
        y0, y1 = sorted((s * 425, s * 720))
        m.add("mudguard_brackets", DARK, [box(x - 40, x + 40, y0, y1, 1070, ZC + 618) for x in (-4100, -5050)])
        y0, y1 = sorted((s * 640, s * 1265))
        xe = XR2 + 615 * math.cos(math.radians(166))
        m.add("rear_mud_flap", RUBBER, box(xe - m.t(22), xe, y0, y1, 280, ZC + 175))
        y0, y1 = sorted((s * 960, s * 1230))
        m.add("front_mud_flap", RUBBER, box(-695 - m.t(20), -695, y0, y1, 300, 1000))
        y0, y1 = sorted((s * 425, s * 1230))
        m.add("front_flap_bracket", DARK, box(-735, -680, y0, y1, 960, 1010))
        m.add("mudguard_markers", AMBER, [box(x - 45, x + 45, s * 1272, s * 1284, ZC + 560, ZC + 600)
                                          for x in (XR1 + 200, XR2 - 200)])

    # spare extension chutes on a rack above the left mudguards
    t = m.t(12)
    rc = 215.0
    sec = (arc_pts(0, 0, rc, 180, 360, 28) + [(rc, 60), (rc - t, 60)] + arc_pts(0, 0, rc - t, 360, 180, 28)
           + [(-(rc - t), 60), (-rc, 60)])
    yc, zb = 1010.0, 1275.0
    spare = [mv3(prism(sec, "x", x0, x0 + 1150), (0, yc, zb + rc)) for x0 in (-4720, -4570)]
    spare = [spare[0], mv3(spare[1], (0, 0, 0.6 * t))]
    m.add("spare_chutes", CHUTE, spare)
    rack = []
    for x in (-3750.0, -4500.0):
        rack.append(box(x - 40, x + 40, 425, yc + rc + 30, zb - 45, zb + 12))
        rack.append(box(x - 40, x + 40, 425, 520, SZ1 - 120, zb - 20))
        rack.append(box(x - 40, x + 40, yc + rc + 5, yc + rc + 45, zb - 45, zb + 260))
        rack.append(box(x - 40, x + 40, yc - rc - 45, yc - rc - 5, zb - 45, zb + 260))
    m.add("chute_rack", DARK, rack)
    m.add("chute_strap", BLACK, [torus(rc + 30, m.r(12), (x, yc, zb + rc), (1, 0, 0)).intersect(
        box(x - 60, x + 60, yc - 400, yc + 400, zb + rc - 30, zb + rc + 400)) for x in (-3750.0, -4500.0)])

    # rear under-run bar and lamps
    m.add("rear_underrun", GREY, box(-6900, -6800, -1150, 1150, 430, 560),
          [box(-6880, -6720, s * RY0, s * RY1, 520, RZ0 + 20) for s in (1, -1)])
    for s in (1, -1):
        y0, y1 = sorted((s * 760, s * 1120))
        m.add("rear_lamp_housing", BLACK, box(-6915, -6890, y0, y1, 455, 545))
        m.add("tail_lights", RED, box(-6925, -6905, *sorted((s * 900, s * 1110)), 465, 535))
        m.add("rear_indicators", AMBER, box(-6925, -6905, *sorted((s * 780, s * 890)), 465, 535))
        m.add("rear_reflectors", RED, box(-6908, -6898, *sorted((s * 300, s * 420)), 470, 520))

    # =========================================================== drum and its drive
    # the print drum is the faceted cone chain; both are cut into the same painted bands, so the
    # painted 3MF prints the stripes too
    if True:
        drum = drum_solid(cones=m.print_mode)
        beta = math.radians(34.0)
        n = math.cos(beta) * U + math.sin(beta) * N        # band planes, slanted across the axis
        z = np.cross(n, Y)
        a, k = -900.0, 0
        widths = (430.0, 300.0)
        while a < 5300:
            w = widths[k % 2]
            slab = place(box(a, a + w, -3000, 3000, -3000, 3000), tuple(n), tuple(Y), tuple(z), tuple(DF))
            pieces = [d.intersect(slab) for d in (drum if isinstance(drum, list) else [drum])]
            pieces = [pc for pc in pieces if pc.Volume() > 1]
            if pieces:
                m.add(f"drum_band_{k + 1}", DRUM_A if k % 2 == 0 else DRUM_B, pieces)
            a += w
            k += 1
    # the open mouth: recessed into the drum, dark inside, the two spiral blades showing
    m.add("drum_mouth", MOUTH, cut(cyl(R_MOUTH + 9, DP(S_MOUTH - 10), DP(4995)), cyl(R_MOUTH - 9, DP(S_MOUTH + 10), DP(5010))),
          cyl(R_MOUTH, DP(S_MOUTH - 12), DP(S_MOUTH + 12)))
    blades = []
    for a0 in (20.0, 200.0):
        for k in range(3):
            a, b = a0 + 32 * k, a0 + 32 * (k + 1)
            sa, sb = S_MOUTH + 15 + 40 * k, S_MOUTH + 15 + 40 * (k + 1)
            am = math.radians((a + b) / 2)
            up = tuple(float(v) for v in math.cos(am) * N + math.sin(am) * Y)
            blades.append(bar(ring_pt(sa, 345, a), ring_pt(sb, 345, b), m.t(40), 150, up=up))
    m.add("drum_blades", GREY, blades)
    m.add("drum_lip", STEEL, torus(428, m.r(24), DP(5000), tuple(U)))
    m.add("roller_track", STEEL, cyl(R_RING, DP(S_RING - 80), DP(S_RING + 80)))
    m.add("drum_head_ring", STEEL, cyl(575, DP(-12), DP(40)))
    m.add("drum_hatch", STEEL, cyl(230, ring_pt(1800, 1125, 90), ring_pt(1800, 1150 + m.t(18), 90)),
          [cyl(m.r(16), ring_pt(1800 + 200 * math.cos(t), 1140, 90 + math.degrees(200 * math.sin(t) / 1150)),
               ring_pt(1800 + 200 * math.cos(t), 1150 + m.t(18) + 14, 90 + math.degrees(200 * math.sin(t) / 1150)))
           for t in np.linspace(0, 2 * math.pi, 10, endpoint=False)])

    # gearbox, hydraulic motor, front pedestal
    bolts = [cyl(m.r(18), ring_pt(-70, 355, a), ring_pt(-40, 355, a)) for a in range(0, 360, 30)]
    m.add("gearbox", DARK, cyl(300, DP(-420), DP(-30)), cyl(395, DP(-70), DP(8)))
    m.add("gearbox_bolts", STEEL, bolts)
    m.add("hydraulic_motor", BLACK, cyl(140, DP(-640), DP(-400)), box(*sorted((DP(-560)[0], DP(-480)[0])),
                                                                        -180, 180, DP(-500)[2] - 60, DP(-500)[2] + 200))
    ped = prism([(-560, 1150), (560, 1150), (360, 1910), (-360, 1910)], "x", -1830, -1550)
    ped = cut(ped, prism([(-330, 1280), (330, 1280), (170, 1650), (-170, 1650)], "x", -1900, -1400))
    m.add("front_pedestal", DARK, ped, box(-1850, -1530, -400, 400, 1880, 1960))
    m.add("hydraulic_tank", BLACK, box(-1830, -1520, 420, 730, 1290, 1730))
    m.add("hydraulic_tank_gauge", GLASS, box(-1700, -1640, 728, 740, 1400, 1640))
    m.add("hydraulic_tank_cap", GALV, cyl(60, (-1670, 560, 1725), (-1670, 560, 1790)))
    m.add("hydraulic_hoses", BLACK, pipe([(-1600, 600, 1650), (-1560, 520, 1900), (-1450, 200, 2060)], m.r(22)),
          pipe([(-1760, 650, 1650), (-1700, 560, 1950), (-1500, 140, 2100)], m.r(22)))

    # rear pedestal: cross beam, legs, roller brackets, rollers
    rollers, brackets, legs = [], [], []
    xr = None
    for s in (1, -1):
        c = np.array(ring_pt(S_RING, R_RING + R_ROLL - 12, 180 - s * 38))
        xr, yr, zr = c
        rollers.append(cyl(R_ROLL, tuple(c - U * 95), tuple(c + U * 95)))
        brackets.append(box(xr - 140, xr + 140, yr - 135, yr + 135, zr - 330, zr - 120))
        legs.append(bar((xr, s * 400, 1380), (xr, yr, zr - 250), 170, 260, up=(1, 0, 0)))
        rollers_pin = cyl(m.r(40), tuple(c - U * 130), tuple(c + U * 130))
        m.add("roller_axles", STEEL, rollers_pin)
    m.add("support_rollers", DARK, rollers)
    m.add("rear_pedestal", DARK, legs, brackets, box(xr - 160, xr + 160, -500, 500, SZ1 - 60, 1460))

    # hopper arms from the rear pedestal up round the drum to the charge hopper
    yr = abs(yr)
    arms, braces = [], []
    pts_arm = lambda s: [(xr - 40, s * (yr + 20), zr - 200), (-6300.0, s * 830, 3150.0), (-6700.0, s * 545, 3820.0)]
    for s in (1, -1):
        p = pts_arm(s)
        arms += [bar(p[0], p[1], 120, 120, up=(0, s, 0)), bar(p[1], p[2], 120, 120, up=(0, s, 0)),
                 box(p[1][0] - 70, p[1][0] + 70, p[1][1] - 70, p[1][1] + 70, p[1][2] - 70, p[1][2] + 70)]
        braces.append(box(-6720, -6620, s * 330, s * 440, RZ1 - 20, 2700))
        braces.append(bar((-6670, s * 385, 2620), (-6300, s * 830, 3150), 90, 90, up=(1, 0, 0)))
    m.add("hopper_arms", DARK, arms, braces)

    # charge hopper
    hb, ht = (-7120, -6780, -250, 250, 3400), (-7620, -6705, -485, 485, 3990)
    m.add("charge_hopper", GALV, hollow_frustum(hb, ht, m.t(12)))
    # its spout, sloping down from the outlet into the drum mouth
    a, b = np.array([-6950.0, 0.0, 3480.0]), np.array(DP(4920, dn=-10))
    d = (b - a) / np.linalg.norm(b - a)
    tw = m.t(12)
    spout = cut(bar(a, b, 300, 200), bar(a - 100 * d, b + 100 * d, 300 - 2 * tw, 200 - 2 * tw))
    m.add("hopper_spout", GALV, spout.intersect(box(-7400, -6500, -400, 400, 2800, 3402)))
    lip = [box(ht[0] - 25, ht[1] + 25, y - 25, y + 25, 3960, 4000) for y in (ht[2], ht[3])]
    lip += [box(x - 25, x + 25, ht[2] - 25, ht[3] + 25, 3960, 4000) for x in (ht[0], ht[1])]
    m.add("hopper_lip", DARK, lip)
    m.add("hopper_brackets", DARK, [box(-6780, -6640, *sorted((s * 380, s * 600)), 3760, 3870) for s in (1, -1)])

    # collection hopper, chute pivot, folding chute (transit: hanging, extension folded over)
    cb, ct = (-7300, -7000, -180, 180, 2470), (-7480, -6880, -430, 430, 2800)
    m.add("collection_hopper", GALV, hollow_frustum(cb, ct, m.t(10)))
    m.add("collection_hopper_brackets", DARK,
          [box(-7300, -6620, *sorted((s * 290, s * 445)), 2600, 2690) for s in (1, -1)])
    P = np.array([-7150.0, 0.0, 2390.0])
    m.add("chute_pivot", STEEL, cyl(195, (P[0], 0, 2380), (P[0], 0, 2500)), cyl(235, (P[0], 0, 2375), (P[0], 0, 2425)))

    t = m.t(10)
    rc = 230.0
    sec = (arc_pts(0, -70, rc, 180, 360, 28) + [(rc, 0), (rc - t, 0)] + arc_pts(0, -70, rc - t, 360, 180, 28)
           + [(-(rc - t), 0), (-rc, 0)])
    Lc, Le, pitch, roll = 1000.0, 700.0, -62.0, 16.0
    main = prism(sec, "x", -Lc, 60)
    # the extension, folded back over the main chute on its hinge and left a little open
    ext = rot(prism([(y, -z) for y, z in sec], "x", -Lc, -Lc + Le), -roll, (0, 1, 0), (-Lc, 0, 0))
    rib = band(arc_pts(0, -70, rc + 4, 180, 360, 28), 14)
    ribs = [prism(rib, "x", x - 25, x + 25) for x in (-300, -800)]

    def chute(shape):
        if isinstance(shape, (list, tuple)):
            return [chute(x) for x in shape]
        return rot(mv3(shape, P), pitch, (0, 1, 0), tuple(P))
    m.add("chute", CHUTE, chute(main), [chute(r) for r in ribs])
    m.add("chute_extension", CHUTE, chute(ext))
    m.add("chute_hinge", DARK, chute(cyl(m.r(40), (-Lc, -rc - 30, 0), (-Lc, rc + 30, 0))),
          chute(box(-Lc - 40, -Lc + 60, -rc - 25, rc + 25, -60, 60)))
    m.add("chute_handle", BLACK, chute(pipe([(-Lc + 150, rc - 5, -40), (-Lc + 150, rc + 90, -40),
                                             (-Lc + 500, rc + 90, -40), (-Lc + 500, rc - 5, -40)], hr)))
    (barrel, rod), eyes = ram((-6790, 0, 1000), tuple(np.array(chute_pt(-560, -300, P, pitch))), 60, 35, 0.55)
    m.add("chute_ram", BLACK, barrel)
    m.add("chute_ram_rod", CHROME, rod, eyes)
    m.add("chute_ram_mount", DARK, box(-6830, -6740, -70, 70, 940, RZ0 + 10))

    # ladder, platform and handrail (left rear)
    xl, ya, yb = -7000.0, 610.0, 1020.0
    m.add("ladder_stringers", BLACK, [box(xl - 25, xl + 25, y - 25, y + 25, 430, 3060) for y in (ya, yb)])
    m.add("ladder_rungs", GALV, [cyl(m.r(16), (xl, ya, z), (xl, yb, z)) for z in np.arange(700, 2900, 300)])
    m.add("ladder_foot", DARK, box(xl - 30, -6880, ya - 30, yb + 30, 450, 530))
    m.add("platform", GALV, box(xl - 30, -6700, 520, 1060, 3030, 3075))
    m.add("platform_strut", DARK, bar((-6720, 800, 3050), (-6400, 757, 3317), 60, 60))
    rails_ = []
    for y in (ya, yb):
        rails_ += pipe([(xl, y, 3050), (xl, y, 3960), (-6720, y, 3960), (-6720, y, 3050)], hr)
        rails_ += pipe([(xl, y, 3500), (-6720, y, 3500)], hr)
    m.add("handrails", BLACK, rails_)

    # water supply pipe from the tank to the hopper
    m.add("water_pipe", GALV, pipe([(tx, 760, tz - 280), (tx - 250, 500, 1170), (-5000, 500, 1170),
                                    (-5080, 950, 1620), (-6300, 945, 3150), (-6690, 640, 3880),
                                    (-6690, 470, 3880)], m.r(24)))
    m.add("drum_controls", BLACK, box(-6810, -6700, 340, 540, 1350, 1550),
          [cyl(m.r(14), (-6760, y, 1540), (-6760, y, 1720)) for y in (385, 440, 495)])
    m.add("control_knobs", RED, [sphere(m.r(28), (-6760, y, 1730)) for y in (385, 440, 495)])


def mv3(shape, p):
    return shape.translate(V(float(p[0]), float(p[1]), float(p[2])))


def chute_pt(x, z, P, pitch):
    """A point of the chute's local frame (x along it, z up from its rim), in the world."""
    a = math.radians(pitch)
    return (P[0] + x * math.cos(a) + z * math.sin(a), 0.0, P[2] - x * math.sin(a) + z * math.cos(a))
