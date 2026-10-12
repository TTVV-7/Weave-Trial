"""Genie GTH-1056 telehandler pen holder: the machine seen from the cab side,
as a 1:32 relief with a flat back, to sit on the desk against the wall (a
3M / Command strip on the back keeps it there when pens are pulled out).

The boom runs over the cab and telescopes: the base section is a hollow
sleeve, and the fly section, with the boom head, carriage and forks on it,
is a separate print that slides in from the front. It slides out about
80 mm; the forks ride on the desk at any reach, so they carry its weight.

Pens go in eight holes: two deep ones (about 85 mm) down through the back of
the boom, three in the engine hood and three in the cab roof. Proportions are
the GTH-1056 model's (telehandler/gth1056.py), with the boom raised clear of
the cab and the forks cut to about half length so it fits a 256 mm bed.

Modelled standing (z up, x toward the forks, y out from the wall, back at
y = 0). Both pieces are written to the 3MF lying on their backs, side by side,
which is how they print: every part grows straight up from the bed, so no
supports. The pen holes have a pointed (teardrop) top for printing sideways,
and the sleeve's front wall bridges its 16 mm channel.
Four filaments: Genie blue, black, light grey, window glass.
"""
import os
import numpy as np, trimesh
from trimesh.creation import cylinder
from common import hull, u, d, x_, write_3mf, report

HERE = os.path.dirname(os.path.abspath(__file__))
S = 1/32                                    # scale: real mm -> model mm
PEN_D, PEN_FLOOR = 14.0, 15.0               # pen hole diameter and bottom (model mm)
GLASS = 1.0                                 # window inlay depth
SINK = 0.8                                  # tyres flattened this much to stand steady
BLUE, BLACK, GREY, GLASS_RGB = (0x00, 0x6B, 0xC2), (0x1E, 0x1E, 0x20), (0xC8, 0xCA, 0xCC), (0x4F, 0x6B, 0x7D)

# Telescopic boom, in model mm. The sleeve runs over the cab roof.
BOOM_X0, MOUTH = 1, 148                     # back end and open front of the sleeve
BOOM_Z0, BOOM_H, BOOM_D = 80, 22, 24        # bottom, height, depth out from the wall
WALL = 3
CH_Y, CH_Z = (WALL, 19), (BOOM_Z0 + WALL, BOOM_Z0 + BOOM_H - WALL)   # the channel
CH_END = 40                                 # back of the channel, the fly stops here
CLEAR = 0.3                                 # sliding clearance, each side
FLY_FRONT = 195                             # where the fly meets the head, retracted
MIN_OVERLAP = 25
MAX_EXTEND = MOUTH - MIN_OVERLAP - CH_END   # about 80 mm

# --- Helpers ------------------------------------------------------------------
def side(pts, y0, y1, s=S):
    """A convex side profile (x, z; real mm unless s=1), extruded from y0 to y1."""
    return hull([(x*s, y, z*s) for x, z in pts for y in (y0, y1)])

def rect(x0, x1, z0, z1, y0, y1, s=S): return side([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], y0, y1, s)
def mrect(x0, x1, z0, z1, y0, y1): return rect(x0, x1, z0, z1, y0, y1, 1)     # model mm

def ycyl(r, x, z, y0, y1, n=64):
    """A cylinder along y (wheels, pins), real x, z, r; model y."""
    c = cylinder(radius=r*S, height=y1 - y0, sections=n)
    c.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, (1, 0, 0)))
    c.apply_translation((x*S, (y0 + y1)/2, z*S)); return c

def round_rect(x0, x1, z0, z1, r, y0, y1, s=S):
    pts = [(cx + r*np.cos(a), cz + r*np.sin(a)) for cx in (x0 + r, x1 - r) for cz in (z0 + r, z1 - r)
           for a in np.linspace(0, 2*np.pi, 24, endpoint=False)]
    return side(pts, y0, y1, s)

def teardrop(x, y, z0, z1, r=PEN_D/2):
    """A round hole along z whose cross-section comes to a 45 degree point
    toward +y, which is up while it prints on its back."""
    ring = [(x + r*np.cos(a), y + r*np.sin(a)) for a in np.linspace(0, 2*np.pi, 48, endpoint=False)]
    ring += [(x, y + r*np.sqrt(2))]
    return hull([(px, py, z) for px, py in ring for z in (z0, z1)])

def mouth(x, y, z):
    """Chamfer where a pen hole comes out of a top face at height z."""
    ring = np.linspace(0, 2*np.pi, 48, endpoint=False)
    return hull([(x + (PEN_D/2 + 1.5)*np.cos(a), y + (PEN_D/2 + 1.5)*np.sin(a), z + 0.01) for a in ring] +
                [(x + PEN_D/2*np.cos(a), y + PEN_D/2*np.sin(a), z - 1.5) for a in ring])

