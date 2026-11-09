"""Pocket capybara: a print-in-place articulated fidget, as a painted 3MF and a plain STL.

About 60 mm nose to rump, printed standing on its feet in one piece, no supports.
The body is four segments that wiggle side to side, the four legs swing on pins,
the head nods, and an orange nestled between its ears spins. An original design.

The shape comes first: a big, deep, blunt head a quarter of its length, held as
high as the shoulders; a barrel that swells at the belly and is highest over a
blunt rump; stubby legs with dark feet set in against the shoulders and haunches.

How it holds together with nothing printed over a gap:
  * body joints: each segment ends in an hourglass pin under a cone-shaped hood;
    the next segment's ring sits on the bed round the pin, under the hood. The
    hood rises at 60 degrees, so it is a gentle overhang, never a bridge. The V
    the joint swings in is shared between the two segments, to keep it small.
  * legs: each leg carries a cone pin that widens at 45 degrees into a pocket in
    the flank, so the leg can't pull off and its outside is plain.
  * head: a tab between two prongs, on two stub cone pins (like the gyro).
  * orange: its shaft runs down through the head to a flared foot on the bed.

Before writing anything the script checks that every part is one separate body,
swings every joint through its range, and measures overhangs and thin features.

Run: python3 make_capybara.py   (needs numpy, trimesh, manifold3d)
"""
import pathlib
import sys
import numpy as np
import manifold3d as mf
sys.path.insert(0, '/home/user/Weave-Trial/fidgets')
import make_fidgets as mk

OUT = pathlib.Path(__file__).resolve().parent
NAME = "pocket-capybara"

FILAMENTS = np.array([
    [0x9A, 0x6A, 0x3E],   # T1 warm brown: the body
    [0x4E, 0x30, 0x1C],   # T2 dark brown: nose, legs, ears
    [0x1A, 0x1A, 0x1A],   # T3 black: eyes, nostrils
    [0xF2, 0x8C, 0x1A],   # T4 orange: the orange
])
BROWN, DARK, BLACK, ORANGE = range(4)

CLEAR = 0.35          # gap square to a 45 degree pin surface
MIN_FEATURE = 0.8
MIN_PIN = 2.5
OVERHANG_OK = 1.0          # mm2 of steeper overhang allowed, for tiny details
SEG = 64

# --- body ---------------------------------------------------------------------
HEAD_LEN = 16.0       # nose to the back of the head: about a quarter of the animal
BODY_X0 = HEAD_LEN + 0.4   # flat front of the body, behind the head
BODY_X1 = 60.0        # rump
BODY_H = 16.5         # the back is highest over the rump
BELLY = 8.2           # half width of the barrel at the belly
FLANK = 7.3           # half width at the shoulders and haunches: the legs sit in against these
PINS = [29.6, 38.6, 47.6]   # x of the three body joints
SWING = 20.0          # each body joint wiggles this far either way
TEST_H = 15.0         # the test strip's barrel

# body joint, as radius/height round the pin's axis
RN = 1.5              # pin neck radius: a 3 mm pin
RF = 2.7              # pin foot radius on the bed (holds the ring down)
HF = RF - RN          # foot height (45 degrees)
Z0 = 3.2              # where the hood starts to flare from the neck
ROOF = 60.0           # hood slope from horizontal
RH = 7.0              # the hood ends this far from the pin
GAPJ = 0.5            # horizontal gap round the pin and under the hood
R_RING = 4.6          # ring outer radius
R_CAV = R_RING + 0.5  # the pocket the ring turns in
RING_TOP = 6.4        # the ring is flat-topped here, to pass under the hood of the joint in front
MARGIN = 3.0          # degrees left over at full swing; the V is shared by both segments

# --- legs ---------------------------------------------------------------------
LEG_X = [21.8, 54.6]  # front and hind legs, both sides
LEG_Z = 4.8           # pin height
LEG_NECK = 2.5        # pin diameter where it leaves the leg; it widens inwards at 45 degrees
LEG_GAP = 0.4         # between leg and flank
LEG_T = 1.6           # the leg is a plate this thick...
LEG_DEPTH = 1.3       # ...on a cone pin that reaches this far into the body
LEG_END = 0.4         # gap behind the pin's end
THIGH_R = 3.2         # the leg's round top, about the pin
ANKLE = 2.3           # half width just above the foot
FOOT_H = 2.6          # the foot: a little wider and prouder than the leg, painted dark
FOOT_PROUD = 0.5

