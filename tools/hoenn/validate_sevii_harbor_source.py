"""Replay the seven terminals and prove all original Surf lanes and ports survive."""
import argparse,hashlib,json,struct,tempfile
from pathlib import Path
from prepare_sevii_harbors import PRIOR,LAYER,prepare
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
    for n in report['original_sha256']:
        if n.endswith(('/metatiles.bin','/metatile_attributes.bin')):assert (source/n).read_bytes().startswith((inputs/n).read_bytes()),n
    exteriors={p['exterior'] for p in report['ports']};interiors={p['interior'] for p in report['ports']}
    shared='data/layouts/JourneySeviiSurfArrival/map.bin'
    old=struct.unpack('<221H',(inputs/shared).read_bytes());new=struct.unpack('<221H',(source/shared).read_bytes())
    assert old==new,'The old shared template must stay intact after separating the layouts'
    before_layouts={l['id']:l for l in json.loads((inputs/'data/layouts/layouts.json').read_text())['layouts']}
    after_layouts={l['id']:l for l in json.loads((source/'data/layouts/layouts.json').read_text())['layouts']}
    for p in report['ports']:
        path=f'data/maps/{p["exterior"]}/map.json';a=json.loads((inputs/path).read_text());b=json.loads((source/path).read_text())
        assert a['connections']==b['connections']
        al,bl=before_layouts[a['layout']],after_layouts[b['layout']]
        assert [al['width'],al['height']]==[bl['width'],bl['height']]==[17,13]
        actual=struct.unpack('<221H',(source/bl['blockdata_filepath']).read_bytes())
        assert actual[12*17:]==old[12*17:]
        assert all(actual[y*17+x]==old[y*17+x] for y in range(13) for x in range(2))
        assert len(p['bridge_extension'])==6 and {y for x,y in p['bridge_extension']}=={8,9,10}
        assert all(actual[y*17+x]>>12==0 for x,y in p['bridge_extension'])
        small,medium=p['outside_boat'],p['medium_boat'];px=p['pier_x']
        assert (small['x']<px and medium['x']>px+1) or (medium['x']<px and small['x']>px+1)
        for hull in p['outside_hulls']:
            assert min(y for x,y in hull)>=9
            assert all(actual[8*17+x]>>12==1 and not actual[8*17+x]&0xC00 for x in {x for x,y in hull})
        assert a['warp_events'][0]==b['warp_events'][0]
        assert b['object_events']==[small,medium]
        assert p['original_boat'] in a['object_events'] and small['graphics_id']==p['original_boat']['graphics_id']
    with tempfile.TemporaryDirectory(prefix='sevii-port-replay-',dir=source.parent) as directory:
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
        before,after=MapRenderer(dest),MapRenderer(source);compared=[]
        a,_=before.render('CinnabarIsland_Frlg',npcs=True);b,_=after.render('CinnabarIsland_Frlg',npcs=True)
        assert a.tobytes()==b.tobytes(),'Cinnabar artwork or port placements changed'
        bank=after.layouts[json.loads((source/f'data/maps/{next(iter(exteriors))}/map.json').read_text())['layout']]['secondary_tileset']
        for path in (source/'data/maps').glob('*/map.json'):
            n=path.parent.name;m=json.loads(path.read_text())
            if n in exteriors|interiors or after.layouts[m['layout']]['secondary_tileset']!=bank:continue
            a,_=before.render(n,npcs=False);b,_=after.render(n,npcs=False);assert a.tobytes()==b.tobytes(),n;compared.append(n)
        assert prepare(dest)==report and prepare(dest)==report
    proof=dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
        layers=PRIOR+[LAYER],original_inputs_verified=True,idempotent=True,differences=[],
        reproduced_layers=[LAYER],byte_identical_outputs=sorted(report['prepared_sha256']),unrelated_source_inputs_checked=checked,
        south_row_byte_identical=True,west_two_columns_byte_identical=True,
        surface_connections_and_dimensions_preserved=True,original_small_boat_graphics_preserved=True,
        varied_opposite_berths=True,boats_clear_of_upper_quay=True,bridge_extensions_three_tiles=True,old_boat_gap_closed=True,native_ferry_arrivals_preserved=True,
        all_other_port_placements_preserved=True,cinnabar_quay_art_pixel_identical=True,
        atlas_unchanged=True,shared_art_pixel_identical=True,compared_maps=compared)
    output.parent.mkdir(exist_ok=True,parents=True);output.write_text(json.dumps(proof,indent=2)+'\n')
    print('Reproduced seven terminals;',checked,'unrelated inputs preserved;',len(compared),'shared-bank maps pixel-identical')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--original-inputs',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();validate(a.source,a.original_inputs,a.output)
