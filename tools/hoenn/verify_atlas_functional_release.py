"""Require the compiled Atlas source, current native matrices and five editions.

The reviewed contract pins the complete exported evidence tree. Old releases
remain explicitly historical and cannot supply any current-ROM obligation.
"""
import gzip
import hashlib
import json
from pathlib import Path

from published_evidence import pinned_release
from verify_legendary_chambers_native import confined

ROOT=Path(__file__).resolve().parents[2]
CONTRACT=ROOT/'docs/design/atlas-functional-review-2026-11-23/final-contract.json'
SCOPE='atlas-surf-layout'
BASELINE_SHA='eca26adfcb0b15f9da78aadec1b8738f66288fcc58d4d727ee2ea2a6274e29ec'
PREVIOUS_INSPECTION_SAVE_SHA='ece5c236e09415b8235d58f4e1d86fb5ef89dbdf10f2cc28c758f4edd1a19574'
GROUPS=frozenset({'chambers','exteriors','rocks','trainers','coasts','dives','legacy',
                  'neighbor','captures','captain','three-port','seven-ports','land'})


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    path=Path(path);raw=path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)


def check_identity(report,frozen,rom=None):
    assert report['passed'] is True
    actual=report.get('artifact_sha256')
    if actual is None:
        actual={'pokeemerald.gba':report['rom_sha256'],'pokeemerald.elf':report['elf_sha256'],
                '.journey-atlas-surf-layout':report['marker_sha256']}
    assert actual=={
        'pokeemerald.gba':rom or frozen['rom_sha256'],'pokeemerald.elf':frozen['elf_sha256'],
        '.journey-atlas-surf-layout':frozen['marker_sha256']},'Stale or mixed native artifact'


def verify_tree(root,index,expected_sha):
    path=confined(root,index);assert sha(path)==expected_sha,'Evidence index changed'
    files=load(path);assert isinstance(files,dict) and files
    assert {p.relative_to(root).as_posix() for p in Path(root).rglob('*') if p.is_file()}==set(files)|{index},'Unindexed evidence attachment'
    for name,digest in files.items():
        assert sha(confined(root,name))==digest,('Changed native attachment',name)
    return files


def reports(root,paths,frozen):
    rows=[]
    for name in paths:
        report=load(confined(root,name));check_identity(report,frozen)
        rows.append(report)
    assert rows
    return rows


def all_cases(rows):return [c for r in rows for c in r['cases']]


def verify_cold(root,path,rom,battery_sha):
    report=load(confined(root,path));assert report['passed'] and report['rom_sha256']==rom
    for flag in ('fresh_rom_boot_to_title','fresh_rom_title_to_new_game','no_assert_screen',
                 'controllers_only','no_game_memory_writes','bundled_save_tested','bundled_save_continue_to_field'):
        assert report[flag] is True,flag
    assert report['bundled_save_sha256']==battery_sha
    state=report['runs'][-1]
    assert state['geometry_version']==8
    return state


def verify_inspection_save(root, paths, rom, save_sha):
    migrated=verify_cold(root,paths['migration'],rom,PREVIOUS_INSPECTION_SAVE_SHA)
    continued=verify_cold(root,paths['continue'],rom,save_sha)
    assert migrated['saved_after_continue_with_controllers'] is True
    assert migrated['saved_battery_sha256']==save_sha
    for state in (migrated,continued):
        assert state['field_map']==[0,6] and state['player_tile']==[28,18]
        assert state['player_surfing'] is False


