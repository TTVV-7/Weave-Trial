"""Targeted measurements on the real solids of the things thin_features() only works out on paper."""
import numpy as np
import manifold3d as mf
from common import cb

parts, joints, info = cb.make_capybara()
tparts, tjoints, tinfo = cb.make_test()

def seg_dist(p, a, b):
    ab = b - a
    t = np.clip(((p - a) @ ab) / (ab @ ab + 1e-18), 0, 1)
    return np.linalg.norm(p - (a + t * ab))

def ring_gap(polys_a, polys_b):
    """Smallest distance between two sets of closed polygons (vertex-to-segment both ways)."""
    best = (9e9, None)
    for A, B in ((polys_a, polys_b), (polys_b, polys_a)):
        for pa in A:
            for pb in B:
                nb = np.roll(pb, -1, axis=0)
                for p in pa:
                    ab = nb - pb
                    t = np.clip(((p - pb) * ab).sum(1) / ((ab * ab).sum(1) + 1e-18), 0, 1)
                    d = np.linalg.norm(p - (pb + t[:, None] * ab), axis=1)
                    i = d.argmin()
                    if d[i] < best[0]:
                        best = (d[i], p.copy())
    return best

def slice_y(m, y0):
    """Section of m in the plane y = y0, as polygons in (x, z)."""
    cs = m.rotate([90, 0, 0]).slice(float(y0))     # (x, y, z) -> (x, -z, y)
    return [np.c_[np.asarray(p)[:, 0], -np.asarray(p)[:, 1]] for p in cs.to_polygons()]

def slice_x(m, x0):
    """Section in the plane x = x0, as polygons in (y, z)."""
    cs = m.rotate([0, -90, 0]).slice(float(x0))    # (x, y, z) -> (-z, y, x)
    return [np.c_[np.asarray(p)[:, 1], -np.asarray(p)[:, 0]] for p in cs.to_polygons()]

def area(p):
    x, y = p[:, 0], p[:, 1]
    return 0.5 * (x * np.roll(y, -1) - np.roll(x, -1) * y).sum()

print("1. neck tab round its nod sockets (design says %.3f)" % cb.thin_features(parts, info)[0]["neck tab round its sockets"])
head = parts["head"]
for y0 in (2.49, 2.4, 2.3, 2.2, 2.0, 1.8, 1.5, 1.1):
    ps = slice_y(head, y0)
    # the socket hole: the polygon round the nod axis with a radius of 1..3.5
    holes, outers = [], []
    for p in ps:
        c = p.mean(0)
        r = np.linalg.norm(p - [cb.NECK_X, cb.NECK_Z], axis=1)
        if abs(c[0] - cb.NECK_X) < 0.2 and abs(c[1] - cb.NECK_Z) < 0.2 and r.max() < 3.6:
            holes.append(p)
        else:
            outers.append(p)
    if not holes:
        print(f"   y={y0}: no socket in this section ({len(ps)} loops)")
        continue
    rr = np.linalg.norm(holes[0] - [cb.NECK_X, cb.NECK_Z], axis=1).max()
    d, at = ring_gap(holes, outers)
    print(f"   y={y0:4.2f} ({cb.TAB_W/2 - y0:4.2f} in from the tab face): socket radius {rr:.3f}, thinnest wall round it {d:.3f} at x={at[0]:.2f} z={at[1]:.2f}")

print("2. roof over the neck slot, along the ridge y=0 (design probes only x = NECK_X = %.1f)" % cb.NECK_X)
b1 = parts["body 1"]
peak = cb.doorway_eave() + cb.TAB_W / 2 + cb.TAB_GAP
print(f"   doorway peak height {peak:.2f}, runs x {cb.NECK_X - cb.R_NOD - 1:.2f}..{cb.NECK_X + cb.TAB_C + 0.5:.2f}")
for x in np.arange(14.5, 28.6, 0.5):
    col = b1 ^ cb.box(x - 0.01, x + 0.01, -0.01, 0.01, 0, 40)
    if col.is_empty():
        print(f"   x={x:5.2f}: nothing on the centre line")
        continue
    zs = []
    for piece in col.decompose():
        bb = piece.bounding_box()
        zs.append((bb[2], bb[5]))
    zs.sort()
    top = zs[-1]
    print(f"   x={x:5.2f}: material on the centre line z " + ", ".join(f"{a:.2f}..{b:.2f}" for a, b in zs) + f"   -> roof {top[1]-top[0]:.2f} thick" )

print("3. socket lip ('horn') at the flank, per layer, width in y at the blunt cut face x = axis + X_CUT")
for label, P, key, at in (("full model body 2", parts, "body 2", cb.AXES[0]), ("full model body 3", parts, "body 3", cb.AXES[1]),
                           ("full model body 4", parts, "body 4", cb.AXES[2]), ("test strip body 2", tparts, "body 2", tinfo["axes"][0])):
    rear = P[key]
    row = []
    for z in (0.02, 0.1, 0.3, 0.5, 0.7, 1.0, 2.0, 4.0, 8.0):
        cs = rear.slice(float(z))
        cs = cs ^ mf.CrossSection.square([0.6, 30]).translate([at + cb.X_CUT - 0.001, 0])
        # width of the horn right at the cut face and 0.3 behind it
        w = []
        for dx in (0.01, 0.3):
            strip = cs ^ mf.CrossSection.square([0.002, 30]).translate([at + cb.X_CUT + dx, 0])
            pieces = [np.asarray(p) for p in strip.to_polygons()]
            w.append(max((p[:, 1].max() - p[:, 1].min() for p in pieces), default=0.0))
        row.append(f"z={z:g}: {w[0]:.2f}/{w[1]:.2f}")
    print(f"   {label}: " + "  ".join(row) + "   (at face / 0.3 mm behind)")
print("   design reports %.3f for the full model, %.3f for the strip" % (
    cb.thin_features(parts, info)[0]["socket lip at the flank (2nd layer up)"],
    cb.thin_features(tparts, tinfo)[0]["socket lip at the flank (2nd layer up)"]))

print("4. socket lip over the top of the ball: section x = axis + X_CUT + d, thickness in z along y")
for key, at in (("body 2", cb.AXES[0]), ("body 3", cb.AXES[1]), ("body 4", cb.AXES[2])):
    for d in (0.02, 0.2, 0.4, 0.8):
        x0 = at + cb.X_CUT + d
        out = []
        for y in (0, 1, 2, 3, 4, 5, 6, 7, 8):
            col = parts[key] ^ cb.box(x0 - 0.005, x0 + 0.005, y - 0.005, y + 0.005, 8.0, 40)
            if col.is_empty():
                out.append(f"y={y}: open")
            else:
                bb = col.bounding_box()
                out.append(f"y={y}: {bb[5]-bb[2]:.2f}")
        print(f"   {key} {d:.2f} behind the cut face: " + "  ".join(out))
