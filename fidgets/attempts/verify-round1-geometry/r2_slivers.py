"""Round 2: every bit of every 0.2 mm layer narrower than one 0.4 mm line (and narrower than 0.8), listed by place,
so that feather edges and fins can be told apart from walls. Also: sections through the keyring scoops' rims."""
import numpy as np, manifold3d as mf
from lib import *
RJ = mf.JoinType.Round
parts, joints, info = cb.make_capybara()
for name in ("head", "body 1", "body 2", "body 4", "front left leg", "hind left leg", "orange"):
    m = parts[name]
    top = m.bounding_box()[5]
    for w in (0.4, 0.8):
        found = []
        for z in np.arange(0.1, top, 0.2):
            cs = m.slice(float(z))
            thin = cs - cs.offset(-w / 2, RJ, 2.0, 64).offset(w / 2 + 0.02, RJ, 2.0, 64)
            for p in thin.decompose():
                if p.area() > (0.03 if w == 0.4 else 0.15):
                    b = p.bounds()
                    found.append((round(float(z), 2), p.area(), b))
        # group by place (rounded centre) so that a feature running through many layers is one line
        groups = {}
        for z, a, b in found:
            key = (round((b[0] + b[2]) / 2 / 1.5), round((b[1] + b[3]) / 2 / 1.5))
            groups.setdefault(key, []).append((z, a, b))
        print(f"{name}: narrower than {w}: {len(found)} bits in {len(groups)} places")
        for key, g in sorted(groups.items(), key=lambda kv: -sum(a for _, a, _ in kv[1])):
            zs = [z for z, _, _ in g]
            tot = sum(a for _, a, _ in g) * 0.2
            x0, y0 = min(b[0] for _, _, b in g), min(b[1] for _, _, b in g)
            x1, y1 = max(b[2] for _, _, b in g), max(b[3] for _, _, b in g)
            if tot > 0.05:
                print(f"     z {min(zs):.1f}..{max(zs):.1f} ({len(g)} layers), {tot:.3f} mm3, x {x0:.2f}..{x1:.2f} y {y0:+.2f}..{y1:+.2f}")
b4 = parts["body 4"]
print("\nkeyring scoops: sections y = const through the scoop, outline of the back near the eye (x, z) for x 53..61, z > 12")
for y in (3.0, 4.5, 6.0, 7.0, 7.6, 8.0):
    for p in sec_y(b4, y):
        s = (p[:, 0] > 53.0) & (p[:, 0] < 61.5) & (p[:, 1] > 12.0)
        if s.any():
            q = p[s]
            print(f"   y={y}: " + " ".join(f"({a:.2f},{b:.2f})" for a, b in q[:: max(1, len(q) // 28)]))
print("sections x = const through the scoop (y, z), y 2..9, z > 11.5")
for x in (54.6, 55.5, 56.6, 57.7, 58.6):
    for p in sec_x(b4, x):
        s = (p[:, 0] > 2.0) & (p[:, 0] < 9.9) & (p[:, 1] > 11.5)
        if s.any():
            q = p[s]
            print(f"   x={x}: " + " ".join(f"({a:.2f},{b:.2f})" for a, b in q[:: max(1, len(q) // 28)]))
