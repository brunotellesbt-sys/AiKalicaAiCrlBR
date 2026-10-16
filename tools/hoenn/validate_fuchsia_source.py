"""Replay only the Fuchsia overlay and prove other source/art stays unchanged."""
import argparse
import hashlib
import json
import tempfile
from pathlib import Path

from prepare_fuchsia_harbor import PRIOR,LAYER,prepare
from render_sea_maps import MapRenderer


def validate(source,inputs,output):
    source,inputs,output=Path(source).resolve(),Path(inputs).resolve(),Path(output)
    report=json.loads((source/('.journey-'+LAYER)).read_text())
    targets={Path(p) for p in report['prepared_sha256']}
    for p,h in report['original_sha256'].items():
        assert hashlib.sha256((inputs/p).read_bytes()).hexdigest()==h,p
    expected=dict(json.loads((source/'.source-acquired.json').read_text())['sha256'])
    for name in PRIOR:
        expected.update(json.loads((source/('.journey-'+name)).read_text())['prepared_sha256'])
    checked=0
    for p,h in expected.items():
        if Path(p) not in targets:
            assert hashlib.sha256((source/p).read_bytes()).hexdigest()==h,p
            checked+=1
    allowed={'data/layouts/Route19_Frlg/map.bin','data/maps/Route19_Frlg/map.json',
        'data/maps/JourneyRoute19PortLodge/map.json','data/layouts/layouts.json',
        'data/maps/map_groups.json','data/event_scripts.s','data/scripts/journey_campaign_gates.inc'}
    assert all(p in allowed or p.startswith(('data/tilesets/secondary/fuchsia_city_frlg/','data/tilesets/secondary/fuchsia_city/','data/maps/JourneyFuchsiaHarbor/','data/layouts/JourneyFuchsiaHarbor/')) for p in report['prepared_sha256'])
    existing=json.loads((inputs/'data/maps/Route19_Frlg/map.json').read_text())
    final=json.loads((source/'data/maps/Route19_Frlg/map.json').read_text())
    assert existing['connections']==final['connections']
    trainers=[o for o in existing['object_events'] if o['trainer_type']!='TRAINER_TYPE_NONE']
    assert all(o in final['object_events'] for o in trainers)
    # Existing metatiles/attributes remain byte-identical; new ones append.
    for name in report['original_sha256']:
        if name.endswith(('/metatiles.bin','/metatile_attributes.bin')):
            assert (source/name).read_bytes().startswith((inputs/name).read_bytes())
    with tempfile.TemporaryDirectory(prefix='fuchsia-replay-',dir=source.parent) as directory:
        dest=Path(directory)
        def clone(relative):
            origin=source/relative;copy=dest/relative
            if str(relative)=='.journey-fuchsia-harbor':return
            if relative in targets:
                if str(relative) in report['original_sha256']:copy.write_bytes((inputs/relative).read_bytes())
                return
            if any(relative in target.parents for target in targets):
                copy.mkdir(exist_ok=True)
                for child in origin.iterdir():clone(child.relative_to(source))
            else:copy.symlink_to(origin,target_is_directory=origin.is_dir())
        for child in source.iterdir():clone(child.relative_to(source))
        before=MapRenderer(dest);after=MapRenderer(source)
        city_maps=[]
        route=json.loads((source/'data/maps/Route19_Frlg/map.json').read_text())
        secondary=after.layouts[route['layout']]['secondary_tileset']
        for p in (source/'data/maps').glob('*/map.json'):
            m=json.loads(p.read_text())
            if p.parent.name!='Route19_Frlg' and after.layouts[m['layout']]['secondary_tileset']==secondary:
                a,_=before.render(p.parent.name,npcs=False);b,_=after.render(p.parent.name,npcs=False)
                assert a.tobytes()==b.tobytes(),p.parent.name
                city_maps.append(p.parent.name)
        result=prepare(dest)
        assert result==report
        assert prepare(dest)==result
    proof=dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
        layers=PRIOR+[LAYER],original_inputs_verified=True,idempotent=True,differences=[],
        reproduced_layers=[LAYER],byte_identical_outputs=sorted(report['prepared_sha256']),
        unrelated_source_inputs_checked=checked,atlas_unchanged=True,other_ports_unchanged=True,
        existing_trainers_preserved=True,secondary_existing_metatiles_preserved=True,
        other_fuchsia_maps_pixel_identical=True,compared_maps=city_maps)
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(proof,indent=2)+'\n')
    print('Fuchsia replay passed;',checked,'unrelated source files preserved;',city_maps,'pixel-identical')
    return proof


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--original-inputs',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();validate(a.source,a.original_inputs,a.output)
