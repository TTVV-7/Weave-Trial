"""Telehandler pen holder for a desk: the engine pod is drilled for pens, the
cab is an open-top cup for scissors and highlighters, and the boom is lowered
so the forks lie flat on the desk (somewhere to park a sticky-note pad).

Modelled standing as it sits on the desk, z up, x toward the forks, y to the
cab side. Nothing hangs in the air: the boom sits in a cradle between cab and
engine pod, and in front of the cab it bridges onto the lift ram and then the
carriage. Three filaments: body yellow, tyres/forks/ram black, glass grey.
"""
import os
import numpy as np, trimesh
from trimesh.creation import box, cylinder
from common import hull, u, d, x_, rounded_slab, write_3mf, report

HERE = os.path.dirname(os.path.abspath(__file__))

# --- Dimensions (mm) ---------------------------------------------------------
CH_X, CH_Y, CH_Z = (-82, 66), 38, 40      # chassis: x range, half width, top
WHEEL_R, WHEEL_W, AXLES = 25, 17, (-50, 46)
WHEEL_Z = WHEEL_R - 0.6                    # axle height: tyres sink a little, flat on the bed
POD_X, POD_Y, POD_TOP = (-80, 34), (-38, -12), 84     # engine pod, right side
CAB_X, CAB_Y, CAB_TOP = (-6, 52), (6, 38), 112       # cab, left side
CAB_WALL, CAB_FLOOR = 3.2, 24
BOOM_Y, BOOM_Z, BOOM_X = (-11, 5), (74, 92), (-92, 108)
CARR_X, CARR_TOP = (108, 114), 62          # fork carriage plate
TINE_L, TINE_W, TINE_T, TINE_Y = 34, 11, 5, (-22, 22)
PEN_D, PEN_FLOOR = 14, 18                  # pen hole diameter, bottom of holes
PEN_X = (-66, -45, -24, -3, 18)            # one row down the engine pod
GLASS = 1.0                                # window inlay depth

def zcyl(r, x, y, z0, z1, n=64):
    c = cylinder(radius=r, height=z1 - z0, sections=n); c.apply_translation((x, y, (z0 + z1)/2)); return c

def ycyl(r, x, y0, y1, z, n=64):
    c = cylinder(radius=r, height=y1 - y0, sections=n)
    c.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, (1, 0, 0)))
    c.apply_translation((x, (y0 + y1)/2, z)); return c

def xslab(x0, x1, y0, y1, z0, z1, r):
    """A slab rounded on its corners seen from the side (x, z), straight in y."""
    m = rounded_slab(x0, x1, z0, z1, y0, y1, r)       # built in x, y then swung
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, (1, 0, 0)))
    m.apply_translation((0, y0 + y1, 0))
    return m

# --- Body --------------------------------------------------------------------
# Chassis, down to the desk so it stands solid; the ends are chamfered so it
# still reads as a frame between the wheels.
chassis = hull([(x, sy*CH_Y, z) for sy in (-1, 1) for x, z in
                ((CH_X[0] + 8, 0), (CH_X[1] - 8, 0), (CH_X[0], 14), (CH_X[1], 14),
                 (CH_X[0], CH_Z), (CH_X[1], CH_Z))])
# Counterweight at the back, its top rounded like the cast ones, flat on the desk
counterweight = u([xslab(-97, -78, -CH_Y - 6, CH_Y + 6, 0, 64, 10),
                   box(bounds=((-97, -CH_Y - 6, 0), (-78, CH_Y + 6, 20)))])
# Engine pod, its top rounded over toward the outside
pod = hull([(x, y, z) for x in POD_X for y, z in
            ((POD_Y[0], CH_Z), (POD_Y[1], CH_Z), (POD_Y[1], POD_TOP), (POD_Y[0] + 7, POD_TOP),
             (POD_Y[0], POD_TOP - 7))])
# Cab, with a chamfered front pillar and a sloped roof edge at the front
cab = hull([(x, y, z) for y in CAB_Y for x, z in
            ((CAB_X[0], CH_Z), (CAB_X[1], CH_Z), (CAB_X[1], 70), (CAB_X[1] - 6, CAB_TOP),
             (CAB_X[0], CAB_TOP))])
