#!/usr/bin/env python3
"""A 600 x 600 mm animated LED sign in the neon style: Santa going down the chimney.

    python neonsign/make_neon_sign.py
    python neonsign/make_neon_sign.py --bed 180 --pitch 16.7 --out out/neon

writes ``neonsign/example/`` (or ``--out``):

* ``channels_plate_N.3mf`` -- everything that holds LEDs, packed onto beds of
  ``--bed`` mm: the channels for the lines, the moon, and the little star and
  dot boxes. Print them in white; it bounces the light.
* ``diffusers_plate_N.3mf`` -- the translucent caps and lids that sit on top
  of all of those. Print them in natural PETG or thin white PLA.
* ``back_parts.3mf`` -- the electronics cover and four wall standoffs.
* ``template.svg`` -- the board at 1:1: where every part goes, and every hole
  to drill. ``template_a4.pdf`` is the same thing tiled onto A4 pages.
* ``neon_layout.h`` -- the LED index of every segment, for the sketch in
  ``firmware/``.
* ``preview.png`` (lit) and ``board_preview.png`` (unlit), plus ``preview.html``,
  which plays the animation in a browser.

The LEDs are an ordinary WS2812B strip: a flat tape, 10 mm wide. A flat strip
bends easily across its face but not sideways, so it cannot lie flat and
follow a drawing. On its edge, though, it follows any smooth curve. So each
line of the drawing is a printed channel with the strip standing on its edge
against one wall, LEDs shining across at the other wall. The light bounces
off the white walls and comes out through a translucent cap pressed into the
top, which glows as one even neon line.

The stars, Santa's eyes and his mittens are shapes rather than lines: a small
star- or dot-shaped box with one LED cut from the strip lying in the bottom,
under a translucent lid of the same shape. The moon is a filled crescent, lit
by strip running round the inside of its outer wall.

All of it screws to a flat 600 x 600 board (6 mm MDF or plywood, painted
black). Wires go straight back through a hole at each end of a run, and all the
wiring and the controller live on the back.

Neon lines cannot turn a sharp corner or cross each other, so the drawing is
made the way a neon bender would: single lines, smooth curves, a gap wherever
two lines would meet. Every line is checked for its tightest bend
(``--min-bend``) and every part for clearance to every other, and nothing is
written if a check fails.

The animation comes from having more than one Santa on the board and lighting
one at a time, like every animated neon sign. The two never overlap: the small
"hat peeking out" Santa sits inside the face of the big waving one, so when
one is lit the other is dark.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

import manifold3d as mf  # noqa: E402

from phonecase.threemf import Part, parts_to_3mf  # noqa: E402

SIZE = 600.0          # the board, mm
STEP = 1.5            # path sampling, mm
WHITE_PLA = (238, 238, 236)
BLACK = (30, 30, 32)
CLEAR = (235, 232, 222)


# --------------------------------------------------------------------------
# paths -- all in board coordinates: mm, origin top-left, y down (as the SVG)
# --------------------------------------------------------------------------

def resample(pts, closed=False, step=STEP) -> np.ndarray:
    """Evenly spaced points along a polyline."""
    p = np.asarray(pts, float)
    if closed:
        p = np.vstack([p, p[:1]])
    seg = np.linalg.norm(np.diff(p, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    n = max(2, int(round(s[-1] / step)) + 1)
    t = np.linspace(0, s[-1], n)
    out = np.column_stack([np.interp(t, s, p[:, 0]), np.interp(t, s, p[:, 1])])
    return out[:-1] if closed else out


def spline(*pts, closed=False) -> np.ndarray:
    """A Catmull-Rom curve through the points (centripetal, so no loops)."""
    p = [np.asarray(q, float) for q in pts]
    if closed:
        ext = [p[-1]] + p + [p[0], p[1]]
    else:
        ext = [2 * p[0] - p[1]] + p + [2 * p[-1] - p[-2]]
    out = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        t0 = 0.0
        t1 = t0 + np.linalg.norm(p1 - p0) ** 0.5
        t2 = t1 + np.linalg.norm(p2 - p1) ** 0.5
        t3 = t2 + np.linalg.norm(p3 - p2) ** 0.5
        for t in np.linspace(t1, t2, 40, endpoint=False):
            a1 = (t1 - t) / (t1 - t0) * p0 + (t - t0) / (t1 - t0) * p1
            a2 = (t2 - t) / (t2 - t1) * p1 + (t - t1) / (t2 - t1) * p2
            a3 = (t3 - t) / (t3 - t2) * p2 + (t - t2) / (t3 - t2) * p3
            b1 = (t2 - t) / (t2 - t0) * a1 + (t - t0) / (t2 - t0) * a2
            b2 = (t3 - t) / (t3 - t1) * a2 + (t - t1) / (t3 - t1) * a3
            out.append((t2 - t) / (t2 - t1) * b1 + (t - t1) / (t2 - t1) * b2)
    if not closed:
        out.append(p[-1])
    return resample(out, closed)


def arc(cx, cy, r, a0, a1) -> np.ndarray:
    """Degrees, measured as in the SVG (y down, so positive is clockwise)."""
    n = max(8, int(abs(a1 - a0) / 2))
    a = np.radians(np.linspace(a0, a1, n))
    return resample(np.column_stack([cx + r * np.cos(a), cy + r * np.sin(a)]))


def circle(cx, cy, r) -> np.ndarray:
    a = np.radians(np.arange(0, 360, 2.0))
    return resample(np.column_stack([cx + r * np.cos(a), cy + r * np.sin(a)]), closed=True)


def rounded(pts, r) -> np.ndarray:
    """A polyline with every corner filleted to radius r."""
    p = [np.asarray(q, float) for q in pts]
    out = [p[0]]
    for a, b, c in zip(p, p[1:], p[2:]):
        u = (a - b) / np.linalg.norm(a - b)
        v = (c - b) / np.linalg.norm(c - b)
        half = math.acos(float(np.clip(u @ v, -1, 1))) / 2
        d = r / math.tan(half)
        centre = b + (u + v) / np.linalg.norm(u + v) * (r / math.sin(half))
        p0, p1 = b + u * d, b + v * d
        a0 = math.atan2(*(p0 - centre)[::-1])
        a1 = math.atan2(*(p1 - centre)[::-1])
        da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
        for t in np.linspace(0, 1, 24):
            ang = a0 + da * t
            out.append(centre + r * np.array([math.cos(ang), math.sin(ang)]))
    out.append(p[-1])
    return resample(out)


def crescent(cx, cy, r, ix, iy, ir, tip_r=4.0) -> np.ndarray:
    """A crescent: a disc with a smaller one bitten out of it, tips rounded."""
    cs = (mf.CrossSection.circle(r, 180).translate((cx, cy))
          - mf.CrossSection.circle(ir, 180).translate((ix, iy)))
    cs = cs.offset(-tip_r, mf.JoinType.Round).offset(tip_r, mf.JoinType.Round)
    return np.array(cs.to_polygons()[0])


def inside_arc(cx, cy, r, ix, iy, keep_out) -> np.ndarray:
    """The part of a circle further than keep_out from (ix, iy): where strip
    can run round the inside of a crescent's outer wall."""
    ang = np.arange(0, 360, 0.5)
    pts = np.column_stack([cx + r * np.cos(np.radians(ang)), cy + r * np.sin(np.radians(ang))])
    ok = np.hypot(pts[:, 0] - ix, pts[:, 1] - iy) >= keep_out
    i = int(np.argmin(np.abs(ang - 180)))           # the run through the back of the moon
    lo, hi = i, i
    while ok[(lo - 1) % len(ang)] and (lo - 1) % len(ang) != i:
        lo -= 1
    while ok[(hi + 1) % len(ang)] and (hi + 1) % len(ang) != i:
        hi += 1
    return arc(cx, cy, r, ang[lo % len(ang)] - (360 if lo < 0 else 0), ang[hi % len(ang)])


