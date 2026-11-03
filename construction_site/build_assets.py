#!/usr/bin/env python3
"""Build the second set of construction-site assets.

    python construction_site/build_assets.py                 # every asset
    python construction_site/build_assets.py mini_excavator  # just these
    python construction_site/build_assets.py --list
    python construction_site/build_assets.py --scale 87      # HO-scale print files
    python construction_site/build_assets.py --set 3         # one set
    python construction_site/build_assets.py wheel_loader --diagnose   # what floats in the print

For each asset this writes, beside this file:

    <Name>.step              CAD, millimetres, every part a coloured solid
    <Name>.glb               web / Blender / game engines, metres, coloured
    print_1-<scale>/<Name>_1-<scale>.stl
                             one watertight body at the print scale, flat on the bed
    <Name>_preview.png       studio render (needs node, Playwright and three.js;
                             skip with --no-render)

Everything is drawn at full size in millimetres: X forward, Y left, Z up, on the
ground at Z = 0. The print file is the same model built again with every thin
part thickened to at least --min-wall at the print scale, so nothing comes out
thinner than a nozzle can lay down.
"""

from __future__ import annotations

import argparse
import importlib
import json
import math
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import cadquery as cq
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from cadkit import (FT, IN, Finish, Model, arc_pts, band, bar, box, clip_poly, cone,  # noqa: E402
                    corrugated_plan, cut, cyl, export_glb, export_print, export_step, frustum, mv,
                    pin, pipe, prism, ram, rgb, rot, rounded_box, sphere, stadium, text, torus, wheel_lugs)

from finishes import *  # noqa: E402,F401,F403  (the colour palette)


# =========================================================================== assets

def jersey_profile():
    """NJ-shape safety barrier section (y, z), mm: 24 in base, 3 in toe,
    55 deg up to 13 in, 84 deg up to a 6 in top, 32 in tall."""
    half_base = 12 * IN
    toe = 3 * IN
    knee_z = 13 * IN
    knee_y = half_base - (knee_z - toe) / math.tan(math.radians(55))
    top_z = 32 * IN
    top_y = knee_y - (top_z - knee_z) / math.tan(math.radians(84))
    right = [(half_base, 0), (half_base, toe), (knee_y, knee_z), (top_y, top_z)]
    left = [(-y, z) for y, z in reversed(right)]
    return right + left


LOOP_OUT = 90.0     # how far a connection loop stands off the end face
LOOP_Z = ((230.0, 590.0), (330.0, 690.0))   # loop heights at the -X end, the +X end


def jersey_barrier_body(m: Model, x0=0.0, name="barrier"):
    L = 10 * FT
    xa, xb = x0 - L / 2, x0 + L / 2
    body = prism(jersey_profile(), "x", xa, xb)
    holes = []
    for xs in (-L / 4, L / 4):     # drainage scuppers, also the fork pockets
        holes.append(box(x0 + xs - 9 * IN, x0 + xs + 9 * IN, -400, 400, -1, 6 * IN))
        holes.append(cyl(40, (x0 + xs, -200, 650), (x0 + xs, 200, 650)))   # lifting hole
    body = cut(body, *holes)
    m.add(name, CONCRETE, body)

    loops = []
    r = m.r(14)
    for end, sign, heights in ((xa, -1, LOOP_Z[0]), (xb, 1, LOOP_Z[1])):
        for z in heights:
            pts = [(end - sign * 60, -35, z), (end + sign * LOOP_OUT, -35, z),
                   (end + sign * LOOP_OUT, 35, z), (end - sign * 60, 35, z)]
            loops += pipe(pts, r)
    m.add(f"{name}_loops", RUST, loops)
    # a reflector on each face, centred, on the upper slope
    lean = 1 / math.tan(math.radians(84))
    knee_y, knee_z = jersey_profile()[2]
    z = 560.0
    face = knee_y - (z - knee_z) * lean
    t = m.t(6)
    for s in (-1, 1):
        y = s * (face + t / 2 - 1)
        m.add(f"{name}_reflector", REFLECTOR,
              bar((x0 - 50, y, z), (x0 + 50, y, z), t, 70, up=(0, -s * lean, 1)))


def jersey_barrier(m: Model):
    jersey_barrier_body(m)


def jersey_barrier_run(m: Model):
    gap = 110.0
    L = 10 * FT
    for i in range(3):
        jersey_barrier_body(m, (i - 1) * (L + gap), name=f"barrier_{i + 1}")
    for j in range(2):                        # the pins, dropped through the loops
        x = (j - 0.5) * (L + gap)
        m.add(f"pin_{j + 1}", RUST, cyl(m.r(19), (x, 0, 150), (x, 0, 780)),
              cyl(m.r(32), (x, 0, 780), (x, 0, 800)))



# --------------------------------------------------------------------------- mini excavator

