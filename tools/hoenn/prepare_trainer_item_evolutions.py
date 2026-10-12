"""Require levels 30–40 for NPC item evolutions; keep player stones unchanged."""
import argparse,hashlib,json
from pathlib import Path
from prepare_galactic_chapter import PRIOR,LAYER as PREVIOUS
LAYER='trainer-item-evolutions';PRIOR=PRIOR+[PREVIOUS]
def prepare(source):
 source=Path(source);marker=source/('.journey-'+LAYER)
 if marker.exists():
  r=json.loads(marker.read_text())
  for p,h in r['prepared_sha256'].items():assert hashlib.sha256((source/p).read_bytes()).hexdigest()==h,p
  return r
 expected=dict(json.loads((source/'.source-acquired.json').read_text())['sha256'])
 for layer in PRIOR:expected.update(json.loads((source/('.journey-'+layer)).read_text())['prepared_sha256'])
 p='src/journey_version.c';old=(source/p).read_bytes();assert hashlib.sha256(old).hexdigest()==expected[p]
 text=old.decode();needle='                u32 threshold=(e[i].method==EVO_LEVEL || e[i].method==EVO_LEVEL_BATTLE_ONLY) ? max(2,e[i].param) : 1;';assert text.count(needle)==1
 text=text.replace(needle,needle+'''
                if(e[i].method==EVO_ITEM)
                {
                    const struct SpeciesInfo *form=&gSpeciesInfo[child];
                    u32 total=form->baseHP+form->baseAttack+form->baseDefense+form->baseSpeed+form->baseSpAttack+form->baseSpDefense;
                    threshold=total>=530?40:total>=500?35:30;
                }
''')
 (source/p).write_text(text);r=dict(layer=LAYER,npc_item_evolution_levels=[30,35,40],thresholds={'BST below 500':30,'BST 500–529':35,'BST 530+':40},full_ancestry_still_enforced=True,player_item_evolutions_unchanged=True,original_sha256={p:hashlib.sha256(old).hexdigest()},prepared_sha256={p:hashlib.sha256(text.encode()).hexdigest()});marker.write_text(json.dumps(r,indent=2)+'\n');return r
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);print(json.dumps(prepare(p.parse_args().source),indent=2))
