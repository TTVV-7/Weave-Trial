"""How far can a joint turn about the axes it is NOT meant to turn about (using all its clearance)?
Random search: small shifts and tilts are accepted while nothing overlaps; the turn about the wanted
axis is pushed as far as it goes. Usage: slop.py case axis sign [tries]"""
import sys
import numpy as np
from common import cb
parts, joints, info = cb.make_capybara()
case, axname, sign = sys.argv[1], sys.argv[2], float(sys.argv[3])
N = int(sys.argv[4]) if len(sys.argv) > 4 else 700
A = cb.AXES
cases = {
  "joint": (["body 2"], ["body 1"], [A[0], 0, 4.0]),
  "head": (["head", "orange"], ["body 1"], [cb.NECK_X, 0, cb.NECK_Z]),
  "leg": (["hind left leg"], ["body 4"], [cb.LEGS["hind"]["x"], cb.FLANK + 1.0, cb.LEG_Z]),
}
mov, fix, ref = cases[case]
ref = np.array(ref, float)
crop = lambda m, r: m ^ cb.box(ref[0] - r, ref[0] + r, -30, 30, -5, 40)
M = crop(cb.union(parts[n] for n in mov), 14.0)
F = crop(cb.union(parts[n] for n in fix), 17.0)
ax = {"x": np.array([1.0, 0, 0]), "y": np.array([0, 1.0, 0]), "z": np.array([0, 0, 1.0])}[axname] * sign
rng = np.random.default_rng(int(abs(hash((case, axname, sign))) % 1000))
def rot(axis, ang):
    axis = axis / np.linalg.norm(axis); K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + np.sin(ang) * K + (1 - np.cos(ang)) * K @ K
def rotvec(R):
    ang = np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1))
    v = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]])
    n = np.linalg.norm(v)
    return v / n * ang if n > 1e-12 else np.zeros(3)
R, t = np.eye(3), np.zeros(3)
best, pose = 0.0, None
for it in range(N):
    a = ax * rng.uniform(0, 1.5) + rng.normal(size=3) * 0.5
    dR = rot(a, np.radians(rng.uniform(0, 1.5)))
    step = rng.normal(size=3); step = step / np.linalg.norm(step) * rng.uniform(0, 0.25)
    p = R @ ref + t
    R2 = dR @ R; t2 = dR @ (t - p) + p + step
    g2, g = np.degrees(rotvec(R2) @ ax), np.degrees(rotvec(R) @ ax)
    if g2 < g - 0.3:
        continue
    if (M.transform(np.c_[R2, t2].tolist()) ^ F).volume() < 1e-5:
        R, t = R2, t2
        if g2 > best:
            best, pose = g2, (np.round(np.degrees(rotvec(R)), 1).tolist(), np.round(R @ ref + t - ref, 2).tolist())
print(f"{case}: turn about {'+' if sign > 0 else '-'}{axname}: {best:.1f} deg (rotation vector deg {pose[0]}, joint centre shifted {pose[1]})")
