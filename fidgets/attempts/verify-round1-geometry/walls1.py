"""Thin places the earlier review found, measured again on sections of the solids.
Part 1: neck tab wall round the nod sockets; roof and walls of the neck slot; nod pins."""
import numpy as np
import manifold3d as mf
from lib import *

parts, joints, info = cb.make_capybara()
tparts, tjoints, tinfo = cb.make_test()
head, b1 = parts["head"], parts["body 1"]
NX, NZ = cb.NECK_X, cb.NECK_Z
c = np.array([NX, NZ])

print("1. NECK TAB WALL ROUND EACH NOD SOCKET (head; sections y = const; tab face is at |y| = %.2f)" % (cb.TAB_W / 2))
for label, hd in (("full model", head), ("test strip", tparts["head"])):
    worst = (9, None)
    for side in (1, -1):
        for d in (0.002, 0.01, 0.03, 0.05, 0.1, 0.2, 0.3, 0.5, 0.8, 1.0):
            y = side * (cb.TAB_W / 2 - d)
            ps = sec_y(hd, y)
            hole = [p for p in ps if np.linalg.norm(p - c, axis=1).max() < 3.25 and inside(p, c)]
            if not hole:
                if label == "full model" and side == 1:
                    print(f"   y={y:+.3f}: no socket in this section")
                continue
            h = hole[0]
            r = np.linalg.norm(h - c, axis=1)
            others = [p for p in ps if p is not h]
            d2, at = min((loop_gap(h, o) for o in others), key=lambda t: t[0])
            if d2 < worst[0]:
                worst = (d2, (y, at))
            if label == "full model" and side == 1:
                print(f"   y={y:+.3f} ({d:.3f} in from the face): socket radius {r.min():.3f}..{r.max():.3f}; thinnest wall to the tab's outside {d2:.3f} at x={at[0]:.2f} z={at[1]:.2f}")
    print(f"   {label}: thinnest over both sides and all depths {worst[0]:.3f} mm (y={worst[1][0]:+.3f}, x={worst[1][1][0]:.2f}, z={worst[1][1][1]:.2f})")
# web left between the two socket tips, on the axis
ps = sec_z(head, NZ)
r = runs([p[:, ::-1] for p in ps], NX)       # runs along y at x = NX  (swap so u = y? no: u must be x)
ps_x = sec_x(head, NX)
print("   along the nod axis itself (x=NECK_X, z=NECK_Z), solid runs in y:", [(round(a, 3), round(b, 3)) for a, b in runs([p[:, ::-1] for p in ps_x], NZ)])
# radial wall in the plane x = NECK_X (straight above / below the axis) and the plane z = NECK_Z
for nm, ps_, u0 in (("plane x=NECK_X", sec_x(head, NX), None), ("plane z=NECK_Z", sec_z(head, NZ), None)):
    pass

print("\n2. BODY 1: THE STUB PINS (sections y = const through the prong wall and the pin)")
for label, body in (("full model", b1), ("test strip", tparts["body 1"])):
    hw = cb.TAB_W / 2 + cb.TAB_GAP
    row = []
    for y in (hw + 0.5, hw + 0.01, hw - 0.01, hw - 0.2, hw - 0.5, hw - cb.NOD_DEPTH + 0.01):
        ps = sec_y(body, y)
        pin = [p for p in ps if inside(p, c)]
        if not pin:
            row.append(f"y={y:.2f}: nothing on the axis"); continue
        p = pin[0]
        rr = np.linalg.norm(p - c, axis=1)
        row.append(f"y={y:.2f}: x-extent {np.ptp(p[:, 0]):.3f} z-extent {np.ptp(p[:, 1]):.3f} (r {rr.min():.3f}..{rr.max():.3f})")
    print(f"   {label}: " + "; ".join(row))

