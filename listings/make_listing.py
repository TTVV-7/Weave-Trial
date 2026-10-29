#!/usr/bin/env python3
"""Put a built scale-model pack together as a listing folder, ready for review.

    python listings/make_scale_models.py      # first: the models, into files/
    python listings/make_listing.py           # then: images/, the zip, listing.json

From what make_scale_models.py wrote (the STLs, painted 3MFs and report.json)
this renders each model in its filament colours, lays them out on one cover
image, zips every file with a print guide, and writes listing.json for
cults_upload.py: title, description, price, tags, which zip and which images.

listing.json is written once and then left alone apart from its file and image
lists, so edits to the title, description or price survive a rebuild. Delete
it to start the text over.
"""

from __future__ import annotations

import argparse
import json
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont

import render

ROOT = Path(__file__).resolve().parent.parent
MAX_IMAGES = 10  # Cults' limit per listing
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# Which models get their own picture, best first: the cover shows all of them.
SHOWCASE = ["Telehandler_10000lb_56ft", "Carry_Deck_Crane", "Trailer_Concrete_Line_Pump",
            "Towable_Air_Compressor", "Roll_Off_Dumpster_20yd", "Temporary_Fence_Panel_6x10ft",
            "Rail_Crossover_Gantry", "Bulk_Bag_Concrete_on_Pallet", "Planetary_Mixer_on_Stand",
            "Industrial_Steel_Stair_12ft", "Pallet_of_Concrete_Bags", "Traffic_Cone_28in",
            "Planetary_Concrete_Mixer_500L", "Mixer_Stand"]


def hex_rgb(h: str) -> list[float]:
    return [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]


def render_model(folder: Path, info: dict, out: Path, size: int, caption: bool = True) -> None:
    stl = folder / "files" / info["file"]
    mesh = trimesh.load(stl)
    slots = np.load(stl.with_suffix(".slots.npy"))
    palette = np.array([hex_rgb(f.split()[-1]) for f in info["filaments"]])
    x, y, z = info["size_mm"]
    render.render(mesh, out, face_rgb=palette[slots], size=size,
                  label=f"{info['name']}  ·  {x:.0f} × {y:.0f} × {z:.0f} mm" if caption else None)


