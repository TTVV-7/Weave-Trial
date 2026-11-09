"""Pocket capybara: a print-in-place articulated fidget, as a painted 3MF and a plain STL.

About 60 mm nose to rump, printed standing on its feet in one piece, no supports.
The body is four segments that wiggle side to side, the four legs swing on axles,
the head nods, and an orange on its head spins. An original design.

The shape: a deep, blunt, blocky head nearly as tall as the shoulders, with a
squared muzzle, small ears far back and eyes high on the sides; a barrel body
that rises to a round rump; short legs with dark paws; no tail.

How it holds together with nothing printed over a gap:
  * body joints: each segment ends in an hourglass pin under a wide cone-shaped
    hood; the next segment's ring sits on the bed round the pin, under the hood.
    The hood rises at 45 degrees, so it is an overhang, never a bridge, and it
    covers the joint from above like a roof shingle. The V notch each joint
    needs to bend is cut half from each segment, so it sits square across.
  * legs: the leg, an hourglass axle through the flank wall, and a keeper standing
    on the bed in a pocket inside the body are one piece. The axle grows out of
    the leg and the keeper at 45 degrees and meets in the middle of the wall, so
    nothing starts in mid-air and nothing shows on the outside of the leg.
  * head: a tab between two prongs, on two stub cone pins (like the gyro).
  * orange: its shaft runs down through the head to a flared foot on the bed.

Before writing anything the script checks that every part is one separate body,
swings every joint through its range, measures overhangs and thin features, and
slices every part into layers to make sure each one starts on the bed and rests
on itself all the way up.

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
LAYER = 0.2                # layer height the layer-by-layer check slices at
SEG = 64

# --- body ---------------------------------------------------------------------
BODY_X0 = 15.0        # flat front of the body, behind the head
BODY_X1 = 60.5        # rump
BODY_H0 = 13.4        # height over the shoulders
BODY_H = 15.2         # height over the rump, the highest point of the back
HALF_W = 8.6          # half width of the barrel at its widest
NECK_TAPER = 0.8      # the shoulders are this much narrower each side where they meet the head
PINS = [28.0, 37.5, 47.0]   # x of the three body joints
SWING = 22.5          # each body joint wiggles this far either way
MARGIN = 2.5          # degrees left over at full swing
V_SHARE = 0.5         # share of each joint's V notch cut from the segment in front, so the
                      # notch sits square across the body instead of slanting back

# body joint, as radius/height round the pin's axis
RN = 1.5              # pin neck radius: a 3 mm pin
RF = 2.7              # pin foot radius on the bed (holds the ring down)
HF = RF - RN          # foot height (45 degrees)
Z0 = 3.2              # where the hood starts to flare from the neck
ROOF = 45.0           # hood slope from horizontal
RH = 8.5              # the hood ends this far from the pin: a wide shingle over the joint
GAPJ = 0.55           # horizontal gap round the pin and under the hood
R_RING = 4.5          # ring outer radius
R_CAV = R_RING + 0.45  # the pocket the ring turns in

# --- legs ---------------------------------------------------------------------
# Each leg is one body: the leg you see outside the flank, an hourglass axle
# through the flank wall, and a keeper on the bed in a pocket inside the body.
# Nothing shows on the outside of the leg, and every bit of it starts on the bed
# or grows out of something that does.
LEG_X = [21.0, 53.8]  # front and hind legs, both sides
LEG_Z = 3.4           # axle height
LEG_NECK = 2.5        # axle diameter at its waist, in the middle of the flank wall
LEG_GAP = 0.4         # between leg and flank, and keeper and wall
LEG_T = 2.4           # leg thickness
LEG_R = 1.2           # rounding of the leg's edges (half its thickness)
WALL = 1.6            # flank wall the axle passes through
KEEP_T = 1.4          # keeper thickness
KEEP_FOOT = 2.2       # width of the keeper's foot on the bed
LEG_SWING = 48.0      # the keeper's pocket lets the leg swing at least this far
PAD_FROM = 4.0        # the pads fill the flanks out from this far off the middle
PAD_R = 4.5           # round flat pad on the flank the leg sits against
# the leg's outline: (x from the axle, z) of the centres of its rounded edge
LEG_SHAPE = [(-2.6, 0.83), (1.2, 0.83), (2.6, 5.0), (1.4, 6.7), (-1.0, 6.6), (-2.4, 4.8)]
PAW_H = 2.3           # the leg is painted dark below this: the paw
PAINT_EDGE = 0.6      # triangles of the head and legs are split to this size for painting

# --- head ---------------------------------------------------------------------
NECK_X, NECK_Z = 18.2, 4.0   # the nod axis
TAB_W = 5.6           # neck tab width
TAB_R = 3.5           # neck tab radius round the axis
TAB_GAP = 0.4
NOD_PIN = 2.5         # stub pin tip diameter
NOD_DEPTH = 1.6       # stub pin length
NOD = 12.5            # the head must nod at least this far each way
# the head is a block with rounded edges: (radius, x, y, z) of the balls at its corners
HEAD = [(3.0, 3.0, 3.0, 2.07), (3.0, 12.5, 4.5, 2.07),      # chin and jaw, on the bed
        (2.4, 2.7, 3.0, 8.8), (2.4, 12.5, 4.1, 10.8)]       # top of the muzzle, crown
EYE = (7.6, 9.3, 1.25)       # x, z, radius: small, high and far back
NOSTRIL = (2.0, 8.4, 0.9)    # y, z, radius: high on the blunt nose
EARS = [((10.9, 11.0), (4.9, 5.7), (11.2, 13.9), 1.9, 1.3)]   # (x, y, z) of root and tip, their radii
EAR_FROM = 12.6           # painted dark above this height
NOSE_BAND = 1.9           # the front this much of the muzzle is painted dark...
NOSE_FROM = 5.2           # ...above this height...
NOSE_HALF_W = 4.7         # ...and this far either side of the middle: a broad flat nose

# --- orange -------------------------------------------------------------------
ORANGE_X = 6.6
ORANGE_R = 4.0        # an 8 mm orange
SHAFT_R = 1.5         # 3 mm shaft down through the head
SHAFT_FOOT = 2.6      # foot radius on the bed
SHAFT_GAP = 0.5

KEYRING_D = 4.5       # hole in the loop behind the rump; 0 for none
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


def body_hull(x0, x1, h0=BODY_H0, h1=BODY_H):
    """A barrel with a flat belly and a flat front that rises from the shoulders
    (h0) to the rump (h1) and ends in a round rump. Every ball sits low enough
    that the bed cuts it where it reaches 45 degrees."""
    r, y = 4.0, HALF_W - 4.0
    lower = [ball(r, x, s * (y - t), 0.69 * r)          # narrower at the neck by t
             for x, t in ((x0 + 1.5, NECK_TAPER), ((x0 + x1) / 2, 0), (x1 - r, 0)) for s in (-1, 1)]
    rs, rr = 5.5, 6.2
    upper = [ball(rs, x0 + 1.5, s * 2.6, h0 - rs) for s in (-1, 1)]
    upper += [ball(rr, x1 - 7.5, s * 2.2, h1 - rr) for s in (-1, 1)]
    hull = mf.Manifold.batch_hull(lower + upper)
    return hull ^ box(x0, x1 + 1, -HALF_W, HALF_W, 0, h1 + 1)


# The V notch each side of a joint, as angles from the body's long axis: the
# ringed segment's front faces, and the pinned segment's rear faces.
RING_EDGE = 90 - (SWING + MARGIN) * (1 - V_SHARE)
PIN_EDGE = 90 + (SWING + MARGIN) * V_SHARE


def joint_solid(px, grow):
    """The front segment's share of a body joint: foot, neck and hood."""
    k = np.tan(np.radians(ROOF))
    top = BODY_H + 5
    prof = [(0, 0), (RF + grow, 0), (RN + grow, HF), (RN + grow, Z0),
            (RH + grow, Z0 + k * (RH - RN)), (RH + grow, top), (0, top)]
    return revolve(prof, px)


