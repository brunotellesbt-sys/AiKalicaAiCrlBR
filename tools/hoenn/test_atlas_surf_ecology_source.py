"""Actual native triggers, implicit enums, family loss and truthful AREA rows."""
import copy
import json
import struct
import unittest

from atlas_surf_ecology import repair_dex_locations
from atlas_surf_ecology import generate_lookup
from atlas_surf_overlay import OverlaySource
from atlas_surf_source import Source
import test_atlas_surf_source_inventory as source_fixtures
from validate_atlas_surf_ecology_source import (CompiledEcology, census, compare,
                                                owner_requirements, terrain_triggers)


class AtlasEcologySourceTests(unittest.TestCase):
    def fixture(self):
        helper = source_fixtures.NativeInventoryTests()
        self.addCleanup(helper.doCleanups)
        source, overlay = helper.fixture({
            'OldWater': ('emerald', 4, 1, [0x1001, 0x1001, 0x1C01, 0x1004]),
            'OldDry': ('emerald', 3, 1, [0x3002, 0x3002, 0x3C02]),
        })
        for name in ('OldWater', 'OldDry'):
            path = f'data/maps/{name}/map.json'
            row = json.loads((source/path).read_bytes())
            row['map_type'] = 'MAP_TYPE_OCEAN_ROUTE'
            overlay.parent(path, row)
        overlay.parent('include/constants/metatile_behaviors.h', b'''
enum { MB_NORMAL, MB_TALL_GRASS, MB_RESERVED=0x80, MB_OCEAN_WATER,
 MB_FAST_WATER, MB_WATERFALL, MB_CAVE, MB_COUNT };
''')
        attrs = [0]*640
        attrs[1], attrs[2], attrs[3], attrs[4] = 0x81, 1, 0x82, 0x83
        overlay.parent('primary.bin', struct.pack('<640H', *attrs))
        overlay.parent('src/metatile_behavior.c', b'''
#define TILE_FLAG_SURFABLE (1 << 2)
#define TILE_FLAG_HAS_ENCOUNTERS (1 << 5)
static const u8 sTileBitAttributes[MB_COUNT] = {
 [MB_TALL_GRASS]=TILE_FLAG_HAS_ENCOUNTERS,
 [MB_OCEAN_WATER]=TILE_FLAG_SURFABLE|TILE_FLAG_HAS_ENCOUNTERS,
 [MB_FAST_WATER]=TILE_FLAG_SURFABLE,
 [MB_WATERFALL]=TILE_FLAG_SURFABLE,
};
bool8 MetatileBehavior_IsEncounterTile(u8 b) {return !!(sTileBitAttributes[b]&TILE_FLAG_HAS_ENCOUNTERS);}
bool8 MetatileBehavior_IsSurfableWaterOrUnderwater(u8 b) {return !!(sTileBitAttributes[b]&TILE_FLAG_SURFABLE);}
bool8 MetatileBehavior_IsLandWildEncounter(u8 b) {return !MetatileBehavior_IsSurfableWaterOrUnderwater(b)&&MetatileBehavior_IsEncounterTile(b);}
bool8 MetatileBehavior_IsWaterWildEncounter(u8 b) {
 if(b==MB_FAST_WATER&&JourneySeviiIsOpenCoast())return TRUE;
 return MetatileBehavior_IsSurfableWaterOrUnderwater(b)&&MetatileBehavior_IsEncounterTile(b);
}
bool8 MetatileBehavior_IsBridgeOverWater(u8 b) {(void)b;return FALSE;}
bool8 MetatileBehavior_IsSurfableFishableWater(u8 b) {return b==MB_OCEAN_WATER;}
bool8 MetatileBehavior_IsWaterfall(u8 b) {return b==MB_WATERFALL;}
''')
        overlay.parent('include/constants/map_types.h', b'enum MapType {MAP_TYPE_OCEAN_ROUTE, MAP_TYPE_UNDERWATER};\n')
        overlay.parent('include/constants/maps.h',b'#include "map_groups.h"\n#define MAP_GROUP(x) ((x)>>8)\n#define MAP_NUM(x) ((x)&255)\n')
        overlay.parent('src/journey_sevii_surf.c', b'''
static bool32 IsConnectedSeviiCoast(u8 group,u8 num) {return group==0&&num==1;}
''')
        overlay.parent('src/wild_encounter.c', b'''
static bool8 JourneyCoastalDepthEncounterTile(u16 behavior) {
 return gMapHeader.mapType==MAP_TYPE_UNDERWATER&&gSaveBlock1Ptr->location.mapNum==1&&behavior==MB_NORMAL;
}
''')
        overlay.parent('include/constants/species.h', b'enum {SPECIES_NONE,SPECIES_LAND=10,SPECIES_WATER,SPECIES_PHANTOM,SPECIES_EVENT=201};\n')
        overlay.parent('src/journey_wild.c', b'''
struct JourneyWildStages {u16 root;u8 count[3];u16 stages[3][8];};
struct JourneyWildPool {u16 map;u8 area,count;u16 species[24];};
static const u16 eventDex[]={201};
''')
        overlay.parent('include/journey_wild_data.h', b'''
static const struct JourneyWildStages sJourneyWildStages[]={
 [SPECIES_LAND]={SPECIES_LAND,{1,1,1},{{SPECIES_LAND},{SPECIES_LAND},{SPECIES_LAND}}},
 [SPECIES_WATER]={SPECIES_WATER,{1,1,1},{{SPECIES_WATER},{SPECIES_WATER},{SPECIES_WATER}}},
 [SPECIES_PHANTOM]={SPECIES_PHANTOM,{1,1,1},{{SPECIES_PHANTOM},{SPECIES_PHANTOM},{SPECIES_PHANTOM}}},
 [SPECIES_EVENT]={SPECIES_EVENT,{1,1,1},{{SPECIES_EVENT},{SPECIES_EVENT},{SPECIES_EVENT}}},
};
static const struct JourneyWildPool sJourneyWildPools[]={
 {MAP_OLDWATER,0,1,{SPECIES_PHANTOM}},
 {MAP_OLDWATER,1,2,{SPECIES_WATER,SPECIES_EVENT}},
 {MAP_OLDWATER,3,1,{SPECIES_WATER}},
 {MAP_OLDDRY,0,1,{SPECIES_LAND}},
};
struct JourneyFishingHabitat {u16 map;u8 percent;};
static const struct JourneyFishingHabitat sJourneyFishingHabitats[]={{MAP_OLDWATER,15}};
''')
        overlay.parent('include/journey_generation4_pools.h', b'''
static const struct JourneyWildPool sJourneyGeneration4Pools[]={
 {MAP_OLDWATER,0,1,{SPECIES_PHANTOM}}, {MAP_OLDWATER,1,1,{SPECIES_WATER}},
 {MAP_OLDWATER,3,1,{SPECIES_WATER}}, {MAP_OLDDRY,0,1,{SPECIES_LAND}},
};
''')
        overlay.parent('include/journey_habitat_data.h', b'''
struct JourneyHabitat {u16 map,count;u16 species[22];};
static const struct JourneyHabitat sJourneyHabitats[]={
 {MAP_OLDWATER,2,{SPECIES_WATER,SPECIES_PHANTOM}}, {MAP_OLDDRY,1,{SPECIES_LAND}},
};
''')
        overlay.parent('include/journey_generation4_habitats.h', b'''
static const struct JourneyHabitat sJourneyGeneration4Habitats[]={
 {MAP_OLDWATER,2,{SPECIES_WATER,SPECIES_PHANTOM}}, {MAP_OLDDRY,1,{SPECIES_LAND}},
};
''')
        overlay.parent('src/data/wild_encounters.json', dict(wild_encounter_groups=[dict(
            for_maps=True, encounters=[
                dict(map='MAP_OLDWATER', land_mons=dict(encounter_rate=20), water_mons=dict(encounter_rate=4), fishing_mons=dict(encounter_rate=0)),
                dict(map='MAP_OLDDRY', land_mons=dict(encounter_rate=20))])]))
        catalog = {str(i): dict(name=n, national_dex=i, types=[12] if i==11 else [0])
                   for i, n in ((10, 'SPECIES_LAND'), (11, 'SPECIES_WATER'),
                                (12, 'SPECIES_PHANTOM'), (201, 'SPECIES_EVENT'))}
        return source, overlay, catalog

    def overlay_fixture(self):
        source,overlay,catalog=self.fixture()
        groups=json.loads((source/'data/maps/map_groups.json').read_bytes())
        groups['group_order'].append('Atlas');groups['Atlas']=['NewSea']
        overlay.stage('data/maps/map_groups.json',json.dumps(groups))
        layouts=json.loads((source/'data/layouts/layouts.json').read_bytes())
        row=copy.deepcopy(layouts['layouts'][0]);row.update(id='LAYOUT_NEWSEA',width=2,height=1,
                                                          blockdata_filepath='new-sea.bin')
        layouts['layouts'].append(row);overlay.stage('data/layouts/layouts.json',json.dumps(layouts))
        mapping=copy.deepcopy(json.loads((source/'data/maps/OldWater/map.json').read_bytes()))
        mapping.update(id='MAP_NEWSEA',layout='LAYOUT_NEWSEA')
        overlay.stage('data/maps/NewSea/map.json',json.dumps(mapping))
        overlay.stage('new-sea.bin',struct.pack('<2H',0x1001,0x1001))
        header,implementation=generate_lookup([dict(map_id='MAP_NEWSEA',owner_map_id='MAP_OLDWATER',
                                                    packed_map_id=256,owner_packed_map_id=0)])
        overlay.stage('include/journey_atlas_ecology.h',header)
        overlay.stage('src/journey_atlas_ecology.c',implementation)
        return source,overlay,catalog

    def test_real_predicates_compile_implicit_enum_values_and_context(self):
        source, _, _ = self.fixture()
        native = CompiledEcology(Source(source)).native
        self.assertEqual(native.ecology_trigger(0, 0, 0x81)&3, 2)
        self.assertEqual(native.ecology_trigger(0, 0, 0x82)&2, 0)
        self.assertEqual(native.ecology_trigger(1, 0, 0x82)&2, 2)
        self.assertEqual(native.ecology_trigger(1, 1, 0)&2, 2)
        self.assertEqual(native.ecology_trigger(1, 0, 0)&2, 0)
        self.assertEqual(native.ecology_trigger(0, 0, 1)&3, 1)

    def test_compiled_ecology_accepts_path_and_real_staged_alias_with_new_macro(self):
        source,overlay,_=self.overlay_fixture()
        self.assertEqual(CompiledEcology(source).native.ecology_owner(256),256)
        compiled=CompiledEcology(OverlaySource(overlay))
        self.assertEqual(compiled.native.ecology_owner(256),0)
        self.assertEqual(compiled.map_registry_proof['historical_maps'],2)
        self.assertEqual(compiled.map_registry_proof['compiled_maps'],3)
        self.assertIn('constants/map_groups.h',compiled.compilation_headers_sha256)
        self.assertFalse((source/'src/journey_atlas_ecology.c').exists())
        self.assertFalse((source/'data/maps/NewSea/map.json').exists())

    def test_census_accepts_source_like_and_new_terrain_without_materializing(self):
        source,overlay,catalog=self.overlay_fixture()
        class SourceProxy:
            def __init__(self,inner):self.inner=inner
            def __getattr__(self,name):return getattr(self.inner,name)
        report=census(SourceProxy(OverlaySource(overlay)),owner_mapping={'NewSea':'OldWater'},
                      retired_maps=['OldWater'],reachable_cells={'NewSea':[[0,0],[1,0]]},catalog=catalog)
        self.assertEqual(report['aliases'],{'NewSea':'OldWater'})
        self.assertEqual(report['families']['493'],[11])
        self.assertTrue(report['graph_reachable_cells_supplied'])
        self.assertTrue(any(row['map']=='NewSea' and row['owner']=='OldWater' for row in report['map_areas']))
        self.assertFalse((source/'new-sea.bin').exists())

    def test_compiler_reads_staged_pool_bytes_instead_of_parent_headers(self):
        source,overlay,_=self.overlay_fixture()
        path='include/journey_wild_data.h'
        raw=(source/path).read_bytes();changed=raw.replace(b'{MAP_OLDWATER,15}',b'{MAP_OLDWATER,27}')
        self.assertNotEqual(changed,raw)
        overlay.stage(path,changed)
        compiled=CompiledEcology(OverlaySource(overlay))
        self.assertEqual(compiled.fishing[0],27)
        self.assertEqual(CompiledEcology(source).fishing[0],15)
        self.assertEqual((source/path).read_bytes(),raw)

    def test_staged_transitive_enum_include_is_compiled_from_logical_view(self):
        source,overlay,_=self.overlay_fixture()
        path='include/constants/metatile_behaviors.h'
        original=(source/path).read_bytes()
        overlay.stage(path,b'#include "enum_base.h"\n'+original.replace(b'MB_RESERVED=0x80',b'MB_RESERVED=ECOLOGY_BEHAVIOR_BASE'))
        overlay.stage('include/constants/enum_base.h',b'#define ECOLOGY_BEHAVIOR_BASE 0x90\n')
        compiled=CompiledEcology(OverlaySource(overlay))
        self.assertEqual(compiled.native.ecology_trigger(256,0,0x91)&3,2)
        self.assertIn('constants/enum_base.h',compiled.compilation_headers_sha256)
        self.assertEqual((source/path).read_bytes(),original)
        self.assertFalse((source/'include/constants/enum_base.h').exists())

    def test_compilation_rejects_cached_identity_tampering(self):
        _,overlay,_=self.overlay_fixture()
        view=OverlaySource(overlay)
        view.identities['OldWater']=7
        with self.assertRaisesRegex(ValueError,'authenticated logical registry'):
            CompiledEcology(view)

    def test_staged_aliases_must_match_requested_owner_contract(self):
        _,overlay,catalog=self.overlay_fixture()
        with self.assertRaisesRegex(ValueError,'aliases differ'):
            census(OverlaySource(overlay),owner_mapping={'NewSea':'OldDry'},catalog=catalog)

    def test_pool_union_is_not_a_catchability_claim(self):
        source, _, catalog = self.fixture()
        report = census(source, catalog=catalog)
        self.assertEqual(report['catchable_family_counts'], {'493': 2, '1025': 2})
        self.assertEqual(report['pool_union_family_counts'], {'493': 3, '1025': 3})
        self.assertEqual(report['families']['1025'], [10, 11])
        self.assertFalse(report['compiled_rom_validated'])
        self.assertFalse(report['global_reachability_proven'])
        self.assertNotIn(201, report['families']['1025'])
        grass = next(r for r in report['land_trigger_maps'] if r['map']=='OldDry')
        self.assertEqual(grass['cells'], 2)  # Collision bits exclude the third tile.
        self.assertEqual([r['area'] for r in owner_requirements(report, ['OldWater'])], [1, 3])

    def test_reachable_cells_and_fishing_waterfall_guard(self):
        source, _, catalog = self.fixture()
        report = census(source, reachable_cells={'OldWater': [[0,0], [1,0]]}, catalog=catalog)
        self.assertEqual(report['families']['493'], [11])
        self.assertTrue(report['graph_reachable_cells_supplied'])
        self.assertFalse(report['global_reachability_proven'])
        inputs = Source(source)
        triggers, _ = terrain_triggers(inputs, CompiledEcology(inputs), 'OldWater')
        self.assertEqual(triggers[1], [(0,0), (1,0)])
        self.assertEqual(triggers[3], [(1,0), (0,0)])

    def test_family_loss_and_native_header_rate_are_visible(self):
        source, overlay, catalog = self.fixture()
        before = census(source, catalog=catalog)
        path = 'src/data/wild_encounters.json'
        data = json.loads((source/path).read_bytes())
        data['wild_encounter_groups'][0]['encounters'][1]['land_mons']['encounter_rate'] = 0
        overlay.parent(path, data)
        after = census(source, catalog=catalog)
        proof = compare(before, after)
        self.assertFalse(proof['preserved'])
        self.assertEqual(proof['missing_families'], {'493':[10], '1025':[10]})

    def dex_fixture(self):
        catalog = {'10': dict(name='SPECIES_LAND'), '11': dict(name='SPECIES_WATER'), '12': dict(name='SPECIES_PHANTOM')}
        base = dict(schema='atlas-surf-ecology-source-v1', native_c_compiled=True,
                    source_manifest_sha256='a'*64, retired_maps=[],
                    map_constants={'OldWater':'MAP_OLDWATER', 'Native':'MAP_NATIVE'},
                    map_areas=[dict(map='OldWater', species={'493':[11], '1025':[11]})])
        after = dict(schema=base['schema'], native_c_compiled=True,
                     source_manifest_sha256='b'*64, retired_maps=['OldWater'],
                     graph_reachable_cells_supplied=True,
                     map_areas=[dict(map='NewSea', owner='OldWater', species={'493':[11], '1025':[11]}, trigger_sample=[[3,2]])])
        plan = dict(scale=8,chunks=[dict(name='NewSea', id='MAP_NEWSEA',origin=[80,160],
                                        width=8,height=8, ecology_owner='OldWater')])
        header = ('struct JourneyWorldDexLocation {u16 species,map;u8 x,y,fixed,cap;};\n'
                  'static const struct JourneyWorldDexLocation sWorldDexLocations[]={\n'
                  '{SPECIES_WATER,MAP_OLDWATER,40,40,0,9},\n'
                  '{SPECIES_WATER,MAP_OLDWATER,40,40,0,4},\n'
                  '{SPECIES_PHANTOM,MAP_OLDWATER,40,40,0,9},\n'
                  '{SPECIES_LAND,MAP_NATIVE,5,5,0,9},\n'
                  '{SPECIES_WATER,MAP_NATIVE,6,6,1,0},\n};\n')
        return header, base, after, plan, catalog

    def test_dex_uses_real_affine_trigger_removes_only_dead_claim(self):
        header, before, after, plan, catalog = self.dex_fixture()
        result, proof = repair_dex_locations(header,before,after,plan,catalog)
        self.assertIn('{SPECIES_WATER,MAP_NEWSEA,10,20,0,9}',result)
        self.assertIn('{SPECIES_WATER,MAP_NEWSEA,10,20,0,4}',result)
        self.assertIn('{SPECIES_LAND,MAP_NATIVE,5,5,0,9}',result)
        self.assertIn('{SPECIES_WATER,MAP_NATIVE,6,6,1,0}',result)
        self.assertNotIn('SPECIES_PHANTOM,',result)
        self.assertEqual(len(proof['removed_dead_claims']),1)
        self.assertFalse(proof['compiled_rom_validated'])

    def test_dex_rejects_lost_effective_species_and_unreachable_claims(self):
        header, before, after, plan, catalog = self.dex_fixture()
        broken = copy.deepcopy(after)
        broken['map_areas'][0]['species']['1025']=[]
        with self.assertRaisesRegex(ValueError,'Previously effective'):
            repair_dex_locations(header,before,broken,plan,catalog)
        after['graph_reachable_cells_supplied']=False
        with self.assertRaisesRegex(ValueError,'graph-reachable'):
            repair_dex_locations(header,before,after,plan,catalog)

    def test_dex_rejects_wrong_owner_outside_map_and_fixed_event_guess(self):
        header, before, after, plan, catalog = self.dex_fixture()
        for change in (lambda p:p['chunks'][0].update(ecology_owner='Another'),
                       lambda p:p['chunks'][0].update(width=2)):
            broken=copy.deepcopy(plan);change(broken)
            with self.assertRaises(ValueError):
                repair_dex_locations(header,before,after,broken,catalog)
        header=header.replace('40,40,0,9','40,40,1,9')
        with self.assertRaisesRegex(ValueError,'Fixed event'):
            repair_dex_locations(header,before,after,plan,catalog)


if __name__ == '__main__':
    unittest.main()
