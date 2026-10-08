"""Rail-yard crossover as built at bulk terminals: two white steel lattice towers, an arched truss walkway
between their tops, and a long, steep straight stair up the side of each tower.

The towers are square, with four legs, horizontal girts and X-bracing in every bay. The walkway's bottom
chord is a parabolic arch springing from the towers, so from track level the bridge reads as an arch,
while the deck stays flat to walk on; the side trusses double as the guards. The stairs have white
channel stringers, open grating treads, a yellow handrail on the track side and a white guard on the
other. They sit on opposite towers and climb in opposite directions along the tracks.

Tracks run along Y; X = 0 is midway between them. Units mm, Z up, top of rail and asphalt at Z = 0.

    python railbridge/footbridge.py OUT_DIR

writes Rail_Footbridge.step (towers, bridge, stairs) and Rail_Footbridge_Site.step (plus asphalt,
embedded rails, gravel around the tower bases and two covered hopper cars).
"""
import math
import sys

import cadquery as cq

# ---------------------------------------------------------------- yard
GAUGE = 1435
TRACKS = (-2250, 2250)
YARD_L = 50000
CAR_HW = 1600               # half-width of a freight car
CLR = 7000                  # clearance over the car envelope (23 ft)

# ---------------------------------------------------------------- towers
TS = 1500                   # tower size, leg centre to leg centre
TX = TRACKS[1] + 2600 + TS / 2   # tower centre: legs 2.6 m clear of the track centre
XI = TX - TS / 2            # inner leg line, where the arch springs

# ---------------------------------------------------------------- arched walkway
RISE = 1500                 # rise of the arch soffit from springing to crown
ZS = 6500                   # soffit at the springing
FL = ZS + RISE + 250        # flat deck, just above the crown
BW = 1200                   # clear walkway width
GUARD = 1100                # top chord above the deck

# ---------------------------------------------------------------- stairs
N = 44                      # risers
R = FL / N
G = 165                     # going: a steep (~50 degree) industrial stair, as on site
SW = 800                    # clear stair width
RUN = (N - 1) * G

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
    """Underside of the arch: a parabola from ZS at the springings (x = +-XI) to ZS + RISE at midspan."""
    return ZS + RISE * (1 - (x / XI) ** 2)


def bridge():
    p = []
    nb = 10
    xs = [-XI + i * 2 * XI / nb for i in range(nb + 1)]
    ss = [-XI + i * 2 * XI / 40 for i in range(41)]
    for s in (1, -1):
        y = s * (BW / 2 + 75)
        arch = [(x, soffit(x)) for x in ss] + [(x, soffit(x) + 300) for x in reversed(ss)]
        p.append((f"arch_chord_{s}", xz_plate(arch, y - 75, y + 75), WH))
        p.append((f"top_chord_{s}", box(-XI, XI, y - 75, y + 75, FL + GUARD - 150, FL + GUARD), WH))
        for i, x in enumerate(xs):
            p.append((f"vertical_{s}_{i}", box(x - 60, x + 60, y - 60, y + 60, soffit(x) + 300, FL + GUARD - 150), WH))
        for i in range(nb):
            a, b = xs[i], xs[i + 1]
            p0, p1 = ((a, y, soffit(a) + 300), (b, y, FL + GUARD - 150)) if i < nb / 2 else ((a, y, FL + GUARD - 150), (b, y, soffit(b) + 300))
            p.append((f"diagonal_{s}_{i}", rod(35, p0, p1), WH))
        yr = s * (BW / 2 - 40)
        p.append((f"handrail_{s}", rod(21, (-XI, yr, FL + 1000), (XI, yr, FL + 1000)), YL))
        p.append((f"toe_plate_{s}", box(-XI, XI, s * (BW / 2 - 5), s * (BW / 2 - 15), FL, FL + 100), YL))
    for i, x in enumerate(xs):
        z = min(soffit(x) + 300, FL - 300)
        p.append((f"floor_beam_{i}", box(x - 60, x + 60, -BW / 2, BW / 2, z, FL - 40), WH))
    p.append(("deck_grating", box(-XI, XI, -BW / 2, BW / 2, FL - 40, FL), GT))
    return p


def tower():
    """East tower, centred on (TX, 0), with its stair on the -Y side climbing toward the tower."""
    p = []
    h = TS / 2
    legs = [(TX - h, -h), (TX + h, -h), (TX + h, h), (TX - h, h)]
    for k, (x, y) in enumerate(legs):
        p.append((f"leg_{k}", box(x - 75, x + 75, y - 75, y + 75, 25, FL - 40), WH))
        p.append((f"base_plate_{k}", box(x - 175, x + 175, y - 175, y + 175, 0, 25), DK))
    levels = [25 + i * (FL - 65) / 5 for i in range(6)]
    for li, z in enumerate(levels[1:], 1):
        for k in range(4):
            (x1, y1), (x2, y2) = legs[k], legs[(k + 1) % 4]
            p.append((f"girt_{li}_{k}", rod(45, (x1, y1, z - 45), (x2, y2, z - 45)), WH))
    for bi in range(5):
        za, zb = levels[bi] + (150 if bi == 0 else 0), levels[bi + 1] - 90
        for k in range(4):
            (x1, y1), (x2, y2) = legs[k], legs[(k + 1) % 4]
            p.append((f"brace_{bi}_{k}_a", rod(28, (x1, y1, za), (x2, y2, zb)), WH))
            p.append((f"brace_{bi}_{k}_b", rod(28, (x2, y2, za), (x1, y1, zb)), WH))
    # top platform, guarded on the outer face and the +Y side (the arch arrives from -X, the stair from -Y)
    p.append(("top_platform", box(TX - h - 75, TX + h + 75, -h - 75, h + 75, FL - 40, FL), GT))
    for r, ((ax, ay), (bx, by)) in enumerate((((TX + h, -h), (TX + h, h)), ((TX - h, h), (TX + h, h)))):
        for hgt in (530, 1070):
            p.append((f"top_rail_{r}_{hgt}", rod(21, (ax, ay, FL + hgt), (bx, by, FL + hgt)), YL))
        p.append((f"top_toe_{r}", box(ax, bx if bx != ax else ax + 10, ay, by if by != ay else ay + 10, FL, FL + 100), YL))
    for k, (x, y) in enumerate(legs):
        p.append((f"top_post_{k}", rod(25, (x, y, FL), (x, y, FL + 1070)), WH))
    p += stair()
    return p