def split(body, pins):
    """Cut a body into len(pins) + 1 segments joined by pin-and-ring joints."""
    tall = BODY_H + 5
    far = 200.0
    segs = []
    for i in range(len(pins) + 1):
        seg = body
        if i > 0:                      # this segment's ring, on the pin in front
            px = pins[i - 1]
            a = np.radians(RING_EDGE)
            sector = mf.Manifold.extrude(mf.CrossSection(
                [[(0, 0), (far * np.cos(a), -far * np.sin(a)), (far * np.cos(a), far * np.sin(a))]]), tall)
            ring = mf.Manifold.cylinder(tall, R_RING, R_RING, 96)
            seg = seg ^ ((ring + sector).translate([px, 0, 0]) - joint_solid(px, GAPJ))
        if i < len(pins):              # this segment's pin and hood, at its rear
            px = pins[i]
            b = np.radians(PIN_EDGE)
            front = mf.Manifold.extrude(mf.CrossSection(
                [[(0, 0), (far * np.cos(b), far * np.sin(b)), (-far, far), (-far, -far),
                  (far * np.cos(b), -far * np.sin(b))]]), tall).translate([px, 0, 0]) - \
                mf.Manifold.cylinder(tall, R_CAV, R_CAV, 96).translate([px, 0, 0])
            seg = seg ^ (front + joint_solid(px, 0.0))
        segs.append(seg)
    return segs


