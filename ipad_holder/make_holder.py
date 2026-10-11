"""The iPad holder with an M5 thread in its clamp, a wing screw for it, and
two logos inlaid in the back.

    python ipad_holder/make_holder.py

Reads ``source_ipad_holder.3mf`` and the two logo SVGs next to this file and
writes ``ipad_holder.3mf``, ``wing_screw.3mf`` / ``.stl`` and ``preview.png``.

The thread: the original 5.2 mm hole runs along x through the left corner of
the diamond loop, at y = 12, z = 6. The loop is a plain extrusion, so it is
rebuilt from its own cross-section (which fills the old hole) and an ISO-60
degree M5 x 0.8 thread is cut back in, opened up for printing so a printed
screw or a real steel M5 both go in.

The logos are cut 0.4 mm into the back face (the face on the bed) and kept as
their own parts, so a slicer opens the file with three filaments to assign.
On the back they are mirrored, so they read correctly from behind.
"""

from __future__ import annotations

import math
import os
import sys

import manifold3d as m3
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from phonecase import svgart                                    # noqa: E402
from phonecase.threemf import Part, parts_to_3mf               # noqa: E402

# --- thread ---------------------------------------------------------------
PITCH = 0.8
HOLE_AXIS = (12.0, 6.0)         # y, z of the clamp hole; it runs along x
HOLE_X = (172.0, 188.0)         # from outside the loop to inside its opening
# Radial limits of the two threads. ISO M5: internal minor 4.134, external
# major 5.0, external minor 4.019. The hole is opened and the screw shrunk
# so the two clear by about 0.12 mm on each flank.
HOLE_MINOR, HOLE_MAJOR = 4.35, 5.30
SCREW_MINOR, SCREW_MAJOR = 3.95, 4.80
FLANK_CLEAR = 0.12

# --- logos ----------------------------------------------------------------
INLAY_DEPTH = 0.4               # two 0.2 mm layers: enough to hide the base colour
# Where each logo goes, in model coordinates, and how wide its artwork is.
LOGOS = [
    # file, keep-dark?, centre x, centre y, width, part name, display colour
    ("logo_vaneye.svg", False, 189.6, -85.0, 105.0, "VanEye logo", (240, 240, 240)),
    ("logo_printyours.svg", True, 189.6, -172.0, 42.0, "printyours.ca logo", (20, 20, 20)),
]

# --- wing screw -----------------------------------------------------------
SHANK_LEN = 15.0                # threaded length: 4.3 mm of wall + reach
WING_SPAN = 30.0
WING_THICK = 3.2
HUB_D, HUB_H = 10.0, 9.0


def to_manifold(mesh: trimesh.Trimesh) -> m3.Manifold:
    return m3.Manifold(m3.Mesh(vert_properties=np.asarray(mesh.vertices, np.float32),
                               tri_verts=np.asarray(mesh.faces, np.uint32)))


def to_trimesh(solid: m3.Manifold) -> trimesh.Trimesh:
    m = solid.to_mesh()
    return trimesh.Trimesh(m.vert_properties[:, :3], m.tri_verts, process=False)


# --------------------------------------------------------------------------
# threads
# --------------------------------------------------------------------------

def threaded_rod(length: float, d_minor: float, d_major: float,
                 offset: float, *, segs: int = 72, steps: int = 20) -> m3.Manifold:
    """A rod along +z from 0 to ``length`` carrying a right-hand 60 degree thread.

    The surface is a radius that depends on angle and height: the sharp ISO
    triangle wave, moved out by ``offset`` (negative shrinks it), clipped to
    the minor and major radii. Moving along the helix keeps the same radius,
    which is what makes it a thread rather than a stack of rings.
    """
    H = PITCH * math.sqrt(3) / 2
    r_pitch = (5.0 - 0.6495 * PITCH) / 2          # basic M5 pitch radius
    r_lo = r_pitch - H / 2 + offset
    nz = max(2, int(math.ceil(length / PITCH * steps)))
    th = np.linspace(0, 2 * math.pi, segs, endpoint=False)
    z = np.linspace(0, length, nz + 1)
    T, Z = np.meshgrid(th, z)
    u = np.mod(Z - PITCH * T / (2 * math.pi), PITCH) / PITCH
    tri = 1 - np.abs(2 * u - 1)
    R = np.clip(r_lo + H * tri, d_minor / 2, d_major / 2)
    verts = np.c_[(R * np.cos(T)).ravel(), (R * np.sin(T)).ravel(), Z.ravel()]
    verts = np.vstack([verts, [0, 0, 0], [0, 0, length]])
    bot, top = len(verts) - 2, len(verts) - 1
    idx = np.arange((nz + 1) * segs).reshape(nz + 1, segs)
    a, b = idx[:-1], np.roll(idx[:-1], -1, axis=1)
    c, d = idx[1:], np.roll(idx[1:], -1, axis=1)
    faces = np.vstack([np.c_[a.ravel(), b.ravel(), d.ravel()],
                       np.c_[a.ravel(), d.ravel(), c.ravel()]])
    r0, r1 = idx[0], idx[-1]
    faces = np.vstack([faces,
                       np.c_[np.full(segs, bot), np.roll(r0, -1), r0],
                       np.c_[np.full(segs, top), r1, np.roll(r1, -1)]])
    mesh = trimesh.Trimesh(verts, faces, process=False)
    if mesh.volume < 0:
        mesh.invert()
    return to_manifold(mesh)


