#!/usr/bin/env python3
"""Put the Pacific Northwest tree magnets together as a listing folder, ready for review.

    python pnw-tree-magnets/make_magnets.py   # first: the painted 3MFs and STLs
    python listings/make_tree_listing.py      # then: images/, the zip, listing.json

From the half-trees make_magnets.py wrote, this renders each one in its
filament colours, lays them out on one cover image, adds the front-and-back
preview sheet, zips the print files with a print guide, and writes
listing.json for cults_upload.py.

listing.json is written once and then left alone apart from its file and image
lists, as with make_listing.py, so edits to the text or price survive a rebuild.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

import manifold3d
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont

import render
from make_listing import FONT, MAX_IMAGES, cover

ROOT = Path(__file__).resolve().parent.parent
TREES_DIR = ROOT / "pnw-tree-magnets"
sys.path.insert(0, str(TREES_DIR))
import make_magnets as mm  # noqa: E402  TREES, PAINT_CODE, MAGNETS and the pocket sizes

FILAMENTS = [("Dark forest green", "needles and leaves"),
             ("Moss green", "lighter needles, moss on the bases"),
             ("Dark brown", "trunks, bark, bases, madrone berries"),
             ("Golden amber", "maple leaves, madrone bark")]
VIEW = (-25, -80)  # a little from the left and above, so the relief shows


def title(name: str) -> str:
    return name.replace("-", " ").title()


def read_3mf(path: Path):
    """Vertices, triangles, filament index per triangle and filament colours."""
    xml = zipfile.ZipFile(path).read("3D/3dmodel.model").decode()
    v = np.array(re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', xml), float)
    t = re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)" paint_color="([^"]+)"', xml)
    f = np.array([x[:3] for x in t], int)
    k = np.array([mm.PAINT_CODE.index(x[3]) for x in t])
    colours = [c[:7] for c in re.findall(r'<m:color color="([^"]+)"', xml)]
    return v, f, k, colours


def pockets(v, f) -> list[tuple[np.ndarray, float, tuple[float, float]]]:
    """(centre, radius, magnet) for each magnet pocket: the round holes in the flat back."""
    solid = manifold3d.Manifold(manifold3d.Mesh(vert_properties=v.astype(np.float32),
                                                tri_verts=f.astype(np.uint32)))
    found = []
    for ring in solid.slice(0.3).to_polygons():
        centre = ring.mean(axis=0)
        r = np.linalg.norm(ring - centre, axis=1)
        for magnet in mm.MAGNETS:
            if r.std() < 0.03 * r.mean() and abs(r.mean() - (magnet[0] + mm.CLEARANCE) / 2) < 0.1:
                found.append((centre, r.mean(), magnet))
    return found


def tree(name: str) -> dict:
    v, f, k, colours = read_3mf(TREES_DIR / "stl" / f"{name}-half.3mf")
    holes = pockets(v, f)
    # Leave the pocket walls out of the pictures: drawn back to front, they show
    # through the hairline gaps between the triangles in front of them.
    centroid = v[f].mean(axis=1)
    hidden = np.zeros(len(f), bool)
    for centre, r, _ in holes:
        hidden |= (np.linalg.norm(centroid[:, :2] - centre, axis=1) < r + 0.3) & (centroid[:, 2] < 4.6)
    upright = np.c_[v[:, 0], -v[:, 2], v[:, 1]]  # front towards -y, top up
    rgb = np.array([[int(c[j:j + 2], 16) / 255 for j in (1, 3, 5)] for c in colours])
    return {"name": title(name), "mesh": trimesh.Trimesh(upright, f[~hidden], process=False),
            "rgb": rgb[k[~hidden]], "size_mm": (v.max(axis=0) - v.min(axis=0)).round(),
            "magnets": [m for _, _, m in holes]}


def caption(path: Path, text: str, band: int | None = None, font: int | None = None) -> None:
    """The text in a strip under the picture, where it can't run over the tree's base.
    The strip's height and the font size follow the picture's width unless given."""
    picture = Image.open(path).convert("RGB")
    band = band or picture.width // 15
    out = Image.new("RGB", (picture.width, picture.height + band), "#eceff1")
    out.paste(picture, (0, 0))
    ImageDraw.Draw(out).text((picture.width // 30, picture.height + band // 4), text, fill="#3b3a36",
                             font=ImageFont.truetype(FONT, font or picture.width // 45))
    out.save(path)


def magnet_text(magnets: list) -> str:
    counts = {m: magnets.count(m) for m in sorted(set(magnets), reverse=True)}
    return " and ".join(f"{n} x {d:.0f}x{t:.0f} mm" for (d, t), n in counts.items())


def guide(trees: dict) -> str:
    every = [m for t in trees.values() for m in t["magnets"]]
    lines = ["Pacific Northwest tree magnets", "",
             "Each magnet is the front half of a tree, with a flat back that sits on the",
             "fridge and a pocket for each magnet.", "",
             "  3mf/*-half.3mf  painted, for a 4-filament printer (Bambu AMS, Snapmaker U1).",
             "                  Opens painted in Bambu Studio, OrcaSlicer and Snapmaker Orca.",
             "  stl/*-half.stl  the same tree as one solid, for one colour or to paint by hand.",
             "  stl/*-lids.stl  one thin disc per magnet pocket.", "",
             "Filaments: the same four slots for every tree, so different trees can share",
             "a plate. Matte PLA suits them. Filaments a shade brighter than these look",
             "closer to the pictures; a bright yellow-orange works well for T4.", ""]
    for i, (name, paints) in enumerate(FILAMENTS):
        lines.append(f"  T{i + 1}  {name:18s} {paints}")
    lines += ["", "Tree                  width x height   depth   magnets (neodymium discs)"]
    for t in trees.values():
        w, h, d = t["size_mm"]
        lines.append(f"{t['name']:21s} {w:4.0f} x {h:3.0f} mm    {d:3.0f} mm   {magnet_text(t['magnets'])}")
    lines += [f"{'For the set':21s} {'':21s} {magnet_text(every)}", "",
              "Printing: half flat back down, 0.12 mm layers for the needle detail, 15% infill;",
              "most of the relief faces up, so it needs few supports. Lids flat, no supports.", "",
              "Assembly:",
              "1. Mark which face of each magnet is 'out' and fit them all the same way up,",
              "   so trees next to each other don't push apart.",
              "2. Drop a magnet into each pocket with a dot of CA glue, then glue a lid on",
              "   top. It sits flush with the back, so the magnets are hidden."]
    return "\n".join(lines) + "\n"


def description(trees: dict) -> str:
    every = [m for t in trees.values() for m in t["magnets"]]
    rows = "\n".join(f"- {t['name']}, {t['size_mm'][0]:.0f} x {t['size_mm'][1]:.0f} mm, "
                     f"{t['size_mm'][2]:.0f} mm deep, {magnet_text(t['magnets'])} magnets"
                     for t in trees.values())
    return f"""Six Pacific Northwest trees as fridge magnets: {", ".join(t["name"] for t in trees.values())}. Each one is the front half of a stylised tree, about 75 mm tall, with a flat back and hidden magnet pockets, so it sits flat on the fridge.

