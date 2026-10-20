#!/usr/bin/env python3
"""A temporary rain-cover hoarding over the generator / tank compound.

    python hoarding/hoarding.py                      # write the STEP + preview
    python hoarding/hoarding.py --length 14000 --width 9000 --eaves 4500

A temporary roof built from scaffold tube and fittings, so it goes up and comes
down without any groundworks. 48.3 mm tube standards stand on base plates and
timber sole boards just outside the compound wall, held down by kentledge
blocks rather than foundations. 450 mm aluminium lattice beams span the
compound as a duo-pitch roof, carrying tube purlins, trapezoidal roof sheets,
gutters and downpipes. The long sides and the far end are wrapped in scaffold
sheeting down to just above the existing wall, on tube ledgers, with facade
and plan bracing in the end bays. One gable end is left open so the trailers
can be towed in and out.

Couplers are not modelled; every crossing of two tubes is a coupler. All
dimensions are in millimetres; X runs along the compound, Y across it, Z up,
with the origin at the inside corner of the compound floor.

Needs CadQuery (`pip install cadquery`).
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path

import cadquery as cq

HERE = Path(__file__).resolve().parent

TUBE = cq.Color(0.62, 0.64, 0.66)       # galvanised scaffold tube
ALU = cq.Color(0.78, 0.80, 0.82)        # aluminium lattice beams
SHEET = cq.Color(0.20, 0.36, 0.55)      # roof sheets
WRAP = cq.Color(0.92, 0.93, 0.95)       # scaffold sheeting
GUTTER = cq.Color(0.15, 0.15, 0.15)
TIMBER = cq.Color(0.70, 0.55, 0.35)
CONCRETE = cq.Color(0.55, 0.55, 0.52)

R = 48.3 / 2                            # scaffold tube, 48.3 x 4.0
WALL = 4.0
D = 48.3                                # centre-to-centre of two coupled tubes


@dataclass
class Spec:
    length: float = 12000      # inside length of the compound (X)
    width: float = 8000        # inside width of the compound (Y)
    wall_height: float = 1200  # existing compound wall; sheeting stops above it
    post_offset: float = 400   # standards sit this far outside the wall line
    eaves: float = 4000        # underside of the lattice beams, clears the tank flue
    pitch: float = 10.0        # roof pitch, degrees
    bay: float = 2500          # target standard spacing along X
    beam_depth: float = 450    # lattice beam, chord centre to chord centre
    purlin_spacing: float = 1200
    overhang: float = 300      # roof sheet past the frame at eaves and gables
    skirt_gap: float = 300     # gap between top of wall and bottom of sheeting
    lift: float = 2000         # max vertical spacing of ledgers
    open_end: str = "x+"       # gable left open for trailer access: x+, x- or none


def tube(p1, p2, r=R, t=WALL):
    """A hollow round tube from p1 to p2."""
    v1, v2 = cq.Vector(*p1), cq.Vector(*p2)
    d = v2 - v1
    wp = cq.Workplane(cq.Plane(origin=v1, normal=d.normalized())).circle(r)
    if t:
        wp = wp.circle(r - t)
    return wp.extrude(d.Length).val()


def compound(shapes):
    return cq.Compound.makeCompound(shapes)


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


def lattice(y_end, y_ridge, x, z_bot_end, z_bot_ridge, depth, panel=600):
    """A lattice beam in the plane x = const, from the eaves end to the ridge:
    two 48.3 chords `depth` apart with verticals and alternating diagonals."""
    n = max(2, round(abs(y_ridge - y_end) / panel))
    pts = [(y_end + (y_ridge - y_end) * i / n, z_bot_end + (z_bot_ridge - z_bot_end) * i / n)
           for i in range(n + 1)]
    bot = [(x, y, z) for y, z in pts]
    top = [(x, y, z + depth) for y, z in pts]
    parts = [tube(bot[0], bot[-1], t=3.2), tube(top[0], top[-1], t=3.2)]
    for i in range(n + 1):
        parts.append(tube(bot[i], top[i], r=19, t=2.5))
        if i < n:
            a, b = (bot[i], top[i + 1]) if i % 2 == 0 else (top[i], bot[i + 1])
            parts.append(tube(a, b, r=19, t=2.5))
    return compound(parts)


def build(s: Spec) -> cq.Assembly:
    asm = cq.Assembly(name="Rain_Hoarding")
    tan = math.tan(math.radians(s.pitch))

    y0, y1 = -s.post_offset, s.width + s.post_offset          # standard centrelines
    x0, x1 = -s.post_offset, s.length + s.post_offset
    span = y1 - y0
    half = span / 2
    ridge_y = y0 + half
    nbays = max(1, round((x1 - x0) / s.bay))
    xs = [x0 + i * (x1 - x0) / nbays for i in range(nbays + 1)]

    sole_t, plate_t = 38, 6
    foot = sole_t + plate_t
    eaves = s.eaves
    top_chord = lambda y: eaves + s.beam_depth + (half - abs(y - ridge_y)) * tan
    sheet_bot = s.wall_height + s.skirt_gap

    # ledger lifts: a kicker just off the ground, one at the bottom of the
    # sheeting, the eaves, and enough in between to keep lifts under s.lift
    lifts = [150, sheet_bot, eaves]
    gap = eaves - sheet_bot
    extra = math.ceil(gap / s.lift) - 1
    lifts += [sheet_bot + gap * (k + 1) / (extra + 1) for k in range(extra)]
    lifts.sort()

    # standards, base plates, sole boards, kentledge
    for i, x in enumerate(xs):
        for j, (y, out) in enumerate(((y0, -1), (y1, 1))):
            asm.add(tube((x, y, foot), (x, y, eaves + s.beam_depth)), name=f"standard_{i}_{j}", color=TUBE)
            asm.add(cq.Workplane().box(150, 150, plate_t).translate((x, y, sole_t + plate_t / 2)).val(),
                    name=f"base_plate_{i}_{j}", color=TUBE)
            asm.add(cq.Workplane().box(225, 600, sole_t).translate((x, y + out * 100, sole_t / 2)).val(),
                    name=f"sole_board_{i}_{j}", color=TIMBER)
            # 1000 x 500 x 500 concrete kentledge (~600 kg), tied back to the
            # standard with a short tube at the kicker lift
            ky = y + out * 650
            asm.add(cq.Workplane().box(1000, 500, 500).translate((x, ky, 250)).val(),
                    name=f"kentledge_{i}_{j}", color=CONCRETE)
            asm.add(tube((x + D, y, 150), (x + D, ky, 150)), name=f"kentledge_tie_{i}_{j}", color=TUBE)

    # lattice beams on every frame line, sat between the standards' heads
    for i, x in enumerate(xs):
        xb = x + D          # coupled to the side of the standard
        for side, y in (("a", y0), ("b", y1)):
            asm.add(lattice(y, ridge_y, xb, eaves, eaves + half * tan, s.beam_depth),
                    name=f"lattice_beam_{i}_{side}", color=ALU)
        asm.add(tube((xb, ridge_y, eaves + half * tan), (xb, ridge_y, top_chord(ridge_y))),
                name=f"ridge_post_{i}", color=TUBE)

    # ledgers along both long sides, outside the standards
    for j, (y, out) in enumerate(((y0, -1), (y1, 1))):
        for z in lifts:
            asm.add(tube((x0 - 300, y + out * D, z), (x1 + 300, y + out * D, z)),
                    name=f"ledger_{j}_{int(z)}", color=TUBE)
        # facade bracing, zig-zag up the end bays
        for b in (0, nbays - 1):
            xa, xc = xs[b], xs[b + 1]
            for k in range(len(lifts) - 1):
                lo, hi = (xa, xc) if (k + b) % 2 == 0 else (xc, xa)
                asm.add(tube((lo, y + out * 2 * D, lifts[k]), (hi, y + out * 2 * D, lifts[k + 1])),
                        name=f"facade_brace_{j}_{b}_{k}", color=TUBE)

    # purlins on the top chords, and plan bracing in the end bays
    slope_len = half / math.cos(math.radians(s.pitch))
    npur = max(2, math.ceil(slope_len / s.purlin_spacing) + 1)
    for k in range(npur):
        dist = 50 + k * (half - 100) / (npur - 1)
        for side, sign in (("a", -1), ("b", 1)):
            y = ridge_y + sign * (half - dist)
            z = top_chord(y) + D
            asm.add(tube((x0 - s.overhang, y, z), (x1 + s.overhang, y, z)),
                    name=f"purlin_{side}_{k}", color=TUBE)
    for b in (0, nbays - 1):
        for side, y in (("a", y0), ("b", y1)):
            asm.add(tube((xs[b] + D, y, top_chord(y) - D), (xs[b + 1] + D, ridge_y, top_chord(ridge_y) - D)),
                    name=f"plan_brace_{b}_{side}", color=TUBE)

    # roof sheets: ribs run down the slope, one sheet run per side
    rz = top_chord(ridge_y) + D + R + 1
    run = (half + s.overhang) / math.cos(math.radians(s.pitch))
    rx0, rlen = x0 - s.overhang, (x1 - x0) + 2 * s.overhang
    for side, sign in (("a", -1), ("b", 1)):
        down = (0, sign * math.cos(math.radians(s.pitch)), -math.sin(math.radians(s.pitch)))
        xdir = (1, 0, 0) if sign < 0 else (-1, 0, 0)
        origin = (rx0 if sign < 0 else rx0 + rlen, ridge_y, rz)
        asm.add(sheet(origin, xdir, down, rlen, run), name=f"roof_sheet_{side}", color=SHEET)
    cap = (cq.Workplane("YZ").polyline([(-250, -250 * tan), (0, 0), (250, -250 * tan),
                                       (250, -250 * tan + 1), (0, 1), (-250, -250 * tan + 1)])
           .close().extrude(rlen).translate((rx0, ridge_y, rz + 40)).val())
    asm.add(cap, name="ridge_capping", color=SHEET)

    # gutters, clipped to the eaves purlin, and downpipes into the compound drain
    gutter_z = rz - half * tan - s.overhang * tan - 60
    for j, (y, sign) in enumerate(((y0 - s.overhang, 1), (y1 + s.overhang, -1))):
        g = (cq.Workplane("YZ").polyline([(-60, 0), (60, 0), (60, 100), (57, 100), (57, 3),
                                         (-57, 3), (-57, 100), (-60, 100)])
             .close().extrude(rlen).translate((rx0, y + sign * 30, gutter_z)).val())
        asm.add(g, name=f"gutter_{j}", color=GUTTER)
        for k, x in enumerate((x0 - 150, x1 + 150)):
            dp = cq.Workplane().circle(34).circle(31).extrude(gutter_z).translate((x, y + sign * 30, 0)).val()
            asm.add(dp, name=f"downpipe_{j}_{k}", color=GUTTER)

    # scaffold sheeting on the outside of the ledgers
    wrap_top = top_chord(y0)
    wrap_t = 1.0
    for j, (y, out) in enumerate(((y0, -1), (y1, 1))):
        yw = y + out * (D + R + wrap_t / 2)
        asm.add(cq.Workplane().box(x1 - x0 + 600, wrap_t, wrap_top - sheet_bot)
                .translate(((x0 + x1) / 2, yw, (sheet_bot + wrap_top) / 2)).val(),
                name=f"side_sheeting_{j}", color=WRAP)

    for key, (x, out) in {"x-": (x0, -1), "x+": (x1, 1)}.items():
        if key == s.open_end:
            continue
        xl = x + out * D
        for z in lifts:
            asm.add(tube((xl, y0 - 300, z), (xl, y1 + 300, z)), name=f"end_ledger_{key}_{int(z)}", color=TUBE)
        for k in range(len(lifts) - 1):
            lo, hi = (y0, ridge_y) if k % 2 == 0 else (ridge_y, y0)
            asm.add(tube((x + out * 2 * D, lo, lifts[k]), (x + out * 2 * D, hi, lifts[k + 1])),
                    name=f"end_brace_{key}_{k}", color=TUBE)
        xw = x + out * (2 * D + R + wrap_t)
        asm.add(cq.Workplane().box(wrap_t, span + 600, wrap_top - sheet_bot)
                .translate((xw, ridge_y, (sheet_bot + wrap_top) / 2)).val(),
                name=f"end_sheeting_{key}", color=WRAP)
        tri = (cq.Workplane("YZ").polyline([(y0 - 300, wrap_top), (y1 + 300, wrap_top),
                                            (ridge_y, top_chord(ridge_y))]).close()
               .extrude(wrap_t).translate((xw, 0, 0)).val())
        asm.add(tri, name=f"gable_sheeting_{key}", color=WRAP)

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
        alpha = 0.45 if "sheeting" in obj.name or "roof" in obj.name else 1
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
    ax.view_init(elev=24, azim=-58)
    ax.set_axis_off()
    ax.set_title(f"Temporary rain hoarding (tube & fitting)  {L/1000:.1f} x {W/1000:.1f} m compound, "
                 f"eaves {s.eaves/1000:.1f} m, {s.pitch:g} deg duo-pitch, {s.open_end} end open")
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
    asm.export(str(a.out))
    print(f"wrote {a.out} ({len(asm.objects) - 1} parts)")
    if not a.no_preview:
        png = a.out.with_name(a.out.stem + "_preview.png")
        preview(asm, s, png)
        print(f"wrote {png}")


if __name__ == "__main__":
    main()
