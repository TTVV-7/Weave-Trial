"""Pocket capybara: a print-in-place articulated fidget, as a painted 3MF and a plain STL.

About 60 mm nose to rump, printed standing on its belly in one piece, no supports.
The body is four segments that wiggle side to side, the four legs swing on pins,
the head nods, and an orange on its head spins. An original design.

How it holds together with nothing printed over a gap:
  * body joints: every segment ends in a ball (an upright cylinder below, a sphere
    above) centred on the joint's upright axis; the next segment's front is the
    matching socket, so the seam is a thin line that never opens when it bends.
    Inside the ball, hidden by the socket, the next segment hooks over a rim:
    an arc-shaped tongue standing on the bed, joined to the socket by a bridge
    that rises at 45 degrees over the rim, whose top rises with it. The ball's
    own roof rises at 45 degrees over that bridge. A V ridge round the inside of
    the socket rides in a V groove round the ball's foot, so the joint cannot
    lift or twist. Nothing is flatter than 45 degrees.
  * legs: a pin on the flank, in a shallow cone-sided recess, goes through the
    lip of the leg (a cone boss that sits in the recess) and ends in a flat
    flange inside the leg, under the leg's closed outer skin. The pin's root is
    a cone that narrows outwards, and from there its underside is cut at 45
    degrees rising outwards, so it never starts in mid-air.
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
BED_GAP = 0.6         # bodies are at least this far apart in the first layer (the slab from 0 to FIRST_LAYER)
FIRST_LAYER = 0.2
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
# each is (x, height) or (x, height, how far off the middle its two spheres are): the rump is wider on top
SHOULDERS = [(21.0, 13.9), (26.0, 14.4), (32.5, 13.7)]
RUMP = [(31.0, 13.7), (41.0, 15.2, 2.0), (49.5, 16.5, 2.8), (54.6, 16.3, 2.8)]
TAPER = (14.0, 7.5, 18.6)    # seen from above the shoulders narrow towards the head: x, half width there, x where it is FLANK again
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
T_IN, T_OUT = 4.1, 7.6      # the hook's tongue
R_RIM = 8.0           # the rim the tongue hooks behind runs from here to R_BALL
Z_RIM = 2.6           # rim height at its inner wall; its top rises outwards at 45 degrees to the ball's surface
Z_A = 3.0             # where the ball's roof starts to lean out over the hook
G_SLOPE = 0.5         # vertical gap between 45 degree faces (0.354 square to them)
HOOK_HALF = 18.0      # half angle of the tongue and bridge
BLEND = 0.35          # the tongue is blended into the bridge with a facet this big
BED_CHAMFER = 0.35    # both sides of a seam are chamfered where they meet the bed
TONGUE_CHAMFER = 0.35 # and so are the foot of the tongue and the foot of the rim's inner wall
RING_Z = 2.2          # a V ridge round the inside of the socket at this height rides in a V groove round the
RING_D = 0.95         # ball this deep (the ridge is RING_FIT shallower): it stops the joint lifting and twisting
RING_FIT = 0.11
TILT_Z = 4.0          # the joint is tilted about axes at this height to measure its slop
MAX_TILT = 6.0        # degrees a body joint may fold nose-down, or twist
MAX_FOLD = 8.0        # degrees it may fold up at the joint. It cannot be held to MAX_TILT: the two stops against it,
                      # the ball's roof on the tongue's front and the rim's top under the hook's bridge, are 45 degree
                      # faces no closer than CLEAR, so each gives 0.5 mm up and down, and they are only 6 mm apart

# --- legs ---------------------------------------------------------------------
LEG_Z = 6.0           # pin height
LEG_NECK = 3.12       # pin diameter where it enters the leg's lip; the 45 degree cut under it leaves 2.6 at the lip's far side
LEG_GAP = 0.4         # between leg and flank, and between the leg's boss and the floor of its recess
LEG_SINK = 1.0        # the pin stands in a cone-sided recess this deep in the flank; the leg's boss sits in it
LEG_ROOT = 0.3        # the pin's root is a cone that narrows outwards as far as this into the lip
LEG_LAND = 0.5        # then the lip's bore is a blunt cylinder this long: with LEG_ROOT, the lip's thickness
LEG_PLAY = 0.4        # between the lip and the pin's flange behind it
LEG_FLANGE = 0.7      # thickness of the flange on the end of the pin: a flat step, not a feather edge
LEG_HOLD = 1.0        # the flange is this much bigger in radius than the bore it cannot pass
LEG_END = 0.35        # gap beyond the pin's end
LEG_SKIN = 0.85       # the leg's closed outer skin
LEG_BOSS = 3.75       # radius of the boss's face
LEG_CHAMFER = 0.6     # round the thigh's outer edge
PAW_OUT = 0.9         # the paw stands this much further out than the thigh
PAW_CHAMFER = 0.7
PAW_Z = 2.4           # painted dark below this
MIN_FOOT = 15.0       # mm2 of bed under each leg
MIN_HOLD = 0.9        # mm of flange over lip left when everything a 0.4 mm nozzle cannot print is taken away...
HOLD_BAND = (1.0, 2.6)   # ...in every layer this far above the pin's axis, the band where the flange stands over the lip
NOZZLE = 0.4
# x of the pin; the thigh is the hull of a big disc (x from the pin, radius) at pin height, a small
# one above it (x and z from the pin, radius) that makes it a pear, the shin and the hock; shin,
# hock (heel) and toe are discs (x from the pin, radius) resting on the bed: the shin keeps the
# thigh's front from overhanging, and the paw is the hull of hock and toe
LEGS = {"front": dict(x=20.9, thigh=(0.0, 4.3), top=(0.2, 3.1, 2.7), shin=(-0.9, 1.3), hock=(1.6, 1.5), toe=(-2.9, 1.3)),
        "hind": dict(x=57.3, thigh=(-0.5, 4.8), top=(-0.4, 3.2, 2.9), shin=(-1.8, 1.3), hock=(2.4, 1.5), toe=(-2.6, 1.3))}

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
HEAD_TOP = 14.2       # as deep as the shoulders
MUZZLE_TOP = 12.2
EYE = (7.8, 11.2, 1.4, 38.0)     # x, z, radius, and how far it is turned to face forwards
NOSTRIL = (1.7, 9.6, 0.8)    # y, z, radius
EARS = [((14.6, 15.2), (4.9, 5.6), (11.8, 14.7), 2.0, 1.5)]   # (x, y, z) of root and tip, their radii
EAR_FROM = 13.1           # painted dark above this height
NOSE = (2.0, 4.0, 2.5)    # the dark nose pad is where an ellipsoid with these radii, centred on...
NOSE_AT = (0.3, 10.6)     # ...this x and z, the top front edge of the muzzle, cuts the head
MOUTH_Z, MOUTH_Y = 5.0, 1.8   # the mouth: one short shallow groove, under a third of the muzzle's width, painted dark brown
MOUTH = 0.35              # its depth (a V with 45 degree faces)

# --- orange -------------------------------------------------------------------
ORANGE_X = 9.6
ORANGE_R = 4.0        # an 8 mm orange
ORANGE_SINK = 1.2     # how far its cone sits into the head
SHAFT_R = 2.25        # 4.5 mm shaft down through the head
SHAFT_FOOT = 3.4      # foot radius on the bed
SHAFT_GAP = 0.5       # round the shaft, and square to the two cones
ORANGE_BROWN = 0.4    # the shaft's colour runs this far up into the cone under the ball

KEYRING_D = 3.0       # hole of the keyring eye on the rump; 0 for none
KEYRING_X = 56.6
KEYRING_Z = 13.3      # hole centre: the eye is sunk into the rump, so that only a low round hump stands above the back
KEYRING_T = 4.5       # thickness of the web the hole goes through
KEYRING_WALL = 2.05   # round the hole and over its peak
KEYRING_FOOT = 1.5    # the hump spreads this much at its foot
KEYRING_SCOOP = 2.2   # radius of the scoop in the back each side of the web, for the ring to swing in
KEYRING_TOP = 17.5    # the hump must not stand higher than this


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
    """m turned deg about the 'x', 'y' or 'z' axis through point."""
    p = np.asarray(point, float)
    rot = {"x": [deg, 0, 0], "y": [0, deg, 0], "z": [0, 0, deg]}[axis]
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
        blobs += [ball(TOP_R, t[0], s * (t[2] if len(t) > 2 else TOP_Y), t[1] - TOP_R) for t in tops for s in (-1, 1)]
        if k == len(groups) - 1:       # hips: they keep the flanks flat back to the hind legs' pins
            blobs += [ball(BELLY_R, x1 - BELLY_R, s * (FLANK - BELLY_R), LEG_Z) for s in (-1, 1)]
        hulls.append(mf.Manifold.batch_hull(blobs))
    xa, wa, xb = TAPER
    plan = [(xa - 3, -wa + 3 * (FLANK - wa) / (xb - xa)), (xb, -FLANK), (x1 + 1, -FLANK)]
    plan += [(x, -y) for x, y in plan[::-1]]
    return union(hulls) ^ mf.Manifold.extrude(mf.CrossSection([plan]), 40)


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
    zone = lip_zone(at)
    lip = seg ^ zone
    thick = (lip ^ lip.translate([0, 0, -LIP_MIN])).project()
    thick = mf.CrossSection(thick.to_polygons(), mf.FillRule.Positive).offset(0.01, mf.JoinType.Round)
    return seg - (zone - mf.Manifold.extrude(thick, 80).translate([0, 0, -1]))


def bed_ring(at, r, ball_side):
    """A 45 degree chamfer along the bed edge of the seam at radius r, behind the axis:
    cut from the ball's foot (ball_side) or from the socket's, so the seam is wider
    at the first layers and the two cannot weld together there."""
    c, e = BED_CHAMFER, 0.05
    tri = [(r - c - e, -e), (r + e, -e), (r + e, c + e)] if ball_side else [(r - e, -e), (r + c + e, -e), (r - e, c + e)]
    return revolve(tri, at) ^ box(at, at + 50, -50, 50, -1, 5)


def hook_peak():
    """Where the hook's bridge is measured: half way across the rim, on its underside."""
    r = (T_OUT + R_BALL) / 2
    return r, Z_RIM + G_SLOPE + r - R_RIM


