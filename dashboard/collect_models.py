#!/usr/bin/env python3
"""Copy the 3D models that live on other branches onto this one.

    python dashboard/collect_models.py            # fetch, then copy what's missing
    python dashboard/collect_models.py --dry-run  # just list what it would copy

Each project in this repo was built on its own branch, so the dashboard (which
only sees the checked-out branch) would otherwise miss most of them. Files are
copied to the same path they have on their branch, with any preview images
beside them. Files already here are left alone.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import build_index

ROOT = build_index.ROOT
IMAGE_EXTS = build_index.PREVIEW_EXTS


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                          text=True, check=True).stdout


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-fetch", action="store_true", help="use the remote branches as last fetched")
    args = p.parse_args()

    if not args.no_fetch:
        git("fetch", "--quiet", "origin", "+refs/heads/*:refs/remotes/origin/*")
    current = git("rev-parse", "--abbrev-ref", "HEAD").strip()
    branches = [b for b in git("for-each-ref", "--format=%(refname:short)", "refs/remotes/origin").split()
                if not b.endswith("/HEAD") and b != f"origin/{current}"]

    wanted: dict[str, str] = {}   # path -> branch to take it from
    for branch in branches:
        files = git("ls-tree", "-r", "--name-only", "--full-tree", branch).splitlines()
        models = [f for f in files if Path(f).suffix.lower() in build_index.TYPES]
        model_dirs = {str(Path(f).parent) for f in models}
        for f in files:
            is_model = f in models
            is_preview = Path(f).suffix.lower() in IMAGE_EXTS and str(Path(f).parent) in model_dirs
            if (is_model or is_preview) and f not in wanted and not (ROOT / f).exists():
                wanted[f] = branch

    for path, branch in sorted(wanted.items()):
        print(f"{'would copy' if args.dry_run else 'copy'}  {path}  <- {branch}")
        if args.dry_run:
            continue
        data = subprocess.run(["git", "show", f"{branch}:{path}"], cwd=ROOT,
                              capture_output=True, check=True).stdout
        dest = ROOT / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    print(f"{len(wanted)} file(s) {'to copy' if args.dry_run else 'copied'}")
    if not args.dry_run and wanted:
        build_index.main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
