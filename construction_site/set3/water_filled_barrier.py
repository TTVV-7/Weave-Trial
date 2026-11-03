"""Water-filled plastic safety barrier (longitudinal channelizing device), 6 ft class, 42 in tall.

A generic, brand-neutral rotomoulded polyethylene barrier of the kind used to channel traffic
and pedestrians through work zones, filled with water on site for ballast and emptied to move.
Dimensions follow the typical proportions of the 6 ft / 42 in class:

* overall length ~1.86 m (73 in) over the knuckles, 1.75 m (69 in) pin to pin (the effective
  length in a run); 1.045 m (41 in) to the top of the body, ~1.08 m (42.5 in) to the top of
  the fill cap and the connecting pin's T-handle;
* a tapered, jersey-like section: a 558 mm (22 in) wide base with a vertical 140 mm toe, a
  short shoulder, then walls leaning in ~9 degrees to a 242 mm (9.5 in) wide rounded crown;
* moulded stiffening panels on both faces: five vertical ribs per face between a belt rib
  above the toe and a belt rib under the crown;
* plan-chamfered ends so a run can articulate, each with interlocking hinge knuckles on the
  centreline: three male knuckles at the +X end, two female knuckles (and matching sockets)
  at the -X end, so the next barrier's knuckles nest between them; a 1.1 in galvanised steel
  connecting pin with a T-handle drops through the +X knuckles;
* a 6 in screw fill cap on a boss in the middle of the crown, two square post sockets in the
  crown for a warning light or sign, and a moulded hand-hold slot through each end of the top;
* two forklift / handling slots through the base, open underneath (~9.5 x 4 in);
* a drain plug in a boss low on the +Y face of the toe, and a strip of white retroreflective
  sheeting on the upper panels of each face.

Millimetres, X along the barrier, Y across, Z up, ground at Z = 0; the barrier stands flat
on the ground.
"""

from __future__ import annotations

import math

import numpy as np

from cadkit import arc_pts, band, box, cone, cut, cyl, prism, rot, sphere, stadium
from finishes import BLACK, GALV, SIGN_ORANGE, WHITE

ASSET = dict(key="water_filled_barrier", stem="Water_Filled_Barrier_6ft",
             title="Water-Filled Barrier (6 ft, plastic)", az=30, el=18, size="1200x900")

# ---------------------------------------------------------------- main dimensions
XP = 875.0                  # pin axes at x = +/-XP (1750 pin to pin)
RK = 55.0                   # knuckle radius
CLR = 7.0                   # clearance round the mating knuckles
E_END = 80.0                # half width of the flat end face
K_CH = 220.0 / 170.0        # plan chamfer: y gained per mm back from the end face
HB = 279.0                  # half base width (22 in base)
Z_TOP = 1045.0              # crown
TOE = 140.0                 # top of the vertical toe
W0 = (248.0, 200.0)         # foot of the leaning wall (y, z)
W1 = (121.4, 976.7)         # top of the leaning wall, where the crown round starts

MALE = [(80.0, 250.0), (470.0, 640.0), (860.0, Z_TOP)]     # knuckles at +X
FEMALE = [(265.0, 455.0), (655.0, 845.0)]                    # knuckles at -X
RIB_X = [-560.0, -280.0, 0.0, 280.0, 560.0]
FORK_X = [-430.0, 430.0]
SLOT_X = 710.0              # hand-hold slots at +/- this


def wall_y(z):
    """Half width of the leaning wall at height z."""
    (y0, z0), (y1, z1) = W0, W1
    return y0 + (y1 - y0) * (z - z0) / (z1 - z0)


def profile():
    """Barrier cross-section (y, z), symmetric."""
    right = [(262, 0), (275, 4), (HB, 17), (HB, TOE), (276, TOE + 12), (266, TOE + 26), W0]
    right += arc_pts(62, 985, 60, -8, 90, 8)
    right = [(float(y), float(z)) for y, z in right]
    right[-1] = (62.0, Z_TOP)
    left = [(-y, z) for y, z in reversed(right)]
    return right + left


