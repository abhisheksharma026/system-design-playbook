from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import build_site
from site_utils import repo_root


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve the system design site locally.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    parser.add_argument(
        "--build",
        action="store_true",
        help="Build the site into dist/ first, then serve dist/.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()

    if args.build:
        build_site.main()
        directory = root / "dist"
    else:
        directory = root

    handler = partial(SimpleHTTPRequestHandler, directory=str(directory))
    server = ThreadingHTTPServer((args.host, args.port), handler)

    print(f"Serving {directory} at http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped server.")
    finally:
        server.server_close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

