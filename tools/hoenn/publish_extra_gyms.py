"""Publish five current ROMs with native evidence and immutable prior history."""
import argparse,hashlib,json,shutil,zipfile
from pathlib import Path
from package_versions import ROOT,package
from package_review_rom import package as package_review
from verify_versions import verify
from verify_fuchsia_update import previous_release

def publish(source,validation,output):
    source,validation,output=map(Path,[source,validation,output])
    raw=(validation/'baseline/versions.json').read_bytes();old=json.loads(raw)
    info=package(source,output)
    package_review(source,output/'Pokemon-Journey-Gen1-9-Normal.gba',ROOT/'roms/rom-de-teste')
    info.update(validation_scope='extra-gyms',validated=False,full_campaign_playthrough=False,proofs=[],
        historical_validation=old['historical_validation'],previous_validation=old['previous_validation'],
        previous_port_validation=dict(manifest=(validation/'baseline/versions.json').relative_to(ROOT).as_posix(),manifest_sha256=hashlib.sha256(raw).hexdigest(),retested_on_current_rom=False),
        previous_review_validation=dict(file=(validation/'baseline/review.json').relative_to(ROOT).as_posix(),sha256=hashlib.sha256((validation/'baseline/review.json').read_bytes()).hexdigest()))
    def add(file,target,kind):
        rel=Path('evidence/extra-gyms')/target.removesuffix('.gba')/(kind+'.json');dest=output/rel
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(file,dest)
        info['proofs'].append(dict(file=rel.as_posix(),target=target,kind=kind,sha256=hashlib.sha256(dest.read_bytes()).hexdigest()))
    add(validation/'source.json','common','extra-gym-source')
    add(validation/'all-surf/all-surf-links.json','common','all-surf-links')
    for kind in ['surf-repairs','coastal-details','marine-network','luffy-approach','coastal-landings','map-finishing']:add(validation/'native'/(kind+'.json'),'common',kind)
    for target,folder in [(r['file'],r['file'].removeprefix('Pokemon-Journey-').removesuffix('.gba')) for r in info['variants']]+[('test','TESTE')]:
        for kind in ['extra-gyms','review-mode','ever-grande-market','dewford-competitive-shop','fallarbor-physics']:add(validation/folder/(kind+'.json'),target,kind)
    (output/'versions.json').write_text(json.dumps(info,indent=2)+'\n');verify(output,require_seal=False)
    info['validated']=True;(output/'versions.json').write_text(json.dumps(info,indent=2)+'\n');verify(output)
    # Keep all immutable evidence JSON, current screenshots and the requested
    # current videos. Old videos are available in the pinned baseline folder
    # and Git history; avoid duplicating every legacy movie in this download.
    with zipfile.ZipFile(output/'Pokemon-Journey-Four-Editions.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name in [r['file'] for r in info['variants']]+['versions.json','SHA256SUMS','START-HERE.md']:z.write(output/name,name)
        for p in (output/'evidence').rglob('*.json'):z.write(p,p.relative_to(output).as_posix())
        for name in ['AGENTS.md','.agents/skills/gba-map-review/SKILL.md']:
            z.write(ROOT/name,name)
        video=validation/'baseline/western-river-fallarbor.mp4'
        z.write(video,video.relative_to(ROOT).as_posix())
        for p in validation.rglob('*'):
            if p.is_file() and p.suffix in ['.json','.png']:z.write(p,p.relative_to(ROOT).as_posix())
        # Previous concept references stay in Git, rather than duplicating
        # them in the four-ROM download. Retain all current visual review art,
        # all native evidence and every immutable historical manifest.
        previous_references={p.relative_to(ROOT).as_posix() for p in (ROOT/'docs/design').glob('proposta*.png')}|{
            'docs/images/fallarbor/proposal.png','docs/images/island-harbors/Dewford-shore-reference.png','docs/images/harbor-concept-reference.png'}
        for p in (ROOT/'docs').rglob('*'):
            if p.is_file() and p.suffix!='.mp4' and p.relative_to(ROOT).as_posix() not in previous_references:z.write(p,p.relative_to(ROOT).as_posix())
        z.writestr('REFERENCE-IMAGES.md','# Earlier concept references\n\nThese earlier design references remain in the repository. Native captures and evidence are included in this download. Full-resolution concept references remain at the links below to keep this four-ROM archive below the GitHub file-size limit.\n\n'+''.join('- ['+name+'](https://github.com/brunotellesbt-sys/AiKalicaAiCrlBR/blob/main/'+name+')\n' for name in sorted(previous_references)))
        for name in ['surf-connections-repaired.mp4','western-river-fallarbor.mp4']:
            p=ROOT/'docs/videos'/name
            if p.exists():z.write(p,p.relative_to(ROOT).as_posix())
        archived=set(z.namelist());history=old
        while 'previous_port_validation' in history:
            name=history['previous_port_validation']['manifest']
            if name not in archived:z.write(ROOT/name,name);archived.add(name)
            history=previous_release(history)
    assert (output/'Pokemon-Journey-Four-Editions.zip').stat().st_size<100*1024*1024
    return info
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--validation',type=Path,default=ROOT/'mods/hoenn/extra-gyms-validation');p.add_argument('--output',type=Path,default=ROOT/'mods/hoenn/versions');a=p.parse_args();publish(a.source,a.validation,a.output)
