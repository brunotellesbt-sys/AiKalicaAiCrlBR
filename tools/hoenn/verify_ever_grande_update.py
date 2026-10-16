"""Require current native market proofs while retaining the Surf release as history."""
import hashlib
import json
from pathlib import Path
from package_review_rom import verify as verify_review
from verify_fuchsia_update import ROOT, previous_release

def verify_update(directory,info):
    directory=Path(directory);old=previous_release(info)
    assert old['validated'] and old['validation_scope']=='dewford-competitive-shop'
    assert old['integration_layers']+['ever-grande-market']==info['integration_layers']
    test=verify_review(ROOT/'roms/rom-de-teste',directory/'Pokemon-Journey-Gen1-9-Normal.gba')
    expected={'common':info['parent_rom_sha256'],'test':test['sha256'],**{r['file']:r['sha256'] for r in info['variants']}}
    covered=set()
    for p in info['proofs']:
        path=Path(p['file']);assert not path.is_absolute() and '..' not in path.parts
        raw=(directory/path).read_bytes();assert hashlib.sha256(raw).hexdigest()==p['sha256']
        r=json.loads(raw);assert r['passed'] and r['rom_sha256']==expected[p['target']]
        covered.add((p['target'],p['kind']))
        if p['kind']=='ever-grande-source':
            assert r['layers']==info['integration_layers'] and r['independent_replay'] and r['idempotent']
            assert r['source_hashes_checked']>30000 and r['unrelated_files_preserved']>30000
            assert r['all_surf_maps_unchanged'] and r['original_city_events_and_connections_preserved']
            assert r['dewford_and_origin_features_preserved']
            assert [h['item'] for h in r['houses']]==['ITEM_FULL_RESTORE','ITEM_MAX_REVIVE']
            assert r['stall']['price']==200000 and len(r['stall']['stock'])>=47
            assert any(c==13 for x,y,c in r['city_pixels'])
        elif p['kind']=='ever-grande-market':
            assert len(r['gifts'])==2
            for g in r['gifts']:
                assert all(g[k] for k in ['bag_full_preserves_gift','exactly_one_item','repeat_talk_no_duplicate','neighbor_talked','controller_entry_and_exit'])
            assert r['market_price']==200000
            for k in ['controller_center_roundtrip','victory_road_and_stairs_walked','market_actual_purchase','insufficient_money_rejected','stock_specific_price_reset','base_item_price_unchanged','save_continue_preserves_gifts_and_purchase','compiled_atlas_and_zoom_match_source','sootopolis_city_red']:assert r[k],k
        elif p['kind']=='dewford-competitive-shop':
            assert r['review_mode']==(p['target']=='test') and r['prices_checked']==71
            assert len(r['purchases'])==3 and r['single_cap_only_one_stat'] and r['gold_cap_all_six_stats']
            assert r['original_genetic_ivs_preserved'] and r['booth_shore_matches_source'] if 'booth_shore_matches_source' in r else r['original_genetic_ivs_preserved']
            for k in ['two_attendants_interacted','footpath_to_bridge_walked','full_restore_picked_up_once','play_rough_picked_up_and_native_teachable','closed_trees_block_walk']:assert r[k],k
            origins=r['origin_forms'];assert origins['wrong_species_orb_rejected'] and origins['giving_and_taking_original_orbs_use_controller_input']
            assert {c['pokemon'] for c in origins['checks']}=={'Dialga','Palkia','Giratina'}
            assert all(c['original_orb_equipped_through_bag'] and c['item_taken_through_party_menu'] and c['stats_change_and_revert'] and c['save_reload_preserves_form_and_item'] and c['modern_reward_still_transforms'] for c in origins['checks'])
        elif p['kind']=='review-mode':
            assert r['review_mode']==(p['target']=='test') and r['fixture_wild_encounters_disabled'] is False
            assert bool(r['checks']['trainer_approach_result'])==(p['target']!='test')
            if p['target']=='test':
                c=r['checks'];assert c['random_wild_attempts']>=200 and c['no_automatic_approach_after_600_frames'] and c['native_flash_save_exported']
                assert all(c[k] for k in ['no_random_encounters','no_fishing_encounters','no_sweet_scent_encounters','no_rock_smash_encounters'])
                assert hashlib.sha256((ROOT/'roms/rom-de-teste/Pokemon-Journey-TESTE.sav').read_bytes()).hexdigest()==c['save_sha256']
        else:raise AssertionError(p['kind'])
    assert {('common','ever-grande-source'),('common','ever-grande-market')}<=covered
    assert {(t,k) for t in expected if t!='common' for k in ['ever-grande-market','dewford-competitive-shop','review-mode']}<=covered
    assert all((directory/r['file']).read_bytes()[test['review_mode_offset']]==0 for r in info['variants'])
    # The old Surf reports keep their original ROM identities. Their terrain,
    # connections, scripts and compiled-water code are preserved by source audit.
    ref=info['previous_review_validation'];path=Path(ref['file']);assert not path.is_absolute() and '..' not in path.parts
    raw=(ROOT/path).read_bytes();assert hashlib.sha256(raw).hexdigest()==ref['sha256'];previous_test=json.loads(raw)
    from verify_dewford_shop_update import verify_update as verify_earlier
    verify_earlier(directory,old,historical_review=previous_test)
