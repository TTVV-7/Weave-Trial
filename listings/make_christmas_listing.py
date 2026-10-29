#!/usr/bin/env python3
"""Put the Christmas figures together as a listing folder, ready for review.

    python christmas-figures/make_figures.py      # first: the painted 3MFs and STLs
    python listings/make_christmas_listing.py     # then: images/, the zip, listing.json

From what make_figures.py wrote, this renders each figure in its filament
colours as a figurine, an ornament and a magnet, lays the figurines out on a
cover, draws the magnet backs with their pockets, zips the print files with a
print guide, and writes listing.json for cults_upload.py.

listing.json is written once and then left alone apart from its file and image
lists, as with make_listing.py, so edits to the text or price survive a rebuild.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import zipfile
from pathlib import Path

import manifold3d
import matplotlib
import numpy as np
import trimesh

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Polygon  # noqa: E402
from PIL import Image  # noqa: E402

import render  # noqa: E402
from make_listing import MAX_IMAGES, cover  # noqa: E402
from make_tree_listing import caption, magnet_text, pockets, read_3mf  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FIGURES_DIR = ROOT / "christmas-figures"
sys.path.insert(0, str(FIGURES_DIR))
import make_figures as mf  # noqa: E402  FIGURES, HEIGHT and the filament colours

NAMES = {"santa": "Santa", "snowman": "Snowman", "reindeer": "Reindeer", "gingerbread": "Gingerbread Man",
         "nutcracker": "Nutcracker", "penguin": "Penguin"}
FILAMENT_NAMES = {mf.RED: "Red", mf.WHITE: "White", mf.GREEN: "Dark green",
                  mf.BROWN: "Golden brown", mf.BLACK: "Black"}
VIEW = (-25, -80)  # a little from the left and above


def painted(path: Path, flat: bool = False):
    """Mesh and per-triangle colours of a painted 3MF, in the renderer's frame
    (x right, z up, front towards -y). A magnet half lies on its back in its
    file, so it is stood up; its pocket walls are left out of the picture."""
    v, f, k, colours = read_3mf(path)
    rgb = np.array([[int(c[j:j + 2], 16) / 255 for j in (1, 3, 5)] for c in colours])
    keep = np.ones(len(f), bool)
    if flat:
        centroid = v[f].mean(axis=1)
        for centre, r, _ in pockets(v, f):
            keep &= ~((np.linalg.norm(centroid[:, :2] - centre, axis=1) < r + 0.3) & (centroid[:, 2] < 4.6))
        v = np.c_[v[:, 0], -v[:, 2], v[:, 1]]
    return trimesh.Trimesh(v, f[keep], process=False), rgb[k[keep]]


def figure(name: str) -> dict:
    stl = FIGURES_DIR / "stl"
    v, f, _, _ = read_3mf(stl / f"{name}-half.3mf")
    body, body_rgb = painted(stl / f"{name}.3mf")
    w, d, h = body.extents
    return {"name": NAMES[name], "size_mm": (round(w), round(d), round(h)),
            "magnets": [m for _, _, m in pockets(v, f)],
            "filaments": [FILAMENT_NAMES[tuple(c)] for c in mf.FIGURES[name]["filaments"]],
            "forms": {"figurine": (body, body_rgb), "ornament": painted(stl / f"{name}-ornament.3mf"),
                      "magnet": painted(stl / f"{name}-half.3mf", flat=True)}}


def three_forms(fig: dict, out: Path, size: int) -> None:
    """Figurine, ornament and magnet side by side, captioned."""
    with tempfile.TemporaryDirectory() as scratch:
        panels = []
        for i, (form, (mesh, rgb)) in enumerate(fig["forms"].items()):
            p = Path(scratch) / f"{i}.png"
            render.render(mesh, p, face_rgb=rgb, azimuth=VIEW[0], elevation=VIEW[1], size=size,
                          label=form)
            panels.append(Image.open(p).convert("RGB"))
    sheet = Image.new("RGB", (size * 3, size), "#eceff1")
    for i, p in enumerate(panels):
        sheet.paste(p, (i * size, 0))
    sheet.save(out)
    w, d, h = fig["size_mm"]
    caption(out, f"{fig['name']}  ·  {w} × {d} × {h} mm  ·  magnets: {magnet_text(fig['magnets'])}"
                 f"  ·  filaments: {', '.join(fig['filaments'])}", band=size // 12, font=size // 36)


def backs(figures: dict, out: Path) -> None:
    """The flat back of each magnet with its pockets, as seen from behind."""
    fig, axes = plt.subplots(2, 3, figsize=(12, 8))
    for ax, (name, f) in zip(axes.ravel(), figures.items()):
        v, faces, _, _ = read_3mf(FIGURES_DIR / "stl" / f"{name}-half.3mf")
        solid = manifold3d.Manifold(manifold3d.Mesh(vert_properties=v.astype(np.float32),
                                                    tri_verts=faces.astype(np.uint32)))
        for ring in solid.slice(0.3).to_polygons():
            ax.add_patch(Polygon(np.c_[-ring[:, 0], ring[:, 1]], closed=True, fc="#dddddd", ec="k", lw=0.8))
        ax.set_title(f"{f['name']}: {magnet_text(f['magnets'])} magnets", fontsize=10)
        ax.autoscale(); ax.set_aspect("equal"); ax.axis("off")
    fig.suptitle("Magnet backs, seen from behind: a pocket and a glue-in lid for each magnet", fontsize=12)
    fig.tight_layout()
    fig.savefig(out, dpi=100)
    plt.close(fig)


def guide(figures: dict) -> str:
    every = [m for f in figures.values() for m in f["magnets"]]
    lines = ["Christmas figures: figurine, ornament and fridge magnet", "",
             "Each figure comes three ways, and each way as a painted 3MF for a 4-filament",
             "printer (Bambu AMS, Snapmaker U1) and as a plain STL for one colour:", "",
             "  <name>            standing figurine, about 70 mm tall",
             "  <name>-ornament   the same with a hanging loop on top (3 mm hole)",
             "  <name>-half       the front half, flat back, with magnet pockets",
             "  <name>-lids       one thin disc per pocket (STL only)", "",
             "The full-colour textured models (GLB) are separate downloads, one zip per",
             "figure: for 3D viewers, rendering or a full-colour printer.", "",
             "Filaments, in slot order T1-T4. Five figures use the same four; the penguin",
             "swaps dark green for black in slot T3. Matte PLA suits them.", ""]
    for f in figures.values():
        w, d, h = f["size_mm"]
        lines.append(f"  {f['name']:16s} {w:3d} x {d:3d} x {h:3d} mm   {', '.join(f['filaments'])}")
    lines += ["", "Magnets (neodymium discs), for the whole set: " + magnet_text(every)]
    for f in figures.values():
        lines.append(f"  {f['name']:16s} {magnet_text(f['magnets'])}")
    lines += ["", "Printing: figurines and ornaments upright on their base, 0.12-0.16 mm layers,",
              "15% infill, tree supports where the slicer asks (Santa's sack, the",
              "reindeer's antlers, the nutcracker's staff). Magnet halves flat back down,",
              "few supports. Lids flat, no supports.", "",
              "Magnets: drop one into each pocket with a dot of CA glue, same face out",
              "for all of them, then glue a lid on top, flush with the back."]
    return "\n".join(lines) + "\n"


def description(figures: dict) -> str:
    every = [m for f in figures.values() for m in f["magnets"]]
    rows = "\n".join(f"- {f['name']}, {f['size_mm'][0]} x {f['size_mm'][1]} x {f['size_mm'][2]} mm"
                     for f in figures.values())
    return f"""Six Christmas figures in a chunky clay style: {", ".join(f["name"] for f in figures.values())}. Each one comes three ways: a standing figurine about 70 mm tall, a hanging ornament with a loop on top, and a fridge magnet (the front half, with hidden magnet pockets and glue-in lids).

