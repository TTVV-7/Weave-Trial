#!/usr/bin/env python3
"""Re-index the models and serve the dashboard.

    python dashboard/serve.py            # http://localhost:8000/dashboard/
    python dashboard/serve.py --port 9000

The repo root is served (not just this folder) so the dashboard can load and
download the model files where they live.
"""

from __future__ import annotations

import argparse
import functools
import http.server
from pathlib import Path

import build_index

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--host", default="127.0.0.1")
    args = p.parse_args()

    build_index.main()
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    with http.server.ThreadingHTTPServer((args.host, args.port), handler) as srv:
        print(f"dashboard at http://{args.host}:{args.port}/dashboard/  (ctrl-c to stop)")
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
