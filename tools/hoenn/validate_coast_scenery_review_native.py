"""Run current coastal scenery proofs and the preserved Surf/shore regression.

Every component reads one frozen ROM/ELF. Placements and progress are declared
fixtures; the journeys after placement use controller input. The native query
trampoline exists only in a private temporary ROM, never the shipped artifact.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(source, library, output, parent_source, regression_parent, *, reuse_components=False):
    from validate_coast_scenery_corners import run as corners, verify_report as verify_corners
    from validate_coast_scenery_objects import run as objects, verify_report as verify_objects
    from verify_coast_scenery_review_native import verify_report

    source, library, output, parent_source, regression_parent = [
        Path(p).resolve() for p in (source, library, output, parent_source, regression_parent)]
    output.mkdir(parents=True, exist_ok=True)
    sha, elfsha = digest(source/'pokeemerald.gba'), digest(source/'pokeemerald.elf')
    components = []
    for name, callback, verifier in [('corners', corners, verify_corners), ('objects', objects, verify_objects)]:
        target = output/name
        target.mkdir(parents=True, exist_ok=True)
        file = target/(name+'.json')
        if reuse_components and file.is_file():
            report = json.loads(file.read_bytes())
            verifier(report, target, sha)
        else:
            report = callback(source, library, target, parent_source=parent_source)
        assert report['passed'] is True and report['rom_sha256'] == sha
        assert report['elf_sha256'] == elfsha
        file.write_text(json.dumps(report, indent=2)+'\n')
        components.append(dict(kind=report['kind'], file=file.relative_to(output).as_posix(), sha256=digest(file)))
        print('Current native component passed:', name, flush=True)
    target = output/'surf-regression'
    file = target/'sevii-route-boundaries-native.json'
    if not (reuse_components and file.is_file()):
        subprocess.run([sys.executable, str(ROOT/'tools/hoenn/validate_sevii_route_boundaries_native.py'),
            '--source', str(source), '--library', str(library), '--coldboot-library', str(library),
            '--parent-source', str(regression_parent), '--output', str(target)], check=True)
    regression = json.loads(file.read_bytes())
    assert regression['rom_sha256'] == sha and regression['elf_sha256'] == elfsha
    from verify_sevii_route_boundaries_native import verify_report as verify_regression
    verify_regression(regression, target, sha)
    components.append(dict(kind=regression['kind'], file=file.relative_to(output).as_posix(), sha256=digest(file)))
    assert digest(source/'pokeemerald.gba') == sha and digest(source/'pokeemerald.elf') == elfsha
    result = dict(kind='coast-scenery-review-native', passed=True,
        rom_sha256=sha, elf_sha256=elfsha, components=components,
        complete_objects=True, camera_cases=True, collision_controls=True,
        animation_checks=True, cold_save=True,
        frozen_source_and_artifact_unchanged=True,
        initial_placements_progress_and_encounter_suppression_are_fixtures=True,
        full_campaign_playthrough=False)
    verify_report(result, output, sha)
    (output/'coast-scenery-review-native.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--library', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--parent-source', type=Path, default=ROOT/'.local/sevii-route-boundaries-src')
    parser.add_argument('--regression-parent', type=Path, default=ROOT/'.local/game-continuity-review-src')
    parser.add_argument('--reuse-components', action='store_true', help='Reuse only strictly verified evidence bound to this ROM and ELF')
    args = parser.parse_args()
    run(args.source, args.library, args.output, args.parent_source, args.regression_parent,
        reuse_components=args.reuse_components)
