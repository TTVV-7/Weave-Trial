"""Pocket capybara: a print-in-place articulated fidget, as a painted 3MF and a plain STL.

About 60 mm nose to rump, printed standing on its belly in one piece, no supports.
The body is four segments that wiggle side to side, the four legs swing on pins,
the head nods, and an orange on its head spins. An original design.

How it holds together with nothing printed over a gap:
  * body joints: every segment ends in a ball (an upright cylinder below, a sphere
    above) centred on the joint's upright axis; the next segment's front is the
    matching socket, so the seam is a thin line that never opens when it bends.
    Inside the ball, hidden by the socket, the next segment hooks over a low rim:
    an arc-shaped tongue standing on the bed, joined to the socket by a bridge
    that rises at 45 degrees over the rim. The ball's own roof rises at 45
    degrees over that bridge. Nothing is flatter than 45 degrees.
  * legs: a cone pin on the flank widens outwards inside the leg, under the leg's
    closed outer skin. The pin's underside is cut at 45 degrees rising outwards,
    so it never starts in mid-air.
  * head: its back is a hollow cylinder round the nod axis and the body's front
    is the matching drum, so that seam stays closed too. A tab between two
    prongs, on two stub cone pins, is the hinge.
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
    [0x4E, 0x30, 0x1C],   # T2 dark brown: nose, feet, ears
    [0x1A, 0x1A, 0x1A],   # T3 black: eyes, nostrils
    [0xF2, 0x8C, 0x1A],   # T4 orange: the orange
])
BROWN, DARK, BLACK, ORANGE = range(4)

CLEAR = 0.35          # gap square to a surface
MIN_FEATURE = 0.8
MIN_PIN = 2.5
OVERHANG_OK = 1.0     # mm2 of steeper overhang allowed, for tiny details
SEG = 64
LENGTH = (55.0, 62.0)  # nose to rump
MAX_H, MAX_W = 21.0, 24.0

# --- body ---------------------------------------------------------------------
BODY_X0 = 14.0        # the barrel starts here; the nod drum cuts its front
BODY_X1 = 61.6        # rump
FLANK = 8.5           # half width; the sides are cut flat here
AXES = [25.0, 34.3, 43.6]   # x of the three upright joint axes
SWING = 25.0          # each body joint wiggles this far either way
MARGIN = 4.0          # degrees left over at full swing

# body joint, as radius/height round the joint's upright axis
R_BALL = 10.2         # ball radius (cylinder up to Z_C, sphere above)
Z_C = 8.0             # height of the sphere's centre
G_SEAM = 0.4          # gap between ball and socket
LAT = 44.0            # the socket follows the sphere up to this latitude, then leans at 45
X_CUT = 7.5           # the socket's lip is cut blunt this far behind the axis
R_CORE = 5.2          # inner wall of the pocket the hook lives in
T_IN, T_OUT = 5.7, 8.2      # the hook's tongue
R_RIM = 8.7           # the rim the tongue hooks behind runs from here to R_BALL
Z_RIM = 2.6           # rim height at its walls (it has a pitched top)
Z_A = 3.8             # where the ball's roof starts to lean out over the hook
G_SLOPE = 0.55        # horizontal gap between 45 degree faces
HOOK_HALF = 14.0      # half angle of the tongue and bridge

# --- legs ---------------------------------------------------------------------
LEG_X = [AXES[0] - 4.3, AXES[2] + 13.3]   # front and hind legs, both sides
LEG_Z = 6.2           # pin height
LEG_NECK = 2.5        # pin diameter at the flank; it widens outwards at 45 degrees
LEG_GAP = 0.4         # between leg and flank
LEG_D = 1.2           # how far the pin reaches into the leg
LEG_END = 0.4         # gap beyond the pin's end
LEG_SKIN = 0.9        # the leg's closed outer skin
LEG_T = LEG_D + LEG_END + LEG_SKIN
R_HAUNCH = 4.6
LEG_CHAMFER = 0.6
LEG_BULGE = 0.5       # height of the dome on the haunch's outer face
LEG_BULGE_R = 3.6     # and its radius
PAW_Z = 2.95          # painted dark below this

# --- head ---------------------------------------------------------------------
NECK_X, NECK_Z = 23.6, 6.6   # the nod axis
R_NOD = 9.4           # the drum on the front of the body
NECK_GAP = 0.4
TAB_W = 5.0           # neck tab width
TAB_RU = 3.1          # tab radius above the axis
TAB_C = 4.2           # the tab's 45 degree underside meets the axis height this far back
TAB_GAP = 0.4
NOD_PIN = 2.5         # stub pin tip diameter
NOD_DEPTH = 1.4       # stub pin length
NOD = 15.0            # the head must nod at least this far each way
HEAD_TOP = 13.4
EYE = (11.8, 10.3, 1.15)     # x, z, radius
NOSTRIL = (1.8, 8.6, 0.85)   # y, z, radius
EARS = [((14.6, 15.2), (4.9, 5.6), (11.0, 13.9), 2.0, 1.5)]   # (x, y, z) of root and tip, their radii
EAR_FROM = 12.3           # painted dark above this height
NOSE_BAND = 2.2           # the front this much of the muzzle is painted dark...
NOSE_FROM = 5.2           # ...above this height, where the mouth is
MOUTH = 0.5               # depth of the mouth groove (a V with 45 degree faces)

# --- orange -------------------------------------------------------------------
ORANGE_X = 10.2
ORANGE_R = 4.0        # an 8 mm orange
ORANGE_SINK = 1.2     # how far its cone sits into the head
SHAFT_R = 1.5         # 3 mm shaft down through the head
SHAFT_FOOT = 2.6      # foot radius on the bed
SHAFT_GAP = 0.5

KEYRING_D = 3.4       # hole in the loop on the back; 0 for none
KEYRING_X = 56.5
KEYRING_Z = 16.0      # hole centre
KEYRING_T = 2.4       # loop thickness
KEYRING_WALL = 1.9


# --- building blocks ----------------------------------------------------------
def ball(r, x, y, z):
    return mf.Manifold.sphere(r, SEG).translate([x, y, z])


def box(x0, x1, y0, y1, z0, z1):
    return mf.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def revolve(profile, at):
    """Solid of revolution about the vertical axis through (at, 0); profile is (r, z)."""
    return mf.CrossSection([profile]).revolve(128).translate([at, 0, 0])


def wedge(at, half):
    """Everything within `half` degrees of straight back from the axis at x = at."""
    a, far = np.radians(half), 60.0
    tri = [(0, 0), (far * np.cos(a), -far * np.sin(a)), (far * np.cos(a), far * np.sin(a))]
    return mf.Manifold.extrude(mf.CrossSection([tri]), 40).translate([at, 0, -1])


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


def drum(r):
    """The cylinder of radius r round the nod axis."""
    return mf.Manifold.cylinder(60, r, r, 180).rotate([-90, 0, 0]).translate([NECK_X, -30, NECK_Z])


def turn(m, axis, point, deg):
    """m turned deg about the 'y' or 'z' axis through point."""
    p = np.asarray(point, float)
    rot = [0, deg, 0] if axis == "y" else [0, 0, deg]
    return m.translate(list(-p)).rotate(rot).translate(list(p))


def barrel(x0, x1, tops):
    """A barrel with a flat belly and flat flanks. `tops` lists (x, height) along the
    back. Every sphere sits low enough that the bed cuts it where it reaches 45 degrees."""
    blobs = [ball(3.5, x, s * 5.6, 2.415) for x in (x0 + 3.5, x1 - 4.3) for s in (-1, 1)]
    blobs += [ball(6.2, x, s * 2.6, top - 6.2) for x, top in tops for s in (-1, 1)]
    hull = mf.Manifold.batch_hull(blobs)
    return hull ^ box(x0 - 1, x1 + 1, -FLANK, FLANK, 0, 40)


# --- body joints --------------------------------------------------------------
def arc(r, a0, a1, n=40):
    return [(r * np.cos(t), Z_C + r * np.sin(t)) for t in np.linspace(np.radians(a0), np.radians(a1), n)]


def ball_end(at):
    """The front segment's rounded end: a cylinder up to Z_C, a sphere above."""
    return revolve([(0, 0), (R_BALL, 0)] + arc(R_BALL, 0, 90)[:-1] + [(0, Z_C + R_BALL)], at)


