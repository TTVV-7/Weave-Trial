"""Rail-yard crossover as built at bulk terminals: an arched truss walkway over four tracks, carried on two
white steel lattice towers at the ends and a steel lattice pier between the middle two tracks.

The towers and pier are square-section lattices: legs, horizontal girts and X-bracing in every bay.
The walkway's bottom chord springs as a parabolic arch across each pair of tracks, tower to pier, so
from track level it reads as two arches, while the deck stays flat to walk on; the side trusses double
as the guards. One tower has a single long, steep straight stair; the other has two flights, switching
back at a landing. Stairs have white channel stringers, open grating treads, a yellow handrail on the
track side and a white guard on the other.

Tracks run along Y; X = 0 is the pier. Units mm, Z up, top of rail and asphalt at Z = 0.

    python railbridge/footbridge.py OUT_DIR

writes Rail_Footbridge.step (towers, pier, bridge, stairs) and Rail_Footbridge_Site.step (plus asphalt,
embedded rails, gravel around the tower bases and covered hopper cars).
"""
import math
import sys

import cadquery as cq

# ---------------------------------------------------------------- yard
GAUGE = 1435
TRACKS = (-7500, -3000, 3000, 7500)   # 4.5 m within each pair, 6 m across the pier
YARD_L = 50000
CAR_HW = 1600               # half-width of a freight car
CLR = 7000                  # clearance over the car envelope (23 ft)

# ---------------------------------------------------------------- towers and pier
TS = 1500                   # tower size, leg centre to leg centre
TX = TRACKS[-1] + 2600 + TS / 2   # tower centre: legs 2.6 m clear of the outer track centre
XI = TX - TS / 2            # tower inner leg line, where an arch springs
PW = 600                    # pier width across the tracks, leg centre to leg centre
XP = PW / 2                 # pier leg line, where the other end of each arch springs

# ---------------------------------------------------------------- arched walkway
RISE = 1500                 # rise of each arch from springing to crown
ZS = 6500                   # soffit at the springings
FL = ZS + RISE + 250        # flat deck, just above the crowns
BW = 1200                   # clear walkway width
GUARD = 1100                # top chord above the deck

# ---------------------------------------------------------------- stairs
N = 44                      # risers from the ground to the deck
R = FL / N
G = 165                     # going: a steep (~50 degree) industrial stair, as on site
SW = 800                    # clear width, straight stair
SW2 = 700                   # clear width of each switchback flight
LD = 1200                   # switchback landing depth

WH = cq.Color(0.9, 0.9, 0.87)
YL = cq.Color(1.0, 0.8, 0.0)
GT = cq.Color(0.55, 0.56, 0.57)
DK = cq.Color(0.3, 0.3, 0.3)
ASPHALT = cq.Color(0.24, 0.24, 0.25)
GRAVEL = cq.Color(0.5, 0.46, 0.42)
RAIL = cq.Color(0.55, 0.52, 0.5)
CAR = (cq.Color(0.55, 0.25, 0.18), cq.Color(0.78, 0.76, 0.7))
BOGIE = cq.Color(0.15, 0.15, 0.15)


def box(x0, x1, y0, y1, z0, z1):
    x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
    return cq.Workplane().box(x1 - x0, y1 - y0, z1 - z0).translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))


def rod(r, p0, p1):
    d = cq.Vector(*p1) - cq.Vector(*p0)
    return cq.Workplane().add(cq.Solid.makeCylinder(r, d.Length, cq.Vector(*p0), d.normalized()))


def yz_plate(pts, x0, x1):
    """A prism whose profile is the (y, z) polygon pts, spanning x0..x1."""
    x0, x1 = sorted((x0, x1))
    return cq.Workplane("YZ").polyline(pts).close().extrude(x1 - x0).translate((x0, 0, 0))


def xz_plate(pts, y0, y1):
    """A prism whose profile is the (x, z) polygon pts, spanning y0..y1."""
    y0, y1 = sorted((y0, y1))
    return yz_plate(pts, 0, y1 - y0).rotate((0, 0, 0), (0, 0, 1), -90).translate((0, y1, 0))