def hole_cutter() -> m3.Manifold:
    flank = FLANK_CLEAR * 2 / math.sqrt(3)        # radial shift for that flank gap
    rod = threaded_rod(HOLE_X[1] - HOLE_X[0], HOLE_MINOR, HOLE_MAJOR, +flank)
    # z -> x, then out to the hole's axis
    return rod.rotate([0, 90, 0]).translate([HOLE_X[0], *HOLE_AXIS])


# --------------------------------------------------------------------------
# holder
# --------------------------------------------------------------------------

def load_source():
    scene = trimesh.load(os.path.join(HERE, "source_ipad_holder.3mf"))
    return {name: g for name, g in scene.geometry.items()}


def rebuilt_loop(loop: trimesh.Trimesh) -> m3.Manifold:
    """The diamond loop from its own cross-section, with the old hole filled."""
    z0, z1 = loop.bounds[:, 2]
    sec = loop.section(plane_origin=[0, 0, z0 + 0.3], plane_normal=[0, 0, 1])
    loops = [np.asarray(e)[:, :2].tolist() for e in sec.discrete]
    cs = m3.CrossSection(loops, m3.FillRule.EvenOdd)
    return cs.extrude(z1 - z0).translate([0, 0, z0])


def logo_region(path: str, keep_dark: bool, cx: float, cy: float,
                width: float) -> m3.CrossSection:
    """The logo's ink as a 2-D region, placed and mirrored for the back face.

    Painter's rule from the top of the stack down: each shape counts only
    where nothing drawn after it covers it, and only the ink colour is kept
    (dark on a light logo, light on a dark one).
    """
    art = svgart.load_file(path, flatness=0.02)
    covered, ink = m3.CrossSection(), []
    for shape in reversed(art.shapes):
        loops = [sp for sp in shape.subpaths if len(sp) >= 3]
        if not loops:
            continue
        rule = m3.FillRule.EvenOdd if shape.even_odd else m3.FillRule.NonZero
        poly = m3.CrossSection(loops, rule)
        visible = poly - covered
        covered = covered + poly
        r, g, b = shape.rgb
        dark = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255 < 0.45
        if dark == keep_dark and not visible.is_empty():
            ink.append(visible)
    region = m3.CrossSection.batch_boolean(ink, m3.OpType.Add)
    x0, y0, x1, y1 = region.bounds()
    s = width / (x1 - x0)
    # Seen from behind, the model's +x runs to the viewer's left; the SVG's
    # y runs down. Scaling both by -s reads the right way round from the back.
    region = (region.translate([-(x0 + x1) / 2, -(y0 + y1) / 2])
                    .scale([-s, -s]).translate([cx, cy]))
    # Drop specks no nozzle could lay down.
    return m3.CrossSection.batch_boolean(
        [p for p in region.decompose() if p.area() > 0.05], m3.OpType.Add)


def build_holder():
    src = load_source()
    names = sorted(src, key=lambda n: -src[n].volume)
    frame, loop, neck = (src[n] for n in names)
    body = m3.Manifold.batch_boolean(
        [to_manifold(frame), rebuilt_loop(loop), to_manifold(neck)], m3.OpType.Add)
    body = body - hole_cutter()

    inlays = []
    for fname, keep_dark, cx, cy, w, label, rgb in LOGOS:
        region = logo_region(os.path.join(HERE, fname), keep_dark, cx, cy, w)
        solid = body ^ region.extrude(INLAY_DEPTH)
        inlays.append((label, rgb, solid))
    for _, _, solid in inlays:
        body = body - solid

    parts = [Part("Holder", 0, (90, 140, 200), body)]
    parts += [Part(label, i + 1, rgb, solid)
              for i, (label, rgb, solid) in enumerate(inlays)]
    return parts


# --------------------------------------------------------------------------
# wing screw
# --------------------------------------------------------------------------

