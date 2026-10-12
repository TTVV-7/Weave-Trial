"""Simplified Genie GTH-1056 telehandler with a working boom, as STEP for Shapr3D.

Dimensions from the Genie GTH-1056 spec sheet, part positions scaled from its
side-view drawing. Units mm, Z up, forks toward +X, cab on the left (+Y).

The boom is posed by two numbers:
  angle   boom raised about its pivot pin, 0 (stowed) to 65 degrees
  extend  telescope extension, 0 to 10500 mm, shared by the three inner sections
          (4-section boom, like the real one; full reach is about 56 ft lift height)
The lift cylinder stretches between its frame and boom pins, and the carriage
counter-rotates about its pin so the forks stay level, the way the machine's
self-levelling does.

In each STEP the moving parts sit in one sub-assembly, "boom", so in Shapr3D
they can be selected together and rotated about the pivot pin (the axis
through PIVOT, parallel to Y) to pose it by hand.

    python gth1056.py OUT_DIR                  # the standard set of poses (in step/)
    python gth1056.py OUT_DIR --angle 40 --extend 2500
"""
import argparse, math, os
import cadquery as cq

def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane().box(x1 - x0, y1 - y0, z1 - z0).translate(((x0 + x1)/2, (y0 + y1)/2, (z0 + z1)/2))
def side(pts, y0, y1):
    return cq.Workplane("XZ").polyline(pts).close().extrude(-(y1 - y0)).translate((0, y0, 0))
def rod(r, p0, p1):
    d = cq.Vector(*p1) - cq.Vector(*p0)
    return cq.Workplane().add(cq.Solid.makeCylinder(r, d.Length, cq.Vector(*p0), d.normalized()))

BL = cq.Color(0.0, 0.42, 0.76); DK = cq.Color(0.12, 0.12, 0.13); TY = cq.Color(0.07, 0.07, 0.07)
RM = cq.Color(0.82, 0.83, 0.84); GL = cq.Color(0.25, 0.35, 0.42, 0.45); CH = cq.Color(0.75, 0.76, 0.78)
WB = 3500; XR, XF = 1310, 1310 + WB         # rear / front axle positions (11 ft 6 in wheelbase)
TR, TW, TY0 = 665, 400, 1095                # tyre radius (400/75-28), width, centre offset -> 8 ft 6 in wide

PIVOT = (380, 1850)                         # boom pivot pin, x and z
CARR_PIN = (6760, 1150)                     # carriage pivot on the boom head, stowed
LIFT_BASE = (1800, 1080)                    # lift cylinder pin on the frame
LIFT_ROD = (4000, 1800)                     # lift cylinder pin under the boom, stowed
MAX_ANGLE, MAX_EXTEND = 65, 10500
# boom centre line, used to slide the telescopic sections out
AX0, AX1 = (150, 2275), (4750, 1975)
_L = math.dist(AX0, AX1); AXIS = ((AX1[0] - AX0[0])/_L, (AX1[1] - AX0[1])/_L)

def zc(x): return AX0[1] + (x - AX0[0])*AXIS[1]/AXIS[0]      # centre line height at x
def section(x0, x1, h):
    """A boom section of height h along the centre line, from x0 to x1."""
    return [(x0, zc(x0) - h/2), (x0, zc(x0) + h/2), (x1, zc(x1) + h/2), (x1, zc(x1) - h/2)]

