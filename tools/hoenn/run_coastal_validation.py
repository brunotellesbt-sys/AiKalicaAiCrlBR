"""Run named native checks against frozen edition bytes, then bind components.

Every subprocess owns its emulator. The source, ELF and ROMs are read-only;
the review-mode check explicitly exports the separate TESTE battery save.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
GROUPS = ('boot', 'six', 'dewford', 'shore', 'route', 'connections')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def assemble(output, editions):
    for edition in editions:
        directory = output / edition['edition']
        components = []
        for kind, relative in [
            ('integrated-piers', 'connections/ports/integrated-piers.json'),
            ('ocean-seams', 'connections/ocean/ocean-seams.json'),
            ('coastal-route-identity', 'route/route-identity.json'),
        ]:
            path = directory / relative
            report = json.loads(path.read_text())
            assert report['passed'] is True and report['rom_sha256'] == edition['sha256'], path
            assert report['review_mode'] is (edition['edition'] == 'TESTE'), path
            components.append(dict(kind=kind, file=relative, sha256=digest(path)))
        report = dict(passed=True, kind='affected-coast-connections',
                      rom_sha256=edition['sha256'], review_mode=edition['edition'] == 'TESTE',
                      components_bound_to_current_rom=True,
                      player_movement_uses_controller_input=True,
                      no_midcrossing_warps_or_coordinate_or_elevation_writes=True,
                      components=components)
        (directory / 'affected-coast-connections.json').write_text(json.dumps(report, indent=2) + '\n')


def run(args):
    frozen = json.loads(args.frozen.read_text())
    editions = frozen['editions']
    if args.editions:
        names = set(args.editions.split(','))
        editions = [row for row in editions if row['edition'] in names]
        assert {row['edition'] for row in editions} == names, 'Unknown edition'
    assert editions
    assert 1 <= args.jobs <= 6
    parent = Path(frozen['parent_source'])
    assert digest(parent / 'pokeemerald.gba') == frozen['parent_rom_sha256']
    initial_elf_sha = digest(parent / 'pokeemerald.elf')
    if 'parent_elf_sha256' in frozen:
        assert initial_elf_sha == frozen['parent_elf_sha256']
    for edition in editions:
        assert digest(Path(edition['source']) / 'pokeemerald.gba') == edition['sha256']
    selected = args.groups.split(',') if args.groups else []
    assert len(selected) == len(set(selected)) and set(selected) <= set(GROUPS)
    logs = args.output / 'logs'
    logs.mkdir(parents=True, exist_ok=True)

    def task(edition, group):
        source = Path(edition['source'])
        directory = args.output / edition['edition']
        directory.mkdir(parents=True, exist_ok=True)
        assert digest(source / 'pokeemerald.gba') == edition['sha256']

        def invoke(script, destination=directory, library=args.library, extra=()):
            command = [sys.executable, str(ROOT / 'tools/hoenn' / script),
                       '--source', str(source), '--library', str(library.resolve()),
                       '--output', str(destination), *map(str, extra)]
            log = logs / (edition['edition'] + '-' + script.removesuffix('.py') + '.log')
            with log.open('w') as stream:
                subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, check=True)

        if group == 'boot':
            invoke('validate_review_mode.py')
            battery = ['--battery', ROOT / 'roms/rom-de-teste/Pokemon-Journey-TESTE.sav'] if edition['edition'] == 'TESTE' else []
            invoke('validate_cold_boot.py', library=args.cold_boot_library, extra=battery)
        elif group == 'six':
            invoke('validate_coastal_six.py', extra=['--baseline', args.baseline.resolve()])
        elif group == 'dewford':
            invoke('validate_coastal_dewford.py', extra=['--baseline', args.baseline.resolve()])
        elif group == 'shore':
            invoke('validate_coastal_shore_animation.py', directory / 'shore')
        elif group == 'route':
            invoke('validate_coastal_route_identity.py', directory / 'route')
        elif group == 'connections':
            video = ['--video'] if args.video and edition['edition'] == 'Gen1-9-Normal' else []
            invoke('validate_integrated_piers.py', directory / 'connections/ports', extra=video)
            invoke('validate_integrated_ocean_seams.py', directory / 'connections/ocean')
        assert digest(source / 'pokeemerald.gba') == edition['sha256']
        return dict(edition=edition['edition'], group=group, passed=True, rom_sha256=edition['sha256'])

    results = []
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = {pool.submit(task, edition, group): (edition['edition'], group)
                   for group in selected for edition in editions}
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(json.dumps(result), flush=True)
    assert digest(parent / 'pokeemerald.elf') == initial_elf_sha
    assert digest(parent / 'pokeemerald.gba') == frozen['parent_rom_sha256']
    if args.assemble:
        assemble(args.output, editions)
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frozen', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--groups', default='boot,six,dewford,shore,route,connections')
    parser.add_argument('--editions', help='Comma-separated subset; default: all frozen editions')
    parser.add_argument('--jobs', type=int, default=2)
    parser.add_argument('--library', type=Path, default=ROOT / '.local/mgba-review.so')
    parser.add_argument('--cold-boot-library', type=Path, default=ROOT / '.local/mgba-coldboot.so')
    parser.add_argument('--baseline', type=Path, default=ROOT / '.local/sevii-integrated-src')
    parser.add_argument('--video', action='store_true')
    parser.add_argument('--assemble', action='store_true')
    options = parser.parse_args()
    run(options)
