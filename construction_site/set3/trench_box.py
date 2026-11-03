"""Steel trench shield (trench box), 8 ft tall x 20 ft long, 4 ft inside width, set on the ground.

A generic, brand-neutral excavation-safety shield with the typical proportions of a medium steel
trench box of the class:

* two side panels, each 20 ft long (6,096 mm) x 8 ft tall (2,438 mm) and 120 mm (~4.7 in)
  thick: a double-skin sandwich of two steel skins over internal stiffeners, closed by a heavy
  cap channel along the top edge and a vertical channel at each end (open outwards, so the
  channel section reads on the end of the box, with stacking / extension pin holes through its
  flanges); both channels stand 20 mm proud of the skins and frame the panel faces;
* a knife edge along the bottom of each panel: the inner skin bevels in over the bottom
  ~280 mm to a ~35 mm flat, the outer skin runs straight down, so the box can be pushed into
  the soil; the bottom 50 mm is worn to bare steel;
* outer faces with welded flat-bar stiffening ribs (90 x 40 mm: five vertical ribs at 40 in
  centres and a horizontal rib along the top of the knife edge) and round socket bosses where
  the spreader sockets pass through (standing a little prouder than the ribs); a fleet-number
  stencil and a tabulated-data decal on each outer face (a raised blank plate in the print);
* four tubular spreaders (152 mm / 6 in OD galvanised pipe), two at each end, upper and lower,
  giving the 4 ft (1,219 mm) clear inside width; each spreader end has a 200 mm OD collar
  that slides over the panel's spreader socket and is held by a vertical pin with a T handle
  and a red keeper clip; each socket is a bolted 340 mm square backing plate on the inner skin;
  ~1.1 m (43 in) pipe clearance under the lower spreaders;
* four lifting padeyes on the top corners (32 mm plate, 84 mm hole, with gussets), each with a
  galvanised ~1 in bow shackle standing ready for the sling; stacking-pin sockets on the top
  channel at the ends; a pulling eye on every end channel near the bottom (below the lower
  pin holes) for dragging the box along the trench.

Print (1:50): the end-channel flanges, socket and eye rings go through m.t() so nothing is under
0.8 mm, and the knife-edge flat widens to 60 mm full size (1.2 mm) for bed adhesion.

Overall ~6.37 m long over the pulling eyes (6.10 m panels), ~1.55 m wide over the socket bosses
(1.46 m over the skins, 1.22 m inside), ~2.64 m high to the top of the shackles (2.44 m panels).

Millimetres, X along the length (+X end towards the camera), Y across (left panel at +Y),
Z up, ground at Z = 0.
"""

from __future__ import annotations

import math

from cadkit import FT, Finish, arc_pts, box, clip_poly, cut, cyl, prism, rgb, text, torus
from finishes import BLACK, GALV, RED, STEEL, YELLOW

ASSET = dict(key="trench_box", stem="Trench_Shield_8x20ft", title="Trench Shield (8 x 20 ft)",
             az=35, el=25, size="1200x900")

PAINT = YELLOW
WORN = Finish(rgb("#5b6066"), metal=0.75, rough=0.4)        # bare steel at the knife edge
SHACKLE = Finish(rgb("#c7ccd0"), metal=0.75, rough=0.35)    # hot-dip galvanised shackles
DECAL = Finish(rgb("#f4f4ef"), rough=0.5)

# ---------------------------------------------------------------- main dimensions
L = 20 * FT                 # panel length, 6096
H = 8 * FT                  # panel height, 2438
WI = 4 * FT                 # clear inside width, 1219
T = 120.0                   # panel thickness
YI = WI / 2                 # inner skin, |Y|
YO = YI + T                 # outer skin, |Y|
YC = (YI + YO) / 2          # panel centre plane, |Y|
ZK = 280.0                  # top of the knife-edge bevel
CH = 20.0                   # how far the edge channels stand proud of the skins
TOPC = 150.0                # depth of the top cap channel
ENDC = 110.0                # depth (along X) of the end channels
X_SPR = L / 2 - 650.0       # spreader centres, |X|
Z_SPR = (1250.0, 2020.0)    # lower and upper spreader heights
R_PIPE, R_COL = 76.0, 100.0  # spreader pipe and collar radii
COL_LEN = 230.0             # collar length
X_LUG = L / 2 - 400.0       # padeyes, |X|
X_STACK = L / 2 - 190.0     # stacking sockets, |X|
Z_PULL = 380.0              # pulling eyes on the end channels (below the lower pin holes)


def build(m):
    for s, side in ((1, "L"), (-1, "R")):
        panel(m, s, side)
    spreaders(m)


# ---------------------------------------------------------------- one side panel

