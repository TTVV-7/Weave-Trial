#!/usr/bin/env python3
"""Post a listing folder to Cults3D through its GraphQL API.

    python listings/cults_upload.py listings/construction-site-1-50            # dry run
    python listings/cults_upload.py listings/construction-site-1-50 \
        --base-url https://example.com/listings/construction-site-1-50         # dry run, checks the links
    python listings/cults_upload.py ... --base-url ... --publish               # really posts it
    python listings/cults_upload.py --categories                               # category ids for listing.json

A listing folder holds a listing.json (title, description, price, tags, which
files and images to attach) and the files it names. Cults does not take
uploads: it downloads each file from a public HTTPS link, so the folder has to
be online somewhere first, and --base-url says where. Every link's path must
end in the file's name and extension, and Cults takes at most ten files and
ten images per listing.

Nothing is sent without --publish. A dry run prints the mutation it would send
and checks everything it can locally, and with --base-url it also checks that
each link answers, so the only thing --publish adds is the post itself.

Credentials come from the environment, never from listing.json:

    CULTS_USERNAME   your Cults username
    CULTS_API_KEY    from https://cults3d.com/en/api/keys

The API is documented by Cults only in outline; the mutation here follows
their published example (createCreation with fileUrls and imageUrls). Cults
also asks for madeWithAi on every design, so listing.json must say.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import quote

ENDPOINT = "https://cults3d.com/graphql"
MAX_LINKS = 10
REQUIRED = ("name", "description", "price", "currency", "made_with_ai", "files", "images")

CATEGORIES = "{ categories { id name(locale: EN) } }"


class Bare(str):
    """A GraphQL enum value (EN, EUR), written without quotes."""


def literal(value) -> str:
    """A Python value as a GraphQL literal."""
    if isinstance(value, Bare):
        return str(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(float(value))
    if isinstance(value, list):
        return "[" + ", ".join(literal(v) for v in value) + "]"
    return json.dumps(str(value), ensure_ascii=False)  # JSON string syntax is GraphQL's


def create_mutation(args: dict) -> str:
    """createCreation with its arguments written inline, as in Cults' own example,
    so nothing depends on guessing the schema's names for the variable types."""
    body = "\n".join(f"    {k}: {literal(v)}" for k, v in args.items())
    return ("mutation {\n  createCreation(\n" + body + "\n  ) {\n"
            "    creation { id url(locale: EN) }\n    errors\n  }\n}")


def graphql(query: str, variables: dict | None = None) -> dict:
    user, key = os.environ.get("CULTS_USERNAME"), os.environ.get("CULTS_API_KEY")
    if not user or not key:
        sys.exit("Set CULTS_USERNAME and CULTS_API_KEY (key from https://cults3d.com/en/api/keys).")
    token = base64.b64encode(f"{user}:{key}".encode()).decode()
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        # Cloudflare in front of Cults turns away Python's default User-Agent (error 1010)
        headers={"Content-Type": "application/json", "Authorization": f"Basic {token}",
                 "User-Agent": "cults_upload/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            reply = json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"Cults answered HTTP {e.code}: {e.read()[:500].decode(errors='replace')}")
    if reply.get("errors"):
        sys.exit("Cults rejected the request:\n" + json.dumps(reply["errors"], indent=2))
    return reply["data"]


def link_answers(url: str) -> str | None:
    """None if the link serves something, otherwise why not."""
    req = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return None if r.status == 200 else f"HTTP {r.status}"
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}"
    except urllib.error.URLError as e:
        return str(e.reason)


def load(folder: Path) -> tuple[dict, list[str]]:
    listing = json.loads((folder / "listing.json").read_text())
    problems = [f"listing.json has no {k!r}" for k in REQUIRED if k not in listing]
    for field in ("files", "images"):
        names = listing.get(field, [])
        if not names:
            problems.append(f"no {field} listed")
        if len(names) > MAX_LINKS:
            problems.append(f"{len(names)} {field}; Cults takes at most {MAX_LINKS}, zip some together")
        for name in names:
            if not (folder / name).is_file():
                problems.append(f"{field}: {name} is not in {folder}")
    if not isinstance(listing.get("made_with_ai"), bool):
        problems.append("made_with_ai must be true or false")
    for field in ("currency", "locale"):  # sent unquoted, as GraphQL enum values
        if field in listing and not re.fullmatch(r"[A-Z]{2,3}", str(listing[field])):
            problems.append(f"{field} must be a code like USD or EN, not {listing[field]!r}")
    return listing, problems


def arguments(listing: dict, base_url: str) -> dict:
    url = lambda name: f"{base_url.rstrip('/')}/{quote(name)}"
    v = {
        "name": listing["name"],
        "description": listing["description"],
        "imageUrls": [url(n) for n in listing["images"]],
        "fileUrls": [url(n) for n in listing["files"]],
        "locale": Bare(listing.get("locale", "EN")),
        "downloadPrice": float(listing["price"]),
        "currency": Bare(listing["currency"]),
        "tagNames": listing.get("tags", []),
        "madeWithAi": listing["made_with_ai"],
    }
    for key, field in (("categoryId", "category_id"), ("subCategoryIds", "sub_category_ids"),
                       ("licenseCode", "license_code")):
        if listing.get(field):
            v[key] = listing[field]
    return v


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("folder", nargs="?", type=Path, help="a listing folder holding listing.json")
    ap.add_argument("--base-url", help="public HTTPS address the folder's files are served from")
    ap.add_argument("--publish", action="store_true", help="really create the listing on Cults")
    ap.add_argument("--categories", action="store_true", help="list Cults category ids and exit")
    args = ap.parse_args()

    if args.categories:
        for c in graphql(CATEGORIES)["categories"]:
            print(f"{c['id']}  {c['name']}")
        return
    if not args.folder:
        ap.error("give a listing folder, or --categories")

    listing, problems = load(args.folder)
    base = args.base_url or "https://YOUR-HOST/" + args.folder.name
    v = arguments(listing, base) if not problems else {}

    if args.base_url and not problems:
        for link in v["fileUrls"] + v["imageUrls"]:
            if why := link_answers(link):
                problems.append(f"{link} does not answer ({why})")

    print(f"{listing.get('name', args.folder.name)}")
    print(f"  {listing.get('price')} {listing.get('currency')}, "
          f"{len(listing.get('files', []))} files, {len(listing.get('images', []))} images, "
          f"made with AI: {listing.get('made_with_ai')}")
    if problems:
        print("  NOT READY")
        for p in problems:
            print(f"    - {p}")
        sys.exit(1)

    if not args.publish:
        print("  ready. Dry run, nothing sent. This is what --publish would send:\n")
        print(create_mutation(v))
        if not args.base_url:
            print("\n  (links are placeholders: pass --base-url to check the real ones)")
        return
    if not args.base_url:
        sys.exit("--publish needs --base-url: Cults downloads the files from there.")

    result = graphql(create_mutation(v))["createCreation"]
    if result.get("errors"):
        sys.exit("Cults refused it:\n  " + "\n  ".join(map(str, result["errors"])))
    print(f"  posted: {result['creation']['url']}")


if __name__ == "__main__":
    main()