def socket_space(at):
    """What the rear segment must keep out of: the ball grown by the seam gap. Above
    latitude LAT the socket stops following the sphere and leans in at 45 degrees."""
    r = R_BALL + G_SEAM
    lip = arc(r, 0, LAT)
    return revolve([(0, -1), (r, -1)] + lip + [(0, lip[-1][1] + lip[-1][0])], at)


def hook_peak():
    r = (T_OUT + R_BALL + G_SLOPE - 0.1) / 2
    return r, Z_RIM + 0.1 + (r - T_OUT)


def hook(at):
    """The rear segment's hook inside the ball: tongue on the bed, bridge over the rim."""
    far = R_BALL + 1.5
    top = lambda r: Z_A + r - R_CORE - G_SLOPE
    prof = [(T_IN, 0), (T_OUT, 0), (T_OUT, Z_RIM + 0.1), hook_peak(), (R_BALL + G_SLOPE, Z_RIM),
            (far, Z_RIM), (far, top(far)), (T_IN, top(T_IN))]
    return revolve(prof, at) ^ wedge(at, HOOK_HALF)


def pocket(at):
    """The space inside the ball the hook swings in, under a roof rising at 45 degrees."""
    far = R_BALL + 0.4
    prof = [(R_CORE, -1), (far, -1), (far, Z_A + far - R_CORE), (R_CORE, Z_A)]
    return revolve(prof, at) ^ wedge(at, HOOK_HALF + SWING + MARGIN)


