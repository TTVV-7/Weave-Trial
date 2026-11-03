"""A small CAD kit for the construction-site assets.

Primitives (all in millimetres, X forward / Y left / Z up, ground at Z = 0),
a `Model` that collects coloured parts, and three exporters:

    export_step   every part a separate coloured solid, millimetres (CAD)
    export_glb    one coloured mesh per part, metres, Y up (glTF standard)
    export_print  one watertight body at a print scale, flat on Z = 0 (STL)

A model is built twice: once as drawn, for STEP and GLB, and once in print
mode, where `Model.t()` and `Model.r()` thicken anything that would come out
thinner than a printable wall at the print scale.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import cadquery as cq
import numpy as np

IN = 25.4
FT = 304.8
V = cq.Vector
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


# --------------------------------------------------------------------------- finishes

@dataclass(frozen=True)
class Finish:
    rgb: tuple[float, float, float]
    metal: float = 0.0
    rough: float = 0.6
    alpha: float = 1.0
    glow: tuple[float, float, float] | None = None   # emissive colour, for lamps


def rgb(h: str) -> tuple[float, float, float]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


# --------------------------------------------------------------------------- primitives

def box(x0, x1, y0, y1, z0, z1) -> cq.Solid:
    """Box between two corners."""
    x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def boxc(lx, ly, lz, cx=0.0, cy=0.0, cz=0.0) -> cq.Solid:
    """Box of size (lx, ly, lz) centred on (cx, cy, cz)."""
    return box(cx - lx / 2, cx + lx / 2, cy - ly / 2, cy + ly / 2, cz - lz / 2, cz + lz / 2)


def cyl(r, a, b) -> cq.Solid:
    """Cylinder of radius r from point a to point b."""
    a, b = V(*a), V(*b)
    d = b - a
    return cq.Solid.makeCylinder(r, d.Length, a, d.normalized())


def cone(r1, r2, a, b) -> cq.Solid:
    a, b = V(*a), V(*b)
    d = b - a
    return cq.Solid.makeCone(r1, r2, d.Length, a, d.normalized())


def sphere(r, c) -> cq.Solid:
    return cq.Solid.makeSphere(r, V(*c), angleDegrees1=-90, angleDegrees2=90)


def torus(R, r, c, axis=(0, 0, 1)) -> cq.Solid:
    return cq.Solid.makeTorus(R, r, V(*c), V(*axis))


def _signed_area(pts):
    return 0.5 * sum(u0 * v1 - u1 * v0 for (u0, v0), (u1, v1) in zip(pts, pts[1:] + pts[:1]))


def prism(pts, axis, a0, a1) -> cq.Solid:
    """2-D polygon extruded along an axis from a0 to a1.

    axis 'x': pts are (y, z); 'y': pts are (x, z); 'z': pts are (x, y).
    """
    a0, a1 = sorted((a0, a1))
    pts = [tuple(map(float, p)) for p in pts]
    # make the face normal point along +axis, so the solid comes out right way in
    want_ccw = axis != "y"           # (x, z) is a left-handed pair about +y
    if (_signed_area(pts) > 0) != want_ccw:
        pts = pts[::-1]
    f = {"x": lambda u, v, w: V(w, u, v),
         "y": lambda u, v, w: V(u, w, v),
         "z": lambda u, v, w: V(u, v, w)}[axis]
    wire = cq.Wire.makePolygon([f(u, v, a0) for u, v in pts], close=True)
    return cq.Solid.extrudeLinear(cq.Face.makeFromWires(wire), f(0, 0, a1 - a0))


def frustum(bottom, top) -> cq.Solid:
    """Ruled loft between two horizontal rectangles, each (x0, x1, y0, y1, z)."""
    def wire(x0, x1, y0, y1, z):
        return cq.Wire.makePolygon([V(x0, y0, z), V(x1, y0, z), V(x1, y1, z), V(x0, y1, z)], close=True)
    return cq.Solid.makeLoft([wire(*bottom), wire(*top)], ruled=True)


def place(s: cq.Shape, x, y, z, origin) -> cq.Shape:
    """Map a shape's local axes onto x, y, z (unit vectors) at origin."""
    plane = cq.Plane(origin=V(*map(float, origin)), xDir=V(*map(float, x)), normal=V(*map(float, z)))
    return s.moved(cq.Location(plane))


