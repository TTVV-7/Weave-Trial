"""Is each part really held in? Not just a 1 mm straight push: a random 'wiggle it out' search.
Each moving group is pulled in 14 directions; at every step it may also shift and tilt a little (6 DOF)
as long as it does not overlap its neighbour. Reports how far the joint centre could be worked along
each pull direction. A held part stalls at about its clearance; a free one keeps going."""
import sys
import numpy as np
from common import cb
G = sys.argv[1]
parts, joints, info = cb.make_capybara()
A = cb.AXES
cases = {
  "orange": (["orange"], ["head"], [cb.ORANGE_X, 0, 8.0]),
  "head": (["head", "orange"], ["body 1"], [cb.NECK_X, 0, cb.NECK_Z]),
  "front leg": (["front left leg"], ["body 1", "body 2"], [cb.LEGS["front"]["x"], cb.FLANK + 1.0, cb.LEG_Z]),
  "hind leg": (["hind left leg"], ["body 4", "body 3"], [cb.LEGS["hind"]["x"], cb.FLANK + 1.0, cb.LEG_Z]),
  "joint 1": (["body 2"], ["body 1"], [A[0], 0, 4.0]),
  "joint 2": (["body 3"], ["body 2"], [A[1], 0, 4.0]),
  "joint 3": (["body 4"], ["body 3"], [A[2], 0, 4.0]),
}
mov, fix, ref = cases[G]
ref = np.array(ref, float)
crop = lambda m, r: m ^ cb.box(ref[0] - r, ref[0] + r, ref[1] - r, ref[1] + r, -5, 40)
M = crop(cb.union(parts[n] for n in mov), 14.0)
F = crop(cb.union(parts[n] for n in fix), 17.0)
rng = np.random.default_rng(1)
def rot(axis, ang):
    axis = axis / np.linalg.norm(axis); K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + np.sin(ang) * K + (1 - np.cos(ang)) * K @ K
def free(R, t):
    T = M.transform(np.c_[R, t].tolist())
    return (T ^ F).volume() < 1e-5
dirs = [np.array(d, float) for d in ([1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1],
        [1,1,0],[1,-1,0],[-1,1,0],[-1,-1,0],[1,0,1],[-1,0,1],[0,1,1],[0,-1,1])]
N = int(sys.argv[2]) if len(sys.argv) > 2 else 220
worst = (0, None)
out = []
for d in dirs:
    d = d / np.linalg.norm(d)
    R, t = np.eye(3), np.zeros(3)
    best = 0.0; tilt = 0.0
    for it in range(N):
        dR = rot(rng.normal(size=3), np.radians(rng.uniform(0, 2.5)))
        step = rng.normal(size=3); step = step / np.linalg.norm(step) * rng.uniform(0, 0.2) + d * rng.uniform(0, 0.15)
        p = R @ ref + t                       # where the joint centre is now
        R2 = dR @ R
        t2 = dR @ (t - p) + p + step          # turn about the joint centre, then shift
        prog2 = (R2 @ ref + t2 - ref) @ d
        prog = (R @ ref + t - ref) @ d
        if prog2 < prog - 0.05:
            continue
        if free(R2, t2):
            R, t = R2, t2
            if prog2 > best:
                best = prog2; tilt = np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1)))
            if best > 6.0:
                break
    out.append((best, d, tilt))
    if best > worst[0]:
        worst = (best, d)
print(f"{G}: joint centre worked along each pull (mm): " + ", ".join(f"{np.round(d, 1).tolist()}: {b:.2f}" for b, d, t in out))
print(f"{G}: FURTHEST {worst[0]:.2f} mm along {np.round(worst[1], 2).tolist()}" + ("   <<< ESCAPES" if worst[0] > 6 else ""))
