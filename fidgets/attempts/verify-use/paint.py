from common import *
import collections
objs, colours = pv.read_3mf(J/'pocket-capybara.3mf')
print('objects', len(objs), 'colours', colours)
v, f, k = objs[0]
m = trimesh.Trimesh(v, f, process=False)
print('bounds', m.bounds, 'extents', m.extents)
names = ['BROWN','DARK','BLACK','ORANGE']
area = m.area_faces
for i,n in enumerate(names):
    print(n, 'tris', (k==i).sum(), 'area mm2 %.2f'%area[k==i].sum())
# bodies
body = pv.components(f, len(v))
ids = sorted(set(body))
print('bodies', len(ids))
# name bodies by centroid
# connected patches per colour: adjacency across shared edges with the same colour
# the mesh is concatenated per part with shared vertices inside a part (manifold output)
adj = m.face_adjacency
same = k[adj[:,0]] == k[adj[:,1]]
import scipy.sparse as sp, scipy.sparse.csgraph as cg
n = len(f)
g = sp.coo_matrix((np.ones(same.sum()), (adj[same,0], adj[same,1])), shape=(n,n))
nc, lab = cg.connected_components(g, directed=False)
print('patches', nc)
rows = []
for c in range(nc):
    sel = lab == c
    cen = (m.triangles_center[sel] * area[sel,None]).sum(0) / area[sel].sum()
    tv = m.triangles[sel].reshape(-1,3)
    rows.append((names[k[sel][0]], sel.sum(), area[sel].sum(), cen, tv.min(0), tv.max(0), body[sel][0]))
rows.sort(key=lambda r: (r[0], -r[2]))
for r in rows:
    print('%-7s tris %5d area %8.3f  centre (%.2f %.2f %.2f)  box x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f body %d' % (r[0], r[1], r[2], *r[3], r[4][0], r[5][0], r[4][1], r[5][1], r[4][2], r[5][2], r[6]))
np.save('patchlab.npy', lab)
