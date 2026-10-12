"""Genie GTH-1056 telehandler pen holder: the machine seen from the cab side,
as a 1:32 relief with a flat back, to sit on the desk against the wall (a
3M / Command strip on the back keeps it there when pens are pulled out).

Pens go in ten holes drilled down through the boom and the cab. Proportions
are the GTH-1056 model's (telehandler/gth1056.py, boom stowed), with the forks
cut to about half length so it fits a 256 mm bed.

Modelled standing (z up, x toward the forks, y out from the wall, back at
y = 0), and written to the 3MF lying on its back, which is how it prints:
every part grows straight up from the bed, so it needs no supports. The pen
holes run sideways while printing, so they have a pointed (teardrop) top.
Four filaments: Genie blue, black, light grey, window glass.
"""
import os
import numpy as np, trimesh
from trimesh.creation import cylinder
from common import hull, u, d, x_, write_3mf, report

HERE = os.path.dirname(os.path.abspath(__file__))
S = 1/32                                    # scale: real mm -> model mm (x and z)
PEN_D, PEN_FLOOR = 14.0, 15.0               # pen hole diameter and bottom (model mm)
GLASS = 1.0                                 # window inlay depth

def P(x, z): return (x*S, z*S)              # real side-view point -> model x, z

def side(pts, y0, y1):
    """A convex side profile (real x, z), extruded from the wall out to y1."""
    return hull([(x*S, y, z*S) for x, z in pts for y in (y0, y1)])

def rect(x0, x1, z0, z1, y0, y1): return side([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], y0, y1)

def ycyl(r, x, z, y0, y1, n=64):
    """A cylinder along y (wheels, pins), real x, z, r; model y."""
    c = cylinder(radius=r*S, height=y1 - y0, sections=n)
    c.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, (1, 0, 0)))
    c.apply_translation((x*S, (y0 + y1)/2, z*S)); return c

def round_rect(x0, x1, z0, z1, r, y0, y1):
    pts = [(cx + r*np.cos(a), cz + r*np.sin(a)) for cx in (x0 + r, x1 - r) for cz in (z0 + r, z1 - r)
           for a in np.linspace(0, 2*np.pi, 24, endpoint=False)]
    return side(pts, y0, y1)

# --- Real dimensions (mm), from the GTH-1056 model ---------------------------
XR, XF, TR = 1310, 4810, 665                # axles and tyre radius
FORK_END = 6880 + 1000                      # tines shortened from 1830
# boom centre line, for the telescopic sections
def zc(x): return 2275 - 300*(x - 150)/4600
def section(x0, x1, h): return [(x0, zc(x0) - h/2), (x0, zc(x0) + h/2), (x1, zc(x1) + h/2), (x1, zc(x1) - h/2)]

# Depths out from the wall (model mm): the boom is the deepest blue part, the
# cab and tyres stand proud of it, so the relief reads front to back.
D_HOOD, D_BOOM, D_CAB, D_TYRE = 30, 34, 48, 46

# --- Blue: frame, counterweight, hood, boom ----------------------------------
blue = [
    rect(450, 6050, 380, 1080, 0, 30),                                  # frame
    round_rect(0, 700, 480, 1420, 120, 0, 38),                          # counterweight
    rect(5600, 6150, 450, 1500, 0, 36),                                 # front frame
    side([(5650, 1250), (5950, 1250), (5900, 320), (5700, 320)], 0, 42),   # stabilizer arm
    side([(800, 700), (2700, 700), (2700, 1550), (2580, 1650), (920, 1650), (800, 1550)], 0, D_HOOD),  # hood
    side([(150, 1080), (800, 1080), (650, 2050), (250, 2050)], 0, 36),  # boom pivot towers
    # solid behind the boom and cab: the pen holes need something to go through
    side([(700, 1080), (2500, 1080), (2500, 2420), (700, zc(700) + 250)], 0, 26),
    side([(150, 1960), (150, 2590), (4750, 2250), (4750, 1700)], 0, D_BOOM),     # boom base
    side(section(4400, 5300, 480), 0, D_BOOM - 2),                      # telescopic sections step
    side(section(4900, 5800, 420), 0, D_BOOM - 4),                      #   down in height and depth
    side(section(5400, 6250, 360), 0, D_BOOM - 6),
    side([(6150, 2120), (6550, 2040), (6800, 1350), (6750, 900), (6450, 950), (6150, 1600)], 0, D_BOOM),  # head
]
blue = u(blue)