def hook(at):
    """The rear segment's hook inside the ball: tongue on the bed, bridge over the rim.
    The bridge's underside rises outwards at 45 degrees all the way, G_SLOPE above the
    rim's top. A facet blends the tongue's outer face into it."""
    far = R_BALL + 1.5
    top = lambda r: Z_A + r - R_CORE - G_SLOPE
    under = lambda r: Z_RIM + G_SLOPE + r - R_RIM
    zb, b = under(T_OUT), BLEND
    c = TONGUE_CHAMFER
    prof = [(T_IN, c), (T_IN + c, 0), (T_OUT - c, 0), (T_OUT, c), (T_OUT, zb - b * np.sqrt(2)), (T_OUT + b, zb + b),
            (far, under(far)), (far, top(far)), (T_IN, top(T_IN))]
    return revolve(prof, at) ^ wedge(at, HOOK_HALF)


def pocket(at):
    """The space inside the ball the hook swings in, under a roof rising at 45 degrees."""
    far = R_BALL + 0.4
    prof = [(R_CORE, -1), (far, -1), (far, Z_A + far - R_CORE), (R_CORE, Z_A)]
    return revolve(prof, at) ^ wedge(at, HOOK_HALF + SWING + MARGIN)


def rim(at):
    """The bar across the pocket's mouth that the tongue hooks behind. Its top rises
    outwards at 45 degrees from its inner wall to the ball's surface, so the hook's
    bridge has a long slope to bear on; its inner top edge is cut back to match the
    tongue's blend and its inner foot is chamfered."""
    b, c = BLEND, TONGUE_CHAMFER
    prof = [(R_RIM + c, 0), (R_BALL, 0), (R_BALL, Z_RIM + R_BALL - R_RIM),
            (R_RIM + b, Z_RIM + b), (R_RIM, Z_RIM - b * np.sqrt(2)), (R_RIM, c)]
    return revolve(prof, at) ^ wedge(at, HOOK_HALF + SWING + MARGIN + 2)


