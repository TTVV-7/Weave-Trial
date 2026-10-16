#!/usr/bin/env python3
"""A "Review us on Google" stand: QR code, NFC tag, your logo and your name.

    python reviewstand/make_review_stand.py \\
        --name "Bella's Bakery" \\
        --url "https://g.page/r/YOUR-PLACE-ID/review" \\
        --logo my_logo.svg

writes ``reviewstand/<name>/``:

* ``review_stand_sign.3mf`` -- the sign plate, one object per filament, ready for the AMS
* ``review_stand_base.3mf`` -- the stand it slots into (and ``.stl``)
* ``review_stand_assembled.3mf`` and ``*_preview.png`` -- to check before printing

Two pieces, because that is what prints well: the sign lies flat, face up,
so every colour is on the top layers (an AMS does it in one go; without one,
the raised artwork is a single filament change at one height), and the base
holds it leaning back at ``--tilt`` degrees.

The NFC tag (an NTAG213/215 sticker or coin, 25 mm by default) goes behind
the "tap" icon. ``--nfc back`` (default) leaves a recess in the back of the
plate to press the tag into after printing; ``--nfc hidden`` seals it inside,
which needs a pause at the height the script prints; ``--nfc none`` drops it.
Program the tag with the same review link (NFC Tools, free on iOS/Android).

The QR code is generated from ``--url`` here, so it is real geometry rather
than a picture, and the module size is checked against what a 0.4 mm nozzle
can print sharply. Needs ``manifold3d``, ``qrcode`` and ``fonttools``.
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

import manifold3d as mf  # noqa: E402
import qrcode  # noqa: E402
from fontTools.pens.basePen import BasePen  # noqa: E402
from fontTools.ttLib import TTFont  # noqa: E402

from phonecase import svgart  # noqa: E402
from phonecase.solid import mesh_to_stl  # noqa: E402
from phonecase.threemf import Part, parts_to_3mf  # noqa: E402

FONT_BOLD = HERE / "fonts" / "Inter-Bold.otf"
FONT_SEMI = HERE / "fonts" / "Inter-SemiBold.otf"
SEG = 48

BODY, INK, ACCENT = 0, 1, 2


def _hex(s: str) -> tuple[int, int, int]:
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


# --------------------------------------------------------------------------
# 2-D shapes
# --------------------------------------------------------------------------

def rrect(w: float, h: float, r: float, cx=0.0, cy=0.0) -> mf.CrossSection:
    r = min(r, w / 2 - 0.01, h / 2 - 0.01)
    core = mf.CrossSection.square((w - 2 * r, h - 2 * r), center=True)
    return core.offset(r, mf.JoinType.Round, circular_segments=SEG).translate((cx, cy))


def star(cx: float, cy: float, R: float, inner=0.45) -> mf.CrossSection:
    pts = []
    for i in range(10):
        a = math.pi / 2 + i * math.pi / 5
        rad = R if i % 2 == 0 else R * inner
        pts.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))
    return mf.CrossSection([pts])


def arc_band(cx, cy, r, w, a0, a1, n=24) -> mf.CrossSection:
    outer = [(cx + (r + w / 2) * math.cos(a), cy + (r + w / 2) * math.sin(a))
             for a in (a0 + (a1 - a0) * i / n for i in range(n + 1))]
    inner = [(cx + (r - w / 2) * math.cos(a), cy + (r - w / 2) * math.sin(a))
             for a in (a1 - (a1 - a0) * i / n for i in range(n + 1))]
    band = mf.CrossSection([outer + inner])
    # round the ends so they print as clean dots rather than knife edges
    caps = [mf.CrossSection.circle(w / 2, 24).translate(
        (cx + r * math.cos(a), cy + r * math.sin(a))) for a in (a0, a1)]
    return mf.CrossSection.batch_boolean([band, *caps], mf.OpType.Add)


def nfc_icon(cx: float, cy: float, size: float) -> mf.CrossSection:
    """Contactless waves: a dot and three arcs, fitting a size x size box."""
    w = size * 0.11
    left = cx - size * 0.42
    parts = [mf.CrossSection.circle(w * 0.75, 24).translate((left + w, cy))]
    for k in range(1, 4):
        r = size * 0.27 * k
        parts.append(arc_band(left, cy, r, w, -math.radians(48), math.radians(48)))
    return mf.CrossSection.batch_boolean(parts, mf.OpType.Add)


# --------------------------------------------------------------------------
# text
# --------------------------------------------------------------------------

class _Flatten(BasePen):
    """Glyph outlines as polylines: lines kept, curves sampled."""

    def __init__(self, glyphset, steps=8):
        super().__init__(glyphset)
        self.steps = steps
        self.loops: list[list[tuple[float, float]]] = []
        self.cur: list[tuple[float, float]] = []
        self.dx = 0.0

    def _p(self, p):
        return (p[0] + self.dx, p[1])

    def _moveTo(self, p):
        self.cur = [self._p(p)]

    def _lineTo(self, p):
        self.cur.append(self._p(p))

    def _curveToOne(self, p1, p2, p3):
        p0 = self.cur[-1]
        p1, p2, p3 = self._p(p1), self._p(p2), self._p(p3)
        for i in range(1, self.steps + 1):
            t = i / self.steps
            u = 1 - t
            self.cur.append(tuple(u ** 3 * a + 3 * u * u * t * b + 3 * u * t * t * c + t ** 3 * d
                                  for a, b, c, d in zip(p0, p1, p2, p3)))

    def _qCurveToOne(self, p1, p2):
        p0 = self.cur[-1]
        p1, p2 = self._p(p1), self._p(p2)
        for i in range(1, self.steps + 1):
            t = i / self.steps
            u = 1 - t
            self.cur.append(tuple(u * u * a + 2 * u * t * b + t * t * c
                                  for a, b, c in zip(p0, p1, p2)))

    def _closePath(self):
        if len(self.cur) >= 3:
            self.loops.append(self.cur)
        self.cur = []

    _endPath = _closePath


_fonts: dict[Path, TTFont] = {}


def text(s: str, cap_h: float, max_w: float, font: Path = FONT_BOLD) -> mf.CrossSection:
    """One line of text, centred on x = 0, baseline at y = 0, caps cap_h tall.

    Shrunk to max_w if it would be wider.
    """
    f = _fonts.setdefault(font, TTFont(str(font)))
    gs = f.getGlyphSet()
    cmap = f.getBestCmap()
    caps = getattr(f["OS/2"], "sCapHeight", 0) or f["head"].unitsPerEm * 0.7
    pen = _Flatten(gs)
    for ch in s:
        g = cmap.get(ord(ch)) or cmap.get(ord("?"))
        gs[g].draw(pen)
        pen.dx += gs[g].width
    if not pen.loops:
        return mf.CrossSection()
    cs = mf.CrossSection(pen.loops, mf.FillRule.NonZero)
    scale = cap_h / caps
    x0, _, x1, _ = cs.bounds()
    if (x1 - x0) * scale > max_w:
        scale = max_w / (x1 - x0)
    cs = cs.scale((scale, scale))
    x0, _, x1, _ = cs.bounds()
    return cs.translate((-(x0 + x1) / 2, 0))


# --------------------------------------------------------------------------
# QR code and logo
# --------------------------------------------------------------------------

def qr(url: str, size: float) -> tuple[mf.CrossSection, float, int]:
    """The dark modules, size x size, centred on the origin."""
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=0)
    q.add_data(url)
    q.make(fit=True)
    m = q.get_matrix()
    n = len(m)
    mod = size / n
    e = 0.002  # a hair of overlap so neighbouring modules fuse into one solid
    rects = []
    for r, row in enumerate(m):
        c = 0
        while c < n:
            if row[c]:
                c1 = c
                while c1 < n and row[c1]:
                    c1 += 1
                x = -size / 2 + c * mod
                y = size / 2 - (r + 1) * mod
                rects.append(mf.CrossSection.square(((c1 - c) * mod + 2 * e, mod + 2 * e))
                             .translate((x - e, y - e)))
                c = c1
            else:
                c += 1
    return mf.CrossSection.batch_boolean(rects, mf.OpType.Add), mod, n


def logo_regions(path: Path, max_w: float, max_h: float, cx: float, cy: float):
    """Visible region per fill colour, fitted into a box centred on (cx, cy)."""
    art = svgart.load_file(path)
    for w in art.warnings:
        print(f"  logo: {w}")
    x0, y0, x1, y1 = art.bbox()
    s = min(max_w / (x1 - x0), max_h / (y1 - y0))
    ox, oy = (x0 + x1) / 2, (y0 + y1) / 2

    def place(p):  # SVG is y-down
        return (cx + (p[0] - ox) * s, cy - (p[1] - oy) * s)

    covered = mf.CrossSection()
    by_rgb: dict[tuple, list] = {}
    for shape in reversed(art.shapes):
        loops = [[place(p) for p in sp] for sp in shape.subpaths if len(sp) >= 3]
        if not loops:
            continue
        rule = mf.FillRule.EvenOdd if shape.even_odd else mf.FillRule.NonZero
        poly = mf.CrossSection(loops, rule)
        visible = poly - covered
        covered = covered + poly
        if not visible.is_empty():
            by_rgb.setdefault(shape.rgb, []).append(visible)
    out = {rgb: mf.CrossSection.batch_boolean(v, mf.OpType.Add).simplify(0.01)
           for rgb, v in by_rgb.items()}
    return out, (x1 - x0) * s, (y1 - y0) * s


# --------------------------------------------------------------------------
# the sign
# --------------------------------------------------------------------------

@dataclass
class Slot:
    name: str
    rgb: tuple[int, int, int]


@dataclass
class Sign:
    w: float
    h: float
    regions: dict[int, mf.CrossSection]
    slots: list[Slot]
    nfc_xy: tuple[float, float] | None
    keepout: float
    qr_module: float
    qr_n: int


def _dist(a, b):
    return math.dist(a, b)


def layout(a) -> Sign:
    W = a.width
    inner = W - 2 * (a.border_inset + a.border + 3)   # usable text width
    slots = [Slot("body", _hex(a.body)), Slot("ink", _hex(a.ink)),
             Slot("accent", _hex(a.accent))]
    regions: dict[int, list] = {}

    def add(slot, cs):
        if cs is not None and not cs.is_empty():
            regions.setdefault(slot, []).append(cs)

    # Build top-down with y = 0 at the top edge and going negative; the whole
    # stack is shifted up into place once the height is known.
    y = -(a.border_inset + a.border + 4)
    gap = 4.0

    if a.logo:
        regs, lw, lh = logo_regions(Path(a.logo), inner, a.logo_height, 0, 0)
        cy = y - lh / 2
        for rgb, cs in regs.items():
            if a.logo_color:
                slot = {"ink": INK, "accent": ACCENT}[a.logo_color]
            else:
                # nearest existing filament, or a new one while the AMS has room
                near = min(range(len(slots)), key=lambda i: _dist(slots[i].rgb, rgb))
                if _dist(slots[near].rgb, rgb) > 60 and len(slots) < a.max_colors:
                    slots.append(Slot(f"logo{len(slots) - 2}", rgb))
                    near = len(slots) - 1
                slot = near
            if slot != BODY:
                add(slot, cs.translate((0, cy)))
        y -= lh + gap

    if a.name:
        t = text(a.name, a.name_height, inner)
        _, b0, _, b1 = t.bounds()
        add(INK, t.translate((0, y - b1)))
        y -= (b1 - b0) + gap

    if a.header:
        t = text(a.header, a.header_height, inner, FONT_SEMI)
        _, b0, _, b1 = t.bounds()
        add(INK, t.translate((0, y - b1)))
        y -= (b1 - b0) + gap * 0.8

    if a.stars:
        R = a.star_size / 2
        pitch = a.star_size * 1.25
        stars = [star((i - 2) * pitch, y - R, R) for i in range(5)]
        add(ACCENT, mf.CrossSection.batch_boolean(stars, mf.OpType.Add))
        y -= a.star_size + gap

    q, module, n = qr(a.url, a.qr_size)
    quiet = max(gap, 3 * module)  # scanners want a clear margin round the code
    y -= quiet - gap
    add(INK, q.translate((0, y - a.qr_size / 2)))
    y -= a.qr_size + quiet

    nfc_xy = None
    if a.cta:
        if a.nfc != "none":
            icon = a.cta_height * 2.2
            t = text(a.cta, a.cta_height, inner - icon - 3, FONT_SEMI)
            tx0, b0, tx1, b1 = t.bounds()
            row_h = max(icon, b1 - b0)
            total = icon + 3 + (tx1 - tx0)
            ix = -total / 2 + icon / 2
            cy = y - row_h / 2
            add(INK, nfc_icon(ix, cy, icon))
            add(INK, t.translate((ix + icon / 2 + 3 - tx0, cy - (b0 + b1) / 2)))
            nfc_xy = (ix, cy)
        else:
            t = text(a.cta, a.cta_height, inner, FONT_SEMI)
            _, b0, _, b1 = t.bounds()
            row_h = b1 - b0
            add(INK, t.translate((0, y - b1)))
        y -= row_h + gap
    elif a.nfc != "none":
        nfc_xy = (0, y - a.tag_d / 2)
        y -= a.tag_d + gap

    keepout = a.slot_depth / math.cos(math.radians(a.tilt)) + 1.5
    H = -y + keepout + (a.border_inset + a.border)
    shift = H  # top edge at y = H, bottom at 0

    if a.border > 0:
        o = rrect(W - 2 * a.border_inset, H - 2 * a.border_inset, a.radius - a.border_inset)
        i = rrect(W - 2 * (a.border_inset + a.border), H - 2 * (a.border_inset + a.border),
                  a.radius - a.border_inset - a.border)
        add(ACCENT if a.border_color == "accent" else INK, (o - i).translate((0, H / 2 - shift)))

    # Nothing raised may go into the slot, or the plate will not seat; the
    # frame simply runs out of sight behind the base.
    visible = mf.CrossSection.square((W, H - keepout + 1.0)).translate((-W / 2, keepout - 1.0))
    merged = {k: mf.CrossSection.batch_boolean(v, mf.OpType.Add).translate((0, shift)) ^ visible
              for k, v in regions.items()}
    if nfc_xy:
        nfc_xy = (nfc_xy[0], nfc_xy[1] + shift)
    return Sign(W, H, merged, slots, nfc_xy, keepout, module, n)


def sign_parts(a, s: Sign) -> list[Part]:
    t, rel = a.thickness, a.relief
    body = rrect(s.w, s.h, a.radius, 0, s.h / 2).extrude(t)

    if s.nfc_xy and a.nfc != "none":
        r = a.tag_d / 2 + 0.3
        z0 = 0.0 if a.nfc == "back" else a.hidden_floor
        pocket = (mf.CrossSection.circle(r, 96).translate(s.nfc_xy)
                  .extrude(a.tag_t + 0.2).translate((0, 0, z0)))
        body = body - pocket

    parts = []
    for slot in sorted(s.regions):
        cs = s.regions[slot]
        if a.flush:
            solid = cs.extrude(rel).translate((0, 0, t - rel))
            body = body - solid
        else:
            solid = cs.extrude(rel).translate((0, 0, t))
        sl = s.slots[slot]
        parts.append(Part(sl.name, slot + 1, sl.rgb, solid))
    b = s.slots[BODY]
    return [Part(b.name, 1, b.rgb, body)] + parts


def base_solid(a, s: Sign) -> mf.Manifold:
    W = s.w + 2 * a.base_margin
    D, H = a.base_depth, a.base_height
    front = H * 0.5
    # side profile in (y, z), extruded along x
    prof = mf.CrossSection([[(0, 0), (D, 0), (D, H), (D * 0.3, H), (0, front)]])
    body = prof.extrude(W).rotate((90, 0, 90)).translate((-W / 2, 0, 0))
    # round the footprint corners
    foot = rrect(W, D, 8, 0, D / 2).extrude(H + 1)
    body = body ^ foot
    slot = (mf.Manifold.cube((s.w + 0.6, a.thickness + a.slot_clearance, 60))
            .translate((-(s.w + 0.6) / 2, -(a.thickness + a.slot_clearance) / 2, 0))
            .rotate((-a.tilt, 0, 0))
            .translate((0, a.slot_y, H - a.slot_depth)))
    return body - slot


def assembled(a, s: Sign, parts: list[Part], base) -> list[Part]:
    """The sign standing in its slot, to look at rather than to print."""
    def place(m):
        return (m.rotate((90, 0, 0)).translate((0, a.thickness / 2, 0))
                .rotate((-a.tilt, 0, 0))
                .translate((0, a.slot_y, a.base_height - a.slot_depth)))
    out = [Part(p.name, p.slot, p.rgb, place(p.solid)) for p in parts]
    return out + [Part("base", parts[0].slot, parts[0].rgb, base)]


# --------------------------------------------------------------------------
# preview
# --------------------------------------------------------------------------

def preview(a, s: Sign, path: Path, px=8):
    from PIL import Image, ImageChops, ImageDraw

    pad = 10
    bw = s.w + 2 * a.base_margin
    W = int((bw + 2 * pad) * px)
    Hpx = int((s.h + 2 * pad) * px)
    img = Image.new("RGB", (W, Hpx), (236, 238, 242))

    def to_px(x, y):
        return ((x + bw / 2 + pad) * px, (s.h + pad - y) * px)

    def fill(cs, rgb):
        mask = Image.new("1", img.size, 0)
        for loop in cs.to_polygons():
            one = Image.new("1", img.size, 0)
            ImageDraw.Draw(one).polygon([to_px(*p) for p in loop], fill=1)
            mask = ImageChops.logical_xor(mask, one)
        img.paste(rgb, mask=mask)

    fill(rrect(s.w + 1.2, s.h + 1.2, a.radius + 0.6, 0, s.h / 2), (190, 192, 198))
    fill(rrect(s.w, s.h, a.radius, 0, s.h / 2), s.slots[BODY].rgb)
    for slot, cs in sorted(s.regions.items()):
        fill(cs, s.slots[slot].rgb)
    d = ImageDraw.Draw(img)
    if s.nfc_xy and a.nfc != "none":
        x, y = to_px(*s.nfc_xy)
        r = a.tag_d / 2 * px
        for k in range(0, 360, 12):  # dashed circle where the tag sits
            d.arc((x - r, y - r, x + r, y + r), k, k + 6, fill=(120, 160, 230), width=2)
    # the base, seen from the front, over the part of the plate it hides
    bh = s.keepout - 1.5
    fill(rrect(bw, bh + 2, 3, 0, (bh + 2) / 2 - 2), (205, 207, 212))
    img.save(path)


def base_preview(a, s: Sign, base, path: Path, px=8):
    """Top view of the base: footprint, the slot, and the ramp shaded."""
    from PIL import Image, ImageDraw

    x0, y0, _, x1, y1, _ = base.bounding_box()
    pad = 10
    img = Image.new("RGB", (int((x1 - x0 + 2 * pad) * px), int((y1 - y0 + 2 * pad) * px)),
                    (236, 238, 242))
    d = ImageDraw.Draw(img)

    def to_px(x, y):
        return ((x - x0 + pad) * px, (y1 - y + pad) * px)

    top = base.slice(a.base_height - 0.01)
    foot = base.slice(0.5)
    for cs, rgb in ((foot, (190, 192, 198)), (top, s.slots[BODY].rgb)):
        for loop in cs.to_polygons():
            d.polygon([to_px(*p) for p in loop], fill=rgb, outline=(150, 152, 158))
    img.save(path)


# --------------------------------------------------------------------------

def build_parser():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_argument_group("content")
    g.add_argument("--name", default="Your Business", help="business name ('' for none)")
    g.add_argument("--url", default="https://g.page/r/YOUR-PLACE-ID/review",
                   help="link the QR code (and NFC tag) opens -- your Google review link")
    g.add_argument("--logo", help="logo as an SVG; its fill colours are matched to filaments")
    g.add_argument("--logo-color", choices=["ink", "accent"],
                   help="print the whole logo in one filament instead of its own colours")
    g.add_argument("--header", default="Review us on Google")
    g.add_argument("--cta", default="Tap or scan to review", help="line by the NFC icon")
    g.add_argument("--no-stars", dest="stars", action="store_false")
    g.add_argument("--out", type=Path, help="output folder (default: reviewstand/<name>)")

    g = p.add_argument_group("colours (hex)")
    g.add_argument("--body", default="#F4F4F2")
    g.add_argument("--ink", default="#1A1A1A")
    g.add_argument("--accent", default="#F2B705")
    g.add_argument("--border-color", choices=["ink", "accent"], default="ink")
    g.add_argument("--max-colors", type=int, default=4, help="filaments available (AMS slots)")

    g = p.add_argument_group("sizes (mm)")
    g.add_argument("--width", type=float, default=100)
    g.add_argument("--thickness", type=float, default=4)
    g.add_argument("--radius", type=float, default=7)
    g.add_argument("--relief", type=float, default=0.6, help="height of the coloured artwork")
    g.add_argument("--flush", action="store_true",
                   help="inlay the artwork flush with the face (needs an AMS)")
    g.add_argument("--border", type=float, default=1.2, help="frame line width, 0 for none")
    g.add_argument("--border-inset", type=float, default=3.5)
    g.add_argument("--logo-height", type=float, default=24)
    g.add_argument("--name-height", type=float, default=8)
    g.add_argument("--header-height", type=float, default=5.5)
    g.add_argument("--star-size", type=float, default=8)
    g.add_argument("--qr-size", type=float, default=60)
    g.add_argument("--cta-height", type=float, default=4.2)

    g = p.add_argument_group("NFC tag")
    g.add_argument("--nfc", choices=["back", "hidden", "none"], default="back")
    g.add_argument("--tag-d", type=float, default=25, help="tag diameter")
    g.add_argument("--tag-t", type=float, default=1.0, help="tag thickness")
    g.add_argument("--hidden-floor", type=float, default=0.6,
                   help="plastic behind a hidden tag")

    g = p.add_argument_group("base")
    g.add_argument("--tilt", type=float, default=12, help="lean back, degrees")
    g.add_argument("--base-depth", type=float, default=60)
    g.add_argument("--base-height", type=float, default=16)
    g.add_argument("--base-margin", type=float, default=6)
    g.add_argument("--slot-depth", type=float, default=10)
    g.add_argument("--slot-y", type=float, default=26, help="slot distance from the front")
    g.add_argument("--slot-clearance", type=float, default=0.35)
    return p


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "review-stand"


def main(argv=None) -> int:
    a = build_parser().parse_args(argv)
    out = a.out or HERE / slug(a.name or "review-stand")
    out.mkdir(parents=True, exist_ok=True)

    s = layout(a)
    parts = sign_parts(a, s)
    base = base_solid(a, s)
    stem = "review_stand"
    (out / f"{stem}_sign.3mf").write_bytes(parts_to_3mf(parts, origin=(s.w / 2 + 5, 5),
                                                        name="review sign"))
    bx0, by0, _, _, _, _ = base.bounding_box()
    (out / f"{stem}_base.3mf").write_bytes(parts_to_3mf(
        [Part("base", 1, _hex(a.body), base)], origin=(-bx0 + 5, -by0 + 5), name="review base"))
    (out / f"{stem}_base.stl").write_bytes(mesh_to_stl(base, header="review stand base"))
    (out / f"{stem}_assembled.3mf").write_bytes(parts_to_3mf(
        assembled(a, s, parts, base), origin=(-bx0 + 5, -by0 + 5), name="review stand"))
    preview(a, s, out / f"{stem}_sign_preview.png")
    preview(a, s, out / f"{stem}_assembled_preview.png")
    base_preview(a, s, base, out / f"{stem}_base_preview.png")

    print(f"wrote {out}/  sign {s.w:.0f} x {s.h:.0f} x {a.thickness:.1f} mm, "
          f"base {s.w + 2 * a.base_margin:.0f} x {a.base_depth:.0f} mm")
    print("  filaments: " + ", ".join(
        f"T{p.slot} {p.name} #{'%02X%02X%02X' % p.rgb}" for p in parts))
    print(f"  QR: {s.qr_n} x {s.qr_n} modules, {s.qr_module:.2f} mm each"
          + ("  ** under 1.2 mm: make --qr-size bigger or the URL shorter **"
             if s.qr_module < 1.2 else ""))
    if a.nfc == "hidden":
        top = a.hidden_floor + a.tag_t + 0.2
        print(f"  NFC: add a pause at {top:.1f} mm (the first layer above it) and drop the tag in")
    elif a.nfc == "back":
        print(f"  NFC: {a.tag_d:.0f} mm recess in the back, behind the tap icon -- press the tag in")
    if not a.flush:
        print(f"  no AMS? the artwork is everything above {a.thickness:.1f} mm: "
              "one filament change there")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
