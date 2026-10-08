"""Telehandler forks key holder: the fork carriage and load backrest screw to
the wall, and two long fork tines stick out to hang keys on.

The backrest is a tube frame with chamfered top corners and vertical bars,
the carriage two heavy plates between the side posts, and the forks hook over
the top plate the way real ones do. Prints on its back with no supports.
Two filaments: frame in yellow, forks in black.
"""
import numpy as np, trimesh
from trimesh.creation import box, cylinder
import os
from common import hull, u, d, x_, prism, keyhole, write_3mf, report, preview

W = 170                                   # overall width
WEB_T = 5                                 # back web behind the carriage plates
BAR_T = 6                                 # carriage plates stand proud of the web
BARS = ((4, 14), (44, 56))                # y-range of the bottom and top plates
CARRIAGE_H = 60
TUBE, TUBE_T = 7, 9                       # backrest frame tube: width, depth
TOP, CHAMFER = 135, 20                    # top of the backrest and its corner cut
SLATS, SLAT_W, SLAT_T = 7, 4, 6
N_TINES, PITCH = 2, 96
SHANK_W, SHANK_T, SHANK_Y = 12, 7, (4, 58)
BLADE_L, BLADE_T, TAPER_L, TIP_T = 110, 7, 40, 2.5
TILT = 7                                  # degrees of tilt-back, keeps keys on
KEYHOLE_X, KEYHOLE_Y = (-20, 20), 24
HERE = os.path.dirname(os.path.abspath(__file__))

# --- Frame: carriage plates, side posts, backrest ---------------------------
hw = W/2
outer = [(-hw, CARRIAGE_H - 6), (hw, CARRIAGE_H - 6), (hw, TOP - CHAMFER),
         (hw - CHAMFER, TOP), (-hw + CHAMFER, TOP), (-hw, TOP - CHAMFER)]
k = TOP - CHAMFER + hw - TUBE*np.sqrt(2)  # chamfer line x + y = k, moved in by a tube
ih, iy0, iy1 = hw - TUBE, CARRIAGE_H + 1, TOP - TUBE
inner = [(-ih, iy0), (ih, iy0), (ih, k - ih), (k - iy1, iy1), (-(k - iy1), iy1), (-ih, k - ih)]
frame = d(prism(outer, 0, TUBE_T), prism(inner, -1, TUBE_T + 1))
pitch = 2*ih / (SLATS + 1)
slats = x_(u(box(bounds=((-ih + i*pitch - SLAT_W/2, iy0 - 1, 0), (-ih + i*pitch + SLAT_W/2, iy1 + 1, SLAT_T)))
             for i in range(1, SLATS + 1)), prism(inner, -1, TUBE_T + 1))
web = box(bounds=((-hw + 1, 0, 0), (hw - 1, CARRIAGE_H, WEB_T)))
posts = [box(bounds=((s*hw - (s > 0)*TUBE, 0, 0), (s*hw + (s < 0)*TUBE, CARRIAGE_H, TUBE_T))) for s in (-1, 1)]
plates = [box(bounds=((-hw, y0, 0), (hw, y1, WEB_T + BAR_T))) for y0, y1 in BARS]
holes = sum((keyhole(x, KEYHOLE_Y) for x in KEYHOLE_X), [])
carriage = d(u([frame, slats, web] + posts + plates), *holes)

# --- Forks -------------------------------------------------------------------
def tine(x):
    z_face = WEB_T + BAR_T                           # front of the carriage plates
    shank = box(bounds=((x - SHANK_W/2, SHANK_Y[0], WEB_T), (x + SHANK_W/2, SHANK_Y[1], z_face + SHANK_T)))
    cap = cylinder(radius=SHANK_W/2, height=SHANK_T + BAR_T, sections=32)
    cap.apply_translation((x, SHANK_Y[1], WEB_T + (SHANK_T + BAR_T)/2))
    z0, y0 = z_face + SHANK_T, SHANK_Y[0]
    w, c = SHANK_W/2, 2.0                            # half width, tip corner chamfer
    straight_end, tip = z0 + BLADE_L - TAPER_L, z0 + BLADE_L
    blade = hull([(sx*w, y, z) for sx in (-1, 1) for y in (y0, y0 + BLADE_T) for z in (z0 - 3, straight_end)])
    taper = hull([(sx*w, y, straight_end) for sx in (-1, 1) for y in (y0, y0 + BLADE_T)] +
                 [(sx*(w - c), y, tip) for sx in (-1, 1) for y in (y0 + BLADE_T - TIP_T, y0 + BLADE_T)] +
                 [(sx*w, y, tip - c) for sx in (-1, 1) for y in (y0 + BLADE_T - TIP_T, y0 + BLADE_T)])
    blade = u([blade, taper]); blade.apply_translation((x, 0, 0))
    blade.apply_transform(trimesh.transformations.rotation_matrix(np.radians(-TILT), (1, 0, 0), (x, y0, z0)))
    r = 6                                            # inner heel fillet
    fil = box(bounds=((x - w, y0 + BLADE_T - 0.5, z0 - 0.5), (x + w, y0 + BLADE_T + r, z0 + r)))
    fc = cylinder(radius=r, height=SHANK_W + 2, sections=48)
    fc.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, (0, 1, 0)))
    fc.apply_translation((x, y0 + BLADE_T + r, z0 + r))
    return u([shank, cap, blade, d(fil, fc)])

xs = (np.arange(N_TINES) - (N_TINES - 1)/2) * PITCH
forks = x_(d(u(tine(x) for x in xs), carriage), box(bounds=((-500, -500, 0), (500, 500, 500))))

parts = [("frame", (0xF2, 0xB7, 0x05), carriage), ("forks", (0x22, 0x22, 0x22), forks)]
write_3mf(parts, HERE + "/forks.3mf", "telehandler forks key holder")
report(parts)
preview(parts, HERE + "/forks.png")
