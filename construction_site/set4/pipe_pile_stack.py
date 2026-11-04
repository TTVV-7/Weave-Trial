"""Stack of six 36 in (914 mm) OD steel pipe piles, 19 mm wall, 12 m long, 3-2-1 on timber dunnage.

A generic, brand-neutral lay-down-yard stack of open-ended steel tubular piles, as delivered to
a wharf / jetty job (berthing dolphins, trestle bents, conveyor-gallery foundations) and
stored next to the pile-pitching crane. Dimensions are those of standard spiral- or
longitudinally-welded structural pipe piles:

* each pile: 914 mm (36 in) outside diameter, 19 mm (3/4 in) wall, so an 876 mm bore; 12.0 m
  long (one mill length, ~5 t each); both ends machine-bevelled (30 deg, 2 mm land) for a
  field butt weld; open ends, the bore is hollow right through; a longitudinal
  submerged-arc weld seam standing ~4 mm proud along each pile;
* a welded lifting / pitching padeye (40 mm plate, 70 mm hole) on the crown ~600 mm from the
  head end of every pile, standing radially;
* a driving shoe on three piles: a 300 mm wide, 12 mm thick steel band welded flush round the
  toe to stiffen it for hard driving (a cutting ring);
* mill marks: a yellow paint-marker patch near the +X end of every pile with its heat number,
  and a white stencil line (size, wall, grade, length, pile number) along the side (lettering
  in the colour model only);
* two surface conditions: blue-black mill scale fresh from the mill (three piles) and light
  brown surface rust on the three that have stood longer in the yard;
* six piles stacked 3-2-1, the bottom row on three 8 x 6 timber skids (200 x 150 mm, laid flat)
  at the quarter points and centre, each upper tier on 6 x 6 (150 mm) dunnage laid across the
  crowns of the tier below; every pile beds ~5 mm into its timbers and the timbers ~5 mm into
  the crowns under them; piles in a row 20 mm apart (934 mm centres); the outer pile of every
  tier is held by a nailed timber wedge chock on each timber. Timbers and piles are a few cm off
  true, as stacked by hand.

Overall ~12.1 m long (over the hand-staggered piles), ~3.4 m wide over the skids (2.8 m over
the bottom row) and ~3.17 m high to the crown of the top pile (3.3 m to its padeye).

Millimetres, X along the piles, Y across the stack, Z up, ground at Z = 0.
"""

from __future__ import annotations

import math

import cadquery as cq

from cadkit import Finish, arc_pts, box, cut, cyl, mv, prism, rgb, rot, text
from finishes import STEEL

ASSET = dict(key="pipe_pile_stack", stem="Steel_Pipe_Pile_Stack",
             title="Steel Pipe Pile Stack (36 in, 12 m)", az=25, el=22, size="1200x900")

MILL_SCALE = Finish(rgb("#30363c"), metal=0.6, rough=0.5)     # blue-black mill scale -> Silver grey
LIGHT_RUST = Finish(rgb("#73401f"), metal=0.35, rough=0.9)    # light yard rust -> Wood brown
PADEYE = Finish(rgb("#5a6066"), metal=0.7, rough=0.45)        # freshly welded plate / shoe steel
SHOE = Finish(rgb("#9ca2a8"), metal=0.8, rough=0.35)      # bright rolled band
TIMBER_YARD = Finish(rgb("#c4a77a"), rough=0.9)                # weathered pine dunnage -> Sand
CHOCK = Finish(rgb("#8a6a45"), rough=0.88)                     # darker hardwood wedges -> Wood brown
END_GRAIN = Finish(rgb("#7a5c38"), rough=0.9)
MARKER = Finish(rgb("#f2c200"), rough=0.5)                     # yellow paint-marker patch
STENCIL_WHITE = Finish(rgb("#f0f0ea"), rough=0.7)
STENCIL_BLACK = Finish(rgb("#1d1f22"), rough=0.7)

# ---------------------------------------------------------------- pile dimensions
RO = 457.0                  # 914 mm OD
WALL = 19.0
L = 12000.0
BEV = 17.0                  # radial depth of the 30 deg end bevel (2 mm land)
BEV_X = BEV * math.tan(math.radians(30))
SHOE_T, SHOE_L = 12.0, 300.0