def mini_excavator(m: Model):
    """3.5 t class compact excavator: blade down, boom up, bucket resting on the ground."""
    BY = -180.0                 # boom plane, right of centre; the cab is on the left
    xr, xf, rr = -800.0, 820.0, 260.0
    zc = rr

    # ---- undercarriage
    for s, side in ((1, "L"), (-1, "R")):
        y0, y1 = sorted((s * 570, s * 870))
        belt = cut(prism(stadium(xr, xf, zc, rr), "y", y0, y1),
                   prism(stadium(xr, xf, zc, rr - 60), "y", y0 - 1, y1 + 1))
        lugs = []
        ym = (y0 + y1) / 2
        for i, x in enumerate(np.arange(xr, xf + 1, 95)):     # top run
            lo, hi = (y0, ym + 30) if i % 2 else (ym - 30, y1)
            lugs.append(box(x - 22, x + 22, lo, hi, zc + rr - 2, zc + rr + 20))
        for xc, a0, a1 in ((xf, -50, 90), (xr, 90, 230)):     # round the ends
            for j, a in enumerate(np.linspace(a0, a1, 7)[1:-1]):
                lo, hi = (y0, ym + 30) if j % 2 else (ym - 30, y1)
                lug = box(xc - 22, xc + 22, lo, hi, zc + rr - 2, zc + rr + 20)
                lugs.append(rot(lug, 90 - a, (0, 1, 0), (xc, 0, zc)))
        m.add(f"track_{side}", RUBBER, belt, lugs)

        fy0, fy1 = sorted((s * 610, s * 830))
        m.add(f"track_frame_{side}", DARK, prism(stadium(-560, 580, 300, 110), "y", fy0, fy1),
              box(-450, 450, s * 610, s * 300, 250, 420))
        teeth = []
        for k in range(22):
            a = 2 * math.pi * k / 22
            rad = 215 if k % 2 else 188
            teeth.append((xr + rad * math.cos(a), zc + rad * math.sin(a)))
        m.add(f"sprocket_{side}", BLACK, prism(teeth, "y", fy0 + 20, fy1 - 20),
              cyl(150, (xr, s * 480, zc), (xr, s * 640, zc)))
        m.add(f"idler_{side}", DARK, cyl(195, (xf, fy0 + 15, zc), (xf, fy1 - 15, zc)),
              cyl(85, (xf, fy0, zc), (xf, fy1, zc)))
        m.add(f"rollers_{side}", BLACK,
              [cyl(62, (x, fy0 + 10, 120), (x, fy1 - 10, 120)) for x in (-480, -160, 160, 480)],
              cyl(45, (0, fy0 + 20, 415), (0, fy1 - 20, 415)))
        m.add(f"roller_brackets_{side}", DARK,
              [box(x - 30, x + 30, fy0, fy1, 120, 200) for x in (-480, -160, 160, 480)])

    m.add("centre_frame", DARK, box(-450, 450, -610, 610, 260, 470))
    m.add("swing_bearing", BLACK, cyl(480, (0, 0, 470), (0, 0, 565)))

    # ---- dozer blade
    front = [(1350, 0), (1300, 90), (1268, 190), (1262, 290), (1280, 370), (1318, 412)]
    back = [(x - 32, z) for x, z in front][::-1]
    blade = prism(front + back, "y", -870, 870)
    ribs = [box(1180, 1245, y - 30, y + 30, 40, 380) for y in (-520, 0, 520)]
    arms = [bar((420, s * 450, 340), (1215, s * 450, 240), 90, 150) for s in (1, -1)]
    m.add("blade", YELLOW, blade, ribs, arms)
    m.add("blade_edge", BLACK, box(1316, 1352, -870, 870, 0, 42))
    barrel, ends = ram((440, 0, 420), (1185, 0, 300), 58, 34)
    m.add("blade_ram", STEEL, barrel[1], ends)
    m.add("blade_ram_barrel", BLACK, barrel[0])

    # ---- upper structure
    tail = cyl(880, (0, 0, 550), (0, 0, 1160))
    deck = box(-900, 0, -775, 775, 565, 760).intersect(tail).fuse(box(0, 640, -775, 775, 565, 760))
    cw = box(-900, -440, -775, 775, 760, 1150).intersect(tail)
    hood = box(-440, 330, -775, -60, 760, 1200)
    m.add("upper", YELLOW, deck, cw, hood)
    m.add("bumper", BLACK, box(-900, -300, -790, 790, 600, 680).intersect(cyl(892, (0, 0, 590), (0, 0, 690))))
    m.add("hood_grille", BLACK, [box(x, x + 38, -785, -772, 850, 1110) for x in range(-360, 120, 70)])
    m.add("exhaust", BLACK, cyl(m.r(34), (-200, -560, 1195), (-200, -560, 1420)),
          cyl(m.r(42), (-200, -560, 1400), (-200, -560, 1430)))

    # cab, on the left
    cx0, cx1, cy0, cy1 = -440.0, 600.0, -20.0, 775.0
    zf, zr = 760.0, 2400.0
    lean = 130.0

    def xfront(z):
        return cx1 - (z - zf) / (zr - zf) * lean

    post = 70
    posts = [bar((cx1 - post / 2, y, zf), (xfront(zr) - post / 2, y, zr), post, post, up=(1, 0, 0))
             for y in (cy0 + post / 2, cy1 - post / 2)]
    posts += [box(cx0, cx0 + post, y - post / 2, y + post / 2, zf, zr) for y in (cy0 + post / 2, cy1 - post / 2)]
    posts.append(box(-80, -40, cy1 - 12, cy1, 1050, zr))                         # door frame
    m.add("cab_frame", BLACK, posts, box(cx0 - 40, xfront(zr) + 40, cy0 - 30, cy1 + 30, zr, zr + 80))
    m.add("cab_lower", YELLOW, box(cx0, xfront(1050), cy0, cy1, zf, 1050))
    g = m.t(10)
    side = [(cx0 + post, 1050), (xfront(1050) - post, 1050), (xfront(zr) - post, zr), (cx0 + post, zr)]
    glass = [prism(side, "y", cy1 - 6 - g, cy1 - 6), prism(side, "y", cy0 + 6, cy0 + 6 + g),
             bar((xfront(1050) - g / 2, (cy0 + cy1) / 2, 1050), (xfront(zr) - g / 2, (cy0 + cy1) / 2, zr),
                 cy1 - cy0 - 2 * post, g, up=(1, 0, 0)),
             box(cx0 + 4, cx0 + 4 + g, cy0 + post, cy1 - post, 1150, zr)]
    m.add("cab_glass", GLASS, glass)
    m.add("seat", BLACK, box(-300, 60, 230, 640, zf, 1230), box(-330, -250, 230, 640, 1230, 1820),
          box(80, 200, 120, 220, zf, 1350), box(80, 200, 650, 750, zf, 1350))
    m.add("beacon", AMBER, cyl(70, (-250, 640, zr + 80), (-250, 640, zr + 210)))
    m.add("grab_handle", BLACK, pipe([(xfront(1100) - post / 2, cy1 - 10, 1100), (xfront(1100) - post / 2, cy1 + 70, 1100),
                                      (xfront(1900) - post / 2, cy1 + 70, 1900), (xfront(1900) - post / 2, cy1 - 10, 1900)],
                                     m.r(16)))

    # ---- digging equipment: boom, arm, bucket, all in the plane y = BY
    F = np.array([720.0, 900.0])
    K = F + 1300 * np.array([math.cos(math.radians(60)), math.sin(math.radians(60))])
    T = K + 1250 * np.array([math.cos(math.radians(-10)), math.sin(math.radians(-10))])
    A = T + 1500 * np.array([math.cos(math.radians(-75)), math.sin(math.radians(-75))])
    u = (A - T) / np.linalg.norm(A - T)          # down the arm
    n = np.array([-u[1], u[0]])                   # its forward side
    if n[0] < 0:
        n = -n
    H = T - 400 * u

    def P(p, y=BY):
        return (float(p[0]), float(y), float(p[1]))

    m.add("swing_bracket", DARK, box(600, 800, BY - 150, BY + 150, 565, 1010),
          box(780, 860, BY - 60, BY + 60, 640, 760))
    m.add("boom", YELLOW, prism(band([F, K, T], [150, 210, 130]), "y", BY - 100, BY + 100),
          cyl(130, P(F, BY - 100), P(F, BY + 100)), cyl(120, P(T, BY - 100), P(T, BY + 100)))
    m.add("arm", YELLOW, prism(band([H, T, A], [130, 150, 95]), "y", BY - 80, BY + 80))

    # bucket, outline relative to the pin A
    def rel(pts):
        return [(A[0] + dx, A[1] + dz) for dx, dz in pts]
    outline = rel([(-60, 70), (130, 110), (250, 30), (340, -360), (200, -352), (60, -340),
                   (-50, -290), (-105, -190), (-100, -60)])
    shell_path = rel([(-60, 60), (-100, -60), (-105, -190), (-50, -290), (60, -340), (200, -352), (330, -358)])
    bw = 250.0
    st = m.t(20)
    m.add("bucket", DARK, prism(outline, "y", BY - bw, BY - bw + st), prism(outline, "y", BY + bw - st, BY + bw),
          prism(band(shell_path, m.t(14)), "y", BY - bw, BY + bw),
          bar(P(A + (-60, 70), BY), P(A + (250, 40), BY), 2 * bw, 40, up=(0, 0, 1)))
    teeth = [bar(P(A + (300, -338), y), P(A + (400, -338), y), 50, 36) for y in np.linspace(BY - 200, BY + 200, 5)]
    m.add("bucket_teeth", STEEL, teeth)

    # cylinders and links
    Cm0, Cm1 = np.array([820.0, 700.0]), F + 750 * (K - F) / np.linalg.norm(K - F) + 190 * np.array([0.866, -0.5])
    Ca0 = K + np.array([60.0, 270.0])
    Cb0 = T + 280 * u + 160 * n
    J = A - 300 * u + 170 * n
    Pl = A - 280 * u + 40 * n
    Lb = A + np.array([130.0, 80.0])
    rams = [ram(P(Cm0), P(Cm1), 65, 40, 0.6), ram(P(Ca0), P(H), 60, 36, 0.58), ram(P(Cb0), P(J), 55, 32, 0.55)]
    m.add("ram_barrels", BLACK, [r[0][0] for r in rams])
    m.add("ram_rods", CHROME, [r[0][1] for r in rams], [e for r in rams for e in r[1]])
    m.add("ram_lug", DARK, box(Ca0[0] - 60, Ca0[0] + 60, BY - 50, BY + 50, Ca0[1] - 120, Ca0[1]))
    links = [bar(P(J, BY + y), P(Lb, BY + y), m.t(30), 70) for y in (-70, 70)]
    links += [bar(P(J, BY + y), P(Pl, BY + y), m.t(30), 70) for y in (-110, 110)]
    m.add("bucket_links", DARK, links)
    m.add("pins", STEEL, [pin(P(p), r, half) for p, r, half in
                          ((F, 55, 160), (T, 50, 150), (A, 48, 270), (H, 45, 110), (J, 40, 130),
                           (Pl, 40, 130), (Lb, 40, 270), (Cm0, 40, 90), (Cm1, 40, 120), (Ca0, 40, 90))])
    hose = [P(F + (30, 200), BY), P(K + (-10, 250), BY), P(T + (-160, 175), BY)]
    m.add("hoses", BLACK, pipe([(x, BY + 55, z) for x, _, z in hose], m.r(16)),
          pipe([(x, BY - 55, z) for x, _, z in hose], m.r(16)))
    m.add("work_light", LED, box(K[0] - 80, K[0] + 20, BY - 60, BY + 60, K[1] + 200, K[1] + 270))


