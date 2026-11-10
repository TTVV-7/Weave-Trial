"""Independent check of the written STL and 3MF files: no trimesh 'process' clean-up, own
vertex merge by exact float32 position, own edge and shell counting."""
import sys, struct, zipfile, re
sys.dont_write_bytecode = True
import numpy as np
import scipy.sparse as sp, scipy.sparse.csgraph as cg
import manifold3d as mf
from lib import cb
J = '/home/user/Weave-Trial/fidgets/attempts/joints/'


def read_stl(path):
    raw = open(path, 'rb').read()
    n = struct.unpack('<I', raw[80:84])[0]
    assert len(raw) == 84 + 50 * n, (len(raw), n)
    rec = np.frombuffer(raw, dtype=np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]), count=n, offset=84)
    return rec['v'].copy(), rec['n'].copy()


def analyse(tri, label):
    n = len(tri)
    v, inv = np.unique(tri.reshape(-1, 3), axis=0, return_inverse=True)
    f = inv.reshape(-1, 3)
    same = (f[:, 0] == f[:, 1]) | (f[:, 1] == f[:, 2]) | (f[:, 0] == f[:, 2])
    t = v[f].astype(np.float64)
    cr = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    ar = np.linalg.norm(cr, axis=1) / 2
    e = np.sort(t - np.roll(t, 1, axis=1), axis=1)
    L = np.linalg.norm(t - np.roll(t, 1, axis=1), axis=2)
    alt = 2 * ar / np.maximum(L.max(1), 1e-30)          # smallest height of the triangle
    # directed edges: every edge must appear once each way
    de = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
    key = de[:, 0].astype(np.int64) * len(v) + de[:, 1]
    rkey = de[:, 1].astype(np.int64) * len(v) + de[:, 0]
    uk, cnt = np.unique(key, return_counts=True)
    dup_directed = int((cnt > 1).sum())
    unmatched = int((~np.isin(key, uk[np.isin(uk, rkey)])).sum()) if True else 0
    und = np.sort(de, axis=1)
    uu, ucnt = np.unique(und, axis=0, return_counts=True)
    # shells: faces joined across shared edges
    order = np.lexsort((und[:, 1], und[:, 0]))
    so = und[order]
    fo = np.tile(np.arange(n), 3)[order]
    eq = (so[1:] == so[:-1]).all(1)
    a, b = fo[:-1][eq], fo[1:][eq]
    ncomp, comp = cg.connected_components(sp.coo_matrix((np.ones(len(a)), (a, b)), shape=(n, n)), directed=False)
    # shells by shared vertices as well (looser)
    vcomp_n, _ = cg.connected_components(sp.coo_matrix((np.ones(3 * n), (np.repeat(np.arange(n), 3) + 0, f.reshape(-1) + n)),
                                                       shape=(n + len(v), n + len(v))), directed=False)
    print(f"{label}: {n} triangles, {len(v)} distinct corners")
    print(f"   triangles with two corners at the same place: {int(same.sum())}; area < 1e-9 mm2: {int((ar < 1e-9).sum())}; "
          f"area < 1e-6: {int((ar < 1e-6).sum())}; height < 1e-4 mm (needles): {int((alt < 1e-4).sum())}; "
          f"height < 1e-3: {int((alt < 1e-3).sum())}; smallest area {ar.min():.3e}, smallest height {alt.min():.3e}")
    print(f"   edges: {len(uu)}; used by 1 face: {int((ucnt == 1).sum())}, by 2: {int((ucnt == 2).sum())}, by 3+: {int((ucnt > 2).sum())}; "
          f"same edge twice in the same direction: {dup_directed}; directed edges without their opposite: {unmatched}")
    print(f"   shells (faces joined across edges): {ncomp}; (joined through corners): {vcomp_n}")
    # stored normals against the winding
    vols, rows = [], []
    for k in range(ncomp):
        tk = t[comp == k]
        vol = float(np.einsum('ij,ij->i', tk[:, 0], np.cross(tk[:, 1], tk[:, 2])).sum() / 6)
        lo, hi = tk.reshape(-1, 3).min(0), tk.reshape(-1, 3).max(0)
        rows.append((vol, len(tk), lo, hi))
    for vol, nt, lo, hi in sorted(rows, key=lambda r: r[2][0]):
        print(f"      shell: {nt:6d} tris, volume {vol:9.3f} mm3, x {lo[0]:6.2f}..{hi[0]:6.2f} y {lo[1]:6.2f}..{hi[1]:6.2f} z {lo[2]:6.3f}..{hi[2]:6.3f}")
    return v, f, comp, ncomp, rows