def bar(a, b, w, h, up=(0, 0, 1)) -> cq.Shape:
    """Rectangular bar from a to b: w wide across, h deep towards `up`."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    L = float(np.linalg.norm(d))
    x = d / L
    y = np.cross(np.asarray(up, float), x)
    if np.linalg.norm(y) < 1e-9:
        y = np.cross([1.0, 0, 0] if abs(x[0]) < 0.9 else [0, 1.0, 0], x)
    y /= np.linalg.norm(y)
    z = np.cross(x, y)
    return place(cq.Solid.makeBox(L, w, h, V(0, -w / 2, -h / 2)), x, y, z, a)


def pipe(points, r, joints=True) -> list[cq.Solid]:
    """A bent pipe through points: cylinders, with balls at the bends."""
    out = [cyl(r, a, b) for a, b in zip(points, points[1:])]
    if joints:
        out += [sphere(r, p) for p in points[1:-1]]
    return out


def mv(s: cq.Shape, x=0.0, y=0.0, z=0.0) -> cq.Shape:
    return s.translate(V(x, y, z))


def rot(s: cq.Shape, deg, axis=(0, 0, 1), about=(0, 0, 0)) -> cq.Shape:
    return s.rotate(V(*about), V(*about) + V(*axis), deg)


def mirror_y(s: cq.Shape) -> cq.Shape:
    return s.mirror("XZ")


def mirror_x(s: cq.Shape) -> cq.Shape:
    return s.mirror("YZ")


def cut(a: cq.Shape, *bs: cq.Shape) -> cq.Shape:
    return a.cut(*bs)


def clip_poly(poly, x0, x1, y0, y1):
    """Clip a 2-D polygon to an axis-aligned rectangle (Sutherland-Hodgman)."""
    def clip(pts, inside, cross):
        out = []
        for i, p in enumerate(pts):
            q = pts[i - 1]
            if inside(p):
                if not inside(q):
                    out.append(cross(q, p))
                out.append(p)
            elif inside(q):
                out.append(cross(q, p))
        return out

    def at_x(xc):
        return lambda q, p: (xc, q[1] + (p[1] - q[1]) * (xc - q[0]) / (p[0] - q[0]))

    def at_y(yc):
        return lambda q, p: (q[0] + (p[0] - q[0]) * (yc - q[1]) / (p[1] - q[1]), yc)

    pts = list(poly)
    for inside, cross in ((lambda p: p[0] >= x0, at_x(x0)), (lambda p: p[0] <= x1, at_x(x1)),
                          (lambda p: p[1] >= y0, at_y(y0)), (lambda p: p[1] <= y1, at_y(y1))):
        if not pts:
            break
        pts = clip(pts, inside, cross)
    return pts


def arc_pts(cx, cy, r, a0, a1, n):
    """n+1 points on an arc, angles in degrees."""
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def stadium(x0, x1, zc, r, n=16):
    """Plan of a track: two half circles of radius r at x0 and x1, centre height zc."""
    return arc_pts(x1, zc, r, -90, 90, n) + arc_pts(x0, zc, r, 90, 270, n)


def band(path, half, ends=True):
    """Polygon of a band of half-depth `half` (scalar or per-point) round a 2-D polyline."""
    p = np.asarray(path, float)
    halves = np.broadcast_to(np.asarray(half, float), (len(p),))
    tang = []
    for i in range(len(p)):
        a = p[max(i - 1, 0)]
        b = p[min(i + 1, len(p) - 1)]
        d = b - a
        tang.append(d / np.linalg.norm(d))
    left, right = [], []
    for i, (q, t) in enumerate(zip(p, tang)):
        n = np.array([-t[1], t[0]])
        if 0 < i < len(p) - 1:   # mitre at the bend, so the band keeps its depth
            d0 = (p[i] - p[i - 1]) / np.linalg.norm(p[i] - p[i - 1])
            n0 = np.array([-d0[1], d0[0]])
            n = n / max(float(np.dot(n, n0)), 0.3)
        left.append(tuple(q + n * halves[i]))
        right.append(tuple(q - n * halves[i]))
    return left + right[::-1]


def text(txt, size, depth, origin, xdir, normal, font=FONT_BOLD):
    """Raised text centred on origin, reading along xdir, standing out along normal."""
    try:
        wp = cq.Workplane(cq.Plane(origin=V(*origin), xDir=V(*xdir), normal=V(*normal)))
        return wp.text(txt, size, depth, fontPath=font, halign="center", valign="center",
                       combine=False).val()
    except Exception:   # no usable font: leave the lettering off rather than fail
        return None


def rounded_box(x0, x1, y0, y1, z0, z1, r):
    s = cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0).edges().fillet(r)
    return mv(s.val(), (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)


# --------------------------------------------------------------------------- machine parts

def ram(a, b, rb, rr, frac=0.55, eye=None):
    """A hydraulic cylinder from a to b: barrel for `frac` of the way, then the rod."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    j = a + (b - a) * frac
    e = eye or rb * 0.9
    return [cyl(rb, a, j), cyl(rr, j - (b - a) * 0.02, b)], [sphere(e, a), sphere(rr * 1.4, b)]


