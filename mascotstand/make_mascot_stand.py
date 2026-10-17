#!/usr/bin/env python3
"""The desk stand for the mascot figure: a round stage for it to stand on,
a sticky-note tray and a pen cup, with yellow trim.

    python mascotstand/make_mascot_stand.py

writes ``mascotstand/models/`` (or ``--out``):

* ``mascot_stand_base.3mf`` / ``.stl`` -- the whole stand in one black print
* ``mascot_stand_trim.3mf`` -- every yellow piece, laid out on one plate
* ``mascot_stand_assembled.3mf`` -- the two together, coloured, to look at
* ``*_preview.png`` -- to check before printing

The colours are separate prints rather than one AMS print, because that is
what costs no purge. The trim sits at five different heights on a part 60 mm
tall, so painting it in would mean a filament swap on most layers of the
base. Instead the base has grooves and the trim is printed on its own, in
yellow, and pressed into them:

* **stage ring** -- an inlay round the top of the disc, broken where the tray sits
* **side band** -- a strip round the whole outside wall, open at the back so
  it can be wrapped on
* **tray rim** and **cup rim** -- caps with a tongue underneath that drops into
  a slot in the top of each wall

The figure fixes on with two M4 countersunk screws from underneath, into
heat-set inserts (or holes tapped in its boots) at ``--boot-spacing``.
Needs ``manifold3d``; ``pillow`` for the previews.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

import manifold3d as mf  # noqa: E402

from phonecase.solid import mesh_to_stl  # noqa: E402
from phonecase.threemf import Part, parts_to_3mf  # noqa: E402

SEG = 128


def _hex(s: str) -> tuple[int, int, int]:
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def rrect(w: float, h: float, r: float, cx=0.0, cy=0.0) -> mf.CrossSection:
    r = min(r, w / 2 - 0.01, h / 2 - 0.01)
    core = mf.CrossSection.square((w - 2 * r, h - 2 * r), center=True)
    return core.offset(r, mf.JoinType.Round, circular_segments=SEG).translate((cx, cy))


def circle(r: float, cx=0.0, cy=0.0) -> mf.CrossSection:
    return mf.CrossSection.circle(r, SEG).translate((cx, cy))


def ring(r0: float, r1: float, cx=0.0, cy=0.0) -> mf.CrossSection:
    return circle(r1, cx, cy) - circle(r0, cx, cy)


def slab(cs: mf.CrossSection, z0: float, z1: float) -> mf.Manifold:
    return cs.extrude(z1 - z0).translate((0, 0, z0))


def biggest(cs: mf.CrossSection, keep=0.3) -> mf.CrossSection:
    """Drop slivers: keep only pieces at least ``keep`` of the largest's area."""
    pieces = cs.decompose()
    top = max(p.area() for p in pieces)
    return mf.CrossSection.batch_boolean([p for p in pieces if p.area() >= keep * top],
                                         mf.OpType.Add)


# --------------------------------------------------------------------------
# layout, all in the base's own coordinates: disc centred on the origin,
# x to the right, y to the back, z up from the bed
# --------------------------------------------------------------------------