def soffit(x):
    """Underside of the arches: a parabola across each span, ZS at the pier and tower, ZS + RISE at the crown."""
    m, h = (XI + XP) / 2, (XI - XP) / 2
    return ZS + RISE * (1 - ((abs(x) - m) / h) ** 2)


def lattice(tag, cx, cy, hx, hy, z_top, bays):
    """A four-legged lattice column with leg lines at cx +- hx, cy +- hy, from the ground to z_top."""
    p = []
    legs = [(cx - hx, cy - hy), (cx + hx, cy - hy), (cx + hx, cy + hy), (cx - hx, cy + hy)]
    for k, (x, y) in enumerate(legs):
        p.append((f"{tag}_leg_{k}", box(x - 75, x + 75, y - 75, y + 75, 25, z_top), WH))
        p.append((f"{tag}_base_plate_{k}", box(x - 175, x + 175, y - 175, y + 175, 0, 25), DK))
    levels = [25 + i * (z_top - 25) / bays for i in range(bays + 1)]
    for li, z in enumerate(levels[1:], 1):
        for k in range(4):
            (x1, y1), (x2, y2) = legs[k], legs[(k + 1) % 4]
            p.append((f"{tag}_girt_{li}_{k}", rod(45, (x1, y1, z - 45), (x2, y2, z - 45)), WH))
    for bi in range(bays):
        za, zb = levels[bi] + (150 if bi == 0 else 0), levels[bi + 1] - 90
        for k in range(4):
            (x1, y1), (x2, y2) = legs[k], legs[(k + 1) % 4]
            p.append((f"{tag}_brace_{bi}_{k}_a", rod(28, (x1, y1, za), (x2, y2, zb)), WH))
            p.append((f"{tag}_brace_{bi}_{k}_b", rod(28, (x2, y2, za), (x1, y1, zb)), WH))
    return p


def bridge():
    p = []
    nb = 6                                   # truss panels per span
    xs = sorted({round(s * (XP + i * (XI - XP) / nb), 3) for s in (1, -1) for i in range(nb + 1)})
    lo = lambda x: soffit(x) + 300           # top of the arched chord
    hi = FL + GUARD - 150                    # underside of the top chord
    for s in (1, -1):
        y = s * (BW / 2 + 75)
        for side in (1, -1):
            ss = [side * (XP + i * (XI - XP) / 30) for i in range(31)]
            arch = [(x, soffit(x)) for x in ss] + [(x, lo(x)) for x in reversed(ss)]
            p.append((f"arch_chord_{s}_{side}", xz_plate(arch, y - 75, y + 75), WH))
        p.append((f"top_chord_{s}", box(-XI, XI, y - 75, y + 75, hi, FL + GUARD), WH))
        for i, x in enumerate(xs):
            p.append((f"vertical_{s}_{i}", box(x - 60, x + 60, y - 60, y + 60, lo(x), hi), WH))
        for i in range(len(xs) - 1):
            a, b = xs[i], xs[i + 1]
            if abs(a) < XP and abs(b) < XP:
                continue                     # the panel over the pier is solid with it
            # Pratt diagonals falling toward each span's crown
            m = math.copysign((XI + XP) / 2, a + b)
            p0, p1 = ((a, y, hi), (b, y, lo(b))) if abs(a - m) > abs(b - m) else ((a, y, lo(a)), (b, y, hi))
            p.append((f"diagonal_{s}_{i}", rod(35, p0, p1), WH))
        yr = s * (BW / 2 - 40)
        p.append((f"handrail_{s}", rod(21, (-XI, yr, FL + 1000), (XI, yr, FL + 1000)), YL))
        p.append((f"toe_plate_{s}", box(-XI, XI, s * (BW / 2 - 5), s * (BW / 2 - 15), FL, FL + 100), YL))
    for i, x in enumerate(xs):
        p.append((f"floor_beam_{i}", box(x - 60, x + 60, -BW / 2, BW / 2, min(lo(x), FL - 300), FL - 40), WH))
    p.append(("deck_grating", box(-XI, XI, -BW / 2, BW / 2, FL - 40, FL), GT))
    # pier between the middle tracks, with a cap beam under both arch springings
    p += lattice("pier", 0, 0, XP, BW / 2 + 75, ZS - 200, 4)
    p.append(("pier_cap", box(-XP - 150, XP + 150, -BW / 2 - 225, BW / 2 + 225, ZS - 200, ZS), WH))
    return p


