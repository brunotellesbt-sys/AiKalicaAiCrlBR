"""Exercise current repaired areas and retain the previous coastal regression."""
import argparse
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
PARTS = (('coast', 'validate_generated_coast_cameras'),
         ('caves', 'validate_generated_cave_portals'),
         ('ports', 'validate_port_boundary_scenery'),
         ('south', 'validate_one_south_surf_link'))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(source, library, output, parent_source, *, reuse_components=False):
    from verify_generated_area_review_native import verify_report
    source, library, output, parent_source = [Path(p).resolve() for p in (source, library, output, parent_source)]
    output.mkdir(parents=True, exist_ok=True)
    sha, elfsha = digest(source/'pokeemerald.gba'), digest(source/'pokeemerald.elf')
    rows = []
    for name, module_name in PARTS:
        module = importlib.import_module(module_name)
        target = output/name
        target.mkdir(parents=True, exist_ok=True)
        file = target/(name+'.json')
        if reuse_components and file.is_file():
            report = json.loads(file.read_bytes())
        else:
            report = module.run(source, library, target, parent_source=parent_source)
        module.verify_report(report, target, sha)
        assert report['passed'] is True and report['rom_sha256'] == sha and report['elf_sha256'] == elfsha
        file.write_text(json.dumps(report, indent=2)+'\n')
        rows.append(dict(kind=report['kind'], file=file.relative_to(output).as_posix(), sha256=digest(file)))
        print('Current generated-area component passed:', name, flush=True)
    target = output/'coast-regression'
    file = target/'coast-scenery-review-native.json'
    if not (reuse_components and file.exists()):
        subprocess.run([sys.executable, str(ROOT/'tools/hoenn/validate_coast_scenery_review_native.py'),
            '--source', str(source), '--library', str(library), '--output', str(target)], check=True)
    from verify_coast_scenery_review_native import verify_report as verify_regression
    regression = json.loads(file.read_bytes())
    verify_regression(regression, target, sha)
    assert regression['elf_sha256'] == elfsha
    rows.append(dict(kind=regression['kind'], file=file.relative_to(output).as_posix(), sha256=digest(file)))
    assert digest(source/'pokeemerald.gba') == sha and digest(source/'pokeemerald.elf') == elfsha
    report = dict(kind='generated-area-review-native', passed=True, rom_sha256=sha, elf_sha256=elfsha,
        components=rows, complete_objects=True, camera_transitions=True, port_surf_roundtrips=True,
        new_vertical_horizontal_connection=True, remaining_cave_exit_and_actors_reachable=True,
        animation_and_battery_continue=True, frozen_source_and_artifact_unchanged=True,
        initial_placements_progress_and_encounter_suppression_are_fixtures=True,
        full_campaign_playthrough=False)
    verify_report(report, output, sha)
    (output/'generated-area-review-native.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--library', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--parent-source', type=Path, default=ROOT/'.local/coast-scenery-review-src')
    parser.add_argument('--reuse-components', action='store_true')
    args = parser.parse_args()
    run(args.source, args.library, args.output, args.parent_source, reuse_components=args.reuse_components)
