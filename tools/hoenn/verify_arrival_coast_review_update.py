"""Verify layer 167 arrivals/coast proofs and retain layer 166 as history."""
import hashlib
import json
from pathlib import Path

import arrival_coast_review_contract as contract
from package_review_rom import verify as verify_review
from publish_coastal_closures import report_dependencies
from verify_coastal_closures_update import verify_cold_boot, verify_review_mode
from verify_fuchsia_update import ROOT, previous_release
from verify_sevii_integrated_piers_update import require_true, verify_captures

SCOPE=contract.SCOPE
COMMON_KINDS=frozenset({'arrival-coast-source','arrival-coast-landing','arrival-coast-photos'})
EDITION_KINDS=frozenset({'review-mode','cold-boot'})
OPTIONAL_COMMON_KINDS=frozenset()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def baseline(name,raw):
    assert hashlib.sha256(raw).hexdigest()==contract.BASELINE_SHA256[name], ('Layer-166 baseline changed',name)
    if name=='versions.json':
        old=json.loads(raw)
        assert old['validated'] is True and old['validation_scope']=='coastal-ecology'
        assert len(old['integration_layers'])==166 and len(old['proofs'])==20
        return old
    if name=='test.sav':assert len(raw)==131072


def require_final_contract():
    assert contract.PREPARED_SHA256, 'Final arrival/coast source hashes are not pinned'
    assert contract.NATIVE_CONTRACT_FINALIZED is True, 'Arrival/coast native contracts are not finalized'


def required_keys(info):
    targets={'test',*[r['file'] for r in info['variants']]}
    return ({('common',kind) for kind in COMMON_KINDS}|
            {(target,kind) for target in targets for kind in EDITION_KINDS})


def verify_landing(report,directory):
    from verify_arrival_coast_landing_proof import verify
    verify(report, directory)


def verify_photos(report,directory):
    from verify_arrival_coast_one_proof import verify as verify_one
    from verify_arrival_coast_forest_proof import verify as verify_forest
    from verify_arrival_coast_cinnabar_proof import verify as verify_cinnabar
    directory = Path(directory)
    assert report['kind'] == 'arrival-coast-photos'
    require_true(report, ['passed', 'compiled_rom', 'native_validation_performed'])
    assert report['full_campaign_playthrough'] is False
    expected = {
        'arrival-coast-one-native': ('one/arrival-coast-one-native.json', verify_one),
        'arrival-coast-forest-native': ('forest/arrival-coast-forest-native.json', verify_forest),
        'cinnabar-door-exit': ('cinnabar/cinnabar-door-exit.json', verify_cinnabar),
    }
    components = report['components']
    assert len(components) == len(expected)
    assert {row['kind'] for row in components} == set(expected)
    for row in components:
        name, verify = expected[row['kind']]
        assert row['file'] == name
        path = directory/name
        report_dependencies(path, expected_sha=row['sha256'])
        child = json.loads(path.read_bytes())
        assert child['kind'] == row['kind'] and child['passed'] is True
        assert child['rom_sha256'] == report['rom_sha256'], ('Stale coastal observation', name)
        assert child['elf_sha256'] == report['elf_sha256'], ('Mixed coastal native ELF', name)
        verify(child, path.parent)