def rim(at):
    mid = (R_RIM + R_BALL) / 2
    prof = [(R_RIM, 0), (R_BALL, 0), (R_BALL, Z_RIM), (mid, Z_RIM + mid - R_RIM), (R_RIM, Z_RIM)]
    return revolve(prof, at) ^ wedge(at, HOOK_HALF + SWING + MARGIN + 2)


def split(body, axes):
    """Cut a body into len(axes) + 1 segments joined by ball-and-hook joints."""
    segs = []
    for i in range(len(axes) + 1):
        seg = body
        if i > 0:                      # this segment's socket and hook, round the ball in front
            at = axes[i - 1]
            seg = seg ^ ((box(at + X_CUT, 500, -100, 100, -1, 100) - socket_space(at)) + hook(at))
        if i < len(axes):              # this segment's ball, at its rear
            at = axes[i]
            seg = seg ^ ((box(-100, at, -100, 100, -1, 100) + ball_end(at)) - pocket(at) + rim(at))
        segs.append(seg)
    return segs


# --- legs ---------------------------------------------------------------------
def leg_pin(x, side):
    """The cone pin on the flank: LEG_NECK across at the flank, widening outwards.
    Its underside is cut by a plane rising outwards at 45 degrees from the bottom
    of the neck, so every layer of it rests on the one below."""
    r0 = LEG_NECK / 2
    reach = LEG_GAP + LEG_D
    pin = frustum_y(x, LEG_Z, FLANK, r0, FLANK + reach, r0 + reach)
    b = LEG_Z - r0
    pin ^= prism_yz([(FLANK - 3, b - 3), (FLANK + 6, b + 6), (FLANK + 6, b + 30), (FLANK - 3, b + 30)], x - 10, x + 10)
    pin += frustum_y(x, LEG_Z, FLANK - 1.5, r0, FLANK, r0)
    return pin if side > 0 else pin.mirror([0, 1, 0])