# ---------------------------------------------------------------- stack
GAP = 20.0
PITCH = 2 * RO + GAP        # 934 mm centres in a row
SINK = 5.0                  # piles into timbers, timbers into crowns
SKID_H, SKID_W = 150.0, 200.0
DUN = 150.0
Z_GROUND = -2.0             # skids sunk 2 mm into the ground plane
# timbers at the quarter points and centre, hand-placed a little off true per tier
X_TIMBER = ((-3800.0, 0.0, 3800.0), (-3770.0, 25.0, 3830.0), (-3825.0, -20.0, 3790.0))
SEAM_DEG = ((35.0, -30.0, 50.0), (-40.0, 30.0), (60.0,))   # seam position round each pile
SKID_HALF = (1700.0, 1160.0, 700.0)    # half-lengths across Y: skids, tier-2 and tier-3 dunnage

# (y, head end +1/-1 along X, x offset, finish, driving shoe on the toe, pile number, heat number)
TIER_ROWS = [
    [(-PITCH, 1, 35.0, LIGHT_RUST, True, "P-21", "HT 6B2817"),
     (0.0, -1, -40.0, LIGHT_RUST, True, "P-22", "HT 6B2817"),
     (PITCH, 1, 15.0, MILL_SCALE, False, "P-23", "HT 6B2904")],
    [(-PITCH / 2, -1, -55.0, MILL_SCALE, True, "P-24", "HT 6B2904"),
     (PITCH / 2, 1, 25.0, LIGHT_RUST, False, "P-25", "HT 6B3150")],
    [(0.0, 1, -20.0, MILL_SCALE, False, "P-26", "HT 6B3150")],
]


def build(m):
    wall = m.t(WALL)
    ri = RO - wall

    # tier centre heights
    z_top_skid = Z_GROUND + SKID_H
    zs = [z_top_skid - SINK + RO]
    for _ in range(2):
        zs.append(zs[-1] + RO - SINK + DUN - SINK + RO)

    # ---- timbers: ground skids, then dunnage across the crowns of each tier
    skids = [box(x - SKID_W / 2, x + SKID_W / 2, -SKID_HALF[0], SKID_HALF[0], Z_GROUND, z_top_skid)
             for x in X_TIMBER[0]]
    m.add("skids", TIMBER_YARD, skids)
    dunnage = []
    for k in (1, 2):
        zb = zs[k - 1] + RO - SINK
        dunnage += [box(x - DUN / 2, x + DUN / 2, -SKID_HALF[k], SKID_HALF[k], zb, zb + DUN)
                    for x in X_TIMBER[k]]
    m.add("dunnage", TIMBER_YARD, dunnage)
    if not m.print_mode:     # darker sawn end grain on every timber
        grain = []
        for b in skids + dunnage:
            bb = b.BoundingBox()
            grain += [box(bb.xmin + 3, bb.xmax - 3, y0, y1, bb.zmin + 3, bb.zmax - 3)
                      for y0, y1 in ((bb.ymin - 1.5, bb.ymin + 1), (bb.ymax - 1, bb.ymax + 1.5))]
        m.add("timber_end_grain", END_GRAIN, grain)

    # ---- piles
    tube = pile_solid(ri)
    chocks, nails = [], []
    for k, row in enumerate(TIER_ROWS):
        zc = zs[k]
        z_timber = z_top_skid if k == 0 else zc - RO + SINK      # top of the timber under this tier
        ys = [r[0] for r in row]
        for i, (y, head, dx, fin, shoe, pno, heat) in enumerate(row):
            tag = f"{k + 1}{'abc'[i]}"
            xh = dx + head * L / 2          # head end
            xt = dx - head * L / 2          # toe end
            # the tube, with its longitudinal submerged-arc weld seam standing ~4 mm proud
            seam = cyl(m.r(10), (dx - L / 2 + BEV_X + 5, 0, RO - 6), (dx + L / 2 - BEV_X - 5, 0, RO - 6))
            seam = rot(seam, SEAM_DEG[k][i], (1, 0, 0))
            m.add(f"pile_{tag}", fin, mv(tube, dx, y, zc), mv(seam, 0, y, zc))
            m.add(f"padeye_{tag}", PADEYE, padeye(m, xh - head * 600.0, y, zc))
            if shoe:
                x0, x1 = sorted((xt, xt + head * SHOE_L))
                band_ = cut(cyl(RO + SHOE_T, (x0, y, zc), (x1, y, zc)),
                            cyl(RO - 4, (x0 - 1, y, zc), (x1 + 1, y, zc)))
                # flush with the toe: the pile's bevel lies inside the band, so the end faces don't touch
                m.add(f"driving_shoe_{tag}", SHOE, band_)
            # the +X end: yellow paint-marker patch with the heat number, and the side stencil
            xe = dx + L / 2
            m.add(f"marker_patch_{tag}", MARKER, marker_patch(xe - 520, xe - 120, y, zc))
            if not m.print_mode:
                m.add(f"heat_number_{tag}", STENCIL_BLACK, patch_text(heat, xe - 320, y, zc))
                m.add(f"stencil_{tag}", STENCIL_WHITE, side_stencil(pno, dx + 1200, y, zc))
            # wedge chocks on the outside of the outer piles of the tier
            for s in (1, -1):
                if (s > 0 and y != max(ys)) or (s < 0 and y != min(ys)):
                    continue
                for xs in X_TIMBER[k]:
                    w, nl = wedge(y, zc, z_timber, s, xs - 50, xs + 50, top=m.t(30))
                    chocks.append(w)
                    nails += nl
    m.add("wedge_chocks", CHOCK, chocks)
    if not m.print_mode:
        m.add("chock_nails", STEEL, nails)


