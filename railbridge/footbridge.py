"""Industrial rail-yard crossover, bulk-terminal style: an open steel Pratt-truss walkway with a grating
deck, safety screens and a corrugated roof, spanning four tracks between two braced steel stair towers.
Each tower holds a switchback stair (four flights, grating treads, safety-yellow rails). The towers
sit on opposite sides of the walkway, so the two stairs run in opposite directions along the tracks.

Tracks run along Y; X = 0 is the middle of the yard. Units mm, Z up, ground (top of ballast) at Z = 0.

    python railbridge/footbridge.py OUT_DIR

writes Rail_Footbridge.step (walkway and towers) and Rail_Footbridge_Site.step (plus tracks,
footings and covered hopper cars).
"""
import math
import sys

import cadquery as cq

# ---------------------------------------------------------------- yard
GAUGE = 1435
TRACKS = (-6750, -2250, 2250, 6750)   # 4.5 m track centres
YARD_L = 60000
RT = 400                    # top of rail above ground
CLR = 7000                  # top of rail to underside of the bridge (23 ft)

# ---------------------------------------------------------------- walkway
ZB = RT + CLR               # underside of the bottom chord
FL = ZB + 250               # deck (walking surface)
WW = 1500                   # clear width between the trusses
TH = 1600                   # truss height above the deck
ROOF = FL + 2500            # roof beams

