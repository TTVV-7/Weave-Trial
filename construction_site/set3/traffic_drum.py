"""Plastic traffic drum (channelizer), 36 in class, on a tyre-ring ballast base, with a Type A light.

A generic, brand-neutral MUTCD-style channelizing drum of the kind lined up along work zones,
with the typical proportions of the class (MUTCD 6F.67: drums at least 36 in tall and at least
18 in wide, with horizontal, circumferential, alternating orange and white retroreflective
stripes 4-6 in wide, at least two of each, the top stripe orange, and non-reflective gaps of
no more than 3 in):

* a one-piece moulded LDPE body, 592 mm (23.3 in) across at the ground tapering to 500 mm
  (19.7 in) at the shoulder, 880 mm up; a rounded shoulder, a raised crown step and a low domed
  top at ~0.94 m (37 in);
* four retroreflective sleeves, 5 in (127 mm) wide, orange / white / orange / white from the
  top, each sitting in a moulded channel between raised ribs (the orange sheeting is a glossier,
  redder orange than the LDPE body, as real prismatic sheeting is); the ribs are the 1.75 in (45 mm)
  non-reflective gaps, with a deeper rib above the top stripe and one below the bottom stripe;
* a moulded hand-hold on the top: a raised bar across the drum (along Y), with flared ends, over
  a stadium-shaped slot and finger well, so the bar can be gripped from either side; the slot
  opens ~45 mm above the top and the bar top is ~1.01 m (39.8 in) above the ground;
* a small bottom flange, hidden under the base, that the ballast ring clamps to the ground;
* a heavy black recycled-rubber tyre-ring base, 0.91 m (36 in) OD, ~100 mm (4 in) thick, with a
  rounded tyre-like section and two staggered rows of fine, shallow tread blocks round its
  outside (render only: the print keeps a clean rounded rim);
* a Type A low-intensity flashing warning light clamped onto the hand-hold bar with a
  galvanised U-clamp, bolt and wing nut: a black battery case (~8 x 4 x 6 in) with screws, a
  photocell and a switch, under a round head with 7 in amber Fresnel lenses facing front and back.

Overall ~0.92 m across the base, ~1.01 m to the top of the drum's hand-hold and ~1.34 m to the
top of the light. Millimetres, Z up, ground at Z = 0; the drum is round, the lenses face +X / -X
and the hand-hold bar runs along Y.
"""

from __future__ import annotations

import math

import cadquery as cq

from cadkit import Finish, arc_pts, box, cut, cyl, prism, rgb, rot, rounded_box, stadium, torus
from finishes import AMBER, BLACK, DARK, GALV, RED, RUBBER, SIGN_ORANGE, STEEL, WHITE

ASSET = dict(key="traffic_drum", stem="Traffic_Drum_Channelizer", title="Traffic Drum (36 in channelizer)",
             az=35, el=15, size="900x1200")

PHOTOCELL = Finish(rgb("#2a2f36"), rough=0.1)        # dark glossy sensor window
SHEET_ORANGE = Finish(rgb("#f04408"), rough=0.15)    # glossy, redder microprismatic orange sheeting

# ---------------------------------------------------------------- main dimensions
RB, RT, ZT = 296.0, 250.0, 880.0    # body radius at the ground, at the shoulder; shoulder height
SH = 45.0                           # shoulder round-over radius
Z_TOP = ZT + SH                     # top deck at the shoulder edge, 925
CROWN = 9.0                         # raised crown step on the top deck
DOME = 5.0                          # the crown rises this much more to the centre
PROUD = 2.5                         # reflective sleeves stand this far off the body
RIB_OUT = 12.0                      # ribs stand this far off the body
STRIPES = [("orange", 708.0, 835.0), ("white", 536.0, 663.0),
           ("orange", 364.0, 491.0), ("white", 192.0, 319.0)]
RIBS = [(835.0, 875.0), (663.0, 708.0), (491.0, 536.0), (319.0, 364.0), (150.0, 192.0)]
HX = 28.0                           # half thickness of the hand-hold bar (along X)
SLOT_TOP = 975.0                    # underside of the hand-hold bar


def rz(z):
    """Outside radius of the drum body at height z."""
    return RB + (RT - RB) * z / ZT


def lathe(pts):
    """Solid of revolution about the Z axis from a closed (r, z) profile."""
    pts = [(float(r), float(z)) for r, z in pts]
    return cq.Workplane("XZ").polyline(pts).close().revolve(360, (0, 0, 0), (0, 1, 0)).val()