# --- Real dimensions (mm), from the GTH-1056 model ---------------------------
XR, XF, TR = 1310, 4810, 665                # axles and tyre radius
CX0, CX1, CZ0, CZ1 = 2500, 4150, 820, 2380  # cab
ROOF = (CZ1 + 70)*S                         # top of the cab roof, model mm
HOOD_X, HOOD_TOP, D_HOOD = (22, 77), 66, 45 # engine hood beside the cab, model mm
D_CAB, D_TYRE = 49, 46
assert BOOM_Z0 > ROOF + 2, "the boom has to clear the cab roof"

# --- Body: blue ---------------------------------------------------------------
sleeve = d(mrect(BOOM_X0, MOUTH, BOOM_Z0, BOOM_Z0 + BOOM_H, 0, BOOM_D),
           mrect(CH_END, MOUTH + 1, CH_Z[0], CH_Z[1], CH_Y[0], CH_Y[1]))
blue = u([
    rect(450, 6050, 380, 1080, 0, 30),                                  # frame
    round_rect(0, 700, 480, 1420, 120, 0, 38),                          # counterweight
    rect(5600, 6150, 450, 1500, 0, 36),                                 # front frame
    side([(5650, 1250), (5950, 1250), (5900, 320), (5700, 320)], 0, 42),   # stabilizer arm
    side([(0, 15), (38, 15), (38, BOOM_Z0 + 1), (6, BOOM_Z0 + 1), (0, BOOM_Z0 - 10)], 0, 30, 1),  # boom tower
    round_rect(HOOD_X[0], HOOD_X[1], 12, HOOD_TOP, 6, 0, D_HOOD, 1),    # engine hood
    sleeve,
])
grille = [mrect(x, x + 2, 30, 58, D_HOOD - 1, D_HOOD + 1) for x in np.arange(25, 75, 6.5)]

# --- Body: black -------------------------------------------------------------
black = u([ycyl(TR, xa, TR, 0, D_TYRE) for xa in (XR, XF)] +
          [rect(CX0, CX1, CZ0 - 60, CZ1, 0, D_CAB),                     # cab
           round_rect(CX0 - 40, CX1 + 40, CZ1, CZ1 + 70, 30, 0, D_CAB + 1),   # roof
           rect(2450, 3950, 420, 820, 0, 44),                           # fuel / hydraulic tank
           rect(2600, 2900, 420, 460, 0, 47),                           # cab step
           rect(5600, 6000, 280, 320, 0, 44),                           # stabilizer pad
           d(mrect(MOUTH - 4, MOUTH, BOOM_Z0 - 1, BOOM_Z0 + BOOM_H + 1, 0, BOOM_D + 1),   # wear pads
             mrect(MOUTH - 5, MOUTH + 1, CH_Z[0], CH_Z[1], CH_Y[0], CH_Y[1]))])

# --- Body: grey ----------------------------------------------------------------
grey = []
for xa in (XR, XF):
    grey += [ycyl(355, xa, TR, D_TYRE - 1, D_TYRE + 1.5), ycyl(140, xa, TR, D_TYRE, D_TYRE + 3)]
grey += [ycyl(70, 1150, 1600, 0, 32)]                                  # boom tower pin
def rod(r, a, b, y0, y1):
    """A round bar between two real (x, z) points."""
    a, b = np.array(a, float)*S, np.array(b, float)*S
    n = np.array([-(b - a)[1], (b - a)[0]]); n *= r*S/np.linalg.norm(n)
    return hull([(p[0] + s*n[0], y, p[1] + s*n[1]) for p in (a, b) for s in (-1, 1) for y in (y0, y1)])
grey += [rod(55, (5780, 1450), (5780, 700), 0, 44)]                     # stabilizer cylinder
grey = u(grey)

# --- Pen holes -----------------------------------------------------------------
REAR = [(11, 11), (29, 11)]                 # down through the back of the boom
HOOD = [(x, 32) for x in (33, 49, 65)]      # in front of the boom, so it does not cover them
CAB = [(x, 32) for x in (88, 104, 120)]
holes = u([teardrop(x, y, PEN_FLOOR, 200) for x, y in REAR + HOOD + CAB] +
          [mouth(x, y, BOOM_Z0 + BOOM_H) for x, y in REAR] +
          [mouth(x, y, HOOD_TOP) for x, y in HOOD] + [mouth(x, y, ROOF) for x, y in CAB])