def plan(grow=0.0):
    """Plan outline (x, y) with the chamfered ends, grown outward by `grow`."""
    e = E_END + grow * math.sqrt(1 + K_CH ** 2)
    xb = XP - (320 - e) / K_CH
    xe = XP + grow
    pts = [(xe, -e), (xe, e), (xb, 320), (-xb, 320), (-xe, e), (-xe, -e), (-xb, -320), (xb, -320)]
    return prism(rounded(pts, (0, 1, 4, 5), 25.0), "z", -5, Z_TOP + 200)


def rounded(pts, corners, d, n=5):
    """Polygon with the given corners rounded off (a quadratic curve d back along each edge)."""
    out = []
    for i, p in enumerate(pts):
        if i not in corners:
            out.append(p)
            continue
        P = np.asarray(p, float)
        A, B = np.asarray(pts[i - 1], float), np.asarray(pts[(i + 1) % len(pts)], float)
        q0 = P + (A - P) / np.linalg.norm(A - P) * d
        q1 = P + (B - P) / np.linalg.norm(B - P) * d
        out += [tuple((1 - t) ** 2 * q0 + 2 * (1 - t) * t * P + t ** 2 * q1) for t in np.linspace(0, 1, n + 1)]
    return out


def chamfer_x(half_width):
    """Where the end chamfer meets a face of the given half width."""
    return XP - (half_width - E_END) / K_CH


