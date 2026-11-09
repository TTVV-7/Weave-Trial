"""Basketball fidgets, as painted 3MFs and plain STLs.

1. basketball-gyro   A print-in-place gyro: a basketball spinning inside four
                     nested rings, each ring pivoting on cone pins at 90 degrees
                     to the last. Comes off the plate moving. No hardware.
2. basketball-spinner A three-lobe fidget spinner with a basketball on each lobe,
                     built round one 608 skateboard bearing, plus two finger caps.

Every triangle carries its filament (`paint_color`, the per-triangle painting that
Bambu Studio, OrcaSlicer and Snapmaker Orca read), so the seams print black on an
orange ball. The seams are also real grooves, so the single-colour STLs still read
as basketballs.

Run: python3 make_fidgets.py   (needs numpy, trimesh, manifold3d)
All dimensions are in millimetres; tweak the constants below and re-run.
"""
import pathlib
import zipfile
import numpy as np
import trimesh
import manifold3d as mf

HERE = pathlib.Path(__file__).parent
OUT = HERE / "stl"
OUT.mkdir(exist_ok=True)

# The filaments, T1-T3, shared by both fidgets so one load prints the set.
FILAMENTS = np.array([
    [0xE8, 0x6A, 0x1C],   # T1 basketball orange
    [0x1A, 0x1A, 0x1A],   # T2 black: seams, rings, spinner body
    [0xF2, 0xF2, 0xF2],   # T3 white: rings, caps
])
ORANGE, BLACK, WHITE = range(3)

SEAM_W = 1.0          # seam groove width
SEAM_D = 0.6          # seam groove depth
SMALL_CIRCLE = 0.72   # the two curved seams sit at x = +-SMALL_CIRCLE * radius

# --- gyro ---------------------------------------------------------------------
BALL_R = 12.0         # 24 mm basketball in the middle
HALF_H = 8.5          # everything is cut to |z| <= HALF_H: 17 mm thick, flat top and bottom;
                      # any thicker and the underside of the ball overhangs past 45 degrees
GAP = 0.6             # radial gap between neighbouring rings (print-in-place clearance)
RING_T = 3.4          # ring wall thickness
RINGS = 4
PIN_DEPTH = 2.0       # how far each cone pin reaches into the part inside it
PIN_CLEAR = 0.35      # gap between a pin and its socket, measured square to the cone
RING_COLOURS = [BLACK, WHITE, BLACK, ORANGE]   # inner to outer

# --- spinner ------------------------------------------------------------------
BEARING_D = 22.0      # 608 bearing: 22 x 8 x 7
BEARING_W = 7.0
BEARING_FIT = 0.15    # added to the bore for a press fit
BORE_D = 8.0
INNER_RACE_D = 12.0   # caps may only touch the inner race
LOBE_R = 13.0         # each basketball lobe is 26 mm across
LOBE_AT = 31.0        # lobe centre distance from the bearing centre
HUB_R = 16.5
ARM_W = 15.0          # arm width where it leaves the hub
CAP_D = 20.0
CAP_T = 2.2
CAP_PEG = 3.2         # each cap's peg fills just under half the bore
CAP_PEG_FIT = 0.05    # taken off the peg diameter

SEG = 192             # circle smoothness


def to_mesh(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3],
                           np.asarray(mesh.tri_verts), process=False)


def sphere(r, seg=SEG):
    return mf.Manifold.sphere(r, seg)


def slab(h=HALF_H, size=200.0):
    return mf.Manifold.cube([size, size, 2 * h], center=True)


def shell(r_in, r_out):
    return (sphere(r_out) - sphere(r_in)) ^ slab()


