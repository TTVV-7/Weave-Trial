from sect import *
parts, joints, info = cb.make_capybara()
leg = parts['front left leg']; x0 = cb.LEG_X[0]; b1 = parts['body 1']
g = cb.CLEAR*np.sqrt(2)
hole_r = cb.LEG_NECK/2 + g + cb.LEG_GAP
pin_r = cb.LEG_NECK/2 + cb.LEG_GAP + cb.LEG_D
print('leg hole radius at its inner face %.3f, pin head radius %.3f, radial catch %.3f' % (hole_r, pin_r, pin_r-hole_r))
def first(fn, vals):
    for a in vals:
        if (fn(a) ^ b1).volume() > 1e-4: return a
    return None
print('leg pulled outwards touches at', first(lambda d: leg.translate([0,d,0]), np.arange(0,1.5,0.05)))
print('leg pushed inwards touches at', first(lambda d: leg.translate([0,-d,0]), np.arange(0,1.5,0.05)))
print('leg lifted touches at', first(lambda d: leg.translate([0,0,d]), np.arange(0,3,0.05)))
print('leg pushed down touches at', first(lambda d: leg.translate([0,0,-d]), np.arange(0,3,0.05)))
p = np.array([x0, cb.FLANK+cb.LEG_GAP, cb.LEG_Z])
def tilt(a, ax):
    r = [a,0,0] if ax=='x' else [0,0,a]
    return leg.translate(list(-p)).rotate(r).translate(list(p))
for ax in 'xz':
    for s in (1,-1):
        a = first(lambda a: tilt(s*a, ax), np.arange(0,40,0.5))
        print('leg tilted about', ax, 'sign', s, 'touches at', a, 'deg')
        if a is not None:
            o = tilt(s*a, ax) ^ b1
            print('    contact bbox', np.round(o.bounding_box(),2))
# catch region lost at the bottom of the pin
pin = b1 ^ cb.box(x0-4, x0+4, cb.FLANK+cb.LEG_GAP, cb.FLANK+3, 2, 11)   # the part of the pin inside the leg
print('pin inside leg bbox', np.round(pin.bounding_box(),2))
# shadow of pin head beyond the hole, seen along y: the catch area
T = np.array([[1,0,0,0],[0,0,1,0],[0,1,0,0]], float)  # (x,z,y)
proj = pin.transform(T).project()
hole = mf.CrossSection.circle(hole_r, 128).translate([x0, cb.LEG_Z])
catch = proj - hole
print('pin shadow area %.2f, hole area %.2f, catch (pin shadow outside the hole) %.2f mm2' % (proj.area(), hole.area(), catch.area()))
full = mf.CrossSection.circle(pin_r,128).translate([x0, cb.LEG_Z]) - hole
print('a full cone head would catch %.2f mm2' % full.area())
below = catch ^ mf.CrossSection.square([20,20]).translate([x0-10, cb.LEG_Z-20])
print('catch below the pin axis %.2f mm2' % below.area())