# --- head ---------------------------------------------------------------------
NECK_X, NECK_Z = BODY_X0 + 3.0, 4.5   # the nod axis
TAB_W = 5.2           # neck tab width
TAB_R = 3.4           # neck tab radius round the axis
TAB_GAP = 0.4
NOD_PIN = 2.5         # stub pin tip diameter
NOD_DEPTH = 1.6       # stub pin length
NOD = 12.5            # the head must nod at least this far each way
NOD_CUT = NOD + 1.0   # the V between head and shoulders
EYE = (9.0, 10.6, 1.3)      # x, z, radius: high and far back
NOSTRIL = (2.0, 9.0, 0.9)    # y, z, radius: high on the blunt nose
NOSE_PAD = 0.5        # the nose pad stands this proud of the muzzle
NOSE_BAND = 1.7       # ...and wraps this far back
NOSE_FROM = 5.6       # ...from this height up

# --- orange -------------------------------------------------------------------
EARS = [((11.9, 11.5), (4.4, 5.2), (12.2, 15.0), 2.1, 1.6)]   # (x, y, z) of root and tip, their radii
EAR_FROM = 13.0           # painted dark above this height
ORANGE_X = 7.0
ORANGE_R = 4.0        # an 8 mm orange
ORANGE_SINK = 2.0     # how deep its seat is sunk into the top of the head
SHAFT_R = 1.5         # 3 mm shaft down through the head
SHAFT_FOOT = 2.6      # foot radius on the bed
SHAFT_GAP = 0.5

KEYRING_D = 4.0       # hole in the loop behind the rump; 0 for none
KEYRING_H = 3.0


# --- building blocks ----------------------------------------------------------
def ball(r, x, y, z):
    return mf.Manifold.sphere(r, SEG).translate([x, y, z])


def box(x0, x1, y0, y1, z0, z1):
    return mf.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def revolve(profile, at):
    """Solid of revolution about the vertical axis through (at, 0); profile is (r, z)."""
    return mf.CrossSection([profile]).revolve(96).translate([at, 0, 0])


def prism_xz(profile, y0, y1):
    """An (x, z) outline extruded from y0 to y1."""
    return mf.Manifold.extrude(mf.CrossSection([profile]), y1 - y0).rotate([90, 0, 0]).translate([0, y1, 0])


def prism_yz(profile, x0, x1):
    """A (y, z) outline extruded from x0 to x1."""
    return (mf.Manifold.extrude(mf.CrossSection([profile]), x1 - x0)
            .rotate([90, 0, 0]).rotate([0, 0, 90]).translate([x0, 0, 0]))


def frustum_y(x, z, y0, r0, y1, r1):
    """Cone frustum on a line parallel to y, radius r0 at y0 and r1 at y1."""
    lo, hi = (y0, r0), (y1, r1)
    if y1 < y0:
        lo, hi = hi, lo
    c = mf.Manifold.cylinder(hi[0] - lo[0], lo[1], hi[1], SEG)
    return c.rotate([-90, 0, 0]).translate([x, lo[0], z])


def turn(m, axis, point, deg):
    """m turned deg about the 'y' or 'z' axis through point."""
    p = np.asarray(point, float)
    rot = [0, deg, 0] if axis == "y" else [0, 0, deg]
    return m.translate(list(-p)).rotate(rot).translate(list(p))


def slab_xz(section, y0, y1):
    """A CrossSection drawn in (x, z), extruded from y0 to y1."""
    return mf.Manifold.extrude(section, y1 - y0).rotate([90, 0, 0]).translate([0, y1, 0])


def flats(x0, x1):
    """Everything between the two flat flanks the legs sit against."""
    return box(x0, x1, -FLANK, FLANK, 0, BODY_H + 6)


def body_hull(x0, x1):
    """The test strip's barrel: flat belly, flat flanks and a flat front. The spheres
    sit low enough that the bed cuts them where they reach 45 degrees."""
    a, b = x0 + 5.0, x1 - 6.5
    blobs = [ball(6.0, x, s * 2.5, 4.1) for x in (a, b) for s in (-1, 1)]
    blobs += [ball(6.5, x, 0, TEST_H - 6.5) for x in (a - 1.0, b)]
    hull = mf.Manifold.batch_hull(blobs)
    return hull ^ flats(x0, x1 + 1)


