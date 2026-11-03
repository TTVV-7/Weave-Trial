"""Single-drum vibratory soil compactor, smooth 84 in drum, about 11 t operating weight.

Front: a smooth steel drum, 2.13 m (84 in) wide and 1.52 m across, with recessed end plates;
each end carries a bearing hub on a ring of eight rubber isolators bolted to a black drum
mount plate, with the drum-drive motor on the left and the vibration motor on the right,
fed by hoses. The drum hangs in a heavy rectangular drum frame (yoke): two deep side
members, a front and a rear cross beam, lifting eyes at the corners, and steel scraper
bars front and rear held on brackets just clear of the drum face.
Middle: centre articulation joint - a clevis on the drum frame round a vertical pin, and a
tongue on a longitudinal oscillation bearing in the rear frame - with a steering cylinder
each side, and the drive hoses running through.
Rear tractor unit: rear frame between two 23.1-26 tyres with an R-1 (tractor bar) tread on
orange 26 in rims with planetary hubs and a rear drive axle; fenders over both tyres; a
long engine hood with side louvre grilles, a rear radiator grille, a grab rail, an exhaust
stack with an angled tip and an air pre-cleaner; a wide rear body with tail lights,
indicators, a bumper and a tow hitch; a hydraulic tank and a battery box under the cab.
Cab: ROPS cab on a raised operator platform, black pillars and large glazing all round, a
door on the left, wiper, grab handles, mirrors both sides, seat, steering console and
armrest controls, roof work lights front and rear, front indicators and a beacon; a
three-step ladder (formed side plates with lightening windows) with a handrail up to the
platform on the left, set far enough behind the hitch pin for the drum frame to articulate
about 35 degrees each way.

Dimensions are typical figures for the 84 in / 11 t class, not any one machine:
  drum 2,130 mm wide, 1,520 mm diameter, sunk 11 mm (1.5 % of its radius) for the print
  rear tyres 23.1-26: OD 1,600 mm, 590 mm wide, sunk 12 mm; track 1,670 mm
  wheelbase (drum centre to rear axle) 2,950 mm; length ~5.95 m over the frames, 6.0 m with
  the tow hitch; width 2.30 m over the drum frame, 2.33 m over the drum motors;
  height 3.00 m to the cab roof (3.13 m to the beacon)
  ground clearance ~450 mm under the rear frame; operator platform at 1.42 m
Generic and brand-neutral: no names, logos or maker-specific styling.
"""

import math

import cadquery as cq
import numpy as np

from cadkit import (Finish, arc_pts, bar, box, cone, cut, cyl, mirror_y, mv, pipe, prism, rgb, rot, rounded_box, sphere,
                    torus)
from finishes import AMBER, BLACK, CHROME, DARK, GLASS, LED, ORANGE, RED, RUBBER, STEEL

ASSET = dict(key="soil_compactor", stem="Vibratory_Soil_Roller_84in",
             title="Single-Drum Vibratory Roller (84 in, 11 t class)", az=40, el=20, size="1200x900")

DRUM = Finish(rgb("#6b7075"), metal=0.75, rough=0.33)     # bare rolled steel drum shell

# ---------------------------------------------------------------- main dimensions (mm)
XD, RD = 1950.0, 760.0          # drum centre X, drum radius (1,520 mm drum)
ZD = RD - 11.0                  # drum sunk 1.5 % of its radius
HW = 1065.0                     # drum half width (2,130 mm = 84 in)
XA, RT = -1000.0, 800.0         # rear axle X, tyre radius (23.1-26, OD 1,600)
ZA = RT - 12.0                  # axle height, tyre sunk 1.5 %
TYC = 835.0                     # tyre centre plane |Y| (tyre 540..1,130)
XJ, ZJ = 760.0, 1035.0          # articulation pin, oscillation-bearing height
FY0, FY1 = 1085.0, 1150.0       # drum-frame side member |Y|
XF0, XF1 = XD - 1010, XD + 1000  # drum frame rear / front faces


def ys(s, a, b):
    """The |Y| range a..b on side s (+1 left, -1 right), as sorted (y0, y1)."""
    return tuple(sorted((s * a, s * b)))


def ax_y(r, x, z, y0, y1):
    """Cylinder of radius r along Y at (x, z), from y0 to y1."""
    return cyl(r, (x, y0, z), (x, y1, z))


def loft_x(sections):
    """Ruled loft through cross sections [(x, [(y, z), ...]), ...] with matching point counts."""
    wires = [cq.Wire.makePolygon([cq.Vector(x, y, z) for y, z in pts], close=True) for x, pts in sections]
    return cq.Solid.makeLoft(wires, ruled=True)


