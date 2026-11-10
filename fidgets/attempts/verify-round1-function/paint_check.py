"""Read the written 3MFs back with the project's own preview.read_3mf and audit the paint."""
import sys
sys.path.insert(0, '/home/user/Weave-Trial/fidgets')
import numpy as np, trimesh
import scipy.sparse as sp, scipy.sparse.csgraph as cg
import preview as pv
J = '/home/user/Weave-Trial/fidgets/attempts/joints/'
NAMES = ["T1 brown", "T2 dark", "T3 black", "T4 orange"]
for f in ("pocket-capybara.3mf", "pocket-capybara-test.3mf"):
    objs, colours = pv.read_3mf(J + f)
    print(f"=== {f}: {len(objs)} object(s), colours {colours}")
    for v, fc, k in objs:
        m = trimesh.Trimesh(v, fc, process=False)
        print(f"  {len(v)} verts {len(fc)} tris; watertight {m.is_watertight}; bounds {np.round(m.bounds, 2).tolist()}; zero-area tris {(m.area_faces < 1e-9).sum()}; "
              f"min tri area {m.area_faces.min():.2e}")
        bodies = m.split(only_watertight=False)
        print(f"  shells {len(bodies)}; all watertight {all(b.is_watertight for b in bodies)}")
        for c in range(4):
            print(f"    {NAMES[c]}: {int((k == c).sum())} tris, {m.area_faces[k == c].sum():.1f} mm2")
        adj = m.face_adjacency
        same = adj[k[adj[:, 0]] == k[adj[:, 1]]]
        n = len(fc)
        cnt, patch = cg.connected_components(sp.coo_matrix((np.ones(len(same)), (same[:, 0], same[:, 1])), shape=(n, n)), directed=False)
        areas = np.bincount(patch, weights=m.area_faces, minlength=cnt)
        print(f"  {cnt} patches; smallest {areas.min():.3f} mm2; under 1 mm2: {(areas < 1).sum()}")
        order = np.argsort(areas)
        for p in order:
            sel = patch == p
            if k[sel][0] == 0 and areas[p] > 50:
                continue
            tc = m.triangles_center[sel]
            lo, hi = tc.min(0), tc.max(0)
            print(f"    patch {NAMES[k[sel][0]]:<10} {areas[p]:8.2f} mm2  {sel.sum():5d} tris  x {lo[0]:6.2f}..{hi[0]:6.2f} y {lo[1]:6.2f}..{hi[1]:6.2f} z {lo[2]:6.2f}..{hi[2]:6.2f}")
        # colour edges: length and straightness; thin triangles along boundaries
        diff = adj[k[adj[:, 0]] != k[adj[:, 1]]]
        e = m.face_adjacency_edges[k[adj[:, 0]] != k[adj[:, 1]]]
        L = np.linalg.norm(v[e[:, 0]] - v[e[:, 1]], axis=1)
        print(f"  colour boundary: {len(e)} edges, total {L.sum():.1f} mm, shortest {L.min():.4f}, median {np.median(L):.3f}")
        # slivers: triangles whose min altitude < 0.01
        t = m.triangles
        el = np.stack([np.linalg.norm(t[:, i] - t[:, (i + 1) % 3], axis=1) for i in range(3)], 1)
        alt = 2 * m.area_faces / el.max(1)
        print(f"  needle triangles (altitude < 0.005 mm): {(alt < 0.005).sum()}, (<0.001): {(alt < 0.001).sum()}")
        np.savez("/tmp/claude-0/-home-user-Weave-Trial/3f840893-e9bb-5631-9c37-1d0c4389d23e/scratchpad/" + f + ".npz", v=v, f=fc, k=k, patch=patch)
