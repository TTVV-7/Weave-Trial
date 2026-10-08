"""Dumper access: a two-flight stair running straight (no switchback) up to a white lattice tower, and
from the tower top a truss ramp turning 90 degrees to cross over the dumper track, rising gently to a
second tower. Same steelwork as the crossover in footbridge.py: square lattice towers, open grating
treads, white stringers and chords, safety-yellow handrails.

The dumper track runs along Y at X = 0; the stair climbs along +Y beside it and the ramp runs along -X
across it. Units mm, Z up, top of rail and asphalt at Z = 0.

    python railbridge/dumper_access.py OUT_DIR

writes Dumper_Access.step / .glb / .stl and Dumper_Access_Site.step / .glb / .stl (plus a dumper shed,
the track and a hopper car), each with a preview PNG.
"""
import os
import sys

import cadquery as cq
import trimesh

import footbridge as fb
from footbridge import GT, WH, YL, box, flight, lattice, rod, support, xz_plate
import render

TS = fb.TS                  # tower size
TX = 4600                   # stair tower centre: legs 3.1 m clear of the dumper track
H = fb.FL                   # tower top / ramp start, as on the crossover
RAMP_RISE = 600             # the ramp climbs this much over its length (about 1:15)
XB = -4600                  # far tower centre, the other side of the track
RW = 1200                   # clear ramp width
GUARD = 1100
SW = 800                    # clear stair width
LD = 1200                   # mid landing depth

SHED = cq.Color(0.16, 0.42, 0.46)     # teal cladding, as on the dumper building
SHED_DARK = cq.Color(0.1, 0.12, 0.13)


def tower_top(tag, cx, z, open_sides):
    """Grating platform on a tower top, with guard rails on the sides not listed in open_sides ('-x', '+x', '-y', '+y')."""
    p = []
    h = TS / 2
    p.append((f"{tag}_platform", box(cx - h - 75, cx + h + 75, -h - 75, h + 75, z - 40, z), GT))
    sides = {"-x": ((cx - h, -h), (cx - h, h)), "+x": ((cx + h, -h), (cx + h, h)),
             "-y": ((cx - h, -h), (cx + h, -h)), "+y": ((cx - h, h), (cx + h, h))}
    for k, ((ax, ay), (bx, by)) in sides.items():
        if k in open_sides:
            continue
        for hgt in (530, 1070):
            p.append((f"{tag}_rail_{k}_{hgt}", rod(21, (ax, ay, z + hgt), (bx, by, z + hgt)), YL))
    for k, (x, y) in enumerate(((cx - h, -h), (cx + h, -h), (cx + h, h), (cx - h, h))):
        p.append((f"{tag}_post_{k}", rod(25, (x, y, z), (x, y, z + 1070)), WH))
    return p


def ramp():
    """Truss ramp from the stair tower's inner face (X = xa, Z = H) to the far tower's (X = xb, Z = H + RAMP_RISE)."""
    p = []
    xa, xb = TX - TS / 2, XB + TS / 2
    za, zb = H, H + RAMP_RISE
    zf = lambda x: za + (x - xa) / (xb - xa) * (zb - za)        # deck level along the ramp
    nb = 8
    xs = [xa + i * (xb - xa) / nb for i in range(nb + 1)]
    band = lambda z0, z1: [(xa, zf(xa) + z0), (xb, zf(xb) + z0), (xb, zf(xb) + z1), (xa, zf(xa) + z1)]
    p.append(("ramp_deck", xz_plate(band(-40, 0), -RW / 2, RW / 2), GT))
    for s in (1, -1):
        y = s * (RW / 2 + 75)
        p.append((f"ramp_bottom_chord_{s}", xz_plate(band(-300, 0), y - 75, y + 75), WH))
        p.append((f"ramp_top_chord_{s}", xz_plate(band(GUARD - 150, GUARD), y - 75, y + 75), WH))
        for i, x in enumerate(xs):
            p.append((f"ramp_vertical_{s}_{i}", box(x - 60, x + 60, y - 60, y + 60, zf(x), zf(x) + GUARD - 150), WH))
        for i in range(nb):
            a, b = xs[i], xs[i + 1]
            p0, p1 = ((a, y, zf(a) + GUARD - 150), (b, y, zf(b))) if i < nb / 2 else ((a, y, zf(a)), (b, y, zf(b) + GUARD - 150))
            p.append((f"ramp_diagonal_{s}_{i}", rod(35, p0, p1), WH))
        yr = s * (RW / 2 - 40)
        p.append((f"ramp_handrail_{s}", rod(21, (xa, yr, za + 1000), (xb, yr, zb + 1000)), YL))
        p.append((f"ramp_toe_plate_{s}", xz_plate(band(0, 100), s * (RW / 2 - 15), s * (RW / 2 - 5)), YL))
    for i, x in enumerate(xs):
        p.append((f"ramp_floor_beam_{i}", box(x - 60, x + 60, -RW / 2, RW / 2, zf(x) - 300, zf(x) - 40), WH))
    return p


