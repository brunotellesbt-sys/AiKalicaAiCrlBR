"""Verify four harbor builds and keep previous coastal evidence bound to its ROM."""
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def verify_update(directory, info):
    directory = Path(directory)
    expected = {v['file']: v['sha256'] for v in info['variants']}
    covered = set()
    for proof in info['proofs']:
        path = Path(proof['file'])
        assert not path.is_absolute() and '..' not in path.parts
        raw = (directory/path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == proof['sha256']
        report = json.loads(raw)
        assert report['passed'] is True
        if proof['kind'] == 'reproduction':
            assert proof['target'] == 'common'
            assert report['original_inputs_verified'] and report['idempotent']
            assert report['layers'] == info['integration_layers']
            assert len(report['byte_identical_outputs']) == 21
        elif proof['kind'] == 'special-encounters':
            assert proof['target'] in expected
            assert report['rom_sha256'] == expected[proof['target']], 'Stale workshop evidence'
            assert report['actual_tv_capture_and_form_ui'] is True
            assert len(report['rotom_changes']) == 6
            assert len(report['dex_locations']) == report['event_only_families'] == 21
            assert report['form_tools_available'] == 54
        else:
            assert proof['kind'] == 'sootopolis-harbor'
            sha = info['parent_rom_sha256'] if proof['target'] == 'common' else expected[proof['target']]
            assert report['rom_sha256'] == sha, 'Stale harbor evidence'
            for field in ['bridge_walked_without_surf', 'controller_entry_and_exit',
                          'crisis_layout_controller_access', 'captain_interacted_physically',
                          'submarine_hull_blocked_over_water', 'returned_to_original_land',
                          'shore_end_uses_native_grass', 'extra_bottom_bridge_row_removed',
                          'bridge_end_stays_in_original_tile']:
                assert report[field] is True, field
            assert report['submarine_sprite_size'] == [64, 64]
            assert [t['destination'] for t in report['trips']] == ['SlateportCity_Harbor', 'JourneySootopolisHarbor']
            assert all(t['native_animation_observations'] >= 5 for t in report['trips'])
            assert report['full_campaign_playthrough'] is False
        covered.add((proof['target'], proof['kind']))
    assert {(name, 'sootopolis-harbor') for name in expected} <= covered
    assert {(name, 'special-encounters') for name in expected} <= covered
    assert info['special_encounters_validated'] is True
    assert {('common', 'sootopolis-harbor'), ('common', 'reproduction')} <= covered
    assert info['full_campaign_playthrough'] is False

    # Preserve the previously published coastal proof instead of claiming its
    # unrelated PWT, battle and journey checks ran on these new ROM bytes.
    previous = info['previous_validation']
    assert previous['retested_on_current_rom'] is False
    for key in ['manifest', 'parent_rom', 'evidence_directory']:
        path = Path(previous[key])
        assert not path.is_absolute() and '..' not in path.parts
    raw = (ROOT/previous['manifest']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == previous['manifest_sha256']
    old = json.loads(raw)
    assert info['historical_validation'] == old['historical_validation']
    archive = (ROOT/previous['parent_rom']).read_bytes()
    assert hashlib.sha256(archive).hexdigest() == previous['parent_archive_sha256']
    parent = gzip.decompress(archive)
    assert hashlib.sha256(parent).hexdigest() == old['parent_rom_sha256']
    for proof in old['proofs']:
        path = Path(proof['file'])
        assert not path.is_absolute() and '..' not in path.parts
        raw = (ROOT/previous['evidence_directory']/path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == proof['sha256']
        report = json.loads(raw)
        assert report['passed'] is True
    return info