def leg_outline(x):
    """The leg seen from the side: a round haunch tapering forwards and down to a foot.
    One convex shape; every circle sits low enough that the bed cuts it at 45 degrees."""
    disc = lambda r, cx, cz: mf.CrossSection.circle(r, 72).translate([cx, cz])
    up = mf.CrossSection.square([60, 40]).translate([x - 30, 0])
    return mf.CrossSection.batch_hull([disc(R_HAUNCH, x, LEG_Z), disc(1.7, x - 4.6, 1.17), disc(1.7, x + 1.0, 1.17)]) ^ up


def leg(x, side):
    c = LEG_CHAMFER
    cs = leg_outline(x)
    m = mf.Manifold.batch_hull([mf.Manifold.extrude(cs, LEG_T - c),
                                mf.Manifold.extrude(cs.offset(-c, mf.JoinType.Round), LEG_T)])
    m = m.rotate([90, 0, 0]).mirror([0, 1, 0]).translate([0, FLANK + LEG_GAP, 0])
    y_out = FLANK + LEG_GAP + LEG_T
    rho = (LEG_BULGE_R ** 2 + LEG_BULGE ** 2) / (2 * LEG_BULGE)      # a shallow dome over the haunch
    m += ball(rho, x, y_out + LEG_BULGE - rho, LEG_Z) ^ box(x - 20, x + 20, y_out - 0.01, y_out + 5, 0, 40)
    g = CLEAR * np.sqrt(2)
    r0 = LEG_NECK / 2 + g
    end = LEG_GAP + LEG_D + LEG_END
    m -= frustum_y(x, LEG_Z, FLANK - 0.5, r0 - 0.5, FLANK + end, r0 + end)
    return m if side > 0 else m.mirror([0, 1, 0])


def leg_cavity_r():
    return LEG_NECK / 2 + CLEAR * np.sqrt(2) + LEG_GAP + LEG_D + LEG_END


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
    """Returns the head, the orange, and where things ended up (for painting)."""
    blobs = [ball(2.8, 2.8, s * 3.3, z) for s in (-1, 1) for z in (1.93, 8.9)]              # blunt muzzle
    blobs += [ball(4.0, x, s * 3.3, z) for x in (10.5, 17.0) for s in (-1, 1) for z in (2.76, HEAD_TOP - 4.0)]
    head = mf.Manifold.batch_hull(blobs) ^ box(0, 40, -20, 20, 0, 40)
    ex, ez, er = EYE
    ys = reach(head, (ex - 0.1, 0, ez - 0.1), (ex + 0.1, 30, ez + 0.1), 1)
    top = reach(head, (ORANGE_X - 0.1, -0.1, 0), (ORANGE_X + 0.1, 0.1, 40), 2)
    seat = top - ORANGE_SINK

    for s in (-1, 1):                              # ears
        (x0, x1), (y0, y1), (z0, z1), r0, r1 = EARS[0]
        head += mf.Manifold.batch_hull([ball(r0, x0, s * y0, z0), ball(r1, x1, s * y1, z1)])
    head -= drum(R_NOD + NECK_GAP)                 # the hollow back, round the nod axis
    # neck tab: flat on the bed, a 45 degree underside behind, a half circle over the axis
    over = [(NECK_X + TAB_RU * np.cos(t), NECK_Z + TAB_RU * np.sin(t)) for t in np.linspace(0, np.pi, 25)]
    tab = prism_xz([(12.5, 0), (NECK_X + TAB_C - NECK_Z, 0), (NECK_X + TAB_C, NECK_Z)] + over + [(12.5, NECK_Z)],
                   -TAB_W / 2, TAB_W / 2)
    head += tab
    g = CLEAR * np.sqrt(2)
    for s in (-1, 1):
        head -= nod_pin(s, shift=g, extend=1.0)
        head -= mk.cone([ex, s * (ys - er), ez], [0, s, 0], er + 2)                 # eye
        ny, nz, nr = NOSTRIL
        head -= mk.cone([nr, s * ny, nz], [-1, 0, 0], nr + 1)                       # nostril
    head -= prism_xz([(-1, NOSE_FROM - MOUTH - 1), (MOUTH, NOSE_FROM), (-1, NOSE_FROM + MOUTH + 1)], -4.2, 4.2)   # mouth
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