# ---------------------------------------------------------------- one pile

def pile_solid(ri):
    """One open tube along X, centred on the origin, both ends bevelled 30 deg with a 2 mm land."""
    h = L / 2
    prof = [(-h, ri), (-h, RO - BEV), (-h + BEV_X, RO), (h - BEV_X, RO), (h, RO - BEV), (h, ri)]
    return cq.Workplane("XZ").polyline(prof).close().revolve(360, (0, 0, 0), (1, 0, 0)).val()


def padeye(m, x, y, zc):
    """Radial lifting padeye plate on the crown, its foot welded 15 mm into the wall."""
    t = m.t(40)
    z0 = zc + RO - 15
    zh = zc + RO + 110            # hole centre
    rr = 85.0
    prof = [(x - 150, z0), (x + 150, z0), (x + 150, zc + RO + 25)] + \
        arc_pts(x, zh, rr, 0, 180, 18) + [(x - 150, zc + RO + 25)]
    plate = prism(prof, "y", y - t / 2, y + t / 2)
    plate = cut(plate, cyl(35, (x, y - 60, zh), (x, y + 60, zh)))
    # fillet welds along the foot, both sides
    welds = [prism([(yy, zc + RO - 8), (yy + d * 22, zc + RO - 8), (yy, zc + RO + 18)], "x", x - 155, x + 155)
             for yy, d in ((y + t / 2 - 2, 1), (y - t / 2 + 2, -1))]
    return [plate] + welds


def marker_patch(x0, x1, y, zc):
    """Yellow paint-marker patch on the upper +Y quarter of the pile, 3 mm proud."""
    ring = cut(cyl(RO + 3, (x0, y, zc), (x1, y, zc)), cyl(RO - 6, (x0 - 1, y, zc), (x1 + 1, y, zc)))
    sector = [(y, zc)] + [(y + 600 * math.cos(math.radians(a)), zc + 600 * math.sin(math.radians(a)))
                          for a in (25, 45, 65, 85)]
    return ring.intersect(prism(sector, "x", x0 - 5, x1 + 5))


def patch_text(txt, x, y, zc, deg=55.0):
    a = math.radians(deg)
    n = (0.0, math.cos(a), math.sin(a))
    r = RO + 1
    return text(txt, 62, 4.0, (x, y + r * n[1], zc + r * n[2]), (-1, 0, 0), n)


def side_stencil(pno, x, y, zc):
    out = []
    for line, deg, size in ((f"{pno}   914 x 19.0 WT   12.00 M", 40.0, 80.0),
                            ("X52   SAWL   HT 6B   LOT 07", 24.0, 66.0)):
        a = math.radians(deg)
        n = (0.0, math.cos(a), math.sin(a))
        r = RO - 2
        out.append(text(line, size, 4.5, (x, y + r * n[1], zc + r * n[2]), (-1, 0, 0), n))
    return out


def wedge(yc, zc, z0, s, x0, x1, h=130.0, phi=40.0, top=30.0):
    """Timber wedge chock on a timber whose top is z0, against the pile at (yc, zc), on side s.

    Its sloped face is tangent to a circle 6 mm inside the pile, so it beds into the pile."""
    a = math.radians(phi)
    rt = RO - 6
    py, pz = yc + s * rt * math.sin(a), zc - rt * math.cos(a)

    def y_at(z):
        return py + s * (z - pz) / math.tan(a)

    zb = z0 - 3
    y_toe, y_tf = y_at(zb), y_at(z0 + h)
    y_tb = y_tf + s * top
    y_bb = y_tb + s * 70
    w = prism([(y_toe, zb), (y_tf, z0 + h), (y_tb, z0 + h), (y_bb, zb)], "x", x0, x1)
    xm, ym = (x0 + x1) / 2, (y_tf + y_tb) / 2
    nails = [cyl(7, (xm + d, ym, z0 + h - 2), (xm + d, ym, z0 + h + 2.5)) for d in (-25, 25)]
    return w, nails
