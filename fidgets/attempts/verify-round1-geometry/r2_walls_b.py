"""Round 2. Thin places measured again on the revised solids, part B: body joints.
 A. socket lip over the ball (upright runs, 3D, and in plan)
 B. horn of the socket beside the ball, layer by layer from the bed
 C. hook: tongue, bridge, and the rim it holds
Own sections and own 3D gaps; none of the design's check functions are used."""
import sys
import numpy as np
import manifold3d as mf
from lib import *

RJ = mf.JoinType.Round
RB, GS, ZC = cb.R_BALL, cb.G_SEAM, cb.Z_C


def bx(x0, x1, y0, y1, z0, z1):
    return mf.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def flat(m):
    return mf.CrossSection(m.project().to_polygons(), mf.FillRule.Positive)


def has(cs, x, y, r=0.02):
    return (cs ^ mf.CrossSection.circle(r, 8).translate([x, y])).area() > 0


def piece2(cs, x, y):
    for p in cs.decompose():
        if has(p, x, y):
            return p
    return mf.CrossSection()


def neck2(cs, a, b, hi=3.0):
    """Width of the narrowest place on the way from point a to point b inside cs: twice the largest
    erosion at which both points (each allowed to slip 2x the erosion) are still in one piece."""
    def joined(r):
        e = cs.offset(-r, RJ, 2.0, 64)
        for p in e.decompose():
            g = p.offset(r + 0.01, RJ, 2.0, 32)
            if has(g, *a) and has(g, *b):
                return True
        return False
    if not joined(0.0):
        return 0.0
    lo = 0.0
    for _ in range(14):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if joined(mid) else (lo, mid)
    return 2 * lo


def radial(m, at, deg):
    """Section of m in the upright half-plane through the joint axis at `deg` from straight back: CrossSection in (r, -z)... returned as polygons (r, z) and as a CrossSection in (r, z)."""
    t = m.translate([-at, 0, 0]).rotate([0, 0, -deg])
    cs = t.rotate([90, 0, 0]).slice(0.0)            # (x, y, z) -> (x, -z, y): coords (x, -z)
    cs = cs.mirror([0, 1])                          # -> (x, z)
    return cs ^ mf.CrossSection.square([40, 60]).translate([0.0, -5])


which = sys.argv[1] if len(sys.argv) > 1 else "full"
parts, joints, info = cb.make_capybara() if which == "full" else cb.make_test()
axes = info["axes"]
print(f"================ {which} model, joints at x = {axes} ================")

print("A. SOCKET LIP OVER THE BALL (rear segment of each joint)")
for i, at in enumerate(axes):
    rear, front = parts[f"body {i + 2}"], parts[f"body {i + 1}"]
    r = RB + GS
    # upright runs
    best = (9, None)
    hist = np.zeros(6, int)
    for y in np.arange(-r, r + 1e-6, 0.05):
        ps = sec_y(rear, y)
        if not ps:
            continue
        for x in np.arange(at + 0.025, at + r, 0.05):
            if (x - at) ** 2 + y ** 2 > (r - 0.05) ** 2:
                continue
            rs = [q for q in runs(ps, x) if q[0] > ZC + 0.5]     # runs that start above the equator: the lip
            for lo, hi in rs:
                t = hi - lo
                hist[min(int(t / 0.2), 5)] += 1
                if t < best[0]:
                    best = (t, (x, y, lo, hi))
    t, (x, y, lo, hi) = best
    print(f"   joint {i + 1} (axis {at}): thinnest upright run of lip {t:.3f} mm at axis+{x - at:.2f}, y={y:+.2f}, z {lo:.2f}..{hi:.2f}; "
          f"columns <0.2,<0.4,<0.6,<0.8,<1.0,>=1.0: {hist.tolist()}")
    # 3D: the socket space straight under the lip against the air straight above it
    zone = mf.Manifold.cylinder(40, r - 0.02, r - 0.02, 256).translate([at, 0, ZC + 0.5]) ^ bx(at, at + 20, -20, 20, 0, 60)
    lip = rear ^ zone
    shadow = mf.Manifold.extrude(flat(lip).offset(-0.02, RJ), 60).translate([0, 0, -1])
    col = shadow ^ bx(at, at + 20, -20, 20, ZC + 0.5, 40)
    void = col - rear
    under, over = [], []
    top = rear.bounding_box()[5]
    for p in void.decompose():
        b = p.bounding_box()
        (over if b[5] > 39.9 else under).append(p)
    if under and over:
        g = cb.union(under).min_gap(cb.union(over), 6.0)
        print(f"      3D: empty space straight under the lip to the open air straight above it: {g:.3f} mm ({len(under)} + {len(over)} spaces)")
    else:
        print(f"      3D: under {len(under)} over {len(over)} - not separated")
    # in plan: per layer, what a 0.8 mm disc cannot enter, inside the lip zone
    found = []
    for z in np.arange(ZC + 0.55, top, 0.1):
        cs = rear.slice(float(z))
        if cs.is_empty():
            continue
        zc = mf.CrossSection.circle(r, 128).translate([at, 0])
        thin = (cs - cs.offset(-0.4, RJ, 2.0, 64).offset(0.42, RJ, 2.0, 64)) ^ zc
        for p in thin.decompose():
            if p.area() > 0.05:
                b = p.bounds()
                found.append((p.area(), float(z), b))
    found.sort(key=lambda f: -f[0])
    print(f"      in plan: {len(found)} bits over 0.05 mm2 that a 0.8 mm disc cannot enter inside the lip zone" +
          ("; largest: " + "; ".join(f"z={z:.2f} {a:.2f} mm2 x {b[0]:.2f}..{b[2]:.2f} y {b[1]:+.2f}..{b[3]:+.2f}" for a, z, b in found[:4]) if found else ""))
    # the lip's blunt front face: its height where it is lowest, from sections through the axis
    row = []
    for deg in (0, 15, 30, 45, 55):
        ps = polys(radial(rear, at, deg))
        tip = None
        for p in ps:
            sel = p[(p[:, 1] > ZC + 0.5) & (p[:, 0] < r)]
            if len(sel):
                rmin = sel[:, 0].min()
                face = sel[np.abs(sel[:, 0] - rmin) < 0.02]
                if tip is None or rmin < tip[0]:
                    tip = (rmin, face[:, 1].min(), face[:, 1].max())
        if tip:
            row.append(f"{deg} deg: face at r={tip[0]:.2f}, z {tip[1]:.2f}..{tip[2]:.2f} ({tip[2] - tip[1]:.2f} tall)")
    print("      the lip's front edge in sections through the axis: " + "; ".join(row))
    # seam between the front segment's collar and the lip, straight pose
    print(f"      3D gap between the two segments as printed {front.min_gap(rear, 3.0):.3f}")