def capybara_body():
    """A heavy barrel: deep at the shoulder, widest at the belly, highest over a
    blunt rump, with flat flanks for the legs. Every low sphere is cut by the bed
    at 45 degrees or steeper."""
    x0, x1 = BODY_X0, BODY_X1
    low = [(6.5, x0 + 2.0, BELLY - 6.5), (6.9, 38.0, BELLY - 6.9), (6.9, x1 - 6.9, BELLY - 5.6)]
    blobs = [ball(r, x, s * y, 0.69 * r) for r, x, y in low for s in (-1, 1)]
    blobs += [ball(6.0, x0 + 1.0, 0, 7.6), ball(6.8, 39.0, 0, 8.9), ball(7.0, x1 - 7.2, 0, BODY_H - 7.0)]
    hull = mf.Manifold.batch_hull(blobs) ^ box(x0, x1 + 1, -20, 20, 0, BODY_H + 1)
    return hull


def joint_solid(px, grow):
    """The front segment's share of a body joint: foot, neck and hood."""
    k = np.tan(np.radians(ROOF))
    top = BODY_H + 5
    prof = [(0, 0), (RF + grow, 0), (RN + grow, HF), (RN + grow, Z0),
            (RH + grow, Z0 + k * (RH - RN)), (RH + grow, top), (0, top)]
    return revolve(prof, px)


def split(body, pins):
    """Cut a body into len(pins) + 1 segments joined by pin-and-ring joints. The V
    each joint needs to swing is shared: each face leans back by half of it, so
    the notch in the flank is as small as the swing allows and the same both sides."""
    tall = BODY_H + 5
    a = np.radians(90 - (SWING + MARGIN) / 2)
    far = 400.0
    wedge = mf.Manifold.extrude(mf.CrossSection(
        [[(0, 0), (far * np.cos(a), -far * np.sin(a)), (far * np.cos(a), far * np.sin(a))]]), tall)
    segs = []
    for i in range(len(pins) + 1):
        seg = body
        if i > 0:                      # this segment's ring, on the pin in front
            px = pins[i - 1]
            ring = mf.Manifold.cylinder(RING_TOP, R_RING, R_RING, 96)
            seg = seg ^ ((ring + wedge).translate([px, 0, 0]) - joint_solid(px, GAPJ))
        if i < len(pins):              # this segment's pin and hood, at its rear
            px = pins[i]
            front = wedge.rotate([0, 0, 180]).translate([px, 0, 0]) - \
                mf.Manifold.cylinder(tall, R_CAV, R_CAV, 96).translate([px, 0, 0])
            seg = seg ^ (front + joint_solid(px, 0.0))
        segs.append(seg)
    return segs


def leg_socket(x, side):
    """The cone pocket in the flank that the leg's pin turns in: it narrows to the
    flank, so the leg can't pull out, and nothing shows on the outside of the leg."""
    r0 = LEG_NECK / 2 + CLEAR * np.sqrt(2)
    out = 1.0                                         # carried on out past the flank
    deep = LEG_DEPTH + LEG_END
    return frustum_y(x, LEG_Z, side * (FLANK + out), r0 + LEG_GAP - out,
                     side * (FLANK - deep), r0 + LEG_GAP + deep)


def leg(x, side):
    """A stubby leg: round thigh about the pin, tapering to the ankle, on a wider
    foot. Its cone pin widens into the body at 45 degrees."""
    r0 = LEG_NECK / 2
    y_in = FLANK + LEG_GAP
    thigh = mf.CrossSection.circle(THIGH_R, SEG).translate([x, LEG_Z])
    ankle = mf.CrossSection.square([2 * ANKLE, 1.0]).translate([x - ANKLE, 0])
    y0, y1 = sorted([side * y_in, side * (y_in + LEG_T)])
    upper = slab_xz(mf.CrossSection.batch_hull([thigh, ankle]), y0, y1)
    h = FOOT_H
    y0, y1 = sorted([side * y_in, side * (y_in + LEG_T + FOOT_PROUD)])
    foot = prism_xz([(x - 3.5, 0.7), (x - 2.8, 0), (x + 2.5, 0), (x + 3.0, 0.5), (x + 3.0, h - 0.6),
                     (x + 2.6, h), (x - 2.7, h), (x - 3.5, h - 0.8)], y0, y1)       # toes point forwards
    pin = frustum_y(x, LEG_Z, side * y_in, r0, side * (FLANK - LEG_DEPTH), r0 + LEG_GAP + LEG_DEPTH)
    root = frustum_y(x, LEG_Z, side * y_in, r0, side * (y_in + 0.8), r0)
    return upper + foot + pin + root


