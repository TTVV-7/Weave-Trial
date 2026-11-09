"""Pocket gear fidget, as painted 3MFs and plain STLs.

A 52 mm rounded square with a ring of internal teeth cut into it, a sun gear in
the middle (with SWC on its hub) and four planet gears between them. Turn the
sun and the planets roll round it, spinning as they go.

Why there are no axles: a gear on an axle has to be held down by something
printed over it, which means bridging plastic across the gear with a hair of air
underneath, and that fuses. Instead the teeth are herringbone (a V up the face of
each tooth), so every gear is locked top and bottom by the gears it meshes with.
Everything sits on the bed, nothing is printed over anything, and it comes off
the plate as one piece that turns.

Also writes a test piece: the same gears and clearance at 4 mm tall, to check the
fit on your printer in a fraction of the time.

The script refuses to write files unless every gear is its own body, the set
turns a full revolution of the sun without a collision, every gear is held in
by its neighbours, nothing overhangs past 45 degrees, and nothing is thinner
than MIN_FEATURE.

Run: python3 make_gear_fidget.py   (needs numpy, trimesh, manifold3d, fonttools, qrcode)
"""
import sys
import numpy as np
import manifold3d as mf
import make_fidgets as mk

sys.path.insert(0, str(mk.HERE.parent / "reviewstand"))
from make_review_stand import text  # noqa: E402  (Inter Bold, outlines to a CrossSection)

OUT = mk.OUT
NAME = "pocket-gear-fidget"

FILAMENTS = np.array([
    [0x1A, 0x1A, 0x1A],   # T1 black: the plate, the monogram
    [0xFF, 0x6A, 0x13],   # T2 safety orange: the gears
    [0xF2, 0xF2, 0xF2],   # T3 white: the hubs
])
BLACK, ORANGE, WHITE = range(3)

# --- gears --------------------------------------------------------------------
MODULE = 1.25
PRESSURE = 25.0       # degrees; 25 rather than 20 keeps the 8-tooth planets from undercutting
ADDENDUM = 0.6        # x module: stubby teeth, so the tips stay 0.8 mm wide at this size
DEDENDUM = 1.15       # x module
Z_SUN, Z_PLANET, Z_RING = 18, 8, 34     # ring = sun + 2 planets; a big sun leaves room for SWC
PLANETS = 4           # (sun + ring) must divide by this for them to space evenly
HELIX = 30.0          # herringbone angle at the pitch circle, degrees
CLEAR = 0.4           # taken off the teeth of each meshing pair; the herringbone slant
                      # leaves about 0.35 mm actual gap square to the tooth face
GEAR_H = 7.0
HUB_H = 1.0           # raised hub on top of each gear
SUN_HUB_D = 18.0      # inside the sun's tooth roots, so it doesn't overhang the tooth gaps
PLANET_HUB_D = 5.5

# --- plate --------------------------------------------------------------------
PLATE = 52.0          # square, across
CORNER_R = 7.0
KEYRING_D = 4.5       # hole in one corner; 0 for none
MONOGRAM = "SWC"
MONO_H = 4.5          # letter height on the sun's hub; any smaller and the strokes drop under 0.8 mm
ENGRAVE = 0.6

MIN_FEATURE = 0.8     # two lines of a 0.4 mm nozzle
TEST_H = 4.0          # test piece height: one V of the herringbone


def inv(a):
    return np.tan(a) - a


def gear_section(z, grow=0.0, pts=10):
    """Involute spur gear outline, a tooth centred on angle 0. `grow` offsets it
    (negative thins every tooth, positive is used for the ring's cutter)."""
    rp = MODULE * z / 2
    rb = rp * np.cos(np.radians(PRESSURE))
    ra = rp + ADDENDUM * MODULE
    rf = rp - DEDENDUM * MODULE
    half_p = np.pi / (2 * z) + inv(np.radians(PRESSURE))   # tooth half-angle at the base circle

    def half(r):            # half the tooth's angular width at radius r
        return half_p - inv(np.arccos(np.clip(rb / r, -1, 1))) if r > rb else half_p

    rs = np.linspace(max(rb, rf), ra, pts)
    loop = []
    for k in range(z):
        c = 2 * np.pi * k / z
        if rf < rb:
            loop.append((rf, c - half(rb)))
        loop += [(r, c - half(r)) for r in rs]
        loop += [(ra, c + t) for t in np.linspace(-half(ra), half(ra), 4)[1:-1]]
        loop += [(r, c + half(r)) for r in rs[::-1]]
        if rf < rb:
            loop.append((rf, c + half(rb)))
        nxt = 2 * np.pi * (k + 1) / z
        a0, a1 = c + half(rb if rf < rb else rf), nxt - half(rb if rf < rb else rf)
        loop += [(rf, a) for a in np.linspace(a0, a1, 5)[1:-1]]
    loop = np.array(loop)
    cs = mf.CrossSection([np.c_[loop[:, 0] * np.cos(loop[:, 1]), loop[:, 0] * np.sin(loop[:, 1])]])
    return cs.offset(grow, mf.JoinType.Round, 2.0, 24) if grow else cs


