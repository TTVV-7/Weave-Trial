#!/usr/bin/env python3
"""Stage the construction models for the Neptune Terminals digital twin (TTVV-7/Neptune-digital-twin).

    python construction_site/export_neptune.py --neptune ../ttvv-7/neptune-digital-twin
    python construction_site/export_neptune.py --pack 4          # only pack 4

Reads construction_site/neptune/manifest.json (which model becomes which library id, in which
category, added or replacing an existing item, or skipped) and writes, under neptune/out/:

    public/library/<id>.glb            slimmed for the web (meshopt, parts joined by colour)
    public/library/thumbs/<id>.webp    256 x 256 card thumbnail, rendered from the model, all in one style
    library-entries.json               the entries to merge into public/library/library.json
    REPORT.md                          sizes, triangles and draw calls per model, and any problems

Copying public/ over the twin's public/ and merging the entries (scripts/merge-construction-
library.mjs in the plan) is a separate, reviewed step: nothing here touches the twin.
With --neptune it also checks the manifest against the twin: an id to add must be free, an id to
replace must exist, and every category must be one the twin's sidebar knows.

Needs node with @gltf-transform/{core,functions,extensions} and meshoptimizer
(run  npm install  in construction_site/: see its package.json).
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "neptune" / "manifest.json"
THUMB = 256
BACKGROUND = (238, 240, 243)


def neptune_facts(root: Path):
    """Ids already taken in the twin (downloaded and built in) and its sidebar's categories."""
    library = json.loads((root / "public/library/library.json").read_text())
    taken = {e["id"] for e in library}
    for js in (root / "src").glob("*.js"):
        taken |= set(re.findall(r"\bid:\s*'([a-z0-9-]+)'", js.read_text()))
    src = (root / "src/library.js").read_text()
    order = re.search(r"CATEGORY_ORDER\s*=\s*\[(.*?)\]", src, re.S).group(1)
    return taken, re.findall(r"'([^']+)'", order), {e["id"]: e for e in library}


