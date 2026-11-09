from sect import *
parts, joints, info = cb.make_capybara()
head, orange, b1 = parts['head'], parts['orange'], parts['body 1']
rest = cb.union(p for n, p in parts.items() if n not in ('head', 'orange'))
P = [cb.NECK_X, 0, cb.NECK_Z]
print('seat', info['seat'], 'orange centre z', info['orange_z'], 'head bbox', np.round(head.bounding_box(),2))
# nod stops
for s, nm in ((1, 'positive'), (-1, 'negative')):
    for a in np.arange(0.5, 60, 0.5):
        hp = cb.turn(head, 'y', P, s*a)
        o = hp ^ rest
        if o.volume() > 1e-4:
            nose = np.array(cb.turn(cb.ball(0.1, 0.1, 0, 5), 'y', P, s*a).bounding_box())
            print('nod %s: first contact at %.1f deg (nose tip then at z=%.1f)' % (nm, a, (nose[2]+nose[5])/2))
            o2 = cb.turn(head, 'y', P, s*(a+1.5)) ^ rest
            for pc in o2.decompose():
                bb = np.array(pc.bounding_box()); cen = (bb[:3]+bb[3:])/2
                print('     overlap 1.5 deg further: vol %.3f centre (%.2f %.2f %.2f), %.2f mm from the nod axis, bbox %s' % (pc.volume(), *cen, np.hypot(cen[0]-P[0], cen[2]-P[2]), np.round(bb,2)))
            break
# the tab: sections across it (planes x = const)
tab = head ^ cb.box(12.0, 30, -cb.TAB_W/2-0.01, cb.TAB_W/2+0.01, -1, 12)
print('tab x-sections (y,z coords):')
for x in np.arange(13.0, 27.9, 0.5):
    A, c, Ixx, Iyy, ext = poly_props(xslice(head, x))
    At, ct, Ixt, Iyt, et = poly_props(xslice(tab, x))
    if At > 0:
        print('   x=%.1f whole head %.2f mm2 | tab-width strip %.2f mm2, y %.2f..%.2f z %.2f..%.2f, Z about z (yaw pry) %.2f, Z about y (nod pry) %.2f mm3' % (x, A, At, *et, Iyt/max(et[1]-ct[0], ct[0]-et[0]), Ixt/max(et[3]-ct[1], ct[1]-et[2])))
# where does the head stop and only the tab continue
for x in np.arange(13.0, 20, 0.25):
    A = xslice(head, x).area(); At = xslice(tab, x).area()
    if abs(A-At) < 0.05: print('behind x=%.2f the head is only the tab (%.2f mm2)' % (x, At)); break
# horizontal slices of tab eye at the axis height
for z in (cb.NECK_Z-0.1, cb.NECK_Z+0.1, cb.NECK_Z+1.0, cb.NECK_Z+2.0, cb.NECK_Z+2.6, cb.NECK_Z+3.0):
    A, c, Ixx, Iyy, ext = poly_props(zslice(tab ^ cb.box(cb.NECK_X-3.2, 40, -5, 5, 0, 20), z))
    print('   tab eye, horizontal slice z=%.2f from x=NECK_X-3.2 back: area %.2f, x %.2f..%.2f' % (z, A, ext[0], ext[1]))
# ligament behind / above the pins: radial half-plane sections from the nod axis
eye = tab
for ang in (0, -45, 45, 90, 135, 180):
    t = eye.translate([-P[0], 0, -P[2]]).rotate([0, ang, 0])   # bring the direction onto +x
    sec = yslice(t ^ cb.box(0, 20, -5, 5, -0.01, 0.01).translate([0,0,0]), 0.0) if False else None
    # section by the plane z=0 (after rotation), x>0
    cs = zslice(t ^ cb.box(0.0, 20, -5, 5, -1, 1), 0.0)
    A, c, Ixx, Iyy, ext = poly_props(cs)
    print('   tab material on the half-plane from the nod axis at %4d deg (0 = straight back, +90 = up): %.2f mm2, reaches %.2f mm from the axis' % (ang, A, ext[1]))
# pins on the body
for s in (1,):
    pin = b1 ^ cb.box(cb.NECK_X-4, cb.NECK_X+4, 0.5, cb.TAB_W/2+cb.TAB_GAP+0.001, cb.NECK_Z-4, cb.NECK_Z+4)
    print('nod pin (left) bbox', np.round(pin.bounding_box(),2), 'volume %.2f' % pin.volume())
    for y in (cb.TAB_W/2+cb.TAB_GAP-0.01, cb.TAB_W/2, cb.TAB_W/2-0.5, cb.TAB_W/2-0.99):
        print('   pin section at y=%.2f: %.2f mm2' % (y, yslice(pin, y).area()))
# play of the head
for nm, v in (('forward', [-1,0,0]), ('back', [1,0,0]), ('left', [0,1,0]), ('up', [0,0,1]), ('down', [0,0,-1])):
    for d in np.arange(0, 3, 0.05):
        if (head.translate([d*c for c in v]) ^ rest).volume() > 1e-4:
            print('head pulled %s touches after %.2f mm; contact %s' % (nm, d, np.round((head.translate([(d+0.05)*c for c in v]) ^ rest).bounding_box(),2))); break
    else: print('head pulled %s: free for 3 mm!' % nm)
for ax in 'xz':
    for s in (1,-1):
        for a in np.arange(0, 40, 0.25):
            r = [s*a,0,0] if ax=='x' else [0,0,s*a]
            hp = head.translate([-P[0],0,-P[2]]).rotate(r).translate(P)
            if (hp ^ rest).volume() > 1e-4:
                r2 = [s*(a+0.5),0,0] if ax=='x' else [0,0,s*(a+0.5)]
                o = head.translate([-P[0],0,-P[2]]).rotate(r2).translate(P) ^ rest
                print('head twisted about %s (%+d): touches at %.2f deg; contacts %s' % (ax, s, a, '; '.join(str(np.round(pc.bounding_box(),1)) for pc in o.decompose()))); break
