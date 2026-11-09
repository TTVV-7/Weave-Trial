"""Construction nut & bolt fidget, as painted 3MFs and plain STLs.

A chunky bolt with a real helical thread and three hex nuts that spin up and down
it. The nuts and the bolt head are wrapped in hazard stripes, cut 0.6 mm deep, so
they read as stripes in one colour and print in yellow and black on a multi-
material printer. Spin a nut and let it run down the thread.

The thread is a twisted extrusion: the cross-section's radius is a sawtooth in
angle, so turning it 360 degrees per pitch as it rises gives a single-start,
right-hand thread with 44-degree flanks. Both the bolt (standing up) and the
nuts (flat) print without supports.

Run: python3 make_nut_bolt.py   (needs numpy, trimesh, manifold3d)
"""
import numpy as np
import manifold3d as mf
import make_fidgets as mk

OUT = mk.OUT

FILAMENTS = np.array([
    [0xF2, 0xC2, 0x00],   # T1 safety yellow
    [0x1A, 0x1A, 0x1A],   # T2 black
    [0xFF, 0x6A, 0x13],   # T3 safety orange
    [0x8C, 0x90, 0x96],   # T4 steel grey
])
YELLOW, BLACK, ORANGE, STEEL = range(4)

# --- thread -------------------------------------------------------------------
PITCH = 4.5           # rise per turn: coarse, so a nut runs down fast
R_MAJOR = 8.0         # 16 mm across the thread crests
DEPTH = 1.8           # crest to root
FLAT = 0.08           # share of each pitch that is flat at crest and at root
CLEAR = 0.5           # the nut's hole is the bolt's section grown by this much (0.36 mm square to the flank)
PTS = 96              # points round the section; also slices per pitch

# --- bolt ---------------------------------------------------------------------
HEAD_AF = 28.0        # head across flats
HEAD_H = 9.0
THREAD_L = 48.0
TIP_CHAMFER = 1.5

# --- nuts ---------------------------------------------------------------------
NUT_AF = 26.0
NUT_H = 12.0
HOLE_CHAMFER = 1.0
NUTS = [("nut-yellow", YELLOW, BLACK),      # (name, body colour, stripe colour)
        ("nut-orange", ORANGE, BLACK),
        ("nut-black", BLACK, YELLOW)]

STRIPE_D = 0.6        # hazard stripe depth
STRIPE_PITCH = 10.0   # roughly; adjusted so a whole number of stripes fits round


def thread_section(grow=0.0):
    """Cross-section of the threaded rod. Its radius is a trapezoid wave in angle:
    root flat, rising flank, crest flat, falling flank. Twisted 360 degrees per
    pitch, angle becomes height and the wave becomes the thread profile."""
    u = np.arange(PTS) / PTS
    flank = 0.5 - FLAT
    w = np.select([u < FLAT, u < 0.5, u < 0.5 + FLAT],
                  [0 * u, (u - FLAT) / flank, 1 + 0 * u], (1 - u) / flank)
    r = R_MAJOR - DEPTH + DEPTH * np.clip(w, 0, 1)
    a = 2 * np.pi * u
    cs = mf.CrossSection([np.c_[r * np.cos(a), r * np.sin(a)]])
    return cs.offset(grow, mf.JoinType.Round) if grow else cs


def threaded(length, grow=0.0):
    turns = length / PITCH
    return mf.Manifold.extrude(thread_section(grow), length, int(round(turns * PTS)), 360 * turns)


def hexagon(af):
    rc = af / np.sqrt(3)
    a = np.radians(np.arange(6) * 60)
    return mf.CrossSection([np.c_[rc * np.cos(a), rc * np.sin(a)]])


