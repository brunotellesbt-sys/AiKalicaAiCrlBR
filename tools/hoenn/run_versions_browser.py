"""Test current verified ROMs on a private temporary site before Pages staging."""
import functools
import http.server
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading

from verify_versions import ROOT, verify, verify_browser


def run():
    versions = ROOT / 'mods/hoenn/versions'
    release = verify(versions)
    with tempfile.TemporaryDirectory(prefix='journey-browser-') as temporary:
        site = Path(temporary)
        shutil.copytree(ROOT / 'web', site, dirs_exist_ok=True)
        games = site / 'games'
        games.mkdir(exist_ok=True)
        shutil.copyfile(versions / 'versions.json', games / 'versions.json')
        for row in release['variants']:
            (games / row['file']).symlink_to(versions / row['file'])
        if release.get('validation_scope') in ('extra-gyms','dewford-coast-safety','generated-world-audit','badge-story','coastal-closures','sevii-integrated-piers'):
            review=ROOT/'roms/rom-de-teste'
            for name in ['Pokemon-Journey-TESTE.gba','review.json']:
                (games/name).symlink_to(review/name)
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(site))
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            environment = dict(os.environ, PLAYABLE_SITE_URL=f'http://127.0.0.1:{server.server_port}/')
            subprocess.run(['node', str(ROOT / 'tools/hoenn/validate_versions_browser.cjs')],
                           env=environment, check=True, timeout=420)
            verify_browser(release)
        finally:
            server.shutdown()
            worker.join()
            server.server_close()


if __name__ == '__main__':
    run()