def cone(apex, axis, length, half_angle=45.0):
    """Solid cone, tip at `apex`, opening along unit `axis`."""
    r = length * np.tan(np.radians(half_angle))
    c = mf.Manifold.cylinder(length, 0.0, r, SEG // 3)   # tip at origin, opens up +z
    axis = np.asarray(axis, float)
    if axis[2] < -0.99:
        c = c.rotate([180, 0, 0])
    elif abs(axis[2]) < 0.99:
        yaw = np.degrees(np.arctan2(axis[1], axis[0]))
        c = c.rotate([0, 90, 0]).rotate([0, 0, yaw])
    return c.translate(apex)


# --- basketball seams --------------------------------------------------------

def ball_seams(r):
    """Groove bands of a basketball of radius r, poles on the x axis: two great
    circles through the poles (planes y=0 and z=0) and a small circle round each
    pole (planes x=+-c). Only the part outside r - SEAM_D matters."""
    big = 4 * r
    bands = [mf.Manifold.cube([big, SEAM_W, big], center=True),
             mf.Manifold.cube([big, big, SEAM_W], center=True)]
    c = SMALL_CIRCLE * r
    # the small circles meet the surface at a slant; thin the slab so the groove
    # is SEAM_W wide along the surface
    t = SEAM_W * np.sqrt(1 - (c / r) ** 2)
    for s in (-1, 1):
        bands.append(mf.Manifold.cube([t, big, big], center=True).translate([s * c, 0, 0]))
    seams = mf.Manifold.batch_boolean(bands, mf.OpType.Add)
    # the great circle over the top carries on across the flat top and bottom
    caps = slab(size=big) - slab(HALF_H - SEAM_D, size=big)
    return (seams - sphere(r - SEAM_D)) + (seams ^ caps)


def ring_radii():
    radii, r = [], BALL_R + GAP
    for _ in range(RINGS):
        radii.append((r, r + RING_T))
        r += RING_T + GAP
    return radii


def make_gyro():
    """The gyro as a list of solids: the ball, then the rings from the inside out."""
    radii = ring_radii()
    seams = ball_seams(BALL_R)
    parts = [sphere(BALL_R) ^ slab() - seams]
    parts += [shell(a, b) for a, b in radii]
    # part k (0 = ball) pivots in part k+1 on two pins; axes alternate x, y, x, y
    inner_outer = [BALL_R] + [b for _, b in radii]
    for k in range(RINGS):
        axis = np.array([1.0, 0, 0]) if k % 2 == 0 else np.array([0, 1.0, 0])
        r_in_out = inner_outer[k]                 # outer surface of the inner part
        host_in, host_out = radii[k]              # the ring carrying the pins
        for s in (-1, 1):
            d = s * axis
            apex = d * (r_in_out - PIN_DEPTH)
            length = host_out - (r_in_out - PIN_DEPTH) - 0.4
            pin = cone(apex, d, length) ^ slab()
            parts[k + 1] = parts[k + 1] + (pin ^ sphere(host_out - 0.4))
            sock = cone(apex - d * PIN_CLEAR * np.sqrt(2), d, length + 2)
            parts[k] = parts[k] - sock
    return parts


def check_gyro(parts):
    """Turn every pivot through a full circle and make sure nothing touches.
    Returns the tightest gap seen; raises if any part is not one piece or collides."""
    if any(len(p.decompose()) != 1 for p in parts):
        raise SystemExit("gyro: a ring has come apart from its pins")
    tightest = 9.0
    for k in range(RINGS):
        inner = mf.Manifold.batch_boolean(parts[:k + 1], mf.OpType.Add)
        for a in range(0, 360, 15):
            turned = inner.rotate([a, 0, 0] if k % 2 == 0 else [0, a, 0])
            if (turned ^ parts[k + 1]).volume() > 1e-6:
                raise SystemExit(f"gyro: pivot {k} jams at {a} degrees")
            tightest = min(tightest, turned.min_gap(parts[k + 1], 1.0))
    return tightest


def paint_gyro(parts):
    meshes, labels = [], []
    for k, p in enumerate(parts):
        m = to_mesh(p)
        lab = np.full(len(m.faces), ORANGE if k == 0 else RING_COLOURS[k - 1])
        if k == 0:
            c = m.triangles_center
            r = np.linalg.norm(c, axis=1)
            z = np.abs(c[:, 2])
            outside = (r > BALL_R - 0.05) | (z > HALF_H - 1e-3)       # the ball's own skin
            groove = (r > BALL_R - SEAM_D - 0.3) | (z > HALF_H - SEAM_D - 0.3)   # not the sockets
            lab[in_bands(c, BALL_R) & ~outside & groove] = BLACK
        meshes.append(m)
        labels.append(lab)
    return meshes, labels


def in_bands(c, r):
    """Is each point inside one of the seam bands (grown a hair to take the walls)?"""
    e = 0.05
    k = SMALL_CIRCLE * r
    t = SEAM_W * np.sqrt(1 - SMALL_CIRCLE ** 2)
    return ((np.abs(c[:, 1]) < SEAM_W / 2 + e) | (np.abs(c[:, 2]) < SEAM_W / 2 + e)
            | (np.abs(np.abs(c[:, 0]) - k) < t / 2 + e))


# --- spinner -----------------------------------------------------------------

def circle(r, at=(0, 0), seg=SEG):
    return mf.CrossSection.circle(r, seg).translate(at)


def flat_seams(r):
    """2D seam lines of a basketball seen face-on: a cross and two side arcs."""
    w = SEAM_W
    lines = [mf.CrossSection.square([2 * r, w], center=True),
             mf.CrossSection.square([w, 2 * r], center=True)]
    arc_r = 1.05 * r
    for s in (-1, 1):
        ring = circle(arc_r + w / 2, (s * 1.45 * r, 0)) - circle(arc_r - w / 2, (s * 1.45 * r, 0))
        lines.append(ring)
    outline = circle(r) - circle(r - w)
    return (mf.CrossSection.batch_boolean(lines, mf.OpType.Add) ^ circle(r)) + outline


def lobe_centres():
    a = np.radians([90, 210, 330])
    return np.c_[np.cos(a), np.sin(a)] * LOBE_AT


def spinner_outline():
    hub = circle(HUB_R)
    shapes = [hub]
    for x, y in lobe_centres():
        shapes.append(circle(LOBE_R, (x, y)))
        shapes.append(mf.CrossSection.batch_hull([circle(ARM_W / 2), circle(LOBE_R * 0.75, (x, y))]))
    body = mf.CrossSection.batch_boolean(shapes, mf.OpType.Add)
    # soften the inside corners between the arms
    return body.offset(-4, mf.JoinType.Round).offset(4, mf.JoinType.Round).offset(
        3, mf.JoinType.Round).offset(-3, mf.JoinType.Round)


def make_spinner():
    body = spinner_outline().extrude(BEARING_W)
    body = body - mf.Manifold.cylinder(BEARING_W * 3, (BEARING_D + BEARING_FIT) / 2, (BEARING_D + BEARING_FIT) / 2, SEG).translate(
        [0, 0, -BEARING_W])
    grooves = []
    for x, y in lobe_centres():
        # rotate each ball so its cross points at the hub
        ang = np.degrees(np.arctan2(y, x))
        s2d = flat_seams(LOBE_R - 1.4).rotate(ang).translate([x, y])
        g = s2d.extrude(SEAM_D + 1)
        grooves.append(g.translate([0, 0, BEARING_W - SEAM_D]))
        grooves.append(g.translate([0, 0, -1]))
    return body - mf.Manifold.batch_boolean(grooves, mf.OpType.Add)


def paint_spinner(m):
    """Lobe faces orange inside their outline seam; seams, sides and hub black."""
    c = m.triangles_center
    z = m.triangles[:, :, 2]
    on_face = (np.ptp(z, axis=1) < 1e-4) & ((np.abs(z[:, 0] - BEARING_W) < 1e-4) | (np.abs(z[:, 0]) < 1e-4))
    lab = np.full(len(m.faces), BLACK)
    for x, y in lobe_centres():
        inside = np.hypot(c[:, 0] - x, c[:, 1] - y) < LOBE_R - 1.4 - SEAM_W
        lab[on_face & inside] = ORANGE
    return lab


def make_cap_printable():
    """Cap printed face-down: a flat 20 mm disc with basketball seams grooved into
    the face (on the bed, so they print as clean first-layer lines), a stand-off
    ring that only touches the bearing's inner race, and a peg for the bore."""
    face = mf.Manifold.cylinder(CAP_T, CAP_D / 2, CAP_D / 2, SEG)
    seams = flat_seams(CAP_D / 2 - 0.8).extrude(SEAM_D + 1).translate([0, 0, -1])
    face = face - seams
    stand = mf.Manifold.cylinder(0.6, INNER_RACE_D / 2 - 0.5, INNER_RACE_D / 2 - 0.5, SEG).translate([0, 0, CAP_T])
    peg_r = (BORE_D - CAP_PEG_FIT) / 2
    peg = mf.Manifold.cylinder(CAP_PEG, peg_r, peg_r - 0.15, SEG).translate([0, 0, CAP_T + 0.6])
    return face + stand + peg


def paint_cap(m):
    c = m.triangles_center
    z = m.triangles[:, :, 2]
    on_face = (np.ptp(z, axis=1) < 1e-4) & (np.abs(z[:, 0]) < 1e-4)
    lab = np.full(len(m.faces), BLACK)
    lab[on_face & (np.hypot(c[:, 0], c[:, 1]) < CAP_D / 2 - 0.8 - SEAM_W)] = ORANGE
    return lab


# --- output ------------------------------------------------------------------

# Bambu Studio / OrcaSlicer / Snapmaker Orca per-triangle filament codes.
PAINT_CODE = ["4", "8", "0C", "1C"]


def write_3mf(path, objects):
    """objects: list of (name, mesh, labels, offset_xy). One object each, painted."""
    hexes = [f"#{r:02X}{g:02X}{b:02X}FF" for r, g, b in FILAMENTS]
    res, build, cfg = [], [], []
    for i, (name, mesh, lab, (ox, oy)) in enumerate(objects, start=1):
        verts = "".join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in mesh.vertices)
        tris = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}" paint_color="{PAINT_CODE[k]}"/>'
                       for (a, b, c), k in zip(mesh.faces, lab))
        res.append(f'<object id="{i}" type="model"><mesh><vertices>{verts}</vertices>'
                   f'<triangles>{tris}</triangles></mesh></object>')
        build.append(f'<item objectid="{i}" transform="1 0 0 0 1 0 0 0 1 {ox:.3f} {oy:.3f} 0"/>')
        cfg.append(f'<object id="{i}"><metadata key="name" value="{name}"/>'
                   '<metadata key="extruder" value="1"/></object>')
    model = ('<?xml version="1.0" encoding="UTF-8"?>'
             '<model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
             'xmlns:m="http://schemas.microsoft.com/3dmanufacturing/material/2015/02">'
             '<resources><m:colorgroup id="100">'
             + "".join(f'<m:color color="{h}"/>' for h in hexes) + '</m:colorgroup>'
             + "".join(res) + '</resources><build>' + "".join(build) + '</build></model>')
    settings = '<?xml version="1.0" encoding="UTF-8"?><config>' + "".join(cfg) + '</config>'
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.'
                   'openxmlformats.org/package/2006/content-types"><Default Extension="rels" '
                   'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="model" ContentType="application/vnd.ms-package.'
                   '3dmanufacturing-3dmodel+xml"/></Types>')
        z.writestr("_rels/.rels",
                   '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.'
                   'openxmlformats.org/package/2006/relationships"><Relationship '
                   'Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/'
                   '3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        z.writestr("3D/3dmodel.model", model)
        z.writestr("Metadata/model_settings.config", settings)


def merged(meshes, labels):
    return trimesh.util.concatenate(meshes), np.concatenate(labels)


def on_bed(mesh):
    mesh = mesh.copy()
    mesh.apply_translation([0, 0, -mesh.bounds[0][2]])
    return mesh


def main():
    parts = make_gyro()
    print(f"gyro: every pivot turns a full circle, tightest gap {check_gyro(parts):.2f} mm")
    meshes, labels = paint_gyro(parts)
    gyro, gyro_lab = merged(meshes, labels)
    gyro = on_bed(gyro)
    gyro.export(OUT / "basketball-gyro.stl")
    write_3mf(OUT / "basketball-gyro.3mf", [("basketball-gyro", gyro, gyro_lab, (0, 0))])

    spinner = to_mesh(make_spinner())
    spinner_lab = paint_spinner(spinner)
    cap = to_mesh(make_cap_printable())
    cap_lab = paint_cap(cap)
    spinner.export(OUT / "basketball-spinner.stl")
    cap.export(OUT / "basketball-spinner-cap.stl")
    write_3mf(OUT / "basketball-spinner.3mf", [
        ("basketball-spinner", spinner, spinner_lab, (0, 0)),
        ("cap-1", cap, cap_lab, (52, -30)),
        ("cap-2", cap, cap_lab, (52, -55)),
    ])

    for name, m in [("basketball-gyro", gyro), ("basketball-spinner", spinner),
                    ("basketball-spinner-cap", cap)]:
        e = m.extents
        print(f"{name:24s} {e[0]:5.1f} x {e[1]:5.1f} x {e[2]:4.1f} mm  {m.volume / 1000:5.1f} cm3  "
              f"{len(m.faces):7d} tris")
    return parts


if __name__ == "__main__":
    main()