def chassis():
    p = []
    for nm, xa in (("rear", XR), ("front", XF)):
        p.append((f"{nm}_axle", rod(110, (xa, -TY0, TR), (xa, TY0, TR)), DK))
        p.append((f"{nm}_diff", box(xa - 260, xa + 260, -260, 260, TR - 230, TR + 230), DK))
        for s in (1, -1):
            y0 = TY0 - TW/2 if s > 0 else -TY0 - TW/2
            p.append((f"{nm}_tyre_{s}", rod(TR, (xa, y0, TR), (xa, y0 + TW, TR)), TY))
            p.append((f"{nm}_rim_{s}", rod(355, (xa, y0 - 2, TR), (xa, y0 + TW + 2, TR)), RM))
            p.append((f"{nm}_hub_{s}", rod(140, (xa, y0 - 5, TR), (xa, y0 + TW + 5, TR)), DK))
    # chassis frame (15 in ground clearance), rear counterweight, front frame / stabilizers
    p.append(("frame", box(450, 6050, -470, 470, 380, 1080), BL))
    p.append(("counterweight", box(0, 700, -1000, 1000, 480, 1420).edges("|Y").fillet(120), BL))
    p.append(("rear_light_bar", box(-15, 0, -800, 800, 1150, 1230), DK))
    p.append(("front_frame", box(5600, 6150, -650, 650, 450, 1500), BL))
    for s in (1, -1):
        p.append((f"stabilizer_arm_{s}", side([(5650, 1250), (5950, 1250), (5900, 320), (5700, 320)], *sorted((s*700, s*820))), BL))
        p.append((f"stabilizer_pad_{s}", box(5600, 6000, *sorted((s*600, s*920)), 280, 320), DK))
        p.append((f"stabilizer_cyl_{s}", rod(55, (5780, s*760, 1450), (5780, s*760, 700)), CH))
    # engine compartment on the right side (-Y), tanks and step under the cab (+Y)
    p.append(("engine_hood", box(800, 2700, -1220, -480, 700, 1650).edges("|X and >Z").fillet(120), BL))
    p.append(("engine_grille", box(1100, 2400, -1225, -1220, 1000, 1500), DK))
    p.append(("tank_left", box(2450, 3950, 480, 1150, 420, 820), DK))
    p.append(("cab_step", box(2600, 2900, 1150, 1260, 420, 460), DK))
    # operator cab (left side): ROPS frame, roof, glazing, seat
    CX0, CX1, CY0, CY1, CZ0, CZ1 = 2500, 4150, 320, 1240, 820, 2380
    for k, (x, y) in enumerate([(CX0, CY0), (CX0, CY1), (CX1, CY0), (CX1, CY1)]):
        p.append((f"cab_post_{k}", box(x - 45 if x == CX1 else x, x if x == CX1 else x + 45,
                                       y - 45 if y == CY1 else y, y if y == CY1 else y + 45, CZ0, CZ1), DK))
    p.append(("cab_roof", box(CX0 - 40, CX1 + 40, CY0 - 30, CY1 + 30, CZ1, CZ1 + 70).edges("|Z").fillet(60), DK))
    p.append(("cab_floor", box(CX0, CX1, CY0, CY1, CZ0 - 60, CZ0), DK))
    p.append(("cab_glass_front", box(CX1 - 40, CX1 - 25, CY0 + 45, CY1 - 45, CZ0 + 300, CZ1 - 40), GL))
    p.append(("cab_glass_rear", box(CX0 + 25, CX0 + 40, CY0 + 45, CY1 - 45, CZ0 + 300, CZ1 - 40), GL))
    p.append(("cab_glass_door", box(CX0 + 45, CX1 - 45, CY1 - 25, CY1 - 10, CZ0 + 80, CZ1 - 40), GL))
    p.append(("cab_glass_inner", box(CX0 + 45, CX1 - 45, CY0 + 10, CY0 + 25, CZ0 + 700, CZ1 - 40), GL))
    p.append(("seat", box(2800, 3350, 560, 1000, 1050, 1250), DK))
    p.append(("seat_back", box(2700, 2820, 560, 1000, 1250, 1800), DK))
    p.append(("dash_steering", box(3700, 3950, 620, 940, 1050, 1500), DK))
    # boom pivot towers and pin stay with the chassis
    p.append(("boom_pivot_towers", side([(150, 1080), (800, 1080), (650, 2050), (250, 2050)], -330, 330), BL))
    p.append(("boom_pivot_pin", rod(70, (PIVOT[0], -360, PIVOT[1]), (PIVOT[0], 360, PIVOT[1])), CH))
    p.append(("lift_cylinder_base_pin", rod(60, (LIFT_BASE[0], -150, LIFT_BASE[1]), (LIFT_BASE[0], 150, LIFT_BASE[1])), CH))
    return p

def rotate_xz(pt, about, deg):
    """Raise a point (x, z) about a pin, counter-clockwise seen from the cab side."""
    a = math.radians(deg); dx, dz = pt[0] - about[0], pt[1] - about[1]
    return (about[0] + dx*math.cos(a) - dz*math.sin(a), about[1] + dx*math.sin(a) + dz*math.cos(a))

def rot(w, about, deg):
    # +Y axis: a positive angle tips +X down, so negate to raise the front
    return w.rotate((about[0], 0, about[1]), (about[0], 1, about[1]), -deg)