def verify_native(root,contract,frozen,metadata):
    paths=contract['native'];assert set(paths)==GROUPS
    groups={k:reports(root,v,frozen) for k,v in paths.items() if k!='legacy'}
    from verify_legendary_chambers_native import verify as verify_rooms
    from verify_large_cave_exteriors_native import verify as verify_exteriors
    from verify_atlas_103_rocks_native import verify as verify_rocks
    from verify_neighbor_layout_camera import verify as verify_neighbor
    verify_rooms(frozen,confined(root,contract['chamber_matrix']).parent,metadata['legendary_individual_chambers']['rooms'])
    verify_exteriors(frozen,confined(root,contract['exterior_matrix']).parent,metadata['large_cave_exteriors'])
    verify_rocks(frozen,confined(root,paths['rocks'][0]).parent)
    verify_neighbor(frozen,confined(root,paths['neighbor'][0]).parent)
    trainers=all_cases(groups['trainers']);expected=metadata['surf_trainer_redesign']['trainers']
    assert len(trainers)==len(expected)==96
    assert {(r['trainer'],r['private_flag'],r['map']) for r in trainers}=={
        (r['id'],r['flag'],r['map']) for r in expected}
    for r in trainers:
        assert r['outcome']==1 and r['native_sight_line_started_battle']
        assert r['private_defeat_flag_set'] and r['unrelated_system_flag_unchanged']
    for r in groups['trainers']:
        assert r['no_battle_RAM_writes'] and r['current_cold_continue_preserves_private_flags']
    coasts=all_cases(groups['coasts']);assert len(coasts)==34 and len({r['adapter'] for r in coasts})==34
    for r in coasts:
        assert r['all_travel_controllers_and_readonly_queries']
        assert len(r['neighbor_camera_phases'])==3 and r['native_reef_bump']
    from PIL import Image
    from verify_sevii_route_boundaries_native import verify_pixels
    for name,report in zip(paths['coasts'],groups['coasts']):
        folder=confined(root,name).parent
        captures={r['file']:r['sha256'] for r in report['captures']}
        images={n:Image.open(confined(folder,n)).convert('RGB') for n in captures}
        for case in report['cases']:
            for phase in case['neighbor_camera_phases']:
                obs=phase['pixels']
                for cell in obs['cells']:
                    verify_pixels(dict(obs,cells=[cell]),phase['capture'],captures,images,cell['cell'],cell['native_metatile'])
    dives=all_cases(groups['dives']);assert len(dives)==5
    assert {r['site'] for r in dives}=={'Mares','Origens','Profundezas','Dimensoes','Abismo'}
    assert all(r['native_field_effect_and_portal_roundtrip_passed'] for r in dives)
    legacy=[]
    for name in paths['legacy']:
        r=load(confined(root,name));assert r['passed'] and r['real_menu_batteries_and_cold_controllers_only']
        assert r['artifacts']['old']=={
            'pokeemerald.gba':'c08cb7771a9731db995b7d99297c8b1ebcdd98d75a9ac5e50cdaef8dcff62c82',
            'pokeemerald.elf':'36989019fbf9b14e8ce93b96701c3c517bee965a6ab755d3c380ebcb9a16449f',
            '.journey-atlas-surf-layout':'10a2b57e222d642aac218b0a4e04e4a296378fa0f5e237cff73c753123a97114'}
        assert r['artifacts']['new']=={
            'pokeemerald.gba':frozen['rom_sha256'],'pokeemerald.elf':frozen['elf_sha256'],
            '.journey-atlas-surf-layout':frozen['marker_sha256']}
        legacy.extend(r['cases'])
    assert len(legacy)==18 and len({(r['name'],r['surfing']) for r in legacy})==18
    for r in legacy:
        assert r['old_save_and_both_new_continues_passed'] and r['capture_flags_checked']==105
        assert r['native_actor_templates_match_current_compiled_map'] and r['second_continue_did_not_repeat_migration']
    captures=all_cases(groups['captures']);assert {r['national_dex'] for r in captures}=={144,487,1025}
    assert len(captures)==3
    for r in captures:
        assert r['locked_with15_badges'] and r['real_challenge_and_master_ball_capture'] and r['own_actor_removed']
        assert r['master_ball_consumed'] and r['native_SAVE_and_cold_Continue_preserve_actual_party_and_catch_flag']
    land=all_cases(groups['land']);assert len(land)==7
    assert {r['map'] for r in land}==set(metadata['sand_land_habitats']['maps'])
    assert all(r['native_battle_started_by_walking'] and r['returned_to_same_island_on_foot'] for r in land)
    ports=all_cases(groups['seven-ports']);assert len(ports)==7
    assert len(groups['seven-ports'])==1 and groups['seven-ports'][0]['full_seven_coverage']
    # These three complete controller reports also bind their actual boat,
    # indoor captain and island access assertions through the reviewed tree.
    assert len(groups['captain'])==len(groups['three-port'])==1
    captain=groups['captain'][0]
    for flag in ('bridge_both_directions','nearest_house_native_door_roundtrip','captain_service_preserved',
                 'original_boat_numeric_local_id_preserved','house_residents_preserved','saved_through_native_menu'):
        assert captain[flag] is True,flag
    assert len(captain['voyages'])==2
    for flag in ('southern_ocean_both_directions','real_coast_connection_both_directions',
                 'surf_departure_and_reboarding','pedestrian_and_reef_and_terminal_barriers','saved_through_native_menu'):
        assert groups['three-port'][0][flag] is True,flag
    return True


