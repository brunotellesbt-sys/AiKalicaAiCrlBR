"""Verify layer 170 complete coast scenery and preserve layer 169 as pinned history."""
import hashlib
import json
from pathlib import Path

import coast_scenery_review_contract as contract
from verify_sevii_route_boundaries_update import review_identity
from publish_coastal_closures import report_dependencies
from verify_coastal_closures_update import verify_cold_boot, verify_review_mode
from verify_fuchsia_update import ROOT, previous_release

SCOPE = contract.SCOPE
COMMON_KINDS = frozenset({'coast-scenery-review-source', 'coast-scenery-review-native'})
EDITION_KINDS = frozenset({'review-mode', 'cold-boot'})
OPTIONAL_COMMON_KINDS = frozenset()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def baseline(name, raw):
    assert hashlib.sha256(raw).hexdigest() == contract.BASELINE_SHA256[name], ('Layer-169 baseline changed', name)
    if name == 'versions.json':
        old = json.loads(raw)
        assert old['validated'] is True and old['validation_scope'] == 'sevii-route-boundaries'
        assert old['parent_rom_sha256'] == contract.PARENT_ROM_SHA256
        assert len(old['integration_layers']) == 169 and len(old['proofs']) == 12
        return old
    if name == 'test.sav':
        assert len(raw) == 131072


def require_final_contract():
    assert contract.PREPARED_SHA256, 'Final coast scenery source hashes are not pinned'
    assert contract.NATIVE_CONTRACT_FINALIZED is True, 'Coast scenery native contracts are not finalized'


def required_keys(info):
    targets = {'test', *[row['file'] for row in info['variants']]}
    return ({('common', kind) for kind in COMMON_KINDS} |
            {(target, kind) for target in targets for kind in EDITION_KINDS})


def verify_source(report, directory, info, old):
    from verify_coast_scenery_review_source import verify_report
    assert report['layers'] == info['integration_layers']
    assert report['parent_rom_sha256'] == old['parent_rom_sha256'] == contract.PARENT_ROM_SHA256
    assert report['prepared_sha256'] == contract.PREPARED_SHA256
    assert set(report['changed_files']) == set(contract.PREPARED_SHA256)
    verify_report(report, directory, report['rom_sha256'])


def verify_native(report, directory):
    from verify_coast_scenery_review_native import verify_report
    verify_report(report, directory, report['rom_sha256'])


def verify_proof(report, directory, kind, target, save, info, old):
    assert report['passed'] is True and report.get('kind', kind) == kind, kind
    if kind in COMMON_KINDS:
        assert target == 'common'
    if kind == 'coast-scenery-review-source':
        verify_source(report, directory, info, old)
    elif kind == 'coast-scenery-review-native':
        verify_native(report, directory)
    elif kind == 'review-mode':
        verify_review_mode(report, target == 'test', save)
    elif kind == 'cold-boot':
        verify_cold_boot(report, target == 'test', save)
    else:
        raise AssertionError(('Unknown coast scenery proof', kind, target))


def verify_elf_binding(reports):
    common = {kind: [report for observed, report in reports if observed == kind] for kind in COMMON_KINDS}
    assert all(len(rows) == 1 for rows in common.values()), 'Exactly one compiled source and native proof are required'
    source = common['coast-scenery-review-source'][0]
    elf = source['elf_sha256']
    assert isinstance(elf, str) and len(elf) == 64 and set(elf) <= set('0123456789abcdef')
    for kind, rows in common.items():
        report = rows[0]
        assert report['elf_sha256'] == elf, ('Unaudited native ELF', kind)
        assert report['rom_sha256'] == source['rom_sha256'], ('Mixed common ROMs', kind)


def verify_update(directory, info, *, historical_review=None, historical_save=None):
    require_final_contract()
    directory = Path(directory)
    old = previous_release(info)
    ref = info['previous_port_validation']
    assert baseline('versions.json', (ROOT/ref['manifest']).read_bytes()) == old
    assert ref['manifest_sha256'] == contract.BASELINE_SHA256['versions.json']
    assert ref['retested_on_current_rom'] is False
    assert info['integration_layers'] == old['integration_layers'] + [SCOPE] and len(info['integration_layers']) == 170
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
    assert info['historical_release'] == dict(scope='sevii-route-boundaries',
        parent_rom_sha256=old['parent_rom_sha256'], variants={row['file']: row['sha256'] for row in old['variants']},
        test_rom_sha256=previous_review['sha256'], proof_count=12, retested_on_current_rom=False)
    from verify_sevii_route_boundaries_update import verify_update as verify_previous
    verify_previous(directory, old, historical_review=previous_review, historical_save=references['test.sav'])
    return info
