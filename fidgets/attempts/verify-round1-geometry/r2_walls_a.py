"""Round 2. Thin places measured again on the revised solids, part A: head / neck.
 1. neck tab wall round each nod socket
 2. roof over the neck slot along its whole length
 3. nod pins
Own sections and own 3D gaps; none of the design's check functions are used."""
import numpy as np
import manifold3d as mf
from lib import *

RJ = mf.JoinType.Round


def cyl_y(x, z, r, y0, y1, n=256):
    return mf.Manifold.cylinder(y1 - y0, r, r, n).rotate([-90, 0, 0]).translate([x, y0, z])


def bx(x0, x1, y0, y1, z0, z1):
    return mf.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def piece_with(m, pt, r=0.02):
    dot = mf.Manifold.sphere(r, 12).translate(list(pt))
    for p in m.decompose():
        if (p ^ dot).volume() > 0:
            return p
    return None


NX, NZ = cb.NECK_X, cb.NECK_Z
c = np.array([NX, NZ])
for label, maker in (("full model", cb.make_capybara), ("test strip", cb.make_test)):
    parts, joints, info = maker()
    head, b1 = parts["head"], parts["body 1"]
    print(f"================ {label} ================")
    # ---------------------------------------------------------------- 1
    w = None
    # the tab's true faces: the head's extent in y in a thin probe on the nod axis
    probe = head ^ bx(NX - 0.3, NX + 0.3, -6, 6, NZ + 2.6, NZ + 3.0)
    pb = probe.bounding_box()
    w = (pb[4] - pb[1]) / 2
    print(f"1. NECK TAB: its faces are at y = {pb[1]:+.3f} and {pb[4]:+.3f} (measured just above the sockets)")
    worst = (9, None)
    for side in (1, -1):
        row = []
        for d in (0.002, 0.01, 0.03, 0.05, 0.1, 0.2, 0.3, 0.5, 0.8, 1.0):
            y = side * (w - d)
            ps = sec_y(head, y)
            hole = [p for p in ps if np.linalg.norm(p - c, axis=1).max() < 3.29 and inside(p, c)]
            if not hole:
                row.append(f"{d:.3f}: no socket")
                continue
            h = hole[0]
            others = [p for p in ps if p is not h]
            d2, at = min((loop_gap(h, o) for o in others), key=lambda t: t[0])
            rr = np.linalg.norm(h - c, axis=1)
            row.append(f"{d:.3f} in: socket r {rr.max():.3f}, wall {d2:.3f} (x={at[0]:.2f} z={at[1]:.2f})")
            if d2 < worst[0]:
                worst = (d2, y, at)
        print(f"   side {side:+d}: " + "; ".join(row))
    print(f"   thinnest tab wall round a socket, any depth, either side: {worst[0]:.3f} mm at y={worst[1]:+.3f} x={worst[2][0]:.2f} z={worst[2][1]:.2f}")
    # 3D: socket space (between the tab faces, shaved 0.002) to every other empty space
    for side in (1, -1):
        y0, y1 = (0.0, w - 0.002) if side > 0 else (-w + 0.002, 0.0)
        clip = bx(NX - 5.5, NX + 5.5, y0, y1, 0.001, NZ + 9)
        void = clip - head
        mine = piece_with(void, (NX, side * (w - 0.3), NZ))
        rest = [p for p in void.decompose() if (p ^ mf.Manifold.sphere(0.02, 12).translate([NX, side * (w - 0.3), NZ])).volume() == 0]
        if mine is None or not rest:
            print(f"   side {side:+d} 3D: could not separate the socket space")
            continue
        print(f"   side {side:+d} 3D: socket space {mine.volume():.3f} mm3; nearest other empty space {mine.min_gap(cb.union(rest), 6.0):.3f} mm ({len(rest)} other spaces)")
    # the web between the two socket tips, along the axis
    ps_x = sec_x(head, NX)
    print("   solid along the nod axis itself (between the two socket tips), y runs:",
          [(round(float(a), 3), round(float(b), 3)) for a, b in runs([p[:, ::-1] for p in ps_x], NZ)])
    # the tab below the sockets: its foot on the bed, per layer (width in y and in x at the axis)
    row = []
    for z in (0.001, 0.1, 0.2, 0.4, 1.0, 2.0, 3.0, 4.0, NZ - 3.35, NZ - 2.5):
        ps = sec_z(head, z)
        ry = runs(ps, NX)
        mid = [r for r in ry if r[0] < 0 < r[1]]
        row.append(f"z={z:.2f}: " + (f"{mid[0][1] - mid[0][0]:.2f} wide" if mid else "none"))
    print("   tab foot / disc at the axis, width in y per layer: " + "; ".join(row))

    # ---------------------------------------------------------------- 2
    print("2. ROOF OVER THE NECK SLOT (body 1)")
    hw = cb.TAB_W / 2 + cb.TAB_GAP
    # (a) upright runs: every column over the slot, the run of solid above the slot's empty space
    best = (9, None)
    perx = {}
    ys = np.arange(-hw - 0.5, hw + 0.5001, 0.05)
    xs = np.arange(14.0, 30.0, 0.05)
    secs = {round(float(y), 3): sec_y(b1, y) for y in ys}
    for y, ps in secs.items():
        for x in xs:
            rs = runs(ps, x)
            if len(rs) < 1:
                continue
            lo, hi = rs[-1]
            if lo < 0.3:            # solid from the bed up: no slot under this column
                continue
            t = hi - lo
            k = round(float(x), 2)
            if k not in perx or t < perx[k][0]:
                perx[k] = (t, y, lo, hi)
    # skip the first 0.3 mm behind the roof's front edge (a corner where two faces meet has no thickness)
    front = min(perx)
    for k, v in sorted(perx.items()):
        if k >= front + 0.3 and v[0] < best[0]:
            best = (v[0], k, v)
    print(f"   upright run of roof: roofed columns from x={front:.2f} to x={max(perx):.2f}; thinnest from 0.3 behind the front edge on: "
          f"{best[0]:.3f} mm at x={best[1]:.2f} y={best[2][1]:+.2f} (z {best[2][2]:.2f}..{best[2][3]:.2f})")
    print("      by x: " + "  ".join(f"{k:.1f}:{perx[k][0]:.2f}" for k in sorted(perx) if abs(k * 2 - round(k * 2)) < 1e-6))
    # (b) exact 3D: the slot's empty space, cut off at the drum's own surface in front, against the open air above the back
    R = cb.R_NOD - 0.05      # 0.05 inside the drum face, so the faceted face itself closes nothing
    drum = cyl_y(NX, NZ, R, -30, 30) + bx(NX, 60, -30, 30, -5, 60)
    region = bx(13.5, 31.0, -6.0, 6.0, 0.001, 30) ^ drum
    void = region - b1
    pieces = void.decompose()
    slot = piece_with(void, (NX, 0, NZ + cb.TAB_RU + 0.6))
    air = piece_with(void, (NX + 1, 0, 15.2))
    if slot is None or air is None or (slot ^ air).volume() > 0:
        print("   3D: could not separate slot from air", slot is None, air is None, len(pieces))
    else:
        sb = slot.bounding_box()
        print(f"   3D: slot space x {sb[0]:.2f}..{sb[3]:.2f} y {sb[1]:.2f}..{sb[4]:.2f} z ..{sb[5]:.2f}; open air above the back: nearest {slot.min_gap(air, 8.0):.3f} mm "
              f"(empty spaces in the region: {len(pieces)})")
        # the same along the length: the slot cut into 1 mm lengths
        row = []
        for x0 in np.arange(np.floor(sb[0]), sb[3], 1.0):
            s = slot ^ bx(x0, x0 + 1.0, -10, 10, -1, 40)
            if s.is_empty():
                continue
            row.append(f"{x0:.0f}-{x0 + 1:.0f}: {s.min_gap(air, 12.0):.2f}")
        print("      nearest open air by 1 mm lengths of the slot: " + "  ".join(row))
        others = [p for p in pieces if (p ^ slot).volume() == 0 and (p ^ air).volume() == 0 and p.volume() > 1e-4]
        for p in others:
            ob = p.bounding_box()
            print(f"      another empty space x {ob[0]:.2f}..{ob[3]:.2f} y {ob[1]:.2f}..{ob[4]:.2f} z {ob[2]:.2f}..{ob[5]:.2f} vol {p.volume():.3f}: gap to the slot {slot.min_gap(p, 8.0):.3f}")
    # (c) sections x = const: the slot's outline against the back's outline, square to the faces
    row = []
    for x in np.arange(15.0, 29.01, 0.5):
        cs = b1.rotate([0, -90, 0]).slice(float(x))            # (x, y, z) -> (-z, y, x): section coords (-z, y)
        if cs.is_empty():
            continue
        zt = -cs.bounds()[0]
        rect = mf.CrossSection.square([zt + 1.0 - 0.001, 12.0]).translate([-(zt + 1.0), -6.0])
        v = rect - cs
        mine = air_ = None
        for p in v.decompose():
            b = p.bounds()
            if b[0] < -(zt + 0.5):
                air_ = p if air_ is None else air_ + p
            elif b[1] < 0 < b[3] and (-b[2] < 0.01 or True) and mine is None and abs(b[1] + b[3]) < 0.2:
                mine = p
        if mine is None or air_ is None:
            row.append(f"{x:.1f}: -")
            continue
        g = 9.0
        for pa in polys(mine):
            for pb_ in polys(air_):
                g = min(g, loop_gap(pa, pb_)[0])
        row.append(f"{x:.1f}: {g:.2f}")
    print("   sections x = const, slot outline to the outline of the air above (square to the faces): " + "  ".join(row))

    # ---------------------------------------------------------------- 3
    print("3. NOD PINS (body 1): sections y = const from the prong wall to the pin's tip")
    for side in (1, -1):
        row = []
        for y in (hw + 0.3, hw + 0.01, hw - 0.01, hw - 0.3, hw - 0.6, hw - cb.NOD_DEPTH + 0.05, hw - cb.NOD_DEPTH + 0.01, hw - cb.NOD_DEPTH + 0.001):
            ps = sec_y(b1, side * y)
            pin = [p for p in ps if inside(p, c)]
            if not pin:
                row.append(f"y={y:.3f}: none")
                continue
            p = pin[0]
            rr = np.linalg.norm(p - c, axis=1)
            if rr.max() > 5:
                row.append(f"y={y:.3f}: in the wall")
                continue
            # across flats = twice the smallest distance from the axis to an edge
            a, b = p, np.roll(p, -1, axis=0)
            ab = b - a
            t = np.clip(((c - a) * ab).sum(1) / (ab ** 2).sum(1), 0, 1)
            flat = 2 * np.linalg.norm(a + t[:, None] * ab - c, axis=1).min()
            row.append(f"y={y:.3f}: {2 * rr.max():.3f} across corners, {flat:.3f} across flats")
        print(f"   side {side:+d}: " + "; ".join(row))
    tip = b1 ^ bx(NX - 4, NX + 4, -hw + 0.0005, hw - 0.0005, NZ - 4, NZ + 4)
    for p in tip.decompose():
        b = p.bounding_box()
        print(f"   pin standing proud of the slot's wall: y {b[1]:+.3f}..{b[4]:+.3f} (length {b[4] - b[1]:.3f}), x-extent {b[3] - b[0]:.3f}, z-extent {b[5] - b[2]:.3f}")
    print(f"   3D gap head / body 1 as printed: {head.min_gap(b1, 3.0):.3f}")