# --------------------------------------------------------------------------
# the artwork
# --------------------------------------------------------------------------

@dataclass
class Stroke:
    """One run of strip: a single length, cut from the reel, with its own wires.
    Most are lines in a channel; one with a ``housing`` is a filled shape (that
    outline, board coordinates) lit by the strip running round its edge."""

    name: str
    pts: np.ndarray
    colour: str           # what the animation lights it, for the previews
    group: str            # scene / santa_up / santa_down
    closed: bool = False
    housing: np.ndarray | None = None

    @property
    def length(self) -> float:
        p = np.vstack([self.pts, self.pts[:1]]) if self.closed else self.pts
        return float(np.linalg.norm(np.diff(p, axis=0), axis=1).sum())


@dataclass
class Pixel:
    """One LED cut from the strip, in a small printed box of this shape under a
    translucent lid: a star, or a dot for eyes and mittens."""

    name: str
    x: float
    y: float
    shape: str = "star"   # star / dot
    colour: str = "#bfe3ff"
    group: str = "stars"


RED, WHITE, GOLD, ICE, BRICK = "#ff2a2a", "#fff4e8", "#ffb43c", "#bfe3ff", "#ff5a1f"


def artwork(a) -> tuple[list[Stroke], list[Pixel]]:
    """Santa, chimney, roof and moon, drawn as neon lines and shapes."""
    roof_y = lambda x: 560 - (x - 25) * 95 / 550           # noqa: E731
    c, rim = 370, 368              # Santa's centre line, the chimney's rim
    cl, cr = c - 72, c + 72        # chimney walls
    moon = (100, 106, 66)          # the moon's disc, and the bite out of it
    bite = (130, 94, 50)
    strip_in = a.wall_gap + a.strip_t / 2                   # strip centre from the wall
    strokes = [
        # --- the scene, always on
        Stroke("roof", resample([(30, roof_y(30)), (570, roof_y(570))]), WHITE, "scene"),
        Stroke("chimney", rounded([(cl, roof_y(cl) - 21), (cl, rim), (cr, rim),
                                   (cr, roof_y(cr) - 21)], 24), RED, "scene"),
        Stroke("brick_1", resample([(c - 50, 414), (c + 6, 414)]), BRICK, "scene"),
        Stroke("brick_2", resample([(c - 6, 456), (c + 50, 456)]), BRICK, "scene"),
        Stroke("moon", inside_arc(*moon[:2], moon[2] - strip_in, *bite[:2], bite[2] + 14),
               GOLD, "scene", housing=crescent(*moon, *bite)),

        # --- Santa up and waving
        Stroke("hat", spline((c - 72, 164), (c - 58, 106), (c - 22, 68), (c + 30, 56),
                             (c + 80, 70), (c + 104, 98), (c + 110, 122)), RED, "santa_up"),
        Stroke("hat_side", spline((c + 74, 164), (c + 70, 142), (c + 63, 122)), RED, "santa_up"),
        Stroke("pom", circle(c + 130, 160, 21), WHITE, "santa_up", closed=True),
        Stroke("brim", resample([(c - 90, 184), (c + 90, 184)]), WHITE, "santa_up"),
        Stroke("nose", circle(c, 252, 21), RED, "santa_up", closed=True),
        Stroke("beard_left", spline((c - 88, 206), (c - 102, 262), (c - 92, 316), (c - 70, 344)),
               WHITE, "santa_up"),
        Stroke("beard_right", spline((c + 88, 206), (c + 102, 262), (c + 92, 316), (c + 70, 344)),
               WHITE, "santa_up"),
        Stroke("arm_left", spline((c - 118, 360), (c - 146, 316), (c - 158, 266),
                                  (c - 150, 222)), RED, "santa_up"),
        Stroke("arm_right", spline((c + 118, 360), (c + 146, 316), (c + 160, 268),
                                   (c + 154, 232)), RED, "santa_up"),

        # --- Santa nearly gone: just his hat above the rim, its tip flopping
        # over. It sits in the lower half of the big Santa's face, so the two
        # never overlap.
        Stroke("hat_low", spline((c - 46, 344), (c - 42, 318), (c - 18, 300), (c + 12, 296),
                                 (c + 36, 306), (c + 48, 328)), RED, "santa_down"),
    ]
    pixels = [Pixel(f"star_{i + 1}", x, y) for i, (x, y) in enumerate(
        [(236, 56), (548, 56), (150, 228), (548, 344), (52, 320), (172, 420)])]
    pixels += [Pixel("eye_left", c - 40, 214, "dot", "#e8f4ff", "santa_up"),
               Pixel("eye_right", c + 40, 214, "dot", "#e8f4ff", "santa_up"),
               Pixel("mitten_left", c - 140, 190, "dot", WHITE, "santa_up"),
               Pixel("mitten_right", c + 168, 204, "dot", WHITE, "santa_up")]
    return strokes, pixels


# --------------------------------------------------------------------------
# lamps: the star and dot boxes
# --------------------------------------------------------------------------

def star_outline(R: float, inner=0.5, round_r=2.5) -> mf.CrossSection:
    pts = []
    for i in range(10):
        ang = math.pi / 2 + i * math.pi / 5
        rad = R if i % 2 == 0 else R * inner
        pts.append((rad * math.cos(ang), rad * math.sin(ang)))
    return (mf.CrossSection([pts]).offset(-round_r, mf.JoinType.Round)
            .offset(round_r, mf.JoinType.Round))


def lamp_cavity(a, px: Pixel, board=True) -> mf.CrossSection:
    """Inside of a lamp box, centred on 0. On the board (y down) the star is
    turned round so it still points up."""
    if px.shape == "dot":
        return mf.CrossSection.circle(a.dot_size / 2, 72)
    star = star_outline(a.star_size / 2)
    return star.rotate(180) if board else star


def lamp_r(a, px: Pixel) -> float:
    """Outer radius of a lamp box, walls included."""
    return (a.star_size if px.shape == "star" else a.dot_size) / 2 + a.wall


def lamp_outline(a, px: Pixel) -> mf.CrossSection:
    """What you see of a lamp from the front, in board coordinates."""
    return lamp_cavity(a, px).offset(a.wall, mf.JoinType.Round).translate((px.x, px.y))


def lamp_holes(a, px: Pixel) -> tuple[tuple, list[tuple]]:
    """(wire hole, [screw holes]) relative to the lamp centre, y up. The LED
    lies in the middle; the wires go down beside it, toward the top point."""
    if px.shape == "dot":
        off = a.dot_size / 2 - 5.5
        return (0.0, off), [(0.0, -off)]
    R = a.star_size / 2
    screws = [(0.55 * R * math.cos(math.radians(d)), 0.55 * R * math.sin(math.radians(d)))
              for d in (234, 306)]                   # the two lower points
    return (0.0, 0.6 * R), screws