# ---------------------------------------------------------------- stair towers
TC = 11300                  # tower centre from the yard centre: 2.7 m from the outer track to the steel
TW = 1300                   # column lines at TC +- TW
LANE = 1000                 # clear flight width
N = 40                      # risers, four flights of ten
R = FL / N
G = 230                     # going: about a 40 degree industrial stair
FR = (N // 4 - 1) * G       # flight run
LD = 1600                   # landing depth
YN0, YN1 = -LD / 2, LD / 2  # near landings (the top one meets the walkway)
YF0, YF1 = YN1 + FR, YN1 + FR + LD   # far landings
TOP = FL + 2600             # tower roof beams

STEEL = cq.Color(0.6, 0.62, 0.64)    # galvanised
DARK = cq.Color(0.4, 0.41, 0.42)     # grating
YL = cq.Color(1.0, 0.78, 0.0)        # safety yellow
SHEET = cq.Color(0.72, 0.74, 0.76)   # corrugated roofing
SCREEN = cq.Color(0.3, 0.32, 0.34, 0.45)
CONC = cq.Color(0.72, 0.71, 0.68)
SLEEPER = cq.Color(0.35, 0.3, 0.27)
RAIL = cq.Color(0.5, 0.45, 0.4)
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


def corrugated(x0, x1, y0, y1, z0, z1, pitch=150, depth=35, t=4):
    """Corrugated sheet over x0..x1, sloping from z0 at y0 to z1 at y1, ribs running down the slope."""
    w, L = x1 - x0, math.hypot(y1 - y0, z1 - z0)
    n = max(2, int(w / (pitch / 2)))
    top = [(k * w / n, depth if k % 2 else 0) for k in range(n + 1)]
    s = yz_plate(top + [(u, z - t) for u, z in reversed(top)], 0, L)   # profile across Y, length along X
    s = s.rotate((0, 0, 0), (0, 0, 1), 90)                             # profile across -X, length along +Y
    s = s.rotate((0, 0, 0), (1, 0, 0), math.degrees(math.atan2(z1 - z0, y1 - y0)))
    return s.translate((x1, y0, z0))


def walkway():
    p = []
    X = TC - TW                      # the trusses run between the towers' inner column lines
    nb = 10
    xs = [-X + i * 2 * X / nb for i in range(nb + 1)]
    lo, hi = ZB + 350, FL + TH - 200
    for s in (1, -1):
        y = s * (WW / 2 + 125)
        p.append((f"bottom_chord_{s}", box(-X, X, y - 125, y + 125, ZB, lo), STEEL))
        p.append((f"top_chord_{s}", box(-X, X, y - 100, y + 100, hi, FL + TH), STEEL))
        for i, x in enumerate(xs):
            p.append((f"truss_vertical_{s}_{i}", box(x - 90, x + 90, y - 90, y + 90, lo, hi), STEEL))
            p.append((f"roof_post_{s}_{i}", box(x - 50, x + 50, y - 50, y + 50, FL + TH, ROOF), STEEL))
        for i in range(nb):
            a, b = xs[i], xs[i + 1]
            p0, p1 = ((a, y, hi), (b, y, lo)) if i < nb / 2 else ((a, y, lo), (b, y, hi))   # Pratt: diagonals fall toward midspan
            p.append((f"truss_diagonal_{s}_{i}", rod(45, p0, p1), STEEL))
            yi = s * (WW / 2 - 15)
            p.append((f"safety_screen_{s}_{i}", box(a + 90, b - 90, yi - 3, yi + 3, FL + 150, FL + TH + 500), SCREEN))
        yr = s * (WW / 2 - 50)
        p.append((f"handrail_{s}", rod(24, (-X, yr, FL + 1070), (X, yr, FL + 1070)), YL))
        p.append((f"midrail_{s}", rod(24, (-X, yr, FL + 530), (X, yr, FL + 530)), YL))
        p.append((f"toe_plate_{s}", box(-X, X, s * (WW / 2 - 10), s * (WW / 2 - 20), FL, FL + 100), YL))
    for i, x in enumerate(xs):
        p.append((f"floor_beam_{i}", box(x - 100, x + 100, -WW / 2, WW / 2, ZB, FL - 40), STEEL))
        p.append((f"roof_beam_{i}", box(x - 50, x + 50, -WW / 2 - 300, WW / 2 + 300, ROOF, ROOF + 150), STEEL))
    p.append(("deck_grating", box(-X, X, -WW / 2, WW / 2, FL - 40, FL), DARK))
    p.append(("roof_sheet", corrugated(-X - 300, X + 300, -WW / 2 - 450, WW / 2 + 450, ROOF + 200, ROOF + 130), SHEET))
    return p


def flight(k, x0, x1, climbs_far):
    """Flight k rises from level k to level k+1 in the lane x0..x1."""
    p = []
    zb = k * (N // 4) * R
    zt = zb + (N // 4) * R
    ya, yb = (YN1, YF0) if climbs_far else (YF0, YN1)      # bottom, top of the flight
    d = 1 if climbs_far else -1
    for i in range(1, N // 4):
        z = zb + i * R
        a = ya + d * (i - 1) * G
        p.append((f"tread_{k}_{i}", box(x0, x1, a, a + d * (G + 25), z - 40, z), DARK))
        p.append((f"nosing_{k}_{i}", box(x0, x1, a + d * (G + 25), a + d * (G - 15), z - 42, z + 1), YL))
    for s, x in enumerate((x0 - 60, x1 + 60)):
        prof = [(ya, max(zb - 250, 0)), (ya, zb + 100), (yb, zt + 100), (yb, zt - 250)]
        p.append((f"stringer_{k}_{s}", yz_plate(prof, x - 60, x + 60), STEEL))
        xr = x0 + 40 if s == 0 else x1 - 40
        p.append((f"flight_handrail_{k}_{s}", rod(24, (xr, ya, zb + 950), (xr, yb, zt + 950)), YL))
        p.append((f"flight_midrail_{k}_{s}", rod(24, (xr, ya, zb + 500), (xr, yb, zt + 500)), YL))
    return p


def tower():
    """East tower: the inner column line faces the tracks; landings stack at the near (-Y) and far (+Y) ends."""
    p = []
    xs, ys = (TC - TW, TC + TW), (YN0, YN1, YF0, YF1)
    levels = [k * (N // 4) * R for k in range(1, 5)]
    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            p.append((f"column_{i}_{j}", box(x - 100, x + 100, y - 100, y + 100, 0, TOP), STEEL))
            p.append((f"base_plate_{i}_{j}", box(x - 200, x + 200, y - 200, y + 200, 0, 25), DARK))
    for li, z in enumerate(levels + [TOP]):
        zt = z - 40 if li < 4 else z
        for i, x in enumerate(xs):
            p.append((f"side_beam_{li}_{i}", box(x - 100, x + 100, YN0, YF1, z - 300, zt), STEEL))
        for j, y in enumerate((YN0, YF1)):
            p.append((f"end_beam_{li}_{j}", box(xs[0], xs[1], y - 100, y + 100, z - 300, zt), STEEL))
    # landings: far at levels 1 and 3, near at 2 and 4 (4 is level with the walkway deck)
    for k, z in enumerate(levels, 1):
        y0, y1 = (YF0, YF1) if k % 2 else (YN0, YN1)
        p.append((f"landing_{k}", box(xs[0] + 100, xs[1] - 100, y0, y1, z - 40, z), DARK))
        ye = y1 if k % 2 else y0
        rails = [((xs[1] - 150, y0), (xs[1] - 150, y1)), ((xs[0] + 150, ye), (xs[1] - 150, ye))]
        if k != 4:                   # the top landing opens onto the walkway
            rails.append(((xs[0] + 150, y0), (xs[0] + 150, y1)))
        for r, ((ax, ay), (bx, by)) in enumerate(rails):
            for h in (530, 1070):
                p.append((f"landing_rail_{k}_{r}_{h}", rod(24, (ax, ay, z + h), (bx, by, z + h)), YL))
            for q in range(3):
                px, py = ax + q / 2 * (bx - ax), ay + q / 2 * (by - ay)
                p.append((f"landing_post_{k}_{r}_{q}", rod(24, (px, py, z), (px, py, z + 1070)), YL))
    # four flights in alternating lanes; the bottom one starts at the ground at the near end
    lane_in = (xs[0] + 150, xs[0] + 150 + LANE)
    lane_out = (xs[1] - 150 - LANE, xs[1] - 150)
    for k in range(4):
        x0, x1 = lane_out if k % 2 == 0 else lane_in
        p += flight(k, x0, x1, climbs_far=(k % 2 == 0))
    # X-bracing on the outer face and the far end
    zs = [300] + levels + [TOP]
    for li in range(len(zs) - 1):
        za, zb = zs[li] + 150, zs[li + 1] - 300
        for j in range(3):
            ya, yb = ys[j], ys[j + 1]
            p.append((f"brace_out_{li}_{j}_a", rod(30, (xs[1], ya, za), (xs[1], yb, zb)), STEEL))
            p.append((f"brace_out_{li}_{j}_b", rod(30, (xs[1], yb, za), (xs[1], ya, zb)), STEEL))
        p.append((f"brace_end_{li}_a", rod(30, (xs[0], YF1, za), (xs[1], YF1, zb)), STEEL))
        p.append((f"brace_end_{li}_b", rod(30, (xs[1], YF1, za), (xs[0], YF1, zb)), STEEL))
    p.append(("roof_sheet", corrugated(xs[0] - 400, xs[1] + 400, YN0 - 400, YF1 + 400, TOP + 300, TOP + 50), SHEET))
    return p


def hopper(tag, x, y, col):
    """A simple covered hopper car on the track at x, centred on y."""
    p = []
    L, W, H = 17500, 3200, 4600
    z0 = RT + 1100
    body = yz_plate([(y - L / 2, z0 + 600), (y - L / 2 + 1500, z0), (y + L / 2 - 1500, z0), (y + L / 2, z0 + 600),
                     (y + L / 2, RT + H), (y - L / 2, RT + H)], x - W / 2, x + W / 2)
    p.append((f"{tag}_body", body, col))
    p.append((f"{tag}_roof_walk", box(x - 300, x + 300, y - L / 2 + 500, y + L / 2 - 500, RT + H, RT + H + 60), DARK))
    for s in (1, -1):
        yt = y + s * (L / 2 - 2000)
        p.append((f"{tag}_bogie_{s}", box(x - 1100, x + 1100, yt - 1300, yt + 1300, RT + 300, RT + 900), BOGIE))
        for a in (-850, 850):
            p.append((f"{tag}_wheelset_{s}_{a}", rod(450, (x - GAUGE / 2 - 60, yt + a, RT + 450), (x + GAUGE / 2 + 60, yt + a, RT + 450)), BOGIE))
    return p


def east_site():
    p = []
    for k, x in enumerate(t for t in TRACKS if t > 0):
        for j in range(int(YARD_L / 1200)):
            y = -YARD_L / 2 + 600 + j * 1200
            p.append((f"sleeper_{k}_{j:02d}", box(x - 1300, x + 1300, y - 125, y + 125, 150, 250), SLEEPER))
        for s in (1, -1):
            xr = x + s * (GAUGE / 2 + 35)
            p.append((f"rail_{k}_{s}", box(xr - 35, xr + 35, -YARD_L / 2, YARD_L / 2, 250, RT), RAIL))
    for i, x in enumerate((TC - TW, TC + TW)):
        p.append((f"tower_footing_{i}", box(x - 500, x + 500, YN0 - 500, YF1 + 500, -300, 0), CONC))
    for n in range(2):
        p += hopper(f"hopper_{n}", TRACKS[-1], -14000 + n * 18500, CAR[n % 2])
    return p


def half_turn(p, tag):
    """The west half is the east half turned 180 degrees about Z."""
    return [(f"{tag}_{n}", w.rotate((0, 0, 0), (0, 0, 1), 180), c) for n, w, c in p]


def bridge_parts():
    t = tower()
    return walkway() + [("east_" + n, w, c) for n, w, c in t] + half_turn(t, "west")


def site_parts():
    s = east_site()
    return [("east_" + n, w, c) for n, w, c in s] + half_turn(s, "west")


def main(out):
    bridge = bridge_parts()
    ft = lambda v: round(v / 304.8, 1)
    for name, parts in (("Rail_Footbridge", bridge), ("Rail_Footbridge_Site", bridge + site_parts())):
        asm = cq.Assembly(name=name)
        for n, w, c in parts:
            asm.add(w, name=n, color=c)
        asm.export(f"{out}/{name}.step")
        bb = asm.toCompound().BoundingBox()
        print(name, "ft: X", ft(bb.xlen), "Y", ft(bb.ylen), "Z", ft(bb.zlen), "| zmin", round(bb.zmin), "| parts", len(parts))
    print("span between towers ft", ft(2 * (TC - TW)), "| clear over rail ft", ft(CLR),
          "| stair", N, "risers of", round(R), "mm, going", G, "mm,", round(math.degrees(math.atan(R / G)), 1), "deg",
          "| tower", 2 * TW + 200, "x", round(YF1 - YN0 + 200), "mm")


if __name__ == "__main__":
    main(sys.argv[1])
