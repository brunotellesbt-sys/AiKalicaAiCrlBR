"""Bind the Sevii-only release to current Surf proof and preserved harbor history."""
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
ISLANDS={'OneIsland_Frlg','TwoIsland_Frlg','ThreeIsland_Port_Frlg','FourIsland_Frlg','FiveIsland_Frlg','SixIsland_Frlg','SevenIsland_Frlg'}

def verify_update(directory,info):
    directory=Path(directory);variants={r['file']:r['sha256'] for r in info['variants']};covered=set()
    for p in info['proofs']:
        path=Path(p['file']);assert not path.is_absolute() and '..' not in path.parts
        raw=(directory/path).read_bytes();assert hashlib.sha256(raw).hexdigest()==p['sha256'];r=json.loads(raw);assert r['passed']
        kind,target=p['kind'],p['target'];expected=info['parent_rom_sha256'] if target=='common' else variants[target]
        if kind=='reproduction':
            assert target=='common' and r['layers']==info['integration_layers'] and not r['differences']
            assert r['original_inputs_verified'] and r['idempotent'] and len(r['reproduced_layers'])==4
        else:assert r['rom_sha256']==expected,(kind,target,'Stale evidence')
        if kind=='sevii-surf-connections':
            assert {i['map'] for i in r['islands']}==ISLANDS and len(r['seams'])==14
            assert r['controller_roundtrip'] and r['native_disembark'] and r['no_midroute_warps_or_coordinate_writes']
            assert r['save_continue_preserves_location'] and r['first_arrival_surf_does_not_trigger_ferry_cutscene']
            assert r['active_screen_fade_frames']==0 and r['observed_seam_frames']>1000 and r['walked_tiles']>1000
            assert len(r['marker_samples'])==r['walked_tiles']+1
        elif kind=='sevii-source-scope':
            assert r['port_buildings_boats_captains_and_warps_unchanged'] and r['native_sevii_land_unchanged']
            assert r['birth_and_navel_arrival_layout_preserved']
            assert r['unchanged_source_inputs_checked']>30000 and r['preserved_port_paths']
            assert r['compiled_gps_tiles']==408618 and r['maximum_neighbor_pixel_step']<=2 and r['maximum_seam_delta']==0
            assert not any('sootopolis' in n.lower() or 'pallet' in n.lower() for n in r['changed_source_files'])
        elif kind=='coast-connectivity':
            assert r['all_integrated_surface_seas_reachable'] and r['compiled_collision_and_water_behaviors']
            assert ISLANDS<=set(r['reachable_maps'])
        elif kind=='special-encounters':
            assert r['actual_tv_capture_and_form_ui'] and len(r['rotom_changes'])==6
            assert len(r['dex_locations'])==r['event_only_families']==21 and r['form_tools_available']==54
        else:assert kind=='reproduction',kind
        covered.add((target,kind))
    assert {('common',k) for k in ['sevii-surf-connections','sevii-source-scope','coast-connectivity','reproduction']}<=covered
    assert {(n,k) for n in variants for k in ['sevii-surf-connections','special-encounters']}<=covered
    reference=info['previous_sootopolis_validation'];assert reference['retested_on_current_rom'] is False
    raw=(ROOT/reference['manifest']).read_bytes();assert hashlib.sha256(raw).hexdigest()==reference['manifest_sha256']
    previous=json.loads(raw)
    from verify_sootopolis_update import verify_update as verify_previous
    verify_previous(directory,previous)
    assert info['historical_validation']==previous['historical_validation']
    assert info['special_encounters_validated'] and info['full_campaign_playthrough'] is False
    return info
