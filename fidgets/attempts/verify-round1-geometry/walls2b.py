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


cases = [("full", parts, f"body {i + 2}", at) for i, at in enumerate(cb.AXES)] + [("strip", tparts, "body 2", tinfo["axes"][0])]
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
        across = [b - a for a, b in runs([np.c_[q[:, 1], q[:, 0]] for q in polys(tg)], 0.0137)]   # along x at y = 0
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
        ps = sec_y(rot, 0.0137)
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
    ps = sec_y(rear, 0.0137)
    pk = cb.hook_peak()
    rs = runs(ps, at + pk[0] + 0.00137)
    print(f"        upright run through the bridge above the rim's peak (x=axis+{pk[0]:.2f}): " + ", ".join(f"{a:.2f}..{b:.2f}" for a, b in rs))
    # rim: section through the front segment at y = 0, and at 30 and 45 degrees off
    for a_deg in (0.0, 30.0, 44.0):
        rot = front.translate([-at, 0, 0]).rotate([0, 0, -a_deg]).translate([at, 0, 0])
        ps = sec_y(rot, 0.0137)
        rim = [p for p in ps if inside(p, (at + (cb.R_RIM + cb.R_BALL) / 2, 1.0))]
        if not rim:
            print(f"        rim at {a_deg:g} deg: none"); continue
        p = rim[0]
        sel = p[(p[:, 0] > at + 6.5)]
        cs = cs_from([p])
        widths = []
        for z in (0.0051, 0.1003, 0.3003, 1.0003, 2.0003, 2.5003, 3.0003, 3.4003):
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