def panel(m, s, side):
    """Side panel at y = s * (YI .. YO): sandwich, knife edge, edge channels, ribs, lugs."""
    xe = L / 2 - ENDC + 5           # the skins run into the end channels by 5 mm

    # knife edge: the inner skin bevels in to a narrow flat, the outer skin runs straight down
    tip = max(35.0, 1.5 * m.min)    # a wider flat in print (1.2 mm at 1:50) for bed adhesion
    sec = [(YO, 0), (YO - tip, 0), (YI, ZK), (YI, ZK + 10), (YO, ZK + 10)]
    flip = [(s * y, z) for y, z in sec]
    lo, hi = sorted((s * YI, s * YO))
    m.add(f"knife_edge_{side}", PAINT, prism(clip_poly(flip, lo, hi, 45, ZK + 10), "x", -L / 2, L / 2))
    m.add(f"cutting_edge_{side}", WORN, prism(clip_poly(flip, lo, hi, 0, 50), "x", -L / 2, L / 2))

    # the sandwich between the skins, and the cap channel along the top
    slab = box(-xe, xe, s * YI, s * YO, ZK, H - TOPC + 10)
    cap = box(-xe, xe, s * (YI - CH), s * (YO + CH), H - TOPC, H)
    m.add(f"panel_{side}", PAINT, slab, cap)

    # end channels, open outwards, with pin holes through the flanges
    ends = []
    for e in (1, -1):
        ch = box(e * (L / 2 - ENDC), e * L / 2, s * (YI - CH), s * (YO + CH), ZK, H)
        recess = box(e * (L / 2 - 70), e * (L / 2 + 1), s * (YI - CH + m.t(22)), s * (YO + CH - m.t(22)),
                     ZK + m.t(25), H - m.t(25))
        holes = [cyl(28, (e * (L / 2 - 35), s * (YI - 30), z), (e * (L / 2 - 35), s * (YO + 30), z))
                 for z in (ZK + 230, H - 330)]
        ends.append(cut(ch, recess, *holes))
    m.add(f"end_channels_{side}", PAINT, ends)

    # outer face: vertical flat-bar ribs, a rib along the top of the knife edge, socket bosses
    rp = 40.0
    ribs = [box(x - 45, x + 45, s * (YO - 2), s * (YO + rp), ZK + 70, H - TOPC + 5)
            for x in (-2032.0, -1016.0, 0.0, 1016.0, 2032.0)]
    ribs.append(box(-xe, xe, s * (YO - 2), s * (YO + rp), ZK, ZK + 80))
    bosses = [cyl(115, (e * X_SPR, s * (YO - 2), z), (e * X_SPR, s * (YO + 28), z))
              for e in (1, -1) for z in Z_SPR]
    bosses += [cyl(70, (e * X_SPR, s * (YO + 5), z), (e * X_SPR, s * (YO + 46), z))
               for e in (1, -1) for z in Z_SPR]
    m.add(f"outer_ribs_{side}", PAINT, ribs, bosses)

    # inner face: bolted spreader-socket backing plates
    plates, bolts = [], []
    for e in (1, -1):
        for z in Z_SPR:
            x = e * X_SPR
            plates.append(box(x - 170, x + 170, s * (YI - 25), s * (YI + 5), z - 170, z + 170))
            for dx in (-130, 130):
                for dz in (-130, 130):
                    hexa = [(x + dx + 24 * math.cos(math.radians(30 + 60 * k)),
                             z + dz + 24 * math.sin(math.radians(30 + 60 * k))) for k in range(6)]
                    bolts.append(prism(hexa, "y", s * (YI - 20), s * (YI - 42)))
    m.add(f"socket_plates_{side}", PAINT, plates)
    m.add(f"socket_bolts_{side}", STEEL, bolts)

    # lifting padeyes on the top corners, with gussets, and a bow shackle in each
    pt = m.t(32)
    lugs, shackles, shackle_pins = [], [], []
    for e in (1, -1):
        x = e * X_LUG
        zh = H + 70.0
        prof = [(x - 130, H - 20), (x + 130, H - 20)] + arc_pts(x, zh, 130, 0, 180, 20)
        eye = prism(prof, "y", s * YC - pt / 2, s * YC + pt / 2)
        lugs.append(cut(eye, cyl(42, (x, s * YC - 100, zh), (x, s * YC + 100, zh))))
        gt = m.t(16)
        for dx in (-95, 95):
            for d in (1, -1):
                y0 = s * YC + d * (pt / 2 - 3)
                y1 = s * YC + d * (pt / 2 + 55)
                lugs.append(prism([(y0, H - 5), (y1, H - 5), (y0, H + 60)], "x", x + dx - gt / 2, x + dx + gt / 2))
        # shackle: pin through the eye, resting on the bottom of the hole
        rp_ = m.r(16)
        rl = m.r(14)
        zp = zh - (42 - rp_) + 3
        off = pt / 2 + rl + 3
        zb = zp + 110
        shackle_pins.append(cyl(rp_, (x, s * YC - off - 28, zp), (x, s * YC + off + 24, zp)))
        shackle_pins.append(cyl(rp_ + 10, (x, s * YC - off - 28, zp), (x, s * YC - off - 14, zp)))
        for d in (1, -1):
            shackles.append(cyl(rl, (x, s * YC + d * off, zp), (x, s * YC + d * off, zb)))
            shackles.append(cyl(rl + 7, (x, s * YC + d * off, zp - 22), (x, s * YC + d * off, zp + 22)))
        bow = torus(off, rl, (x, s * YC, zb), (1, 0, 0)).intersect(
            box(x - 100, x + 100, s * YC - 200, s * YC + 200, zb, zb + 200))
        shackles.append(bow)
    m.add(f"padeyes_{side}", PAINT, lugs)
    m.add(f"shackles_{side}", SHACKLE, shackles)
    m.add(f"shackle_pins_{side}", STEEL, shackle_pins)

    # stacking-pin sockets on the top channel and pulling eyes on the end channels
    socks, eyes = [], []
    for e in (1, -1):
        x = e * X_STACK
        socks.append(cut(cyl(28 + m.t(20), (x, s * YC, H - 20), (x, s * YC, H + 45)),
                         cyl(28, (x, s * YC, H - 10), (x, s * YC, H + 50))))
        xb = e * (L / 2 + 90)
        re = 26 + m.t(19)           # eye half-width: a 19 mm ring round the 26 mm hole (0.8 mm in print)
        pts = [(e * (L / 2 - 80), -re), (xb, -re)]
        pts += [(xb + e * re * math.cos(math.radians(a)), re * math.sin(math.radians(a)))
                for a in range(-90, 91, 15)]
        pts += [(e * (L / 2 - 80), re)]
        pts = [(px, s * YC + py) for px, py in pts]
        pe = m.t(40)
        eyes.append(cut(prism(pts, "z", Z_PULL - pe / 2, Z_PULL + pe / 2),
                        cyl(26, (xb, s * YC, Z_PULL - 50), (xb, s * YC, Z_PULL + 50))))
    m.add(f"stacking_sockets_{side}", PAINT, socks)
    m.add(f"pulling_eyes_{side}", PAINT, eyes)

    # markings on the outer face: fleet number stencil and a tabulated-data decal
    ef = max(2.0, 0.3 * m.scale) if m.print_mode else 2.0
    xdir = (-1, 0, 0) if s > 0 else (1, 0, 0)
    words = [text("TS-0817", 165, ef, (s * 508.0, s * (YO - 1), 1720), xdir, (0, s, 0)),
             text("8 x 20", 140, ef, (s * 508.0, s * (YO - 1), 1420), xdir, (0, s, 0))]
    m.add(f"stencil_{side}", BLACK, [w for w in words if w is not None])
    xd0, xd1 = s * 1150.0, s * 1600.0
    if m.print_mode:
        # the decal's lettering is far below one print layer: print it as a raised blank plate
        m.add(f"data_decal_{side}", DECAL, box(xd0, xd1, s * (YO - 1), s * (YO - 1 + ef), 1450, 1960))
    else:
        m.add(f"data_decal_{side}", DECAL, box(xd0, xd1, s * (YO - 1), s * (YO + 3), 1450, 1960))
        m.add(f"data_decal_header_{side}", RED,
              box(xd0 + s * 20, xd1 - s * 20, s * (YO + 2), s * (YO + 5), 1860, 1940))
        m.add(f"data_decal_text_{side}", BLACK,
              [box(xd0 + s * 30, xd1 - s * (30 + 80 * (k % 3)), s * (YO + 2), s * (YO + 5), z, z + 18)
               for k, z in enumerate(range(1490, 1830, 42))])


