"""Round 2. Thin places measured again on the revised solids, part C:
 E. leg pins (body) section by section; flange; the leg's lip, socket wall and outer skin
 F. keyring eye
 G. orange shaft and the head's wall round its bore
 H. gaps between bodies: 3D as printed, and sideways in slabs at the bed
Own sections and own 3D gaps; none of the design's check functions are used."""
import sys
import numpy as np
import manifold3d as mf
from lib import *

RJ = mf.JoinType.Round


def bx(x0, x1, y0, y1, z0, z1):
    return mf.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def has(cs, x, y, r=0.02):
    return (cs ^ mf.CrossSection.circle(r, 8).translate([x, y])).area() > 0


def piece2(cs, x, y):
    for p in cs.decompose():
        if has(p, x, y):
            return p
    return mf.CrossSection()


def disc(cs, hi=4.0):
    """Diameter of the largest disc that fits in cs."""
    lo = 0.0
    for _ in range(16):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if not cs.offset(-mid, RJ, 2.0, 64).is_empty() else (lo, mid)
    return 2 * lo


def ysec(m, y):
    """Section y = const as a CrossSection in (x, z)."""
    return m.rotate([90, 0, 0]).slice(float(y)).mirror([0, 1])


which = sys.argv[1] if len(sys.argv) > 1 else "full"
loop = not (len(sys.argv) > 2 and sys.argv[2] == "noloop")
parts, joints, info = (cb.make_capybara(loop=loop) if which == "full" else cb.make_test())
print(f"================ {which} model{'' if loop else ', no keyring eye'} ================")