print("\nB. HORN OF THE SOCKET BESIDE THE BALL (rear segment), per layer: width in y at its blunt front face, 0.02 / 0.1 / 0.3 behind the face")
for i, at in enumerate(axes):
    rear = parts[f"body {i + 2}"]
    rows, worst = [], (9, None)
    zs = [0.001, 0.02, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.5, 0.7, 1.0, 1.25, 1.5, 2.0, 2.2, 2.5, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 8.5, 9.0, 10.0, 11.0]
    for z in zs:
        for side in (1,):
            cs = rear.slice(float(z)) ^ mf.CrossSection.square([12, 8]).translate([at + 4, 3.5])
            if cs.is_empty():
                continue
            # the horn is the piece of the layer furthest forward, beside the ball
            ps = polys(cs)
            x0 = min(p[:, 0].min() for p in ps)
            ws = []
            for d in (0.02, 0.1, 0.3):
                rr = runs([p[:, ::-1] for p in ps], x0 + d) if False else None
                ry = []
                for p in ps:
                    a, b = p, np.roll(p, -1, axis=0)
                    s = (a[:, 0] - (x0 + d)) * (b[:, 0] - (x0 + d)) < 0
                    if s.any():
                        tt = (x0 + d - a[s, 0]) / (b[s, 0] - a[s, 0])
                        ry += list(a[s, 1] + tt * (b[s, 1] - a[s, 1]))
                ry = sorted(ry)
                ws.append(min((ry[k + 1] - ry[k] for k in range(0, len(ry) - 1, 2)), default=0.0))
            rows.append(f"z={z:g}: {ws[0]:.2f}/{ws[1]:.2f}/{ws[2]:.2f} (face at axis+{x0 - at:.2f})")
            if ws[0] < worst[0]:
                worst = (ws[0], z)
    print(f"   joint {i + 1}: narrowest at the face {worst[0]:.3f} mm at z={worst[1]}")
    if i == 0:
        for k in range(0, len(rows), 5):
            print("      " + "   ".join(rows[k:k + 5]))
    # the horn as a whole: what a 0.8 disc cannot enter, per layer, near the bed, in the front 3 mm of the rear segment beside the ball
    found = []
    for z in np.arange(0.05, 9.0, 0.1):
        cs = rear.slice(float(z))
        win = mf.CrossSection.square([4.5, 20]).translate([at + 6.5, -10])
        thin = (cs - cs.offset(-0.4, RJ, 2.0, 64).offset(0.42, RJ, 2.0, 64)) ^ win
        for p in thin.decompose():
            if p.area() > 0.05:
                found.append((p.area(), float(z), p.bounds()))
    found.sort(key=lambda f: -f[0])
    print(f"      {len(found)} bits over 0.05 mm2 that a 0.8 mm disc cannot enter in layers 0..9 at the socket's front" +
          ("; largest: " + "; ".join(f"z={z:.2f} {a:.2f} mm2 x {b[0]:.2f}..{b[2]:.2f} y {b[1]:+.2f}..{b[3]:+.2f}" for a, z, b in found[:5]) if found else ""))

