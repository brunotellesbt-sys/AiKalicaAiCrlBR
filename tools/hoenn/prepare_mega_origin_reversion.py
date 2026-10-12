"""Restore Mega Floette to Eternal Flower after battle or fainting."""
import argparse,hashlib,json
from pathlib import Path
from prepare_galactic_continuity import PRIOR,LAYER as PREVIOUS
LAYER='mega-origin-reversion';PRIOR=PRIOR+[PREVIOUS]
def prepare(source):
 source=Path(source);marker=source/('.journey-'+LAYER)
 if marker.exists():
  r=json.loads(marker.read_text())
  for p,h in r['prepared_sha256'].items():assert hashlib.sha256((source/p).read_bytes()).hexdigest()==h,p
  return r
 expected=dict(json.loads((source/'.source-acquired.json').read_text())['sha256'])
 for layer in PRIOR:expected.update(json.loads((source/('.journey-'+layer)).read_text())['prepared_sha256'])
 p='src/data/pokemon/form_change_tables.h';raw=(source/p).read_bytes();assert hashlib.sha256(raw).hexdigest()==expected[p]
 t=raw.decode();a=t.index('static const struct FormChange sFloetteEternalFormChangeTable[]');b=t.index('};',a);part=t[a:b];assert part.count('SPECIES_FLOETTE}')==2;part=part.replace('SPECIES_FLOETTE}','SPECIES_FLOETTE_ETERNAL}');t=t[:a]+part+t[b:];(source/p).write_text(t)
 r=dict(layer=LAYER,mega_floette_returns_to_eternal_flower=True,faint_and_battle_end_fixed=True,original_sha256={p:hashlib.sha256(raw).hexdigest()},prepared_sha256={p:hashlib.sha256(t.encode()).hexdigest()});marker.write_text(json.dumps(r,indent=2)+'\n');return r
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);print(json.dumps(prepare(p.parse_args().source),indent=2))
