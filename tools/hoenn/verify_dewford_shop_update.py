"""Verify the five current shop ROMs and keep earlier navigation proof historical."""
import hashlib,json
from pathlib import Path
from verify_fuchsia_update import ROOT,previous_release
from package_review_rom import verify as verify_review


def verify_update(directory,info):
    directory=Path(directory);old=previous_release(info)
    assert old['validated'] and old['integration_layers']+['dewford-competitive-shop']==info['integration_layers']
    test=verify_review(ROOT/'roms/rom-de-teste',directory/'Pokemon-Journey-Gen1-9-Normal.gba')
    expected={'common':info['parent_rom_sha256'],'test':test['sha256'],**{r['file']:r['sha256'] for r in info['variants']}}
    covered=set()
    for p in info['proofs']:
        path=Path(p['file']);assert not path.is_absolute() and '..' not in path.parts
        raw=(directory/path).read_bytes();assert hashlib.sha256(raw).hexdigest()==p['sha256']
        r=json.loads(raw);assert r['passed'] and r['rom_sha256']==expected[p['target']]
        if p['kind']=='dewford-shop-source':
            assert p['target']=='common' and r['layers']==info['integration_layers']
            assert r['unrelated_inputs_checked']>30000 and r['independent_replay'] and r['idempotent']
            assert r['all_existing_events_preserved'] and r['only_requested_terrain_changed'] and r['mega_stones_unchanged']
            assert r['unchanged_map_cells_pixel_checked']>3000 and r['existing_tm_hm_numbers_preserved'] and r['animated_flag_graphics_reserved']
        else:
            assert p['kind']=='dewford-competitive-shop' and p['target']!='common'
            assert r['review_mode']==(p['target']=='test') and r['prices_checked']==71
            assert len(r['purchases'])==3 and {x['item'] for x in r['purchases']}=={'CHOICE_SCARF','BOTTLE_CAP','GOLD_BOTTLE_CAP'}
            for key in ['insufficient_money_preserves_money_and_bag','two_attendants_interacted',
                        'footpath_to_bridge_walked','single_cap_only_one_stat','gold_cap_all_six_stats',
                        'original_genetic_ivs_preserved','cancellation_preserves_caps','perfect_stats_preserve_caps',
                        'play_rough_picked_up_and_native_teachable','lighthouse_back_path_walked','level49_rejected','eggs_rejected','full_restore_picked_up_once','closed_trees_block_walk']:assert r[key],key
        covered.add((p['target'],p['kind']))
    assert {('common','dewford-shop-source')}|{(t,'dewford-competitive-shop') for t in expected if t!='common'}<=covered
    assert all((directory/r['file']).read_bytes()[test['review_mode_offset']]==0 for r in info['variants'])
    prior=info['previous_review_validation'];path=Path(prior['file'])
    assert not path.is_absolute() and '..' not in path.parts
    raw=(ROOT/path).read_bytes();assert hashlib.sha256(raw).hexdigest()==prior['sha256']
    from verify_surf_review_update import verify_update as verify_previous
    verify_previous(directory,old,historical_review=json.loads(raw))
