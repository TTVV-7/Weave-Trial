"""Independent layer-by-layer printability test of the pocket capybara.

Does not use any of the design's own checks: it only calls make_capybara() and
make_test() for the bodies, then slices each body itself.

  (a) each body's lowest layer is at z = 0
  (b) every island of every layer overlaps the same body's layer below
  (c) overhang: area of each layer outside (layer below grown by h*tan45 + 0.05)
  (d) horizontal gap between different bodies in each layer
  (e) extra: vertical clearance where one body is printed over another

Run: python3 verify_layers.py [layer_height] [phase 0..1]
"""
import sys
import json
import numpy as np
import manifold3d as mf

sys.path.insert(0, '/home/user/Weave-Trial/fidgets/attempts/joints')
sys.path.insert(0, '/home/user/Weave-Trial/fidgets')
import make_capybara as mc   # noqa: E402

H = float(sys.argv[1]) if len(sys.argv) > 1 else 0.1
PHASE = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5      # 0.5 = slice at mid layer
GROW = H * np.tan(np.radians(45)) + 0.05
RJ = mf.JoinType.Round
EPS_A = 1e-5


def layers(m):
    top = m.bounding_box()[5]
    zs = np.arange(PHASE * H, top, H)
    return zs, [m.slice(float(z)) for z in zs]


def polys(cs):
    return [np.asarray(p, float) for p in cs.to_polygons()]


def centroid(cs):
    """Area centroid of a cross-section (holes counted negative)."""
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


def seg_pt_dist(P, A, B):
    """Distances from points P (n,2) to segments A->B (m,2): (n,m) matrix and nearest points."""
    AB = B - A
    L2 = (AB ** 2).sum(1)
    L2 = np.where(L2 < 1e-18, 1e-18, L2)
    t = ((P[:, None, :] - A[None]) * AB[None]).sum(2) / L2[None]
    t = np.clip(t, 0, 1)
    Q = A[None] + t[..., None] * AB[None]
    D = np.sqrt(((P[:, None, :] - Q) ** 2).sum(2))
    return D, Q


def cs_gap(a, b):
    """Exact min distance between the outlines of two cross-sections, and where."""
    best = (9e9, None)
    for pa in polys(a):
        for pb in polys(b):
            for P, Q in ((pa, pb), (pb, pa)):
                D, N = seg_pt_dist(P, Q, np.roll(Q, -1, axis=0))
                i = np.unravel_index(np.argmin(D), D.shape)
                if D[i] < best[0]:
                    best = (float(D[i]), tuple((P[i[0]] + N[i]) / 2))
    return best


def overhang_reach(up, low, lo=0.0, hi=6.0):
    """Smallest grow of `low` that covers `up` (how far the layer sticks out), by bisection."""
    if (up - low.offset(hi, RJ, 2.0, 64)).area() > EPS_A:
        return hi
    for _ in range(18):
        mid = (lo + hi) / 2
        if (up - low.offset(mid, RJ, 2.0, 64)).area() > 1e-4:
            lo = mid
        else:
            hi = mid
    return hi


