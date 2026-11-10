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
    prongs, on two stub cone pins, is the hinge. The tab's neck strap meets a
    lintel in the body when the nose goes up, and a horn on top of the tab meets
    the front wall of its pocket when the nose goes down: two solid stops.
  * orange: its shaft runs down through the head to a flared foot on the bed.

Before writing anything the script checks that every part is one separate body,
swings every joint through its range, and measures overhangs and thin features
on sections of the solids themselves.

Run: python3 make_capybara.py   (needs numpy, trimesh, manifold3d)
"""
import pathlib
import sys
import numpy as np
import trimesh
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
BED_GAP = 0.6         # bodies are at least this far apart in the first layer
MIN_PATCH = 1.0       # mm2: no painted patch smaller than this
SEG = 64
LENGTH = (55.0, 62.0)  # nose to rump
MAX_H, MAX_W = 21.0, 24.0

# --- body ---------------------------------------------------------------------
BODY_X0 = 14.0        # the barrel starts here; the nod drum cuts its front
BODY_X1 = 61.6        # rump
FLANK = 8.5           # half width; the sides are cut flat here
BELLY_R = 4.5         # the belly's rounded corners
BELLY_Z = 0.69 * BELLY_R     # their height: the bed cuts them where they are just steeper than 45 degrees
TOP_R, TOP_Y = 7.0, 1.5      # the back is two spheres this size, this far off the middle
# (x, height) along the back: shoulders, a dip behind them, then up to the rump
SHOULDERS = [(21.0, 13.9), (26.0, 14.4), (32.5, 13.7)]
RUMP = [(31.0, 13.7), (41.0, 15.0), (49.5, 15.8), (54.6, 15.3)]
AXES = [26.2, 35.2, 44.2]   # x of the three upright joint axes
SWING = 25.0          # each body joint wiggles this far either way
MARGIN = 4.0          # degrees left over at full swing

# body joint, as radius/height round the joint's upright axis
R_BALL = 10.2         # ball radius (cylinder up to Z_C, sphere above)
Z_C = 8.0             # height of the sphere's centre
G_SEAM = 0.4          # gap between ball and socket
LAT = 44.0            # the socket follows the sphere up to this latitude, then leans at 45
X_CUT = 8.0           # the socket's lip is cut blunt this far behind the axis
LIP_MIN = 1.0         # ...and cut back over the top of the ball to where it is this thick
HORN_MIN = 1.4        # ...and near the bed to where the horn beside the socket is this wide
R_CORE = 3.6          # inner wall of the pocket the hook lives in
T_IN, T_OUT = 4.1, 7.55     # the hook's tongue
R_RIM = 8.0           # the rim the tongue hooks behind runs from here to R_BALL
Z_RIM = 2.6           # rim height at its walls (it has a pitched top)
Z_A = 3.4             # where the ball's roof starts to lean out over the hook
G_SLOPE = 0.55        # vertical gap between 45 degree faces
HOOK_HALF = 18.0      # half angle of the tongue and bridge
BLEND = 0.35          # the tongue is blended into the bridge with a facet this big
BED_CHAMFER = 0.3     # both sides of a seam are chamfered where they meet the bed
TONGUE_CHAMFER = 0.3  # and so is the foot of the tongue

# --- legs ---------------------------------------------------------------------
LEG_Z = 7.2           # pin height
LEG_NECK = 2.5        # pin diameter at the flank; it widens outwards at 45 degrees
LEG_GAP = 0.4         # between leg and flank
LEG_END = 0.4         # gap beyond the pin's end
LEG_SKIN = 0.9        # the leg's closed outer skin
LEG_CHAMFER = 0.5
LEG_BULGE = 0.5       # height of the dome on the haunch's outer face
PAW_Z = 2.4           # painted dark below this
# x of the pin, haunch radius, how far the pin reaches into the leg, a second disc
# that makes the haunch a thigh (x and z from the pin, radius), then the hock (heel)
# and toe as (x from the pin, radius): each is a disc resting on the bed
LEGS = {"front": dict(x=20.9, haunch=4.6, d=1.2, thigh=(0.5, 1.2, 3.6), hock=(1.2, 1.4), toe=(-2.6, 1.2)),
        "hind": dict(x=56.0, haunch=4.6, d=1.2, thigh=(1.5, 1.5, 3.9), hock=(1.5, 1.7), toe=(-2.9, 1.3))}

# --- head ---------------------------------------------------------------------
NECK_X, NECK_Z = 23.6, 6.6   # the nod axis
R_NOD = 9.4           # the drum on the front of the body
NECK_GAP = 0.4
TAB_X0 = 12.5         # the neck strap starts here, inside the head
TAB_W = 4.6           # neck tab width
TAB_RU = 3.3          # the tab is a disc of this radius round the axis
TAB_GAP = 0.4
STRAP_Z = 5.9         # ridge of the neck strap (it has a pitched top)
NOD_PIN = 2.5         # stub pin tip diameter
NOD_DEPTH = 1.0       # stub pin length
NOD = 15.0            # the head must nod at least this far each way
NOD_STOP = 18.5       # ...and is stopped here, both ways
NOD_MAX = 30.0        # the check fails if it nods further than this
HORN_R = 6.0          # the horn on top of the tab reaches this far from the axis
HORN_HALF = 45.0 - NOD_STOP   # its half angle: its pocket's walls must lean at 45
HEAD_TOP = 13.4
EYE = (8.4, 10.4, 1.2, 25.0)     # x, z, radius, and how far it is turned to face forwards
NOSTRIL = (1.7, 9.0, 0.8)    # y, z, radius
EARS = [((14.6, 15.2), (4.9, 5.6), (11.0, 13.9), 2.0, 1.5)]   # (x, y, z) of root and tip, their radii
EAR_FROM = 12.3           # painted dark above this height
NOSE = (2.0, 4.0, 2.5)    # the dark nose pad is where an ellipsoid with these radii, centred on...
NOSE_AT = (0.3, 10.0)     # ...this x and z, the top front edge of the muzzle, cuts the head
MOUTH_Z, MOUTH_Y = 4.5, 2.1   # the mouth: a short groove, joined to the nose by a groove down the middle
MOUTH = 0.5               # depth of those grooves (a V with 45 degree faces)

# --- orange -------------------------------------------------------------------
ORANGE_X = 9.6
ORANGE_R = 4.0        # an 8 mm orange
ORANGE_SINK = 1.2     # how far its cone sits into the head
SHAFT_R = 2.25        # 4.5 mm shaft down through the head
SHAFT_FOOT = 3.4      # foot radius on the bed
SHAFT_GAP = 0.5       # round the shaft, and square to the two cones
ORANGE_BROWN = 0.4    # the shaft's colour runs this far up into the cone under the ball

KEYRING_D = 3.4       # hole in the lug on the back; 0 for none
KEYRING_X = 57.1
KEYRING_Z = 14.6      # hole centre
KEYRING_T = 4.5       # lug thickness
KEYRING_WALL = 2.1    # round the hole and over its peak
KEYRING_FOOT = 1.5    # the lug spreads this much at its foot


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


def frustum_y(x, z, y0, r0, y1, r1, seg=SEG):
    """Cone frustum on a line parallel to y, radius r0 at y0 and r1 at y1."""
    lo, hi = (y0, r0), (y1, r1)
    if y1 < y0:
        lo, hi = hi, lo
    c = mf.Manifold.cylinder(hi[0] - lo[0], lo[1], hi[1], seg)
    return c.rotate([-90, 0, 0]).translate([x, lo[0], z])


def drum(r):
    """The cylinder of radius r round the nod axis."""
    return mf.Manifold.cylinder(60, r, r, 180).rotate([-90, 0, 0]).translate([NECK_X, -30, NECK_Z])


def turn(m, axis, point, deg):
    """m turned deg about the 'y' or 'z' axis through point."""
    p = np.asarray(point, float)
    rot = [0, deg, 0] if axis == "y" else [0, 0, deg]
    return m.translate(list(-p)).rotate(rot).translate(list(p))


def barrel(x0, x1, groups):
    """A barrel with a flat belly and flat flanks. Each group lists (x, height) along
    the back and is one convex hull; the barrel is their union, so the back can dip
    between them. Every sphere sits low enough that the bed cuts it where it
    reaches 45 degrees."""
    hulls = []
    for k, tops in enumerate(groups):
        xa = x0 + BELLY_R if k == 0 else tops[0][0]
        xb = x1 - BELLY_R - 0.8 if k == len(groups) - 1 else tops[-1][0]
        blobs = [ball(BELLY_R, x, s * (FLANK - BELLY_R), BELLY_Z) for x in (xa, xb) for s in (-1, 1)]
        blobs += [ball(TOP_R, x, s * TOP_Y, top - TOP_R) for x, top in tops for s in (-1, 1)]
        if k == len(groups) - 1:       # hips: they keep the flanks flat back to the hind legs' pins
            blobs += [ball(BELLY_R, x1 - BELLY_R, s * (FLANK - BELLY_R), LEG_Z) for s in (-1, 1)]
        hulls.append(mf.Manifold.batch_hull(blobs))
    return union(hulls) ^ box(x0 - 1, x1 + 1, -FLANK, FLANK, 0, 40)


def union(ms):
    return mf.Manifold.batch_boolean(list(ms), mf.OpType.Add)


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


def behind(at):
    """Where the rear segment may be: behind its blunt front face, X_CUT behind the
    axis. Near the bed the belly narrows, and the face leans back with it so that
    the horn left between the socket and the flank is HORN_MIN wide at every layer."""
    r = R_BALL + G_SEAM
    zb = BELLY_Z
    face = []
    for z in np.linspace(0, zb, 16):
        half = FLANK - BELLY_R + np.sqrt(BELLY_R ** 2 - (z - zb) ** 2)
        face.append((at + max(X_CUT, np.sqrt(max(r ** 2 - (half - HORN_MIN) ** 2, 0))), z))
    face = [(face[0][0], -1)] + face + [(at + X_CUT, 100), (at + 500, 100), (at + 500, -1)]
    return prism_xz(face[::-1], -100, 100)


def trim_lip(seg, at):
    """Over the top of the ball the socket's lip would feather out to nothing where it
    meets the back. Keep only the columns of it that are LIP_MIN thick, so that it
    ends in a blunt upright step."""
    r = R_BALL + G_SEAM
    z1 = Z_A + r - R_CORE - G_SLOPE + 0.3          # just above the hook's bridge
    zone = mf.Manifold.cylinder(60, r, r, 128).translate([at, 0, z1])
    lip = seg ^ zone
    thick = (lip ^ lip.translate([0, 0, -LIP_MIN])).project()
    thick = mf.CrossSection(thick.to_polygons(), mf.FillRule.Positive).offset(0.01, mf.JoinType.Round)
    return seg - (zone - mf.Manifold.extrude(thick, 80).translate([0, 0, z1 - 1]))


def bed_ring(at, r, ball_side):
    """A 45 degree chamfer along the bed edge of the seam at radius r, behind the axis:
    cut from the ball's foot (ball_side) or from the socket's, so the seam is wider
    at the first layers and the two cannot weld together there."""
    c, e = BED_CHAMFER, 0.05
    tri = [(r - c - e, -e), (r + e, -e), (r + e, c + e)] if ball_side else [(r - e, -e), (r + c + e, -e), (r - e, c + e)]
    return revolve(tri, at) ^ box(at, at + 50, -50, 50, -1, 5)


def hook_peak():
    r = (T_OUT + R_BALL + G_SLOPE - 0.1) / 2
    return r, Z_RIM + 0.1 + (r - T_OUT)


def hook(at):
    """The rear segment's hook inside the ball: tongue on the bed, bridge over the rim.
    A facet blends the tongue's outer face into the underside of the bridge."""
    far = R_BALL + 1.5
    top = lambda r: Z_A + r - R_CORE - G_SLOPE
    zb, b = Z_RIM + 0.1, BLEND
    c = TONGUE_CHAMFER
    prof = [(T_IN, c), (T_IN + c, 0), (T_OUT - c, 0), (T_OUT, c), (T_OUT, zb - b * np.sqrt(2)), (T_OUT + b, zb + b), hook_peak(),
            (R_BALL + G_SLOPE, Z_RIM), (far, Z_RIM), (far, top(far)), (T_IN, top(T_IN))]
    return revolve(prof, at) ^ wedge(at, HOOK_HALF)


