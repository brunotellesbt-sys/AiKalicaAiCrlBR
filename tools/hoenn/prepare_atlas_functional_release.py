"""Build a reviewable final contract and preflight every current obligation.

Publication remains a separate action. This only writes staged manifests and
the exported evidence wrappers after all native runs have finished.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import shutil

from verify_atlas_functional_release import ROOT,load,sha,verify_native,verify_inspection_save
from export_atlas_functional_evidence import write


def prepare(evidence,artifacts,output):
    evidence,artifacts,output=(Path(p).resolve() for p in (evidence,artifacts,output))
    output.mkdir(parents=True,exist_ok=True)
    frozen=load(evidence/'freeze.json.gz')
    def path(name):
        p=evidence/name
        if not p.exists():p=p.with_suffix('.json.gz')
        assert p.is_file(),('Missing current proof',name)
        return p.relative_to(evidence).as_posix()
    native={
        'chambers':[path('chambers/legendary-chambers-native.json')],
        'exteriors':[path('exteriors/large-cave-exteriors-native.json')],
        'rocks':[path('rocks103/rocks103-native.json')],
        'trainers':[path('trainers/surf-trainers-native.json')],
        'coasts':[path('coasts/coast-faces-native.json')],
        'dives':[path('dives/dives-native.json')],
        'legacy':[path('legacy/large-cave-native-save-migrations.json')],
        'neighbor':[path('neighbor/neighbor-camera-native.json')],
        'captures':[path('captures/legendary-captures-native.json')],
        'captain':[path('captain/captain-native.json')],
        'three-port':[path('three-port/three-native.json')],
        'seven-ports':[path('seven-ports/seven-current-ports-native.json')],
        'land':[path('land-habitats-complete/land-habitats-native.json')]}
    profiles={r['file']:r['sha256'] for r in frozen['release']['variants']};profiles['test']=frozen['review']['sha256']
    editions={}
    for ed in frozen['editions']:
        target='test' if ed['edition']=='TESTE' else 'Pokemon-Journey-'+ed['edition']+'.gba'
        prefix='editions/'+ed['edition']+'/'
        editions[target]={
            'rules':path(prefix+'rules/edition-native-rules.json'),
            'trainer':path(prefix+'trainer/surf-trainers-native.json'),
            'cold':path(prefix+'trainer/cold-continue/cold-boot.json'),
            'wild':path(prefix+'water-wild/coastal-ecology-native-case.json')}
    inspection='editions/TESTE/inspection-save/'
    inspection_proofs={'migration':path(inspection+'first/cold-boot.json'),
                       'continue':path(inspection+'second/cold-boot.json')}
    test_battery=evidence/inspection/'Pokemon-Journey-TESTE.sav'
    verify_inspection_save(evidence,inspection_proofs,profiles['test'],sha(test_battery))
    shutil.copyfile(test_battery,artifacts/'test/Pokemon-Journey-TESTE.sav')
    source=path('compiled-source/atlas-surf-final-source.json')
    verify_native(evidence,dict(native=native,chamber_matrix='chambers/legendary-chambers-native-matrix.json',
        exterior_matrix='exteriors/large-cave-exteriors-native-matrix.json'),frozen,load(evidence/'metadata.json.gz'))
    write(evidence/'native-summary.json',dict(kind='atlas-functional-native',passed=True,
        rom_sha256=frozen['rom_sha256'],elf_sha256=frozen['elf_sha256'],marker_sha256=frozen['marker_sha256'],
        obligations=native,full_campaign_playthrough=False,all105_captures_claimed=False))
    files={p.relative_to(evidence).as_posix():sha(p) for p in evidence.rglob('*') if p.is_file() and p.name!='evidence-files.json'}
    write(evidence/'evidence-files.json',files)
    contract=dict(schema='atlas-functional-release/v1',finalized=True,
        evidence_root=evidence.relative_to(ROOT).as_posix(),index='evidence-files.json',index_sha256=sha(evidence/'evidence-files.json'),
        freeze='freeze.json.gz',metadata='metadata.json.gz',rom_sha256=frozen['rom_sha256'],
        elf_sha256=frozen['elf_sha256'],marker_sha256=frozen['marker_sha256'],prepared_sha256=frozen['prepared_sha256'],
        source=source,family_comparison=path('ecology/family-comparison.json'),native=native,
        chamber_matrix='chambers/legendary-chambers-native-matrix.json',
        exterior_matrix='exteriors/large-cave-exteriors-native-matrix.json',profiles=profiles,editions=editions,
        test_save_sha256=sha(test_battery),inspection_save_proofs=inspection_proofs,
        scope='atlas-surf-layout',full_campaign_playthrough=False)
    contract_file=output/'final-contract.json';write(contract_file,contract)
    # Carry historical references exactly; they continue pointing to 171.
    current=load(ROOT/'mods/hoenn/versions/versions.json')
    previous_root=ROOT/'mods/hoenn/atlas-surf-layout-validation/baseline'
    old=load(previous_root/'versions.json')
    from verify_generated_area_review_update import verify_update as verify_previous
    verify_previous(ROOT/'mods/hoenn/versions',old,historical_review=load(previous_root/'review.json'),
                    historical_save=previous_root/'test.sav')
    info=deepcopy(frozen['release'])
    for name in ('historical_validation','previous_validation'):
        info[name]=deepcopy(old[name])
    info['previous_port_validation']=deepcopy(current['previous_port_validation'])
    for key,name in [('previous_review_validation','review.json'),('previous_review_save_validation','test.sav')]:
        info[key]=dict(file=(previous_root/name).relative_to(ROOT).as_posix(),sha256=sha(previous_root/name))
    info.update(validation_scope='atlas-surf-layout',candidate=False,validated=True,final_release_validated=True,
        full_campaign_playthrough=False,previous_features_retested_on_current_rom=False,proofs=[],
        functional_contract_sha256=sha(contract_file))
    # Public proof paths live below versions/evidence. The same source tree
    # is exported there for a final preflight before any ROM is replaced.
    relative=Path('evidence/atlas-surf-layout')
    for target,kind,name in [('common','atlas-functional-source',source),('common','atlas-functional-native','native-summary.json')]:
        info['proofs'].append(dict(target=target,kind=kind,file=(relative/name).as_posix(),sha256=sha(evidence/name)))
    for target,paths in editions.items():
        for key,kind in [('rules','edition-native-rules'),('trainer','atlas-surf-trainers-native')]:
            info['proofs'].append(dict(target=target,kind=kind,file=(relative/paths[key]).as_posix(),sha256=sha(evidence/paths[key])))
    write(output/'versions.json',info)
    return info,contract_file


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('evidence','artifacts','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();prepare(a.evidence,a.artifacts,a.output)
