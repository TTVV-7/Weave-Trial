#!/usr/bin/env python3
"""A 600 x 600 mm animated LED neon sign: Santa going down the chimney.

    python neonsign/make_neon_sign.py
    python neonsign/make_neon_sign.py --bed 180 --min-bend 25 --out out/neon

writes ``neonsign/example/`` (or ``--out``):

* ``channels_plate_N.3mf`` -- the printed channels that hold the LED neon flex,
  packed onto beds of ``--bed`` mm. Print them in black.
* ``pixel_caps.3mf`` -- diffusers for the single pixels: stars, and Santa's
  eyes. Print them in white or natural (translucent) PETG.
* ``back_parts.3mf`` -- the electronics cover and four wall standoffs.
* ``template.svg`` -- the board at 1:1: where every channel goes, and every hole
  to drill. ``template_a4.pdf`` is the same thing tiled onto A4 pages.
* ``neon_layout.h`` -- the LED index of every segment, for the sketch in
  ``firmware/``.
* ``preview.png`` (lit) and ``board_preview.png`` (unlit), plus ``preview.html``,
  which plays the animation in a browser.

The sign is a flat 600 x 600 board (6 mm MDF or plywood, painted black) with
the artwork laid on it in "LED neon flex": a silicone tube, 6 x 12 mm, with
addressable WS2812B LEDs inside, that lights from its narrow face and bends
sideways. The flex sits in printed U-channels screwed to the board. Its wires
go straight back through a hole at each end, and all the wiring and the
controller live on the back.

Neon flex cannot turn a sharp corner and cannot cross itself, so the artwork
is drawn the way a neon bender would: single lines, smooth curves, a gap
wherever two lines would meet. Every stroke is checked for its tightest bend
(``--min-bend``) and for clearance to every other stroke, and nothing is
written if a check fails.

The animation comes from having more than one Santa on the board and lighting
one at a time, like every animated neon sign. The two never overlap: the small
"hat peeking out" Santa sits inside the face of the big waving one, so when
one is lit the other is dark and invisible.
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


# --------------------------------------------------------------------------
# the artwork
# --------------------------------------------------------------------------

@dataclass
class Stroke:
    """One run of neon flex: a single piece, cut to length, with its own wires."""

    name: str
    pts: np.ndarray
    colour: str           # what the animation lights it, for the previews
    group: str            # scene / santa_up / santa_down
    closed: bool = False

    @property
    def length(self) -> float:
        p = np.vstack([self.pts, self.pts[:1]]) if self.closed else self.pts
        return float(np.linalg.norm(np.diff(p, axis=0), axis=1).sum())


@dataclass
class Pixel:
    """A single 12 mm pixel pushed through the board, under a printed cap."""

    name: str
    x: float
    y: float
    shape: str = "star"   # star / dot
    colour: str = "#bfe3ff"
    group: str = "stars"


RED, WHITE, GOLD, ICE, BRICK = "#ff2a2a", "#fff4e8", "#ffb43c", "#bfe3ff", "#ff5a1f"


def artwork() -> tuple[list[Stroke], list[Pixel]]:
    """Santa, chimney, roof and moon, drawn as neon strokes."""
    roof_y = lambda x: 560 - (x - 25) * 95 / 550           # noqa: E731
    c, rim = 370, 352              # Santa's centre line, the chimney's rim
    cl, cr = c - 70, c + 70        # chimney walls
    strokes = [
        # --- the scene, always on
        Stroke("roof", resample([(25, roof_y(25)), (575, roof_y(575))]), WHITE, "scene"),
        Stroke("chimney", rounded([(cl, roof_y(cl) - 17), (cl, rim), (cr, rim),
                                   (cr, roof_y(cr) - 17)], 22), RED, "scene"),
        Stroke("brick_1", resample([(c - 52, 402), (c + 8, 402)]), BRICK, "scene"),
        Stroke("brick_2", resample([(c - 8, 446), (c + 52, 446)]), BRICK, "scene"),
        Stroke("moon_outer", arc(110, 110, 62, 55, 305), GOLD, "scene"),
        Stroke("moon_inner", arc(124.2, 110, 41.2, 72, 288), GOLD, "scene"),

        # --- Santa up and waving
        Stroke("hat", spline((c - 70, 172), (c - 56, 112), (c - 22, 74), (c + 30, 62),
                             (c + 78, 76), (c + 102, 104), (c + 108, 128)), RED, "santa_up"),
        Stroke("hat_side", spline((c + 72, 172), (c + 68, 146), (c + 60, 124)), RED, "santa_up"),
        Stroke("pom", circle(c + 112, 166, 20), WHITE, "santa_up", closed=True),
        Stroke("brim", resample([(c - 86, 188), (c + 86, 188)]), WHITE, "santa_up"),
        Stroke("nose", circle(c, 248, 20), RED, "santa_up", closed=True),
        Stroke("beard_left", spline((c - 82, 206), (c - 96, 262), (c - 84, 316), (c - 60, 336)),
               WHITE, "santa_up"),
        Stroke("beard_right", spline((c + 82, 206), (c + 96, 262), (c + 84, 316), (c + 60, 336)),
               WHITE, "santa_up"),
        Stroke("arm_left", spline((c - 104, 346), (c - 132, 304), (c - 144, 256),
                                  (c - 134, 214)), RED, "santa_up"),
        Stroke("arm_right", spline((c + 104, 346), (c + 132, 304), (c + 146, 262),
                                   (c + 142, 222)), RED, "santa_up"),

        # --- Santa nearly gone: just his hat above the rim. It sits in the
        # lower half of the big Santa's face, so the two never overlap.
        Stroke("hat_low", spline((c - 46, 338), (c - 40, 306), (c - 14, 290), (c + 18, 289),
                                 (c + 40, 302)), RED, "santa_down"),
    ]
    pixels = [Pixel(f"star_{i + 1}", x, y) for i, (x, y) in enumerate(
        [(232, 52), (565, 52), (196, 200), (566, 272), (60, 300), (182, 400)])]
    pixels += [Pixel("eye_left", c - 34, 222, "dot", "#e8f4ff", "santa_up"),
               Pixel("eye_right", c + 34, 222, "dot", "#e8f4ff", "santa_up"),
               Pixel("mitten_left", c - 126, 188, "dot", WHITE, "santa_up"),
               Pixel("mitten_right", c + 146, 200, "dot", WHITE, "santa_up"),
               Pixel("pom_low", c + 30, 324, "dot", WHITE, "santa_down")]
    return strokes, pixels


def wire_holes(a, strokes) -> list[dict]:
    """Where each run's wires go through the board: under the slot in the
    channel floor, one at each end (one for a closed loop)."""
    out = []
    for s in strokes:
        ends = [(s.pts[0], s.pts[6], "in")] if s.closed else [
            (s.pts[0], s.pts[6], "in"), (s.pts[-1], s.pts[-7], "out")]
        for e, n, kind in ends:
            t = (n - e) / np.linalg.norm(n - e)
            h = e + t * (3 + a.slot_len / 2)
            out.append({"x": float(h[0]), "y": float(h[1]), "run": s.name, "end": kind})
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
    clear = a.outer_w + a.min_gap                  # centre to centre
    for s in strokes:
        r = tightest_bend(s)
        if r < a.min_bend - 0.5:
            problems.append(f"{s.name}: bends to r={r:.0f} mm, flex allows {a.min_bend:.0f}")
        if s.pts.min() < a.margin or s.pts.max() > SIZE - a.margin:
            problems.append(f"{s.name}: runs into the {a.margin:.0f} mm edge margin")
    for i, s in enumerate(strokes):
        for t in strokes[i + 1:]:
            g = gap(s.pts, t.pts)
            if g < clear:
                problems.append(f"{s.name} / {t.name}: {g:.0f} mm apart, "
                                f"channels need {clear:.0f}")
    for k, st in enumerate(pixels):
        p = np.array([[st.x, st.y]])
        for s in strokes:
            g = gap(p, s.pts)
            if g < cap_r(a, st) + a.outer_w / 2 + a.min_gap:
                problems.append(f"{st.name} is {g:.0f} mm from {s.name}")
        for o in pixels[k + 1:]:
            if math.dist((st.x, st.y), (o.x, o.y)) < cap_r(a, st) + cap_r(a, o) + a.min_gap:
                problems.append(f"{st.name} overlaps {o.name}")
    back = back_layout(a)
    holes = [(h["x"], h["y"], a.wire_hole / 2, h["run"]) for h in wire_holes(a, strokes)]
    holes += [(st.x, st.y, a.pixel_d / 2, st.name) for st in pixels]
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
# geometry: channels
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
    """One printed channel: a stroke, or a bed-sized part of a long one."""

    id: str
    stroke: Stroke
    pts: np.ndarray
    closed: bool
    end0: bool            # True where the flex ends here (closed end wall,
    end1: bool            # wire slot), False where the channel just butts
    tabs: list = field(default_factory=list)   # (x, y) screw holes
    solid: object = None


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
    # wire slots through the floor where the flex ends
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


def pieces(a, strokes) -> list[Piece]:
    all_pts = np.vstack([s.pts for s in strokes])
    out = []
    for s in strokes:
        cut = split(s, a.bed, a.outer_w / 2 + 2 * a.tab_r + 4)
        for k, (q, e0, e1) in enumerate(cut):
            pid = s.name if len(cut) == 1 else f"{s.name}_{k + 1}"
            pc = Piece(pid, s, q, s.closed, e0, e1)
            place_tabs(a, pc, all_pts)
            pc.solid = channel_solid(a, pc)
            out.append(pc)
    return out


# --------------------------------------------------------------------------
# geometry: star caps and the parts on the back
# --------------------------------------------------------------------------

def star_outline(R: float, inner=0.5, round_r=2.5) -> mf.CrossSection:
    pts = []
    for i in range(10):
        ang = math.pi / 2 + i * math.pi / 5
        rad = R if i % 2 == 0 else R * inner
        pts.append((rad * math.cos(ang), rad * math.sin(ang)))
    return (mf.CrossSection([pts]).offset(-round_r, mf.JoinType.Round)
            .offset(round_r, mf.JoinType.Round))


def cap_r(a, px: Pixel) -> float:
    return (a.star_size if px.shape == "star" else a.dot_size) / 2


def cap_outline(a, px: Pixel, board=True) -> mf.CrossSection:
    """The cap's face; on the board (y down) the star is turned to point up."""
    if px.shape == "dot":
        return mf.CrossSection.circle(a.dot_size / 2, 64)
    star = star_outline(a.star_size / 2)
    return star.rotate(180) if board else star