class Layout:
    def __init__(self, a):
        self.a = a
        t = a.wall
        self.tray_w = a.pad + 2 * a.pad_clearance + 2 * t        # outside of the tray
        self.tray_c = (a.disc_r - 25 + self.tray_w / 2, -a.disc_r + 2.5 + self.tray_w / 2)
        tx, ty = self.tray_c
        self.cup_c = (tx + a.cup_dx, ty + self.tray_w / 2 + a.cup_gap + a.cup_r)
        self.tray = rrect(self.tray_w, self.tray_w, 6, tx, ty)
        self.cup = circle(a.cup_r, *self.cup_c)
        # a rounded tab off the side of the disc, round the tray and the cup
        cx, cy = self.cup_c
        x0 = a.disc_r * 0.3
        x1 = max(tx + self.tray_w / 2, cx + a.cup_r) + a.ledge
        y0 = ty - self.tray_w / 2 - a.ledge
        y1 = cy + a.cup_r + a.ledge
        self.wing = rrect(x1 - x0, y1 - y0, 10, (x0 + x1) / 2, (y0 + y1) / 2)
        self.disc = circle(a.disc_r)
        self.outline = self.disc + self.wing

        # the notch in the front of the tray, to get a finger under the pad
        nz = a.tray_floor + a.notch_floor
        self.notch = (mf.Manifold.cylinder(100, a.notch_w / 2, a.notch_w / 2, SEG)
                      .rotate((-90, 0, 0)).translate((tx, ty - 50, nz + a.notch_w / 2))
                      + mf.Manifold.cube((a.notch_w, 100, 200))
                      .translate((tx - a.notch_w / 2, ty - 50, nz + a.notch_w / 2)))
        self.notch_cs = rrect(a.notch_w, self.tray_w / 2, 0.01, tx,
                              ty - self.tray_w / 2)        # the notch, seen from above

        # 2-D shapes of the trim slots (the trim itself is these, less clearance)
        self.tray_wall = (self.tray - rrect(self.tray_w - 2 * t, self.tray_w - 2 * t, 2.5, tx, ty)
                          - self.notch_cs - self.cup.offset(0.2, mf.JoinType.Round,
                                                            circular_segments=SEG))
        self.tray_slot = (rrect(self.tray_w - t + a.slot_w, self.tray_w - t + a.slot_w, 4.5, tx, ty)
                          - rrect(self.tray_w - t - a.slot_w, self.tray_w - t - a.slot_w, 4, tx, ty)
                          - self.notch_cs.offset(1.2, mf.JoinType.Miter)
                          - self.cup.offset(1.2, mf.JoinType.Round, circular_segments=SEG))
        cr = a.cup_r - t / 2
        self.cup_wall = ring(a.cup_r - t, a.cup_r, *self.cup_c)
        self.cup_slot = ring(cr - a.slot_w / 2, cr + a.slot_w / 2, *self.cup_c)
        sr = a.disc_r - a.ring_inset - a.ring_w / 2
        keep_out = (self.tray + self.cup).offset(2.0, mf.JoinType.Round, circular_segments=SEG)
        self.stage_slot = biggest(ring(sr - a.ring_w / 2, sr + a.ring_w / 2) - keep_out)
        # cut from 1 mm outside the wall, so no sliver of skin is left on it
        self.band_slot = self.outline.offset(1.0, mf.JoinType.Round, circular_segments=SEG) - \
            self.outline.offset(-a.band_depth, mf.JoinType.Round,
                                                            circular_segments=SEG)

        self.boots = [(a.dog_x - a.boot_spacing / 2, a.dog_y),
                      (a.dog_x + a.boot_spacing / 2, a.dog_y)]
        x0, y0, x1, y1 = self.outline.bounds()
        self.feet = [(-a.disc_r * 0.62, a.disc_r * 0.55), (-a.disc_r * 0.62, -a.disc_r * 0.55),
                     (0, a.disc_r * 0.78), (0, -a.disc_r * 0.78),
                     (x1 - 14, y1 - 16), (x1 - 14, y0 + 14)]


# --------------------------------------------------------------------------
# the base
# --------------------------------------------------------------------------

def base_solid(a, L: Layout) -> mf.Manifold:
    c = a.chamfer
    # disc with a chamfered top edge
    disc = (slab(L.disc, 0, a.disc_h - c)
            + mf.Manifold.cylinder(c, a.disc_r, a.disc_r - c, SEG)
            .translate((0, 0, a.disc_h - c)))
    wing = slab(L.wing, 0, a.wing_h - c) + (L.wing.offset(-c, mf.JoinType.Round,
                                                          circular_segments=SEG)
                                            .extrude(c).translate((0, 0, a.wing_h - c)))
    tray = slab(L.tray, 0, a.tray_h)
    cup = slab(L.cup, 0, a.cup_h)
    body = mf.Manifold.batch_boolean([disc, wing, tray, cup], mf.OpType.Add)

    t = a.wall
    tx, ty = L.tray_c
    inner = rrect(L.tray_w - 2 * t, L.tray_w - 2 * t, 2.5, tx, ty)
    cuts = [slab(inner, a.tray_floor, a.tray_h + 1),
            L.notch,
            slab(circle(a.cup_r - t, *L.cup_c), a.cup_floor, a.cup_h + 1),
            # trim slots
            slab(L.tray_slot, a.tray_h - a.slot_d, a.tray_h + 1),
            slab(L.cup_slot, a.cup_h - a.slot_d, a.cup_h + 1),
            slab(L.stage_slot, a.disc_h - a.ring_d, a.disc_h + 1),
            slab(L.band_slot, a.band_z, a.band_z + a.band_h)]
    # figure screws: countersunk from underneath
    for x, y in L.boots:
        cuts.append(mf.Manifold.cylinder(a.disc_h + 2, a.screw_d / 2, a.screw_d / 2, 48)
                    .translate((x, y, -1)))
        cuts.append(mf.Manifold.cylinder(a.head_d / 2 - a.screw_d / 2 + 0.01,
                                         a.head_d / 2, a.screw_d / 2, 48)
                    .translate((x, y, a.head_recess)))
        cuts.append(mf.Manifold.cylinder(a.head_recess + 1, a.head_d / 2, a.head_d / 2, 48)
                    .translate((x, y, -1)))
    # bump-on feet
    if a.foot_d > 0:
        for x, y in L.feet:
            cuts.append(mf.Manifold.cylinder(a.foot_depth + 1, a.foot_d / 2 + 0.3,
                                             a.foot_d / 2 + 0.3, 64).translate((x, y, -1)))
    return body - mf.Manifold.batch_boolean(cuts, mf.OpType.Add)


