"""Hollow, two-piece versions of the strawberry and cloud, laid out for printing.

Run: python3 split.py   (after make_shapes.py works)
Writes stl/print/*.stl, one file per part per half, already turned so the cut
face is on the bed, plus a coupler ring for each, and halves.glb for the renders.

Strawberry: a 2 mm shell cut level at its widest point. Both halves print cut
face down, so no supports are needed outside, and any inside the dome come out
through the open cut before gluing. A separate coupler ring (12 mm tall, printed
flat) glues 6 mm into each half, so the halves line up and the joint is strong.
Keeping it separate lets both halves sit flat on their cut faces.

Cloud: a 2.5 mm shell cut front-to-back down the middle, with its own coupler
ring. Each half fits the U1's 270 mm bed turned about 45 degrees.
"""
from pathlib import Path
import numpy as np
import trimesh
import manifold3d as m3
import strawberry as sb
import make_shapes as ms

HERE = Path(__file__).parent
OUT = HERE / "stl" / "print"
OUT.mkdir(parents=True, exist_ok=True)
BERRY_WALL = 2.0
CLOUD_WALL = 2.5
LIP_H, LIP_T, GAP = 6.0, 1.8, 0.2     # alignment lip: height, thickness, sliding clearance


def man(mesh):
    return sb.man(mesh)


def coupler(cs):
    """A ring that follows the cavity outline at the cut, just inside the wall,
    2 * LIP_H tall: half of it slides into each half."""
    ring = cs.offset(-GAP, m3.JoinType.Round) - cs.offset(-GAP - LIP_T, m3.JoinType.Round)
    return m3.Manifold.extrude(ring, 2 * LIP_H)


# ---- strawberry -------------------------------------------------------------
def strawberry_halves():
    parts, _ = sb.strawberry(wall=BERRY_WALL)
    body = sb.body_solid()
    z_cut = 0.6 * sb.H - sb.FLAT            # widest point, in the shifted frame
    cavity = (sb.inner_solid(body, BERRY_WALL)).translate((0, 0, -sb.FLAT))
    ring = coupler(cavity.slice(z_cut)).translate((0, 0, z_cut - LIP_H))
    halves = {}
    for name, mesh in parts.items():
        mf = man(mesh)
        bot = mf.trim_by_plane((0, 0, -1), -z_cut)          # keep z <= z_cut
        top = mf.trim_by_plane((0, 0, 1), z_cut)            # keep z >= z_cut
        halves[f"{name}-bottom"] = bot
        halves[f"{name}-top"] = top
    halves["strawberry-ring"] = ring
    return halves, z_cut


# ---- cloud ------------------------------------------------------------------
def cloud_shells():
    """Outer cloud and the same puffs shrunk by the wall: a shell of even
    thickness with a closed flat underside."""
    W, t = ms.CLOUD_W, CLOUD_WALL
    puffs = [(x, 0, z, r, 0.55) for x, z, r in ms.PUFFS] + \
            [(x, y, z, r, 0.8) for x, y, z, r in ms.FRONT]
    def blob(shrink):
        out = None
        for x, y, z, r, sy in puffs:
            R = r * W
            s = m3.Manifold.sphere(1, 96).scale((R - shrink, R * sy - shrink, R - shrink)) \
                .translate((x * W, y * W, z * W))
            out = s if out is None else out + s
        return out
    floor = 0.06 * W
    cut = m3.Manifold.cube((W * 2, W * 2, W), True)
    outer = blob(0) - cut.translate((0, 0, -W / 2 + floor))
    inner = blob(t) - cut.translate((0, 0, -W / 2 + floor + t))
    return (outer - inner).translate((0, 0, -floor)), inner.translate((0, 0, -floor))


def cloud_halves():
    shell, inner = cloud_shells()
    # section of the cavity in the y=0 plane, as an x/z outline
    rot = inner.rotate((90, 0, 0))         # y -> z, so slicing at 0 cuts the y=0 plane
    ring = coupler(rot.slice(0)).translate((0, 0, -LIP_H)).rotate((-90, 0, 0))
    front = shell.trim_by_plane((0, -1, 0), 0)      # y <= 0
    back = shell.trim_by_plane((0, 1, 0), 0)        # y >= 0
    return {"cloud-front": front, "cloud-back": back, "cloud-ring": ring}


def to_bed(mf, rot):
    """Turn a half so its cut face is down, and drop it onto z = 0."""
    m = sb.tri(mf.rotate(rot))
    m.apply_translation((-m.bounds[:, 0].mean(), -m.bounds[:, 1].mean(), -m.bounds[0, 2]))
    return m


if __name__ == "__main__":
    berry, z_cut = strawberry_halves()
    cloud = cloud_halves()
    # print orientation: bottom berry half tip-up, top half leaves-up but resting on its cut
    layout = {}
    layout["strawberry-ring"] = to_bed(berry["strawberry-ring"], (0, 0, 0))
    group_bot = [k for k in berry if k.endswith("-bottom")]
    group_top = [k for k in berry if k.endswith("-top")]
    whole_bot = m3.Manifold.batch_boolean([berry[k] for k in group_bot], m3.OpType.Add)
    whole_top = m3.Manifold.batch_boolean([berry[k] for k in group_top], m3.OpType.Add)
    for keys, rot, whole in ((group_bot, (180, 0, 0), whole_bot), (group_top, (0, 0, 0), whole_top)):
        ref = sb.tri(whole.rotate(rot))
        off = (-ref.bounds[:, 0].mean(), -ref.bounds[:, 1].mean(), -ref.bounds[0, 2])
        for k in keys:
            m = sb.tri(berry[k].rotate(rot))
            if len(m.faces) == 0:
                continue
            m.apply_translation(off)
            layout[k] = m
    for k, rot in (("cloud-front", (-90, 0, 45)), ("cloud-back", (90, 0, 45)), ("cloud-ring", (90, 0, 45))):
        layout[k] = to_bed(cloud[k], rot)
    for k, m in layout.items():
        m = layout[k] = sb.drop_slivers(m)
        m.export(OUT / f"{k}.stl")
        e = m.extents
        print(f"{k:26s} {e[0]:5.0f} x {e[1]:5.0f} x {e[2]:5.0f} mm  {m.volume * 1.24 / 1000:5.0f} g"
              f"  watertight={m.is_watertight}")
    # assembled-but-apart halves for the renders
    colours = {"body": "#c4142c", "strawberry-ring": "#c4142c", "seeds": "#f2c230",
               "leaves": "#2f8a2f", "cloud": "#f4f6fa"}
    scene = trimesh.Scene()
    for k, mf in {**berry, **cloud}.items():
        m = sb.tri(mf)
        if len(m.faces) == 0:
            continue
        m = sb.drop_slivers(m)
        if len(m.faces) == 0:
            continue
        col = next(v for c, v in colours.items() if c in k)
        rgb = [int(col[i:i + 2], 16) for i in (1, 3, 5)]
        m.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(
            baseColorFactor=rgb + [255], roughnessFactor=0.55, metallicFactor=0.0, doubleSided=True))
        scene.add_geometry(m, geom_name=k, node_name=k)
    scene.export(HERE / "halves.glb")
    print(f"strawberry cut at {z_cut:.0f} mm")
