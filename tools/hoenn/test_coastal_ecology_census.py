"""Regressions for the independent compiled-ROM aquatic census."""
import copy
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch

from validate_coastal_ecology import census,eligibility,framebuffer_visibility


class AquaticInventory(unittest.TestCase):
    def test_city_coast_is_required_even_without_any_old_encounter_header(self):
        for name in ('MauvilleCity','RustboroCity','SixIsland','PalletTown_Frlg'):
            self.assertEqual(eligibility(name,'MAP_TYPE_CITY',{21:8}), (True,None))

    def test_ordinary_fast_coast_and_underwater_no_surfacing_are_not_ignored(self):
        self.assertEqual(eligibility('SixIsland','MAP_TYPE_TOWN',{44:40}), (True,None))
        self.assertEqual(eligibility('Underwater_Route105','MAP_TYPE_UNDERWATER',{25:195,0:24}), (True,None))

    def test_normal_floor_is_a_habitat_only_in_the_five_added_depth_maps(self):
        for suffix in ('Abismo','Dimensoes','Mares','Origens','Profundezas'):
            self.assertEqual(eligibility('JourneyDepth'+suffix,'MAP_TYPE_UNDERWATER',{0:992}), (True,None))
        self.assertFalse(eligibility('Underwater_Route128','MAP_TYPE_UNDERWATER',{0:491,108:1})[0])
        self.assertFalse(eligibility('Underwater_SealedChamber','MAP_TYPE_UNDERWATER',{0:315,108:1})[0])

    def test_transit_water_facilities_and_indoor_rooms_are_explicit_exceptions(self):
        for name,map_type,behaviors,retired in (
            ('OneIsland_KindleRoad_EmberSpa_Frlg','MAP_TYPE_UNDERGROUND',{19:4},False),
            ('BattleFrontier_OutsideWest','MAP_TYPE_ROUTE',{21:850},False),
            ('SafariZone_East_Frlg','MAP_TYPE_ROUTE',{21:52},False),
            ('JourneySootopolisHarbor','MAP_TYPE_INDOOR',{21:56},False),
            ('JourneyHoennCrossing','MAP_TYPE_OCEAN_ROUTE',{21:880},True),
        ):
            required,reason=eligibility(name,map_type,behaviors,retired)
            self.assertFalse(required)
            self.assertTrue(reason)


