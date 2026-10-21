"""Generate printable STLs for Jubilee's X-logo accessories.

Run: python3 make_props.py   (needs trimesh, shapely, manifold3d, mapbox_earcut)
All dimensions are in millimetres; tweak the constants below and re-run.
"""
import math
import trimesh
from shapely.geometry import Point, Polygon, box
from shapely import affinity
from shapely.ops import unary_union

OUT = __import__("pathlib").Path(__file__).parent / "stl"
OUT.mkdir(exist_ok=True)

BELT_WIDTH = 38.0      # width of the belt strap the buckle must accept (1.5" = 38 mm)
RES = 128              # circle smoothness


def circle(r, x=0, y=0):
    return Point(x, y).buffer(r, resolution=RES)


def ellipse(rx, ry):
    return affinity.scale(circle(1), rx, ry)


def x_mark(rx, ry, w_center, w_tip):
    """Tapered X spanning an ellipse of radii (rx, ry); arms flare toward the rim."""
    L = 1.2 * max(rx, ry)  # extend past rim, clipped by caller
    arm = Polygon([(-L, -w_tip / 2), (0, -w_center / 2), (L, -w_tip / 2),
                   (L, w_tip / 2), (0, w_center / 2), (-L, w_tip / 2)])
    ang = math.degrees(math.atan2(ry, rx))
    return unary_union([affinity.rotate(arm, a, origin=(0, 0)) for a in (ang, -ang)])


def extrude(shape, h, z=0.0):
    m = trimesh.creation.extrude_polygon(shape, h) if shape.geom_type == "Polygon" else \
        trimesh.util.concatenate([trimesh.creation.extrude_polygon(g, h) for g in shape.geoms])
    m.apply_translation((0, 0, z))
    return m


def union(*meshes):
    return trimesh.boolean.union(list(meshes), engine="manifold")


def diff(a, *bs):
    return trimesh.boolean.difference([a, *bs], engine="manifold")


def x_logo(rx, ry, ring, w_c, w_t):
    """Ring + X as a single 2D shape (open background)."""
    outer, inner = ellipse(rx, ry), ellipse(rx - ring, ry - ring)
    x = x_mark(rx - ring * 0.5, ry - ring * 0.5, w_c, w_t).intersection(ellipse(rx - ring * 0.5, ry - ring * 0.5))
    return unary_union([outer.difference(inner), x])


def save(mesh, name):
    assert mesh.is_watertight, name
    mesh.export(OUT / f"{name}.stl")
    ext = mesh.extents
    print(f"{name:22s} {ext[0]:6.1f} x {ext[1]:6.1f} x {ext[2]:4.1f} mm  watertight={mesh.is_watertight}")
    return mesh


# 1. Earrings: open oval ring with X and a hanging loop on top (print 2).
def earring():
    rx, ry, ring, t = 10.0, 14.0, 2.2, 2.4
    logo = x_logo(rx, ry, ring, 2.6, 3.4)
    loop = circle(2.6, 0, ry + 1.6).difference(circle(1.1, 0, ry + 1.6))
    return extrude(unary_union([logo, loop]), t)


# 2. Necklace pendant: open ring + X (the shirt shows through), bail on top for a cord/jump ring.
def pendant():
    r, ring, t = 12.0, 2.2, 3.0
    logo = x_logo(r, r, ring, 3.0, 4.0)
    bail = circle(3.2, 0, r + 2.2).difference(circle(1.5, 0, r + 2.2))
    return extrude(unary_union([logo, bail]), t)


# 3. Chest pin: open ring + X (the shirt shows through); glue a pin back along one X arm.
def pin_badge():
    r, ring, t = 16.0, 2.6, 3.5
    return extrude(x_logo(r, r, ring, 5.0, 6.0), t)


# 4. Belt buckle: X medallion flanked by two bar frames with slots for the belt.
def belt_buckle():
    r, ring, base, relief = 26.0, 4.0, 3.5, 2.5
    slot_h, slot_w = BELT_WIDTH + 3.0, 5.0
    frame_w, frame_h = 16.0, slot_h + 9.0
    cx = r + frame_w / 2 - 1.0
    frames, slots = [], []
    for s in (-1, 1):
        frames.append(box(s * cx - frame_w / 2, -frame_h / 2, s * cx + frame_w / 2, frame_h / 2)
                      .buffer(1.5, resolution=16).buffer(-1.5, resolution=16))
        slots.append(box(s * cx - slot_w / 2, -slot_h / 2, s * cx + slot_w / 2, slot_h / 2))
    plate = unary_union([circle(r)] + frames).difference(unary_union(slots))
    body = extrude(plate, base)
    logo = extrude(x_logo(r, r, ring, 7.0, 9.5), relief, base)
    # raised border on each side frame so it reads like the drawing
    frame_rims = [f.difference(f.buffer(-2.2)).difference(circle(r - 0.5)) for f in frames]
    rims = extrude(unary_union(frame_rims), relief, base)
    return union(body, logo, rims)


if __name__ == "__main__":
    e = save(earring(), "earring_x_oval")
    e2 = e.copy(); e2.apply_translation((25, 0, 0))
    save(union(e, e2), "earrings_pair")
    save(pendant(), "necklace_pendant_x")
    save(pin_badge(), "chest_pin_x")
    save(belt_buckle(), "belt_buckle_x")
