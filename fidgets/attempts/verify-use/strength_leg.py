from sect import *
parts, joints, info = cb.make_capybara()
leg = parts['front left leg']; x0 = cb.LEG_X[0]
print('LEG bbox', np.round(leg.bounding_box(),2), 'volume', round(leg.volume(),1))
print(' z    area   y-extent     Zx (bending the foot outwards, about the x axis) ')
rows=[]
for z in np.arange(0.1, 10.8, 0.2):
    A, c, Ixx, Iyy, ext = poly_props(zslice(leg, z))
    # slice coordinates (x,y): Ixx = int (y-cy)^2 dA -> bending about the x axis
    cmax = max(ext[3]-c[1], c[1]-ext[2])
    rows.append((z, A, ext, Ixx/cmax if cmax>0 else 0))
for z, A, ext, Z in rows:
    print('%5.1f %6.2f  x %.2f..%.2f y %.2f..%.2f  Z=%.2f mm3' % (z, A, *ext, Z))
r = min(rows[10:], key=lambda r: r[3]); print('weakest in bending above z=2:', r)
r = min(rows[10:45], key=lambda r: r[1]); print('least area z 2..9:', r)
# the pin
b1 = parts['body 1']
pinbox = cb.box(x0-4, x0+4, cb.FLANK-0.01, cb.FLANK+3, 2, 11)
pin = b1 ^ pinbox
print('PIN bbox', np.round(pin.bounding_box(),2))
for y in np.arange(cb.FLANK+0.0, cb.FLANK+1.61, 0.1):
    A, c, Ixx, Iyy, ext = poly_props(yslice(pin, y+1e-4))
    # coords (z, x): Iyy = int (z-cz)^2 -> bending about x axis (foot outward); Ixx = int (x-cx)^2 -> bending about z (leg pushed fore/aft... no, twist about z)
    cz = max(ext[1]-c[0], c[0]-ext[0]); cxm = max(ext[3]-c[1], c[1]-ext[2])
    print('pin at y=FLANK+%.1f: area %.2f mm2, z %.2f..%.2f, x-width %.2f, Z(about x) %.2f mm3, Z(about z) %.2f mm3' % (y-cb.FLANK, A, ext[0], ext[1], ext[3]-ext[2], Iyy/cz, Ixx/cxm))
# retention overlap
g = cb.CLEAR*np.sqrt(2)
hole_r = cb.LEG_NECK/2 + g + cb.LEG_GAP
pin_r = cb.LEG_NECK/2 + cb.LEG_GAP + cb.LEG_D
print('leg hole radius at its inner face %.3f, pin head radius %.3f, radial catch %.3f' % (hole_r, pin_r, pin_r-hole_r))
# slop: how far can the leg be pulled out (y) before it touches, and how far it can tilt
for d in np.arange(0.0, 1.01, 0.05):
    if (leg.translate([0, d, 0]) ^ b1).volume() > 1e-4:
        print('leg pulled outwards touches at %.2f mm' % d); break
for d in np.arange(0.0, 1.01, 0.05):
    if (leg.translate([0, -d, 0]) ^ b1).volume() > 1e-4:
        print('leg pushed inwards touches at %.2f mm' % d); break
for a in np.arange(0, 30, 0.5):
    t = cb.turn(leg, 'y', [0,0,0], 0)  # noop
    # tilt about the x axis through the pin centre (foot outwards)
    p = np.array([x0, cb.FLANK+cb.LEG_GAP, cb.LEG_Z])
    for sgn in (1,):
        tl = leg.translate(list(-p)).rotate([-a, 0, 0]).translate(list(p))
        if (tl ^ b1).volume() > 1e-4:
            print('leg foot pried outwards (rotation about x through the pin) touches at %.1f deg' % a); break
    else: continue
    break
# contact area between pin cone and the leg socket cone if pulled out: overlap test
out = leg.translate([0, 0.6, 0]) ^ b1
print('overlap when the leg is pulled 0.6 out: volume %.3f, bbox %s' % (out.volume(), np.round(out.bounding_box(),2)))
