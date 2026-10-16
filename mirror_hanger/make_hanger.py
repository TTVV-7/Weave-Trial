"""Renolux rearview-mirror hanger: logo -> three-colour printable model.

    python3 mirror_hanger/make_hanger.py [logo.jpg] [--out mirror_hanger/out]

Writes, all in one coordinate system (mm, base plate bottom-left at origin):
    black_base.stl   the plate with its hanging tab and hole
    white_layer.stl  white artwork, raised on top of the plate
    red_layer.stl    red artwork, raised on top of the plate
    hanger.3mf       the three as parts of one object, coloured and assigned
                     to extruders 1/2/3 (black/white/red)
    preview.png      original logo next to a top-down render of the model,
                     plus a map of what was thickened

Needs: opencv-python-headless, numpy, shapely, trimesh, mapbox-earcut,
matplotlib.
"""
import argparse
import io
import os
import sys
import zipfile

import cv2
import numpy as np
import shapely
import trimesh
from shapely import affinity
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from segment import segment  # noqa: E402

# ============================ dimensions (mm) ==============================
OVERALL_WIDTH = 80.0       # width of the base plate (tab not included)
MARGIN = 3.0               # base plate edge to artwork bounds
CORNER_RADIUS = 4.0        # base plate corner rounding
BASE_THICKNESS = 3.0       # black plate
RAISE = 0.8                # white/red stand this far above the plate

HOLE_DIAMETER = 4.0        # hanging hole
HOLE_WALL = 2.5            # minimum material all round the hole
HOLE_ABOVE_EDGE = 3.0      # hole centre sits this far above the plate's top
TAB_FILLET = 2.0           # rounding where the tab meets the plate

MIN_FEATURE = 0.8          # thinnest white/red feature allowed
MIN_GAP = 0.4              # black grooves narrower than this get filled
RASTER_RES = 0.02          # mm/px grid the thickening is worked out on
MIN_AREA = 0.05            # mm^2; specks smaller than this are dropped
SPIKE_FRAC = 0.75          # slivers under this x MIN_FEATURE wide are removed
CORNER_MAX_W = 0.5         # mm; corner slivers are narrower than this
CORNER_SKIP = 1.5          # x half-min-width; higher = leave sharper corners alone

SIMPLIFY_TOL = 0.04        # general outline simplification
STRAIGHT_TOL = 0.12        # stronger simplification -> crisp straight edges
STRAIGHT_BANDS = (0,)      # which horizontal bands get STRAIGHT_TOL (0 = top)
BAND_NAMES = ("building", "RENOLUX", "CONTRACTING")
BAND_MERGE_GAP = 1.5       # mm; bands closer than this count as one
ARC_SEGMENTS = 16          # per quarter circle on round edges

COLOURS = {                # display colour, extruder
    "black": ((0x1A, 0x1A, 0x1A), 1),
    "white": ((0xF2, 0xF2, 0xF2), 2),
    "red":   ((0xD7, 0x1F, 0x26), 3),
}
# ===========================================================================

MITRE = dict(join_style="mitre", mitre_limit=2.0)


def as_polys(g):
    if g.is_empty:
        return []
    if isinstance(g, Polygon):
        return [g]
    return [p for p in getattr(g, "geoms", []) if isinstance(p, Polygon)
            and not p.is_empty]


# ------------------------------------------------------------- vectorizing
def bands(fg):
    """Row ranges of the artwork separated by fully empty rows."""
    rows = fg.any(axis=1)
    out, start = [], None
    for y, on in enumerate(rows):
        if on and start is None:
            start = y
        elif not on and start is not None:
            out.append((start, y))
            start = None
    if start is not None:
        out.append((start, len(rows)))
    return out


def mask_to_polys(mask):
    """Pixel mask -> shapely polygons (with holes), pixel coordinates."""
    cs, hier = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    if hier is None:
        return []
    hier = hier[0]
    out = []
    for i, c in enumerate(cs):
        if hier[i][3] != -1 or len(c) < 3:
            continue                        # holes are picked up by parents
        holes, j = [], hier[i][2]
        while j != -1:
            if len(cs[j]) >= 3:
                holes.append(cs[j][:, 0, :] + 0.5)
            j = hier[j][0]
        p = Polygon(cs[i][:, 0, :] + 0.5, holes).buffer(0)
        out += as_polys(p)
    return out


