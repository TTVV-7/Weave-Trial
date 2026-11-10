"""Part 2: body joints - socket lip over the ball, horn at the flank per layer, hook tongue /
bridge / rim, wall between a socket and the next ball's hook pocket."""
import numpy as np
import manifold3d as mf
from lib import *

parts, joints, info = cb.make_capybara()
tparts, tjoints, tinfo = cb.make_test()
R = cb.R_BALL + cb.G_SEAM


def cs_from(ps):
    return mf.CrossSection([p.tolist() for p in ps], mf.FillRule.EvenOdd)


print("A. SOCKET LIP OVER THE BALL: every upright line inside the socket's radius, behind the axis; the run of solid that starts above the ball's equator")
cases = [("full", parts, f"body {i + 2}", at) for i, at in enumerate(cb.AXES)] + [("strip", tparts, "body 2", tinfo["axes"][0])]
for label, P, key, at in cases:
    seg = P[key]
    best = (9, None)
    hist = np.zeros(6, int)
    edge_rows = {}
    for y in np.arange(-8.45, 8.4501, 0.05):
        ps = sec_y(seg, y)
        if not ps:
            continue
        for x in np.arange(at + 6.0, at + R, 0.025):
            if (x - at) ** 2 + y ** 2 >= R ** 2:
                continue
            for lo, hi in runs(ps, x):
                if lo > cb.Z_C - 0.05:
                    t = hi - lo
                    hist[min(int(t / 0.2), 5)] += 1
                    if t < best[0]:
                        best = (t, (x, y, lo, hi))
    print(f"   {label} {key} (axis {at}): thinnest upright run of lip {best[0]:.3f} mm at x={best[1][0]:.2f} (axis+{best[1][0]-at:.2f}) y={best[1][1]:+.2f}, z {best[1][2]:.2f}..{best[1][3]:.2f}; "
          f"columns by thickness <0.2,<0.4,<0.6,<0.8,<1.0,>=1.0: {hist.tolist()}")

print("\n   the lip in plan: narrowest piece of each layer above the equator, inside the socket radius (anything a 0.8 mm disc cannot enter)")
for label, P, key, at in cases:
    seg = P[key]
    top = seg.bounding_box()[5]
    zone = mf.CrossSection.circle(R, 256).translate([at, 0])
    rows = []
    for z in np.arange(cb.Z_C + 0.05, top, 0.1):
        cs = seg.slice(float(z))
        if cs.is_empty():
            continue
        opened = cs.offset(-0.4, mf.JoinType.Round, 2.0, 64).offset(0.4, mf.JoinType.Round, 2.0, 64)
        thin = (cs - opened.offset(0.01, mf.JoinType.Round)) ^ zone
        for q in thin.decompose():
            if q.area() > 0.05:
                b = q.bounds()
                rows.append((float(z), q.area(), b))
    rows.sort(key=lambda r: -r[1])
    print(f"   {label} {key}: {len(rows)} thin bits > 0.05 mm2 in the lip zone" + ("" if not rows else "; largest: " + "; ".join(
        f"z={z:.2f} {a:.2f} mm2 x {b[0]:.2f}..{b[2]:.2f} y {b[1]:+.2f}..{b[3]:+.2f}" for z, a, b in rows[:5])))

print("\nB. HORN OF THE SOCKET BESIDE THE BALL, per layer: width in y at the blunt front face, 0.02 / 0.1 / 0.3 mm behind it, and the face's x")
for label, P, key, at in cases:
    seg = P[key]
    worst = (9, None)
    line = []
    for z in (0.005, 0.02, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.7, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 7.0, 7.9, 8.0, 8.5, 9.0):
        ps = sec_z(seg, z)
        # the horn on the +y side: front-most x of the section at y > 4
        pts = np.vstack(ps)
        sel = pts[(pts[:, 1] > 4.0) & (pts[:, 0] < at + 10.5)]
        xf = sel[:, 0].min()
        ws = []
        for dx in (0.02, 0.1, 0.3):
            rs = [r for r in runs([p[:, ::1] for p in ps], xf + dx) if r[0] > 3.0]
            ws.append(min((b - a for a, b in rs), default=0.0))
        if ws[0] < worst[0]:
            worst = (ws[0], z)
        line.append(f"z={z:g}: {ws[0]:.2f}/{ws[1]:.2f}/{ws[2]:.2f} (face at axis+{xf - at:.2f})")
    print(f"   {label} {key}: narrowest at the face {worst[0]:.3f} mm at z={worst[1]}")
    if key == "body 2" and label == "full":
        for i in range(0, len(line), 4):
            print("      " + "   ".join(line[i:i + 4]))

