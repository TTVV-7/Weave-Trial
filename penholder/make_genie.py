"""Genie GTH-1056 telehandler pen holder, built from the GTH-1056 STEP model
(telehandler/gth1056.py, boom stowed) at 1:35: the boom beside the cab, two
forks, the full 72 in tines.

It stands on the desk with its engine side to the wall. That side is cut flat
at the engine hood, so a 3M / Command strip on the hood keeps it put when pens
are pulled out. Pens go in three holes down through the engine hood, and the
cab is an open-top cup: glass all round, so with clear filament you see the
pens inside it.

It prints standing on its wheels with no supports. To get there, a few things
reach the bed that sit just off the ground on the real machine (the frame,
the tank under the cab, the carriage and forks, the stabilizers, which are
shown let down), and the boom has a 45 degree web under it on the side you
do not see. Four filaments: Genie blue, black, light grey, window glass.
"""
import os
import numpy as np, trimesh
from trimesh.creation import cylinder
from common import hull, u, d, x_, write_3mf, report

HERE = os.path.dirname(os.path.abspath(__file__))
S = 1/35                                    # scale
BACK = -1220                                # real y of the flat back (the engine hood's outer face)
SINK = 28                                   # real mm the tyres sink, so they stand on flats
PEN_D = 14.0                                # pen hole diameter, model mm
BLUE, BLACK, GREY, GLASS = (0x00, 0x6B, 0xC2), (0x1E, 0x1E, 0x20), (0xC8, 0xCA, 0xCC), (0x6E, 0x8C, 0xA0)

# --- Solids, all in real mm (x forward, y to the cab side, z up) --------------
def box(x0, x1, y0, y1, z0, z1): return trimesh.creation.box(bounds=((x0, y0, z0), (x1, y1, z1)))
def side(pts, y0, y1): return hull([(x, y, z) for x, z in pts for y in (y0, y1)])
def rod(r, p0, p1, n=48):
    return cylinder(radius=r, segment=(np.array(p0, float), np.array(p1, float)), sections=n)
def rounded(x0, x1, y0, y1, z0, z1, r, axis):
    """A box with its edges along `axis` ("x" or "y") rounded to r."""
    a = np.linspace(0, 2*np.pi, 24, endpoint=False)
    if axis == "y":
        pts = [(cx + r*np.cos(t), cz + r*np.sin(t)) for cx in (x0 + r, x1 - r) for cz in (z0 + r, z1 - r) for t in a]
        return side(pts, y0, y1)
    pts = [(x, cy + r*np.cos(t), cz + r*np.sin(t)) for cy in (y0 + r, y1 - r) for cz in (z0 + r, z1 - r) for t in a for x in (x0, x1)]
    return hull(pts)

WB = 3500; XR, XF = 1310, 1310 + WB         # axles (11 ft 6 in wheelbase)
TR, TW, TY0 = 665, 400, 1095                # tyre radius, width, centre offset
CX0, CX1, CY0, CY1, CZ0, CZ1 = 2500, 4150, 320, 1240, 820, 2380   # cab
ROOF = CZ1 + 70
GW = 70                                     # cab glass / post thickness (2 mm printed)

blue, black, grey, glass = [], [], [], []

# Wheels: tyre, then a rim and hub standing proud on the outer face
for xa in (XR, XF):
    black.append(rod(110, (xa, -TY0, TR), (xa, TY0, TR)))              # axle
    black.append(box(xa - 260, xa + 260, -260, 260, TR - 230, TR + 230))   # diff
    for s in (1, -1):
        y0, y1 = sorted((s*(TY0 - TW/2), s*(TY0 + TW/2)))
        black.append(rod(TR, (xa, y0, TR), (xa, y1, TR), 96))
        out = y1 if s > 0 else y0
        grey.append(rod(355, (xa, out - s*10, TR), (xa, out + s*35, TR), 64))   # rim
        grey.append(rod(140, (xa, out, TR), (xa, out + s*70, TR), 32))          # hub