def pocket(at):
    """The space inside the ball the hook swings in, under a roof rising at 45 degrees."""
    far = R_BALL + 0.4
    prof = [(R_CORE, -1), (far, -1), (far, Z_A + far - R_CORE), (R_CORE, Z_A)]
    return revolve(prof, at) ^ wedge(at, HOOK_HALF + SWING + MARGIN)


def rim(at):
    """The bar across the pocket's mouth that the tongue hooks behind; it has a pitched
    top, and its inner top edge is cut back to match the tongue's blend."""
    mid, b = (R_RIM + R_BALL) / 2, BLEND
    prof = [(R_RIM, 0), (R_BALL, 0), (R_BALL, Z_RIM), (mid, Z_RIM + mid - R_RIM),
            (R_RIM + b, Z_RIM + b), (R_RIM, Z_RIM - b * np.sqrt(2))]
    return revolve(prof, at) ^ wedge(at, HOOK_HALF + SWING + MARGIN + 2)


def split(body, axes):
    """Cut a body into len(axes) + 1 segments joined by ball-and-hook joints."""
    segs = []
    for i in range(len(axes) + 1):
        seg = body
        if i > 0:                      # this segment's socket and hook, round the ball in front
            at = axes[i - 1]
            seg = seg ^ ((behind(at) - socket_space(at)) + hook(at))
            seg = trim_lip(seg, at) - bed_ring(at, R_BALL + G_SEAM, False)
        if i < len(axes):              # this segment's ball, at its rear
            at = axes[i]
            seg = seg ^ ((box(-100, at, -100, 100, -1, 100) + ball_end(at)) - pocket(at) + rim(at))
            seg -= bed_ring(at, R_BALL, True)
        segs.append(seg)
    return segs


