#!/usr/bin/env python3
"""Serve the browser player locally without duplicating the 32 MB ROM."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / 'web'), **kwargs)

    def translate_path(self, path):
        if path.split('?', 1)[0] == '/games/LeafGreen-Journey-SeaRoutes.gba':
            return str(ROOT / 'mods/sea-routes/LeafGreen-Journey-SeaRoutes.gba')
        requested = path.split('?', 1)[0]
        if requested in ['/games/Pokemon-Journey-World-Alpha-1.gba', '/games/release.json']:
            return str(ROOT / 'mods/hoenn/playable' / requested.rsplit('/', 1)[1])
        if requested == '/START-HERE.md':
            return str(ROOT / 'mods/hoenn/playable/START-HERE.md')
        return super().translate_path(path)

if __name__ == '__main__':
    ThreadingHTTPServer(('127.0.0.1', 8765), Handler).serve_forever()
