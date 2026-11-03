"""Stack of six 24 in reinforced concrete pipes (RCP), bell-and-spigot, 3-2-1 on timber dunnage.

A generic, brand-neutral pipe-yard / job-site stack of storm-drain pipe, with the dimensions of
24 in circular RCP to the usual concrete-pipe standard (ASTM C76 / AASHTO M170 class), Wall B:

* each pipe: 24 in (610 mm) inside diameter, 3 in (76 mm) wall, so 30 in (762 mm) outside
  diameter over the barrel; 8 ft (2,438 mm) laying length, 2.55 m overall with the socket;
  roughly 2,400 lb (1.1 t) each;
* a bell-and-spigot (O-ring gasket) joint: the bell is an enlarged socket ~37 in (940 mm) OD,
  reached by a short conical shoulder, with a 744 mm socket 115 mm (4.5 in) deep and a chamfered
  entrance, stepping down to the 610 mm bore; the spigot is a 732 mm OD, 110 mm long reduced
  end with a cast gasket groove and a black rubber O-ring gasket stretched into it, a 45 deg
  shoulder back up to the barrel and a chamfered nose;
* the pipe ends are open (hollow) and every pipe has a cast lift hole through the top of the
  wall near its centre of gravity, and a stencilled marking (class, wall, date) on its side;
* six pipes stacked 3-2-1 in a pyramid, bells alternating ends, the bottom row on two 6 x 8
  timber skids (laid flat, 10 ft long, at about the fifth points of the pipe), the upper tiers
  on 6 x 6 dunnage laid across the crowns of the tier below, deep enough that a bell in one
  tier clears the bell under it; every pipe is held by a pair of nailed timber wedge chocks on
  each skid / dunnage timber. Timbers and pipes sit a few cm off true, as stacked by hand.

Bottom row at 880 mm centres (a bell clears its neighbour's barrel), the tiers above in the
valleys at 440 mm offsets. Overall ~2.6 m long (along the staggered pipes), ~3.05 m wide over the
skids (2.7 m over the bottom-row bells) and ~2.8 m high to the top of the uppermost bell.

Millimetres, X along the pipes, Y across the stack, Z up, ground at Z = 0.
"""

from __future__ import annotations

import math

import cadquery as cq

from cadkit import FT, IN, Finish, box, cut, cyl, mv, prism, rgb, rot, text, torus
from finishes import RUBBER, STEEL, TIMBER, TIMBER_DARK

ASSET = dict(key="concrete_pipe_stack", stem="Concrete_Pipe_Stack_24in", title="Concrete Pipe Stack (24 in RCP)",
             az=30, el=22, size="1200x900")

STENCIL = Finish(rgb("#2a2b2d"), rough=0.8)            # black spray-stencil marking
PIPE_CONCRETE = Finish(rgb("#807d76"), rough=0.95)     # weathered precast grey (CONCRETE renders near-white)
END_GRAIN = Finish(rgb("#5e4428"), rough=0.9)          # sawn timber ends, darker than the faces

# ---------------------------------------------------------------- pipe dimensions
RI = 12 * IN                # bore radius, 304.8 (24 in ID)
RO = RI + 3 * IN            # barrel radius, 381 (Wall B, 3 in)
LAY = 8 * FT                # laying length, 2438.4
DS = 115.0                  # socket depth
LO = LAY + DS               # overall length, 2553
RB = 470.0                  # bell outside radius (~37 in OD)
RS = 372.0                  # socket radius
RSP = 366.0                 # spigot radius
SPL = 110.0                 # spigot length
XG = (38.0, 62.0)           # gasket groove, from the spigot nose
GROOVE = 10.0               # groove depth
SHOULDER = (LO - 270.0, LO - 150.0)   # conical shoulder up to the bell

# ---------------------------------------------------------------- stack
PITCH = 880.0               # bottom-row centres
SKID_H, SKID_W = 140.0, 190.0         # 6 x 8 laid flat
DUN = 140.0                 # 6 x 6 dunnage between tiers
# supports at about the fifth points (~+-760 mm); hand-placed, so each tier's timbers (and each
# pipe, along its length) sit a little off the nominal
X_TIMBER = ((-760.0, 760.0), (-742.0, 778.0), (-781.0, 748.0))
SINK = 4.0                  # pipes bed into the timber, timber into the pipe crowns


