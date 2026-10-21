#!/usr/bin/env python3
"""Build the dashboard as a standalone static site, for hosting (Vercel).

    python dashboard/build_site.py          # -> site/

The page goes at the site root, and each model (and its preview image) is
copied in at the same path it has in the repo, so nothing else of the repo is
published.

When BLOB_READ_WRITE_TOKEN is set (a Vercel Blob store is connected to the
project), the model files are left out of the site instead: each one is listed
in site/blob-manifest.json under a content-addressed Blob pathname for
upload_blobs.mjs to upload, and the page fetches it through api/file. Only the
preview images are copied, which keeps each deployment to a few megabytes.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from urllib.parse import quote

import build_index

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
WEB_FILES = ("index.html", "sw.js", "manifest.webmanifest",
             "icon.svg", "icon-180.png", "icon-192.png", "icon-512.png")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(out: Path = ROOT / "site") -> int:
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    for name in WEB_FILES:
        shutil.copy2(HERE / name, out / name)

    models = build_index.scan()
    use_blob = bool(os.environ.get("BLOB_READ_WRITE_TOKEN"))
    uploads = []
    for m in models:
        copies = [m["preview"]]
        if use_blob:
            pathname = f"models/{sha256(ROOT / m['path'])[:16]}/{m['path']}"
            m["url"] = f"api/file?pathname={quote(pathname)}"
            uploads.append({"path": m["path"], "pathname": pathname, "size": m["size"]})
        else:
            copies.append(m["path"])
        for rel in filter(None, copies):
            dest = out / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, dest)
    if use_blob:
        (out / "blob-manifest.json").write_text(json.dumps(uploads, indent=2) + "\n")

    # "root": model paths are relative to the page itself here, not to ../
    (out / "models.json").write_text(json.dumps({
        "root": "./",
        "generated": build_index.datetime.now(build_index.timezone.utc).isoformat(timespec="seconds"),
        "models": models,
    }, indent=2) + "\n")
    total = sum(m["size"] for m in models)
    where = "in Vercel Blob" if use_blob else "copied in"
    print(f"built {out.relative_to(ROOT)}/ with {len(models)} model(s), {total / 1e6:.1f} MB {where}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
