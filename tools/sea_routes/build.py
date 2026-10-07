#!/usr/bin/env python3
"""Build the sea-route milestone from an already prepared all-region source."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/unova'))
from build import export
from prepare import COMMIT
import importlib.util
spec = importlib.util.spec_from_file_location('sea_prepare', Path(__file__).with_name('prepare.py'))
overlay = importlib.util.module_from_spec(spec); spec.loader.exec_module(overlay)
NAME = 'LeafGreen-Journey-SeaRoutes'
OUT = ROOT / 'mods/sea-routes'

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--jobs', type=int, default=4)
    p.add_argument('--export-only', action='store_true')
    a = p.parse_args(); source = a.source.resolve()
    if subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip() != COMMIT:
        raise ValueError('Wrong pinned source commit')
    report = overlay.prepare(source)
    if not a.export_only:
        env = os.environ.copy()
        env['PATH'] = str(ROOT / '.local/arm-gcc/usr/bin') + os.pathsep + str(ROOT / '.local/arm-binutils/usr/bin') + os.pathsep + env['PATH']
        # This engine's generated assembly dependencies omit changed .bin
        # layouts; force the map assembly to consume the current map blocks.
        subprocess.run(['make', '-W', 'data/maps.s', '-W', 'data/event_scripts.s',
                        '-j' + str(a.jobs), 'GAME_VERSION=LEAFGREEN', 'REVISION=1'], cwd=source, env=env, check=True)
    OUT.mkdir(parents=True, exist_ok=True)
    # Shared catalog package; copied here only for the release's own manifest.
    shutil.copyfile(ROOT / 'mods/all-regions/donor-assets.zip', OUT / 'donor-assets.zip')
    shutil.copyfile(ROOT / 'mods/all-regions/donor-inventory.json', OUT / 'donor-inventory.json')
    export(source, ROOT / '.local/arm-binutils/usr/bin/arm-none-eabi-nm', OUT, NAME,
           ['tools/unova', 'tools/regions', 'tools/journey', 'tools/sea_routes'])
    (OUT / 'routes.json').write_text(json.dumps(report, indent=2) + '\n')