# --- legs ---------------------------------------------------------------------
Y_FLANK = HALF_W                       # the pad's flat face
Y_LEG = Y_FLANK + LEG_GAP              # inner face of the leg
Y_WAIST = Y_FLANK - WALL / 2           # the axle's waist, mid wall
Y_KEEP1 = Y_FLANK - WALL - LEG_GAP     # outer face of the keeper
Y_KEEP0 = Y_KEEP1 - KEEP_T
Y_CAV0, Y_CAV1 = Y_KEEP0 - LEG_GAP, Y_FLANK - WALL     # the keeper's pocket
AXLE_FLARE = Y_LEG - Y_WAIST           # the axle widens this much (45 degrees) to either end
KEEP_R = LEG_NECK / 2 + (Y_WAIST - Y_KEEP1) + 0.2      # keeper disc, a little wider than the axle's end
KEEP_REACH = np.hypot(LEG_Z, KEEP_FOOT / 2)            # axle to the corner of the keeper's foot
CAV_HX = KEEP_REACH * np.sin(np.radians(LEG_SWING) + np.arctan2(KEEP_FOOT / 2, LEG_Z)) + LEG_GAP
CAV_TOP = LEG_Z + (KEEP_R + LEG_GAP) * np.sqrt(2)      # ridge of the pocket's 45 degree roof


def teardrop(r, half_foot):
    """(x, z) outline: a circle of radius r at the axle with straight sides down
    to a foot on the bed, so it has no underside flatter than 45 degrees."""
    assert half_foot >= np.sqrt(2) * r - LEG_Z, "sides would be flatter than 45 degrees"
    shape = mf.CrossSection.batch_hull([mf.CrossSection.circle(r, SEG).translate((0, LEG_Z)),
                                        mf.CrossSection.square([2 * half_foot, 0.01]).translate((-half_foot, 0))])
    return [tuple(p) for p in shape.to_polygons()[0]]


def at_x(profile, x):
    return [(px + x, pz) for px, pz in profile]


def leg_pads(x):
    """Flat round pads on both flanks for the legs to sit against."""
    pad = at_x(teardrop(PAD_R, PAD_R), x)
    return prism_xz(pad, -Y_FLANK, -PAD_FROM) + prism_xz(pad, PAD_FROM, Y_FLANK)


