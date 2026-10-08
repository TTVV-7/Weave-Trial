"""What the key holders share: solid helpers, a wall keyhole, the 3MF writer
and a preview render. Every model is built in print orientation: back on the
bed (z = 0), x across, y up the wall, and things that stick out grow in +z.
"""
import zipfile
import numpy as np, trimesh
from trimesh.creation import box, cylinder

SCREW_HEAD, SCREW_SHANK = 9.0, 4.5

def hull(pts): return trimesh.convex.convex_hull(np.array(pts, float))
def u(ms): return trimesh.boolean.union(list(ms), engine="manifold")
def d(a, *bs): return trimesh.boolean.difference([a, *bs], engine="manifold")
def x_(a, b): return trimesh.boolean.intersection([a, b], engine="manifold")

def prism(pts_xy, z0, z1):
    """A convex outline in x, y, extruded from z0 to z1."""
    return hull([(x, y, z) for x, y in pts_xy for z in (z0, z1)])

def side_prism(pts_zy, x0, x1):
    """A convex side profile in z, y, extruded across from x0 to x1."""
    return hull([(x, y, z) for z, y in pts_zy for x in (x0, x1)])

def rounded_slab(x0, x1, y0, y1, z0, z1, r):
    pts = [(cx + r*np.cos(a), cy + r*np.sin(a))
           for cx in (x0 + r, x1 - r) for cy in (y0 + r, y1 - r)
           for a in np.linspace(0, 2*np.pi, 32, endpoint=False)]
    return prism(pts, z0, z1)

def keyhole(x, y, pocket=3):
    """Screw head goes in the round hole, the holder drops onto the slot.
    The pocket on the back lets the head sit behind the wall of the part."""
    def zcyl(r, cx, cy, z0, z1):
        c = cylinder(radius=r, height=z1 - z0, sections=48); c.apply_translation((cx, cy, (z0 + z1)/2)); return c
    return [zcyl(SCREW_HEAD/2, x, y, -1, 40),
            box(bounds=((x - SCREW_SHANK/2, y, -1), (x + SCREW_SHANK/2, y + 9, 40))),
            zcyl(SCREW_SHANK/2, x, y + 9, -1, 40),
            box(bounds=((x - SCREW_HEAD/2, y, -1), (x + SCREW_HEAD/2, y + 9, pocket))),
            zcyl(SCREW_HEAD/2, x, y + 9, -1, pocket)]

_TYPES = ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
_RELS = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
         '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')

def _esc(s): return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")

def write_3mf(parts, path, name):
    """One object per filament, grouped as one, each pointing at its colour."""
    lo = np.min([m.bounds[0] for _, _, m in parts], axis=0)
    objs, ids = [], []
    for i, (pname, rgb, m) in enumerate(parts):
        oid = i + 2
        objs.append(f'<object id="{oid}" type="model" name="{_esc(pname)}" pid="1" pindex="{i}"><mesh><vertices>'
                    + "".join(f'<vertex x="{a:.4f}" y="{b:.4f}" z="{c:.4f}"/>' for a, b, c in m.vertices - lo)
                    + "</vertices><triangles>"
                    + "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in m.faces)
                    + "</triangles></mesh></object>")
        ids.append(oid)
    gid = len(parts) + 2
    objs.append(f'<object id="{gid}" type="model" name="{_esc(name)}"><components>'
                + "".join(f'<component objectid="{i}"/>' for i in ids) + "</components></object>")
    bases = "".join(f'<base name="{_esc(n)}" displaycolor="#%02X%02X%02XFF"/>' % rgb for n, rgb, _ in parts)
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             f'<resources><basematerials id="1">{bases}</basematerials>{"".join(objs)}</resources>'
             f'<build><item objectid="{gid}" transform="1 0 0 0 1 0 0 0 1 20 20 0"/></build></model>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _TYPES); z.writestr("_rels/.rels", _RELS); z.writestr("3D/3dmodel.model", model)

def report(parts):
    for name, _, m in parts:
        print(f"{name}: watertight={m.is_watertight} volume={m.volume/1000:.1f} cm3 faces={len(m.faces)}")
    if len(parts) > 1:
        ov = x_(parts[0][2], u(m for _, _, m in parts[1:]))
        print("overlap mm3:", round(ov.volume, 2) if len(ov.faces) else 0)
    print("size mm (x, y, z):", np.round(u(m for _, _, m in parts).extents, 1))

def preview(parts, path, azim=-60, elev=20):
    """Render it as it hangs on the wall: y up, sticking out toward the viewer."""
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    wall = trimesh.transformations.rotation_matrix(np.pi/2, (1, 0, 0))
    fig = plt.figure(figsize=(10, 7)); ax = fig.add_subplot(projection="3d")
    L = np.array([0.3, -0.8, 0.5]); L /= np.linalg.norm(L)
    ms = []
    for _, rgb, m in parts:
        m = m.copy(); m.apply_transform(wall); ms.append(m)
        shade = np.clip(m.face_normals @ L, 0.2, 1)[:, None]
        ax.add_collection3d(Poly3DCollection(m.triangles, facecolors=np.array(rgb)/255*(0.35 + 0.65*shade), edgecolor="none"))
    lo = np.min([m.bounds[0] for m in ms], axis=0); hi = np.max([m.bounds[1] for m in ms], axis=0)
    ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1]); ax.set_zlim(lo[2], hi[2])
    ax.set_box_aspect(hi - lo); ax.view_init(elev=elev, azim=azim); ax.set_axis_off()
    plt.savefig(path, dpi=110, bbox_inches="tight"); plt.close(fig)