def tip_width(z):
    """Width across the tip of a tooth after its share of the clearance comes off."""
    rp = MODULE * z / 2
    rb = rp * np.cos(np.radians(PRESSURE))
    ra = rp + ADDENDUM * MODULE
    half = np.pi / (2 * z) + inv(np.radians(PRESSURE)) - inv(np.arccos(rb / ra))
    return 2 * half * ra - CLEAR


def herringbone(cs, z, hand, h):
    """Extrude a gear section into a herringbone gear h tall. hand = +1 / -1;
    gears that mesh outside each other take opposite hands, a gear meshing inside
    the ring takes the ring's hand."""
    rp = MODULE * z / 2
    twist = hand * np.degrees(np.tan(np.radians(HELIX)) * (h / 2) / rp)
    n = max(3, int(abs(twist) / 1.5))     # a slice every 1.5 degrees of twist
    lower = mf.Manifold.extrude(cs, h / 2, n, twist)
    upper = mf.Manifold.extrude(cs.rotate(twist), h / 2, n, -twist).translate([0, 0, h / 2])
    return lower + upper


def plate_outline():
    s = PLATE / 2 - CORNER_R
    return mf.CrossSection.square([2 * s, 2 * s], center=True).offset(CORNER_R, mf.JoinType.Round, 2.0, 96)


def keyring_xy():
    s = PLATE / 2 - CORNER_R
    return (s, s)


def centre_distance():
    return MODULE * (Z_SUN + Z_PLANET) / 2


def planet_angles():
    return [360 * k / PLANETS for k in range(PLANETS)]


def make_parts(h=GEAR_H, hubs=True, keyring=True):
    """[plate, sun, planet, planet, ...] in the as-printed position."""
    half = -CLEAR / 2
    # the ring: a gear-shaped hole with a tooth gap facing each planet's tooth
    cutter = gear_section(Z_RING, CLEAR / 2).rotate(180 / Z_RING)
    plate = mf.Manifold.extrude(plate_outline(), h) - herringbone(cutter, Z_RING, -1, h)
    if keyring and KEYRING_D:
        x, y = keyring_xy()
        plate = plate - mf.Manifold.cylinder(3 * h, KEYRING_D / 2, KEYRING_D / 2, 64).translate([x, y, -h])

    sun = herringbone(gear_section(Z_SUN, half), Z_SUN, +1, h)
    if hubs:
        hub = mf.Manifold.cylinder(HUB_H, SUN_HUB_D / 2, SUN_HUB_D / 2, 96).translate([0, 0, h])
        letters = text(MONOGRAM, MONO_H, SUN_HUB_D - 2.4).translate((0, -MONO_H / 2))
        cut = mf.Manifold.extrude(letters, ENGRAVE + 1).translate([0, 0, h + HUB_H - ENGRAVE])
        sun = sun + hub - cut
    parts = [plate, sun]

    a = centre_distance()
    # sun tooth at 0 deg: the planet on +x needs a gap facing it, so turn it half a tooth
    base = herringbone(gear_section(Z_PLANET, half).rotate(180 / Z_PLANET), Z_PLANET, -1, h)
    if hubs:
        base = base + mf.Manifold.cylinder(HUB_H, PLANET_HUB_D / 2, PLANET_HUB_D / 2, 64).translate([0, 0, h])
    for psi in planet_angles():
        # as if the carrier had rolled the planet there: it turns -psi * ring/planet
        # relative to the carrier (the rotate by psi below supplies the carrier's turn)
        spin = -psi * Z_RING / Z_PLANET
        parts.append(base.rotate([0, 0, spin]).translate([a, 0, 0]).rotate([0, 0, psi]))
    return parts, base


def turned(parts, base, sun_deg):
    """The gear set after the sun turns sun_deg with the plate held still."""
    plate, sun = parts[0], parts[1]
    carrier = sun_deg * Z_SUN / (Z_SUN + Z_RING)
    a = centre_distance()
    out = [plate, sun.rotate([0, 0, sun_deg])]
    for psi in planet_angles():
        spin = -(psi + carrier) * Z_RING / Z_PLANET
        out.append(base.rotate([0, 0, spin]).translate([a, 0, 0]).rotate([0, 0, psi + carrier]))
    return out


# --- checks -------------------------------------------------------------------

