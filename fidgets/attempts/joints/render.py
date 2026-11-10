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


def as_draw(angles=None):
    mesh, lab = cb.paint(parts, info, (joints, angles) if angles else None)
    return [(mesh.vertices, mesh.faces, lab)]


pose = {"body joint 1": 25, "body joint 2": -25, "body joint 3": 25, "head nod": 12, "orange": 90,
        "front left leg": 35, "front right leg": -30, "hind left leg": -40, "hind right leg": 30}
straight = as_draw()
wiggled = as_draw(pose)
views = [(straight, 25, 60, "straight (as printed)"), (wiggled, 25, 60, "wiggled"), (straight, 8, 0, "side"),
         (straight, 89, 180, "from above, straight"), (wiggled, 89, 180, "from above, wiggled"),
         (straight, 12, 90, "face"), (straight, 15, 125, "front three-quarter"), (straight, 30, -60, "rear quarter"),
         (as_draw({"head nod": -18}), 8, 0, "nose down to its stop"), (as_draw({"head nod": 18}), 8, 0, "nose up to its stop"),
         (straight, 0, 90, "dead-on face"), (straight, 20, 20, "low side quarter")]
fig, ax = plt.subplots(4, 3, figsize=(21, 19))
for a, (m, elev, azim, title) in zip(ax.flat, views):
    pv.draw(a, m, colours, elev=elev, azim=azim)
    a.set_title(title, fontsize=13)
fig.tight_layout()
fig.savefig(HERE / "preview.png", dpi=80, bbox_inches="tight", facecolor="white")