def build(m):
    pipe = pipe_solid()
    gasket = torus(RSP - GROOVE + 4, m.r(12), (XG[0] / 2 + XG[1] / 2 - LO / 2, 0, 0), (1, 0, 0))

    # tiers: (y, bell direction) for each pipe; z of the pipe axis
    z1 = SKID_H + RO - SINK
    z2 = z1 + RO - SINK + DUN + RO - SINK
    z3 = z2 + RO - SINK + DUN + RO - SINK
    tiers = [
        (z1, [(-PITCH, 1, 22.0), (0.0, -1, -18.0), (PITCH, 1, 9.0)]),       # (y, bell end, x offset)
        (z2, [(-PITCH / 2, -1, -31.0), (PITCH / 2, 1, 17.0)]),
        (z3, [(0.0, 1, -12.0)]),
    ]

    # ground skids, then dunnage across the crowns of each tier
    skids = [box(x - SKID_W / 2, x + SKID_W / 2, -5 * FT, 5 * FT, 0, SKID_H) for x in X_TIMBER[0]]
    m.add("skids", TIMBER, skids)
    dunnage = []
    for (zc, row), half, xs in zip(tiers[:-1], (4 * FT, 2.5 * FT), X_TIMBER[1:]):
        zt = zc + RO - SINK
        dunnage += [box(x - DUN / 2, x + DUN / 2, -half, half, zt, zt + DUN) for x in xs]
    m.add("dunnage", TIMBER, dunnage)
    if not m.print_mode:     # darker end grain on every timber
        grain = []
        for b in skids + dunnage:
            bb = b.BoundingBox()
            grain += [box(bb.xmin + 3, bb.xmax - 3, y0, y1, bb.zmin + 3, bb.zmax - 3)
                      for y0, y1 in ((bb.ymin - 1.5, bb.ymin + 1), (bb.ymax - 1, bb.ymax + 1.5))]
        m.add("timber_end_grain", END_GRAIN, grain)

    chocks, nails = [], []
    for k, (zc, row) in enumerate(tiers):
        z0 = SKID_H if k == 0 else zc - RO + SINK      # top of the timber under this tier
        cw = 100.0 if k == 0 else 90.0
        for i, (y, d, dx) in enumerate(row):
            p = pipe if d > 0 else rot(pipe, 180, (0, 0, 1))
            m.add(f"pipe_{k + 1}{'abc'[i]}", PIPE_CONCRETE, mv(p, dx, y, zc))
            m.add(f"gasket_{k + 1}{'abc'[i]}", RUBBER,
                  mv(gasket if d > 0 else rot(gasket, 180, (0, 0, 1)), dx, y, zc))
            for xs in X_TIMBER[k]:
                for s in (1, -1):
                    w, nl = wedge(y, zc, z0, s, xs - cw / 2, xs + cw / 2, top=m.t(30))
                    chocks.append(w)
                    nails += nl
            if not m.print_mode:
                m.add(f"marking_{k + 1}{'abc'[i]}", STENCIL, marking(300 + dx, y, zc))
    m.add("wedge_chocks", TIMBER_DARK, chocks)
    if not m.print_mode:
        m.add("chock_nails", STEEL, nails)


# ---------------------------------------------------------------- one pipe

def pipe_solid():
    """One pipe along +X, bell at +X, spigot at -X, centred on the origin, with its lift hole."""
    g0, g1 = XG
    prof = [
        (0, RI), (0, RSP - 9), (9, RSP),                                       # spigot nose, chamfered
        (g0, RSP), (g0, RSP - GROOVE), (g1, RSP - GROOVE), (g1, RSP),          # gasket groove
        (SPL, RSP), (SPL + RO - RSP, RO),                                      # 45 deg shoulder to the barrel
        (SHOULDER[0], RO), (SHOULDER[1], RB),                                  # conical bell shoulder
        (LO - 14, RB), (LO, RB - 14),                                          # bell, chamfered lip
        (LO, RS + 14), (LO - 14, RS),                                          # socket entrance chamfer
        (LO - DS, RS), (LO - DS, RI),                                          # socket, stepping to the bore
    ]
    solid = cq.Workplane("XZ").polyline(prof).close().revolve(360, (0, 0, 0), (1, 0, 0)).val()
    xh = LO / 2 + 60                                                           # lift hole, near the CG
    solid = cut(solid, cyl(32, (xh, 0, RI - 40), (xh, 0, RO + 40)))
    return mv(solid, -LO / 2)


def marking(x, y, zc):
    """Stencilled class / wall / date marking on the +Y side, reading from that side."""
    out = []
    for line, deg in (('C76  CL III  24"', 30.0), ("WALL B  11-03-26", 18.5)):
        a = math.radians(deg)
        n = (0.0, math.cos(a), math.sin(a))
        r = RO - 4
        out.append(text(line, 58, 5.5, (x, y + r * n[1], zc + r * n[2]), (-1, 0, 0), n))
    return out


def wedge(yc, zc, z0, s, x0, x1, h=105.0, phi=40.0, top=30.0):
    """Timber wedge chock on a timber whose top is z0, against the pipe at (yc, zc), on side s.

    Its sloped face is tangent to a circle 6 mm inside the pipe, so it beds into the pipe."""
    a = math.radians(phi)
    rt = RO - 6
    py, pz = yc + s * rt * math.sin(a), zc - rt * math.cos(a)

    def y_at(z):
        return py + s * (z - pz) / math.tan(a)

    zb = z0 - 3
    y_toe, y_tf = y_at(zb), y_at(z0 + h)
    y_tb = y_tf + s * top
    y_bb = y_tb + s * 60          # back leans out: a clearly triangular wedge
    w = prism([(y_toe, zb), (y_tf, z0 + h), (y_tb, z0 + h), (y_bb, zb)], "x", x0, x1)
    xm, ym = (x0 + x1) / 2, (y_tf + y_tb) / 2
    nails = [cyl(7, (xm + dx, ym, z0 + h - 2), (xm + dx, ym, z0 + h + 2.5)) for dx in (-22, 22)]
    return w, nails