def leg_socket(x, side):
    """What a leg takes out of the body: the keeper's pocket, with a pitched
    roof, and the hourglass hole through the flank wall."""
    house = [(-CAV_HX, -1), (CAV_HX, -1), (CAV_HX, CAV_TOP - CAV_HX), (0, CAV_TOP), (-CAV_HX, CAV_TOP - CAV_HX)]
    y0, y1 = sorted([side * Y_CAV0, side * Y_CAV1])
    pocket = prism_xz(at_x(house, x), y0, y1)
    r = LEG_NECK / 2 + CLEAR * np.sqrt(2)
    e = WALL / 2 + 0.3                  # just through each face of the wall, no further
    hole = frustum_y(x, LEG_Z, side * Y_WAIST, r, side * (Y_WAIST + e), r + e) + \
        frustum_y(x, LEG_Z, side * Y_WAIST, r, side * (Y_WAIST - e), r + e)
    return pocket + hole


def leg(x, side):
    """One leg: the leg outside, its axle, and the keeper inside the body."""
    yc = side * (Y_LEG + LEG_R)
    outer = mf.Manifold.batch_hull([ball(LEG_R, x + dx, yc, z) for dx, z in LEG_SHAPE]) ^ \
        box(x - 20, x + 20, -40, 40, 0, 40)
    r0, d = LEG_NECK / 2, 0.1          # d: how far the axle is sunk into the leg and the keeper
    axle = frustum_y(x, LEG_Z, side * Y_WAIST, r0, side * (Y_LEG + d), r0 + AXLE_FLARE + d) + \
        frustum_y(x, LEG_Z, side * Y_WAIST, r0, side * (Y_KEEP1 - d), r0 + (Y_WAIST - Y_KEEP1) + d)
    y0, y1 = sorted([side * Y_KEEP0, side * Y_KEEP1])
    keeper = prism_xz(at_x(teardrop(KEEP_R, KEEP_FOOT / 2), x), y0, y1)
    return outer + axle + keeper


# --- head and orange ----------------------------------------------------------
def reach(m, lo, hi, axis):
    """Furthest m reaches along `axis` inside the probe box lo..hi."""
    probe = m ^ box(lo[0], hi[0], lo[1], hi[1], lo[2], hi[2])
    return probe.bounding_box()[3 + axis]


def orange_profile(seat, grow=0.0, hole=False):
    """(r, z) outline of the orange on its shaft; `hole` gives the bore through the head."""
    s = SHAFT_R + grow
    prof = [(0, 0), (SHAFT_FOOT + grow, 0), (s, SHAFT_FOOT - SHAFT_R), (s, seat)]
    if hole:
        return prof + [(s + 12, seat + 12), (0, seat + 12)]
    lat = ORANGE_R * np.sqrt(0.5)                 # the cone meets the ball at 45 degrees
    zc = seat + (lat - SHAFT_R) + lat
    dimple = 0.9
    t1 = np.arccos(dimple / ORANGE_R)
    prof += [(ORANGE_R * np.cos(t), zc + ORANGE_R * np.sin(t)) for t in np.linspace(-np.pi / 4, t1, 40)]
    return prof + [(0, zc + ORANGE_R * np.sin(t1) - dimple)], zc


