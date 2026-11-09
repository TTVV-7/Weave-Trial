"""Why does the shipped STL load as more shells than there are parts?"""
import numpy as np
import trimesh
from common import cb
import make_fidgets as mk

for title, maker, f in (("full", cb.make_capybara, "pocket-capybara.stl"), ("test", cb.make_test, "pocket-capybara-test.stl")):
    parts, joints, info = maker()
    print(f"== {title}")
    for name, p in parts.items():
        m0 = mk.to_mesh(p)
        m = trimesh.Trimesh(m0.vertices, m0.faces, process=False)
        comps = m.split(only_watertight=False)
        deg = int((m.area_faces < 1e-10).sum())
        # merged by position, as an STL reader does
        mm = trimesh.Trimesh(m0.vertices, m0.faces, process=True, merge_tex=True)
        mm.merge_vertices()
        e = mm.edges_sorted
        _, cnt = np.unique(e, axis=0, return_counts=True)
        comps2 = mm.split(only_watertight=False)
        small = [c for c in comps2 if abs(c.volume) < 0.01]
        print(f"  {name:<16} manifold pieces {len(p.decompose())}, genus {p.genus()}, tris {len(m.faces)}, zero-area tris {deg}; "
              f"as built: {len(comps)} shell(s); verts merged by position: {len(comps2)} shell(s), edges not shared by exactly 2 faces: {(cnt != 2).sum()}")
        for c in small:
            b = c.bounds
            print(f"      stray shell: {len(c.faces)} tris, area {c.area:.5f} mm2, volume {c.volume:.2e}, "
                  f"x {b[0][0]:.3f}..{b[1][0]:.3f} y {b[0][1]:.3f}..{b[1][1]:.3f} z {b[0][2]:.3f}..{b[1][2]:.3f}")
    s = trimesh.load('/home/user/Weave-Trial/fidgets/attempts/joints/' + f)
    e = s.edges_sorted
    _, cnt = np.unique(e, axis=0, return_counts=True)
    print(f"  shipped {f}: watertight {s.is_watertight}, edges not shared by exactly 2 faces {(cnt != 2).sum()} (1 face: {(cnt == 1).sum()}, 3+: {(cnt > 2).sum()}), zero-area tris {(s.area_faces < 1e-10).sum()}")
