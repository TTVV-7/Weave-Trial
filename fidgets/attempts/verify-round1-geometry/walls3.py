"""Part 3: hook bridge neck (fixed probe points), leg pin and leg skin, keyring lug, orange shaft,
head wall round the bore, first-layer and 3D gaps between bodies."""
import numpy as np
import manifold3d as mf
from lib import *

parts, joints, info = cb.make_capybara()
tparts, tjoints, tinfo = cb.make_test()
RJ = mf.JoinType.Round


def cs_from(ps):
    return mf.CrossSection([p.tolist() for p in ps], mf.FillRule.EvenOdd)


def neck(cs, a, b, hi=2.0):
    """Diameter of the largest disc that can be rolled from point a to point b inside cs."""
    da = mf.CrossSection.circle(0.02, 8).translate(list(a))
    db = mf.CrossSection.circle(0.02, 8).translate(list(b))
    lo = 0.0
    for _ in range(22):
        m_ = (lo + hi) / 2
        er = cs.offset(-m_, RJ, 2.0, 64)
        ok = any((q ^ da).area() > 0 and (q ^ db).area() > 0 for q in er.decompose())
        lo, hi = (m_, hi) if ok else (lo, m_)
    return 2 * lo


print("C2. HOOK BRIDGE: largest disc that can be rolled from the middle of the tongue into the body, in upright sections through the axis")
for label, P, i, at in [("full", parts, i, at) for i, at in enumerate(cb.AXES)] + [("strip", tparts, 0, tinfo["axes"][0])]:
    rear = P[f"body {i + 2}"]
    row = []
    for a_deg in (0.0, 8.0, 14.0, 17.5):
        rot = rear.translate([-at, 0, 0]).rotate([0, 0, -a_deg]).translate([at, 0, 0])
        cs = cs_from(sec_y(rot, 0.0137))
        tp = (at + (cb.T_IN + cb.T_OUT) / 2, 1.725)
        best = 0
        for bp in ((at + 12.5, 11.0), (at + 12.2, 6.0), (at + 13.0, 8.5)):
            best = max(best, neck(cs, tp, bp))
        row.append(f"{a_deg:g} deg: {best:.3f}")
    print(f"   {label} joint {i + 1}: " + ", ".join(row))