# --- legs ---------------------------------------------------------------------
def leg_pin(kind, side):
    """The cone pin on the flank: LEG_NECK across at the flank, widening outwards.
    Its underside is cut by a plane rising outwards at 45 degrees from the bottom
    of the neck, so every layer of it rests on the one below."""
    x, r0 = LEGS[kind]["x"], LEG_NECK / 2
    reach = LEG_GAP + LEGS[kind]["d"]
    pin = frustum_y(x, LEG_Z, FLANK, r0, FLANK + reach, r0 + reach)
    b = LEG_Z - r0
    pin ^= prism_yz([(FLANK - 3, b - 3), (FLANK + 6, b + 6), (FLANK + 6, b + 30), (FLANK - 3, b + 30)], x - 10, x + 10)
    pin += frustum_y(x, LEG_Z, FLANK - 1.5, r0, FLANK, r0)
    return pin if side > 0 else pin.mirror([0, 1, 0])


def leg_pieces(kind):
    """The leg seen from the side, as two convex outlines: the thigh, from the round
    haunch down to the hock, and the paw, from the hock forwards to the toe. Hock
    and toe are discs low enough that the bed cuts them at 45 degrees."""
    g = LEGS[kind]
    disc = lambda r, cx, cz: mf.CrossSection.circle(r, 72).translate([cx, cz])
    low = lambda dx_r: disc(dx_r[1], g["x"] + dx_r[0], dx_r[1] * np.sqrt(0.5))
    up = mf.CrossSection.square([60, 40]).translate([g["x"] - 30, 0])
    tx, tz, tr = g["thigh"]
    thigh = mf.CrossSection.batch_hull([disc(g["haunch"], g["x"], LEG_Z), disc(tr, g["x"] + tx, LEG_Z + tz), low(g["hock"])]) ^ up
    paw = mf.CrossSection.batch_hull([low(g["hock"]), low(g["toe"])]) ^ up
    return thigh, paw


def leg_thickness(kind):
    return LEGS[kind]["d"] + LEG_END + LEG_SKIN


def leg(kind, side):
    g, c, t = LEGS[kind], LEG_CHAMFER, leg_thickness(kind)
    x = g["x"]
    m = union(mf.Manifold.batch_hull([mf.Manifold.extrude(cs, t - c),
                                      mf.Manifold.extrude(cs.offset(-c, mf.JoinType.Round), t)])
              for cs in leg_pieces(kind))
    m = m.rotate([90, 0, 0]).mirror([0, 1, 0]).translate([0, FLANK + LEG_GAP, 0])
    y_out = FLANK + LEG_GAP + t
    br = g["haunch"] - 1.0
    rho = (br ** 2 + LEG_BULGE ** 2) / (2 * LEG_BULGE)      # a shallow dome over the haunch
    m += ball(rho, x, y_out + LEG_BULGE - rho, LEG_Z) ^ box(x - 20, x + 20, y_out - 0.01, y_out + 5, 0, 40)
    r0 = LEG_NECK / 2 + CLEAR * np.sqrt(2)
    end = LEG_GAP + g["d"] + LEG_END
    m -= frustum_y(x, LEG_Z, FLANK - 0.5, r0 - 0.5, FLANK + end, r0 + end)
    return m if side > 0 else m.mirror([0, 1, 0])


# --- head and orange ----------------------------------------------------------
def reach(m, lo, hi, axis):
    """Furthest m reaches along `axis` inside the probe box lo..hi."""
    probe = m ^ box(lo[0], hi[0], lo[1], hi[1], lo[2], hi[2])
    return probe.bounding_box()[3 + axis]


def gable(x0, x1, half, ridge, floor=-1.0):
    """A prism along x with a pitched top: |y| <= half, below ridge - |y|."""
    pts = [(x, s * half, z) for x in (x0, x1) for s in (-1, 1) for z in (floor, ridge - half)]
    return mf.Manifold.hull_points(pts + [(x0, 0, ridge), (x1, 0, ridge)])


def bicone(r_ridge, half):
    """Round the nod axis: radius r_ridge in the middle, falling at 45 degrees to each side."""
    return (frustum_y(NECK_X, NECK_Z, -half, r_ridge - half, 0, r_ridge, 128)
            + frustum_y(NECK_X, NECK_Z, 0, r_ridge, half, r_ridge - half, 128))


def fan(a0, a1):
    """Everything round the nod axis between a0 and a1 degrees from straight up
    (positive leans towards the tail)."""
    pts = [(NECK_X + 30 * np.sin(a), NECK_Z + 30 * np.cos(a)) for a in np.radians(np.linspace(a1, a0, 8))]
    return prism_xz([(NECK_X, NECK_Z)] + pts, -30, 30)


def bed_strip(y, x0, x1, inwards):
    """45 degree chamfer along a bed edge that runs along x at y: cut from the part
    on the inside (inwards) or from the one on the outside of it."""
    c, e = BED_CHAMFER, 0.05
    tri = [(y - c - e, -e), (y + e, -e), (y + e, c + e)] if inwards else [(y - e, -e), (y + c + e, -e), (y - e, c + e)]
    one = prism_yz(tri, x0, x1)
    return one + one.mirror([0, 1, 0])


def nod_pin(side, shift=0.0, extend=0.0):
    """Stub cone pin from a prong into the neck tab; shifted inwards it is the socket."""
    y_face = TAB_W / 2 + TAB_GAP
    r_tip = NOD_PIN / 2
    y0 = y_face + extend
    y1 = y_face - NOD_DEPTH
    return frustum_y(NECK_X, NECK_Z, side * (y0 - shift), r_tip + NOD_DEPTH + extend,
                     side * (y1 - shift), r_tip)


