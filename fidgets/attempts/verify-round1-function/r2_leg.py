"""Round 2: the new leg pin, measured independently of the design's own leg_hold().
 (a) the pin's section all the way from the recess floor to the flange's end: bbox, area, largest inscribed circle
 (b) where the flange stands over the lip (angle round the axis), with the leg as printed and swung
 (c) pull-off: play and interference volume for the leg at swing angles 0..180, pulled straight and pulled askew
 (d) bed contact"""
import numpy as np
import manifold3d as mf
from common import cb
parts, joints, info = cb.make_capybara()
floor, face, land, lip, f0, f1, end, out = cb.leg_stations()
rn, bore, rf, rc = cb.leg_radii()
print(f"stations (y, left side): recess floor {floor:.2f}, boss face {face:.2f}, land {land:.2f}, lip outer face {lip:.2f}, flange {f0:.2f}..{f1:.2f}, socket end {end:.2f}, leg outer face {out:.2f}")
print(f"radii: neck {rn:.3f}, bore {bore:.3f}, flange {rf:.3f}, socket {rc:.3f}")

def inscribed(cs):
    """Diameter of the largest circle that fits in a section (bisection on erosion)."""
    lo, hi = 0.0, 5.0
    for _ in range(14):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if cs.offset(-mid, mf.JoinType.Round, 2.0, 64).area() > 1e-6 else (lo, mid)
    return 2 * lo

