"""Mockup of white lines on the iPad holder's front face: four options drawn
on the real geometry. Not part of the print yet.

    python ipad_holder/front_lines_mockup.py ipad_holder/front_lines_mockup.png
"""
import sys; sys.path.insert(0,'ipad_holder'); sys.path.insert(0,'.')
import make_holder as mh, numpy as np, manifold3d as m3, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.path import Path; from matplotlib.patches import PathPatch, Rectangle

parts = mh.build_holder(); b = parts[0].solid
outline = b.slice(6.0)                 # full silhouette
face = b.slice(11.75)                  # the flat front face
outer = mh.rounded_rect(118, -208.6, 261.2, 1.9, mh.CORNER_R)
keep = face.offset(-0.7, m3.JoinType.Round)   # lines stay 0.7 mm off every edge

def ring(d, w):
    return (outer.offset(-d, m3.JoinType.Round) - outer.offset(-d - w, m3.JoinType.Round)) ^ keep

def corners(d, w, L):
    r = ring(d, w)
    boxes = [m3.CrossSection.square([L, L]).translate([x, y]) for x, y in
             ((118, 1.9 - L), (261.2 - L, 1.9 - L), (118, -208.6), (261.2 - L, -208.6))]
    return r ^ m3.CrossSection.batch_boolean(boxes, m3.OpType.Add)

def swoosh(x0, y0, x1, y1, sag, wmax, n=80):
    """A tapered stroke from (x0, y0) to (x1, y1), bowed down by ``sag``,
    widest in the middle and coming to points at both ends."""
    t = np.linspace(0, 1, n)
    x = x0 + (x1 - x0) * t
    y = y0 + (y1 - y0) * t - sag * 4 * t * (1 - t)
    w = wmax * np.sin(np.pi * t) ** 0.7
    pts = np.vstack([np.c_[x, y], np.c_[x[::-1], (y + w)[::-1]]])
    cs = m3.CrossSection([pts.tolist()], m3.FillRule.NonZero)
    if cs.area() == 0:
        cs = m3.CrossSection([pts[::-1].tolist()], m3.FillRule.NonZero)
    return cs

cx = 188.6                                 # home button centre
sw = swoosh(cx - 62, -203.0, cx - 7.5, -200.2, 2.6, 1.4)
sw = (sw + sw.mirror([1, 0]).translate([2 * cx, 0])) ^ keep

variants = [
    ("A  Single pinstripe", "0.8 mm line, 3 mm in from the edge", ring(3.0, 0.8)),
    ("B  Double pinstripe", "two 0.6 mm lines, 1.1 mm apart", ring(2.2, 0.6) + ring(3.9, 0.6)),
    ("C  Corner accents", "0.8 mm line, 35 mm along each corner", corners(3.0, 0.8, 35)),
    ("D  Swoosh", "tapered, up to 1.4 mm; nods to the VanEye swoosh", sw),
]

NAVY, NAVY_EDGE, WHITE, SCREEN = "#16284a", "#0d1a33", "#f4f5f7", "#0b0c0f"
def fill(ax, cs, fc, ec="none", lw=0):
    loops = cs.to_polygons()
    if not loops: return
    verts = np.vstack([np.vstack([l, l[:1]]) for l in loops]); codes = []
    for l in loops: codes += [Path.MOVETO] + [Path.LINETO] * (len(l) - 1) + [Path.CLOSEPOLY]
    ax.add_patch(PathPatch(Path(verts, codes), fc=fc, ec=ec, lw=lw))

fig = plt.figure(figsize=(20, 10.5), facecolor="white")
gs = fig.add_gridspec(2, 4, height_ratios=[3.1, 1], top=0.9, bottom=0.02, left=0.01, right=0.99, hspace=0.12, wspace=0.04)
for i, (title, sub, lines) in enumerate(variants):
    ax = fig.add_subplot(gs[0, i])
    # the iPad behind the opening
    ax.add_patch(Rectangle((121, -205.1), 134.8, 204, fc=SCREEN))
    fill(ax, outline, NAVY_EDGE)          # rounded-over edge reads darker
    fill(ax, face, NAVY)
    fill(ax, lines, WHITE)
    ax.set_xlim(112, 267); ax.set_ylim(-214, 30); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(f"{title}\n{sub}", fontsize=13, loc="left")
    # close-up of the bottom-left corner and home button
    az = fig.add_subplot(gs[1, i])
    az.add_patch(Rectangle((121, -205.1), 134.8, 204, fc=SCREEN))
    fill(az, outline, NAVY_EDGE); fill(az, face, NAVY); fill(az, lines, WHITE)
    az.set_xlim(115, 200); az.set_ylim(-212, -180); az.set_aspect("equal"); az.axis("off")
    az.set_title("close-up: bottom-left and home button", fontsize=10, loc="left", color="#555")
fig.suptitle("iPad holder: white lines on the front face (mockup, drawn on the real geometry)", fontsize=17, x=0.02, y=0.98, ha="left")
plt.savefig(sys.argv[1], dpi=110)
for t, _, l in variants: print(t, 'area', round(l.area(), 1), 'mm2, pieces', len(l.decompose()))