def ring(at, r, d):
    """A V ring d deep, pointing inwards from radius r at height RING_Z, behind the axis."""
    e = 0.2
    return revolve([(r + e, RING_Z - d - e), (r + e, RING_Z + d + e), (r - d, RING_Z)], at) ^ box(at, at + 50, -50, 50, -1, 20)


def lip_zone(at):
    """Everything over the ball, above the hook's bridge: where the socket's lip is."""
    r = R_BALL + G_SEAM
    return mf.Manifold.cylinder(60, r, r, 128).translate([at, 0, Z_A + r - R_CORE - G_SLOPE + 0.3])


def lip_reach(seg, at):
    """How near the joint's axis the socket's lip comes, seen from above, measured on
    the trimmed solid: the radius of the largest circle round the axis that misses it."""
    flat = (seg ^ lip_zone(at)).project()
    flat = mf.CrossSection(flat.to_polygons(), mf.FillRule.Positive)
    lo, hi = 0.0, R_BALL + G_SEAM
    for _ in range(14):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if (flat ^ mf.CrossSection.circle(mid, 256).translate([at, 0])).area() < 1e-5 else (lo, mid)
    return lo


def split(body, axes):
    """Cut a body into len(axes) + 1 segments joined by ball-and-hook joints. Each
    front segment keeps the body's own back, as a low collar over its ball, right up
    to G_SEAM from where the next segment's trimmed lip swings past, so that the
    back reads as one barrel with a fine seam and not a groove at each joint."""
    rears = {}
    for i, at in enumerate(axes):      # the socket and hook of the segment behind each joint
        seg = body ^ ((behind(at) - (socket_space(at) - ring(at, R_BALL + G_SEAM, RING_D - RING_FIT))) + hook(at))
        rears[i + 1] = trim_lip(seg, at) - bed_ring(at, R_BALL + G_SEAM, False)
    segs = []
    for i in range(len(axes) + 1):
        seg = rears.get(i, body)
        if i < len(axes):              # this segment's ball, at its rear
            at = axes[i]
            rc = lip_reach(rears[i + 1], at) - G_SEAM
            collar = mf.Manifold.cylinder(60, rc, rc, 256).translate([at, 0, -1])
            seg = seg ^ ((box(-100, at, -100, 100, -1, 100) + ball_end(at) + collar) - pocket(at) + rim(at))
            seg -= bed_ring(at, R_BALL, True) + ring(at, R_BALL, RING_D)
        segs.append(seg)
    return segs