print("E. LEGS")
FL = cb.FLANK
for name, (kind, s) in info["legs"].items():
    if s < 0 and which == "full" and kind == "front":
        pass
    g = cb.LEGS[kind]
    px, pz = g["x"], cb.LEG_Z
    body = parts["body 1" if kind == "front" else f"body {len(info['axes']) + 1}"]
    leg = parts[name]
    if s < 0:
        body, leg = body.mirror([0, 1, 0]), leg.mirror([0, 1, 0])
    lb = leg.bounding_box()
    pin_end = (body ^ bx(px - 5, px + 5, FL - 0.5, FL + 6, pz - 5, pz + 5)).bounding_box()[4]
    print(f" {name}: pin axis x={px} z={pz}; leg y {lb[1]:.3f}..{lb[4]:.3f}; pin reaches y={pin_end:.3f}; leg / body 3D gap {leg.min_gap(body, 3.0):.3f}")
    # the pin, section by section along its length
    rows, worst = [], {}
    ys = np.round(np.arange(FL - 1.2, pin_end - 0.004, 0.05), 3)
    for y in ys:
        cs = piece2(ysec(body, y) ^ mf.CrossSection.square([12, 12]).translate([px - 6, pz - 6]), px, pz + 0.9)
        if cs.is_empty():
            rows.append((y, None))
            continue
        b = cs.bounds()
        if b[2] - b[0] > 11.9:              # still inside the flank
            rows.append((y, "flank"))
            continue
        rows.append((y, (b[2] - b[0], b[3] - b[1], b[1], b[3], cs.area(), disc(cs))))
    print("    y: width (x) x height (z), z-range, area, largest disc")
    for y, r in rows:
        if r is None or r == "flank":
            continue
        print(f"      y={y:.2f} ({y - FL:+.2f} from the flank): {r[0]:.3f} x {r[1]:.3f}, z {r[2]:.2f}..{r[3]:.2f}, {r[4]:.2f} mm2, disc {r[5]:.3f}")
    real = [(y, r) for y, r in rows if r not in (None, "flank")]
    y_min, r_min = min(real, key=lambda t: t[1][5])
    print(f"    smallest section of the pin anywhere along it: largest disc {r_min[5]:.3f} mm ({r_min[0]:.3f} x {r_min[1]:.3f}, {r_min[4]:.2f} mm2) at y={y_min:.2f}")
    # where the leg's lip actually is (the bore through the leg), from the leg at the pin's height
    lz = sec_z(leg, pz)                      # polygons (x, y)
    row = []
    for dx in (1.6, 2.0, 2.06, 2.1, 2.2, 2.36, 2.5, 3.0, 3.4, 3.7):
        r_ = runs(lz, px + dx)
        row.append(f"x=pin+{dx}: " + (" ".join(f"[{a:.2f},{b:.2f}]={b - a:.2f}" for a, b in r_) if r_ else "-"))
    print("    leg at pin height, runs of solid along y: " + "; ".join(row))
    lzb = sec_z(body, pz + 1.8)
    row = []
    for dx in (0.0, 1.0, 1.7, 2.0, 2.5, 2.9):
        r_ = [q for q in runs(lzb, px + dx) if q[1] > FL - 1.01]
        row.append(f"x=pin+{dx}: " + (" ".join(f"[{a:.2f},{b:.2f}]={b - a:.2f}" for a, b in r_) if r_ else "-"))
    print("    body 1.8 above the pin's axis, runs of solid along y (pin, flange): " + "; ".join(row))
    # flange: its thickness along y wherever it stands clear of the neck, and its outline
    fl = None
    for y in np.arange(pin_end - 0.02, FL, -0.02):
        cs = ysec(body, y) ^ mf.CrossSection.square([12, 12]).translate([px - 6, pz - 6])
        if cs.is_empty():
            continue
        b = cs.bounds()
        if fl is None:
            fl = [y, y, b]
        if b[2] - b[0] > fl[2][2] - fl[2][0] - 0.3:
            fl[1] = y
        else:
            break
    print(f"    flange: full width from y={fl[1]:.2f} to y={fl[0]:.2f} (about {fl[0] - fl[1] + 0.02:.2f} thick), outline x {fl[2][0]:.2f}..{fl[2][2]:.2f} z {fl[2][1]:.2f}..{fl[2][3]:.2f} "
          f"(pin axis at z={pz}: {pz - fl[2][1]:.2f} below, {fl[2][3] - pz:.2f} above)")
    # 3D: the leg's socket space against everything else empty round the leg (face shaved 0.002), and its skin
    clip = bx(lb[0] - 1, lb[3] + 1, lb[1] + 0.002, lb[4] + 1, -1, lb[5] + 1)
    void = clip - leg
    dot = mf.Manifold.sphere(0.02, 12).translate([px, lb[1] + 1.3, pz])
    mine = [p for p in void.decompose() if (p ^ dot).volume() > 0]
    rest = [p for p in void.decompose() if (p ^ dot).volume() == 0]
    if mine and rest:
        cav = mine[0]
        cb_ = cav.bounding_box()
        outer = cb.union(rest)
        print(f"    socket space x {cb_[0]:.2f}..{cb_[3]:.2f} y {cb_[1]:.2f}..{cb_[4]:.2f} z {cb_[2]:.2f}..{cb_[5]:.2f}: nearest outside air {cav.min_gap(outer, 6.0):.3f} mm; "
              f"to the air beyond the leg's outer face only (skin) {cav.min_gap(bx(lb[0] - 1, lb[3] + 1, lb[4], lb[4] + 1, -1, 30), 6.0):.3f}")
        # skin by position: runs along y through the socket at several heights
        row = []
        for dz in (-3.0, -2.0, 0.0, 2.0, 3.0, 4.0, 4.5):
            lzz = sec_z(leg, pz + dz)
            best = 9
            for dx in np.arange(-3.4, 3.41, 0.1):
                r_ = runs(lzz, px + dx)
                if len(r_) >= 2:
                    best = min(best, r_[-1][1] - r_[-1][0])
            row.append(f"dz={dz:+.1f}: {best:.2f}" if best < 9 else f"dz={dz:+.1f}: -")
        print("    outer skin (last run of solid along y, over the socket) by height from the pin's axis: " + "; ".join(row))
        # the lip: the leg's wall between its inner face and the socket, away from the bore
        sec = ysec(leg, (lb[1] + cb_[1] + 0.3) / 2)
    # the membrane above the bore: sections x = const through the top of the bore
    row = []
    for dz in (1.9, 2.0, 2.06, 2.1, 2.2, 2.3, 2.4, 2.6, 2.8, 2.95):
        lzz = sec_z(leg, pz + dz)
        r_ = runs(lzz, px)
        row.append(f"+{dz}: " + (" ".join(f"[{a:.2f},{b:.2f}]" for a, b in r_) if r_ else "-"))
    print("    leg on the pin's centre line (x = pin), runs of solid along y by height above the axis: " + "; ".join(row))
    foot = leg.slice(0.001)
    print(f"    bed contact {foot.area():.2f} mm2; first 0.2 mm slab min width (largest disc) {disc(foot):.2f}")
    if which == "full" and s > 0 and kind == "hind":
        pass

