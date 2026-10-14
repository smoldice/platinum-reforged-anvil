#!/usr/bin/env python3
"""Serves the built site (anvil/dist/site) on this machine, to try it before it's deployed:
  .venv/Scripts/python anvil/web/serve.py [PORT]        (default 8765; http://127.0.0.1:8765/)
For dev.js (make_site.py --dev), /dev-roms/NAME serves "original nds roms/NAME", so a test can load the ROMs without
a file dialog. Only on 127.0.0.1: the ROMs never leave this machine."""
import functools
import http.server
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "anvil" / "dist" / "site"
ROMS = ROOT / "original nds roms"


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, ".js": "text/javascript",
                      ".zip": "application/zip", ".nds": "application/octet-stream"}

    def translate_path(self, path):
        path = unquote(path.split("?", 1)[0])
        if path.startswith("/dev-roms/"):
            name = Path(path[len("/dev-roms/"):]).name
            return str(ROMS / name)
        return super().translate_path(path)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    handler = functools.partial(Handler, directory=str(SITE))
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as server:
        print(f"http://127.0.0.1:{port}/", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