# --------------------------------------------------------------------------- skid steer

def skid_steer(m: Model):
    """Radial-lift skid steer loader, about 2,000 lb rated operating capacity, 68 in bucket."""
    R, sink = 406.0, 6.0
    zc = R - sink
    for x in (-575.0, 575.0):
        for s in (1, -1):
            y0, y1 = sorted((s * 600, s * 870))
            m.add("tyre", RUBBER, cyl(R - 26, (x, y0, zc), (x, y1, zc)),
                  wheel_lugs(x, zc, R, 26, y0, y1, 24, 62))
            yo = s * 870
            m.add("axle_hub", DARK, cyl(120, (x, s * 560, zc), (x, s * 640, zc)))
            m.add("rim", STEEL, cyl(235, (x, yo - s * 20, zc), (x, yo + s * 4, zc)),
                  cyl(110, (x, yo, zc), (x, yo + s * 30, zc)),
                  [cyl(m.r(14), (x + 75 * math.cos(a), yo, zc + 75 * math.sin(a)),
                       (x + 75 * math.cos(a), yo + s * 45, zc + 75 * math.sin(a)))
                   for a in np.linspace(0, 2 * math.pi, 8, endpoint=False)])

    m.add("body", ORANGE, box(-1000, 820, -590, 590, 200, 820), box(-1250, -650, -590, 590, 300, 1260),
          box(-1150, -800, -700, -590, 600, 1560), box(-1150, -800, 590, 700, 600, 1560))
    m.add("belly", DARK, box(-950, 780, -560, 560, 150, 200))
    m.add("rear_grille", BLACK, [box(-1262, -1250, -420, 420, z, z + 30) for z in range(560, 1180, 60)])
    m.add("tail_lights", RED, [box(-1262, -1250, s * 480 - 50, s * 480 + 50, 1100, 1170) for s in (1, -1)])
    m.add("exhaust", BLACK, cyl(m.r(34), (-1100, -380, 1255), (-1100, -380, 1460)))

    # ROPS cab
    cx0, cx1, cw, zf, zr = -650.0, 450.0, 480.0, 820.0, 1940.0
    pp = 75
    frame = [box(x, x + pp, y - pp / 2, y + pp / 2, zf, zr) for x in (cx0, cx1 - pp) for y in (-cw + pp / 2, cw - pp / 2)]
    frame += [box(cx0, cx1, s * cw - s * 8, s * cw, z - 20, z + 20) for s in (1, -1) for z in (1150, 1450, 1750)]
    m.add("cab_frame", BLACK, frame, box(cx0 - 30, cx1 + 30, -cw - 20, cw + 20, zr, zr + 60))
    g = m.t(10)
    m.add("cab_glass", GLASS, box(cx1 - g, cx1, -cw + pp, cw - pp, zf + 80, zr),
          [box(cx0 + pp, cx1 - pp, s * (cw - 4), s * (cw - 4 - g), zf + 200, zr) for s in (1, -1)],
          box(cx0, cx0 + g, -cw + pp, cw - pp, 1200, zr))
    m.add("seat", BLACK, box(-560, -200, -300, 300, zf, 1260), box(-600, -520, -300, 300, 1260, 1760),
          [box(-200, 0, s * 300, s * 440, zf, 1150) for s in (1, -1)])
    m.add("work_lights", LED, [box(cx1 + 30, cx1 + 60, s * 320 - 70, s * 320 + 70, zr - 70, zr) for s in (1, -1)])
    m.add("light_housings", BLACK, [box(cx1, cx1 + 30, s * 320 - 80, s * 320 + 80, zr - 80, zr + 10) for s in (1, -1)])

    # lift arms (radial), cross tube, rams
    P0, P1, P2, P3 = (-975.0, 1450.0), (150.0, 1530.0), (930.0, 1150.0), (1110.0, 430.0)
    arm = band([P0, P1, P2, P3], [120, 130, 120, 90])
    for s in (1, -1):
        y0, y1 = sorted((s * 600, s * 690))
        m.add("lift_arm", ORANGE, prism(arm, "y", y0, y1))
        barrel, ends = ram((-900, s * 645, 700), (-150, s * 645, 1400), 58, 36, 0.6)
        m.add("lift_ram", BLACK, barrel[0])
        m.add("lift_ram_rod", CHROME, barrel[1], ends)
        barrel, ends = ram((930, s * 300, 1150), (1185, s * 300, 860), 50, 30, 0.55)
        m.add("tilt_ram", BLACK, barrel[0])
        m.add("tilt_ram_rod", CHROME, barrel[1], ends)
    m.add("cross_tube", ORANGE, cyl(70, (930, -690, 1150), (930, 690, 1150)))
    m.add("pivot_pins", STEEL, pin((P0[0], 0, P0[1]), 45, 720), pin((P3[0], 0, P3[1]), 40, 720))
    m.add("quick_attach", DARK, box(1110, 1175, -700, 700, 380, 960),
          [box(1060, 1110, s * 300 - 40, s * 300 + 40, 820, 900) for s in (1, -1)])

    # 68 in bucket
    b0, b1, bw = 1175.0, 1800.0, 875.0
    side = [(b0, 0), (b1, 0), (b1 - 10, 60), (1500, 420), (1270, 560), (b0, 560)]
    st = m.t(16)
    m.add("bucket", DARK, prism(side, "y", -bw, -bw + st), prism(side, "y", bw - st, bw),
          prism(band([(b0 + 10, 560), (b0 + 10, 130), (b0 + 90, 15), (b1, 10)], m.t(14)), "y", -bw, bw),
          box(b0, 1300, -bw, bw, 530, 590))
    m.add("bucket_edge", STEEL, box(1640, b1 + 10, -bw, bw, 0, 26))


# --------------------------------------------------------------------------- shipping container