if which == "full" and loop:
    print("\nF. KEYRING EYE (last body segment)")
    b4 = parts[f"body {len(info['axes']) + 1}"]
    KX, KZ, r = cb.KEYRING_X, cb.KEYRING_Z, cb.KEYRING_D / 2
    c = np.array([KX, KZ])
    print(f"   top of the segment {b4.bounding_box()[5]:.3f}")
    for y in (0.0, 0.5, 1.0, 1.5, 2.0, 2.2, 2.24, 2.3, 2.6, 3.0):
        ps = sec_y(b4, y + 0.001)
        hole = [p for p in ps if inside(p, c) and np.linalg.norm(p - c, axis=1).max() < 3.5]
        if not hole:
            # the web has ended: is there solid at all round the hole here
            row = [f"[{a:.2f},{b:.2f}]" for a, b in runs(ps, KX)]
            print(f"   section y={y:.2f}: no closed hole here; solid on the upright line through the hole's centre: {' '.join(row)}")
            continue
        h = hole[0]
        others = [p for p in ps if p is not h]
        d2, at_ = min((loop_gap(h, o) for o in others), key=lambda t: t[0])
        up = [q for q in runs(ps, KX) if q[0] > KZ]
        print(f"   section y={y:.2f}: hole x {h[:, 0].min():.2f}..{h[:, 0].max():.2f} z {h[:, 1].min():.2f}..{h[:, 1].max():.2f}; thinnest wall round it {d2:.3f} at x={at_[0]:.2f} z={at_[1]:.2f}; "
              f"over its peak {up[0][1] - up[0][0]:.3f} (top z={up[0][1]:.2f})")
    # web thickness across the body round the hole
    row = []
    for dx, dz in ((r + 0.4, 0.0), (-(r + 0.4), 0.0), (0.0, r * 1.4142 + 0.3), (0.0, r * 1.4142 + 1.0), (0.0, r * 1.4142 + 1.7), (r + 1.0, 1.0), (-(r + 1.0), 1.0), (0.0, -(r + 0.3))):
        lz = sec_z(b4, KZ + dz)
        r_ = [q for q in runs([p for p in lz], KX + dx) if q[0] < 0 < q[1]]
        row.append(f"({dx:+.1f},{dz:+.1f}): " + (f"{r_[0][1] - r_[0][0]:.2f}" if r_ else "-"))
    print("   web thickness across the body at (dx, dz) from the hole's centre: " + "; ".join(row))
    # 3D: the hole's space inside the web against every other empty space (socket of the last joint, scoops, outside)
    t = cb.KEYRING_T / 2
    for shave in (0.002, 0.3):
        clip = bx(KX - 8, KX + 6, -t + shave, t - shave, 8.0, KZ + 8)
        void = clip - b4
        dot = mf.Manifold.sphere(0.02, 12).translate([KX, 0, KZ])
        mine = [p for p in void.decompose() if (p ^ dot).volume() > 0]
        rest = [p for p in void.decompose() if (p ^ dot).volume() == 0]
        if mine and rest:
            gs = sorted((mine[0].min_gap(p, 8.0), p.bounding_box()) for p in rest)
            print(f"   3D (web shaved {shave} each side): hole space to other empty spaces: " +
                  "; ".join(f"{g_:.3f} (space x {b[0]:.1f}..{b[3]:.1f} z {b[2]:.1f}..{b[5]:.1f})" for g_, b in gs[:4]))
        else:
            print(f"   3D (web shaved {shave}): hole not closed ({len(mine)}, {len(rest)})")
    # the scoops: thin edges they leave
    found = []
    for z in np.arange(11.05, b4.bounding_box()[5], 0.1):
        cs = b4.slice(float(z))
        thin = cs - cs.offset(-0.4, RJ, 2.0, 64).offset(0.42, RJ, 2.0, 64)
        for p in thin.decompose():
            if p.area() > 0.08:
                found.append((p.area(), float(z), p.bounds()))
    found.sort(key=lambda f: -f[0])
    print(f"   layers 11..top: {len(found)} bits over 0.08 mm2 that a 0.8 mm disc cannot enter; largest: " +
          "; ".join(f"z={z:.2f} {a:.2f} mm2 x {b[0]:.2f}..{b[2]:.2f} y {b[1]:+.2f}..{b[3]:+.2f}" for a, z, b in found[:8]))

