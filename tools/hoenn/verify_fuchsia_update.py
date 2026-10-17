"""Verify the focused Fuchsia release and its explicitly historical baseline."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def previous_release(info):
    reference=info['previous_port_validation']
    path=Path(reference['manifest'])
    assert not path.is_absolute() and '..' not in path.parts
    raw=(ROOT/path).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==reference['manifest_sha256']
    assert reference['retested_on_current_rom'] is False
    return json.loads(raw)


def harbor_baseline(info):
    """Resolve the release on which unchanged older features were exercised."""
    while info.get('validation_scope') in ('ever-grande-market','dewford-competitive-shop','surf-review','annotated-world-links','island-harbors','sevii-harbors','three-harbor-terminals','fuchsia-harbor'):
        info=previous_release(info)
    return info


def verify_update(directory,info):
    directory=Path(directory)
    baseline=previous_release(info)
    assert info['historical_validation']==baseline['historical_validation']
    assert info['previous_validation']==baseline['previous_validation']
    assert baseline['validated'] and baseline['integration_layers']+['fuchsia-harbor']==info['integration_layers']
    expected={'common':info['parent_rom_sha256'],**{r['file']:r['sha256'] for r in info['variants']}}
    covered=set()
    for proof in info['proofs']:
        path=Path(proof['file']);assert not path.is_absolute() and '..' not in path.parts
        raw=(directory/path).read_bytes();assert hashlib.sha256(raw).hexdigest()==proof['sha256']
        r=json.loads(raw);assert r['passed']
        kind,target=proof['kind'],proof['target']
        if kind=='fuchsia-harbor':
            assert r['rom_sha256']==expected[target]
            for field in ['controller_entry_and_exit','quay_walked_without_surf','outside_captain_removed',
                'one_indoor_captain','captain_interacted_physically','medium_boat_hull_blocked_over_water',
                'ship_hull_blocked_over_water','network_arrivals_inside_terminal',
                'save_continue_inside_terminal','returned_to_original_beach','old_lodge_exit_walked']:
                assert r[field] is True,field
            assert r['medium_boat_sprite_size']==[64,64] and r['ship_sprite_size']==[96,40]
            assert [t['destination'] for t in r['trips']]==['JourneyPalletHarbor','JourneyFuchsiaHarbor']
        elif kind=='fuchsia-source':
            assert target=='common' and r['rom_sha256']==expected[target]
            assert r['original_inputs_verified'] and r['idempotent'] and not r['differences']
            assert r['unrelated_source_inputs_checked']>30000
            assert r['atlas_unchanged'] and r['other_ports_unchanged'] and r['existing_trainers_preserved']
            assert r['secondary_existing_metatiles_preserved'] and r['other_fuchsia_maps_pixel_identical']
        else:raise AssertionError(kind)
        covered.add((target,kind))
    assert {(t,'fuchsia-harbor') for t in expected}|{('common','fuchsia-source')}<=covered
    # Historical reports remain attached to their original hashes; do not
    # relabel old campaign/coast tests as runs of the new ROM.
    for p in baseline['proofs']:
        assert hashlib.sha256((directory/p['file']).read_bytes()).hexdigest()==p['sha256']