def stair():
    """Straight stair centred on the tower's x, climbing along +Y and arriving at the tower's -Y face."""
    p = []
    ye = -TS / 2 - 75                  # top of the flight
    ys = ye - RUN                      # foot of the flight
    slope = FL / (RUN + G)
    SD = 300                           # stringer depth
    for s in (1, -1):
        x = TX + s * (SW / 2 + 6)
        web = yz_plate([(ys - G, 0), (ye, FL), (ye, FL + SD * 0.6), (ys - G - SD / slope, 0)], x - 6, x + 6)
        p.append((f"stringer_{s}", web, WH))
        for k, dz in enumerate((0, SD * 0.6 - 10)):
            fl = yz_plate([(ys - G - dz / slope, 0), (ye, FL + dz - SD * 0.0), (ye, FL + dz + 10), (ys - G - (dz + 10) / slope, 0)],
                          x + s * 6, x + s * 80)
            p.append((f"stringer_flange_{s}_{k}", fl, WH))
    for i in range(1, N):
        z = i * R
        y0 = ys + (i - 1) * G
        t = box(TX - SW / 2, TX + SW / 2, y0 - 15, y0 + G + 15, z - 35, z)
        for k in range(5):
            t = t.cut(box(TX - SW / 2 + 30, TX + SW / 2 - 30, y0 + 10 + k * 34, y0 + 26 + k * 34, z - 36, z + 1))
        p.append((f"tread_{i:02d}", t, GT))
        p.append((f"nosing_{i:02d}", box(TX - SW / 2, TX + SW / 2, y0 + G - 10, y0 + G + 15, z - 40, z), YL))
    # yellow handrail on the track side (-X), white guard on the outer side, as on site
    for s, col in ((-1, YL), (1, WH)):
        x = TX + s * (SW / 2 + 45)
        ya, za = ys + G * 0.5, R * 1.5
        p.append((f"stair_top_rail_{s}", rod(21, (x, ya, za + 900), (x, ye, FL + 900)), col))
        p.append((f"stair_mid_rail_{s}", rod(21, (x, ya, za + 450), (x, ye, FL + 450)), col))
        for k, i in enumerate(range(1, N, 7)):
            y = ys + (i - 1) * G + G * 0.5
            p.append((f"stair_post_{s}_{k}", rod(21, (x, y, max(i * R - 200, 0)), (x, y, i * R + 940)), col))
    # support frames at a third and two thirds of the way up
    for j, f in enumerate((1 / 3, 2 / 3)):
        ym = ys + RUN * f
        zm = FL * f - 350
        for s in (1, -1):
            x = TX + s * (SW / 2 + 6)
            p.append((f"stair_support_leg_{j}_{s}", box(x - 50, x + 50, ym - 50, ym + 50, 0, zm), WH))
        p.append((f"stair_support_beam_{j}", box(TX - SW / 2 - 60, TX + SW / 2 + 60, ym - 50, ym + 50, zm - 150, zm), WH))
        p.append((f"stair_support_brace_{j}", rod(25, (TX - SW / 2, ym, 200), (TX + SW / 2, ym, zm - 150)), WH))
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
    x = TRACKS[1]
    for s in (1, -1):
        xr = x + s * (GAUGE / 2 + 35)
        p.append((f"rail_{s}", box(xr - 35, xr + 35, -YARD_L / 2, YARD_L / 2, -150, 10), RAIL))
    p.append(("asphalt", box(0, TX - TS / 2 - 600, -YARD_L / 2, YARD_L / 2, -150, 0), ASPHALT))
    p.append(("asphalt_outer", box(TX + TS / 2 + 600, TX + 6000, -YARD_L / 2, YARD_L / 2, -150, 0), ASPHALT))
    p.append(("gravel_strip", box(TX - TS / 2 - 600, TX + TS / 2 + 600, -YARD_L / 2, YARD_L / 2, -150, -20), GRAVEL))
    p += hopper("hopper", x, -9500, CAR[0])
    return p


def half_turn(p, tag):
    """The west half is the east half turned 180 degrees about Z."""
    return [(f"{tag}_{n}", w.rotate((0, 0, 0), (0, 0, 1), 180), c) for n, w, c in p]


def bridge_parts():
    t = tower()
    return bridge() + [("east_" + n, w, c) for n, w, c in t] + half_turn(t, "west")


def site_parts():
    s = east_site()
    west = half_turn(s, "west")
    return [("east_" + n, w, c) for n, w, c in s] + [(n, w, CAR[1] if n.endswith("hopper_body") else c) for n, w, c in west]


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
    clear = min(soffit(x) for x in (t + s * CAR_HW for t in TRACKS for s in (1, -1)))
    print("arch span ft", ft(2 * XI), "rise ft", ft(RISE), "| deck ft", ft(FL),
          "| clear over car envelope ft", ft(clear), "| stair", N, "risers of", round(R), "mm, going", G,
          "mm,", round(math.degrees(math.atan(R / G)), 1), "deg, run ft", ft(RUN))


if __name__ == "__main__":
    main(sys.argv[1])
