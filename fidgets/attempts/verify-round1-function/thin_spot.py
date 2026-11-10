"""Spot checks of the walls the fixes were about, measured another way (2-D sections, not cavity_wall)."""
import numpy as np
from common import cb
import manifold3d as mf
parts, joints, info = cb.make_capybara()
head, b1 = parts["head"], parts["body 1"]
w = cb.TAB_W / 2
# 1. neck tab round its sockets: section of the head in planes y = const, wall = ring between socket hole and outside
for y in (w - 0.001, w - 0.05, w - 0.3, w - 0.6, 1.3):
    cs = cb.section_y(head, y)                     # (x, -z)
    best = None
    for p in cs.decompose():
        b = p.bounds()
        if b[0] < cb.NECK_X < b[2]:
            polys = p.to_polygons()
            if len(polys) < 2:
                continue
            # the hole is the loop closest to the axis; the wall is its distance to the other loops
            loops = [np.asarray(q) for q in polys]
            d = [np.abs(np.hypot(q[:, 0] - cb.NECK_X, q[:, 1] + cb.NECK_Z)).max() for q in loops]
            hole = loops[int(np.argmin(d))]
            others = np.vstack([q for q in loops if q is not hole])
            # densify outer loops
            dens = []
            for q in [q for q in loops if q is not hole]:
                for i in range(len(q)):
                    a, b_ = q[i], q[(i + 1) % len(q)]
                    for t in np.linspace(0, 1, 30, endpoint=False):
                        dens.append(a + t * (b_ - a))
            dens = np.array(dens)
            dd = np.sqrt(((hole[:, None, :] - dens[None, :, :]) ** 2).sum(-1))
            i, j = np.unravel_index(dd.argmin(), dd.shape)
            best = (dd.min(), hole[i], dens[j], np.hypot(hole[:, 0] - cb.NECK_X, hole[:, 1] + cb.NECK_Z).max())
    if best:
        print(f"tab section y = {y:.3f}: socket radius {best[3]:.3f}, thinnest wall to the outside {best[0]:.3f} mm (hole pt x {best[1][0]:.2f} z {-best[1][1]:.2f} -> outside pt x {best[2][0]:.2f} z {-best[2][1]:.2f})")
    else:
        print(f"tab section y = {y:.3f}: no closed socket ring found")
# 2. roof over the neck slot: upright thickness of the roof on a grid, and x 0.707 for a 45 deg face
tmin = (9, None)
for x in np.arange(cb.NECK_X - 6, cb.NECK_X + 5.01, 0.25):
    for y in np.arange(0, 2.71, 0.15):
        runs = cb.column(b1, x, y, 2.0)
        cav = cb.column(cb.doorway(), x, y, -0.5)
        if not runs or not cav:
            continue
        top = runs[-1]
        if top[0] > cav[-1][1] - 0.2:               # the top run sits over the slot
            t = top[1] - top[0]
            if t < tmin[0]:
                tmin = (t, (round(float(x), 2), round(float(y), 2), round(top[0], 2), round(top[1], 2)))
print(f"roof over the slot: thinnest upright run {tmin[0]:.2f} mm at (x, y, z0, z1) = {tmin[1]}")
# 3. head-nod pin engagement: how far each stub pin reaches into the tab, with the head pushed to one side
for dy in (0.0, 0.2, 0.4):
    H = head.translate([0, dy, 0])
    hit = (H ^ b1).volume()
    # overlap of pin with the tab's convex filling (socket filled) = engagement
    y_face = w + cb.TAB_GAP
    eng = [y_face - cb.NOD_DEPTH - (-w + dy) if s < 0 else None for s in (-1,)]
    print(f"head pushed {dy} mm to +y: overlaps body {hit:.4f} mm3; pin tip at |y| = {y_face - cb.NOD_DEPTH:.2f}; tab faces at y = {-w + dy:.2f} and {w + dy:.2f} -> "
          f"-y pin is {(-w + dy) - (-(y_face - cb.NOD_DEPTH)):+.2f} mm inside the tab face, +y pin {(y_face - cb.NOD_DEPTH) - (w + dy):+.2f} (negative = engaged)")
# how far can the head really be pushed sideways
for dy in np.arange(0.02, 1.0, 0.02):
    if (head.translate([0, dy, 0]) ^ b1).volume() > 1e-6:
        print(f"head side play: {dy - 0.02:.2f} mm each way"); break
