"""Station footbridge: an enclosed, barrel-roofed walkway over the two middle tracks, landing on two
island platforms by enclosed stairs that turn 90 degrees off the walkway and descend in opposite
directions along the platforms.

Tracks run along Y; X = 0 is midway between the two middle tracks. Units mm, Z up.

    python railbridge/footbridge.py OUT_DIR

writes Rail_Footbridge.step (the bridge alone, platform level at Z = 0) and
Rail_Footbridge_Site.step (bridge plus platforms, canopies and four tracks, ground at Z = 0).
"""
import math
import sys

import cadquery as cq

# ---------------------------------------------------------------- site layout
GAUGE = 1435
TRACK_C = 4500             # centre-to-centre of the two middle tracks
EDGE = 1600                # track centre to platform edge
PLAT_W = 10000             # island platform width
PLAT_L = 60000
RT = 400                   # top of rail above ground
PT = RT + 1220             # platform top (48 in above rail)
CLR = 7000                 # clearance, top of rail to underside of the bridge (23 ft)

P_IN = TRACK_C / 2 + EDGE  # platform inner edge  (3850)
P_OUT = P_IN + PLAT_W      # platform outer edge (13850)
OUTER_TRACK = P_OUT + EDGE

# ---------------------------------------------------------------- bridge
ZB = RT + CLR              # underside of the girders
FL = ZB + 300              # walkway floor
WW = 3000                  # clear walkway width
GW = 300                   # girder width
GD = 900                   # girder depth (stands 600 above the floor as a parapet)
WALL = 2600                # floor to eaves
ROOF_RISE = 600