print("\nC. HOOK (rear segment) AND RIM (front segment)")
for i, at in enumerate(axes):
    rear, front = parts[f"body {i + 2}"], parts[f"body {i + 1}"]
    rm = (cb.T_IN + cb.T_OUT) / 2
    print(f"   joint {i + 1}:")
    row = []
    for z in (0.001, 0.1, 0.2, 0.35, 0.5, 1.0, 2.0, 3.0):
        cs = rear.slice(float(z))
        tg = piece2(cs, at + rm, 0)
        if tg.is_empty():
            row.append(f"z={z:g}: none")
            continue
        P = np.vstack(polys(tg))
        rr = np.hypot(P[:, 0] - at, P[:, 1])
        ang = np.degrees(np.arctan2(P[:, 1], P[:, 0] - at))
        own = has(tg, at + 12, 0)            # joined to the rest of the segment in this layer?
        # largest disc that fits
        lo, hi = 0.0, 3.0
        for _ in range(14):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if not tg.offset(-mid, RJ, 2.0, 64).is_empty() else (lo, mid)
        inner = P[rr < rr.min() + 0.03]
        chord = np.ptp(inner[:, 1])
        row.append(f"z={z:g}: r {rr.min():.2f}..{rr.max():.2f} ({rr.max() - rr.min():.2f} across), half angle {ang.max():.1f}, chord at its inner corners {chord:.2f}, "
                   f"area {tg.area():.1f}, largest disc {2 * lo:.2f}" + (" [joined to the segment]" if own else ""))
    print("      tongue per layer: " + "\n                        ".join(row))
    # bridge: sections through the axis; narrowest place between the tongue and the body of the segment
    row = []
    for deg in (0, 8, 14, 17.5, -17.5):
        cs = radial(rear, at, deg)
        row.append(f"{deg:g} deg: {neck2(cs, (rm, 0.6), (RB + 1.3, 6.0)):.3f}")
    print("      narrowest place between tongue and segment, in upright sections through the axis: " + "; ".join(row))
    cs = radial(rear, at, 0)
    ps = polys(cs)
    rp = (cb.T_OUT + RB) / 2
    rs = runs(ps, rp)
    print(f"      upright runs of solid at r={rp:.2f} (over the rim): " + ", ".join(f"{a:.2f}..{b:.2f} ({b - a:.2f}; square to 45 deg {0.7071 * (b - a):.2f})" for a, b in rs[:2]))
    # rim: radial width per layer, in sections through the axis
    for deg in (0, 30, 46):
        cs = radial(front, at, deg)
        ps = polys(cs)
        row = []
        for z in (0.001, 0.1, 0.2, 0.35, 0.5, 1.0, 1.5, 2.0, 2.2, 2.4, 2.6, 3.0, 3.5, 4.0, 4.4, 4.7):
            rr = runs([p[:, ::-1] for p in ps], z)
            rr = [q for q in rr if q[0] > cb.R_RIM - 0.6 and q[1] < RB + 0.1]
            row.append(f"{z:g}:" + ("/".join(f"{b - a:.2f}" for a, b in rr) if rr else "-"))
        print(f"      rim, section {deg} deg from straight back, radial width by height: " + "  ".join(row))
    # rim: where it joins the ball at each end (horizontal layers): narrowest place between the rim's middle and the ball's core
    row = []
    for z in (0.2, 1.0, 2.2, 3.0, 4.0):
        cs = front.slice(float(z)) ^ mf.CrossSection.square([16, 24]).translate([at - 4, -12])
        row.append(f"z={z:g}: {neck2(cs, (at + 9.0 if z < 3.5 else at + 9.9, 0.0), (at + 2.6, 0.0)):.2f}")
    print("      rim to ball, narrowest place on the way in each layer: " + "; ".join(row))
    # the rim's whole cross-section, and its narrowest place top to bottom (section through the axis, straight back)
    cs = radial(front, at, 0)
    rim_ = piece2(cs ^ mf.CrossSection.square([4, 6]).translate([cb.R_RIM - 1.0, -0.5]), 9.2, 1.0)
    print(f"      rim cross-section straight back: area {rim_.area():.2f} mm2, bounds r {rim_.bounds()[0]:.2f}..{rim_.bounds()[2]:.2f} z {rim_.bounds()[1]:.2f}..{rim_.bounds()[3]:.2f}; "
          f"narrowest place between its foot and its top {neck2(rim_, (9.1, 0.3), (9.6, 3.6)):.2f}")
    # pocket walls: the ball's skin beside / in front of the pocket, 3D below the rim's top
    clip = bx(at - 2.5, at + RB + 3, -12, 12, 0.001, 2.0)
    void = clip - front
    dot = mf.Manifold.sphere(0.02, 12).translate([at + 5.8, 0, 1.0])
    mine = [p for p in void.decompose() if (p ^ dot).volume() > 0]
    rest = [p for p in void.decompose() if (p ^ dot).volume() == 0]
    if mine and rest:
        gs = sorted((mine[0].min_gap(p, 8.0), p.bounding_box()) for p in rest)
        print("      pocket (below z=2) to the other empty spaces round the ball: " +
              "; ".join(f"{g:.3f} (space x {b[0]:.1f}..{b[3]:.1f} y {b[1]:.1f}..{b[4]:.1f})" for g, b in gs[:4]))
