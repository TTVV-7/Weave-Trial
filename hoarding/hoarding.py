#!/usr/bin/env python3
"""A temporary rain-cover hoarding over the generator / tank compound.

    python hoarding/hoarding.py                      # write the STEP + preview
    python hoarding/hoarding.py --length 14000 --width 9000 --eaves 4500

A free-standing steel canopy: SHS posts on base plates set just outside the
compound wall, duo-pitch RHS rafters, a ridge beam, purlins, trapezoidal roof
sheeting with an overhang, eaves gutters and downpipes, and side cladding that
skirts down to just above the existing wall. One gable end is left open so the
trailers can be towed in and out. All dimensions are in millimetres; X runs
along the compound, Y across it, Z up, with the origin at the inside corner of
the compound floor.

Needs CadQuery (`pip install cadquery`).
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path

import cadquery as cq

HERE = Path(__file__).resolve().parent

STEEL = cq.Color(0.42, 0.45, 0.48)
SHEET = cq.Color(0.20, 0.36, 0.55)
CLAD = cq.Color(0.82, 0.84, 0.86)
GUTTER = cq.Color(0.15, 0.15, 0.15)


@dataclass
class Spec:
    length: float = 12000      # inside length of the compound (X)
    width: float = 8000        # inside width of the compound (Y)
    wall_height: float = 1200  # existing compound wall; cladding stops above it
    post_offset: float = 400   # posts sit this far outside the wall line
    eaves: float = 4000        # underside of eaves beam, clears the tank flue
    pitch: float = 10.0        # roof pitch, degrees
    bay: float = 3000          # target post spacing along X
    purlin_spacing: float = 1200
    overhang: float = 300      # roof sheet past the frame at eaves and gables
    skirt_gap: float = 300     # gap between top of wall and bottom of cladding
    open_end: str = "x+"       # gable left open for trailer access: x+, x- or none


def beam(p1, p2, b, h, t=None, up=(0, 0, 1)):
    """A rectangular (optionally hollow) section from p1 to p2. `h` is measured
    in the plane containing `up`."""
    v1, v2 = cq.Vector(*p1), cq.Vector(*p2)
    d = v2 - v1
    n = d.normalized()
    side = n.cross(cq.Vector(*up))
    if side.Length < 1e-9:          # vertical member
        side = cq.Vector(1, 0, 0)
    wp = cq.Workplane(cq.Plane(origin=v1, xDir=side.normalized(), normal=n)).rect(b, h)
    if t:
        wp = wp.rect(b - 2 * t, h - 2 * t)
    return wp.extrude(d.Length).val()


def trapezoidal(width, pitch=200.0, rib=32.0, crest=40.0, t=0.7):
    """Points of a trapezoidal sheet profile `width` wide, as (u, v) pairs:
    ribs up in +v, closed into a solid of thickness t."""
    n = max(1, round(width / pitch))
    p = width / n
    flank = (p - crest) / 2 * 0.35
    top = []
    for i in range(n):
        x0 = i * p
        valley = (p - crest - 2 * flank) / 2
        top += [(x0, 0), (x0 + valley, 0), (x0 + valley + flank, rib),
                (x0 + valley + flank + crest, rib), (x0 + valley + 2 * flank + crest, 0)]
    top.append((width, 0))
    bottom = [(u, v - t) for u, v in reversed(top)]
    return top + bottom


def sheet(origin, x_dir, normal, width, length, **kw):
    """Profiled sheet: profile laid out along x_dir, ribs toward the plane's
    y, extruded `length` along normal."""
    plane = cq.Plane(origin=cq.Vector(*origin), xDir=cq.Vector(*x_dir), normal=cq.Vector(*normal))
    return cq.Workplane(plane).polyline(trapezoidal(width, **kw)).close().extrude(length).val()


def build(s: Spec) -> cq.Assembly:
    asm = cq.Assembly(name="Rain_Hoarding")
    tan = math.tan(math.radians(s.pitch))

    y0, y1 = -s.post_offset, s.width + s.post_offset          # post centrelines
    x0, x1 = -s.post_offset, s.length + s.post_offset
    span = y1 - y0
    half = span / 2
    ridge_y = y0 + half
    nbays = max(1, round((x1 - x0) / s.bay))
    xs = [x0 + i * (x1 - x0) / nbays for i in range(nbays + 1)]

    post, post_t = 100, 5         # 100x100x5 SHS
    raft_b, raft_h, raft_t = 75, 150, 5   # 150x75x5 RHS
    eaves_z = s.eaves
    top_of_raft = lambda y: eaves_z + raft_h / 2 + (half - abs(y - ridge_y)) * tan

    # posts, base plates, knee braces, rafters
    for i, x in enumerate(xs):
        for j, y in enumerate((y0, y1)):
            asm.add(beam((x, y, 15), (x, y, eaves_z), post, post, post_t),
                    name=f"post_{i}_{j}", color=STEEL)
            plate = cq.Workplane().box(300, 300, 15).translate((x, y, 7.5)).val()
            asm.add(plate, name=f"base_plate_{i}_{j}", color=STEEL)
            inward = 1 if j == 0 else -1
            asm.add(beam((x, y + inward * post / 2, eaves_z - 700),
                         (x, y + inward * 700, eaves_z + 700 * tan),
                         60, 60, 4),
                    name=f"knee_brace_{i}_{j}", color=STEEL)
        zc = eaves_z + raft_h / 2
        asm.add(beam((x, y0, zc), (x, ridge_y, zc + half * tan), raft_b, raft_h, raft_t),
                name=f"rafter_{i}_a", color=STEEL)
        asm.add(beam((x, y1, zc), (x, ridge_y, zc + half * tan), raft_b, raft_h, raft_t),
                name=f"rafter_{i}_b", color=STEEL)

    # eaves beams and ridge
    for j, y in enumerate((y0, y1)):
        asm.add(beam((x0 - post / 2, y, eaves_z - 75), (x1 + post / 2, y, eaves_z - 75), 75, 150, 5),
                name=f"eaves_beam_{j}", color=STEEL)
    ridge_z = eaves_z + raft_h / 2 + half * tan
    asm.add(beam((x0, ridge_y, ridge_z), (x1, ridge_y, ridge_z), 100, 100, 5),
            name="ridge_beam", color=STEEL)

    # purlins (100x50 C approximated as RHS), sat on the rafters
    slope_len = half / math.cos(math.radians(s.pitch))
    npur = max(2, math.ceil(slope_len / s.purlin_spacing) + 1)
    for k in range(npur):
        dist = 50 + k * (half - 100) / (npur - 1)
        for side, sign in (("a", -1), ("b", 1)):
            y = ridge_y + sign * (half - dist)
            z = top_of_raft(y) + 50
            asm.add(beam((x0 - s.overhang / 2, y, z), (x1 + s.overhang / 2, y, z), 50, 100, 2.5),
                    name=f"purlin_{side}_{k}", color=STEEL)

    # roof sheets: ribs run down the slope, one sheet run per side
    roof_z = top_of_raft(y0) + 100
    run = (half + s.overhang) / math.cos(math.radians(s.pitch))
    rx0, rlen = x0 - s.overhang, (x1 - x0) + 2 * s.overhang
    rz = roof_z + half * tan
    for side, sign in (("a", -1), ("b", 1)):
        down = (0, sign * math.cos(math.radians(s.pitch)), -math.sin(math.radians(s.pitch)))
        xdir = (1, 0, 0) if sign < 0 else (-1, 0, 0)
        origin = (rx0 if sign < 0 else rx0 + rlen, ridge_y, rz + 1)
        asm.add(sheet(origin, xdir, down, rlen, run), name=f"roof_sheet_{side}", color=SHEET)
    # ridge capping
    cap = (cq.Workplane("YZ").polyline([(-250, -250 * tan), (0, 0), (250, -250 * tan),
                                       (250, -250 * tan + 1), (0, 1), (-250, -250 * tan + 1)])
           .close().extrude(rlen).translate((rx0, ridge_y, rz + 40)).val())
    asm.add(cap, name="ridge_capping", color=SHEET)

    # gutters and downpipes
    gutter_z = roof_z - s.overhang * tan - 60
    for j, (y, sign) in enumerate(((y0 - s.overhang, 1), (y1 + s.overhang, -1))):
        g = (cq.Workplane("YZ").polyline([(-60, 0), (60, 0), (60, 100), (57, 100), (57, 3),
                                         (-57, 3), (-57, 100), (-60, 100)])
             .close().extrude(rlen).translate((rx0, y + sign * 30, gutter_z)).val())
        asm.add(g, name=f"gutter_{j}", color=GUTTER)
        for k, x in enumerate((x0, x1)):
            dp = cq.Workplane().circle(34).circle(31).extrude(gutter_z).translate((x, y + sign * 30, 0)).val()
            asm.add(dp, name=f"downpipe_{j}_{k}", color=GUTTER)

    # cladding: ribs vertical, hung off the outside face of the posts
    clad_bot = s.wall_height + s.skirt_gap
    clad_top = eaves_z
    h = clad_top - clad_bot
    off = post / 2 + 50   # rails sit 50 mm proud of the posts
    for j, (y, sign) in enumerate(((y0, -1), (y1, 1))):
        for z in (clad_bot + 150, (clad_bot + clad_top) / 2, clad_top - 150):
            asm.add(beam((x0, y + sign * (post / 2 + 25), z), (x1, y + sign * (post / 2 + 25), z), 50, 100, 2.5),
                    name=f"side_rail_{j}_{int(z)}", color=STEEL)
        # ribs point along normal x xdir, so pick xdir to put them outward
        xdir = (-1, 0, 0) if sign < 0 else (1, 0, 0)
        origin = (x1 + post / 2 if sign < 0 else x0 - post / 2, y + sign * off, clad_bot)
        asm.add(sheet(origin, xdir, (0, 0, 1), (x1 - x0) + post, h), name=f"side_cladding_{j}", color=CLAD)

    ends = {"x-": (x0, -1), "x+": (x1, 1)}
    for key, (x, sign) in ends.items():
        if key == s.open_end:
            continue
        for z in (clad_bot + 150, (clad_bot + clad_top) / 2, clad_top - 150):
            asm.add(beam((x + sign * (post / 2 + 25), y0, z), (x + sign * (post / 2 + 25), y1, z), 50, 100, 2.5),
                    name=f"end_rail_{key}_{int(z)}", color=STEEL)
        ydir = (0, 1, 0) if sign < 0 else (0, -1, 0)
        origin = (x + sign * off, y0 - post / 2 if sign < 0 else y1 + post / 2, clad_bot)
        asm.add(sheet(origin, ydir, (0, 0, 1), span + post, h), name=f"end_cladding_{key}", color=CLAD)
        # gable triangle above the eaves
        tri = (cq.Workplane("YZ").polyline([(y0 - post / 2, eaves_z), (y1 + post / 2, eaves_z),
                                            (ridge_y, ridge_z + 50)]).close()
               .extrude(2).translate((x + sign * off, 0, 0)).val())
        asm.add(tri, name=f"gable_{key}", color=CLAD)

    return asm


def preview(asm: cq.Assembly, s: Spec, out: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    fig = plt.figure(figsize=(12, 9), dpi=110)
    ax = fig.add_subplot(projection="3d")
    for obj in [asm.objects[n] for n in asm.objects]:
        if obj.obj is None:
            continue
        col = obj.color.toTuple() if obj.color else (0.5, 0.5, 0.5, 1)
        verts, tris = obj.obj.tessellate(25, 0.5)
        polys = [[verts[a].toTuple(), verts[b].toTuple(), verts[c].toTuple()] for a, b, c in tris]
        alpha = 0.55 if "cladding" in obj.name or "gable" in obj.name or "roof" in obj.name else 1
        ax.add_collection3d(Poly3DCollection(polys, facecolor=col[:3], edgecolor="none",
                                             alpha=alpha, linewidths=0))
    # the compound wall and kit, for context only (not in the STEP)
    def ghost(x, y, z, dx, dy, dz, c):
        b = cq.Workplane().box(dx, dy, dz, centered=False).translate((x, y, z)).val()
        v, t = b.tessellate(10)
        ax.add_collection3d(Poly3DCollection([[v[i].toTuple() for i in tri] for tri in t],
                                             facecolor=c, edgecolor="k", linewidths=0.2, alpha=0.9))
    L, W, H = s.length, s.width, s.wall_height
    for args in ((-200, -200, 0, L + 400, 200, H), (-200, W, 0, L + 400, 200, H),
                 (-200, 0, 0, 200, W, H)):
        ghost(*args, (0.6, 0.6, 0.6))
    ghost(2200, 5600, 0, 2000, 1800, 2600, (0.85, 0.4, 0.15))    # tank
    ghost(5200, 5400, 0, 3600, 2000, 2300, (0.95, 0.75, 0.1))    # generator
    ghost(3600, 2400, 0, 3200, 1700, 2100, (0.85, 0.6, 0.1))     # generator
    span = max(L, W) + 2000
    ax.set_xlim(-1000, -1000 + span); ax.set_ylim(-1000 - (span - W - 2000) / 2, -1000 + span - (span - W - 2000) / 2)
    ax.set_zlim(0, span * 0.6)
    ax.set_box_aspect((1, 1, 0.6))
    ax.view_init(elev=28, azim=-58)
    ax.set_axis_off()
    ax.set_title(f"Rain hoarding  {L/1000:.1f} x {W/1000:.1f} m compound, eaves {s.eaves/1000:.1f} m, "
                 f"{s.pitch:g} deg duo-pitch, {s.open_end} end open")
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for f, v in Spec.__dataclass_fields__.items():
        p.add_argument("--" + f.replace("_", "-"), type=type(v.default), default=v.default)
    p.add_argument("--out", type=Path, default=HERE / "Rain_Hoarding.step")
    p.add_argument("--no-preview", action="store_true")
    a = p.parse_args()
    s = Spec(**{f: getattr(a, f) for f in Spec.__dataclass_fields__})
    asm = build(s)
    asm.save(str(a.out), exportType="STEP")
    print(f"wrote {a.out} ({len(asm.objects) - 1} parts)")
    if not a.no_preview:
        png = a.out.with_name(a.out.stem + "_preview.png")
        preview(asm, s, png)
        print(f"wrote {png}")


if __name__ == "__main__":
    main()
