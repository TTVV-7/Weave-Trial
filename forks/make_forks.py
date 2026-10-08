"""Telehandler fork key holder: a fork carriage and load backrest that screws
to the wall, with fork tines sticking out to hang keys on.

Modelled in print orientation: the back lies on the bed (z = 0), x is across,
y is up the wall, and the tines grow straight up in +z. No supports needed.
Two parts, two filaments: carriage + backrest in yellow, forks in black.
"""
import io, zipfile
import numpy as np, trimesh
from trimesh.creation import box, cylinder

W, PLATE_H, PLATE_T = 170, 60, 5          # carriage plate
BAR_T = 6                                 # carriage bars stand proud by this
BARS = ((6, 16), (44, 56))                # y-range of bottom and top bar
REST_H, REST_T, FRAME = 50, 4, 6          # load backrest above the plate
N_TINES, PITCH = 4, 40                    # tines and their spacing
SHANK_W, SHANK_T, SHANK_Y = 10, 6, (4, 58)
BLADE_L, BLADE_T, TAPER_L, TIP_T = 70, 6, 28, 2.5
TILT = 7                                  # degrees of fork tilt-back, keeps keys on
KEYHOLE_X = (-PITCH, PITCH)               # between the tines, 80 mm screw centres
SCREW_HEAD, SCREW_SHANK = 9.0, 4.5

def hull(pts): return trimesh.convex.convex_hull(np.array(pts, float))
def u(ms): return trimesh.boolean.union(ms, engine="manifold")
def d(a, *bs): return trimesh.boolean.difference([a, *bs], engine="manifold")

def rounded_slab(x0, x1, y0, y1, z0, z1, r):
    pts = []
    for cx in (x0 + r, x1 - r):
        for cy in (y0 + r, y1 - r):
            for a in np.linspace(0, 2*np.pi, 32, endpoint=False):
                pts += [(cx + r*np.cos(a), cy + r*np.sin(a), z) for z in (z0, z1)]
    return hull(pts)

# --- Carriage: plate, two bars, load backrest ------------------------------
plate = rounded_slab(-W/2, W/2, 0, PLATE_H, 0, PLATE_T, 4)
bars = [box(bounds=((-W/2 + 2, y0, PLATE_T - 0.01), (W/2 - 2, y1, PLATE_T + BAR_T))) for y0, y1 in BARS]
rest = rounded_slab(-W/2, W/2, PLATE_H - 6, PLATE_H + REST_H, 0, REST_T, 6)
# open the backrest into a frame with vertical slats
n_gaps = 7
inner_x0, inner_x1 = -W/2 + FRAME, W/2 - FRAME
slat = 5
gap_w = (inner_x1 - inner_x0 - slat*(n_gaps - 1)) / n_gaps
windows = [box(bounds=((inner_x0 + i*(gap_w + slat), PLATE_H + 2, -1),
                       (inner_x0 + i*(gap_w + slat) + gap_w, PLATE_H + REST_H - FRAME, 10)))
           for i in range(n_gaps)]
rest = d(rest, *windows)

def keyhole(x, y):
    """Screw head goes in the round hole, carriage drops onto the slot."""
    head = cylinder(radius=SCREW_HEAD/2, height=40, sections=48); head.apply_translation((x, y, 0))
    slot = box(bounds=((x - SCREW_SHANK/2, y, -1), (x + SCREW_SHANK/2, y + 9, 20)))
    slot_end = cylinder(radius=SCREW_SHANK/2, height=40, sections=32); slot_end.apply_translation((x, y + 9, 0))
    pocket = box(bounds=((x - SCREW_HEAD/2, y, -1), (x + SCREW_HEAD/2, y + 9, 3)))   # head slides behind
    pocket_end = cylinder(radius=SCREW_HEAD/2, height=8, sections=48); pocket_end.apply_translation((x, y + 9, -1))
    return [head, slot, slot_end, pocket, pocket_end]

holes = sum((keyhole(x, 22) for x in KEYHOLE_X), [])
carriage = d(u([plate] + bars + [rest]), *holes)

