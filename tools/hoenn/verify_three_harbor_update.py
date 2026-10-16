"""Bind exact harbor bounds and physical evidence to every current edition."""
import hashlib,json
from pathlib import Path
from verify_fuchsia_update import previous_release

BOXES={19:[4,11,7,4],21:[61,6,6,4],12:[15,47,5,4]}


def verify_update(directory,info):
    directory=Path(directory);old=previous_release(info)
    assert old['validated'] and old['integration_layers']+['three-harbor-terminals']==info['integration_layers']
    assert info['historical_validation']==old['historical_validation'] and info['previous_validation']==old['previous_validation']
    expected={'common':info['parent_rom_sha256'],**{r['file']:r['sha256'] for r in info['variants']}}
    covered=set()
    for p in info['proofs']:
        path=Path(p['file']);assert not path.is_absolute() and '..' not in path.parts
        raw=(directory/path).read_bytes();assert hashlib.sha256(raw).hexdigest()==p['sha256']
        r=json.loads(raw);assert r['passed'] and r['rom_sha256']==expected[p['target']]
        if p['kind']=='three-harbors':
            assert {c['pid'] for c in r['ports']}==set(BOXES)
            for c in r['ports']:
                assert c['terminal']==BOXES[c['pid']]
                for field in ['controller_entry_and_exit','quay_walked_without_surf','one_indoor_captain',
                    'medium_boat_hull_blocked_over_water','inside_ship_hull_blocked_over_water',
                    'captain_interacted_physically','network_arrival_inside','save_continue_inside']:
                    assert c[field] is True,(c['name'],field)
                assert [t['destination'] for t in c['trips']]==['JourneyPalletHarbor',c['interior']]
                if c['pid']==12:assert c['briney_local_service_preserved']
                if c['pid']==19:assert c['legacy_exit_preserved']
        elif p['kind']=='three-harbor-source':
            assert p['target']=='common' and r['original_inputs_verified'] and r['idempotent'] and not r['differences']
            assert r['unrelated_source_inputs_checked']>30000
            for field in ['exact_requested_bounds','existing_npcs_and_story_preserved','atlas_unchanged',
                'vermilion_and_pacifidlog_preserved','all_other_ports_preserved','shared_art_pixel_identical']:
                assert r[field] is True,field
        else:raise AssertionError(p['kind'])
        covered.add((p['target'],p['kind']))
    assert {(t,'three-harbors') for t in expected}|{('common','three-harbor-source')}<=covered
    for p in old['proofs']:assert hashlib.sha256((directory/p['file']).read_bytes()).hexdigest()==p['sha256']
