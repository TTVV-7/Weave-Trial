"""Mobile site office, single-wide 10 x 40 ft, set up on cribbing with its tow tongue still on.

A generic, brand-neutral jobsite office trailer with the typical proportions of the class:

* box: 40 ft long x 10 ft wide (12,192 x 3,048 mm), walls 2.66 m from the bottom of the floor
  frame to the eave, so the body stands ~2.8 m tall to its slightly crowned roof (ridge ~110 mm
  above the eaves); floor surface at ~884 mm above grade, which is where these units sit once
  levelled on blocks;
* siding: off-white ribbed steel (vertical ribs at 12 in / 305 mm), dark slate trim: corner
  trims, base flashing, roof-edge fascia following the crown on the gable ends, drip caps over
  every opening; galvanised steel roof with transverse seams, ridge cap, plumbing vent stacks and
  a static roof vent;
* openings: eight 48 x 36 in (1,200 x 900 mm) horizontal sliding windows (four on the door side,
  four on the back wall) plus a 36 x 36 in window in each end wall, all in mill-aluminium frames
  with a meeting rail, two staggered sashes and partly drawn mini blinds inside; two 36 x 80 in steel doors (the two exits a 40 ft office needs) with casing, threshold,
  vision lite, lever handle, deadbolt, hinges, kick plate, closer and a wall-pack light above;
* stairs: a pressure-treated timber landing (5 x 4 ft) with closed-stringer steps (4 treads,
  five equal ~6.6 in risers down to a 30 mm-proud concrete pad, 10 in run), 42 in guards with
  balusters and sloped handrails, on precast deck blocks; and a prefab galvanised steel stair unit
  with a grating landing, steps running along the wall onto a paver, braced legs on pavers and
  pipe handrails both sides;
* services: a wall-mount package A/C unit (42 x 22 x 75 in class, the common vertical HVAC on
  these offices) on each end wall with louvres, mounting brackets, a condensate drain down the
  wall and a fused disconnect with a flexible whip in a drip loop; a main service panel with
  strapped conduit to a fitting on the base flashing and a feeder cord run out along the ground;
  a "SITE OFFICE" sign between the middle windows;
* under-carriage: two 10 in steel I-beam main rails ~1.8 m apart with tapered outriggers and
  cross members, set on six double-CMU piers per rail (16 x 16 in, two courses cross-laid, on
  concrete pads, timber cap and shim wedges), tie-down straps to ground anchors; axles and tyres
  removed, as they usually are on site; the bolt-on A-frame tow tongue stays at the +X end with
  its round-nosed cast coupler with latch lever, safety chains and a side-wind tongue jack on a
  timber pad.

Print (1:50): the siding ribs are 40 mm wide x 30 mm proud (0.8 x 0.6 mm), window frames and the
sign stand out further to suit, and the door vision lites stay recessed inside raised gaskets.

Overall ~14.8 m from the far A/C unit to the coupler (12.2 m box), ~5.8 m from the back fascia to
the stair pad and feeder cord (3.05 m box), ~3.75 m high to the top of the vent stacks (ridge ~3.53 m).

Millimetres, X along the length (tongue at +X), Y left (door side +Y), Z up, ground at Z = 0.
"""

from __future__ import annotations

import math

import numpy as np

from cadkit import FT, Finish, band, bar, box, clip_poly, cone, cut, cyl, frustum, pipe, prism, rgb, sphere, text
from finishes import (BLACK, BLUE, CMU, CONCRETE, DARK, GALV, GLASS, LED, RUBBER, STEEL, TIMBER, TIMBER_DARK, WHITE,
                      YELLOW)

ASSET = dict(key="site_office_trailer", stem="Mobile_Site_Office_10x40ft", title="Mobile Site Office (10 x 40 ft)",
             az=35, el=20, size="1200x900")

SIDING = Finish(rgb("#ece6d5"), rough=0.6)                  # off-white ribbed steel siding
SIDING_RIB = Finish(rgb("#dcd5c2"), rough=0.6)              # the ribs catch less light
TRIM = Finish(rgb("#4d5661"), rough=0.5)                    # dark slate trim
DOOR = Finish(rgb("#66707b"), metal=0.25, rough=0.45)       # painted steel door
ALU = Finish(rgb("#c3c7cb"), metal=0.6, rough=0.38)         # mill aluminium frames
BLINDS = Finish(rgb("#e7e3d8"), rough=0.7)
HVAC = Finish(rgb("#d4ccb6"), rough=0.5)                    # beige HVAC cabinet
PANEL = Finish(rgb("#9ba1a7"), metal=0.3, rough=0.5)        # electrical enclosures
PT_WOOD = Finish(rgb("#a3906b"), rough=0.88)                # pressure-treated framing
CHASSIS = Finish(rgb("#2b2d30"), metal=0.3, rough=0.6)      # black-painted steel frame
CHROME_DARK = Finish(rgb("#8c9196"), metal=0.8, rough=0.35)  # jack crank
COUPLER = Finish(rgb("#5d6267"), metal=0.35, rough=0.55)    # painted/zinc-dull cast coupler

# ---- box
X, Y = 20 * FT, 5 * FT              # half length, half width: 6096 x 1524
ZB, FZ = 744.0, 884.0               # bottom of the floor frame / top of the floor
ZE, ZR = 3400.0, 3510.0             # eave, ridge
RY = 900.0                          # main rail centres, +-y
ZI0 = 490.0                         # underside of the main rails (top of the pier shims)

WIN_Z = (2000.0, 2900.0)
DOOR_W, DOOR_H = 915.0, 2032.0
RECESS = 100.0                      # window reveal depth
PAD_T = 30.0                        # top of the concrete pads at the stair feet
D1_X, D2_X = 3300.0, -3200.0        # doors on the +Y side

