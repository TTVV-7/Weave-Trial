#!/usr/bin/env python3
"""A 1 tonne bulk bag (FIBC) of dry concrete mix, as a STEP model.

    python bulkbag/bulk_bag.py                       # bag on a pallet + bag alone
    python bulkbag/bulk_bag.py --width 1000 --height 1100

A woven polypropylene bulk bag filled with dry concrete mix: a 900 x 900 base
that bulges out at the sides once filled, a domed top gathered into a tied
fill spout, four lift loops on the corner seams and a document pocket on one
face. By default it sits on a 1200 x 1000 timber pallet; a second file has the
bag on its own for stacking or placing straight on the ground.

1 t of dry mix at ~1.6 t/m3 is about 0.63 m3, which a 900 x 900 bag holds at
roughly 800-900 mm filled height. All dimensions are in millimetres, Z up,
with the origin at the centre of the footprint on the ground.

Needs CadQuery (`pip install cadquery`).
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path

import cadquery as cq

HERE = Path(__file__).resolve().parent

BAG = cq.Color(0.93, 0.93, 0.90)        # white woven PP
LOOP = cq.Color(0.20, 0.40, 0.75)       # blue lift loops
TIE = cq.Color(0.15, 0.15, 0.15)
POCKET = cq.Color(0.95, 0.80, 0.15)
TIMBER = cq.Color(0.72, 0.58, 0.38)


@dataclass
class Spec:
    width: float = 900          # empty bag base, square
    height: float = 850         # filled body height, base to shoulder
    bulge: float = 60           # how far each side bows out when full
    dome: float = 120           # top crowning above the shoulder
    loop_height: float = 250    # lift loops stand this far above the shoulder
    spout_dia: float = 350
    pallet: bool = True         # 1200 x 1000 UK pallet under the bag


def rrect(w, d, r):
    return cq.Sketch().rect(w, d).vertices().fillet(min(r, w / 2 - 1, d / 2 - 1))


def body(s: Spec):
    """Loft through rounded-square sections: tucked in at the base, bulging
    at mid-height, back in at the shoulder, then crowned into the spout."""
    w, h, b = s.width, s.height, s.bulge
    sections = [
        (0.0, w - 20, 90),
        (0.12 * h, w + 0.7 * b, 140),
        (0.45 * h, w + 2 * b, 180),
        (0.80 * h, w + 1.2 * b, 160),
        (h, w - 10, 120),
        (h + 0.6 * s.dome, 0.62 * w, 160),
        (h + s.dome, s.spout_dia + 40, s.spout_dia / 2),
    ]
    wp = cq.Workplane()
    sk = [rrect(size, size, r).moved(cq.Location(cq.Vector(0, 0, z))) for z, size, r in sections]
    return wp.placeSketch(*sk).loft(ruled=False).val()


def spout(s: Spec, z0):
    """The fill spout: gathered, tied off, and flopped over a little."""
    r = s.spout_dia / 2 - 40
    neck = cq.Workplane().circle(r).workplane(offset=60).circle(r * 0.55).loft().translate((0, 0, z0)).val()
    tie = cq.Workplane().circle(r * 0.58).circle(r * 0.50).extrude(18).translate((0, 0, z0 + 50)).val()
    tail = (cq.Workplane().circle(r * 0.55).workplane(offset=90).center(30, 0).circle(r * 0.7)
            .loft().translate((0, 0, z0 + 60)).val())
    return neck, tie, tail


def lift_loop(s: Spec, corner_xy, angle, z_base):
    """A flat 70 mm webbing loop, sewn down the corner seam and standing up
    as an arch above the shoulder."""
    leg = 180                                         # sewn length down the seam
    half = 90
    path = (cq.Workplane("XZ").moveTo(-half, -leg).lineTo(-half, 0)
            .threePointArc((0, s.loop_height), (half, 0)).lineTo(half, -leg))
    # the webbing section sits at the start of the path, facing along it
    strap = (cq.Workplane("XY", origin=(-half, 0, -leg)).rect(6, 70)
             .sweep(path, transition="round"))
    x, y = corner_xy
    return (strap.val().rotate((0, 0, 0), (0, 0, 1), angle)
            .translate((x, y, z_base)))


def pallet_parts(length=1200, width=1000):
    """A UK four-way block pallet: top deck, 9 blocks, bottom boards."""
    parts = []
    top_t, block_h, bot_t = 22, 100, 22
    z_block = bot_t
    z_top = bot_t + block_h
    # bottom boards along X
    for y in (-width / 2 + 50, 0, width / 2 - 50):
        parts.append(cq.Workplane().box(length, 100, bot_t).translate((0, y, bot_t / 2)).val())
    # 9 blocks
    for x in (-length / 2 + 72.5, 0, length / 2 - 72.5):
        for y in (-width / 2 + 50, 0, width / 2 - 50):
            parts.append(cq.Workplane().box(145, 100, block_h).translate((x, y, z_block + block_h / 2)).val())
    # stringer boards along Y on top of the blocks
    for x in (-length / 2 + 72.5, 0, length / 2 - 72.5):
        parts.append(cq.Workplane().box(145, width, 22).translate((x, 0, z_top + 11)).val())
    # top deck boards along X
    n = 7
    for i in range(n):
        y = -width / 2 + 72.5 + i * (width - 145) / (n - 1)
        parts.append(cq.Workplane().box(length, 145 if i in (0, n - 1) else 100, top_t)
                     .translate((0, y, z_top + 22 + top_t / 2)).val())
    return parts, z_top + 22 + top_t


def build(s: Spec) -> cq.Assembly:
    asm = cq.Assembly(name="Bulk_Bag_Concrete")
    z0 = 0.0
    if s.pallet:
        boards, z0 = pallet_parts()
        asm.add(cq.Compound.makeCompound(boards), name="pallet_1200x1000", color=TIMBER)

    asm.add(body(s).translate((0, 0, z0)), name="bag_body", color=BAG)
    for name, part, col in zip(("spout", "spout_tie", "spout_tail"),
                               spout(s, z0 + s.height + s.dome - 5), (BAG, TIE, BAG)):
        asm.add(part, name=name, color=col)

    # loops sit on the rounded corner of the shoulder, on the diagonal
    a, r = (s.width - 10) / 2, 120
    c = ((a - r) * math.sqrt(2) + r + 8) / math.sqrt(2)
    for i, (sx, sy) in enumerate(((1, 1), (-1, 1), (-1, -1), (1, -1))):
        ang = math.degrees(math.atan2(sy, sx)) + 90
        asm.add(lift_loop(s, (sx * c, sy * c), ang, z0 + s.height), name=f"lift_loop_{i}", color=LOOP)

    # document pocket on the +X face, at the widest part of the bulge
    face_x = (s.width + 2 * s.bulge) / 2
    pocket = cq.Workplane().box(4, 260, 340).translate((face_x - 4, 0, z0 + 0.45 * s.height)).val()
    asm.add(pocket, name="document_pocket", color=POCKET)
    return asm


def preview(asm: cq.Assembly, out: Path, title: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from matplotlib.colors import LightSource

    fig = plt.figure(figsize=(8, 8), dpi=110)
    ax = fig.add_subplot(projection="3d")
    ls = LightSource(azdeg=315, altdeg=45)
    for obj in [asm.objects[n] for n in asm.objects]:
        if obj.obj is None:
            continue
        col = obj.color.toTuple()[:3] if obj.color else (0.5, 0.5, 0.5)
        verts, tris = obj.obj.tessellate(2, 0.3)
        polys = [[verts[a].toTuple(), verts[b].toTuple(), verts[c].toTuple()] for a, b, c in tris]
        pc = Poly3DCollection(polys, edgecolor="none", linewidths=0, shade=True,
                              lightsource=ls, facecolors=col)
        ax.add_collection3d(pc)
    ax.set_xlim(-700, 700); ax.set_ylim(-700, 700); ax.set_zlim(0, 1400)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=20, azim=-55)
    ax.set_axis_off()
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for f, v in Spec.__dataclass_fields__.items():
        if f == "pallet":
            continue
        p.add_argument("--" + f.replace("_", "-"), type=type(v.default), default=v.default)
    p.add_argument("--out-dir", type=Path, default=HERE)
    p.add_argument("--no-preview", action="store_true")
    a = p.parse_args()
    for pallet, stem in ((True, "Bulk_Bag_Concrete_on_Pallet"), (False, "Bulk_Bag_Concrete")):
        s = Spec(**{f: getattr(a, f) for f in Spec.__dataclass_fields__ if f != "pallet"}, pallet=pallet)
        asm = build(s)
        out = a.out_dir / f"{stem}.step"
        asm.export(str(out))
        print(f"wrote {out} ({len(asm.objects) - 1} parts)")
        if not a.no_preview:
            png = out.with_name(stem + "_preview.png")
            preview(asm, png, f"1 t bulk bag of dry concrete mix{' on 1200 x 1000 pallet' if pallet else ''}")
            print(f"wrote {png}")


if __name__ == "__main__":
    main()
