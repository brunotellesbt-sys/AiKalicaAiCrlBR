"""Save explicitly requested candidate ROMs in the PR without claiming release.

This checkpoint requires compiled bytes, matching five-edition cold boots and
the frozen source marker. It never sets a final validator/contract to PASS.
The separate final publication pipeline remains responsible for complete proof.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[2]


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


PARENT_MANIFEST='mods/hoenn/atlas-surf-layout-validation/baseline/versions.json'
PARENT_MANIFEST_SHA256='eca26adfcb0b15f9da78aadec1b8738f66288fcc58d4d727ee2ea2a6274e29ec'


def preserve_historical_references(info):
    """Keep old proof ownership explicit; never attach old proofs to new bytes."""
    assert info['candidate'] is True and info['validated'] is False
    assert info['final_release_validated'] is False
    assert info.get('proofs',[])==[], 'Candidate checkpoint must not masquerade as a sealed release'
    raw=(ROOT/PARENT_MANIFEST).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==PARENT_MANIFEST_SHA256
    previous=json.loads(raw)
    assert previous['validated'] is True and previous['validation_scope']=='generated-area-review'
    assert len(previous['integration_layers'])==171
    assert info['integration_layers']==previous['integration_layers']+['atlas-surf-layout']
    info['proofs']=[]
    info['historical_validation']=previous['historical_validation']
    info['previous_validation']=previous['previous_validation']
    info['previous_port_validation']=dict(manifest=PARENT_MANIFEST,
        manifest_sha256=PARENT_MANIFEST_SHA256,retested_on_current_rom=False)
    return info


def checkpoint(frozen_path,artifacts,cold_boot,*,battery=None,revision=None):
    frozen_path,artifacts,cold_boot=map(Path,(frozen_path,artifacts,cold_boot))
    frozen=json.loads(frozen_path.read_bytes());source=Path(frozen['source'])
    assert revision in (None,'rocks103-v6','neighbor-layouts-v7'),'Unknown candidate revision'
    proof=ROOT/'docs/design/atlas-surf-layout'
    if revision:proof=proof/revision
    assert not (proof/'candidate-cold-boot').exists(),'Keep prior candidate evidence intact'
    if revision:
        from verify_atlas_103_rocks_native import verify as verify_native_rocks
        from verify_atlas_surf_checkpoint import verify_rocks103_evidence
        assert frozen['migration_version']==(7 if revision=='neighbor-layouts-v7' else 6) and frozen['global_source_validation_passed'] is True
        assert verify_rocks103_evidence(ROOT)['native_ROM_validation_complete'] is True
        native_folder=ROOT/'docs/design/native-rock-fragments-review/native-v6'
        if revision=='neighbor-layouts-v7':
            from verify_neighbor_layout_camera import verify as verify_neighbor_camera,verify_reference
            verify_reference(ROOT,frozen)
            verify_neighbor_camera(frozen,ROOT/'docs/design/neighbor-layout-camera-review/native-v7')
            native_folder=ROOT/'docs/design/neighbor-layout-camera-review/rock-regression-v7'
        verify_native_rocks(frozen,native_folder)
    marker=source/'.journey-atlas-surf-layout'
    assert digest(marker)==frozen['marker_sha256']
    assert digest(source/'pokeemerald.gba')==frozen['rom_sha256']
    assert digest(source/'pokeemerald.elf')==frozen['elf_sha256']
    for path,sha in frozen['prepared_sha256'].items():assert digest(source/path)==sha,path
    reports={}
    for row in frozen['editions']:
        assert digest(row['rom'])==row['sha256']
        proof_folder=row['edition']
        if row['edition']=='TESTE' and battery is not None:
            proof_folder='TESTE-continued-after-save'
        report_path=cold_boot/proof_folder/'cold-boot.json'
        report=json.loads(report_path.read_bytes())
        assert report['passed'] and report['controllers_only'] and report['no_game_memory_writes']
        assert report['rom_sha256']==row['sha256']
        if row['edition']=='TESTE':
            assert report['bundled_save_continue_to_field']
            if battery is not None:assert report['bundled_save_sha256']==digest(battery)
        reports[row['edition']]={'report':(proof.relative_to(ROOT)/'candidate-cold-boot'/proof_folder/'cold-boot.json').as_posix(),
                                 'sha256':digest(report_path)}
    info=json.loads((artifacts/'versions.json').read_bytes())
    assert info['candidate'] and not info['validated']
    assert len(info['integration_layers'])==172 and info['integration_layers'][-1]=='atlas-surf-layout'
    review=json.loads((artifacts/'test/review.json').read_bytes())
    validate_artifacts(frozen,artifacts,info,review)
    info.update(candidate=True,validated=False,final_release_validated=False,
                validation_scope='atlas-surf-layout-candidate',native_cold_boot=reports,
                parent_elf_sha256=frozen['elf_sha256'],layer_marker_sha256=frozen['marker_sha256'],
                rom_used_bytes=frozen['rom_used_bytes'],rom_limit_bytes=frozen['rom_limit_bytes'],
                known_generated_water_components=frozen['known_generated_water_components'],
                user_requested_progress_checkpoint=True)
    preserve_historical_references(info)
    if revision:info['candidate_revision']=revision
    review.update(candidate=True,validated=False,final_release_validated=False,
                  validation_scope='atlas-surf-layout-candidate',cold_boot=reports['TESTE'])
    if battery is not None:
        first=json.loads((cold_boot/'TESTE-save-menu-v2/cold-boot.json').read_bytes())
        second=json.loads((cold_boot/'TESTE-continued-after-save/cold-boot.json').read_bytes())
        a,b=first['runs'][-1],second['runs'][-1]
        assert a['saved_after_continue_with_controllers'] and a['saved_battery_sha256']==digest(battery)
        for key in ('field_map','player_tile','player_surfing','player_elevation'):assert a[key]==b[key],key
        review['native_battery_roundtrip']=dict(continue_save_menu_continue=True,
            field_map=b['field_map'],player_tile=b['player_tile'],player_elevation=b['player_elevation'],
            player_surfing=b['player_surfing'],all_retired_save_positions_natively_proven=False)
    versions=ROOT/'mods/hoenn/versions';roms=ROOT/'roms';test=roms/'rom-de-teste'
    versions.mkdir(parents=True,exist_ok=True);test.mkdir(parents=True,exist_ok=True)
    def copy(before,after):
        pending=after.with_suffix(after.suffix+'.candidate-tmp');shutil.copyfile(before,pending)
        assert digest(pending)==digest(before);pending.replace(after)
    for row in info['variants']:
        for destination in (versions,roms):copy(artifacts/row['file'],destination/row['file'])
    copy(artifacts/'test'/review['file'],test/review['file'])
    if battery is not None:
        assert Path(battery).stat().st_size==131072
        copy(Path(battery),test/'Pokemon-Journey-TESTE.sav')
    review['bundled_save_sha256']=digest(test/'Pokemon-Journey-TESTE.sav')
    (versions/'versions.json').write_text(json.dumps(info,indent=2)+'\n')
    (test/'review.json').write_text(json.dumps(review,indent=2)+'\n')
    checksum=''.join(r['sha256']+'  '+r['file']+'\n' for r in info['variants'])
    (versions/'SHA256SUMS').write_text(checksum);(roms/'SHA256SUMS').write_text(checksum)
    (test/'SHA256SUMS').write_text(review['sha256']+'  '+review['file']+'\n')
    proof.mkdir(parents=True,exist_ok=True);target=proof/'candidate-cold-boot'
    assert not target.exists(),'Keep prior candidate evidence intact'
    shutil.copytree(cold_boot,target)
    (proof/'candidate-compiled-freeze.json.gz').write_bytes(gzip.compress(frozen_path.read_bytes(),mtime=0))
    summary=dict(schema='atlas-requested-candidate-checkpoint/v1',compiled_roms_updated=True,
                 final_release_validated=False,global_gameplay_validation_complete=False,
                 source_raw_rom_sha256=frozen['rom_sha256'],elf_sha256=frozen['elf_sha256'],
                 marker_sha256=frozen['marker_sha256'],ROM_used_bytes=frozen['rom_used_bytes'],
                 variants=[dict(file=r['file'],sha256=r['sha256']) for r in info['variants']],
                 TESTE=dict(file='rom-de-teste/'+review['file'],sha256=review['sha256'],
                            battery_sha256=review['bundled_save_sha256']),cold_boot=reports,
                 pending_obligations=info['pending_obligations'],
                 previous_port_validation=info['previous_port_validation'])
    if revision:summary['candidate_revision']=revision
    (roms/'CANDIDATA-172.json').write_text(json.dumps(summary,indent=2)+'\n')
    archive=write_archive(versions,roms,test,ROOT/'docs/design/atlas-surf-layout',info)
    summary['archive_sha256']=digest(archive);summary['archive_bytes']=archive.stat().st_size
    # Archive checksum is external; its embedded manifest cannot hash itself.
    (ROOT/'docs/design/atlas-surf-layout/candidate-ROM-checkpoint.json').write_text(json.dumps(summary,indent=2)+'\n')
    return summary


def validate_artifacts(frozen,artifacts,info,review):
    frozen_files={Path(row['rom']).name:row['sha256'] for row in frozen['editions']}
    assert len(frozen_files)==5
    assert {r['file'] for r in info['variants']}==set(frozen_files)-{review['file']}
    for row in info['variants']:
        assert row['sha256']==frozen_files[row['file']]==digest(artifacts/row['file'])
    assert review['sha256']==frozen_files[review['file']]==digest(artifacts/'test'/review['file'])


def write_archive(versions,roms,test,proof,info):
    """Rebuild the checkpoint ZIP after continuity notes change, keeping ROM bytes."""
    from publish_badge_story import CONTINUITY_FILES
    archive=versions/'Pokemon-Journey-Four-Editions.zip';pending=archive.with_suffix('.zip.candidate-tmp')
    files={r['file']:versions/r['file'] for r in info['variants']}
    files.update({p:ROOT/p for p in CONTINUITY_FILES})
    for p in (ROOT/'Aqui').rglob('*'):
        if p.is_file():files[p.relative_to(ROOT).as_posix()]=p
    for name in ('errors/README.md','errors/2026-11-15-candidate-history-ci.txt'):
        files[name]=ROOT/name
    baseline=ROOT/PARENT_MANIFEST
    for p in baseline.parent.iterdir():
        if p.is_file():files[p.relative_to(ROOT).as_posix()]=p
    for p in proof.rglob('*'):
        if p.is_file() and p.name!='candidate-ROM-checkpoint.json':
            files[p.relative_to(ROOT).as_posix()]=p
    for p in [roms/'README.md',roms/'CANDIDATA-172.json',test/'LEIA-ME.md',test/'review.json',test/'SHA256SUMS',test/'Pokemon-Journey-TESTE.sav']:
        files[p.relative_to(ROOT).as_posix()]=p
    files['versions.json']=versions/'versions.json';files['SHA256SUMS']=versions/'SHA256SUMS'
    with zipfile.ZipFile(pending,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as bundle:
        for name,path in sorted(files.items()):bundle.write(path,name)
        review=json.loads((test/'review.json').read_bytes())
        bundle.writestr('TESTE-DOWNLOAD.md',
            '# TESTE da candidata172\n\n'
            'https://github.com/brunotellesbt-sys/AiKalicaAiCrlBR/raw/refs/heads/fix/atlas-continuity-2026-11-16/roms/rom-de-teste/Pokemon-Journey-TESTE.gba\n\n'
            'SHA-256: '+review['sha256']+'\n\n'
            'O save e os metadados acompanham este ZIP. Validacao global pendente.\n')
        bundle.writestr('CANDIDATA-EM-VALIDACAO.txt',
            'As quatro ROMs deste ZIP e a TESTE separada foram recompiladas com a camada172.\n'
            'Este e um checkpoint solicitado pelo usuario. Boot real passou; validacao global ainda pendente.\n'
            'Consulte roms/CANDIDATA-172.json e docs/CONTINUIDADE-TECNICA-IA.md antes de continuar o desenvolvimento.\n')
    assert pending.stat().st_size<100*1024*1024,'Candidate archive exceeds GitHub single-file limit'
    with zipfile.ZipFile(pending) as bundle:assert bundle.testzip() is None
    pending.replace(archive)
    return archive


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frozen',type=Path,required=True);parser.add_argument('--artifacts',type=Path,required=True)
    parser.add_argument('--cold-boot',type=Path,required=True);parser.add_argument('--battery',type=Path)
    parser.add_argument('--revision',choices=['rocks103-v6','neighbor-layouts-v7'])
    a=parser.parse_args();r=checkpoint(a.frozen,a.artifacts,a.cold_boot,battery=a.battery,revision=a.revision)
    print(json.dumps(dict(ROMs=5,archive_bytes=r['archive_bytes'],final_release_validated=False),indent=2))
