import importlib.util
import numpy as np, manifold3d as mf
J = '/home/user/Weave-Trial/fidgets/attempts/joints/make_capybara.py'
spec = importlib.util.spec_from_file_location('joints_capybara', J)
mc = importlib.util.module_from_spec(spec); spec.loader.exec_module(mc)
RJ = mf.JoinType.Round
parts, joints, info = mc.make_capybara()
def grow(cs, d): return cs.offset(d, RJ, 2.0, 96)
def polys(cs): return [np.asarray(p, float) for p in cs.to_polygons()]
def pdist(P, Q):
    A, B = Q, np.roll(Q, -1, axis=0); AB = B - A
    L2 = np.maximum((AB ** 2).sum(1), 1e-18)
    t = np.clip(((P[:, None, :] - A[None]) * AB[None]).sum(2) / L2[None], 0, 1)
    N = A[None] + t[..., None] * AB[None]
    return np.sqrt(((P[:, None, :] - N) ** 2).sum(2)).min()

print("A. neck tab wall round the hinge sockets (vertical sections y=const of the head, window round the nod axis)")
head = parts["head"].rotate([90, 0, 0])      # section at z'=y is in (x, -z)
c = np.array([mc.NECK_X, -mc.NECK_Z])
for y in (2.49, 2.4, 2.3, 2.1, 1.9, 1.6, 1.3, 1.05):
    cs = head.slice(y)
    ps = polys(cs)
    hole = [p for p in ps if np.abs(np.linalg.norm(p - c, axis=1) - np.linalg.norm(p - c, axis=1).mean()).max() < 0.02 and np.linalg.norm(p - c, axis=1).mean() < 4]
    if not hole:
        print(f"   y={y}: no round hole found, {len(ps)} outlines"); continue
    h = hole[0]; r = np.linalg.norm(h - c, axis=1).mean()
    others = [p for p in ps if p is not h]
    d = min(min(pdist(h, o), pdist(o, h)) for o in others)
    # where is it thinnest
    best = (9, None)
    for o in others:
        for i, pt in enumerate(h):
            dd = pdist(pt[None], o)
            if dd < best[0]: best = (dd, pt)
    print(f"   y={y:.2f}: socket radius {r:.3f} mm; thinnest wall to the tab's outside {d:.3f} mm, at x={best[1][0]:.2f} z={-best[1][1]:.2f}")
g = mc.CLEAR * np.sqrt(2)
print(f"   the design's check uses socket radius {mc.NOD_PIN/2 + mc.NOD_DEPTH - g:.3f} and reports wall "
      f"{min(mc.TAB_RU, mc.TAB_C*np.sqrt(.5), mc.NECK_Z) - (mc.NOD_PIN/2 + mc.NOD_DEPTH - g):.3f}; "
      f"true radius at the tab face = {mc.NOD_PIN/2 + mc.NOD_DEPTH - mc.TAB_GAP + g:.3f}")

print("\nB. slivers thinner than 0.4 mm by place (body 1, body 2, body 4, head, front left leg)")
H = 0.1
for n in ("head", "body 1", "body 2", "body 4", "front left leg"):
    p = parts[n]
    rows = []
    for z in np.arange(H/2, p.bounding_box()[5], H):
        cs = p.slice(float(z))
        if cs.is_empty(): continue
        thin = cs - grow(grow(cs, -0.2), 0.22)
        for q in thin.decompose():
            if q.area() > 0.03:
                b = q.bounds()
                rows.append((float(z), q.area(), (b[0]+b[2])/2, (b[1]+b[3])/2, b[2]-b[0], b[3]-b[1]))
    # cluster by rounded xy centre
    cl = {}
    for z, a, cx, cy, w, h in rows:
        key = (round(cx / 1.5), round(cy / 1.5))
        cl.setdefault(key, []).append((z, a, cx, cy, w, h))
    print(f"   {n}:")
    for key, v in sorted(cl.items(), key=lambda kv: -sum(t[1] for t in kv[1])):
        zs = [t[0] for t in v]
        print(f"      x~{np.mean([t[2] for t in v]):6.2f} y~{np.mean([t[3] for t in v]):6.2f}  z {min(zs):.2f}..{max(zs):.2f} ({len(v)} layers)  "
              f"largest {max(t[1] for t in v):.3f} mm2, up to {max(t[4] for t in v):.2f} x {max(t[5] for t in v):.2f} mm")

print("\nC. downward-facing area by steepness, per body (mesh normals; independent of the slices)")
import trimesh
for n, p in parts.items():
    me = p.to_mesh()
    m = trimesh.Trimesh(np.asarray(me.vert_properties)[:, :3], np.asarray(me.tri_verts), process=False)
    nz = m.face_normals[:, 2]; up = m.triangles_center[:, 2] > 0.01
    ang = np.degrees(np.arcsin(np.clip(-nz, -1, 1)))    # 90 = flat ceiling, 45 = 45 deg overhang
    a = m.area_faces
    print(f"   {n:<16} bed face {a[(~up) & (nz < -0.99)].sum():7.2f} mm2 | overhang 44-46 deg {a[up & (ang > 44) & (ang <= 46)].sum():7.2f} | "
          f"46-50 {a[up & (ang > 46) & (ang <= 50)].sum():6.3f} | 50-70 {a[up & (ang > 50) & (ang <= 70)].sum():6.3f} | >70 {a[up & (ang > 70)].sum():6.3f} | "
          f"30-44 {a[up & (ang > 30) & (ang <= 44)].sum():7.2f}")