def pin(c, r, half, axis="y"):
    x, y, z = c
    d = {"x": (half, 0, 0), "y": (0, half, 0), "z": (0, 0, half)}[axis]
    return cyl(r, (x - d[0], y - d[1], z - d[2]), (x + d[0], y + d[1], z + d[2]))


def wheel_lugs(xc, zc, R, depth, y0, y1, n, width, split=0.15):
    """Bar tread round a tyre: n lugs, alternating halves, one straight down."""
    lugs = []
    ym, half = (y0 + y1) / 2, (y1 - y0) / 2
    for i in range(n):
        a = 270 + 360 * i / n
        lo, hi = (y0, ym + split * half) if i % 2 else (ym - split * half, y1)
        lug = box(xc - width / 2, xc + width / 2, lo, hi, zc + R - depth - 2, zc + R)
        lugs.append(rot(lug, 90 - a, (0, 1, 0), (xc, 0, zc)))
    return lugs


def corrugated_plan(x0, x1, y_out, depth, y_back, pitch=278.0, flat_out=72.0, flat_in=68.0):
    """Plan of a corrugated wall: x along the wall, outer face at y_out, solid back to y_back."""
    run = (pitch - flat_out - flat_in) / 2
    inward = -1 if y_back < y_out else 1
    y_in = y_out + inward * depth
    pts, x = [], x0 - pitch
    while x < x1 + pitch:
        pts += [(x, y_out), (x + flat_out, y_out), (x + flat_out + run, y_in), (x + pitch - run, y_in)]
        x += pitch
    pts += [(x, y_out), (x, y_back), (x0 - pitch, y_back)]
    lo, hi = sorted((y_out, y_back))
    return clip_poly(pts, x0, x1, lo, hi)


# --------------------------------------------------------------------------- model