for name, maker in (("pocket-capybara", cb.make_capybara), ("pocket-capybara-test", cb.make_test)):
    parts, joints, info = maker()
    tri, nrm = read_stl(J + name + '.stl')
    v, f, comp, ncomp, rows = analyse(tri, name + '.stl')
    t = v[f].astype(np.float64)
    cr = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    ln = np.linalg.norm(cr, axis=1)
    ok = ln > 1e-12
    dots = (cr[ok] / ln[ok, None] * nrm[ok]).sum(1)
    print(f"   stored normals agreeing with the winding: min dot {dots.min():.4f}; zero-length stored normals {int((np.linalg.norm(nrm, axis=1) < 0.5).sum())}")
    print(f"   parts built from the source now: {len(parts)}; shells in file: {ncomp}  -> {'MATCH' if ncomp == len(parts) else 'MISMATCH'}")
    # does each shell equal a part built from the current source?
    whole = cb.union(parts.values())
    lo = np.array(whole.bounding_box()[:3]); hi = np.array(whole.bounding_box()[3:])
    shift = np.array([-lo[0], -(lo[1] + hi[1]) / 2, 0.0])
    pv = sorted((float(p.volume()), n) for n, p in parts.items())
    sv = sorted(r[0] for r in rows)
    print("   part volumes  " + ", ".join(f"{a:.2f}" for a, _ in pv))
    print("   shell volumes " + ", ".join(f"{a:.2f}" for a in sv))
    worst = 0.0
    for k in range(ncomp):
        fk = f[comp == k]
        used, inv = np.unique(fk.reshape(-1), return_inverse=True)
        try:
            m = mf.Manifold(mf.Mesh(vert_properties=np.ascontiguousarray(v[used], dtype=np.float32), tri_verts=np.ascontiguousarray(inv.reshape(-1, 3), dtype=np.uint32)))
            st = m.status()
        except Exception as ex:
            print(f"      shell {k}: manifold3d refuses it: {ex}")
            continue
        if m.is_empty():
            print(f"      shell {k}: manifold3d status {st}: not a valid closed solid")
            continue
        best = None
        for n, p in parts.items():
            q = p.translate(list(shift))
            d = (m - q).volume() + (q - m).volume()
            if best is None or d < best[0]:
                best = (d, n, q.volume())
        worst = max(worst, best[0])
        print(f"      shell {k}: valid solid, genus {m.genus()}; nearest part '{best[1]}': volume outside each other {best[0]:.4f} mm3 of {best[2]:.1f}")
    print(f"   largest difference between a shell and its part: {worst:.4f} mm3")
    # the 3MF
    z = zipfile.ZipFile(J + name + '.3mf')
    txt = z.read('3D/3dmodel.model').decode()
    vv = np.array(re.findall(r'<vertex x="([-0-9.e]+)" y="([-0-9.e]+)" z="([-0-9.e]+)"/>', txt), dtype=np.float64)
    tt = re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)" paint_color="([0-9A-F]+)"/>', txt)
    ff = np.array([[int(a), int(b), int(c)] for a, b, c, _ in tt])
    cols = [c for *_, c in tt]
    print(f"{name}.3mf: objects {txt.count('<object ')}, vertices {len(vv)}, triangles {len(ff)} ({txt.count('<triangle ')} triangle tags), "
          f"paint codes {dict(zip(*np.unique(cols, return_counts=True)))}, z {vv[:, 2].min():.4f}..{vv[:, 2].max():.4f}")
    analyse(vv[ff].astype(np.float32), name + '.3mf mesh')
    print()
