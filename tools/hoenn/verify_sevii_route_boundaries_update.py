"""Verify layer 169 Sevii boundaries and preserve layer 168 as pinned history."""
import hashlib
import json
from pathlib import Path

import sevii_route_boundaries_contract as contract
from package_review_rom import verify as verify_review
from publish_coastal_closures import report_dependencies
from verify_coastal_closures_update import verify_cold_boot, verify_review_mode
from verify_fuchsia_update import ROOT, previous_release

SCOPE = contract.SCOPE
COMMON_KINDS = frozenset({'sevii-route-boundaries-source', 'sevii-route-boundaries-native'})
EDITION_KINDS = frozenset({'review-mode', 'cold-boot'})
OPTIONAL_COMMON_KINDS = frozenset()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def baseline(name, raw):
    assert hashlib.sha256(raw).hexdigest() == contract.BASELINE_SHA256[name], ('Layer-168 baseline changed', name)
    if name == 'versions.json':
        old = json.loads(raw)
        assert old['validated'] is True and old['validation_scope'] == 'game-continuity-review'
        assert old['parent_rom_sha256'] == contract.PARENT_ROM_SHA256
        assert len(old['integration_layers']) == 168 and len(old['proofs']) == 13
        return old
    if name == 'test.sav':
        assert len(raw) == 131072


def require_final_contract():
    assert contract.PREPARED_SHA256, 'Final Sevii boundary source hashes are not pinned'
    assert contract.NATIVE_CONTRACT_FINALIZED is True, 'Sevii boundary native contracts are not finalized'


def required_keys(info):
    targets = {'test', *[row['file'] for row in info['variants']]}
    return ({('common', kind) for kind in COMMON_KINDS} |
            {(target, kind) for target in targets for kind in EDITION_KINDS})


def verify_source(report, directory, info, old):
    from verify_sevii_route_boundaries_source import verify_report
    assert report['layers'] == info['integration_layers']
    assert report['parent_rom_sha256'] == old['parent_rom_sha256'] == contract.PARENT_ROM_SHA256
    assert report['prepared_sha256'] == contract.PREPARED_SHA256
    assert set(report['changed_files']) == set(contract.PREPARED_SHA256)
    verify_report(report, directory, report['rom_sha256'])


def verify_native(report, directory):
    from verify_sevii_route_boundaries_native import verify_report
    verify_report(report, directory, report['rom_sha256'])


def verify_proof(report, directory, kind, target, save, info, old):
    assert report['passed'] is True and report.get('kind', kind) == kind, kind
    if kind in COMMON_KINDS:
        assert target == 'common'
    if kind == 'sevii-route-boundaries-source':
        verify_source(report, directory, info, old)
    elif kind == 'sevii-route-boundaries-native':
        verify_native(report, directory)
    elif kind == 'review-mode':
        verify_review_mode(report, target == 'test', save)
    elif kind == 'cold-boot':
        verify_cold_boot(report, target == 'test', save)
    else:
        raise AssertionError(('Unknown Sevii boundary proof', kind, target))


def verify_elf_binding(reports):
    common = {kind: [report for observed, report in reports if observed == kind] for kind in COMMON_KINDS}
    assert all(len(rows) == 1 for rows in common.values()), 'Exactly one compiled source and native proof are required'
    source = common['sevii-route-boundaries-source'][0]
    elf = source['elf_sha256']
    assert isinstance(elf, str) and len(elf) == 64 and set(elf) <= set('0123456789abcdef')
    for kind, rows in common.items():
        report = rows[0]
        assert report['elf_sha256'] == elf, ('Unaudited native ELF', kind)
        assert report['rom_sha256'] == source['rom_sha256'], ('Mixed common ROMs', kind)


def review_identity(directory, info, *, historical_review=None, historical_save=None):
    """Resolve the TESTE identity without reading a newer public edition."""
    if historical_review is None:
        assert historical_save is None
        test = verify_review(ROOT/'roms/rom-de-teste', Path(directory)/'Pokemon-Journey-Gen1-9-Normal.gba')
        return test, ROOT/'roms/rom-de-teste/Pokemon-Journey-TESTE.sav'
    assert historical_save is not None, 'Historical TESTE evidence requires its pinned save'
    test = historical_review
    normal = next(row for row in info['variants'] if row['file'] == test['base_normal_file'])
    assert test['base_normal_sha256'] == normal['sha256'] and test['bytes'] == 33554432
    assert test['file'] == 'Pokemon-Journey-TESTE.gba' and test['separate_save_identity'] is True
    assert test['random_wild_encounters'] is False and test['automatic_trainer_approaches'] is False
    assert test['fishing_encounters'] is False and test['manual_trainer_and_legendary_interactions_preserved'] is True
    save = Path(historical_save)
    assert save.is_file() and save.stat().st_size == 131072
    return test, save


def verify_update(directory, info, *, historical_review=None, historical_save=None):
    require_final_contract()
    directory = Path(directory)
    old = previous_release(info)
    ref = info['previous_port_validation']
    assert baseline('versions.json', (ROOT/ref['manifest']).read_bytes()) == old
    assert ref['manifest_sha256'] == contract.BASELINE_SHA256['versions.json']
    assert ref['retested_on_current_rom'] is False
    assert info['integration_layers'] == old['integration_layers'] + [SCOPE] and len(info['integration_layers']) == 169
    assert info['historical_validation'] == old['historical_validation']
    assert info['previous_validation'] == old['previous_validation']
    assert info['full_campaign_playthrough'] is info['previous_features_retested_on_current_rom'] is False
    references = {}
    for key, name in [('previous_review_validation', 'review.json'), ('previous_review_save_validation', 'test.sav')]:
        row = info[key]
        relative = Path(row['file'])
        assert not relative.is_absolute() and '..' not in relative.parts
        path = ROOT/relative
        assert digest(path) == row['sha256'] == contract.BASELINE_SHA256[name]
        baseline(name, path.read_bytes())
        references[name] = path
    test, proof_save = review_identity(directory, info, historical_review=historical_review,
                                       historical_save=historical_save)
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
                     proof_save, info, old)
    assert required_keys(info) == covered
    verify_elf_binding(reports)
    previous_review = json.loads(references['review.json'].read_bytes())
    assert info['historical_release'] == dict(scope='game-continuity-review',
        parent_rom_sha256=old['parent_rom_sha256'], variants={row['file']: row['sha256'] for row in old['variants']},
        test_rom_sha256=previous_review['sha256'], proof_count=13, retested_on_current_rom=False)
    from verify_game_continuity_review_update import verify_update as verify_previous
    verify_previous(directory, old, historical_review=previous_review, historical_save=references['test.sav'])
    return info