def verify_update(directory,info,*,contract_path=None,review_directory=None):
    contract_file=Path(contract_path) if contract_path is not None else CONTRACT
    contract=load(contract_file)
    assert contract['schema']=='atlas-functional-release/v1' and contract['finalized'] is True
    assert info['validation_scope']==SCOPE and info['candidate'] is False and info['final_release_validated'] is True
    assert info['integration_layers'][-1]==SCOPE and len(info['integration_layers'])==172
    root=confined(ROOT,contract['evidence_root'])
    assert root==ROOT/'mods/hoenn/versions/evidence/atlas-surf-layout'
    files=verify_tree(root,contract['index'],contract['index_sha256'])
    frozen=load(confined(root,contract['freeze']));metadata=load(confined(root,contract['metadata']))
    assert frozen['rom_sha256']==info['parent_rom_sha256']==contract['rom_sha256']
    assert frozen['elf_sha256']==contract['elf_sha256'] and frozen['marker_sha256']==contract['marker_sha256']
    assert frozen['prepared_sha256']==metadata['prepared_sha256']==contract['prepared_sha256']
    assert metadata['migration']['final_version']==frozen['migration_version']==8
    _,old=pinned_release(info['previous_port_validation'])
    assert info['previous_port_validation']['manifest_sha256']==BASELINE_SHA
    assert old['validated'] and old['validation_scope']=='generated-area-review'
    assert old['integration_layers']+[SCOPE]==info['integration_layers']
    assert info['full_campaign_playthrough'] is info['previous_features_retested_on_current_rom'] is False
    source=load(confined(root,contract['source']))
    assert source['passed'] and source['kind']=='atlas-surf-final-source'
    assert (source['rom_sha256'],source['elf_sha256'],source['marker_sha256'])==(
        frozen['rom_sha256'],frozen['elf_sha256'],frozen['marker_sha256'])
    assert source['prepared_sha256']==frozen['prepared_sha256']
    assert source['source_inputs_checked']==frozen['complete_source_files_checked']>=34000
    assert source['independent_replay'] and source['source_file_hashes_match_compiled_snapshot']
    assert source['physical']['passed'] and not source['physical']['errors']
    assert source['immutable_atlas_art_matches'] and source['warps_checked']>=3118
    assert source['current_AREA_rows']==2539
    assert len(source['dex_relocation']['relocated'])==1044
    assert sum(r['restored_land_trigger'] for r in source['dex_relocation']['relocated'])==66
    comparison=load(confined(root,contract['family_comparison']))
    assert comparison['preserved'] and not any(comparison['missing_families'].values())
    assert comparison['after_counts']=={'493':199,'1025':402}
    verify_native(root,contract,frozen,metadata)
    from package_review_rom import verify as verify_review
    review_dir=Path(review_directory) if review_directory is not None else ROOT/'roms/rom-de-teste'
    review=verify_review(review_dir,Path(directory)/'Pokemon-Journey-Gen1-9-Normal.gba')
    save=review_dir/'Pokemon-Journey-TESTE.sav'
    assert save.stat().st_size==131072 and sha(save)==contract['test_save_sha256']
    verify_inspection_save(root,contract['inspection_save_proofs'],review['sha256'],sha(save))
    targets={r['file']:r['sha256'] for r in info['variants']};targets['test']=review['sha256']
    assert targets==contract['profiles']
    assert set(contract['editions'])==set(targets)
    for target,rom in targets.items():
        paths=contract['editions'][target];assert set(paths)=={'rules','trainer','cold','wild'}
        rules=load(confined(root,paths['rules']));battle=load(confined(root,paths['trainer']))
        check_identity(rules,frozen,rom);check_identity(battle,frozen,rom)
        assert len(rules['canonical_location_counts'])==1025
        cap=rules['max_national']
        assert all(bool(count)==(int(number)<=cap) for number,count in rules['canonical_location_counts'].items())
        assert len(rules['aquatic_samples'])>=3*410
        assert rules['enemy_party_created_by_native_generator_only']
        assert battle['current_cold_continue_preserves_private_flags'] and battle['no_battle_RAM_writes']
        verify_cold(root,paths['cold'],rom,battle['battery']['sha256'])
        assert len(battle['cases'])==1 and battle['cases'][0]['outcome']==1
        assert bool(rules['review_mode'])==(target=='test')
        if target=='test':
            assert battle['cases'][0]['native_manual_interaction_started_battle']
            assert battle['cases'][0]['no_automatic_approach_after600_frames']
            assert rules['review_checks']
            for flag in ('no_random_encounters','no_fishing_encounters','no_sweet_scent_encounters','no_rock_smash_encounters'):
                assert rules['review_checks'][flag] is True
        else:assert battle['cases'][0]['native_sight_line_started_battle']
        wild=load(confined(root,paths['wild']))
        assert wild['passed'] and wild['rom_sha256']==rom and wild['elf_sha256']==frozen['elf_sha256']
        assert wild['controller_input_only_after_initial_fixture'] and not wild['wild_encounters_disabled_fixture']
        assert wild['repel_fixture_steps']==0 and wild['review_mode']==(target=='test')
        if target=='test':assert wild['battle'] is None and wild['standard_encounter_suppression_attempts']==200
        else:assert wild['battle']['actual_battle_main_callback'] and wild['actual_controller_steps']>0
    assert info['proofs'] and info['functional_contract_sha256']==sha(contract_file)
    expected={('common','atlas-functional-source'),('common','atlas-functional-native')}
    expected|={(target,kind) for target in targets for kind in ('edition-native-rules','atlas-surf-trainers-native')}
    assert {(r['target'],r['kind']) for r in info['proofs']}==expected and len(info['proofs'])==len(expected)
    for row in info['proofs']:
        relative=Path(row['file']).relative_to('evidence/atlas-surf-layout')
        p=confined(root,relative);assert sha(p)==row['sha256']
    return dict(passed=True,source_files=source['source_inputs_checked'],rooms=105,
                trainers=96,coasts=34,ports=7,land_habitats=7,editions=5,attachments=len(files))
