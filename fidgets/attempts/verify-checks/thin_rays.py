"""Wall thickness measured on the mesh: from surface samples, shoot a ray straight inwards and
see how far it is to the other side. Lists clusters thinner than MIN_FEATURE.
'slab' = the far face is close to parallel (dot of normals < -0.9): a real wall.
'wedge' = far face at an angle (feather edge); reported separately with the edge angle."""
import sys
import numpy as np
import trimesh
from common import cb
import make_fidgets as mk
np.random.seed(1)
N = 60000
LIM = cb.MIN_FEATURE

def measure(name, part):
    m = mk.to_mesh(part)
    m = trimesh.Trimesh(m.vertices, m.faces, process=False)
    pts, fi = trimesh.sample.sample_surface(m, N)
    n = m.face_normals[fi]
    org = pts - n * 1e-4
    ray = trimesh.ray.ray_triangle.RayMeshIntersector(m)
    t = np.full(N, np.inf); dot = np.zeros(N)
    for s0 in range(0, N, 2500):
        sl = slice(s0, s0 + 2500)
        loc, ridx, tidx = ray.intersects_location(org[sl], -n[sl], multiple_hits=False)
        ridx = ridx + s0
        t[ridx] = np.linalg.norm(loc - org[ridx], axis=1)
        dot[ridx] = (m.face_normals[tidx] * n[ridx]).sum(1)
    return m, pts, n, t, dot

def clusters(pts, cell=1.5):
    """Greedy grid clustering; returns list of index arrays."""
    keys = np.floor(pts / cell).astype(int)
    d = {}
    for i, k in enumerate(map(tuple, keys)):
        d.setdefault(k, []).append(i)
    seen, out = set(), []
    for k in d:
        if k in seen:
            continue
        stack, grp = [k], []
        seen.add(k)
        while stack:
            c = stack.pop()
            grp += d[c]
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        q = (c[0]+dx, c[1]+dy, c[2]+dz)
                        if q in d and q not in seen:
                            seen.add(q); stack.append(q)
        out.append(np.array(grp))
    return out

def report(title, maker):
    parts, joints, info = maker()
    print(f"=== {title} ===")
    for name, part in parts.items():
        m, pts, n, t, dot = measure(name, part)
        per = m.area / N                       # mm2 each sample stands for
        slab = (t < LIM - 0.005) & (dot < -0.9)
        wedge = (t < LIM - 0.005) & (dot >= -0.9) & (dot < -0.3)
        print(f"{name}: area {m.area:.0f} mm2; under {LIM}: slab-like {slab.sum()*per:.2f} mm2, wedge-like {wedge.sum()*per:.2f} mm2; "
              f"thinnest slab-like {t[dot < -0.9].min():.3f}")
        for kind, mask in (("SLAB ", slab), ("wedge", wedge)):
            idx = np.where(mask)[0]
            if not len(idx):
                continue
            for g in sorted(clusters(pts[idx]), key=lambda g: -len(g)):
                gi = idx[g]
                a = len(gi) * per
                if a < (0.15 if kind == "SLAB " else 0.6):
                    continue
                lo, hi = pts[gi].min(0), pts[gi].max(0)
                ang = np.degrees(np.arccos(np.clip(-dot[gi], -1, 1)))
                nm = n[gi].mean(0)
                print(f"   {kind} {a:6.2f} mm2  x {lo[0]:6.2f}..{hi[0]:6.2f}  y {lo[1]:6.2f}..{hi[1]:6.2f}  z {lo[2]:5.2f}..{hi[2]:5.2f}  "
                      f"t min {t[gi].min():.3f} median {np.median(t[gi]):.3f}  edge angle median {np.median(ang):4.0f} deg  mean normal ({nm[0]:+.2f},{nm[1]:+.2f},{nm[2]:+.2f})")
    print()

if __name__ == "__main__":
    report("pocket capybara", cb.make_capybara)
    report("test strip", cb.make_test)