# --------------------------------------------------------------- thickening
def rasterize(g, shape, res):
    """Polygons in mm -> uint8 mask at `res` mm/px (row 0 at y=0)."""
    m = np.zeros(shape, np.uint8)
    scale = 16 / res                                # fillPoly shift=4
    for p in sorted(as_polys(g), key=lambda q: -q.area):   # islands last
        pts = lambda ring: np.round(np.asarray(ring.coords) * scale).astype(np.int32)
        cv2.fillPoly(m, [pts(p.exterior)], 255, cv2.LINE_8, 4)
        if p.interiors:
            cv2.fillPoly(m, [pts(i) for i in p.interiors], 0, cv2.LINE_8, 4)
    return m


def thicken_local(g, shape, res=None, min_w=None):
    """Bring every stroke of g up to min_w, leaving thicker parts alone.

    Strokes are found on the distance transform: a ridge pixel sits on a
    stroke's centreline and its distance value is half the stroke's width
    there. Every ridge pixel narrower than min_w gets a disc of diameter
    min_w drawn round it, so a 0.64 mm stroke grows 0.08 mm per side and a
    tapered tip ends in a 0.8 mm round end -- instead of the whole shape
    being offset by whatever its sharpest tip needs.

    Narrow ridge pixels close to a part that is already wide enough are
    skipped: those are the medial-axis branches running into ordinary
    corners, and growing them would just blunt every corner of every letter.

    Returns (added region in mm, stroke widths in mm that were thickened,
    their ridge pixels).
    """
    res = res or RASTER_RES
    min_w = min_w or MIN_FEATURE
    m = rasterize(g, shape, res)
    r_px = min_w / 2 / res
    disc = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                     (2 * round(r_px) + 1,) * 2)
    opened = cv2.morphologyEx(m, cv2.MORPH_OPEN, disc)
    dist = cv2.distanceTransform(m, cv2.DIST_L2, 5)
    ridge = (dist > 0) & (dist >= cv2.dilate(dist, np.ones((3, 3), np.uint8)))
    to_ok = cv2.distanceTransform(255 - opened, cv2.DIST_L2, 5)
    # A corner's sliver is never wide (under ~0.46 mm even for the X's
    # sharp corners), so a ridge pixel that is wide-ish but still under
    # min_w is a real stroke end -- the C and G terminals -- even when it
    # sits right next to an already-thick part.
    seeds = ridge & (2 * dist < 2 * r_px) & (to_ok > 1) & (
        (to_ok > CORNER_SKIP * r_px) | (2 * dist * res >= CORNER_MAX_W))
    add = cv2.dilate(seeds.astype(np.uint8) * 255, disc)
    add[m > 0] = 0
    added = unary_union([affinity.scale(p, res, res, origin=(0, 0))
                         for p in mask_to_polys(add)])
    added = added.simplify(res, preserve_topology=True).buffer(0)
    return added, 2 * dist[seeds] * res, seeds


