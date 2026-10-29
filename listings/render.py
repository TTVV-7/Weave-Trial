"""Shaded still images of a mesh, for listings: no GPU and no window needed.

    python listings/render.py model.stl out.png

render() draws the triangles back to front with a soft key light, which is
what matplotlib can do quickly for a few hundred thousand triangles.
"""

from __future__ import annotations

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import trimesh  # noqa: E402
from matplotlib.collections import PolyCollection  # noqa: E402

LIGHT = np.array([-0.4, -0.7, 0.9])


def view_matrix(azimuth: float, elevation: float) -> np.ndarray:
    a, e = np.radians(azimuth), np.radians(elevation)
    rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    rx = np.array([[1, 0, 0], [0, np.cos(e), -np.sin(e)], [0, np.sin(e), np.cos(e)]])
    return rx @ rz


def render(mesh: trimesh.Trimesh, path, color=(0.93, 0.70, 0.13), azimuth=-35, elevation=-62,
           size=1000, background="#eceff1", label: str | None = None,
           face_rgb: np.ndarray | None = None) -> None:
    """One view of the mesh. The default angle looks down from the front left.
    face_rgb, one 0-1 colour per triangle, paints it; otherwise it is all color."""
    view = view_matrix(azimuth, elevation)
    v = (mesh.vertices - mesh.bounds.mean(axis=0)) @ view.T
    tris = v[mesh.faces]
    normals = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    lengths = np.linalg.norm(normals, axis=1)
    keep = (lengths > 0) & (normals[:, 2] > 0)  # facing the camera
    tris, normals = tris[keep], normals[keep] / lengths[keep, None]
    base = np.tile(color, (len(mesh.faces), 1)) if face_rgb is None else np.asarray(face_rgb)
    base = base[keep]
    order = np.argsort(tris[:, :, 2].mean(axis=1))
    tris, normals, base = tris[order], normals[order], base[order]

    light = LIGHT / np.linalg.norm(LIGHT)
    shade = 0.35 + 0.65 * np.clip(normals @ light, 0, 1)
    colours = np.clip(base * shade[:, None], 0, 1)

    fig = plt.figure(figsize=(size / 100, size / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor(background)
    fig.patch.set_facecolor(background)
    ax.add_collection(PolyCollection(tris[:, :, :2], facecolors=colours,
                                     edgecolors=colours, linewidths=0.15))
    lo, hi = tris[:, :, :2].reshape(-1, 2).min(axis=0), tris[:, :, :2].reshape(-1, 2).max(axis=0)
    centre, half = (lo + hi) / 2, (hi - lo).max() / 2 * 1.12
    ax.set_xlim(centre[0] - half, centre[0] + half)
    ax.set_ylim(centre[1] - half, centre[1] + half)
    ax.set_aspect("equal")
    ax.axis("off")
    if label:
        ax.text(0.04, 0.04, label, transform=ax.transAxes, fontsize=size / 55,
                color="#3b3a36", family="DejaVu Sans")
    fig.savefig(path, dpi=100, facecolor=background)
    plt.close(fig)


if __name__ == "__main__":
    render(trimesh.load(sys.argv[1]), sys.argv[2])
