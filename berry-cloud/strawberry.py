"""Detailed strawberry for a three-colour print on the Snapmaker U1.

Three parts that fit together without overlapping, one per toolhead:
  body   red    rounded, slightly lumpy berry with a pit for every seed and a
                sunken top where the leaves sit; a small flat on the tip so it
                stands on the bed
  seeds  yellow ~250 little seeds, each lying in its pit, pointing to the tip
  leaves green  two rings of serrated leaves with a raised midrib, lying on the
                shoulders, plus a tapered, slightly bent stem
"""
import math
import numpy as np
import trimesh
from shapely.geometry import Polygon
import manifold3d as m3
from scipy.spatial import cKDTree

H = 205.0           # body height (with the stem the berry is ~9" / 229 mm)
W = 190.0           # 7.5"
FLAT = 5.0          # mm cut off the tip so it sits on the bed
DIMPLE = 9.0        # how far the top sinks around the stem
SEG = 192
SEED_GAP = 12.5     # centre-to-centre seed spacing
rng = np.random.default_rng(7)


def man(mesh):
    return m3.Manifold(m3.Mesh(vert_properties=np.asarray(mesh.vertices, np.float32),
                               tri_verts=np.asarray(mesh.faces, np.uint32)))


def tri(mf):
    m = mf.to_mesh()
    out = trimesh.Trimesh(m.vert_properties[:, :3], m.tri_verts)
    return out


def drop_slivers(mesh):
    """Booleans leave a few zero-volume crumbs where three parts meet."""
    keep = [p for p in mesh.split(only_watertight=False) if abs(p.volume) > 1.0]
    return trimesh.util.concatenate(keep)


# ---- body -------------------------------------------------------------------
def profile(u):
    """Radius at height fraction u: rounded tip, widest ~60 % up, soft shoulders."""
    p = math.log(0.5) / math.log(0.6)
    r = (W / 2) * np.sin(np.pi * np.clip(u, 0, 1) ** p) ** 0.42
    tip = np.clip(u / 0.12, 0, 1)
    return r * np.sqrt(tip * (2 - tip)) ** 0.7


def lumps(theta, u):
    """Gentle irregular bulges, fading out under the leaves and at the tip."""
    fade = np.sin(np.pi * u) * (1 - np.clip((u - 0.72) / 0.15, 0, 1))
    return 1 + fade * (0.025 * np.sin(3 * theta + 0.6) + 0.018 * np.sin(5 * theta + 2.1 + 4 * u)
                       + 0.012 * np.sin(7 * theta - 1.3))


def dimple(rho):
    return DIMPLE * np.exp(-(rho / 38.0) ** 2)


def body_solid():
    u = np.linspace(0, 1, 260)[1:-1]
    th = np.linspace(0, 2 * np.pi, SEG, endpoint=False)
    U, T = np.meshgrid(u, th, indexing="ij")
    R = profile(U) * lumps(T, U)
    Z = U * H - dimple(R) * (U > 0.75)
    v = np.c_[(R * np.cos(T)).ravel(), (R * np.sin(T)).ravel(), Z.ravel()]
    zb = 0.0
    zt = H - DIMPLE
    v = np.vstack([[0, 0, zb], v, [0, 0, zt]])
    n, f = len(u), []
    idx = lambda i, j: 1 + i * SEG + j % SEG
    for j in range(SEG):
        f.append([0, idx(0, j + 1), idx(0, j)])
        for i in range(n - 1):
            f += [[idx(i, j), idx(i, j + 1), idx(i + 1, j + 1)], [idx(i, j), idx(i + 1, j + 1), idx(i + 1, j)]]
        f.append([idx(n - 1, j), idx(n - 1, j + 1), len(v) - 1])
    mesh = trimesh.Trimesh(v, f)
    mesh.fix_normals()
    return mesh


def top_z(rho):
    """Height of the upper surface at radius rho (the top has no lumps)."""
    u = np.linspace(0.6, 1, 400)
    r = profile(u)
    z = u * H - dimple(r)
    return np.interp(rho, r[::-1], z[::-1])


# ---- leaves -----------------------------------------------------------------
def leaf_outline(length, width, teeth=5):
    """One leaf pointing along +x from the origin, with small serrations."""
    s = np.linspace(0, 1, 80)
    half = width / 2 * np.sin(np.pi * s ** 0.8) ** 0.9
    saw = 1 - 0.18 * np.abs(((s * teeth * 2) % 2) - 1) * (s > 0.25) * (s < 0.95)
    top = np.c_[s * length, half * saw]
    bot = np.c_[s[::-1] * length, -half[::-1] * saw[::-1]]
    return Polygon(np.vstack([top, bot]))


def drape(mesh, base, curl):
    """Lay a flat part over the berry's top, tips lifting slightly."""
    v = mesh.vertices.copy()
    rho = np.hypot(v[:, 0], v[:, 1])
    v[:, 2] += top_z(rho) - 0.4 + base + curl * np.clip((rho - 55) / 25, 0, 1) ** 2
    return trimesh.Trimesh(v, mesh.faces)


