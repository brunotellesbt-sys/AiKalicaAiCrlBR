"""Build an original island terminal and a arched two-level suspension bridge."""
import argparse,copy,json,re,struct
from pathlib import Path
from candidate_layer import Layer
from compile_dewford_harbor_art import compile_art
from render_sea_maps import MapRenderer
from prepare_mossdeep_harbor import PRIOR,LAYER as PREVIOUS
LAYER='dewford-island-harbor';PRIOR=PRIOR+[PREVIOUS]
HARBOR='JourneyDewfordHarbor';MAP='MAP_JOURNEY_DEWFORD_HARBOR'
NORTH='JourneyDewfordPortIsland';NORTH_MAP='MAP_JOURNEY_DEWFORD_PORT_ISLAND'
BANK='gTileset_JourneyDewfordHarbor';ARRIVAL=(16,13)


def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if old:=layer.existing():return old
    s=layer.source;r=MapRenderer(s);data=json.loads((s/'data/layouts/layouts.json').read_text());layouts={l['id']:l for l in data['layouts']}
    maps={};grids={};used=set()
    for name in ['DewfordTown','Route106','Route107']:
        m=json.loads((s/f'data/maps/{name}/map.json').read_text());l=layouts[m['layout']];maps[name]=m
        grids[name]=list(struct.unpack('<'+'H'*(l['width']*l['height']),(s/l['blockdata_filepath']).read_bytes()))
        for field in ['blockdata_filepath','border_filepath']:
            raw=(s/l[field]).read_bytes();used.update(b&1023 for b in struct.unpack('<'+'H'*(len(raw)//2),raw))
    originals={n:v.copy() for n,v in grids.items()}
    files,art,graphics_count=compile_art(r,used)
    folder='data/tilesets/secondary/journey_dewford_harbor'
    # The original shared bank stays byte-identical. Only these three maps use the new bank.
    for name,raw in files.items():layer.stage(folder+'/'+name,raw)
    for path in ['src/data/tilesets/headers.h','src/data/tilesets/graphics.h','src/data/tilesets/metatiles.h']:
        text=(s/path).read_text()
        if path.endswith('headers.h'):
            chunk=re.search(r'const struct Tileset gTileset_Dewford\s*=\s*\{.*?\};',text,re.S)[0]
        elif path.endswith('graphics.h'):
            a=text.index('const u32 gTilesetTiles_Dewford[]');b=text.index('\nconst u32 ',a+1);chunk=text[a:b]
        else:
            chunk='\n'.join(line for line in text.splitlines() if re.search(r'gMetatiles_Dewford\[|gMetatileAttributes_Dewford\[',line))
        chunk=chunk.replace('_Dewford','_JourneyDewfordHarbor').replace('secondary/dewford/','secondary/journey_dewford_harbor/')
        # Preserve Dewford's native flag callback and reserve its animated graphics.
        chunk=chunk.replace('InitTilesetAnim_JourneyDewfordHarbor','InitTilesetAnim_Dewford')
        layer.stage(path,text+'\n'+chunk+'\n')
    north_l=copy.deepcopy(layouts[maps['Route107']['layout']]);north_l.update(id='LAYOUT_JOURNEY_DEWFORD_PORT_ISLAND',name=NORTH+'_Layout',width=16,height=12,border_width=2,border_height=2,blockdata_filepath=f'data/layouts/{NORTH}/map.bin',border_filepath=f'data/layouts/{NORTH}/border.bin',secondary_tileset=BANK)
    data['layouts'].append(north_l);grids[NORTH]=[0x1170]*192
    north=copy.deepcopy(maps['Route107']);north.update(id=NORTH_MAP,name=NORTH,layout=north_l['id'],show_map_name=False,object_events=[],warp_events=[],coord_events=[],bg_events=[],connections=[dict(map='MAP_ROUTE107',direction='down',offset=0),dict(map='MAP_ROUTE106',direction='left',offset=-8)])
    maps[NORTH]=north
    maps['Route107']['connections'].append(dict(map=NORTH_MAP,direction='up',offset=0));maps['Route106']['connections'].append(dict(map=NORTH_MAP,direction='right',offset=8))
    def locate(x,y):
        if y<0:
            if x<0:return 'Route106',x+80,y+20
            return NORTH,x,y+12
        if x<0:return 'DewfordTown',x+20,y
        return 'Route107',x,y
    def put(x,y,b):
        name,xx,yy=locate(x,y);l=north_l if name==NORTH else layouts[maps[name]['layout']]
        assert 0<=xx<l['width'] and 0<=yy<l['height'],(name,xx,yy)
        grids[name][yy*l['width']+xx]=b
    # A stepped northern extension closes the forest without touching the complete
    # native NW boulder. The eastern margin leaves a water corridor beyond the trees.
    shore=[0x11B,0x11C,0x11D,0x123,0x124,0x125,0x12B,0x12C,0x12D]
    land={(x,y) for y in range(-8,7) for x in range(-7,14)}|{(x,y) for y in range(-11,-8) for x in range(-5,14)}
    for y in range(-11,8):
        for x in range(-7,14):
            if (x,y) not in land:
                if y>=-8 or x>=-5:put(x,y,0x1170)
                continue
            row=0 if (x,y-1) not in land else 2 if (x,y+1) not in land else 1
            col=0 if (x-1,y) not in land else 2 if (x+1,y) not in land else 1
            put(x,y,(0x4000 if row==col==1 else 0x3000)|shore[row*3+col])
    planted_trees=[]
    for x,y in [(x,-10) for x in range(-4,13)]+[(12,y) for y in range(-8,5,2)]:
        assert (x,y) in land and (x,y+1) in land
        put(x,y,0x4639);put(x,y+1,0x463A);planted_trees.append([x,y])
    # Place the generated 13x9 terminal. The graphic's arched entrance falls at (5,2).
    for x,y,mid in art['terminal']['cells']:put(x-3,y-6,0x4400|mid)
    door_mid=next(mid for x,y,mid in art['terminal']['cells'] if (x,y)==(8,8))
    attr_path=folder+'/metatile_attributes.bin';attrs=bytearray(layer.outputs[attr_path])
    donor=(s/'data/tilesets/secondary/slateport/metatile_attributes.bin').read_bytes()
    attrs[(door_mid-512)*2:(door_mid-511)*2]=donor[(0x2C6-512)*2:(0x2C7-512)*2]
    layer.stage(attr_path,bytes(attrs));put(5,2,0x4000|door_mid)
    # Clear complete trees only; preserve the full native rock and coastline at x=7..8.
    tree_ids={0x239,0x23A,0x243};cleared=[]
    for y in range(13,17):
        for x in range(3,8):
            at=y*60+x
            if grids['Route107'][at]&1023 in tree_ids:
                grids['Route107'][at]=0x3124;cleared.append([x,y])
    # Remaining dense tree columns start with whole crowns below the clearing.
    for x in range(3,7):
        if grids['Route107'][17*60+x]&1023 in tree_ids:grids['Route107'][17*60+x]=0x3239
    requested_water=[[4,10],[5,10],[5,11]]
    for x,y in requested_water:put(x,y,0x1170)
    # The western cable previously covered the top of this narrow two-cell rock.
    # Retire the entire rock so no bottom fragment remains at the bridge landing.
    for y in (14,15):put(7,y,0x1170)
    # The upper route is elevation 4; level 15 retains that elevation for walkers
    # and retains elevation 1 for vessels and Surf below the bridge.
    bridge=[];rail_ids=[];walk=set(map(tuple,art['arched-bridge']['walk']))
    for x,y,mid in art['arched-bridge']['cells']:
        put(x+4,y+4,0xF000|mid);bridge.append([x+4,y+4])
        if (x,y) not in walk:rail_ids.append(mid)
    put(6,16,0x0124);put(6,15,0x4124)
    # Finish exposed sand using native eight-pixel beach quadrants, including
    # the concave bend beside the three requested water cells. Reuse graphics;
    # only unreferenced metatile slots in this private bank may be allocated.
    primary=r.tileset('gTileset_General')[2]
    before_beach={n:v.copy() for n,v in grids.items()}
    def sea(x,y):
        # These cells are ocean under the retained elevated deck and cables.
        if [x,y] in requested_water:return True
        try:
            name,xx,yy=locate(x,y);ll=north_l if name==NORTH else layouts[maps[name]['layout']]
            if not (0<=xx<ll['width'] and 0<=yy<ll['height']):return False
            return before_beach[name][yy*ll['width']+xx]&1023==0x170
        except KeyError:return False
    meta_path=folder+'/metatiles.bin';beach_words=list(struct.unpack('<'+'H'*(len(layer.outputs[meta_path])//2),layer.outputs[meta_path]));beach_attrs=bytearray(layer.outputs[attr_path])
    referenced={b&1023 for vv in grids.values() for b in vv}|used
    spare=iter(mid for mid in range(512,512+len(beach_words)//8) if mid not in referenced)
    patterns={tuple(primary[mid*8:mid*8+8]):mid for mid in shore};beach_edits=[]
    cells=land|{(x,y) for y in range(10,19) for x in range(0,10)}
    for x,y in sorted(cells):
        name,xx,yy=locate(x,y);ll=north_l if name==NORTH else layouts[maps[name]['layout']];at=yy*ll['width']+xx;old=before_beach[name][at]
        if old&1023 not in shore:continue
        ww=list(primary[0x124*8:0x124*8+8])
        for q,(dx,dy) in enumerate([(-1,-1),(1,-1),(-1,1),(1,1)]):
            horizontal,vertical=sea(x+dx,y),sea(x,y+dy)
            if not horizontal and not vertical and sea(x+dx,y+dy):
                mid=shore[[8,6,2,0][q]];opp=3-q
                for lev in [0,1]:ww[lev*4+q]=primary[mid*8+lev*4+opp]^0xC00
            else:
                row=(0 if dy<0 else 2) if vertical else 1;col=(0 if dx<0 else 2) if horizontal else 1;mid=shore[row*3+col]
                for lev in [0,1]:ww[lev*4+q]=primary[mid*8+lev*4+q]
        north_sea,south_sea,west_sea,east_sea=sea(x,y-1),sea(x,y+1),sea(x-1,y),sea(x+1,y)
        inner=any(not sea(x+dx,y) and not sea(x,y+dy) and sea(x+dx,y+dy) for dx,dy in [(-1,-1),(1,-1),(-1,1),(1,1)])
        if not inner and not (north_sea and south_sea or west_sea and east_sea):
            # Ordinary straights and bends use the COMPLETE native beach tiles,
            # exactly like Route107 (2,10), Dewford (14,10), and their rotations.
            row=0 if north_sea else 2 if south_sea else 1;col=0 if west_sea else 2 if east_sea else 1
            mid=shore[row*3+col];ww=list(primary[mid*8:mid*8+8])
        pattern=tuple(ww)
        if pattern not in patterns:
            mid=next(spare);patterns[pattern]=mid;beach_words[(mid-512)*8:(mid-511)*8]=ww;struct.pack_into('<H',beach_attrs,(mid-512)*2,0)
        value=(old&~1023)|patterns[pattern]
        if value!=old:grids[name][at]=value;beach_edits.append([x,y])
    layer.stage(meta_path,struct.pack('<'+'H'*len(beach_words),*beach_words));layer.stage(attr_path,bytes(beach_attrs))
    rock_audit=[]
    for name in originals:
        ll=layouts[maps[name]['layout']];w=ll['width'];old=originals[name];new=grids[name]
        for pattern in [[(0,0,0x175),(1,0,0x176),(0,1,0x17D),(1,1,0x17E)],[(0,0,0x154),(0,1,0x15C)],[(0,0,0x150),(1,0,0x151),(0,1,0x158),(1,1,0x159)]]:
            for at,block in enumerate(old):
                if block&1023!=pattern[0][2]:continue
                x,y=at%w,at//w
                if not all(x+dx<w and y+dy<ll['height'] and old[(y+dy)*w+x+dx]&1023==mid for dx,dy,mid in pattern):continue
                kept=[new[(y+dy)*w+x+dx]&1023==mid for dx,dy,mid in pattern]
                assert all(kept) or not any(kept),(name,'Partial rock',x,y)
                rock_audit.append(dict(map=name,anchor=[x,y],whole=len(kept),preserved=all(kept)))
    route=maps['Route107'];index=len(route['warp_events']);route['warp_events'].append(dict(x=5,y=2,elevation=0,dest_map=MAP,dest_warp_id='0'))
    # Exactly one world captain is indoors. Native Briney, his boat and all trainers stay.
    town=maps['DewfordTown'];town['object_events']=[o for o in town['object_events'] if o['script']!='Journey_FerryPort9']
    # Restrict only the upper walkway's cable/tower tiles; ships at level 1 can pass underneath.
    header='''#ifndef GUARD_JOURNEY_DEWFORD_BRIDGE_H
#define GUARD_JOURNEY_DEWFORD_BRIDGE_H
static bool8 JourneyDewfordBridgeRailBlocks(const struct ObjectEvent *object, s16 x, s16 y)
{
    static const u16 rails[] = {RAILS};
    u32 i;
    u16 metatile;
    if (gSaveBlock1Ptr->location.mapGroup != MAP_GROUP(MAP_ROUTE107)
        || gSaveBlock1Ptr->location.mapNum != MAP_NUM(MAP_ROUTE107)
        || object->currentElevation != 4)
        return FALSE;
    metatile = MapGridGetMetatileIdAt(x, y);
    for (i = 0; i < ARRAY_COUNT(rails); i++)
        if (metatile == rails[i])
            return TRUE;
    return FALSE;
}
#endif
'''.replace('RAILS',', '.join(hex(i) for i in rail_ids))
    layer.stage('include/journey_dewford_bridge.h',header)
    path='src/event_object_movement.c';text=(s/path).read_text();anchor='static enum Collision GetVanillaCollision(struct ObjectEvent *objectEvent, s16 x, s16 y, enum Direction direction)\n{'
    assert text.count(anchor)==1;text=text.replace(anchor,'#include "journey_dewford_bridge.h"\n\n'+anchor+'\n    if (JourneyDewfordBridgeRailBlocks(objectEvent, x, y))\n        return COLLISION_IMPASSABLE;')
    layer.stage(path,text)
    # Native S.S. Tidal interior, with this terminal's world-network captain.
    inside=json.loads((s/'data/maps/JourneyPalletHarbor/map.json').read_text());old_l=layouts[inside['layout']];il=copy.deepcopy(old_l)
    il.update(id='LAYOUT_JOURNEY_DEWFORD_HARBOR',name=HARBOR+'_Layout',blockdata_filepath=f'data/layouts/{HARBOR}/map.bin',border_filepath=f'data/layouts/{HARBOR}/border.bin');data['layouts'].append(il)
    inside.update(id=MAP,name=HARBOR,layout=il['id'],region='REGION_HOENN',region_map_section='MAPSEC_DEWFORD_TOWN',music=town['music'])
    for o in inside['object_events']:
        if o['script']=='Journey_FerryPort18':o['script']='Journey_FerryPort9'
    for warp in inside['warp_events']:warp.update(dest_map=route['id'],dest_warp_id=str(index))
    for field in ['blockdata_filepath','border_filepath']:layer.stage(il[field],(s/old_l[field]).read_bytes())
    layer.stage(f'data/maps/{HARBOR}/map.json',json.dumps(inside,indent=2)+'\n');maps[HARBOR]=inside
    layer.stage(north_l['border_filepath'],struct.pack('<4H',*[0x1170]*4))
    for name in grids:
        l=north_l if name==NORTH else layouts[maps[name]['layout']]
        if name!=NORTH:l['secondary_tileset']=BANK
        layer.stage(l['blockdata_filepath'],struct.pack('<'+'H'*len(grids[name]),*grids[name]))
        layer.stage(f'data/maps/{name}/map.json',json.dumps(maps[name],indent=2)+'\n')
    groups=json.loads((s/'data/maps/map_groups.json').read_text());group=next(k for k in groups['group_order'] if 'JourneyMossdeepHarbor' in groups[k]);groups[group]+=[NORTH,HARBOR]
    layer.stage('data/maps/map_groups.json',json.dumps(groups,indent=2)+'\n');layer.stage('data/layouts/layouts.json',json.dumps(data,indent=2)+'\n')
    text=(s/'data/event_scripts.s').read_text()
    for name in [NORTH,HARBOR]:
        layer.stage(f'data/maps/{name}/scripts.inc',name+'_MapScripts::\n\t.byte 0\n');text+=f'\n\t.include "data/maps/{name}/scripts.inc"\n'
    layer.stage('data/event_scripts.s',text)
    path='data/scripts/journey_campaign_gates.inc';text=(s/path).read_text();a=text.index('LavenderNetwork_Destination9::\n');b=text.index('\n\n',a);chunk=text[a:b].replace('MAP_DEWFORD_TOWN)',MAP+')')
    for var,value in [('0x8009',16),('0x800A',13)]:
        chunk,count=re.subn(r'(setvar VAR_'+var+r', )\d+',lambda m:m[1]+str(value),chunk);assert count==1
    layer.stage(path,text[:a]+chunk+text[b:])
    return layer.finish(interior=HARBOR,door=[5,2],terminal=[-3,-6,13,9],port_island=NORTH,bridge=bridge,bridge_walk=[[x+4,y+4] for x,y in art['arched-bridge']['walk']],bridge_rail_metatiles=rail_ids,cleared_tree_tiles=cleared,planted_whole_trees=planted_trees,whole_rock_audit=rock_audit,requested_water_tiles=requested_water,beach_edges_finished=beach_edits,custom_graphics=graphics_count,arrival=list(ARRIVAL),captain=[16,12],upper_elevation=4,lower_elevation=1,original_trainers_and_local_briney_preserved=True,other_ports_preserved=True,changed_terrain={n:[[i%layouts[maps[n]['layout']]['width'],i//layouts[maps[n]['layout']]['width']] for i,(a,b) in enumerate(zip(originals[n],grids[n])) if a!=b] for n in originals})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);print(json.dumps(prepare(p.parse_args().source),indent=2))
