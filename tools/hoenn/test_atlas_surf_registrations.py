"""Concrete coast proposals: real mouths, fixed art, banks and reservations.

Tests run on small native-source fixtures and, when available, all source171
interfaces. They establish source geometry, not emulated-ROM travel or art.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import unittest

from atlas_surf_adapters import inventory as adapter_inventory, plan_adapters
from atlas_surf_geometry import chunk_water, plan_geometry
from atlas_surf_plan import plan_reserved_geometry
from atlas_surf_registrations import diagnose_legacy_gps, propose_registrations
from atlas_surf_source import CARDINAL, OPPOSITE, Source
from atlas_surf_truth import decode_atlas
import test_atlas_surf_source_inventory as native_fixtures


def atlas_header(pixels,extra_anchor=''):
    # Encode the real 4bpp/tilemap representation consumed by decode_atlas.
    # Every tile has its own bytes so the fixture can put blue ink anywhere.
    tiles, tilemap = [],[0]*(32*17)
    for ty in range(14):
        for tx in range(28):
            tilemap[(ty+3)*32+tx+1] = len(tiles)//32
            for y in range(8):
                for x in range(0,8,2):
                    low = 2 if (tx*8+x,ty*8+y) in pixels else 1
                    high = 2 if (tx*8+x+1,ty*8+y) in pixels else 1
                    tiles.append(low | high<<4)
    return ('static const u8 sWorldTiles[] = {'+','.join(map(str,tiles))+'};\n'
            'static const u16 sWorldTilemap[] = {'+','.join(map(str,tilemap))+'};\n'
            'static const u16 sWorldPalette[] = {'+','.join('0' for _ in range(16))+'};\n'
            'static const u8 sWorldDetailPixels[] = {0};\n'
            '{(MAP_GROUP(MAP_NATIVE)<<8)|MAP_NUM(MAP_NATIVE), MAPSEC_NATIVE, 10, 10, COMPOUND_STRING("NATIVE")}\n'
            +extra_anchor).encode()


@unittest.skipUnless(shutil.which('cc') or shutil.which('gcc'),'Native behavior enum compiler required')
class RegistrationFixtureTests(unittest.TestCase):
    def fixture(self,direction='right',width=6,height=1,two=False):
        helper = native_fixtures.NativeInventoryTests()
        self.addCleanup(helper.doCleanups)
        native_words = [height<<12|1]*(12*12)
        retired_words = [0x1001]*(12*12)
        donor_words = [0x1001]*(12*12);donor_words[0] = 0x1643
        if width < 6:
            native_words = [0x1643]*(12*12)
            for y in range(4,4+width): native_words[y*12+11] = height<<12|1
        root,layer = helper.fixture({'Native':('emerald',12,12,native_words),
                                     'Retired':('emerald',12,12,retired_words),
                                     'JourneyDonor':('emerald',12,12,donor_words)})
        for name,other,d in [('Native','Retired',direction),('Retired','Native',OPPOSITE[direction])]:
            path = f'data/maps/{name}/map.json'
            row = json.loads((root/path).read_bytes())
            row['connections'] = [dict(map='MAP_'+other.upper(),direction=d,offset=0)]
            layer.parent(path,row)
        dx,dy = CARDINAL[direction]
        pixels = {(10+dx*i,10+dy*i) for i in range(9)}
        coast = dict(native_interfaces=[dict(native_map='Native',retired_map='Retired',
            direction=OPPOSITE[direction],offset=0,reciprocal=True)])
        authored = {('Native',0):[(direction,(10,10),'fixture coast with a returning ink segment')]}
        extra = ''
        if two:
            for name,original,other,d in [('Native2','Native','Retired2',direction),
                                         ('Retired2','Retired','Native2',OPPOSITE[direction])]:
                row = json.loads((root/f'data/maps/{original}/map.json').read_bytes())
                row['id'] = 'MAP_'+name.upper()
                row['connections'] = [dict(map='MAP_'+other.upper(),direction=d,offset=0)]
                layer.parent(f'data/maps/{name}/map.json',row)
            groups = json.loads((root/'data/maps/map_groups.json').read_bytes())
            groups['Group'] += ['Native2','Retired2']
            layer.parent('data/maps/map_groups.json',groups)
            extra = '{(MAP_GROUP(MAP_NATIVE2)<<8)|MAP_NUM(MAP_NATIVE2), MAPSEC_NATIVE, 10, 10, COMPOUND_STRING("NATIVE2")}\n'
            coast['native_interfaces'].append(dict(native_map='Native2',retired_map='Retired2',
                direction=OPPOSITE[direction],offset=0,reciprocal=True))
            authored['Native2',0] = [(direction,(10,10),'second conflicting authored coast')]
        layer.parent('src/data/journey_world_map.h',atlas_header(pixels,extra))
        inputs = Source(root)
        truth = decode_atlas(inputs.read('src/data/journey_world_map.h').decode())
        return root,layer,inputs,adapter_inventory(inputs,coast),truth,authored

    def test_all_four_directions_have_source_returns_and_exact_offsets(self):
        for direction in CARDINAL:
            with self.subTest(direction=direction):
                root,layer,source,inventory,truth,authored = self.fixture(direction)
                before = {path:hashlib.sha256((root/path).read_bytes()).hexdigest() for path in layer.expected}
                result = propose_registrations(source,inventory,truth,authored=authored)
                self.assertTrue(result['all_inventory_components_registered'])
                self.assertEqual(result['conflicts'],[])
                reg = result['registrations'][0];binding = result['adapter_plan']['bindings'][0]
                self.assertEqual(reg['direction'],direction)
                self.assertEqual(reg['mouth_width'],6)
                self.assertEqual(binding['native_connection']['offset'],-binding['adapter_connection']['offset'])
                self.assertTrue(result['geography_authored_not_recovered'])
                self.assertFalse(result['native_rom_validated'])
                self.assertFalse(result['old_player_gps_used'])
                self.assertNotIn('src/data/journey_world_position.h',result['input_sha256'])
                self.assertEqual(before,{path:hashlib.sha256((root/path).read_bytes()).hexdigest() for path in layer.expected})
                self.assertFalse(layer.outputs)

    def test_narrow_authentic_mouth_and_height3_transition_preserve_native(self):
        _,_,source,inventory,truth,authored = self.fixture(width=3,height=3)
        original = source.words('Native')
        result = propose_registrations(source,inventory,truth,authored=authored)
        self.assertEqual(result['registrations'][0]['mouth_width'],3)
        binding = result['adapter_plan']['bindings'][0]
        self.assertEqual(binding['native_heights'],[3])
        self.assertTrue(binding['transition_height_zero_only_in_new_adapter'])
        words = result['adapter_plan']['reservations'][0]['word_overrides']
        self.assertEqual({row['word']>>12 for row in words},{0,3})
        self.assertEqual(source.words('Native'),original)

    def test_missing_design_or_return_is_reported_without_painting_water(self):
        _,_,source,inventory,truth,authored = self.fixture()
        for custom,plan in [({},None),(authored,plan_geometry([(10,10)])),
                            ({('Native',0):[('right',(20,20),'unapproved ocean')]},None)]:
            with self.subTest(custom=custom,plan=plan is None):
                result = propose_registrations(source,inventory,truth,plan,authored=custom)
                self.assertFalse(result['all_inventory_components_registered'])
                self.assertEqual(result['registered_component_count'],0)
                self.assertEqual(result['conflicts'][0]['reason'],'no-eight-tile-returning-fit')
                self.assertFalse(result['generated_water_added'])

    def test_changed_component_or_fabricated_edge_is_rejected(self):
        for change in ('component','word','offset'):
            _,_,source,inventory,truth,authored = self.fixture()
            if change == 'component': inventory['adapters'][0]['component_sha256'] = '0'*64
            elif change == 'word': inventory['adapters'][0]['source_wet_edge_witnesses'][0]['words'][1] ^= 0x1000
            else: inventory['adapters'][0]['source_wet_edge_witnesses'][0]['offset'] = 1
            with self.subTest(change=change),self.assertRaises(ValueError):
                propose_registrations(source,inventory,truth,authored=authored)

    def test_authored_geography_conflict_is_explicit_and_deterministic(self):
        _,_,source,inventory,truth,authored = self.fixture(two=True)
        first = propose_registrations(source,inventory,truth,authored=authored)
        second = propose_registrations(source,inventory,truth,authored=authored)
        self.assertEqual(first,second)
        self.assertFalse(first['all_inventory_components_registered'])
        self.assertEqual(first['registered_component_count'],1)
        self.assertEqual(first['conflicts'][0]['reason'],'reservation-or-native-patch-overlap')

    def test_stale_art_and_changed_source_connection_fail_closed(self):
        root,layer,source,inventory,truth,authored = self.fixture()
        truth = deepcopy(truth)
        object.__setattr__(truth,'array_sha256',{'changed':'0'*64})
        with self.assertRaisesRegex(ValueError,'truth differs'):
            propose_registrations(source,inventory,truth,authored=authored)
        truth = decode_atlas((root/'src/data/journey_world_map.h').read_text())
        row = json.loads((root/'data/maps/Native/map.json').read_bytes());row['connections'] = []
        layer.parent('data/maps/Native/map.json',row)
        with self.assertRaisesRegex(ValueError,'reciprocal source connections'):
            propose_registrations(Source(root),inventory,truth,authored=authored)

    def test_old_gps_is_secondary_diagnostic_and_cannot_choose_the_mouth(self):
        _,layer,source,inventory,truth,authored = self.fixture()
        proposal = propose_registrations(source,inventory,truth,authored=authored)
        original = deepcopy(proposal['registrations'])
        pixels = ','.join(str(20|20<<8) for _ in range(12*12))
        layer.parent('src/data/journey_world_position.h',(
            'static const u16 sWorldNavigationPixels[] = {'+pixels+'};\n'
            'static const struct JourneyWorldTileGrid sWorldTileGrids[] = {\n'
            '{0, (MAP_GROUP(MAP_NATIVE)<<8)|MAP_NUM(MAP_NATIVE), 12, 12},\n'
            '{0, (MAP_GROUP(MAP_RETIRED)<<8)|MAP_NUM(MAP_RETIRED), 12, 12},\n};\n').encode())
        diagnostic = diagnose_legacy_gps(source,proposal)
        self.assertFalse(diagnostic['used_to_select_or_move_mouths'])
        self.assertTrue(diagnostic['native_gps_integration_pending'])
        self.assertGreater(diagnostic['maximum_cyan_jump_manhattan_pixels'],0)
        self.assertEqual(diagnostic['records'][0]['cells'][0]['legacy_native_atlas'],[20,20])
        self.assertEqual(proposal['registrations'],original)
        self.assertNotIn('src/data/journey_world_position.h',proposal['input_sha256'])


@unittest.skipUnless(shutil.which('cc') or shutil.which('gcc'),'Native behavior enum compiler required')
class Actual171RegistrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Path(__file__).resolve().parents[2]
        cls.path = cls.repo/'.local/generated-area-review-src'
        if not (cls.path/'src/data/journey_world_map.h').is_file():
            raise unittest.SkipTest('Immutable source171 is not available locally')
        from restore_generated_area_review import verify_prefix
        cls.before = verify_prefix(cls.path,complete=True)
        cls.source = Source(cls.path)
        cls.truth = decode_atlas(cls.source.read('src/data/journey_world_map.h').decode())
        cls.inventory = json.loads((cls.repo/'docs/design/atlas-surf-layout/parent-inventory.json').read_bytes())['adapters']
        cls.result = propose_registrations(cls.source,cls.inventory,cls.truth)

    def test_every_inventory_component_has_one_valid_concrete_registration(self):
        result = self.result
        self.assertEqual(result['conflicts'],[])
        self.assertEqual({(r['native_map'],r['component']) for r in result['registrations']},
                         {(r['native_map'],r['component']) for r in self.inventory['adapters']})
        self.assertTrue(result['all_inventory_components_registered'])
        rechecked = plan_adapters(self.source,self.inventory,
            plan_geometry(self.truth.blue_pixels-{(96,40)}),result['registrations'],self.truth)
        self.assertTrue(rechecked['complete_component_coverage'])

    def test_all_reservations_partition_the_same_real_route_water(self):
        pixels = self.truth.blue_pixels-{(96,40)}
        plan = plan_reserved_geometry(pixels,self.result['adapter_plan']['reservations'])
        cells = set()
        for chunk in plan['chunks']:
            for x,y in chunk_water(chunk):
                point = chunk['origin'][0]+x,chunk['origin'][1]+y
                self.assertNotIn(point,cells)
                cells.add(point)
        original = plan_geometry(pixels)
        self.assertEqual(len(cells),original['water_tiles'])
        self.assertEqual(cells,{(c['origin'][0]+x,c['origin'][1]+y) for c in original['chunks'] for x,y in chunk_water(c)})
        self.assertTrue(all(r['ecology_owner']==r['evidence']['native_map']
                            for r in self.result['adapter_plan']['reservations']))

    def test_ever_grande_native_height3_and_narrow_mouths_are_explicit(self):
        upper = next(b for b in self.result['adapter_plan']['bindings']
                     if (b['native_map'],b['component'])==('EverGrandeCity',2))
        self.assertEqual(upper['native_heights'],[3])
        self.assertTrue(upper['transition_height_zero_only_in_new_adapter'])
        narrow = {r['native_map']:r['mouth_width'] for r in self.result['registrations'] if r['mouth_width']<6}
        self.assertEqual(narrow,{'JourneyRoute12Shipyard':4,'Route12_Frlg':4,'Route14_Frlg':2,'NavelRock_Harbor_Frlg':5})
        stub = next(r for r in self.result['fitting_summary'] if (r['native_map'],r['component'])==('JourneyRoute12Shipyard',0))
        self.assertEqual(stub['atlas_ink_component_pixels'],2)
        self.assertIn('Global SCC including small real ink stubs and native land/Surf transitions.',self.result['pending'])

    def test_full_parent_contract_and_art_are_still_exact(self):
        from restore_generated_area_review import verify_prefix
        self.assertEqual(self.before,verify_prefix(self.path,complete=True))
        self.assertEqual(dict(self.truth.array_sha256),dict(decode_atlas(
            (self.path/'src/data/journey_world_map.h').read_text()).array_sha256))

    def test_new_route127_corner_requires_opt_in_and_keeps_actual_native_words(self):
        selected=deepcopy(self.inventory)
        selected['adapters']=[r for r in selected['adapters'] if r['native_map']=='Route127']
        result=propose_registrations(self.source,selected,self.truth,allow_extended_native_contacts=True)
        contacts=result['adapter_plan']['bindings'][0]['source_wet_mouth']
        extended=[w for w in contacts if w.get('newly_authored_corner_contact')]
        self.assertTrue(extended)
        self.assertTrue(any(not w['old_neighbor_passable'] for w in extended))
        labels,_=self.source.water_components('Route127')
        for w in extended:
            self.assertEqual(labels[tuple(w['native_tile'])],selected['adapters'][0]['component'])
            self.assertEqual(w['words'][1],self.source.word('Route127',*w['native_tile']))
            self.assertEqual(w['native_blockdata_sha256'],hashlib.sha256(self.source.read(
                self.source.layout('Route127')['blockdata_filepath'])).hexdigest())
            self.assertEqual(w['words'][0],self.source.word(w['retired_map'],*w['retired_tile']))
            self.assertTrue(w['native_word_preserved'])
        self.source.assert_unchanged()


if __name__ == '__main__':
    unittest.main()