class Model:
    """Coloured parts, as drawn or thickened for printing."""

    def __init__(self, print_mode=False, scale=50.0, min_wall=0.8):
        self.print_mode = print_mode
        self.scale = scale
        self.min = min_wall * scale if print_mode else 0.0     # mm, full size
        self.parts: list[tuple[str, Finish, list[cq.Shape]]] = []

    def t(self, mm: float) -> float:
        """A thickness: at least a printable wall in print mode."""
        return max(mm, self.min)

    def r(self, mm: float) -> float:
        """A radius of a rod: at least half a printable wall in print mode."""
        return max(mm, self.min / 2)

    def add(self, name: str, finish: Finish, *shapes):
        flat = []

        def walk(items):
            for s in items:
                if isinstance(s, (list, tuple)):
                    walk(s)
                elif s is not None:
                    flat.append(s)
        walk(shapes)
        if not flat:
            return
        taken = {n for n, _, _ in self.parts}
        base, k = name, 2
        while name in taken:
            name, k = f"{base}_{k}", k + 1
        self.parts.append((name, finish, flat))

    def bounds(self):
        bb = cq.Compound.makeCompound([s for _, _, ss in self.parts for s in ss]).BoundingBox()
        return (bb.xmin, bb.xmax), (bb.ymin, bb.ymax), (bb.zmin, bb.zmax)


# --------------------------------------------------------------------------- exporters

def export_step(model: Model, path: Path, title: str):
    assy = cq.Assembly(name=title.replace(" ", "_"))
    for name, fin, shapes in model.parts:
        assy.add(cq.Compound.makeCompound(shapes), name=name,
                 color=cq.Color(*fin.rgb, fin.alpha))
    assy.export(str(path))


def _tess(shape: cq.Shape, tol, ang):
    vs, ts = shape.tessellate(tol, ang)
    v = np.array([(p.x, p.y, p.z) for p in vs], float).reshape(-1, 3)
    t = np.array(ts, np.int64).reshape(-1, 3)
    return v, t


def export_glb(model: Model, path: Path, tol=0.6, ang=0.2):
    import trimesh
    from trimesh.visual.material import PBRMaterial

    scene = trimesh.Scene()
    for name, fin, shapes in model.parts:
        v, t = _tess(cq.Compound.makeCompound(shapes), tol, ang)
        if not len(t):
            continue
        v = np.column_stack([v[:, 0], v[:, 2], -v[:, 1]]) / 1000.0   # mm, Z up -> m, Y up
        mat = PBRMaterial(name=name, baseColorFactor=[*fin.rgb, fin.alpha],
                          metallicFactor=fin.metal, roughnessFactor=fin.rough,
                          emissiveFactor=list(fin.glow) if fin.glow else None,
                          alphaMode="BLEND" if fin.alpha < 1 else "OPAQUE",
                          doubleSided=fin.alpha < 1)
        mesh = trimesh.Trimesh(v, t, process=False,
                               visual=trimesh.visual.TextureVisuals(material=mat))
        mesh.vertex_normals   # per OCC face, so edges stay sharp and curves stay smooth
        scene.add_geometry(mesh, node_name=name, geom_name=name)
    path.write_bytes(scene.export(file_type="glb", include_normals=True))


def _to_manifold(solid: cq.Shape, tol, ang):
    import manifold3d as mf
    v, t = _tess(solid, tol, ang)
    key = np.round(v * 1000).astype(np.int64)            # weld at a micron
    _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    t = inv.reshape(-1)[t]
    t = t[(t[:, 0] != t[:, 1]) & (t[:, 1] != t[:, 2]) & (t[:, 0] != t[:, 2])]
    m = mf.Manifold(mf.Mesh(vert_properties=v[first].astype(np.float32),
                            tri_verts=t.astype(np.uint32)))
    return m if m.status() == mf.Error.NoError and not m.is_empty() else None


def weld_float32(v, t):
    """Round vertices to float32, merge the identical ones, drop triangles that collapse."""
    v32 = np.asarray(v, np.float64).astype(np.float32)
    uniq, inv = np.unique(v32, axis=0, return_inverse=True)
    t = inv.reshape(-1)[np.asarray(t, np.int64)]
    keep = (t[:, 0] != t[:, 1]) & (t[:, 1] != t[:, 2]) & (t[:, 0] != t[:, 2])
    return uniq, t[keep]