# Frame, down to the desk between the wheels (set back, in shadow)
blue.append(box(450, 6050, -470, 470, 0, 1080))
# Counterweight, its underside sloped in to the frame so it prints
cw = rounded(0, 700, -1000, 1000, 480, 1420, 120, "y")
blue.append(u([cw, hull(np.vstack([cw.vertices[cw.vertices[:, 2] < 600], box(0, 700, -470, 470, 0, 10).vertices]))]))
black.append(box(-15, 0, -800, 800, 1150, 1230))                       # rear light bar
# Front frame, wide enough to carry the stabilizers, sloped in underneath
ff = box(5600, 6150, -700, 700, 450, 1500)
blue.append(hull(np.vstack([ff.vertices, box(5600, 6050, -470, 470, 0, 10).vertices])))
for s in (1, -1):                                                      # stabilizers, let down
    blue.append(side([(5650, 1250), (5950, 1250), (5900, 40), (5700, 40)], *sorted((s*690, s*820))))
    black.append(box(5600, 6000, *sorted((s*600, s*920)), 0, 40))
    grey.append(rod(55, (5780, s*760, 1450), (5780, s*760, 700)))
# Engine hood on the wall side, carried down to the desk (that side is not seen)
blue.append(u([rounded(800, 2700, BACK, -480, 0, 1650, 120, "x"), box(800, 2700, BACK, -480, 0, 1500)]))
# Tank and step under the cab, and a base under the cab cup
black.append(box(2450, 3950, 480, 1150, 0, 820))
black.append(box(2600, 2900, 1150, 1260, 420, 460))
black.append(box(CX0, CX1, CY0, CY1, 0, CZ0))

# Cab: posts, roof rim, glass walls; open on top, a cup for pens
for x in (CX0, CX1 - GW):
    for y in (CY0, CY1 - GW):
        black.append(box(x, x + GW, y, y + GW, CZ0, CZ1))
roof = d(rounded(CX0 - 40, CX1 + 40, CY0 - 30, CY1 + 30, CZ1, ROOF, 60, "x"),
         box(CX0 + GW, CX1 - GW, CY0 + GW, CY1 - GW, CZ1 - 10, ROOF + 10))
black.append(roof)
glass += [box(CX1 - GW, CX1, CY0 + GW, CY1 - GW, CZ0, CZ1),           # front
          box(CX0, CX0 + GW, CY0 + GW, CY1 - GW, CZ0, CZ1),           # rear
          box(CX0 + GW, CX1 - GW, CY1 - GW, CY1, CZ0, CZ1),           # door
          box(CX0 + GW, CX1 - GW, CY0, CY0 + GW, CZ0, CZ1)]           # boom side
black.append(box(CX0 + GW, CX1 - GW, CY1 - GW - 1, CY1 + 1, 1500, 1560))   # door rail
cab_cup = box(CX0 + GW, CX1 - GW, CY0 + GW, CY1 - GW, 300, ROOF + 100)

# Boom: pivot towers and pin, base section, inner section, head
blue.append(side([(150, 1080), (800, 1080), (650, 2050), (250, 2050)], -330, 330))
grey.append(rod(70, (380, -360, 1850), (380, 360, 1850)))
def zb(x): return 1960 + (1700 - 1960)*(x - 150)/4600                   # underside of the base section
blue.append(side([(150, 1960), (150, 2590), (4750, 2250), (4750, 1700)], -260, 260))
blue.append(side([(4700, 2200), (4700, 1750), (6250, 1620), (6250, 2080)], -215, 215))
# head: its underside slopes into the carriage rather than overhanging it
blue.append(side([(6150, 2120), (6550, 2040), (6800, 1350), (6790, 850), (6650, 1000), (6150, 1600)], -260, 260))
black.append(box(4700, 4800, -270, 270, 1750, 2200))                  # wear pads
black.append(box(800, 4700, -330, -260, 2050, 2350))                  # hose tray
# Web under the boom so it prints: a 45 degree slope up to the front edge of
# its underside, on a wall behind the lift cylinder, out of sight from the cab side
def zi(x): return 1750 + (1620 - 1750)*(x - 4700)/1550                   # underside of the inner section
for (xa, xb, z, front) in ((700, 4750, zb, 260), (4750, 6200, zi, 215)):
    blue.append(hull([(x, y, z(x) - dz) for x in (xa, xb) for y, dz in ((front, 0), (-260, 0), (-260, front + 120), (-120, front + 120))]))
    blue.append(hull([(x, y, zz) for x in (xa, xb) for y in (-260, -120) for zz in (1000, z(x) - front - 100)]))
