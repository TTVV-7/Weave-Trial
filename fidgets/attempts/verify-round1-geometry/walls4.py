"""Part 4: neck slot roof in 3D; bore wall below the countersink; groove left at each body joint; head's rear top edge."""
import numpy as np
import manifold3d as mf
from lib import *
parts, joints, info = cb.make_capybara()
tparts, _, tinfo = cb.make_test()
b1, head = parts["body 1"], parts["head"]
NX, NZ = cb.NECK_X, cb.NECK_Z

print("1. NECK SLOT ROOF, exact 3D distance from the slot's empty space to the open air above the back")
for label, body in (("full", b1), ("strip", tparts["body 1"])):
    for zcut in (9.5, 10.5, 11.5):
        air = (cb.box(10, 31, -12, 12, zcut, 22) - body).decompose()
        cav = [p for p in air if (p ^ cb.ball(0.02, NX, 0, 12.9)).volume() > 0]
        sky = [p for p in air if (p ^ cb.ball(0.02, NX, 0, 21)).volume() > 0]
        if not cav or not sky or cav[0] is sky[0] or (cav[0] ^ cb.ball(0.02, NX, 0, 21)).volume() > 0:
            print(f"   {label}: above z={zcut} the slot is OPEN to the air ({len(air)} pieces of empty space)")
            continue
        bbx = cav[0].bounding_box()
        print(f"   {label}: slot space above z={zcut}: x {bbx[0]:.2f}..{bbx[3]:.2f} y {bbx[1]:.2f}..{bbx[4]:.2f} top z {bbx[5]:.2f}; nearest it comes to the open air {cav[0].min_gap(sky[0], 6.0):.3f} mm")
# the whole slot (down to the bed) against the air outside the flanks and above, with the front and bed openings plugged
plug = cb.box(8, NX - 6.0, -3.2, 3.2, -1, 9.6) + cb.box(8, 31, -3.2, 3.2, -1, 0.02)
air = (cb.box(8, 31, -12, 12, -1, 22) - (b1 + plug)).decompose()
cav = [p for p in air if (p ^ cb.ball(0.02, NX, 0, 12.9)).volume() > 0]
rest = [p for p in air if (p ^ cb.ball(0.02, NX, 0, 12.9)).volume() == 0]
if cav and rest:
    print(f"   full: whole slot (front and bed openings plugged) against every other empty space round body 1 (outside, hook pocket, leg-pin side): {cav[0].min_gap(cb.union(rest), 6.0):.3f} mm, {len(rest)} other spaces")
    for p in rest:
        bbx = p.bounding_box()
        print(f"        other space x {bbx[0]:.1f}..{bbx[3]:.1f} y {bbx[1]:.1f}..{bbx[4]:.1f} z {bbx[2]:.1f}..{bbx[5]:.1f}: gap to the slot {cav[0].min_gap(p, 6.0):.3f}")

print("\n2. HEAD WALL ROUND THE ORANGE'S BORE, per layer (bore loop to any other outline)")
OX = cb.ORANGE_X
row = []
for z in (0.005, 0.1, 0.3, 0.6, 1.0, 1.4, 2.0, 3.0, 4.0, 5.0, 6.0, 6.6, 7.0, 8.0, 9.0, 10.0, 11.0, 11.8, 12.0, 12.2, 12.35):
    ps = sec_z(head, z)
    bore = [p for p in ps if inside(p, (OX, 0.0137)) and np.hypot(p[:, 0] - OX, p[:, 1]).max() < 6]
    if not bore:
        row.append(f"z={z}: bore not a closed loop"); continue
    d, atp = min((loop_gap(bore[0], o) for o in ps if o is not bore[0]), key=lambda t: t[0])
    row.append(f"z={z}: {d:.3f} (x={atp[0]:.2f}, y={atp[1]:+.2f})")
for i in range(0, len(row), 6):
    print("   " + "   ".join(row[i:i + 6]))

print("\n3. GROOVE ACROSS THE BACK AT EACH BODY JOINT (straight pose), on the centre line y = 0 and at y = 4")
whole = cb.union([parts[f"body {k}"] for k in (1, 2, 3, 4)])
for i, at in enumerate(cb.AXES):
    for y in (0.0137, 4.0):
        ps = sec_y(whole, y)
        xs = np.arange(at + 6.0, at + 11.0, 0.02)
        tops = np.array([max((b for a, b in runs(ps, x + 0.0003)), default=0.0) for x in xs])
        # the groove: where the top falls below the line joining the back either side
        ref = np.interp(xs, [xs[0], xs[-1]], [tops[0], tops[-1]])
        dip = ref - tops
        g = dip > 0.2
        if g.any():
            print(f"   joint {i + 1}, y={y:.1f}: back is {tops[0]:.2f} in front and {tops[-1]:.2f} behind; groove more than 0.2 deep from axis+{xs[g][0] - at:.2f} to axis+{xs[g][-1] - at:.2f} "
                  f"({xs[g][-1] - xs[g][0]:.2f} mm wide), deepest {dip.max():.2f} mm at axis+{xs[np.argmax(dip)] - at:.2f}; step at the lip's face {np.abs(np.diff(tops)).max():.2f} mm")
        else:
            print(f"   joint {i + 1}, y={y:.1f}: no groove deeper than 0.2")

print("\n4. HEAD: the top rear edge over the hollow back (section y = 0 and y = 3)")
for y in (0.0137, 3.0):
    ps = sec_y(head, y)
    outer = max(ps, key=lambda p: abs(area(p)))
    i = int(np.argmax(outer[:, 0] * (outer[:, 1] > 12.0)))
    pts = outer[(outer[:, 1] > 11.5) & (outer[:, 0] > 14.5) & (outer[:, 0] < 17.5)]
    k = int(np.argmax(pts[:, 0] + pts[:, 1]))
    print(f"   y={y:.1f}: rear top corner at x={pts[k][0]:.2f} z={pts[k][1]:.2f}; thickness in x at 0.2 / 0.4 / 0.8 below it: " + " / ".join(
        f"{max((b - a for a, b in runs([np.c_[p[:, 1], p[:, 0]] for p in ps], pts[k][1] - d) if b > pts[k][0] - 3), default=0):.2f}" for d in (0.2, 0.4, 0.8)))