# --- Forks ------------------------------------------------------------------
def tine(x):
    z_face = PLATE_T + BAR_T                         # front of the bars
    shank = box(bounds=((x - SHANK_W/2, SHANK_Y[0], PLATE_T), (x + SHANK_W/2, SHANK_Y[1], z_face + SHANK_T)))
    # rounded top of the shank, like a fork's upper hook over the carriage bar
    cap = cylinder(radius=SHANK_W/2, height=SHANK_T + BAR_T, sections=32)
    cap.apply_translation((x, SHANK_Y[1], PLATE_T + (SHANK_T + BAR_T)/2))
    z0 = z_face + SHANK_T                            # blade starts at shank front
    y0 = SHANK_Y[0]
    hw, c = SHANK_W/2, 2.0                           # half width, tip corner chamfer
    straight_end = z0 + BLADE_L - TAPER_L
    tip = z0 + BLADE_L
    blade = hull([(sx*hw, y, z) for sx in (-1, 1) for y in (y0, y0 + BLADE_T) for z in (z0 - 3, straight_end)])
    taper = hull([(sx*hw, y, straight_end) for sx in (-1, 1) for y in (y0, y0 + BLADE_T)] +
                 [(sx*(hw - c), y, tip) for sx in (-1, 1) for y in (y0 + BLADE_T - TIP_T, y0 + BLADE_T)] +
                 [(sx*hw, y, tip - c) for sx in (-1, 1) for y in (y0 + BLADE_T - TIP_T, y0 + BLADE_T)])
    blade = u([blade, taper])
    blade.apply_translation((x, 0, 0))
    # tilt the blade up about the heel so keys slide back, not off
    blade.apply_transform(trimesh.transformations.rotation_matrix(np.radians(-TILT), (1, 0, 0), (x, y0, z0)))
    # inner heel fillet, where the load sits against the shank
    r = 6
    fil = box(bounds=((x - hw, y0 + BLADE_T - 0.5, z0 - 0.5), (x + hw, y0 + BLADE_T + r, z0 + r)))
    fc = cylinder(radius=r, height=SHANK_W + 2, sections=48)
    fc.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, (0, 1, 0)))
    fc.apply_translation((x, y0 + BLADE_T + r, z0 + r))
    fillet = d(fil, fc)
    return u([shank, cap, blade, fillet])

xs = (np.arange(N_TINES) - (N_TINES - 1)/2) * PITCH
forks = d(u([tine(x) for x in xs]), carriage)
# keep everything off the underside of the bed plane
bed = box(bounds=((-500, -500, 0), (500, 500, 500)))
forks = trimesh.boolean.intersection([forks, bed], engine="manifold")

# --- 3MF: one object per filament, grouped, with a material each ------------
parts = [("carriage", (0xF2, 0xB7, 0x05), carriage), ("forks", (0x22, 0x22, 0x22), forks)]
lo = np.min([m.bounds[0] for _, _, m in parts], axis=0)

def esc(s): return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")
objs, ids = [], []
for i, (name, rgb, m) in enumerate(parts):
    oid = i + 2
    v = m.vertices - lo
    objs.append(f'<object id="{oid}" type="model" name="{esc(name)}" pid="1" pindex="{i}"><mesh><vertices>'
                + "".join(f'<vertex x="{a:.4f}" y="{b:.4f}" z="{c:.4f}"/>' for a, b, c in v)
                + "</vertices><triangles>"
                + "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in m.faces)
                + "</triangles></mesh></object>")
    ids.append(oid)
gid = len(parts) + 2
objs.append(f'<object id="{gid}" type="model" name="telehandler fork key holder"><components>'
            + "".join(f'<component objectid="{i}"/>' for i in ids) + "</components></object>")
bases = "".join(f'<base name="{n}" displaycolor="#%02X%02X%02XFF"/>' % rgb for n, rgb, _ in parts)
model = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
         'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
         f'<resources><basematerials id="1">{bases}</basematerials>{"".join(objs)}</resources>'
         f'<build><item objectid="{gid}" transform="1 0 0 0 1 0 0 0 1 20 20 0"/></build></model>')
TYPES = ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
         '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
         '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
RELS = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
with zipfile.ZipFile("forks/telehandler_fork_key_holder.3mf", "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("[Content_Types].xml", TYPES); z.writestr("_rels/.rels", RELS); z.writestr("3D/3dmodel.model", model)

whole = u([carriage, forks])
for name, _, m in parts:
    print(f"{name}: watertight={m.is_watertight} volume={m.volume/1000:.1f} cm3 faces={len(m.faces)}")
print("overlap cm3:", round(trimesh.boolean.intersection([carriage, forks], engine="manifold").volume/1000, 3)
      if trimesh.boolean.intersection([carriage, forks], engine="manifold").volume > 0 else 0)
print("size mm (x, y, z):", np.round(whole.extents, 1))

# --- Preview, as it hangs on the wall --------------------------------------
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
wall = trimesh.transformations.rotation_matrix(np.pi/2, (1, 0, 0))      # y up -> z up, tines toward -y
fig = plt.figure(figsize=(10, 7)); ax = fig.add_subplot(projection="3d")
L = np.array([0.3, -0.8, 0.5]); L /= np.linalg.norm(L)
for _, rgb, m in parts:
    m = m.copy(); m.apply_transform(wall)
    shade = np.clip(m.face_normals @ L, 0.2, 1)[:, None]
    ax.add_collection3d(Poly3DCollection(m.triangles, facecolors=np.array(rgb)/255*(0.35 + 0.65*shade), edgecolor="none"))
ax.set_xlim(-85, 85); ax.set_ylim(-110, 20); ax.set_zlim(-10, 110); ax.set_box_aspect((170, 130, 120))
ax.view_init(elev=20, azim=-60); ax.set_axis_off()
plt.savefig("forks/preview.png", dpi=110, bbox_inches="tight")
