"""Independent layer-by-layer printability test of attempts/joints (pocket capybara).

Loads attempts/joints/make_capybara.py BY FILE PATH (there is an older
make_capybara.py one folder up that a plain `import` can pick up by mistake),
calls make_capybara() and make_test(), and slices every separate body itself.
None of the design's own checks are used.

  (a) each body's lowest layer is at z = 0
  (b) every island of every layer overlaps the same body's layer below
  (c) overhang: area of each layer outside (layer below grown by H*tan45 + 0.05)
  (d) horizontal gap between different bodies in each layer
  (e) extra: vertical clearance where one body is printed over another
  (f) extra: slivers thinner than one 0.4 mm line in a layer

Run: python3 layer_test.py [layer_height=0.1] [phase=0.5]
     phase = where in each layer the slice is taken (0 bottom .. 1 top)
"""
import sys
import importlib.util
import numpy as np
import manifold3d as mf

DESIGN = '/home/user/Weave-Trial/fidgets/attempts/joints/make_capybara.py'
spec = importlib.util.spec_from_file_location('joints_capybara', DESIGN)
mc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mc)
assert mc.__file__ == DESIGN, mc.__file__

H = float(sys.argv[1]) if len(sys.argv) > 1 else 0.1
PHASE = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
GROW = H * np.tan(np.radians(45)) + 0.05
RJ = mf.JoinType.Round
TINY = 1e-5          # mm2: below this an area is numerical noise
LINE = 0.4           # nozzle line width for the sliver test


def grow(cs, d):
    return cs.offset(d, RJ, 2.0, 96)


def polys(cs):
    return [np.asarray(p, float) for p in cs.to_polygons()]


