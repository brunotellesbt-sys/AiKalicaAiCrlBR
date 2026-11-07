"""Check the new One southern mouth without writing the frozen parent source."""
import copy
from collections import deque
import hashlib
import json
from pathlib import Path
import re
import struct
import tempfile
import unittest
from unittest.mock import patch

from candidate_layer import Layer
from one_south_surf_link import repair, projection
from prepare_generated_area_review import PRIOR, LAYER
from render_sea_maps import MapRenderer
from validate_sevii_route_boundaries_source import Inputs


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'.local/coast-scenery-review-src'
BEACH = 'OneIsland_TreasureBeach_Frlg'
SEA = 'JourneyKantoSeviiTransit'
NEW = 'JourneyOneSouthPassage'
GPS = 'src/data/journey_world_position.h'
LAYOUTS = 'data/layouts/layouts.json'


def parsed_gps(raw):
    text = raw.decode()
    body = re.search(r'sWorldNavigationPixels\[\] = \{([^}]+)', text)[1]
    values = list(map(int, body.split(',')))
    grids = {ident: (int(first), int(w), int(h)) for first, ident, w, h in re.findall(
        r'\{(\d+), \(MAP_GROUP\((\w+)\)<<8\)\|MAP_NUM\(\2\), (\d+), (\d+)\}', text)}
    return body, values, grids