# --------------------------------------------------------------------------
# the trim, in place on the base and laid out for printing
# --------------------------------------------------------------------------

def _cap(wall: mf.CrossSection, slot: mf.CrossSection, a, z_top: float) -> mf.Manifold:
    k = a.fit
    top = slab(wall, z_top, z_top + a.cap_t)
    tongue = slab(slot.offset(-k, mf.JoinType.Round, circular_segments=SEG),
                  z_top - a.slot_d + 0.4, z_top)
    return top + tongue


def trim_in_place(a, L: Layout) -> dict[str, mf.Manifold]:
    k = a.fit
    stage = slab(L.stage_slot.offset(-k, mf.JoinType.Round, circular_segments=SEG),
                 a.disc_h - a.ring_d, a.disc_h)
    # the band: the slot less clearance, opened at the back-left so it wraps on
    band_cs = L.outline.offset(-k * 0.5, mf.JoinType.Round, circular_segments=SEG) - \
        L.outline.offset(-a.band_depth, mf.JoinType.Round, circular_segments=SEG)
    gap = rrect(a.band_gap, 30, 0.01).rotate(45).translate(
        (-a.disc_r * math.cos(math.radians(45)), a.disc_r * math.sin(math.radians(45))))
    band = slab(band_cs - gap, a.band_z + k, a.band_z + a.band_h - k)
    return {
        "stage ring": stage,
        "side band": band,
        "tray rim": _cap(L.tray_wall, L.tray_slot, a, a.tray_h),
        "cup rim": _cap(L.cup_wall, L.cup_slot, a, a.cup_h),
    }


def trim_for_print(a, L: Layout, placed: dict[str, mf.Manifold]) -> dict[str, mf.Manifold]:
    """Every piece flat on the bed. They nest: the ring sits inside the band,
    the caps (flipped, so their tops are on the bed) inside the wing."""
    out = {}
    for name, m in placed.items():
        if name.endswith("rim"):
            x0, y0, z0, x1, y1, z1 = m.bounding_box()
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            m = m.translate((-cx, -cy, 0)).rotate((180, 0, 0)).translate((cx, cy, 0))
        out[name] = m.translate((0, 0, -m.bounding_box()[2]))
    return out


# --------------------------------------------------------------------------
# preview: flat-shaded, painter's algorithm, no dependencies past PIL
# --------------------------------------------------------------------------

