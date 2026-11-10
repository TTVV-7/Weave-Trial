"""2-D map: leg angle x neighbouring body-joint angle. For every joint angle (not only its end stops)
how far can the leg swing each way before it hits the neighbouring segment, and the tightest gap inside +-45."""
import sys
import numpy as np
from common import cb
parts, joints, info = cb.make_capybara()
J = {j["name"]: j for j in joints}
def study(leg, jname, other):
    lj, bj = J[leg], J[jname]
    L = parts[leg]
    # the leg rides on the segment that moves (hind) or stays (front); the "other" segment is the one it can hit
    leg_moves_with_joint = leg in bj["moving"]
    O = parts[other]
    print(f"--- {leg} against {other}, {jname} from -29 to 29 ---")
    worst = (999, None)
    for phi in np.arange(-29, 29.01, 1.0):
        if leg_moves_with_joint:
            Op = cb.turn(O, bj["axis"], bj["point"], -phi)      # same relative pose, leg's segment held still
        else:
            Op = cb.turn(O, bj["axis"], bj["point"], phi)
        Op = Op ^ cb.box(lj["point"][0] - 14, lj["point"][0] + 14, -30, 30, -1, 30)
        res = []
        tight = (9, 0)
        hits = []
        for a in np.arange(-180, 180, 2.5):
            T = cb.turn(L, "y", lj["point"], a)
            v = (T ^ Op).volume()
            if v > 1e-6:
                hits.append((a, v))
            elif abs(a) <= 45:
                g = T.min_gap(Op, 1.0)
                if g < tight[0]:
                    tight = (g, a)
        if hits or tight[0] < 0.3:
            pos = [a for a, v in hits if a > 0]; neg = [a for a, v in hits if a < 0]
            fp = (min(pos) - 2.5) if pos else 180; fn = (-max(neg) - 2.5) if neg else 180
            inwant = [(a, round(v, 3)) for a, v in hits if abs(a) <= 45]
            print(f"  {jname} {phi:+5.1f}: leg free +{fp:g}/-{fn:g}; hits at {len(hits)} of 144 leg angles "
                  f"({min(a for a, v in hits) if hits else ''}..{max(a for a, v in hits) if hits else ''}), max overlap {max([v for a, v in hits], default=0):.3f} mm3; "
                  f"hits inside +-45: {inwant[:4]}; tightest gap inside +-45: {tight[0]:.3f} at {tight[1]:g}", flush=True)
            if min(fp, fn) < worst[0]:
                worst = (min(fp, fn), phi)
    print(f"  => smallest free leg swing over all {jname} angles: {worst[0]} deg at {jname} = {worst[1]}")
which = sys.argv[1]
if which == "hind":
    study("hind left leg", "body joint 3", "body 3")
else:
    study("front left leg", "body joint 1", "body 2")