# --- Black: tyres, cab, carriage, forks, wear pads, stabilizer pad, tank ------
CX0, CX1, CZ0, CZ1 = 2500, 4150, 820, 2380
black = [ycyl(TR, xa, TR, 0, D_TYRE) for xa in (XR, XF)]
black += [rect(CX0, CX1, CZ0 - 60, CZ1, 0, D_CAB),                      # cab
          round_rect(CX0 - 40, CX1 + 40, CZ1, CZ1 + 70, 30, 0, D_CAB + 1),   # roof
          rect(2450, 3950, 420, 820, 0, 44),                            # fuel / hydraulic tank
          rect(2600, 2900, 420, 460, 0, 47),                            # cab step
          rect(5600, 6000, 280, 320, 0, 44),                            # stabilizer pad
          rect(6780, 6880, 180, 1250, 0, 30), rect(6780, 6840, 1250, 1650, 0, 30),   # carriage
          ]
# the forks, one behind the other from the side; at 1:32 they are under 2 mm
# tall, so they are one wide piece from the wall out, which prints without a gap to bridge
black += [rect(6880, 6937, 60, 1150, 0, 28), rect(6880, FORK_END, 60, 117, 0, 28)]
black += [rect(x - 50, x + 50, zc(x) - h/2 - 10, zc(x) + h/2 + 10, 0, dep)
          for x, h, dep in ((4750, 550, D_BOOM + 1), (5300, 480, D_BOOM - 1), (5800, 420, D_BOOM - 3))]
black = u(black)

# --- Light grey: rims, hubs, pins, cylinders ---------------------------------
grey = []
for xa in (XR, XF):
    grey += [ycyl(355, xa, TR, D_TYRE - 1, D_TYRE + 1.5), ycyl(140, xa, TR, D_TYRE, D_TYRE + 3)]
grey += [ycyl(70, 380, 1850, 0, 38),                                    # boom pivot pin
         ycyl(55, 6760, 1150, 0, 33)]                                    # carriage pin
def rod(r, a, b, y0, y1):
    """A round bar between two real (x, z) points, sunk to the wall."""
    a, b = np.array(a, float)*S, np.array(b, float)*S
    n = np.array([-(b - a)[1], (b - a)[0]]); n *= r*S/np.linalg.norm(n)
    return hull([(p[0] + s*n[0], y, p[1] + s*n[1]) for p in (a, b) for s in (-1, 1) for y in (y0, y1)])
grey += [rod(60, (6200, 1750), (6650, 900), 0, 31),                      # tilt cylinder
         rod(55, (5780, 1450), (5780, 700), 0, 44)]                      # stabilizer cylinder
grey = u(grey)

# --- Pen holes, top down through the boom and the cab ------------------------
def teardrop(x, y, z0, z1, r=PEN_D/2):
    """A round hole along z whose cross-section comes to a 45 degree point
    toward +y, which is up while it prints on its back."""
    ring = [(x + r*np.cos(a), y + r*np.sin(a)) for a in np.linspace(0, 2*np.pi, 48, endpoint=False)]
    ring += [(x, y + r*np.sqrt(2))]
    return hull([(px, py, z) for px, py in ring for z in (z0, z1)])
