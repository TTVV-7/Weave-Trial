"""How deep does the hind leg bite into body 3's ball corner (found in leg_map)? And where."""
import numpy as np
from common import cb
parts, joints, info = cb.make_capybara()
J = {j["name"]: j for j in joints}
L, B3 = parts["hind left leg"], parts["body 3"]
lj, bj = J["hind left leg"], J["body joint 3"]
print("hind leg pin x", lj["point"][0], "joint 3 axis x", bj["point"][0], "ball radius", cb.R_BALL, "flank", cb.FLANK, "leg inner face y", cb.FLANK + cb.LEG_GAP)
for phi, a in ((-13, 30), (-13, 45), (-13, 60), (-13, 90), (-8, 45), (-18, 45), (-25, 80), (-25, 27.5), (-25, 45)):
    O = cb.turn(B3, "z", bj["point"], -phi)
    T = cb.turn(L, "y", lj["point"], a)
    X = T ^ O
    msg = f"joint 3 {phi:+}, leg {a:+}: overlap {X.volume():.3f} mm3"
    if X.volume() > 1e-6:
        bb = X.bounding_box()
        msg += f" at x {bb[0]:.2f}..{bb[3]:.2f} y {bb[1]:.2f}..{bb[4]:.2f} z {bb[2]:.2f}..{bb[5]:.2f}"
        for dy in np.arange(0.05, 2.0, 0.05):          # how far must the leg be pushed outwards to clear
            if (T.translate([0, dy, 0]) ^ O).volume() < 1e-6:
                msg += f"; clears if the leg moves {dy:.2f} mm outwards"
                break
    else:
        msg += f"; gap {T.min_gap(O, 2.0):.3f}"
    print(msg)
# the leg's own free play outwards on its pin
B4 = parts["body 4"]
for dy in np.arange(0.05, 1.5, 0.05):
    if (L.translate([0, dy, 0]) ^ B4).volume() > 1e-6:
        print(f"the leg's own play outwards on its pin: {dy - 0.05:.2f} mm"); break
# same question for 1 deg steps of leg angle at the worst joint angle: the true first-hit angle
for phi in (-6, -10, -14, -18, -20):
    O = cb.turn(B3, "z", bj["point"], -phi)
    for a in np.arange(15, 60, 0.5):
        if (cb.turn(L, "y", lj["point"], a) ^ O).volume() > 1e-6:
            print(f"joint 3 at {phi}: leg first touches body 3 at +{a} deg"); break