def render(parts: list[tuple[mf.Manifold, tuple[int, int, int]]], path: Path,
           az=-35.0, el=28.0, size=900):
    import numpy as np
    from PIL import Image

    ca, sa = math.cos(math.radians(az)), math.sin(math.radians(az))
    ce, se = math.cos(math.radians(el)), math.sin(math.radians(el))
    # camera basis: right, up, toward viewer
    right = np.array([ca, sa, 0.0])
    fwd = np.array([-sa * ce, ca * ce, -se])          # into the screen
    up = np.cross(right, fwd)
    light = np.array([-0.4, -0.7, 0.9])
    light /= np.linalg.norm(light)

    tris, cols = [], []
    for m, rgb in parts:
        mesh = m.to_mesh()
        v = mesh.vert_properties[:, :3]
        t = v[mesh.tri_verts]
        tris.append(t)
        cols.append(np.tile(np.array(rgb, float), (len(t), 1)))
    t = np.concatenate(tris)
    col = np.concatenate(cols)
    n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    vis = n @ fwd < 0
    t, n, col = t[vis], n[vis], col[vis]
    shade = 0.35 + 0.65 * np.clip(n @ light, 0, 1)
    col = np.clip(col * shade[:, None] + 18, 0, 255)

    sx, sy, depth = t @ right, t @ up, t @ fwd
    lo_x, hi_x, lo_y, hi_y = sx.min(), sx.max(), sy.min(), sy.max()
    pad = 0.06
    scale = size * (1 - 2 * pad) / max(hi_x - lo_x, hi_y - lo_y)
    W = int((hi_x - lo_x) * scale + 2 * pad * size)
    H = int((hi_y - lo_y) * scale + 2 * pad * size)
    px = (sx - lo_x) * scale + pad * size
    py = H - ((sy - lo_y) * scale + pad * size)

    # a z-buffer, so trim sitting in a slot doesn't fight the slot's walls
    zbuf = np.full((H, W), np.inf)
    rgb = np.empty((H, W, 3))
    rgb[:] = (236, 238, 242)
    for i in range(len(t)):
        xs, ys, zs = px[i], py[i], depth[i]
        bx0, bx1 = max(int(xs.min()), 0), min(int(xs.max()) + 2, W)
        by0, by1 = max(int(ys.min()), 0), min(int(ys.max()) + 2, H)
        if bx0 >= bx1 or by0 >= by1:
            continue
        gx, gy = np.meshgrid(np.arange(bx0, bx1) + 0.5, np.arange(by0, by1) + 0.5)
        (x0, x1, x2), (y0, y1, y2) = xs, ys
        den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(den) < 1e-9:
            continue
        w0 = ((y1 - y2) * (gx - x2) + (x2 - x1) * (gy - y2)) / den
        w1 = ((y2 - y0) * (gx - x2) + (x0 - x2) * (gy - y2)) / den
        w2 = 1 - w0 - w1
        inside = (w0 >= -1e-3) & (w1 >= -1e-3) & (w2 >= -1e-3)
        z = w0 * zs[0] + w1 * zs[1] + w2 * zs[2]
        win = zbuf[by0:by1, bx0:bx1]
        hit = inside & (z < win)
        win[hit] = z[hit]
        rgb[by0:by1, bx0:bx1][hit] = col[i]
    img = Image.fromarray(rgb.astype(np.uint8))
    img.save(path)


# --------------------------------------------------------------------------

def build_parser():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", type=Path, default=HERE / "models")
    p.add_argument("--body", default="#161616", help="base colour (hex)")
    p.add_argument("--trim", default="#F5C400", help="trim colour (hex)")

    g = p.add_argument_group("stage (mm)")
    g.add_argument("--disc-r", type=float, default=62, help="radius of the round stage")
    g.add_argument("--disc-h", type=float, default=20)
    g.add_argument("--chamfer", type=float, default=1.5)

    g = p.add_argument_group("figure mount (mm)")
    g.add_argument("--dog-x", type=float, default=0, help="centre between the boots")
    g.add_argument("--dog-y", type=float, default=0)
    g.add_argument("--boot-spacing", type=float, default=44, help="boot centre to boot centre")
    g.add_argument("--screw-d", type=float, default=4.5, help="clearance hole (M4)")
    g.add_argument("--head-d", type=float, default=8.6, help="countersink diameter")
    g.add_argument("--head-recess", type=float, default=3.0,
                   help="how far the screw head sits up inside the base")

    g = p.add_argument_group("organiser (mm)")
    g.add_argument("--pad", type=float, default=76, help="sticky-note pad size (76 = 3 in)")
    g.add_argument("--pad-clearance", type=float, default=1.75)
    g.add_argument("--wall", type=float, default=4)
    g.add_argument("--wing-h", type=float, default=14, help="height of the organiser's platform")
    g.add_argument("--ledge", type=float, default=3.5, help="platform past the tray and cup")
    g.add_argument("--tray-h", type=float, default=36)
    g.add_argument("--tray-floor", type=float, default=22, help="height the pad sits at")
    g.add_argument("--notch-w", type=float, default=34)
    g.add_argument("--notch-floor", type=float, default=3, help="notch bottom above the tray floor")
    g.add_argument("--cup-r", type=float, default=21, help="pen cup outside radius")
    g.add_argument("--cup-h", type=float, default=64)
    g.add_argument("--cup-floor", type=float, default=10)
    g.add_argument("--cup-dx", type=float, default=8, help="cup offset right of the tray centre")
    g.add_argument("--cup-gap", type=float, default=4, help="space between the tray and the cup")

    g = p.add_argument_group("trim (mm)")
    g.add_argument("--fit", type=float, default=0.12,
                   help="clearance per side between trim and slot")
    g.add_argument("--slot-w", type=float, default=1.8, help="slot in the top of the walls")
    g.add_argument("--slot-d", type=float, default=2.5)
    g.add_argument("--cap-t", type=float, default=1.6, help="rim thickness above the wall")
    g.add_argument("--ring-w", type=float, default=3.2)
    g.add_argument("--ring-d", type=float, default=1.4)
    g.add_argument("--ring-inset", type=float, default=4.5, help="edge of disc to the ring")
    g.add_argument("--band-z", type=float, default=4)
    g.add_argument("--band-h", type=float, default=4)
    g.add_argument("--band-depth", type=float, default=1.6)
    g.add_argument("--band-gap", type=float, default=1.0, help="opening in the band")

    g = p.add_argument_group("feet")
    g.add_argument("--foot-d", type=float, default=10, help="bump-on diameter, 0 for none")
    g.add_argument("--foot-depth", type=float, default=1.0)
    return p


