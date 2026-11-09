from common import *
objs, colours = pv.read_3mf(J/'pocket-capybara.3mf')
v, f, k = objs[0]
m = trimesh.Trimesh(v, f, process=False)
T = m.triangles
for z in (3.0, 4.5, 5.5, 6.5, 8.0):
    segs = []
    for i in np.where((T[:,:,2].min(1) < z) & (T[:,:,2].max(1) > z) & (T[:,:,0].min(1) < 3.0) & (T[:,:,1].min(1) > 0))[0]:
        tri = T[i]; pts = []
        for a in range(3):
            p, q = tri[a], tri[(a+1)%3]
            if (p[2]-z)*(q[2]-z) < 0:
                t = (z-p[2])/(q[2]-p[2]); pts.append(p+(q-p)*t)
        if len(pts)==2 and min(pts[0][0], pts[1][0]) < 2.2 and m.face_normals[i][0] < 0.2:
            mid = (pts[0]+pts[1])/2
            segs.append((np.arctan2(mid[1]-3.3, -(mid[0]-2.8)), np.linalg.norm(pts[0]-pts[1]), k[i], mid))
    segs.sort(key=lambda s: s[0])
    cols = [s[2] for s in segs]
    trans = sum(1 for a, b in zip(cols, cols[1:]) if a != b)
    dark = sum(s[1] for s in segs if s[2]==1); brown = sum(s[1] for s in segs if s[2]==0); black = sum(s[1] for s in segs if s[2]==2)
    widths = [s[1] for s in segs if s[2] in (0,1)]
    print('z=%.1f left half of the muzzle front, x<2.2: %d pieces of outline, %d colour changes along it; dark %.2f mm, brown %.2f mm, black %.2f mm; median piece %.2f mm' % (z, len(segs), trans, dark, brown, black, np.median(widths)))