def chamfer_body(af, h, top=True, bottom=True):
    """Solid that trims a hex prism's corners at 30 degrees, the way real nuts are."""
    rc = af / np.sqrt(3) + 0.5
    r0 = 0.97 * af / 2
    ch = (rc - r0) * np.tan(np.radians(30))
    lo = mf.Manifold.cylinder(ch, r0, rc, mk.SEG) if bottom else \
        mf.Manifold.cylinder(ch, rc, rc, mk.SEG)
    mid = mf.Manifold.cylinder(h - 2 * ch, rc, rc, mk.SEG).translate([0, 0, ch])
    hi = (mf.Manifold.cylinder(ch, rc, r0, mk.SEG) if top else
          mf.Manifold.cylinder(ch, rc, rc, mk.SEG)).translate([0, 0, h - ch])
    return lo + mid + hi


def stripe_pitch(af):
    perim = 6 * af / np.sqrt(3)
    return perim / max(1, round(perim / STRIPE_PITCH))


def face_frames(af):
    rc = af / np.sqrt(3)
    side = rc   # a regular hexagon's side equals its corner radius
    for i in range(6):
        a0, a1 = np.radians(60 * i), np.radians(60 * (i + 1))
        v0 = rc * np.array([np.cos(a0), np.sin(a0)])
        v1 = rc * np.array([np.cos(a1), np.sin(a1)])
        t = (v1 - v0) / np.linalg.norm(v1 - v0)
        yield i, v0, t, i * side, a0, a1


def hazard_recess(af, h):
    """The solid cut out of a hex prism (across flats af, height h) to leave
    diagonal hazard stripes that run on unbroken round all six faces."""
    p = stripe_pitch(af)
    shell = mf.Manifold.extrude(hexagon(af + 2), h) - mf.Manifold.extrude(hexagon(af - 2 * STRIPE_D), h)
    cuts = []
    big = 4 * af + 4 * h
    for i, v0, t, u0, a0, a1 in face_frames(af):
        n = np.array([t[0], t[1], 1.0]) / np.sqrt(2)          # stripe slab normal
        e1 = np.array([-t[1], t[0], 0.0])                      # along the stripe, horizontal
        e2 = np.cross(n, e1)
        basis = np.c_[e1, e2, n]
        slabs = []
        # stripe k covers u + z in [k p, k p + p/2], where u = u0 + (x - v0).t
        for k in range(int(-big / p) - 2, int(big / p) + 2):
            lo = k * p - u0 + v0 @ t
            c = mf.Manifold.cube([big, big, p / 2 / np.sqrt(2)], center=True)
            off = (lo + p / 4) / np.sqrt(2)
            m = np.c_[basis, n * off]
            slabs.append(c.transform(m))
        sector = mf.Manifold.extrude(mf.CrossSection([np.array(
            [[0, 0], [3 * af * np.cos(a0), 3 * af * np.sin(a0)],
             [3 * af * np.cos(a1), 3 * af * np.sin(a1)]])]), h + 2).translate([0, 0, -1])
        cuts.append(mf.Manifold.batch_boolean(slabs, mf.OpType.Add) ^ sector)
    return mf.Manifold.batch_boolean(cuts, mf.OpType.Add) ^ shell