def test_model(title, parts):
    print(f"\n================ {title}: layer {H} mm, sliced at {PHASE:.2f} of each layer, "
          f"allowed step-out {GROW:.3f} mm ================")
    names = list(parts)
    sl = {}
    for n in names:
        sl[n] = layers(parts[n])

    findings = {"a": [], "b": [], "c": [], "d": [], "e": []}

    # ---------------- (a) starts on the bed ----------------
    print("\n(a) lowest layer / footprint on the bed")
    for n in names:
        bb = parts[n].bounding_box()
        zs, cs = sl[n]
        a0 = cs[0].area()
        foot = parts[n].slice(0.0)
        b = foot.bounds() if not foot.is_empty() else (0, 0, 0, 0)
        npieces = len(foot.decompose()) if not foot.is_empty() else 0
        print(f"   {n:<16} zmin {bb[2]:+.4f}  ztop {bb[5]:.2f}  footprint at z=0: {foot.area():7.2f} mm2 in "
              f"{npieces} piece(s), {b[2]-b[0]:.1f} x {b[3]-b[1]:.1f} mm; first slice (z={zs[0]:.2f}) {a0:.2f} mm2; "
              f"volume {parts[n].volume():.0f} mm3")
        if abs(bb[2]) > 1e-6 or a0 < EPS_A:
            findings["a"].append((n, bb[2], a0))

    # ---------------- (b) islands, (c) overhang ----------------
    print("\n(b) islands with nothing of their own body beneath, (c) overhang beyond the allowed step-out")
    for n in names:
        zs, cs = sl[n]
        tot = 0.0
        worst = []
        air = []
        weak = []
        for k in range(1, len(zs)):
            up, low = cs[k], cs[k - 1]
            if up.is_empty():
                continue
            for piece in up.decompose():
                pa = piece.area()
                if pa < EPS_A:
                    continue
                ov = (piece ^ low).area()
                cx, cy = centroid(piece)
                if ov < EPS_A:
                    g = cs_gap(piece, low)[0] if not low.is_empty() else float('nan')
                    air.append((float(zs[k]), pa, cx, cy, g))
                elif ov < 0.25 * pa:
                    weak.append((float(zs[k]), pa, ov, cx, cy))
            ex = up - low.offset(GROW, RJ, 2.0, 64)
            a = ex.area()
            if a > 1e-4:
                tot += a
                for piece in ex.decompose():
                    if piece.area() > 1e-4:
                        b = piece.bounds()
                        worst.append((piece.area(), float(zs[k]), b, k))
        worst.sort(key=lambda t: -t[0])
        print(f"   {n:<16} mid-air islands: {len(air)}   weakly-rooted islands (<25% on layer below): {len(weak)}"
              f"   overhang area beyond {GROW:.2f} mm: {tot:.3f} mm2 in {len(worst)} patches")
        for z, pa, cx, cy, g in air[:12]:
            print(f"        MID-AIR  z={z:.2f}  area {pa:.3f} mm2  at x={cx:.2f} y={cy:.2f}  "
                  f"nearest own material in layer below {g:.2f} mm away")
            findings["b"].append((n, z, pa, cx, cy, g))
        for z, pa, ov, cx, cy in weak[:12]:
            print(f"        weak     z={z:.2f}  area {pa:.3f} mm2, only {ov:.3f} mm2 rests on the layer below, "
                  f"at x={cx:.2f} y={cy:.2f}")
        for a, z, b, k in worst[:8]:
            zs_, cs_ = sl[n]
            patch = (cs_[k] - cs_[k - 1]) ^ mf.CrossSection.square([b[2] - b[0] + 0.6, b[3] - b[1] + 0.6]).translate(
                [b[0] - 0.3, b[1] - 0.3])
            r = overhang_reach(patch, cs_[k - 1])
            print(f"        overhang z={z:.2f}  {a:.3f} mm2  x {b[0]:.2f}..{b[2]:.2f}  y {b[1]:.2f}..{b[3]:.2f}  "
                  f"sticks out {r:.2f} mm past the layer below (45 deg = {H:.2f})")
            findings["c"].append((n, z, a, [float(v) for v in b], r))
        findings.setdefault("c_tot", {})[n] = tot

    # ---------------- (d) horizontal gaps between bodies ----------------
    print("\n(d) horizontal gap between different bodies, per layer (min over layers)")
    rows = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            ba, bb = parts[a].bounding_box(), parts[b].bounding_box()
            if any(ba[j] > bb[j + 3] + 1.5 or bb[j] > ba[j + 3] + 1.5 for j in range(3)):
                continue
            za, ca = sl[a]
            zb, cb = sl[b]
            best = (9e9, None, None)
            fused = []
            per = []
            for k in range(min(len(za), len(zb))):
                if ca[k].is_empty() or cb[k].is_empty():
                    continue
                A, B = ca[k].bounds(), cb[k].bounds()
                if A[0] > B[2] + 1.5 or B[0] > A[2] + 1.5 or A[1] > B[3] + 1.5 or B[1] > A[3] + 1.5:
                    continue
                ov = (ca[k] ^ cb[k]).area()
                if ov > EPS_A:
                    fused.append((float(za[k]), ov))
                    continue
                g, where = cs_gap(ca[k], cb[k])
                per.append((float(za[k]), g, where))
                if g < best[0]:
                    best = (g, float(za[k]), where)
            if best[1] is None and not fused:
                continue
            rows.append((best[0], a, b, best[1], best[2], fused, per))
    rows.sort(key=lambda r: r[0])
    for g, a, b, z, where, fused, per in rows:
        if g > 1.5 and not fused:
            continue
        under = [p for p in per if p[1] < 0.3]
        g0 = [p for p in per if p[0] < H]          # the first layer
        first = f"  first layer {g0[0][1]:.3f}" if g0 else ""
        print(f"   {a:<16} {b:<16} min {g:.3f} mm at z={z:.2f} x={where[0]:.2f} y={where[1]:.2f};"
              f"{first}  layers under 0.30: {len(under)}  overlapping layers: {len(fused)}")
        if g < 0.3 or fused:
            findings["d"].append((a, b, g, z, where, fused[:3]))

    # ---------------- (e) one body printed over another: vertical clearance ----------------
    print("\n(e) vertical clearance where one body is printed directly over another (min, layers apart)")
    for i, a in enumerate(names):
        for b in names:
            if a == b:
                continue
            ba, bb = parts[a].bounding_box(), parts[b].bounding_box()
            if any(ba[j] > bb[j + 3] or bb[j] > ba[j + 3] for j in range(2)):
                continue
            za, ca = sl[a]
            zb, cb = sl[b]
            best = None
            for k in range(len(za)):               # a below at layer k, b above at layer k+n
                if ca[k].is_empty():
                    continue
                for nn in range(1, 8):
                    if k + nn >= len(zb):
                        break
                    ov = ca[k] ^ cb[k + nn]
                    # only count where b's material at k+nn is new over a (not b all the way down)
                    if ov.area() > 0.01:
                        if best is None or nn < best[0] or (nn == best[0] and ov.area() > best[2]):
                            cx, cy = centroid(ov)
                            best = (nn, float(za[k]), ov.area(), cx, cy)
                        break
            if best:
                print(f"   {b:<16} over {a:<16} {best[0] * H:.2f} mm clear above z={best[1]:.2f} "
                      f"({best[2]:.2f} mm2 at x={best[3]:.2f} y={best[4]:.2f})")
                if best[0] * H < 0.3 - 1e-9:
                    findings["e"].append((b, a, best[0] * H, best[1], best[2], best[3], best[4]))
    return findings


def main():
    out = {}
    for title, maker in (("pocket capybara", mc.make_capybara), ("test strip", mc.make_test)):
        parts, joints, info = maker()
        # are the named parts really separate single bodies?
        for n, p in parts.items():
            d = p.decompose()
            if len(d) != 1:
                print(f"!! {title}: {n} decomposes into {len(d)} bodies, volumes {[round(x.volume(), 3) for x in d]}")
        out[title] = test_model(title, parts)
    print("\n\nSUMMARY")
    for t, f in out.items():
        print(t, {k: (len(v) if isinstance(v, list) else v) for k, v in f.items()})


if __name__ == "__main__":
    main()
