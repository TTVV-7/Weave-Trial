"""Round 2: true thickness of the socket's lip over each ball, by sampling the two surfaces of the rear
segment: its socket surface (on the 10.6 mm sphere, above the equator, and the 45 degree cone above it)
against every face near it that looks up."""
import numpy as np, trimesh
from scipy.spatial import cKDTree
from lib import *
parts, joints, info = cb.make_capybara()
R = cb.R_BALL + cb.G_SEAM
for i, at in enumerate(info["axes"]):
    rear = parts[f"body {i + 2}"]
    mm = rear.to_mesh()
    V, F = np.asarray(mm.vert_properties)[:, :3].astype(float), np.asarray(mm.tri_verts)
    m = trimesh.Trimesh(V, F, process=False)
    cen, nrm, tri = m.triangles_center, m.face_normals, m.triangles
    d = np.linalg.norm(cen - np.array([at, 0, cb.Z_C]), axis=1)
    sock = (np.abs(d - R) < 0.03) & (cen[:, 2] > cb.Z_C + 0.3) & (nrm[:, 2] < -0.05)
    cone = (nrm[:, 2] < -0.6) & (np.hypot(cen[:, 0] - at, cen[:, 1]) < R) & (cen[:, 2] > cb.Z_C + 5) & (cen[:, 0] > at)
    under = sock | cone
    near = (np.hypot(tri[:, :, 0] - at, tri[:, :, 1]).min(1) < R + 1.5) & (tri[:, :, 0].max(1) > at)
    up = (nrm[:, 2] > 0.15) & (cen[:, 2] > cb.Z_C + 2) & near
    def sample(mask, step):
        v, f = trimesh.remesh.subdivide_to_size(V, F[mask], step)
        return v[np.unique(f)]
    U, T = sample(under, 0.06), sample(up, 0.04)
    T = T[(np.hypot(T[:, 0] - at, T[:, 1]) < R + 1.5)]
    dist, idx = cKDTree(T).query(U)
    k = int(np.argmin(dist))
    print(f"joint {i + 1}: socket surface {under.sum()} faces / {len(U)} points, upper surface {up.sum()} faces / {len(T)} points", flush=True)
    print(f"   lip thickness (socket surface to the nearest face that looks up): {dist[k]:.3f} mm, from x={U[k][0]:.2f} y={U[k][1]:+.2f} z={U[k][2]:.2f} to x={T[idx[k]][0]:.2f} y={T[idx[k]][1]:+.2f} z={T[idx[k]][2]:.2f}")
    for lim in (0.8, 0.9, 1.0):
        print(f"   share of the sampled socket surface under the lip thinner than {lim}: {100 * (dist < lim).mean():.2f}%")
    row = []
    for y0 in np.arange(-8, 8, 2.0):
        s = (U[:, 1] >= y0) & (U[:, 1] < y0 + 2)
        if s.any():
            row.append(f"y {y0:+.0f}..{y0 + 2:+.0f}: {dist[s].min():.2f}")
    print("   thinnest by strip across the body: " + "  ".join(row), flush=True)