def cover(tiles: list[Path], out: Path, title: str, subtitle: str, cols: int | None = None) -> None:
    """All the models on one sheet under a title, four or five to a row unless cols says."""
    cell, cols = 400, cols or (4 if len(tiles) <= 12 else 5)
    rows = -(-len(tiles) // cols)
    head = 150
    sheet = Image.new("RGB", (cell * cols, head + cell * rows), "#eceff1")
    for i, path in enumerate(tiles):
        tile = Image.open(path).convert("RGB").resize((cell, cell), Image.LANCZOS)
        sheet.paste(tile, ((i % cols) * cell, head + (i // cols) * cell))
    draw = ImageDraw.Draw(sheet)
    draw.text((40, 30), title, font=ImageFont.truetype(FONT_BOLD, 52), fill="#2b2a27")
    draw.text((42, 95), subtitle, font=ImageFont.truetype(FONT, 28), fill="#5b5952")
    sheet.save(out)


def guide(report: dict) -> str:
    lines = [f"Construction site scale models, {report['scale']}", "",
             "Each model comes twice:",
             "  *.3mf  painted, for a multi-colour printer (AMS, Snapmaker U1, MMU).",
             "         Opens painted in Bambu Studio, OrcaSlicer and Snapmaker Orca.",
             "         Load the filaments listed below into T1-T4.",
             "  *.stl  one solid, for a single-colour print or to paint by hand.", "",
             "Print settings: 0.4 mm nozzle, 0.12-0.16 mm layers, 3 walls,",
             "15% infill, tree supports from the build plate. Thin rails and",
             f"wires are thickened to {report['min_feature_mm']} mm so they print. The fence",
             "mesh is 0.5 mm wire: turn on thin-wall detection in the slicer.", "",
             "Model                                  size (mm)        filaments"]
    for info in report["models"].values():
        x, y, z = info["size_mm"]
        names = ", ".join(" ".join(f.split()[1:-1]) for f in info["filaments"])
        lines.append(f"{info['name']:38s} {x:4.0f} x {y:3.0f} x {z:3.0f}   {names}")
    return "\n".join(lines) + "\n"


def description(report: dict) -> str:
    models = report["models"].values()
    rows = "\n".join(f"- {m['name']}, {m['size_mm'][0]:.0f} x {m['size_mm'][1]:.0f} x "
                     f"{m['size_mm'][2]:.0f} mm" for m in models)
    colours = sorted({" ".join(f.split()[1:-1]) for m in models for f in m["filaments"]})
    return f"""{len(report['models'])} construction site models at {report['scale']}, the scale of diecast construction equipment, for dioramas, model railways and desk display.

Every model comes as a painted 3MF for multi-colour printers (Bambu AMS, Snapmaker U1, Prusa MMU), with up to four filaments per model, and as a plain STL for single-colour printing. Thin parts such as handrails, ladders and forks are thickened so they print on a 0.4 mm nozzle, and the fence mesh is drawn as single 0.5 mm lines.

Included:
{rows}

Filaments used across the set: {", ".join(colours)}.

Print with 0.12-0.16 mm layers and tree supports. A print guide with each model's size and filament slots is in the zip.
"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("folder", nargs="?", type=Path,
                    default=ROOT / "listings" / "construction-site-1-50")
    ap.add_argument("--size", type=int, default=1200, help="image size, px")
    args = ap.parse_args()
    folder = args.folder
    report = json.loads((folder / "report.json").read_text())
    models = report["models"]
    (folder / "images").mkdir(exist_ok=True)

    shots, tiles = [], []
    with tempfile.TemporaryDirectory() as scratch:
        for stem in [s for s in SHOWCASE if s in models]:
            info = models[stem]
            out = folder / "images" / f"{stem}.png"
            render_model(folder, info, out, args.size)
            shots.append(out)
            # the model library shows the picture named like a model beside it (STL and 3MF both)
            thumb = (folder / "files" / info["file"]).with_suffix(".png")
            Image.open(out).convert("RGB").resize((480, 480), Image.LANCZOS).save(thumb)
            tiles.append(Path(scratch) / f"{stem}.png")
            render_model(folder, info, tiles[-1], 800, caption=False)
            print(f"rendered {out.name}")
        cover_path = folder / "images" / "00_cover.png"
        cover(tiles, cover_path, f"Construction Site Pack  {report['scale']}",
              f"{len(models)} painted models  ·  multi-colour 3MF + STL  ·  up to 4 filaments each")

    zip_path = folder / f"{folder.name}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for info in models.values():
            z.write(folder / "files" / info["file"], f"stl/{info['file']}")
            z.write(folder / "files" / info["painted"], f"3mf/{info['painted']}")
        z.writestr("PRINT-GUIDE.txt", guide(report))
    print(f"zipped {zip_path.name}: {zip_path.stat().st_size / 1e6:.1f} MB")

    listing_path = folder / "listing.json"
    listing = json.loads(listing_path.read_text()) if listing_path.exists() else {
        "name": f"Construction Site Pack {report['scale']} - {len(models)} painted multi-colour models",
        "description": description(report),
        "price": 5.0,
        "currency": "USD",
        "locale": "EN",
        "made_with_ai": True,
        "tags": ["construction", "diorama", "scale model", "1:50", "telehandler", "dumpster",
                 "concrete mixer", "multicolor", "AMS", "model railway"],
        "category_id": None,
        "license_code": None,
    }
    listing["files"] = [zip_path.name]
    listing["images"] = [p.relative_to(folder).as_posix()
                         for p in [cover_path] + shots][:MAX_IMAGES]
    listing_path.write_text(json.dumps(listing, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {listing_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
