#!/usr/bin/env python3
"""A bunded tarp for environmental spill protection under the batch plant.

    python tarp/esp_tarp.py                          # write the STEP + preview
    python tarp/esp_tarp.py --length 10000 --width 7000 --berm 200

A heavy-duty PVC/HDPE ground sheet that catches cement slurry, wash water and
fuel drips under the batch plant and holds them until they can be pumped out.
The sheet lies on a geotextile underlay (so stones don't puncture it) and its
edges are wrapped up and over timber kerbs to make a continuous bund, held
down with sandbags. On one long side the kerb is swapped for a low rubber
drive-over ramp with the sheet draped over it, so the loader can get in to
feed the plant without breaking the bund.

All dimensions are in millimetres; X runs along the tarp, Y across it, Z up,
with the origin at the centre of the tarp on the ground.

Needs CadQuery (`pip install cadquery`).
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import cadquery as cq

HERE = Path(__file__).resolve().parent

LINER = cq.Color(0.13, 0.30, 0.20)      # dark green PVC
GEO = cq.Color(0.55, 0.55, 0.58)        # grey geotextile
TIMBER = cq.Color(0.72, 0.58, 0.38)
RUBBER = cq.Color(0.12, 0.12, 0.12)
SANDBAG = cq.Color(0.80, 0.72, 0.52)


@dataclass
class Spec:
    length: float = 8000        # inside the bund (X)
    width: float = 6000         # inside the bund (Y)
    berm: float = 150           # kerb height = bund depth
    kerb_width: float = 150     # kerb timber width (150 x 150 sleeper)
    liner_t: float = 1.0        # 1 mm PVC / HDPE
    geo_t: float = 4.0          # non-woven geotextile underlay
    ramp_width: float = 4000    # drive-over opening on the -Y side; 0 for none
    ramp_depth: float = 900     # ramp front-to-back
    ramp_height: float = 75
    sandbag_spacing: float = 1500


def frame(x_in, y_in, w, h, z=0.0):
    """A rectangular ring: inside x_in by y_in, `w` wide, `h` tall."""
    outer = cq.Workplane().rect(x_in + 2 * w, y_in + 2 * w).extrude(h)
    inner = cq.Workplane().rect(x_in, y_in).extrude(h)
    return outer.cut(inner).translate((0, 0, z))


def build(s: Spec) -> cq.Assembly:
    asm = cq.Assembly(name="Batch_Plant_ESP_Tarp")
    L, W, k, h, t = s.length, s.width, s.kerb_width, s.berm, s.liner_t
    z_liner = s.geo_t
    z_kerb = z_liner + t

    # where the ramp replaces the kerb, on the -Y side
    gap = None
    if s.ramp_width > 0:
        gap = cq.Workplane().box(s.ramp_width, 4 * k + s.ramp_depth, 4 * h).translate((0, -W / 2, h))

    # geotextile underlay, a little bigger than the bund all round
    margin = 300
    geo = cq.Workplane().box(L + 2 * k + 2 * margin, W + 2 * k + 2 * margin, s.geo_t).translate((0, 0, s.geo_t / 2))
    asm.add(geo.val(), name="geotextile_underlay", color=GEO)

    # timber kerbs
    kerb = frame(L, W, k, h, z_kerb)
    if gap is not None:
        kerb = kerb.cut(gap)
    asm.add(kerb.val(), name="timber_kerbs", color=TIMBER)

    # the liner: a flat base, then up the inside of the kerb, over the top,
    # down the outside and out onto the ground as an apron, all one sheet
    apron = 200
    base = cq.Workplane().box(L + 2 * k + 2 * apron, W + 2 * k + 2 * apron, t).translate((0, 0, z_liner + t / 2))
    wrap = frame(L - 2 * t, W - 2 * t, k + 2 * t, h + t, z_kerb).cut(frame(L, W, k, h, z_kerb))
    if gap is not None:
        wrap = wrap.cut(gap)
    liner = base.union(wrap)

    if gap is not None:
        # rubber drive-over ramp: a low trapezoid across the opening, with
        # the sheet draped over it so the bund stays continuous
        d, rh = s.ramp_depth, s.ramp_height
        prof = [(-d / 2, 0), (d / 2, 0), (d / 6, rh), (-d / 6, rh)]
        y_ramp = -W / 2 - k / 2
        ramp = (cq.Workplane("YZ").polyline(prof).close().extrude(s.ramp_width + 2 * k)
                .translate((-s.ramp_width / 2 - k, y_ramp, z_kerb)))
        asm.add(ramp.val(), name="drive_over_ramp", color=RUBBER)
        skin_prof = [(-d / 2 - 2 * t, 0), (d / 2 + 2 * t, 0), (d / 6 + t, rh + t), (-d / 6 - t, rh + t)]
        skin = (cq.Workplane("YZ").polyline(skin_prof).close().extrude(s.ramp_width)
                .translate((-s.ramp_width / 2, y_ramp, z_kerb)).cut(ramp))
        liner = liner.union(skin)
    asm.add(liner.val(), name="pvc_liner", color=LINER)

    # sandbags on the kerb tops, skipping the ramp
    bag = cq.Workplane().box(550, 300, 110).edges().fillet(45)
    z_bag = z_kerb + h + t + 55
    n = 0
    for side, y in (("n", W / 2 + k / 2), ("s", -W / 2 - k / 2)):
        count = max(2, round((L + 2 * k) / s.sandbag_spacing) + 1)
        for i in range(count):
            x = -L / 2 - k / 2 + i * (L + k) / (count - 1)
            if gap is not None and side == "s" and abs(x) < s.ramp_width / 2 + 300:
                continue
            asm.add(bag.translate((x, y, z_bag)).val(), name=f"sandbag_{n}", color=SANDBAG)
            n += 1
    for side, x in (("e", L / 2 + k / 2), ("w", -L / 2 - k / 2)):
        count = max(2, round((W + 2 * k) / s.sandbag_spacing) + 1)
        for i in range(1, count - 1):
            y = -W / 2 - k / 2 + i * (W + k) / (count - 1)
            asm.add(bag.rotate((0, 0, 0), (0, 0, 1), 90).translate((x, y, z_bag)).val(),
                    name=f"sandbag_{n}", color=SANDBAG)
            n += 1
    return asm


def preview(asm: cq.Assembly, s: Spec, out: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LightSource
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    fig = plt.figure(figsize=(12, 8), dpi=110)
    ax = fig.add_subplot(projection="3d")
    ls = LightSource(azdeg=315, altdeg=45)

    def split(tri, max_edge=400.0):
        """Matplotlib depth-sorts whole triangles, so the big flat sheets
        have to be cut small or they get drawn over the kerbs and bags."""
        a, b, c = tri
        e = [(a, b, c), (b, c, a), (c, a, b)]
        lens = [sum((p - q) ** 2 for p, q in zip(u, v)) for u, v, _ in e]
        i = lens.index(max(lens))
        if lens[i] <= max_edge ** 2:
            return [tri]
        u, v, w = e[i]
        m = tuple((p + q) / 2 for p, q in zip(u, v))
        return split((u, m, w), max_edge) + split((m, v, w), max_edge)

    # surfaces a few mm apart flicker through each other when depth-sorted:
    # draw only the border of underlay that shows past the liner, skip the
    # kerbs (the liner wraps them) and skip downward faces
    shown = {}
    for name in asm.objects:
        obj = asm.objects[name]
        if obj.obj is None or name == "timber_kerbs":
            continue
        shape = obj.obj
        if name == "geotextile_underlay":
            bb = asm.objects["pvc_liner"].obj.BoundingBox()
            shape = shape.cut(cq.Workplane().box(bb.xlen, bb.ylen, 100).val())
        shown[name] = (shape, obj.color)

    polys, cols = [], []
    for shape, color in shown.values():
        col = color.toTuple()[:3] if color else (0.5, 0.5, 0.5)
        verts, tris = shape.tessellate(5, 0.5)
        for a, b, c in tris:
            pa, pb, pc = verts[a], verts[b], verts[c]
            n = (pb - pa).cross(pc - pa)
            if n.Length < 1e-9 or n.z / n.Length < -0.5:
                continue
            for tri in split((pa.toTuple(), pb.toTuple(), pc.toTuple())):
                polys.append(tri)
                cols.append(col)
    ax.add_collection3d(Poly3DCollection(polys, facecolors=cols, edgecolor="none", linewidths=0,
                                         shade=True, lightsource=ls))
    span = max(s.length, s.width) / 2 + 800
    # heights drawn 4x so the bund reads at this scale
    ax.set_xlim(-span, span); ax.set_ylim(-span, span); ax.set_zlim(0, span / 4)
    ax.set_box_aspect((1, 1, 0.25))
    ax.view_init(elev=30, azim=-60)
    ax.set_axis_off()
    vol = s.length * s.width * s.berm / 1e9
    ax.set_title(f"Batch plant ESP tarp  {s.length/1000:.1f} x {s.width/1000:.1f} m inside, "
                 f"{s.berm:g} mm bund (~{vol:.1f} m3), drive-over ramp {s.ramp_width/1000:.1f} m")
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for f, v in Spec.__dataclass_fields__.items():
        p.add_argument("--" + f.replace("_", "-"), type=type(v.default), default=v.default)
    p.add_argument("--out", type=Path, default=HERE / "Batch_Plant_ESP_Tarp.step")
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