def verify_proof(report,directory,kind,target,save,info,old):
    assert report['passed'] is True and report.get('kind',kind)==kind, kind
    if kind=='arrival-coast-source':
        require_true(report,['compiled_rom','independent_replay','idempotent',
            'unrelated_source_files_unchanged','atlas_graphics_unchanged',
            'ecology_and_battle_source_unchanged','campaign_scripts_and_save_abi_unchanged'])
        assert report['preflight'] is False and report['layers']==info['integration_layers']
        assert report['parent_rom_sha256']==old['parent_rom_sha256']==contract.PARENT_ROM_SHA256
        assert report['prepared_sha256']==contract.PREPARED_SHA256
        assert set(report['changed_files'])==set(contract.PREPARED_SHA256)
        assert report['source_hashes_checked']>=32244 and report['preserved_spatial_inputs']>=6000
        blocks=report['compiled_blockdata']
        expected={name:sha for name,sha in contract.PREPARED_SHA256.items() if name.endswith('.bin')}
        assert {r['file']:r['sha256'] for r in blocks}==expected
        assert all(row['bytes']>0 for row in blocks)
        table=report['compiled_birth_table']
        assert table['symbol']=='sJourneyBirthArrivals' and table['bytes']==31*12
        assert len(table['sha256'])==64
        runtime=report['compiled_runtime_symbols']
        assert {row['symbol'] for row in runtime}=={'GetCollisionAtCoords','ObjectEventUpdateElevation','InitObjectEventsReturnToField'}
        assert all(row['bytes']>0 and len(row['sha256'])==64 for row in runtime)
    elif kind=='arrival-coast-landing':verify_landing(report,directory)
    elif kind=='arrival-coast-photos':verify_photos(report,directory)
    elif kind=='review-mode':verify_review_mode(report,target=='test',save)
    elif kind=='cold-boot':verify_cold_boot(report,target=='test',save)
    else:raise AssertionError(('Unknown arrival/coast proof',kind,target))


def verify_elf_binding(reports):
    sources=[report for kind,report in reports if kind=='arrival-coast-source']
    assert len(sources)==1, 'Exactly one compiled source proof is required'
    elf=sources[0]['elf_sha256']
    assert isinstance(elf,str) and len(elf)==64
    for kind,report in reports:
        if kind in COMMON_KINDS:assert report['elf_sha256']==elf, ('Unaudited native ELF',kind)
        if kind=='arrival-coast-landing':
            assert report['compiled_arrival_census']['compiled_table_sha256']==sources[0]['compiled_birth_table']['sha256'], 'Arrival observations differ from the bound compiled table'


def verify_update(directory,info):
    require_final_contract()
    directory=Path(directory);old=previous_release(info)
    ref=info['previous_port_validation']
    assert baseline('versions.json',(ROOT/ref['manifest']).read_bytes())==old
    assert ref['manifest_sha256']==contract.BASELINE_SHA256['versions.json']
    assert ref['retested_on_current_rom'] is False
    assert info['integration_layers']==old['integration_layers']+[SCOPE] and len(info['integration_layers'])==167
    assert info['historical_validation']==old['historical_validation']
    assert info['previous_validation']==old['previous_validation']
    assert info['full_campaign_playthrough'] is info['previous_features_retested_on_current_rom'] is False
    references={}
    for key,name in [('previous_review_validation','review.json'),('previous_review_save_validation','test.sav')]:
        row=info[key];path=ROOT/row['file']
        assert digest(path)==row['sha256']==contract.BASELINE_SHA256[name]
        baseline(name,path.read_bytes());references[name]=path
    test=verify_review(ROOT/'roms/rom-de-teste',directory/'Pokemon-Journey-Gen1-9-Normal.gba')
    expected={'common':info['parent_rom_sha256'],'test':test['sha256'],
              **{r['file']:r['sha256'] for r in info['variants']}}
    covered=set();reports=[]
    for proof in info['proofs']:
        key=proof['target'],proof['kind']
        assert key not in covered and key in required_keys(info)
        covered.add(key);relative=Path(proof['file'])
        assert not relative.is_absolute() and '..' not in relative.parts
        file=directory/relative;report_dependencies(file,expected_sha=proof['sha256'])
        report=json.loads(file.read_bytes())
        assert report['rom_sha256']==expected[proof['target']], ('Stale current proof',key)
        reports.append((proof['kind'],report))
        verify_proof(report,file.parent,proof['kind'],proof['target'],
                     ROOT/'roms/rom-de-teste/Pokemon-Journey-TESTE.sav',info,old)
    assert required_keys(info)==covered
    verify_elf_binding(reports)
    previous_review=json.loads(references['review.json'].read_bytes())
    assert info['historical_release']==dict(scope='coastal-ecology',
        parent_rom_sha256=old['parent_rom_sha256'],variants={r['file']:r['sha256'] for r in old['variants']},
        test_rom_sha256=previous_review['sha256'],proof_count=20,retested_on_current_rom=False)
    from verify_coastal_ecology_update import verify_update as verify_previous
    verify_previous(directory,old,historical_review=previous_review,historical_save=references['test.sav'])
    return info
