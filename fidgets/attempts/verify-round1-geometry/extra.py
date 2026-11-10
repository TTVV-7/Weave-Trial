"""Overhang from the mesh normals (independent of slicing); the lug-less variant; leg footprints."""
import sys, importlib.util
import numpy as np, trimesh, manifold3d as mf
from lib import *

parts, joints, info = cb.make_capybara()
print("A. downward-facing area by steepness (angle of the face below horizontal-normal: 90 = flat ceiling, 45 = the limit), faces above z = 0.01")
tot = 0
for n, p in parts.items():
    me = p.to_mesh()
    m = trimesh.Trimesh(np.asarray(me.vert_properties)[:, :3], np.asarray(me.tri_verts), process=False)
    nz = m.face_normals[:, 2]
    up = m.triangles_center[:, 2] > 0.01
    ang = np.degrees(np.arcsin(np.clip(-nz, -1, 1)))
    a = m.area_faces
    bins = [(44.0, 45.05), (45.05, 46), (46, 50), (50, 70), (70, 90.1)]
    tot += a[up & (ang > 45.05)].sum()
    worst = np.argsort(-(a * (up & (ang > 45.05))))[:2]
    extra = "; ".join(f"{a[i]:.4f} mm2 at {np.round(m.triangles_center[i], 2).tolist()} {ang[i]:.1f} deg" for i in worst if up[i] and ang[i] > 45.05 and a[i] > 1e-4)
    print(f"   {n:<16} bed face {a[(~up) & (nz < -0.99)].sum():7.2f} | " + " | ".join(f"{lo:g}-{hi:g}: {a[up & (ang > lo) & (ang <= hi)].sum():8.3f}" for lo, hi in bins) + (f"   worst: {extra}" if extra else ""))
print(f"   total steeper than 45.05 deg: {tot:.4f} mm2")

print("\nB. bed contact and stance of the free-standing bodies")
for n, p in parts.items():
    foot = p.slice(1e-4)
    b = foot.bounds()
    bb = p.bounding_box()
    # centre of mass against the footprint
    me = p.to_mesh()
    m = trimesh.Trimesh(np.asarray(me.vert_properties)[:, :3], np.asarray(me.tri_verts), process=False)
    c = m.center_mass
    print(f"   {n:<16} contact {foot.area():7.2f} mm2, footprint x {b[0]:.2f}..{b[2]:.2f} y {b[1]:.2f}..{b[3]:.2f}; body x {bb[0]:.2f}..{bb[3]:.2f} y {bb[1]:.2f}..{bb[4]:.2f} top {bb[5]:.2f}; "
          f"centre of mass x={c[0]:.2f} y={c[1]:.2f} z={c[2]:.2f}; {'inside' if b[0] < c[0] < b[2] and b[1] < c[1] < b[3] else 'OUTSIDE'} the footprint's box")

print("\nC. the variant without the keyring lug: body 4 layer by layer")
p2, j2, i2 = cb.make_capybara(loop=False)
b4 = p2["body 4"]
print(f"   body 4 pieces {len(b4.decompose())}, zmin {b4.bounding_box()[2]:.5f}, top {b4.bounding_box()[5]:.2f}, genus {b4.genus()}")
for H in (0.1, 0.2):
    zs = np.arange(H / 2, b4.bounding_box()[5], H)
    cs = [b4.slice(float(z)) for z in zs]
    air = over = 0
    oa = 0.0
    for k in range(1, len(zs)):
        for piece in cs[k].decompose():
            if piece.area() > 1e-5 and (piece ^ cs[k - 1]).area() < 1e-5:
                air += 1
        ex = cs[k] - cs[k - 1].offset(H + 0.05, mf.JoinType.Round, 2.0, 96)
        if ex.area() > 1e-5:
            over += 1
            oa += ex.area()
    print(f"   layer {H}: mid-air islands {air}; layers with overhang past 45 deg (+0.05) {over}, total {oa:.4f} mm2")
for a, b in (("body 3", "body 4"), ("body 4", "hind left leg"), ("body 4", "hind right leg")):
    print(f"   {a} / {b}: 3D gap {p2[a].min_gap(p2[b], 2.0):.3f}")