# Boom cradle between cab and pod, so the boom rests on something
cradle = box(bounds=((BOOM_X[0] + 4, BOOM_Y[0], CH_Z - 1), (CAB_X[1], BOOM_Y[1], BOOM_Z[0] + 1)))
# Boom: square section, a pivot boss at the back, a head dropping to the carriage
boom = box(bounds=((BOOM_X[0], BOOM_Y[0], BOOM_Z[0]), (BOOM_X[1] - 10, BOOM_Y[1], BOOM_Z[1])))
pivot = ycyl(13, BOOM_X[0] + 6, BOOM_Y[0] - 2, BOOM_Y[1] + 2, (BOOM_Z[0] + BOOM_Z[1])/2)
pivot_tower = hull([(x, y, z) for y in (BOOM_Y[0] - 2, BOOM_Y[1] + 2) for x, z in
                    ((-90, 64), (-72, 64), (-84, 83), (-98, 83))])
head = hull([(x, y, z) for y in BOOM_Y for x, z in
             ((BOOM_X[1] - 14, BOOM_Z[0]), (BOOM_X[1] - 14, BOOM_Z[1]), (CARR_X[0], BOOM_Z[1] - 4),
              (CARR_X[0], CARR_TOP - 20))])     # underside slopes ~70 degrees, prints clean
# Carriage plate and load backrest the forks hang from
carriage = u([box(bounds=((CARR_X[0], -CH_Y + 2, 0), (CARR_X[1], CH_Y - 2, CARR_TOP))),
              box(bounds=((CARR_X[0], -CH_Y + 2, 44), (CARR_X[1] + 4, CH_Y - 2, 54)))])   # top fork bar

# Hubs on the outside of each wheel, yellow like the body
hubs = [ycyl(12, x, *sorted((sy*(CH_Y + WHEEL_W - 0.5), sy*(CH_Y + WHEEL_W + 1.5))), WHEEL_Z)
        for x in AXLES for sy in (-1, 1)]

body = u([chassis, counterweight, pod, cab, cradle, boom, pivot, pivot_tower, head, carriage] + hubs)

# --- What comes out of the body ---------------------------------------------
pens = [zcyl(PEN_D/2, x, (POD_Y[0] + POD_Y[1])/2, PEN_FLOOR, 200) for x in PEN_X]
# chamfer the hole mouths so pens drop in easily
pens += [hull([(x + (PEN_D/2 + 1.5)*np.cos(a), (POD_Y[0] + POD_Y[1])/2 + (PEN_D/2 + 1.5)*np.sin(a), POD_TOP + 0.01)
               for a in np.linspace(0, 2*np.pi, 48, endpoint=False)] +
              [(x + PEN_D/2*np.cos(a), (POD_Y[0] + POD_Y[1])/2 + PEN_D/2*np.sin(a), POD_TOP - 1.5)
               for a in np.linspace(0, 2*np.pi, 48, endpoint=False)]) for x in PEN_X]
cab_cup = box(bounds=((CAB_X[0] + CAB_WALL, CAB_Y[0] + CAB_WALL, CAB_FLOOR),
                      (CAB_X[1] - 6 - CAB_WALL, CAB_Y[1] - CAB_WALL, 200)))
# Engine grille slats on the outside of the pod
grille = [box(bounds=((x, POD_Y[0] - 1, 50), (x + 3, POD_Y[0] + 1, 74))) for x in np.arange(-70, -20, 7)]
body = d(body, *pens, cab_cup, *grille)

# Windows: shallow recesses in the cab, filled flush by a grey glass part
def recess(pts):
    """Prism through the face given by 4 points on it, GLASS deep inward."""
    pts = np.array(pts, float)
    n = np.cross(pts[1] - pts[0], pts[2] - pts[0]); n /= np.linalg.norm(n)
    c = np.array([(CAB_X[0] + CAB_X[1])/2, (CAB_Y[0] + CAB_Y[1])/2, 80])
    if np.dot(c - pts[0], n) < 0: n = -n                 # n points into the cab
    return hull(np.vstack([pts + n*GLASS, pts - n*2]))

