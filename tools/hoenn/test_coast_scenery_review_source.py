"""Negative controls for whole reefs, authenticated edges and world connectivity."""
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import coast_scenery_review_contract as contract
import validate_coast_scenery_review_source as source
from verify_coast_scenery_review_source import verify_report


class World:
    def __init__(self, directory, grids):
        self.source = Path(directory)
        self.maps, self.layouts, self.words = {}, {}, {}
        for name, (width, height, words) in grids.items():
            self.maps[name] = dict(id='MAP_'+name, layout=name, connections=[])
            self.layouts[name] = dict(id=name, width=width, height=height,
                layout_version='frlg', primary_tileset='gTileset_JourneySeviiSea',
                border_filepath='border.bin', blockdata_filepath=name+'/map.bin')
            self.words[name] = list(words)
        self.by_id = {mapping['id']: name for name, mapping in self.maps.items()}
        (self.source/'border.bin').write_bytes(b'unchanged border')
        self.water = {1}

    def layout(self, name): return self.layouts[self.maps[name]['layout']]
    def grid(self, name): return self.words[name]
    def word(self, name, x, y):
        layout = self.layout(name)
        assert 0 <= x < layout['width'] and 0 <= y < layout['height']
        return self.words[name][y*layout['width']+x]
    def behavior(self, name, word): return int(word & 1023 == 0x12B)
    perimeter = source.Inputs.perimeter
    target = source.Inputs.target


class IndependentGeometryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='coast-source-test-', dir='/tmp')
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def world(self, grids): return World(self.root, grids)

    def test_family_census_finds_round_angled_and_cliff_attached_partial_reefs(self):
        for family in source.FRLG_FAMILIES:
            with self.subTest(family=family):
                words = [0x1400 | mid for mid in family]
                old = self.world({'Reef': (2, 2, words)})
                current = copy.deepcopy(old)
                current.words['Reef'][1] = current.words['Reef'][3] = 0x1643
                rows = source.boulder_patterns(current, ['Reef'])
                self.assertTrue(any(row['classification'] == 'mixed_small_and_large' for row in rows))
                with self.assertRaises(AssertionError):
                    source.check_boulders(current, old, ['Reef'])

    def test_complete_cliff_attached_object_and_high_bit_variants_pass(self):
        old = self.world({'Reef': (2, 2, [0x165E, 0x065F, 0x164C, 0x564D])})
        report = source.check_boulders(old, old, ['Reef'])
        self.assertEqual(report['classifications'], {'complete': 1})
        self.assertEqual(len(report['objects']), 1)

    def repaired_objects(self):
        width, name = 148, 'OneIsland_KindleRoad_Frlg'
        words = [0x112B]*(width*2)
        for number in range(37):
            x = number*4
            for at, mid in enumerate((0x110, 0x243, 0x118, 0x243)):
                words[(at//2)*width+x+at%2] = (0x1400 if at % 2 else 0x0400) | mid
        old = self.world({name: (width, 2, words)})
        current = copy.deepcopy(old)
        for number in range(37):
            for at in range(4):
                index = at//2*width+number*4+at%2
                current.words[name][index] = (words[index] & ~1023) | 0x243
        return old, current, name

    def test_whole_footprint_checks_preserve_every_collision_and_elevation_bit(self):
        old, current, name = self.repaired_objects()
        geometry, scenery = source.check_geometry(current, old, [name])
        self.assertEqual(scenery['whole_replaced_objects'], 37)
        self.assertEqual(geometry['changed_cells'], 74)
        current.words[name][0] ^= 0x1000
        with self.assertRaisesRegex(AssertionError, 'collision/elevation'):
            source.check_geometry(current, old, [name])

    def test_authentic_parent_donor_required_for_cliff_restoration(self):
        old, current, name = self.repaired_objects()
        at = 147
        old.words[name][at] = 0x1643
        current.words[name][at] = 0x1664
        geometry, scenery = source.check_geometry(current, old, [name], {(name, at, 0): (0x1264, 0x1643)})
        self.assertEqual(len(scenery['restored_native_edge_cells']), 1)
        with self.assertRaisesRegex(AssertionError, 'authenticated'):
            source.check_geometry(current, old, [name], {(name, at, 0): (0x1265, 0x1643)})

    def test_world_connectivity_accepts_neighbor_detour_and_rejects_real_split(self):
        old = self.world({'A': (3, 2, [0x112B]*6), 'B': (3, 1, [0x112B]*3)})
        old.maps['A']['connections'] = [dict(direction='down', offset=0, map='MAP_B')]
        old.maps['B']['connections'] = [dict(direction='up', offset=0, map='MAP_A')]
        current = copy.deepcopy(old)
        current.words['A'][1] = current.words['A'][4] = 0x1643
        report = source.check_navigation(current, old, ['A'], ['A'])
        self.assertEqual(len(report['component_maps'][0]['after_component_sizes']), 2)
        self.assertEqual(report['global_components_before'], report['global_components_after'])
        current.words['B'][1] = 0x1643
        with self.assertRaisesRegex(AssertionError, 'World Surf component split'):
            source.check_navigation(current, old, ['A'], ['A', 'B'])

    def test_spawn_guards_and_native_runtime_preservation_are_independent(self):
        from sevii_boundary_scenery_actor import C_HELPER
        name = 'OneIsland_Frlg'
        old = self.world({name: (1, 8, [0x1664]*8)})
        old.maps[name]['object_events'] = [dict(graphics_id='OTHER') for _ in range(3)]+[
            dict(graphics_id=source.SCENERY_GRAPHICS, x=0, y=7, elevation=1,
                 movement_type='MOVEMENT_TYPE_FACE_DOWN', movement_range_x=0, movement_range_y=0,
                 trainer_type='TRAINER_TYPE_NONE', script='0', flag='0')]
        current = copy.deepcopy(old)
        current.source = self.root/'candidate'
        (old.source/'src').mkdir()
        (current.source/'src').mkdir(parents=True)
        before = 'void TrySpawnObjectEvents(s16 cameraX, s16 cameraY)\n{\n    NativeSpawn();\n}\nvoid RemoveObjectEventsOutsideView(void) { NativeUnload(); }\n'
        after = C_HELPER+'\n'+before.replace('    NativeSpawn();', '    NativeSpawn();\n    JourneySpawnConnectedCoastScenery(cameraX, cameraY);')
        (old.source/source.SCENERY_PATH).write_text(before)
        path = current.source/source.SCENERY_PATH
        path.write_text(after)
        self.assertTrue(source.check_scenery_runtime(current, old)['original_identity_preserved'])
        for token in ('FlagGet(original->flagId)', 'NativeUnload();', 'originX = -incoming->mapLayout->width;'):
            with self.subTest(token=token):
                path.write_text(after.replace(token, 'BROKEN();'))
                with self.assertRaises(AssertionError):
                    source.check_scenery_runtime(current, old)


class SourceReportTests(unittest.TestCase):
    def setUp(self):
        import test_sevii_route_boundaries_source as prior_tests
        previous = prior_tests.SeviiBoundarySourceProof()
        previous.setUp()
        self.addCleanup(previous.doCleanups)
        self.root, self.romsha = previous.root, previous.romsha
        self.prepared = {'src/event_object_movement.c': 'a'*64,
                         'data/layouts/Sea0/map.bin': 'b'*64}
        pin = patch.object(contract, 'PREPARED_SHA256', self.prepared)
        pin.start()
        self.addCleanup(pin.stop)
        old = previous.report()
        from prepare_coast_scenery_review import PRIOR
        self.report = {key: copy.deepcopy(old[key]) for key in (
            'passed', 'preflight', 'compiled_rom', 'independent_replay', 'prefix_markers_unchanged',
            'unrelated_source_files_unchanged', 'scripts_and_atlas_art_unchanged', 'source_hashes_checked',
            'elf_rom_load_segments_checked', 'compiled_layouts', 'compiled_gps', 'compiled_runtime',
            'runtime_export_names', 'rom_sha256', 'elf_sha256')}
        self.report.update(kind='coast-scenery-review-source', layers=PRIOR+[contract.SCOPE],
            parent_rom_sha256=contract.PARENT_ROM_SHA256, prepared_sha256=copy.deepcopy(self.prepared),
            changed_files=sorted(self.prepared), source_gallery_not_emulator=True,
            source_gallery_rendered=False, captures=[], reviewed_maps=['OneIsland_Frlg', 'Sea0'])
        self.report['camera_runtime'] = dict(dedicated_primary='gTileset_JourneySeviiSea',
            map_type='MAP_TYPE_OCEAN_ROUTE', visual_queries_only=True,
            collision_elevation_and_movement_code_unchanged=True,
            compatible_art_and_undefined_grid_rules_unchanged=True)
        names = sorted(row['map'] for row in old['compiled_layouts'])
        self.report['geometry_audit'] = dict(maps=284, map_names=names, changed_maps=['Sea0'],
            changed_cells=72, cells=[dict(map='Sea0', cell=[i%24, i//24], before=0x1643, after=0x1664) for i in range(72)],
            no_dry_land_changed=True, all_map_metadata_unchanged=True, all_borders_unchanged=True,
            only_reviewed_primary_banks_changed=True,
            bank_alignment=[dict(map=name, before=source.BANK_BEFORE, after=source.BANK_AFTER,
                used_primary_ids=[0x12B, 0x243], used_metatiles_sha256='1'*64,
                shared_symbols=dict(isCompressed='TRUE', isSecondary='FALSE',
                    tiles='gTilesetTiles_General_Frlg', palettes='gTilesetPalettes_General_Frlg',
                    metatileAttributes='gMetatileAttributes_General_Frlg', callback='InitTilesetAnim_General_Frlg'),
                original_metatiles=dict(file='data/tilesets/primary/general_frlg/metatiles.bin', sha256='2'*64),
                selected_metatiles=dict(file='data/tilesets/primary/journey/metatiles.bin', sha256='3'*64),
                every_existing_primary_metatile_identical=True, secondary_bank_unchanged=True,
                dimensions_events_connections_and_own_terrain_unchanged=True) for name in source.BANK_MAPS])
        self.report['scenery_audit'] = dict(whole_replaced_objects=37, objects=[dict(map='Sea0', anchor=[i, 0],
            family=[0x110, 0x111, 0x118, 0x119], before=[0x1510, 0x1643, 0x1518, 0x1643],
            after=[0x1643]*4, whole_footprint=True) for i in range(37)],
            restored_native_edge_cells=[dict(row, native_pre169_word=0x1264) for row in self.report['geometry_audit']['cells']],
            all_collision_and_elevation_preserved=True, all_cells_outside_reviewed_changes_unchanged=True,
            native_edge_cells_authenticated_by_parent_marker=True)
        self.report['permanent_scenery'] = dict(map='OneIsland_Frlg', local_id=4, cell=[0,7],
            cardinal_transforms_checked=4, only_dedicated_scenery=True, original_identity_preserved=True,
            event_templates_unchanged=True, native_spawn_and_unload_preserved=True)
        self.report['boulder_census'] = dict(maps=284, map_names=names,
            family_metatiles=[list(row) for row in source.FRLG_FAMILIES+source.EMERALD_FAMILIES],
            objects=[dict(map='Sea0', classification='complete', metatiles=[0x110,0x111,0x118,0x119], cells=[['Sea0',0,0]]*4)],
            classifications=dict(complete=1), new_partial_objects=0, mixed_small_and_large_objects=0,
            inherited_context_patterns_preserved=True, source_census_not_native_camera_proof=True)
        self.report['corner_audit'] = dict(before_ambiguous_cells=107, after_ambiguous_cells=0,
            all_actual_candidates_agree=True, movement_boundaries_and_runtime_unchanged=True, full_world_camera_certified=False)
        self.report['surface_navigation'] = dict(surf_components_preserved=True, no_new_surf_passages=True,
            all_existing_water_connections_open=True, all_surviving_cells_retain_global_connectivity=True,
            network_maps=names, network_maps_checked=284, global_components_before=1, global_components_after=1,
            component_maps=[dict(map='Sea0', before_component_sizes=[5], after_component_sizes=[4],
                                 removed_water_cells=1, retained_local_components=1)],
            physical_connections_checked=1, physical_connections=[dict(map='Sea0', target='Sea1',
                direction='right', before_openings=1, after_openings=1)])
        self.report['runtime_export_names'].append('TrySpawnObjectEvents')
        self.report['compiled_runtime'].append(dict(symbol='TrySpawnObjectEvents', address=0x08021000,
            bytes=16, sha256='3'*64))

    def verify(self): return verify_report(self.report, self.root, self.romsha)

    def test_complete_compiled_report_passes(self):
        self.assertIs(self.verify(), self.report)

    def test_preflight_stale_rom_unpinned_scope_and_missing_runtime_fail(self):
        for key, value in (('preflight', True), ('compiled_rom', False), ('rom_sha256', contract.PARENT_ROM_SHA256)):
            with self.subTest(key=key):
                previous = self.report[key]
                self.report[key] = value
                with self.assertRaises(AssertionError): self.verify()
                self.report[key] = previous
        with patch.object(contract, 'PREPARED_SHA256', {}):
            with self.assertRaises(AssertionError): self.verify()
        self.report['compiled_runtime'].pop()
        with self.assertRaises(AssertionError): self.verify()

    def test_incomplete_objects_ambiguous_corners_and_disconnected_routes_fail(self):
        for section, key, value in (('scenery_audit', 'whole_replaced_objects', 36),
                ('boulder_census', 'mixed_small_and_large_objects', 1),
                ('corner_audit', 'after_ambiguous_cells', 1),
                ('surface_navigation', 'global_components_after', 2)):
            with self.subTest(key=key):
                previous = self.report[section][key]
                self.report[section][key] = value
                with self.assertRaises(AssertionError): self.verify()
                self.report[section][key] = previous
        self.report['scenery_audit']['restored_native_edge_cells'][0]['native_pre169_word'] = 0x1265
        with self.assertRaises(AssertionError): self.verify()

    def test_before_after_galleries_are_complete_labelled_and_content_bound(self):
        captures = []
        for phase in ('before', 'after'):
            for name in self.report['reviewed_maps']:
                path = self.root/(phase+'-'+name+'.png')
                path.write_bytes((phase+name).encode())
                captures.append(dict(file=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                    map=name, phase=phase, full_map=True, npcs=True, source_render_not_emulator=True,
                    label_present=True, width_tiles=24, height_tiles=40))
        self.report.update(captures=captures, source_gallery_rendered=True)
        self.verify()
        row = captures.pop()
        with self.assertRaises(AssertionError): self.verify()
        captures.append(row)
        row['label_present'] = False
        with self.assertRaises(AssertionError): self.verify()
        row['label_present'] = True
        (self.root/row['file']).write_bytes(b'changed source image')
        with self.assertRaises(AssertionError): self.verify()


if __name__ == '__main__':
    unittest.main()