def neck_tab():
    """The head's half of the hinge. A neck strap with a pitched top runs back from the
    head to a disc round the nod axis, which carries the two pin sockets and stands
    on a foot with a 45 degree underside. On top of the disc is the horn: its front
    face meets the front wall of its pocket in the body when the nose goes down."""
    w, t = TAB_W / 2, TAB_RU * np.sqrt(0.5)
    strap = gable(TAB_X0, NECK_X, w, STRAP_Z, 0.0)
    disc = frustum_y(NECK_X, NECK_Z, -w, TAB_RU, w, TAB_RU, 128)
    foot = prism_xz([(NECK_X - t, 0), (NECK_X + t - (NECK_Z - t), 0), (NECK_X + t, NECK_Z - t), (NECK_X - t, NECK_Z - t)], -w, w)
    horn = bicone(HORN_R, w) ^ fan(-HORN_HALF, HORN_HALF)
    tab = strap + disc + foot + horn - bed_strip(w, TAB_X0 - 1, NECK_X + 5, True)
    for s in (-1, 1):
        tab -= nod_pin(s, shift=CLEAR * np.sqrt(2), extend=1.0)
    return tab


def doorway():
    """The slot in the front of the body the neck tab sits in. Every roof in it is
    pitched. In front, the lintel: its underside is where the neck strap's top comes
    to when the nose is NOD_STOP up. Round the axis, room for the disc. Above it,
    the horn's pocket: its front wall leans forward at 45 degrees, where the horn's
    front face comes to when the nose is NOD_STOP down."""
    hw, rc, g = TAB_W / 2 + TAB_GAP, TAB_RU + TAB_GAP, CLEAR * np.sqrt(2)
    x0, x1, x2 = NECK_X - R_NOD - 1, NECK_X - rc, NECK_X + rc
    front = gable(x0, x1 + 0.3, hw, STRAP_Z + g)
    lintel = turn(gable(x0 - 4, NECK_X, hw, STRAP_Z), "y", [NECK_X, 0, NECK_Z], NOD_STOP) ^ box(x0, x1 + 0.3, -hw, hw, -1, 40)
    middle = box(x1, x2, -hw, hw, -1, NECK_Z) + frustum_y(NECK_X, NECK_Z, -hw, rc, hw, rc, 128)
    pocket_ = bicone(HORN_R + g + 0.03, hw) ^ fan(-45.0, 45.0 + 4.5)
    return front + lintel + middle + pocket_ + bed_strip(hw, x0, x2, False)


def neck_mount(seg):
    """Give a body segment the body's half of the hinge: the drum front, the doorway
    and the two stub pins on the doorway's walls."""
    seg = seg ^ (drum(R_NOD) + box(NECK_X, 500, -100, 100, -1, 100))
    seg -= doorway()
    hw, r = TAB_W / 2 + TAB_GAP, NOD_PIN / 2 + NOD_DEPTH
    for s in (-1, 1):
        seg += nod_pin(s) + frustum_y(NECK_X, NECK_Z, s * (hw + 1), r, s * hw, r)
    return seg


def orange_profile(seat, hole=False):
    """(r, z) outline of the orange on its shaft; `hole` gives the bore through the head,
    SHAFT_GAP from the shaft and SHAFT_GAP square to the two cones."""
    s, f = SHAFT_R, SHAFT_FOOT
    if hole:
        gs, gc = SHAFT_GAP, SHAFT_GAP * np.sqrt(2)
        top = seat + gs - gc
        return [(0, -1), (f + gc + 1, -1), (s + gs, f + gc - s - gs), (s + gs, top), (s + gs + 12, top + 12), (0, top + 12)]
    lat = ORANGE_R * np.sqrt(0.5)                 # the cone meets the ball at 45 degrees
    zc = seat + (lat - s) + lat
    dimple = 0.9
    t1 = np.arccos(dimple / ORANGE_R)
    prof = [(0, 0), (f, 0), (s, f - s), (s, seat)]
    prof += [(ORANGE_R * np.cos(t), zc + ORANGE_R * np.sin(t)) for t in np.linspace(-np.pi / 4, t1, 40)]
    return prof + [(0, zc + ORANGE_R * np.sin(t1) - dimple)], zc


def eye_cone(side, ys, grow=0.0):
    ex, ez, er, fwd = EYE
    a = np.array([-np.sin(np.radians(fwd)), side * np.cos(np.radians(fwd)), 0.0])
    apex = np.array([ex, side * ys, ez]) - (er + grow * np.sqrt(2)) * a
    return mk.cone(list(apex), list(a), er + 3)


def nostril_cone(side, grow=0.0):
    ny, nz, nr = NOSTRIL
    return mk.cone([nr + grow * np.sqrt(2), side * ny, nz], [-1, 0, 0], nr + 2)


def mouth_cut(grow=0.0):
    """The mouth: a short V groove across the muzzle, and one down the middle from the
    nose pad to it. The upright groove's top end rises outwards at 45 degrees."""
    d, e = MOUTH + grow * np.sqrt(2), grow
    across = prism_xz([(-1, MOUTH_Z - d - 1), (d, MOUTH_Z), (-1, MOUTH_Z + d + 1)], -MOUTH_Y - e, MOUTH_Y + e)
    top = NOSE_AT[1] - NOSE[2] + 0.2 + e
    down = mf.Manifold.extrude(mf.CrossSection([[(-1, -d - 1), (d, 0), (-1, d + 1)]]), top - MOUTH_Z).translate([0, 0, MOUTH_Z])
    down ^= prism_xz([(-2, 0), (3, 0), (3, top - 3), (-2, top + 2)], -5, 5)
    return across + down


def ear(side, grow=0.0):
    (x0, x1), (y0, y1), (z0, z1), r0, r1 = EARS[0]
    return mf.Manifold.batch_hull([ball(r0 + grow, x0, side * y0, z0), ball(r1 + grow, x1, side * y1, z1)])


def make_head(stub=False):
    """Returns the head, the orange, and where things ended up. `stub` gives only the
    back of the head with its hinge, for the test strip."""
    blobs = [ball(4.0, x, s * 3.3, z) for x in (10.5, 17.0) for s in (-1, 1) for z in (2.76, HEAD_TOP - 4.0)]
    if not stub:
        blobs += [ball(2.8, 2.8, s * 3.3, z) for s in (-1, 1) for z in (1.93, 8.9)]              # blunt muzzle
    head = mf.Manifold.batch_hull(blobs) ^ box(0, 40, -20, 20, 0, 40)
    info = {"paint": {}}
    if not stub:
        ex, ez, er, _ = EYE
        ys = reach(head, (ex - 0.1, 0, ez - 0.1), (ex + 0.1, 30, ez + 0.1), 1)
        top = reach(head, (ORANGE_X - 0.1, -0.1, 0), (ORANGE_X + 0.1, 0.1, 40), 2)
        seat = top - ORANGE_SINK
        head += ear(1) + ear(-1)
    head -= drum(R_NOD + NECK_GAP)                 # the hollow back, round the nod axis
    edge = NECK_X - np.sqrt((R_NOD + NECK_GAP) ** 2 - NECK_Z ** 2)
    head -= box(edge - 0.35, edge + 2, -20, 20, -1, 0.6)     # blunt the feather edge it leaves on the bed
    head += neck_tab()
    if stub:
        return head, None, info
    for s in (-1, 1):
        head -= eye_cone(s, ys) + nostril_cone(s)
    head -= mouth_cut()
    head -= revolve(orange_profile(seat, hole=True), ORANGE_X)
    prof, zc = orange_profile(seat)
    orange = revolve(prof, ORANGE_X)
    black = union([eye_cone(s, ys, 0.12) for s in (-1, 1)] + [nostril_cone(s, 0.12) for s in (-1, 1)] + [mouth_cut(0.12)])
    nose = mf.Manifold.sphere(1.0, 96).scale(list(NOSE)).translate([NOSE_AT[0], 0, NOSE_AT[1]])
    ears = (ear(1, 0.05) + ear(-1, 0.05)) ^ box(0, 40, -20, 20, EAR_FROM, 40)
    info["paint"]["head"] = [(black, BLACK), (nose + ears, DARK)]
    stalk = mf.Manifold.cylinder(3, 1.3, 1.3, 48).translate([ORANGE_X, 0, zc + ORANGE_R - 1.2])
    info["paint"]["orange"] = [(box(-50, 50, -50, 50, -1, seat + ORANGE_BROWN), BROWN), (stalk, DARK)]
    info.update(eye_y=ys, seat=seat, orange_z=zc)
    return head, orange, info


