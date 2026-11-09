from sect import *
from scipy.spatial import cKDTree
parts, joints, info = cb.make_capybara()
def outline_pts(cs, step=0.03):
    out = []
    for p in cs.to_polygons():
        p = np.asarray(p, float); q = np.roll(p, -1, 0)
        for a, b in zip(p, q):
            L = np.linalg.norm(b-a); n = max(1, int(np.ceil(L/step)))
            t = (np.arange(n)+0.5)/n
            out.append(np.c_[a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t, np.full(n, L/n)])
    return np.concatenate(out) if out else np.zeros((0,3))
def surf_pts(m, n):
    mesh = mk.to_mesh(m)
    A = mesh.area_faces; rng = np.random.default_rng(1)
    pick = rng.choice(len(A), n, p=A/A.sum())
    r1, r2 = rng.random(n), rng.random(n); s = np.sqrt(r1)
    T = mesh.triangles[pick]
    pts = (1-s)[:,None]*T[:,0] + (s*(1-r2))[:,None]*T[:,1] + (s*r2)[:,None]*T[:,2]
    return pts, mesh.face_normals[pick], A.sum()/n
pairs = [('body 1','body 2'), ('body 2','body 3'), ('body 3','body 4'), ('body 1','head'), ('head','orange'),
         ('body 1','front left leg'), ('body 4','hind left leg')]
for a, b in pairs:
    A, B = parts[a], parts[b]
    print('== %s  <->  %s  ' % (a, b), flush=True)
    for z in (0.1, 0.3):
        pa, pb = outline_pts(zslice(A, z)), outline_pts(zslice(B, z))
        d, _ = cKDTree(pb[:,:2], balanced_tree=False).query(pa[:,:2], distance_upper_bound=3.0)
        s = '   layer at z=%.1f: smallest gap %.2f mm; length of outline facing the other part within' % (z, d.min())
        for g in (0.45, 0.55, 0.65, 0.85):
            s += '  %.2f mm: %.1f mm' % (g, pa[d<=g, 2].sum())
        print(s)
    # whole-surface facing area
    pa, na, wa = surf_pts(A, 200000); pb, nb, wb = surf_pts(B, 800000)
    d, _ = cKDTree(pb, balanced_tree=False).query(pa, distance_upper_bound=1.0)
    for g in (0.37, 0.45, 0.6):
        near = d <= g
        low = near & (pa[:,2] < 0.45)
        over = near & (np.abs(na[:,2]) > 0.5)     # faces within 30 deg of horizontal... 45-degree faces have |nz| 0.707
        print('   whole surface: %.1f mm2 of %s lies within %.2f mm of %s (of that %.1f mm2 in the bottom two layers; %.1f mm2 on sloping faces |nz|>0.5, z %.1f..%.1f)' % (near.sum()*wa, a, g, b, low.sum()*wa, over.sum()*wa, pa[near,2].min() if near.any() else 0, pa[near,2].max() if near.any() else 0))