def centroid(cs):
    A = cx = cy = 0.0
    for p in polys(cs):
        x, y = p[:, 0], p[:, 1]
        xn, yn = np.roll(x, -1), np.roll(y, -1)
        c = x * yn - xn * y
        A += c.sum() / 2
        cx += ((x + xn) * c).sum() / 6
        cy += ((y + yn) * c).sum() / 6
    if abs(A) < 1e-12:
        b = cs.bounds()
        return (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    return cx / A, cy / A


def outline_gap(a, b):
    """Exact smallest distance between the outlines of two disjoint cross-sections
    (vertex to segment, both ways), and the midpoint of that shortest hop."""
    best, where = 9e9, None
    for pa in polys(a):
        for pb in polys(b):
            for P, Q in ((pa, pb), (pb, pa)):
                A, B = Q, np.roll(Q, -1, axis=0)
                AB = B - A
                L2 = np.maximum((AB ** 2).sum(1), 1e-18)
                t = np.clip(((P[:, None, :] - A[None]) * AB[None]).sum(2) / L2[None], 0, 1)
                N = A[None] + t[..., None] * AB[None]
                D = np.sqrt(((P[:, None, :] - N) ** 2).sum(2))
                i = np.unravel_index(np.argmin(D), D.shape)
                if D[i] < best:
                    best, where = float(D[i]), tuple((P[i[0]] + N[i]) / 2)
    return best, where


def stick_out(up, low, hi=8.0):
    """How far `up` reaches past `low`: the smallest grow of low that covers up."""
    if low.is_empty():
        return float('inf')
    if (up - grow(low, hi)).area() > TINY:
        return hi
    lo = 0.0
    for _ in range(20):
        mid = (lo + hi) / 2
        if (up - grow(low, mid)).area() > TINY:
            lo = mid
        else:
            hi = mid
    return hi


def slices(m):
    top = m.bounding_box()[5]
    zs = np.arange(PHASE * H, top, H)
    return zs, [m.slice(float(z)) for z in zs]


def test_model(title, parts):
    print(f"\n=========== {title}: layer {H} mm, slice taken {PHASE:.2f} of the way up each layer; "
          f"allowed step-out {GROW:.3f} mm ===========")
    names = list(parts)
    for n in names:
        d = parts[n].decompose()
        if len(d) != 1:
            print(f"!! {n} is {len(d)} bodies, volumes {[round(x.volume(), 3) for x in d]}")
    sl = {n: slices(parts[n]) for n in names}
    res = {"a": [], "b": [], "weak": [], "c": [], "c_tot": {}, "d": [], "e": [], "f": []}

    # ---------------------------------------------------------------- (a)
    print("\n(a) does each body start on the bed?")
    for n in names:
        bb = parts[n].bounding_box()
        foot = parts[n].slice(1e-4)
        first = sl[n][1][0]
        fb = foot.bounds() if not foot.is_empty() else (0, 0, 0, 0)
        fp = [p for p in foot.decompose() if p.area() > TINY] if not foot.is_empty() else []
        vol = parts[n].volume()
        h = bb[5] - bb[2]
        cx, cy = centroid(foot) if fp else (float('nan'),) * 2
        print(f"   {n:<16} zmin {bb[2]:+.5f}  top {bb[5]:6.2f}  bed contact {foot.area():7.2f} mm2 in {len(fp)} piece(s) "
              f"[{fb[0]:.1f}..{fb[2]:.1f} x {fb[1]:.1f}..{fb[3]:.1f}]  first slice z={sl[n][0][0]:.3f}: {first.area():7.2f} mm2  "
              f"vol {vol:6.0f} mm3  height/min-foot-width {h / max(min(fb[2]-fb[0], fb[3]-fb[1]), 1e-9):.1f}")
        if abs(bb[2]) > 1e-6 or foot.area() < TINY:
            res["a"].append((n, bb[2], foot.area()))

    # ---------------------------------------------------------------- (b) (c)
    print("\n(b) islands with none of their own body beneath   (c) overhang past the allowed step-out")
    for n in names:
        zs, cs = sl[n]
        air, weak, patches, tot = [], [], [], 0.0
        per_layer = []
        for k in range(1, len(zs)):
            up, low = cs[k], cs[k - 1]
            if up.is_empty():
                continue
            for piece in up.decompose():
                pa = piece.area()
                if pa < TINY:
                    continue
                ov = (piece ^ low).area()
                if ov < TINY:
                    cx, cy = centroid(piece)
                    g = outline_gap(piece, low)[0] if not low.is_empty() else float('inf')
                    air.append((float(zs[k]), pa, cx, cy, g, piece.bounds()))
                elif ov < 0.3 * pa:
                    cx, cy = centroid(piece)
                    weak.append((float(zs[k]), pa, ov, cx, cy))
            ex = up - grow(low, GROW)
            a = ex.area()
            if a > TINY:
                tot += a
                per_layer.append((float(zs[k]), a))
                for piece in ex.decompose():
                    if piece.area() > TINY:
                        patches.append((piece.area(), float(zs[k]), piece.bounds(), k, piece))
        patches.sort(key=lambda t: -t[0])
        res["c_tot"][n] = tot
        print(f"   {n:<16} mid-air islands {len(air)}   weakly rooted (<30% on layer below) {len(weak)}   "
              f"overhang past {GROW:.2f}: {tot:.4f} mm2 in {len(patches)} patches over {len(per_layer)} layers")
        for z, pa, cx, cy, g, b in air[:10]:
            print(f"        MID-AIR z={z:.3f}  {pa:.4f} mm2  x {b[0]:.2f}..{b[2]:.2f}  y {b[1]:.2f}..{b[3]:.2f}  "
                  f"nearest own material in the layer below is {g:.3f} mm away sideways")
            res["b"].append((n, z, pa, cx, cy, g))
        for z, pa, ov, cx, cy in weak[:10]:
            print(f"        weak    z={z:.3f}  island {pa:.4f} mm2, {ov:.4f} mm2 of it on the layer below, at x={cx:.2f} y={cy:.2f}")
            res["weak"].append((n, z, pa, ov, cx, cy))
        for a, z, b, k, piece in patches[:8]:
            r = stick_out(piece, cs[k - 1])
            print(f"        overhang z={z:.3f}  {a:.4f} mm2  x {b[0]:.2f}..{b[2]:.2f}  y {b[1]:.2f}..{b[3]:.2f}  "
                  f"reaches {r:.3f} mm past the layer below ({np.degrees(np.arctan2(r, H)):.0f} deg from vertical)")
            res["c"].append((n, z, a, tuple(round(float(v), 3) for v in b), r))

    # ---------------------------------------------------------------- (d)
    print("\n(d) horizontal gap between different bodies in the same layer (minimum over all layers)")
    rows = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            ba, bb = parts[a].bounding_box(), parts[b].bounding_box()
            if any(ba[j] > bb[j + 3] + 2 or bb[j] > ba[j + 3] + 2 for j in range(3)):
                continue
            (za, ca), (zb, cb) = sl[a], sl[b]
            per, fused = [], []
            for k in range(min(len(za), len(zb))):
                if ca[k].is_empty() or cb[k].is_empty():
                    continue
                A, B = ca[k].bounds(), cb[k].bounds()
                if A[0] > B[2] + 2 or B[0] > A[2] + 2 or A[1] > B[3] + 2 or B[1] > A[3] + 2:
                    continue
                ov = (ca[k] ^ cb[k]).area()
                if ov > TINY:
                    fused.append((float(za[k]), ov))
                    continue
                g, w = outline_gap(ca[k], cb[k])
                per.append((float(za[k]), g, w))
            if not per and not fused:
                continue
            rows.append((min(per, key=lambda p: p[1]) if per else (None, 9e9, None), a, b, per, fused))
    rows.sort(key=lambda r: r[0][1])
    for (z, g, w), a, b, per, fused in rows:
        if g > 2 and not fused:
            continue
        under3 = [p for p in per if p[1] < 0.30]
        under4 = [p for p in per if p[1] < 0.40 - 1e-6]
        first = per[0] if per and per[0][0] < H else None
        ftxt = f"first layer {first[1]:.3f} at x={first[2][0]:.2f} y={first[2][1]:.2f}" if first else "not side by side in the first layer"
        print(f"   {a:<16} {b:<16} min {g:.3f} mm at z={z:.3f} x={w[0]:.2f} y={w[1]:.2f}; {ftxt}; "
              f"layers <0.30: {len(under3)}, <0.40: {len(under4)}, overlapping: {len(fused)}")
        res["d"].append((a, b, g, z, w, first[1] if first else None, len(under3), len(under4), len(fused)))

    # ---------------------------------------------------------------- (e)
    print("\n(e) one body printed over another: fewest empty layers between them")
    for a in names:
        for b in names:
            if a == b:
                continue
            ba, bb = parts[a].bounding_box(), parts[b].bounding_box()
            if any(ba[j] > bb[j + 3] or bb[j] > ba[j + 3] for j in range(2)):
                continue
            (za, ca), (zb, cb) = sl[a], sl[b]
            best = None
            for k in range(len(za)):            # a's layer k below, b's layer k+nn above
                if ca[k].is_empty():
                    continue
                for nn in range(1, 10):
                    if k + nn >= len(zb):
                        break
                    ov = ca[k] ^ cb[k + nn]
                    if ov.area() > 0.005:
                        if best is None or nn < best[0] or (nn == best[0] and ov.area() > best[2]):
                            cx, cy = centroid(ov)
                            best = (nn, float(za[k]), ov.area(), cx, cy)
                        break
            if best:
                clear = (best[0] - 1) * H
                print(f"   {b:<16} over {a:<16} {best[0] - 1} empty layer(s) = {clear:.2f} mm, above z={best[1]:.3f} "
                      f"({best[2]:.3f} mm2 at x={best[3]:.2f} y={best[4]:.2f})")
                res["e"].append((b, a, clear, best[1], best[2], best[3], best[4]))

    # ---------------------------------------------------------------- (f)
    print(f"\n(f) slivers narrower than one {LINE} mm line (area that vanishes when the layer is shrunk and regrown by {LINE/2})")
    for n in names:
        zs, cs = sl[n]
        found = []
        for k in range(len(zs)):
            if cs[k].is_empty():
                continue
            opened = grow(grow(cs[k], -LINE / 2), LINE / 2 + 0.02)
            thin = cs[k] - opened
            for piece in thin.decompose():
                if piece.area() > 0.03:
                    found.append((float(zs[k]), piece.area(), piece.bounds()))
        if found:
            zlo, zhi = min(f[0] for f in found), max(f[0] for f in found)
            big = sorted(found, key=lambda f: -f[1])[:4]
            print(f"   {n:<16} {len(found)} slivers in z {zlo:.2f}..{zhi:.2f}; largest: " +
                  "; ".join(f"z={z:.2f} {a:.3f} mm2 x {b[0]:.2f}..{b[2]:.2f} y {b[1]:.2f}..{b[3]:.2f}" for z, a, b in big))
            res["f"].append((n, len(found), zlo, zhi, big))
        else:
            print(f"   {n:<16} none")
    return res


def main():
    print(f"design under test: {mc.__file__}")
    out = {}
    for title, maker in (("pocket capybara", mc.make_capybara), ("test strip", mc.make_test)):
        parts, joints, info = maker()
        out[title] = test_model(title, parts)
    print("\nSUMMARY")
    for t, f in out.items():
        print(f"  {t}: not on bed {len(f['a'])}; mid-air islands {len(f['b'])}; weak islands {len(f['weak'])}; "
              f"overhang mm2 total {sum(f['c_tot'].values()):.4f}; "
              f"body pairs under 0.30 mm {sum(1 for d in f['d'] if d[2] < 0.30 or d[8])}; "
              f"tightest pair {min(f['d'], key=lambda d: d[2])[:4] if f['d'] else None}")


if __name__ == "__main__":
    main()
