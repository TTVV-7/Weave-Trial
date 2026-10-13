#!/usr/bin/env python3
"""Build the dashboard as a standalone static site, for hosting (Vercel).

    python dashboard/build_site.py          # -> site/

The page goes at the site root, and each model (and its preview image) is
copied in at the same path it has in the repo, so nothing else of the repo is
published.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import build_index

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
WEB_FILES = ("index.html", "sw.js", "manifest.webmanifest",
             "icon.svg", "icon-180.png", "icon-192.png", "icon-512.png")


def main(out: Path = ROOT / "site") -> int:
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    for name in WEB_FILES:
        shutil.copy2(HERE / name, out / name)

    models = build_index.scan()
    for m in models:
        for rel in filter(None, (m["path"], m["preview"])):
            dest = out / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, dest)

    # "root": model paths are relative to the page itself here, not to ../
    (out / "models.json").write_text(json.dumps({
        "root": "./",
        "generated": build_index.datetime.now(build_index.timezone.utc).isoformat(timespec="seconds"),
        "models": models,
    }, indent=2) + "\n")
    total = sum(m["size"] for m in models)
    print(f"built {out.relative_to(ROOT)}/ with {len(models)} model(s), {total / 1e6:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