def build_screw() -> m3.Manifold:
    """Printed head-down: wings flat on the bed, thread pointing up."""
    flank = FLANK_CLEAR * 2 / math.sqrt(3)
    # Wings: a bow-tie outline in the xz plane, extruded WING_THICK in y.
    lobe = m3.CrossSection.circle(4.5, 64)
    wing = m3.CrossSection.batch_hull([
        m3.CrossSection.square([HUB_D, HUB_H]).translate([-HUB_D / 2, 0]),
        lobe.translate([-(WING_SPAN / 2 - 4.5), 4.5]),
        lobe.translate([+(WING_SPAN / 2 - 4.5), 4.5]),
    ])
    # Waist the outline between hub and lobes so it reads as two wings.
    waist = m3.CrossSection.circle(6.0, 64)
    wing = wing - waist.translate([-8.6, HUB_H + 3.2]) - waist.translate([8.6, HUB_H + 3.2])
    wings = (wing.extrude(WING_THICK).translate([0, 0, -WING_THICK / 2])
             .rotate([90, 0, 0]))
    hub = m3.Manifold.cylinder(HUB_H, HUB_D / 2, HUB_D / 2, 64)
    collar = m3.Manifold.cylinder(1.0, 4.5, 4.5, 64).translate([0, 0, HUB_H])
    rod = threaded_rod(SHANK_LEN, SCREW_MINOR, SCREW_MAJOR, -flank)
    # Chamfer the tip so the thread starts cleanly.
    tip = m3.Manifold.cylinder(SHANK_LEN, SCREW_MAJOR / 2 + SHANK_LEN - 0.6,
                               SCREW_MAJOR / 2 - 0.6, 64)
    rod = (rod ^ tip).translate([0, 0, HUB_H + 1.0])
    return m3.Manifold.batch_boolean([wings, hub, collar, rod], m3.OpType.Add)


# --------------------------------------------------------------------------
# output
# --------------------------------------------------------------------------

def preview(parts, screw, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    fig = plt.figure(figsize=(16, 9))
    light = np.array([0.3, -0.5, 0.8]) / np.linalg.norm([0.3, -0.5, 0.8])

    def draw(ax, meshes, view):
        for mesh, rgb in meshes:
            shade = np.clip(np.abs(mesh.face_normals @ light), 0.25, 1)[:, None]
            ax.add_collection3d(Poly3DCollection(
                mesh.triangles, facecolors=np.c_[np.array(rgb) / 255 * shade,
                                                 np.ones(len(shade))],
                edgecolor="none"))
        allv = np.vstack([m.vertices for m, _ in meshes])
        c, r = allv.mean(0), (allv.max(0) - allv.min(0)).max() / 2
        ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r)
        ax.set_zlim(c[2] - r, c[2] + r); ax.view_init(*view); ax.set_axis_off()

    meshes = [(to_trimesh(p.solid), p.rgb) for p in parts]
    ax = fig.add_subplot(1, 3, 1, projection="3d"); ax.set_title("Back (logos)")
    draw(ax, meshes, (-90, 90))              # from below: the back face
    ax = fig.add_subplot(1, 3, 2, projection="3d"); ax.set_title("Clamp thread")
    clip = m3.Manifold.cube([40, 30, 12]).translate([170, -5, 0])
    draw(ax, [(to_trimesh(parts[0].solid ^ clip ^
                          m3.Manifold.cube([40, 40, 6]).translate([170, -10, 0])),
               parts[0].rgb)], (35, -60))
    ax = fig.add_subplot(1, 3, 3, projection="3d"); ax.set_title("Wing screw")
    draw(ax, [(to_trimesh(screw), (200, 200, 200))], (15, -60))
    plt.savefig(path, dpi=110, bbox_inches="tight")


def main():
    parts = build_holder()
    screw = build_screw()
    lo = np.min([p.solid.bounding_box()[:3] for p in parts], axis=0)
    with open(os.path.join(HERE, "ipad_holder.3mf"), "wb") as f:
        f.write(parts_to_3mf(parts, origin=(10 - lo[0], 10 - lo[1]),
                             name="iPad holder"))
    with open(os.path.join(HERE, "wing_screw.3mf"), "wb") as f:
        f.write(parts_to_3mf([Part("Wing screw", 0, (200, 200, 200), screw)],
                             origin=(20, 20), name="M5 wing screw"))
    to_trimesh(screw).export(os.path.join(HERE, "wing_screw.stl"))
    for p in parts:
        print(f"{p.name:20s} volume {p.solid.volume():9.1f} mm3  "
              f"genus {p.solid.genus()}")
    print(f"{'Wing screw':20s} volume {screw.volume():9.1f} mm3  "
          f"height {screw.bounding_box()[5]:.1f} mm")
    preview(parts, screw, os.path.join(HERE, "preview.png"))


if __name__ == "__main__":
    main()