def make_head():
    """Returns the head, the orange, and where things ended up (for painting).
    The head is a deep blunt block: a squared muzzle, a flat top that rises to
    the crown, ears far back, eyes high on the sides."""
    blobs = [ball(r, x, s * y, z) for r, x, y, z in HEAD for s in (-1, 1)]
    head = mf.Manifold.batch_hull(blobs) ^ box(0, 40, -20, 20, 0, 40)
    ex, ez, er = EYE
    ny, nz, nr = NOSTRIL
    ys = reach(head, (ex - 0.1, 0, ez - 0.1), (ex + 0.1, 30, ez + 0.1), 1)
    top = reach(head, (ORANGE_X - 0.1, -0.1, 0), (ORANGE_X + 0.1, 0.1, 40), 2)
    nose_x = (head ^ box(-1, 5, ny - 0.1, ny + 0.1, nz - 0.1, nz + 0.1)).bounding_box()[0]
    seat = top - 1.0

    for s in (-1, 1):                              # ears
        (x0, x1), (y0, y1), (z0, z1), r0, r1 = EARS[0]
        head += mf.Manifold.batch_hull([ball(r0, x0, s * y0, z0), ball(r1, x1, s * y1, z1)])
    # the back of the head is a shallow V about the nod axis, so it clears the body
    behind = box(-50, BODY_X0 - TAB_GAP, -50, 50, -50, 50)
    for a in (-NOD, NOD):
        head ^= turn(behind, "y", [NECK_X, 0, NECK_Z], a)
    # neck tab: flat on the bed up to the axis, then a quarter circle and a 45 degree chamfer
    arc = [(NECK_X + TAB_R * np.cos(t), NECK_Z + TAB_R * np.sin(t)) for t in np.linspace(0, np.pi / 2, 17)]
    tab = prism_xz([(11.0, 0), (NECK_X + NECK_Z - TAB_R, 0)] + arc + [(11.0, NECK_Z + TAB_R)],
                   -TAB_W / 2, TAB_W / 2)
    head += tab
    g = CLEAR * np.sqrt(2)
    for s in (-1, 1):
        head -= nod_pin(s, shift=g, extend=1.0)
        head -= mk.cone([ex, s * (ys - er), ez], [0, s, 0], er + 2)                 # eye
        head -= mk.cone([nose_x + nr, s * ny, nz], [-1, 0, 0], nr + 1)              # nostril
    head -= revolve(orange_profile(seat, SHAFT_GAP, hole=True), ORANGE_X)
    prof, zc = orange_profile(seat)
    orange = revolve(prof, ORANGE_X)
    return head, orange, {"eye_y": ys, "seat": seat, "orange_z": zc, "nose_x": nose_x, "head_top": top}


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
    body = body_hull(BODY_X0, BODY_X1)
    for x in LEG_X:
        body += leg_pads(x)
    segs = split(body, PINS)
    segs[0] -= doorway()
    for s in (-1, 1):
        segs[0] += nod_pin(s, extend=0.3)          # rooted a little way inside the prong
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
        joints.append(joint(f"body joint {i + 1}", "z", [PINS[i], 0, 0], moving, SWING, 40, 2.5))
    joints.append(joint("head nod", "y", [NECK_X, 0, NECK_Z], ["head", "orange"], NOD, 40, 2.5))
    return parts, joints, info


TEST_LEG_X, TEST_PIN, TEST_LEN = 7.5, 15.0, 27.0


def make_test():
    """Two body segments, one body joint and one leg: the same joints, a 20 minute print."""
    a, b = split(body_hull(0, TEST_LEN, BODY_H0, BODY_H0) + leg_pads(TEST_LEG_X), [TEST_PIN])
    a -= leg_socket(TEST_LEG_X, 1)
    parts = {"body 1": a, "body 2": b, "leg": leg(TEST_LEG_X, 1)}
    joints = [joint("leg", "y", [TEST_LEG_X, 0, LEG_Z], ["leg"], 45, 180, 15),
              joint("body joint", "z", [TEST_PIN, 0, 0], ["body 2"], SWING, 40, 2.5)]
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


def layer_report(part):
    """Slice a part into layers. Returns (area that reaches more than one layer
    height beyond the layer below, number of islands with nothing under them)."""
    top = part.bounding_box()[5]
    below, hang, islands = None, 0.0, 0
    for z in np.arange(LAYER / 2, top, LAYER):
        now = part.slice(float(z))
        if below is not None:
            hang += (now - below.offset(LAYER + 0.03, mf.JoinType.Round)).area()
            islands += sum((c ^ below).area() < 1e-6 for c in now.decompose())
        below = now
    return hang, islands