def pixel_cap(a, px: Pixel) -> mf.Manifold:
    """A translucent cap that a 12 mm pixel pushes into from behind the board."""
    face = cap_outline(a, px, board=False)
    body = face.extrude(a.star_h)
    pocket = mf.CrossSection.circle(a.pixel_d / 2 + 0.2, 48).extrude(a.star_h - a.star_face)
    body = body - pocket
    # it sits face up on the bed; flip so the face is on top when printed
    # face down instead: the face is the first layers, the smoothest finish
    return body.mirror((0, 0, 1)).translate((0, 0, a.star_h))


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
    """LEDs in the flex for a stroke: whole cut sections, minus the end caps."""
    usable = s.length - (0 if s.closed else 2 * a.end_cap) - (2 * a.end_cap if s.closed else 0)
    sections = int(usable // (a.pitch * a.cut_every))
    return sections * a.cut_every


GROUPS = ["scene", "stars", "santa_up", "santa_down"]


def data_chain(a, strokes, pixels) -> list:
    """The order the data line visits every run and pixel: always on to the
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
                         "count": 1, "flex_mm": 0, "path_mm": 0})
            i += 1
            continue
        n = led_count(a, s)
        rows.append({"name": s.name, "group": s.group, "colour": s.colour, "start": i,
                     "count": n, "flex_mm": round(n * a.pitch), "path_mm": round(s.length)})
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
        what = f"{r['flex_mm']} mm of flex" if r["flex_mm"] else "single pixel"
        lines.append(f"  {{\"{r['name']}\", {r['start']:3d}, {r['count']:2d}, "
                     f"0x{r['colour'][1:].upper()}, G_{r['group'].upper()}}},  // {what}")
    lines += ["};", ""]
    return "\n".join(lines), rows


# --------------------------------------------------------------------------
# drawings: template, previews
# --------------------------------------------------------------------------

def template_svg(a, strokes, pixels, pcs) -> str:
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE}mm" height="{SIZE}mm" '
           f'viewBox="0 0 {SIZE} {SIZE}" font-family="Helvetica, Arial, sans-serif">',
           f'<rect x="0" y="0" width="{SIZE}" height="{SIZE}" fill="none" stroke="#000" '
           f'stroke-width="0.5"/>']
    for pc in pcs:
        p = pc.pts
        d = "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in p) + (" Z" if pc.closed else "")
        out.append(f'<path d="{d}" fill="none" stroke="#bbb" stroke-width="{a.outer_w}" '
                   f'stroke-linejoin="round"/>')
        out.append(f'<path d="{d}" fill="none" stroke="{pc.stroke.colour}" stroke-width="0.6"/>')
        for _, (cx, cy) in pc.tabs:
            out.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{a.screw_d / 2}" fill="none" '
                       f'stroke="#000" stroke-width="0.3"/>'
                       f'<path d="M{cx - 2:.2f},{cy:.2f}h4M{cx:.2f},{cy - 2:.2f}v4" '
                       f'stroke="#000" stroke-width="0.2"/>')
        m = p[len(p) // 2]
        out.append(f'<text x="{m[0] + 7:.1f}" y="{m[1] - 7:.1f}" font-size="5">{pc.id}</text>')
    for h in wire_holes(a, strokes):     # drill these through the board
        out.append(f'<circle cx="{h["x"]:.2f}" cy="{h["y"]:.2f}" r="{a.wire_hole / 2}" '
                   f'fill="#ffd0d0" stroke="#d00" stroke-width="0.4"/>')
    for st in pixels:
        out.append(f'<circle cx="{st.x}" cy="{st.y}" r="{a.pixel_d / 2}" fill="#ffd0d0" '
                   f'stroke="#d00" stroke-width="0.4"/>'
                   f'<text x="{st.x + 9}" y="{st.y + 2}" font-size="5">{st.name}</text>')
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
               '<text x="200" y="590" font-size="5">red: drill through (wires 8 mm, '
               'pixels 12 mm)   crosshairs: tab screws   grey: channel footprint</text>')
    out.append("</svg>")
    return "\n".join(out)


def raster(a, strokes, pixels, pcs, px: float, lit: bool, on=None):
    """The front of the sign as an image, px pixels per mm."""
    from PIL import Image, ImageDraw, ImageFilter

    W = int(SIZE * px)
    img = Image.new("RGB", (W, W), (14, 14, 18) if lit else (40, 40, 44))
    if not lit:
        from PIL import ImageChops
        d = ImageDraw.Draw(img)
        for pc in pcs:
            P = mf.CrossSection.batch_boolean(
                [band(pc.pts, a.outer_w, pc.closed)] + [
                    mf.CrossSection.circle(a.tab_r, 24).translate(c) for _, c in pc.tabs],
                mf.OpType.Add)
            mask = Image.new("1", img.size, 0)
            for loop in P.to_polygons():           # xor, so rings keep their hole
                one = Image.new("1", img.size, 0)
                ImageDraw.Draw(one).polygon([(x * px, y * px) for x, y in loop], fill=1)
                mask = ImageChops.logical_xor(mask, one)
            img.paste((12, 12, 12), mask=mask)
        for pc in pcs:
            d.line([(x * px, y * px) for x, y in pc.pts] + (
                [tuple(pc.pts[0] * px)] if pc.closed else []), fill=CLEAR,
                width=max(1, int(a.inner_w * px * 0.9)), joint="curve")
        for st in pixels:
            P = cap_outline(a, st).translate((st.x, st.y))
            for loop in P.to_polygons():
                d.polygon([(x * px, y * px) for x, y in loop], fill=CLEAR)
        return img
    glow = Image.new("RGB", (W, W), (0, 0, 0))
    core = Image.new("RGB", (W, W), (0, 0, 0))
    dg, dc = ImageDraw.Draw(glow), ImageDraw.Draw(core)
    rgb = lambda h: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))   # noqa: E731
    for s in strokes:
        if on is not None and s.group not in on:
            continue
        line = [(x * px, y * px) for x, y in s.pts] + ([tuple(s.pts[0] * px)] if s.closed else [])
        c = rgb(s.colour)
        dg.line(line, fill=c, width=int(16 * px), joint="curve")
        dc.line(line, fill=tuple(min(255, int(v * 0.35 + 170)) for v in c),
                width=max(1, int(a.inner_w * px)), joint="curve")
    for st in pixels:
        if on is not None and st.group not in on and st.group != "stars":
            continue
        P = cap_outline(a, st).translate((st.x, st.y))
        for loop in P.to_polygons():
            pts = [(x * px, y * px) for x, y in loop]
            dg.polygon(pts, fill=rgb(st.colour))
            dc.polygon(pts, fill=(235, 245, 255))
    glow = glow.filter(ImageFilter.GaussianBlur(10 * px))
    from PIL import ImageChops
    img = ImageChops.add(img, glow)
    img = ImageChops.lighter(img, core.filter(ImageFilter.GaussianBlur(0.6 * px)))
    return img


def tiled_pdf(a, strokes, pixels, pcs, path: Path, dpi=150):
    """The 1:1 template on A4 pages, with overlap to tape them together."""
    from PIL import Image, ImageDraw

    px = dpi / 25.4
    full = Image.new("RGB", (int(SIZE * px), int(SIZE * px)), "white")
    d = ImageDraw.Draw(full)
    lw = max(1, int(0.4 * px))
    d.rectangle([0, 0, full.width - 1, full.height - 1], outline="black", width=lw)
    for pc in pcs:
        P = band(pc.pts, a.outer_w, pc.closed)
        for loop in P.to_polygons():
            d.polygon([(x * px, y * px) for x, y in loop], outline=(120, 120, 120), width=lw)
        for _, (cx, cy) in pc.tabs:
            r = a.screw_d / 2 * px
            d.ellipse([cx * px - r, cy * px - r, cx * px + r, cy * px + r], outline="black",
                      width=lw)
            d.line([(cx * px - 2 * px, cy * px), (cx * px + 2 * px, cy * px)], fill="black")
            d.line([(cx * px, cy * px - 2 * px), (cx * px, cy * px + 2 * px)], fill="black")
        m = pc.pts[len(pc.pts) // 2]
        d.text((m[0] * px + 8 * px, m[1] * px - 10 * px), pc.id, fill="black")
    for hole in wire_holes(a, strokes):
        h = np.array([hole["x"], hole["y"]]) * px
        r = a.wire_hole / 2 * px
        d.ellipse([h[0] - r, h[1] - r, h[0] + r, h[1] + r], fill=(255, 190, 190),
                  outline=(200, 0, 0), width=lw)
    for st in pixels:
        r = a.pixel_d / 2 * px
        d.ellipse([st.x * px - r, st.y * px - r, st.x * px + r, st.y * px + r],
                  fill=(255, 190, 190), outline=(200, 0, 0), width=lw)
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
        "strokes": [{"name": s.name, "closed": s.closed, "pts": rd(s.pts[::2])} for s in strokes],
        "pixels": [{"name": st.name, "x": st.x, "y": st.y,
                    "outline": rd(cap_outline(a, st).translate((st.x, st.y)).to_polygons()[0])}
                   for st in pixels],
        "leds": rows,
        "pieces": [{"id": pc.id, "run": pc.stroke.name,
                    "outline": [rd(loop) for loop in mf.CrossSection.batch_boolean(
                        [band(pc.pts, a.outer_w, pc.closed)] + [
                            mf.CrossSection.circle(a.tab_r, 24).translate(c)
                            for _, c in pc.tabs], mf.OpType.Add).to_polygons()],
                    "tabs": rd([c for _, c in pc.tabs])} for pc in pcs],
        "holes": [dict(h, x=round(h["x"], 1), y=round(h["y"], 1)) for h in wire_holes(a, strokes)],
        "back": back_layout(a),
        "dims": {k: round(getattr(a, k), 1) for k in (
            "flex_w", "inner_w", "outer_w", "wall", "floor", "depth", "tab_t", "screw_d",
            "wire_hole", "pixel_d", "standoff_h", "box_h", "min_bend", "bed", "star_size")},
        "stats": stats,
    }
    return (HERE / "preview_template.html").read_text().replace(
        "/*DATA*/null", json.dumps(data, separators=(",", ":")))


# --------------------------------------------------------------------------

def build_parser():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", type=Path, default=HERE / "example")
    g = p.add_argument_group("neon flex")
    g.add_argument("--flex-w", type=float, default=6.0, help="width of the flex's lit face")
    g.add_argument("--min-bend", type=float, default=20,
                   help="tightest bend radius the flex allows (check its datasheet)")
    g.add_argument("--pitch", type=float, default=1000 / 60, help="mm per LED (60/m)")
    g.add_argument("--cut-every", type=int, default=1, help="LEDs between cut marks")
    g.add_argument("--end-cap", type=float, default=6, help="length an end cap adds, mm")
    g = p.add_argument_group("channel (mm)")
    g.add_argument("--fit", type=float, default=0.3, help="clearance each side of the flex")
    g.add_argument("--wall", type=float, default=1.6)
    g.add_argument("--floor", type=float, default=1.2)
    g.add_argument("--depth", type=float, default=8,
                   help="wall height: how much of the 12 mm flex is hidden")
    g.add_argument("--min-gap", type=float, default=3,
                   help="space between neighbouring channels")
    g.add_argument("--tab-r", type=float, default=6)
    g.add_argument("--tab-t", type=float, default=2.4)
    g.add_argument("--tab-spacing", type=float, default=110)
    g.add_argument("--tab-inset", type=float, default=14)
    g.add_argument("--screw-d", type=float, default=3.4, help="hole for the tab screws")
    g.add_argument("--slot-w", type=float, default=5.5, help="wire slot in the floor")
    g.add_argument("--slot-len", type=float, default=9)
    g.add_argument("--wire-hole", type=float, default=8, help="hole through the board")
    g = p.add_argument_group("printer")
    g.add_argument("--bed", type=float, default=220, help="usable bed size, mm")
    g = p.add_argument_group("stars, back parts (mm)")
    g.add_argument("--star-size", type=float, default=46)
    g.add_argument("--dot-size", type=float, default=22, help="the eyes")
    g.add_argument("--star-h", type=float, default=10)
    g.add_argument("--star-face", type=float, default=2.0, help="diffuser thickness")
    g.add_argument("--pixel-d", type=float, default=12, help="the 12 mm WS2811 bullet pixels")
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
    a.inner_w = a.flex_w + 2 * a.fit
    a.outer_w = a.inner_w + 2 * a.wall

    strokes, pixels = artwork()
    problems = check(a, strokes, pixels)
    total = sum(led_count(a, s) for s in strokes) + len(pixels)
    flex = sum(led_count(a, s) * a.pitch for s in strokes) / 1000
    print(f"neon sign: {SIZE:.0f} x {SIZE:.0f} mm, {len(strokes)} runs of flex "
          f"({flex:.2f} m), {len(pixels)} single pixels, {total} LEDs")
    for s in strokes:
        print(f"  {s.name:<12} {s.length:6.0f} mm  {led_count(a, s):3d} LEDs  "
              f"tightest bend r={tightest_bend(s):.0f} mm")
    if problems:
        print("\nNOT written -- the artwork does not fit the flex:")
        for msg in problems:
            print("  " + msg)
        return 1
    print("  checks         OK (bends, clearances, margins)")
    if a.check_only:
        return 0

    out = a.out
    out.mkdir(parents=True, exist_ok=True)
    chain = data_chain(a, strokes, pixels)       # may turn runs round, so first
    pcs = pieces(a, strokes)
    print(f"  channels       {len(pcs)} printed pieces")

    plates = pack([(pc.id, pc.solid) for pc in pcs], a.bed)
    for k, plate in enumerate(plates, 1):
        parts = [Part(n, 1, BLACK, m) for n, m in plate]
        (out / f"channels_plate_{k}.3mf").write_bytes(
            parts_to_3mf(parts, name=f"neon channels {k}"))
    print(f"  plates         {len(plates)} x {a.bed:.0f} mm bed, black")

    caps = pack([(st.name, pixel_cap(a, st)) for st in pixels], a.bed)[0]
    (out / "pixel_caps.3mf").write_bytes(parts_to_3mf(
        [Part(n, 1, CLEAR, m) for n, m in caps], name="pixel caps"))
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
    grams = sum(float(pc.solid.volume()) for pc in pcs) * 1.24 / 1000
    stats = {"leds": total, "flex_m": round(flex, 2), "runs": len(strokes),
             "pixels": len(pixels), "pieces": len(pcs), "plates": len(plates),
             "grams": round(grams), "pages": n}
    (out / "preview.html").write_text(preview_html(a, strokes, pixels, pcs, rows, stats))
    print(f"  filament       ~{grams:.0f} g of channels")
    print(f"  template       template.svg, template_a4.pdf ({n} pages)")
    print(f"  -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
