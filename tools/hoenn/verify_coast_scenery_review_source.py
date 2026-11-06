"""Reject stale, partial or unbound layer-170 source evidence."""
import hashlib
from pathlib import Path

import coast_scenery_review_contract as contract
from verify_sevii_route_boundaries_source import _sha, _integer, _rom_range, _relative, _true

RUNTIME_SYMBOLS = frozenset({'MapGridGetMetatileIdAt', 'NewGameInitData',
                            'CopyPartyAndObjectsFromSave', 'TrySpawnObjectEvents'})


def verify_report(report, directory, romsha):
    from prepare_coast_scenery_review import PRIOR
    directory = Path(directory).resolve()
    assert report['kind'] == 'coast-scenery-review-source'
    _true(report, ('passed', 'compiled_rom', 'independent_replay', 'prefix_markers_unchanged',
                  'unrelated_source_files_unchanged', 'scripts_and_atlas_art_unchanged',
                  'source_gallery_not_emulator'))
    assert report['preflight'] is False
    assert len(PRIOR) == 169 and report['layers'] == PRIOR+[contract.SCOPE]
    assert report['parent_rom_sha256'] == contract.PARENT_ROM_SHA256
    assert contract.PREPARED_SHA256, 'Final coast scenery source hashes are not pinned'
    for name, sha in contract.PREPARED_SHA256.items():
        _relative(name)
        _sha(sha)
    assert report['prepared_sha256'] == contract.PREPARED_SHA256
    assert report['changed_files'] == sorted(contract.PREPARED_SHA256)
    _sha(romsha)
    _sha(report['rom_sha256'])
    _sha(report['elf_sha256'])
    assert report['rom_sha256'] == romsha != contract.PARENT_ROM_SHA256, 'Stale source ROM'
    assert report['elf_sha256'] != contract.PARENT_ELF_SHA256, 'Stale source ELF'
    _integer(report['source_hashes_checked'], len(contract.PREPARED_SHA256))
    _integer(report['elf_rom_load_segments_checked'], 1)

    geometry = report['geometry_audit']
    assert type(geometry['maps']) is int and geometry['maps'] == 284
    names = geometry['map_names']
    assert isinstance(names, list) and all(isinstance(name, str) and name for name in names)
    assert names == sorted(set(names)) and len(names) == 284
    _true(geometry, ('no_dry_land_changed', 'all_map_metadata_unchanged', 'all_borders_unchanged'))
    assert geometry['only_reviewed_primary_banks_changed'] is True
    banks = geometry['bank_alignment']
    assert [r['map'] for r in banks] == ['JourneyWorldSea06', 'JourneyWorldSea07']
    for row in banks:
        assert (row['before'], row['after']) == ('gTileset_General_Frlg', 'gTileset_JourneySeviiSea')
        _true(row, ('every_existing_primary_metatile_identical', 'secondary_bank_unchanged',
                    'dimensions_events_connections_and_own_terrain_unchanged'))
        mids = row['used_primary_ids']
        assert mids and mids == sorted(set(mids))
        assert all(type(mid) is int and 0 <= mid < 640 for mid in mids)
        assert not {0x110, 0x111, 0x118, 0x119}.intersection(mids)
        _sha(row['used_metatiles_sha256'])
        assert row['shared_symbols'] == dict(isCompressed='TRUE', isSecondary='FALSE',
            tiles='gTilesetTiles_General_Frlg', palettes='gTilesetPalettes_General_Frlg',
            metatileAttributes='gMetatileAttributes_General_Frlg', callback='InitTilesetAnim_General_Frlg')
        for key in ('original_metatiles', 'selected_metatiles'):
            _relative(row[key]['file'])
            _sha(row[key]['sha256'])
    changed = geometry['changed_maps']
    assert isinstance(changed, list) and changed == sorted(set(changed)) and set(changed) <= set(names)
    assert changed
    cells = geometry['cells']
    _integer(geometry['changed_cells'], 1)
    assert len(cells) == geometry['changed_cells']
    seen = set()
    for row in cells:
        assert row['map'] in changed
        assert isinstance(row['cell'], list) and len(row['cell']) == 2
        for value in row['cell']:
            _integer(value)
        for key in ('before', 'after'):
            _integer(row[key])
            assert row[key] <= 65535
        assert row['before'] != row['after']
        key = row['map'], *row['cell']
        assert key not in seen, 'Duplicate changed geometry cell'
        seen.add(key)
    assert {row['map'] for row in cells} == set(changed)

    scenery = report['scenery_audit']
    _true(scenery, ('all_collision_and_elevation_preserved',
                    'all_cells_outside_reviewed_changes_unchanged',
                    'native_edge_cells_authenticated_by_parent_marker'))
    _integer(scenery['whole_replaced_objects'], 37)
    assert len(scenery['objects']) == scenery['whole_replaced_objects']
    anchors = set()
    for row in scenery['objects']:
        assert row['map'] in changed and row['whole_footprint'] is True
        assert len(row['anchor']) == 2
        key = row['map'], *row['anchor']
        assert key not in anchors
        anchors.add(key)
        assert len(row['before']) == len(row['after']) == len(row['family']) == 4
        assert set(value & 1023 for value in row['after']) == {0x243}
        assert all(a & ~1023 == b & ~1023 for a, b in zip(row['before'], row['after']))
    restored = scenery['restored_native_edge_cells']
    assert len(restored) >= 72, 'Incomplete wet-cliff/shore source restoration'
    for row in restored:
        assert (row['map'], *row['cell']) in seen
        assert row['after'] & 1023 == row['native_pre169_word'] & 1023
        assert row['before'] & ~1023 == row['after'] & ~1023

    actor = report['permanent_scenery']
    _true(actor, ('only_dedicated_scenery', 'original_identity_preserved',
                  'event_templates_unchanged', 'native_spawn_and_unload_preserved'))
    assert actor['cardinal_transforms_checked'] == 4
    assert (actor['map'], actor['local_id'], actor['cell']) == ('OneIsland_Frlg', 4, [0, 7])
    camera = report['camera_runtime']
    assert camera['dedicated_primary'] == 'gTileset_JourneySeviiSea'
    assert camera['map_type'] == 'MAP_TYPE_OCEAN_ROUTE'
    _true(camera, ('visual_queries_only', 'collision_elevation_and_movement_code_unchanged',
                   'compatible_art_and_undefined_grid_rules_unchanged'))
    census = report['boulder_census']
    assert census['maps'] == 284 and census['map_names'] == names
    _true(census, ('inherited_context_patterns_preserved', 'source_census_not_native_camera_proof'))
    assert census['new_partial_objects'] == census['mixed_small_and_large_objects'] == 0
    assert isinstance(census['objects'], list) and census['objects']
    assert census['family_metatiles'] == [
        [0x110, 0x111, 0x118, 0x119], [0x1CB, 0x1CC, 0x1D3, 0x1D4],
        [0x212, 0x213, 0x21A, 0x21B], [0x244, 0x245, 0x24C, 0x24D],
        [0x25E, 0x25F, 0x24C, 0x24D], [0x150, 0x151, 0x158, 0x159]]
    from collections import Counter
    counts = Counter(row['classification'] for row in census['objects'])
    assert dict(counts) == census['classifications']
    assert set(counts) <= {'complete', 'native_context_variant', 'outer_continuation'}
    assert all(row['map'] in names and len(row['metatiles']) == len(row['cells']) == 4 for row in census['objects'])
    corners = report['corner_audit']
    assert corners['before_ambiguous_cells'] == 107 and corners['after_ambiguous_cells'] == 0
    _true(corners, ('all_actual_candidates_agree', 'movement_boundaries_and_runtime_unchanged'))
    assert corners['full_world_camera_certified'] is False
    navigation = report['surface_navigation']
    _true(navigation, ('surf_components_preserved', 'no_new_surf_passages', 'all_existing_water_connections_open',
                       'all_surviving_cells_retain_global_connectivity'))
    assert navigation['network_maps'] == sorted(set(navigation['network_maps']))
    assert set(names) <= set(navigation['network_maps'])
    assert len(navigation['network_maps']) == navigation['network_maps_checked']
    _integer(navigation['global_components_before'], 1)
    assert navigation['global_components_before'] == navigation['global_components_after']
    assert sorted(row['map'] for row in navigation['component_maps']) == changed
    for row in navigation['component_maps']:
        assert row['before_component_sizes'] and row['after_component_sizes']
        assert len(row['before_component_sizes']) == row['retained_local_components']
        for size in row['before_component_sizes']+row['after_component_sizes']:
            _integer(size, 1)
        _integer(row['removed_water_cells'])
        assert sum(row['before_component_sizes'])-sum(row['after_component_sizes']) == row['removed_water_cells']
    _integer(navigation['physical_connections_checked'], 1)
    assert len(navigation['physical_connections']) == navigation['physical_connections_checked']
    for row in navigation['physical_connections']:
        assert row['map'] in navigation['network_maps'] and isinstance(row['target'], str) and row['target']
        assert row['direction'] in {'up', 'down', 'left', 'right'}
        _integer(row['before_openings'], 1)
        _integer(row['after_openings'], 1)

    layouts = report['compiled_layouts']
    assert isinstance(layouts, list) and len(layouts) == 284
    assert {row['map'] for row in layouts} == set(names)
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
        assert (row['stored_border_width'], row['stored_border_height']) == (
            (row['border_width'], row['border_height']) if row['is_frlg'] else (0, 0))
        for key in ('primary_pointer', 'secondary_pointer'):
            _rom_range(row[key])
            assert row[key] % 4 == 0
        assert row['compiled_layout_bytes_match'] is True
        for key, size in (('blockdata', 2*row['width']*row['height']),
                          ('borderdata', 2*row['border_width']*row['border_height'])):
            binding = row[key]
            path = _relative(binding['file'])
            assert path.parts[:2] == ('data', 'layouts') and path.suffix == '.bin'
            assert binding['bytes'] == size
            _sha(binding['sha256'])
            _rom_range(binding['address'], size)
    projection = report['compiled_gps']
    assert projection['symbol'] == 'sWorldNavigationPixels'
    _integer(projection['bytes'], 2*40*48)
    assert projection['bytes'] % 2 == 0
    _rom_range(projection['address'], projection['bytes'])
    _sha(projection['sha256'])
    exports = report['runtime_export_names']
    assert isinstance(exports, list) and len(exports) == len(set(exports))
    assert set(exports) == RUNTIME_SYMBOLS
    runtime = report['compiled_runtime']
    assert len(runtime) == len(exports) and {row['symbol'] for row in runtime} == set(exports)
    for row in runtime:
        _rom_range(row['address'], row['bytes'])
        _sha(row['sha256'])

    reviewed = report['reviewed_maps']
    assert isinstance(reviewed, list) and reviewed == sorted(set(reviewed))
    assert set(changed) | {actor['map']} <= set(reviewed)
    captures = report['captures']
    assert isinstance(captures, list) and type(report['source_gallery_rendered']) is bool
    files, views = set(), set()
    for row in captures:
        path = _relative(row['file'])
        assert path.as_posix() not in files, 'Duplicate source attachment'
        files.add(path.as_posix())
        _sha(row['sha256'])
        target = (directory/path).resolve()
        assert target.is_relative_to(directory), 'Source attachment escaped report directory'
        assert hashlib.sha256(target.read_bytes()).hexdigest() == row['sha256'], 'Source attachment changed'
        assert row['map'] in reviewed and row['phase'] in {'before', 'after'}
        _true(row, ('full_map', 'npcs', 'source_render_not_emulator', 'label_present'))
        _integer(row['width_tiles'], 1)
        _integer(row['height_tiles'], 1)
        key = row['phase'], row['map']
        assert key not in views
        views.add(key)
    assert views == ({(phase, name) for phase in ('before', 'after') for name in reviewed}
                     if report['source_gallery_rendered'] else set())
    return report
