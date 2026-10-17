"""Move the battle-item seller to one outdoor Slateport-style Frontier booth."""
import json
import struct
from import_native_pier import import_pier
from render_sea_maps import MapRenderer


def prepare_market(layer):
    source=layer.source
    r=MapRenderer(source)
    name='BattleFrontier_OutsideWest'
    path=f'data/maps/{name}/map.json'
    town=json.loads((source/path).read_text())
    layout=r.layouts[town['layout']]
    bank=layout['secondary_tileset']
    used=set()
    for l in r.layouts.values():
        if l['secondary_tileset']!=bank:continue
        for key in ['blockdata_filepath','border_filepath']:
            raw=(source/l[key]).read_bytes()
            used.update(v&1023 for v in struct.unpack('<'+'H'*(len(raw)//2),raw))
    booth=[[0x270,0x216,0x216,0x272],[0x278,0x21E,0x21E,0x27A]]
    donors=list(dict.fromkeys(sum(booth,[])+[0x263,0x264]))
    old_words=r.tileset(bank)[2]
    assert set(range(730,736))<={word&1023 for word in old_words}, 'Reserve all six animated flag tiles'
    available=[mid for mid in range(512,512+len(old_words)//8) if mid not in used]
    assert len(available)>=len(donors)
    ids,files=import_pier(source,bank,emerald=True,donor='gTileset_Slateport',
                          donor_emerald=True,mids=donors,metatile_slots=available[:len(donors)])
    metapath=next(p for p in files if p.endswith('/metatiles.bin'))
    attrpath=next(p for p in files if p.endswith('/metatile_attributes.bin'))
    words=list(struct.unpack('<'+'H'*(len(files[metapath])//2),files[metapath]))
    grass=r.tileset('gTileset_General')[2][8:12]
    attrs=bytearray(files[attrpath])
    for mid in ids.values():
        words[(mid-512)*8:(mid-512)*8+4]=grass
        struct.pack_into('<H',attrs,(mid-512)*2,0)
    files[metapath]=struct.pack('<'+'H'*len(words),*words)
    files[attrpath]=bytes(attrs)
    for p,raw in files.items():layer.stage(p,raw)
    raw=(source/layout['blockdata_filepath']).read_bytes()
    grid=list(struct.unpack('<'+'H'*(len(raw)//2),raw));width=layout['width']
    left,top=37,40
    cells={(left+x,top+y) for x in range(4) for y in range(3)}
    for kind in ['object_events','warp_events','coord_events','bg_events']:
        assert not any((e.get('x'),e.get('y')) in cells for e in town.get(kind,[]))
    assert all(not grid[y*width+x]&0xC00 for x,y in cells)
    for y,row in enumerate(booth):
        for x,donor in enumerate(row):grid[(top+y)*width+left+x]=0xC00|ids[donor]
    for x,donor in [(left,0x263),(left+3,0x264)]:grid[(top+2)*width+x]=0xC00|ids[donor]
    layer.stage(layout['blockdata_filepath'],struct.pack('<'+'H'*len(grid),*grid))
    dewford_path='data/maps/Route107/map.json'
    dewford=json.loads(layer.outputs[dewford_path])
    sellers=[o for o in dewford['object_events'] if o.get('script')=='JourneyCompetitive_Seller']
    assert len(sellers)==1
    seller=sellers[0]
    dewford['object_events'].remove(seller)
    seller.update(x=left+1,y=top+2,elevation=0)
    town['object_events'].append(seller)
    layer.stage(dewford_path,json.dumps(dewford,indent=2)+'\n')
    layer.stage(path,json.dumps(town,indent=2)+'\n')
    return dict(map=name,booth=[left,top,4,3],seller=[left+1,top+2],
                approach=[left+1,top+3],seller_count=1,hyper_training_stays_in_dewford=True)
