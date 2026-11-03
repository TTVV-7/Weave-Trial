"""Electric slab scissor lift, 26 ft class, 46 in wide, shown raised with the deck at 3.9 m.

Chassis: a low steel slab chassis on four 15 x 5 in solid non-marking tyres (rear drive,
front steer), steel rims recessed in the tyre faces with hub caps and wheel nuts. Swing-out
side trays between the wheels - batteries on the left, hydraulic power unit and controller on
the right - with louvred covers, latches and handles; the ground control box (key switch,
emergency stop, lift toggle) on the left tray, emergency-lowering knob and charger inlet on
the right. Pothole protection bars deployed down along both sides on link arms; rubber end
bumpers, tie-down / lifting lugs at the corners, a flashing beacon on the front end and a
three-step entry ladder bolted to the rear end below the gate.
Scissor stack: five stages of crossed arm pairs on each side, in an inner and an outer arm
plane. Each arm runs pin to pin; the two arms of a stage cross at their middles on a centre
pin, and each arm end joins the next stage's arm on a common joint pin, so the inner arms make
one zig-zag chain and the outer arms another. Cross tubes tie left and right at every joint.
At the bottom the inner chain is pinned in fixed brackets at the rear of the chassis and the
outer chain runs on rollers in tracks at the front; at the top the outer chain is pinned under
the rear of the platform and the inner chain rolls in tracks under its front end, so the deck
stays level over the chassis. One lift cylinder lies in the middle of the stack between cross
tubes on the first and second stages. The platform cable zig-zags down the left inner arms, and
a red maintenance safety prop is stowed along the right first-stage inner arm; rubber rest pads
on the chassis deck take the arms when stowed.
Platform: steel deck on an orange skirt frame, 2.27 x 1.12 m, with a 1.5 m long, 0.98 m wide
roll-out extension deck run out 0.6 m at the front (its own floor, toeboards and rails, running
inside the main posts and guided by clamps on the main rails), 1.1 m guardrails with mid rails
on round posts, toeboards, fold-down hinge brackets with ring-pull quick pins at the post feet,
a spring saloon gate at the rear entry, the platform control box (dark housing, yellow panel,
joystick and emergency stop) hung on the left top rail mid-way along the main deck, a manual
holder, four lanyard anchor rings on the deck, and a locking pedal on the extension deck.

Dimensions are typical figures for the 26 ft (7.9 m maximum platform height), 46 in wide class
of electric slab scissors, not any one machine:
  chassis 2.44 m long, 1.17 m (46 in) wide, deck top 0.48 m; wheelbase 1.85 m
  tyres 381 x 127 mm (15 x 5 in) solid, sunk 3 mm (1.5 % of the radius) for the print
  arms 2.05 m pin to pin, 130 x 55 mm section, five stages, here at about 18 deg
  platform 2.27 x 1.12 m, extension deck 1.5 x 0.98 m, 0.9 m travel (shown 0.6 m out), rails 1.1 m
  deck raised to 3.9 m; overall about 2.98 m long, 1.21 m wide over the ground controls,
  5.03 m high as shown (to the rail caps)
Generic and brand-neutral: no names, logos or maker-specific styling.
"""

import math

import numpy as np

from cadkit import Finish, bar, box, cut, cyl, pipe, rgb, sphere, torus
from finishes import AMBER, BLACK, CHROME, DARK, GALV, GREEN, ORANGE, RED, RUBBER, STEEL, WHITE, YELLOW

ASSET = dict(key="scissor_lift", stem="Electric_Scissor_Lift_26ft",
             title="Electric Scissor Lift (26 ft class, raised)", az=40, el=15, size="900x1200")

DECK = Finish(rgb("#7f8489"), metal=0.55, rough=0.55)      # galvanised / painted steel deck plate
NYLON = Finish(rgb("#2a2b2d"), rough=0.5)                   # slide rollers

# ---------------------------------------------------------------- chassis (mm)
XC, YC = 1220.0, 585.0          # chassis half length (2,440), half width (1,170 = 46 in)
ZCB, ZCT = 110.0, 480.0         # bottom of the chassis spine, top of the chassis deck plate
RT = 190.5                      # 15 in solid tyre
ZW = RT * (1 - 0.015)           # axle height: tyre sunk 1.5 % of its radius
XWH = 925.0                     # half wheelbase (1,850)
YT0, YT1 = 450.0, 577.0         # tyre |Y| (127 mm = 5 in wide)