print("\nE. LEG PINS (body) and LEG SOCKET WALLS / SKIN (leg)")
for label, P, name, body_key in (("full front", parts, "front left leg", "body 1"), ("full hind", parts, "hind left leg", "body 4"),
                                 ("full hind right", parts, "hind right leg", "body 4"), ("strip front", tparts, "front left leg", "body 1")):
    kind = "front" if "front" in name else "hind"
    s = 1 if "left" in name else -1
    g = cb.LEGS[kind]
    x0, z0 = g["x"], cb.LEG_Z
    body, leg = P[body_key], P[name]
    # pin: sections y = const
    row = []
    for dy in (-0.3, -0.02, 0.02, 0.2, 0.4, 0.8, 1.2, 1.58):
        ps = sec_y(body, s * (cb.FLANK + dy))
        pin = [p for p in ps if inside(p, (x0, z0 + 0.6))]
        if not pin:
            row.append(f"{dy:+.2f}: none"); continue
        p = pin[0]
        if dy < 0:
            row.append(f"{dy:+.2f}: inside the body (section {np.ptp(p[:, 0]):.1f} x {np.ptp(p[:, 1]):.1f})"); continue
        cs = cs_from([p])
        lo, hi = 0.0, 4.0
        for _ in range(24):
            m_ = (lo + hi) / 2
            lo, hi = (m_, hi) if cs.offset(-m_, RJ, 2.0, 64).area() > 1e-7 else (lo, m_)
        row.append(f"{dy:+.2f}: {np.ptp(p[:, 0]):.3f} wide x {np.ptp(p[:, 1]):.3f} tall, z {p[:, 1].min():.2f}..{p[:, 1].max():.2f}, largest disc {2 * lo:.3f}, area {abs(area(p)):.2f}")
    print(f"   {label} pin, sections at flank+dy: " + "; ".join(row))
    # the leg: sections through the pin axis at many angles; wall round the socket (radial) and skin beyond its end
    rad, skin, lipw = (9, None), (9, None), (9, None)
    for phi in np.arange(0, 180, 5.0):
        rot = leg.translate([-x0, 0, -z0]).rotate([0, phi, 0])
        ps = sec_x(rot, 0.0013)                       # (y, rho)
        if s < 0:
            ps = [np.c_[-p[:, 0], p[:, 1]] for p in ps]
        yin = cb.FLANK + cb.LEG_GAP
        # skin: runs along y at each rho inside the socket's end radius
        for rho in np.arange(-3.7, 3.71, 0.1):
            rs = runs([np.c_[p[:, 1], p[:, 0]] for p in ps], rho + 0.0007)
            if len(rs) and rs[-1][0] > yin + 0.5:
                t = rs[-1][1] - rs[-1][0]
                if t < skin[0]:
                    skin = (t, (phi, rho, rs[-1]))
        # radial wall: runs along rho at each y within the socket's depth
        for y in np.arange(yin + 0.02, yin + 1.6, 0.05):
            rs = runs(ps, y)
            for a, b in rs:
                if (a > 0.5 or b < -0.5):
                    if b - a < rad[0]:
                        rad = (b - a, (phi, y, a, b))
    print(f"   {label} leg: thinnest wall round the pin's socket, measured along a radius {rad[0]:.3f} (section turned {rad[1][0]:g} deg about the pin, y={rad[1][1]:.2f}, rho {rad[1][2]:.2f}..{rad[1][3]:.2f}); "
          f"thinnest skin beyond the socket's end {skin[0]:.3f} (turned {skin[1][0]:g} deg, rho={skin[1][1]:+.1f}, y {skin[1][2][0]:.2f}..{skin[1][2][1]:.2f})")
    # exact 3D: the socket's empty space against everything else that is empty
    bb = leg.bounding_box()
    clip = cb.box(bb[0] - 1, bb[3] + 1, (bb[1] if s > 0 else bb[1] - 1) + (0.03 if s > 0 else 0), (bb[4] + 1 if s > 0 else bb[4] - 0.03), -1, bb[5] + 1)
    air = (clip - leg).decompose()
    dot = cb.ball(0.02, x0, s * (cb.FLANK + cb.LEG_GAP + 0.5), z0)
    mine = [p for p in air if (p ^ dot).volume() > 0]
    others = [p for p in air if (p ^ dot).volume() == 0]
    if mine and others:
        print(f"        3D: socket space to all other empty space (leg's own face shaved 0.03): {mine[0].min_gap(cb.union(others), 6.0):.3f} mm; pieces of empty space {len(air)}")
    # how the leg is kept on: overlap of the pin's head over the socket's mouth
    print(f"        gap pin-to-leg as printed {body.min_gap(leg, 3.0):.3f}")

print("\nF. KEYRING LUG (body 4)")
b4 = parts["body 4"]
KX, KZ, KR = cb.KEYRING_X, cb.KEYRING_Z, cb.KEYRING_D / 2
for y in (0.0137, 1.0, 2.0, 2.2, 2.5, 3.0, 3.5):
    ps = sec_y(b4, y)
    outer = max(ps, key=lambda p: abs(area(p)))
    hole = [p for p in ps if p is not outer and inside(p, (KX, KZ))]
    if hole:
        d, atp = loop_gap(hole[0], outer)
        rs = runs(ps, KX + 0.0007)
        over = [b - a for a, b in rs if a > KZ]
        print(f"   section y={y:.2f}: hole is closed; thinnest wall round it {d:.3f} at x={atp[0]:.2f} z={atp[1]:.2f}; over the hole's peak {over[0] if over else float('nan'):.3f}; top of lug {outer[:, 1][np.abs(outer[:, 0] - KX) < 3].max():.2f}")
    else:
        top = outer[np.abs(outer[:, 0] - KX) < 2.5][:, 1].max()
        print(f"   section y={y:.2f}: hole is open here (a groove in the back); surface height near the lug {top:.2f}")
for z in (KZ - 1.0, KZ, KZ + 1.0, KZ + KR, KZ + KR * np.sqrt(2) + 0.1, KZ + KR * np.sqrt(2) + 0.5, KZ + KR * np.sqrt(2) + 1.0, KZ + KR * np.sqrt(2) + 1.5, 19.0):
    ps = sec_z(b4, z)
    lug = [p for p in ps if p[:, 0].min() > KX - 6 and np.abs(p[:, 1]).max() < 6.5 and inside(p, (KX + KR + 0.8, 0.0)) or inside(p, (KX, 0.01))]
    txt = []
    for p in ps:
        if abs(area(p)) > 0.01 and p[:, 0].max() > KX - 3 and (inside(p, (KX + KR + 0.9, 0.0137)) or inside(p, (KX - KR - 0.9, 0.0137)) or inside(p, (KX, 0.0137))):
            txt.append(f"piece x {p[:, 0].min():.2f}..{p[:, 0].max():.2f} ({np.ptp(p[:, 0]):.2f}) y {p[:, 1].min():+.2f}..{p[:, 1].max():+.2f} ({np.ptp(p[:, 1]):.2f}) area {abs(area(p)):.2f}")
    print(f"   layer z={z:.2f}: " + ("; ".join(txt) if txt else "nothing of the lug"))
