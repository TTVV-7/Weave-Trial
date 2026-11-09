from common import *
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
colours = [f"#{r:02X}{g:02X}{b:02X}" for r, g, b in cb.FILAMENTS]
parts, joints, info = cb.make_capybara()
def as_draw(ps):
    mesh, lab = cb.paint(parts, info, ps)
    return [(mesh.vertices, mesh.faces, lab)]
straight = as_draw(parts)
down = as_draw(cb.posed(parts, joints, {'head nod': -63}))
up = as_draw(cb.posed(parts, joints, {'head nod': 26}))
fig, ax = plt.subplots(2, 3, figsize=(21, 11))
for a, (m, e, z, t) in zip(ax.flat, [(straight, 8, 75, 'eye level, front quarter'), (straight, 20, 120, 'rear quarter'), (straight, 0, 90, 'dead-on face'),
                                      (down, 5, 0, 'head at its DOWN stop (63 deg)'), (up, 5, 0, 'head at its UP stop (26 deg)'), (straight, 35, 20, 'high side')]):
    pv.draw(a, m, colours, elev=e, azim=z); a.set_title(t, fontsize=13)
fig.tight_layout(); fig.savefig('views.png', dpi=60, facecolor='white')