# --- Windows: recessed into the front of the cab, filled by glass ------------
win = d(rect(CX0 + 120, CX1 - 120, CZ0 + 300, CZ1 - 80, D_CAB - GLASS, D_CAB + 5),
        rect(CX0 + 100, CX1 - 100, 1700, 1780, D_CAB - 5, D_CAB + 6))      # door rail splits the glass
glass = x_(win, rect(CX0, CX1, CZ0, CZ1, 0, D_CAB))

grey = d(grey, holes)
black = d(black, grey, holes, win)
blue = d(blue, black, grey, holes, *grille)
glass = d(glass, holes)

# --- Fly section: slides in the sleeve, carries head, carriage and forks -----
FY0 = CH_Y[0] + CLEAR                       # its back face, which goes on the bed
fly_bar = mrect(CH_END + CLEAR, FLY_FRONT, CH_Z[0] + CLEAR, CH_Z[1] - CLEAR, FY0, CH_Y[1] - CLEAR)
head = side([(FLY_FRONT - 3, CH_Z[1] - CLEAR), (204, CH_Z[1] - 1), (213, 72), (213, 32), (206, 32),
             (FLY_FRONT - 3, CH_Z[0] + CLEAR)], FY0, BOOM_D, 1)
fly_blue = u([fly_bar, head])
fly_black = d(u([mrect(213, 217, SINK, 53, FY0, 30), mrect(213, 215, 53, 62, FY0, 30),   # carriage
                 mrect(217, 219.5, SINK, 37, FY0, 30), mrect(217, 247, SINK, SINK + 3.7, FY0, 30)]),  # forks
              fly_blue)

# --- Assemble: sit it on the desk, each colour a part --------------------------
floor = mrect(-50, 400, SINK, 200, -50, 100)
def clean(m):
    """Drop the zero-volume slivers the booleans leave where faces touch."""
    return trimesh.util.concatenate([c for c in m.split(only_watertight=False) if abs(c.volume) > 1])
def place(m):
    m = clean(x_(m, floor)); m.apply_translation((0, 0, -SINK)); return m
body = [("body", BLUE, place(blue)), ("tyres, cab", BLACK, place(black)),
        ("rims, pins", GREY, place(grey)), ("glass", GLASS_RGB, place(glass))]
fly = [("boom fly and head", BLUE, place(fly_blue)), ("carriage and forks", BLACK, place(fly_black))]
report(body + fly)

def extended(e):
    out = []
    for n, c, m in fly:
        m = m.copy(); m.apply_translation((e, 0, 0)); out.append((n, c, m))
    return out

# --- Print layout: both pieces on their backs, side by side --------------------
lay = trimesh.transformations.rotation_matrix(np.pi/2, (1, 0, 0))     # y (out from the wall) -> z
printed = []
for n, c, m in body:
    m = m.copy(); m.apply_transform(lay); printed.append((n, c, m))
for n, c, m in fly:
    m = m.copy(); m.apply_translation((-CH_END, 0, 0)); m.apply_transform(lay)
    m.apply_translation((0, BOOM_Z0 + BOOM_H + 10, -FY0)); printed.append((n, c, m))
write_3mf(printed, HERE + "/genie_pen_holder.3mf", "Genie GTH-1056 pen holder")

# --- Preview, standing on the desk: retracted and extended ---------------------
if __name__ == "__main__":
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    L = np.array([0.3, 0.8, 0.6]); L /= np.linalg.norm(L)
    fig = plt.figure(figsize=(16, 6))
    views = [(body + extended(0), 12, 75, "retracted"), (body + extended(MAX_EXTEND), 12, 75, f"extended {MAX_EXTEND:.0f} mm"),
             (body + extended(0), 45, 120, "from above")]
    for k, (ps, elev, azim, title) in enumerate(views):
        tris = np.vstack([m.triangles for _, _, m in ps])
        cols = np.vstack([np.array(rgb)/255*(0.35 + 0.65*np.clip(m.face_normals @ L, 0.1, 1))[:, None] for _, rgb, m in ps])
        lo, hi = tris.reshape(-1, 3).min(0), tris.reshape(-1, 3).max(0)
        ax = fig.add_subplot(1, 3, k + 1, projection="3d")
        ax.add_collection3d(Poly3DCollection(tris, facecolors=cols, edgecolor="none"))
        ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1]); ax.set_zlim(lo[2], hi[2])
        ax.set_box_aspect(hi - lo); ax.view_init(elev=elev, azim=azim); ax.set_axis_off(); ax.set_title(title)
    plt.savefig(HERE + "/genie_preview.png", dpi=90, bbox_inches="tight"); plt.close(fig)