def bad_edges(t):
    """Vertex pairs of the edges not shared by exactly two triangles."""
    e = np.sort(np.concatenate([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]]), axis=1)
    edges, counts = np.unique(e, axis=0, return_counts=True)
    return edges[counts != 2]


def count_bad_edges(t):
    """Edges not shared by exactly two triangles: 0 for a closed, manifold mesh."""
    return len(bad_edges(t))


def _bead(a, b, r):
    """A thin manifold cylinder from a to b, a little longer than the edge."""
    import manifold3d as mf
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    L = float(np.linalg.norm(d))
    z = d / L
    x = np.cross(z, [1.0, 0, 0] if abs(z[0]) < 0.9 else [0, 1.0, 0])
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    m = np.column_stack([x, y, z, a - z * r])          # 3 x 4: rotate local Z onto the edge, then move
    return mf.Manifold.cylinder(L + 2 * r, r, r, 8).transform(m)


def export_print(model: Model, path: Path, scale: float):
    """Union every solid into one body at 1:scale, flat on the bed, as binary STL."""
    import manifold3d as mf

    tol = 0.01 * scale          # 0.01 mm at print size
    pieces, failed = [], 0
    for _, _, shapes in model.parts:
        for s in shapes:
            for solid in s.Solids():
                m = _to_manifold(solid, tol, 0.15)
                if m is None:
                    failed += 1
                else:
                    pieces.append(m)
    body = mf.Manifold.batch_boolean(pieces, mf.OpType.Add)
    body = body.scale((1 / scale,) * 3).trim_by_plane((0, 0, 1), 0.0)
    # trimming at the bed can leave zero-volume slivers where a curve just touched it
    parts = [c for c in body.decompose() if abs(c.volume()) > 1e-3]
    body = mf.Manifold.compose(parts)
    (x0, y0, _), (x1, y1, _) = (lambda b: (b[:3], b[3:]))(body.bounding_box())
    body = body.translate((-(x0 + x1) / 2, -(y0 + y1) / 2, 0))

    # STL stores float32. Snap to it here, the way a slicer will, and clean up what that does:
    # a 5 um simplify merges parts that only touch along a line, and welding at float32 can
    # collapse an edge shorter than float32 can resolve, leaving a triangle with a repeated
    # vertex. Dropping those is exactly that edge collapse.
    # Parts that only touch along a line can't be written as a closed STL at all, so as a last
    # resort each edge that is still not shared by exactly two triangles gets a 0.03 mm weld bead
    # along it, which turns the line contact into a real (if invisible) joint.
    for _ in range(4):
        body = body.simplify(0.005)
        mesh = body.to_mesh64() if hasattr(body, "to_mesh64") else body.to_mesh()
        v, t = weld_float32(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts))
        bad = bad_edges(t)
        if not len(bad):
            break
        beads = [_bead(v[i], v[j], 0.03) for i, j in bad if np.linalg.norm(v[i] - v[j]) > 1e-6]
        body = mf.Manifold.batch_boolean([body] + beads, mf.OpType.Add).trim_by_plane((0, 0, 1), 0.0)
    bad_edge_count = len(bad)
    tri = v[t]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    rec = np.zeros(len(t), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec["n"], rec["v"] = n, tri
    with open(path, "wb") as fh:
        fh.write(f"1:{scale:g} print, binary STL, mm".encode().ljust(80, b" "))
        fh.write(np.uint32(len(t)).tobytes())
        fh.write(rec.tobytes())

    bb = body.bounding_box()
    return {
        "size_mm": tuple(round(bb[i + 3] - bb[i], 1) for i in range(3)),
        "volume_cm3": round(body.volume() / 1000, 2),
        "triangles": len(t),
        "pieces": sum(1 for c in parts if c.volume() > 0),
        "sealed_voids": sum(1 for c in parts if c.volume() < 0),
        "genus": body.genus(),
        "skipped_solids": failed,
        "nonmanifold_edges": bad_edge_count,
    }
