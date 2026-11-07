"""Validate every current native component and its complete dependency tree."""
import importlib
import json
from pathlib import Path

import generated_area_review_contract as contract
from publish_coastal_closures import report_dependencies
from validate_generated_area_review_native import PARTS, digest


def verify_report(report, directory, romsha):
    directory = Path(directory)
    assert report['kind'] == 'generated-area-review-native' and report['passed'] is True
    assert report['rom_sha256'] == romsha != contract.PARENT_ROM_SHA256
    elf = report['elf_sha256']
    assert len(elf) == 64 and set(elf) <= set('0123456789abcdef') and elf != contract.PARENT_ELF_SHA256
    for name in ('complete_objects', 'camera_transitions', 'port_surf_roundtrips',
                 'new_vertical_horizontal_connection', 'remaining_cave_exit_and_actors_reachable',
                 'animation_and_battery_continue', 'frozen_source_and_artifact_unchanged',
                 'initial_placements_progress_and_encounter_suppression_are_fixtures'):
        assert report[name] is True, name
    assert report['full_campaign_playthrough'] is False
    expected = [name+'/'+name+'.json' for name, _ in PARTS]+['coast-regression/coast-scenery-review-native.json']
    rows = report['components']
    assert [row['file'] for row in rows] == expected
    modules = [module for _, module in PARTS]+['verify_coast_scenery_review_native']
    for row, module_name in zip(rows, modules):
        file = directory/row['file']
        assert digest(file) == row['sha256']
        report_dependencies(file, expected_sha=row['sha256'])
        child = json.loads(file.read_bytes())
        assert child['kind'] == row['kind'] and child['rom_sha256'] == romsha and child['elf_sha256'] == elf
        importlib.import_module(module_name).verify_report(child, file.parent, romsha)
    return report
