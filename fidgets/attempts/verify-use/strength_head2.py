from sect import *
parts, joints, info = cb.make_capybara()
head, orange, b1 = parts['head'], parts['orange'], parts['body 1']
ho = head + orange
rest = cb.union(p for n, p in parts.items() if n not in ('head', 'orange'))
P = [cb.NECK_X, 0, cb.NECK_Z]
for a in np.arange(30, 181, 1.0):
    o = cb.turn(ho, 'y', P, -a) ^ rest
    if o.volume() > 1e-4:
        nose = np.array(cb.turn(cb.ball(0.1, 0.1, 0, 5), 'y', P, -a).bounding_box())
        print('head DOWN: first contact at %.0f deg; nose tip then at x=%.1f z=%.1f (bed plane is z=0)' % (a, (nose[0]+nose[3])/2, (nose[2]+nose[5])/2))
        o2 = cb.turn(ho, 'y', P, -(a+2)) ^ rest
        for pc in o2.decompose():
            bb = np.array(pc.bounding_box()); cen = (bb[:3]+bb[3:])/2
            print('     overlap 2 deg further: vol %.3f centre (%.2f %.2f %.2f), %.2f mm from the nod axis, bbox %s' % (pc.volume(), *cen, np.hypot(cen[0]-P[0], cen[2]-P[2]), np.round(bb,2)))
        break
else: print('head DOWN: no contact up to 180 deg')
# how far below the belly plane does the head go at 15, 25, 40 deg down
for a in (15, 25, 40):
    bb = cb.turn(ho, 'y', P, -a).bounding_box()
    print('head down %d deg: lowest point z=%.1f' % (a, bb[2]))
# head UP contact: wall thickness of the body at the contact points
up = cb.turn(head, 'y', P, 26.0)
o = cb.turn(head, 'y', P, 27.5) ^ rest
for pc in o.decompose():
    bb = np.array(pc.bounding_box()); c = (bb[:3]+bb[3:])/2
    # thickness of body 1 along the radial line from the nod axis through c (in the plane y = c[1])
    d = np.array([c[0]-P[0], 0, c[2]-P[2]]); R = np.linalg.norm(d); d /= R
    m = mk.to_mesh(b1)
    loc, idx, tri = m.ray.intersects_location([[P[0], c[1], P[2]]], [d])
    rr = np.sort(np.linalg.norm(loc - np.array([P[0], c[1], P[2]]), axis=1))
    print('contact at %.2f mm from the axis, y=%.2f: body 1 along that radial line occupies r = %s' % (R, c[1], np.round(rr,2)))
    loc, idx, tri = m.ray.intersects_location([[c[0], c[1], 0.01+c[2]-3]], [[0,0,1.0]])
    print('    vertical line through it: body 1 surfaces at z = %s' % np.round(np.sort(loc[:,2]),2))
# section of body 1 round the doorway mouth: plane x = 15.5, 16, 17, 18 ; thickness of the roof at |y| = 2.3
m = mk.to_mesh(b1)
for x in (15.3, 15.5, 16, 17, 18, 20, 23.6):
    out = []
    for y in (0.0, 1.0, 2.0, 2.4):
        loc, idx, tri = m.ray.intersects_location([[x, y, 6.6]], [[0,0,1.0]])
        z = np.sort(loc[:,2])
        out.append('y=%.1f: %s' % (y, ' '.join('%.2f' % v for v in z)))
    print('body 1 above the neck slot at x=%.1f  ' % x, ' | '.join(out))