def thumbnail(src: Path, dst: Path):
    """The studio preview cropped to the model, then fitted (not cut) into a square."""
    im = Image.open(src).convert("RGB")
    px = im.load()
    w, h = im.size
    bg = px[2, 2]
    xs, ys = [], []
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            r, g, b = px[x, y]
            if abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) > 40:
                xs.append(x); ys.append(y)
    if xs:
        pad = 12
        im = im.crop((max(min(xs) - pad, 0), max(min(ys) - pad, 0), min(max(xs) + pad, w), min(max(ys) + pad, h)))
    im.thumbnail((THUMB, THUMB), Image.LANCZOS)
    sq = Image.new("RGB", (THUMB, THUMB), BACKGROUND)
    sq.paste(im, ((THUMB - im.width) // 2, (THUMB - im.height) // 2))
    dst.parent.mkdir(parents=True, exist_ok=True)
    sq.save(dst, "WEBP", quality=80, method=6)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--neptune", type=Path, help="a checkout of the twin, to check ids and categories")
    p.add_argument("--pack", type=int, action="append", help="only these packs (repeatable)")
    p.add_argument("--out", type=Path, default=HERE / "neptune" / "out")
    args = p.parse_args()

    manifest = json.loads(MANIFEST.read_text())
    items = [i for i in manifest["items"] if i["action"] != "skip" and (not args.pack or i["pack"] in args.pack)]
    problems = []
    if args.neptune:
        taken, categories, existing = neptune_facts(args.neptune)
        for i in items:
            if i["action"] == "add" and i["id"] in taken:
                problems.append(f"{i['id']}: marked add, but the twin already has this id")
            if i["action"] == "replace" and i["id"] not in existing:
                problems.append(f"{i['id']}: marked replace, but the twin has no downloaded item with this id")
            if i["category"] not in categories:
                problems.append(f"{i['id']}: category {i['category']!r} is not in the twin's CATEGORY_ORDER")

    sys.path.insert(0, str(HERE))
    import build_assets
    angles = {a.stem: (a.az, a.el) for a in build_assets.all_assets()}
    lib = args.out / "public" / "library"
    if args.out.exists():
        shutil.rmtree(args.out)
    lib.mkdir(parents=True)
    entries, rows, raw_total, out_total = [], [], 0, 0
    for i in items:
        glb = HERE / f"{i['stem']}.glb"
        if not glb.exists():
            problems.append(f"{i['id']}: {glb.name} has not been built yet; left out")
            continue
        r = subprocess.run(["node", str(HERE / "neptune" / "optimize.mjs"), str(glb), str(lib / f"{i['id']}.glb")],
                           capture_output=True, text=True, check=True)
        info = json.loads(r.stdout.strip().splitlines()[-1])
        # one studio style for every card: rendered fresh from the model at its own camera angle
        az, el = angles.get(i["stem"], (35, 20))
        shot = args.out / "renders" / f"{i['id']}.png"
        shot.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["node", str(HERE / "render_previews.mjs"), "--az", str(az), "--el", str(el), "--size", "640x640",
                        "--out", str(shot), str(glb)], capture_output=True, check=True)
        thumbnail(shot, lib / "thumbs" / f"{i['id']}.webp")
        (x0, y0, z0), (x1, y1, z1) = info["min"], info["max"]
        dims = {"length": round(x1 - x0, 2), "width": round(z1 - z0, 2), "height": round(y1 - y0, 2)}
        if abs(y0) > 0.02:
            problems.append(f"{i['id']}: the model's base is at y = {y0:.3f} m, not on the ground")
        entry = {
            "id": i["id"], "name": i["name"], "category": i["category"],
            "file": f"{i['id']}.glb", "thumb": f"thumbs/{i['id']}.webp",
            "front": "+x", "scale": 1, "dimensions": dims,
            "triangles": int(info["triangles"]), "sizeKB": round(info["bytes"] / 1024),
            "source": {"site": "Construction Site packs", "id": i["stem"], "url": manifest["source_url"],
                       "title": i["name"], "author": manifest["author"],
                       "authorUrl": "https://github.com/" + manifest["author"],
                       "license": manifest["license"], "licenseUrl": manifest["source_url"]},
        }
        for k in ("premium", "rowLength", "drive"):
            if k in i:
                entry[k] = i[k]
        if i["action"] == "replace":
            entry["_merge"] = "replace: keep the twin's existing fields this entry does not set (drive, premium)"
        entries.append(entry)
        raw = glb.stat().st_size
        raw_total += raw
        out_total += info["bytes"]
        rows.append(f"| {i['pack']} | `{i['id']}` | {i['action']} | {i['category']} | {dims['length']} x {dims['width']} x "
                    f"{dims['height']} | {raw / 1e6:.2f} -> {info['bytes'] / 1e6:.2f} MB | {int(info['triangles']):,} | "
                    f"{info['draws']} |")
        print(f"{i['id']:32s} {raw / 1e6:5.2f} -> {info['bytes'] / 1e6:5.2f} MB, {info['draws']} draw(s)")

    (args.out / "library-entries.json").write_text(json.dumps(entries, indent="\t", ensure_ascii=False) + "\n")
    report = ["# Neptune staging report", "",
              f"{len(entries)} models staged: {raw_total / 1e6:.1f} MB as built, {out_total / 1e6:.1f} MB for the twin.", "",
              "| Pack | id | Action | Category | L x W x H (m) | Size | Triangles | Draw calls |",
              "|---|---|---|---|---|---|---|---|", *rows, "", "## Problems", ""]
    report += [f"- {x}" for x in problems] or ["None."]
    (args.out / "REPORT.md").write_text("\n".join(report) + "\n")
    print(f"\n{len(entries)} staged, {raw_total / 1e6:.1f} -> {out_total / 1e6:.1f} MB; {len(problems)} problem(s)")
    for x in problems:
        print("  -", x)
    return 0


if __name__ == "__main__":
    sys.exit(main())
