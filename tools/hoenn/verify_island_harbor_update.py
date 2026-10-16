"""Bind the island harbor controls and authored terrain to the current four ROMs."""
import hashlib,json
from pathlib import Path
from verify_fuchsia_update import previous_release


def verify_update(directory,info):
    directory=Path(directory);old=previous_release(info)
    assert old['validated'] and old['integration_layers']+['mossdeep-harbor','dewford-island-harbor']==info['integration_layers']
    expected={'common':info['parent_rom_sha256'],**{r['file']:r['sha256'] for r in info['variants']}};covered=set()
    for p in info['proofs']:
        path=Path(p['file']);assert not path.is_absolute() and '..' not in path.parts
        raw=(directory/path).read_bytes();assert hashlib.sha256(raw).hexdigest()==p['sha256']
        r=json.loads(raw);assert r['passed'] and r['rom_sha256']==expected[p['target']]
        if p['kind']=='mossdeep-harbor':
            assert r['terminal']==[3,26,5,5]
            assert r['pier']==[[x,y] for y in (29,30) for x in range(8,12)]
            for field in ['controller_entry_and_exit','both_pier_rows_walked_without_surf','outside_boat_over_water','inside_ship_over_water','legacy_exit_preserved']:assert r[field] is True,field
            assert [t['destination'] for t in r['trips']]==['JourneyPalletHarbor','JourneyMossdeepHarbor']
        elif p['kind']=='dewford-island-harbor':
            assert r['door']==[5,2] and r['stairs_walked']==[[5,3],[6,3],[5,15],[6,15]]
            for field in ['continuous_straight_two_tile_deck','bridge_walked_above_without_surf','surf_crossed_below_without_dismounting','exterior_transit_boat_removed','controller_entry_and_exit','north_island_seamless_controller_connections']:assert r[field] is True,field
            assert [t['destination'] for t in r['trips']]==['JourneyPalletHarbor','JourneyDewfordHarbor']
        elif p['kind']=='island-harbor-source':
            assert p['target']=='common' and r['layers']==info['integration_layers']
            assert r['requested_tile_copies_verified']==17 and r['stairs']==[[5,3],[6,3],[5,15],[6,15]]
            assert r['whole_trees']==31 and r['complete_rock_groups']==52
            for field in ['original_inputs_verified','idempotent','independent_replay_passed','battle_frontier_preserved','other_port_inputs_preserved','bridge_foreground_retained']:assert r[field] is True,field
            assert not r['differences'] and r['unrelated_source_inputs_checked']>30000
        else:raise AssertionError(p['kind'])
        covered.add((p['target'],p['kind']))
    assert {(t,k) for t in expected for k in ['mossdeep-harbor','dewford-island-harbor']}|{('common','island-harbor-source')}<=covered
    from verify_sevii_harbor_update import verify_update as verify_previous
    verify_previous(directory,old)
