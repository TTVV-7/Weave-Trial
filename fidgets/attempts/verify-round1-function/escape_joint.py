"""Follow-up on escape.py: the rear segment of a body joint could be worked 2.4-2.7 mm upwards.
Run the same search longer for the upward pulls, print the pose reached, and see if it comes right out."""
import sys
import numpy as np
from common import cb
parts, joints, info = cb.make_capybara()
at = cb.AXES[0]
ref = np.array([at, 0, 4.0])
crop = lambda m, r: m ^ cb.box(ref[0] - r, ref[0] + r, -30, 30, -5, 40)
M = crop(parts["body 2"], 14.0)       # NB: body 2 cut off 14 mm behind the joint (its own ball is not in play)
F = crop(parts["body 1"], 17.0)
seed, dname = int(sys.argv[1]), sys.argv[2]
d = {"up": np.array([0, 0, 1.0]), "upback": np.array([1, 0, 1.0]), "upfwd": np.array([-1, 0, 1.0]), "back": np.array([1.0, 0, 0])}[dname]
d = d / np.linalg.norm(d)
rng = np.random.default_rng(seed)
def rot(axis, ang):
    axis = axis / np.linalg.norm(axis); K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + np.sin(ang) * K + (1 - np.cos(ang)) * K @ K
def vol(R, t):
    return (M.transform(np.c_[R, t].tolist()) ^ F).volume()
R, t = np.eye(3), np.zeros(3)
best = 0
for it in range(int(sys.argv[3])):
    dR = rot(rng.normal(size=3), np.radians(rng.uniform(0, 2.5)))
    step = rng.normal(size=3); step = step / np.linalg.norm(step) * rng.uniform(0, 0.25) + d * rng.uniform(0, 0.2)
    p = R @ ref + t
    R2 = dR @ R; t2 = dR @ (t - p) + p + step
    prog2 = (R2 @ ref + t2 - ref) @ d; prog = (R @ ref + t - ref) @ d
    if prog2 < prog - 0.05:
        continue
    if vol(R2, t2) < 1e-5:
        R, t = R2, t2
        if prog2 > best + 0.5 or prog2 > 12:
            best = prog2
            ang = np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1)))
            ax = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]]); ax = ax / (np.linalg.norm(ax) + 1e-12)
            print(f"  it {it}: joint centre moved {np.round(R @ ref + t - ref, 2).tolist()}, turned {ang:.1f} deg about {np.round(ax, 2).tolist()}", flush=True)
        if prog2 > 12:
            print(f"seed {seed} {dname}: OUT - joint centre is 12 mm away, min gap to body 1 now {M.transform(np.c_[R, t].tolist()).min_gap(F, 5.0):.2f}")
            np.save(f"escape_pose_{dname}_{seed}.npy", np.c_[R, t])
            break
else:
    print(f"seed {seed} {dname}: stalled at {best:.2f} mm after {sys.argv[3]} tries")
