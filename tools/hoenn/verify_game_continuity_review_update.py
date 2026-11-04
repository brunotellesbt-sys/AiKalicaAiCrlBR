"""Verify layer 168 campaign/camera proofs while retaining layer 167 as history."""
import hashlib
import json
from pathlib import Path

import game_continuity_review_contract as contract
from package_review_rom import verify as verify_review
from publish_coastal_closures import report_dependencies
from verify_coastal_closures_update import verify_cold_boot, verify_review_mode
from verify_fuchsia_update import ROOT, previous_release
from verify_sevii_integrated_piers_update import require_true

SCOPE = contract.SCOPE
COMMON_KINDS = frozenset({'game-continuity-source', 'game-continuity-campaign', 'game-continuity-coasts'})
EDITION_KINDS = frozenset({'review-mode', 'cold-boot'})
OPTIONAL_COMMON_KINDS = frozenset()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def baseline(name, raw):
    assert hashlib.sha256(raw).hexdigest() == contract.BASELINE_SHA256[name], ('Layer-167 baseline changed', name)
    if name == 'versions.json':
        old = json.loads(raw)
        assert old['validated'] is True and old['validation_scope'] == 'arrival-coast-review'
        assert len(old['integration_layers']) == 167 and len(old['proofs']) == 13
        return old
    if name == 'test.sav':
        assert len(raw) == 131072


def require_final_contract():
    assert contract.PREPARED_SHA256, 'Final game-continuity source hashes are not pinned'
    assert contract.NATIVE_CONTRACT_FINALIZED is True, 'Game-continuity native contracts are not finalized'


def required_keys(info):
    targets = {'test', *[row['file'] for row in info['variants']]}
    return ({('common', kind) for kind in COMMON_KINDS} |
            {(target, kind) for target in targets for kind in EDITION_KINDS})


def verify_campaign(report, directory):
    # Import only after the actual native observations establish the schema.
    from verify_game_continuity_campaign import verify
    verify(report, directory)


def verify_coasts(report, directory):
    from verify_game_continuity_coasts import verify
    verify(report, directory)


def verify_proof(report, directory, kind, target, save, info, old):
    assert report['passed'] is True and report.get('kind', kind) == kind, kind
    if kind == 'game-continuity-source':
        require_true(report, ['compiled_rom', 'independent_replay', 'idempotent',
            'unrelated_source_files_unchanged', 'atlas_graphics_unchanged',
            'ecology_and_battle_source_unchanged', 'arrival_and_pier_source_unchanged',
            'event_scripts_and_save_abi_unchanged'])
        assert report['preflight'] is False and report['layers'] == info['integration_layers']
        assert report['parent_rom_sha256'] == old['parent_rom_sha256'] == contract.PARENT_ROM_SHA256
        assert report['prepared_sha256'] == contract.PREPARED_SHA256
        assert set(report['changed_files']) == set(contract.PREPARED_SHA256)
        assert report['source_hashes_checked'] >= 32244 and report['preserved_spatial_inputs'] >= 6000
        blocks = report['compiled_blockdata']
        expected = {name: sha for name, sha in contract.PREPARED_SHA256.items() if name.endswith('.bin')}
        assert {row['file']: row['sha256'] for row in blocks} == expected
        assert all(row['bytes'] > 0 for row in blocks)
        runtime = report['compiled_runtime_symbols']
        assert {row['symbol'] for row in runtime} == {'JourneyPendingCampaignEvent', 'JourneyStoryObjectVisible', 'JourneyCurrentGymGate'}
        assert all(row['bytes'] > 0 and len(row['sha256']) == 64 for row in runtime)
        banks = report['compiled_layout_banks']
        assert len(banks) == len({row['layout'] for row in banks}) == 16
        assert all(row['primary_symbol'] and row['secondary_symbol'] and row['compiled_bank_pointers_match'] is True for row in banks)
    elif kind == 'game-continuity-campaign':
        verify_campaign(report, directory)
    elif kind == 'game-continuity-coasts':
        verify_coasts(report, directory)
    elif kind == 'review-mode':
        verify_review_mode(report, target == 'test', save)
    elif kind == 'cold-boot':
        verify_cold_boot(report, target == 'test', save)
    else:
        raise AssertionError(('Unknown game-continuity proof', kind, target))


