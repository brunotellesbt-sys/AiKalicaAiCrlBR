"""Reject incomplete aquatic coverage and source-only publication claims."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image

import coastal_ecology_contract as contract
from publish_coastal_ecology import publish,write_plan
from verify_coastal_ecology_update import (required_keys,verify_elf_binding,
    verify_encounter_observations,verify_kindle_cliff,verify_ocean_palette,
    verify_pier_perimeters,verify_proof,verify_pier_visibility)


class EcologyRelease(unittest.TestCase):
    def check(self,report,kind):
        verify_proof(report,Path('.'),kind,'common',Path('/unused'),
                     dict(integration_layers=['source']),dict(parent_rom_sha256='parent'))

    def census(self):
        rows=[]
        for name in ('Coast','Depth'):
            rows.append(dict(map=name,required=True,water_cells=40,native_header_index=1,
                time_periods=[dict(time=i,rate=4,species=[72]*5) for i in range(4)],
                fishing_time_periods=[] if name=='Depth' else
                    [dict(time=i,rate=4,species=[72]*5) for i in range(4)],
                pools={cap:[72] for cap in ('493','1025')},
                fishing_pools={cap:[72] for cap in ('493','1025')},
                underwater=name=='Depth',standard_wild_trigger_behaviors=[16]))
        return dict(passed=True,kind='coastal-ecology-census',compiled_rom=True,
            native_headers_read_from_compiled_rom=True,habitat_pools_read_from_compiled_rom=True,
            terrain_behaviors_read_from_compiled_tilesets=True,layer166_marker_present=True,
            diagnostic_allow_gaps=False,all_time_periods_checked=4,missing_headers=[],
            missing_fishing_headers=[],missing_standard_wild_triggers=[],
            maps=rows,aquatic_maps=2,required_aquatic_maps=2,quiet_or_retired_maps=0,
            coverage_by_cap={cap:dict(missing_pools=[],missing_fishing_pools=[],invalid_roots=[],empty_phases=[])
                             for cap in ('493','1025')})

    def test_complete_compiled_census_is_accepted(self):
        with patch.object(contract,'EXPECTED_WATER_MAPS',('Coast','Depth')):
            self.check(self.census(),'coastal-ecology-census')

    def test_one_map_cannot_disappear_behind_passed_counter(self):
        report=self.census();report['maps'].pop()
        with patch.object(contract,'EXPECTED_WATER_MAPS',('Coast','Depth')):
            with self.assertRaises(AssertionError):self.check(report,'coastal-ecology-census')

    def test_variant_four_missing_pool_is_rejected(self):
        report=self.census();report['coverage_by_cap']['493']['missing_pools']=['Depth']
        with patch.object(contract,'EXPECTED_WATER_MAPS',('Coast','Depth')):
            with self.assertRaises(AssertionError):self.check(report,'coastal-ecology-census')

    def test_header_without_a_real_tile_trigger_is_rejected(self):
        report=self.census();report['missing_standard_wild_triggers']=['Depth']
        with patch.object(contract,'EXPECTED_WATER_MAPS',('Coast','Depth')):
            with self.assertRaises(AssertionError):self.check(report,'coastal-ecology-census')

    def test_missing_fishing_pool_is_rejected(self):
        report=self.census();report['coverage_by_cap']['493']['missing_fishing_pools']=['Coast']
        with patch.object(contract,'EXPECTED_WATER_MAPS',('Coast','Depth')):
            with self.assertRaises(AssertionError):self.check(report,'coastal-ecology-census')

    def test_an_empty_evolution_phase_is_rejected(self):
        report=self.census();report['coverage_by_cap']['1025']['empty_phases']=[['Depth',72,2]]
        with patch.object(contract,'EXPECTED_WATER_MAPS',('Coast','Depth')):
            with self.assertRaises(AssertionError):self.check(report,'coastal-ecology-census')

    def test_unpopulated_night_table_is_rejected(self):
        report=self.census();report['maps'][0]['time_periods'][3]['species']=[]
        with patch.object(contract,'EXPECTED_WATER_MAPS',('Coast','Depth')):
            with self.assertRaises(AssertionError):self.check(report,'coastal-ecology-census')

    def test_unpopulated_fishing_night_table_is_rejected(self):
        report=self.census();report['maps'][0]['fishing_time_periods'][3]['species']=[]
        with patch.object(contract,'EXPECTED_WATER_MAPS',('Coast','Depth')):
            with self.assertRaises(AssertionError):self.check(report,'coastal-ecology-census')

    def test_diagnostic_allow_gaps_never_becomes_release_evidence(self):
        report=self.census();report['diagnostic_allow_gaps']=True
        with patch.object(contract,'EXPECTED_WATER_MAPS',('Coast','Depth')):
            with self.assertRaises(AssertionError):self.check(report,'coastal-ecology-census')

    def pallet(self):
        result=dict(passed=True,kind='coastal-pallet',
            whole_standalone_tree_pattern=[0xE,0xF,0x1E,0x1F,0x26,0x27],
            captures=[dict(file='native.png',sha256='a'*64)],
            route21_atlas_seam_delta=0,trips=[dict()])
        for key in ('original_bridge_preserved','bridge_walked_without_surf',
            'controller_entry_and_exit','interior_captain_interacted_physically',
            'bridges_joined_and_walked','complete_trees_checked','upper_cliff_rim',
            'returned_to_original_land','route21_surf_roundtrip','merged_bay_surfed',
            'south_bridge_walked','eastern_corridor_walked','bridge_crossed_by_surf_below',
            'compiled_rom','native_validation_performed',
            'all_tree_parts_checked_through_native_map_grid',
            'walking_surf_doors_and_ferry_use_controller','fixture_wild_encounters_disabled'):
            result[key]=True
        result.update(north_rim_cells=[dict(tile=[x,17],metatile=0x302 if x<22 else 0x303,
            elevation=3,collision=1,behavior=0) for x in range(15,23)],
            all_wet_mixed_rim_cells_blocked=True,north_rim_surrounding_land_route_walked=True,
            south_bridge_from_full_grass_controller_roundtrip=True,
            no_new_travel_fixture_after_initial_land_route=True,
            south_bridge_dry_roundtrip=[dict(tile=[18,y],surfing=False,elevation=3,
                tile_elevation=15 if y==25 else 3) for y in (26,25,24,25,26)])
        edges=[((14,17),(15,17),16),*(( (x,16),(x,17),128) for x in (15,16,17,18,19,21,22)),
               ((23,17),(22,17),32)]
        result['north_rim_blocked_probes']=[]
        for start,target,key in edges:
            state=dict(tile=list(start),surfing=False,elevation=3,tile_elevation=3)
            result['north_rim_blocked_probes'].append(dict(start=list(start),target=list(target),
                direction_key=key,held_input_frames=48,before=state,after=dict(state),
                controller_input_only=True,blocked=True))
        return result

    def test_pallet_controller_proof_uses_complete_standalone_tree(self):
        self.check(self.pallet(),'coastal-pallet')

    def test_old_forest_overlap_pieces_cannot_verify_standalone_tree(self):
        report=self.pallet();report['whole_standalone_tree_pattern']=[0xE,0xF,0x1C,0x1F,0x24,0x27]
        with self.assertRaises(AssertionError):self.check(report,'coastal-pallet')

    def test_pallet_source_only_tree_inspection_is_rejected(self):
        report=self.pallet();report['all_tree_parts_checked_through_native_map_grid']=False
        with self.assertRaises(AssertionError):self.check(report,'coastal-pallet')

    def test_wet_pallet_rim_cannot_keep_an_open_collision_or_drop_a_probe(self):
        for mutate in (lambda r:r['north_rim_cells'][0].update(collision=0),
                       lambda r:r['north_rim_blocked_probes'].pop()):
            report=self.pallet();mutate(report)
            with self.assertRaises(AssertionError):self.check(report,'coastal-pallet')

    def test_pallet_bridge_roundtrip_keeps_the_pedestrian_on_native_level3(self):
        report=self.pallet();report['south_bridge_dry_roundtrip'][1]['elevation']=0
        with self.assertRaises(AssertionError):self.check(report,'coastal-pallet')

    def test_required_plan_covers_each_edition_and_both_encounter_caps(self):
        files=['Pokemon-Journey-'+name+'.gba' for name in
               ('Gen1-4-Normal','Gen1-4-Hard','Gen1-9-Normal','Gen1-9-Hard')]
        keys=required_keys(dict(variants=[dict(file=file) for file in files]))
        self.assertEqual(len(keys),20)
        self.assertIn(('common','coastal-fragments'),keys)
        self.assertIn(('common','coastal-pier-visibility'),keys)
        for target in [*files,'test']:
            self.assertTrue({(target,'cold-boot'),(target,'review-mode')}<=keys)
        self.assertIn(('common','coastal-ecology-native'),keys)
        self.assertIn(('Pokemon-Journey-Gen1-4-Normal.gba','coastal-ecology-native'),keys)
        self.assertIn(('test','coastal-ecology-review'),keys)

    def test_native_census_is_bound_to_same_compiled_elf_as_source(self):
        reports=[('coastal-ecology-source',dict(elf_sha256='a'*64)),
                 ('coastal-ecology-census',dict(elf_sha256='a'*64)),
                 ('coastal-pallet',dict(elf_sha256='a'*64))]
        verify_elf_binding(reports)
        reports[1][1]['elf_sha256']='b'*64
        with self.assertRaisesRegex(AssertionError,'unaudited ELF'):
            verify_elf_binding(reports)

    def native(self,review=False,cap=1025):
        rows=[]
        for name,profile,behavior,phase in [('SixIsland_Frlg','coast',44,0),
            ('JourneyHoennMiddleSea','open-sea',21,1),('Route114','river',21,2),
            ('JourneyDepthMares','new-depth',0,2),('Underwater_Route105','native-depth',25,1)]:
            row=dict(kind='coastal-ecology-native-case',passed=True,rom_sha256='r'*64,
                elf_sha256='e'*64,compiled_rom=True,native_validation_performed=True,
                map=name,profile=profile,native_case_behavior=behavior,phase=phase,area=1,
                review_mode=review,max_national_dex=cap,
                underwater=profile in {'new-depth','native-depth'},
                native_fishing_available=not review,initial_position=[5,5],walking_pair=[[5,5],[6,5]],
                actual_controller_steps=220 if review else 4,
                controller_input_only_after_initial_fixture=True,
                party_and_map_and_badges_are_initial_fixtures=True,
                trainer_defeat_flags_not_written=True,
                no_battle_result_or_avatar_coordinate_writes=True,
                wild_encounters_disabled_fixture=False,repel_fixture_steps=0,
                allowed_species=[72],native_pool_samples=[72],
                battle=None if review else dict(species=72,national_dex=72,level=34,
                    actual_battle_main_callback=True,battle_action_menu_rendered=True,battle_type_flags=4,
                    framebuffer_distinct_rgb_colors=71,framebuffer_nonblack_pixels=38400),
                standard_encounter_suppression_attempts=200 if review else 0,
                captures=[dict(file=name+'/capture.png',sha256='a'*64)])
            rows.append(row)
        return dict(passed=True,kind='coastal-ecology-review' if review else 'coastal-ecology-native',
            rom_sha256='r'*64,elf_sha256='e'*64,compiled_rom=True,native_validation_performed=True,
            review_mode=review,max_national_dex=cap,cases=rows,
            captures=[capture for row in rows for capture in row['captures']],
            coast_open_sea_river_new_and_native_depth_checked=True,
            actual_controller_steps=sum(row['actual_controller_steps'] for row in rows),
            all_normal_cases_started_actual_wild_battles=None if review else True,
            all_review_cases_suppressed_encounters=True if review else None,
            no_encounter_forcing_repel_or_disabled_wild_fixture=True,
            no_battle_result_or_avatar_coordinate_writes=True)

    def test_controller_matrix_accepts_real_battles_and_test_suppression(self):
        verify_encounter_observations(self.native(),'coastal-ecology-native','common')
        verify_encounter_observations(self.native(cap=493),'coastal-ecology-native',
                                      'Pokemon-Journey-Gen1-4-Normal.gba')
        verify_encounter_observations(self.native(review=True),'coastal-ecology-review','test')

    def test_new_depth_cannot_be_omitted_from_native_matrix(self):
        report=self.native();report['cases'].pop(3)
        with self.assertRaises(AssertionError):
            verify_encounter_observations(report,'coastal-ecology-native','common')

    def test_a_fake_or_missing_native_battle_is_rejected(self):
        for mutation in (lambda row:row.update(battle=None),
                         lambda row:row['battle'].update(actual_battle_main_callback=False),
                         lambda row:row['battle'].update(battle_action_menu_rendered=False),
                         lambda row:row['battle'].update(framebuffer_distinct_rgb_colors=4),
                         lambda row:row['battle'].update(framebuffer_nonblack_pixels=240),
                         lambda row:row.update(wild_encounters_disabled_fixture=True)):
            report=self.native();mutation(report['cases'][0])
            with self.assertRaises(AssertionError):
                verify_encounter_observations(report,'coastal-ecology-native','common')

    def test_test_edition_suppression_cannot_use_repel(self):
        report=self.native(review=True);report['cases'][0]['repel_fixture_steps']=200
        with self.assertRaises(AssertionError):
            verify_encounter_observations(report,'coastal-ecology-review','test')

    def test_cap493_native_battle_rejects_gen9_species(self):
        report=self.native(cap=493);report['cases'][0]['battle']['national_dex']=900
        with self.assertRaises(AssertionError):
            verify_encounter_observations(report,'coastal-ecology-native','Pokemon-Journey-Gen1-4-Normal.gba')

    def test_ocean_proof_rechecks_actual_pixels_and_all_animation_phases(self):
        import hashlib
        maps=list(contract.OCEAN_TARGET_MAPS)
        paths={f'data/tilesets/bank{i}.bin':format(i,'x')*64 for i in range(11)}
        image=Image.new('RGB',(240,160),(0,80,192))
        for x in range(16):image.putpixel((x,0),(x*8,0,0))
        pixel_sha=hashlib.sha256(image.crop((32,88,48,104)).tobytes()).hexdigest()
        names=[name+'-native.png' for name in maps]
        names += ['treasure-bay-and-border-phase-'+str(i)+'.png' for i in range(8)]
        names += ['mossdeep-ocean-native-phase-'+str(i)+'.png' for i in range(8)]
        names += ['mossdeep-ocean-seam-'+n+'.png' for n in ('JourneyMossdeepOuterSea','MossdeepCity')]
        images={name:image.copy() for name in names}
        headers=[dict(original=old,private=new,original_address=0x08010000+i*48,
            private_address=0x08010018+i*48,
            header_fields_except_private_metatile_pointer_identical=True)
            for i,(old,new) in enumerate(contract.OCEAN_HEADER_ALIASES.items())]
        addresses={row['private']:row['private_address'] for row in headers}
        report=dict(compiled_rom=True,native_validation_performed=True,
            former_bay_border_palette_seam_removed=True,
            upper_object_layers_attributes_and_geometry_preserved=True,
            initial_party_progress_travel_and_encounter_suppression_are_fixtures=True,
            no_palette_vram_map_grid_or_avatar_coordinate_writes=True,
            lower_water_words_changed=498,
            compiled_tables=[dict(path=path,sha256=sha,tileset='Bank'+str(i),
                words_changed=50 if i<6 else 38 if i==6 else 40) for i,(path,sha) in enumerate(paths.items())],
            target_maps=maps,loaded_map_count=43,
            loaded_maps=[dict(map=name,primary=banks[0],secondary=banks[1],
                primary_pointer=addresses[banks[0]],secondary_pointer=addresses.get(banks[1],0x08070000),
                banks_loaded_from_final_rom=True,initial_position=[2,2],surfing=False)
                for name,banks in contract.OCEAN_LOADED_BANKS.items()],captures=[],
            compiled_native_bank_aliases=headers,
            native_coast_layout_aliases=[dict(map=name,layout=layout,primary=primary,secondary=secondary,
                primary_pointer=addresses[primary],secondary_pointer=addresses.get(secondary,0x08070000),
                actual_loaded_private_bank_pointers_match_final_layout=True)
                for name,(layout,primary,secondary) in contract.OCEAN_LAYOUT_ALIASES.items()],
            native_same_frame_pixel_checks=[dict(sample=i,bay_cell=[15,7],offshore_cell=[21,3],
                identical_rgb_sha256=pixel_sha,same_native_frame=True,valid_animation_phases=[i])
                for i in range(8)])
        kanto={'CinnabarIsland_Frlg','JourneyRoute12OuterSea','JourneyRoute12Shipyard',
            'NavelRock_Exterior_Frlg','PalletTown_Frlg','Route11_Frlg','Route12_Frlg','Route13_Frlg',
            'Route14_Frlg','Route19_Frlg','Route20_Frlg','Route21_North_Frlg','Route21_South_Frlg',
            'TwoIsland_Harbor_Frlg','VermilionCity_Frlg'}
        report['source_ocean_groups']=[dict(region='kanto',maps=sorted(kanto),lower_water_words_changed=160),
            dict(region='sevii',maps=sorted(set(maps)-kanto),lower_water_words_changed=338)]
        report['hoenn_ocean']=dict(all_eight_original_water_frames_observed=True,
            native_visible_pixels_match_loaded_graphics=True,
            identical_loaded_banks_across_mossdeep_city_outer_sea=True,
            controller_surf_crossing_both_directions=True,
            primary_animation_clock_continuous_across_both_connections=True,
            palette_vram_animation_clock_and_map_grid_not_written=True,
            initial_travel_progress_and_surf_state_are_fixtures=True,
            source_census=dict(source_analysis_only=True,map_count=85,
                all_referenced_hoenn_ocean_words_use_palette4=True,
                original_river_deep_water_dive_and_current_behaviors_unchanged=True,
                maps=[dict(map=n,primary='gTileset_General',blockdata_sha256='a'*64)
                    for n in ['MossdeepCity','JourneyMossdeepOuterSea',*[f'Native{i}' for i in range(83)]]],
                water_graphics=[454,455],ocean_palette=4,
                water_banks=[dict(bank='General',referenced_lower_water_words=10)]),
            phases=[dict(phase=i,visible_native_water_pixels=1001,water_vram_sha256='a'*64,tile=[79,34])
                for i in range(8)],crossings=[dict(map=n,tile=xy,surfing=True,
                    primary_pointer=0x08080000,secondary_pointer=0x08081000,
                    primary_animation_clock_continuous_across_connection=True,
                    native_primary_animation_counter_steps=[dict(before=100,after=101,map=n)])
                    for n,xy in [('JourneyMossdeepOuterSea',[0,26]),('MossdeepCity',[79,34])]],
            captures=[dict(file=n,sha256='a'*64) for n in names if n.startswith('mossdeep-')])
        with patch.object(contract,'PREPARED_SHA256',paths), \
             patch('verify_coastal_ecology_update.verify_captures',return_value=images):
            verify_ocean_palette(report,Path('.'))
            broken=copy.deepcopy(report)
            broken['native_same_frame_pixel_checks'][7]['valid_animation_phases']=[6]
            with self.assertRaises(AssertionError):verify_ocean_palette(broken,Path('.'))
            changed=images['treasure-bay-and-border-phase-7.png']
            changed.putpixel((128,24),(255,0,0))
            with self.assertRaises(AssertionError):verify_ocean_palette(report,Path('.'))

    def test_source_only_pier_report_cannot_pass_on_optimistic_flags(self):
        report=dict(compiled_rom=False,native_validation_performed=True,
            all_seven_ports_verified=True,all_exposed_dry_water_edges_tested=True,
            previous_video_defect_edges_included=True,
            initial_placements_party_and_progress_are_fixtures=True,
            movement_fixture_random_encounters_disabled=True,
            controller_only_after_initial_placement=True,
            no_midtrip_coordinate_elevation_or_avatar_writes=True,
            legacy_save_recovery_tested=True)
        with self.assertRaises(AssertionError):verify_pier_perimeters(report,Path('.'))

    def test_kindle_cliff_requires_the_whole_face_and_real_town_roundtrip(self):
        road,town='OneIsland_KindleRoad_Frlg','OneIsland_Frlg'
        treasure='OneIsland_TreasureBeach_Frlg'
        expected={(town,22,18):0x112C,(town,23,18):0x047B,
            (town,22,19):0x112B,(town,23,19):0x1123,
            **{(road,x,138):0x047C for x in range(6)},
            (road,6,138):0x047D,(road,7,138):0x1120,
            **{(road,x,139):0x1123 for x in range(7)},(road,7,139):0x1131,
            **{(treasure,x,y):0x112B for x in (22,23) for y in range(3)}}
        start=dict(tile=[7,137],location=[37,45],surfing=True,elevation=1)
        route=[([7,138],128),([7,139],128)]
        route += [([x,139],32) for x in range(6,-1,-1)]
        route += [([23,19],32),([23,0],128),([23,1],128),([23,2],128),
                  ([22,2],32),([22,1],64),([22,0],64),([23,0],16),
                  ([23,19],64),([0,139],16)]
        route += [([x,139],16) for x in range(1,8)]
        route += [([7,138],64),([7,137],64)]
        moves=[];previous=start['tile'];location=start['location']
        for i,(tile,key) in enumerate(route):
            target=[37,12] if i in (9,17) else [37,46] if 10<=i<=16 else [37,45]
            moves.append(dict(start=previous,end=tile,source_location=location,
                destination_location=target,direction_key=key,held_input_frames=8,
                controller_input_only=True,surfing_preserved=True))
            previous,location=tile,target
        report=dict(map=road,initial_fixture=start,return_state=copy.deepcopy(start),
            native_loaded_cells=[dict(source_map=name,source_tile=[x,y],
                loaded_tile=[x-24,y+120] if name==town else [x,y],
                loaded_map=treasure if name==treasure else road,
                expected=word,observed=word,native_grid_checked=True,native_banks_checked=True)
                for (name,x,y),word in expected.items()],
            all26_native_cells_checked=True,complete_face_and_water_toe_loaded=True,
            all_six_retired_treasure_foot_cells_surfed=True,
            town_treasure_surf_seam_roundtrip_controller=True,
            cape_surf_roundtrip_and_town_seam_controller=True,
            restored_private_16bit_initial_warp_fixture=True,movements=moves,controller_steps=28)
        for name,tile,key in [('west_face_probe',[7,138],32),
                              ('south_boundary_probe',[7,139],128)]:
            state=dict(start,tile=tile)
            report[name]=dict(before=state,after=copy.deepcopy(state),direction_key=key,
                held_input_frames=48,blocked=True,controller_input_only=True)
        verify_kindle_cliff(report)
        for mutation in (lambda r:r['native_loaded_cells'].pop(),
                         lambda r:r['movements'][9].update(destination_location=[37,45]),
                         lambda r:r['south_boundary_probe'].update(blocked=False),
                         lambda r:r['native_loaded_cells'][0].update(observed=0x0473)):
            broken=copy.deepcopy(report);mutation(broken)
            with self.assertRaises(AssertionError):verify_kindle_cliff(broken)

    def test_missing_edition_boot_keeps_plan_incomplete(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);validation=root/'validation';validation.mkdir()
            names=['Gen1-4-Normal','Gen1-4-Hard','Gen1-9-Normal','Gen1-9-Hard','TESTE']
            frozen=dict(parent_rom_sha256='raw',editions=[dict(edition=name,sha256=name) for name in names])
            snapshot=root/'frozen.json';snapshot.write_text(json.dumps(frozen))
            info=dict(variants=[dict(file='Pokemon-Journey-'+name+'.gba') for name in names[:-1]])
            identities={'common':'raw','test':'TESTE',**{r['file']:name for r,name in zip(info['variants'],names)}}
            missing=('test','cold-boot')
            for index,(target,kind) in enumerate(sorted(required_keys(info)-{missing})):
                (validation/(str(index)+'.json')).write_text(json.dumps(dict(
                    passed=True,kind=kind,rom_sha256=identities[target])))
            plan=root/'plan.json'
            with self.assertRaisesRegex(AssertionError,'Current native runs incomplete'):
                write_plan(validation,snapshot,plan)
            self.assertFalse(plan.exists())

    def test_unfinished_native_contract_does_not_write_public_roms(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);output=root/'published'
            with patch.object(contract,'NATIVE_CONTRACT_FINALIZED',False), \
                 patch.object(contract,'PREPARED_SHA256',{'file':'hash'}), \
                 patch.object(contract,'EXPECTED_WATER_MAPS',('Coast',)), \
                 patch('publish_coastal_ecology.package') as package:
                with self.assertRaisesRegex(AssertionError,'not finalized'):
                    publish(root/'source',root/'validation',output,root/'plan.json')
                package.assert_not_called()
            self.assertFalse(output.exists())


if __name__=='__main__':unittest.main()
