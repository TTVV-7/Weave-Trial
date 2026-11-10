"""Round 2: does the back read as one barrel? Height of the top surface along the back, the steps and
grooves at each joint, and the notches in the side silhouette near the bed."""
import numpy as np
import manifold3d as mf
from common import cb
parts, joints, info = cb.make_capybara()
bodies = {n: p for n, p in parts.items() if n.startswith("body")}
U = cb.union(bodies.values())
for y in (0.0, 3.0, 6.0):
    print(f"--- top of the back along y = {y} (x: height, owner) every 0.25 mm near each joint ---")
    for i, at in enumerate(cb.AXES):
        row = []
        prev = None
        steps = []
        for x in np.arange(at + 2.0, at + 11.01, 0.1):
            best = (0, None)
            for n, p in bodies.items():
                c = cb.column(p, float(x), y)
                if c and c[-1][1] > best[0]:
                    best = (c[-1][1], n)
            if prev and best[1] != prev[1]:
                steps.append((round(float(x), 2), prev[1], round(prev[0], 2), best[1], round(best[0], 2)))
            if prev and best[1] == prev[1] and abs(best[0] - prev[0]) > 0.3:
                steps.append((round(float(x), 2), "jump within " + best[1], round(prev[0], 2), "", round(best[0], 2)))
            prev = best
        print(f"   joint {i + 1} (axis x {at}): surface changes hands / jumps at: {steps}")
# the seam seen from above: width of the gap between the segments' top-view outlines
print("--- seen from straight above: open area (bed visible) between neighbouring segments inside the body outline ---")
flat = lambda m: mf.CrossSection(m.project().to_polygons(), mf.FillRule.Positive)
tops = {n: flat(p) for n, p in bodies.items()}
names = list(bodies)
for a, b in zip(names, names[1:]):
    hullab = mf.CrossSection.batch_hull([tops[a], tops[b]])
    gap = hullab - tops[a] - tops[b]
    pcs = sorted(gap.decompose(), key=lambda p: -p.area())[:4]
    print(f"   {a} / {b}: " + ", ".join(f"{p.area():.2f} mm2 at x {p.bounds()[0]:.1f}..{p.bounds()[2]:.1f} y {p.bounds()[1]:.1f}..{p.bounds()[3]:.1f}" for p in pcs if p.area() > 0.05))
# the side silhouette: project on the x-z plane
print("--- seen from the side: holes / notches in the body's silhouette (legs left out) ---")
side = lambda m: mf.CrossSection(m.rotate([90, 0, 0]).project().to_polygons(), mf.FillRule.Positive)     # (x, -z)
S = {n: side(p) for n, p in bodies.items()}
allS = mf.CrossSection.batch_boolean(list(S.values()), mf.OpType.Add)
bx = allS.bounds()
env = mf.CrossSection.batch_hull(list(S.values()))
for a, b in zip(names, names[1:]):
    at = cb.AXES[names.index(a)]
    win = mf.CrossSection.square([14, 30]).translate([at + 1, -30])
    miss = (env ^ win) - allS
    pcs = sorted(miss.decompose(), key=lambda p: -p.area())[:4]
    print(f"   {a} / {b}: " + ", ".join(f"{p.area():.2f} mm2 at x {p.bounds()[0]:.1f}..{p.bounds()[2]:.1f} z {-p.bounds()[3]:.1f}..{-p.bounds()[1]:.1f}" for p in pcs if p.area() > 0.05))
# through-gaps: is there daylight through the body from side to side at a joint (slice at heights)
print("--- gap between segments at the flank (y = FLANK - 0.05) by height: x-width of the opening ---")
for i, at in enumerate(cb.AXES):
    out = []
    for z in (0.1, 0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0, 10.0, 12.0):
        cs = (bodies[f"body {i + 1}"] + bodies[f"body {i + 2}"]).slice(float(z))
        line = cs ^ mf.CrossSection.square([16, 0.04]).translate([at, cb.FLANK - 0.3])
        xs = sorted((p.bounds()[0], p.bounds()[2]) for p in line.decompose())
        gaps = [round(xs[k + 1][0] - xs[k][1], 2) for k in range(len(xs) - 1)]
        out.append(f"z {z}: {gaps}")
    print(f"   joint {i + 1}: " + "; ".join(out))
# overall proportions
hb, ob = parts["head"].bounding_box(), parts["orange"].bounding_box()
print(f"head: x {hb[0]:.1f}..{hb[3]:.1f}, width {hb[4] - hb[1]:.1f}, top {hb[5]:.1f} (ears); body width {2 * cb.FLANK}, back heights: "
      + ", ".join(f"x {x}: {max((c[-1][1] for c in [cb.column(U, x, 0.0)] if c), default=0):.1f}" for x in (18, 22, 26, 30, 34, 38, 42, 46, 50, 54, 58, 60)))
for n in ("front left leg", "hind left leg"):
    b = parts[n].bounding_box()
    print(f"{n}: x {b[0]:.1f}..{b[3]:.1f}, y {b[1]:.1f}..{b[4]:.1f} (flank at {cb.FLANK}), z ..{b[5]:.1f}")