# --- head and orange ----------------------------------------------------------
def reach(m, lo, hi, axis):
    """Furthest m reaches along `axis` inside the probe box lo..hi."""
    probe = m ^ box(lo[0], hi[0], lo[1], hi[1], lo[2], hi[2])
    return probe.bounding_box()[3 + axis]


def orange_profile(seat, grow=0.0, hole=False):
    """(r, z) outline of the orange on its shaft; `hole` gives the bore through the
    head, which opens into a cone-shaped seat the orange nestles in."""
    s = SHAFT_R + grow
    prof = [(0, 0), (SHAFT_FOOT + grow, 0), (s, SHAFT_FOOT - SHAFT_R), (s, seat)]
    if hole:
        rim = ORANGE_R + 0.6
        return prof + [(rim, seat + rim - s), (rim, seat + 30), (0, seat + 30)]
    lat = ORANGE_R * np.sqrt(0.5)                 # the cone meets the ball at 45 degrees
    zc = seat + (lat - SHAFT_R) + lat
    dimple = 0.9
    t1 = np.arccos(dimple / ORANGE_R)
    prof += [(ORANGE_R * np.cos(t), zc + ORANGE_R * np.sin(t)) for t in np.linspace(-np.pi / 4, t1, 40)]
    return prof + [(0, zc + ORANGE_R * np.sin(t1) - dimple)], zc


def head_hull():
    """A big, deep, blunt head: a squared-off muzzle nearly as deep as the skull."""
    n = NOSE_PAD
    blobs = [ball(2.4, n + 2.4, s * 3.2, 0.69 * 2.4) for s in (-1, 1)]       # chin corners
    blobs += [ball(2.4, n + 2.5, s * 2.9, 9.8) for s in (-1, 1)]             # top of the nose
    blobs += [ball(5.2, 12.5, s * 2.0, 0.69 * 5.2) for s in (-1, 1)]         # jowls
    blobs += [ball(4.6, 12.0, s * 2.3, 9.8) for s in (-1, 1)]                # crown
    return mf.Manifold.batch_hull(blobs) ^ box(0, 40, -20, 20, 0, 40)


def nose_pad(hull):
    """The broad flat nose: the front of the muzzle, standing a little proud. Its
    lower edge is a 45 degree chamfer."""
    n = NOSE_PAD
    keep = prism_xz([(-1, NOSE_FROM + n + 1), (NOSE_BAND, NOSE_FROM + n - NOSE_BAND),
                     (NOSE_BAND, 40), (-1, 40)], -20, 20)
    return hull.translate([-n, 0, 0]) ^ keep


def make_head():
    """Returns the head, the orange, and where things ended up (for painting)."""
    head = head_hull()
    ex, ez, er = EYE
    ys = reach(head, (ex - 0.1, 0, ez - 0.1), (ex + 0.1, 30, ez + 0.1), 1)
    top = reach(head, (ORANGE_X - 0.1, -0.1, 0), (ORANGE_X + 0.1, 0.1, 40), 2)
    seat = top - ORANGE_SINK
    head += nose_pad(head)

    for s in (-1, 1):                              # ears
        (x0, x1), (y0, y1), (z0, z1), r0, r1 = EARS[0]
        head += mf.Manifold.batch_hull([ball(r0, x0, s * y0, z0), ball(r1, x1, s * y1, z1)])
    # the back of the head is a shallow V about the nod axis, so it clears the body
    behind = box(-50, HEAD_LEN, -50, 50, -50, 50)
    for a in (-NOD_CUT, NOD_CUT):
        head ^= turn(behind, "y", [NECK_X, 0, NECK_Z], a)
    # neck tab: flat on the bed up to the axis, then a quarter circle and a chamfer
    arc = [(NECK_X + TAB_R * np.cos(t), NECK_Z + TAB_R * np.sin(t)) for t in np.linspace(0, np.pi / 2, 17)]
    tab = prism_xz([(HEAD_LEN - 5.0, 0), (NECK_X + NECK_Z - TAB_R, 0)] + arc + [(HEAD_LEN - 5.0, NECK_Z + TAB_R)],
                   -TAB_W / 2, TAB_W / 2)
    head += tab
    g = CLEAR * np.sqrt(2)
    for s in (-1, 1):
        head -= nod_pin(s, shift=g, extend=1.0)
        head -= mk.cone([ex, s * (ys - er), ez], [0, s, 0], er + 2)                 # eye
        ny, nz, nr = NOSTRIL
        head -= mk.cone([nr, s * ny, nz], [-1, 0, 0], nr + 1)                       # nostril
    head -= revolve(orange_profile(seat, SHAFT_GAP, hole=True), ORANGE_X)
    prof, zc = orange_profile(seat)
    orange = revolve(prof, ORANGE_X)
    return head, orange, {"eye_y": ys, "seat": seat, "orange_z": zc}