# Lift and tilt cylinders
blue.append(rod(110, (2900, 0, 1080), (3900, 0, 1720)))
grey.append(rod(65, (3900, 0, 1720), (4600, 0, 2050)))
grey.append(rod(60, (6200, 0, 1750), (6650, 0, 900)))
# Carriage (48 in) and two forks (2.25 x 4 in, 72 in tines), standing on the desk
black.append(box(6780, 6880, -610, 610, 0, 1250))
black.append(box(6780, 6840, -610, 610, 1250, 1650))
for s in (1, -1):
    y = s*420
    black.append(box(6880, 6937, y - 51, y + 51, 0, 1150))
    black.append(box(6880, 6880 + 1830, y - 51, y + 51, 0, SINK + 86))  # tines 2.5 mm thick, to last

# --- Pen holes down through the engine hood -----------------------------------
HOLE_Y = (BACK + -480)/2
HOLES_X = (1080, 1750, 2420)
def mouth(x, y, z, r):
    a = np.linspace(0, 2*np.pi, 48, endpoint=False)
    return hull([(x + (r + 50)*np.cos(t), y + (r + 50)*np.sin(t), z + 1) for t in a] +
                [(x + r*np.cos(t), y + r*np.sin(t), z - 50) for t in a])
r = PEN_D/2/S
holes = u([rod(r, (x, HOLE_Y, 120), (x, HOLE_Y, 3000), 64) for x in HOLES_X] +
          [mouth(x, HOLE_Y, 1650, r) for x in HOLES_X] + [cab_cup])

# --- Each colour owns its space; cut the back flat; scale ---------------------
grey, glass = d(u(grey), holes), d(u(glass), holes)
black = d(u(black), grey, glass, holes)
blue = d(u(blue), black, grey, glass, holes)
keep = box(-500, 9000, BACK, 2000, SINK, 4000)                          # flat back, tyre flats
def clean(m):
    """Drop the zero-volume slivers the booleans leave where faces touch."""
    return trimesh.util.concatenate([c for c in m.split(only_watertight=False) if abs(c.volume) > 1e3])
parts = []
for name, rgb, m in (("body", BLUE, blue), ("tyres, cab, forks", BLACK, black),
                     ("rims, pins, cylinders", GREY, grey), ("cab glass", GLASS, glass)):
    m = clean(x_(m, keep)); m.apply_translation((0, -BACK, -SINK)); m.apply_scale(S)
    parts.append((name, rgb, m))
report(parts)
write_3mf(parts, HERE + "/genie_pen_holder.3mf", "Genie GTH-1056 pen holder")

# --- Preview, standing on the desk ------------------------------------------
if __name__ == "__main__":
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    L = np.array([0.3, 0.8, 0.6]); L /= np.linalg.norm(L)
    tris = np.vstack([m.triangles for _, _, m in parts])
    cols = np.vstack([np.array(rgb)/255*(0.35 + 0.65*np.clip(m.face_normals @ L, 0.1, 1))[:, None] for _, rgb, m in parts])
    lo, hi = tris.reshape(-1, 3).min(0), tris.reshape(-1, 3).max(0)
    fig = plt.figure(figsize=(16, 6))
    for k, (elev, azim, title) in enumerate(((5, 90, "from the front"), (20, 60, ""), (60, -60, "from above, wall side"))):
        ax = fig.add_subplot(1, 3, k + 1, projection="3d")
        ax.add_collection3d(Poly3DCollection(tris, facecolors=cols, edgecolor="none"))
        ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1]); ax.set_zlim(lo[2], hi[2])
        ax.set_box_aspect(hi - lo); ax.view_init(elev=elev, azim=azim); ax.set_axis_off(); ax.set_title(title)
    plt.savefig(HERE + "/genie_preview.png", dpi=90, bbox_inches="tight"); plt.close(fig)
