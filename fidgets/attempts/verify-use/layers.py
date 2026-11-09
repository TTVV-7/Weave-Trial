from common import *
objs, colours = pv.read_3mf(J/'pocket-capybara.3mf')
v, f, k = objs[0]
m = trimesh.Trimesh(v, f, process=False)
T = m.triangles; names = ['brown','dark','black','orange']
zmin = T[:,:,2].min(1); zmax = T[:,:,2].max(1)
for h in (0.2, 0.16):
    n = int(np.ceil(m.bounds[1][2]/h))
    used = np.zeros((n, 4), bool); width = np.zeros((n,4))
    for L in range(n):
        z = (L+0.5)*h
        hit = (zmin <= z) & (zmax >= z) & (zmax > zmin + 1e-9)
        for c in range(4):
            sel = hit & (k==c)
            used[L,c] = sel.any()
            if sel.any():
                # outline length of this colour at this height: sum of the chords of each triangle with the plane
                tt = T[sel]; tot = 0
                for tri in tt:
                    pts = []
                    for i in range(3):
                        a, b = tri[i], tri[(i+1)%3]
                        if (a[2]-z)*(b[2]-z) < 0:
                            t = (z-a[2])/(b[2]-a[2]); pts.append(a+(b-a)*t)
                    if len(pts)==2: tot += np.linalg.norm(pts[0]-pts[1])
                width[L,c] = tot
    print('layer height', h, 'layers', n)
    for c in range(4):
        Ls = np.where(used[:,c])[0]
        print('  %-6s in %3d layers, z %.2f..%.2f; layers where its painted outline is under 3 mm long: %d, under 1 mm: %d' % (names[c], len(Ls), Ls.min()*h, (Ls.max()+1)*h, ((width[:,c] < 3) & used[:,c]).sum(), ((width[:,c] < 1) & used[:,c]).sum()))
    cnt = used.sum(1)
    print('  layers with 1/2/3/4 colours:', [(cnt==i).sum() for i in (1,2,3,4)], ' -> filament changes if every colour is loaded once per layer: %d' % (np.maximum(cnt-1,0).sum() + (cnt>0).sum() - 1 if False else np.maximum(cnt,1).sum() - 1))
    # black in detail
    c = 2
    print('  black outline length by layer (mm):', ' '.join('%.1f:%.2f' % ((L+0.5)*h, width[L,c]) for L in range(n) if used[L,c]))
    c = 1
    print('  dark outline length for the top layers:', ' '.join('%.1f:%.1f' % ((L+0.5)*h, width[L,c]) for L in range(n) if used[L,c] and (L+0.5)*h > 15))
    # without the two sliver triangles
    sl = (k==2) & (zmax-zmin > 5)
    print('  black sliver triangles:', sl.sum(), 'spanning z', zmin[sl], zmax[sl], 'x', T[sl][:,:,0].min(1), T[sl][:,:,0].max(1), 'y', T[sl][:,:,1].min(1), T[sl][:,:,1].max(1))
    k2 = k.copy(); k2[sl] = 0
    usedb = np.array([(((zmin <= (L+0.5)*h) & (zmax >= (L+0.5)*h)) & (k2==2)).any() for L in range(n)])
    print('  black layers with slivers %d, without %d' % (used[:,2].sum(), usedb.sum()))