# --------------------------------------------------------------- geometry
def build(logo):
    img, masks = segment(logo)
    fg = np.maximum(masks["white"], masks["red"]) > 0
    ys, xs = np.nonzero(fg)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1

    art_w = OVERALL_WIDTH - 2 * MARGIN
    s = art_w / (x1 - x0)                                   # mm per pixel
    art_h = (y1 - y0) * s
    plate_h = art_h + 2 * MARGIN

    def to_mm(g):
        g = affinity.translate(g, -x0, -y1)
        g = affinity.scale(g, s, -s, origin=(0, 0))         # flip y
        return affinity.translate(g, MARGIN, MARGIN)

    # bands of artwork split by empty rows; tiny splits (inside the
    # building) don't count
    band_rows = []
    for r0, r1 in bands(fg):
        if band_rows and (r0 - band_rows[-1][1]) * s < BAND_MERGE_GAP:
            band_rows[-1] = (band_rows[-1][0], r1)
        else:
            band_rows.append((r0, r1))
    band_y = [(MARGIN + (y1 - r1) * s, MARGIN + (y1 - r0) * s)
              for r0, r1 in band_rows]
    band_name = lambda i: BAND_NAMES[i] if i < len(BAND_NAMES) else f"band {i}"

    raw = {}
    for colour in ("white", "red"):
        pieces = []
        for bi, (r0, r1) in enumerate(band_rows):
            m = np.zeros_like(masks[colour])
            m[r0:r1] = masks[colour][r0:r1]
            tol = STRAIGHT_TOL if bi in STRAIGHT_BANDS else SIMPLIFY_TOL
            for p in mask_to_polys(m):
                p = to_mm(p).simplify(tol, preserve_topology=True).buffer(0)
                pieces += [q for q in as_polys(p) if q.area >= MIN_AREA]
        raw[colour] = unary_union(pieces)

    shape = (int(np.ceil(plate_h / RASTER_RES)) + 2,
             int(np.ceil(OVERALL_WIDTH / RASTER_RES)) + 2)
    report, grown = [], {}
    for colour in ("white", "red"):
        added, widths, seeds = thicken_local(raw[colour], shape)
        grown[colour] = unary_union([raw[colour], added])
        sy = np.nonzero(seeds)[0] * RASTER_RES
        for bi, (lo, hi) in enumerate(band_y):
            sel = (sy >= lo - 0.5) & (sy <= hi + 0.5)
            if not sel.any():
                continue
            hit = [q for q in as_polys(raw[colour])
                   if q.intersects(added) and lo - 0.5 <= q.centroid.y <= hi + 0.5
                   and q.buffer(RASTER_RES * 2).intersection(added).area > 1e-3]
            report.append((colour, band_name(bi), len(hit),
                           np.percentile(widths[sel], 50), widths[sel].min(),
                           added.intersection(box(0, lo - 0.5, OVERALL_WIDTH,
                                                  hi + 0.5)).area))

    # Fill black grooves too narrow to print, on both colours together so
    # the seam where white meets red closes as well; the fill goes to
    # whichever colour it touches first (white on ties).
    g = MIN_GAP / 2
    both = unary_union([grown["white"], grown["red"]])
    filled = both.buffer(g, **MITRE).buffer(-g, **MITRE).difference(both)
    fill_w = filled.intersection(grown["white"].buffer(g, **MITRE))

    # Thickening can push one colour onto the other. Each keeps its own
    # original area; contested new area goes to white.
    white = unary_union([grown["white"], fill_w]).difference(raw["red"])
    red = unary_union([grown["red"], filled.difference(fill_w)]).difference(white)
    # After thickening every real feature is >= MIN_FEATURE, so an opening
    # at SPIKE_FRAC of that only removes slivers and spikes left behind by
    # the segmentation and the colour split.
    o = SPIKE_FRAC * MIN_FEATURE / 2

    def clean(x):
        # mitred offsets divide by zero on near-degenerate edges, so snap
        # and drop micro-segments first
        x = shapely.set_precision(x.buffer(0), 0.001).simplify(0.005)
        x = x.buffer(-o, **MITRE).buffer(o, **MITRE)
        return unary_union([p for p in as_polys(x) if p.area >= MIN_AREA])
    white, red = clean(white), clean(red)
    gaps_closed = {c: len(as_polys(raw[c])) - len(as_polys(v))
                   for c, v in (("white", white), ("red", red))}

    # Base plate from the *original* art bounds, so it is exactly
    # OVERALL_WIDTH wide; thickening grows at most MIN_FEATURE/2 into margin.
    plate = box(0, 0, OVERALL_WIDTH, plate_h)
    plate = plate.buffer(-CORNER_RADIUS, quad_segs=ARC_SEGMENTS).buffer(
        CORNER_RADIUS, quad_segs=ARC_SEGMENTS)
    hx, hy = OVERALL_WIDTH / 2, plate_h + HOLE_ABOVE_EDGE
    # a polygonised circle's chords sit inside the true circle; size the
    # tab so the chords, not just the vertices, clear HOLE_WALL
    tab_r = (HOLE_DIAMETER / 2 + HOLE_WALL) / np.cos(np.pi / (4 * ARC_SEGMENTS))
    tab = unary_union([Point(hx, hy).buffer(tab_r, quad_segs=ARC_SEGMENTS),
                       box(hx - tab_r, plate_h - CORNER_RADIUS, hx + tab_r, hy)])
    f = TAB_FILLET
    base = unary_union([plate, tab]).buffer(f, quad_segs=ARC_SEGMENTS).buffer(
        -f, quad_segs=ARC_SEGMENTS)
    hole = Point(hx, hy).buffer(HOLE_DIAMETER / 2, quad_segs=ARC_SEGMENTS)
    base = base.difference(hole)

    # sanity checks
    wall = Point(hx, hy).distance(base.exterior) - HOLE_DIAMETER / 2
    assert wall >= HOLE_WALL - 0.01, f"only {wall:.2f} mm round the hole"
    art = unary_union([white, red])
    assert base.buffer(1e-6).contains(art), "artwork overhangs the base"

    info = dict(gaps_closed=gaps_closed, wall=wall, scale=s, plate_h=plate_h, crop=(x0, y0, x1, y1), img=img,
                hole=(hx, hy), tab_top=hy + tab_r)
    return base, white, red, raw, report, info