# --------------------------------------------------------------------------
# where things are
# --------------------------------------------------------------------------

def wire_holes(a, strokes, pixels=()) -> list[dict]:
    """Where wires go through the board: under the slot at each end of a run
    (one for a closed loop), and beside the LED in each lamp."""
    out = []
    for s in strokes:
        ends = [(s.pts[0], s.pts[6], "in")] if s.closed else [
            (s.pts[0], s.pts[6], "in"), (s.pts[-1], s.pts[-7], "out")]
        for e, n, kind in ends:
            t = (n - e) / np.linalg.norm(n - e)
            h = e + t * (3 + a.slot_len / 2)
            out.append({"x": float(h[0]), "y": float(h[1]), "run": s.name, "end": kind})
    for px in pixels:
        (hx, hy), _ = lamp_holes(a, px)
        out.append({"x": px.x + hx, "y": px.y - hy, "run": px.name, "end": "in"})
    return out


def back_layout(a) -> dict:
    """The parts on the back, in front-of-board coordinates (seen from the
    front, as if the board were glass)."""
    m = a.standoff_x
    return {
        "cover": {"x": a.cover_x, "y": a.cover_y, "w": a.box_w + 8, "h": a.box_d + 8},
        "standoffs": [{"x": x, "y": y, "s": 48} for y in a.standoff_y
                      for x in (m, SIZE - m)],
    }


def footprints(a, strokes, pixels) -> list[tuple[str, np.ndarray, float]]:
    """Every part as (name, line, half-width): a channel is its centre line and
    half its width; a filled shape is the inside of its wall, plus the wall."""
    out = []
    for s in strokes:
        if s.housing is not None:
            out.append((s.name, resample(s.housing, closed=True), a.wall))
        else:
            out.append((s.name, s.pts, a.outer_w / 2))
    for px in pixels:
        loop = np.array(lamp_cavity(a, px).translate((px.x, px.y)).to_polygons()[0])
        out.append((px.name, resample(loop, closed=True), a.wall))
    return out


# --------------------------------------------------------------------------
# checks
# --------------------------------------------------------------------------

def tightest_bend(s: Stroke, span=6.0) -> float:
    """Smallest radius of the circle through points `span` mm apart."""
    k = max(1, int(round(span / STEP)))
    p = s.pts
    if s.closed:
        a, b, c = np.roll(p, k, 0), p, np.roll(p, -k, 0)
    else:
        a, b, c = p[:-2 * k], p[k:-k], p[2 * k:]
    ab = np.linalg.norm(b - a, axis=1)
    bc = np.linalg.norm(c - b, axis=1)
    ca = np.linalg.norm(a - c, axis=1)
    cross = np.abs((b - a)[:, 0] * (c - a)[:, 1] - (b - a)[:, 1] * (c - a)[:, 0])
    with np.errstate(divide="ignore", invalid="ignore"):
        r = ab * bc * ca / (2 * cross)
    return float(np.nanmin(np.where(cross < 1e-9, np.inf, r)))


def gap(a: np.ndarray, b: np.ndarray) -> float:
    d = np.linalg.norm(a[:, None, :] - b[None, :, :], axis=2)
    return float(d.min())


def check(a, strokes, pixels) -> list[str]:
    problems = []
    for s in strokes:
        r = tightest_bend(s)
        if r < a.min_bend - 0.5:
            problems.append(f"{s.name}: bends to r={r:.0f} mm, the strip needs {a.min_bend:.0f}")
    fps = footprints(a, strokes, pixels)
    for name, p, half in fps:
        if p.min() - half < a.margin or p.max() + half > SIZE - a.margin:
            problems.append(f"{name}: runs into the {a.margin:.0f} mm edge margin")
    for i, (n1, p1, h1) in enumerate(fps):
        for n2, p2, h2 in fps[i + 1:]:
            g = gap(p1, p2) - h1 - h2
            if g < a.min_gap:
                problems.append(f"{n1} / {n2}: {max(g, 0):.0f} mm apart, need {a.min_gap:.0f}")
    back = back_layout(a)
    holes = [(h["x"], h["y"], a.wire_hole / 2, h["run"]) for h in wire_holes(a, strokes, pixels)]
    boxes = [("cover", back["cover"]["x"], back["cover"]["y"], back["cover"]["w"],
              back["cover"]["h"])]
    boxes += [(f"standoff {i + 1}", so["x"], so["y"], so["s"], so["s"])
              for i, so in enumerate(back["standoffs"])]
    for name, cx, cy, w, h in boxes:
        for x, y, r, what in holes:
            if abs(x - cx) < w / 2 + r and abs(y - cy) < h / 2 + r:
                problems.append(f"{name} on the back covers the hole for {what}")
    return problems


# --------------------------------------------------------------------------
# geometry: channels and their caps
# --------------------------------------------------------------------------

def normals(p: np.ndarray, closed: bool) -> np.ndarray:
    d = np.roll(p, -1, 0) - np.roll(p, 1, 0) if closed else np.gradient(p, axis=0)
    d /= np.linalg.norm(d, axis=1)[:, None]
    return np.column_stack([-d[:, 1], d[:, 0]])


def ccw(poly: np.ndarray) -> np.ndarray:
    x, y = poly[:, 0], poly[:, 1]
    area = (x * np.roll(y, -1) - np.roll(x, -1) * y).sum()
    return poly if area > 0 else poly[::-1]


def band(p: np.ndarray, w: float, closed=False, ext0=0.0, ext1=0.0) -> mf.CrossSection:
    """The 2-D outline of a line of width w along p, ends squared off and
    optionally carried on past the ends by ext0 / ext1."""
    if closed:
        cs = mf.CrossSection([ccw(p).tolist()])
        return cs.offset(w / 2, mf.JoinType.Round) - cs.offset(-w / 2, mf.JoinType.Round)
    p = p.copy()
    t0 = (p[0] - p[1]) / np.linalg.norm(p[0] - p[1])
    t1 = (p[-1] - p[-2]) / np.linalg.norm(p[-1] - p[-2])
    p = np.vstack([p[0] + t0 * ext0, p[1:-1], p[-1] + t1 * ext1]) if len(p) > 2 else p
    n = normals(p, False)
    poly = np.vstack([p + n * w / 2, (p - n * w / 2)[::-1]])
    return mf.CrossSection([ccw(poly).tolist()])


@dataclass
class Piece:
    """One printed holder: a channel (a stroke, or a bed-sized part of a long
    one) or a filled shape, and the translucent cap that goes on it."""

    id: str
    stroke: Stroke
    pts: np.ndarray
    closed: bool
    end0: bool            # True where the strip ends here (closed end wall,
    end1: bool            # wire slot), False where the channel just butts
    tabs: list = field(default_factory=list)   # (root, centre) of each screw tab
    solid: object = None
    cap: object = None
    outline: object = None   # what it covers on the board, board coordinates