# ---------------------------------------------------------------- stairs
XS = 7000                  # stair centreline on the east platform
SW = 2400                  # clear stair width
N = 36                     # risers, two flights of 18
R = (FL - PT) / N
G = 280                    # going
LD = 1800                  # intermediate landing
FLIGHT = (N // 2 - 1) * G
RUN = 2 * FLIGHT + LD
HEAD = 2900                # roof above the pitch line
SX0, SX1 = XS - SW / 2 - 100, XS + SW / 2 + 100   # stair outer faces
XE = SX1 + 600             # walkway ends

WH = cq.Color(0.92, 0.92, 0.9)
BL = cq.Color(0.16, 0.36, 0.62)
GL = cq.Color(0.55, 0.75, 0.88, 0.4)
GT = cq.Color(0.58, 0.58, 0.57)
CO = cq.Color(0.74, 0.73, 0.7)
YL = cq.Color(1.0, 0.8, 0.0)
SS = cq.Color(0.75, 0.77, 0.8)
RF = cq.Color(0.8, 0.82, 0.84)
BA = cq.Color(0.45, 0.42, 0.4)
SL = cq.Color(0.35, 0.3, 0.27)
RA = cq.Color(0.5, 0.45, 0.4)


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


def walkway():
    p = []
    yo = WW / 2 + GW
    # girders: full depth, except where a stair leaves, where they stop at the floor
    for s in (1, -1):
        y0, y1 = s * WW / 2, s * yo
        gap = (SX0, SX1) if s == 1 else (-SX1, -SX0)        # east stair leaves +Y, west stair -Y
        p.append((f"girder_{s}_a", box(-XE, gap[0], y0, y1, ZB, ZB + GD), WH))
        p.append((f"girder_{s}_b", box(gap[0], gap[1], y0, y1, ZB, FL), WH))
        p.append((f"girder_{s}_c", box(gap[1], XE, y0, y1, ZB, ZB + GD), WH))
    p.append(("walkway_floor", box(-XE, XE, -WW / 2, WW / 2, FL - 150, FL), GT))
    for i in range(13):
        x = -XE + 150 + i * (2 * XE - 300) / 12
        p.append((f"floor_crossbeam_{i}", box(x - 100, x + 100, -WW / 2, WW / 2, ZB, FL - 150), WH))
    # side walls: glazing above the parapet, mullions, eaves beams
    zt = FL + WALL
    nb = 12
    for s in (1, -1):
        yg = s * (WW / 2 + GW / 2)
        gap = (SX0, SX1) if s == 1 else (-SX1, -SX0)
        xs = [-XE + i * 2 * XE / nb for i in range(nb + 1)]
        for i in range(nb):
            a, b = xs[i], xs[i + 1]
            for lo, hi in ((a, min(b, gap[0])), (max(a, gap[1]), b)):
                if hi - lo > 50:
                    p.append((f"wall_glass_{s}_{i}_{int(lo)}", box(lo, hi, yg - 12, yg + 12, ZB + GD, zt), GL))
        for i, x in enumerate(xs + list(gap)):
            p.append((f"wall_mullion_{s}_{i}", box(x - 60, x + 60, yg - 60, yg + 60, FL if gap[0] <= x <= gap[1] else ZB + GD, zt), WH))
        p.append((f"eaves_beam_{s}", box(-XE, XE, s * WW / 2, s * yo, zt, zt + 200), WH))
        p.append((f"handrail_{s}", rod(25, (-XE, s * (WW / 2 - 60), FL + 900), (gap[0], s * (WW / 2 - 60), FL + 900)), SS))
        p.append((f"handrail_{s}_b", rod(25, (gap[1], s * (WW / 2 - 60), FL + 900), (XE, s * (WW / 2 - 60), FL + 900)), SS))
    for s in (1, -1):
        x = s * XE
        p.append((f"end_glass_{s}", box(x - s * 24, x, -WW / 2, WW / 2, FL, zt), GL))
        p.append((f"end_frame_{s}", box(x - s * 120, x, -yo, yo, ZB, FL), WH))
    # barrel roof
    z0, t, B = zt + 200, 100, WW / 2 + GW + 150
    roof = (cq.Workplane("YZ").moveTo(-B, z0).threePointArc((0, z0 + ROOF_RISE), (B, z0))
            .lineTo(B - t, z0).threePointArc((0, z0 + ROOF_RISE - t), (-B + t, z0)).close()
            .extrude(2 * XE + 400).translate((-XE - 200, 0, 0)))
    p.append(("roof", roof, RF))
    # portal frames standing on the platforms
    for side in (1, -1):
        for k, x in enumerate((XS - SW / 2 - 700, XE - 250)):
            x *= side
            for s in (1, -1):
                y = s * (WW / 2 + GW / 2)
                p.append((f"column_{side}_{k}_{s}", box(x - 175, x + 175, y - 175, y + 175, PT, ZB - 400), WH))
                p.append((f"column_base_{side}_{k}_{s}", box(x - 300, x + 300, y - 300, y + 300, PT, PT + 30), GT))
            p.append((f"portal_beam_{side}_{k}", box(x - 200, x + 200, -WW / 2 - GW - 100, WW / 2 + GW + 100, ZB - 400, ZB), WH))
    return p


def east_stair():
    """Stair off the walkway's +Y side, descending toward +Y onto the east platform."""
    p = []
    y0 = WW / 2 + GW                          # top of the stair, at the outer face of the girder
    yL0 = y0 + FLIGHT
    yL1 = yL0 + LD
    yE = yL1 + FLIGHT                         # foot of the stair
    zL = FL - (N // 2) * R
    xi0, xi1 = XS - SW / 2, XS + SW / 2
    # head landing bridging the girder gap to the stair
    p.append(("stair_head_landing", box(xi0, xi1, WW / 2, y0, FL - 150, FL), GT))
    # treads and nosings
    for f, (ys, ztop) in enumerate(((y0, FL), (yL1, zL))):
        for i in range(1, N // 2):
            z = ztop - i * R
            a = ys + (i - 1) * G
            p.append((f"tread_{f}_{i:02d}", box(xi0, xi1, a, a + G + 20, z - 50, z), GT))
            p.append((f"nosing_{f}_{i:02d}", box(xi0, xi1, a, a + 40, z - 52, z + 1), YL))
    p.append(("stair_mid_landing", box(xi0, xi1, yL0, yL1, zL - 200, zL), GT))
    for s in (1, -1):
        for k, y in enumerate((yL0 + 150, yL1 - 150)):
            x = XS + s * (SW / 2 + 50)
            p.append((f"landing_post_{s}_{k}", box(x - 100, x + 100, y - 100, y + 100, PT, zL - 200), WH))
    # stringers, one pair per flight
    for f, (ya, za) in enumerate(((y0, FL), (yL1, zL))):
        yb, zb = ya + FLIGHT, za - (N // 2) * R
        for s in (1, -1):
            x = XS + s * (SW / 2 + 50)
            p.append((f"stringer_{f}_{s}", yz_plate([(ya, za + 80), (yb, zb + R + 80), (yb, max(zb - 260, PT)), (ya, za - 260)], x - 50, x + 50), WH))
            for h in (900, 1000):
                rail = rod(25, (XS + s * (SW / 2 - 60), ya, za - R + h), (XS + s * (SW / 2 - 60), yb, zb + R + h))
                p.append((f"stair_handrail_{f}_{s}_{h}", rail, SS))
    # enclosure: blue cladding below a straight pitch line, glazing above it, a sloped roof
    pitch = (FL - PT) / (yE - y0)
    zp = lambda y: FL - (y - y0) * pitch
    for s in (1, -1):
        x0 = XS + s * (SW / 2 + 100)
        x1 = x0 + s * 30
        p.append((f"cladding_{s}", yz_plate([(y0, PT), (y0, FL - 300), (yE - 300 / pitch, PT)], x0, x1), BL))
        p.append((f"stair_glass_{s}", yz_plate([(y0, FL - 300), (y0, FL + HEAD), (yE, PT + HEAD), (yE - 300 / pitch, PT)], x0, x1), GL))
        n = 8
        for i in range(n + 1):
            y = y0 + 60 + i * (yE - y0 - 120) / n
            p.append((f"stair_mullion_{s}_{i}", box(x0 - s * 20, x0 + s * 100, y - 50, y + 50, PT, zp(y) + HEAD), WH))
    t = 120
    p.append(("stair_roof", yz_plate([(y0, FL + HEAD), (yE + 600, PT + HEAD - 600 * pitch),
                                      (yE + 600, PT + HEAD - 600 * pitch + t), (y0, FL + HEAD + t)], SX0 - 150, SX1 + 150), RF))
    return p


def east_site():
    p = []
    xc = (P_IN + P_OUT) / 2
    p.append(("platform", box(P_IN, P_OUT, -PLAT_L / 2, PLAT_L / 2, 0, PT), CO))
    for k, x in enumerate((P_IN, P_OUT)):
        e = 1 if k == 0 else -1
        p.append((f"platform_edge_{k}", box(x, x + e * 600, -PLAT_L / 2, PLAT_L / 2, PT, PT + 5), YL))
    # canopy beside the stair, on the outer half of the platform (it passes under the walkway)
    cx0, cx1 = SX1 + 700, P_OUT - 400
    cz = PT + 3600
    p.append(("canopy_roof", box(cx0, cx1, -PLAT_L / 2 + 3000, PLAT_L / 2 - 3000, cz, cz + 250), RF))
    p.append(("canopy_fascia_a", box(cx0, cx0 + 80, -PLAT_L / 2 + 3000, PLAT_L / 2 - 3000, cz - 300, cz + 250), WH))
    p.append(("canopy_fascia_b", box(cx1 - 80, cx1, -PLAT_L / 2 + 3000, PLAT_L / 2 - 3000, cz - 300, cz + 250), WH))
    cc = (cx0 + cx1) / 2
    for i in range(7):
        y = -PLAT_L / 2 + 3000 + 1500 + i * (PLAT_L - 9000) / 6
        if abs(y) < WW:                       # keep clear of the bridge columns
            y += 3000
        p.append((f"canopy_column_{i}", rod(110, (cc, y, PT), (cc, y, cz)), WH))
    for k, x in enumerate((TRACK_C / 2, OUTER_TRACK)):
        p.append((f"ballast_{k}", box(x - 1700, x + 1700, -PLAT_L / 2, PLAT_L / 2, 0, 150), BA))
        for j in range(int(PLAT_L / 1200)):
            y = -PLAT_L / 2 + 600 + j * 1200
            p.append((f"sleeper_{k}_{j:02d}", box(x - 1300, x + 1300, y - 125, y + 125, 150, 250), SL))
        for s in (1, -1):
            xr = x + s * (GAUGE / 2 + 35)
            p.append((f"rail_{k}_{s}", box(xr - 35, xr + 35, -PLAT_L / 2, PLAT_L / 2, 250, RT), RA))
    return p


def half_turn(p, tag):
    """The west half is the east half turned 180 degrees about Z."""
    return [(f"{tag}_{n}", w.rotate((0, 0, 0), (0, 0, 1), 180), c) for n, w, c in p]


def assemble(parts, name, dz):
    asm = cq.Assembly(name=name)
    for n, w, c in parts:
        asm.add(w.translate((0, 0, dz)), name=n, color=c)
    return asm


def main(out):
    stair = east_stair()
    bridge = walkway() + [("east_" + n, w, c) for n, w, c in stair] + half_turn(stair, "west")
    site = [("east_" + n, w, c) for n, w, c in east_site()] + half_turn(east_site(), "west")
    a = assemble(bridge, "Rail_Footbridge", -PT)
    a.export(f"{out}/Rail_Footbridge.step")
    b = assemble(bridge + site, "Rail_Footbridge_Site", 0)
    b.export(f"{out}/Rail_Footbridge_Site.step")
    ft = lambda v: round(v / 304.8, 1)
    for asm in (a, b):
        bb = asm.toCompound().BoundingBox()
        print(asm.name, "ft: X", ft(bb.xlen), "Y", ft(bb.ylen), "Z", ft(bb.zlen), "| zmin", round(bb.zmin))
    print("bridge parts", len(bridge), "| site parts", len(bridge) + len(site))
    print("span between platforms ft", ft(2 * P_IN), "| walkway ft", ft(2 * XE), "| clear over rail ft", ft(CLR),
          "| stair", N, "risers of", round(R), "mm, going", G, "| stair run ft", ft(RUN),
          "| pitch deg", round(math.degrees(math.atan(R / G)), 1))


if __name__ == "__main__":
    main(sys.argv[1])