def flight(tag, xc, w, y_bot, z_bot, z_top, d, rail_side):
    """A straight flight centred on xc, climbing in direction d (+1/-1 along Y) from (y_bot, z_bot) to
    z_top. Its last riser lands on whatever is at y_bot + d * run. rail_side (+1/-1 in X) gets the yellow
    handrail, the other side a white guard. Returns (parts, y at the top)."""
    p = []
    n = round((z_top - z_bot) / R)
    r = (z_top - z_bot) / n            # risers stay equal whatever the height
    run = (n - 1) * G
    y_top = y_bot + d * run
    slope = (z_top - z_bot) / (run + G)
    SD = 300
    for s in (1, -1):
        x = xc + s * (w / 2 + 6)
        y0 = y_bot - d * G
        prof = [(y0, z_bot), (y_top, z_top), (y_top, z_top + SD * 0.6), (y0 - d * SD / slope, z_bot)]
        p.append((f"{tag}_stringer_{s}", yz_plate(prof, x - 6, x + 6), WH))
        for k, dz in enumerate((0, SD * 0.6 - 10)):
            fl = [(y0 - d * dz / slope, z_bot), (y_top, z_top + dz), (y_top, z_top + dz + 10), (y0 - d * (dz + 10) / slope, z_bot)]
            p.append((f"{tag}_stringer_flange_{s}_{k}", yz_plate(fl, x + s * 6, x + s * 80), WH))
    for i in range(1, n):
        z = z_bot + i * r
        a = y_bot + d * (i - 1) * G
        t = box(xc - w / 2, xc + w / 2, a - d * 15, a + d * (G + 15), z - 35, z)
        for k in range(5):
            c = a + d * (10 + k * 34)
            t = t.cut(box(xc - w / 2 + 30, xc + w / 2 - 30, c, c + d * 16, z - 36, z + 1))
        p.append((f"{tag}_tread_{i:02d}", t, GT))
        e = a + d * G
        p.append((f"{tag}_nosing_{i:02d}", box(xc - w / 2, xc + w / 2, e - d * 10, e + d * 15, z - 40, z), YL))
    for s in (1, -1):
        col = YL if s == rail_side else WH
        x = xc + s * (w / 2 + 45)
        ya, za = y_bot + d * G * 0.5, z_bot + r * 1.5
        p.append((f"{tag}_top_rail_{s}", rod(21, (x, ya, za + 900), (x, y_top, z_top + 900)), col))
        p.append((f"{tag}_mid_rail_{s}", rod(21, (x, ya, za + 450), (x, y_top, z_top + 450)), col))
        for k, i in enumerate(range(1, n, 7)):
            y = y_bot + d * ((i - 1) * G + G * 0.5)
            z = z_bot + i * r
            p.append((f"{tag}_post_{s}_{k}", rod(21, (x, y, max(z - 200, z_bot)), (x, y, z + 940)), col))
    return p, y_top


def support(tag, xc, w, y, z):
    """A portal frame under a flight: two legs and a cross beam topping out at z."""
    p = []
    for s in (1, -1):
        x = xc + s * (w / 2 + 6)
        p.append((f"{tag}_leg_{s}", box(x - 50, x + 50, y - 50, y + 50, 0, z), WH))
    p.append((f"{tag}_beam", box(xc - w / 2 - 60, xc + w / 2 + 60, y - 50, y + 50, z - 150, z), WH))
    p.append((f"{tag}_brace", rod(25, (xc - w / 2, y, 200), (xc + w / 2, y, z - 150)), WH))
    return p


