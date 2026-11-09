from sect import *
parts, joints, info = cb.make_capybara()
at = cb.AXES[0]
front, rear = parts['body 1'], parts['body 2']
# --- the hook (on the rear segment), isolated: everything of the rear segment inside the ball's radius
cyl = lambda r, h0=-1, h1=30: mf.Manifold.cylinder(h1-h0, r, r, 128).translate([at, 0, h0])
hook = rear ^ cyl(cb.R_BALL + cb.G_SEAM - 0.001)
print('hook (rear segment inside the socket radius): volume %.1f mm3, bbox %s, pieces %d' % (hook.volume(), np.round(hook.bounding_box(),2), len(hook.decompose())))
print('-- hook: section through cylinders about the joint axis (what carries a pull along the body)')
for r in np.arange(5.8, 10.61, 0.2):
    dr = 0.02
    shell = hook ^ (cyl(r+dr) - cyl(r))
    A = shell.volume()/dr
    bb = shell.bounding_box()
    print('   r=%.1f  area %.2f mm2  z %.2f..%.2f  width %.2f' % (r, A, bb[2], bb[5], bb[4]-bb[1]))
print('-- hook: horizontal slices (layer planes)')
for z in np.arange(0.1, 9.0, 0.4):
    A, c, Ixx, Iyy, ext = poly_props(zslice(hook, z))
    if A>0: print('   z=%.1f area %.2f  x %.2f..%.2f (r %.2f..%.2f on the centre line) y %.2f..%.2f' % (z, A, ext[0], ext[1], ext[0]-at, ext[1]-at, ext[2], ext[3]))
# tongue only: below the rim top
tongue = hook ^ cb.box(0, 100, -20, 20, 0, cb.Z_RIM + 0.1)
print('tongue volume %.2f, footprint on bed %.2f mm2' % (tongue.volume(), zslice(hook, 0.05).area()))
A, c, Ixx, Iyy, ext = poly_props(zslice(hook, cb.Z_RIM + 0.15))
print('tongue root slice at z=%.2f: area %.2f, x %.2f..%.2f y %.2f..%.2f; Z about y axis (pull along body) %.2f mm3; Z about x axis (sideways) %.2f mm3' % (cb.Z_RIM+0.15, A, *ext, Iyy/max(ext[1]-c[0], c[0]-ext[0]), Ixx/max(ext[3]-c[1], c[1]-ext[2])))
# --- the rim on the front segment
rimreg = front ^ (cyl(cb.R_BALL+0.001) - cyl(cb.R_RIM-0.001)) ^ cb.wedge(at, cb.HOOK_HALF+cb.SWING+cb.MARGIN) ^ cb.box(0,100,-20,20,0,4)
print('rim across the pocket mouth: volume %.2f bbox %s' % (rimreg.volume(), np.round(rimreg.bounding_box(),2)))
# its cross-section in the plane y=0
A, c, Ixx, Iyy, ext = poly_props(yslice(rimreg, 0.0))
print('rim section at y=0 (z,x coords): area %.2f, z %.2f..%.2f, x %.2f..%.2f, Z for bending in the horizontal plane %.2f mm3' % (A, *ext, Ixx/max(ext[3]-c[1], c[1]-ext[2])))
half = np.radians(cb.HOOK_HALF+cb.SWING+cb.MARGIN)
rm = (cb.R_RIM+cb.R_BALL)/2
print('rim free span: +-%.0f deg at r=%.2f -> arc %.1f mm, chord %.1f mm' % (np.degrees(half), rm, 2*rm*half, 2*rm*np.sin(half)))
# how the rim ends join the ball
for ang in (cb.HOOK_HALF+cb.SWING+cb.MARGIN+0.5, cb.HOOK_HALF+cb.SWING+cb.MARGIN+1.5, 50):
    a = np.radians(ang)
    probe = front ^ cb.box(0,100,-20,20,0,4)
    # section in the radial plane at this angle: rotate so that plane becomes y=0
    pr = cb.turn(probe, 'z', [at,0,0], -ang)
    A, c, Ixx, Iyy, ext = poly_props(yslice(pr ^ cb.box(at+4, at+12, -1, 1, 0, 4), 0.0))
    print('   radial section of the front segment at %.1f deg, r 4..12, z<4: area %.2f  (r %.2f..%.2f)' % (ang, A, ext[2]-at, ext[3]-at))
# --- pull apart: how far before it touches, and the contact patch
for d in np.arange(0, 2, 0.05):
    o = rear.translate([d,0,0]) ^ front
    if o.volume() > 1e-4:
        print('rear segment pulled back touches after %.2f mm' % d)
        o = rear.translate([d+0.1,0,0]) ^ front
        print('   contact after 0.1 more: bbox', np.round(o.bounding_box(),2), 'pieces', len(o.decompose())); break
for d in np.arange(0, 2, 0.05):
    o = rear.translate([-d,0,0]) ^ front
    if o.volume() > 1e-4:
        print('rear segment pushed forward touches after %.2f mm' % d); 
        print('   contact bbox', np.round((rear.translate([-d-0.05,0,0]) ^ front).bounding_box(),2)); break
for name, v in (('lifted', [0,0,1]), ('pushed down', [0,0,-1]), ('sideways', [0,1,0])):
    for d in np.arange(0, 3, 0.05):
        o = rear.translate([d*c for c in v]) ^ front
        if o.volume() > 1e-4:
            print('rear segment %s touches after %.2f mm; contact bbox %s' % (name, d, np.round((rear.translate([(d+0.05)*c for c in v]) ^ front).bounding_box(),2))); break
# --- yaw past the stop
for s in (1,-1):
    for a in np.arange(20, 40, 0.5):
        o = cb.turn(rear, 'z', [at,0,0], s*a) ^ front
        if o.volume() > 1e-4:
            o2 = cb.turn(rear, 'z', [at,0,0], s*(a+1)) ^ front
            print('yaw %+d: first contact at %.1f deg; 1 deg further the overlap has %d piece(s):' % (s, a, len(o2.decompose())))
            for pc in o2.decompose():
                bb = np.array(pc.bounding_box()); cen = (bb[:3]+bb[3:])/2
                print('     vol %.3f centre (%.2f %.2f %.2f) r=%.2f from the axis, z %.2f..%.2f' % (pc.volume(), *cen, np.hypot(cen[0]-at, cen[1]), bb[2], bb[5]))
            break
# --- pitch and roll play about the ball centre
cen = [at, 0, cb.Z_C]
def rot(m, axis, a, c):
    r = {'x':[a,0,0], 'y':[0,a,0]}[axis]
    return m.translate([-c[0],-c[1],-c[2]]).rotate(r).translate(c)
for axis in 'yx':
    for pivz in (0.0, cb.Z_C, 4.0):
        for s in (1,-1):
            c = [at, 0, pivz]
            hit = None
            for a in np.arange(0.25, 40, 0.25):
                o = rot(rear, axis, s*a, c) ^ front
                if o.volume() > 1e-4:
                    hit = a; break
            o2 = rot(rear, axis, s*(hit+0.75), c) ^ front
            desc = '; '.join('(%.1f %.1f %.1f)' % tuple((np.array(pc.bounding_box())[:3]+np.array(pc.bounding_box())[3:])/2) for pc in o2.decompose())
            print('rotation about %s through z=%.1f, sign %+d: free to %.2f deg; contacts at %s' % (axis, pivz, s, hit-0.25, desc))
