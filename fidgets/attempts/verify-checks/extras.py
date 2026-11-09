"""A. at what bend the front leg starts to hit body 2; C. shipped STL integrity; D. overhang by angle,
first-layer seam gaps; E. ear, eye-to-bore wall, dict values next to the old formulas."""
import numpy as np
import trimesh
import manifold3d as mf
from common import cb
import make_fidgets as mk

parts, joints, info = cb.make_capybara()
tparts, tjoints, tinfo = cb.make_test()
J = {j["name"]: j for j in joints}

print("A. front left leg full circle vs body joint 1 bend (2.5 deg leg steps)")
leg = "front left leg"
for bend in (5, 10, 12.5, 15, 17.5, 20, 22.5, 25):
    p = cb.posed(parts, joints, {"body joint 1": bend})
    R = cb.union(v for k, v in p.items() if k != leg)
    hits, tight = [], (9, None)
    for a in np.arange(-180, 180, 2.5):
        L = cb.turn(parts[leg], "y", J[leg]["point"], a)
        v = (L ^ R).volume()
        if v > 1e-6:
            hits.append((a, v))
        elif abs(a) <= 45:
            g = L.min_gap(p["body 2"], 3.0)
            if g < tight[0]:
                tight = (g, a)
    print(f"   bend {bend:5.1f}: " + (f"leg hits body 2 at leg angles {hits[0][0]:g}..{hits[-1][0]:g}, worst {max(h[1] for h in hits):.3f} mm3" if hits else "no hit")
          + f"; closest the leg comes to body 2 inside +-45: {tight[0]:.2f} mm at {tight[1]}")
print("   same on the test strip (leg vs body 2, joint at +-25):")
TJ = {j["name"]: j for j in tjoints}
for bend in (-25, 25):
    p = cb.posed(tparts, tjoints, {"body joint": bend})
    hits = []
    for a in np.arange(-180, 180, 2.5):
        L = cb.turn(tparts["leg"], "y", TJ["leg"]["point"], a)
        v = (L ^ p["body 2"]).volume()
        if v > 1e-6:
            hits.append((a, v))
    print(f"   bend {bend}: " + (f"hits at {hits[0][0]:g}..{hits[-1][0]:g}, worst {max(h[1] for h in hits):.3f} mm3" if hits else "no hit"))

print("C. shipped STLs")
for f, want in (("pocket-capybara.stl", 10), ("pocket-capybara-test.stl", 3)):
    m = trimesh.load('/home/user/Weave-Trial/fidgets/attempts/joints/' + f)
    comps = m.split(only_watertight=False)
    print(f"   {f}: {len(m.faces)} tris, {len(comps)} shells (want {want}), watertight each: {all(c.is_watertight for c in comps)}, "
          f"winding ok: {all(c.is_winding_consistent for c in comps)}, min z {m.bounds[0][2]:.4f}, extents {np.round(m.extents, 2)}, "
          f"volumes {sorted(round(float(c.volume), 1) for c in comps)}")

print("D1. down-facing surface off the bed, by angle from the horizontal (degrees below which a slicer wants support: 45)")
for title, P in (("full", parts), ("test", tparts)):
    bins = [(0, 30), (30, 40), (40, 44.9), (44.9, 45.08), (45.08, 50), (50, 89.9)]
    tot = np.zeros(len(bins))
    for name, p in P.items():
        m = mk.to_mesh(p)
        nz = m.face_normals[:, 2]
        off = m.triangles_center[:, 2] > 0.01
        ang = np.degrees(np.arcsin(np.clip(-nz, -1, 1)))      # 90 = flat ceiling, 45 = the limit
        for i, (a, b) in enumerate(bins):
            sel = off & (nz < 0) & (ang >= a) & (ang < b)
            tot[i] += m.area_faces[sel].sum()
    print(f"   {title}: " + ", ".join(f"{a}-{b} deg from vertical-ish: {t:.1f} mm2" for (a, b), t in zip(bins, tot)))
print("   (angle = how far the face's normal tips below the horizon; the design's test only counts > 45.06)")

print("D2. first layer (z = 0.1): gaps between neighbouring bodies, length of seam closer than 0.45 mm")
names = list(parts)
sl = {n: parts[n].slice(0.1) for n in names}
for i, a in enumerate(names):
    for b in names[i + 1:]:
        A, B = sl[a], sl[b]
        if A.is_empty() or B.is_empty():
            continue
        near = A.offset(0.6, mf.JoinType.Round) ^ B
        if near.is_empty():
            continue
        # smallest gap: grow A until it touches B
        lo, hi = 0.0, 0.6
        for _ in range(20):
            mid = (lo + hi) / 2
            if (A.offset(mid, mf.JoinType.Round) ^ B).area() > 1e-6:
                hi = mid
            else:
                lo = mid
        band = (A.offset(0.45, mf.JoinType.Round) ^ B).area()
        # seam length ~ area of B within 0.45 of A divided by the mean depth (0.45 - gap)/1 ... report area only
        print(f"   {a} / {b}: smallest first-layer gap {hi:.3f} mm; area of {b} within 0.45 mm of {a}: {band:.2f} mm2")

print("E. thin_features() as the design computes it, and the values for comparison")
walls, pins = cb.thin_features(parts, info)
for k, v in sorted(walls.items(), key=lambda kv: kv[1]):
    print(f"   wall  {k:<45} {v:.3f}")
for k, v in pins.items():
    print(f"   pin   {k:<45} {v:.3f}")
g = cb.CLEAR * np.sqrt(2)
true_r = cb.NOD_PIN / 2 + cb.NOD_DEPTH + g - cb.TAB_GAP
print(f"   socket radius at the tab face: design formula {cb.NOD_PIN/2 + cb.NOD_DEPTH - g:.3f}; from the socket solid {true_r:.3f}")
print(f"   so 'neck tab round its sockets' is really top {cb.TAB_RU - true_r:.3f}, 45 deg underside {cb.TAB_C*np.sqrt(.5) - true_r:.3f}")
print(f"   eye_y {info['eye_y']:.3f}; HEAD's formula for the wall round the shaft would give {info['eye_y'] - cb.EYE[2] - 1.0 - (cb.SHAFT_R + cb.SHAFT_GAP):.3f}")

print("E2. ears: section of the head at several heights, the ear's own width (largest disc that fits = erosion depth)")
head = parts["head"]
for z in (12.0, 12.5, 13.0, 13.45, 13.8, 14.2, 14.6, 15.0, 15.3):
    cs = head.slice(float(z))
    out = []
    for piece in cs.decompose():
        b = piece.bounds()
        if b[3] < 2.0:      # keep the +y ear / +y side only
            continue
        lo_, hi_ = 0.0, 5.0
        for _ in range(18):
            mid = (lo_ + hi_) / 2
            if piece.offset(-mid, mf.JoinType.Round).area() > 1e-6:
                lo_ = mid
            else:
                hi_ = mid
        out.append(f"piece x {b[0]:.2f}..{b[2]:.2f} y {b[1]:.2f}..{b[3]:.2f} area {piece.area():.2f} widest inscribed disc dia {2*lo_:.2f}")
    print(f"   z={z}: " + (" | ".join(out) if out else "nothing at y>2"))
