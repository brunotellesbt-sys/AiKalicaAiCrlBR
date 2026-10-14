"""Publish four ROMs with fresh coastal evidence and an explicit old PWT baseline."""
import argparse,hashlib,json,shutil,zipfile
from pathlib import Path
from package_versions import package,ROOT
from verify_versions import verify
from published_evidence import baseline

def publish(source,validation,output):
 source=Path(source);validation=Path(validation);output=Path(output);info=package(source,output)
 info.update(validation_scope='campaign-coastal-update',full_campaign_playthrough=False,special_encounters_validated=True,proofs=[])
 baseline_dir,old,_=baseline();info['historical_validation']=dict(manifest=str((baseline_dir/'versions.json').relative_to(ROOT)),manifest_sha256=hashlib.sha256((baseline_dir/'versions.json').read_bytes()).hexdigest(),parent_rom_sha256=old['parent_rom_sha256'],compressed_parent_sha256=hashlib.sha256((baseline_dir/'parent.gba.gz').read_bytes()).hexdigest(),retested_on_current_rom=False,source='PR79',notes='Earlier PWT/mechanics runs remain bound to their original ROM bytes; no tournaments repeated for this coastal update.')
 # Only packager-owned old evidence is replaced; archive was verified first.
 if (output/'evidence').exists():shutil.rmtree(output/'evidence')
 def add(path,target,kind):
  relative=Path('evidence')/target.removesuffix('.gba')/(kind+'.json');dest=output/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest);info['proofs'].append(dict(file=relative.as_posix(),target=target,kind=kind,sha256=hashlib.sha256(dest.read_bytes()).hexdigest()))
 for path in sorted((validation/'common').rglob('*.json')):
  r=json.loads(path.read_text())
  if r.get('passed'):add(path,'common',path.stem)
 for row in info['variants']:
  edition=row['file'].removeprefix('Pokemon-Journey-').removesuffix('.gba')
  for kind in ['gym-teams','special-encounters']:add(validation/edition/(kind+'.json'),row['file'],kind)
 (output/'versions.json').write_text(json.dumps(info,indent=2)+'\n');verify(output,require_seal=False);info['validated']=True;(output/'versions.json').write_text(json.dumps(info,indent=2)+'\n');verify(output)
 archive=output/'Pokemon-Journey-Four-Editions.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for name in [r['file'] for r in info['variants']]+['versions.json','SHA256SUMS']:z.write(output/name,name)
  z.writestr('START-HERE.md',(output/'START-HERE.md').read_text().replace('../../../docs/','docs/').replace('../INTEGRATION-STATUS.md','docs/VALIDATION.md'))
  for p in info['proofs']:z.write(output/p['file'],p['file'])
  for p in sorted((ROOT/'docs').rglob('*')):
   if p.is_file():z.write(p,'docs/'+p.relative_to(ROOT/'docs').as_posix())
  z.write(ROOT/'mods/hoenn/INTEGRATION-STATUS.md','docs/VALIDATION.md')
 return archive
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--validation',required=True);p.add_argument('--output',required=True);a=p.parse_args();print(publish(a.source,a.validation,a.output))