# --- legs ---------------------------------------------------------------------
def leg_stations():
    """Where things are along the pin, as y for the left side: the recess's floor, the
    boss's face, where the bore's blunt land starts, the lip's outer face, the two
    faces of the flange, the end of the socket, the leg's outer face."""
    floor = FLANK - LEG_SINK
    face = floor + LEG_GAP
    land = face + LEG_ROOT
    lip = land + LEG_LAND
    f0 = lip + LEG_PLAY
    f1 = f0 + LEG_FLANGE
    end = f1 + LEG_END
    return floor, face, land, lip, f0, f1, end, end + LEG_SKIN


def leg_radii():
    """Pin neck, the lip's bore, the flange, the socket round the flange."""
    rn = LEG_NECK / 2
    bore = rn + CLEAR * np.sqrt(2)
    return rn, bore, bore + LEG_HOLD, bore + LEG_HOLD + CLEAR


def teardrop_y(x, z, r, y0, y1, n=128):
    """A cylinder along y with its roof drawn up to a 45 degree peak, so it prints as a hole."""
    pts = [(x + r * np.cos(t), z + r * np.sin(t)) for t in np.linspace(3 * np.pi / 4, 9 * np.pi / 4, 3 * n // 4 + 1)]
    return prism_xz(pts + [(x, z + r * np.sqrt(2))], y0, y1)


def leg_mount(seg, kind, sides=(1, -1)):
    """Give a body segment the pins for a pair of legs. Each stands in a shallow recess
    with a 45 degree cone side. The pin's root is a cone narrowing outwards (so its
    underside rises at 45 degrees and prints all round), then a straight neck through
    the leg's lip, then a flat flange behind the lip. Of the neck and flange only what
    lies within 45 degrees above the lower half of the root cone's end is kept: their
    underside rises at 45 degrees or more away from it in every direction, sideways
    as well as outwards, so no layer of them starts in mid-air."""
    x = LEGS[kind]["x"]
    floor, face, land, lip, f0, f1, end, out = leg_stations()
    rn, bore, rf, rc = leg_radii()
    root = rn + (land - floor)
    r_floor = LEG_BOSS + CLEAR * np.sqrt(2) - LEG_GAP
    recess = frustum_y(x, LEG_Z, floor, r_floor, FLANK + 1.0, r_floor + LEG_SINK + 1.0, 128)
    pin = frustum_y(x, LEG_Z, floor - 1.5, root, floor, root, 128) + frustum_y(x, LEG_Z, floor, root, land, rn, 128)
    beyond = frustum_y(x, LEG_Z, land - 0.01, rn, f1, rn, 128) + frustum_y(x, LEG_Z, f0, rf, f1, rf, 128)
    # what can be printed beyond the root cone's end: everything within 45 degrees above the lower half of its rim
    rim_ = [(x + rn * np.sin(a), LEG_Z - rn * np.cos(a)) for a in np.radians(np.linspace(-90, 90, 37))]
    pin += beyond ^ union(mf.Manifold.cylinder(14, 0, 14, 64).translate([px, land - 0.01, pz]) for px, pz in rim_)
    for s in sides:
        seg = seg - (recess if s > 0 else recess.mirror([0, 1, 0])) + (pin if s > 0 else pin.mirror([0, 1, 0]))
    return seg


def leg_pieces(kind):
    """The leg seen from the side, as two convex outlines: the thigh, a pear from the
    small disc at its top through the big one round the pin down to the hock, and
    the paw, from the hock forwards to the toe. Hock and toe are discs low enough
    that the bed cuts them at 45 degrees."""
    g = LEGS[kind]
    disc = lambda r, cx, cz: mf.CrossSection.circle(r, 72).translate([cx, cz])
    low = lambda dx_r: disc(dx_r[1], g["x"] + dx_r[0], dx_r[1] * np.sqrt(0.5))
    (bx, br), (tx, tz, tr) = g["thigh"], g["top"]
    thigh = mf.CrossSection.batch_hull([disc(br, g["x"] + bx, LEG_Z), disc(tr, g["x"] + tx, LEG_Z + tz), low(g["shin"]), low(g["hock"])])
    paw = mf.CrossSection.batch_hull([low(g["hock"]), low(g["toe"])])
    return thigh, paw


def leg(kind, side):
    """A leg: a plate with a rounded outer edge, a paw that stands out a little
    further, and on the inside a cone boss that sits in the flank's recess. The boss
    is the lip the pin's flange is caught behind; the socket for the flange has a
    45 degree peaked roof and a closed outer skin."""
    x = LEGS[kind]["x"]
    floor, face, land, lip, f0, f1, end, out = leg_stations()
    rn, bore, rf, rc = leg_radii()
    y0 = FLANK + LEG_GAP
    thigh, paw = leg_pieces(kind)

    def plate(cs, t, c):
        m = mf.Manifold.batch_hull([mf.Manifold.extrude(cs, t - c), mf.Manifold.extrude(cs.offset(-c, mf.JoinType.Round), t)])
        return m.rotate([90, 0, 0]).mirror([0, 1, 0]).translate([0, y0, 0])

    m = plate(thigh, out - y0, LEG_CHAMFER) + plate(paw, out - y0 + PAW_OUT, PAW_CHAMFER)
    boss = frustum_y(x, LEG_Z, face, LEG_BOSS, y0 + 0.01, LEG_BOSS + y0 + 0.01 - face, 128)
    m += boss ^ mf.Manifold.extrude(thigh, 5).rotate([90, 0, 0]).mirror([0, 1, 0]).translate([0, face - 1, 0])
    m ^= box(x - 30, x + 30, 0, 40, 0, 40)
    m -= frustum_y(x, LEG_Z, face - 0.5, bore + land - face + 0.5, land, bore, 128) + teardrop_y(x, LEG_Z, bore, land - 0.01, lip + 0.01)
    # the socket: its peak is kept LEG_SKIN-and-a-bit inside the boss's cone
    room = teardrop_y(x, LEG_Z, rc, lip, end)
    keep = LEG_BOSS - (face - lip) - MIN_FEATURE * np.sqrt(2) - 0.01
    m -= room ^ frustum_y(x, LEG_Z, lip, keep, end, keep + end - lip, 128)
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
        z0, g0 = FIRST_LAYER + 0.02, BED_GAP + 0.02    # straight up from the bed first: the first layer's gap is all of g0
        return [(0, -1), (f + g0, -1), (f + g0, z0), (s + gs, z0 + f + g0 - s - gs), (s + gs, top), (s + gs + 12, top + 12), (0, top + 12)]
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
    """The mouth: a short shallow V groove across the front of the muzzle."""
    d, e = MOUTH + grow * np.sqrt(2), grow
    return prism_xz([(-1, MOUTH_Z - d - 1), (d, MOUTH_Z), (-1, MOUTH_Z + d + 1)], -MOUTH_Y - e, MOUTH_Y + e)


def ear(side, grow=0.0):
    (x0, x1), (y0, y1), (z0, z1), r0, r1 = EARS[0]
    return mf.Manifold.batch_hull([ball(r0 + grow, x0, side * y0, z0), ball(r1 + grow, x1, side * y1, z1)])


def make_head(stub=False):
    """Returns the head, the orange, and where things ended up. `stub` gives only the
    back of the head with its hinge, for the test strip."""
    blobs = [ball(4.0, x, s * 3.3, z) for x in (10.5, 17.0) for s in (-1, 1) for z in (2.76, HEAD_TOP - 4.0)]
    if not stub:
        blobs += [ball(2.8, 2.8, s * 3.3, z) for s in (-1, 1) for z in (1.93, MUZZLE_TOP - 2.8)]   # blunt muzzle
    head = mf.Manifold.batch_hull(blobs) ^ box(0, 40, -20, 20, 0, 40)
    # the nape: above where the hollow back reaches 45 degrees it would lean back over the body
    # too flat to print, so from there up the back of the head rises forwards at 45 degrees
    k = (R_NOD + NECK_GAP) * np.sqrt(0.5)
    head -= prism_xz([(NECK_X - k, NECK_Z + k), (NECK_X + 20, NECK_Z + k), (NECK_X + 20, NECK_Z + k + 30), (NECK_X - k - 30, NECK_Z + k + 30)], -20, 20)
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
    black = union([eye_cone(s, ys, 0.12) for s in (-1, 1)] + [nostril_cone(s, 0.12) for s in (-1, 1)])
    nose = mf.Manifold.sphere(1.0, 128).scale(list(NOSE)).translate([NOSE_AT[0], 0, NOSE_AT[1]])
    ears = (ear(1, 0.05) + ear(-1, 0.05)) ^ box(0, 40, -20, 20, EAR_FROM, 40)
    info["paint"]["head"] = [(black, BLACK), (nose + ears + mouth_cut(0.12), DARK)]
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
    """A low eye on the rump. The hole is sunk below the back; a web KEYRING_T thick
    with KEYRING_WALL round the hole and over its peak stands over it as a low round
    hump, and each side of the web a scoop in the back, rising outwards to nothing,
    gives a split ring room to pass through and swing. All the scoops' faces look up."""
    r, t, q = KEYRING_D / 2, KEYRING_T / 2, KEYRING_SCOOP
    rr = r + KEYRING_WALL
    plate = lambda rad, cz: prism_xz([(KEYRING_X + rad * np.cos(a), cz + rad * np.sin(a))
                                      for a in np.linspace(0, 2 * np.pi, 64, endpoint=False)], -t, t)
    f = KEYRING_FOOT
    foot = box(KEYRING_X - rr + 0.8, KEYRING_X + rr - 1.2, -t - f, t + f, KEYRING_Z - r - 0.8, KEYRING_Z - r - 0.7)
    lug = mf.Manifold.batch_hull([plate(rr, KEYRING_Z), plate(KEYRING_WALL, KEYRING_Z + r * np.sqrt(2)), foot])
    seg = seg + (lug - socket_space(AXES[-1]))
    for s in (-1, 1):
        ends = [(s * (t + q), KEYRING_Z - r - 0.2 + q), (s * (FLANK + 1.5), KEYRING_Z + r + q + 1.2)]
        seg -= mf.Manifold.batch_hull([ball(q, KEYRING_X, y, z + up) for y, z in ends for up in (0, 12)])
    return seg - keyhole(-t - 1, t + 1)


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
    segs[0], segs[-1] = leg_mount(segs[0], "front"), leg_mount(segs[-1], "hind")
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
    a = leg_mount(neck_mount(a), "front", (1,))
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
BED = 0.001           # sections 'at the bed' are taken this far above it: a clip face exactly on the bed joins every void


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
    for z in [BED, 0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, Z_C]:
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
        if s > 0 and f"{kind} leg pin" not in pins:
            face = parts[name].bounding_box()[1]              # the boss's face, as built
            clip = (g["x"] - 12, g["x"] + 12, face, face + 8, -1, 20)
            walls[f"{kind} leg round its pin's socket"] = cavity_wall(parts[name], clip, (g["x"], face + 0.1, LEG_Z))
            body = parts[leg_body(kind, axes)]
            land, lip = leg_stations()[2:4]                   # the pin where it passes through the lip
            pins[f"{kind} leg pin"] = min(extent(piece_at(section_y(body, y), g["x"], -LEG_Z - 0.5))
                                          for y in np.linspace(land + 0.01, lip, 6))
    for i, at in enumerate(axes):
        front, rear = parts[f"body {i + 1}"], parts[f"body {i + 2}"]
        k = f" {i + 1}" if len(axes) > 1 else ""
        clip = (at - 2, at + R_BALL + 3, -12, 12, BED, Z_RIM - BLEND * np.sqrt(2) - 0.05)
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
        clip = (NECK_X - 5, NECK_X + 5, -w, w, BED, NECK_Z + 8)                 # between the tab's true faces, from the bed
        walls["neck tab round its sockets"] = min(cavity_wall(head, clip, (NECK_X, s * (w - 0.3), NECK_Z)) for s in (-1, 1))
        clip = (NECK_X - 6.5, NECK_X + rc + 4, -12, 12, BED, 30)
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
        clip = (KEYRING_X - 7, KEYRING_X + 7, -t, t, KEYRING_Z - 4, KEYRING_Z + 8)
        walls["keyring eye round its hole"] = cavity_wall(b4, clip, (KEYRING_X, 0, KEYRING_Z))
        # the web between the two scoops: its run of solid across the body through the middle, at
        # heights from the hole's bottom to above its peak (beside the hole where the hole is)
        r = KEYRING_D / 2
        web = []
        for x, z in [(KEYRING_X + r + 0.5, KEYRING_Z - r), (KEYRING_X + r + 0.5, KEYRING_Z), (KEYRING_X - r - 0.5, KEYRING_Z),
                     (KEYRING_X, KEYRING_Z + r * np.sqrt(2) + 0.3), (KEYRING_X, KEYRING_Z + r * np.sqrt(2) + 1.0)]:
            run = piece_at(b4.slice(float(z)) ^ mf.CrossSection.square([0.04, 40]).translate([x - 0.02, -20]), x, 0).bounds()
            web.append(run[3] - run[1])
        info["lug"] = (min(web), min(b - a for a, b in column(b4, KEYRING_X, 0, KEYRING_Z)), b4.bounding_box()[5])
    return walls, pins


def leg_body(kind, axes):
    return "body 1" if kind == "front" else f"body {len(axes) + 1}"


def printable(cs, w=NOZZLE):
    """What is left of a layer when everything a nozzle w wide cannot get into is dropped."""
    return cs.offset(-w / 2, mf.JoinType.Round, 2.0, 32).offset(w / 2, mf.JoinType.Round, 2.0, 32) ^ cs


def leg_hold(leg_, body, x, side, layer=0.2, bite=0.3):
    """How well a leg is held on its pin by material that will really be printed. The
    leg is pulled straight off sideways until it touches (its play), then `bite`
    further, and what overlaps is measured twice: on the solids, and layer by layer
    after dropping from both everything a nozzle cannot print. Returns the play, the
    share of the interference that is left, and the hold: the least, in any layer of
    HOLD_BAND above the pin's axis, that the printable flange reaches over the printable
    lip on either side of the pin."""
    touches = lambda d: (leg_.translate([0, side * d, 0]) ^ body).volume() > 1e-7
    hi = next((d for d in np.arange(0.05, 4.0, 0.05) if touches(d)), None)
    if hi is None:
        return 4.0, 0.0, 0.0                    # it comes straight off
    lo = hi - 0.05
    for _ in range(8):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if touches(mid) else (mid, hi)
    pull = side * (lo + bite)
    exact = (leg_.translate([0, pull, 0]) ^ body).volume()
    window = mf.CrossSection.square([16, 8]).translate([x - 8, FLANK - 2 if side > 0 else -FLANK - 6])
    left, hold = 0.0, []
    for z in np.arange(layer / 2, leg_.bounding_box()[5], layer):
        if abs(z - LEG_Z) > 8:
            continue
        over = printable(leg_.slice(float(z))).translate([0, pull]) ^ printable(body.slice(float(z)) ^ window)
        left += over.area() * layer
        if HOLD_BAND[0] <= z - LEG_Z <= HOLD_BAND[1]:
            sides = [over ^ mf.CrossSection.square([8, 40]).translate([x - 8 * k, -20]) for k in (0, 1)]
            hold.append(min(0.0 if c.is_empty() else c.bounds()[2] - c.bounds()[0] for c in sides))
    return lo, left / max(exact, 1e-9), min(hold)


def leg_map(parts, joints, j, free, step=2.5):
    """Swing leg j every `step` degrees out to the range it is meant to have, at every
    `step` degrees of the body joint beside it across that joint's whole free range.
    Returns the smallest free swing each way, and the joint angle it was found at."""
    bj = next(k for k in joints if k["name"] == j["beside"])
    name = j["name"]
    others = {n: p for n, p in parts.items() if n != name}
    worst, at = [j["want"], j["want"]], 0.0
    angles = sorted(set(np.arange(-free[1], free[0] + 1e-6, step)) | {-free[1], free[0], 0.0})
    for phi in angles:
        pose = {bj["name"]: phi}
        pivot = posed({name: ball(0.01, *j["point"])}, joints, pose)[name].bounding_box()
        c = [(pivot[i] + pivot[i + 3]) / 2 for i in range(3)]
        near = box(c[0] - 16, c[0] + 16, c[1] - 40, c[1] + 40, -1, 40)
        rest = union(p ^ near for p in posed(others, joints, pose).values())
        for k, sign in enumerate((1, -1)):
            reached = 0.0
            for a in np.arange(step, j["want"] + 1e-6, step):
                turned = posed({name: parts[name]}, joints, dict(pose, **{name: sign * a}))[name]
                if (turned ^ rest).volume() > 1e-6:
                    break
                reached = a
            if reached < worst[k]:
                worst[k], at = reached, phi
    return worst, at


def tilt_limit(front, rear, at, axis, sign, stop, step=0.5):
    """How far a body joint can be turned the wrong way, measured on the solids. The
    rear segment is turned about the crosswise ('y': + folds the joint up, nose of the
    rear segment rising) or lengthwise ('x': twist) axis through the joint at height
    TILT_Z, `step` degrees at a time, and at each angle is free to shift: first near
    where it last fitted, then anywhere on a grid 0.2 mm apart (refined to 0.05 round
    the best places). Returns the largest angle, up to `stop`, at which it still fits
    somewhere without touching the front segment."""
    import itertools
    ref = [at, 0, TILT_Z]
    fixed = front ^ box(at - 17, at + 17, -30, 30, -5, 40)
    moving = rear ^ box(at - 14, at + 14, -30, 30, -5, 40)
    if axis == "y":
        grid = (np.arange(-0.8, 2.41, 0.2), [0.0], np.arange(-0.8, 3.61, 0.2))
    else:
        grid = ([0.0, 0.3], np.arange(-1.0, 1.01, 0.2), np.arange(-0.8, 1.21, 0.2))
    free = [len(g) > 1 for g in grid]
    last, best = (0.0, 0.0, 0.0), 0.0
    for deg in np.arange(step, stop + 1e-6, step):
        turned = turn(moving, axis, ref, sign * deg)
        hits = lambda d: (turned.translate([float(c) for c in d]) ^ fixed).volume() > 1e-6
        near = itertools.product(*[[last[k] + e for e in ((0, -0.1, 0.1, -0.2, 0.2) if free[k] else (0,))] for k in range(3)])
        found = next((d for d in near if not hits(d)), None)
        if found is None:
            vols = sorted(((turned.translate([float(c) for c in d]) ^ fixed).volume(), d) for d in itertools.product(*grid))
            fine = [np.arange(-0.15, 0.151, 0.05) if free[k] else [0.0] for k in range(3)]
            tries = (tuple(a + b for a, b in zip(d0, e)) for _, d0 in vols[:4] for e in itertools.product(*fine))
            found = vols[0][1] if vols[0][0] < 1e-6 else next((d for d in tries if not hits(d)), None)
        if found is None:
            break
        last, best = tuple(float(c) for c in found), float(deg)
    return best


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
    first = {n: p ^ box(-100, 200, -100, 100, -1, FIRST_LAYER) for n, p in parts.items()}
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
    #    leg is swung again at every 2.5 degrees of the body joint beside it
    lines, free_of = {}, {}
    for j in joints:
        free, gap = sweep(parts, joints, j)
        free_of[j["name"]] = free
        if min(free) < j["want"] - 1e-6:
            raise SystemExit(f"{j['name']} only swings +{free[0]:.0f}/-{free[1]:.0f} degrees, wanted {j['want']:.0f}")
        line = f"   {j['name']:<16} {spread(free):<16} tightest gap {gap:.2f} mm"
        if j["stop"]:
            if max(free) > j["stop"]:
                raise SystemExit(f"{j['name']} swings +{free[0]:.0f}/-{free[1]:.0f} degrees: nothing stops it by {j['stop']:.0f}")
            line += f"; stopped both ways before {j['stop']:.0f}"
        lines[j["name"]] = line
    for j in joints:
        if j["beside"]:
            far = free_of[j["beside"]]
            worst, at = leg_map(parts, joints, j, far)
            if min(worst) < j["want"] - 1e-6:
                raise SystemExit(f"{j['name']} only swings +{worst[0]:g}/-{worst[1]:g} with {j['beside']} at {at:+g}")
            lines[j["name"]] += (f"; at least +{worst[0]:g}/-{worst[1]:g} with {j['beside']} anywhere "
                                 f"from -{far[1]:g} to +{far[0]:g} (every 2.5)")
    out += [lines[j["name"]] for j in joints]

    # 2a. the body joints turned the wrong way: folded up, folded down and twisted
    for i, at in enumerate(info["axes"]):
        front, rear = parts[f"body {i + 1}"], parts[f"body {i + 2}"]
        up, down, twist = (tilt_limit(front, rear, at, axis, sign, limit + 0.5)
                           for axis, sign, limit in (("y", 1, MAX_FOLD), ("y", -1, MAX_TILT), ("x", 1, MAX_TILT)))
        name = f"body joint {i + 1}"
        if up > MAX_FOLD or down > MAX_TILT or twist > MAX_TILT:
            raise SystemExit(f"{name} is too loose the wrong way: it folds up {up:g}, down {down:g} and twists {twist:g} degrees")
        lines[name] += f"; the wrong way it folds up {up:g}, down {down:g} and twists {twist:g} deg at most"
    out[-len(joints):] = [lines[j["name"]] for j in joints]

    # 2b. each leg: enough bed under it, and held on its pin by material a nozzle can print
    feet, holds = [], []
    for name, (kind, s) in info["legs"].items():
        foot = parts[name].slice(1e-3).area()
        if foot < MIN_FOOT:
            raise SystemExit(f"{name} stands on only {foot:.1f} mm2 of bed, wanted {MIN_FOOT:g}")
        play, left, hold = leg_hold(parts[name], parts[leg_body(kind, info["axes"])], LEGS[kind]["x"], s)
        if hold < MIN_HOLD or left < 0.6:
            raise SystemExit(f"{name}: as printed with a {NOZZLE} mm nozzle its pin's flange holds only {hold:.2f} mm of lip "
                             f"each side, {100 * left:.0f}% of the interference of the exact solids")
        feet.append(foot)
        holds.append((hold, left, play))
    worst = min(holds)
    out.append(f"   legs: {min(feet):.1f} mm2 or more of bed under each; pulled off sideways they move {worst[2]:.2f} mm and stop on "
               f"{worst[0]:.2f} mm or more of flange over lip each side in every layer {HOLD_BAND[0]:g}-{HOLD_BAND[1]:g} mm above the pin's "
               f"axis, {100 * worst[1]:.0f}% of the exact interference left, once everything a {NOZZLE} mm nozzle cannot print is dropped")

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
        thick, over, top = info["lug"]
        if thick < 4.0 or over < 2.0 or top > KEYRING_TOP:
            raise SystemExit(f"keyring eye: web {thick:.2f} thick, {over:.2f} over the hole's peak, top at {top:.2f}")
        out.append(f"   keyring eye: web {thick:.2f} thick at its thinnest, {over:.2f} over the hole's peak, top at {top:.2f} (limit {KEYRING_TOP:g})")

    # 7. overall size (the full model only)
    if info["full"]:
        lo, hi = np.array(union(parts.values()).bounding_box()).reshape(2, 3)
        size = hi - lo
        if not LENGTH[0] <= size[0] <= LENGTH[1] or size[1] >= MAX_W or size[2] >= MAX_H:
            raise SystemExit(f"size {size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} is outside the brief")
        back = max(parts[n].bounding_box()[5] for n in parts if n.startswith("body"))
        out.append(f"   nose to rump {size[0]:.1f}, width {size[1]:.1f}, height {size[2]:.1f} "
                   f"(top of the {'keyring eye' if info['loop'] else 'back'} {back:.1f})")
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
    if KEYRING_D:                    # the keyring eye is optional: the plain back must pass too
        parts, joints, info = make_capybara(loop=False)
        check(parts, joints, info)
        print("pocket capybara without the keyring eye: passes every check as well\n")
    build(NAME, make_capybara, "pocket capybara")


if __name__ == "__main__":
    main()