for kind, bname, lname in (("front", "body 1", "front left leg"), ("hind", "body 4", "hind left leg")):
    x = cb.LEGS[kind]["x"]
    body, leg = parts[bname], parts[lname]
    print(f"\n=== {kind} leg, pin at x {x}, z {cb.LEG_Z} ===")
    print("(a) pin section at y: bbox x-extent, z-extent, area, largest inscribed circle dia, lowest point below axis")
    for y in [floor + 0.01, face, land + 0.01, (land + lip) / 2, lip, lip + 0.1, lip + 0.2, lip + 0.3, f0 - 0.01, f0 + 0.01, (f0 + f1) / 2, f1 - 0.01]:
        cs = cb.piece_at(cb.section_y(body, y) ^ mf.CrossSection.square([12, 12]).translate([x - 6, -cb.LEG_Z - 6]), x, -cb.LEG_Z - 0.6)
        if cs.is_empty():
            print(f"   y {y:.2f}: nothing"); continue
        b = cs.bounds()
        print(f"   y {y:.2f} ({y - cb.FLANK:+.2f} from the flank): {b[2] - b[0]:.2f} x {b[3] - b[1]:.2f}, {cs.area():.2f} mm2, inscribed {inscribed(cs):.2f}, bottom {-(b[3]) - cb.LEG_Z:+.2f}, top {-(b[1]) - cb.LEG_Z:+.2f}")
    # (b) the flange and the lip, seen along the pin
    fl = cb.section_y(body, (f0 + f1) / 2) ^ mf.CrossSection.square([12, 12]).translate([x - 6, -cb.LEG_Z - 6])
    lp = cb.section_y(leg, (land + lip) / 2)                                  # the lip (solid of the leg round its bore)
    hole = (mf.CrossSection.circle(6, 64).translate([x, -cb.LEG_Z]) - lp)     # the bore as the flange sees it
    hole = cb.piece_at(hole, x, -cb.LEG_Z)
    over = fl - hole
    print(f"(b) flange section {fl.area():.2f} mm2; bore {hole.area():.2f} mm2 (round bore would be {np.pi * bore ** 2:.2f}); flange standing over the lip {over.area():.2f} mm2 "
          f"(a full ring would be {np.pi * (rf ** 2 - bore ** 2):.2f})")
    ang = []
    for a in np.arange(-180, 180, 5.0):
        ray = mf.CrossSection([[(0, -0.02), (8, -0.02), (8, 0.02), (0, 0.02)]]).rotate(a).translate([x, -cb.LEG_Z])
        seg = over ^ ray
        ang.append((a, 0.0 if seg.is_empty() else seg.area() / 0.04))
    # section_y is (x, -z): angle a measured from +x towards -z, so 'up' is a = -90
    up = [(-(a) , w) for a, w in ang]
    held = sorted(a for a, w in up if w > 0.3)
    print("    radial overlap of flange over lip by direction (deg from horizontal-forward... 90 = straight up): "
          + ", ".join(f"{a:g}:{w:.2f}" for a, w in sorted(up) if -1 <= a <= 181 and a % 15 == 0))
    print(f"    directions with more than 0.3 mm of overlap: {held[0] if held else None}..{held[-1] if held else None} deg ({len(held) * 5} of 360)")
    # (c) pull-off at swing angles
    j = next(k for k in joints if k["name"] == lname)
    win = cb.box(x - 9, x + 9, cb.FLANK - 3, cb.FLANK + 6, -2, 20)
    B = body ^ win
    print("(c) leg swung, then pulled straight off sideways: play before it touches, then interference volume 0.3 mm further")
    for a in (0, 22.5, 45, 90, 135, 180, -45, -90, -135):
        L = cb.turn(leg, "y", j["point"], a)
        touch = next((d for d in np.arange(0.02, 4.0, 0.02) if (L.translate([0, d, 0]) ^ B).volume() > 1e-7), None)
        if touch is None:
            print(f"    swing {a:+6.1f}: COMES STRAIGHT OFF"); continue
        v = (L.translate([0, touch + 0.3, 0]) ^ B).volume()
        X = (L.translate([0, touch + 0.3, 0]) ^ B)
        bb = X.bounding_box()
        print(f"    swing {a:+6.1f}: play {touch - 0.02:.2f} mm, interference {v:.3f} mm3, lying z {bb[2] - cb.LEG_Z:+.2f}..{bb[5] - cb.LEG_Z:+.2f} about the axis, x {bb[0] - x:+.2f}..{bb[3] - x:+.2f}")
    # pulled askew: the leg first lifted / dropped / slid in its play, then pulled off
    print("    leg shifted in its play (dx, dz), then pulled off: play and interference 0.3 mm further (as printed, swing 0)")
    for dx, dz in ((0, 0), (0, 0.45), (0, 0.9), (0, -0.45), (0.45, 0), (-0.45, 0), (0.3, 0.9), (0, 1.2)):
        L = leg.translate([dx, 0, dz])
        if (L ^ B).volume() > 1e-7:
            print(f"    shift ({dx:+.2f}, {dz:+.2f}): not reachable (overlaps)"); continue
        touch = next((d for d in np.arange(0.02, 4.0, 0.02) if (L.translate([0, d, 0]) ^ B).volume() > 1e-7), None)
        if touch is None:
            print(f"    shift ({dx:+.2f}, {dz:+.2f}): COMES STRAIGHT OFF"); continue
        print(f"    shift ({dx:+.2f}, {dz:+.2f}): play {touch - 0.02:.2f}, interference {(L.translate([0, touch + 0.3, 0]) ^ B).volume():.3f} mm3")
    # how far can the leg be lifted / dropped / slid on its pin (its radial play)
    for lab, d in (("up", (0, 0, 1)), ("down", (0, 0, -1)), ("forward", (-1, 0, 0)), ("back", (1, 0, 0)), ("inwards", (0, -1, 0))):
        t = next((s for s in np.arange(0.02, 3.0, 0.02) if (leg.translate([c * s for c in d]) ^ B).volume() > 1e-7), None)
        print(f"    radial/axial play {lab}: {t - 0.02 if t else '>3'}")
    print(f"(d) bed contact {leg.slice(1e-3).area():.2f} mm2; in the slab 0..0.2 the narrowest contact piece: "
          + ", ".join(f"{p.area():.1f} mm2 ({p.bounds()[2] - p.bounds()[0]:.1f} x {p.bounds()[3] - p.bounds()[1]:.1f})" for p in leg.slice(0.1).decompose()))
