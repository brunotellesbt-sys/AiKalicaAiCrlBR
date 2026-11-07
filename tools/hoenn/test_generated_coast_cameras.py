"""Reject unsafe apron owners and incomplete native camera evidence."""
import copy
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

import generated_coast_cameras as cameras
import validate_generated_coast_cameras as native
from marine_corner_coherence import Source

ROOT = Path(__file__).resolve().parents[2]
PARENT = ROOT/'.local/coast-scenery-review-src'


class World:
    def __init__(self, directory):
        self.source = Path(directory)
        self.maps, self.layouts, self.words, self.by_id = {}, {}, {}, {}

    def add(self, name, width=10, height=10, block=0x112B, border=0x1643):
        self.maps[name] = dict(id='MAP_'+name, layout=name, connections=[])
        self.layouts[name] = dict(width=width, height=height, layout_version='frlg',
            border_width=2, border_height=2, border_filepath=name+'.bin',
            primary_tileset='Primary', secondary_tileset='Secondary')
        self.words[name] = [block]*(width*height)
        self.by_id['MAP_'+name] = name
        (self.source/(name+'.bin')).write_bytes(struct.pack('<4H',*([border]*4)))
        return name

    def connect(self, name, other, direction, offset=0):
        self.maps[name]['connections'].append(dict(map='MAP_'+other, direction=direction, offset=offset))

    def layout(self, name):
        return self.layouts[name]

    def word(self, name, x, y):
        layout = self.layout(name)
        assert 0 <= x < layout['width'] and 0 <= y < layout['height']
        return self.words[name][y*layout['width']+x]


class ApronPolicyTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='coast-policy-',dir='/tmp')
        self.addCleanup(directory.cleanup)
        self.world = World(directory.name)

    def drawing(self, name, cell):
        return cameras._owner_view(self.world,dict(map=name,cell=list(cell)))

    def test_closest_direct_rectangle_beats_farther_actual_water(self):
        world = self.world
        current = world.add(cameras.SCOPED_MAPS[0])
        west = world.add('West',width=8,height=8)
        north = world.add('North',width=8,height=8)
        world.connect(current,west,'left')
        world.connect(current,north,'up',4)
        owners = cameras.apron_owner(world,current,2,-1)
        self.assertEqual([(r['map'],r['distance']) for r in owners],[('North',2)])
        with patch.object(cameras,'compatible',side_effect=lambda _w,_a,_b,block:block & 1023):
            view = cameras.source_apron_view(world,current,2,-1)
        self.assertTrue(view['accepted'])
        self.assertEqual(view['metatile'],0x243)
        self.assertEqual(view['owners'][0]['drawing']['kind'],'owner-border')

    def tied_world(self, equal=False):
        world = self.world
        current = world.add(cameras.SCOPED_MAPS[0])
        west = world.add('West',border=0x1643)
        north = world.add('North',border=0x1643 if equal else 0x112B)
        world.connect(current,west,'left')
        world.connect(current,north,'up')
        return current

    def test_disagreeing_tied_owners_are_rejected_independent_of_order(self):
        current = self.tied_world()
        with patch.object(cameras,'compatible',side_effect=lambda _w,_a,_b,block:block & 1023):
            for reverse in (False,True):
                if reverse:
                    self.world.maps[current]['connections'].reverse()
                view = cameras.source_apron_view(self.world,current,-1,-1)
                self.assertFalse(view['accepted'])
                self.assertIsNone(view['metatile'])
                self.assertEqual(len(view['owners']),2)

    def test_agreeing_tied_owners_need_all_banks_to_be_compatible(self):
        current = self.tied_world(equal=True)
        with patch.object(cameras,'compatible',return_value=0x243):
            self.assertTrue(cameras.source_apron_view(self.world,current,-1,-1)['accepted'])
        with patch.object(cameras,'compatible',side_effect=lambda _w,name,_target,_block:None if name == 'North' else 0x243):
            self.assertFalse(cameras.source_apron_view(self.world,current,-1,-1)['accepted'])

    def test_no_owner_cannot_invent_a_canonical_apron(self):
        current = self.world.add(cameras.SCOPED_MAPS[0])
        self.assertEqual(cameras.apron_owner(self.world,current,-1,-1),[])
        self.assertFalse(cameras.source_apron_view(self.world,current,-1,-1)['accepted'])

    def test_native_strips_use_seven_north_south_west_and_eight_east(self):
        world = self.world
        owner = world.add('Owner')
        directions = {
            'left':((-7,2),(-8,2)),
            'right':((17,2),(18,2)),
            'up':((2,-7),(2,-8)),
            'down':((2,16),(2,17)),
        }
        for index,(direction,(inside,outside)) in enumerate(directions.items()):
            with self.subTest(direction=direction):
                other = world.add('Donor'+direction,32,32,block=0x1100+index)
                world.maps[owner]['connections'] = []
                world.connect(owner,other,direction)
                self.assertEqual(self.drawing(owner,inside)['map'],other)
                self.assertEqual(self.drawing(owner,inside)['kind'],'owner-native-connection')
                self.assertEqual(self.drawing(owner,outside)['kind'],'owner-border')

    def test_perpendicular_overhang_is_native_connection_art(self):
        world = self.world
        owner = world.add('Owner')
        for direction,cell in [('left',(-1,-2)),('right',(10,-2)),('up',(-2,-1)),('down',(-2,10))]:
            with self.subTest(direction=direction):
                donor = world.add('Donor'+direction,32,32,block=0x1234)
                world.maps[owner]['connections'] = []
                world.connect(owner,donor,direction,-5)
                draw = self.drawing(owner,cell)
                self.assertEqual((draw['map'],draw['block']),(donor,0x1234))

    def test_last_matching_connection_wins_but_actual_owner_cells_remain(self):
        world = self.world
        owner = world.add('Owner',block=0x112B)
        west = world.add('West',32,32,block=0x1110)
        north = world.add('North',32,32,block=0x1111)
        world.connect(owner,west,'left',-2)
        world.connect(owner,north,'up',-2)
        self.assertEqual(self.drawing(owner,(-1,-1))['block'],0x1111)
        world.maps[owner]['connections'].reverse()
        self.assertEqual(self.drawing(owner,(-1,-1))['block'],0x1110)
        self.assertEqual(self.drawing(owner,(0,0)),dict(kind='owner-actual',map=owner,cell=[0,0],block=0x112B))

    def test_signed_border_modulo_preserves_pattern_phase(self):
        owner = self.world.add('Owner')
        (self.world.source/'Owner.bin').write_bytes(struct.pack('<4H',11,12,13,14))
        self.assertEqual(self.drawing(owner,(-1,-1))['block'],14)
        self.assertEqual(self.drawing(owner,(-2,-1))['block'],13)

    def test_metatile_attributes_words_graphics_palettes_and_callback_must_match(self):
        world = self.world
        a,b = world.add('A'),world.add('B')
        world.layouts[a]['primary_tileset'] = 'A'
        world.layouts[b]['primary_tileset'] = 'B'
        fields = dict(tiles='Tiles',palettes='Palettes',callback='Animation')
        raw = dict(metatiles=bytes(640*16),metatileAttributes=bytes(640*4))
        def bank(_source,name):
            return first if name == 'A' else second
        first = (fields,raw)
        second = copy.deepcopy(first)
        with patch.object(cameras,'_bank',side_effect=bank):
            self.assertEqual(cameras.compatible(world,a,b,0x112B),0x12B)
            for field in ('tiles','palettes','callback'):
                with self.subTest(field=field):
                    second = (dict(fields,**{field:'Different'}),raw)
                    self.assertIsNone(cameras.compatible(world,a,b,0x112B))
            for key,stride in (('metatiles',16),('metatileAttributes',4)):
                with self.subTest(binary=key):
                    changed = bytearray(raw[key]); changed[0x12B*stride] = 1
                    second = (fields,dict(raw,**{key:bytes(changed)}))
                    self.assertIsNone(cameras.compatible(world,a,b,0x112B))

    def test_cross_format_translation_accepts_only_established_native_families(self):
        a,b = self.world.add('Frlg'),self.world.add('Emerald')
        self.world.layouts[b]['layout_version'] = 'emerald'
        self.assertEqual(cameras.compatible(self.world,a,b,0x112B),0x170)
        self.assertEqual(cameras.compatible(self.world,b,a,0x1170),0x12B)
        self.assertIsNone(cameras.compatible(self.world,a,b,0x13FF))
        self.assertIsNone(cameras.compatible(self.world,b,a,0x13FF))