holes = [teardrop(x*S, 13, PEN_FLOOR, 200) for x in (600, 1150, 1700, 2250)]       # boom row
holes += [teardrop(x*S, y, PEN_FLOOR, 200) for x in (2820, 3330, 3840) for y in (13, 33)]   # cab, two rows
# chamfer the mouths where they come out of the cab roof
holes += [hull([(x*S + (PEN_D/2 + 1.5)*np.cos(a), y + (PEN_D/2 + 1.5)*np.sin(a), (CZ1 + 70)*S + 0.01)
                for a in np.linspace(0, 2*np.pi, 48, endpoint=False)] +
               [(x*S + PEN_D/2*np.cos(a), y + PEN_D/2*np.sin(a), (CZ1 + 70)*S - 1.5)
                for a in np.linspace(0, 2*np.pi, 48, endpoint=False)])
          for x in (2820, 3330, 3840) for y in (13, 33)]
holes = u(holes)

# --- Windows: recessed into the front of the cab, filled by glass ------------
win = d(rect(CX0 + 120, CX1 - 120, CZ0 + 300, CZ1 - 80, D_CAB - GLASS, D_CAB + 5),
        rect(CX0 + 100, CX1 - 100, 1700, 1780, D_CAB - 5, D_CAB + 6))      # door rail splits the glass
glass = x_(win, rect(CX0, CX1, CZ0, CZ1, 0, D_CAB))

# --- Each colour owns its space, front parts win ------------------------------
grey = d(grey, holes)
black = d(black, grey, holes, win)
blue = d(blue, black, grey, holes)
glass = d(glass, holes)
parts = [("body", (0x00, 0x6B, 0xC2), blue), ("tyres, cab, forks", (0x1E, 0x1E, 0x20), black),
         ("rims, pins, cylinders", (0xC8, 0xCA, 0xCC), grey), ("glass", (0x4F, 0x6B, 0x7D), glass)]
# flatten the tyre bottoms so it stands steady on the desk
floor = trimesh.creation.box(bounds=((-50, -50, 0.8), (400, 100, 200)))
def clean(m):
    """Drop the zero-volume slivers the booleans leave where faces touch."""
    return trimesh.util.concatenate([c for c in m.split(only_watertight=False) if abs(c.volume) > 1])
parts = [(n, c, clean(x_(m, floor))) for n, c, m in parts]
for _, _, m in parts: m.apply_translation((0, 0, -0.8))
report(parts)

# --- Lay it on its back to print: wall side down ----------------------------
lay = trimesh.transformations.rotation_matrix(np.pi/2, (1, 0, 0))     # y (out from the wall) -> z
printed = []
for n, c, m in parts:
    m = m.copy(); m.apply_transform(lay); printed.append((n, c, m))
write_3mf(printed, HERE + "/genie_pen_holder.3mf", "Genie GTH-1056 pen holder")

# --- Preview, standing on the desk: from the front and from above -------------
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
L = np.array([0.3, 0.8, 0.6]); L /= np.linalg.norm(L)
tris = np.vstack([m.triangles for _, _, m in parts])
cols = np.vstack([np.array(rgb)/255*(0.35 + 0.65*np.clip(m.face_normals @ L, 0.1, 1))[:, None] for _, rgb, m in parts])
lo, hi = tris.reshape(-1, 3).min(0), tris.reshape(-1, 3).max(0)
fig = plt.figure(figsize=(14, 6))
for k, (elev, azim) in enumerate(((12, 75), (40, 120))):
    ax = fig.add_subplot(1, 2, k + 1, projection="3d")
    ax.add_collection3d(Poly3DCollection(tris, facecolors=cols, edgecolor="none"))
    ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1]); ax.set_zlim(lo[2], hi[2])
    ax.set_box_aspect(hi - lo); ax.view_init(elev=elev, azim=azim); ax.set_axis_off()
plt.savefig(HERE + "/genie_preview.png", dpi=100, bbox_inches="tight"); plt.close(fig)
