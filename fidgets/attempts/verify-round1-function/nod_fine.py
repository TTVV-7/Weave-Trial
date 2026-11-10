"""Head nod: exact stop angles (0.25 deg), what touches at the stop, how the bite grows past it,
and how far the head gets when its hinge slop (translation inside the clearances) is used too."""
import numpy as np
from common import cb
parts, joints, info = cb.make_capybara()
P = [cb.NECK_X, 0, cb.NECK_Z]
head = parts["head"] + parts["orange"]
rest = cb.union(p for n, p in parts.items() if n not in ("head", "orange"))
b1 = parts["body 1"]
print("as printed: head-body1 gap", round(parts["head"].min_gap(b1, 2.0), 3))
for sign, lab in ((1, "nose up (+)"), (-1, "nose down (-)")):
    stop = None
    for a in np.arange(15, 31, 0.25):
        T = cb.turn(head, "y", P, sign * a)
        if (T ^ rest).volume() > 1e-6:
            stop = a; break
    print(f"{lab}: first overlap at {stop} deg (free to {stop - 0.25})")
    for extra in (0.5, 1.5, 3.0, 6.0, 11.5):
        a = stop + extra
        T = cb.turn(parts["head"], "y", P, sign * a)
        for other in ("body 1", "body 2", "front left leg", "front right leg"):
            X = T ^ parts[other]
            if X.volume() > 1e-6:
                for piece in sorted(X.decompose(), key=lambda q: -q.volume())[:3]:
                    bb = piece.bounding_box()
                    r = np.hypot((bb[0] + bb[3]) / 2 - P[0], (bb[2] + bb[5]) / 2 - P[2])
                    print(f"   at {sign * a:+.2f}: head x {other}: {piece.volume():.3f} mm3, x {bb[0]:.2f}..{bb[3]:.2f} y {bb[1]:.2f}..{bb[4]:.2f} z {bb[2]:.2f}..{bb[5]:.2f}, ~{r:.1f} mm from the axis")
# gap just before each stop: where is the nearest approach
# with slop
H = parts["head"] ^ cb.box(9, 40, -20, 20, -5, 30)
B = b1 ^ cb.box(0, 33, -20, 20, -5, 30)
grid = np.arange(-0.75, 0.751, 0.15)
print("\nwith hinge slop (head also shifted by up to 0.75 mm in x and z, 0 / 0.3 mm in y): largest collision-free nod")
for sign, lab in ((1, "nose up"), (-1, "nose down")):
    best = 0
    for a in np.arange(16, 60, 1.0):
        T = cb.turn(H, "y", P, sign * a)
        ok = None
        for dy in (0.0, 0.3):
            for dx in grid:
                for dz in grid:
                    if (T.translate([dx, dy, dz]) ^ B).volume() < 1e-6:
                        ok = (round(float(dx), 2), dy, round(float(dz), 2)); break
                if ok: break
            if ok: break
        if not ok:
            break
        best = a; how = ok
    print(f"  {lab}: {best} deg (reached with shift dx, dy, dz = {how})", flush=True)