def check(parts, base, h, step=4.0):
    """Refuse to go on unless the set is printable and turns. Returns a report."""
    for i, p in enumerate(parts):
        if len(p.decompose()) != 1:
            raise SystemExit(f"part {i} is not one piece")
    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            if (parts[i] ^ parts[j]).volume() > 1e-6:
                raise SystemExit(f"parts {i} and {j} overlap as printed")

    # one full turn of the sun (and the planets' full cycle comes with it)
    tight = 9.0
    for n, d in enumerate(np.arange(0, 360, step)):
        s = turned(parts, base, d)
        for i in range(len(s)):
            for j in range(i + 1, len(s)):
                if i >= 2 and j >= 2:
                    continue    # planets never get near each other
                if (s[i] ^ s[j]).volume() > 1e-6:
                    raise SystemExit(f"gears {i} and {j} collide with the sun turned {d:.0f} degrees")
                if n % 3 == 0:      # measuring the gap is the slow part
                    tight = min(tight, s[i].min_gap(s[j], 1.0))

    # held in: lift each gear 1 mm and it must hit a neighbour
    for i in range(1, len(parts)):
        lifted = parts[i].translate([0, 0, 1.0])
        others = mf.Manifold.batch_boolean([p for k, p in enumerate(parts) if k != i], mf.OpType.Add)
        if (lifted ^ others).volume() < 1e-3:
            raise SystemExit(f"gear {i} is not held in: it would lift straight out")

    # overhangs: downward-facing area steeper than 45 degrees, off the bed
    worst_area = 0.0
    for p in parts:
        m = mk.to_mesh(p)
        down = (m.face_normals[:, 2] < -np.sin(np.radians(45)) - 1e-6) & (m.triangles_center[:, 2] > 0.01)
        worst_area += m.area_faces[down].sum()
    if worst_area > 1.0:
        raise SystemExit(f"{worst_area:.1f} mm2 overhangs past 45 degrees")

    # thinnest features
    thin = {"tooth tip (planet)": tip_width(Z_PLANET), "tooth tip (sun)": tip_width(Z_SUN)}
    ring_root = MODULE * Z_RING / 2 + DEDENDUM * MODULE + CLEAR / 2
    thin["plate wall at the sides"] = PLATE / 2 - ring_root
    if KEYRING_D:
        x, y = keyring_xy()
        thin["keyring loop"] = min(CORNER_R - KEYRING_D / 2,
                                   np.hypot(x, y) - KEYRING_D / 2 - ring_root)
    thin["monogram strokes"] = stroke_width(text(MONOGRAM, MONO_H, SUN_HUB_D - 2.4))
    for k, v in thin.items():
        if v < MIN_FEATURE - 1e-6:
            raise SystemExit(f"{k} is {v:.2f} mm, thinner than {MIN_FEATURE} mm")
    return tight, worst_area, thin


def stroke_width(cs):
    """Roughly the thinnest stroke: twice the widest opening (shrink, then grow back)
    that keeps 75% of the lettering. A stroke thinner than that would vanish."""
    lo, hi = 0.0, 1.5
    for _ in range(12):
        d = (lo + hi) / 2
        opened = cs.offset(-d, mf.JoinType.Round).offset(d, mf.JoinType.Round)
        lo, hi = (d, hi) if opened.area() > 0.75 * cs.area() else (lo, d)
    return 2 * lo


# --- paint and write ----------------------------------------------------------

def paint(parts, h, hubs=True):
    meshes, labels = [], []
    for k, p in enumerate(parts):
        m = mk.to_mesh(p)
        lab = np.full(len(m.faces), BLACK if k == 0 else ORANGE)
        if k > 0 and hubs:
            c = m.triangles_center
            lab[c[:, 2] > h + 1e-3] = WHITE
            if k == 1:          # monogram cut into the sun's hub
                r = np.hypot(c[:, 0], c[:, 1])
                cut = (c[:, 2] > h + 1e-3) & (c[:, 2] < h + HUB_H - 1e-3) & (r < SUN_HUB_D / 2 - 0.05)
                lab[cut] = BLACK
        meshes.append(m)
        labels.append(lab)
    return mk.merged(meshes, labels)


def build(name, h, hubs, keyring):
    parts, base = make_parts(h, hubs, keyring)
    tight, over, thin = check(parts, base, h)
    print(f"{name}: turns a full revolution of the sun, tightest gap {tight:.2f} mm; "
          f"every gear held in; overhang past 45 deg {over:.2f} mm2")
    print("   thinnest: " + ", ".join(f"{k} {v:.2f}" for k, v in thin.items()))
    mesh, lab = paint(parts, h, hubs)
    mesh.export(OUT / f"{name}.stl")
    mk.write_3mf(OUT / f"{name}.3mf", [(name, mesh, lab, (0, 0))], FILAMENTS)
    e = mesh.extents
    print(f"   {e[0]:.1f} x {e[1]:.1f} x {e[2]:.1f} mm  {mesh.volume / 1000:.1f} cm3  {len(mesh.faces)} tris")
    return parts, base


def main():
    build(f"{NAME}-test", TEST_H, hubs=False, keyring=False)
    build(NAME, GEAR_H, hubs=True, keyring=True)


if __name__ == "__main__":
    main()
