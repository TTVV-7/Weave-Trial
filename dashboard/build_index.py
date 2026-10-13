#!/usr/bin/env python3
"""Find every 3D model in the repo and write dashboard/models.json.

    python dashboard/build_index.py

The dashboard reads that file, so run this after adding or removing a model.
`python dashboard/serve.py` runs it for you before serving.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "models.json"

# extension -> the type the dashboard filters by
TYPES = {
    ".3mf": "3MF",
    ".stl": "STL",
    ".step": "STEP", ".stp": "STEP",
    ".iges": "IGES", ".igs": "IGES",
    ".obj": "OBJ",
    ".glb": "glTF", ".gltf": "glTF",
    ".ply": "PLY",
    ".gcode": "G-code",
}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", ".pytest_cache", "site", "out"}
PREVIEW_EXTS = (".png", ".jpg", ".jpeg", ".webp")


def git_date(path: Path) -> str | None:
    """Last commit date of a file, or None if it isn't committed."""
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cI", "--", str(path.relative_to(ROOT))],
            cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    return out or None


def find_preview(path: Path) -> str | None:
    """An image for the model: <stem>.png or <stem>_preview.png beside it, or a
    folder-wide preview.png when the model is the only one in its folder."""
    names = [path.stem, path.stem + "_preview"]
    siblings = [p for p in path.parent.iterdir() if p.suffix.lower() in TYPES]
    if len(siblings) == 1:
        names.append("preview")
    for stem in names:
        for ext in PREVIEW_EXTS:
            cand = path.with_name(stem + ext)
            if cand.exists():
                return cand.relative_to(ROOT).as_posix()
    return None


def scan() -> list[dict]:
    models = []
    for path in sorted(ROOT.rglob("*")):
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        kind = TYPES.get(path.suffix.lower())
        if kind is None or not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        st = path.stat()
        modified = git_date(path) or datetime.fromtimestamp(
            st.st_mtime, tz=timezone.utc).isoformat(timespec="seconds")
        models.append({
            "name": path.stem.replace("_", " ").replace("-", " "),
            "file": path.name,
            "path": rel.as_posix(),
            "folder": rel.parent.as_posix() if rel.parent != Path(".") else "",
            "ext": path.suffix.lower().lstrip("."),
            "type": kind,
            "size": st.st_size,
            "modified": modified,
            "preview": find_preview(path),
        })
    return models


def main() -> int:
    models = scan()
    OUT.write_text(json.dumps({
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "models": models,
    }, indent=2) + "\n")
    counts: dict[str, int] = {}
    for m in models:
        counts[m["type"]] = counts.get(m["type"], 0) + 1
    summary = ", ".join(f"{n} {t}" for t, n in sorted(counts.items())) or "none"
    print(f"indexed {len(models)} model(s): {summary} -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