def doorway_eave():
    return NECK_Z + TAB_RU + 0.5


def doorway():
    """The slot in the front of the body the neck tab sits in, with a pitched roof."""
    hw = TAB_W / 2 + TAB_GAP
    eave = doorway_eave()
    return prism_yz([(-hw, -1), (hw, -1), (hw, eave), (0, eave + hw), (-hw, eave)],
                    NECK_X - R_NOD - 1, NECK_X + TAB_C + 0.5)


def keyhole(y0, y1):
    """The keyring hole: a circle with a 45 degree peak, so its top needs no bridge."""
    r = KEYRING_D / 2
    pts = [(KEYRING_X + r * np.cos(t), KEYRING_Z + r * np.sin(t)) for t in np.linspace(3 * np.pi / 4, 9 * np.pi / 4, 40)]
    return prism_xz(pts + [(KEYRING_X, KEYRING_Z + r * np.sqrt(2))], y0, y1)


def keyring(seg):
    """A low loop standing on the back; the hole dips into the back as a shallow groove.
    The loop is a disc on a foot wide enough to carry it at 45 degrees."""
    r = KEYRING_D / 2 + KEYRING_WALL
    disc = [(KEYRING_X + r * np.cos(t), KEYRING_Z + r * np.sin(t)) for t in np.linspace(0, 2 * np.pi, 64, endpoint=False)]
    foot = r * np.sqrt(0.5) + 0.05
    loop = prism_xz(disc, -KEYRING_T / 2, KEYRING_T / 2) + box(KEYRING_X - foot, KEYRING_X + foot,
                                                               -KEYRING_T / 2, KEYRING_T / 2, 10.0, KEYRING_Z)
    return seg + (loop - socket_space(AXES[-1])) - keyhole(-20, 20)


# --- the two models -----------------------------------------------------------
def joint(name, axis, point, moving, want, limit, step):
    return dict(name=name, axis=axis, point=point, moving=moving, want=want, limit=limit, step=step)


def make_capybara():
    """parts: name -> Manifold.  joints: in the order to pose them (leaves first)."""
    head, orange, info = make_head()
    body = barrel(BODY_X0, BODY_X1, [(BODY_X0 + 6.2, 13.7), (46.0, 15.5), (BODY_X1 - 6.2, 15.5)])
    segs = split(body, AXES)
    segs[0] ^= drum(R_NOD) + box(NECK_X, 500, -100, 100, -1, 100)
    segs[0] -= doorway()
    for s in (-1, 1):
        segs[0] += nod_pin(s) + frustum_y(NECK_X, NECK_Z, s * (TAB_W / 2 + TAB_GAP + 1),
                                          NOD_PIN / 2 + NOD_DEPTH, s * (TAB_W / 2 + TAB_GAP), NOD_PIN / 2 + NOD_DEPTH)
        segs[0] += leg_pin(LEG_X[0], s)
        segs[-1] += leg_pin(LEG_X[1], s)
    if KEYRING_D:
        segs[-1] = keyring(segs[-1])
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
    for i in reversed(range(len(AXES))):
        moving = [f"body {k + 1}" for k in range(i + 1, len(segs))] + hind
        joints.append(joint(f"body joint {i + 1}", "z", [AXES[i], 0, 0], moving, SWING, 40, 5))
    joints.append(joint("head nod", "y", [NECK_X, 0, NECK_Z], ["head", "orange"], NOD, 40, 2.5))
    info["axes"] = AXES
    return parts, joints, info


def make_test():
    """Two body segments, one body joint and one leg: the same joints, a 20 minute print."""
    at = 9.0
    a, b = split(barrel(0, 30, [(6.2, 14.5), (23.8, 14.5)]), [at])
    x = at - 4.3
    a += leg_pin(x, 1)
    parts = {"body 1": a, "body 2": b, "leg": leg(x, 1)}
    joints = [joint("leg", "y", [x, 0, LEG_Z], ["leg"], 45, 180, 15),
              joint("body joint", "z", [at, 0, 0], ["body 2"], SWING, 40, 5)]
    return parts, joints, {"axes": [at]}


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