def arc_band(cx, cz, r0, r1, a0, a1, n=28):
    """Side-plane polygon of a curved strip between radii r0 and r1, angles in degrees."""
    return arc_pts(cx, cz, r1, a0, a1, n) + arc_pts(cx, cz, r0, a1, a0, n)


def slats(m, lo, hi, thick, gap):
    """(a0, a1) spans of louvre slats filling lo..hi, centred in it.

    In print mode a slat thinner than a printable wall is made a printable wall thick, and the
    gap is kept at least 30 mm, so the louvres print as fewer, sturdier ribs."""
    if m.print_mode:
        thick, gap = m.t(thick), max(gap, 30.0)
    pitch = thick + gap
    n = int((hi - lo - thick) // pitch) + 1
    a = lo + (hi - lo - (n - 1) * pitch - thick) / 2
    return [(a + k * pitch, a + k * pitch + thick) for k in range(n)]


def steer_cylinder(a, b, rb, rr, frac):
    """Hydraulic cylinder with vertical eye bosses: (barrel parts, rod parts)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    u = d / np.linalg.norm(d)
    j = a + d * frac
    t = lambda p: tuple(map(float, p))      # noqa: E731
    up = np.array([0.0, 0.0, 1.0])
    barrel = [cyl(rb, t(a + u * 35), t(j)), cyl(rb * 1.12, t(j - u * 60), t(j + u * 4)),
              cyl(rb * 1.1, t(a + u * 35), t(a + u * 95)), cyl(rb * 0.95, t(a - up * 45), t(a + up * 45))]
    rod = [cyl(rr, t(j - u * 20), t(b - u * 30)), cyl(rr * 1.5, t(b - up * 38), t(b + up * 38))]
    return barrel, rod


# ---------------------------------------------------------------- wheels

def tyre_at_origin():
    """23.1-26 tractor tyre, axis along Y through the origin: carcass plus R-1 bar lugs."""
    prof = [(322, -262), (380, -272), (450, -285), (530, -293), (610, -295), (668, -289), (710, -274),
            (737, -248), (751, -205), (758, -130), (760, 0), (758, 130), (751, 205), (737, 248), (710, 274),
            (668, 289), (610, 295), (530, 293), (450, 285), (380, 272), (322, 262)]
    carcass = cq.Workplane("XY").polyline(prof).close().revolve(360, (0, 0, 0), (0, 1, 0)).val()
    crown = cyl(RT, (0, -400, 0), (0, 400, 0))
    n, w, sweep = 44, 82.0, 250.0
    lugs = []
    for k in range(n):
        s = 1 if k % 2 == 0 else -1
        pts = [(-w / 2 - sweep / 2, s * 293), (w / 2 - sweep / 2, s * 293),
               (w / 2 + sweep / 2, -s * 22), (-w / 2 + sweep / 2, -s * 22)]
        lug = prism(pts, "z", 700, RT + 20).intersect(crown)
        lugs.append(rot(lug, 360.0 * k / n, (0, 1, 0)))
    return [carcass] + lugs


def wheel_at_origin():
    """26 in rim with its outer face towards +Y, planetary hub and wheel nuts."""
    rim = [cyl(335, (0, -262, 0), (0, 230, 0)),
           cut(cyl(372, (0, 222, 0), (0, 272, 0)), cyl(318, (0, 215, 0), (0, 280, 0))),
           cut(cyl(368, (0, -272, 0), (0, -228, 0)), cyl(318, (0, -280, 0), (0, -220, 0))),
           cyl(320, (0, 120, 0), (0, 150, 0))]
    nuts = []
    for k in range(12):
        a = 2 * math.pi * k / 12
        x, z = 262 * math.cos(a), 262 * math.sin(a)
        nuts.append(cyl(22, (x, 145, z), (x, 178, z)))
    hub = [cyl(215, (0, 80, 0), (0, 205, 0)), cyl(165, (0, 200, 0), (0, 245, 0)), cyl(55, (0, 240, 0), (0, 262, 0))]
    bolts = []
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        x, z = 190 * math.cos(a), 190 * math.sin(a)
        bolts.append(cyl(14, (x, 200, z), (x, 220, z)))
    return rim, hub, nuts + bolts


# ---------------------------------------------------------------- the machine

def build(m):
    t = m.t
    lt = t(10)            # lamp lens thickness

    # ================================================================ drum
    sw = t(28)            # drum shell wall: the exposed lip at each end prints at 0.8 mm or more
    shell = cut(ax_y(RD, XD, ZD, -HW, HW), ax_y(RD - sw, XD, ZD, -HW - 1, HW + 1))
    m.add("drum_shell", DRUM, shell)
    m.add("drum_end_plates", DARK, ax_y(RD - sw + 2, XD, ZD, -(HW - 90), HW - 90))
    for s, side in ((1, "L"), (-1, "R")):
        m.add(f"drum_hub_{side}", DARK, ax_y(210, XD, ZD, *ys(s, HW - 110, 1084)),
              ax_y(330, XD, ZD, *ys(s, 1000, 1030)))
        m.add(f"drum_end_bolts_{side}", STEEL,
              [ax_y(16, XD + 300 * math.cos(a), ZD + 300 * math.sin(a), *ys(s, 1025, 1042))
               for a in np.linspace(0, 2 * math.pi, 12, endpoint=False)])
        ang = np.linspace(0, 2 * math.pi, 8, endpoint=False) + math.pi / 8
        m.add(f"rubber_isolators_{side}", RUBBER,
              [ax_y(46, XD + 255 * math.cos(a), ZD + 255 * math.sin(a), *ys(s, 1025, 1084)) for a in ang])
        mount = [(XD - 440, 1205), (XD + 440, 1205), (XD + 400, ZD - 60), (XD + 250, ZD - 340),
                 (XD - 250, ZD - 340), (XD - 400, ZD - 60)]
        m.add(f"drum_mount_plate_{side}", BLACK, prism(mount, "y", *ys(s, 1078, 1128)))
        m.add(f"isolator_bolts_{side}", STEEL,
              [ax_y(18, XD + 255 * math.cos(a), ZD + 255 * math.sin(a), *ys(s, 1122, 1142)) for a in ang])
        # drum drive motor on the left, vibration motor on the right
        motor = [ax_y(175, XD, ZD, *ys(s, 1120, 1148)), ax_y(118, XD, ZD, *ys(s, 1144, 1166))]
        if s < 0:
            motor.append(box(XD - 70, XD + 70, *ys(s, 1146, 1164), ZD + 100, ZD + 172))   # valve block
        m.add(f"{'drive' if s > 0 else 'vibration'}_motor", DARK, motor)
        m.add(f"motor_bolts_{side}", STEEL,
              [ax_y(12, XD + 148 * math.cos(a), ZD + 148 * math.sin(a), *ys(s, 1144, 1158))
               for a in np.linspace(0, 2 * math.pi, 8, endpoint=False)])
        hr = m.r(16)
        m.add(f"motor_hoses_{side}", BLACK,
              pipe([(XD - 380, s * 1140, 1165), (XD - 330, s * 1148, 1010), (XD - 120, s * 1140, ZD + 110)], hr),
              pipe([(XD - 300, s * 1140, 1165), (XD - 230, s * 1150, 1050), (XD - 60, s * 1140, ZD + 135)], hr))

    # ================================================================ drum frame (yoke)
    side_prof = [(XF0, 820), (XF0, 1430), (XF1 - 120, 1430), (XF1, 1340), (XF1, 900), (XD + 850, 770), (XD + 710, 1150),
                 (XD - 710, 1150), (XD - 840, 820)]
    m.add("drum_frame_sides", ORANGE, [prism(side_prof, "y", *ys(s, FY0, FY1)) for s in (1, -1)])
    front = [(XD + 830, 820), (XD + 850, 760), (XF1 - 50, 760), (XF1, 1000), (XF1, 1340), (XF1 - 120, 1430),
             (XD + 830, 1430)]
    m.add("drum_frame_front", ORANGE, prism(front, "y", -FY1, FY1))
    m.add("drum_frame_rear", ORANGE, box(XF0, XD - 840, -FY1, FY1, 820, 1290))
    m.add("frame_edge_strips", BLACK,
          [box(XF0 + 40, XF1 - 140, *ys(s, FY1 - 20, FY1 + 4), 1360, 1395) for s in (1, -1)],
          box(XF1 - 20, XF1 + 4, -FY1 + 40, FY1 - 40, 1280, 1315))
    eyes = []
    for x in (XF0 + 90, XF1 - 220):
        for s in (1, -1):
            e = prism([(x - 85, 1425), (x + 85, 1425), (x + 45, 1535), (x - 45, 1535)], "y", *ys(s, 1095, 1140))
            eyes.append(cut(e, ax_y(24, x, 1468, -1200, 1200)))      # >= 43 mm of eye all round
    m.add("lifting_eyes", ORANGE, eyes)
    m.add("front_tie_down", BLACK, [box(XF1 - 5, XF1 + 40, y - 60, y + 60, 1100, 1180) for y in (-700, 700)])

    # scrapers: steel blades on a holder bar, hung on brackets from the cross beams
    for front_end, name in ((True, "front"), (False, "rear")):
        k = 1 if front_end else -1
        a = math.radians(-14 if front_end else 194)
        tip = np.array([XD + (RD + 12) * math.cos(a), ZD + (RD + 12) * math.sin(a)])
        d = np.array([k * math.cos(math.radians(35)), math.sin(math.radians(35))])
        nb = np.array([-d[1], d[0]])
        h = t(14) / 2
        end = tip + 190 * d
        blade = [tuple(tip + h * nb), tuple(end + h * nb), tuple(end - h * nb), tuple(tip - h * nb)]
        m.add(f"{name}_scraper_blade", STEEL, prism(blade, "y", -1030, 1030))
        hx, hz = end + 20 * d
        m.add(f"{name}_scraper_holder", BLACK, box(hx - 45, hx + 45, -1045, 1045, hz - 45, hz + 45))
        ztop = 820 if front_end else 840
        bw = t(50) / 2
        m.add(f"{name}_scraper_brackets", BLACK,
              [box(hx - 35, hx + 35, y - bw, y + bw, hz, ztop) for y in (-860, -290, 290, 860)])

    # ================================================================ articulation and oscillation joint
    clevis = [(XF0 + 40, 170)] + arc_pts(XJ, 0, 170, 90, 270, 14) + [(XF0 + 40, -170)]
    m.add("hitch_clevis", ORANGE, [prism(clevis, "z", z0, z1) for z0, z1 in ((1170, 1230), (840, 900))])
    tongue = [(520, -150)] + arc_pts(XJ, 0, 150, -90, 90, 14) + [(520, 150)]
    m.add("hitch_tongue", DARK, prism(tongue, "z", 906, 1164))
    m.add("oscillation_bearing", DARK, cyl(200, (380, 0, ZJ), (540, 0, ZJ)), cyl(245, (525, 0, ZJ), (550, 0, ZJ)))
    m.add("oscillation_bolts", STEEL, [cyl(16, (545, 220 * math.cos(a), ZJ + 220 * math.sin(a)),
                                           (565, 220 * math.cos(a), ZJ + 220 * math.sin(a)))
                                       for a in np.linspace(0, 2 * math.pi, 10, endpoint=False)])
    m.add("hitch_pin", STEEL, cyl(62, (XJ, 0, 815), (XJ, 0, 1255)), cyl(105, (XJ, 0, 1228), (XJ, 0, 1250)),
          cyl(105, (XJ, 0, 820), (XJ, 0, 842)))
    hoses = []
    for s in (1, -1):
        hoses += pipe([(410, s * 330, 1250), (680, s * 330, 1300), (XF0 + 10, s * 420, 1260)], m.r(18))
        hoses += pipe([(410, s * 260, 1215), (690, s * 270, 1270), (XF0 + 10, s * 330, 1240)], m.r(16))
    m.add("joint_hoses", BLACK, hoses)

    # steering cylinders across the joint
    for s in (1, -1):
        m.add("steering_cylinder_lug", ORANGE, box(150, 300, *ys(s, 490, 680), 925, 985))
        m.add("steering_cylinder_lug_front", ORANGE, box(845, XF0 + 15, *ys(s, 625, 780), 925, 985))
        barrel, rod = steer_cylinder((220, s * 600, 1015), (900, s * 700, 1015), 58, 34, 0.56)
        m.add("steering_cylinder", BLACK, barrel)
        m.add("steering_cylinder_rod", CHROME, rod)
        m.add("steering_pins", STEEL, cyl(28, (220, s * 600, 1055), (220, s * 600, 1080)),
              cyl(26, (900, s * 700, 1050), (900, s * 700, 1072)))

    # ================================================================ rear tractor unit
    tyre = tyre_at_origin()
    rim, hub, nuts = wheel_at_origin()

    def place(shapes, s):
        out = [mv(sh, XA, TYC, ZA) for sh in shapes]
        return out if s > 0 else [mirror_y(sh) for sh in out]

    for s, side in ((1, "L"), (-1, "R")):
        m.add(f"tyre_{side}", RUBBER, place(tyre, s))
        m.add(f"rim_{side}", ORANGE, place(rim, s))
        m.add(f"hub_{side}", DARK, place(hub, s))
        m.add(f"wheel_nuts_{side}", STEEL, place(nuts, s))

    axle = [ax_y(170, XA, ZA, -650, 650), sphere(255, (XA, 0, ZA - 25)), cyl(140, (XA, 0, ZA), (XA + 380, 0, ZA + 40))]
    for s in (1, -1):
        axle += [cone(170, 235, (XA, s * 520, ZA), (XA, s * 600, ZA)), ax_y(235, XA, ZA, *ys(s, 600, 700))]
    m.add("rear_axle", DARK, axle)

    # rear frame: front section under the platform, narrow section between the tyres, rear body
    m.add("rear_frame", ORANGE, box(-200, 420, -520, 520, 450, 1360), box(-1890, -190, -520, 520, 450, 1660),
          box(-260, 420, -560, 560, 1240, 1360))
    m.add("belly_guard", DARK, box(-1850, 380, -470, 470, 430, 460))
    rb_plan = [(-1870, -900), (-1870, 900)] + arc_pts(-2780, 780, 120, 90, 180, 8) + \
        arc_pts(-2780, -780, 120, 180, 270, 8)
    rb_side = [(-1870, 480), (-1870, 1700), (-2850, 1700), (-2900, 1630), (-2900, 760), (-2830, 480)]
    m.add("rear_body", ORANGE, prism(rb_plan, "z", 480, 1700).intersect(prism(rb_side, "y", -950, 950)))
    m.add("rear_bumper", BLACK, box(-2955, -2880, -880, 880, 480, 690), box(-2955, -2880, -880, 880, 690, 715))
    hitch = cut(box(-3000, -2940, -110, 110, 520, 660), box(-3005, -2955, -115, 115, 565, 615))
    m.add("tow_hitch", BLACK, hitch)
    m.add("rear_reflectors", RED, [box(-2955 - t(6), -2950, *ys(s, 560, 760), 560, 620) for s in (1, -1)])
    m.add("tow_pin", STEEL, cyl(22, (-2975, 0, 505), (-2975, 0, 680)), cyl(38, (-2975, 0, 658), (-2975, 0, 680)))
    if not m.print_mode:
        seams = []
        for s in (1, -1):
            seams += [box(x - 4, x + 4, *ys(s, 897, 903), 760, 1600) for x in (-2780, -2000)]
            seams += [box(-2780, -2000, *ys(s, 897, 903), z - 4, z + 4) for z in (760, 1600)]
        m.add("rear_body_door_seams", BLACK, seams)
    m.add("rear_body_handles", BLACK, [box(-2120, -2040, *ys(s, 895, 925), 1150, 1230) for s in (1, -1)])
    m.add("fuel_cap", BLACK, cyl(62, (-2450, 820, 1690), (-2450, 820, 1745)), cyl(28, (-2450, 820, 1740), (-2450, 820, 1765)))

    # tail lights and rear lamps on the rear body
    lamps, red, amber, white = [], [], [], []
    for s in (1, -1):
        lamps.append(box(-2925, -2890, *ys(s, 600, 840), 1380, 1580))
        red.append(box(-2925 - lt, -2920, *ys(s, 615, 715), 1395, 1565))
        amber.append(box(-2925 - lt, -2920, *ys(s, 730, 825), 1490, 1565))
        white.append(box(-2925 - lt, -2920, *ys(s, 730, 825), 1395, 1475))
    m.add("tail_lamp_housings", BLACK, lamps)
    m.add("tail_lights", RED, red)
    m.add("rear_indicators", AMBER, amber)
    m.add("reverse_lights", LED, white)
    m.add("rear_panel", BLACK, box(-2912, -2895, -460, 460, 820, 1220))
    dp = 16 if m.print_mode else 4          # how far the slots stand proud (not a wall: backed all along)
    m.add("rear_panel_slots", DARK,
          [box(-2918 - dp, -2908, -420, 420, z0, z1) for z0, z1 in slats(m, 850, 1176, 26, 34)])

    # fenders over the tyres
    fth = t(18)
    for s in (1, -1):
        y0, y1 = ys(s, 515, 1155)
        m.add("fender", ORANGE, prism(arc_band(XA, ZA, 862, 862 + fth, 41, 180), "y", y0, y1),
              prism(arc_band(XA, ZA, 860, 925, 41, 180), "y", *ys(s, 1160 - t(35), 1160)))
        m.add("fender_lip", BLACK, prism(arc_band(XA, ZA, 918, 935, 41, 180), "y", *ys(s, 1157 - t(25), 1157)))

    # engine hood
    front_sec = [(-740, 1640), (740, 1640), (740, 2010), (610, 2150), (-610, 2150), (-740, 2010)]
    rear_sec = [(-740, 1640), (740, 1640), (740, 1930), (610, 2060), (-610, 2060), (-740, 1930)]
    m.add("hood", ORANGE, loft_x([(-330, front_sec), (-2860, rear_sec)]))
    grille, louvres = [], []
    lv = 20 if m.print_mode else 8          # how far the slats stand proud of the grille
    for s in (1, -1):
        grille.append(box(-2600, -1500, *ys(s, 728, 752), 1700, 1905))
        louvres += [box(-2585, -1515, *ys(s, 740, 752 + lv), z0, z1) for z0, z1 in slats(m, 1716, 1896, 20, 20)]
    grille.append(box(-2878, -2850, -560, 560, 1720, 1990))
    louvres += [box(-2878 - lv, -2866, -540, 540, z0, z1) for z0, z1 in slats(m, 1735, 1987, 22, 24)]
    m.add("hood_grilles", BLACK, grille)
    m.add("grille_louvres", DARK, louvres)
    if not m.print_mode:
        m.add("hood_seams", BLACK, [box(x - 5, x + 5, *ys(s, 736, 744), 1660, 1960)
                                     for x in (-2700, -1400) for s in (1, -1)])
    m.add("hood_intake", BLACK, box(-2620, -2120, -420, 420, 2040, 2092))
    m.add("hood_intake_louvres", DARK, [box(x0, x1, -395, 395, 2088, 2092 + (16 if m.print_mode else 6))
                                        for x0, x1 in slats(m, -2595, -2153, 26, 26)])
    m.add("hood_latches", BLACK, [box(-1460, -1400, *ys(s, 735, 760), 1900, 1960) for s in (1, -1)])
    m.add("hood_grab_rail", BLACK, pipe([(-2760, 320, 2050), (-2760, 320, 2130), (-2760, -320, 2130),
                                         (-2760, -320, 2050)], m.r(16)))
    m.add("exhaust_stack", DARK, cyl(70, (-760, -470, 2080), (-760, -470, 2620)),
          cyl(92, (-760, -470, 2130), (-760, -470, 2420)),
          [box(-860, -660, -490, -450, z - 15, z + 15) for z in (2180, 2370)])
    tip0, tip1 = np.array([-760.0, -470.0, 2600.0]), np.array([-860.0, -470.0, 2740.0])
    m.add("exhaust_tip", STEEL, cyl(74, tuple(tip0), tuple(tip1)), sphere(74, tuple(tip0)))
    m.add("air_precleaner", BLACK, cyl(60, (-760, 470, 2100), (-760, 470, 2300)),
          cyl(120, (-760, 470, 2290), (-760, 470, 2500)))
    m.add("precleaner_cap", DARK, cyl(150, (-760, 470, 2495), (-760, 470, 2545)),
          cone(150, 60, (-760, 470, 2545), (-760, 470, 2600)))

    # hydraulic tank (right) and battery box (left) under the platform
    m.add("hydraulic_tank", ORANGE, box(-180, 130, -760, -500, 720, 1330))
    m.add("tank_gauge", CHROME, box(-60, 20, -768, -756, 900, 1150))
    m.add("tank_filler", BLACK, cyl(55, (0, -640, 1325), (0, -640, 1352)))
    m.add("battery_box", BLACK, box(-180, 110, 500, 720, 880, 1300))
    m.add("battery_box_latch", STEEL, box(-60, 0, 718, 730, 1180, 1240))
    m.add("articulation_lock_bar", RED, box(-170, 250, 560 - t(30) / 2, 560 + t(30) / 2, 640, 690))
    m.add("lock_bar_clips", BLACK, [box(x - 25, x + 25, 515, 585, 630, 700) for x in (-120, 200)])

    # ================================================================ operator platform and ROPS cab
    CX0, CX1, CW, CZ0, CZ1, lean = -350.0, 960.0, 780.0, 1420.0, 2880.0, 60.0

    def xf(z):
        return CX1 + lean * (z - CZ0) / (CZ1 - CZ0)

    m.add("platform", DARK, box(CX0 - 30, CX1 + 40, -820, 820, 1350, CZ0))
    m.add("platform_edge", BLACK, box(CX1 + 38, CX1 + 52, -820, 820, 1350, 1420),
          [box(CX0 - 30, CX1 + 40, *ys(s, 818, 828), 1350, 1420) for s in (1, -1)])
    pp = 80.0
    frame = [bar((xf(CZ0) - pp / 2, s * (CW - pp / 2), CZ0), (xf(CZ1) - pp / 2, s * (CW - pp / 2), CZ1), pp, pp,
                 up=(1, 0, 0)) for s in (1, -1)]
    frame += [box(160, 240, *ys(s, CW - pp, CW), CZ0, CZ1) for s in (1, -1)]        # B pillars
    frame += [box(CX0, CX0 + pp, *ys(s, CW - pp, CW), CZ0, CZ1) for s in (1, -1)]
    frame += [box(CX0, xf(1520) - 10, *ys(s, CW - pp, CW), CZ0, 1520) for s in (1, -1)]
    frame.append(box(xf(CZ0) - pp, xf(1520), -CW, CW, CZ0, 1520))
    frame.append(box(CX0, CX0 + pp, -CW, CW, CZ0, 2170))
    frame.append(box(CX0, xf(CZ1), -CW, CW, CZ1 - 60, CZ1))
    m.add("cab_frame", BLACK, frame)

    g = t(12)
    zt = CZ1 - 60
    glass = [bar((xf(1520) - pp / 2, 0, 1520), (xf(zt) - pp / 2, 0, zt), 2 * CW - pp, g, up=(1, 0, 0))]
    for s in (1, -1):
        yc = s * (CW - pp / 2)
        door = [(200, 1520), (xf(1520) - pp / 2, 1520), (xf(zt) - pp / 2, zt), (200, zt)]
        quarter = [(CX0 + pp / 2, 1520), (200, 1520), (200, zt), (CX0 + pp / 2, zt)]
        glass += [prism(door, "y", yc - g / 2, yc + g / 2), prism(quarter, "y", yc - g / 2, yc + g / 2)]
    glass.append(box(CX0 + pp / 2 - g / 2, CX0 + pp / 2 + g / 2, -(CW - pp / 2), CW - pp / 2, 2160, zt))
    m.add("cab_glass", GLASS, glass)
    m.add("cab_roof", ORANGE, rounded_box(CX0 - 70, xf(CZ1) + 80, -CW - 60, CW + 60, CZ1, CZ1 + 120, 35))
    m.add("roof_panel", DARK, box(-150, 650, -480, 480, CZ1 + 112, CZ1 + 128))

    if m.print_mode:      # solid interior, so the glazed cab is not a sealed hollow
        core = [(CX0 + 40, CZ0 - 10), (xf(CZ0 - 10) - 40, CZ0 - 10), (xf(CZ1 + 10) - 40, CZ1 + 10), (CX0 + 40, CZ1 + 10)]
        m.add("cab_core", DARK, prism(core, "y", -CW + 40, CW - 40))

    # interior
    m.add("seat", BLACK, box(-160, 260, -270, 270, 1720, 1860),
          bar((-170, 0, 1830), (-260, 0, 2470), 520, 140, up=(1, 0, 0)),
          box(-120, 220, -230, 230, CZ0, 1720))
    m.add("armrest_console", DARK, box(-80, 380, -470, -300, CZ0, 1990),
          cyl(20, (300, -385, 1985), (300, -385, 2120)), sphere(38, (300, -385, 2130)))
    m.add("steering_console", DARK, box(700, 900, -260, 260, CZ0, 1900),
          bar((760, 0, 1880), (670, 0, 2150), 110, 110, up=(1, 0, 0)),
          box(640, 760, -200, 200, 2080, 2200))
    wa = np.array([-110.0, 0.0, 300.0]) / np.linalg.norm([-110.0, 0.0, 300.0])
    wc = np.array([640.0, 0.0, 2190.0])
    e1 = np.array([0.0, 1.0, 0.0])
    e2 = np.cross(wa, e1)
    spokes = [bar(tuple(wc), tuple(wc + 175 * (math.cos(a) * e1 + math.sin(a) * e2)), 30, t(14), up=tuple(wa))
              for a in (math.radians(-90), math.radians(30), math.radians(150))]
    m.add("steering_wheel", BLACK, torus(180, m.r(17), tuple(wc), tuple(wa)),
          cyl(40, (650, 0, 2150), (636, 0, 2200)), spokes)

    # exterior cab details
    wt = t(10)
    off = g / 2 + wt / 2 - 4
    m.add("wiper", BLACK, bar((xf(1560) - pp / 2 + off, 300, 1560), (xf(2650) - pp / 2 + off, -150, 2650), t(30), wt,
                              up=(1, 0, 0)),
          cyl(30, (xf(1560) - pp / 2 + off - 5, 300, 1560), (xf(1560) - pp / 2 + off + 25, 300, 1560)))
    rr = m.r(15)
    m.add("cab_grab_handles", BLACK,
          pipe([(xf(z) - pp / 2, CW - 10 if k in (0, 3) else CW + 70, z) for k, z in enumerate((1700, 1700, 2650, 2650))],
               rr),
          pipe([(200, CW - 10, 1700), (200, CW + 70, 1700), (200, CW + 70, 2650), (200, CW - 10, 2650)], rr))
    m.add("door_handle", BLACK, box(760, 880, CW - 20, CW + 28, 2020, 2065))
    m.add("door_hinges", DARK, [cyl(22, (190, CW + 18, z), (190, CW + 18, z + 110)) for z in (1650, 2600)],
          [box(160, 200, CW - 10, CW + 30, z, z + 110) for z in (1650, 2600)])
    for s in (1, -1):
        xa = xf(2500) - pp / 2
        m.add("mirror_arm", BLACK, pipe([(xa, s * (CW - 30), 2500), (xa + 60, s * (CW + 150), 2550),
                                         (xa + 90, s * (CW + 250), 2470)], m.r(15)))
        m.add("mirror_housing", BLACK, box(xa + 70, xa + 130, *ys(s, CW + 210, CW + 380), 2260, 2550))
        m.add("mirror_glass", CHROME, box(xa + 72 - t(6), xa + 74, *ys(s, CW + 222, CW + 368), 2272, 2538))

    # roof lamps, indicators and beacon
    zr = CZ1 + 120
    xr = xf(CZ1)
    fl = [box(xr - 60, xr + 50, *ys(s, 440, 620), zr - 10, zr + 85) for s in (1, -1)]
    fl += [box(CX0 - 60, CX0 + 50, *ys(s, 440, 620), zr - 10, zr + 85) for s in (1, -1)]
    m.add("roof_lamp_housings", BLACK, fl)
    m.add("roof_work_lights", LED, [box(xr + 46, xr + 50 + lt, *ys(s, 455, 605), zr + 2, zr + 73) for s in (1, -1)],
          [box(CX0 - 60 - lt, CX0 - 56, *ys(s, 455, 605), zr + 2, zr + 73) for s in (1, -1)])
    m.add("indicators_front", AMBER, [box(xr + 40, xr + 85, *ys(s, 690, 790), CZ1 + 35, CZ1 + 90) for s in (1, -1)])
    m.add("beacon_base", BLACK, cyl(85, (-200, 520, zr - 8), (-200, 520, zr + 30)),
          cyl(45, (-200, 520, zr + 105), (-200, 520, zr + 128)))
    m.add("beacon", AMBER, cyl(68, (-200, 520, zr + 28), (-200, 520, zr + 108)))

    # ---- access ladder on the left, just ahead of the rear tyre and well behind the hitch pin, so
    # the drum-frame corners swing clear of it as the machine articulates
    sx = (-100.0, 250.0)       # stringer inner faces: frame clears the ladder to ~35 deg, tyre 75 mm behind
    st = t(25)
    # formed side plates as deep as the treads, with a gusset up to the platform
    string = [(790, 1330), (790, 1415), (1120, 1415), (1120, 360), (860, 360), (860, 1280), (810, 1330)]
    def window(z0, z1, y0=915.0, y1=1065.0, c=30.0):
        return [(y0 + c, z0), (y1 - c, z0), (y1, z0 + c), (y1, z1 - c), (y1 - c, z1), (y0 + c, z1), (y0, z1 - c),
                (y0, z0 + c)]
    plates = []
    for a0, a1 in ((sx[0] - st, sx[0]), (sx[1], sx[1] + st)):
        plates.append(cut(prism(string, "x", a0, a1),
                          *[prism(window(z0, z1), "x", a0 - 5, a1 + 5) for z0, z1 in ((500, 680), (840, 1010))]))
    m.add("ladder_stringers", BLACK, plates)
    m.add("ladder_steps", DARK, [box(sx[0] - 2, sx[1] + 2, 865, 1115, z - 25, z + 25) for z in (420, 760, 1090)])
    m.add("step_nosings", Finish(rgb("#f2c200"), rough=0.5),
          [box(sx[0], sx[1], 1105, 1118, z + 18, z + 28) for z in (420, 760, 1090)])
    hr = m.r(16)
    m.add("ladder_handrail", BLACK,
          pipe([(sx[0] - st / 2, 1110, 900), (sx[0] - st / 2, 1110, 1400), (sx[0] - st / 2, 1110, 2050),
                (200, CW - 20, 2050)], hr))
