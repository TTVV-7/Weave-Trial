"""Render preview.png for this attempt: python3 render.py"""
import sys
import pathlib
sys.path.insert(0, '/home/user/Weave-Trial/fidgets')
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import preview as pv
import make_capybara as cb

colours = [f"#{r:02X}{g:02X}{b:02X}" for r, g, b in cb.FILAMENTS]
parts, joints, info = cb.make_capybara()
plain = cb.make_capybara(loop=False)


def as_draw(angles=None, model=None):
    p, j, i = model or (parts, joints, info)
    mesh, lab = cb.paint(p, i, (j, angles) if angles else None)
    return [(mesh.vertices, mesh.faces, lab)]


pose = {"body joint 1": 25, "body joint 2": -25, "body joint 3": 25, "head nod": 12, "orange": 90,
        "front left leg": 35, "front right leg": -30, "hind left leg": -40, "hind right leg": 30}
straight = as_draw()
wiggled = as_draw(pose)
bent = as_draw({"body joint 2": 25})
# (mesh, elev, azim, title, close-up: point to centre on and half width of the view, or None)
joint2 = ([cb.AXES[1] + 6, 0, 13], 11)
views = [(straight, 25, 60, "straight (as printed)", None), (wiggled, 25, 60, "wiggled", None),
         (straight, 8, 0, "side", None), (straight, 89, 180, "from above, straight", None),
         (wiggled, 89, 180, "from above, wiggled", None), (straight, 12, 90, "face", None),
         (straight, 0, 90, "dead-on face", None), (straight, 15, 125, "front three-quarter", None),
         (straight, 30, -60, "rear quarter", None), (as_draw({"head nod": -18}), 8, 0, "nose down to its stop", None),
         (as_draw({"head nod": 18}), 8, 0, "nose up to its stop", None), (straight, 20, 20, "low side quarter", None),
         (straight, 35, 20, "close-up: the seam at body joint 2, straight", joint2),
         (bent, 35, 20, "close-up: body joint 2 bent 25 degrees", joint2),
         (straight, 8, 0, "close-up: hind leg and the keyring eye", ([56, 0, 9], 11)),
         (as_draw(model=plain), 30, -60, "without the keyring eye", None)]
fig, ax = plt.subplots(4, 4, figsize=(28, 19))
for a, (m, elev, azim, title, close) in zip(ax.flat, views):
    pv.draw(a, m, colours, elev=elev, azim=azim)
    if close:
        c = pv.view(elev, azim) @ np.array(close[0], float)
        a.set_xlim(c[0] - close[1], c[0] + close[1])
        a.set_ylim(c[1] - close[1] * 0.7, c[1] + close[1] * 0.7)
    a.set_title(title, fontsize=13)
fig.tight_layout()
fig.savefig(HERE / "preview.png", dpi=80, bbox_inches="tight", facecolor="white")