def keyhole(y0, y1):
    """The keyring hole: a circle with a 45 degree peak, so its top needs no bridge."""
    r = KEYRING_D / 2
    pts = [(KEYRING_X + r * np.cos(t), KEYRING_Z + r * np.sin(t)) for t in np.linspace(3 * np.pi / 4, 9 * np.pi / 4, 40)]
    return prism_xz(pts + [(KEYRING_X, KEYRING_Z + r * np.sqrt(2))], y0, y1)


def keyring(seg):
    """A low, thick lug on the rump. The hole is half sunk into the back, where it
    carries on as a shallow groove for the ring; KEYRING_WALL stands round the hole
    and over its peak, and the lug spreads sideways into the back at its foot."""
    r, t = KEYRING_D / 2, KEYRING_T / 2
    rr = r + KEYRING_WALL
    plate = lambda rad, cz: prism_xz([(KEYRING_X + rad * np.cos(a), cz + rad * np.sin(a))
                                      for a in np.linspace(0, 2 * np.pi, 64, endpoint=False)], -t, t)
    f = KEYRING_FOOT
    foot = box(KEYRING_X - rr + 0.8, KEYRING_X + rr - 1.2, -t - f, t + f, KEYRING_Z - r - 0.8, KEYRING_Z - r - 0.7)
    lug = mf.Manifold.batch_hull([plate(rr, KEYRING_Z), plate(KEYRING_WALL, KEYRING_Z + r * np.sqrt(2)), foot])
    return seg + (lug - socket_space(AXES[-1])) - keyhole(-8, 8)


# --- the two models -----------------------------------------------------------
def joint(name, axis, point, moving, want, limit, step, stop=None, beside=None):
    """`stop`: the joint must not turn further than this. `beside`: a joint whose
    bending could get in this one's way; it is swept with that one bent as well."""
    return dict(name=name, axis=axis, point=point, moving=moving, want=want, limit=limit, step=step,
                stop=stop, beside=beside)


def leg_joint(name, kind, beside):
    return joint(name, "y", [LEGS[kind]["x"], 0, LEG_Z], [name], 45, 180, 5, beside=beside)


def nod_joint(moving):
    return joint("head nod", "y", [NECK_X, 0, NECK_Z], moving, NOD, 180, 1, stop=NOD_MAX)


def make_capybara(loop=True):
    """parts: name -> Manifold.  joints: in the order to pose them (leaves first)."""
    head, orange, info = make_head()
    segs = split(barrel(BODY_X0, BODY_X1, [SHOULDERS, RUMP]), AXES)
    segs[0] = neck_mount(segs[0])
    for s in (-1, 1):
        segs[0] += leg_pin("front", s)
        segs[-1] += leg_pin("hind", s)
    if loop and KEYRING_D:
        segs[-1] = keyring(segs[-1])
    parts = {"head": head, "orange": orange}
    parts.update({f"body {i + 1}": s for i, s in enumerate(segs)})
    joints, info["legs"] = [], {}
    for kind, beside in (("front", "body joint 1"), ("hind", f"body joint {len(AXES)}")):
        for s, side in ((1, "left"), (-1, "right")):
            name = f"{kind} {side} leg"
            parts[name] = leg(kind, s)
            info["legs"][name] = (kind, s)
            joints.append(leg_joint(name, kind, beside))
    joints.append(joint("orange", "z", [ORANGE_X, 0, 0], ["orange"], 180, 180, 45))
    hind = ["hind left leg", "hind right leg"]
    for i in reversed(range(len(AXES))):
        moving = [f"body {k + 1}" for k in range(i + 1, len(segs))] + hind
        joints.append(joint(f"body joint {i + 1}", "z", [AXES[i], 0, 0], moving, SWING, 60, 1))
    joints.append(nod_joint(["head", "orange"]))
    info.update(axes=AXES, full=True, loop=bool(loop and KEYRING_D))
    return parts, joints, info


def make_test():
    """The back of the head on its hinge, the first body segment with one leg, and the
    front of the second: one of each kind of joint, built by the same functions as
    the real thing, as a short print to try the clearances."""
    head, _, info = make_head(stub=True)
    at = AXES[0]
    a, b = split(barrel(BODY_X0, BODY_X1, [SHOULDERS, RUMP]) ^ box(0, at + 14, -50, 50, -1, 50), [at])
    a = neck_mount(a) + leg_pin("front", 1)
    name = "front left leg"
    parts = {"head": head, "body 1": a, "body 2": b, name: leg("front", 1)}
    joints = [leg_joint(name, "front", "body joint 1"),
              joint("body joint 1", "z", [at, 0, 0], ["body 2"], SWING, 60, 1),
              nod_joint(["head"])]
    info.update(axes=[at], full=False, loop=False, legs={name: ("front", 1)})
    return parts, joints, info


def posed(parts, joints, angles):
    """The parts with each joint turned by angles[name] degrees. The joints are
    listed leaves first, so a joint's own pivot has never moved when its turn comes."""
    parts = dict(parts)
    for j in joints:
        a = angles.get(j["name"], 0)
        if a:
            for n in j["moving"]:
                if n in parts:
                    parts[n] = turn(parts[n], j["axis"], j["point"], a)
    return parts


# --- measuring the solids -----------------------------------------------------
def section_y(m, y):
    """The section of m in the plane y = const, as a CrossSection in (x, -z)."""
    return m.rotate([90, 0, 0]).slice(float(y))


