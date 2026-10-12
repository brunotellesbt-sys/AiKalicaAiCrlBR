"""Validate the whole ancestral chain and remove instant trade-item bypasses."""
import argparse,hashlib,json,re
from pathlib import Path
from prepare_trainer_level_coherence import PRIOR,LAYER as PREVIOUS
LAYER='evolution-coherence';PRIOR=PRIOR+[PREVIOUS]
CHAIN='''    // A stone evolution can still have a level-gated ancestor (e.g.
    // Ludicolo -> Lombre -> Lotad). Inspect the full chain before choosing.
    u16 child=species, eligible=species;
    for(pass=0;pass<8;pass++)
    {
        u16 previous=GetSpeciesPreEvolution(child);
        const struct Evolution *e;
        u32 required=101;
        if(previous==SPECIES_NONE || previous==child)break;
        e=GetSpeciesEvolutions(previous);
        for(i=0;e[i].method!=EVOLUTIONS_END;i++)
            if(e[i].targetSpecies==child && e[i].method!=EVO_NONE)
            {
                u32 threshold=(e[i].method==EVO_LEVEL || e[i].method==EVO_LEVEL_BATTLE_ONLY) ? max(2,e[i].param) : 1;
                if(threshold<required)required=threshold;
            }
        if(required>level && required<=100)eligible=previous;
        child=previous;
    }
    return eligible;
'''
def prepare(source):
 source=Path(source);marker=source/('.journey-'+LAYER)
 if marker.exists():
  r=json.loads(marker.read_text())
  for p,h in r['prepared_sha256'].items():assert hashlib.sha256((source/p).read_bytes()).hexdigest()==h,p
  return r
 expected=dict(json.loads((source/'.source-acquired.json').read_text())['sha256'])
 for layer in PRIOR:expected.update(json.loads((source/('.journey-'+layer)).read_text())['prepared_sha256'])
 outputs={};originals={}
 def stage(p,t):
  h=hashlib.sha256((source/p).read_bytes()).hexdigest();assert h==expected[p],p;originals[p]=h;outputs[p]=t.encode()
 p='src/journey_version.c';t=(source/p).read_text();start=t.index('    for(pass=0;pass<4;pass++)');end=t.index('    return species;\n}',start);stage(p,t[:start]+CHAIN+t[end+len('    return species;\n'):])
 p='src/journey_competitive.c';t=(source/p).read_text();start=t.index('static u16 RespectEvolutionLevel(');end=t.index('void JourneyPrepareCompetitiveMon(',start);t=t[:start]+'''static u16 RespectEvolutionLevel(u16 species,u32 level)
{
    return JourneyTrainerSpecies(species,level);
}
'''+t[end:];stage(p,t)
 targets={e['target'] for e in json.loads((source/'.journey-campaign-variants').read_text())['trade_evolutions']};removed=[]
 for file in sorted((source/'src/data/pokemon/species_info').glob('*.h')):
  text=file.read_text();original=text;cursor=0
  while True:
   m=re.search(r'\{EVO_ITEM,\s*\w+,\s*(SPECIES_\w+)',text[cursor:])
   if not m:break
   start=cursor+m.start();target=m[1];depth=0
   for end in range(start,len(text)):
    if text[end]=='{':depth+=1
    elif text[end]=='}':
     depth-=1
     if not depth:break
   if target not in targets:cursor=end+1;continue
   removed.append(dict(target=target,entry=text[start:end+1]))
   # Remove the following comma, or the preceding comma for a last entry.
   after=end+1
   while after<len(text) and text[after].isspace():after+=1
   if text[after:after+1]==',':text=text[:start]+text[after+1:]
   else:
    before=start-1
    while text[before].isspace():before-=1
    assert text[before]==',',target
    text=text[:before]+text[end+1:]
   cursor=max(0,start-2)
  if text!=original:stage(str(file.relative_to(source)),text)
 r=dict(layer=LAYER,full_ancestral_evolution_levels=True,trade_item_requires_level_and_held_item=True,trade_requires_level=True,removed_instant_trade_bypasses=removed,original_sha256=originals,prepared_sha256={p:hashlib.sha256(raw).hexdigest() for p,raw in outputs.items()})
 for p,raw in outputs.items():(source/p).write_bytes(raw)
 marker.write_text(json.dumps(r,indent=2)+'\n');return r
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);a=p.parse_args();print(json.dumps(prepare(a.source),indent=2))