def main(argv=None) -> int:
    a = build_parser().parse_args(argv)
    out = a.out
    out.mkdir(parents=True, exist_ok=True)
    body_rgb, trim_rgb = _hex(a.body), _hex(a.trim)

    L = Layout(a)
    base = base_solid(a, L)
    placed = trim_in_place(a, L)
    flat = trim_for_print(a, L, placed)

    x0, y0, _, x1, y1, z1 = base.bounding_box()
    origin = (-x0 + 20, -y0 + 20)
    stem = "mascot_stand"
    (out / f"{stem}_base.3mf").write_bytes(parts_to_3mf(
        [Part("base", 1, body_rgb, base)], origin=origin, name="mascot stand base"))
    (out / f"{stem}_base.stl").write_bytes(mesh_to_stl(base, header="mascot stand base"))
    (out / f"{stem}_trim.3mf").write_bytes(parts_to_3mf(
        [Part(n, 1, trim_rgb, m) for n, m in flat.items()], origin=origin,
        name="mascot stand trim"))
    for n, m in flat.items():
        (out / f"{stem}_trim_{n.replace(' ', '_')}.stl").write_bytes(
            mesh_to_stl(m, header=f"mascot stand {n}"))
    (out / f"{stem}_assembled.3mf").write_bytes(parts_to_3mf(
        [Part("base", 1, body_rgb, base)]
        + [Part(n, 2, trim_rgb, m) for n, m in placed.items()],
        origin=origin, name="mascot stand"))

    render([(base, body_rgb)] + [(m, trim_rgb) for m in placed.values()],
           out / f"{stem}_assembled_preview.png")
    render([(base, body_rgb)], out / f"{stem}_base_preview.png", az=-35, el=40)
    render([(m, trim_rgb) for m in flat.values()], out / f"{stem}_trim_preview.png",
           az=0, el=70)

    tv = sum(m.volume() for m in flat.values())
    print(f"wrote {out}/")
    print(f"  base  {x1 - x0:.0f} x {y1 - y0:.0f} x {z1:.0f} mm, "
          f"{base.volume() / 1000:.0f} cm3 solid")
    tx0, ty0, _, tx1, ty1, tz1 = mf.Manifold.batch_boolean(
        list(flat.values()), mf.OpType.Add).bounding_box()
    print(f"  trim  {tx1 - tx0:.0f} x {ty1 - ty0:.0f} x {tz1:.1f} mm plate, "
          f"{tv / 1000:.1f} cm3 ({tv * 1.24 / 1000:.0f} g PLA)")
    print(f"  pad tray {a.pad + 2 * a.pad_clearance:.1f} mm inside, "
          f"{a.tray_h - a.tray_floor:.0f} mm deep; pen cup {2 * (a.cup_r - a.wall):.0f} mm across, "
          f"{a.cup_h - a.cup_floor:.0f} mm deep")
    print(f"  figure: M4 countersunk screws {a.boot_spacing:.0f} mm apart at "
          f"({a.dog_x:.0f}, {a.dog_y:.0f}) from the stage centre")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