@unittest.skipUnless((PARENT/'.journey-coast-scenery-review').is_file(),'Frozen layer 170 source unavailable')
class FrozenCameraSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = Source(PARENT)

    def test_two_pops_and_three_controls_have_explicit_source_owners(self):
        for case in cameras.REPRO_CASES+cameras.CONTROL_CASES:
            with self.subTest(case=case['label']):
                self.assertEqual(cameras.legacy_metatile(self.inputs,case['map'],*case['cell']),0x243)
                view = cameras.source_apron_view(self.inputs,case['map'],*case['cell'])
                self.assertTrue(view['accepted'])
                self.assertEqual(view['metatile'],case['expected_metatile'])
                self.assertTrue(view['owners'])

    def test_real_fill21_tie_remains_rejected_without_changing_terrain(self):
        view = cameras.source_apron_view(self.inputs,'JourneyWorldFill21Right',-1,41)
        self.assertFalse(view['accepted'])
        self.assertIsNone(view['metatile'])
        self.assertEqual({row['owner']['distance'] for row in view['owners']},{7})
        self.assertEqual({row['metatile'] for row in view['owners']},{0x12B,0x243})

    def test_apron_repair_changes_only_drawing_runtime_and_keeps_eleven_east_openings(self):
        before = (PARENT/cameras.PATH).read_bytes()
        class Capture:
            source = PARENT
            expected = {cameras.PATH:hashlib.sha256(before).hexdigest()}
            outputs = {}
            def stage(self,path,content):
                self.outputs[path] = content.encode() if isinstance(content,str) else content
        layer = Capture()
        cameras.repair(layer)
        self.assertEqual(set(layer.outputs),{cameras.PATH})
        after = layer.outputs[cameras.PATH].decode()
        self.assertEqual(after.replace(cameras.C_HELPERS+'\n','').replace(cameras.GATE,''),before.decode())
        openings = cameras.seven_east_openings(self.inputs)
        expected = [dict(map=cameras.OPENING_MAP,player=[16,y],direction='right',
                         neighbor=cameras.OPENING_NEIGHBOR,target=[0,y],blocks=[0x112B,0x112B]) for y in range(1,12)]
        self.assertEqual(openings,expected)