def shipping_container(m: Model):
    """20 ft ISO container (1CC), 20 x 8 x 8.5 ft, doors closed, for site storage."""
    L, W, H = 6058.0, 2438.0, 2591.0
    X, Yh = L / 2, W / 2
    C = CONTAINER
    castings = []
    for sx in (1, -1):
        for sy in (1, -1):
            for z0, z1 in ((0, 118), (H - 118, H)):
                c = box(sx * X, sx * (X - 178), sy * Yh, sy * (Yh - 162), z0, z1)
                xm, ym, zm = sx * (X - 89), sy * (Yh - 81), (z0 + z1) / 2
                holes = [box(xm - 40, xm + 40, sy * (Yh + 1), sy * (Yh - 25), zm - 20, zm + 20),
                         box(sx * (X + 1), sx * (X - 25), ym - 40, ym + 40, zm - 20, zm + 20),
                         box(xm - 62, xm + 62, ym - 32, ym + 32, z1 - 25 if z0 else -1, z1 + 1 if z0 else 25)]
                castings.append(cut(c, *holes))
    m.add("corner_castings", C, castings)
    posts = [box(sx * (X - 8), sx * (X - 170), sy * (Yh - 8), sy * (Yh - 150), 118, H - 118)
             for sx in (1, -1) for sy in (1, -1)]
    fork = [box(sx * 845, sx * 1205, -Yh - 5, Yh + 5, 12, 127) for sx in (1, -1)]
    rails = [box(-(X - 178), X - 178, sy * (Yh - 4), sy * (Yh - 64), 12, 165) for sy in (1, -1)]
    rails = [cut(r, *fork) for r in rails]
    rails += [box(-(X - 178), X - 178, sy * (Yh - 4), sy * (Yh - 74), H - 150, H - 6) for sy in (1, -1)]
    m.add("frame", C, posts, rails,
          [box(sx * 845, sx * 1205, -Yh + 4, Yh - 4, 127, 165) for sx in (1, -1)])

    z_lo, z_hi = 160.0, H - 150
    for sy in (1, -1):
        plan = corrugated_plan(-(X - 170), X - 170, sy * (Yh - 10), 36, sy * (Yh - 120))
        m.add("side_wall", C, prism(plan, "z", z_lo, z_hi))
    end = corrugated_plan(-(Yh - 150), Yh - 150, X - 10, 36, X - 120)
    m.add("front_wall", C, prism([(x, y) for y, x in end], "z", z_lo, z_hi))
    roof = corrugated_plan(-(X - 170), X - 170, H - 22, 18, H - 120, pitch=230, flat_out=60, flat_in=60)
    m.add("roof", C, prism(roof, "y", -(Yh - 60), Yh - 60))
    core_z = 12 if m.print_mode else 165
    core = box(-(X - 60), X - 100, -(Yh - 60), Yh - 60, core_z, H - 100)
    m.add("core", DARK, cut(core, *fork))
    if not m.print_mode:
        m.add("cross_members", DARK, [box(x - 40, x + 40, -(Yh - 60), Yh - 60, 40, 165)
                                      for x in np.arange(-2700, 2701, 450) if not 800 < abs(x) < 1250])

    # door end, -X
    xd = -X
    m.add("door_frame", C, box(xd + 8, xd + 160, -(Yh - 150), Yh - 150, H - 260, H - 118),
          box(xd + 8, xd + 160, -(Yh - 150), Yh - 150, 12, 230))
    doors = []
    for y0, y1 in ((-(Yh - 150), -4), (4, Yh - 150)):
        doors.append(box(xd + 20, xd + 80, y0, y1, 230, H - 260))
        doors += [box(xd + 10, xd + 20, y0 + 30, y1 - 30, z - 45, z + 45) for z in np.linspace(500, 2100, 5)]
        doors += [box(xd + 10, xd + 20, y, y + 40, 230, H - 260) for y in (y0, y1 - 40)]
    m.add("doors", C, doors)
    gear, handles = [], []
    for y in (-800.0, -300.0, 300.0, 800.0):
        xb = xd - 12
        gear.append(cyl(m.r(14), (xb, y, 140), (xb, y, H - 140)))
        gear += [box(xd - 38, xd + 20, y - 32, y + 32, z - 25, z + 25) for z in (500, 1350, 2150)]
        gear += [box(xd - 45, xd + 10, y - 40, y + 40, z0, z1) for z0, z1 in ((130, 215), (H - 230, H - 145))]
        toward = -math.copysign(1, y) if abs(y) < 500 else math.copysign(1, y)
        handles.append(pipe([(xb, y, 1150), (xb - 30, y, 1150), (xb - 30, y + toward * 260, 1150)], m.r(12)))
        gear.append(box(xd - 45, xd + 10, y + toward * 260 - 25, y + toward * 260 + 25, 1110, 1190))
    m.add("locking_bars", GALV, gear)
    m.add("handles", GALV, handles)
    hinges = []
    for sy in (1, -1):
        for z in (450, 1100, 1750, 2300):
            hinges.append(cyl(m.r(22), (xd - 5, sy * (Yh - 150), z - 60), (xd - 5, sy * (Yh - 150), z + 60)))
            hinges.append(box(xd - 5, xd + 25, sy * (Yh - 150), sy * (Yh - 260), z - 35, z + 35))
    m.add("hinges", GALV, hinges)
    m.add("data_plate", GALV, box(xd + 15, xd + 21, 400, 700, 1750, 1950))


# --------------------------------------------------------------------------- light tower

def light_tower(m: Model):
    """Towable LED light tower: four 300 W LED heads on a 30 ft mast, raised, outriggers down."""
    R, sink = 290.0, 6.0
    zc, xa = R - sink, -50.0
    for s in (1, -1):
        y0, y1 = sorted((s * 690, s * 860))
        m.add("tyre", RUBBER, cyl(R, (xa, y0, zc), (xa, y1, zc)))
        m.add("rim", STEEL, cyl(165, (xa, s * 860, zc), (xa, s * 866, zc)),
              cyl(70, (xa, s * 860, zc), (xa, s * 885, zc)))
        arch = arc_pts(xa, zc, 360, 0, 180, 20) + arc_pts(xa, zc, 320, 180, 0, 20)
        m.add("fender", BLACK, prism(arch, "y", s * 640, s * 885))
    m.add("axle", BLACK, cyl(m.r(40), (xa, -700, zc), (xa, 700, zc)))
    m.add("chassis", BLACK, [box(-1150, 1050, s * 480, s * 560, 420, 540) for s in (1, -1)],
          [box(x - 40, x + 40, -560, 560, 420, 540) for x in (-1100, -50, 1000)],
          box(xa - 50, xa + 50, -560, 560, zc - 50, 440))

    Y = YELLOW
    m.add("enclosure", Y, box(-1100, 1000, -650, 650, 540, 1600), box(-1130, 1030, -680, 680, 1600, 1645))
    trim = []
    for s in (1, -1):
        yf = s * 650
        trim += [box(x - 4, x + 4, yf, yf + s * 3, 600, 1550) for x in (-950, -200, 550)]
        trim += [box(-880, -320, yf, yf + s * 8, z, z + 22) for z in range(760, 1400, 70)]
        trim += [box(x, x + 90, yf, yf + s * 20, 1050, 1080) for x in (-330, 420)]
    m.add("doors_and_louvres", BLACK, trim)
    m.add("control_panel", DARK, box(-1112, -1100, -350, 350, 1050, 1450))
    m.add("switches", RED, [box(-1122, -1112, y - 25, y + 25, 1350, 1400) for y in (-200, 0, 200)])

    m.add("drawbar", BLACK, [bar((1000, s * 480, 480), (2300, 0, 480), 80, 100) for s in (1, -1)],
          box(2250, 2420, -70, 70, 430, 540))
    m.add("tow_eye", STEEL, torus(70, m.r(18), (2490, 0, 485)))
    m.add("jockey", BLACK, cyl(m.r(38), (1900, 200, 150), (1900, 200, 900)),
          pipe([(1900, 200, 900), (1900, 200, 960), (1900, 340, 960)], m.r(14)),
          box(1870, 1930, 150, 250, 100, 220), cyl(m.r(20), (1900, 145, 100), (1900, 255, 100)))
    m.add("jockey_wheel", RUBBER, cyl(100, (1900, 165, 100), (1900, 235, 100)))

    legs = []
    for x in (900.0, -950.0):
        for s in (1, -1):
            legs.append(box(x - 50, x + 50, s * 560, s * 1650, 560, 660))
            legs.append(box(x - 45, x + 45, s * 1605, s * 1695, 60, 900))
            legs.append(pipe([(x, s * 1650, 900), (x, s * 1650, 960), (x + 150, s * 1650, 960)], m.r(12)))
            m.add("outrigger_pad", BLACK, box(x - 150, x + 150, s * 1500, s * 1800, 0, 35),
                  box(x - 30, x + 30, s * 1620, s * 1680, 35, 80))
    m.add("outriggers", Y, legs)

    mx = -750.0
    m.add("mast_base", Y, box(mx - 160, mx + 160, -170, 170, 1645, 1900))
    m.add("mast", GALV, cyl(95, (mx, 0, 1645), (mx, 0, 4300)), cyl(78, (mx, 0, 4250), (mx, 0, 6500)),
          cyl(62, (mx, 0, 6450), (mx, 0, 8650)))
    m.add("mast_collars", BLACK, cyl(112, (mx, 0, 4230), (mx, 0, 4320)), cyl(94, (mx, 0, 6430), (mx, 0, 6520)),
          cyl(80, (mx, 0, 8620), (mx, 0, 8780)))
    zb, zt, fy = 8780.0, 9620.0, 640.0
    frame = [bar((mx + 30, -fy, z), (mx + 30, fy, z), 70, 70) for z in (zb, zt)]
    frame += [box(mx, mx + 70, y - 35, y + 35, zb, zt) for y in (-fy, -330, 0, 330, fy)]
    m.add("head_frame", BLACK, frame)
    heads, lenses = [], []
    for yc in (-330.0, 330.0):
        for zh in (8990.0, 9410.0):
            h = box(-45, 45, -265, 265, -180, 180)
            fins = [box(-80, -40, -250, 250, z - 6, z + 6) for z in np.linspace(-150, 150, 7)]
            arm = box(-140, -20, -40, 40, -40, 40)
            lens = box(45, 52, -240, 240, -155, 155)
            place = lambda sh: mv(rot(sh, 12, (0, 1, 0)), mx + 165, yc, zh)
            heads += [place(h), place(arm)] + [place(f) for f in fins]
            lenses.append(place(lens))
    m.add("led_heads", DARK, heads)
    m.add("led_lenses", LED, lenses)
    m.add("beacon", AMBER, cyl(60, (-300, 0, 1645), (-300, 0, 1760)))