@unittest.skipUnless((SOURCE/'.journey-coast-scenery-review').is_file(), 'Frozen layer 170 source unavailable')
class OneSouthSurfLink(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = Inputs(SOURCE)
        cls.layer = Layer(SOURCE, LAYER, PRIOR)
        cls.report = repair(cls.layer)

    def original(self, path):
        return (SOURCE/path).read_bytes()

    def staged(self, path):
        return self.layer.outputs.get(path, self.original(path) if (SOURCE/path).exists() else None)

    def mapping(self, name):
        return json.loads(self.staged(f'data/maps/{name}/map.json'))

    def layouts(self):
        return {r['id']: r for r in json.loads(self.staged(LAYOUTS))['layouts']}

    def layout(self, name):
        return self.layouts()[self.mapping(name)['layout']]

    def grid(self, name):
        raw = self.staged(self.layout(name)['blockdata_filepath'])
        return struct.unpack('<'+'H'*(len(raw)//2), raw)

    def test_registration_appends_without_changing_old_numeric_ids(self):
        old_layouts = json.loads(self.original(LAYOUTS))['layouts']
        current = json.loads(self.staged(LAYOUTS))['layouts']
        self.assertEqual(current[:-1], old_layouts)
        self.assertEqual(current[-1]['id'], 'LAYOUT_JOURNEYONESOUTHPASSAGE')
        path = 'data/maps/map_groups.json'
        old, current = (json.loads(data) for data in (self.original(path), self.staged(path)))
        group = 'JourneyWorldOcean'
        expected = copy.deepcopy(old)
        expected[group].append(NEW)
        self.assertEqual(current, expected)
        self.assertLess(len(current[group]), 256)
        self.assertEqual(current[group].index(NEW), self.report['appended_map_number'])
        self.assertNotIn('include/constants/region_map_sections.h', self.layer.outputs)
        self.assertNotIn('src/data/region_map/region_map_sections.json', self.layer.outputs)

    def test_existing_events_metadata_and_connection_order_survive(self):
        for name, direction, offset in ((BEACH, 'down', 0), (SEA, 'up', 62)):
            original, current = self.inputs.maps[name], self.mapping(name)
            expected = copy.deepcopy(original)
            expected['connections'].append(dict(map='MAP_JOURNEYONESOUTHPASSAGE', direction=direction, offset=offset))
            self.assertEqual(current, expected)
        mapping = self.mapping(NEW)
        for field in ('object_events', 'warp_events', 'coord_events', 'bg_events'):
            self.assertEqual(mapping[field], [])
        self.assertEqual(mapping['region_map_section'], 'MAPSEC_ONE_ISLAND')

    def test_both_mouths_have_one_reciprocal_owner_and_six_surf_cells(self):
        mapping = self.mapping(NEW)
        self.assertEqual(mapping['connections'], [
            dict(map=self.inputs.maps[BEACH]['id'], direction='up', offset=0),
            dict(map=self.inputs.maps[SEA]['id'], direction='down', offset=-62)])
        for name in (BEACH, SEA, NEW):
            l = self.layout(name)
            spans = {d: set() for d in ('up', 'down', 'left', 'right')}
            for c in self.mapping(name)['connections']:
                target = next((n for n, m in self.inputs.maps.items() if m['id'] == c['map']), NEW)
                t = self.layout(target)
                vertical = c['direction'] in ('up', 'down')
                limit = l['width' if vertical else 'height']
                length = t['width' if vertical else 'height']
                cells = set(range(max(0, c['offset']), min(limit, c['offset']+length)))
                self.assertFalse(spans[c['direction']] & cells, (name, c))
                spans[c['direction']].update(cells)
        self.assertEqual(self.grid(BEACH)[47*40:47*40+8], (0x1643, *([0x112B]*6), 0x1643))
        self.assertEqual(self.grid(SEA)[62:70], (0x1643, *([0x112B]*6), 0x1643))
        self.assertEqual(self.grid(SEA)[112+62:112+70], (0x1643, *([0x112B]*6), 0x1643))

    def test_vertical_corridor_has_complete_reefs_and_surf_height(self):
        self.assertEqual((self.layout(NEW)['width'], self.layout(NEW)['height']), (8, 32))
        words = self.grid(NEW)
        for y in range(32):
            self.assertEqual(words[y*8:y*8+8], (0x1643, *([0x112B]*6), 0x1643))
        border = self.staged(self.layout(NEW)['border_filepath'])
        self.assertEqual(border, struct.pack('<4H', *([0x1643]*4)))
        for word in (0x1643, 0x112B):
            self.assertIn(self.inputs.behavior(BEACH, word), self.inputs.water)
            self.assertEqual(word >> 12, 1)

    def test_actual_water_component_reaches_both_sides_of_the_southern_sea(self):
        names = (BEACH, NEW, SEA)
        maps = {name: self.mapping(name) for name in names}
        layouts = {name: self.layout(name) for name in names}
        words = {name: self.grid(name) for name in names}
        by_id = {mapping['id']: name for name, mapping in maps.items()}

        def target(name, x, y):
            l = layouts[name]
            direction = 'left' if x < 0 else 'right' if x >= l['width'] else 'up' if y < 0 else 'down' if y >= l['height'] else None
            if direction is None:
                return name, x, y
            for connection in maps[name]['connections']:
                if connection['direction'] != direction or connection['map'] not in by_id:
                    continue
                other = by_id[connection['map']]
                t = layouts[other]
                xx = x-connection['offset'] if direction in ('up', 'down') else x+t['width'] if direction == 'left' else x-l['width']
                yy = y-connection['offset'] if direction in ('left', 'right') else y+t['height'] if direction == 'up' else y-l['height']
                if 0 <= xx < t['width'] and 0 <= yy < t['height']:
                    return other, xx, yy
            return None

        pending = deque([(BEACH, 4, 43)])
        visited = set(pending)
        while pending:
            name, x, y = pending.popleft()
            for xx, yy in ((x-1, y), (x+1, y), (x, y-1), (x, y+1)):
                point = target(name, xx, yy)
                if point is None or point in visited:
                    continue
                n, tx, ty = point
                word = words[n][ty*layouts[n]['width']+tx]
                behavior_map = BEACH if n == NEW else n
                if word&0xC00 or self.inputs.behavior(behavior_map, word) not in self.inputs.water:
                    continue
                visited.add(point)
                pending.append(point)
        self.assertTrue((SEA, 50, 3) in visited, 'Western horizontal sea remains blocked behind a reef row')
        self.assertTrue((SEA, 80, 3) in visited, 'Eastern horizontal sea remains blocked behind a reef row')

    def test_only_two_reef_mouths_and_four_cliff_cells_change_old_terrain(self):
        allowed = {BEACH: {(x, 47) for x in range(1, 7)} | {(7, 37), (6, 38), (32, 37), (33, 38)},
                   SEA: {(x, y) for y in (0, 1) for x in range(63, 69)}}
        count = 0
        for name in (BEACH, SEA):
            width = self.layout(name)['width']
            before, after = self.inputs.grid(name), self.grid(name)
            self.assertEqual(len(before), len(after))
            changed = {(index % width, index//width) for index, (a, b) in enumerate(zip(before, after)) if a != b}
            self.assertEqual(changed, allowed[name])
            count += len(changed)
        self.assertEqual(count, 22)
        old, new = self.inputs.grid(BEACH), self.grid(BEACH)
        for y in range(40):
            self.assertEqual(new[y*40+8:y*40+32], old[y*40+8:y*40+32])

    def test_cliff_caps_face_outward_and_keep_collision_and_height(self):
        expected = {(7, 37): 0x0517, (6, 38): 0x1128, (32, 37): 0x051F, (33, 38): 0x1129}
        words = self.grid(BEACH)
        for (x, y), value in expected.items():
            self.assertEqual(words[y*40+x], value)
            self.assertEqual(self.inputs.word(BEACH, x, y)&0xFC00, value&0xFC00)
        self.assertEqual([words[y*40+7] for y in (37, 38, 39, 40, 41)], [0x517, 0x473, 0x473, 0x47B, 0x1123])
        self.assertEqual([words[y*40+32] for y in (37, 38, 39, 40, 41)], [0x51F, 0x475, 0x475, 0x47D, 0x1123])

    def test_gps_preserves_every_old_packed_value_and_descriptor(self):
        old_text, before, old_grids = parsed_gps(self.original(GPS))
        new_text, after, new_grids = parsed_gps(self.staged(GPS))
        self.assertEqual(new_text[:len(old_text)], old_text)
        self.assertEqual(after[:len(before)], before)
        self.assertEqual(len(after)-len(before), 256)
        self.assertEqual(new_grids.pop('MAP_JOURNEYONESOUTHPASSAGE'), (len(before), 8, 32))
        self.assertEqual(new_grids, old_grids)

    def test_gps_seams_match_and_no_step_jumps_off_the_drawn_corridor(self):
        _, values, grids = parsed_gps(self.staged(GPS))
        start, w, h = grids['MAP_JOURNEYONESOUTHPASSAGE']
        added = values[start:start+w*h]
        first, bw, bh = grids[self.inputs.maps[BEACH]['id']]
        self.assertEqual(added[:8], values[first+47*bw:first+47*bw+8])
        first, sw, sh = grids[self.inputs.maps[SEA]['id']]
        self.assertEqual(added[-8:], values[first+62:first+70])
        for y in range(h):
            for x in range(w):
                a = added[y*w+x]
                self.assertTrue(135 <= a&255 <= 138 and 40 <= a >> 8 <= 53)
                if 40 < a >> 8 < 53:
                    self.assertEqual(a&255, 135)
                for xx, yy in ((x+1, y), (x, y+1)):
                    if xx < w and yy < h:
                        b = added[yy*w+xx]
                        self.assertLessEqual(max(abs((a&255)-(b&255)), abs((a >> 8)-(b >> 8))), 1)

    def test_atlas_arrays_unchanged_and_new_map_has_a_factual_point_label(self):
        path = 'src/data/journey_world_map.h'
        before, after = self.original(path).decode(), self.staged(path).decode()
        for symbol in ('sWorldPalette', 'sWorldTiles', 'sWorldTilemap'):
            pattern = symbol+r'\[\] = \{[^}]+\}'
            self.assertEqual(re.search(pattern, before)[0], re.search(pattern, after)[0])
        line = '    {(MAP_GROUP(MAP_JOURNEYONESOUTHPASSAGE)<<8)|MAP_NUM(MAP_JOURNEYONESOUTHPASSAGE), MAPSEC_ONE_ISLAND, 135, 47, COMPOUND_STRING("ONE SOUTH PASSAGE")},\n'
        self.assertEqual(after.count(line), 1)
        self.assertEqual(after.replace(line, ''), before)

    def test_encounters_append_the_same_normal_water_and_fishing_family(self):
        path = 'src/data/wild_encounters.json'
        before, after = (json.loads(raw) for raw in (self.original(path), self.staged(path)))
        additions = []
        for group in after['wild_encounter_groups']:
            for row in list(group['encounters']):
                if row.get('map') == 'MAP_JOURNEYONESOUTHPASSAGE':
                    additions.append(row)
                    group['encounters'].remove(row)
        self.assertEqual(after, before)
        self.assertEqual(len(additions), 1)
        source = next(row for group in before['wild_encounter_groups'] for row in group['encounters'] if row.get('map') == self.inputs.maps[SEA]['id'])
        addition = additions[0]
        self.assertEqual(addition.pop('map'), 'MAP_JOURNEYONESOUTHPASSAGE')
        self.assertEqual(addition.pop('base_label'), 'gCoastalEcology_'+NEW)
        self.assertEqual(addition, {k: source[k] for k in ('water_mons', 'fishing_mons')})
        self.assertGreater(addition['water_mons']['encounter_rate'], 0)
        self.assertNotIn('src/wild_encounter.c', self.layer.outputs)

    def test_water_and_reef_artwork_matches_both_adjacent_cameras(self):
        renderer = MapRenderer(SOURCE)
        try:
            a = renderer.render(BEACH, values=[0x112B, 0x1643], dimensions=(2, 1), npcs=False)[0]
            b = renderer.render(SEA, values=[0x112B, 0x1643], dimensions=(2, 1), npcs=False)[0]
            self.assertEqual(a.tobytes(), b.tobytes())
            for word in (0x112B, 0x1643):
                self.assertEqual(self.inputs.behavior(BEACH, word), self.inputs.behavior(SEA, word))
        finally:
            for tiles, _, _ in renderer.cache.values():
                tiles.close()

    def test_port_repair_staging_survives_the_new_connection(self):
        import port_boundary_scenery as ports
        layer = Layer(SOURCE, LAYER, PRIOR)
        terrain_class, terrains = ports.Terrain, []
        def tracked_terrain(*args, **kwargs):
            terrain = terrain_class(*args, **kwargs)
            terrains.append(terrain)
            return terrain
        try:
            with patch.object(ports, 'Terrain', side_effect=tracked_terrain):
                ports.repair(layer)
        finally:
            for terrain in terrains:
                for tiles, _, _ in terrain.renderer.cache.values():
                    tiles.close()
        path = self.inputs.layout(BEACH)['blockdata_filepath']
        before = struct.unpack('<1920H', layer.outputs[path])
        repair(layer)
        after = struct.unpack('<1920H', layer.outputs[path])
        for x, y in ((19, 7), (19, 8), (20, 8), (20, 7)):
            self.assertEqual(before[y*40+x], after[y*40+x])
        for x, y in ((19, 7), (19, 8), (20, 8)):
            self.assertEqual(after[y*40+x]&1023, 0x243)
        self.assertEqual(after[7*40+20], 0x112B)

    def test_unreviewed_mouth_donor_and_existing_southern_connection_are_rejected(self):
        layer = Layer(SOURCE, LAYER, PRIOR)
        path = self.inputs.layout(BEACH)['blockdata_filepath']
        words = list(self.inputs.grid(BEACH))
        words[47*40+4] = 0x112B
        layer.outputs[path] = struct.pack('<1920H', *words)
        with self.assertRaisesRegex(AssertionError, 'Old mouth'):
            repair(layer)
        layer = Layer(SOURCE, LAYER, PRIOR)
        name = 'SevenIsland_TrainerTower_Frlg'
        l = self.inputs.layout(name)
        words = list(self.inputs.grid(name))
        words[36*l['width']+39] = 0x051F
        layer.outputs[l['blockdata_filepath']] = struct.pack('<'+'H'*len(words), *words)
        with self.assertRaisesRegex(AssertionError, 'Native cliff donor'):
            repair(layer)
        layer = Layer(SOURCE, LAYER, PRIOR)
        mapping = copy.deepcopy(self.inputs.maps[BEACH])
        mapping['connections'].append(dict(map=self.inputs.maps[SEA]['id'], direction='down', offset=0))
        layer.outputs[f'data/maps/{BEACH}/map.json'] = json.dumps(mapping).encode()
        with self.assertRaises(AssertionError):
            repair(layer)

    def test_projection_rejects_changed_endpoint_contracts(self):
        top = [136 | (40 << 8)]*8
        bottom = [x | (53 << 8) for x in (135, 135, 135, 136, 136, 137, 138, 138)]
        with self.assertRaises(AssertionError):
            projection([top[0]+1, *top[1:]], bottom)
        with self.assertRaises(AssertionError):
            projection(top, [*bottom[:-1], bottom[-1]+1])

    def test_staging_does_not_write_parent_files(self):
        for path in self.layer.originals:
            self.assertEqual(hashlib.sha256(self.original(path)).hexdigest(), self.layer.expected[path])
        self.assertFalse((SOURCE/f'data/maps/{NEW}/map.json').exists())
        self.assertFalse((SOURCE/f'data/layouts/{NEW}/map.bin').exists())


class OneSouthNativeReport(unittest.TestCase):
    """Test orchestration checks; pixel/cold verifiers retain their own suites."""
    def setUp(self):
        import validate_one_south_surf_link as native
        self.native = native
        self.folder = tempfile.TemporaryDirectory(prefix='one-south-proof-', dir='/tmp')
        self.addCleanup(self.folder.cleanup)
        self.directory = Path(self.folder.name)
        for name in ('verify_pixels', 'verify_native_avatar_pixels', 'verify_cold'):
            mock = patch.object(native, name, return_value=True)
            mock.start()
            self.addCleanup(mock.stop)
        mock = patch.object(native, 'verify_captures', side_effect=lambda rows, directory: {r['file']: object() for r in rows})
        mock.start()
        self.addCleanup(mock.stop)

    def report(self):
        native = self.native
        captures = []
        def capture(name):
            item = dict(file=name+'.png', sha256='c'*64)
            captures.append(item)
            return item
        def player(point):
            surfing = point[0]+':'+','.join(map(str, point[1:])) not in native.DRY_GOALS
            return dict(map=point[0], tile=point[1:], surfing=surfing,
                        elevation=1 if surfing else 3, active_surf_blobs=int(surfing),
                        sprite_visible=True, object_visible=True)
        arrivals = [dict(goal=point, player=player(point), avatar_pixels={}, capture=capture(f'route-{i:02d}'))
                    for i, point in enumerate(native.GOALS)]
        transitions = [dict(source=[BEACH, 4, 47], destination=[NEW, 4, 0]),
                       dict(source=[NEW, 4, 31], destination=[SEA, 66, 0]),
                       dict(source=[SEA, 66, 0], destination=[NEW, 4, 31]),
                       dict(source=[NEW, 4, 0], destination=[BEACH, 4, 47])]
        # Adjacent synthetic controller observations exercise this report's
        # trajectory contract, independently of emulator and pixel fixtures.
        path = [native.START.copy()]
        def segment(goal):
            while path[-1][1:] != goal[1:]:
                point = path[-1].copy()
                axis = 1 if point[1] != goal[1] else 2
                point[axis] += 1 if goal[axis] > point[axis] else -1
                path.append(point)
        crossings = iter(transitions)
        for goal in native.GOALS:
            if path[-1][0] != goal[0]:
                crossing = next(crossings)
                segment(crossing['source'])
                path.append(crossing['destination'].copy())
            segment(goal)
        gps = []
        for i, point in enumerate(path):
            item = dict(map=point[0], tile=point[1:], marker=[135, 53],
                        seam=i > 0 and path[i-1][0] != point[0])
            if i:
                item['delta'] = 0
            gps.append(item)
        bumps = []
        for x, key in ((0, 32), (7, 16)):
            before = player([NEW, 1 if x == 0 else 6, 16])
            bumps.append(dict(reef_cell=[x, 16], direction_key=key, before=before, after=copy.deepcopy(before),
                              observation_player=player([NEW, 2 if x == 0 else 5, 16]), collision=1,
                              held_input_frames=120, native_directional_input_blocked=True,
                              pixels={}, capture=capture('reef-'+str(x))))
        view_cells = {
            'west-cliff': ([BEACH, 4, 39], 4), 'east-cliff': ([BEACH, 35, 39], 4),
            'top-from-beach': ([BEACH, 4, 45], 3), 'top-from-passage': ([NEW, 4, 2], 3),
            'bottom-from-passage': ([NEW, 4, 29], 3), 'bottom-from-sea': ([SEA, 66, 2], 4)}
        views = [dict(label=label, player=player(point), pixels=dict(map=point[0], cells=[{} for _ in range(count)]),
                      capture=capture(label)) for label, (point, count) in view_cells.items()]
        hashes = [format(index, '064x') for index in range(8)]
        animation = dict(phases_observed=list(range(8)), source_frames_sha256=hashes,
                         samples=[dict(matches=[i % 8], vram_sha256=hashes[i % 8],
                                       capture=capture('water-'+str(i))) for i in range(16)])
        saves = []
        for i, point in enumerate(([NEW, 4, 16], [BEACH, 20, 6])):
            battery = self.directory/('save-'+str(i)+'.sav')
            battery.write_bytes(bytes(131072))
            folder = self.directory/('cold-'+str(i))
            folder.mkdir(exist_ok=True)
            component = folder/'cold-boot.json'
            component.write_text('{}\n')
            saves.append(dict(file=battery.name, bytes=131072, sha256=hashlib.sha256(battery.read_bytes()).hexdigest(),
                              player=player(point), map_id=[50, 67 if i == 0 else 2], saved_with_controllers=True,
                              save_menu_callbacks=['SaveReturnSuccessCallback'], cold_continue={},
                              cold_directory=folder.name, cold_report_sha256=hashlib.sha256(component.read_bytes()).hexdigest(),
                              capture=capture('saved-'+str(i))))
        return dict(kind='one-south-surf-link-native', passed=True, rom_sha256='a'*64, elf_sha256='b'*64,
                    native_validation_performed=True, full_campaign_playthrough=False,
                    initial_party_progress_encounter_suppression_and_placement_are_fixtures=True,
                    after_placement_movement_controllers_only=True, gameplay_scripts_not_injected_after_placement=True,
                    native_hardware_bg_oam_vram_palette_and_scanout_checked=True, old_source_and_rom_unchanged=True,
                    source_overlay_inputs_checked=14, source_overlay_marker_sha256='e'*64,
                    fixtures=[dict(map=native.START[0], tile=native.START[1:], surfing=True)], goals=native.GOALS,
                    arrivals=arrivals, transitions=transitions, walked_tiles=len(path)-1, gps_samples=gps,
                    maximum_gps_step=0, maximum_seam_delta=0, surf_prompts=[[BEACH, 24, 21], [BEACH, 20, 6]],
                    boundary_bumps=bumps, terrain_views=views, water_animation=animation,
                    inputs=[dict(frames=1, key=key) for key in (0, 1, 8, 16, 32, 64, 128)],
                    queries=[dict(function='JourneyWorldMapPosition')], saves=saves, captures=captures,
                    components=[dict(file=row['cold_directory']+'/cold-boot.json', sha256=row['cold_report_sha256']) for row in saves],
                    battery_saves=[{key: row[key] for key in ('file', 'bytes', 'sha256')} for row in saves])

    def verify(self, report):
        return self.native.verify_report(report, self.directory, 'a'*64)

    def rejects(self, change):
        report = self.report()
        change(report)
        with self.assertRaises((AssertionError, KeyError)):
            self.verify(report)

    def test_complete_orchestration_contract_passes_with_delegated_pixel_checks(self):
        self.assertTrue(self.verify(self.report()))

    def test_walk_count_and_ordered_trajectory_are_bound_to_the_actual_route(self):
        self.rejects(lambda report: report.update(walked_tiles=report['walked_tiles']+1))
        self.rejects(lambda report: report['gps_samples'].__delitem__(8))

    def test_cold_verifier_receives_each_real_battery_path(self):
        report = self.report()
        self.verify(report)
        self.assertEqual([call.args[2] for call in self.native.verify_cold.call_args_list],
                         [self.directory/row['file'] for row in report['saves']])

    def test_stale_hashes_missing_fixture_and_uncontrolled_claims_are_rejected(self):
        for key, value in (('rom_sha256', 'd'*64), ('elf_sha256', 'z'*64), ('passed', False),
                           ('after_placement_movement_controllers_only', False), ('fixtures', [])):
            with self.subTest(key=key):
                self.rejects(lambda report, key=key, value=value: report.update({key: value}))

    def test_wrong_physical_crossing_and_gps_seam_or_teleport_are_rejected(self):
        self.rejects(lambda report: report['transitions'][1]['destination'].__setitem__(1, 65))
        self.rejects(lambda report: report['gps_samples'][1].update(tile=[12, 43]))
        self.rejects(lambda report: report['gps_samples'][1].update(seam=True))
        self.rejects(lambda report: report['gps_samples'][1].update(delta=3, marker=[138, 53]))

    def test_missing_horizontal_turn_arrival_and_wrong_surf_state_are_rejected(self):
        self.rejects(lambda report: report['arrivals'].pop(12))
        self.rejects(lambda report: report['arrivals'][12]['player'].update(tile=[60, 6]))
        self.rejects(lambda report: report['arrivals'][22]['player'].update(surfing=True))

    def test_distant_reef_bump_and_wrong_terrain_camera_are_rejected(self):
        def distant(report):
            report['boundary_bumps'][0]['before']['tile'] = [2, 16]
            report['boundary_bumps'][0]['after']['tile'] = [2, 16]
        self.rejects(distant)
        self.rejects(lambda report: report['boundary_bumps'][1]['observation_player'].update(tile=[6, 16]))
        self.rejects(lambda report: report['terrain_views'][0]['player'].update(tile=[4, 45]))
        self.rejects(lambda report: report['terrain_views'][-1]['pixels']['cells'].pop())

    def test_missing_animation_phase_injected_gameplay_and_unsaved_battery_are_rejected(self):
        self.rejects(lambda report: report['water_animation'].update(phases_observed=list(range(7))))
        self.rejects(lambda report: report['queries'].append(dict(function='SetPlayerAvatarTransitionFlags')))
        self.rejects(lambda report: report['saves'][1].update(saved_with_controllers=False))
        self.rejects(lambda report: report['saves'][0].update(sha256='d'*64))


if __name__ == '__main__':
    unittest.main()
