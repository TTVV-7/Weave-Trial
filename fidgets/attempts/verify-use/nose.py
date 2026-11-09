from common import *
objs, colours = pv.read_3mf(J/'pocket-capybara.3mf')
v, f, k = objs[0]
m = trimesh.Trimesh(v, f, process=False)
T = m.triangles; A = m.area_faces; C = m.triangles_center
names = ['BROWN','DARK','BLACK','ORANGE']
front = (T[:,:,0].max(1) < 0.02)
print('flat front face tris', front.sum(), 'area', A[front].sum())
for i in range(4):
    s = front & (k==i)
    if s.sum(): print('  ', names[i], s.sum(), 'area %.2f'%A[s].sum(), 'z range', T[s][:,:,2].min(), T[s][:,:,2].max(), 'y range', T[s][:,:,1].min(), T[s][:,:,1].max())
# brown tris on the front face above mouth
s = front & (k==0) & (C[:,2] > 5.2)
print('brown front-face tris with centroid above NOSE_FROM:', s.sum(), 'area', A[s].sum())
for t in T[s]: print(np.round(t[:,1:],2).tolist())
# dark tris on head: how far do they reach beyond the intended band (x<2.2, z>5.2)
head = (C[:,0] < 3) & (k==1)
print('dark nose tris', head.sum())
below = T[head][:,:,2].min(1)
over_x = T[head][:,:,0].max(1)
print('dark nose triangles with a vertex below z=5.2-0.5:', (below < 4.7).sum(), 'their area', A[head][below<4.7].sum(), 'lowest vertex', below.min())
print('dark nose triangles with a vertex past x=2.2:', (over_x > 2.21).sum(), 'max x', over_x.max())
# brown triangles that intrude into the band: vertex inside x<2.2,z>5.2 region with large area
band = (k==0) & (T[:,:,0].min(1) < 2.2) & (T[:,:,2].max(1) > 5.2) & (C[:,0] < 6)
inside = []
print('brown tris touching the nose band:', band.sum(), 'area', A[band].sum())
# estimate the area of brown inside the band and dark outside the band by sampling
import trimesh.sample
rng = np.random.default_rng(0)
def sample(sel, n=200000):
    idx = np.where(sel)[0]
    p = A[idx]/A[idx].sum()
    pick = rng.choice(idx, n, p=p)
    r1, r2 = rng.random(n), rng.random(n)
    s = np.sqrt(r1)
    pts = (1-s)[:,None]*T[pick,0] + (s*(1-r2))[:,None]*T[pick,1] + (s*r2)[:,None]*T[pick,2]
    return pts, A[idx].sum()
hd = (C[:,0] < 8)
for i in (0,1):
    pts, tot = sample(hd & (k==i))
    inband = (pts[:,0] < 2.2) & (pts[:,2] > 5.2)
    print(names[i], 'head-front area', round(tot,2), 'of which inside intended nose band: %.2f mm2, outside: %.2f mm2' % (tot*inband.mean(), tot*(1-inband.mean())))
    if i==1:
        out = pts[~inband]
        print('   dark outside band: z min %.2f, x max %.2f; area below z<5.2: %.2f; area x>2.2: %.2f' % (out[:,2].min(), out[:,0].max(), tot*((pts[:,2]<5.2).mean()), tot*((pts[:,0]>2.2).mean())))
    else:
        ins = pts[inband]
        print('   brown inside band: y range %.2f..%.2f z %.2f..%.2f x %.2f..%.2f' % (ins[:,1].min(), ins[:,1].max(), ins[:,2].min(), ins[:,2].max(), ins[:,0].min(), ins[:,0].max()))
        # where: front face or sides?
        print('   of which on the flat front face (x<0.02): %.2f mm2' % (tot*(inband & (pts[:,0]<0.02)).mean()))