# --------------------------------------------------------------------------- scaffold tower

def scaffold_tower(m: Model):
    """Frame scaffold tower, two lifts of 5 x 6 ft 7 in walk-through frames at 7 ft,
    planked on top with guardrails and toeboards, base jacks and a clip-on ladder."""
    span, width, fh, z0 = 7 * FT, 5 * FT, 2007.0, 250.0
    rl, rs = m.r(21.5), m.r(12.7)
    xs = (-span / 2, span / 2)
    ys = (-width / 2, width / 2)
    frames, braces, pins = [], [], []
    for lift in range(2):
        zb, zt = z0 + lift * fh, z0 + (lift + 1) * fh
        for x in xs:
            frames += [cyl(rl, (x, y, zb), (x, y, zt)) for y in ys]
            frames.append(cyl(rl, (x, ys[0], zt - 30), (x, ys[1], zt - 30)))
            frames.append(cyl(rs, (x, ys[0], zt - 380), (x, ys[1], zt - 380)))
            for s in (1, -1):
                yi = s * (width / 2 - 300)
                frames.append(cyl(rs, (x, yi, zt - 380), (x, yi, zb + 1100)))
                frames.append(cyl(rs, (x, yi, zb + 1100), (x, s * width / 2, zb + 800)))
                frames.append(cyl(rs, (x, yi, zt - 380), (x, s * width / 2, zt - 700)))
            if lift:
                pins += [cyl(rl + 5, (x, y, zb - 30), (x, y, zb + 30)) for y in ys]
        for y in ys:
            yb = y + math.copysign(40, y)
            braces.append(cyl(rs, (xs[0], yb, zb + 300), (xs[1], yb, zb + 1800)))
            braces.append(cyl(rs, (xs[0], yb, zb + 1800), (xs[1], yb, zb + 300)))
            braces.append(sphere(rs * 1.6, (0, yb, zb + 1050)))
            for x in xs:
                for z in (zb + 300, zb + 1800):
                    pins.append(cyl(m.r(9), (x, y, z), (x, yb + math.copysign(15, y), z)))
    m.add("frames", BLUE, frames)
    m.add("cross_braces", GALV, braces)
    m.add("lock_pins", STEEL, pins)

    jacks = []
    for x in xs:
        for y in ys:
            jacks += [box(x - 75, x + 75, y - 75, y + 75, 0, 8), cyl(m.r(17), (x, y, 8), (x, y, z0 + 150)),
                      cyl(45, (x, y, 170), (x, y, 210)), cyl(m.r(10), (x - 90, y, 190), (x + 90, y, 190))]
    m.add("base_jacks", STEEL, jacks)

    zt = z0 + 2 * fh
    pz = zt - 9
    m.add("planks", TIMBER, [box(-span / 2 - 150, span / 2 + 150, y - 235, y + 235, pz, pz + 50) for y in (-500, 0, 500)])
    m.add("plank_hooks", GALV, [box(x - 30, x + 30, y - 200, y + 200, zt - 60, pz) for x in xs for y in (-500, 0, 500)])
    rails = [cyl(m.r(19), (x, y, zt), (x, y, zt + 1100)) for x in xs for y in ys]
    for z in (zt + 530, zt + 1000):
        rails += [cyl(m.r(19), (xs[0], y, z), (xs[1], y, z)) for y in ys]
        rails += [cyl(m.r(19), (x, ys[0], z), (x, ys[1], z)) for x in xs]
    m.add("guardrails", YELLOW, rails)
    tb, tt = pz + 50, pz + 50 + 140
    m.add("toeboards", TIMBER_DARK, [box(xs[0], xs[1], y - math.copysign(30, y), y - math.copysign(30 + m.t(25), y), tb, tt) for y in ys],
          [box(x - math.copysign(30, x), x - math.copysign(30 + m.t(25), x), ys[0] + 30, ys[1] - 30, tb, tt) for x in xs])

    xl = xs[0] - 130
    ladder = [box(xl - 25, xl + 25, s * 205, s * 255, 0, zt + 1000) for s in (1, -1)]
    ladder += [cyl(m.r(14), (xl, -230, z), (xl, 230, z)) for z in np.arange(300, zt + 900, 300)]
    for lift in range(2):
        for z in (z0 + (lift + 1) * fh - 30, z0 + (lift + 1) * fh - 380):
            ladder += [box(xl, xs[0], s * 215, s * 245, z - 20, z + 20) for s in (1, -1)]
    m.add("ladder", GALV, ladder)


# --------------------------------------------------------------------------- portable toilet

def portable_toilet(m: Model):
    """Standard single portable toilet, 44 x 47 x 90 in, door facing +X."""
    hx, hy = 1194 / 2, 1118 / 2
    m.add("base", DARK, cut(box(-hx, hx, -hy, hy, 0, 110),
                            *[box(-hx - 10, hx + 10, y - 100, y + 100, -1, 55) for y in (-320, 320)]))
    B = TOILET_BLUE
    shell = [box(-hx + 30, hx - 30, -hy + 30, hy - 30, 110, 2060)]
    shell += [cyl(45, (sx * (hx - 45), sy * (hy - 45), 110), (sx * (hx - 45), sy * (hy - 45), 2080))
              for sx in (1, -1) for sy in (1, -1)]
    for s in (1, -1):
        shell += [box(x - 35, x + 35, s * (hy - 30), s * (hy - 12), 250, 1800) for x in (-330, -110, 110, 330)]
    shell += [box(-hx + 12, -hx + 30, y - 35, y + 35, 250, 1800) for y in (-300, 0, 300)]
    shell.append(box(hx - 30, hx - 12, -470, 470, 150, 2000))                           # door
    shell += [box(hx - 12, hx - 4, -400, 400, z0, z1) for z0, z1 in ((300, 950), (1100, 1850))]
    m.add("shell", B, shell)
    m.add("vents", BLACK, [box(-320, 320, s * (hy - 30), s * (hy - 24), 1850, 1990) for s in (1, -1)])
    m.add("door_handle", DARK, pipe([(hx - 4, -390, 980), (hx + 40, -390, 980), (hx + 40, -390, 1180),
                                     (hx - 4, -390, 1180)], m.r(14)))
    m.add("latch", WHITE, box(hx - 4, hx + 6, -440, -330, 1250, 1310))
    m.add("occupied_flag", RED, box(hx + 6, hx + 9, -425, -345, 1268, 1292))
    m.add("hinge", GALV, cyl(m.r(18), (hx - 8, 485, 300), (hx - 8, 485, 1900)))
    m.add("roof", TRANSLUCENT, box(-hx - 15, hx + 15, -hy - 15, hy + 15, 2060, 2140),
          frustum((-hx - 15, hx + 15, -hy - 15, hy + 15, 2140), (-hx + 220, hx - 220, -hy + 200, hy - 200, 2286)))
    sx, sy = -hx - 45, -hy + 220
    m.add("vent_stack", BLACK, cyl(50, (sx, sy, 1550), (sx, sy, 2400)), cyl(70, (sx, sy, 2400), (sx, sy, 2440)),
          cone(70, 20, (sx, sy, 2440), (sx, sy, 2490)),
          [box(sx, -hx + 31, sy - 15, sy + 15, z - 20, z + 20) for z in (1650, 2000)])


# --------------------------------------------------------------------------- Type III barricade