def split(s: Stroke, bed: float, pad: float) -> list[tuple[np.ndarray, bool, bool]]:
    """Cut a stroke into lengths whose footprint fits the bed."""
    def fits(q):
        span = q.max(0) - q.min(0) + 2 * pad
        return span.max() <= bed
    if fits(s.pts):
        return [(s.pts, not s.closed, not s.closed)]
    if s.closed:
        raise SystemExit(f"{s.name} is a closed loop bigger than the bed")
    n = 2
    while True:
        idx = np.linspace(0, len(s.pts) - 1, n + 1).round().astype(int)
        parts = [s.pts[i:j + 1] for i, j in zip(idx, idx[1:])]
        if all(fits(q) for q in parts):
            return [(q, k == 0, k == n - 1) for k, q in enumerate(parts)]
        n += 1


def place_tabs(a, piece: Piece, all_pts: np.ndarray):
    """Screw tabs along the channel, on whichever side has room."""
    p = piece.pts
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))])
    L = s[-1]
    if piece.closed:
        where = np.linspace(0, L, 4)[:-1] + L / 6
    else:
        n = max(2, int(math.ceil((L - 2 * a.tab_inset) / a.tab_spacing)) + 1)
        where = np.linspace(a.tab_inset, L - a.tab_inset, n) if L > 2 * a.tab_inset \
            else [L / 2]
    nrm = normals(p, piece.closed)
    off = a.outer_w / 2 + a.tab_r - 1.0
    need = a.tab_r + a.outer_w / 2 + 1.0
    out = []
    for k, sv in enumerate(where):
        i = int(np.argmin(np.abs(s - sv)))
        near = np.linalg.norm(p - p[i], axis=1) < off + a.tab_r + 3
        for side in ((1, -1) if k % 2 == 0 else (-1, 1)):
            c = p[i] + side * nrm[i] * off
            d = np.linalg.norm(all_pts - c, axis=1)
            mine = np.linalg.norm(all_pts[:, None, :] - p[near][None, :, :], axis=2).min(1) < 0.01
            if (d[~mine] >= need).all() and a.tab_r <= c.min() and c.max() <= SIZE - a.tab_r:
                out.append((tuple(p[i]), tuple(c)))
                break
    piece.tabs = out


def to3d(p: np.ndarray) -> np.ndarray:
    """Board coordinates (y down) to print coordinates (y up), unmirrored."""
    return np.column_stack([p[:, 0], SIZE - p[:, 1]])


def poly3d(p: np.ndarray) -> mf.CrossSection:
    return mf.CrossSection([ccw(to3d(np.asarray(p))).tolist()])


def lid(a, cavity: mf.CrossSection, outer: mf.CrossSection) -> mf.Manifold:
    """A translucent cap: a plate over the whole outline, with a thin rim
    underneath that presses into the cavity. Made the way up it sits, then
    turned over to print face down, so the face is the smooth side."""
    rim = cavity.offset(-a.fit, mf.JoinType.Round) - cavity.offset(
        -a.fit - a.rail_w, mf.JoinType.Round)
    body = rim.extrude(a.rail_h) + outer.extrude(a.cap_t).translate((0, 0, a.rail_h))
    return body.rotate((0, 180, 0))


def channel_solid(a, pc: Piece) -> mf.Manifold:
    p = to3d(pc.pts)
    wall = a.wall
    outer = band(p, a.outer_w, pc.closed, wall if pc.end0 else 0, wall if pc.end1 else 0)
    cavity = band(p, a.inner_w, pc.closed)
    body = outer.extrude(a.floor + a.depth) - cavity.extrude(a.depth + 1).translate((0, 0, a.floor))
    tabs, holes = [], []
    for root, c in pc.tabs:
        r3, c3 = to3d(np.array([root]))[0], to3d(np.array([c]))[0]
        disc = mf.CrossSection.circle(a.tab_r, 40).translate(tuple(c3))
        neck = mf.CrossSection.circle(a.tab_r * 0.8, 40).translate(tuple(r3))
        tabs.append(mf.CrossSection.batch_hull([disc, neck]))
        holes.append(mf.CrossSection.circle(a.screw_d / 2, 32).translate(tuple(c3)))
    if tabs:
        body = body + (mf.CrossSection.batch_boolean(tabs, mf.OpType.Add) - outer.offset(-0.01)
                       ).extrude(a.tab_t)
        body = body - mf.CrossSection.batch_boolean(holes, mf.OpType.Add).extrude(50).translate(
            (0, 0, -1))
    # wire slots through the floor where the strip ends
    for here, there, on in ((p[0], p[min(len(p) - 1, 6)], pc.end0),
                            (p[-1], p[max(0, len(p) - 7)], pc.end1)):
        if not on and not pc.closed:
            continue
        t = (there - here) / np.linalg.norm(there - here)
        a0, a1 = here + t * 3, here + t * (3 + a.slot_len)
        slot = mf.CrossSection.batch_hull([
            mf.CrossSection.circle(a.slot_w / 2, 24).translate(tuple(a0)),
            mf.CrossSection.circle(a.slot_w / 2, 24).translate(tuple(a1))])
        body = body - slot.extrude(a.floor + 2).translate((0, 0, -1))
        if pc.closed:
            break
    return body


def channel_cap(a, pc: Piece) -> mf.Manifold:
    p = to3d(pc.pts)
    outer = band(p, a.outer_w, pc.closed, a.wall if pc.end0 else 0, a.wall if pc.end1 else 0)
    return lid(a, band(p, a.inner_w, pc.closed), outer)


def countersunk(a, x: float, y: float, top: float) -> mf.Manifold:
    """A screw hole through a floor, countersunk from the inside."""
    hole = mf.Manifold.cylinder(top + 2, a.screw_d / 2, circular_segments=32).translate(
        (x, y, -1))
    sink = mf.Manifold.cylinder(1.6, a.screw_d / 2, a.screw_d / 2 + 1.6,
                                circular_segments=32).translate((x, y, top - 1.6))
    return hole + sink


def box_solid(a, cavity: mf.CrossSection, depth: float, holes: list, screws: list):
    """A shaped box: walls round `cavity`, a floor with wire holes and
    countersunk screw holes. All in print coordinates."""
    outer = cavity.offset(a.wall, mf.JoinType.Round)
    body = outer.extrude(a.lamp_floor + depth) - cavity.extrude(depth + 1).translate(
        (0, 0, a.lamp_floor))
    for x, y in holes:
        body = body - mf.Manifold.cylinder(a.lamp_floor + 2, a.slot_w / 2 + 0.75,
                                           circular_segments=32).translate((x, y, -1))
    for x, y in screws:
        body = body - countersunk(a, x, y, a.lamp_floor)
    return body