# ---------------------------------------------------------------- spreaders

def spreaders(m):
    pipes, collars, pins, clips = [], [], [], []
    yc0 = YI - 20                   # collar starts in the backing plate
    yc1 = YI - 25 - COL_LEN         # collar inner end
    for e in (1, -1):
        x = e * X_SPR
        for z in Z_SPR:
            pipes.append(cyl(R_PIPE, (x, -(yc1 + 15), z), (x, yc1 + 15, z)))
            for s in (1, -1):
                collars.append(cyl(R_COL, (x, s * yc0, z), (x, s * yc1, z)))
                collars.append(cyl(R_COL + 7, (x, s * yc1, z), (x, s * (yc1 + 28), z)))     # end ring
                collars.append(cyl(R_COL + 7, (x, s * (yc0 - 10), z), (x, s * (yc0 - 38), z)))
                yp = s * (YI - 25 - COL_LEN / 2)
                rp = m.r(22)
                pins.append(cyl(rp, (x, yp, z - R_COL - 60), (x, yp, z + R_COL + 8)))
                pins.append(cyl(38, (x, yp, z + R_COL - 4), (x, yp, z + R_COL + 20)))      # head
                pins.append(cyl(m.r(11), (x - 55, yp, z + R_COL + 32), (x + 55, yp, z + R_COL + 32)))  # T handle
                pins.append(cyl(m.r(10), (x, yp, z + R_COL + 15), (x, yp, z + R_COL + 40)))
                clips.append(cyl(m.r(7), (x - 40, yp, z - R_COL - 35), (x + 40, yp, z - R_COL - 35)))
    m.add("spreader_pipes", GALV, pipes)
    m.add("spreader_collars", GALV, collars)
    m.add("spreader_pins", STEEL, pins)
    m.add("pin_keepers", RED, clips)