def nod_pin(side, shift=0.0, extend=0.0):
    """Stub cone pin from a prong into the neck tab; shifted inwards it is the socket."""
    y_face = TAB_W / 2 + TAB_GAP
    r_tip = NOD_PIN / 2
    y0 = y_face + extend
    y1 = y_face - NOD_DEPTH
    return frustum_y(NECK_X, NECK_Z, side * (y0 - shift), r_tip + NOD_DEPTH + extend,
                     side * (y1 - shift), r_tip)


def doorway():
    """The slot in the front of the body the neck tab sits in, with a pitched roof."""
    hw = TAB_W / 2 + TAB_GAP
    eave = NECK_Z + TAB_R + 1.3
    return prism_yz([(-hw, -1), (hw, -1), (hw, eave), (0, eave + hw), (-hw, eave)],
                    BODY_X0 - 1, NECK_X + TAB_R + 0.5)


def keyring():
    r = KEYRING_D / 2
    cx = BODY_X1 + r - 0.6
    loop = mf.Manifold.cylinder(KEYRING_H, r + 1.8, r + 1.8, SEG) - \
        mf.Manifold.cylinder(KEYRING_H + 2, r, r, SEG).translate([0, 0, -1])
    return loop.translate([cx, 0, 0])


# --- the two models -----------------------------------------------------------
def joint(name, axis, point, moving, want, limit, step):
    return dict(name=name, axis=axis, point=point, moving=moving, want=want, limit=limit, step=step)


def make_capybara():
    """parts: name -> Manifold.  joints: in the order to pose them (leaves first)."""
    head, orange, info = make_head()
    segs = split(capybara_body(), PINS)
    segs[0] ^= flats(-100, 100)                    # shoulders and haunches are narrower than the
    segs[-1] ^= flats(-100, 100)                   # belly, so the legs sit in against them
    segs[0] -= doorway()
    for s in (-1, 1):
        segs[0] += nod_pin(s) + frustum_y(NECK_X, NECK_Z, s * (TAB_W / 2 + TAB_GAP + 1),
                                          NOD_PIN / 2 + NOD_DEPTH, s * (TAB_W / 2 + TAB_GAP), NOD_PIN / 2 + NOD_DEPTH)
        segs[0] -= leg_socket(LEG_X[0], s)
        segs[-1] -= leg_socket(LEG_X[1], s)
    if KEYRING_D:
        segs[-1] += keyring()
    parts = {"head": head, "orange": orange}
    parts.update({f"body {i + 1}": s for i, s in enumerate(segs)})
    joints = []
    for i, x in enumerate(LEG_X):
        for s, side in ((1, "left"), (-1, "right")):
            name = f"{'front' if i == 0 else 'hind'} {side} leg"
            parts[name] = leg(x, s)
            joints.append(joint(name, "y", [x, 0, LEG_Z], [name], 45, 180, 15))
    joints.append(joint("orange", "z", [ORANGE_X, 0, 0], ["orange"], 180, 180, 45))
    hind = ["hind left leg", "hind right leg"]
    for i in reversed(range(len(PINS))):
        moving = [f"body {k + 1}" for k in range(i + 1, len(segs))] + hind
        joints.append(joint(f"body joint {i + 1}", "z", [PINS[i], 0, 0], moving, SWING, 40, 5))
    joints.append(joint("head nod", "y", [NECK_X, 0, NECK_Z], ["head", "orange"], NOD, 40, 2.5))
    return parts, joints, info