def type3_barricade(m: Model):
    """MUTCD Type III barricade, 8 ft rails with 6 in orange/white stripes, ROAD CLOSED sign,
    two amber warning lights, sandbagged feet. Faces -Y."""
    L, t = 8 * FT, m.t(25)
    px, pw = 560.0, 76.0
    m.add("posts", GALV, [box(x - pw / 2, x + pw / 2, -pw / 2, pw / 2, 60, 2340) for x in (-px, px)])
    feet = []
    for x in (-px, px):
        feet.append(box(x - pw / 2, x + pw / 2, -620, 620, 0, 60))
        feet += [bar((x, s * 520, 60), (x, s * pw / 2, 760), m.t(38), m.t(38), up=(1, 0, 0)) for s in (1, -1)]
    m.add("feet", GALV, feet)
    sand = Finish(rgb("#b49b6c"), rough=0.95)
    m.add("sandbags", sand, [rounded_box(x - 230, x + 230, y0, y1, 60, 190, 45)
                             for x in (-px, px) for y0, y1 in ((-640, -330), (330, 640))])
    w = 6 * IN * math.sqrt(2)
    for k, (z0, z1) in enumerate(((559, 762), (940, 1143), (1321, 1524))):
        for face, (y0, y1) in (("front", (-pw / 2 - t, -pw / 2)), ("back", (pw / 2, pw / 2 + t))):
            h = z1 - z0
            u = -L / 2 - h
            i = 0
            while u < L / 2:
                quad = [(u, z0), (u + w, z0), (u + w + h, z1), (u + h, z1)]
                poly = clip_poly(quad, -L / 2, L / 2, z0, z1)
                if len(poly) >= 3:
                    m.add(f"rail{k + 1}_{face}_{'orange' if i % 2 else 'white'}",
                          SIGN_ORANGE if i % 2 else WHITE, prism(poly, "y", y0, y1))
                u += w
                i += 1
    st = m.t(12)
    e = max(2.0, 0.3 * m.scale) if m.print_mode else 2.0
    ys = -pw / 2 - st
    m.add("sign", WHITE, box(-609.6, 609.6, ys, -pw / 2, 1580, 2342))
    border = [box(-584, 584, ys - e, ys, z, z + 25) for z in (1605, 2292)]
    border += [box(x, x + 25, ys - e, ys, 1605, 2317) for x in (-584, 559)]
    words = [text(word, 170, e, (0, ys, z), (1, 0, 0), (0, -1, 0)) for word, z in (("ROAD", 2100), ("CLOSED", 1810))]
    m.add("sign_legend", BLACK, border, words)
    for x in (-px, px):
        m.add("lamp_housing", BLACK, box(x - 70, x + 70, -80, 60, 2340, 2520))
        m.add("lamp_lens", AMBER, cyl(80, (x, -80, 2430), (x, -100, 2430)))


# --------------------------------------------------------------------------- pallet of CMU

def cmu_pallet(m: Model):
    """Cube of 90 standard 8 x 8 x 16 in concrete blocks (two-core), banded on a 48 x 40 in pallet."""
    bl, bw, bh = 397.0, 194.0, 194.0
    gap = 0.0 if m.print_mode else 4.0
    ch = 10.0 if m.print_mode else 3.0
    block = cq.Workplane("XY").box(bl, bw, bh).edges().chamfer(ch)
    block = block.cut(cq.Workplane("XY").pushPoints([(-91, 0), (91, 0)]).rect(150, 130).extrude(bh + 2, both=True))
    block = block.val()

    hx, hy = 1219 / 2, 1016 / 2
    pallet = [box(x - 70, x + 70, -hy, hy, 0, 16) for x in (-520, 0, 520)]
    notches = [box(x - 115, x + 115, -hy - 1, hy + 1, 15, 54) for x in (-300, 300)]
    pallet += [cut(box(-hx, hx, y - 19, y + 19, 16, 105), *notches) for y in (-460, 0, 460)]
    m.add("pallet_frame", TIMBER_DARK, pallet)
    m.add("pallet_deck", TIMBER, [box(x - 70, x + 70, -hy, hy, 105, 124) for x in np.linspace(-hx + 70, hx - 70, 7)])

    z0 = 124 + gap
    blocks = []
    for layer in range(6):
        for i in range(3):
            for j in range(5):
                blocks.append(mv(block, (i - 1) * (bl + gap), (j - 2) * (bw + gap), z0 + layer * (bh + gap) + bh / 2))
    m.add("blocks", CMU, blocks)

    sx, sy = (3 * bl + 2 * gap) / 2, (5 * bw + 4 * gap) / 2
    top = z0 + 6 * bh + 5 * gap
    bt = 12.0 if m.print_mode else 2.0
    bands = []
    for yb in (-300, 300):
        bands += [box(-sx - bt, sx + bt, yb - 10, yb + 10, top, top + bt),
                  box(sx, sx + bt, yb - 10, yb + 10, 105, top), box(-sx - bt, -sx, yb - 10, yb + 10, 105, top)]
    for xb in (-400, 400):
        bands += [box(xb - 10, xb + 10, -sy - bt, sy + bt, top + bt, top + 2 * bt),
                  box(xb - 10, xb + 10, sy, sy + bt, 105, top + bt), box(xb - 10, xb + 10, -sy - bt, -sy, 105, top + bt)]
    m.add("bands", STEEL, bands)


# --------------------------------------------------------------------------- steel beams

def steel_beam_bundle(m: Model):
    """Twelve W12 x 26 wide-flange beams, 20 ft, stacked 5-4-3 on 4 x 4 timber dunnage."""
    d, bf = 310.4, 164.8
    tf, tw = m.t(9.65), m.t(5.84)
    L, gap, dn = 20 * FT, 12.0, 89.0
    prof = [(-bf / 2, 0), (bf / 2, 0), (bf / 2, tf), (tw / 2, tf), (tw / 2, d - tf), (bf / 2, d - tf),
            (bf / 2, d), (-bf / 2, d), (-bf / 2, d - tf), (-tw / 2, d - tf), (-tw / 2, tf), (-bf / 2, tf)]
    beam = prism(prof, "x", -L / 2, L / 2)
    scale_rust = Finish(rgb("#6b5446"), metal=0.4, rough=0.75)
    z = dn
    dunnage = [box(x - dn / 2, x + dn / 2, -560, 560, 0, dn) for x in (-2400, 0, 2400)]
    marks = []
    for layer, count in enumerate((5, 4, 3)):
        for i in range(count):
            y = (i - (count - 1) / 2) * (bf + gap)
            b = mv(beam, 0, y, z)
            m.add(f"beam_{layer + 1}_{i + 1}", scale_rust if (i + layer) % 3 == 1 else MILL, b)
            if not m.print_mode:
                marks.append(box(L / 2, L / 2 + 2, y - 30 + 20 * (i % 2), y + 30 + 20 * (i % 2),
                                 z + 130, z + 185))
        z += d
        if layer < 2:
            width = count * (bf + gap) / 2 + 60
            dunnage += [box(x - dn / 2, x + dn / 2, -width, width, z, z + dn) for x in (-2400, 0, 2400)]
            z += dn
    m.add("dunnage", TIMBER, dunnage)
    m.add("paint_marks", Finish(rgb("#f2c200"), rough=0.6), marks)


# --------------------------------------------------------------------------- wheelbarrow