# side, centre along the wall, width, kind, blinds drawn (fraction) or hinge side
OPENINGS = [
    ("+y", 5250.0, 1200.0, "win", 0.35),
    ("+y", D1_X, DOOR_W, "door", -1),
    ("+y", 1350.0, 1200.0, "win", 0.0),
    ("+y", -1350.0, 1200.0, "win", 0.55),
    ("+y", D2_X, DOOR_W, "door", 1),
    ("+y", -5250.0, 1200.0, "win", 0.2),
    ("-y", 4600.0, 1200.0, "win", 0.5),
    ("-y", 1500.0, 1200.0, "win", 0.3),
    ("-y", -1500.0, 1200.0, "win", 0.0),
    ("-y", -4600.0, 1200.0, "win", 0.45),
    ("+x", 700.0, 900.0, "win", 0.4),
    ("-x", -700.0, 900.0, "win", 0.25),
]


# wall-mount A/C units: wall, centre along it, disconnect position; cabinet half width and height span
AC_UNITS = [("+x", -700.0, 20.0), ("-x", 700.0, -20.0)]
AC_W2, AC_Z = 535.0, (1345.0, 3250.0)


def rib_depth(m):
    """How far the siding ribs stand proud: 18 mm (3/4 in), 30 mm in print so they survive at 1:50."""
    return 30.0 if m.print_mode else 18.0


def zrange(kind):
    return WIN_Z if kind == "win" else (FZ, FZ + DOOR_H)


# --------------------------------------------------------------------------- wall coordinates

def wpt(side, u, d, z):
    """A point on a wall: u along it, d out from its base siding face, z up."""
    return {"+y": (u, Y + d, z), "-y": (u, -Y - d, z), "+x": (X + d, u, z), "-x": (-X - d, u, z)}[side]


def wbox(side, u0, u1, d0, d1, z0, z1):
    a, b = wpt(side, u0, d0, z0), wpt(side, u1, d1, z1)
    return box(a[0], b[0], a[1], b[1], a[2], b[2])


def subtract(spans, a, b):
    out = []
    for s0, s1 in spans:
        if b <= s0 or a >= s1:
            out.append((s0, s1))
            continue
        if a > s0:
            out.append((s0, a))
        if b < s1:
            out.append((b, s1))
    return out


# --------------------------------------------------------------------------- shell

