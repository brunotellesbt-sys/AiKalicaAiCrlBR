"""Reject stale or incomplete compiled layer-169 source evidence."""
import hashlib
from pathlib import Path
import re

import sevii_route_boundaries_contract as contract


RUNTIME_SYMBOLS = frozenset({'MapGridGetMetatileIdAt', 'NewGameInitData',
                             'CopyPartyAndObjectsFromSave'})
ROM_START, ROM_END = 0x08000000, 0x0A000000


def _sha(value):
    assert isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value), 'Invalid SHA-256'


def _integer(value, minimum=0):
    assert type(value) is int and value >= minimum, ('Invalid integer', value)


def _rom_range(address, size=1):
    _integer(address)
    _integer(size, 1)
    assert ROM_START <= address < address + size <= ROM_END, ('Invalid ROM span', address, size)


def _relative(name):
    assert isinstance(name, str) and name and '\\' not in name
    path = Path(name)
    assert not path.is_absolute() and '..' not in path.parts and path != Path('.'), ('Unsafe file', name)
    return path


def _true(report, names):
    for name in names:
        assert report[name] is True, ('Required source observation is absent', name)


def verify_report(report, directory, romsha):
    """Verify the finalized report and every optional attachment in its folder."""
    from prepare_sevii_route_boundaries import PRIOR

    directory = Path(directory).resolve()
    assert report['kind'] == 'sevii-route-boundaries-source'
    _true(report, ('passed', 'compiled_rom', 'independent_replay',
                  'prefix_markers_unchanged', 'unrelated_source_files_unchanged',
                  'scripts_and_atlas_art_unchanged'))
    assert report['preflight'] is False
    assert len(PRIOR) == 168 and report['layers'] == PRIOR + [contract.SCOPE]
    assert report['parent_rom_sha256'] == contract.PARENT_ROM_SHA256
    assert contract.PREPARED_SHA256, 'Final Sevii boundary source hashes are not pinned'
    for name, sha in contract.PREPARED_SHA256.items():
        _relative(name)
        _sha(sha)
    assert report['prepared_sha256'] == contract.PREPARED_SHA256
    assert report['changed_files'] == sorted(contract.PREPARED_SHA256), 'Changed source scope differs'
    _sha(romsha)
    _sha(report['rom_sha256'])
    _sha(report['elf_sha256'])
    assert report['rom_sha256'] == romsha != contract.PARENT_ROM_SHA256, 'Stale source ROM'
    assert report['elf_sha256'] != contract.PARENT_ELF_SHA256, 'Stale source ELF'
    _integer(report['source_hashes_checked'], len(contract.PREPARED_SHA256))
    _integer(report['elf_rom_load_segments_checked'], 1)

    audit = report['boundary_audit']
    assert audit['maps'] == 284 and type(audit['maps']) is int
    assert audit['unconnected_water_edges'] == 0 and type(audit['unconnected_water_edges']) is int
    _true(audit, ('connected_openings_preserved', 'complete_small_reefs'))
    names = audit['map_names']
    assert isinstance(names, list) and all(isinstance(name, str) and name for name in names)
    assert len(names) == len(set(names)) == 284, 'Incomplete boundary map census'

    geography = report['geography']
    assert geography['old_dimensions'] == [24, 40] and geography['dimensions'] == [40, 48]
    assert geography['old_cells_preserved'] == 960 and type(geography['old_cells_preserved']) is int
    assert geography['offset'] == [8, 0]
    _true(geography, ('objects_and_warps_preserved', 'geology_preserved'))
    projection = report['projection']
    assert projection['dimensions'] == [40, 48]
    assert projection['old_logical_pixels_preserved'] == 960 and type(projection['old_logical_pixels_preserved']) is int
    _true(projection, ('other_logical_grids_preserved',))
    for name in ('shared_border_maximum_step', 'closed_loop_neighbor_maximum_step'):
        _integer(projection[name])
        assert projection[name] <= 2, ('Discontinuous world projection', name)
    gps = report['compiled_gps']
    assert gps['symbol'] == 'sWorldNavigationPixels'
    _integer(gps['bytes'], 2 * 40 * 48)
    assert gps['bytes'] % 2 == 0
    _rom_range(gps['address'], gps['bytes'])
    _sha(gps['sha256'])

    layouts = report['compiled_layouts']
    assert isinstance(layouts, list) and len(layouts) == 284
    assert len({row['map'] for row in layouts}) == 284 and {row['map'] for row in layouts} == set(names)
    for row in layouts:
        assert isinstance(row['layout'], str) and row['layout']
        assert isinstance(row['symbol'], str) and row['symbol']
        _rom_range(row['address'], 28)
        assert row['address'] % 4 == 0
        _integer(row['width'], 1)
        _integer(row['height'], 1)
        assert type(row['is_frlg']) is bool
        _integer(row['border_width'], 1)
        _integer(row['border_height'], 1)
        assert (row['stored_border_width'],row['stored_border_height']) == (
            (row['border_width'],row['border_height']) if row['is_frlg'] else (0,0))
        for name in ('primary_pointer', 'secondary_pointer'):
            _rom_range(row[name])
            assert row[name] % 4 == 0
        assert row['compiled_layout_bytes_match'] is True
        for name, size in (('blockdata', 2 * row['width'] * row['height']),
                           ('borderdata', 2 * row['border_width'] * row['border_height'])):
            block = row[name]
            path = _relative(block['file'])
            assert path.parts[:2] == ('data', 'layouts') and path.suffix == '.bin'
            _integer(block['bytes'], 1)
            assert block['bytes'] == size, ('Incomplete compiled map data', row['map'], name)
            _sha(block['sha256'])
            _rom_range(block['address'], size)

    exports = report['runtime_export_names']
    assert isinstance(exports, list) and all(isinstance(name, str) and name for name in exports)
    assert len(exports) == len(set(exports)) >= 3 and RUNTIME_SYMBOLS <= set(exports)
    runtime = report['compiled_runtime']
    assert isinstance(runtime, list) and len(runtime) == len(exports)
    assert len({row['symbol'] for row in runtime}) == len(runtime)
    assert {row['symbol'] for row in runtime} == set(exports), 'Missing compiled runtime path'
    for row in runtime:
        _rom_range(row['address'], row['bytes'])
        _sha(row['sha256'])

    limitations = report['camera_limitations']
    assert limitations['full_world_camera_certified'] is False
    _integer(limitations['ambiguous_graph_cells'])
    ambiguous = limitations['ambiguous_graph_maps']
    assert isinstance(ambiguous, list) and all(isinstance(name, str) and name for name in ambiguous)
    assert len(ambiguous) == len(set(ambiguous))
    assert bool(ambiguous) == bool(limitations['ambiguous_graph_cells'])

    captures = report.get('captures', [])
    assert isinstance(captures, list)
    seen = set()
    for row in captures:
        path = _relative(row['file'])
        assert path.as_posix() not in seen, 'Duplicate source attachment'
        seen.add(path.as_posix())
        target = (directory/path).resolve()
        assert target.is_relative_to(directory), ('Attachment escapes report folder', row['file'])
        _sha(row['sha256'])
        assert hashlib.sha256(target.read_bytes()).hexdigest() == row['sha256'], ('Source attachment changed', row['file'])
    return report
