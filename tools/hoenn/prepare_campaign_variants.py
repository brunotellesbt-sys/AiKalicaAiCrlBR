"""Version limits, important opponents and usable evolution methods."""
import argparse,hashlib,json,re
from pathlib import Path
from prepare_competitive_bosses import PRIOR,LAYER as PREVIOUS
LAYER='campaign-variants';PRIOR=PRIOR+[PREVIOUS];ROOT=Path(__file__).resolve().parents[2]
def prepare(source):
 source=Path(source);marker=source/('.journey-'+LAYER)
 if marker.exists():
  r=json.loads(marker.read_text())
  for p,h in r['prepared_sha256'].items():assert hashlib.sha256((source/p).read_bytes()).hexdigest()==h,p
  return r
 expected=dict(json.loads((source/'.source-acquired.json').read_text())['sha256'])
 for layer in PRIOR:expected.update(json.loads((source/('.journey-'+layer)).read_text())['prepared_sha256'])
 outputs={};originals={}
 def stage(p,text):
  old=(source/p).read_bytes() if (source/p).exists() else None;h=hashlib.sha256(old).hexdigest() if old else None
  assert h==expected.get(p),p
  if h:originals[p]=h
  outputs[p]=text.encode()
 stage('include/journey_version.h','#ifndef GUARD_JOURNEY_VERSION_H\n#define GUARD_JOURNEY_VERSION_H\nstruct JourneyBuildRules {u16 maxNational; bool8 perfectIvs; u8 reserved;};\nextern const struct JourneyBuildRules gJourneyBuildRules;\nbool32 JourneySpeciesAllowed(u32);\nbool32 JourneyPerfectTrainerIvs(void);\n#endif\n')
 stage('src/journey_version.c',(ROOT/'tools/hoenn/journey_version.c').read_text())
 stage('src/journey_version_data.c','#include "global.h"\n#include "journey_version.h"\nconst struct JourneyBuildRules gJourneyBuildRules={1025,TRUE,0};\n')
 p='src/journey_competitive.c';t=(source/p).read_text().replace('#include "global.h"','#include "global.h"\n#include "journey_version.h"',1).replace('    mon->iv=0x3FFFFFFF;','    if(JourneyPerfectTrainerIvs())mon->iv=0x3FFFFFFF;');stage(p,t)
 # Convert every trade entry in the authoritative species tables. Hold items
 # survive as conditions; trade-partner requirements cannot block solo play.
 changes=[]
 for file in sorted((source/'src/data/pokemon/species_info').glob('*.h')):
  text=file.read_text();old=text;cursor=0
  while True:
   m=re.search(r'\{EVO_TRADE,\s*\w+,\s*(SPECIES_\w+)',text[cursor:])
   if not m:break
   start=cursor+m.start();end=start;depth=0
   for end in range(start,len(text)):
    if text[end]=='{':depth+=1
    elif text[end]=='}':
     depth-=1
     if depth==0:break
   entry=text[start:end+1];species=m[1];item=re.search(r'IF_HOLD_ITEM,\s*(ITEM_\w+)',entry)
   level=30 if item else 36
   new='{EVO_LEVEL, '+str(level)+', '+species+(', CONDITIONS({IF_HOLD_ITEM, '+item[1]+'})' if item else '')+'}'
   changes.append(dict(target=species,method='level+held_item' if item else 'level',level=level,item=item[1] if item else None,original=entry))
   text=text[:start]+new+text[end+1:];cursor=start+len(new)
  if text!=old:stage(str(file.relative_to(source)),text)
 r=dict(layer=LAYER,versions=[dict(name='Gen1-4 Normal',max_national=493,perfect_ivs=False),dict(name='Gen1-4 Hard',max_national=493,perfect_ivs=True),dict(name='Gen1-9 Normal',max_national=1025,perfect_ivs=False),dict(name='Gen1-9 Hard',max_national=1025,perfect_ivs=True)],trade_evolutions=changes,original_sha256=originals,prepared_sha256={p:hashlib.sha256(raw).hexdigest() for p,raw in outputs.items()})
 for p,raw in outputs.items():(source/p).write_bytes(raw)
 marker.write_text(json.dumps(r,indent=2)+'\n');return r
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);a=p.parse_args();print(json.dumps(prepare(a.source),indent=2))