def extent(cs):
    """Smaller of a section's two extents."""
    b = cs.bounds()
    return min(b[2] - b[0], b[3] - b[1])


def piece_at(cs, x, y):
    """The piece of a CrossSection that contains the point (x, y)."""
    dot = mf.CrossSection.circle(0.02, 8).translate([x, y])
    for p in cs.decompose():
        if (p ^ dot).area() > 0:
            return p
    return mf.CrossSection()


def cavity_wall(solid, clip, inside, outside=None):
    """Thinnest wall round a cavity, measured on the solid itself: the distance from
    the pocket of empty space inside the box `clip` that holds the point `inside`
    to all the other empty space in the box. 0 if the cavity is open to the point
    `outside` (by default the box's top corner), which is in the open air."""
    dot = ball(0.02, *inside)
    air = ball(0.02, *(outside or (clip[0] + 0.05, clip[3] - 0.05, clip[5] - 0.05)))
    mine, others = None, []
    for p in (box(*clip) - solid).decompose():
        if mine is None and (p ^ dot).volume() > 0:
            mine = p
        else:
            others.append(p)
    if mine is None or (mine ^ air).volume() > 0 or not any((p ^ air).volume() > 0 for p in others):
        return 0.0
    return mine.min_gap(union(others), 8.0)


def column(m, x, y, z0=0.0):
    """Heights (bottom, top) of each run of solid on the upright line through (x, y) above z0."""
    col = m ^ box(x - 0.004, x + 0.004, y - 0.004, y + 0.004, z0, 60)
    return sorted((p.bounding_box()[2], p.bounding_box()[5]) for p in col.decompose()) if not col.is_empty() else []


def lip_thickness(seg, at):
    """Thinnest upright run of the socket's lip over the ball (the part of the rear
    segment above the hook's bridge, inside the socket's radius): the largest t for
    which every column of it is t thick, found by bisection on the solid."""
    r = R_BALL + G_SEAM
    z1 = Z_A + r - R_CORE - G_SLOPE + 0.3
    lip = seg ^ mf.Manifold.cylinder(60, r, r, 128).translate([at, 0, z1])
    flat = lambda m: mf.CrossSection(m.project().to_polygons(), mf.FillRule.Positive)
    whole = flat(lip)
    thin = lambda t: (whole - flat(lip ^ lip.translate([0, 0, -t])).offset(0.02, mf.JoinType.Round)).area() > 0.005
    lo, hi = 0.0, 4.0
    if thin(0.02):
        return 0.0
    for _ in range(9):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if thin(mid) else (mid, hi)
    return lo


def horn_width(seg, at):
    """Narrowest the horn of the socket's lip beside the ball is at its blunt front
    face, over the print layers from the bed up to the ball's equator."""
    widths = []
    for z in [0.1, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, Z_C]:
        cs = seg.slice(float(z)) ^ mf.CrossSection.square([40, 40]).translate([at - 5, 5.0])
        x = cs.bounds()[0]
        b = (cs ^ mf.CrossSection.square([0.04, 40]).translate([x + 0.02, 0])).bounds()
        widths.append(b[3] - b[1])
    return min(widths)


def thin_features(parts, info):
    """Thinnest walls (>= MIN_FEATURE) and pins (>= MIN_PIN), measured on sections and
    probes of the solids, not worked out from the dimensions."""
    walls, pins = {}, {}
    axes = info["axes"]
    for name, (kind, s) in info["legs"].items():
        g = LEGS[kind]
        y0 = FLANK + LEG_GAP
        if s > 0 and kind not in pins:
            clip = (g["x"] - 12, g["x"] + 12, y0 + 0.05, y0 + 6, -1, 20)
            walls[f"{kind} leg round its pin's socket"] = cavity_wall(parts[name], clip, (g["x"], y0 + 0.3, LEG_Z))
            body = parts["body 1" if kind == "front" else f"body {len(axes) + 1}"]
            pins[f"{kind} leg pin"] = extent(piece_at(section_y(body, FLANK + 0.02), g["x"], -LEG_Z))
    for i, at in enumerate(axes):
        front, rear = parts[f"body {i + 1}"], parts[f"body {i + 2}"]
        k = f" {i + 1}" if len(axes) > 1 else ""
        clip = (at - 2, at + R_BALL + 3, -12, 12, 0.05, Z_RIM - BLEND * np.sqrt(2) - 0.05)
        walls[f"ball{k} round the hook's pocket (rim, sides)"] = cavity_wall(front, clip, (at + (R_CORE + R_RIM) / 2, 0, 1.0))
        walls[f"socket lip{k} over the ball"] = lip_thickness(rear, at)
        walls[f"socket lip{k} horn at the flank, any layer"] = horn_width(rear, at)
        strip = lambda cs, x0, x1, y0, y1: cs ^ mf.CrossSection.square([x1 - x0, y1 - y0]).translate([x0, y0])
        rim_ = piece_at(strip(front.slice(1.0), at, at + 20, -0.02, 0.02), at + (R_RIM + R_BALL) / 2, 0).bounds()
        walls[f"rim{k} the hook holds"] = rim_[2] - rim_[0]
        tongue = piece_at(rear.slice(1.0), at + (T_IN + T_OUT) / 2, 0)
        x0 = tongue.bounds()[0]                               # its two inner corners are its narrowest place
        across, wide = strip(tongue, at, at + 20, -0.02, 0.02).bounds(), strip(tongue, x0 + 0.02, x0 + 0.06, -20, 20).bounds()
        lo, hi = column(rear, at + hook_peak()[0], 0)[0]
        pins[f"hook{k} tongue (across, wide)"] = min(across[2] - across[0], wide[3] - wide[1])
        pins[f"hook{k} bridge"] = (hi - lo) * np.sqrt(0.5)    # square to its 45 degree faces
        info.setdefault("tongue", (across[2] - across[0], wide[3] - wide[1], tongue.area()))
    if "head" in parts:
        head, b1 = parts["head"], parts["body 1"]
        w, rc = TAB_W / 2, TAB_RU + TAB_GAP
        clip = (NECK_X - 5, NECK_X + 5, -w + 0.05, w - 0.05, 0.3, NECK_Z + 8)
        walls["neck tab round its sockets"] = min(cavity_wall(head, clip, (NECK_X, s * (w - 0.3), NECK_Z)) for s in (-1, 1))
        clip = (NECK_X - 6.5, NECK_X + rc + 4, -12, 12, 0.05, 30)
        slot = (NECK_X, 0, NECK_Z + rc + 0.5)
        walls["roof over the neck slot"] = cavity_wall(b1 + box(clip[0], clip[1], -12, 12, -1, NECK_Z + 3), clip, slot)
        walls["walls of the neck slot"] = cavity_wall(b1 + box(clip[0], clip[1], -12, 12, NECK_Z + 3, 30) - doorway(), clip, slot,
                                                      (clip[0] + 0.05, 11.95, 0.1))
        pins["head nod pins"] = extent(piece_at(section_y(b1, w + TAB_GAP - NOD_DEPTH + 0.01), NECK_X, -NECK_Z))
    if info["full"]:
        seat = info["seat"]
        clip = (ORANGE_X - 9, ORANGE_X + 9, -9, 9, SHAFT_FOOT, seat - 0.6)
        walls["head round the orange's shaft"] = cavity_wall(parts["head"], clip, (ORANGE_X, 0, 6.0))
        pins["orange shaft"] = min(extent(parts["orange"].slice(float(z))) for z in (SHAFT_FOOT, seat / 2, seat - 0.05))
        walls["ear tip"] = extent(piece_at(parts["head"].slice(14.6), EARS[0][0][1], EARS[0][1][1]))
    if info["loop"]:
        b4, t = parts[f"body {len(axes) + 1}"], KEYRING_T / 2
        clip = (KEYRING_X - 7, KEYRING_X + 7, -t + 0.05, t - 0.05, KEYRING_Z - 4, KEYRING_Z + 8)
        walls["keyring lug round its hole"] = cavity_wall(b4, clip, (KEYRING_X, 0, KEYRING_Z))
        info["lug"] = (extent(piece_at(b4.slice(KEYRING_Z + KEYRING_D / 2 * np.sqrt(2) + 0.5), KEYRING_X, 0)),
                       min(b - a for a, b in column(b4, KEYRING_X, 0, KEYRING_Z)))
    return walls, pins