def tower(switchback):
    """East tower, centred on (TX, 0). Its stair stands on the -Y side and arrives at the tower's -Y face:
    one straight flight, or (switchback) two flights with a landing out at the far end."""
    p = lattice("tower", TX, 0, TS / 2, TS / 2, FL - 40, 5)
    h = TS / 2
    p.append(("top_platform", box(TX - h - 75, TX + h + 75, -h - 75, h + 75, FL - 40, FL), GT))
    # guarded on the outer face and the +Y side (the arch arrives from -X, the stair from -Y)
    for r, ((ax, ay), (bx, by)) in enumerate((((TX + h, -h), (TX + h, h)), ((TX - h, h), (TX + h, h)))):
        for hgt in (530, 1070):
            p.append((f"top_rail_{r}_{hgt}", rod(21, (ax, ay, FL + hgt), (bx, by, FL + hgt)), YL))
    for k, (x, y) in enumerate(((TX - h, -h), (TX + h, -h), (TX + h, h), (TX - h, h))):
        p.append((f"top_post_{k}", rod(25, (x, y, FL), (x, y, FL + 1070)), WH))
    ye = -h - 75                                   # the tower's -Y face, where the stair arrives
    if not switchback:
        n = N
        run = (n - 1) * G
        f, _ = flight("stair", TX, SW, ye - run, 0, FL, 1, -1)
        p += f
        for j, frac in enumerate((1 / 3, 2 / 3)):
            p += support(f"stair_support_{j}", TX, SW, ye - run * frac, FL * (1 - frac) - 350)
        return p
    # two flights: the lower one climbs away from the tower in the outer lane, the upper one climbs
    # back toward the tower in the inner (track-side) lane
    zl = (N // 2) * R
    run = (N // 2 - 1) * G
    # the lower flight stands outside the tower's outer legs and starts OFF_Y out from its face, so it
    # is clear of the tower; the upper one stays within the tower's width to arrive on the top platform
    OFF_Y = 600
    x_out = TX + h + 450 + SW2 / 2 + 90
    x_in = TX + h - SW2 / 2 - 90
    y_land1 = ye - run                              # near edge of the landing, where the upper flight starts
    y_land0 = y_land1 - OFF_Y - LD                  # far edge, beyond where the lower flight arrives
    lower, _ = flight("stair_lower", x_out, SW2, ye - OFF_Y, 0, zl, -1, 1)
    upper, _ = flight("stair_upper", x_in, SW2, y_land1, zl, FL, 1, -1)
    p += lower + upper
    x0, x1 = x_in - SW2 / 2 - 90, x_out + SW2 / 2 + 90
    p.append(("stair_landing", box(x0, x1, y_land0, y_land1, zl - 40, zl), GT))
    p.append(("stair_landing_beam", box(x0, x1, y_land0, y_land0 + 150, zl - 300, zl - 40), WH))
    for k, (x, y) in enumerate(((x0 + 60, y_land0 + 60), (x1 - 60, y_land0 + 60), (x0 + 60, y_land1 - 60), (x1 - 60, y_land1 - 60))):
        p.append((f"stair_landing_post_{k}", box(x - 60, x + 60, y - 60, y + 60, 0, zl - 40), WH))
    for hgt in (530, 1070):
        p.append((f"stair_landing_rail_end_{hgt}", rod(21, (x0, y_land0, zl + hgt), (x1, y_land0, zl + hgt)), YL))
        for s, x in ((0, x0), (1, x1)):
            p.append((f"stair_landing_rail_{s}_{hgt}", rod(21, (x, y_land0, zl + hgt), (x, y_land1, zl + hgt)), YL))
    p += support("stair_support", x_in, SW2, y_land1 + run / 2, zl + (FL - zl) / 2 - 350)
    return p


def hopper(tag, x, y, col):
    """A simple covered hopper car on the track at x, centred on y."""
    p = []
    L, W, H = 17500, 3200, 4600
    z0 = 1100
    body = yz_plate([(y - L / 2, z0 + 600), (y - L / 2 + 1500, z0), (y + L / 2 - 1500, z0), (y + L / 2, z0 + 600),
                     (y + L / 2, H), (y - L / 2, H)], x - W / 2, x + W / 2)
    p.append((f"{tag}_body", body, col))
    p.append((f"{tag}_roof_walk", box(x - 300, x + 300, y - L / 2 + 500, y + L / 2 - 500, H, H + 60), DK))
    for s in (1, -1):
        yt = y + s * (L / 2 - 2000)
        p.append((f"{tag}_bogie_{s}", box(x - 1100, x + 1100, yt - 1300, yt + 1300, 300, 900), BOGIE))
        for a in (-850, 850):
            p.append((f"{tag}_wheelset_{s}_{a}", rod(450, (x - GAUGE / 2 - 60, yt + a, 450), (x + GAUGE / 2 + 60, yt + a, 450)), BOGIE))
    return p


def east_site():
    p = []
    for k, x in enumerate(t for t in TRACKS if t > 0):
        for s in (1, -1):
            xr = x + s * (GAUGE / 2 + 35)
            p.append((f"rail_{k}_{s}", box(xr - 35, xr + 35, -YARD_L / 2, YARD_L / 2, -150, 10), RAIL))
    p.append(("pier_pad", box(0, XP + 600, -BW / 2 - 700, BW / 2 + 700, -150, 0), GRAVEL))
    p.append(("asphalt", box(XP + 600, XI - 600, -YARD_L / 2, YARD_L / 2, -150, 0), ASPHALT))
    p.append(("asphalt_mid_a", box(0, XP + 600, -YARD_L / 2, -BW / 2 - 700, -150, 0), ASPHALT))
    p.append(("asphalt_mid_b", box(0, XP + 600, BW / 2 + 700, YARD_L / 2, -150, 0), ASPHALT))
    p.append(("gravel_strip", box(XI - 600, TX + TS / 2 + 600, -YARD_L / 2, YARD_L / 2, -150, -20), GRAVEL))
    p.append(("asphalt_outer", box(TX + TS / 2 + 600, TX + 6000, -YARD_L / 2, YARD_L / 2, -150, 0), ASPHALT))
    return p


def half_turn(p, tag):
    """The west half is the east half turned 180 degrees about Z."""
    return [(f"{tag}_{n}", w.rotate((0, 0, 0), (0, 0, 1), 180), c) for n, w, c in p]


MIRROR = True               # mirror the layout across the yard centreline: the stairs swap ends


def mirrored(p):
    """Mirror parts across X = 0 when MIRROR is set, swapping their east/west names to match."""
    if not MIRROR:
        return p
    swap = lambda n: n.replace("east_", "TMP_").replace("west_", "east_").replace("TMP_", "west_")
    return [(swap(n), w.mirror("YZ"), c) for n, w, c in p]


def bridge_parts():
    return mirrored(bridge() + [("east_" + n, w, c) for n, w, c in tower(switchback=False)]
                    + half_turn(tower(switchback=True), "west"))


def site_parts():
    s = east_site()
    p = [("east_" + n, w, c) for n, w, c in s] + half_turn(s, "west")
    for i, (x, y) in enumerate(((TRACKS[3], -9500), (TRACKS[1], 9500), (TRACKS[2], 14000))):
        p += hopper(f"hopper_{i}", x, y, CAR[i % 2])
    return mirrored(p)


def main(out):
    bridge_ = bridge_parts()
    ft = lambda v: round(v / 304.8, 1)
    for name, parts in (("Rail_Footbridge", bridge_), ("Rail_Footbridge_Site", bridge_ + site_parts())):
        asm = cq.Assembly(name=name)
        for n, w, c in parts:
            asm.add(w, name=n, color=c)
        asm.export(f"{out}/{name}.step")
        bb = asm.toCompound().BoundingBox()
        print(name, "ft: X", ft(bb.xlen), "Y", ft(bb.ylen), "Z", ft(bb.zlen), "| zmin", round(bb.zmin), "| parts", len(parts))
    edges = [t + s * CAR_HW for t in TRACKS for s in (1, -1)]
    print("overall span ft", ft(2 * XI), "| each arch ft", ft(XI - XP), "rise ft", ft(RISE), "| deck ft", ft(FL),
          "| clear over car envelope ft", ft(min(soffit(x) for x in edges)),
          "| pier to nearest track centre ft", ft(TRACKS[2] - XP - 75),
          "| stair", N, "risers of", round(R), "mm,", round(math.degrees(math.atan(R / G)), 1), "deg")


if __name__ == "__main__":
    main(sys.argv[1])
