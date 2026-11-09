from sect import *
parts, joints, info = cb.make_capybara()
head, orange, b4 = parts['head'], parts['orange'], parts['body 4']
rest = cb.union(p for n, p in parts.items() if n != 'orange')
print('ORANGE bbox', np.round(orange.bounding_box(),2), 'seat z %.2f centre z %.2f' % (info['seat'], info['orange_z']))
for z in (0.05, 0.3, 0.6, 0.9, 1.2, 2, 6, 12.0, 12.19, 12.3, 12.6, 13.0, 13.5, 14, 16.35):
    A, c, Ixx, Iyy, ext = poly_props(zslice(orange, z))
    d = ext[1]-ext[0]
    print('   z=%.2f  dia %.2f  area %.2f mm2  Z %.2f mm3 (bending)  polar Zp %.2f mm3 (twist)' % (z, d, A, Ixx/(d/2), (Ixx+Iyy)/(d/2)))
bb = orange.bounding_box(); print('orange widest %.2f mm, top z %.2f; ball diameter by design %.1f' % (bb[3]-bb[0], bb[5], 2*cb.ORANGE_R))
# bore
for z in (0.05, 0.3, 0.6, 0.9, 1.2, 2, 6, 11.5):
    hs = zslice(head, z)
    holes = [p for p in hs.to_polygons() if np.hypot(*(np.asarray(p).mean(0) - [cb.ORANGE_X, 0])) < 0.5]
    r = max(np.hypot(*(np.asarray(holes[0]) - [cb.ORANGE_X, 0]).T)) if holes else float('nan')
    print('   bore radius in the head at z=%.2f: %.2f' % (z, r))
for nm, v in (('up', [0,0,1]), ('down', [0,0,-1]), ('sideways', [0,1,0]), ('forward', [-1,0,0])):
    for d in np.arange(0, 4, 0.05):
        if (orange.translate([d*c for c in v]) ^ rest).volume() > 1e-4:
            print('orange pushed %s touches after %.2f mm; contact %s' % (nm, d, np.round((orange.translate([(d+0.05)*c for c in v]) ^ rest).bounding_box(),2))); break
# tilt of the orange about the seat
for piv in ([cb.ORANGE_X, 0, info['seat']], [cb.ORANGE_X, 0, 6.0]):
    for a in np.arange(0, 30, 0.25):
        t = orange.translate([-piv[0], 0, -piv[2]]).rotate([a, 0, 0]).translate(piv)
        if (t ^ rest).volume() > 1e-4:
            o = orange.translate([-piv[0], 0, -piv[2]]).rotate([a+0.5, 0, 0]).translate(piv) ^ rest
            print('orange tipped sideways about z=%.1f touches at %.2f deg: contacts %s' % (piv[2], a, '; '.join(str(np.round(pc.bounding_box(),1)) for pc in o.decompose()))); break
# foot catch
proj_foot = zslice(orange, 0.02)
print('foot area on the bed %.2f; bore minimum radius %.2f -> ring of foot caught under the bore: %.2f mm2, catch %.2f mm radially' % (proj_foot.area(), cb.SHAFT_R+cb.SHAFT_GAP, proj_foot.area() - np.pi*(cb.SHAFT_R+cb.SHAFT_GAP)**2, cb.SHAFT_FOOT-(cb.SHAFT_R+cb.SHAFT_GAP)))
# EARS
print('EARS: horizontal slices of the head at the left ear (y>3.5, x 12.5..17.5)')
earbox = cb.box(12.0, 17.5, 3.4, 8, 0, 20)
for z in np.arange(11.0, 15.4, 0.4):
    cs = zslice(head ^ earbox, z)
    A, c, Ixx, Iyy, ext = poly_props(cs)
    full = zslice(head, z).area()
    print('   z=%.1f area in ear box %.2f (x %.2f..%.2f y %.2f..%.2f) pieces %d ; whole head slice %.1f' % (z, A, *ext, len(cs.decompose()), full))
# is the ear a separate island on the head slice (i.e. standing proud) and its smallest neck
for z in np.arange(12.0, 15.4, 0.2):
    pcs = zslice(head, z).decompose()
    print('   z=%.1f head slice pieces: %s' % (z, ', '.join('%.2f' % p.area() for p in sorted(pcs, key=lambda p: -p.area()))))
# KEYRING LOOP
print('LOOP: horizontal slices of body 4 above the back')
loopbox = cb.box(cb.KEYRING_X-5, cb.KEYRING_X+5, -1.3, 1.3, 13, 21)
for z in np.arange(14.3, 19.7, 0.3):
    cs = zslice(b4, z)
    A, c, Ixx, Iyy, ext = poly_props(cs)
    cl = zslice(b4 ^ loopbox, z)
    Al, cc, Ixl, Iyl, el = poly_props(cl)
    print('   z=%.1f whole slice %.2f mm2 | within the loop thickness: %.2f mm2 in %d piece(s), x %.2f..%.2f y %.2f..%.2f, Z sideways %.2f mm3' % (z, A, Al, len(cl.decompose()), *el, Ixl/1.2))
# section through the top of the loop (plane x = KEYRING_X), above the hole
A, c, Ixx, Iyy, ext = poly_props(xslice(b4 ^ cb.box(0,100,-5,5,cb.KEYRING_Z+0.5,30), cb.KEYRING_X))
print('loop crown section at x=%.1f: area %.2f mm2, y %.2f..%.2f z %.2f..%.2f' % (cb.KEYRING_X, A, *ext))
for dx in (-2.5, -1.7, 1.7, 2.5):
    A, c, Ixx, Iyy, ext = poly_props(zslice(b4 ^ cb.box(cb.KEYRING_X+min(dx,dx*3), cb.KEYRING_X+max(dx,dx*3), -5, 5, 0, 30), cb.KEYRING_Z))
print('hole: width at centre height', end=' ')
cs = yslice(b4 ^ cb.box(cb.KEYRING_X-6, cb.KEYRING_X+6, -5, 5, 12, 21), 0.0)
for p in cs.to_polygons():
    p = np.asarray(p); print('contour z %.2f..%.2f x %.2f..%.2f' % (p[:,0].min(), p[:,0].max(), p[:,1].min(), p[:,1].max()), end='; ')
print()
back = mk.to_mesh(b4)
for x in (cb.KEYRING_X-4.5, cb.KEYRING_X+4.5, cb.KEYRING_X):
    loc, idx, tri = back.ray.intersects_location([[x, 1.5, 30]], [[0,0,-1.0]])
    print('top of the back beside the loop at x=%.1f, y=1.5: z=%.2f' % (x, loc[:,2].max()))
