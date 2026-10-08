"""Excavator bucket key holder: a digging bucket hung on the wall by its back,
mouth facing out, with a row of teeth along the cutting edge to hang keys on.
The bucket itself is a tray for loose keys, a pen or a phone.

Side profile in (z out from the wall, y up), extruded across x. The heel is
rounded like a real bucket, the side plates follow the straight side-cutter
line from the lip to the cutting edge, and the linkage ears stand up on the
back. Prints on its back with no supports. Two filaments: bucket in yellow,
teeth in black.
"""
import os
import numpy as np, trimesh
from trimesh.creation import box, cylinder
from common import hull, u, d, x_, side_prism, keyhole, write_3mf, report, preview

HERE = os.path.dirname(os.path.abspath(__file__))
W = 150                     # width across the cutting edge
H = 80                      # height on the wall
DEPTH = 58                  # cutting edge, out from the wall
LIP = 14                    # top lip, out from the wall
HEEL_R = 26                 # radius of the rounded heel
EDGE_T = 7                  # cutting edge thickness
T = 5                       # shell and side plate thickness
N_TEETH = 5
TOOTH_L, TOOTH_TILT = 38, 15    # teeth length and how far they point up, degrees
EAR_X, EAR_H, EAR_T = 26, 16, 6 # linkage ears: spacing either side, height above, thickness
KEYHOLE_X, KEYHOLE_Y = (-35, 35), 46

def arc(cz, cy, r, a0, a1, n=24):
    return [(cz + r*np.cos(a), cy + r*np.sin(a)) for a in np.linspace(np.radians(a0), np.radians(a1), n)]

# outer side profile: heel arc, floor out to the cutting edge, mouth line back to the lip
# below 45 degrees the heel would overhang the bed, so it runs flat at 45 there
c45 = HEEL_R*(1 - np.cos(np.radians(45)))
outer = [(0, 2*c45)] + arc(HEEL_R, HEEL_R, HEEL_R, 225, 270) + [(DEPTH, 0), (DEPTH, EDGE_T), (LIP, H), (0, H)]
shell = side_prism(outer, -W/2, W/2)

# cavity: the same heel moved in by T, open right through the mouth
r_in = HEEL_R - T
slope = (EDGE_T - 0) / (DEPTH - HEEL_R)          # how the floor rises toward the edge
def floor_y(z): return T + slope*(z - HEEL_R)
far = DEPTH + 40
cavity = arc(HEEL_R, HEEL_R, r_in, 180, 270) + [(far, floor_y(far)), (far, H - T), (T, H - T)]
bucket = d(shell, side_prism(cavity, -W/2 + T, W/2 - T))

# linkage ears with pin holes, standing up off the back
ears = []
for s in (-1, 1):
    for x in (s*EAR_X - EAR_T/2 - 4, s*EAR_X + EAR_T/2 + 4):
        ear = side_prism(arc(11, H, 11, -90, 90) + [(0, H - 6), (22, H - 6), (0, H)], x - EAR_T/2, x + EAR_T/2)
        ears.append(ear)
    pin = cylinder(radius=3.2, height=8 + 2*EAR_T, sections=32)   # spans the ear pair only
    pin.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, (0, 1, 0)))
    pin.apply_translation((s*EAR_X, H + 2, 11))
    ears.append(pin)                                  # linkage pin, part of the bucket
bucket = u([bucket] + ears)
bucket = d(bucket, *sum((keyhole(x, KEYHOLE_Y) for x in KEYHOLE_X), []))

# --- Teeth: adapter + tip, along the cutting edge, tilted up -----------------
def tooth(x):
    yb, yt = 0.5, EDGE_T - 0.5                       # sit within the edge thickness
    base = [(x + sx*7, y, DEPTH - 8) for sx in (-1, 1) for y in (yb, yt)]
    shoulder = [(x + sx*6.5, y, DEPTH + 10) for sx in (-1, 1) for y in (yb + 0.3, yt - 0.3)]
    adapter = hull(base + shoulder)
    point = [(x + sx*2.5, y, DEPTH + TOOTH_L) for sx in (-1, 1) for y in (yt - 2.5, yt - 0.5)]
    tip = hull(shoulder + point)
    t = u([adapter, tip])
    t.apply_transform(trimesh.transformations.rotation_matrix(np.radians(-TOOTH_TILT), (1, 0, 0), (x, EDGE_T/2, DEPTH)))
    return t

pitch = (W - 2*T - 16) / (N_TEETH - 1)
xs = (np.arange(N_TEETH) - (N_TEETH - 1)/2) * pitch
teeth = d(u(tooth(x) for x in xs), bucket)
# tilting the teeth drops their bases below the floor: trim them flush with it
teeth = x_(teeth, box(bounds=((-500, 0, 0), (500, 500, 500))))

parts = [("bucket", (0xF2, 0xB7, 0x05), bucket), ("teeth", (0x22, 0x22, 0x22), teeth)]
write_3mf(parts, HERE + "/bucket.3mf", "excavator bucket key holder")
report(parts)
preview(parts, HERE + "/bucket.png", azim=-55, elev=25)
