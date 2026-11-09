"""What actually stops each joint just past its range (which surfaces meet first)."""
import numpy as np
from common import cb
parts, joints, info = cb.make_capybara()
def show(pose, label):
    p = cb.posed(parts, joints, pose)
    ks = list(p)
    for i, a in enumerate(ks):
        for b in ks[i + 1:]:
            x = p[a] ^ p[b]
            if x.volume() > 1e-6:
                for piece in x.decompose():
                    bb = piece.bounding_box()
                    print(f"  {label}: {a} x {b}: {piece.volume():.3f} mm3 at x {bb[0]:.2f}..{bb[3]:.2f} y {bb[1]:.2f}..{bb[4]:.2f} z {bb[2]:.2f}..{bb[5]:.2f}")
for a in (29.5, 30, 31):
    show({"body joint 2": a}, f"body joint 2 at {a}")
for a in (25.5, 26, 27.5):
    show({"head nod": a}, f"head nod at +{a}")
show({"head nod": -40}, "head nod at -40")
# how far below the bed the head and tab go when nodding (a table would stop it)
for a in (15, -15, 25, -40):
    p = cb.posed(parts, joints, {"head nod": a})
    print(f"  head nod {a:+}: head lowest point z = {p['head'].bounding_box()[2]:.2f}, orange lowest z = {p['orange'].bounding_box()[2]:.2f}")
