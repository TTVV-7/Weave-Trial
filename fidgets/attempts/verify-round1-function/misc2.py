import sys
sys.path.insert(0, '/home/user/Weave-Trial/fidgets')
import numpy as np, trimesh
from common import cb
parts, joints, info = cb.make_capybara()
tp, tj, ti = cb.make_test()
J = {j["name"]: j for j in joints}
d = lambda a, b: ((a - b) + (b - a)).volume()
hb = cb.box(12.9, 30, -3.0, 3.0, -1, 12.0)
print(f"hinge region proper (x 12.9..30, |y| < 3, z < 12): strip head vs real head differ by {d(tp['head'] ^ hb, parts['head'] ^ hb):.5f} mm3")
fb = cb.box(0, 37.0, -30, 30, -1, 30)
print(f"body 2 in front of x = 37: strip vs real differ by {d(tp['body 2'] ^ fb, parts['body 2'] ^ fb):.5f} mm3")
# the design's own sweep(), at joint angles its check never tries
for phi in (-25, -19, -13, -8, -5, 13):
    for name in ("hind left leg", "hind right leg"):
        j = dict(J[name], step=1)
        free, tight = cb.sweep(parts, joints, j, {"body joint 3": phi})
        print(f"design's sweep(): {name} with body joint 3 at {phi:+}: {cb.spread(free)}  (want 45), tightest gap in range {tight:.3f}")
# paint boundaries in the written 3MF: do they lie on the surfaces they were cut along?
import preview as pv
objs, _ = pv.read_3mf('/home/user/Weave-Trial/fidgets/attempts/joints/pocket-capybara.3mf')
v, f, k = objs[0]
m = trimesh.Trimesh(v, f, process=False)
adj, e = m.face_adjacency, m.face_adjacency_edges
head_lo = parts["head"].bounding_box()[0]
allx = cb.union(parts.values()).bounding_box()
sx = -allx[0]; sy = -(allx[1] + allx[4]) / 2
print("file shift x", round(sx, 4), "y", round(sy, 4))
def edges(c0, c1):
    sel = ((k[adj[:, 0]] == c0) & (k[adj[:, 1]] == c1)) | ((k[adj[:, 0]] == c1) & (k[adj[:, 1]] == c0))
    return e[sel]
ed = edges(0, 1)
pts = v[np.unique(ed)]
paw = pts[pts[:, 2] < 3]
print(f"brown/dark edge at the paws: {len(paw)} corners, z from {paw[:, 2].min():.4f} to {paw[:, 2].max():.4f} (cut plane z = {cb.PAW_Z})")
nose = pts[(pts[:, 0] < 3) & (pts[:, 2] > 5)]
q = ((nose[:, 0] - sx - cb.NOSE_AT[0]) / cb.NOSE[0]) ** 2 + ((nose[:, 1] - sy) / cb.NOSE[1]) ** 2 + ((nose[:, 2] - cb.NOSE_AT[1]) / cb.NOSE[2]) ** 2
print(f"brown/dark edge round the nose pad: {len(nose)} corners, ellipsoid equation value {q.min():.4f}..{q.max():.4f} (1 = exactly on the cut)")
ear = pts[(pts[:, 0] > 10) & (pts[:, 2] > 10) & (pts[:, 0] < 20)]
print(f"brown/dark edge at the ears: {len(ear)} corners, z {ear[:, 2].min():.4f}..{ear[:, 2].max():.4f} (cut plane z = {cb.EAR_FROM})")
for c0, c1, lab in ((0, 2, "brown/black (eyes, mouth)"), (1, 2, "dark/black (nostrils)"), (0, 3, "brown/orange"), (1, 3, "dark/orange (stalk)")):
    ed = edges(c0, c1)
    L = np.linalg.norm(v[ed[:, 0]] - v[ed[:, 1]], axis=1)
    # closed loops?
    deg = np.bincount(ed.ravel())
    print(f"{lab}: {len(ed)} edges, {L.sum():.1f} mm, every corner on exactly 2 boundary edges (clean closed loops): {bool(set(deg[deg > 0]) <= {2})}")
ed = edges(0, 3); p3 = v[np.unique(ed)]
print(f"brown/orange edge on the orange: z {p3[:, 2].min():.3f}..{p3[:, 2].max():.3f}, radius about the shaft {np.hypot(p3[:, 0] - sx - cb.ORANGE_X, p3[:, 1] - sy).min():.3f}..{np.hypot(p3[:, 0] - sx - cb.ORANGE_X, p3[:, 1] - sy).max():.3f}; head top at the bore {info['seat'] + cb.ORANGE_SINK:.2f}, seat {info['seat']:.2f}")
# mouth: width of the black lines
mo = (k == 2) & (m.triangles_center[:, 2] < 8) & (m.triangles_center[:, 0] < 2)
tc = m.triangles[mo].reshape(-1, 3)
print(f"black mouth: y {tc[:, 1].min():.2f}..{tc[:, 1].max():.2f}, z {tc[:, 2].min():.2f}..{tc[:, 2].max():.2f}, area {m.area_faces[mo].sum():.1f} mm2; nose pad area {m.area_faces[(k == 1) & (m.triangles_center[:, 0] < 3) & (m.triangles_center[:, 2] > 5)].sum():.1f}; eyes {m.area_faces[(k == 2) & (m.triangles_center[:, 0] > 5)].sum():.1f}")