print("\n3. ROOF OVER THE NECK SLOT, whole length (body 1). For every upright line over the slot: the top run of solid.")
for label, body in (("full model", b1), ("test strip", tparts["body 1"])):
    hw = cb.TAB_W / 2 + cb.TAB_GAP
    best = (9, None)
    perx = {}
    open_cols = []
    for y in np.arange(-hw - 0.6, hw + 0.6001, 0.05):
        ps = sec_y(body, y)
        if not ps:
            continue
        for x in np.arange(13.25, 31.0, 0.05):
            rs = runs(ps, x)
            if not rs:
                continue
            lo, hi = rs[-1]
            # only columns with empty space beneath the top run that belongs to the slot (inside the doorway's reach)
            if lo < 0.5:
                continue
            t = hi - lo
            k = round(float(x), 2)
            if k not in perx or t < perx[k][0]:
                perx[k] = (t, y, lo, hi)
            if t < best[0]:
                best = (t, (x, y, lo, hi))
    print(f"   {label}: thinnest upright run of roof {best[0]:.3f} mm at x={best[1][0]:.2f} y={best[1][1]:.2f} (z {best[1][2]:.2f}..{best[1][3]:.2f})")
    if label == "full model":
        for x in np.arange(13.5, 30.6, 0.5):
            k = round(float(x), 2)
            if k in perx:
                t, y, lo, hi = perx[k]
                print(f"      x={k:5.2f}: thinnest {t:.3f} at y={y:+.2f} (z {lo:.2f}..{hi:.2f})")
            else:
                print(f"      x={k:5.2f}: no roofed column (open, or solid to the bed)")

print("\n   roof measured square to its faces: sections x = const, distance between the slot's outline and the body's outer outline")
for x in np.arange(14.0, 29.01, 0.5):
    ps = sec_x(b1, x)
    if not ps:
        continue
    # outer loop = the one with the largest area; slot = empty space inside |y| < hw+1 that is not the outer loop
    A = [abs(area(p)) for p in ps]
    outer = ps[int(np.argmax(A))]
    top = outer[(np.abs(outer[:, 0]) < 6.0) & (outer[:, 1] > 9.0)]       # the back's surface above the slot
    inner = [p for p in ps if p is not outer and np.abs(p[:, 0]).max() < 4.5]
    # when the slot is open to the bed or the front it is part of the outer loop: take its roof = outer vertices with |y|<3.2 and 4 < z < top
    if inner:
        cav = np.vstack(inner)
    else:
        cav = outer[(np.abs(outer[:, 0]) < hw + 0.05) & (outer[:, 1] > 3.0) & (outer[:, 1] < 13.5)]
    if not len(cav) or not len(top):
        print(f"      x={x:5.2f}: no roof here"); continue
    # distance from cavity vertices to the top polyline and back
    D = np.sqrt(((cav[:, None, :] - top[None]) ** 2).sum(2))
    i = np.unravel_index(np.argmin(D), D.shape)
    print(f"      x={x:5.2f}: slot roof peak z={cav[:, 1].max():.2f}, back at y=0 z={outer[np.abs(outer[:, 0]) < 0.3][:, 1].max():.2f}; nearest slot-to-back distance {D[i]:.3f} "
          f"(slot point y={cav[i[0]][0]:+.2f} z={cav[i[0]][1]:.2f})")

print("\n4. WALLS OF THE NECK SLOT (the prongs): section z = const, material between the slot and the flank / the leg pin's root")
for z in (0.1, 1.0, 3.0, 5.0, cb.NECK_Z, 8.0, 10.0, 12.0):
    ps = sec_z(b1, z)
    out = []
    for x in (15.0, 17.0, 19.0, 21.0, 23.0, NX, 25.0, 27.0):
        rs = runs([p[:, ::-1] for p in ps], x) if False else None
    # runs along y at given x: swap columns so that u = x
    for x in (16.0, 18.0, 20.0, 22.0, NX, 25.5, 27.0):
        rs = runs([np.c_[p[:, 0], p[:, 1]] for p in ps], x)
        out.append(f"x={x:.1f}: " + (" ".join(f"[{a:+.2f},{b:+.2f}]" for a, b in rs) if rs else "-"))
    print(f"   z={z:5.2f}: " + "  ".join(out))