# ---------------------------------------------------------------- scissor stack
NST = 5                         # stages
Z0 = 540.0                      # bottom pins
DECKZ = 3900.0                  # platform deck height as shown
Z5 = DECKZ - 230.0              # top pins
HST = (Z5 - Z0) / NST           # rise per stage
LARM = 2050.0                   # arm length pin to pin
SPAN = math.sqrt(LARM ** 2 - HST ** 2)
XR, XF = -SPAN / 2, SPAN / 2    # rear (fixed) and front (rolling) pin stations
AD, AW = 130.0, 55.0            # arm depth (in its plane) and width (Y)
YI0 = 370.0                     # inner face of the inner arm plane

# ---------------------------------------------------------------- platform
PX0, PX1, PY = -1190.0, 1080.0, 560.0     # main deck 2,270 x 1,120
EXT_OUT, EXT_L = 600.0, 1500.0            # extension deck: run out, length
EX1 = PX1 + EXT_OUT
EX0 = EX1 - EXT_L
EY = 492.0                                # extension deck half width, inside the main posts and hinges
RAIL = 1100.0                             # guardrail height
YR = 538.0                                # main rail centre |Y|
YE = 470.0                                # extension rail centre |Y|
XRR = -1165.0                             # rear rail / gate line
YG = 300.0                                # gate post |Y|


def ys(s, a, b):
    """The |Y| range a..b on side s (+1 left, -1 right), sorted."""
    return tuple(sorted((s * a, s * b)))


def ax_y(r, x, z, y0, y1):
    """Cylinder of radius r along Y at (x, z)."""
    return cyl(r, (x, y0, z), (x, y1, z))


def ax_x(r, y, z, x0, x1):
    return cyl(r, (x0, y, z), (x1, y, z))


def ax_z(r, x, y, z0, z1):
    return cyl(r, (x, y, z0), (x, y, z1))


def chain(front_first):
    """Pin stations (x, z) of one zig-zag arm chain, bottom to top."""
    return [((XF if (k % 2 == 0) == front_first else XR), Z0 + k * HST) for k in range(NST + 1)]


def lerp(p, q, t):
    return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)


# ================================================================ build