def wheelbarrow(m: Model):
    """Contractor wheelbarrow, 6 cu ft steel tray, 16 in pneumatic wheel, hardwood handles."""
    t = m.t(2.5)
    bottom, top = (-175, 275, -190, 190, 380), (-400, 600, -350, 350, 700)
    tray = cq.Workplane("XY").add(frustum(bottom, top))
    try:
        tray = tray.edges("not(<Z or >Z)").fillet(90)
    except Exception:
        pass
    tray = tray.faces(">Z").shell(-t).val()
    rt = m.t(14)
    cx, cy = (top[0] + top[1]) / 2, 0
    lx, ly = top[1] - top[0], top[3] - top[2]
    rim = (cq.Workplane("XY").workplane(offset=700 - rt).center(cx, cy).sketch()
           .rect(lx + 36, ly + 36).vertices().fillet(110).finalize().extrude(rt))
    rim = rim.cut(cq.Workplane("XY").workplane(offset=700 - rt - 1).center(cx, cy).sketch()
                  .rect(lx - 2 * t, ly - 2 * t).vertices().fillet(85).finalize().extrude(rt + 2)).val()
    m.add("tray", GREEN, tray, rim)

    hs = m.t(45)
    a0, a1 = np.array([500.0, 210.0, 320.0]), np.array([-780.0, 300.0, 560.0])
    d = (a1 - a0) / np.linalg.norm(a1 - a0)
    handles, grips = [], []
    for s in (1, -1):
        p0, p1 = a0 * [1, s, 1], a1 * [1, s, 1]
        ds = d * [1, s, 1]
        handles.append(bar(p0, p1, hs, hs))
        grips.append(cyl(m.r(21) + hs / 2 - 10, p1 - ds * 230, p1 + ds * 15))
    m.add("handles", TIMBER, handles)
    m.add("grips", BLACK, grips)

    wc, R = (650.0, 0.0, 197.0), 203.0
    tread = []
    for k in range(28):        # a chevron tread: two offset blocks per pitch, inside the crown
        y0, y1 = (-30, 4) if k % 2 else (-4, 30)
        tread.append(rot(box(650 - 11, 650 + 11, y0, y1, 197 + R - 20, 197 + R + 5), 360 * k / 28, (0, 1, 0), wc))
    m.add("tyre", RUBBER, torus(R - 45, 45, wc, (0, 1, 0)), cyl(R - 45, (650, -45, 197), (650, 45, 197)), tread)
    m.add("wheel_rim", RED, cyl(110, (650, -40, 197), (650, 40, 197)))
    m.add("axle", STEEL, cyl(m.r(12), (650, -75, 197), (650, 75, 197)))
    steel = [bar((650, s * 62, 197), (500, s * 210, 320), m.t(30), m.t(8)) for s in (1, -1)]
    steel += [bar((590, s * 170, 680), (648, s * 58, 215), m.t(25), m.t(8)) for s in (1, -1)]
    for s in (1, -1):
        top_leg = (-200, s * 259, 451)
        foot = (-240, s * 275, 0)
        steel.append(bar(top_leg, foot, m.t(35), m.t(8), up=(1, 0, 0)))
        steel.append(box(-300, -180, s * 245, s * 305, 0, 14))
        steel.append(bar((-220, s * 267, 230), (-150, s * 170, 380), m.t(25), m.t(8), up=(1, 0, 0)))
    steel.append(bar((-150, -170, 380), (-150, 170, 380), m.t(30), m.t(8), up=(0, 0, 1)))
    m.add("frame", BLACK, steel)


# --------------------------------------------------------------------------- cable reel

def cable_reel(m: Model):
    """Wooden cable drum, 49 in flanges, wound with black power cable, tail run out on the ground."""
    R, Rb, half, ft = 625.0, 300.0, 350.0, 30.0
    zc = R - 8

    def ax(y, r):
        return cyl(r, (0, -y, zc), (0, y, zc)) if y > 0 else None

    flanges, battens, seams = [], [], []
    for s in (1, -1):
        flanges.append(cut(cyl(R, (0, s * half, zc), (0, s * (half + ft), zc)), cyl(50, (0, -2000, zc), (0, 2000, zc))))
        disc = cyl(R - 12, (0, s * (half + ft), zc), (0, s * (half + 2 * ft), zc))
        for off in (-430, -145, 145, 430):
            battens.append(box(-R, R, s * (half + ft), s * (half + 2 * ft), zc + off - 80, zc + off + 80).intersect(disc))
        if not m.print_mode:
            seams += [box(x - 3, x + 3, s * (half + ft - 4), s * (half + ft + 1), zc - R, zc + R).intersect(
                cyl(R - 4, (0, -2000, zc), (0, 2000, zc))) for x in range(-450, 451, 150)]
    m.add("flanges", TIMBER, flanges)
    m.add("battens", TIMBER_DARK, battens)
    m.add("plank_seams", Finish(rgb("#5a4530"), rough=0.9), seams)
    m.add("barrel", TIMBER_DARK, cut(ax(half, Rb), ax(half + 10, 50)))
    wraps = [torus(505, 27, (0, y, zc), (0, 1, 0)) for y in np.linspace(-half + 25, half - 25, 14)]   # overlapping, not tangent
    m.add("cable", RUBBER, cut(ax(half, 505), ax(half + 10, Rb - 1)), wraps)

    nuts = []
    for s in (1, -1):
        plate = box(-110, 110, s * (half + 2 * ft), s * (half + 2 * ft + m.t(8)), zc - 110, zc + 110)
        nuts.append(cut(plate, ax(half + 200, 50)))
        for a in (45, 135, 225, 315):
            x, z = 380 * math.cos(math.radians(a)), zc + 380 * math.sin(math.radians(a))
            hexa = [(x + 28 * math.cos(math.radians(k * 60)), z + 28 * math.sin(math.radians(k * 60))) for k in range(6)]
            nuts.append(prism(hexa, "y", s * (half + ft), s * (half + 2 * ft + 22)))
            nuts.append(cyl(m.r(10), (x, s * (half + 2 * ft), z), (x, s * (half + 2 * ft + 40), z)))
    m.add("hardware", STEEL, nuts)

    e = max(2.0, 0.3 * m.scale) if m.print_mode else 2.0
    yb = half + 2 * ft
    arrow = [(-260, -35), (140, -35), (140, -85), (280, 0), (140, 85), (140, 35), (-260, 35)]
    m.add("roll_arrow", RED, prism([(x, zc + 430 + z) for x, z in arrow], "y", yb, yb + e))
    tail = [(-60, 250, zc + 530), (320, 250, zc + 420), (560, 250, 320), (700, 250, 21),
            (1050, 280, 21), (1300, 180, 21)]
    m.add("cable_tail", RUBBER, pipe(tail, 25))
    m.add("cable_tape", RED, cyl(26, (1281.4, 187.4, 21), (1360, 156, 21)))   # sleeves the last 20 mm of the cable


# =========================================================================== registry

@dataclass
class Asset:
    key: str
    stem: str
    title: str
    build: Callable[[Model], None]
    az: float = 35
    el: float = 22
    size: str = "1200x900"
    set: int = 2


SET2 = [
    Asset("mini_excavator", "Mini_Excavator_3-5t", "Mini Excavator (3.5 t class)", mini_excavator, az=40, el=20),
    Asset("skid_steer", "Skid_Steer_Loader", "Skid Steer Loader (radial lift, 68 in bucket)", skid_steer, az=40, el=20),
    Asset("shipping_container", "Shipping_Container_20ft", "Shipping Container (20 ft ISO, site storage)",
          shipping_container, az=215, el=20),
    Asset("light_tower", "LED_Light_Tower", "LED Light Tower (towable, 30 ft mast)", light_tower, az=40, el=12,
          size="900x1200"),
    Asset("scaffold_tower", "Frame_Scaffold_Tower", "Frame Scaffold Tower (2 lifts, 5 x 7 ft)", scaffold_tower,
          az=210, el=18, size="900x1200"),
    Asset("portable_toilet", "Portable_Toilet", "Portable Toilet (site unit)", portable_toilet, az=35, el=15),
    Asset("type3_barricade", "Type_III_Barricade_Road_Closed", "Type III Barricade with ROAD CLOSED sign",
          type3_barricade, az=-60, el=12),
    Asset("jersey_barrier", "Jersey_Barrier_NJ_10ft", "Jersey Barrier (NJ shape, 10 ft)", jersey_barrier, az=30),
    Asset("jersey_barrier_run", "Jersey_Barrier_Run_3x10ft", "Jersey Barrier Run (3 x 10 ft, pinned)",
          jersey_barrier_run, az=25, el=18),
    Asset("cmu_pallet", "Pallet_of_CMU_Blocks", "Pallet of CMU Blocks (90 x 8x8x16 in)", cmu_pallet, az=35, el=25),
    Asset("steel_beam_bundle", "Steel_Beam_Bundle_W12x26", "Steel Beam Bundle (12 x W12x26, 20 ft)",
          steel_beam_bundle, az=25, el=22),
    Asset("wheelbarrow", "Contractor_Wheelbarrow", "Contractor Wheelbarrow (6 cu ft)", wheelbarrow, az=40, el=25),
    Asset("cable_reel", "Cable_Reel_Wooden", "Wooden Cable Reel (49 in, wound)", cable_reel, az=55, el=18),
]


