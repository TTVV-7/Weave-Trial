"""Render preview.png for this attempt: python3 render.py"""
import pathlib
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(1, '/home/user/Weave-Trial/fidgets')
import make_capybara as cb
import preview as pv


def main(out="preview.png"):
    colours = [f"#{r:02X}{g:02X}{b:02X}" for r, g, b in cb.FILAMENTS]
    parts, joints, info = cb.make_capybara()

    def as_draw(ps):
        mesh, lab = cb.paint(parts, info, ps)
        return [(mesh.vertices, mesh.faces, lab)]

    s = cb.SWING
    pose = {"body joint 1": s, "body joint 2": -s, "body joint 3": s, "head nod": 10, "orange": 90,
            "front left leg": 35, "front right leg": -30, "hind left leg": -40, "hind right leg": 30}
    straight = as_draw(parts)
    wiggled = as_draw(cb.posed(parts, joints, pose))
    views = [(straight, 25, 60, "straight, as printed"), (wiggled, 25, 60, "wiggled"),
             (straight, 10, 0, "side"), (straight, 89, 180, "top, straight"),
             (wiggled, 89, 180, "top, wiggled"), (straight, 12, 90, "face")]
    fig, ax = plt.subplots(2, 3, figsize=(19, 10))
    for a, (m, e, z, t) in zip(ax.ravel(), views):
        pv.draw(a, m, colours, elev=e, azim=z)
        a.set_title(t, fontsize=13)
    fig.tight_layout()
    fig.savefig(HERE / out, dpi=80, facecolor="white")


if __name__ == "__main__":
    main(*sys.argv[1:])
