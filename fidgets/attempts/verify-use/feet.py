from common import *
objs, colours = pv.read_3mf(J/'pocket-capybara.3mf')
v, f, k = objs[0]
m = trimesh.Trimesh(v, f, process=False)
T = m.triangles; A = m.area_faces; C = m.triangles_center; N = m.face_normals
rng = np.random.default_rng(0)
def sample(sel, n=300000):
    idx = np.where(sel)[0]; p = A[idx]/A[idx].sum(); pick = rng.choice(idx, n, p=p)
    r1, r2 = rng.random(n), rng.random(n); s = np.sqrt(r1)
    return (1-s)[:,None]*T[pick,0] + (s*(1-r2))[:,None]*T[pick,1] + (s*r2)[:,None]*T[pick,2], A[idx].sum(), pick
# front left leg in file coordinates: y 8.9..11.9, x 14.4..25.3
leg = (C[:,1] > 8.85) & (C[:,0] < 26)
outer = leg & (C[:,1] > 8.93)          # not the inner face
print('front-left leg tris', leg.sum(), 'dark', (leg & (k==1)).sum())
for c, nm in ((1,'dark'), (0,'brown')):
    pts, tot, pick = sample(outer & (k==c))
    side = np.abs(N[pick,1]) > 0.9      # the flat outer face
    print('%s on the outer surfaces: %.1f mm2; below z=2.95: %.1f, above: %.1f (reaching z=%.2f / down to z=%.2f)' % (nm, tot, tot*(pts[:,2]<2.95).mean(), tot*(pts[:,2]>=2.95).mean(), pts[:,2].max(), pts[:,2].min()))
    print('     on the flat outer face only: below 2.95: %.1f mm2, above: %.1f mm2' % (tot*((pts[:,2]<2.95)&side).mean(), tot*((pts[:,2]>=2.95)&side).mean()))
# largest triangles on the leg outer face
big = np.where(outer)[0][np.argsort(-A[outer])[:6]]
for i in big: print('   big triangle area %.1f mm2 colour %d z %.2f..%.2f x %.2f..%.2f' % (A[i], k[i], T[i][:,2].min(), T[i][:,2].max(), T[i][:,0].min(), T[i][:,0].max()))
# ears
ear = (k==1) & (C[:,2] > 11) & (C[:,0] > 12) & (C[:,0] < 18) & (C[:,1] > 0)
pts, tot, pick = sample(ear)
print('left ear dark %.1f mm2; of it below z=12.3: %.2f mm2; lowest %.2f' % (tot, tot*(pts[:,2]<12.3).mean(), pts[:,2].min()))
# brown on the ear skin above 12.3: sample brown near ear axis
(x0,x1),(y0,y1),(z0,z1),r0,r1 = cb.EARS[0]
hb = (k==0) & (C[:,2] > 11.5) & (C[:,0] > 12) & (C[:,0] < 18) & (C[:,1] > 3)
pts, tot, pick = sample(hb)
t = np.linspace(0,1,41)[:,None]
d = np.sqrt((pts[:,0]-(x0+(x1-x0)*t))**2 + (pts[:,1]-(y0+(y1-y0)*t))**2 + (pts[:,2]-(z0+(z1-z0)*t))**2) - (r0+(r1-r0)*t)
on = (d.min(0) < 0.05) & (pts[:,2] > 12.3)
print('brown left on the ear skin above z=12.3: %.2f mm2 (z %.2f..%.2f)' % (tot*on.mean(), pts[on,2].min() if on.any() else 0, pts[on,2].max() if on.any() else 0))
# visible ear above the head surface
print('ear tip z %.2f; head top %.2f' % (z1+r1, cb.HEAD_TOP))
# overall size
print('extents', m.extents)
for nm, sel in (('head', C[:,0] < 13), ):
    pass
