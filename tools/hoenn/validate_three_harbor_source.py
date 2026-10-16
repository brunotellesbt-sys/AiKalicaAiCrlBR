"""Replay the three terminal overlay and check all unrelated source and artwork."""
import argparse,hashlib,json,struct,tempfile
from pathlib import Path
from prepare_three_harbor_terminals import PRIOR,LAYER,prepare
from render_sea_maps import MapRenderer


def validate(source,inputs,output):
    source,inputs,output=Path(source).resolve(),Path(inputs).resolve(),Path(output)
    report=json.loads((source/('.journey-'+LAYER)).read_text());targets={Path(n) for n in report['prepared_sha256']}
    for n,h in report['original_sha256'].items():assert hashlib.sha256((inputs/n).read_bytes()).hexdigest()==h,n
    expected=dict(json.loads((source/'.source-acquired.json').read_text())['sha256'])
    for n in PRIOR:expected.update(json.loads((source/('.journey-'+n)).read_text())['prepared_sha256'])
    checked=0
    for n,h in expected.items():
        if Path(n) not in targets:
            assert hashlib.sha256((source/n).read_bytes()).hexdigest()==h,n
            checked+=1
    exteriors={p['exterior'] for p in report['ports']}; interiors={p['interior'] for p in report['ports']}
    allowed={'data/layouts/layouts.json','data/maps/map_groups.json','data/event_scripts.s','data/scripts/journey_campaign_gates.inc','data/maps/JourneyCinnabarSailorsLodge/map.json'}
    for n in report['prepared_sha256']:
        assert n in allowed or any(n.startswith(f'data/maps/{m}/') or n.startswith(f'data/layouts/{m}/') for m in exteriors|interiors) or n.startswith(('data/tilesets/secondary/rustboro/','data/tilesets/secondary/cerulean_city_frlg/','data/tilesets/secondary/cerulean_city/','data/tilesets/secondary/cinnabar_island_frlg/','data/tilesets/secondary/cinnabar_island/')),n
    for p in report['ports']:
        n=p['exterior'];old=json.loads((inputs/f'data/maps/{n}/map.json').read_text());new=json.loads((source/f'data/maps/{n}/map.json').read_text())
        assert old['connections']==new['connections']
        for o in old['object_events']:
            if o['script'] in ('JourneyCompactPort_Boat','Journey_FerryPort'+str(p['pid'])):continue
            expected_o=dict(o)
            if o['script']=='Route104_EventScript_Rival':expected_o.update(x=16,y=50)
            assert expected_o in new['object_events'],(n,o['script'])
        expected_boxes={19:[4,11,7,4],21:[61,6,7,4],12:[13,47,7,4]}
        assert p['terminal']==expected_boxes[p['pid']]
        if p['pid']==12:
            assert p['door']==[16,50] and new['warp_events'][0]['x']==16
            assert [c for c in new['coord_events'] if c['script']=='Route104_EventScript_RivalTrigger'][0]['x']==16
            assert 'setobjectxyperm LOCALID_ROUTE104_RIVAL, 16, 52' in (source/'data/maps/Route104/scripts.inc').read_text()
    for n in report['original_sha256']:
        if n.endswith(('/metatiles.bin','/metatile_attributes.bin')):assert (source/n).read_bytes().startswith((inputs/n).read_bytes())
    with tempfile.TemporaryDirectory(prefix='three-port-replay-',dir=source.parent) as directory:
        dest=Path(directory)
        def clone(relative):
            origin=source/relative;copy=dest/relative
            if str(relative)=='.journey-'+LAYER:return
            if relative in targets:
                if str(relative) in report['original_sha256']:copy.write_bytes((inputs/relative).read_bytes())
                return
            if any(relative in target.parents for target in targets):
                copy.mkdir(exist_ok=True)
                for child in origin.iterdir():clone(child.relative_to(source))
            else:copy.symlink_to(origin,target_is_directory=origin.is_dir())
        for child in source.iterdir():clone(child.relative_to(source))
        before,after=MapRenderer(dest),MapRenderer(source)
        banks={after.layouts[json.loads((source/f'data/maps/{n}/map.json').read_text())['layout']]['secondary_tileset'] for n in exteriors}
        compared=[]
        for path in (source/'data/maps').glob('*/map.json'):
            n=path.parent.name;m=json.loads(path.read_text())
            if n in exteriors|interiors or after.layouts[m['layout']]['secondary_tileset'] not in banks:continue
            a,_=before.render(n,npcs=False);b,_=after.render(n,npcs=False)
            assert a.tobytes()==b.tobytes(),n
            compared.append(n)
        assert prepare(dest)==report and prepare(dest)==report
    proof=dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
        layers=PRIOR+[LAYER],original_inputs_verified=True,idempotent=True,differences=[],
        reproduced_layers=[LAYER],byte_identical_outputs=sorted(report['prepared_sha256']),unrelated_source_inputs_checked=checked,
        exact_requested_bounds=True,existing_npcs_and_story_preserved=True,atlas_unchanged=True,
        vermilion_and_pacifidlog_preserved=True,all_other_ports_preserved=True,shared_art_pixel_identical=True,compared_maps=compared)
    output.parent.mkdir(exist_ok=True,parents=True);output.write_text(json.dumps(proof,indent=2)+'\n')
    print('Reproduced three terminals;',checked,'unrelated files preserved;',len(compared),'maps pixel-identical')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--original-inputs',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();validate(a.source,a.original_inputs,a.output)
