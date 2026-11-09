from common import *
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
objs, colours = pv.read_3mf(J/'pocket-capybara.3mf')
v, f, k = objs[0]
rgb = np.array([[int(c[j:j+2],16)/255 for j in (1,3,5)] for c in colours])
m = trimesh.Trimesh(v, f, process=False)
def ortho(ax, axis_from, hx, hy, xlim, ylim, title, flat=True):
    # axis_from: unit vector pointing from the object toward the viewer
    n = m.face_normals
    d = np.array(axis_from, float); d /= np.linalg.norm(d)
    keep = n @ d > 1e-3
    tri = m.triangles[keep]
    depth = tri.mean(1) @ d
    P = np.stack([tri @ np.array(hx, float), tri @ np.array(hy, float)], -1)
    shade = 0.75 + 0.25 * np.clip(n[keep] @ d, 0, 1)
    col = np.clip(rgb[k[keep]] * shade[:, None], 0, 1)
    o = np.argsort(depth)
    ax.add_collection(PolyCollection(P[o], facecolors=col[o], edgecolors=(1,1,1,0.35), linewidths=0.2))
    ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.set_aspect('equal'); ax.set_title(title, fontsize=10)
fig, ax = plt.subplots(2, 3, figsize=(21, 13))
ortho(ax[0,0], [-1,0,0], [0,-1,0], [0,0,1], (-8,8), (-0.5,16), 'face from the front (looking along +x), mm')
ortho(ax[0,1], [0,1,0], [-1,0,0], [0,0,1], (-28,2), (-0.5,21), 'left side of head + front leg (from +y)')
ortho(ax[0,2], [0,1,0], [-1,0,0], [0,0,1], (-63,-48), (-0.5,21), 'left hind leg + loop (from +y)')
ortho(ax[1,0], [0,0,1], [1,0,0], [0,1,0], (-1,22), (-12.5,12.5), 'head from above')
ortho(ax[1,1], [0,0,-1], [1,0,0], [0,-1,0], (-1,63), (-13,13), 'belly (from below, as it sits on the bed)')
ortho(ax[1,2], [-0.6,0.5,0.6], [0.64,0.77,0], [0.46,-0.38,0.8], (-2,18), (0,20), 'head 3/4')
fig.tight_layout(); fig.savefig('closeups.png', dpi=70, facecolor='white')