def make_test():
    """Two body segments, one body joint and one leg: the same split(), leg() and
    leg_socket() as the capybara, so the same joints, as a 20 minute print."""
    a, b = split(body_hull(0, 26), [14])
    a -= leg_socket(7.0, 1)
    parts = {"body 1": a, "body 2": b, "leg": leg(7.0, 1)}
    joints = [joint("leg", "y", [7.0, 0, LEG_Z], ["leg"], 45, 180, 15),
              joint("body joint", "z", [14, 0, 0], ["body 2"], SWING, 40, 5)]
    return parts, joints, {}


def posed(parts, joints, angles):
    """The parts with each joint turned by angles[name] degrees. The joints are
    listed leaves first, so a joint's own pivot has never moved when its turn comes."""
    parts = dict(parts)
    for j in joints:
        a = angles.get(j["name"], 0)
        if a:
            for n in j["moving"]:
                parts[n] = turn(parts[n], j["axis"], j["point"], a)
    return parts


# --- checks -------------------------------------------------------------------
def union(ms):
    return mf.Manifold.batch_boolean(list(ms), mf.OpType.Add)


def clash(parts, moving):
    """(overlap volume, gap) between the parts named in `moving` and all the rest."""
    a = union(parts[n] for n in moving)
    b = union(p for n, p in parts.items() if n not in moving)
    return (a ^ b).volume(), a.min_gap(b, 2.0)


def sweep(parts, joints, j):
    """Turn joint j each way until it hits something. Returns the free range each
    way (degrees) and the tightest gap inside the range it is meant to have."""
    free, tight = [], 9.0
    for sign in (1, -1):
        reached = 0.0
        for a in np.arange(j["step"], j["limit"] + 1e-6, j["step"]):
            vol, gap = clash(posed(parts, joints, {j["name"]: sign * a}), j["moving"])
            if vol > 1e-6:
                break
            reached = a
            if a <= j["want"] + 1e-6:
                tight = min(tight, gap)
        free.append(reached)
    return free, tight


def thin_features(parts, info):
    """Thinnest walls (>= MIN_FEATURE) and pins (>= MIN_PIN), from the dimensions."""
    g = CLEAR * np.sqrt(2)
    socket_end = LEG_NECK / 2 + g + LEG_GAP + LEG_DEPTH + LEG_END     # radius at its deep end
    walls = {
        "leg plate": LEG_T,
        "leg round its pin": THIGH_R - LEG_NECK / 2,
        "ankle": 2 * ANKLE,
        "body under the leg socket": LEG_Z - socket_end,
        "leg pin's hold in its socket": LEG_DEPTH - g,       # how much wider the pin's end is than the mouth
        "joint ring wall": R_RING - (RF + GAPJ),
        "ring to pocket wall": FLANK - R_CAV,
        "ring height": min(RING_TOP, Z0 + np.tan(np.radians(ROOF)) * (RF - RN)),
    }
    pins = {"body pin neck": 2 * RN, "leg pin": LEG_NECK}
    if "head" in parts:
        socket_r = NOD_PIN / 2 + NOD_DEPTH - CLEAR * np.sqrt(2)      # at the face of the tab
        walls.update({
            "neck tab round its sockets": min(TAB_R, NECK_Z) - socket_r,
            "neck tab between its sockets": TAB_W - 2 * (NOD_DEPTH + CLEAR * np.sqrt(2) - TAB_GAP),
            "wall behind the neck slot": (PINS[0] - R_CAV) - (NECK_X + TAB_R + 0.5),
            "roof over the neck slot": reach(parts["body 1"], (BODY_X0 + 0.3, -0.1, 0), (BODY_X0 + 0.5, 0.1, 40), 2)
            - (NECK_Z + TAB_R + 1.3 + TAB_W / 2 + TAB_GAP),
            "head wall between eye and orange": np.hypot(EYE[0] - ORANGE_X, info["eye_y"] - EYE[2])
            - (SHAFT_R + SHAFT_GAP + max(0.0, EYE[1] + EYE[2] - info["seat"])),
            "wall between leg socket and neck slot": (FLANK - LEG_DEPTH - LEG_END) - (TAB_W / 2 + TAB_GAP),
            "wall in front of the front leg socket": LEG_X[0] - socket_end - BODY_X0,
            "wall behind the hind leg socket": reach(
                parts[f"body {len(PINS) + 1}"], (LEG_X[1], FLANK - LEG_DEPTH - LEG_END - 0.1, LEG_Z - 0.1),
                (99, FLANK - LEG_DEPTH - LEG_END, LEG_Z + 0.1), 0) - (LEG_X[1] + socket_end),
            "ear tip": 2 * EARS[0][4],
        })
        pins.update({"head nod pins": NOD_PIN, "orange shaft": 2 * SHAFT_R})
        if KEYRING_D:
            walls["keyring loop"] = 1.8
    return walls, pins


