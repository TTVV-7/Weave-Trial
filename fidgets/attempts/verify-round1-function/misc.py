import sys
sys.path.insert(0, '/home/user/Weave-Trial/fidgets')
import numpy as np, trimesh
from common import cb
J = '/home/user/Weave-Trial/fidgets/attempts/joints/'
parts, joints, info = cb.make_capybara()
tp, tj, ti = cb.make_test()
print("== test strip ==")
print(" parts:", {n: [round(x, 2) for x in p.bounding_box()] for n, p in tp.items()})
print(" joints:", [(j["name"], j["axis"], j["want"], j["stop"], j["beside"]) for j in tj])
# is the strip's hinge the same geometry as the real one?
hb = cb.box(11.5, 30, -6, 6, -1, 20)
d = lambda a, b: ((a - b) + (b - a)).volume()
print(f" head hinge region (x 11.5..30, |y| < 6): strip head vs real head differ by {d(tp['head'] ^ hb, parts['head'] ^ hb):.4f} mm3")
bb = cb.box(0, cb.AXES[0] + 10.5, -30, 30, -1, 30)
print(f" body 1: strip vs real differ by {d(tp['body 1'], parts['body 1']):.4f} mm3 (real body 1 has two leg pins, strip one: right pin volume {(parts['body 1'] ^ cb.box(0, 60, -30, -cb.FLANK - 0.001, -1, 30)).volume():.4f})")
fb = cb.box(0, cb.AXES[0] + 13.9, -30, 30, -1, 30)
print(f" body 2 front (to 13.9 mm behind joint 1): strip vs real differ by {d(tp['body 2'] ^ fb, parts['body 2'] ^ fb):.4f} mm3")
print(f" leg: strip vs real differ by {d(tp['front left leg'], parts['front left leg']):.4f} mm3")
print(" strip has an orange / orange bore:", "orange" in tp, "| strip head volume", round(tp["head"].volume(), 1))
# strip head: how is the stub held and can it be gripped
print("== written STLs reloaded ==")
for f, n in (("pocket-capybara.stl", 10), ("pocket-capybara-test.stl", 4)):
    m = trimesh.load(J + f, process=True)
    sh = m.split(only_watertight=False)
    print(f" {f}: {len(m.faces)} tris, shells {len(sh)} (want {n}), watertight {[bool(s.is_watertight) for s in sh].count(True)}, zero-area {(m.area_faces < 1e-9).sum()}, "
          f"winding ok {m.is_winding_consistent}, volume {m.volume:.1f}, extents {np.round(m.extents, 2).tolist()}")
    model = cb.union((parts if n == 10 else tp).values())
    print(f"   volume of the solids {model.volume():.1f}")
print("== first layers: smallest gap between any two bodies in the slab 0..h ==")
names = list(parts)
for h in (0.1, 0.2, 0.3, 0.4):
    slab = {n: p ^ cb.box(-100, 200, -100, 100, -1, h) for n, p in parts.items()}
    best = (9, None)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            g = slab[a].min_gap(slab[b], 2.0)
            if g < best[0]:
                best = (g, (a, b))
    print(f" h = {h}: {best[0]:.3f} mm between {best[1]}")
