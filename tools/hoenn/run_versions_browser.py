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
from stage_pages import CURRENT_BROWSER_EVIDENCE, VERSIONS, stage_current_editions


def run():
    base = verify(VERSIONS)
    with tempfile.TemporaryDirectory(prefix='journey-browser-') as temporary:
        site = Path(temporary)
        shutil.copytree(ROOT / 'web', site, dirs_exist_ok=True)
        release, review = stage_current_editions(site, base)
        report = CURRENT_BROWSER_EVIDENCE if 'atlas' in release else ROOT / 'mods/hoenn/versions-validation/browser/browser-versions.json'
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(site))
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            environment = dict(os.environ, PLAYABLE_SITE_URL=f'http://127.0.0.1:{server.server_port}/',
                               PLAYABLE_GAMES_DIR=str(site / 'games'),
                               BROWSER_VALIDATION_OUTPUT=str(report.parent))
            subprocess.run(['node', str(ROOT / 'tools/hoenn/validate_versions_browser.cjs')],
                           env=environment, check=True, timeout=420)
            verify_browser(release, review=review, report_path=report)
        finally:
            server.shutdown()
            worker.join()
            server.server_close()


if __name__ == '__main__':
    run()