def shell(m, P):
    recesses = []
    for side, uc, w, kind, _ in OPENINGS:
        z0, z1 = zrange(kind)
        depth = RECESS if kind == "win" else 60.0
        recesses.append(wbox(side, uc - w / 2, uc + w / 2, -depth, 5, z0, z1))
    body = prism([(-Y, ZB), (Y, ZB), (Y, ZE), (0, ZR), (-Y, ZE)], "x", -X, X)
    m.add("body", SIDING, cut(body, *recesses))

    # vertical ribs, broken round the openings and stopped under the A/C units; on the gable ends they
    # run up into the crowned fascia. Print: wider and deeper, so the ribbed siding still reads at 1:50.
    rw, rd = m.t(36), rib_depth(m)
    ribs = []
    for side, half in (("+y", X), ("-y", X), ("+x", Y), ("-x", Y)):
        n = int((2 * half - 480) // 305) + 1
        ops = [(uc, w, *zrange(kind)) for s, uc, w, kind, _ in OPENINGS if s == side]
        acs = [uc for s, uc, _ in AC_UNITS if s == side]
        for u in (np.arange(n) - (n - 1) / 2) * 305:
            if side in ("+y", "-y"):
                ztop = ZE - 90
            else:
                ztop = ZE - 94 + (ZR - ZE) * (1 - abs(u) / (Y + 45)) + 5
            spans = [(ZB + 90, ztop)]
            for uc, w, z0, z1 in ops:
                if abs(u - uc) < w / 2 + 75:
                    spans = subtract(spans, z0 - 75, z1 + 85)
            for uc in acs:
                if abs(u - uc) < AC_W2 + 18 + rw / 2 + 25:
                    spans = subtract(spans, AC_Z[0] - 75, ZR + 100)
            ribs += [wbox(side, u - rw / 2, u + rw / 2, -2, rd, a, b) for a, b in spans if b - a > 60]
    m.add("siding_ribs", SIDING_RIB, ribs)

    # trim: corners, base flashing, roof-edge fascia
    trim = []
    for sx in (1, -1):
        for sy in (1, -1):
            trim.append(box(sx * (X - 110), sx * (X + 22), sy * Y, sy * (Y + 22), ZB - 10, ZE))
            trim.append(box(sx * X, sx * (X + 22), sy * (Y - 110), sy * (Y + 22), ZB - 10, ZE))
    for side, half in (("+y", X), ("-y", X), ("+x", Y), ("-x", Y)):
        trim.append(wbox(side, -half - 20, half + 20, -2, 20, ZB - 10, ZB + 90))
    for side in ("+y", "-y"):
        trim.append(wbox(side, -X - 45, X + 45, -2, 45, ZE - 95, ZE + 28))
    crown = [(-Y - 45, ZE - 33), (0, ZR - 33), (Y + 45, ZE - 33)]
    trim += [prism(band(crown, 61), "x", X - 2, X + 45), prism(band(crown, 61), "x", -X - 45, -X + 2)]
    m.add("trim", TRIM, trim)

    # roof: galvanised sheet over the crown, seams, ridge cap
    m.add("roof", GALV, prism(band([(-Y - 45, ZE), (0, ZR), (Y + 45, ZE)], 20), "x", -X - 45, X + 45))
    seams = []
    for x in np.arange(-X + 610, X - 600, 915):
        for s in (1, -1):
            seams.append(bar((x, s * (Y + 40), ZE + 18), (x, 0, ZR + 18), 28, 26))
    seams.append(box(-X - 45, X + 45, -80, 80, ZR + 4, ZR + 32))
    m.add("roof_seams", GALV, seams)

    def zroof(y):
        return ZR + 20 - abs(y) * (ZR - ZE) / (Y + 45)

    vents, boots = [], []
    for x, y in ((-2600.0, 650.0), (2300.0, -700.0)):
        z = zroof(y)
        vents.append(cyl(m.r(45), (x, y, z - 40), (x, y, z + 260)))
        boots.append(cone(140, 55, (x, y, z - 15), (x, y, z + 70)))
    x, y = 600.0, 750.0
    z = zroof(y)
    boots += [cyl(150, (x, y, z - 30), (x, y, z + 120)), cyl(215, (x, y, z + 120), (x, y, z + 150)),
              cone(215, 60, (x, y, z + 150), (x, y, z + 230))]
    m.add("vent_stacks", BLACK, vents)
    m.add("roof_vents", GALV, boots)


# --------------------------------------------------------------------------- windows and doors

def window(m, P, side, uc, w, frac):
    z0, z1 = WIN_Z
    u0, u1 = uc - w / 2, uc + w / 2
    g = m.t(6)
    gd = -58.0 if m.print_mode else -30.0         # print: glass set deeper so the reveal reads at 1:50
    fd = -66.0 if m.print_mode else -52.0         # frames reach back over the glass edges
    back = -RECESS + 8 if not m.print_mode else gd - g + 2      # print: solid up to the glass, no sealed void
    P["dark"].append(wbox(side, u0, u1, -RECESS - 4, back, z0, z1))
    if frac > 0 and not m.print_mode:
        zb = z1 - frac * (z1 - z0)
        z = z1 - 4
        while z - 24 > zb:
            P["blinds"].append(wbox(side, u0 + 4, u1 - 4, -RECESS + 8, -RECESS + 16, z - 24, z))
            z -= 30
        P["blinds"].append(wbox(side, u0 + 4, u1 - 4, -RECESS + 8, -RECESS + 22, zb - 22, zb))
    P["glass"] += [wbox(side, u0, uc + 25, gd - g, gd, z0, z1), wbox(side, uc - 25, u1, gd - 16 - g, gd - 16, z0, z1)]
    po = 12.0 if m.print_mode else 0.0            # print: frames stand proud of the deeper ribs
    P["frames"] += [wbox(side, u0 - 40, u1 + 40, fd, 22 + po, z1 - 30, z1 + 40),
                    wbox(side, u0 - 40, u1 + 40, fd, 32 + po, z0 - 45, z0 + 30),
                    wbox(side, u0 - 40, u0 + 30, fd, 22 + po, z0 - 45, z1 + 40),
                    wbox(side, u1 - 30, u1 + 40, fd, 22 + po, z0 - 45, z1 + 40),
                    wbox(side, uc - 30, uc + 30, fd - 4, 10, z0, z1)]
    P["latches"] += [wbox(side, uc + 30, uc + 75, 0, 16, (z0 + z1) / 2 - 40, (z0 + z1) / 2 + 40)]
    P["trim"].append(wbox(side, u0 - 75, u1 + 75, -2, 48 + po, z1 + 40, z1 + 40 + m.t(22)))


def wall_light(P, side, uc, z):
    P["light_housings"] += [wbox(side, uc - 130, uc + 130, -3, 190, z, z + 170),
                            wbox(side, uc - 150, uc + 150, -3, 215, z + 170, z + 192)]
    P["lamps"] += [wbox(side, uc - 100, uc + 100, 20, 170, z - 12, z + 4),
                   wbox(side, uc - 95, uc + 95, 186, 196, z + 30, z + 120)]


def door(m, P, side, uc, hinge):
    w, z0, z1 = DOOR_W, FZ, FZ + DOOR_H
    u0, u1 = uc - w / 2, uc + w / 2
    face = -22.0
    P["doors"].append(wbox(side, u0 + 3, u1 - 3, -61, face, z0 + 3, z1 - 3))
    P["casing"] += [wbox(side, u0 - 55, u0 + 6, -62, 24, z0, z1 + 55),
                    wbox(side, u1 - 6, u1 + 55, -62, 24, z0, z1 + 55),
                    wbox(side, u0 - 55, u1 + 55, -62, 24, z1 - 6, z1 + 55)]
    P["trim"].append(wbox(side, u0 - 85, u1 + 85, -2, 52, z1 + 55, z1 + 55 + m.t(22)))
    P["frames"].append(wbox(side, u0 - 55, u1 + 55, -62, 48, z0 - 28, z0 + 4))          # threshold

    # vision lite
    lu0, lu1, lz0, lz1 = uc - 160, uc + 160, z0 + 1180, z0 + 1800
    P["dark"].append(wbox(side, lu0, lu1, face - 2, face + 4, lz0, lz1))
    # glass grows inwards from a fixed front face, so the lite stays recessed behind its gasket in print
    P["glass"].append(wbox(side, lu0, lu1, face + 8 - m.t(5), face + 8, lz0, lz1))
    k, gf = 30, face + (30 if m.print_mode else 12)
    P["gaskets"] += [wbox(side, lu0 - k, lu1 + k, face - 2, gf, lz0 - k, lz0 + 6),
                     wbox(side, lu0 - k, lu1 + k, face - 2, gf, lz1 - 6, lz1 + k),
                     wbox(side, lu0 - k, lu0 + 6, face - 2, gf, lz0 - k, lz1 + k),
                     wbox(side, lu1 - 6, lu1 + k, face - 2, gf, lz0 - k, lz1 + k)]

    # hardware: latch on the side away from the hinges, lever pointing at the hinges
    hu = u0 if hinge < 0 else u1
    inward = 1 if hinge < 0 else -1
    lu = hu + inward * (w - 85)
    zh = z0 + 1000
    P["chrome"] += [cyl(m.r(30), wpt(side, lu, face - 2, zh), wpt(side, lu, face + 28, zh)),
                    cyl(m.r(11), wpt(side, lu, face + 26, zh), wpt(side, lu - inward * 140, face + 26, zh)),
                    sphere(m.r(14), wpt(side, lu - inward * 140, face + 26, zh)),
                    cyl(m.r(28), wpt(side, lu, face - 2, zh + 260), wpt(side, lu, face + 14, zh + 260)),
                    cyl(m.r(12), wpt(side, lu, face + 10, zh + 260), wpt(side, lu, face + 20, zh + 260))]
    P["hinges"] += [wbox(side, hu - 14, hu + 14, face - 6, face + 12, z, z + 115) for z in (z0 + 230, z0 + 1000, z1 - 350)]
    P["hinges"].append(wbox(side, u0 + 40, u1 - 40, face - 1, face + 3, z0 + 40, z0 + 290))     # kick plate
    # door closer on the hinge side, arm up to the head casing
    P["frames"] += [wbox(side, hu + inward * 90, hu + inward * 400, face - 1, face + 62, z1 - 175, z1 - 95),
                    bar(wpt(side, hu + inward * 380, face + 45, z1 - 120), wpt(side, hu + inward * 560, 34, z1 + 30),
                        m.t(28), m.t(16))]
    wall_light(P, side, uc, z1 + 115)


# --------------------------------------------------------------------------- HVAC and electrics

def wall_ac(m, P, side, uc, ud):
    """Wall-mount package A/C, 42 x 22 x 75 in class, with its disconnect at ud."""
    w2, (z0, z1), dep = AC_W2, AC_Z, 575.0
    P["hvac"] += [wbox(side, uc - w2, uc + w2, -3, dep, z0, z1),
                  wbox(side, uc - w2 - 18, uc + w2 + 18, -3, dep + 28, z1, z1 + 38)]
    P["hvac_dark"].append(wbox(side, uc - w2 + 60, uc + w2 - 60, dep - 2, dep + 4, z0 + 90, z0 + 820))
    P["hvac"] += [wbox(side, uc - w2 + 60, uc + w2 - 60, dep, dep + 16, z, z + 20)
                  for z in np.arange(z0 + 110, z0 + 800, 46)]
    for s in (1, -1):
        uo = uc + s * w2
        P["hvac_dark"].append(wbox(side, uo - s * 2, uo + s * 4, 72, dep - 72, z0 + 950, z1 - 160))
        P["hvac"] += [wbox(side, uo, uo + s * 15, 70, dep - 70, z, z + 18) for z in np.arange(z0 + 975, z1 - 170, 42)]
    # service panels, handles, rating plate
    if not m.print_mode:
        P["hvac_dark"] += [wbox(side, uc - w2 + 20, uc + w2 - 20, dep - 1, dep + 2, z, z + 6)
                           for z in (z0 + 880, z0 + 1500)]
        P["hvac_dark"].append(wbox(side, uc - 3, uc + 3, dep - 1, dep + 2, z0 + 880, z1 - 30))
    P["chrome"] += [wbox(side, u - 50, u + 50, dep - 2, dep + 14, z0 + 1180, z0 + 1210) for u in (uc - 270, uc + 270)]
    P["labels"].append(wbox(side, uc + 120, uc + 380, dep - 2, dep + 3, z0 + 1620, z0 + 1760))
    # brackets and braces; the wall straps stand clear of the siding ribs they cross
    for s in (1, -1):
        ub = uc + s * 420
        P["hvac_dark"] += [wbox(side, ub - 30, ub + 30, -3, dep - 30, z0 - 70, z0 + 5),
                           wbox(side, ub - 30, ub + 30, -3, max(22.0, rib_depth(m) + 6), z0 - 520, z0)]
        P["hvac_dark"].append(bar(wpt(side, ub, 10, z0 - 470), wpt(side, ub, dep - 60, z0 - 40), m.t(40), m.t(40)))
    # condensate drain: out of the cabinet base, back to the wall and down it (so the print grows it from the wall)
    ux = uc + 150
    P["cords"] += pipe([wpt(side, ux, 130, z0 + 10), wpt(side, ux, 130, z0 - 40), wpt(side, ux, 14, z0 - 130),
                        wpt(side, ux, 14, ZB + 160)], m.r(14))
    # fused disconnect and its flexible whip into the side of the cabinet
    P["panels"].append(wbox(side, ud - 120, ud + 120, -3, 118, 2050, 2420))
    P["hvac_dark"].append(wbox(side, ud + 120, ud + 150, 40, 90, 2180, 2300))
    # the whip sags in a drip loop between the disconnect and the cabinet side
    sg = 1 if ud > uc else -1
    ue = uc + sg * (w2 - 40)
    P["cords"] += pipe([wpt(side, ud, 60, 2060), wpt(side, ud, 66, 1955), wpt(side, ud - sg * 45, 100, 1870),
                        wpt(side, (ud + ue) / 2, 150, 1828), wpt(side, ue + sg * 40, 185, 1838),
                        wpt(side, ue, 200, 1850)], m.r(16))


def service_panel(m, P, side, uc):
    P["panels"].append(wbox(side, uc - 200, uc + 200, -3, 112, 1100, 1700))
    P["hvac_dark"] += [wbox(side, uc + 150, uc + 175, 110, 122, 1350, 1450),
                       wbox(side, uc - 170, uc - 120, 110, 116, 1640, 1660)]
    P["labels"].append(wbox(side, uc - 120, uc + 60, 110, 115, 1560, 1635))
    # conduit strapped flat to the siding (between two ribs) down to a fitting on the base flashing
    P["conduit"] += [cyl(m.r(24), wpt(side, uc, 22, 1110), wpt(side, uc, 22, 800)),
                     wbox(side, uc - 45, uc + 45, -2, 80, 760, 860)]
    P["conduit"] += [wbox(side, uc - 45, uc + 45, -2, 50, z, z + 20) for z in (900.0, 1000.0)]
    # feeder cord: down from the fitting, out along the ground
    if side == "+x":
        pts = [wpt(side, uc, 46, 770), wpt(side, uc, 90, 480), wpt(side, uc, 160, 260), wpt(side, uc + 60, 300, 21), (X + 520, uc + 330, 21),
               (X + 640, uc + 900, 21), (X + 560, uc + 1550, 21)]
        P["cords"] += pipe(pts, m.r(21))
        d = np.subtract(pts[-1], pts[-2])
        d = d / np.linalg.norm(d)
        a = np.add(pts[-1], d * -20) + (0, 0, 22)   # sits 2 mm into the ground, not tangent to it
        P["connector"] += [cyl(45, tuple(a), tuple(a + d * 150)), cone(40, 34, tuple(a + d * 146), tuple(a + d * 210))]
    # outdoor receptacle
    P["panels"].append(wbox(side, uc - 360, uc - 260, -3, 70, 1250, 1400))


# --------------------------------------------------------------------------- stairs

def timber_stair(m, xc):
    """Timber landing with closed-stringer steps out from the wall, 42 in guards."""
    xa, xb, ya, yb = xc - 750, xc + 750, Y, Y + 1220
    DT = FZ - 20
    GT = DT + 1070
    R, RUN, TD = (DT - PAD_T) / 5, 254.0, 290.0      # five equal risers, the last one onto the pad
    SW, ST = 915.0, 38.0
    gap = -1.0 if m.print_mode else 6.0
    frame, deck, posts, rails, blocks, stair = [], [], [], [], [], []
    jz0, jz1 = DT - 25 - 184, DT - 25
    frame += [box(xa, xb, ya - 12, ya + 38, jz0, jz1), box(xa, xb, yb - 38, yb, jz0, jz1),
              box(xa, xa + 38, ya, yb, jz0, jz1), box(xb - 38, xb, ya, yb, jz0, jz1)]
    frame += [box(x - 19, x + 19, ya, yb, jz0, jz1) for x in (xc - 380, xc, xc + 380)]
    n = 8
    bw = (yb - ya + 3 - (n - 1) * gap) / n
    deck += [box(xa - 25, xb + 25, ya - 3 + i * (bw + gap), ya - 3 + i * (bw + gap) + bw, DT - 25, DT) for i in range(n)]

    xs0, xs1 = xc - SW / 2 - ST, xc + SW / 2 + ST        # outer faces of the stringers
    pp = [(xa, ya + 38), (xb - 89, ya + 38), (xa, yb - 89), (xb - 89, yb - 89), (xs0 - 89, yb - 89), (xs1, yb - 89)]
    for x0, y0 in pp:
        posts.append(box(x0, x0 + 89, y0, y0 + 89, 140, GT - 36))
        cx, cy = x0 + 44.5, y0 + 44.5
        blocks.append(frustum((cx - 150, cx + 150, cy - 150, cy + 150, 0), (cx - 95, cx + 95, cy - 95, cy + 95, 160)))
    # guards: 2x6 cap, 2x4 bottom rail, 2x2 balusters
    bt = m.t(38)
    for xcen in (xa + 44.5, xb - 44.5):
        rails += [box(xcen - 70, xcen + 70, ya + 30, yb, GT - 38, GT),
                  box(xcen - 19, xcen + 19, ya + 127, yb - 89, DT + 60, DT + 149)]
        rails += [box(xcen - bt / 2, xcen + bt / 2, y - bt / 2, y + bt / 2, DT - 5, GT - 33)
                  for y in np.arange(ya + 127 + 70, yb - 89 - 40, 125)]
    ycen = yb - 44.5
    for x0, x1 in ((xa, xs0), (xs1, xb)):
        rails += [box(x0, x1, ycen - 70, ycen + 70, GT - 38, GT), box(x0, x1, ycen - 19, ycen + 19, DT + 60, DT + 149)]

    # steps
    slope = R / RUN

    def nose(y):
        return DT - R - (y - (yb + TD)) * slope

    DV = 300 / math.cos(math.atan(slope))
    for x0, x1 in ((xs0, xs0 + ST), (xs1 - ST, xs1)):
        y0, y1 = yb - 30, yb + 2000
        poly = [(y0, nose(y0) + 50), (y1, nose(y1) + 50), (y1, nose(y1) + 50 - DV), (y0, nose(y0) + 50 - DV)]
        stair.append(prism(clip_poly(poly, y0, y1, PAD_T - 5, DT), "x", x0, x1))
    treads = [box(xs0 + ST - 10, xs1 - ST + 10, yb + (k - 1) * RUN, yb + (k - 1) * RUN + TD, DT - k * R - 38, DT - k * R)
              for k in range(1, 5)]
    pad = box(xs0 - 220, xs1 + 220, yb + 690, yb + 1450, 0, PAD_T)
    # stair handrails: posts at the foot, sloped 2x4 cap and mid rail, balusters fixed to the stringers
    yp = yb + 1150
    top_a = GT - 19
    top_b = top_a - (yp + 44.5 - (yb - 44.5)) * slope
    for xp0 in (xs0 - 89, xs1):
        xcen = xp0 + 44.5
        posts.append(box(xp0, xp0 + 89, yp, yp + 89, PAD_T - 10, top_b - 10))
        rails.append(bar((xcen, yb - 44.5, top_a), (xcen, yp + 89, top_b - 44.5 * slope), 89, 38))
        rails.append(bar((xcen + (44.5 - 19) * (1 if xp0 > xc else -1), yb - 44.5, top_a - 480),
                         (xcen + (44.5 - 19) * (1 if xp0 > xc else -1), yp, top_b - 480), m.t(38), 89))
        xin = xp0 + 89 if xp0 < xc else xp0
        for y in np.arange(yb + 90, yp - 30, 125):
            zt = top_a - (y - (yb - 44.5)) * slope
            xb0 = xin - 5 if xp0 < xc else xin - 33
            rails.append(box(xb0, xb0 + bt, y - bt / 2, y + bt / 2, nose(y) + 50 - 140, zt - 14))
    m.add("landing_frame", PT_WOOD, frame)
    m.add("landing_deck", TIMBER, deck)
    m.add("stair_posts", PT_WOOD, posts)
    m.add("guards", PT_WOOD, rails)
    m.add("stringers", PT_WOOD, stair)
    m.add("treads", TIMBER, treads)
    m.add("deck_blocks", CONCRETE, blocks, pad)


def steel_stair(m, xc):
    """Prefab galvanised stair unit: grating landing on braced legs, steps along the wall to -X."""
    xa, xb, ya, yb = xc - 610, xc + 610, Y, Y + 1220
    DT = FZ - 20
    GT = DT + 1070
    R, RUN, TD = (DT - PAD_T) / 5, 254.0, 290.0
    st, legs, grip, pads, rail = [], [], [], [], []
    st.append(box(xa, xb, ya - 6, yb, DT - 40, DT))                                    # landing plate
    st += [box(xa, xb, ya, ya + 50, DT - 190, DT - 30), box(xa, xb, yb - 50, yb, DT - 190, DT - 30),
           box(xa, xa + 50, ya, yb, DT - 190, DT - 30), box(xb - 50, xb, ya, yb, DT - 190, DT - 30)]
    if not m.print_mode:
        grip += [box(xa + 30, xb - 30, y - 6, y + 6, DT, DT + 2) for y in np.arange(ya + 50, yb - 30, 55)]
    lp = [(xa + 15, ya + 70), (xb - 91, ya + 70), (xa + 15, yb - 91), (xb - 91, yb - 91)]
    for x0, y0 in lp:
        legs.append(box(x0, x0 + 76, y0, y0 + 76, 60, DT - 30))
        legs.append(box(x0 - 50, x0 + 126, y0 - 50, y0 + 126, 55, 55 + m.t(12)))
        pads.append(box(x0 - 110, x0 + 186, y0 - 110, y0 + 186, 0, 60))
    bt = m.t(14)
    legs += [bar((xa + 53, yb - 53, 200), (xb - 53, yb - 53, DT - 220), 60, bt, up=(0, 1, 0)),
             bar((xb - 53, yb - 53, 200), (xa + 53, yb - 53, DT - 220), 60, bt, up=(0, 1, 0)),
             bar((xb - 53, ya + 108, 200), (xb - 53, yb - 53, DT - 220), 60, bt, up=(1, 0, 0)),
             bar((xb - 53, yb - 53, 200), (xb - 53, ya + 108, DT - 220), 60, bt, up=(1, 0, 0))]

    # steps run down towards -X, outer stringer flush with the landing's outer edge
    slope = R / RUN
    ys0, ys1 = yb - 1015, yb                       # outer faces of the two stringers

    def nose(x):
        return DT - R - ((xa - TD) - x) * slope

    DV = 230 / math.cos(math.atan(slope))
    for y0, y1 in ((ys0, ys0 + 50), (ys1 - 50, ys1)):
        x0, x1 = xa - 2000, xa + 30
        poly = [(x1, nose(x1) + 40), (x0, nose(x0) + 40), (x0, nose(x0) + 40 - DV), (x1, nose(x1) + 40 - DV)]
        st.append(prism(clip_poly(poly, x0, x1, PAD_T - 5, DT - 10), "y", y0, y1))
    treads = [box(xa - (k - 1) * RUN - TD, xa - (k - 1) * RUN, ys0 + 40, ys1 - 40, DT - k * R - 40, DT - k * R)
              for k in range(1, 5)]
    if not m.print_mode:
        for k in range(1, 5):
            xt0 = xa - (k - 1) * RUN - TD
            grip += [box(x - 6, x + 6, ys0 + 70, ys1 - 70, DT - k * R, DT - k * R + 2)
                     for x in np.arange(xt0 + 35, xt0 + TD - 20, 50)]
    pads.append(box(xa - 1450, xa - 780, ys0 - 120, ys1 + 120, 0, PAD_T))

    # pipe handrails: landing guard, then both sides of the steps
    r = m.r(21)
    pa, pb, pc = (xb - 35, yb - 35), (xa + 35, yb - 35), (xb - 35, ya + 75)
    rail += pipe([(pc[0], pc[1], GT), (pa[0], pa[1], GT), (pb[0], pb[1], GT)], r)
    rail += pipe([(pc[0], pc[1], DT + 520), (pa[0], pa[1], DT + 520), (pb[0], pb[1], DT + 520)], r)
    rail += [cyl(r, (x, y, DT - 30), (x, y, GT)) for x, y in (pa, pb, pc)]
    xf = xa - 1150                                   # foot posts, on the pad
    zf = GT - (pb[0] - xf) * slope
    for y in (ys1 - 25, ys0 + 25):
        xtop = pb[0] if y > yb - 100 else xa - 60
        ztop = GT - (pb[0] - xtop) * slope
        rail += pipe([(xf, y, PAD_T - 10), (xf, y, zf), (xtop, y, ztop)], r)
        rail.append(cyl(r, (xf + 20, y, zf - 470), (xtop, y, ztop - 470)))
        if xtop != pb[0]:
            rail.append(cyl(r, (xtop, y, nose(xtop) - 60), (xtop, y, ztop)))
    m.add("steel_stair", GALV, st, legs, treads)
    m.add("steel_stair_rails", GALV, rail)
    m.add("stair_grip", DARK, grip)
    m.add("stair_pavers", CONCRETE, pads)


# --------------------------------------------------------------------------- under-carriage

def chassis(m):
    bf, tf, tw = 102.0, m.t(8.4), m.t(6.1)
    z0, z1 = ZI0, ZB + 5
    rails = []
    for s in (1, -1):
        y = s * RY
        prof = [(y - bf / 2, z0), (y + bf / 2, z0), (y + bf / 2, z0 + tf), (y + tw / 2, z0 + tf), (y + tw / 2, z1 - tf),
                (y + bf / 2, z1 - tf), (y + bf / 2, z1), (y - bf / 2, z1), (y - bf / 2, z1 - tf), (y - tw / 2, z1 - tf),
                (y - tw / 2, z0 + tf), (y - bf / 2, z0 + tf)]
        rails.append(prism(prof, "x", -X + 120, X - 60))
        for xo in np.linspace(-X + 400, X - 400, 11):
            out = [(s * (RY + 10), ZB + 5), (s * (Y - 15), ZB + 5), (s * (Y - 15), ZB - 60), (s * (RY + 10), ZB - 170)]
            rails.append(prism(out, "x", xo - 30, xo + 30))
    rails += [box(x - 40, x + 40, -RY, RY, ZB - 150, ZB + 5) for x in (-X + 160, -3000, 0, 3000, X - 100)]

    # tie-downs: galvanised straps from the main rails to ground anchors
    straps, anchors = [], []
    for s in (1, -1):
        for x in (-4300.0, 0.0, 4300.0):
            straps.append(bar((x, s * (RY + 35), z0 + 5), (x, s * 1340, 105), m.t(32), m.t(4)))
            anchors += [cyl(55, (x, s * 1340, 0), (x, s * 1340, 70)), cyl(38, (x, s * 1340, 70), (x, s * 1340, 125))]
    m.add("main_rails", CHASSIS, rails)
    m.add("tie_down_straps", GALV, straps, anchors)

    # piers: pad, two courses of cross-laid CMU, timber cap, a pair of shim wedges
    g = -1.0 if m.print_mode else 6.0
    pads, cmu, caps, wedges = [], [], [], []
    for s in (1, -1):
        y = s * RY
        for xp in (-5400.0, -3250.0, -1100.0, 1100.0, 3250.0, 5400.0):
            pads.append(box(xp - 230, xp + 230, y - 230, y + 230, 0, 50))
            for k in (-1, 1):
                cmu.append(box(xp + k * g / 2, xp + k * (194 + g / 2), y - 198, y + 198, 50, 244))
                cmu.append(box(xp - 198, xp + 198, y + k * g / 2, y + k * (194 + g / 2), 244 - (1 if g < 0 else 0), 438))
            caps.append(box(xp - 205, xp + 205, y - 120, y + 120, 437, 476))
            wedges.append(prism([(xp - 160, 475), (xp + 160, 475), (xp + 160, ZI0 + 3), (xp - 160, 481)], "y", y - 50, y))
            wedges.append(prism([(xp - 160, 475), (xp + 160, 475), (xp + 160, 481), (xp - 160, ZI0 + 3)], "y", y, y + 50))
    m.add("pier_pads", CONCRETE, pads)
    m.add("pier_blocks", CMU, cmu)
    m.add("pier_caps", TIMBER, caps)
    m.add("pier_wedges", TIMBER_DARK, wedges)


def tongue(m):
    """Bolt-on A-frame tow tongue with coupler, safety chains and a side-wind jack."""
    TX = X + 1750.0
    zt0, zt1 = 560.0, 716.0
    zc = (zt0 + zt1) / 2
    xs = X - 900.0
    frame = []

    def ym(x):
        return 880 - 825 * (x - xs) / (TX - 40 - xs)

    for s in (1, -1):
        frame.append(bar((xs, s * 880, zc), (TX - 40, s * 55, zc), m.t(76), zt1 - zt0))
        frame += [cyl(m.r(22), (x, s * (ym(x) + 45), zc + 40), (x, s * (ym(x) - 60), zc + 40)) for x in (X - 300, X - 600)]
    frame.append(box(X + 260, X + 340, -ym(X + 300), ym(X + 300), zt0 + 20, zt1 - 20))
    frame.append(box(TX - 320, TX + 20, -100, 100, zt0, zt1))
    m.add("tongue", CHASSIS, frame)

    # coupler
    # coupler: cast body rising to a rounded nose (the ball-socket hood), as wide as the body, with the latch lever
    rc = 64.0
    coup = [box(TX - 300, TX + 60, -95, 95, zt1 - 5, zt1 + 22),
            prism([(TX - 260, zt1 + 15), (TX + 175, zt1 + 15), (TX + 175, zt1 + 80 + rc), (TX - 200, zt1 + 60)],
                  "y", -rc, rc),
            sphere(rc, (TX + 175, 0, zt1 + 80))]
    m.add("coupler", COUPLER, coup)
    m.add("coupler_latch", DARK, bar((TX - 40, 0, zt1 + 104), (TX + 165, 0, zt1 + 150), m.t(40), m.t(26)),
          cyl(m.r(16), (TX - 30, -rc - 8, zt1 + 104), (TX - 30, rc + 8, zt1 + 104)))

    # safety chains, crossed under the coupler and hooked back
    chains = []
    for s in (1, -1):
        y0 = ym(TX - 300)
        pts = [(TX - 300, s * y0, zt0 + 20), (TX - 200, s * (y0 - 10), 420), (TX - 40, s * 60, 360),
               (TX + 80, -s * 20, 400), (TX + 110, -s * 30, zt1 + 10)]
        chains += pipe(pts, m.r(9))
        chains.append(box(TX + 85, TX + 135, -s * 30 - 25, -s * 30 + 25, zt1 - 10, zt1 + 40))
    m.add("safety_chains", GALV, chains)

    # side-wind tongue jack on a timber pad
    JX = X + 1150.0
    yj = ym(JX) + 38 + 48
    jack = [box(JX - 75, JX + 75, ym(JX) - 15, yj + 15, zt0 + 10, zt1 - 10),
            cyl(48, (JX, yj, 380), (JX, yj, 1150)), cyl(58, (JX, yj, 1150), (JX, yj, 1240))]
    m.add("jack", BLACK, jack)
    m.add("jack_leg", STEEL, cyl(34, (JX, yj, 80), (JX, yj, 400)), cyl(115, (JX, yj, 65), (JX, yj, 90)))
    m.add("jack_crank", CHROME_DARK, pipe([(JX, yj + 40, 1195), (JX, yj + 150, 1195), (JX + 10, yj + 150, 1010)], m.r(13)),
          cyl(m.r(19), (JX + 10, yj + 150, 1010), (JX + 10, yj + 260, 1010)))
    m.add("jack_pad", TIMBER_DARK, box(JX - 220, JX + 220, yj - 180, yj + 180, 0, 75))


# --------------------------------------------------------------------------- build

def build(m):
    P = {k: [] for k in ("dark", "blinds", "glass", "frames", "latches", "trim", "doors", "casing", "gaskets",
                         "chrome", "hinges", "light_housings", "lamps", "hvac", "hvac_dark", "labels", "panels",
                         "cords", "conduit", "connector")}
    shell(m, P)
    for side, uc, w, kind, opt in OPENINGS:
        if kind == "win":
            window(m, P, side, uc, w, opt)
        else:
            door(m, P, side, uc, opt)

    for side, uc, ud in AC_UNITS:
        wall_ac(m, P, side, uc, ud)
    service_panel(m, P, "+x", 700.0)
    for side, uw in (("+x", 700.0), ("-x", -700.0)):
        wall_light(P, side, uw, 2990.0)
    # permit / plan box beside the main door
    P["panels"] += [wbox("+y", D1_X + 830, D1_X + 1150, -3, 110, 1450, 1880),
                    wbox("+y", D1_X + 815, D1_X + 1165, -3, 135, 1880, 1915)]
    P["hvac_dark"].append(wbox("+y", D1_X + 960, D1_X + 1020, 108, 120, 1780, 1820))

    # sign between the middle windows
    e = max(2.0, 0.3 * m.scale) if m.print_mode else 2.5
    sz0, sz1 = 2250.0, 2650.0
    sf = rib_depth(m) + 14                       # sign face, standing clear of the ribs behind it
    m.add("sign_panel", BLUE, wbox("+y", -650, 650, 6, sf, sz0, sz1))
    legend = [wbox("+y", -620, 620, sf - 1, sf - 1 + e, z, z + 16) for z in (sz0 + 28, sz1 - 44)]
    legend += [wbox("+y", u, u + 16, sf - 1, sf - 1 + e, sz0 + 28, sz1 - 28) for u in (-620, 604)]
    legend.append(text("SITE OFFICE", 150, e + 1, wpt("+y", 0, sf - 1, (sz0 + sz1) / 2), (-1, 0, 0), (0, 1, 0)))
    m.add("sign_legend", WHITE, legend)

    m.add("window_backs", DARK, P["dark"])
    m.add("blinds", BLINDS, P["blinds"])
    m.add("glass", GLASS, P["glass"])
    m.add("window_frames", ALU, P["frames"])
    m.add("window_latches", DARK, P["latches"])
    m.add("drip_caps", TRIM, P["trim"])
    m.add("doors", DOOR, P["doors"])
    m.add("door_casings", TRIM, P["casing"])
    m.add("vision_lite_gaskets", BLACK, P["gaskets"])
    m.add("door_hardware", STEEL, P["chrome"])
    m.add("hinges_kick_plates", STEEL, P["hinges"])
    m.add("light_housings", DARK, P["light_housings"])
    m.add("lamps", LED, P["lamps"])
    m.add("hvac_units", HVAC, P["hvac"])
    m.add("hvac_grilles_brackets", DARK, P["hvac_dark"])
    m.add("labels", WHITE, P["labels"])
    m.add("electrical_boxes", PANEL, P["panels"])
    m.add("conduit", GALV, P["conduit"])
    m.add("cords_drains", RUBBER, P["cords"])
    m.add("cord_connector", YELLOW, P["connector"])

    timber_stair(m, D1_X)
    steel_stair(m, D2_X)
    chassis(m)
    tongue(m)