Every tree comes as a painted 3MF for 4-filament printers (Bambu AMS, Snapmaker U1) and as a plain STL for single-colour printing. All six use the same four filaments in the same slots, so you load the printer once and can mix trees on one plate.

Included:
{rows}

Magnets to buy: {magnet_text(every)} neodymium discs. Each pocket gets a thin printed lid, so the magnets are hidden.

Filaments: {", ".join(n for n, _ in FILAMENTS)}. Matte PLA suits them.

Print flat back down with 0.12 mm layers; few supports needed. A print guide is in the zip.

The trees were generated with Hi3D, then cut flat, fitted with magnet pockets and painted for multi-colour printing.
"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("folder", nargs="?", type=Path, default=ROOT / "listings" / "pnw-tree-magnets")
    ap.add_argument("--size", type=int, default=1200, help="image size, px")
    args = ap.parse_args()
    folder = args.folder
    (folder / "images").mkdir(parents=True, exist_ok=True)
    trees = {name: tree(name) for name in mm.TREES}

    shots, tiles = [], []
    with tempfile.TemporaryDirectory() as scratch:
        for i, (name, t) in enumerate(trees.items()):
            w, h, d = t["size_mm"]
            out = folder / "images" / f"{i + 1}_{name}.png"
            render.render(t["mesh"], out, face_rgb=t["rgb"], azimuth=VIEW[0], elevation=VIEW[1],
                          size=args.size)
            caption(out, f"{t['name']}  ·  {w:.0f} × {h:.0f} mm, {d:.0f} mm deep  ·  "
                         f"magnets: {magnet_text(t['magnets'])}")
            shots.append(out)
            tiles.append(Path(scratch) / f"{name}.png")
            render.render(t["mesh"], tiles[-1], face_rgb=t["rgb"], azimuth=0, elevation=-90, size=800)
            print(f"rendered {out.name}: {magnet_text(t['magnets'])}")
        cover_path = folder / "images" / "0_cover.png"
        cover(tiles, cover_path, "Pacific Northwest Tree Magnets",
              "6 fridge magnets  ·  painted 3MF + STL  ·  the same 4 filaments for all", cols=3)
    backs = folder / "images" / "7_front-and-back.png"
    shutil.copyfile(TREES_DIR / "magnet-preview.png", backs)

    zip_path = folder / f"{folder.name}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for name in trees:
            z.write(TREES_DIR / "stl" / f"{name}-half.3mf", f"3mf/{name}-half.3mf")
            z.write(TREES_DIR / "stl" / f"{name}-half.stl", f"stl/{name}-half.stl")
            z.write(TREES_DIR / "stl" / f"{name}-lids.stl", f"stl/{name}-lids.stl")
        z.writestr("PRINT-GUIDE.txt", guide(trees))
    print(f"zipped {zip_path.name}: {zip_path.stat().st_size / 1e6:.1f} MB")

    listing_path = folder / "listing.json"
    listing = json.loads(listing_path.read_text()) if listing_path.exists() else {
        "name": "Pacific Northwest Tree Magnets - 6 painted multi-colour fridge magnets",
        "description": description(trees),
        "price": 3.0,
        "currency": "USD",
        "locale": "EN",
        "made_with_ai": True,
        "tags": ["fridge magnet", "magnet", "tree", "Pacific Northwest", "PNW", "Douglas fir",
                 "cedar", "maple", "multicolor", "AMS"],
        "category_id": "Q2F0ZWdvcnkvMzA",          # Home
        "sub_category_ids": ["Q2F0ZWdvcnkvNjE"],   # Home Decor
        "license_code": None,
    }
    listing["files"] = [zip_path.name]
    listing["images"] = [p.relative_to(folder).as_posix()
                         for p in [cover_path] + shots + [backs]][:MAX_IMAGES]
    listing_path.write_text(json.dumps(listing, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {listing_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