Every file comes as a painted 3MF for 4-filament printers (Bambu AMS, Snapmaker U1) and as a plain STL for single-colour printing. Five figures use the same four filaments in the same slots, red, white, dark green and golden brown, so you load the printer once; the penguin swaps green for black.

Included:
{rows}

Magnets to buy for the set: {magnet_text(every)} neodymium discs.

Files: three zips of print files (figurines, ornaments, magnets), each with a print guide, and one zip per figure with its full-colour GLB model, textured, for 3D viewers, rendering or full-colour printing. Print upright with 0.12-0.16 mm layers; the magnet halves print flat on their back.

The figures were generated with Hi3D from clay-style pictures, then given their loops and magnet pockets and painted for multi-colour printing.
"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("folder", nargs="?", type=Path, default=ROOT / "listings" / "christmas-figures")
    ap.add_argument("--size", type=int, default=1000, help="panel size, px")
    ap.add_argument("--skip-images", action="store_true", help="keep the images already made")
    args = ap.parse_args()
    folder = args.folder
    (folder / "images").mkdir(parents=True, exist_ok=True)
    figures = {name: figure(name) for name in mf.FIGURES}

    shots = [folder / "images" / f"{i + 1}_{name}.png" for i, name in enumerate(figures)]
    cover_path = folder / "images" / "0_cover.png"
    backs_path = folder / "images" / "7_magnet-backs.png"
    if not args.skip_images:
        tiles = []
        with tempfile.TemporaryDirectory() as scratch:
            for (name, f), out in zip(figures.items(), shots):
                three_forms(f, out, args.size)
                tiles.append(Path(scratch) / f"{name}.png")
                mesh, rgb = f["forms"]["figurine"]
                render.render(mesh, tiles[-1], face_rgb=rgb, azimuth=VIEW[0], elevation=VIEW[1], size=800)
                print(f"rendered {out.name}")
            cover(tiles, cover_path, "Christmas Figures Pack",
                  "6 figures  ·  figurine + ornament + fridge magnet  ·  3MF + STL, 4 filaments",
                  cols=3)
        backs(figures, backs_path)

    # One zip per form: all together they are 184 MB, and GitHub, which serves
    # the files to Cults, takes nothing over 100 MB.
    zips = []
    for form, suffixes in (("figurines", ("",)), ("ornaments", ("-ornament",)),
                           ("magnets", ("-half", "-lids"))):
        zip_path = folder / f"{folder.name}-{form}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for name in figures:
                for suffix in suffixes:
                    z.write(FIGURES_DIR / "stl" / f"{name}{suffix}.stl", f"stl/{name}{suffix}.stl")
                    if suffix != "-lids":
                        z.write(FIGURES_DIR / "stl" / f"{name}{suffix}.3mf", f"3mf/{name}{suffix}.3mf")
            z.writestr("PRINT-GUIDE.txt", guide(figures))
        print(f"zipped {zip_path.name}: {zip_path.stat().st_size / 1e6:.1f} MB")
        zips.append(zip_path)
    # The full-colour hi3D models too, zipped one per figure (about 30 MB each):
    # no listing on Cults carries a bare .glb, so it may not take one.
    for name in figures:
        zip_path = folder / f"{folder.name}-glb-{name}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(FIGURES_DIR / f"{name}.glb", f"{name}.glb")
        print(f"zipped {zip_path.name}: {zip_path.stat().st_size / 1e6:.1f} MB")
        zips.append(zip_path)

    listing_path = folder / "listing.json"
    listing = json.loads(listing_path.read_text()) if listing_path.exists() else {
        "name": "Christmas Figures Pack - 6 painted multi-colour figurines, ornaments and fridge magnets",
        "description": description(figures),
        "price": 5.0,
        "currency": "USD",
        "locale": "EN",
        "made_with_ai": True,
        "tags": ["christmas", "ornament", "fridge magnet", "santa", "snowman", "reindeer",
                 "gingerbread", "nutcracker", "penguin", "multicolor"],
        "category_id": "Q2F0ZWdvcnkvMjk",           # Various
        "sub_category_ids": ["Q2F0ZWdvcnkvMTIw"],   # Seasonal & Celebrations
        "license_code": None,
    }
    listing["files"] = [z.name for z in zips]
    listing["images"] = [p.relative_to(folder).as_posix()
                         for p in [cover_path] + shots + [backs_path]][:MAX_IMAGES]
    listing_path.write_text(json.dumps(listing, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {listing_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
