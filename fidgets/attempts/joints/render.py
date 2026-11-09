"""Render preview.png for this attempt: python3 render.py"""
import sys
import pathlib
sys.path.insert(0, '/home/user/Weave-Trial/fidgets')
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import preview as pv
import make_capybara as cb

colours = [f"#{r:02X}{g:02X}{b:02X}" for r, g, b in cb.FILAMENTS]
parts, joints, info = cb.make_capybara()


def as_draw(ps):
    mesh, lab = cb.paint(parts, info, ps)
    return [(mesh.vertices, mesh.faces, lab)]


pose = {"body joint 1": 25, "body joint 2": -25, "body joint 3": 25, "head nod": 12, "orange": 90,
        "front left leg": 35, "front right leg": -30, "hind left leg": -40, "hind right leg": 30}
straight = as_draw(parts)
wiggled = as_draw(cb.posed(parts, joints, pose))
views = [(straight, 25, 60, "straight (as printed)"), (wiggled, 25, 60, "wiggled"), (straight, 10, 0, "side"),
         (straight, 89, 180, "from above, straight"), (wiggled, 89, 180, "from above, wiggled"),
         (straight, 12, 90, "face")]
fig, ax = plt.subplots(2, 3, figsize=(21, 10))
for a, (m, elev, azim, title) in zip(ax.flat, views):
    pv.draw(a, m, colours, elev=elev, azim=azim)
    a.set_title(title, fontsize=13)
fig.tight_layout()
fig.savefig(HERE / "preview.png", dpi=80, bbox_inches="tight", facecolor="white")
