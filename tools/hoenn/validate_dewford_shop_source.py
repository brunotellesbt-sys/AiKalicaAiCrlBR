"""Independently replay the shop layer and compare every unchanged source/map cell."""
import argparse,hashlib,json,re,struct,tempfile,subprocess
from pathlib import Path
from prepare_dewford_competitive_shop import prepare,PRIOR,LAYER
from render_sea_maps import MapRenderer


def digest(raw):return hashlib.sha256(raw).hexdigest()
def validate(source,preimages,output):
    source,preimages,output=map(Path,[source,preimages,output]);source=source.resolve()
    report=json.loads((source/('.journey-'+LAYER)).read_text())
    expected=dict(json.loads((source/'.source-acquired.json').read_text())['sha256'])
    for layer in PRIOR:expected.update(json.loads((source/('.journey-'+layer)).read_text())['prepared_sha256'])
    unrelated=0
    for name,sha in expected.items():
        if name in report['prepared_sha256']:continue
        assert digest((source/name).read_bytes())==sha,name
        unrelated+=1
    assert unrelated>30000
    with tempfile.TemporaryDirectory(prefix='dewford-replay-',dir='/tmp') as tmp:
        replay=Path(tmp)
        for p in source.iterdir():
            if p.name!='.journey-'+LAYER:(replay/p.name).symlink_to(p,target_is_directory=p.is_dir())
        def materialize(folder):
            if folder==replay:return
            materialize(folder.parent)
            if folder.is_symlink():
                target=folder.resolve();folder.unlink();folder.mkdir()
                for p in target.iterdir():(folder/p.name).symlink_to(p,target_is_directory=p.is_dir())
        for name in report['prepared_sha256']:
            p=replay/name;materialize(p.parent)
            p.unlink(missing_ok=True)
            if name in report['original_sha256']:
                raw=(preimages/name).read_bytes();assert digest(raw)==expected[name],name;p.write_bytes(raw)
        before=MapRenderer(replay);after=MapRenderer(source)
        allowed={'Route107':{(x,y) for x in range(4) for y in (13,14)}|{(0,15),(1,15),(2,15),(3,15)},
                 'Route106':{(78,14),(79,14)},'JourneyDewfordPortIsland':{(8,6),(8,7),(9,6),(9,7)}}
        ta=before.tileset('gTileset_JourneyDewfordHarbor')[0];tb=after.tileset('gTileset_JourneyDewfordHarbor')[0]
        for tile in range(682,688):
            i=tile-512;box=(i%16*8,i//16*8,i%16*8+8,i//16*8+8)
            assert ta.crop(box).tobytes()==tb.crop(box).tobytes(),'Animated flag graphic overwritten'
        grid=after.render('Route107',npcs=False)[1];layout=after.layouts[grid['layout']]
        blocks=struct.unpack('<'+'H'*(layout['width']*layout['height']),(source/layout['blockdata_filepath']).read_bytes())
        words=after.tileset('gTileset_JourneyDewfordHarbor')[2]
        tool=Path(__file__).resolve().parents[2]/'.local/arm-binutils/usr/bin/arm-none-eabi-nm'
        symbols=subprocess.check_output([str(tool),'-n',str(source/'pokeemerald.elf')],text=True)
        offset=int(re.search(r'^(\w+) [Rr] gMetatiles_JourneyDewfordHarbor$',symbols,re.M)[1],16)-0x8000000
        expected=struct.pack('<'+'H'*len(words),*words)
        assert (source/'pokeemerald.gba').read_bytes()[offset:offset+len(expected)]==expected,'Stale compiled shore/booth metatiles'
        reference=blocks[12*layout['width']+3]&1023
        for y in (13,14):
            target=blocks[y*layout['width']+3]&1023
            assert words[(target-512)*8:(target-512)*8+4]==words[(reference-512)*8+4:(reference-511)*8]
        cells=0;events=0
        for p in (source/'data/maps').glob('*/map.json'):
            m=json.loads(p.read_text());n=p.parent.name;l=after.layouts[m['layout']]
            if l['secondary_tileset']!='gTileset_JourneyDewfordHarbor':continue
            old=json.loads((replay/p.relative_to(source)).read_text())
            assert all(o in m['object_events'] for o in old['object_events']),n
            events+=len(old['object_events'])
            for key in set(m)-{'object_events'}:assert m[key]==old[key],(n,key)
            oldim,_=before.render(n,npcs=False);newim,_=after.render(n,npcs=False)
            a=(replay/l['blockdata_filepath']).read_bytes();b=(source/l['blockdata_filepath']).read_bytes()
            for y in range(l['height']):
                for x in range(l['width']):
                    if (x,y) in allowed.get(n,set()):continue
                    at=2*(y*l['width']+x);assert a[at:at+2]==b[at:at+2],(n,x,y,'terrain')
                    box=(x*16,y*16,(x+1)*16,(y+1)*16)
                    assert oldim.crop(box).tobytes()==newim.crop(box).tobytes(),(n,x,y,'pixels')
                    cells+=1
            assert (replay/l['border_filepath']).read_bytes()==(source/l['border_filepath']).read_bytes()
        a=(replay/'src/data/items.h').read_text();b=(source/'src/data/items.h').read_text()
        records=lambda text:dict(re.findall(r'\[ITEM_(\w+)\]\s*=\s*(\{.*?\n    \},)',text,re.S))
        original,current=records(a),records(b);changed=set(report['prices'])|{'TM_PLAY_ROUGH','ADAMANT_ORB','LUSTROUS_ORB','GRISEOUS_ORB'}
        for name,record in original.items():
            if name not in changed:assert current[name]==record,name
        mega=[n for n,record in original.items() if 'HOLD_EFFECT_MEGA_STONE' in record]
        assert len(mega)>30 and all(current[n]==original[n] for n in mega)
        tms=lambda root:re.findall(r'F\((\w+)\)',(root/'include/constants/tms_hms.h').read_text().split('#define FOREACH_TM(F)',1)[1].split('#define FOREACH_HM',1)[0])
        assert tms(source)==tms(replay)+['PLAY_ROUGH']
        original_forms=(replay/'src/data/pokemon/form_change_tables.h').read_text()
        updated_forms=(source/'src/data/pokemon/form_change_tables.h').read_text()
        for species,item in [('DIALGA','ADAMANT_ORB'),('PALKIA','LUSTROUS_ORB')]:
            updated_forms=updated_forms.replace('\n    {FORM_CHANGE_ITEM_HOLD, SPECIES_'+species+'_ORIGIN, ITEM_'+item+'},','')
        updated_forms=updated_forms.replace('    {FORM_CHANGE_ITEM_HOLD, SPECIES_GIRATINA_ORIGIN, ITEM_GRISEOUS_ORB},','#if I_GRISEOUS_ORB_FORM_CHANGE < GEN_9\n    {FORM_CHANGE_ITEM_HOLD, SPECIES_GIRATINA_ORIGIN, ITEM_GRISEOUS_ORB},\n#endif')
        assert updated_forms==original_forms
        result=prepare(replay);assert result==report
        assert prepare(replay)==report
        for name,sha in report['prepared_sha256'].items():assert digest((replay/name).read_bytes())==sha,name
    proof=dict(passed=True,rom_sha256=digest((source/'pokeemerald.gba').read_bytes()),layers=PRIOR+[LAYER],
               unrelated_inputs_checked=unrelated,independent_replay=True,idempotent=True,
               all_existing_events_preserved=True,existing_events_checked=events,unchanged_map_cells_pixel_checked=cells,
               only_requested_terrain_changed=True,mega_stones_unchanged=True,existing_tm_hm_numbers_preserved=True,animated_flag_graphics_reserved=True,booth_shore_matches_3_12=True,compiled_booth_shore_matches_source=True)
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--preimages',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();validate(a.source,a.preimages,a.output)