# ----------------------------------------------------------------- meshing
def extrude(g, h, z0=0.0):
    # Snapping to a 1 um grid merges near-coincident vertices; left in, the
    # triangulator welds them and the walls come out non-manifold.
    g = shapely.set_precision(g, 0.001)
    meshes = [trimesh.creation.extrude_polygon(p, h) for p in as_polys(g)]
    m = trimesh.util.concatenate(meshes)
    m.apply_translation((0, 0, z0))
    return m


def write_3mf(path, parts):
    """parts: list of (name, mesh, rgb, extruder). One object, N parts."""
    esc = lambda s: s.replace("&", "&amp;").replace('"', "&quot;")
    xml = ['<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" '
           'xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing'
           '/core/2015/02" xmlns:m="http://schemas.microsoft.com/3dmanufacturing'
           '/material/2015/02"><metadata name="Title">Renolux mirror hanger'
           '</metadata><resources><m:colorgroup id="1">']
    xml += ['<m:color color="#%02X%02X%02XFF"/>' % rgb for _, _, rgb, _ in parts]
    xml.append("</m:colorgroup>")
    cfg = ['<?xml version="1.0" encoding="UTF-8"?>\n<config>\n'
           f'  <object id="{len(parts) + 2}">\n'
           '    <metadata key="name" value="Renolux mirror hanger"/>\n'
           '    <metadata key="extruder" value="1"/>\n']
    for i, (name, mesh, _, ext) in enumerate(parts):
        oid = i + 2
        xml.append(f'<object id="{oid}" type="model" name="{esc(name)}" '
                   f'pid="1" pindex="{i}"><mesh><vertices>')
        xml += [f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>'
                for x, y, z in mesh.vertices]
        xml.append("</vertices><triangles>")
        xml += [f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in mesh.faces]
        xml.append("</triangles></mesh></object>")
        cfg.append(f'    <part id="{oid}" subtype="normal_part">\n'
                   f'      <metadata key="name" value="{esc(name)}"/>\n'
                   '      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 '
                   '0 0 0 1"/>\n'
                   f'      <metadata key="extruder" value="{ext}"/>\n'
                   '    </part>\n')
    top = len(parts) + 2
    comps = "".join(f'<component objectid="{i + 2}"/>' for i in range(len(parts)))
    xml.append(f'<object id="{top}" type="model" name="Renolux mirror hanger">'
               f'<components>{comps}</components></object></resources>'
               f'<build><item objectid="{top}"/></build></model>')
    cfg.append("  </object>\n</config>\n")

    types = ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://'
             'schemas.openxmlformats.org/package/2006/content-types"><Default '
             'Extension="rels" ContentType="application/vnd.openxmlformats-'
             'package.relationships+xml"/><Default Extension="model" '
             'ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel'
             '+xml"/><Default Extension="config" ContentType="text/xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="'
            'http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://'
            'schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
            '</Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", types)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", "".join(xml))
        z.writestr("Metadata/model_settings.config", "".join(cfg))