def thin_features(parts, info):
    """Thinnest walls (>= MIN_FEATURE) and pins (>= MIN_PIN), from the dimensions."""
    gap_j = (PINS[1] - PINS[0]) if "head" in parts else 99.0
    walls = {
        "leg": LEG_T,
        "leg keeper": KEEP_T,
        "leg keeper foot": KEEP_FOOT,
        "flank wall round the leg axle": WALL,
        "floor of the leg pad beside the pocket": PAD_R - CAV_HX,
        "joint ring wall": min(R_RING, gap_j - R_CAV) - (RF + GAPJ),
        "ring to pocket wall": HALF_W - R_CAV,
        "hood rim": BODY_H0 - (Z0 + np.tan(np.radians(ROOF)) * (RH - RN)),
    }
    pins = {"body pin neck": 2 * RN, "leg axle": LEG_NECK}
    # the leg pocket's corners against the joint pocket behind it and the V face in front of it
    lx, px = (LEG_X[0], PINS[0]) if "head" in parts else (TEST_LEG_X, TEST_PIN)
    walls["leg pocket to joint pocket"] = np.hypot(px - (lx + CAV_HX), Y_CAV0) - R_CAV
    if "head" in parts:
        a = np.radians(RING_EDGE)
        dx = LEG_X[1] - CAV_HX - PINS[-1]
        walls["hind leg pocket to the joint's V face"] = dx * np.sin(a) - Y_CAV1 * np.cos(a)
        b = np.radians(PIN_EDGE)
        dx = PINS[0] - (LEG_X[0] + CAV_HX)
        walls["front leg pocket to the joint's V face"] = dx * np.sin(b) - Y_CAV1 * np.cos(b)
        walls["leg pocket to neck slot"] = Y_CAV0 - (TAB_W / 2 + TAB_GAP)
        socket_r = NOD_PIN / 2 + NOD_DEPTH - CLEAR * np.sqrt(2)      # at the face of the tab
        walls.update({
            "neck tab round its sockets": min(TAB_R, NECK_Z) - socket_r,
            "neck tab between its sockets": TAB_W - 2 * (NOD_DEPTH + CLEAR * np.sqrt(2) - TAB_GAP),
            "wall behind the neck slot": (PINS[0] - R_CAV) - (NECK_X + TAB_R + 0.5),
            "roof over the neck slot": reach(parts["body 1"], (BODY_X0 + 0.3, -0.1, 0), (BODY_X0 + 0.5, 0.1, 40), 2)
            - (NECK_Z + TAB_R + 1.3 + TAB_W / 2 + TAB_GAP),
            "head wall round the orange's shaft": info["eye_y"] - EYE[2] - 1.0 - (SHAFT_R + SHAFT_GAP),
            "head roof over the neck tab": info["head_top"] - 1.0 - (NECK_Z + TAB_R),
            "ear tip": 2 * EARS[0][4],
        })
        pins.update({"head nod pins": NOD_PIN, "orange shaft": 2 * SHAFT_R})
        if KEYRING_D:
            walls["keyring loop"] = 1.8
    return walls, pins


