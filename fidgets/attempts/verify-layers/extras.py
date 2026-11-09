"""Follow-up measurements on attempts/joints, from slices only."""
import importlib.util
import numpy as np, manifold3d as mf
J = '/home/user/Weave-Trial/fidgets/attempts/joints/make_capybara.py'
spec = importlib.util.spec_from_file_location('joints_capybara', J)
mc = importlib.util.module_from_spec(spec); spec.loader.exec_module(mc)
RJ = mf.JoinType.Round
parts, joints, info = mc.make_capybara()
H = 0.1

def grow(cs, d): return cs.offset(d, RJ, 2.0, 96)

# 1. islands per layer: free-standing pieces on the bed and the height they join the rest
print("1. separate pieces of one body in a layer (bed islands and where they join)")
for n, p in parts.items():
    top = p.bounding_box()[5]
    zs = np.arange(H / 2, top, H)
    counts = []
    for z in zs:
        cs = p.slice(float(z))
        pcs = sorted([(q.area(), q.bounds()) for q in cs.decompose() if q.area() > 1e-5], key=lambda t: t[0])
        counts.append(pcs)
    runs, prev, start = [], None, None
    for z, pcs in zip(zs, counts):
        k = len(pcs)
        if k != prev:
            runs.append([float(z), k, [round(a, 2) for a, _ in pcs], [tuple(round(float(v), 2) for v in b) for _, b in pcs]])
            prev = k
    print(f"   {n}: " + " | ".join(f"from z={z:.2f}: {k} piece(s) {areas if k > 1 else ''}" for z, k, areas, _ in runs))
    for z, k, areas, bs in runs:
        if k > 1:
            print(f"        at z={z:.2f} smallest piece {areas[0]} mm2 at x {bs[0][0]}..{bs[0][2]} y {bs[0][1]}..{bs[0][3]}")

# 2. first layer: how much seam is at <= 0.41 mm and <= 0.51 mm between bodies
print("\n2. first layer (z=0.05): outline length of each pair lying within 0.41 / 0.51 / 0.56 mm of the other body")
names = list(parts)
first = {n: parts[n].slice(0.05) for n in names}
def near_len(a, b, d):
    tot = 0.0
    bp = [np.asarray(q, float) for q in b.to_polygons()]
    for pa in a.to_polygons():
        pa = np.asarray(pa, float)
        A, B = pa, np.roll(pa, -1, axis=0)
        for s in range(len(A)):
            L = np.linalg.norm(B[s] - A[s])
            if L < 1e-9: continue
            m = max(2, int(L / 0.05) + 1)
            pts = A[s] + (B[s] - A[s]) * (np.arange(m)[:, None] + 0.5) / m
            dmin = np.full(m, 9e9)
            for q in bp:
                QA, QB = q, np.roll(q, -1, axis=0)
                AB = QB - QA
                L2 = np.maximum((AB ** 2).sum(1), 1e-18)
                t = np.clip(((pts[:, None, :] - QA[None]) * AB[None]).sum(2) / L2[None], 0, 1)
                N = QA[None] + t[..., None] * AB[None]
                dmin = np.minimum(dmin, np.sqrt(((pts[:, None, :] - N) ** 2).sum(2)).min(1))
            tot += L / m * (dmin <= d).sum()
    return tot
for i, a in enumerate(names):
    for b in names[i + 1:]:
        A, B = first[a].bounds(), first[b].bounds()
        if A[0] > B[2] + 1 or B[0] > A[2] + 1 or A[1] > B[3] + 1 or B[1] > A[3] + 1: continue
        l41, l51, l56 = (near_len(first[a], first[b], d) for d in (0.41, 0.51, 0.56))
        if l56 > 0:
            print(f"   {a:<10} / {b:<16} {l41:6.1f} mm at <=0.41, {l51:6.1f} mm at <=0.51, {l56:6.1f} mm at <=0.56")

# 3. neck tab: wall left round the hinge sockets
print("\n3. neck tab (head) round its hinge sockets: vertical sections y = const through the tab")
head = parts["head"]
rot = head.rotate([90, 0, 0])          # (x, y, z) -> (x, -z, y): slicing at z'=y gives an (x, -z) section
for y in (2.49, 2.4, 2.3, 2.2, 2.0, 1.8, 1.5, 1.2):
    cs = rot.slice(y)                   # outline in (x, -z)
    win = mf.CrossSection.square([12, 12]).translate([mc.NECK_X - 6, -mc.NECK_Z - 6])
    cs = cs ^ win
    # socket hole radius at this y (measured): largest disc round the axis that is empty
    def empty(r): return (cs ^ mf.CrossSection.circle(r, 256).translate([mc.NECK_X, -mc.NECK_Z])).area() < 1e-6
    lo, hi = 0.0, 5.0
    for _ in range(30):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if empty(mid) else (lo, mid)
    r_hole = lo
    # wall = thinnest material between the hole and the outside of the tab: grow the hole until it breaks out
    lo2, hi2 = r_hole, 6.0
    def inside(r):   # ring between r_hole and r fully material?
        ring = mf.CrossSection.circle(r, 256).translate([mc.NECK_X, -mc.NECK_Z]) - mf.CrossSection.circle(r_hole + 1e-3, 256).translate([mc.NECK_X, -mc.NECK_Z])
        return (ring - cs).area() < 1e-5
    for _ in range(30):
        mid = (lo2 + hi2) / 2
        lo2, hi2 = (mid, hi2) if inside(mid) else (lo2, mid)
    print(f"   y={y:.2f}: socket radius {r_hole:.3f}, thinnest wall round it {lo2 - r_hole:.3f} mm")
g = mc.CLEAR * np.sqrt(2)
print(f"   design's own figure: 'neck tab round its sockets' uses socket radius {mc.NOD_PIN/2 + mc.NOD_DEPTH - g:.3f} -> wall "
      f"{min(mc.TAB_RU, mc.TAB_C*np.sqrt(.5), mc.NECK_Z) - (mc.NOD_PIN/2 + mc.NOD_DEPTH - g):.3f}")

# 4. leg on its pin: what holds it
print("\n4. leg pin and the leg's lip, vertical sections through the pin axis")
x = mc.LEG_X[0]
b1, leg = parts["body 1"], parts["front left leg"]
for nm, m in (("body 1 pin", b1), ("leg", leg)):
    r = m.rotate([90, 0, 0])
    for y in (8.7, 8.91, 9.2, 9.6, 10.0, 10.09):
        cs = r.slice(y) ^ mf.CrossSection.square([12, 12]).translate([x - 6, -mc.LEG_Z - 6])
        if cs.is_empty():
            print(f"   {nm} y={y}: empty"); continue
        bb = cs.bounds()
        print(f"   {nm} section y={y:5.2f}: area {cs.area():7.3f} mm2, x {bb[0]-x:+.2f}..{bb[2]-x:+.2f} from pin centre, z {-bb[3]:.2f}..{-bb[1]:.2f}")