def housing_parts(a, s: Stroke, hole_xy: list) -> tuple[mf.Manifold, mf.Manifold]:
    """The moon: a crescent box with the strip round its outer wall, and its lid."""
    cav = poly3d(s.housing)
    # two screws in the fat middle of the crescent, clear of the strip
    centre = s.housing.mean(0)
    back = s.pts[len(s.pts) // 2]
    mid = back + (centre - back) * 0.55
    screws = to3d(np.array([mid + (0, -14), mid + (0, 14)]))
    holes = to3d(np.array(hole_xy))
    body = box_solid(a, cav, a.depth, [tuple(h) for h in holes], [tuple(q) for q in screws])
    return body, lid(a, cav, cav.offset(a.wall, mf.JoinType.Round))


def lamp_parts(a, px: Pixel) -> tuple[mf.Manifold, mf.Manifold]:
    """A star or dot box (print coordinates, centred on 0) and its lid."""
    cav = lamp_cavity(a, px, board=False)
    hole, screws = lamp_holes(a, px)
    body = box_solid(a, cav, a.lamp_depth, [hole], screws)
    return body, lid(a, cav, cav.offset(a.wall, mf.JoinType.Round))


def pieces(a, strokes, pixels) -> list[Piece]:
    all_pts = np.vstack([p for _, p, _ in footprints(a, strokes, pixels)])
    holes = wire_holes(a, strokes)
    out = []
    for s in strokes:
        if s.housing is not None:
            pc = Piece(s.name, s, s.pts, False, True, True)
            pc.solid, pc.cap = housing_parts(
                a, s, [(h["x"], h["y"]) for h in holes if h["run"] == s.name])
            pc.outline = mf.CrossSection([ccw(s.housing).tolist()]).offset(
                a.wall, mf.JoinType.Round)
            out.append(pc)
            continue
        cut = split(s, a.bed, a.outer_w / 2 + 2 * a.tab_r + 4)
        for k, (q, e0, e1) in enumerate(cut):
            pid = s.name if len(cut) == 1 else f"{s.name}_{k + 1}"
            pc = Piece(pid, s, q, s.closed, e0, e1)
            place_tabs(a, pc, all_pts)
            pc.solid = channel_solid(a, pc)
            pc.cap = channel_cap(a, pc)
            pc.outline = mf.CrossSection.batch_boolean(
                [band(q, a.outer_w, s.closed, a.wall if e0 else 0, a.wall if e1 else 0)] + [
                    mf.CrossSection.circle(a.tab_r, 24).translate(c) for _, c in pc.tabs],
                mf.OpType.Add)
            out.append(pc)
    return out


# --------------------------------------------------------------------------
# geometry: the parts on the back
# --------------------------------------------------------------------------

def cover(a) -> mf.Manifold:
    """An open box screwed over the controller on the back of the board."""
    W, D, H, t = a.box_w, a.box_d, a.box_h, 2.0
    outer = mf.CrossSection.square((W, D), center=True).offset(4, mf.JoinType.Round)
    inner = mf.CrossSection.square((W - 2 * t, D - 2 * t), center=True).offset(
        4 - t, mf.JoinType.Round)
    box = outer.extrude(H) - inner.extrude(H).translate((0, 0, t))
    # flanges with screw holes, at the open rim (which goes against the board)
    fl = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            c = (sx * (W / 2 + 6), sy * (D / 2 - 6))
            fl.append(mf.CrossSection.batch_hull([
                mf.CrossSection.circle(6, 40).translate(c),
                mf.CrossSection.circle(6, 40).translate((sx * (W / 2 - 2), c[1]))]))
    flange = mf.CrossSection.batch_boolean(fl, mf.OpType.Add).extrude(3).translate((0, 0, H - 3))
    box = box + flange
    for sx in (-1, 1):
        for sy in (-1, 1):
            box = box - mf.Manifold.cylinder(10, a.screw_d / 2, circular_segments=32).translate(
                (sx * (W / 2 + 6), sy * (D / 2 - 6), H - 5))
    # notches in the rim for the wires to come in along the board
    notch = mf.Manifold.cube((14, D + 20, 6)).translate((-7, -(D + 20) / 2, H - 6))
    for x in (-W / 2 + 20, 0, W / 2 - 20):
        box = box - notch.translate((x, 0, 0))
    # the DC jack and a USB slot in one end
    jack = mf.Manifold.cylinder(20, 4.0, circular_segments=40).rotate((0, 90, 0))
    box = box - jack.translate((W / 2 - 5, -D / 4, H / 2))
    usb = mf.Manifold.cube((20, 12, 7)).translate((-W / 2 - 10, D / 4 - 6, H / 2 - 3.5))
    return box - usb


def standoff(a) -> mf.Manifold:
    """Holds the sign off the wall; hangs on a screw head by a keyhole."""
    s, h = 40.0, a.standoff_h
    block = mf.CrossSection.square((s, s), center=True).offset(4, mf.JoinType.Round).extrude(h)
    # printed wall-side down: keyhole through the base, pocket above it
    key = mf.CrossSection.batch_hull([mf.CrossSection.circle(2.6, 32).translate((0, 6)),
                                      mf.CrossSection.circle(2.6, 32).translate((0, -6))])
    head = mf.CrossSection.circle(5.2, 40).translate((0, -6))
    pocket = mf.CrossSection.batch_hull([mf.CrossSection.circle(5.2, 40).translate((0, 6)),
                                         head])
    block = block - (key + head).extrude(3.2).translate((0, 0, -1)) \
        - pocket.extrude(6).translate((0, 0, 2.2))
    # two screws up into the back of the board, from inside a counterbored hole
    for x in (-13, 13):
        block = block - mf.Manifold.cylinder(h + 2, a.screw_d / 2, circular_segments=32).translate(
            (x, 13, -1))
        block = block - mf.Manifold.cylinder(h - 4, 3.8, circular_segments=32).translate(
            (x, 13, -1))
    return block


# --------------------------------------------------------------------------
# packing onto beds
# --------------------------------------------------------------------------

def best_rotation(m: mf.Manifold, bed: float) -> mf.Manifold:
    """Turn a part to the smallest rectangle that still fits the bed, long
    side along x so the shelves pack tight."""
    best = None
    for deg in range(0, 180, 3):
        r = m.rotate((0, 0, deg))
        x0, y0, _, x1, y1, _ = r.bounding_box()
        w, h = x1 - x0, y1 - y0
        fits = max(w, h) <= bed - 10
        key = (not fits, max(w, h) if not fits else w * h + (0 if w >= h else 1))
        if best is None or key < best[0]:
            best = (key, r)
    r = best[1]
    x0, y0, z0, x1, y1, _ = r.bounding_box()
    return r.translate((-x0, -y0, -z0))


def pack(items: list[tuple[str, mf.Manifold]], bed: float, gap=6.0) -> list[list]:
    """Shelf-pack parts onto as few beds as it takes."""
    items = sorted(((n, best_rotation(m, bed)) for n, m in items),
                   key=lambda it: -(it[1].bounding_box()[4]))
    plates = []
    for name, m in items:
        _, _, _, w, h, _ = m.bounding_box()
        for pl in plates:
            x, y, row_h = pl["cursor"]
            if x + w <= bed - 5:
                pl["parts"].append((name, m.translate((x, y, 0))))
                pl["cursor"] = (x + w + gap, y, max(row_h, h))
                break
            if y + row_h + gap + h <= bed - 5:
                y = y + row_h + gap
                pl["parts"].append((name, m.translate((5, y, 0))))
                pl["cursor"] = (5 + w + gap, y, h)
                break
        else:
            plates.append({"parts": [(name, m.translate((5, 5, 0)))],
                           "cursor": (5 + w + gap, 5, h)})
    return [pl["parts"] for pl in plates]

# --------------------------------------------------------------------------
# LEDs and wiring
# --------------------------------------------------------------------------

def led_count(a, s: Stroke) -> int:
    """LEDs in a run: whole LEDs that fit, leaving room at each end for the
    soldered wires."""
    usable = s.length - 2 * a.end_gap
    return max(1, int(usable // a.pitch))


GROUPS = ["scene", "stars", "santa_up", "santa_down"]


def data_chain(a, strokes, pixels) -> list:
    """The order the data line visits every run and lamp: always on to the
    nearest one from where the last ended, starting at the controller. An
    open run is turned round when its far end is the nearer one, so its data
    goes in there. Keeps the wiring on the back short and untangled."""
    todo = list(strokes) + list(pixels)
    here = np.array([a.cover_x, a.cover_y])
    chain = []
    while todo:
        best = None
        for item in todo:
            if isinstance(item, Pixel):
                ends = [(np.array([item.x, item.y]), False)]
            elif item.closed:
                ends = [(item.pts[0], False)]
            else:
                ends = [(item.pts[0], False), (item.pts[-1], True)]
            for at, flip in ends:
                d = float(np.linalg.norm(at - here))
                if best is None or d < best[0]:
                    best = (d, item, flip)
        _, item, flip = best
        todo.remove(item)
        if flip:
            item.pts = item.pts[::-1].copy()
        here = np.array([item.x, item.y]) if isinstance(item, Pixel) else item.pts[-1]
        chain.append(item)
    return chain


def layout_header(a, chain) -> tuple[str, list[dict]]:
    """The LED index of every segment, in data-line order."""
    rows, i = [], 0
    for s in chain:
        if isinstance(s, Pixel):
            rows.append({"name": s.name, "group": s.group, "colour": s.colour, "start": i,
                         "count": 1, "strip_mm": 0, "path_mm": 0})
            i += 1
            continue
        n = led_count(a, s)
        rows.append({"name": s.name, "group": s.group, "colour": s.colour, "start": i,
                     "count": n, "strip_mm": round(n * a.pitch), "path_mm": round(s.length)})
        i += n
    lines = ["// Generated by neonsign/make_neon_sign.py: the LED index of every",
             "// segment, in the order the data line is wired. Edit the artwork",
             "// there and regenerate rather than editing this.",
             "#pragma once", "#include <stdint.h>", "",
             f"#define NUM_LEDS {i}", "",
             "enum Group : uint8_t { " + ", ".join(f"G_{g.upper()}" for g in GROUPS) + " };", "",
             "struct Segment {", "  const char *name;", "  uint16_t start, count;",
             "  uint32_t colour;  // 0xRRGGBB", "  Group group;", "};", "",
             "enum SegmentId : uint8_t {"]
    lines += [f"  {r['name'].upper()}," for r in rows]
    lines += ["  NUM_SEGMENTS", "};", "", "const Segment SEGMENTS[NUM_SEGMENTS] = {"]
    for r in rows:
        what = f"{r['count']} LEDs, {r['strip_mm']} mm of strip" if r["strip_mm"] \
            else "1 LED in a lamp box"
        lines.append(f"  {{\"{r['name']}\", {r['start']:3d}, {r['count']:2d}, "
                     f"0x{r['colour'][1:].upper()}, G_{r['group'].upper()}}},  // {what}")
    lines += ["};", ""]
    return "\n".join(lines), rows


# --------------------------------------------------------------------------
# drawings: template, previews
# --------------------------------------------------------------------------

def svg_loops(cs: mf.CrossSection) -> str:
    return "".join("M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in loop) + " Z"
                   for loop in cs.to_polygons())


def template_svg(a, strokes, pixels, pcs) -> str:
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE}mm" height="{SIZE}mm" '
           f'viewBox="0 0 {SIZE} {SIZE}" font-family="Helvetica, Arial, sans-serif">',
           f'<rect x="0" y="0" width="{SIZE}" height="{SIZE}" fill="none" stroke="#000" '
           f'stroke-width="0.5"/>']
    for pc in pcs:
        out.append(f'<path d="{svg_loops(pc.outline)}" fill="#eee" fill-rule="evenodd" '
                   f'stroke="#888" stroke-width="0.4"/>')
        for _, (cx, cy) in pc.tabs:
            out.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{a.screw_d / 2}" fill="none" '
                       f'stroke="#000" stroke-width="0.3"/>'
                       f'<path d="M{cx - 2:.2f},{cy:.2f}h4M{cx:.2f},{cy - 2:.2f}v4" '
                       f'stroke="#000" stroke-width="0.2"/>')
        m = pc.pts[len(pc.pts) // 2]
        out.append(f'<text x="{m[0] + 10:.1f}" y="{m[1] - 10:.1f}" font-size="5">{pc.id}</text>')
    for px in pixels:
        out.append(f'<path d="{svg_loops(lamp_outline(a, px))}" fill="#eee" stroke="#888" '
                   f'stroke-width="0.4"/><text x="{px.x + lamp_r(a, px) + 2:.1f}" '
                   f'y="{px.y + 2:.1f}" font-size="5">{px.name}</text>')
    for h in wire_holes(a, strokes, pixels):     # drill these through the board
        out.append(f'<circle cx="{h["x"]:.2f}" cy="{h["y"]:.2f}" r="{a.wire_hole / 2}" '
                   f'fill="#ffd0d0" stroke="#d00" stroke-width="0.4"/>')
    back = back_layout(a)               # on the back: dashed, for placing them
    for r in [back["cover"]] + [dict(so, w=so["s"], h=so["s"]) for so in back["standoffs"]]:
        out.append(f'<rect x="{r["x"] - r["w"] / 2:.1f}" y="{r["y"] - r["h"] / 2:.1f}" '
                   f'width="{r["w"]:.1f}" height="{r["h"]:.1f}" fill="none" stroke="#06c" '
                   f'stroke-width="0.4" stroke-dasharray="3 2"/>')
    out.append(f'<text x="{back["cover"]["x"] - 30:.0f}" y="{back["cover"]["y"]:.0f}" '
               f'font-size="5" fill="#06c">controller cover (on the back)</text>')
    # a scale bar, to check the print came out 1:1
    out.append('<path d="M20,585h100M20,582v6M120,582v6" stroke="#000" stroke-width="0.5"/>'
               '<text x="20" y="579" font-size="5">100 mm -- measure me</text>'
               f'<text x="200" y="590" font-size="5">red: drill {a.wire_hole:.0f} mm through '
               '(wires)   crosshairs: tab screws   grey: where each printed part sits</text>')
    out.append("</svg>")
    return "\n".join(out)


def _fill(img, cs: mf.CrossSection, px: float, rgb):
    """Fill a cross-section's area (holes kept) on a PIL image."""
    from PIL import Image, ImageChops, ImageDraw

    mask = Image.new("1", img.size, 0)
    for loop in cs.to_polygons():
        one = Image.new("1", img.size, 0)
        ImageDraw.Draw(one).polygon([(x * px, y * px) for x, y in loop], fill=1)
        mask = ImageChops.logical_xor(mask, one)
    img.paste(rgb, mask=mask)


def raster(a, strokes, pixels, pcs, px: float, lit: bool, on=None):
    """The front of the sign as an image, px pixels per mm."""
    from PIL import Image, ImageChops, ImageFilter

    W = int(SIZE * px)
    img = Image.new("RGB", (W, W), (14, 14, 18) if lit else (40, 40, 44))
    if not lit:
        for pc in pcs:
            _fill(img, pc.outline, px, (205, 205, 200))   # white channel and its tabs
            cap = (mf.CrossSection([ccw(pc.stroke.housing).tolist()]).offset(a.wall)
                   if pc.stroke.housing is not None else band(pc.pts, a.outer_w, pc.closed))
            _fill(img, cap, px, CLEAR)
        for st in pixels:
            _fill(img, lamp_outline(a, st), px, CLEAR)
        return img
    glow = Image.new("RGB", (W, W), (0, 0, 0))
    core = Image.new("RGB", (W, W), (0, 0, 0))
    rgb = lambda h: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))   # noqa: E731
    pale = lambda c: tuple(min(255, int(v * 0.4 + 160)) for v in c)  # noqa: E731
    for s in strokes:
        if on is not None and s.group not in on:
            continue
        c = rgb(s.colour)
        shape = (mf.CrossSection([ccw(s.housing).tolist()]).offset(a.wall)
                 if s.housing is not None else band(s.pts, a.outer_w, s.closed))
        _fill(glow, shape, px, c)
        _fill(core, shape.offset(-2), px, pale(c))
    for st in pixels:
        if on is not None and st.group not in on and st.group != "stars":
            continue
        _fill(glow, lamp_outline(a, st), px, rgb(st.colour))
        _fill(core, lamp_outline(a, st).offset(-2), px, pale(rgb(st.colour)))
    glow = glow.filter(ImageFilter.GaussianBlur(9 * px))
    img = ImageChops.add(img, glow)
    return ImageChops.lighter(img, core.filter(ImageFilter.GaussianBlur(0.8 * px)))