def midair_starts(part):
    """Places where a part would have to start printing in mid-air: points of its
    skin that are lower than everything round them, face downwards, and are not
    on the bed. Returns [(x, y, z)]."""
    m = mk.to_mesh(part)
    v, f = m.vertices, m.faces
    z = v[:, 2]
    e = np.vstack([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
    e = np.vstack([e, e[:, ::-1]])
    tol = 1e-5
    has_lower = np.zeros(len(v), bool)
    np.logical_or.at(has_lower, e[:, 0], z[e[:, 1]] < z[e[:, 0]] - tol)
    grounded = has_lower | (z < 0.02)
    flat = e[np.abs(z[e[:, 0]] - z[e[:, 1]]) <= tol]       # level edges pass "grounded" along
    while True:
        new = grounded.copy()
        np.logical_or.at(new, flat[:, 0], grounded[flat[:, 1]])
        if (new == grounded).all():
            break
        grounded = new
    nz = np.zeros(len(v))
    np.add.at(nz, f.ravel(), np.repeat(m.face_normals[:, 2] * m.area_faces, 3))
    bad = ~grounded & (nz < 0)
    return [tuple(np.round(p, 2)) for p in v[bad]]


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
        for flip in (1, -1):
            pose = dict(extra)
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

    # 5. overhangs past 45 degrees, off the bed
    area = 0.0
    for p in parts.values():
        m = mk.to_mesh(p)
        down = (m.face_normals[:, 2] < -np.sin(np.radians(45)) - 1e-3) & (m.triangles_center[:, 2] > 0.01)
        area += m.area_faces[down].sum()
    if area > OVERHANG_OK:
        raise SystemExit(f"{area:.1f} mm2 overhangs past 45 degrees")
    out.append(f"   overhang past 45 deg {area:.2f} mm2; nothing below the bed")

    # 5b. nothing starts in mid-air: every low point of every part is on the bed
    for n in names:
        lows = midair_starts(parts[n])
        if lows:
            raise SystemExit(f"{n} would start printing in mid-air at {lows[:4]}")
    out.append("   every part starts on the bed: no low point hangs in mid-air")

    # 5c. the same again the way a printer sees it, layer by layer: every island of
    # every layer rests on that part's own layer below (so nothing bridges over a
    # neighbour), and almost none of it reaches more than one layer height out
    worst = 0.0
    for n in names:
        hang, islands = layer_report(parts[n])
        if islands:
            raise SystemExit(f"{n} has {islands} island(s) that start in mid-air")
        if hang > OVERHANG_OK:
            raise SystemExit(f"{n}: {hang:.2f} mm2 of its layers hang past 45 degrees")
        worst = max(worst, hang)
    out.append(f"   sliced at {LAYER} mm: no floating islands; at most {worst:.2f} mm2 of any part "
               "hangs past 45 deg (the crowns of the leg axle holes)")

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
        fine = name == "head" or "leg" in name      # small triangles where a colour edge crosses a face
        m = mk.to_mesh(p.refine_to_length(PAINT_EDGE) if fine else p)
        c = m.triangles_center
        x, y, z = c[:, 0], np.abs(c[:, 1]), c[:, 2]
        lab = np.full(len(m.faces), ORANGE if name == "orange" else BROWN)
        if "leg" in name:
            lab[(y > Y_LEG - 0.01) & (z < PAW_H)] = DARK      # the paws
        if name == "head":
            lab[(x < NOSE_BAND) & (z > NOSE_FROM) & (y < NOSE_HALF_W)] = DARK     # the broad flat nose
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
            apex = info["nose_x"] + nr
            lab[(x < apex + 0.01) & (np.hypot(y - ny, z - nz) < apex - x + 0.03)] = BLACK
        if name == "orange":
            rad = np.hypot(x - ORANGE_X, c[:, 1])
            lab[(z < info["seat"] + 0.01) & (rad < SHAFT_FOOT + 0.1)] = BROWN       # the shaft, hidden in the head
            lab[(rad < 1.3) & (z > info["orange_z"] + ORANGE_R - 1.2)] = DARK      # the stalk dimple
        if shown:                                   # the same mesh, moved to where the part is shown
            a, b = mk.to_mesh(p).vertices, mk.to_mesh(shown[name]).vertices
            assert len(a) == len(b)
            ca, cb = a.mean(0), b.mean(0)
            u, _, vt = np.linalg.svd((a - ca).T @ (b - cb))
            rot = (u @ vt).T
            m.vertices = (m.vertices - ca) @ rot.T + cb
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
