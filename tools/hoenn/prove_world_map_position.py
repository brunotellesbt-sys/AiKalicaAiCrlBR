"""Replay the position-only layer against its unchanged prior-layer inputs."""
import argparse,hashlib,json,re,tempfile
from pathlib import Path
from prepare_world_map_position import prepare,PRIOR,CORRECTIONS
ROOT=Path(__file__).resolve().parents[2]
def prove(source,output):
 source=Path(source);current=json.loads((source/'.journey-world-map-position').read_text())
 with tempfile.TemporaryDirectory() as temporary:
  base=Path(temporary)
  for folder in ['src/data','include']:(base/folder).mkdir(parents=True)
  # Input map/layout trees are read-only. Only the layer's own files are copied.
  (base/'data').symlink_to(source.resolve()/'data',target_is_directory=True)
  for name in ['.source-acquired.json']+['.journey-'+p for p in PRIOR]:(base/name).symlink_to(source.resolve()/name)
  (base/'src/journey_world_map.c').write_bytes((ROOT/'tools/hoenn/world_map_screen.c').read_bytes())
  header=(source/'include/journey_world_map.h').read_text().replace('u16 JourneyWorldMapPosition(void);\n','')
  (base/'include/journey_world_map.h').write_text(header)
  header=(source/'src/data/journey_world_map.h').read_text()
  points={p['map']:p for p in json.loads((source/'.journey-coastal-world-map').read_text())['points']}
  for n in CORRECTIONS:
   p=points[n];header,count=re.subn(r'(\{\(MAP_GROUP\('+p['id']+r'\).*?, MAPSEC_\w+, )\d+, \d+,',lambda m:m[1]+f"{p['x']}, {p['y']},",header);assert count==1
  (base/'src/data/journey_world_map.h').write_text(header)
  reproduced=json.loads(json.dumps(prepare(base)))
  assert reproduced==current,'Position layer did not reproduce from its original inputs'
  assert prepare(base)==reproduced,'Position layer is not repeatable'
 report=dict(passed=True,original_input_hashes_checked=True,byte_identical_prepared_files=current['prepared_sha256'],atlas_arrays_unchanged=current['atlas_arrays_sha256'],idempotent=True)
 output=Path(output);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2)+'\n')
 print('Position layer reproduced byte-for-byte; approved atlas preserved')
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();prove(a.source,a.output)