air = (cb.box(KX - 7, KX + 7, -2.2, 2.2, KZ - 4, KZ + 8) - b4).decompose()
dot = cb.ball(0.02, KX, 0, KZ)
mine = [p for p in air if (p ^ dot).volume() > 0]
others = [p for p in air if (p ^ dot).volume() == 0]
print(f"   3D, within |y| < 2.2: hole space to all other empty space {mine[0].min_gap(cb.union(others), 6.0):.3f} mm" if mine and others else "   3D: hole is not closed inside |y| < 2.2")

print("\nG. ORANGE: the shaft from the bed up into the ball; head wall round its bore")
org, head = parts["orange"], parts["head"]
OX = cb.ORANGE_X
zs = np.r_[np.arange(0.005, 4.0, 0.25), np.arange(4.0, info["seat"] + 3.0, 0.2)]
best = (9, None)
row = []
for z in zs:
    ps = sec_z(org, z)
    p = max(ps, key=lambda q: abs(area(q)))
    r = np.hypot(p[:, 0] - OX, p[:, 1])
    flats = 2 * r.max() * np.cos(np.pi / len(p))
    if flats < best[0]:
        best = (flats, z)
    row.append((z, 2 * r.min(), 2 * r.max(), len(ps)))
print(f"   seat (shaft meets the cone) z={info['seat']:.2f}, ball centre z={info['orange_z']:.2f}; smallest diameter across flats anywhere from the bed to 3 mm above the seat: {best[0]:.3f} at z={best[1]:.2f}")
print("   diameter by height: " + ", ".join(f"z={z:.2f}: {b:.2f}" for z, a, b, n in row[::4]))
worst = (9, None)
for z in np.r_[np.arange(0.005, 3.6, 0.1), np.arange(3.6, 13.6, 0.25)]:
    ps = sec_z(head, z)
    bore = [p for p in ps if inside(p, (OX, 0.0137)) and abs(area(p)) < 80 and np.hypot(p[:, 0] - OX, p[:, 1]).max() < 6]
    if not bore:
        continue
    for o in ps:
        if o is bore[0]:
            continue
        d, atp = loop_gap(bore[0], o)
        if d < worst[0]:
            worst = (d, (z, atp))
print(f"   head: thinnest wall between the bore and any other surface of the head, per layer: {worst[0]:.3f} at z={worst[1][0]:.2f}, x={worst[1][1][0]:.2f} y={worst[1][1][1]:+.2f}")
print(f"   3D gap orange-to-head as printed: {org.min_gap(head, 3.0):.3f}")

print("\nH. GAPS BETWEEN BODIES: 3D as printed, and sideways in thin slabs near the bed")
for label, P in (("full", parts), ("strip", tparts)):
    names = list(P)
    rows = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            g = P[a].min_gap(P[b], 2.5)
            if g < 2.5:
                row = [g]
                for z0, z1 in ((0, 0.02), (0, 0.1), (0, 0.2), (0.2, 0.4)):
                    sa = P[a] ^ cb.box(-100, 200, -100, 100, z0, z1)
                    sb = P[b] ^ cb.box(-100, 200, -100, 100, z0, z1)
                    row.append(sa.min_gap(sb, 3.0) if not sa.is_empty() and not sb.is_empty() else float('nan'))
                # first slice outlines
                ga = []
                for z in (0.001, 0.1, 0.2):
                    A, B = P[a].slice(z), P[b].slice(z)
                    if A.is_empty() or B.is_empty():
                        ga.append(float('nan')); continue
                    dd = min(loop_gap(pa, pb)[0] for pa in polys(A) for pb in polys(B))
                    ga.append(dd)
                rows.append((a, b, row, ga, (P[a] ^ P[b]).volume()))
    for a, b, row, ga, ov in sorted(rows, key=lambda r: r[2][0]):
        print(f"   {label}: {a:<16} {b:<16} 3D {row[0]:.3f} | slab 0-0.02: {row[1]:.3f}  0-0.1: {row[2]:.3f}  0-0.2: {row[3]:.3f}  0.2-0.4: {row[4]:.3f} | outline gap at z=0.001: {ga[0]:.3f}  z=0.1: {ga[1]:.3f}  z=0.2: {ga[2]:.3f} | overlap {ov:.1e}")