# --- checks -------------------------------------------------------------------
def sweep(parts, joints, j, pose=None):
    """Turn joint j each way until it hits something, with the other joints as in
    `pose`. Returns the free range each way (degrees) and the tightest gap inside
    the range it is meant to have."""
    pose = dict(pose or {})
    rest = union(posed({n: p for n, p in parts.items() if n not in j["moving"]}, joints, pose).values())
    mine = {n: parts[n] for n in j["moving"]}
    free, tight = [], 9.0
    for sign in (1, -1):
        reached = 0.0
        for a in np.arange(j["step"], j["limit"] + 1e-6, j["step"]):
            turned = union(posed(mine, joints, dict(pose, **{j["name"]: sign * a})).values())
            if (turned ^ rest).volume() > 1e-6:
                break
            reached = a
            if a <= j["want"] + 1e-6:
                tight = min(tight, turned.min_gap(rest, 2.0))
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


def spread(free):
    return "full circle" if min(free) >= 180 else f"+{free[0]:g}/-{free[1]:g} deg"


def check(parts, joints, info):
    """Refuse to go on unless it prints in place and every joint moves. Returns report lines."""
    names = list(parts)
    # 1. every moving part is its own single body, standing on the bed, clear of the others as printed
    tight, bed = 9.0, 9.0
    first = {n: p ^ box(-100, 200, -100, 100, -1, 0.1) for n, p in parts.items()}
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
            gap = first[a].min_gap(first[b], 2.0)
            if gap < BED_GAP - 0.005:
                raise SystemExit(f"{a} and {b} are only {gap:.2f} mm apart in the first layer")
            bed = min(bed, gap)
    out = [f"{len(names)} separate bodies, each starting on the bed with no layer starting in mid-air; "
           f"tightest gap as printed {tight:.2f} mm, in the first layer {bed:.2f} mm"]

    # 2. each joint through its range; a joint with a stop must not go past it, and a
    #    leg is swung again with the body joint beside it bent each way
    for j in joints:
        free, gap = sweep(parts, joints, j)
        if min(free) < j["want"] - 1e-6:
            raise SystemExit(f"{j['name']} only swings +{free[0]:.0f}/-{free[1]:.0f} degrees, wanted {j['want']:.0f}")
        line = f"   {j['name']:<16} {spread(free):<16} tightest gap {gap:.2f} mm"
        if j["stop"]:
            if max(free) > j["stop"]:
                raise SystemExit(f"{j['name']} swings +{free[0]:.0f}/-{free[1]:.0f} degrees: nothing stops it by {j['stop']:.0f}")
            line += f"; stopped both ways before {j['stop']:.0f}"
        if j["beside"]:
            bent = [sweep(parts, joints, j, {j["beside"]: s * SWING})[0] for s in (1, -1)]
            worst = [min(f[0] for f in bent), min(f[1] for f in bent)]
            if min(worst) < j["want"] - 1e-6:
                raise SystemExit(f"{j['name']} only swings +{worst[0]:.0f}/-{worst[1]:.0f} with {j['beside']} bent")
            line += f"; with {j['beside']} bent {SWING:g} either way: {spread(worst)}"
        out.append(line)

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

    # 6. thin features, measured on the solids
    walls, pins = thin_features(parts, info)
    for what, limit in ((walls, MIN_FEATURE), (pins, MIN_PIN)):
        for k, v in what.items():
            if v < limit - 1e-6:
                raise SystemExit(f"{k} is {v:.2f} mm, under {limit}")
    out.append("   thinnest walls (measured): " + ", ".join(f"{k} {v:.2f}" for k, v in sorted(walls.items(), key=lambda kv: kv[1])))
    out.append("   pins (measured): " + ", ".join(f"{k} {v:.2f}" for k, v in pins.items())
               + "; each tongue is {:.2f} across and {:.2f} wide at its narrowest, {:.1f} mm2".format(*info["tongue"]))
    if info["loop"]:
        thick, over = info["lug"]
        if thick < 4.0 or over < 2.0:
            raise SystemExit(f"keyring lug is {thick:.2f} thick with {over:.2f} over the hole's peak")
        out.append(f"   keyring lug {thick:.2f} thick, {over:.2f} over the hole's peak")

    # 7. overall size (the full model only)
    if info["full"]:
        lo, hi = np.array(union(parts.values()).bounding_box()).reshape(2, 3)
        size = hi - lo
        if not LENGTH[0] <= size[0] <= LENGTH[1] or size[1] >= MAX_W or size[2] >= MAX_H:
            raise SystemExit(f"size {size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} is outside the brief")
        back = max(parts[n].bounding_box()[5] for n in parts if n.startswith("body"))
        out.append(f"   nose to rump {size[0]:.1f}, width {size[1]:.1f}, height {size[2]:.1f} "
                   f"(top of the {'keyring lug' if info['loop'] else 'back'} {back:.1f})")
    return out


