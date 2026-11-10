"""How much of each leg's hold on its pin is made of feather edges?
1. exact solids: overlap volume and blocked area when the leg is pulled straight off (+y)
2. the same with every layer 'opened' by a nozzle line (anything a 0.4 mm line cannot enter is dropped),
   and with thin-wall printing (drop only what a 0.2 mm disc cannot enter)."""
import sys
import numpy as np
import manifold3d as mf
from lib import *
RJ = mf.JoinType.Round
parts, joints, info = cb.make_capybara()

for name, body_key in (("front left leg", "body 1"), ("hind left leg", "body 4")):
    kind = name.split()[0]
    g = cb.LEGS[kind]
    x0, z0 = g["x"], cb.LEG_Z
    leg, body = parts[name], parts[body_key]
    pinbox = cb.box(x0 - 5, x0 + 5, cb.FLANK + 0.01, cb.FLANK + 4, 0, 20)
    pin = body ^ pinbox
    print(f"{name}: pin head reaches y={pin.bounding_box()[4]:.2f}; leg inner face y={leg.bounding_box()[1]:.2f}")
    # projected onto the plane y = const: what of the pin lies outside the socket's mouth
    def proj(m):
        return mf.CrossSection(m.rotate([90, 0, 0]).project().to_polygons(), mf.FillRule.Positive)
    mouth_slab = (cb.box(x0 - 6, x0 + 6, cb.FLANK + cb.LEG_GAP, cb.FLANK + cb.LEG_GAP + 0.02, z0 - 6, z0 + 6) - leg)
    mouth = mf.CrossSection(mouth_slab.rotate([90, 0, 0]).project().to_polygons(), mf.FillRule.Positive)
    head = proj(pin ^ cb.box(x0 - 6, x0 + 6, cb.FLANK + cb.LEG_GAP, 30, 0, 30))
    blocked = head - mouth
    b = mouth.bounds()
    hb = head.bounds()
    print(f"   exact: socket mouth {b[2] - b[0]:.3f} wide x {b[3] - b[1]:.3f} tall; pin head inside the leg {hb[2] - hb[0]:.3f} wide x {hb[3] - hb[1]:.3f} tall; "
          f"area of the head that cannot pass the mouth {blocked.area():.2f} mm2")
    for s in (0.5, 0.6, 0.8, 1.0, 1.2, 1.6):
        print(f"      leg pulled {s:.1f} mm off sideways: overlap with the body {(leg.translate([0, s, 0]) ^ body).volume():.3f} mm3")
    for LH in (0.2, 0.12):
        for w in (0.4, 0.2):
            zs = np.arange(LH / 2, 12.6, LH)
            tot = {s: 0.0 for s in (0.6, 0.8, 1.0, 1.2, 1.6)}
            lost_pin = lost_leg = 0.0
            win = mf.CrossSection.square([12, 5]).translate([x0 - 6, cb.FLANK + 0.01])
            for z in zs:
                if abs(z - z0) > 4.5:
                    continue
                A = body.slice(float(z)) ^ win
                B = leg.slice(float(z))
                Ao = A.offset(-w / 2, RJ, 2.0, 32).offset(w / 2, RJ, 2.0, 32) ^ A
                Bo = B.offset(-w / 2, RJ, 2.0, 32).offset(w / 2, RJ, 2.0, 32) ^ B
                lost_pin += (A.area() - Ao.area()) * LH
                lost_leg += (B.area() - Bo.area()) * LH
                for s in tot:
                    tot[s] += (Bo.translate([0, s]) ^ Ao).area() * LH
            print(f"   layers {LH} mm, dropping what a {w} mm disc cannot enter: pin loses {lost_pin:.2f} mm3, leg loses {lost_leg:.2f} mm3; overlap when pulled off by "
                  + ", ".join(f"{s}: {v:.3f}" for s, v in tot.items()) + " mm3")
    # the same, how far can the leg be pulled before it first touches (exact)
    lo, hi = 0.0, 2.0
    for _ in range(20):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if (leg.translate([0, mid, 0]) ^ body).volume() < 1e-7 else (lo, mid)
    print(f"   exact: sideways play before the cone seats {lo:.3f} mm")
