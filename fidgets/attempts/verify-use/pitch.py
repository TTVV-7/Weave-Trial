from sect import *
parts, joints, info = cb.make_capybara()
at = cb.AXES[0]
front, rear = parts['body 1'], parts['body 2']
def rot(m, a, c):
    return m.translate([-c[0],-c[1],-c[2]]).rotate([0,a,0]).translate(c)
def contacts(m):
    o = m ^ front
    return [(pc.volume(), np.round((np.array(pc.bounding_box())[:3]+np.array(pc.bounding_box())[3:])/2,2)) for pc in o.decompose()]
# greedy: tail-down (+) and tail-up (-). At each angle let the rear segment slide in x and z to find a pose with no overlap.
import itertools
def free_pose(a, piv):
    best = None
    for dx in np.arange(-0.6, 0.61, 0.1):
        for dz in np.arange(-0.6, 0.61, 0.1):
            m = rot(rear, a, piv).translate([dx, 0, dz])
            v = (m ^ front).volume()
            if v < 1e-5:
                return (dx, dz)
    return None
piv = [at, 0, 4.0]
for s in (1, -1):
    last = 0
    for a in np.arange(1, 25, 1.0):
        p = free_pose(s*a, piv)
        if p is None:
            print('pitch %+d (%s): with the segment free to slide +-0.6 mm, it locks between %.0f and %.0f deg' % (s, 'tail down' if s>0 else 'tail up', last, a))
            # show the contacts at this angle for the least-overlap offset
            best = min(((rot(rear, s*a, piv).translate([dx,0,dz]) ^ front).volume(), dx, dz) for dx in np.arange(-0.6,0.61,0.1) for dz in np.arange(-0.6,0.61,0.1))
            m = rot(rear, s*a, piv).translate([best[1],0,best[2]])
            print('    least overlap %.3f mm3 at slide dx=%.1f dz=%.1f; contact patches (volume, centre):' % best)
            for v, c in contacts(m): print('       %.4f at %s  (r=%.1f from the joint axis)' % (v, c, np.hypot(c[0]-at, c[1])))
            break
        last = a