def stair():
    """Two flights in line along +Y, with a landing on posts between them, arriving at the tower's -Y face."""
    p = []
    ye = -TS / 2 - 75
    n = fb.N // 2
    run = (n - 1) * fb.G
    zl = n * fb.R
    y_up = ye - run                       # foot of the upper flight = near edge of the landing
    y_lo = y_up - LD - run                # foot of the lower flight
    lower, _ = flight("stair_lower", TX, SW, y_lo, 0, zl, 1, -1)
    upper, _ = flight("stair_upper", TX, SW, y_up, zl, H, 1, -1)
    p += lower + upper
    x0, x1 = TX - SW / 2 - 90, TX + SW / 2 + 90
    p.append(("stair_landing", box(x0, x1, y_up - LD, y_up, zl - 40, zl), GT))
    p.append(("stair_landing_beam", box(x0, x1, y_up - LD, y_up, zl - 300, zl - 40), WH))
    for k, (x, y) in enumerate(((x0 + 60, y_up - LD + 60), (x1 - 60, y_up - LD + 60), (x0 + 60, y_up - 60), (x1 - 60, y_up - 60))):
        p.append((f"stair_landing_post_{k}", box(x - 60, x + 60, y - 60, y + 60, 0, zl - 300), WH))
    for s, x in ((0, x0), (1, x1)):
        for hgt in (530, 1070):
            p.append((f"stair_landing_rail_{s}_{hgt}", rod(21, (x, y_up - LD, zl + hgt), (x, y_up, zl + hgt)), YL))
    p += support("stair_support_lo", TX, SW, y_lo + run / 2, zl / 2 - 350)
    p += support("stair_support_up", TX, SW, y_up + run / 2, zl + (H - zl) / 2 - 350)
    return p


def structure():
    p = lattice("stair_tower", TX, 0, TS / 2, TS / 2, H - 40, 5)
    p += tower_top("stair_tower_top", TX, H, open_sides=("-x", "-y"))
    p += stair()
    p += ramp()
    zb = H + RAMP_RISE
    p += lattice("far_tower", XB, 0, TS / 2, TS / 2, zb - 40, 5)
    p += tower_top("far_tower_top", XB, zb, open_sides=("+x", "-x"))   # -x: onward access onto the dumper building
    return p


def site():
    p = []
    L = 50000
    for s in (1, -1):
        xr = s * (fb.GAUGE / 2 + 35)
        p.append((f"rail_{s}", box(xr - 35, xr + 35, -L / 2, L / 2, -150, 10), fb.RAIL))
    p.append(("asphalt", box(-12000, 12000, -L / 2, L / 2, -160, 0), fb.ASPHALT))
    # dumper shed straddling the track just beyond the ramp, open portal facing -Y
    y0, y1, x0, x1, ht = 2500, 26000, -9000, 9000, H + RAMP_RISE + 1500
    for s, (a, b) in enumerate(((x0, -2400), (2400, x1))):
        p.append((f"shed_wall_{s}", box(a, b, y0, y1, 0, ht), SHED))
    p.append(("shed_lintel", box(-2400, 2400, y0, y0 + 600, 5600, ht), SHED))
    p.append(("shed_roof", box(x0 - 300, x1 + 300, y0 - 300, y1 + 300, ht, ht + 300), SHED_DARK))
    for i in range(int((x1 - x0) / 600)):
        x = x0 + 300 + i * 600
        if abs(x) > 2500:
            p.append((f"shed_rib_{i}", box(x - 40, x + 40, y0 - 60, y0, 0, ht), SHED_DARK))
    p += fb.hopper("hopper", 0, -16000, fb.CAR[0])
    return p


def export(parts, out, name):
    asm = cq.Assembly(name=name)
    for n, w, c in parts:
        asm.add(w, name=n, color=c)
    step = os.path.join(out, name + ".step")
    asm.export(step)
    shape = cq.importers.importStep(step)
    solids = shape.solids().vals()
    glb = os.path.join(out, name + ".glb")
    cq.Assembly.load(step).export(glb)
    scene = trimesh.load(glb)
    scene.apply_scale(0.001)
    scene.export(glb)
    cq.exporters.export(shape, os.path.join(out, name + ".stl"), tolerance=2, angularTolerance=0.3)
    bb = asm.toCompound().BoundingBox()
    ft = lambda v: round(v / 304.8, 1)
    print(name, "ft: X", ft(bb.xlen), "Y", ft(bb.ylen), "Z", ft(bb.zlen), "| zmin", round(bb.zmin),
          "| solids", len(solids), "all valid", all(s.isValid() for s in solids))


def main(out):
    s = structure()
    export(s, out, "Dumper_Access")
    export(s + site(), out, "Dumper_Access_Site")
    render.render(s, 0, os.path.join(out, "Dumper_Access_preview.png"), [(18, -60), (25, 45)])
    render.render(s + site(), 0, os.path.join(out, "Dumper_Access_Site_preview.png"), [(30, -60), (40, 210)], size=(16, 9))
    ft = lambda v: round(v / 304.8, 1)
    print("ramp length ft", ft(TX - XB - TS), "rise ft", ft(RAMP_RISE), "| tower top ft", ft(H),
          "| stair two flights of", fb.N // 2, "risers, landing at ft", ft(fb.N // 2 * fb.R))


if __name__ == "__main__":
    main(sys.argv[1])
