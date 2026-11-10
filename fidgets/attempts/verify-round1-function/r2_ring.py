"""Round 2: can a split ring actually sit in the keyring eye and swing? A ring (torus) is put through the hole and
leaned from straight up towards the tail (+) and towards the head (-); at each lean it may sit anywhere in the hole.
Reports the range of lean it can take without cutting into the body."""
import numpy as np
import manifold3d as mf
from common import cb
parts, joints, info = cb.make_capybara()
b4 = parts["body 4"]
others = cb.union([parts["body 3"], parts["hind left leg"], parts["hind right leg"]])
H = np.array([cb.KEYRING_X, 0.0, cb.KEYRING_Z])
print(f"hole: {cb.KEYRING_D} mm at x {cb.KEYRING_X}, z {cb.KEYRING_Z}; web {cb.KEYRING_T} thick; top of the eye {b4.bounding_box()[5]:.2f}; rump end x {b4.bounding_box()[3]:.2f}")
# the direction the ring pulls when the toy hangs from it: from the centre of mass to the hole
m = cb.union(parts.values())
tm = __import__("trimesh").Trimesh(*[np.asarray(a) for a in (m.to_mesh().vert_properties[:, :3], m.to_mesh().tri_verts)])
com = tm.center_mass
pull = H - com
print(f"centre of mass {np.round(com, 1).tolist()}; hanging from the eye the ring pulls {np.degrees(np.arctan2(pull[0], pull[2])):.0f} deg from straight up, towards the tail")
def torus(R, d):
    return mf.CrossSection.circle(d / 2, 24).translate([R, 0]).revolve(96)      # in the x-y plane, axis z
def ring_at(R, d, lean, du=0.0, dv=0.0):
    """Ring through the hole, its plane holding the hole's axis (y) and leaning `lean` deg from upright towards the tail."""
    t = torus(R, d).rotate([90, 0, 0])            # now in the x-z plane, axis y ... want plane containing y: rotate about z by 90
    t = torus(R, d).rotate([0, 90, 0])            # plane y-z, axis x; the ring's lowest point is at z = -R
    t = t.translate([0, 0, R + du])               # lowest point of the wire's centre line at the origin (+du up)
    t = t.rotate([0, lean, 0])                    # lean about y: + takes the top towards +x (the tail)
    return t.translate([H[0] + dv * np.cos(np.radians(lean)), 0, H[2] - dv * np.sin(np.radians(lean))])
for R, d in ((6.0, 1.6), (8.0, 1.6), (10.0, 2.0), (12.5, 2.0), (12.5, 2.4)):
    free = []
    slack = cb.KEYRING_D / 2 - d / 2
    for lean in np.arange(-120, 120.1, 5.0):
        ok = False
        for du in np.linspace(-slack, slack * 1.4, 6):
            for dv in np.linspace(-slack, slack, 5):
                r = ring_at(R, d, lean, du, dv)
                if (r ^ b4).volume() < 1e-4 and (r ^ others).volume() < 1e-4:
                    ok = True; break
            if ok: break
        free.append((lean, ok))
    okl = [l for l, o in free if o]
    runs = []
    for l in okl:
        if runs and l - runs[-1][1] <= 5.01: runs[-1][1] = l
        else: runs.append([l, l])
    print(f"ring {2 * R - d:.0f} mm inside / {2 * R + d:.0f} outside, wire {d}: fits leaning " + (", ".join(f"{a:+.0f}..{b:+.0f}" for a, b in runs) if runs else "NOWHERE") + " deg (0 = straight up, + = towards the tail)")
