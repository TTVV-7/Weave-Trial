"""Stronger 'nothing can fall off' test: the design pushes each part 1 mm along the six axes only.
Here each part is pushed in 146 directions, as far as it takes, to see if any straight pull frees it,
and how much it bites into its neighbours after 1 mm (weakest direction)."""
import numpy as np
from common import cb

def dirs():
    out = []
    for x in (-1, 0, 1):
        for y in (-1, 0, 1):
            for z in (-1, 0, 1):
                if (x, y, z) != (0, 0, 0):
                    out.append((x, y, z))
    n = 120
    i = np.arange(n) + 0.5
    phi = np.arccos(1 - 2 * i / n); th = np.pi * (1 + 5 ** 0.5) * i
    out += list(np.c_[np.cos(th) * np.sin(phi), np.sin(th) * np.sin(phi), np.cos(phi)])
    d = np.array(out, float)
    return d / np.linalg.norm(d, axis=1)[:, None]

D = dirs()
STEPS = (0.6, 0.8, 1.0, 1.25, 1.5, 2, 3, 4, 6, 8, 12, 16, 24, 40)
for title, maker in (("test strip", cb.make_test), ("pocket capybara", cb.make_capybara)):
    parts, joints, info = maker()
    print(f"=== {title} ===")
    for n, p in parts.items():
        rest = cb.union(q for k, q in parts.items() if k != n)
        free, worst_bite, worst_dir, far = [], (9e9, None), None, (0, None)
        for d in D:
            hit_at = None
            for t in STEPS:
                v = (p.translate(list(t * d)) ^ rest).volume()
                if v > 1e-3:
                    hit_at = t
                    break
            if hit_at is None:
                free.append(d)
                continue
            if hit_at > far[0]:
                far = (hit_at, d)
            bite = (p.translate(list(1.0 * d)) ^ rest).volume()
            if bite < worst_bite[0]:
                worst_bite = (bite, d)
        print(f"  {n:<16} straight pulls that free it: {len(free)} of {len(D)}"
              + (f" e.g. {np.round(free[0], 2)}" if free else "")
              + f"; longest free travel before it catches {far[0]} mm along {np.round(far[1], 2) if far[1] is not None else None}"
              + f"; smallest bite after 1 mm: {worst_bite[0]:.3f} mm3 along {np.round(worst_bite[1], 2) if worst_bite[1] is not None else None}", flush=True)