side = CAB_Y[1]
def slope_x(z): return CAB_X[1] - 6*(z - 70)/(CAB_TOP - 70)   # sloped upper windscreen
windows = [
    recess([(CAB_X[0] + 6, side, 50), (CAB_X[1] - 6, side, 50), (CAB_X[1] - 6, side, 70),
            (slope_x(106) - 6, side, 106), (CAB_X[0] + 6, side, 106)]),
    recess([(CAB_X[1], CAB_Y[0] + 5, 50), (CAB_X[1], CAB_Y[1] - 5, 50), (CAB_X[1], CAB_Y[1] - 5, 68), (CAB_X[1], CAB_Y[0] + 5, 68)]),
    recess([(slope_x(z), y, z) for z, y in ((74, CAB_Y[0] + 5), (74, CAB_Y[1] - 5),
                                            (106, CAB_Y[1] - 5), (106, CAB_Y[0] + 5))]),
    recess([(CAB_X[0], CAB_Y[0] + 5, 50), (CAB_X[0], CAB_Y[1] - 5, 50), (CAB_X[0], CAB_Y[1] - 5, 106), (CAB_X[0], CAB_Y[0] + 5, 106)]),
]
win = u(windows)
glass = x_(win, u([cab]))
glass = d(glass, cab_cup)
body = d(body, win)

# --- Black parts: tyres, forks, lift ram ------------------------------------
def tyre(x, sy):
    y0, y1 = sorted((sy*CH_Y, sy*(CH_Y + WHEEL_W)))
    t = ycyl(WHEEL_R, x, y0, y1, WHEEL_Z)
    treads = [box(bounds=((-1.5, y0 - 1, WHEEL_R - 1.2), (1.5, y1 + 1, WHEEL_R + 2))) for _ in range(20)]
    for i, tr in enumerate(treads):
        tr.apply_transform(trimesh.transformations.rotation_matrix(2*np.pi*i/20, (0, 1, 0)))
        tr.apply_translation((x, 0, WHEEL_Z))
    return d(t, *treads)
tyres = [tyre(x, sy) for x in AXLES for sy in (-1, 1)]

def tine(y):
    shank = box(bounds=((CARR_X[1], y - TINE_W/2, 0), (CARR_X[1] + 6, y + TINE_W/2, 58)))
    hook = box(bounds=((CARR_X[1] - 0.01, y - TINE_W/2, 54), (CARR_X[1] + 6, y + TINE_W/2, 58)))
    blade = hull([(x, sy*TINE_W/2 + y, z) for sy in (-1, 1) for x, z in
                  ((CARR_X[1], 0), (CARR_X[1] + TINE_L, 0), (CARR_X[1] + TINE_L, 1.6),
                   (CARR_X[1] + TINE_L - 14, TINE_T), (CARR_X[1], TINE_T))])
    return u([shank, hook, blade])
forks = d(u(tine(y) for y in TINE_Y), body)

# Lift ram from the chassis front up under the boom; it also props the bridge
a, b = np.array([60, -3, 34]), np.array([88, -3, BOOM_Z[0] + 4])
ram = cylinder(radius=6.5, segment=(a, b), sections=48)
ram = d(ram, body)

black = d(u(tyres + [forks, ram]), body)
parts = [("body", (0xF2, 0xB7, 0x05), body), ("tyres, forks, ram", (0x22, 0x22, 0x22), black),
         ("glass", (0x55, 0x66, 0x77), glass)]
# flatten the tyre bottoms so they sit on the bed with the chassis
floor = box(bounds=((-500, -500, 0), (500, 500, 500)))
parts = [(n, c, x_(m, floor) if n.startswith("tyres") else m) for n, c, m in parts]

write_3mf(parts, HERE + "/telehandler_pen_holder.3mf", "telehandler pen holder")
report(parts)

# --- Preview, standing on the desk, from both sides --------------------------
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
L = np.array([0.4, 0.5, 0.8]); L /= np.linalg.norm(L)
tris = np.vstack([m.triangles for _, _, m in parts])     # one collection, so faces depth-sort together
cols = np.vstack([np.array(rgb)/255*(0.35 + 0.65*np.clip(m.face_normals @ L, 0.1, 1))[:, None]
                  for _, rgb, m in parts])
lo, hi = tris.reshape(-1, 3).min(0), tris.reshape(-1, 3).max(0)
fig = plt.figure(figsize=(14, 6))
for k, azim in enumerate((60, -50)):
    ax = fig.add_subplot(1, 2, k + 1, projection="3d")
    ax.add_collection3d(Poly3DCollection(tris, facecolors=cols, edgecolor="none"))
    ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1]); ax.set_zlim(lo[2], hi[2])
    ax.set_box_aspect(hi - lo); ax.view_init(elev=25, azim=azim); ax.set_axis_off()
plt.savefig(HERE + "/preview.png", dpi=100, bbox_inches="tight"); plt.close(fig)
