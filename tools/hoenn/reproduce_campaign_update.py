"""Reproduce coastal overlays against the independently reproduced PR79 source."""
import argparse,hashlib,importlib,json,os,shutil
from pathlib import Path
from prepare_offscreen_rival_entrances import PRIOR,LAYER
from package_playable import verify_source
import package_playable
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
layers=PRIOR+[LAYER];delta=layers[116:];expected={}
for n in layers:expected.update(json.loads((a.source/('.journey-'+n)).read_text())['prepared_sha256'])
affected=set()
for n in delta:affected.update(json.loads((a.source/('.journey-'+n)).read_text())['prepared_sha256'])
shutil.copytree(a.baseline,a.output,copy_function=os.link)
# Break links for every mutable input before any overlay writes it.
for n in affected:
 p=a.output/n
 if p.exists():raw=p.read_bytes();mode=p.stat().st_mode;p.unlink();p.write_bytes(raw);p.chmod(mode)
for n in delta:importlib.import_module('prepare_'+n.replace('-','_')).prepare(a.output)
differences=[n for n,h in expected.items() if hashlib.sha256((a.output/n).read_bytes()).hexdigest()!=h]
assert not differences,differences
r=dict(passed=True,layers=layers,baseline_layers=116,incremental_reproduction=True,new_layers_reproduced=delta,prepared_files_compared=len(expected),differences=differences)
(a.output/'.campaign-reproduction.json').write_text(json.dumps(r,indent=2)+'\n');print('Independent overlay reproduction:',len(delta),'new layers;',len(expected),'files')