def islands(part, layer=0.2):
    """Slice the part in print layers. Returns the height of the first piece of any
    layer that has nothing of the layer below under it (it would start in mid-air)."""
    top = part.bounding_box()[5]
    below = None
    for z in np.arange(layer / 2, top, layer):
        now = part.slice(float(z))
        if below is not None:
            grown = below.offset(layer + 0.1, mf.JoinType.Round)
            for piece in now.decompose():
                if piece.area() > 0.02 and (piece ^ grown).area() < 1e-4:
                    return float(z)
        below = now
    return None


def thin_features(parts, info):
    """Thinnest walls (>= MIN_FEATURE) and pins (>= MIN_PIN), from the dimensions."""
    g = CLEAR * np.sqrt(2)
    hook_r, hook_z = hook_peak()
    bridge = (Z_A + hook_r - R_CORE - G_SLOPE - hook_z) * np.sqrt(0.5)       # square to its 45 degree faces
    at = info["axes"][0]
    rear = parts["body 2"]
    horn = (reach(rear, (at + X_CUT, 0, 0.2), (at + X_CUT + 0.05, 30, 0.4), 1)
            - np.sqrt((R_BALL + G_SEAM) ** 2 - (X_CUT + 0.05) ** 2))
    walls = {
        "leg skin over its pin": LEG_SKIN,
        "leg round its pin": min(R_HAUNCH, LEG_Z) - leg_cavity_r(),
        "leg skin at its chamfer": (R_HAUNCH + LEG_T - LEG_CHAMFER - leg_cavity_r() - (LEG_D + LEG_END)) * np.sqrt(0.5),
        "rim the hook holds": R_BALL - R_RIM,
        "socket lip at the flank (2nd layer up)": horn,
        "ball wall in front of the hook's pocket": R_CORE - (R_BALL + G_SEAM - (AXES[1] - AXES[0])),
    }
    pins = {"leg pin": LEG_NECK,
            "body hook (tongue, bridge, width)": min(T_OUT - T_IN, bridge, 2 * T_IN * np.sin(np.radians(HOOK_HALF)))}
    if "head" in parts:
        socket_r = NOD_PIN / 2 + NOD_DEPTH - g                               # at the face of the tab
        hw = TAB_W / 2 + TAB_GAP
        ex, ez, er = EYE
        walls.update({
            "neck tab round its sockets": min(TAB_RU, TAB_C * np.sqrt(0.5), NECK_Z) - socket_r,
            "neck tab between its sockets": TAB_W - 2 * (NOD_DEPTH + g - TAB_GAP),
            "wall behind the neck slot": (AXES[0] + np.sqrt(R_CORE ** 2 - hw ** 2)) - (NECK_X + TAB_C + 0.5),
            "roof over the neck slot": reach(parts["body 1"], (NECK_X - 0.1, -0.1, 0), (NECK_X + 0.1, 0.1, 40), 2)
            - (doorway_eave() + hw),
            "head wall round the orange's shaft": np.hypot(ex - ORANGE_X, info["eye_y"] - er) - (SHAFT_R + SHAFT_GAP),
            "ear tip": 2 * EARS[0][4],
        })
        pins.update({"head nod pins": NOD_PIN, "orange shaft": 2 * SHAFT_R})
        if KEYRING_D:
            walls["keyring loop"] = min(KEYRING_T, KEYRING_WALL - KEYRING_D / 2 * (np.sqrt(2) - 1))
    return walls, pins