def check(parts, joints, info):
    """Refuse to go on unless it prints in place and every joint moves. Returns report lines."""
    names = list(parts)
    # 1. every moving part is its own single body, clear of the others as printed
    tight = 9.0
    for n in names:
        if len(parts[n].decompose()) != 1:
            raise SystemExit(f"{n} is not one piece")
        if parts[n].bounding_box()[2] < -1e-6:
            raise SystemExit(f"{n} pokes below the bed")
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if (parts[a] ^ parts[b]).volume() > 1e-6:
                raise SystemExit(f"{a} and {b} are fused as printed")
            gap = parts[a].min_gap(parts[b], 2.0)
            if gap < CLEAR - 0.005:
                raise SystemExit(f"{a} and {b} are only {gap:.2f} mm apart as printed")
            tight = min(tight, gap)
    out = [f"{len(names)} separate bodies, tightest gap as printed {tight:.2f} mm"]

    # 2. each joint through its range
    for j in joints:
        free, gap = sweep(parts, joints, j)
        if min(free) < j["want"] - 1e-6:
            raise SystemExit(f"{j['name']} only swings +{free[0]:.0f}/-{free[1]:.0f} degrees, wanted {j['want']:.0f}")
        rng = "full circle" if min(free) >= 180 else f"+{free[0]:g}/-{free[1]:g} deg"
        out.append(f"   {j['name']:<16} {rng:<16} tightest gap {gap:.2f} mm")

    # 3. the body curled up and S-bent, legs and head turned too
    body = [j for j in joints if j["name"].startswith("body joint")]
    extra = {j["name"]: j["want"] for j in joints if j not in body and j["want"] < 180}
    for label, signs in (("curled", [1, 1, 1]), ("S-bent", [1, -1, 1])):
        for flip in (1, -1, 2, -2):                # 2: the same again with legs and head turned the other way
            pose = {k: v if abs(flip) == 1 else -v for k, v in extra.items()}
            flip = int(np.sign(flip))
            pose.update({j["name"]: flip * s * SWING for j, s in zip(body, signs)})
            p = posed(parts, joints, pose)
            ks = list(p)
            for i, a in enumerate(ks):
                for b in ks[i + 1:]:
                    if (p[a] ^ p[b]).volume() > 1e-6:
                        raise SystemExit(f"{a} hits {b} with the body {label}")
    out.append("   curled and S-bent with every joint at its limit: nothing collides")

    # 4. nothing can fall off: push each part 1 mm each way and it must hit a neighbour
    for n in names:
        rest = union(p for k, p in parts.items() if k != n)
        for d in ([1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]):
            if (parts[n].translate([1.0 * c for c in d]) ^ rest).volume() < 1e-3:
                raise SystemExit(f"{n} is not held in: it slides out along {d}")
    out.append("   every part is held in whichever way it is pulled")

    # 4b. the flank is flat right round each leg's socket, so the socket's mouth is as small as designed
    for j in joints:
        if "leg" in j["name"]:
            n = j["moving"][0]
            side = np.sign(parts[n].bounding_box()[1] + parts[n].bounding_box()[4])
            mouth = LEG_NECK / 2 + CLEAR * np.sqrt(2) + LEG_GAP
            y0, y1 = sorted([side * (FLANK - 0.1), side * (FLANK - 0.02)])
            probe = frustum_y(j["point"][0], LEG_Z, y0, mouth + 0.6, y1, mouth + 0.6) - \
                frustum_y(j["point"][0], LEG_Z, y0 - 1, mouth + 0.1, y1 + 1, mouth + 0.1)
            rest = union(p for k, p in parts.items() if k != n)
            if (probe - rest).volume() > 1e-3:
                raise SystemExit(f"the flank is not flat round the socket of the {n}")
    out.append("   the flank is flat round every leg socket")

    # 5. overhangs past 45 degrees, off the bed
    area = 0.0
    for p in parts.values():
        m = mk.to_mesh(p)
        down = (m.face_normals[:, 2] < -np.sin(np.radians(45)) - 1e-3) & (m.triangles_center[:, 2] > 0.01)
        area += m.area_faces[down].sum()
    if area > OVERHANG_OK:
        raise SystemExit(f"{area:.1f} mm2 overhangs past 45 degrees")
    out.append(f"   overhang past 45 deg {area:.2f} mm2; nothing below the bed")

    # 6. thin features
    walls, pins = thin_features(parts, info)
    for what, limit in ((walls, MIN_FEATURE), (pins, MIN_PIN)):
        for k, v in what.items():
            if v < limit - 1e-6:
                raise SystemExit(f"{k} is {v:.2f} mm, under {limit}")
    out.append("   thinnest walls: " + ", ".join(f"{k} {v:.2f}" for k, v in sorted(walls.items(), key=lambda kv: kv[1])[:4]))
    out.append("   pins: " + ", ".join(f"{k} {v:.2f}" for k, v in pins.items()))
    return out