def tiled_pdf(a, strokes, pixels, pcs, path: Path, dpi=150):
    """The 1:1 template on A4 pages, with overlap to tape them together."""
    from PIL import Image, ImageDraw

    px = dpi / 25.4
    full = Image.new("RGB", (int(SIZE * px), int(SIZE * px)), "white")
    d = ImageDraw.Draw(full)
    lw = max(1, int(0.4 * px))
    d.rectangle([0, 0, full.width - 1, full.height - 1], outline="black", width=lw)
    shapes = [(pc.outline, pc.id, pc.pts[len(pc.pts) // 2]) for pc in pcs]
    shapes += [(lamp_outline(a, st), st.name, (st.x + lamp_r(a, st), st.y)) for st in pixels]
    for cs, name, at in shapes:
        for loop in cs.to_polygons():
            d.polygon([(x * px, y * px) for x, y in loop], outline=(120, 120, 120), width=lw)
        d.text((at[0] * px + 8 * px, at[1] * px - 10 * px), name, fill="black")
    for pc in pcs:
        for _, (cx, cy) in pc.tabs:
            r = a.screw_d / 2 * px
            d.ellipse([cx * px - r, cy * px - r, cx * px + r, cy * px + r], outline="black",
                      width=lw)
            d.line([(cx * px - 2 * px, cy * px), (cx * px + 2 * px, cy * px)], fill="black")
            d.line([(cx * px, cy * px - 2 * px), (cx * px, cy * px + 2 * px)], fill="black")
    for hole in wire_holes(a, strokes, pixels):
        h = np.array([hole["x"], hole["y"]]) * px
        r = a.wire_hole / 2 * px
        d.ellipse([h[0] - r, h[1] - r, h[0] + r, h[1] + r], fill=(255, 190, 190),
                  outline=(200, 0, 0), width=lw)
    d.line([(20 * px, 585 * px), (120 * px, 585 * px)], fill="black", width=lw)
    d.text((20 * px, 575 * px), "100 mm -- check this before you drill", fill="black")

    pw, ph = 210 * px, 297 * px
    cw, ch = 180.0, 267.0                         # content per page, mm
    step_x, step_y = cw - 10, ch - 10             # 10 mm overlap
    pages = []
    nx = math.ceil((SIZE - 10) / step_x)
    ny = math.ceil((SIZE - 10) / step_y)
    for j in range(ny):
        for i in range(nx):
            x0, y0 = i * step_x, j * step_y
            tile = full.crop((int(x0 * px), int(y0 * px),
                              int((x0 + cw) * px), int((y0 + ch) * px)))
            page = Image.new("RGB", (int(pw), int(ph)), "white")
            page.paste(tile, (int(15 * px), int(20 * px)))
            pd = ImageDraw.Draw(page)
            pd.rectangle([15 * px, 20 * px, 15 * px + cw * px, 20 * px + ch * px],
                         outline=(150, 150, 150))
            pd.text((15 * px, 8 * px), f"neon sign template  row {j + 1} / col {i + 1}   "
                    f"(overlap 10 mm, print at 100% / actual size)", fill="black")
            pages.append(page)
    pages[0].save(path, save_all=True, append_images=pages[1:], resolution=dpi)
    return len(pages)


def preview_html(a, strokes, pixels, pcs, rows, stats) -> str:
    """The animation, LED by LED, plus the build sheet, as one page."""
    rd = lambda p: [[round(float(x), 1), round(float(y), 1)] for x, y in p]  # noqa: E731
    data = {
        "size": SIZE,
        "strokes": [{"name": s.name, "closed": s.closed, "pts": rd(s.pts[::2]),
                     "fill": rd(mf.CrossSection([ccw(s.housing).tolist()]).offset(
                         a.wall, mf.JoinType.Round).to_polygons()[0])
                     if s.housing is not None else None} for s in strokes],
        "pixels": [{"name": st.name, "x": st.x, "y": st.y,
                    "outline": rd(lamp_outline(a, st).to_polygons()[0])} for st in pixels],
        "leds": rows,
        "pieces": [{"id": pc.id, "run": pc.stroke.name,
                    "outline": [rd(loop) for loop in pc.outline.to_polygons()],
                    "tabs": rd([c for _, c in pc.tabs])} for pc in pcs],
        "holes": [dict(h, x=round(h["x"], 1), y=round(h["y"], 1))
                  for h in wire_holes(a, strokes, pixels)],
        "back": back_layout(a),
        "dims": {k: round(getattr(a, k), 1) for k in (
            "strip_w", "strip_t", "pitch", "inner_w", "outer_w", "wall", "floor", "depth",
            "cap_t", "tab_t", "screw_d", "wire_hole", "standoff_h", "box_h", "min_bend", "bed",
            "star_size", "dot_size", "lamp_depth")},
        "stats": stats,
    }
    return (HERE / "preview_template.html").read_text().replace(
        "/*DATA*/null", json.dumps(data, separators=(",", ":")))


# --------------------------------------------------------------------------

def build_parser():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", type=Path, default=HERE / "example")
    g = p.add_argument_group("LED strip (mm)")
    g.add_argument("--strip-w", type=float, default=10, help="width of the strip")
    g.add_argument("--strip-t", type=float, default=3,
                   help="thickness of the strip with its LEDs and tape")
    g.add_argument("--pitch", type=float, default=15, help="LED centre to centre")
    g.add_argument("--end-gap", type=float, default=5,
                   help="room left at each end of a run for the soldered wires")
    g.add_argument("--min-bend", type=float, default=20,
                   help="tightest bend radius for the strip on its edge")
    g = p.add_argument_group("channel (mm)")
    g.add_argument("--inner-w", type=float, default=12,
                   help="inside width: the strip on one wall, and room for the light to spread")
    g.add_argument("--wall", type=float, default=1.6)
    g.add_argument("--floor", type=float, default=1.2)
    g.add_argument("--depth", type=float, default=12.5,
                   help="inside height: the strip stands 10 mm, the cap's rim drops 1.6")
    g.add_argument("--wall-gap", type=float, default=0.5, help="strip to wall, for the moon")
    g.add_argument("--cap-t", type=float, default=1.0, help="translucent cap thickness")
    g.add_argument("--rail-h", type=float, default=1.6, help="cap rim height")
    g.add_argument("--rail-w", type=float, default=1.0, help="cap rim thickness")
    g.add_argument("--fit", type=float, default=0.25, help="cap rim clearance")
    g.add_argument("--min-gap", type=float, default=3,
                   help="space between neighbouring parts")
    g.add_argument("--tab-r", type=float, default=6)
    g.add_argument("--tab-t", type=float, default=2.4)
    g.add_argument("--tab-spacing", type=float, default=110)
    g.add_argument("--tab-inset", type=float, default=14)
    g.add_argument("--screw-d", type=float, default=3.4, help="hole for the screws")
    g.add_argument("--slot-w", type=float, default=5.5, help="wire slot in the floor")
    g.add_argument("--slot-len", type=float, default=9)
    g.add_argument("--wire-hole", type=float, default=8, help="hole through the board")
    g = p.add_argument_group("printer")
    g.add_argument("--bed", type=float, default=220, help="usable bed size, mm")
    g = p.add_argument_group("lamps, back parts (mm)")
    g.add_argument("--star-size", type=float, default=56, help="star tip to tip, inside")
    g.add_argument("--dot-size", type=float, default=30, help="eyes and mittens, inside")
    g.add_argument("--lamp-depth", type=float, default=16,
                   help="LED to lid in a star or dot: deeper is a softer glow")
    g.add_argument("--lamp-floor", type=float, default=2.0)
    g.add_argument("--box-w", type=float, default=110)
    g.add_argument("--box-d", type=float, default=70)
    g.add_argument("--box-h", type=float, default=32)
    g.add_argument("--standoff-h", type=float, default=40)
    g.add_argument("--standoff-x", type=float, default=60,
                   help="standoff centres from the left and right edges")
    g.add_argument("--standoff-y", type=float, nargs=2, default=[110, 500],
                   help="heights of the top (hanging) pair and the bottom pair")
    g.add_argument("--cover-x", type=float, default=150, help="controller cover centre")
    g.add_argument("--cover-y", type=float, default=468)
    g.add_argument("--margin", type=float, default=20, help="keep artwork this far from the edge")
    g.add_argument("--check-only", action="store_true")
    return p


def main(argv=None) -> int:
    a = build_parser().parse_args(argv)
    a.outer_w = a.inner_w + 2 * a.wall

    strokes, pixels = artwork(a)
    problems = check(a, strokes, pixels)
    total = sum(led_count(a, s) for s in strokes) + len(pixels)
    strip = (sum(led_count(a, s) for s in strokes) + len(pixels)) * a.pitch / 1000
    print(f"neon sign: {SIZE:.0f} x {SIZE:.0f} mm, {len(strokes)} runs of strip "
          f"and {len(pixels)} lamps, {total} LEDs ({strip:.2f} m of strip)")
    for s in strokes:
        print(f"  {s.name:<12} {s.length:6.0f} mm  {led_count(a, s):3d} LEDs  "
              f"tightest bend r={tightest_bend(s):.0f} mm")
    if problems:
        print("\nNOT written -- the drawing does not fit:")
        for msg in problems:
            print("  " + msg)
        return 1
    print("  checks         OK (bends, clearances, margins)")
    if a.check_only:
        return 0

    out = a.out
    out.mkdir(parents=True, exist_ok=True)
    for old in list(out.glob("channels_plate_*.3mf")) + list(out.glob("diffusers_plate_*.3mf")) \
            + list(out.glob("pixel_caps.3mf")):
        old.unlink()                             # so a smaller run leaves no stale plates
    chain = data_chain(a, strokes, pixels)       # may turn runs round, so first
    pcs = pieces(a, strokes, pixels)
    lamps = [(st.name, *lamp_parts(a, st)) for st in pixels]
    print(f"  parts          {len(pcs)} channel pieces and shapes, {len(lamps)} lamp boxes")

    holders = [(pc.id, pc.solid) for pc in pcs] + [(n, b) for n, b, _ in lamps]
    plates = pack(holders, a.bed)
    for k, plate in enumerate(plates, 1):
        (out / f"channels_plate_{k}.3mf").write_bytes(parts_to_3mf(
            [Part(n, 1, WHITE_PLA, m) for n, m in plate], name=f"neon channels {k}"))
    covers = [(pc.id + "_cap", pc.cap) for pc in pcs] + [(n + "_lid", c) for n, _, c in lamps]
    dplates = pack(covers, a.bed)
    for k, plate in enumerate(dplates, 1):
        (out / f"diffusers_plate_{k}.3mf").write_bytes(parts_to_3mf(
            [Part(n, 1, CLEAR, m) for n, m in plate], name=f"neon diffusers {k}"))
    print(f"  plates         {len(plates)} white + {len(dplates)} translucent, "
          f"{a.bed:.0f} mm bed")
    back = pack([("cover", cover(a))] + [(f"standoff{i}", standoff(a)) for i in range(1, 5)],
                a.bed)
    for k, plate in enumerate(back, 1):
        name = "back_parts.3mf" if len(back) == 1 else f"back_parts_{k}.3mf"
        (out / name).write_bytes(parts_to_3mf([Part(n, 1, BLACK, m) for n, m in plate],
                                              name="back parts"))

    header, rows = layout_header(a, chain)
    (out / "neon_layout.h").write_text(header)
    (HERE / "firmware" / "santa_neon" / "neon_layout.h").write_text(header)
    (out / "template.svg").write_text(template_svg(a, strokes, pixels, pcs))
    n = tiled_pdf(a, strokes, pixels, pcs, out / "template_a4.pdf")
    raster(a, strokes, pixels, pcs, 1.6, lit=True, on={"scene", "santa_up"}).save(
        out / "preview.png")
    raster(a, strokes, pixels, pcs, 1.6, lit=False).save(out / "board_preview.png")
    grams = sum(float(m.volume()) for _, m in holders) * 1.24 / 1000
    grams_d = sum(float(m.volume()) for _, m in covers) * 1.27 / 1000
    stats = {"leds": total, "strip_m": round(strip, 2), "runs": len(strokes),
             "pixels": len(pixels), "pieces": len(pcs), "plates": len(plates),
             "dplates": len(dplates), "grams": round(grams), "grams_d": round(grams_d),
             "pages": n}
    (out / "preview.html").write_text(preview_html(a, strokes, pixels, pcs, rows, stats))
    print(f"  filament       ~{grams:.0f} g white, ~{grams_d:.0f} g translucent")
    print(f"  template       template.svg, template_a4.pdf ({n} pages)")
    print(f"  -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