def boom(angle, extend):
    """The moving parts, posed. Returns parts and the stowed-to-posed transform for points."""
    e1, e2, e_fly = extend/3, 2*extend/3, extend    # each section slides a third out of the one around it
    def slide(e): return (e*AXIS[0], 0, e*AXIS[1])
    def pose_pt(pt, e):                             # where a boom point ends up
        return rotate_xz((pt[0] + e*AXIS[0], pt[1] + e*AXIS[1]), PIVOT, angle)

    p = []
    # base section, pinned at the back; three sections nest inside it
    p.append(("boom_base", side([(150, 1960), (150, 2590), (4750, 2250), (4750, 1700)], -260, 260), BL, 0, False))
    p.append(("boom_hose_tray", box(800, 4700, -280, -260, 2050, 2350), DK, 0, False))
    p.append(("boom_rod_pin", rod(60, (LIFT_ROD[0], -280, LIFT_ROD[1]), (LIFT_ROD[0], 280, LIFT_ROD[1])), CH, 0, False))
    p.append(("boom_section_2", side(section(500, 5300, 480), -235, 235), BL, e1, False))
    p.append(("boom_section_3", side(section(850, 5800, 420), -210, 210), BL, e2, False))
    p.append(("boom_fly", side(section(1200, 6250, 360), -185, 185), BL, e_fly, False))
    for k, (x, h, w, e) in enumerate(((4750, 520, 270, 0), (5250, 460, 245, e1), (5750, 400, 220, e2))):
        p.append((f"boom_wear_pads_{k + 1}", box(x - 50, x + 50, -w, w, zc(x) - h/2, zc(x) + h/2), DK, e, False))
    p.append(("boom_head", side([(6150, 2120), (6550, 2040), (6800, 1350), (6750, 900), (6450, 950), (6150, 1600)], -260, 260), BL, e_fly, False))
    # carriage and forks (48 in carriage, 2.25 x 4 in forks, 72 in tines): these level
    p.append(("carriage_pin", rod(55, (CARR_PIN[0], -300, CARR_PIN[1]), (CARR_PIN[0], 300, CARR_PIN[1])), CH, e_fly, True))
    p.append(("carriage_frame", box(6780, 6880, -610, 610, 180, 1250), DK, e_fly, True))
    p.append(("carriage_backrest", box(6780, 6840, -610, 610, 1250, 1650), DK, e_fly, True))
    for s in (1, -1):
        y = s*420
        p.append((f"fork_shank_{s}", box(6880, 6937, y - 51, y + 51, 60, 1150), DK, e_fly, True))
        p.append((f"fork_tine_{s}", box(6880, 6880 + 1830, y - 51, y + 51, 60, 117), DK, e_fly, True))

    out = []
    pin = pose_pt(CARR_PIN, e_fly)
    for name, w, col, e, level in p:
        w = rot(w.translate(slide(e)), PIVOT, angle)
        if level:                                    # undo the boom angle about the carriage pin
            w = rot(w, pin, -angle)
        out.append((name, w, col))

    # tilt cylinder: from the head to the carriage, both ends follow their parts
    a = pose_pt((6200, 1750), e_fly)
    b = rotate_xz(pose_pt((6650, 900), e_fly), pin, -angle)
    out.append(("tilt_cylinder", rod(60, (a[0], 0, a[1]), (b[0], 0, b[1])), CH))
    return out

def lift_cylinder(angle):
    """Barrel on the frame pin, rod into the boom pin, stretched to fit the pose."""
    r = rotate_xz(LIFT_ROD, PIVOT, angle)
    stowed = math.dist(LIFT_BASE, LIFT_ROD)
    barrel = stowed - 150                        # rod is just showing when the boom is down
    ux, uz = (r[0] - LIFT_BASE[0])/math.dist(LIFT_BASE, r), (r[1] - LIFT_BASE[1])/math.dist(LIFT_BASE, r)
    end = (LIFT_BASE[0] + ux*barrel, LIFT_BASE[1] + uz*barrel)
    return [("lift_cylinder_barrel", rod(110, (LIFT_BASE[0], 0, LIFT_BASE[1]), (end[0], 0, end[1])), BL),
            ("lift_cylinder_rod", rod(65, (end[0], 0, end[1]), (r[0], 0, r[1])), CH)]

def build(angle=0.0, extend=0.0):
    if not 0 <= angle <= MAX_ANGLE: raise ValueError(f"angle must be 0 to {MAX_ANGLE} degrees")
    if not 0 <= extend <= MAX_EXTEND: raise ValueError(f"extend must be 0 to {MAX_EXTEND} mm")
    asm = cq.Assembly(name="Genie_GTH-1056")
    fixed = cq.Assembly(name="chassis")
    for n, w, c in chassis(): fixed.add(w, name=n, color=c)
    moving = cq.Assembly(name="boom")
    for n, w, c in boom(angle, extend): moving.add(w, name=n, color=c)
    lift = cq.Assembly(name="lift_cylinder")
    for n, w, c in lift_cylinder(angle): lift.add(w, name=n, color=c)
    asm.add(fixed); asm.add(moving); asm.add(lift)
    return asm

POSES = {"stowed": (0, 0), "raised_30deg": (30, 0), "raised_45deg_extended_5m": (45, 5000),
         "max_65deg_extended_10m": (65, 10500)}

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out"); ap.add_argument("--angle", type=float); ap.add_argument("--extend", type=float, default=0)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    poses = {f"angle{a.angle:g}_extend{a.extend:g}": (a.angle, a.extend)} if a.angle is not None else POSES
    for tag, (ang, ext) in poses.items():
        asm = build(ang, ext)
        path = os.path.join(a.out, f"Genie_GTH-1056_{tag}.step")
        asm.export(path)
        bb = asm.toCompound().BoundingBox()
        print(f"{tag}: {path}  top of forks {round(bb.zmax/304.8, 1)} ft, reach x {round(bb.xmax/304.8, 1)} ft")
