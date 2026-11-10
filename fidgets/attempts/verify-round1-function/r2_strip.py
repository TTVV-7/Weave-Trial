"""Round 2: is the test strip's head hinge the real one, and does the strip exercise it?"""
import numpy as np
from common import cb
parts, joints, info = cb.make_capybara()
tp, tj, ti = cb.make_test()
d = lambda a, b: ((a - b) + (b - a)).volume()
print("strip parts:", list(tp), "| strip joints:", [(j["name"], j["moving"], j["want"], j["stop"]) for j in tj])
for x0 in (12.9, 13.7):
    hb = cb.box(x0, 30, -3.0, 3.0, -1, 12.0)
    print(f"hinge region (x {x0}..30, |y| < 3, z < 12): strip head vs real head differ by {d(tp['head'] ^ hb, parts['head'] ^ hb):.5f} mm3; "
          f"strip body 1 vs real body 1 there: {d(tp['body 1'] ^ hb, parts['body 1'] ^ hb):.5f} mm3")
hb = cb.box(13.7, 30, -8, 8, -1, 30)
print(f"whole back of the head (x 13.7..30): strip vs real differ by {d(tp['head'] ^ hb, parts['head'] ^ hb):.4f} mm3")
P = [cb.NECK_X, 0, cb.NECK_Z]
rest = cb.union(p for n, p in tp.items() if n != "head")
for sign, lab in ((1, "nose up"), (-1, "nose down")):
    stop = next(a for a in np.arange(10, 40, 0.25) if (cb.turn(tp["head"], "y", P, sign * a) ^ rest).volume() > 1e-6)
    blocked = all((cb.turn(tp["head"], "y", P, sign * a) ^ rest).volume() > 1e-6 for a in np.arange(stop, 180.1, 2.5))
    print(f"strip head {lab}: free to {stop - 0.25:g} deg, then blocked at every 2.5 deg step out to 180: {blocked}")
b = tp["head"].bounding_box()
print(f"strip head stub: x {b[0]:.1f}..{b[3]:.1f} ({b[3] - b[0]:.1f} long), {b[4] - b[1]:.1f} wide, {b[5]:.1f} tall; bed contact {tp['head'].slice(0.001).area():.0f} mm2; "
      f"in front of the body's drum face it sticks out {cb.NECK_X - cb.R_NOD - b[0]:.1f} mm to hold it by")
