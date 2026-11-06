"""Reject incomplete, stale or altered current coastal native evidence."""
import hashlib
import json
from pathlib import Path

import coast_scenery_review_contract as contract
from publish_coastal_closures import report_dependencies


def verify_report(report, directory, romsha):
    from validate_coast_scenery_corners import verify_report as verify_corners
    from validate_coast_scenery_objects import verify_report as verify_objects
    from verify_sevii_route_boundaries_native import verify_report as verify_regression

    directory = Path(directory)
    assert report['kind'] == 'coast-scenery-review-native'
    assert report['rom_sha256'] == romsha != contract.PARENT_ROM_SHA256
    assert report['elf_sha256'] != contract.PARENT_ELF_SHA256
    assert len(report['elf_sha256']) == 64
    for name in ('passed', 'complete_objects', 'camera_cases', 'collision_controls',
                 'animation_checks', 'cold_save', 'frozen_source_and_artifact_unchanged',
                 'initial_placements_progress_and_encounter_suppression_are_fixtures'):
        assert report[name] is True, name
    assert report['full_campaign_playthrough'] is False
    rows = report['components']
    assert [r['file'] for r in rows] == [
        'corners/corners.json', 'objects/objects.json', 'surf-regression/sevii-route-boundaries-native.json']
    for row, verifier in zip(rows, (verify_corners, verify_objects, verify_regression)):
        file = directory/row['file']
        assert hashlib.sha256(file.read_bytes()).hexdigest() == row['sha256']
        report_dependencies(file, expected_sha=row['sha256'])
        child = json.loads(file.read_bytes())
        assert child['kind'] == row['kind'] and child['rom_sha256'] == romsha
        assert child['elf_sha256'] == report['elf_sha256']
        verifier(child, file.parent, romsha)
    return True