# ----------------------------------------------------------------- preview
def write_preview(path, base, white, red, raw, info):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import PathPatch
    from matplotlib.path import Path as MPath

    def patch(ax, g, rgb, **kw):
        for p in as_polys(g):
            verts, codes = [], []
            for ring in [p.exterior, *p.interiors]:
                c = np.asarray(ring.coords)
                verts += c.tolist()
                codes += [MPath.MOVETO] + [MPath.LINETO] * (len(c) - 2) + [
                    MPath.CLOSEPOLY]
            ax.add_patch(PathPatch(MPath(verts, codes), fc=rgb, ec="none", **kw))

    c = {k: np.array(v[0]) / 255 for k, v in COLOURS.items()}
    x0, y0, x1, y1 = info["crop"]
    s = info["scale"]
    img = cv2.cvtColor(info["img"], cv2.COLOR_BGR2RGB)
    pad = int(MARGIN / s)
    crop = img[max(0, y0 - pad):y1 + pad, max(0, x0 - pad):x1 + pad]

    fig, axs = plt.subplots(1, 3, figsize=(18, 6.5), facecolor="#d0d0d0")
    axs[0].imshow(crop)
    axs[0].set_title("original")
    for ax, title in ((axs[1], "model, top view"),
                      (axs[2], "thickened (yellow = added)")):
        patch(ax, base, c["black"])
        if ax is axs[1]:
            patch(ax, white, c["white"])
            patch(ax, red, c["red"])
        else:
            patch(ax, raw["white"], c["white"] * 0.55)
            patch(ax, raw["red"], c["red"] * 0.55)
            added = unary_union([white, red]).difference(
                unary_union([raw["white"], raw["red"]]))
            patch(ax, added, (1.0, 0.85, 0.0))
        minx, miny, maxx, maxy = base.bounds
        ax.set_xlim(minx - 2, maxx + 2)
        ax.set_ylim(miny - 2, maxy + 2)
        ax.set_aspect("equal")
        ax.set_title(title)
        ax.set_xlabel("mm")
    for ax in axs:
        ax.set_facecolor("#d0d0d0")
    fig.tight_layout()
    fig.savefig(path, dpi=130, facecolor=fig.get_facecolor())
    plt.close(fig)


# -------------------------------------------------------------------- main
def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("logo", nargs="?", default=os.path.join(here, "logo.jpg"))
    ap.add_argument("--out", default=os.path.join(here, "out"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    base, white, red, raw, report, info = build(a.logo)

    if report:
        print(f"WARNING: features thinner than {MIN_FEATURE} mm were thickened "
              f"to {MIN_FEATURE} mm:")
        for colour, name, n, med, lo, area in report:
            print(f"  {colour:5s} {name:12s} {n:3d} shape(s): typical thin stroke "
                  f"{med:.2f} mm, thinnest {lo:.2f} mm, "
                  f"+{area:.1f} mm2 added")
        for colour, n in info["gaps_closed"].items():
            if n > 0:
                print(f"  {colour}: {n} gap(s) closed, neighbouring shapes merged")
    else:
        print(f"all features already >= {MIN_FEATURE} mm")

    meshes = {
        "black": extrude(base, BASE_THICKNESS),
        "white": extrude(white, RAISE, BASE_THICKNESS),
        "red": extrude(red, RAISE, BASE_THICKNESS),
    }
    names = {"black": "black_base", "white": "white_layer", "red": "red_layer"}
    for k, m in meshes.items():
        m.export(os.path.join(a.out, names[k] + ".stl"))
        print(f"{names[k]}.stl  {len(m.faces):6d} tris  watertight={m.is_watertight}"
              f"  volume={m.volume / 1000:.2f} cm3")
    write_3mf(os.path.join(a.out, "hanger.3mf"),
              [(names[k], meshes[k], *COLOURS[k]) for k in ("black", "white", "red")])
    write_preview(os.path.join(a.out, "preview.png"), base, white, red, raw, info)

    bx = base.bounds
    print(f"plate {OVERALL_WIDTH:.1f} x {info['plate_h']:.1f} mm, overall incl. tab "
          f"{bx[2] - bx[0]:.1f} x {bx[3] - bx[1]:.1f} mm, "
          f"height {BASE_THICKNESS + RAISE:.1f} mm")
    print(f"hole {HOLE_DIAMETER} mm at ({info['hole'][0]:.1f}, {info['hole'][1]:.1f}),"
          f" {info['wall']:.2f} mm of material round it")
    print(f"wrote {a.out}/: black_base.stl white_layer.stl red_layer.stl "
          "hanger.3mf preview.png")


if __name__ == "__main__":
    main()