# --- paint and write ----------------------------------------------------------
def paint(parts, info, pose=None):
    """One mesh for the lot, and a filament index for every triangle. Each part is cut
    along its colour boundaries first, so the boundaries are edges of the mesh and
    every triangle is one colour all over; the cut pieces are put back together as
    one closed body. `pose` = (joints, angles) gives the same thing posed."""
    whole, colour = {}, {}
    for name, p in parts.items():
        cuts = list(info["paint"].get(name, []))
        if "leg" in name:
            cuts.append((box(-100, 200, -100, 100, -1, PAW_Z), DARK))        # the paws
        pieces, rest = [], p
        for cut, c in cuts:
            pieces.append(((rest ^ cut).as_original(), c))
            rest = rest - cut
        pieces.append((rest.as_original(), ORANGE if name == "orange" else BROWN))
        colour.update({m.original_id(): c for m, c in pieces})
        real = [m for m in union(m for m, _ in pieces).decompose() if m.volume() > 1e-6]     # drops shells with no volume
        if len(real) != 1 or abs(real[0].volume() - p.volume()) > 1e-3:
            raise SystemExit(f"{name} did not go back together after being cut for painting")
        whole[name] = real[0]
    if pose:
        whole = posed(whole, *pose)
    meshes, labels = [], []
    for name, p in whole.items():
        m = p.to_mesh()
        tris = np.asarray(m.tri_verts)
        run = np.searchsorted(np.asarray(m.run_index), 3 * np.arange(len(tris)), side="right") - 1
        labels.append(np.array([colour[i] for i in np.asarray(m.run_original_id)])[run])
        meshes.append(trimesh.Trimesh(np.asarray(m.vert_properties)[:, :3], tris, process=False))
    return mk.merged(meshes, labels)


def clean(mesh, lab):
    """Make the mesh fit to write: corners snapped to 0.1 micron and merged, and every
    triangle with no area taken out. Such a sliver (b on the edge a-c) is removed by
    splitting the triangle on the other side of a-c at b, which keeps the surface
    closed; a pair of slivers back to back is simply dropped."""
    v, inv = np.unique(np.round(mesh.vertices, 4), axis=0, return_inverse=True)
    f, lab = inv.reshape(-1)[mesh.faces], np.array(lab)
    for _ in range(50):
        keep = (f[:, 0] != f[:, 1]) & (f[:, 1] != f[:, 2]) & (f[:, 2] != f[:, 0])
        f, lab = f[keep], lab[keep]
        t = v[f]
        area = np.linalg.norm(np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]), axis=1) / 2
        flat = np.where(area < 1e-9)[0]
        if not len(flat):
            return trimesh.Trimesh(v, f, process=False), lab
        owner = {(int(a), int(b)): i for i, tri in enumerate(f) for a, b in zip(tri, np.roll(tri, -1))}
        gone, new, new_lab = set(), [], []
        for i in flat:
            if i in gone:
                continue
            k = int(np.argmax([np.linalg.norm(v[f[i][(e + 1) % 3]] - v[f[i][e]]) for e in range(3)]))
            a, c, b = int(f[i][k]), int(f[i][(k + 1) % 3]), int(f[i][(k + 2) % 3])     # b lies on a-c
            n = owner.get((c, a))
            if n is None or n in gone:
                continue
            d = int([x for x in f[n] if x not in (a, c)][0])
            gone.update((i, n))
            if d != b:
                new += [(c, b, d), (b, a, d)]
                new_lab += [lab[n]] * 2
        if not gone:
            break
        keep = np.array([i not in gone for i in range(len(f))])
        f = np.vstack([f[keep]] + ([np.array(new)] if new else []))
        lab = np.concatenate([lab[keep], np.array(new_lab, dtype=lab.dtype)])
    raise SystemExit("could not clean the mesh of triangles with no area")


def check_paint(mesh, lab):
    """Every patch of one colour (triangles joined edge to edge) must be MIN_PATCH or
    more. Returns the number of patches and the smallest."""
    import scipy.sparse as sp
    import scipy.sparse.csgraph as cg
    adj = mesh.face_adjacency
    adj = adj[lab[adj[:, 0]] == lab[adj[:, 1]]]
    n = len(mesh.faces)
    count, patch = cg.connected_components(sp.coo_matrix((np.ones(len(adj)), (adj[:, 0], adj[:, 1])), shape=(n, n)), directed=False)
    areas = np.bincount(patch, weights=mesh.area_faces, minlength=count)
    worst = int(np.argmin(areas))
    if areas[worst] < MIN_PATCH:
        at = mesh.triangles_center[patch == worst].mean(0)
        raise SystemExit(f"a stray patch of filament {lab[patch == worst][0] + 1}, {areas[worst]:.3f} mm2, at {np.round(at, 1)}")
    return count, areas[worst]


def check_file(path, bodies):
    """Read the written STL back as a slicer would (corners merged by position): it
    must be exactly `bodies` closed shells, with no triangle without area."""
    m = trimesh.load(path, process=True)
    shells = m.split(only_watertight=False)
    flat = int((m.area_faces < 1e-9).sum())
    if len(shells) != bodies or not all(s.is_watertight and s.volume > 0.01 for s in shells) or flat:
        raise SystemExit(f"{path.name}: {len(shells)} shells for {bodies} bodies, "
                         f"{sum(not s.is_watertight for s in shells)} of them open, {flat} triangles with no area")
    return len(shells)


def build(name, maker, title):
    parts, joints, info = maker()
    report = check(parts, joints, info)
    print(f"{title}: " + "\n".join(report))
    mesh, lab = paint(parts, info)
    lo = mesh.bounds[0]
    if lo[2] < -1e-6:
        raise SystemExit("something pokes below the bed")
    mesh.apply_translation([-lo[0], -(mesh.bounds[0][1] + mesh.bounds[1][1]) / 2, 0])
    mesh, lab = clean(mesh, lab)
    patches, smallest = check_paint(mesh, lab)
    mesh.export(OUT / f"{name}.stl")
    mk.write_3mf(OUT / f"{name}.3mf", [(name, mesh, lab, (0, 0))], FILAMENTS)
    shells = check_file(OUT / f"{name}.stl", len(parts))
    used = ", ".join(f"T{k + 1} {mesh.area_faces[lab == k].sum():.0f} mm2" for k in range(len(FILAMENTS)) if (lab == k).any())
    print(f"   paint: {patches} patches cut along their edges, the smallest {smallest:.1f} mm2 ({used})")
    print(f"   written file: {shells} closed shells for {len(parts)} bodies, no triangle without area")
    e = mesh.extents
    print(f"{name}  {e[0]:.1f} x {e[1]:.1f} x {e[2]:.1f} mm  {mesh.volume / 1000:.1f} cm3  {len(mesh.faces)} tris\n")


def main():
    build(f"{NAME}-test", make_test, "test strip")
    if KEYRING_D:                    # the keyring lug is optional: the plain back must pass too
        parts, joints, info = make_capybara(loop=False)
        check(parts, joints, info)
        print("pocket capybara without the keyring lug: passes every check as well\n")
    build(NAME, make_capybara, "pocket capybara")


if __name__ == "__main__":
    main()
