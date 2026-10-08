"""Preview renders of the footbridge: python railbridge/render.py OUT_DIR"""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import footbridge as fb


def tris(parts, dz):
    P, C = [], []
    for _, w, c in parts:
        rgba = c.toTuple()
        for sh in w.vals():
            v, f = sh.tessellate(30, 0.5)
            v = np.array([(q.x, q.y, q.z + dz) for q in v])
            for t in f:
                P.append(v[list(t)]); C.append(rgba)
    return np.array(P), np.array(C)


def shade(P, C, light=(0.4, -0.5, 0.9)):
    n = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
    k = 0.55 + 0.45 * np.abs(n @ (np.array(light) / np.linalg.norm(light)))
    out = C.copy(); out[:, :3] *= k[:, None]
    return out


def render(parts, dz, path, views, size=(16, 8)):
    P, C = tris(parts, dz); C = shade(P, C)
    fig = plt.figure(figsize=size)
    lo, hi = P.reshape(-1, 3).min(0), P.reshape(-1, 3).max(0)
    for i, (el, az) in enumerate(views):
        ax = fig.add_subplot(1, len(views), i + 1, projection="3d")
        ax.add_collection3d(Poly3DCollection(P, facecolors=C, edgecolors="none"))
        ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1]); ax.set_zlim(lo[2], hi[2])
        ax.set_box_aspect(hi - lo); ax.view_init(el, az); ax.set_axis_off()
    plt.subplots_adjust(0, 0, 1, 1, 0, 0)
    fig.savefig(path, dpi=110, facecolor="white"); plt.close(fig)


def main(out):
    bridge = fb.bridge_parts()
    site = bridge + fb.site_parts()
    render(bridge, 0, f"{out}/Rail_Footbridge_preview.png", [(22, -55), (35, 35)])
    render(site, 0, f"{out}/Rail_Footbridge_Site_preview.png", [(40, -60), (60, 20)], size=(16, 9))


if __name__ == "__main__":
    main(sys.argv[1])