print("\nC. HOOK: tongue on the bed, bridge over the rim (rear segment), and the rim (front segment)")
for label, P, i, at in [("full", parts, i, at) for i, at in enumerate(cb.AXES)] + [("strip", tparts, 0, tinfo["axes"][0])]:
    front, rear = P[f"body {i + 1}"], P[f"body {i + 2}"]
    out = []
    for z in (0.005, 0.1, 0.31, 1.0, 2.0, 2.6):
        cs = rear.slice(float(z))
        pcs = [q for q in cs.decompose() if q.area() > 1e-4]
        dot = mf.CrossSection.circle(0.05, 16).translate([at + (cb.T_IN + cb.T_OUT) / 2, 0])
        tg = [q for q in pcs if (q ^ dot).area() > 0]
        if not tg:
            out.append(f"z={z}: no tongue piece"); continue
        tg = tg[0]
        p = np.vstack(polys(tg))
        rr = np.hypot(p[:, 0] - at, p[:, 1])
        ang = np.degrees(np.arctan2(p[:, 1], p[:, 0] - at))
        across = [b - a for a, b in runs([np.c_[q[:, 1], q[:, 0]] for q in polys(tg)], 0.0)]   # along x at y = 0
        # width at the inner corners: chord between the two inner corners
        inner = p[rr < rr.min() + 0.05]
        chord = np.ptp(inner[:, 1])
        # largest disc that fits: bisection on erosion
        lo_, hi_ = 0.0, 3.0
        for _ in range(24):
            m_ = (lo_ + hi_) / 2
            if tg.offset(-m_, mf.JoinType.Round, 2.0, 64).area() > 1e-6:
                lo_ = m_
            else:
                hi_ = m_
        out.append(f"z={z}: {'separate island' if len(pcs) > 1 else 'joined to the body'}, area {tg.area():.2f} mm2, r {rr.min():.2f}..{rr.max():.2f}, "
                   f"across at y=0 {across[0]:.3f}, chord at the inner corners {chord:.3f}, half angle {ang.max():.1f}, largest disc that fits {2 * lo_:.3f}")
    print(f"   {label} joint {i + 1} tongue: " + "\n        ".join(out))
    # bridge: section y = 0 of the rear segment (and at +-12 degrees), bottleneck between the tongue and the body by erosion
    for a_deg in (0.0, 12.0, 17.0):
        rot = rear.translate([-at, 0, 0]).rotate([0, 0, -a_deg]).translate([at, 0, 0])
        ps = sec_y(rot, 0.0)
        cs = cs_from(ps)
        tp = mf.CrossSection.circle(0.02, 8).translate([at + (cb.T_IN + cb.T_OUT) / 2, 1.2])
        bp = mf.CrossSection.circle(0.02, 8).translate([at + cb.R_BALL + 3.0, 5.0])
        lo_, hi_ = 0.0, 1.7
        for _ in range(22):
            m_ = (lo_ + hi_) / 2
            er = cs.offset(-m_, mf.JoinType.Round, 2.0, 64)
            okk = any((q ^ tp).area() > 0 and (q ^ bp).area() > 0 for q in er.decompose())
            lo_, hi_ = (m_, hi_) if okk else (lo_, m_)
        print(f"        section {a_deg:g} deg off the middle: narrowest neck between tongue and body {2 * lo_:.3f} mm (largest disc that can be rolled through)")
    # the hook's footprint against the three numbers: vertical column through the bridge peak
    ps = sec_y(rear, 0.0)
    pk = cb.hook_peak()
    rs = runs(ps, at + pk[0])
    print(f"        upright run through the bridge above the rim's peak (x=axis+{pk[0]:.2f}): " + ", ".join(f"{a:.2f}..{b:.2f}" for a, b in rs))
    # rim: section through the front segment at y = 0, and at 30 and 45 degrees off
    for a_deg in (0.0, 30.0, 44.0):
        rot = front.translate([-at, 0, 0]).rotate([0, 0, -a_deg]).translate([at, 0, 0])
        ps = sec_y(rot, 0.0)
        rim = [p for p in ps if inside(p, (at + (cb.R_RIM + cb.R_BALL) / 2, 1.0))]
        if not rim:
            print(f"        rim at {a_deg:g} deg: none"); continue
        p = rim[0]
        sel = p[(p[:, 0] > at + 6.5)]
        cs = cs_from([p])
        widths = []
        for z in (0.005, 0.1, 0.3, 1.0, 2.0, 2.5, 3.0, 3.4):
            rs = [r for r in runs([np.c_[p[:, 1], p[:, 0]]], z) if r[0] > at + 7.0]
            widths.append(f"z={z:g}: {rs[0][1] - rs[0][0]:.2f}" if rs else f"z={z:g}: -")
        print(f"        rim at {a_deg:g} deg: radial thickness " + ", ".join(widths) + f"; top z {sel[:, 1].max():.2f}; section is {'its own loop (a bar)' if p[:, 0].min() > at + 6.5 else 'part of the ball here'}")

print("\nD. WALL BETWEEN A SOCKET AND THE NEXT BALL'S HOOK POCKET (bodies 2 and 3), and the pocket's other walls, per layer")
for key in ("body 1", "body 2", "body 3"):
    seg = parts[key]
    i = int(key[-1]) - 1
    at = cb.AXES[i]
    worst = (9, None)
    for z in (0.002, 0.02, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0, 2.0, 2.5, 3.0, 3.3):
        ps = sec_z(seg, z)
        outer = max(ps, key=lambda p: abs(area(p)))
        pk = [p for p in ps if p is not outer and inside(p, (at + 5.5, 0.0)) is False and np.hypot(p[:, 0] - at, p[:, 1]).max() < 8.2]
        # the pocket is a hole in the section (closed by the rim) below the rim's top; take every other loop
        holes = [p for p in ps if p is not outer]
        if not holes:
            print(f"   {key} z={z}: pocket is not a closed hole in this layer"); continue
        d, atp = min((loop_gap(h, outer) for h in holes), key=lambda t: t[0])
        if d < worst[0]:
            worst = (d, (z, atp))
        print(f"   {key} z={z:5.3f}: {len(holes)} hole(s); thinnest wall between the pocket and the body's outside {d:.3f} at x={atp[0]:.2f} (axis+{atp[0]-at:.2f}) y={atp[1]:+.2f}")
    print(f"   {key}: thinnest {worst[0]:.3f} at z={worst[1][0]}")