def in_stripe(c, af, z0=0.0, tol=0.06):
    """Does each point (x, y, z) fall in a cut stripe of a hex whose base is at z0?"""
    p = stripe_pitch(af)
    ang = np.degrees(np.arctan2(c[:, 1], c[:, 0])) % 360
    face = np.minimum((ang // 60).astype(int), 5)
    hit = np.zeros(len(c), bool)
    for i, v0, t, u0, _, _ in face_frames(af):
        sel = face == i
        u = u0 + (c[sel, :2] - v0) @ t
        s = (u + c[sel, 2] - z0) % p
        hit[sel] = (s < p / 2 + tol) | (s > p - tol)
    return hit


def hex_radius(c):
    """Distance out to the hex face each point sits behind (flats at 30 + 60 i)."""
    a = np.radians(30 + 60 * np.arange(6))
    return (c[:, :2] @ np.c_[np.cos(a), np.sin(a)].T).max(axis=1)


def make_nut():
    body = mf.Manifold.extrude(hexagon(NUT_AF), NUT_H) ^ chamfer_body(NUT_AF, NUT_H)
    body = body - hazard_recess(NUT_AF, NUT_H)
    # start a millimetre below the nut, phased so the thread is at angle 0 at its base
    hole = threaded(NUT_H + 2, CLEAR).rotate([0, 0, -360 / PITCH]).translate([0, 0, -1])
    rh = R_MAJOR + CLEAR + HOLE_CHAMFER          # 45-degree lead-in at both ends
    hole = hole + mf.Manifold.cylinder(rh, rh, 0, mk.SEG) \
        + mf.Manifold.cylinder(rh, 0, rh, mk.SEG).translate([0, 0, NUT_H - rh])
    return body - hole


def make_bolt():
    head = mf.Manifold.extrude(hexagon(HEAD_AF), HEAD_H) ^ chamfer_body(HEAD_AF, HEAD_H, bottom=False)
    head = head - hazard_recess(HEAD_AF, HEAD_H)
    shank = threaded(THREAD_L).translate([0, 0, HEAD_H])
    top = HEAD_H + THREAD_L
    tip = mf.Manifold.cylinder(top, R_MAJOR - DEPTH - 0.3 + top, R_MAJOR - DEPTH - 0.3, mk.SEG)
    return head + (shank ^ tip)


def nut_on_bolt(nut, z):
    """The nut screwed onto the bolt with its bottom at height z."""
    return nut.rotate([0, 0, 360 * (z - HEAD_H) / PITCH]).translate([0, 0, z])


def check(bolt, nut):
    """Screw a nut along the bolt and make sure the thread never binds."""
    tight = 9.0
    for z in np.linspace(HEAD_H + 0.5, HEAD_H + THREAD_L - NUT_H - 2, 23):
        placed = nut_on_bolt(nut, z)
        if (placed ^ bolt).volume() > 1e-3:
            raise SystemExit(f"nut binds on the bolt at z = {z:.1f}")
        tight = min(tight, placed.min_gap(bolt, 1.0))
    return tight


def paint_hex(m, af, body, stripe, z0, z1):
    """Body colour, stripe colour inside the stripe cuts (floors and walls)."""
    c = m.triangles_center
    z = m.triangles[:, :, 2]
    flat = np.ptp(z, axis=1) < 1e-4
    cap = flat & ((np.abs(z[:, 0] - z0) < 1e-4) | (np.abs(z[:, 0] - z1) < 1e-4))
    h = hex_radius(c)
    cut = (h < af / 2 - 0.03) & (h > af / 2 - STRIPE_D - 0.08) & in_stripe(c, af, z0) & ~cap
    lab = np.full(len(m.faces), body)
    lab[cut & (c[:, 2] >= z0) & (c[:, 2] <= z1)] = stripe
    return lab


def main():
    bolt = make_bolt()
    nut = make_nut()
    print(f"nut & bolt: a nut runs the full thread, tightest gap {check(bolt, nut):.2f} mm")

    bm = mk.to_mesh(bolt)
    blab = paint_hex(bm, HEAD_AF, YELLOW, BLACK, 0, HEAD_H)
    blab[bm.triangles_center[:, 2] > HEAD_H + 1e-3] = STEEL     # the threaded shank
    nm = mk.to_mesh(nut)
    bm.export(OUT / "construction-bolt.stl")
    nm.export(OUT / "construction-nut.stl")
    objs = [("bolt", bm, blab, (0, 0))]
    for (name, body, stripe), xy in zip(NUTS, [(34, -16), (34, 16), (0, 32)]):
        objs.append((name, nm, paint_hex(nm, NUT_AF, body, stripe, 0, NUT_H), xy))
    mk.write_3mf(OUT / "construction-nut-bolt.3mf", objs, FILAMENTS)
    for name, m in [("construction-bolt", bm), ("construction-nut", nm)]:
        e = m.extents
        print(f"{name:24s} {e[0]:5.1f} x {e[1]:5.1f} x {e[2]:4.1f} mm  {m.volume / 1000:5.1f} cm3  "
              f"{len(m.faces):7d} tris")


if __name__ == "__main__":
    main()
