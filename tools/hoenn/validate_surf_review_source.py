"""Reproduce the review layer from the independent merged-PR input."""
import argparse,hashlib,json,struct,tempfile
from pathlib import Path
from prepare_surf_review import prepare,PRIOR,LAYER
from prepare_world_dex_map import decode

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def validate(source,inputs,output):
    source,inputs=Path(source).resolve(),Path(inputs).resolve();r=json.loads((source/('.journey-'+LAYER)).read_text());targets={Path(p) for p in r['prepared_sha256']}
    expected=dict(json.loads((inputs/'.source-acquired.json').read_text())['sha256'])
    for n in PRIOR:expected.update(json.loads((inputs/('.journey-'+n)).read_text())['prepared_sha256'])
    for p,d in r['original_sha256'].items():assert sha(inputs/p)==d==expected[p],p
    expected.update(r['prepared_sha256'])
    for p,d in expected.items():assert sha(source/p)==d,p
    with tempfile.TemporaryDirectory(prefix='review-replay-',dir=source.parent) as d:
        dest=Path(d)
        def clone(p):
            origin,copy=inputs/p,dest/p
            if p in targets:copy.parent.mkdir(exist_ok=True,parents=True);copy.write_bytes(origin.read_bytes())
            elif any(p in t.parents for t in targets):
                copy.mkdir(exist_ok=True,parents=True)
                for c in origin.iterdir():clone(c.relative_to(inputs))
            else:copy.symlink_to(origin,target_is_directory=origin.is_dir())
        for p in inputs.iterdir():
            if p.name in ['build','.git','pokeemerald.gba','pokeemerald.elf','pokeemerald.map']:continue
            clone(p.relative_to(inputs))
        assert prepare(dest)==r
        assert prepare(dest)==r
    old=json.loads((inputs/'.journey-sanctuaries').read_text());new=r['effective_sanctuaries']
    assert len(old['captures'])==len(new['captures'])==105
    for a,b in zip(old['captures'],new['captures']):
        assert all(a[k]==b[k] for k in ['species','id','national_dex','flag','flag_id']),a
    counts={site['map']:site['species_count'] for site in old['sites']};moved=[]
    for b in r['branches']:
        if b['existing_cave']:continue
        assert counts[b['donor']]==max(counts.values())==b['donor_before_count'];counts[b['donor']]-=1;moved.extend(b['species'])
    assert len(moved)==8 and len(set(moved))==8
    assert all(c['national_dex']<=493 for c in new['captures'] if c['species'] in moved)
    assert r['foreign_rock_and_beach_aprons']
    maps={p.parent.name:json.loads(p.read_text()) for p in (source/'data/maps').glob('*/map.json')};ls={l['id']:l for l in json.loads((source/'data/layouts/layouts.json').read_text())['layouts']};byid={m['id']:n for n,m in maps.items()}
    for p in (inputs/'data/maps').glob('*/map.json'):
        oldmap=json.loads(p.read_text());newmap=maps[p.parent.name]
        for field in ['warp_events','coord_events','bg_events']:
            assert all(e in newmap.get(field,[]) for e in oldmap.get(field,[])),(p.parent.name,field)
        removed=[o for o in oldmap.get('object_events',[]) if o not in newmap.get('object_events',[])]
        assert all(o['flag'] in {c['flag'] for c in old['captures'] if c['species'] in moved} for o in removed)
    atlas=decode((source/'src/data/journey_world_map.h').read_text());before=decode((inputs/'src/data/journey_world_map.h').read_text())
    for b in r['branches']:
        x,y=b['position'];assert atlas.getpixel((x,y))==0
        nearest=b['nearest_existing_ink'];distance=abs(nearest[0]-x)+abs(nearest[1]-y)
        assert distance==min(abs(xx-x)+abs(yy-y) for yy in range(112) for xx in range(224) if before.getpixel((xx,yy))==2)
        assert all(a[0]==c[0] or a[1]==c[1] for a,c in zip(b['polyline'],b['polyline'][1:]))
    names=[row['map'] for row in r['boundaries']]+[b['surface'] for b in r['branches'] if b['surface']!=b['parent']]
    for n in names:
        l=ls[maps[n]['layout']];w,h=l['width'],l['height'];v=struct.unpack('<'+'H'*(w*h),(source/l['blockdata_filepath']).read_bytes());sp={d:set() for d in ['left','right','up','down']}
        for c in maps[n].get('connections') or []:
            d=c['direction']
            if d not in sp:continue
            q=ls[maps[byid[c['map']]]['layout']];limit=h if d in ['left','right'] else w;length=q['height'] if d in ['left','right'] else q['width'];sp[d].update(range(max(0,c['offset']),min(limit,c['offset']+length)))
        for y in range(h):
            for x in range(w):
                closed=(x<2 and y not in sp['left'] or x>=w-2 and y not in sp['right'] or y<2 and x not in sp['up'] or y>=h-2 and x not in sp['down'])
                if closed:assert v[y*w+x]&0xC00 or v[y*w+x]>>12>=3,(n,x,y,hex(v[y*w+x]))
    assert r['gps']['maximum_neighbor_pixel_step']<=2 and r['gps']['maximum_seam_delta']==0
    assert '#define MAP_POPUP_STRING_BUFFER_LENGTH 96' in (source/'include/map_name_popup.h').read_text()
    proof=dict(foreign_rock_and_beach_aprons=True,all_relocated_available_in_four_editions=True,popup_buffer_bytes=96,passed=True,rom_sha256=sha(source/'pokeemerald.gba'),layers=PRIOR+[LAYER],independent_source_reproduced=True,idempotent=True,all_source_hashes_verified=len(expected),all_original_warps_and_nonlegendary_events_preserved=True,legendary_capture_flags_and_species_preserved=True,total_special_species=105,redistributed_from_fullest=moved,branches=r['branches'],boundaries=names,all_exposed_route_limits_blocked=True,complete_native_cave_shells=r['mountain_repairs'],complete_single_tile_rock_art=r['rock_art'],gps=r['gps'],chart=r['chart'])
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(proof,indent=2)+'\n');print('Review layer reproduced; 8 unique legendary relocations; limits checked:',len(names))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--original-inputs',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();validate(a.source,a.original_inputs,a.output)