if which == "full":
    print("\nG. ORANGE")
    orange, head = parts["orange"], parts["head"]
    OX = cb.ORANGE_X
    seat, zc = info["seat"], info["orange_z"]
    row, best = [], (9, None)
    for z in np.arange(0.001, seat + 3.0, 0.05):
        cs = orange.slice(float(z))
        P = np.vstack(polys(cs))
        a, b = P, np.roll(P, -1, axis=0)
        d = disc(cs, 6.0)
        if d < best[0]:
            best = (d, z)
    print(f"   seat z={seat:.2f}, ball centre z={zc:.2f}, top {orange.bounding_box()[5]:.2f}; smallest section from the bed to 3 mm above the seat: largest disc {best[0]:.3f} at z={best[1]:.2f}")
    print("   largest disc by height: " + ", ".join(f"z={z:.2f}: {disc(orange.slice(float(z)), 6.0):.2f}" for z in (0.001, 0.2, 0.5, 1.0, 1.15, 1.3, 2.0, 4.0, 8.0, seat - 0.05, seat + 0.3, seat + 1.0)))
    print(f"   3D gap orange / head as printed {orange.min_gap(head, 3.0):.3f}")
    worst = (9, None)
    row = []
    for z in list(np.arange(0.001, head.bounding_box()[5], 0.1)):
        ps = sec_z(head, z)
        c2 = np.array([OX, 0.0])
        hole = [p for p in ps if inside(p, c2) and np.linalg.norm(p - c2, axis=1).max() < 6.5 and abs(area(p)) < 80]
        if not hole:
            continue
        h = hole[0]
        others = [p for p in ps if p is not h]
        d2, at_ = min((loop_gap(h, o) for o in others), key=lambda t: t[0])
        if d2 < worst[0]:
            worst = (d2, z, at_)
        if abs(z * 10 % 10 - 0.01) < 0.02 or z < 0.05:
            row.append(f"z={z:.1f}: {d2:.2f}")
    print(f"   head wall round the bore, per layer (bore outline to any other outline of the head): thinnest {worst[0]:.3f} at z={worst[1]:.2f} x={worst[2][0]:.2f} y={worst[2][1]:+.2f}")
    print("      " + "  ".join(row))
    # 3D: bore space against other empty spaces, below the seat
    clip = bx(OX - 9, OX + 9, -9, 9, 0.001, seat - 0.3)
    void = clip - head
    dot = mf.Manifold.sphere(0.02, 12).translate([OX, 0, 6.0])
    mine = [p for p in void.decompose() if (p ^ dot).volume() > 0]
    rest = [p for p in void.decompose() if (p ^ dot).volume() == 0]
    if mine and rest:
        gs = sorted((mine[0].min_gap(p, 8.0), p.bounding_box()) for p in rest)
        print("   3D: bore space (bed to 0.3 under the seat) to other empty spaces: " + "; ".join(f"{g_:.3f} (space x {b[0]:.1f}..{b[3]:.1f} y {b[1]:.1f}..{b[4]:.1f} z {b[2]:.1f}..{b[5]:.1f})" for g_, b in gs[:4]))
    # the rim of the seat cone in the top of the head: the head's wall between the seat cone and the head's own top surface
    row = []
    for deg in (0, 45, 90, 135, 180):
        t = head.translate([-OX, 0, 0]).rotate([0, 0, -deg])
        cs = t.rotate([90, 0, 0]).slice(0.0).mirror([0, 1]) ^ mf.CrossSection.square([12, 30]).translate([0.0, 0.0])
        # the edge where the seat cone meets the top: the highest point of the head's outline within 7 mm of the axis, nearest the axis
        P = np.vstack(polys(cs))
        near = P[(P[:, 0] < 6.9) & (P[:, 1] > seat - 0.5)]
        k = np.argmin(near[:, 0] - 0.0 * near[:, 1])
        row.append(f"{deg} deg: bore reaches r={near[:, 0].min():.2f}; head top there z={near[np.argmax(near[:, 1])][1]:.2f}")
    print("   seat cone in the top of the head, sections through the shaft's axis: " + "; ".join(row))

print("\nH. GAPS BETWEEN BODIES")
names = list(parts)
slab = lambda m, z0, z1: m ^ bx(-100, 200, -100, 100, z0, z1)
rows = []
for i, a in enumerate(names):
    for b in names[i + 1:]:
        A, B = parts[a], parts[b]
        ba, bb = A.bounding_box(), B.bounding_box()
        if any(ba[j] > bb[j + 3] + 2.5 or bb[j] > ba[j + 3] + 2.5 for j in range(3)):
            continue
        g3 = A.min_gap(B, 2.5)
        if g3 >= 2.5:
            continue
        sl = []
        for z0, z1 in ((0, 0.02), (0, 0.1), (0, 0.2), (0, 0.28), (0, 0.3), (0.2, 0.4)):
            sa, sb = slab(A, z0, z1), slab(B, z0, z1)
            sl.append(sa.min_gap(sb, 3.0) if not sa.is_empty() and not sb.is_empty() else 9.0)
        rows.append((g3, a, b, sl, (A ^ B).volume()))
rows.sort()
for g3, a, b, sl, ov in rows:
    print(f"   {a:<16} {b:<16} 3D {g3:.3f} | slab 0-0.02: {sl[0]:.3f}  0-0.1: {sl[1]:.3f}  0-0.2: {sl[2]:.3f}  0-0.28: {sl[3]:.3f}  0-0.3: {sl[4]:.3f}  0.2-0.4: {sl[5]:.3f} | overlap {ov:.1e}")
whole = cb.union(parts.values())
bb = whole.bounding_box()
print(f"   overall: x {bb[0]:.2f}..{bb[3]:.2f} ({bb[3] - bb[0]:.2f}), y {bb[1]:.2f}..{bb[4]:.2f} ({bb[4] - bb[1]:.2f}), z {bb[2]:.3f}..{bb[5]:.2f}; bodies {len(names)}, "
      f"each one piece: {all(len(p.decompose()) == 1 for p in parts.values())}")