def verify_elf_binding(reports):
    sources = [report for kind, report in reports if kind == 'game-continuity-source']
    assert len(sources) == 1, 'Exactly one compiled source proof is required'
    elf = sources[0]['elf_sha256']
    assert isinstance(elf, str) and len(elf) == 64
    for kind, report in reports:
        if kind in COMMON_KINDS:
            assert report['elf_sha256'] == elf, ('Unaudited native ELF', kind)
        if kind=='game-continuity-coasts':
            expected={r['layout']:(r['primary_pointer'],r['secondary_pointer']) for r in sources[0]['compiled_layout_banks']}
            layouts={r['map']:r['layout'] for r in report['source_assignments']}
            observed={layouts[r['map']]:(r['before_bank']['primary_pointer'],r['before_bank']['secondary_pointer']) for r in report['cases']}
            assert observed==expected,'Native camera banks differ from compiled source bindings'


def verify_update(directory, info):
    require_final_contract()
    directory = Path(directory)
    old = previous_release(info)
    ref = info['previous_port_validation']
    assert baseline('versions.json', (ROOT/ref['manifest']).read_bytes()) == old
    assert ref['manifest_sha256'] == contract.BASELINE_SHA256['versions.json']
    assert ref['retested_on_current_rom'] is False
    assert info['integration_layers'] == old['integration_layers'] + [SCOPE] and len(info['integration_layers']) == 168
    assert info['historical_validation'] == old['historical_validation']
    assert info['previous_validation'] == old['previous_validation']
    assert info['full_campaign_playthrough'] is info['previous_features_retested_on_current_rom'] is False
    references = {}
    for key, name in [('previous_review_validation', 'review.json'), ('previous_review_save_validation', 'test.sav')]:
        row = info[key]
        path = ROOT/row['file']
        assert digest(path) == row['sha256'] == contract.BASELINE_SHA256[name]
        baseline(name, path.read_bytes())
        references[name] = path
    test = verify_review(ROOT/'roms/rom-de-teste', directory/'Pokemon-Journey-Gen1-9-Normal.gba')
    expected = {'common': info['parent_rom_sha256'], 'test': test['sha256'],
                **{row['file']: row['sha256'] for row in info['variants']}}
    covered, reports = set(), []
    for proof in info['proofs']:
        key = proof['target'], proof['kind']
        assert key not in covered and key in required_keys(info)
        covered.add(key)
        relative = Path(proof['file'])
        assert not relative.is_absolute() and '..' not in relative.parts
        file = directory/relative
        report_dependencies(file, expected_sha=proof['sha256'])
        report = json.loads(file.read_bytes())
        assert report['rom_sha256'] == expected[proof['target']], ('Stale current proof', key)
        reports.append((proof['kind'], report))
        verify_proof(report, file.parent, proof['kind'], proof['target'],
                     ROOT/'roms/rom-de-teste/Pokemon-Journey-TESTE.sav', info, old)
    assert required_keys(info) == covered
    verify_elf_binding(reports)
    previous_review = json.loads(references['review.json'].read_bytes())
    assert info['historical_release'] == dict(scope='arrival-coast-review',
        parent_rom_sha256=old['parent_rom_sha256'], variants={row['file']: row['sha256'] for row in old['variants']},
        test_rom_sha256=previous_review['sha256'], proof_count=13, retested_on_current_rom=False)
    from verify_arrival_coast_review_update import verify_update as verify_previous
    verify_previous(directory, old, historical_review=previous_review, historical_save=references['test.sav'])
    return info