def native_fixture(directory, *, baseline):
    """Small synthetic attachments exercise the verifier, without emulating ROMs."""
    directory.mkdir(parents=True,exist_ok=True)
    captures,fixtures,controls,cases,openings,bumps = [],[],[],[],[],[]

    def picture(label):
        path = directory/(label+'.png')
        Image.new('RGB',(240,160),(0,0,0)).save(path)
        row = dict(file=path.name,sha256=native.digest(path))
        captures.append(row)
        return row

    def state(name,tile):
        return dict(map=name,tile=list(tile),surfing=True)

    def grid(cell,mid, *, actual=False):
        return dict(cell=list(cell),block=0x112B if actual else 1023,metatile=mid,
                    collision=0 if actual else 1,elevation=1 if actual else 0,
                    border_id=2 if actual else 0xFFFFFFFF)

    def view(name,tile,cell,mid,label, *, actual=False):
        pixels = dict(undefined_cells_included=True,actual_hardware_bg_words_and_scanout_checked=True,
            sprites_and_opaque_ui_explicitly_excluded=True,mismatches_not_discarded=True,
            cells=[dict(cell=list(cell),expected_metatile=mid,native_metatile=mid,layer=0,
                        definition_words=[0]*8,quadrants=[0,1,2,3],checked_pixels=64,
                        actual_bg_words=[dict(quadrant=q,words=[0,0,0x3014]) for q in range(4)],
                        samples=[[i+1,1,0,0,0,i % 4] for i in range(16)])])
        return dict(state=state(name,tile),grid=grid(cell,mid,actual=actual),pixels=pixels,capture=picture(label))

    for case in native.CASES:
        label = case['label']; first = 0x243 if baseline else case['expected_metatile']
        before = view(case['map'],case['player'],case['cell'],first,label+'-before')
        after = view(case['neighbor'],case['target'],case['neighbor_cell'],case['expected_metatile'],label+'-after',actual=case == cameras.REPRO_CASES[1])
        returned = view(case['map'],case['player'],case['cell'],first,label+'-returned')
        cases.append(dict(case=copy.deepcopy(case),before=before,after=after,returned=returned,
            outbound_and_return_with_controllers=True,parent_pop_observed=baseline and case in cameras.REPRO_CASES))
        fixtures.append(dict(label=label,**state(case['map'],case['player'])))
        controls.extend((dict(label=label,key=native.KEY[case['direction']],frames=12),
                         dict(label=label,key=native.KEY[native.OPPOSITE[case['direction']]],frames=12)))
    for y in range(1,12):
        label = 'seven-east-'+str(y).zfill(2)
        opening = dict(map=cameras.OPENING_MAP,player=[16,y],direction='right',
                       neighbor=cameras.OPENING_NEIGHBOR,target=[0,y],blocks=[0x112B,0x112B])
        before = dict(state=state(cameras.OPENING_MAP,[16,y]),grid=grid([16,y],0x12B,actual=True))
        after = dict(state=state(cameras.OPENING_NEIGHBOR,[0,y]),grid=grid([0,y],0x12B,actual=True))
        returned = dict(copy.deepcopy(before),capture=picture(label+'-returned'))
        openings.append(dict(opening=opening,before=before,after=after,returned=returned,outbound_and_return_with_controllers=True))
        fixtures.append(dict(label=label,**state(cameras.OPENING_MAP,[16,y])))
        controls.extend((dict(label=label,key=16,frames=12),dict(label=label,key=32,frames=12)))
    for case in native.BUMPS:
        mid = 0x243 if baseline else case['expected_metatile']
        seen = view(case['map'],case['player'],case['cell'],mid,case['label']+'-blocked')
        seen.pop('pixels')  # The adjacent Surf sprite occludes these bump views.
        bumps.append(dict(case=copy.deepcopy(case),before=state(case['map'],case['player']),
            after=state(case['map'],case['player']),target=copy.deepcopy(seen['grid']),
            held_frames=48,native_directional_input_blocked=True,view=seen))
        fixtures.append(dict(label=case['label'],**state(case['map'],case['player'])))
        controls.append(dict(label=case['label'],key=native.KEY[case['direction']],frames=48))
    hashes = {'src/fieldmap.c':'c'*64,**{'input'+str(i):'d'*64 for i in range(17)}}
    return dict(kind='generated-coast-cameras-native',passed=True,baseline=baseline,
        rom_sha256=native.contract.PARENT_ROM_SHA256 if baseline else 'a'*64,
        elf_sha256=native.contract.PARENT_ELF_SHA256 if baseline else 'b'*64,
        native_validation_performed=True,initial_placements_and_surf_state_are_fixtures=True,
        private_query_trampoline_declared=True,only_read_only_queries_after_placement=True,
        gameplay_scripts_not_injected_after_placement=True,
        no_midtrip_position_collision_elevation_camera_palette_or_vram_writes=True,
        source_and_rom_unchanged=True,source_inputs_sha256=hashes,scoped_maps=list(cameras.SCOPED_MAPS),
        full_world_camera_certified=False,full_campaign_playthrough=False,corner_cases=cases,
        seven_east_openings=openings,undefined_boundary_bumps=bumps,fixtures=fixtures,
        controls=controls,queries=[dict(label='test',function='MapGridGetCollisionAt',arguments=[7,7])],
        captures=captures,components=[])


class NativeCameraEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='coast-proof-tests-',dir='/tmp')
        cls.directory = Path(cls.temporary.name)
        parent = native_fixture(cls.directory/'parent170',baseline=True)
        path = cls.directory/'parent170/coast.json'
        path.write_text(json.dumps(parent,indent=2)+'\n')
        cls.report = native_fixture(cls.directory,baseline=False)
        cls.report['parent_baseline'] = parent
        cls.report['components'] = [dict(kind=parent['kind'],file='parent170/coast.json',sha256=native.digest(path))]

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def reject(self, mutate):
        report = copy.deepcopy(self.report)
        mutate(report)
        with self.assertRaises(AssertionError):
            native.verify_report(report,self.directory,self.report['rom_sha256'])

    def test_complete_fixture_and_nested_parent_pass(self):
        self.assertTrue(native.verify_report(self.report,self.directory,self.report['rom_sha256']))

    def test_wrong_reef_missing_return_and_lost_mouth_control_fail(self):
        self.reject(lambda r:r['corner_cases'][0]['before']['grid'].update(metatile=0x243))
        self.reject(lambda r:r['corner_cases'][0]['returned']['state'].update(tile=[1,2]))
        self.reject(lambda r:r['corner_cases'].pop(2))

    def test_missing_quadrant_or_incorrect_hardware_words_fail(self):
        self.reject(lambda r:r['corner_cases'][0]['before']['pixels']['cells'][0]['quadrants'].pop())
        self.reject(lambda r:r['corner_cases'][0]['before']['pixels']['cells'][0]['actual_bg_words'][0].update(words=[1,0,0x3014]))

    def test_rgb_witnesses_must_match_the_rehashed_attachment(self):
        report = copy.deepcopy(self.report)
        view = report['corner_cases'][0]['before']
        path = self.directory/view['capture']['file']
        original = path.read_bytes()
        try:
            image = Image.open(path).convert('RGB')
            sample = view['pixels']['cells'][0]['samples'][0]
            image.putpixel(tuple(sample[:2]),(255,0,255))
            image.save(path)
            sha = native.digest(path)
            view['capture']['sha256'] = sha
            next(row for row in report['captures'] if row['file'] == path.name)['sha256'] = sha
            with self.assertRaisesRegex(AssertionError,'Native corner pixels'):
                native.verify_report(report,self.directory,report['rom_sha256'])
        finally:
            path.write_bytes(original)

    def test_undefined_art_cannot_open_movement_or_remove_invalid_border(self):
        self.reject(lambda r:r['corner_cases'][0]['before']['grid'].update(collision=0))
        self.reject(lambda r:r['corner_cases'][0]['before']['grid'].update(elevation=1))
        self.reject(lambda r:r['corner_cases'][0]['before']['grid'].update(border_id=1))
        self.reject(lambda r:r['undefined_boundary_bumps'][1]['after'].update(tile=[-1,47]))

    def test_all_eleven_openings_and_native_controller_inputs_are_required(self):
        self.reject(lambda r:r['seven_east_openings'].pop())
        self.reject(lambda r:r['seven_east_openings'][5]['after']['grid'].update(block=0x1643))
        self.reject(lambda r:r['controls'][0].update(key=16))
        self.reject(lambda r:r['controls'][0].update(frames=0))
        self.reject(lambda r:r['queries'].append(dict(label='test',function='SetPlayerAvatarTransitionFlags',arguments=[8])))

    def test_parent_hash_pop_count_component_and_exact_baseline_are_required(self):
        self.reject(lambda r:r['components'][0].update(sha256='f'*64))
        self.reject(lambda r:r['parent_baseline'].update(rom_sha256='f'*64))
        self.reject(lambda r:r['parent_baseline']['corner_cases'][0].update(parent_pop_observed=False))
        self.reject(lambda r:r['parent_baseline'].update(baseline=False))

    def test_rehashed_parent_component_still_needs_pinned_hashes_and_two_pops(self):
        path = self.directory/'parent170/coast.json'
        original = path.read_bytes()
        for mutate in (lambda r:r.update(rom_sha256='f'*64),
                       lambda r:r['corner_cases'][0].update(parent_pop_observed=False)):
            with self.subTest(mutate=mutate):
                report = copy.deepcopy(self.report)
                try:
                    mutate(report['parent_baseline'])
                    path.write_text(json.dumps(report['parent_baseline'],indent=2)+'\n')
                    report['components'][0]['sha256'] = native.digest(path)
                    with self.assertRaises(AssertionError):
                        native.verify_report(report,self.directory,report['rom_sha256'])
                finally:
                    path.write_bytes(original)


if __name__ == '__main__':
    unittest.main()
