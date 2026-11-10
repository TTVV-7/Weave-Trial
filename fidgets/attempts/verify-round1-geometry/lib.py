"""Shared loader and section helpers for the round-1 geometry review.
Loads attempts/joints/make_capybara.py by path, writes nothing into its folder."""
import sys, importlib.util
sys.dont_write_bytecode = True
import numpy as np
import manifold3d as mf

SRC = '/home/user/Weave-Trial/fidgets/attempts/joints/make_capybara.py'
spec = importlib.util.spec_from_file_location("joints_capybara_r1", SRC)
cb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cb)
assert cb.__file__ == SRC


def polys(cs):
    return [np.asarray(p, float) for p in cs.to_polygons()]


def sec_z(m, z):
    """Section z = const as polygons in (x, y)."""
    return polys(m.slice(float(z)))


def sec_y(m, y):
    """Section y = const as polygons in (x, z)."""
    cs = m.rotate([90, 0, 0]).slice(float(y))          # (x, y, z) -> (x, -z, y)
    return [np.c_[p[:, 0], -p[:, 1]] for p in polys(cs)]


def sec_x(m, x):
    """Section x = const as polygons in (y, z)."""
    cs = m.rotate([0, -90, 0]).slice(float(x))         # (x, y, z) -> (-z, y, x)
    return [np.c_[p[:, 1], -p[:, 0]] for p in polys(cs)]


def runs(ps, u0):
    """Runs of solid along the line u = u0 through section polygons (u, v): list of (v_lo, v_hi)."""
    vs = []
    for p in ps:
        a, b = p, np.roll(p, -1, axis=0)
        s = (a[:, 0] - u0) * (b[:, 0] - u0) < 0
        if s.any():
            t = (u0 - a[s, 0]) / (b[s, 0] - a[s, 0])
            vs += list(a[s, 1] + t * (b[s, 1] - a[s, 1]))
    vs = sorted(vs)
    return [(vs[i], vs[i + 1]) for i in range(0, len(vs) - 1, 2)]


def pdist(P, Q):
    """Smallest distance from the vertices of P to the outline Q, and the vertex."""
    A, B = Q, np.roll(Q, -1, axis=0)
    AB = B - A
    L2 = np.maximum((AB ** 2).sum(1), 1e-18)
    t = np.clip(((P[:, None, :] - A[None]) * AB[None]).sum(2) / L2[None], 0, 1)
    N = A[None] + t[..., None] * AB[None]
    D = np.sqrt(((P[:, None, :] - N) ** 2).sum(2)).min(1)
    i = int(np.argmin(D))
    return float(D[i]), P[i]


def loop_gap(a, b):
    """Smallest distance between two outlines (vertex to edge, both ways) and where."""
    d1, p1 = pdist(a, b)
    d2, p2 = pdist(b, a)
    return (d1, p1) if d1 < d2 else (d2, p2)


def area(p):
    x, y = p[:, 0], p[:, 1]
    return 0.5 * float((x * np.roll(y, -1) - np.roll(x, -1) * y).sum())


def inside(p, pt):
    """Is pt inside the closed outline p (even-odd)?"""
    a, b = p, np.roll(p, -1, axis=0)
    c = ((a[:, 1] > pt[1]) != (b[:, 1] > pt[1])) & (pt[0] < (b[:, 0] - a[:, 0]) * (pt[1] - a[:, 1]) / (b[:, 1] - a[:, 1] + 1e-300) + a[:, 0])
    return bool(c.sum() % 2)