def build(m):
    shown = not m.print_mode

    # ------------------------------------------------------------ body shell
    body = prism(profile(), "x", -XP - 10, XP + 10).intersect(plan())
    holes = []
    for x in FORK_X:                        # forklift slots, open underneath
        arch = [(x - 120, -10), (x + 120, -10), (x + 120, 70)] + arc_pts(x + 85, 70, 35, 0, 90, 5) \
            + arc_pts(x - 85, 70, 35, 90, 180, 5)
        holes.append(prism(arch, "y", -400, 400))
    for s in (1, -1):                       # hand-hold slots through the top
        holes.append(prism(stadium(s * SLOT_X - 40, s * SLOT_X + 40, 850, 45), "y", -300, 300))
    for x in (-430.0, 430.0):               # post sockets for a light or sign
        holes.append(box(x - 25, x + 25, -25, 25, Z_TOP - 70, Z_TOP + 10))
    for z0, z1 in FEMALE:                   # sockets at +X for the next barrier's knuckles
        holes.append(cyl(RK + CLR, (XP, 0, z0 - CLR), (XP, 0, z1 + CLR)))
    for z0, z1 in MALE:                     # and at -X
        holes.append(cyl(RK + CLR, (-XP, 0, z0 - CLR), (-XP, 0, z1 + CLR + (40 if z1 >= Z_TOP else 0))))
    body = cut(body, *holes)
    m.add("barrier_body", SIGN_ORANGE, body)

    # ------------------------------------------------------------ hinge knuckles
    def knuckle(x, z0, z1, ch=9.0):
        """A moulded knuckle with its top and bottom edges rounded off (but flush with the crown)."""
        top = z1 if z1 >= Z_TOP else z1 - ch
        out = [cyl(RK, (x, 0, z0 + ch), (x, 0, top)), cone(RK - ch, RK, (x, 0, z0), (x, 0, z0 + ch))]
        if top < z1:
            out.append(cone(RK, RK - ch, (x, 0, top), (x, 0, z1)))
        return out

    male = [knuckle(XP, z0, z1) for z0, z1 in MALE]
    m.add("knuckles_male", SIGN_ORANGE, male)
    female = [cyl(RK, (-XP, 0, z0 + 9), (-XP, 0, z1 - 9)).fuse(cone(RK - 9, RK, (-XP, 0, z0), (-XP, 0, z0 + 9)),
                                                              cone(RK, RK - 9, (-XP, 0, z1 - 9), (-XP, 0, z1)))
              for z0, z1 in FEMALE]
    if shown:                               # the open pin holes
        female = [cut(k, cyl(17, (-XP, 0, z0 - 1), (-XP, 0, z1 + 1))) for k, (z0, z1) in zip(female, FEMALE)]
    m.add("knuckles_female", SIGN_ORANGE, female)

    # ------------------------------------------------------------ moulded ribs and panels
    rib_h = 16.0
    za, zb = 250.0, 945.0                   # the ribs run into the belts, framing the panels
    ribs = []
    for s in (1, -1):
        path = [(s * wall_y(za), za), (s * wall_y(zb), zb)]
        for x in RIB_X:
            ribs.append(prism(band(path, rib_h), "x", x - 32, x + 32))
    belts = []
    for z0, z1 in ((226.0, 264.0), (930.0, 960.0)):
        xe = chamfer_x(wall_y(z0)) + 40
        for s in (1, -1):
            sec = [(s * (wall_y(z0) - 12), z0), (s * (wall_y(z0) + rib_h), z0 + 5),
                   (s * (wall_y(z1) + rib_h), z1 - 5), (s * (wall_y(z1) - 12), z1)]
            belts.append(prism(sec, "x", -xe, xe).intersect(plan()))
    m.add("moulded_ribs", SIGN_ORANGE, ribs, belts)

    # retroreflective sheeting on the upper panels, between the ribs: 2 mm proud, the rest of
    # its (print-thickened) depth sunk into the wall
    t, proud = m.t(3), 2.0
    zs0, zs1 = 745.0, 835.0
    sheets = []
    for s in (1, -1):
        sec = [(s * (wall_y(zs0) + proud - t), zs0), (s * (wall_y(zs0) + proud), zs0),
               (s * (wall_y(zs1) + proud), zs1), (s * (wall_y(zs1) + proud - t), zs1)]
        for xa, xb in zip(RIB_X[:-1], RIB_X[1:]):
            sheets.append(prism(sec, "x", xa + 52, xb - 52))
    m.add("reflective_sheeting", WHITE, sheets)

    # ------------------------------------------------------------ fill cap
    m.add("fill_boss", SIGN_ORANGE, cyl(92, (0, 0, Z_TOP - 40), (0, 0, Z_TOP + 8)))
    cap_z0, cap_z1 = Z_TOP + 6, Z_TOP + 30
    grips = [rot(box(68, 81, -6, 6, cap_z0 + 1, cap_z1 - 3), 360 * k / 18) for k in range(18)]
    m.add("fill_cap", BLACK, cyl(76, (0, 0, cap_z0), (0, 0, cap_z1)), grips,
          box(-58, 58, -11, 11, cap_z1 - 2, cap_z1 + 14))

    # ------------------------------------------------------------ drain plug, low on the +Y toe
    xd, zd = 640.0, 78.0
    m.add("drain_boss", SIGN_ORANGE, cyl(50, (xd, HB - 10, zd), (xd, HB + 10, zd)))
    hexa = [(xd + 22 * math.cos(math.radians(30 + 60 * k)), zd + 22 * math.sin(math.radians(30 + 60 * k)))
            for k in range(6)]
    m.add("drain_plug", BLACK, cyl(38, (xd, HB + 6, zd), (xd, HB + 20, zd)),
          prism(hexa, "y", HB + 18, HB + 34))

    # ------------------------------------------------------------ connecting pin, +X joint
    r = m.r(14)
    zh = Z_TOP + 38
    m.add("connecting_pin", GALV, cyl(r, (XP, 0, 55), (XP, 0, zh)),
          cyl(30, (XP, 0, Z_TOP - 2), (XP, 0, Z_TOP + 12)),
          cyl(m.r(13), (XP, -85, zh), (XP, 85, zh)),
          sphere(m.r(13) * 1.25, (XP, -85, zh)), sphere(m.r(13) * 1.25, (XP, 85, zh)),
          sphere(r * 1.3, (XP, 0, zh)))