def check(parts, joints, info):
    """Refuse to go on unless it prints in place and every joint moves. Returns report lines."""
    names = list(parts)
    # 1. every moving part is its own single body, standing on the bed, clear of the others as printed
    tight = 9.0
    for n in names:
        if len(parts[n].decompose()) != 1:
            raise SystemExit(f"{n} is not one piece")
        lo = parts[n].bounding_box()[2]
        if lo < -1e-6:
            raise SystemExit(f"{n} pokes below the bed")
        if lo > 1e-6:
            raise SystemExit(f"{n} does not start on the bed")
        z = islands(parts[n])
        if z is not None:
            raise SystemExit(f"{n} has a piece that starts in mid-air at z = {z:.1f}")
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if (parts[a] ^ parts[b]).volume() > 1e-6:
                raise SystemExit(f"{a} and {b} are fused as printed")
            gap = parts[a].min_gap(parts[b], 2.0)
            if gap < CLEAR - 0.005:
                raise SystemExit(f"{a} and {b} are only {gap:.2f} mm apart as printed")
            tight = min(tight, gap)
    out = [f"{len(names)} separate bodies, each starting on the bed with no layer starting in mid-air; "
           f"tightest gap as printed {tight:.2f} mm"]

    # 2. each joint through its range
    for j in joints:
        free, gap = sweep(parts, joints, j)
        if min(free) < j["want"] - 1e-6:
            raise SystemExit(f"{j['name']} only swings +{free[0]:.0f}/-{free[1]:.0f} degrees, wanted {j['want']:.0f}")
        rng = "full circle" if min(free) >= 180 else f"+{free[0]:g}/-{free[1]:g} deg"
        out.append(f"   {j['name']:<16} {rng:<16} tightest gap {gap:.2f} mm")

    # 3. the body curled up and S-bent, legs and head turned too (each way)
    body = [j for j in joints if j["name"].startswith("body joint")]
    others = [j for j in joints if j not in body and j["want"] < 180]
    for label, signs in (("curled", [1, 1, 1]), ("S-bent", [1, -1, 1])):
        for flip in (1, -1):
            for way in (1, -1):
                pose = {j["name"]: way * j["want"] for j in others}
                pose.update({j["name"]: flip * s * SWING for j, s in zip(body, signs)})
                p = posed(parts, joints, pose)
                ks = list(p)
                for i, a in enumerate(ks):
                    for b in ks[i + 1:]:
                        if (p[a] ^ p[b]).volume() > 1e-6:
                            raise SystemExit(f"{a} hits {b} with the body {label}")
    out.append("   curled and S-bent with every joint at its limit, either way: nothing collides")

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

    # 6. thin features
    walls, pins = thin_features(parts, info)
    for what, limit in ((walls, MIN_FEATURE), (pins, MIN_PIN)):
        for k, v in what.items():
            if v < limit - 1e-6:
                raise SystemExit(f"{k} is {v:.2f} mm, under {limit}")
    out.append("   thinnest walls: " + ", ".join(f"{k} {v:.2f}" for k, v in sorted(walls.items(), key=lambda kv: kv[1])[:5]))
    out.append("   pins: " + ", ".join(f"{k} {v:.2f}" for k, v in pins.items()))

    # 7. overall size (the full model only)
    if "head" in parts:
        lo, hi = np.array(union(parts.values()).bounding_box()).reshape(2, 3)
        size = hi - lo
        if not LENGTH[0] <= size[0] <= LENGTH[1] or size[1] >= MAX_W or size[2] >= MAX_H:
            raise SystemExit(f"size {size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} is outside the brief")
        back = max(parts[n].bounding_box()[5] for n in parts if n.startswith("body"))
        out.append(f"   nose to rump {size[0]:.1f}, width {size[1]:.1f}, height {size[2]:.1f} (top of the back's loop {back:.1f})")
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
            lab[(z < PAW_Z) & (y > FLANK + LEG_GAP + 0.02)] = DARK          # the feet
        if name == "head":
            lab[(x < NOSE_BAND) & (z > NOSE_FROM)] = DARK     # the broad flat nose
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
            lab[(x > 0.005) & (x < MOUTH + 0.01) & (np.abs(z - NOSE_FROM) < MOUTH - x + 0.03) & (y < 4.25)] = BLACK   # mouth
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
