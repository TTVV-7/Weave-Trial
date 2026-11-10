"""Round 2: the socket lip at its blunt front face, exact, in sections x = const just behind the face:
distance from the socket's arc to the outer surface of the segment (the two sides of the lip there)."""
import numpy as np
from lib import *
R = cb.R_BALL + cb.G_SEAM
def seg_dist(P, A, B):
    AB = B - A
    L2 = np.maximum((AB ** 2).sum(1), 1e-18)
    t = np.clip(((P[:, None, :] - A[None]) * AB[None]).sum(2) / L2[None], 0, 1)
    N = A[None] + t[..., None] * AB[None]
    D = np.sqrt(((P[:, None, :] - N) ** 2).sum(2))
    i = np.unravel_index(np.argmin(D), D.shape)
    return float(D[i]), P[i[0]], N[i]
for label, maker in (("full", cb.make_capybara), ("strip", cb.make_test)):
    parts, joints, info = maker()
    for i, at in enumerate(info["axes"]):
        rear = parts[f"body {i + 2}"]
        best = (9,)
        rows = []
        for dx in (0.0005, 0.005, 0.02, 0.05, 0.1, 0.2, 0.3, 0.5, 0.8, 1.2):
            x = at + cb.X_CUT + dx
            rs = np.sqrt(R ** 2 - (x - at) ** 2)
            c = np.array([0.0, cb.Z_C])
            res = (9, None, None)
            for p in sec_x(rear, x):
                d = np.linalg.norm(p - c, axis=1)
                on = (np.abs(d - rs) < 0.03) & (p[:, 1] > cb.Z_C + 1.0)
                if not on.any():
                    continue
                # densify the socket arc
                a, b = p, np.roll(p, -1, axis=0)
                both = on & np.roll(on, -1)
                S = np.vstack([a[both] + t * (b[both] - a[both]) for t in np.linspace(0, 1, 9)]) if both.any() else p[on]
                # outer edges: both ends off the arc, above the equator
                off = (d > rs + 0.05) & (p[:, 1] > cb.Z_C + 1.0)
                e = off & np.roll(off, -1)
                if not e.any():
                    continue
                r_ = seg_dist(S, a[e], b[e])
                if r_[0] < res[0]:
                    res = r_
            if res[1] is not None:
                rows.append(f"{dx:g}: {res[0]:.3f} (y={res[1][0]:+.2f} z={res[1][1]:.2f} -> y={res[2][0]:+.2f} z={res[2][1]:.2f})")
                best = min(best, (res[0], dx))
        print(f"{label} joint {i + 1}: lip between socket arc and outer surface, by distance behind the front face:\n      " + "\n      ".join(rows))
