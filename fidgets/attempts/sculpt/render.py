"""Render preview.png for this attempt: python3 render.py"""
import pathlib
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, '/home/user/Weave-Trial/fidgets')
sys.path.insert(0, str(HERE))
import preview as pv
import make_capybara as cb

POSE = {"body joint 1": 22.5, "body joint 2": -22.5, "body joint 3": 22.5, "head nod": 12, "orange": 90,
        "front left leg": 35, "front right leg": -30, "hind left leg": -40, "hind right leg": 30}


def main(out="preview.png", only=None):
    colours = [f"#{r:02X}{g:02X}{b:02X}" for r, g, b in cb.FILAMENTS]
    parts, joints, info = cb.make_capybara()

    def as_draw(ps):
        mesh, lab = cb.paint(parts, info, ps)
        return [(mesh.vertices, mesh.faces, lab)]

    straight = as_draw(parts)
    wiggled = as_draw(cb.posed(parts, joints, POSE))
    views = [(straight, 25, 60, "front three-quarter, straight (as printed)"),
             (wiggled, 25, 60, "the same view, wiggled"),
             (straight, 10, 0, "side"),
             (straight, 89, 180, "from above, straight"),
             (wiggled, 89, 180, "from above, wiggled"),
             (straight, 12, 90, "the face")]
    fig, ax = plt.subplots(2, 3, figsize=(21, 10))
    for a, (m, elev, azim, title) in zip(ax.ravel(), views):
        pv.draw(a, m, colours, elev=elev, azim=azim)
        a.set_title(title, fontsize=13)
    fig.tight_layout()
    fig.savefig(HERE / out, dpi=80, bbox_inches="tight", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