# --- paint and write ----------------------------------------------------------
def paint(parts, info, shown=None):
    """One mesh for the lot, and a filament index for every triangle. The colours
    are worked out on `parts` as printed; `shown` can give the same parts posed."""
    meshes, labels = [], []
    for name, p in parts.items():
        m = mk.to_mesh(p)
        c = m.triangles_center
        x, y, z = c[:, 0], np.abs(c[:, 1]), c[:, 2]
        lab = np.full(len(m.faces), ORANGE if name == "orange" else BROWN)
        if "leg" in name:
            lab[(z < FOOT_H + 0.01) & (y > FLANK + LEG_GAP - 0.01)] = DARK      # the feet
        if name == "head":
            vx, vz = m.triangles[:, :, 0], m.triangles[:, :, 2]
            lab[((vx < NOSE_BAND + 0.01) & (vz > NOSE_FROM + NOSE_PAD - vx - 0.02)).all(1)] = DARK   # the broad flat nose
            for cx, cy, cz, r0, r1 in EARS:                   # ears: anything on the ear's own skin
                t = np.linspace(0, 1, 9)[:, None]
                px = cx[0] + (cx[1] - cx[0]) * t
                py = cy[0] + (cy[1] - cy[0]) * t
                pz = cz[0] + (cz[1] - cz[0]) * t
                d = np.sqrt((x - px) ** 2 + (y - py) ** 2 + (z - pz) ** 2) - (r0 + (r1 - r0) * t)
                lab[(d.min(0) < 0.05) & (z > EAR_FROM)] = DARK
            ex, ez, er = EYE
            deep = y - (info["eye_y"] - er)
            lab[(deep > -0.01) & (np.hypot(x - ex, z - ez) < deep + 0.03)] = BLACK
            ny, nz, nr = NOSTRIL
            lab[(x > 0.01) & (np.hypot(y - ny, z - nz) < nr - x + 0.03)] = BLACK
        if name == "orange":
            rad = np.hypot(x - ORANGE_X, c[:, 1])
            lab[(z < info["seat"] + 0.01) & (rad < SHAFT_FOOT + 0.1)] = BROWN       # the shaft, hidden in the head
            lab[(rad < 1.3) & (z > info["orange_z"] + ORANGE_R - 1.2)] = DARK      # the stalk dimple
        if shown:
            m = mk.to_mesh(shown[name])
            assert len(m.faces) == len(lab)
        meshes.append(m)
        labels.append(lab)
    return mk.merged(meshes, labels)


def build(name, maker, title):
    parts, joints, info = maker()
    report = check(parts, joints, info)
    print(f"{title}: " + "\n".join(report))
    mesh, lab = paint(parts, info)
    lo = mesh.bounds[0]
    mesh.apply_translation([-lo[0], -(mesh.bounds[0][1] + mesh.bounds[1][1]) / 2, 0])
    if lo[2] < -1e-6:
        raise SystemExit("something pokes below the bed")
    mesh.export(OUT / f"{name}.stl")
    mk.write_3mf(OUT / f"{name}.3mf", [(name, mesh, lab, (0, 0))], FILAMENTS)
    e = mesh.extents
    print(f"{name}  {e[0]:.1f} x {e[1]:.1f} x {e[2]:.1f} mm  {mesh.volume / 1000:.1f} cm3  {len(mesh.faces)} tris\n")


def main():
    build(f"{NAME}-test", make_test, "test strip")
    build(NAME, make_capybara, "pocket capybara")


if __name__ == "__main__":
    main()
