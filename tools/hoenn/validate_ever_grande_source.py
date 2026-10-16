"""Replay the market overlay and verify unrelated 157-layer inputs stay intact."""
import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from prepare_ever_grande_market import prepare, PRIOR, LAYER

def validate(source, baseline, output):
    source,baseline,output=map(Path,[source,baseline,output])
    report=json.loads((source/('.journey-'+LAYER)).read_text())
    expected=dict(json.loads((baseline/'.source-acquired.json').read_text())['sha256'])
    for name in PRIOR:
        expected.update(json.loads((baseline/('.journey-'+name)).read_text())['prepared_sha256'])
    outputs=report['prepared_sha256']
    for name,digest in (expected|outputs).items():
        assert hashlib.sha256((source/name).read_bytes()).hexdigest()==digest,name
    with tempfile.TemporaryDirectory(prefix='ever-replay-',dir='/tmp') as directory:
        replay=Path(directory)
        for name in expected:
            dest=replay/name;dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(baseline/name,dest)
        for name in ['.source-acquired.json',*['.journey-'+n for n in PRIOR]]:
            shutil.copyfile(baseline/name,replay/name)
        fresh=json.loads(json.dumps(prepare(replay)))
        assert fresh==report
        assert prepare(replay)==fresh
    city=json.loads((source/'data/maps/EverGrandeCity/map.json').read_text())
    old=json.loads((baseline/'data/maps/EverGrandeCity/map.json').read_text())
    assert city['warp_events'][:len(old['warp_events'])]==old['warp_events']
    assert city['connections']==old['connections'] and city['coord_events']==old['coord_events']
    assert all(not p.startswith(('data/maps/Route','data/layouts/Route','data/layouts/Journey')) for p in outputs)
    r=dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
        layers=PRIOR+[LAYER],independent_replay=True,idempotent=True,source_hashes_checked=len(expected|outputs),
        unrelated_files_preserved=len(expected.keys()-outputs.keys()),original_city_events_and_connections_preserved=True,
        all_surf_maps_unchanged=True,houses=report['houses'],stall=report['stall'],city_pixels=report['city_pixels'])
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(r,indent=2)+'\n')
    return r

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--baseline',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();validate(a.source,a.baseline,a.output)
