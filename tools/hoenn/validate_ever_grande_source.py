"""Replay the market overlay and preserve the Surf and Dewford release inputs."""
import argparse
import hashlib
import json
import re
import shutil
import tempfile
from pathlib import Path
from candidate_layer import Layer
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
        for p in baseline.iterdir():
            (replay/p.name).symlink_to(p.resolve(),target_is_directory=p.is_dir())
        def materialize(folder):
            if folder==replay:return
            materialize(folder.parent)
            if folder.is_symlink():
                target=folder.resolve();folder.unlink();folder.mkdir()
                for p in target.iterdir():(folder/p.name).symlink_to(p,target_is_directory=p.is_dir())
        # Copy the writable outputs and only read the remaining linked inputs.
        # This keeps an independent replay practical on inode-limited CI.
        for name in outputs:
            dest=replay/name;materialize(dest.parent);dest.unlink(missing_ok=True)
            if name in expected:shutil.copyfile(baseline/name,dest)
        finish=Layer.finish
        def isolated_finish(layer,**metadata):
            # Also isolate any newly introduced output before Layer writes it.
            for name in layer.outputs:
                dest=replay/name;materialize(dest.parent)
                if dest.is_symlink():
                    raw=dest.read_bytes();dest.unlink();dest.write_bytes(raw)
            return finish(layer,**metadata)
        Layer.finish=isolated_finish
        try:
            fresh=json.loads(json.dumps(prepare(replay)))
            assert fresh==report
            assert prepare(replay)==fresh
        finally:Layer.finish=finish
    city=json.loads((source/'data/maps/EverGrandeCity/map.json').read_text())
    old=json.loads((baseline/'data/maps/EverGrandeCity/map.json').read_text())
    assert city['warp_events'][:len(old['warp_events'])]==old['warp_events']
    assert city['connections']==old['connections'] and city['coord_events']==old['coord_events']
    river=report['fallarbor_river']
    changed_routes={p for p in outputs if p.startswith(('data/maps/Route','data/layouts/Route','data/layouts/Journey'))}
    assert changed_routes==set(river['source_paths'])
    for name in ['JourneyWestRiver','Route114','FallarborTown']:
        p=f'data/maps/{name}/map.json'
        assert (source/p).read_bytes()==(baseline/p).read_bytes()
    assert river['beach_elevation']==3 and river['whole_native_trees_restored']
    assert river['all_events_connections_and_city_buildings_preserved']
    dewford=json.loads((baseline/'.journey-dewford-competitive-shop').read_text())
    for name in dewford['prepared_sha256']:
        if name in outputs:
            if name=='src/data/journey_world_map.h':
                from prepare_world_dex_map import PAT
                assert re.findall(PAT,(source/name).read_text())==re.findall(PAT,(baseline/name).read_text())
            else:
                assert name in ['include/constants/flags.h','data/event_scripts.s']
                assert (source/name).read_bytes().startswith((baseline/name).read_bytes())
    caves=dewford['legendary_caves'];market=dewford['frontier_market']
    assert caves['total']==105 and caves['cave_count']==48 and market['seller_count']==1
    assert {h['flag_id'] for h in report['houses']}.isdisjoint({dewford['item']['flag'],dewford['tm']['flag']})
    r=dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
        layers=PRIOR+[LAYER],independent_replay=True,idempotent=True,source_hashes_checked=len(expected|outputs),
        unrelated_files_preserved=len(expected.keys()-outputs.keys()),original_city_events_and_connections_preserved=True,
        unrelated_surf_maps_unchanged=True,fallarbor_river=river,
        dewford_and_origin_features_preserved=True,houses=report['houses'],stall=report['stall'],city_pixels=report['city_pixels'])
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(r,indent=2)+'\n')
    return r

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--baseline',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();validate(a.source,a.baseline,a.output)