def build(m):
    t, r = m.t, m.r
    gap = -1.0 if m.print_mode else 12.0      # washer gap between the arm planes
    YI1 = YI0 + AW
    YO0 = YI1 + gap
    YO1 = YO0 + AW
    planes = {"inner": (YI0, YI1), "outer": (YO0, YO1)}
    c_in, c_out = chain(False), chain(True)   # inner chain fixed at the rear-bottom

    # ------------------------------------------------------------ chassis
    m.add("chassis_spine", ORANGE, box(-1180, 1180, -440, 440, ZCB, ZCT - 30))
    m.add("chassis_deck", ORANGE, box(-XC, XC, -YC, YC, ZCT - 40, ZCT))
    m.add("chassis_ends", ORANGE, [box(sx * 1125, sx * XC, -YC, YC, 150, ZCT - 30) for sx in (1, -1)])
    m.add("bumpers", BLACK, [box(sx * (XC - 10), sx * (XC + 28), -520, 520, 290, 410) for sx in (1, -1)])
    # deck edge trim and wheel-well lips
    m.add("deck_edge", DARK, [box(-XC, XC, s * YC, s * (YC - 6), ZCT - 6, ZCT + 4) for s in (1, -1)])

    # side trays between the wheels: batteries left, hydraulics / controller right
    trays, louvres, latches = [], [], []
    for s in (1, -1):
        trays.append(box(-715, 715, s * 430, s * (YC - 4), 125, ZCT - 35))
        trays.append(box(-705, 705, s * (YC - 6), s * YC, 135, ZCT - 45))     # cover panel
        lx0, lx1 = (-640, -120) if s > 0 else (-300, 300)
        louvres += [box(lx0, lx1, s * (YC - 2), s * (YC + 7), z, z + 22) for z in range(200, 400, 42)]
        latches += [box(x - 22, x + 22, s * (YC - 2), s * (YC + 14), 400, 440) for x in (-660, 660)]
        latches += [box(x - 30, x + 30, s * (YC - 2), s * (YC + 10), 140, 168) for x in (-560, 560)]   # hinges
        latches += [box(x - 15, x + 15, s * (YC - 2), s * (YC + 16), 158, 182) for x in (lx0 + 60, lx1 - 60)]
        latches.append(box(lx0 + 45, lx1 - 45, s * (YC + 6), s * (YC + 6 + t(10)), 163, 177))     # grab handle
    m.add("side_trays", ORANGE, trays)
    m.add("tray_louvres", DARK, louvres)
    m.add("tray_latches", BLACK, latches)
    if not m.print_mode:     # lid seams round the tray tops
        m.add("tray_lid_seams", DARK, [box(-715, 715, s * 436, s * 444, ZCT, ZCT + 2) for s in (1, -1)],
              [box(x - 4, x + 4, s * 440, s * YC, ZCT, ZCT + 2) for x in (-715, 715) for s in (1, -1)])

    # ground control box on the left tray
    m.add("ground_control_box", DARK, box(140, 560, YC - 30, YC + 4, 215, 425))
    m.add("ground_estop", RED, ax_y(r(26), 470, 355, YC, YC + 10), ax_y(38, 470, 355, YC + 8, YC + 20))
    m.add("ground_key_switch", BLACK, ax_y(r(20), 330, 355, YC, YC + 12))
    m.add("ground_toggle", STEEL, ax_y(30, 230, 355, YC, YC + 8), ax_y(r(8), 230, 355, YC + 4, YC + 22))
    m.add("ground_lamp", GREEN, ax_y(14, 230, 270, YC, YC + 8))
    if not m.print_mode:
        m.add("decals", WHITE, box(300, 520, YC + 4, YC + 5, 240, 300),
              box(-300, 300, -YC - 1, -YC, 405, 432), box(160, 300, YC + 4, YC + 5, 390, 410))
    # right tray: emergency lowering knob and charger inlet
    m.add("emergency_lowering", RED, ax_y(r(12), 520, 300, -YC + 2, -YC - 12), ax_y(30, 520, 300, -YC - 10, -YC - 20))
    m.add("charger_inlet", BLACK, box(-560, -420, -YC + 2, -YC - 12, 280, 400),
          ax_y(30, -490, 340, -YC - 10, -YC - 20))

    # pothole protection, deployed down along both sides
    ph = []
    for s in (1, -1):
        ph.append(box(-640, 640, s * 545, s * 590, 32, 88))
        ph.append(box(-640, 640, s * 545, s * 560, 88, 112))
        for x in (-520, 520):
            ph.append(bar((x, s * 552, 80), (x - math.copysign(110, x), s * 552, 160), t(22), 34, up=(0, 1, 0)))
            ph.append(ax_y(22, x - math.copysign(110, x), 150, s * 538, s * 566))
    m.add("pothole_guards", BLACK, ph)

    # tie-down / lifting lugs at the corners
    lugs = []
    for sx in (1, -1):
        for s in (1, -1):
            lug = box(sx * (XC - 10), sx * (XC + 70), s * 380 - t(14) / 2, s * 380 + t(14) / 2, 160, 280)
            lugs.append(cut(lug, ax_y(26, sx * (XC + 35), 225, -2000, 2000)))
    m.add("tie_down_lugs", DARK, lugs)

    # beacon on the front end
    m.add("beacon_base", BLACK, box(1110, 1200, -45, 45, ZCT - 5, ZCT + 30))
    m.add("beacon", AMBER, ax_z(42, 1155, 0, ZCT + 28, ZCT + 110), sphere(42, (1155, 0, ZCT + 110)))

    # entry ladder bolted to the rear end
    lad = []
    xl0, xl1 = -XC - 42, -XC - 12
    lw = t(30)                                   # side rail section
    yl = 255 + lw / 2                            # rungs run halfway into the rails
    for s in (1, -1):
        lad.append(box(xl1 - lw, xl1, s * 255, s * (255 + lw), 140, 1060))
        lad += [box(-XC - 20, -XC + 8, s * 250, s * (260 + lw), z, z + 50) for z in (190, 380)]
    lad += [box(xl0 - 45, xl1, -yl, yl, z, z + t(28)) for z in (330, 580, 830)]
    lad += [box(xl0 - 45, xl0 - 45 + t(10), -yl, yl, z - 30, z + t(28)) for z in (330, 580, 830)]
    m.add("ladder", GALV, lad)

    # ------------------------------------------------------------ wheels
    for xw in (XWH, -XWH):
        for s in (1, -1):
            yo = s * YT1
            tyre = cyl(RT - 9, (xw, s * YT0, ZW), (xw, yo, ZW)).fuse(cyl(RT, (xw, s * (YT0 + 8), ZW), (xw, s * (YT1 - 8), ZW)))
            tyre = cut(tyre, ax_y(128, xw, ZW, s * (YT1 - 10), s * (YT1 + 5)))
            m.add("tyre", RUBBER, tyre)
            m.add("rim", DARK, ax_y(126, xw, ZW, s * (YT0 + 6), s * (YT1 - 8)))
            nuts = [ax_y(r(10), xw + 82 * math.cos(a), ZW + 82 * math.sin(a), s * (YT1 - 10), s * (YT1 + 4))
                    for a in np.linspace(0, 2 * math.pi, 6, endpoint=False)]
            m.add("hub", STEEL, ax_y(58, xw, ZW, s * (YT1 - 10), s * (YT1 + 14)), nuts)
            m.add("axle_hub", DARK, ax_y(72, xw, ZW, s * 400, s * (YT0 + 10)))

    # ------------------------------------------------------------ scissor stack
    arms, bosses, pins, heads, tubes, washers = [], [], [], [], [], []
    pr, hr = r(22), 32.0
    hy0, hy1 = (0.0, t(10)) if m.print_mode else (6.0, 16.0)   # retainer heads: print flush and thick
    for s in (1, -1):
        for name, ch in (("inner", c_in), ("outer", c_out)):
            y0, y1 = planes[name]
            yc = s * (y0 + y1) / 2
            for k in range(NST):
                p, q = ch[k], ch[k + 1]
                arms.append(bar((p[0], yc, p[1]), (q[0], yc, q[1]), AW, AD))
            for (x, z) in ch:
                bosses.append(ax_y(AD / 2, x, z, *ys(s, y0, y1)))
                pins.append(ax_y(pr, x, z, *ys(s, y0 - 12, y1 + 12)))
                heads.append(ax_y(hr, x, z, *ys(s, y1 + hy0, y1 + hy1)))
        for k in range(NST):         # centre pins, where the two arms of a stage cross
            zc = Z0 + (k + 0.5) * HST
            pins.append(ax_y(pr, 0, zc, *ys(s, YI0 - 12, YO1 + 12)))
            heads.append(ax_y(hr, 0, zc, *ys(s, YO1 + hy0, YO1 + hy1)))
            washers.append(ax_y(44, 0, zc, *ys(s, YI1 - 2, YO0 + 2)))
    # cross tubes at every pin station of each chain
    for (x, z) in c_in:
        tubes.append(ax_y(40, x, z, -(YI0 + 6), YI0 + 6))
    for (x, z) in c_out:
        tubes.append(ax_y(40, x, z, -(YO0 + 6), YO0 + 6))
    m.add("scissor_arms", ORANGE, arms, bosses)
    m.add("cross_tubes", ORANGE, tubes)
    m.add("arm_pins", STEEL, pins, washers)
    m.add("pin_retainers", DARK, heads)

    # bottom: fixed pivot brackets (inner chain, rear) and roller tracks (outer chain, front)
    lt = tw = t(16)                    # bracket plates; track wall and lip
    brk, track, rollers = [], [], []
    for s in (1, -1):
        for ya, yb in ((YI0 - 4 - lt, YI0 - 4), (YI1 + 4, YI1 + 4 + lt)):
            brk.append(box(XR - 85, XR + 85, s * ya, s * yb, ZCT - 5, Z0))
            brk.append(ax_y(80, XR, Z0, *ys(s, ya, yb)))
        # bottom roller (outer arm, front), outboard of the arm
        rollers.append(ax_y(62, XF, Z0, *ys(s, YO1 - 3, YO1 + 36)))
        track.append(box(560, 1180, s * (YO1 - 2), s * (YO1 + 62), ZCT - 8, Z0 - 59))
        track.append(box(560, 1180, s * (YO1 + 58 - tw), s * (YO1 + 58), ZCT - 8, Z0 + 66 + tw))
        track.append(box(560, 1180, s * (YO1 + 6), s * (YO1 + 58), Z0 + 66, Z0 + 66 + tw))
        # top: fixed brackets under the platform (outer chain, rear)
        for ya, yb in ((YO0 - 4 - lt, YO0 - 4), (YO1 + 4, YO1 + 4 + lt)):
            brk.append(box(XR - 80, XR + 80, s * ya, s * yb, Z5, DECKZ - 145))
            brk.append(ax_y(75, XR, Z5, *ys(s, ya, yb)))
        # top roller (inner arm, front) in a track under the platform
        rollers.append(ax_y(60, XF, Z5, *ys(s, YI1 - 3, YI1 + 36)))
        track.append(box(430, PX1 - 10, s * (YI1 - 2), s * (YI1 + 44), Z5 + 57, DECKZ - 145))
    m.add("pivot_brackets", DARK, brk)
    # rubber pads the stowed arms rest on
    m.add("stack_rest_pads", BLACK, [box(x - 60, x + 60, *ys(s, YI0 - 5, YO1 + 5), ZCT - 2, ZCT + 34)
                                     for x in (-420, 420) for s in (1, -1)])
    m.add("roller_tracks", DARK, track)
    m.add("slide_rollers", NYLON, rollers)

    # lift cylinder, between cross tubes on the first and second stages, in the middle
    A = lerp(c_in[0], c_in[1], 0.25)
    B = lerp(c_out[1], c_out[2], 0.75)
    m.add("cylinder_tubes", ORANGE, ax_y(42, A[0], A[1], -(YI0 + 6), YI0 + 6),
          ax_y(42, B[0], B[1], -(YO0 + 6), YO0 + 6))
    a3, b3 = np.array([A[0], 0, A[1]]), np.array([B[0], 0, B[1]])
    u = (b3 - a3) / np.linalg.norm(b3 - a3)
    j = a3 + (b3 - a3) * 0.6
    T = lambda p: tuple(map(float, p))      # noqa: E731
    m.add("lift_cylinder", DARK, cyl(62, T(a3 + u * 40), T(j)), cyl(68, T(a3 + u * 40), T(a3 + u * 120)),
          cyl(68, T(j - u * 70), T(j)), ax_y(48, A[0], A[1], -55, 55),
          [box(A[0] - 50, A[0] + 50, sy * 55, sy * 75, A[1] - 50, A[1] + 50) for sy in (1, -1)])
    m.add("lift_cylinder_rod", CHROME, cyl(r(32), T(j - u * 20), T(b3 - u * 40)), ax_y(45, B[0], B[1], -50, 50))
    m.add("cylinder_hose", BLACK, pipe([T(a3 + u * 100 + np.array([0, 60, 0])), (A[0] - 120, 60, A[1] - 40),
                                        (A[0] - 250, 60, ZCT + 10)], r(14)))
    # platform cable zig-zagging down the left inner arms
    yc_cab = YI0 - 12
    cab = [(c_in[0][0] - 180, yc_cab, ZCT + 5)] + [(x, yc_cab, z) for x, z in c_in] + \
          [(XF - 160, yc_cab, DECKZ - 140)]
    m.add("platform_cable", BLACK, pipe(cab, r(14)))
    # maintenance safety prop, stowed along the inside of the right first-stage inner arm
    p, q = c_in[0], c_in[1]
    d = np.array([q[0] - p[0], q[1] - p[1]]) / LARM
    nrm = np.array([d[1], -d[0]]) * 40           # towards the arm's lower edge
    a2, b2 = np.array(lerp(p, q, 0.33)) + nrm, np.array(lerp(p, q, 0.8)) + nrm
    yp = -(YI0 - 12)
    m.add("safety_prop", RED, bar((a2[0], yp, a2[1]), (b2[0], yp, b2[1]), t(26), 38),
          ax_y(30, a2[0], a2[1], -(YI0 + 2), -(YI0 - 30)))

    # ------------------------------------------------------------ platform
    m.add("platform_frame", ORANGE, box(PX0, PX1, -PY, PY, DECKZ - 150, DECKZ - 8))
    m.add("platform_ribs", ORANGE, [box(x - 40, x + 40, -PY + 20, PY - 20, DECKZ - 172, DECKZ - 148)
                                    for x in (-700, -120, 460)])
    m.add("deck", DECK, box(PX0 + 8, PX1 - 4, -PY + 8, PY - 8, DECKZ - 10, DECKZ))
    tb = t(6)
    toe = [box(PX0, PX1, s * PY, s * (PY - tb), DECKZ - 4, DECKZ + 150) for s in (1, -1)]
    toe += [box(PX0, PX0 + tb, s * YG, s * PY, DECKZ - 4, DECKZ + 150) for s in (1, -1)]
    m.add("toeboards", ORANGE, toe)
    if not m.print_mode:
        grip = [box(x - 70, x + 70, y - 12, y + 12, DECKZ, DECKZ + 1.5)
                for x in np.arange(-1050, 1000, 230) for y in (-380, -130, 130, 380)]
        m.add("deck_grip", DARK, grip)
        m.add("platform_decals", WHITE, [box(x0, x1, s * PY, s * (PY + 1), DECKZ - 125, DECKZ - 35)
                                         for s in (1, -1) for x0, x1 in ((-950, -600), (-450, -300))])

    # guardrails: round posts, top and mid rails
    rr = r(21)
    rails, caps = [], []
    zt, zm = DECKZ + RAIL, DECKZ + 560
    posts_x = (XRR, -420.0, 330.0, PX1 - 25)
    for s in (1, -1):
        y = s * YR
        rails += [ax_z(rr, x, y, DECKZ - 4, zt) for x in posts_x]
        rails += [ax_x(rr, y, z, XRR, PX1 - 25) for z in (zt, zm)]
        rails += [cyl(rr, (XRR, s * YG, z), (XRR, y, z)) for z in (zt, zm)]
        rails.append(ax_z(rr, XRR, s * YG, DECKZ - 4, zt))
        caps += [sphere(rr + 6, (x, y, zt)) for x in posts_x]
        caps.append(sphere(rr + 6, (XRR, s * YG, zt)))
    m.add("guardrails", GALV, rails, caps)
    # fold-down hinge brackets and quick pins at the post feet
    hinge, qpins = [], []
    for s in (1, -1):
        for x in posts_x:
            hinge.append(box(x - 38, x + 38, s * (YR - 40), s * (PY - 3), DECKZ + 30, DECKZ + 140))
            qpins.append(ax_x(r(9), s * (YR - 20), DECKZ + 100, x - 60, x + 72))
            qpins.append(torus(22 + r(5), r(5), (x + 66, s * (YR - 20), DECKZ + 80), (0, 1, 0)))   # pull ring
    m.add("rail_hinges", GALV, hinge)
    m.add("rail_quick_pins", RED, qpins)

    # saloon entry gate at the rear
    gate = []
    gr = r(18)
    for s in (1, -1):
        y_end = s * ((gr - 8) if m.print_mode else 32)     # print: the leaves fuse at the centreline
        gate += [cyl(gr, (XRR, s * (YG - 10), z), (XRR, y_end, z)) for z in (DECKZ + 1060, DECKZ + 560)]
        gate.append(ax_z(gr, XRR, y_end, DECKZ + 540, DECKZ + 1080))
        gate.append(sphere(gr + 2, (XRR, y_end, DECKZ + 1060)))
        gate += [ax_z(30, XRR, s * YG, z - 40, z + 40) for z in (DECKZ + 1060, DECKZ + 560)]
    m.add("entry_gate", YELLOW, gate)

    # extension deck, rolled out at the front
    ey = 528.0 if m.print_mode else EY       # print: wider, so the extension rails sit on its toeboards
    m.add("extension_deck", DECK, box(EX0, EX1, -ey, ey, DECKZ - 2, DECKZ + 30))
    m.add("extension_nose", ORANGE, box(PX1 - 2, EX1, -ey, ey, DECKZ - 110, DECKZ),
          box(EX0, EX0 + 40, -ey, ey, DECKZ + 20, DECKZ + 60))
    etoe = [box(EX0, EX1, s * ey, s * (ey - tb), DECKZ + 26, DECKZ + 180) for s in (1, -1)]
    etoe.append(box(EX1 - tb, EX1, -ey, ey, DECKZ + 26, DECKZ + 180))
    m.add("extension_toeboards", ORANGE, etoe)
    er = r(20)
    YE_ = YR - 25 if m.print_mode else YE      # print: fuse the two rail runs rather than leave a hairline
    ezt, ezm = DECKZ + RAIL - 30, DECKZ + 545
    xf_post, xr_post = EX1 - 25, EX0 + 80
    erails = []
    for s in (1, -1):
        y = s * YE_
        erails += [ax_z(er, x, y, DECKZ + 26, ezt) for x in (xf_post, xr_post, (xf_post + xr_post) / 2)]
        erails += [ax_x(er, y, z, xr_post, xf_post) for z in (ezt, ezm)]
        erails += [sphere(er + 5, (x, y, ezt)) for x in (xf_post, xr_post)]
    erails += [cyl(er, (xf_post, -YE_, z), (xf_post, YE_, z)) for z in (ezt, ezm)]
    m.add("extension_rails", GALV, erails)
    # guide clamps tying the extension rails to the main rails
    clamps = []
    for s in (1, -1):
        for x in (PX1 - 90, 420.0):
            clamps.append(box(x - 30, x + 30, *ys(s, YE_ - 25, YR + 25), ezt - 25, zt + 25))
            clamps.append(box(x - 30, x + 30, *ys(s, YE_ - 25, YR + 25), ezm - 20, zm + 25))
    m.add("extension_guides", DARK, clamps)
    m.add("extension_pedal", BLACK, box(EX1 - 260, EX1 - 140, 260, 400, DECKZ + 28, DECKZ + 62))

    # platform control box hung on the left top rail, between the second and third posts
    cx0, cx1 = -340.0, -80.0
    zb = zt - 120                                  # top face of the control box
    m.add("control_box", DARK, box(cx0, cx1, 380, YR - 12, zb - 200, zb))
    m.add("control_hooks", STEEL, [box(x - 25, x + 25, 380, YR + 32, zb - 10, zt + 40) for x in (cx0 + 40, cx1 - 40)])
    m.add("control_face", YELLOW, box(cx0 + 15, cx1 - 15, 395, YR - 27, zb - 2, zb + 6))
    if not m.print_mode:     # yellow label panels on the box sides
        m.add("control_labels", YELLOW, box(cx0 + 20, cx1 - 20, YR - 12, YR - 10, zb - 175, zb - 40),
              box(cx0 + 20, cx1 - 20, 378, 380, zb - 175, zb - 40))
    m.add("joystick", BLACK, ax_z(32, cx1 - 70, 450, zb, zb + 22), ax_z(r(12), cx1 - 70, 450, zb + 15, zb + 125),
          sphere(28, (cx1 - 70, 450, zb + 130)))
    m.add("platform_estop", RED, ax_z(r(24), cx0 + 70, 450, zb, zb + 35), ax_z(36, cx0 + 70, 450, zb + 32, zb + 52))
    m.add("control_buttons", GREEN, [ax_z(14, cx0 + 140, y, zb, zb + 12) for y in (420, 480)])
    # manual holder and lanyard anchors
    m.add("manual_holder", BLACK, ax_z(45, -1000, -YR + 62, zt - 330, zt - 40),
          [box(x - 20, x + 20, -YR - 28, -YR + 62, zt - 60, zt + 30) for x in (-1040, -960)])
    anchors = [torus(30, r(8), (x, s * (PY - 60), DECKZ + 6), (0, 0, 1)) for x in (-1080, -150) for s in (1, -1)]
    m.add("lanyard_anchors", YELLOW, anchors)
