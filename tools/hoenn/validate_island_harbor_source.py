"""Replay both island harbors and verify requested terrain and untouched inputs."""
import argparse,hashlib,json,struct,tempfile
from pathlib import Path
from PIL import Image
from prepare_mossdeep_harbor import prepare as mossdeep,PRIOR as BASE
from prepare_dewford_island_harbor import prepare as dewford,PRIOR,LAYER,TILE_COPIES,BRIDGE_GROUND,NORTH,NORTH_Y
from render_sea_maps import MapRenderer


def validate(source,mossdeep_inputs,dewford_inputs,output):
    source=Path(source).resolve();inputs=[Path(mossdeep_inputs),Path(dewford_inputs)]
    reports=[json.loads((source/('.journey-'+n)).read_text()) for n in ['mossdeep-harbor',LAYER]]
    targets={Path(n) for r in reports for n in r['prepared_sha256']}
    expected=dict(json.loads((source/'.source-acquired.json').read_text())['sha256'])
    for n in BASE:expected.update(json.loads((source/('.journey-'+n)).read_text())['prepared_sha256'])
    checked=0
    for n,h in expected.items():
        if Path(n) not in targets:
            assert hashlib.sha256((source/n).read_bytes()).hexdigest()==h,n;checked+=1
    for folder,r in zip(inputs,reports):
        for n,h in r['original_sha256'].items():assert hashlib.sha256((folder/n).read_bytes()).hexdigest()==h,n
    compared=['BirthIsland_Exterior','NavelRock_Exterior','Route105','BattleFrontier_OutsideEast','BattleFrontier_OutsideWest']
    needed_maps=set(compared)|{'MossdeepCity','SlateportCity','JourneyPalletHarbor','JourneyMossdeepSailorsLodge','DewfordTown','Route106','Route107'}
    baseline_layouts=json.loads((inputs[0]/'data/layouts/layouts.json').read_text())['layouts']
    needed_layouts={Path(l[field]).parts[2] for l in baseline_layouts if l['secondary_tileset'] in ('gTileset_Mossdeep','gTileset_Dewford') for field in ('blockdata_filepath','border_filepath')}
    for name in needed_maps:
        m=json.loads((source/f'data/maps/{name}/map.json').read_text());l=next(l for l in baseline_layouts if l['id']==m['layout']);needed_layouts.update(Path(l[f]).parts[2] for f in ('blockdata_filepath','border_filepath'))
    with tempfile.TemporaryDirectory(prefix='island-harbor-replay-',dir=source.parent) as tmp:
        dest=Path(tmp)
        def clone(rel):
            origin=source/rel;target=dest/rel
            if str(rel) in ['.journey-mossdeep-harbor','.journey-'+LAYER]:return
            if rel in targets:
                for folder,r in zip(inputs,reports):
                    if str(rel) in r['prepared_sha256']:
                        if str(rel) in r['original_sha256']:target.write_bytes((folder/rel).read_bytes())
                        return
            if any(rel in t.parents for t in targets):
                target.mkdir(exist_ok=True)
                for child in origin.iterdir():clone(child.relative_to(source))
            elif rel.parts[0]!='include':
                if len(rel.parts)==3 and rel.parts[:2]==('data','maps') and origin.is_dir() and rel.name not in needed_maps:return
                if len(rel.parts)==3 and rel.parts[:2]==('data','layouts') and origin.is_dir() and rel.name not in needed_layouts:return
                target.symlink_to(origin,target_is_directory=origin.is_dir())
        for p in source.iterdir():clone(p.relative_to(source))
        before,after=MapRenderer(dest),MapRenderer(source)
        for name in compared:
            a,_=before.render(name,npcs=False);b,_=after.render(name,npcs=False);assert a.tobytes()==b.tobytes(),name
        assert mossdeep(dest)==reports[0] and mossdeep(dest)==reports[0]
        assert dewford(dest)==reports[1] and dewford(dest)==reports[1]
    renderer=MapRenderer(source)
    def block(x,y):
        name='Route106' if y<0 and x<0 else NORTH if y<0 else 'DewfordTown' if x<0 else 'Route107'
        xx=x+80 if name=='Route106' else x+20 if name=='DewfordTown' else x
        yy=y+20 if name=='Route106' else y-NORTH_Y if y<0 else y
        m=json.loads((source/f'data/maps/{name}/map.json').read_text());l=renderer.layouts[m['layout']]
        return struct.unpack_from('<H',(source/l['blockdata_filepath']).read_bytes(),2*(yy*l['width']+xx))[0]
    words=renderer.tileset('gTileset_JourneyDewfordHarbor')[2]
    for dst,ref,mid in TILE_COPIES:
        if dst in BRIDGE_GROUND:
            # Hide only the foreground in a verification view: the lower layer
            # must exactly match the requested beach while the bridge remains.
            bridge_mid=block(*dst)&1023;lower=words[(bridge_mid-512)*8:(bridge_mid-512)*8+4]
            p=renderer.tileset('gTileset_General');q=renderer.tileset('gTileset_JourneyDewfordHarbor')
            actual=Image.new('RGB',(16,16))
            for quadrant,entry in enumerate(lower):
                tile_id=entry&1023;bank=entry>>12;tiles=(p if tile_id<512 else q)[0];tid=tile_id if tile_id<512 else tile_id-512
                colors=(p if bank<6 else q)[1][bank]
                for y in range(8):
                    for x in range(8):
                        xx=7-x if entry&0x400 else x;yy=7-y if entry&0x800 else y
                        actual.putpixel((quadrant%2*8+x,quadrant//2*8+y),colors[tiles.getpixel((tid%16*8+xx,tid//16*8+yy))])
            wanted,_=renderer.render('Route107',values=[mid],dimensions=(1,1),npcs=False)
            assert actual.tobytes()==wanted.tobytes(),dst
        elif dst==(6,15):
            # Its copied sand is below the staircase requested on the same cell.
            assert words[((block(*dst)&1023)-512)*8:((block(*dst)&1023)-512)*8+4]==renderer.tileset('gTileset_General')[2][0x124*8:0x124*8+4]
        else:assert block(*dst)&1023==(block(*ref)&1023 if mid is None else mid),dst
    for x,y in reports[1]['planted_whole_trees']:assert block(x,y)&1023==0x239 and block(x,y+1)&1023==0x23A
    assert reports[1]['stairs']==[[5,3],[6,3],[5,15],[6,15]]
    report=dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),layers=PRIOR+[LAYER],original_inputs_verified=True,idempotent=True,differences=[],unrelated_source_inputs_checked=checked,independent_replay_passed=True,shared_art_maps_pixel_identical=compared,battle_frontier_preserved=True,other_port_inputs_preserved=True,requested_tile_copies_verified=17,bridge_foreground_retained=True,stairs=reports[1]['stairs'],whole_trees=len(reports[1]['planted_whole_trees']),complete_rock_groups=len(reports[1]['whole_rock_audit']))
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2)+'\n');print('Replayed both harbors; verified 17 terrain copies, stairs and whole trees;',checked,'unrelated inputs intact.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',required=True);p.add_argument('--mossdeep-inputs',required=True);p.add_argument('--dewford-inputs',required=True);p.add_argument('--output',required=True);a=p.parse_args();validate(a.source,a.mossdeep_inputs,a.dewford_inputs,a.output)