def leaves_solid():
    parts = []
    rings = [(7, 66.0, 30.0, 0.0, 2.6), (7, 50.0, 24.0, np.pi / 7, 2.6)]   # outer, inner
    for k, (n, L, Wd, off, T) in enumerate(rings):
        for i in range(n):
            a = off + 2 * np.pi * i / n + rng.uniform(-0.12, 0.12)
            Li = L * rng.uniform(0.88, 1.08)
            leaf = trimesh.creation.extrude_polygon(leaf_outline(Li, Wd * rng.uniform(0.9, 1.1)), T)
            rib = trimesh.creation.extrude_polygon(
                Polygon([(4, -1.6), (Li * 0.85, -0.4), (Li * 0.85, 0.4), (4, 1.6)]), 1.0)
            rib.apply_translation((0, 0, T - 0.1))
            for m in (leaf, rib):
                m.apply_translation((10, 0, 0))
                m.apply_transform(trimesh.transformations.rotation_matrix(a, (0, 0, 1)))
            leaf = leaf.subdivide_to_size(3.0)
            rib = rib.subdivide_to_size(3.0)
            curl = 2.0 if k == 0 else 1.0
            lift = 0.0 if k == 0 else 1.5          # inner ring lies on the outer one
            parts += [drape(leaf, lift, curl), drape(rib, lift, curl)]
    # stem: tapered, bent a little, with a ring where it meets the leaves
    zs = top_z(0) + 1
    ring = trimesh.creation.cylinder(radius=13, height=5, sections=64)
    ring.apply_translation((0, 0, zs + 1.5))
    t = np.linspace(0, 1, 30)
    path = np.c_[6 * t ** 2, np.zeros_like(t), zs + 3 + 28 * t]
    circ = [(np.cos(a), np.sin(a)) for a in np.linspace(0, 2 * np.pi, 40, endpoint=False)]
    rings_v = []
    for p, tt in zip(path, t):
        r = 6.5 - 2.0 * tt
        rings_v.append([(p[0] + r * c, p[1] + r * s, p[2]) for c, s in circ])
    stem = trimesh.convex.convex_hull(np.vstack(rings_v[:15]))
    stem2 = trimesh.convex.convex_hull(np.vstack(rings_v[14:]))
    out = man(ring) + man(stem) + man(stem2)
    for p in parts:
        out = out + man(p)
    return out


# ---- seeds ------------------------------------------------------------------
def seed_frames(body):
    """Even spots over the visible red surface, with an outward normal and a
    'down the berry' direction for each."""
    cand, cfid = trimesh.sample.sample_surface(body, 60000, seed=3)
    tree, taken = cKDTree(cand), np.zeros(len(cand), bool)
    keep_i = []
    for i in range(len(cand)):                # greedy Poisson-disc thinning
        if not taken[i]:
            keep_i.append(i)
            taken[tree.query_ball_point(cand[i], SEED_GAP)] = True
    pts, fid = cand[keep_i], cfid[keep_i]
    nrm = body.face_normals[fid]
    rho = np.hypot(pts[:, 0], pts[:, 1])
    under_leaves = (rho < 82) & (pts[:, 2] > top_z(82) - 3)
    keep = (pts[:, 2] > FLAT + 10) & ~under_leaves
    pts, nrm = pts[keep], nrm[keep]
    down = np.array([0, 0, -1.0]) - nrm * (nrm @ np.array([0, 0, -1.0]))[:, None]
    down /= np.linalg.norm(down, axis=1)[:, None]
    return pts, nrm, down


def ellipsoid(c, x, z, axes):
    s = m3.Manifold.sphere(1.0, 24).scale(axes)
    y = np.cross(z, x)
    M = np.c_[x, y, z, c].astype(float)      # 3x4 affine
    return s.transform(M.tolist())


def inner_solid(body, wall):
    """The cavity: the smooth body pushed in along its normals by the wall
    thickness, with a floor left above the flat foot."""
    inner = trimesh.Trimesh(body.vertices - body.vertex_normals * wall, body.faces)
    floor = m3.Manifold.cube((400, 400, FLAT + wall), True).translate((0, 0, (FLAT + wall) / 2))
    return man(inner) - floor


def strawberry(wall=None):
    """The three parts, solid, or hollow with a `wall`-mm shell."""
    body = body_solid()
    pts, nrm, down = seed_frames(body)
    pits, seeds = [], []
    for p, n, d in zip(pts, nrm, down):
        tw = rng.uniform(-0.25, 0.25)              # small random twist
        x = d * math.cos(tw) + np.cross(n, d) * math.sin(tw)
        pits.append(ellipsoid(p + n * 0.9, x, n, (4.6, 3.2, 2.2)))
        seeds.append(ellipsoid(p - n * 0.6, x, n, (3.0, 1.7, 1.25)))
    pits = m3.Manifold.batch_boolean(pits, m3.OpType.Add)
    seeds = m3.Manifold.batch_boolean(seeds, m3.OpType.Add)
    leaves = leaves_solid()
    flat = m3.Manifold.cube((400, 400, FLAT), True).translate((0, 0, FLAT / 2 - 0.001))
    red = man(body) - pits - seeds - leaves - flat
    if wall:
        red = red - inner_solid(body, wall)
    seeds = seeds - flat
    shift = (0, 0, -FLAT)
    return {"strawberry-body": drop_slivers(tri(red.translate(shift))),
            "strawberry-seeds": tri(seeds.translate(shift)),
            "strawberry-leaves": drop_slivers(tri(leaves.translate(shift)))}, len(pts)