class CompiledCensus(unittest.TestCase):
    """Drive the census with ROM-table observations without invoking a build."""
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.source=Path(self.temporary.name)
        (self.source/'src').mkdir()
        (self.source/'pokeemerald.elf').write_bytes(b'compiled fixture elf')
        self.wild=self.source/'src/wild_encounter.c'
        self.wild.write_text('static bool8 JourneyCoastalDepthEncounterTile(void)\n{\n'
            ' return MAP_JOURNEY_DEPTH_MARES && MB_NORMAL;\n}\n')
        (self.source/'src/metatile_behavior.c').write_text(
            'bool8 MetatileBehavior_IsWaterWildEncounter(u32 metatileBehavior)\n{\n'
            ' return metatileBehavior == MB_FAST_WATER && JourneySeviiIsOpenCoast();\n}\n')
        self.rows=[self.row('Coast','MAP_COAST',1,{16:40}),
            self.row('JourneyDepthMares','MAP_JOURNEY_DEPTH_MARES',2,{0:40},underwater=True)]
        self.headers={mid:dict(index=mid,times=[dict(water_mons=dict(rate=6,species=[72]*5),
            fishing_mons=dict(rate=25,species=[72]*10)) for _ in range(4)]) for mid in (1,2)}
        self.pools={cap:{(1,1):[72],(1,3):[72],(2,1):[72]} for cap in (493,1025)}
        self.tables=SimpleNamespace(rom=b'compiled fixture rom',
            abi=dict(time_count=4,time_enabled=1,time_disable_fallback=1,time_fallback=0),
            symbols={'sTileBitAttributes':(100,256)},catalog={'72':dict(national_dex=72)},
            header_tables=lambda:self.headers,
            pool_tables=lambda name:self.pools[493 if name=='sJourneyGeneration4Pools' else 1025],
            stage_members=Mock(return_value=[72]),integer=lambda address,size:3 if address==116 else 0)

    def row(self,name,map_id,mid,behaviors,underwater=False,required=True):
        return dict(map=name,map_id=map_id,packed_map_id=mid,type='MAP_TYPE_UNDERWATER' if underwater else 'MAP_TYPE_ROUTE',
            required=required,exception=None if required else 'native facility uses separate encounter rules',
            water_cells=sum(behaviors.values()),behavior_counts=behaviors,underwater=underwater,
            connected_sevii_coast=False)

    def run_census(self,allow_gaps=False):
        with patch('validate_coastal_ecology.RomTables',return_value=self.tables), \
             patch('validate_coastal_ecology.aquatic_candidates',return_value=copy.deepcopy(self.rows)):
            return census(self.source,allow_gaps)

    def test_complete_inventory_checks_both_caps_and_every_native_time_period(self):
        report=self.run_census()
        self.assertTrue(report['passed'])
        self.assertEqual((report['aquatic_maps'],report['required_aquatic_maps'],report['quiet_or_retired_maps']),(2,2,0))
        self.assertEqual(set(report['coverage_by_cap']),{'493','1025'})
        for row in report['maps']:
            self.assertEqual([r['time'] for r in row['time_periods']],list(range(4)))
            self.assertTrue(row['standard_wild_trigger_behaviors'])
        self.assertEqual({call.args[2] for call in self.tables.stage_members.call_args_list},{493,1025})
        self.assertEqual({call.args[1] for call in self.tables.stage_members.call_args_list},{0,1,2})

    def test_missing_old_header_cannot_remove_a_real_water_map_from_inventory(self):
        del self.headers[1]
        with self.assertRaisesRegex(AssertionError,'Missing aquatic encounters'):self.run_census()
        report=self.run_census(allow_gaps=True)
        self.assertFalse(report['passed'])
        self.assertEqual(report['missing_headers'],['Coast'])
        self.assertEqual(report['missing_fishing_headers'],['Coast'])
        self.assertEqual(report['required_map_names'],['Coast','JourneyDepthMares'])

    def test_empty_night_table_is_a_gap_when_native_fallback_is_disabled(self):
        self.headers[1]['times'][3]['water_mons']=None
        report=self.run_census(allow_gaps=True)
        self.assertEqual(report['missing_headers'],['Coast'])
        self.assertEqual(report['maps'][0]['time_periods'][3]['species'],[])

    def test_enabled_native_time_fallback_uses_the_compiled_fallback_period(self):
        self.tables.abi['time_disable_fallback']=0
        self.headers[1]['times'][3]['water_mons']=None
        report=self.run_census()
        self.assertEqual(report['maps'][0]['time_periods'][3]['effective_time'],0)

    def test_fishing_header_and_each_cap_fishing_pool_are_required_on_surface_water(self):
        self.headers[1]['times'][0]['fishing_mons']=None
        del self.pools[493][1,3]
        report=self.run_census(allow_gaps=True)
        self.assertEqual(report['missing_fishing_headers'],['Coast'])
        self.assertEqual(report['coverage_by_cap']['493']['missing_fishing_pools'],['Coast'])
        self.assertEqual(report['coverage_by_cap']['1025']['missing_fishing_pools'],[])

    def test_underwater_maps_do_not_require_fishing_headers_or_pools(self):
        for time in self.headers[2]['times']:time['fishing_mons']=None
        self.assertTrue(self.run_census()['passed'])

    def test_fishing_coverage_includes_night_and_native_fallback(self):
        self.headers[1]['times'][3]['fishing_mons']=None
        report=self.run_census(allow_gaps=True)
        self.assertEqual(report['missing_fishing_headers'],['Coast'])
        self.assertEqual(report['maps'][0]['fishing_time_periods'][3]['species'],[])
        self.tables.abi['time_disable_fallback']=0
        report=self.run_census()
        self.assertEqual(report['maps'][0]['fishing_time_periods'][3]['effective_time'],0)

    def test_generation_four_missing_water_pool_is_reported_separately(self):
        del self.pools[493][2,1]
        report=self.run_census(allow_gaps=True)
        self.assertEqual(report['coverage_by_cap']['493']['missing_pools'],['JourneyDepthMares'])
        self.assertEqual(report['coverage_by_cap']['1025']['missing_pools'],[])

    def test_empty_late_phase_and_event_root_are_rejected(self):
        self.tables.stage_members.side_effect=lambda root,stage,cap,water:[] if stage==2 and cap==493 else [72]
        self.pools[1025][1,1]=[137]
        self.tables.catalog['137']=dict(national_dex=137)
        report=self.run_census(allow_gaps=True)
        self.assertIn(['JourneyDepthMares',1,72,2],report['coverage_by_cap']['493']['empty_phases'])
        self.assertEqual(report['coverage_by_cap']['1025']['invalid_roots'],[['Coast',1,137]])

    def test_fast_water_requires_the_native_connected_coast_guard(self):
        self.rows[0]['behavior_counts']={44:40}
        report=self.run_census(allow_gaps=True)
        self.assertEqual(report['missing_standard_wild_triggers'],['Coast'])
        self.rows[0]['connected_sevii_coast']=True
        self.assertTrue(self.run_census()['passed'])

    def test_new_depth_floor_requires_its_named_runtime_predicate(self):
        self.wild.write_text('/* no depth encounter predicate */\n')
        self.assertEqual(self.run_census(allow_gaps=True)['missing_standard_wild_triggers'],['JourneyDepthMares'])

    def test_no_surfacing_behavior_requires_its_named_native_depth_guard(self):
        self.rows[1].update(map='Underwater_Route105',map_id='MAP_UNDERWATER_ROUTE105',behavior_counts={25:40})
        self.assertEqual(self.run_census(allow_gaps=True)['missing_standard_wild_triggers'],['Underwater_Route105'])
        self.wild.write_text('static bool8 JourneyCoastalDepthEncounterTile(void)\n{\n'
            ' return MAP_UNDERWATER_ROUTE105 && MB_NO_SURFACING;\n}\n')
        self.assertTrue(self.run_census()['passed'])

    def test_quiet_facility_keeps_an_explicit_inventory_row_without_pools(self):
        self.rows.append(self.row('SafariZone','MAP_SAFARI_ZONE',3,{16:40},required=False))
        report=self.run_census()
        self.assertEqual((report['aquatic_maps'],report['required_aquatic_maps'],report['quiet_or_retired_maps']),(3,2,1))
        self.assertTrue(report['maps'][2]['exception'])


class VisibleNativeCapture(unittest.TestCase):
    def test_black_and_nearly_empty_intro_frames_are_rejected(self):
        for pixels in (bytes(240*160*4),bytes((255,255,255,255))*240+bytes(240*159*4)):
            with self.assertRaisesRegex(AssertionError,'blank or faded'):framebuffer_visibility(pixels)

    def test_rendered_native_frame_records_direct_framebuffer_evidence(self):
        pixels=b''.join(bytes((32+i%64,64+i%32,128+i%16,255)) for i in range(240*160))
        report=framebuffer_visibility(pixels)
        self.assertEqual(report['framebuffer_nonblack_pixels'],240*160)
        self.assertEqual(report['framebuffer_distinct_rgb_colors'],64)


if __name__=='__main__':
    unittest.main()