def load_module_assets(folder: str, set_no: int, keys=None) -> list[Asset]:
    """Assets that live one per module in a folder (set3/wheel_loader.py, ...).

    Each module defines ASSET = {key, stem, title, az?, el?, size?} and build(m).
    Only the modules asked for are imported, so one half-written module cannot
    stop another from building; a module that fails to import is reported and
    skipped.
    """
    order_file = HERE / folder / "ORDER"
    names = [f.stem for f in sorted((HERE / folder).glob("*.py")) if not f.stem.startswith("_")]
    if order_file.exists():
        ranked = [n for n in order_file.read_text().split() if n in names]
        names = ranked + [n for n in names if n not in ranked]
    out = []
    for name in names:
        if keys and name not in keys:
            continue
        try:
            mod = importlib.import_module(f"{folder}.{name}")
            a = mod.ASSET
            assert a["key"] == name, f"ASSET key {a['key']!r} must match the file name"
        except Exception as e:  # noqa: BLE001  report and carry on with the rest
            print(f"skipping {folder}/{name}.py: {type(e).__name__}: {e}", file=sys.stderr)
            continue
        out.append(Asset(a["key"], a["stem"], a["title"], mod.build, a.get("az", 35), a.get("el", 22),
                         a.get("size", "1200x900"), set_no))
    return out


def all_assets(keys=None) -> list[Asset]:
    return SET2 + load_module_assets("set3", 3, keys)


# =========================================================================== build

COLLECTIONS = {2: "collection_set2.json", 3: "collection_set3.json"}


def render(asset: Asset, scale: float):
    cmd = ["node", str(HERE / "render_previews.mjs"), "--az", str(asset.az), "--el", str(asset.el)]
    subprocess.run(cmd + ["--size", asset.size, str(HERE / f"{asset.stem}.glb")], check=True)
    stl = HERE / f"print_1-{scale:g}" / f"{asset.stem}_1-{scale:g}.stl"
    subprocess.run(cmd + ["--size", "900x900", str(stl)], check=True)


def render_collection(set_no: int):
    scene = HERE / COLLECTIONS[set_no]
    if scene.exists():
        subprocess.run(["node", str(HERE / "render_previews.mjs"), "--scene", str(scene),
                        "--az", "30", "--el", "26", "--size", "1800x1100",
                        "--out", str(HERE / f"Construction_Set_{set_no}_collection.png")], check=True)


def diagnose(asset: Asset, scale: float, min_wall: float):
    """Which parts end up in which separate piece of the print, to find what floats."""
    import manifold3d as mf
    from cadkit import _to_manifold

    m = Model(print_mode=True, scale=scale, min_wall=min_wall)
    asset.build(m)
    items = [(f"{name}[{i}]", _to_manifold(so, 0.02 * scale, 0.15))
             for name, _, shapes in m.parts for i, s in enumerate(shapes) for so in s.Solids()]
    bad = [n for n, x in items if x is None]
    items = [(n, x) for n, x in items if x is not None]
    body = mf.Manifold.batch_boolean([x for _, x in items], mf.OpType.Add)
    comps = sorted(body.decompose(), key=lambda c: -c.volume())
    print(f"{asset.key}: {len(comps)} piece(s) before trimming at the bed"
          + (f"; not closed solids, left out: {bad}" if bad else ""))
    for k, c in enumerate(comps):
        owners = [n for n, x in items
                  if mf.Manifold.batch_boolean([x, c], mf.OpType.Intersect).volume() > 0.5 * x.volume()]
        bb = [round(v) for v in c.bounding_box()]
        kind = "void" if c.volume() < 0 else "piece"
        shown = owners if k else owners[:6] + (["..."] if len(owners) > 6 else [])
        print(f"  {kind} {k}: volume {c.volume() / 1e9:.4f} m3, box {bb}: {shown}")


def build_print(asset: Asset, scale: float, min_wall: float) -> dict:
    printed = Model(print_mode=True, scale=scale, min_wall=min_wall)
    asset.build(printed)
    pdir = HERE / f"print_1-{scale:g}"
    pdir.mkdir(exist_ok=True)
    return export_print(printed, pdir / f"{asset.stem}_1-{scale:g}.stl", scale)


def build(asset: Asset, scale: float, min_wall: float, do_render: bool) -> dict:
    t0 = time.time()
    shown = Model()
    asset.build(shown)
    (x0, x1), (y0, y1), (z0, z1) = shown.bounds()
    step, glb = HERE / f"{asset.stem}.step", HERE / f"{asset.stem}.glb"
    export_step(shown, step, asset.title)
    export_glb(shown, glb)

    report = build_print(asset, scale, min_wall)

    if do_render:
        render(asset, scale)

    info = {
        "key": asset.key, "title": asset.title, "stem": asset.stem, "set": asset.set,
        "size_mm": [round(x1 - x0), round(y1 - y0), round(z1 - z0)],
        "parts": len(shown.parts),
        "print": report,
        "seconds": round(time.time() - t0, 1),
    }
    L, W, H = (v / FT for v in info["size_mm"])
    print(f"{asset.stem}: {L:.1f} x {W:.1f} x {H:.1f} ft, {info['parts']} parts; "
          f"1:{scale:g} print {report['size_mm']} mm, {report['volume_cm3']} cm3, "
          f"{report['pieces']} piece(s), {info['seconds']} s")
    if report["nonmanifold_edges"]:
        print(f"  WARNING: {report['nonmanifold_edges']} edges of the print mesh are not shared by exactly two triangles")
    if report["pieces"] != 1 or report["skipped_solids"]:
        print(f"  WARNING: {report['pieces']} separate pieces, {report['skipped_solids']} solids skipped"
              f" (run with --diagnose to see which parts)")
    if report["sealed_voids"]:
        print(f"  note: {report['sealed_voids']} small sealed void(s) inside the print body")
    return info


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("keys", nargs="*", help="assets to build (default: all)")
    p.add_argument("--list", action="store_true")
    p.add_argument("--set", type=int, choices=sorted(COLLECTIONS), help="only this set")
    p.add_argument("--scale", type=float, default=50, help="print scale, 1:N (default 50)")
    p.add_argument("--min-wall", type=float, default=0.8, help="thinnest printed wall, mm (default 0.8)")
    p.add_argument("--no-render", action="store_true", help="skip the preview renders")
    p.add_argument("--render-only", action="store_true", help="re-render the previews of what is built")
    p.add_argument("--print-only", action="store_true", help="only rewrite the print STLs (and their index entries)")
    p.add_argument("--no-index", action="store_true", help="don't update assets.json")
    p.add_argument("--diagnose", action="store_true", help="list which parts make up each separate print piece")
    args = p.parse_args()

    assets = all_assets(args.keys or None)
    if args.list:
        for a in assets:
            print(f"set {a.set}  {a.key:24s} {a.title}")
        return 0
    chosen = [a for a in assets if (not args.keys or a.key in args.keys) and (not args.set or a.set == args.set)]
    unknown = set(args.keys) - {a.key for a in assets}
    if unknown:
        p.error(f"unknown or unloadable asset(s): {', '.join(sorted(unknown))}")

    if args.diagnose:
        for a in chosen:
            diagnose(a, args.scale, args.min_wall)
        return 0
    whole_sets = sorted({a.set for a in chosen}) if not args.keys else []
    if args.render_only:
        for a in chosen:
            render(a, args.scale)
        for n in whole_sets:
            render_collection(n)
        return 0
    if args.print_only:
        index = HERE / "assets.json"
        known = {r["key"]: r for r in json.loads(index.read_text())} if index.exists() else {}
        results = []
        for a in chosen:
            report = build_print(a, args.scale, args.min_wall)
            flag = "" if report["pieces"] == 1 and not report["nonmanifold_edges"] else "  WARNING"
            print(f"{a.stem}: 1:{args.scale:g} print {report['size_mm']} mm, {report['pieces']} piece(s), "
                  f"{report['nonmanifold_edges']} bad edges{flag}")
            if a.key in known and args.scale == 50:
                results.append({**known[a.key], "print": report})
        args.no_render = True
        if args.scale != 50:
            args.no_index = True
    else:
        results = [build(a, args.scale, args.min_wall, not args.no_render) for a in chosen]
    if not args.no_render:
        for n in whole_sets:
            render_collection(n)
    if not args.no_index:
        index = HERE / "assets.json"
        old = {r["key"]: r for r in json.loads(index.read_text())} if index.exists() else {}
        old.update({r["key"]: r for r in results})
        order = [a.key for a in all_assets()]
        index.write_text(json.dumps([old[k] for k in order if k in old], indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