def build(m):
    # ------------------------------------------------------------ drum body
    body_prof = [(0, -2), (338, -2), (341, 16), (333, 28), (rz(30), 30), (rz(ZT), ZT)]
    body_prof += arc_pts(RT - SH, ZT, SH, 0, 90, 8)[1:]
    body_prof += [(186, Z_TOP + 1.5), (180, Z_TOP + CROWN), (0, Z_TOP + CROWN + DOME)]   # crown step
    body = lathe(body_prof)

    ridge_top = SLOT_TOP + m.t(37)
    ridge = [(-185, 905), (185, 905), (150, 965)] + arc_pts(115, ridge_top - 35, 35, 0, 90, 8) \
        + arc_pts(-115, ridge_top - 35, 35, 90, 180, 8) + [(-150, 965)]       # flared moulded ends
    ridge = prism(ridge, "x", -HX, HX)
    well = prism(stadium(-57, 57, (892 + SLOT_TOP) / 2, (SLOT_TOP - 892) / 2), "x", -62, 62)   # finger well
    m.add("drum_body", SIGN_ORANGE, cut(body, well), cut(ridge, well))

    def rib(z0, z1, out=RIB_OUT, ch=8.0, sink=10.0):
        return lathe([(rz(z0) - sink, z0), (rz(z0) + PROUD, z0), (rz(z0 + ch) + out, z0 + ch),
                      (rz(z1 - ch) + out, z1 - ch), (rz(z1) + PROUD, z1), (rz(z1) - sink, z1)])
    m.add("moulded_ribs", SIGN_ORANGE, [rib(z0, z1) for z0, z1 in RIBS])

    depth = m.t(4) - PROUD              # how far each sleeve reaches into the body
    for k, (colour, z0, z1) in enumerate(STRIPES):
        sleeve = lathe([(rz(z0) - depth, z0), (rz(z0) + PROUD, z0), (rz(z1) + PROUD, z1), (rz(z1) - depth, z1)])
        m.add(f"stripe_{k + 1}_{colour}", WHITE if colour == "white" else SHEET_ORANGE, sleeve)

    # ------------------------------------------------------------ tyre-ring ballast base
    ring = lathe([(288, 32), (342, 32), (342, -2), (442, -2), (452, 10), (455, 48), (452, 74),
                  (438, 92), (412, 101), (330, 101), (302, 97), (288, 86)])
    fine = not m.print_mode             # relief finer than a print can hold: shown only
    tread = []                          # two staggered rows of shallow crumb-rubber tread blocks
    if fine:
        for row, (z0, z1) in enumerate(((14.0, 42.0), (52.0, 78.0))):
            for i in range(60):
                tread.append(rot(box(447, 457, -10, 10, z0, z1), 6.0 * i + 3.0 * row))
    m.add("ballast_ring", RUBBER, ring, tread)

    # ------------------------------------------------------------ Type A warning light
    t = m.t(6)
    xi = HX + 1.0                       # clamp plates just clear of the bar faces
    xo = xi + t
    clamp = [box(s * xi, s * xo, -38, 38, 905, ridge_top + 2) for s in (1, -1)]
    clamp.append(box(-xo, xo, -38, 38, ridge_top - 2, ridge_top + t))
    m.add("light_clamp", GALV, clamp)
    zb = 916.0
    hexa = [(22 * math.cos(math.radians(30 + 60 * k)), zb + 22 * math.sin(math.radians(30 + 60 * k)))
            for k in range(6)]
    wing = [prism([(y, z) for y, z in hexa], "x", -xo - 14, -xo)]
    if fine:                            # the thin wings of the wing nut
        wing += [box(-xo - 12, -xo - 4, s * 14, s * 52, zb - 6, zb + 30) for s in (1, -1)]
    m.add("clamp_bolt", STEEL, cyl(m.r(8), (-xo - 20, 0, zb), (xo + 18, 0, zb)),
          prism(hexa, "x", xo, xo + 14), wing)

    hb = ridge_top + t - 2              # battery case sits on the clamp
    ht = hb + 150
    m.add("light_case", BLACK, rounded_box(-48, 48, -102, 102, hb, ht, 12))
    m.add("case_seam", DARK, rounded_box(-50, 50, -104, 104, hb + 92, hb + 102, 4))
    if fine:
        m.add("case_screws", STEEL, [cyl(7, (s * 46, y, z), (s * 52, y, z))
                                     for s in (1, -1) for y in (-80, 80) for z in (hb + 18, hb + 76)])
        m.add("photocell_rim", WHITE, torus(14, 3, (53, 0, hb + 48), (1, 0, 0)))
    m.add("photocell", PHOTOCELL, cyl(m.r(13), (45, 0, hb + 48), (54, 0, hb + 48)))
    m.add("switch_knob", RED, cyl(m.r(14), (0, 100, hb + 125), (0, 118, hb + 125)),
          [box(-5, 5, 112, 124, hb + 106, hb + 144)] if fine else [])          # toggle lever

    zc = ht + 75                        # lens centre
    m.add("lens_head", BLACK, cyl(100, (-40, 0, zc), (40, 0, zc)),
          [torus(92, 6, (s * 44, 0, zc), (1, 0, 0)) for s in (1, -1) if fine],     # bezel lips
          box(-40, 40, -60, 60, ht - 20, zc - 60))
    lens = [cyl(88, (-49, 0, zc), (49, 0, zc))]
    for s in (1, -1):
        if fine:                        # Fresnel rings
            lens += [torus(R, 2.5, (s * 49, 0, zc), (1, 0, 0)) for R in (24, 46, 68)]
            lens.append(cyl(12, (s * 48, 0, zc), (s * 53, 0, zc)))          # centre boss
    m.add("amber_lens", AMBER, lens)
