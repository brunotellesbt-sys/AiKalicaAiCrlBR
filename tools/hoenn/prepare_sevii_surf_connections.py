"""Connect the existing world seas to all seven native Sevii coasts by Surf.

No port buildings, boats, captains, town land, or non-Sevii terrain are edited.
"""
import argparse,copy,json,struct
from pathlib import Path
from candidate_layer import Layer
from prepare_sootopolis_harbor import PRIOR,LAYER as PREVIOUS
from sevii_navigation_grid import reconcile

ROOT=Path(__file__).resolve().parents[2]
LAYER='sevii-surf-connections';PRIOR=PRIOR+[PREVIOUS]
ISLANDS=['One','Two','Three','Four','Five','Six','Seven']


def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if old:=layer.existing():return old
    s=layer.source;maps={p.parent.name:json.loads(p.read_text()) for p in (s/'data/maps').glob('*/map.json')};before=copy.deepcopy(maps)
    layouts={l['id']:l for l in json.loads((s/'data/layouts/layouts.json').read_text())['layouts']};byid={m['id']:n for n,m in maps.items()}
    masks=json.loads((ROOT/'tools/hoenn/data/route-navigation-reference.json').read_text())['compiled_water_masks']
    seams=[];redirected=[];terrain=[]
    for island in ISLANDS:
        harbor=island+'Island_Harbor_Frlg';town='ThreeIsland_Port_Frlg' if island=='Three' else island+'Island_Frlg'
        h,c=maps[harbor],maps[town];hl,cl=layouts[h['layout']],layouts[c['layout']]
        assert not any(edge['direction']=='left' for edge in c.get('connections') or []),town
        # Its eastern sea boundary is now occupied by the native island coast.
        # The former sea neighbours retain their other world-network links.
        for edge in [edge for edge in h.get('connections') or [] if edge['direction']=='right']:
            other=byid[edge['map']];maps[other]['connections']=[e for e in maps[other]['connections'] or [] if e['map']!=h['id']]
            h['connections'].remove(edge);redirected.append(dict(port=harbor,former_neighbor=other))
        offset=hl['height']-cl['height']
        h['connections']=(h.get('connections') or [])+[dict(map=c['id'],direction='right',offset=offset)]
        c['connections']=(c.get('connections') or [])+[dict(map=h['id'],direction='left',offset=-offset)]
        h.update(map_type='MAP_TYPE_ROUTE',weather='WEATHER_SUNNY',requires_flash=False,allow_running=True,allow_cycling=True)
        p=cl['blockdata_filepath'];raw=(s/p).read_bytes();v=list(struct.unpack('<'+'H'*(len(raw)//2),raw));assert len(masks[town])==len(v)
        old=v.copy()
        for i,wet in enumerate(masks[town]):
            if wet=='1':
                # The imported ocean animation tiles were blocked. Use native
                # outdoor ocean tiles without changing a single land cell.
                v[i]=0x112B if v[i]&1023>=640 else (v[i]&~0xFC00)|0x1000
        width=cl['width'];entries=[y for y in range(max(0,offset),min(hl['height'],offset+cl['height'])) if masks[town][(y-offset)*width]=='1']
        assert entries,(town,'No water at the shared native shoreline')
        layer.stage(p,struct.pack('<'+'H'*len(v),*v));terrain.append(dict(map=town,water_cells_changed=sum(a!=b for a,b in zip(old,v)),native_land_unchanged=all(a==b for a,b,wet in zip(old,v,masks[town]) if wet!='1')))
        # Keep warp IDs/arrival coordinates stable for existing ferry saves,
        # but eliminate the invisible step warp on the outdoor sand.
        p=hl['blockdata_filepath'];raw=(s/p).read_bytes();v=list(struct.unpack('<'+'H'*(len(raw)//2),raw));w=h['warp_events'][0]
        assert [w['x'],w['y']]==[8,2],(harbor,w)
        v[w['y']*hl['width']+w['x']]=0x3115;layer.stage(p,struct.pack('<'+'H'*len(v),*v))
        seams.append(dict(harbor=harbor,town=town,direction='right',offset=offset,shared_water_rows=entries))
    # A legacy first-ferry-arrival sequence teleports to the town/PC. Surf
    # arrivals bypass that sequence; normal native ferry story entry remains.
    layer.stage('include/journey_sevii_surf.h','#ifndef GUARD_JOURNEY_SEVII_SURF_H\n#define GUARD_JOURNEY_SEVII_SURF_H\nvoid JourneySeviiSurfEntry(void);\n#endif\n')
    layer.stage('src/journey_sevii_surf.c','''#include "global.h"
#include "event_data.h"
#include "journey_sevii_surf.h"
#include "constants/vars.h"

void JourneySeviiSurfEntry(void)
{
    if ((gPlayerAvatar.flags & PLAYER_AVATAR_FLAG_SURFING)
        && VarGet(VAR_MAP_SCENE_ONE_ISLAND_HARBOR) < 3)
        VarSet(VAR_MAP_SCENE_ONE_ISLAND_HARBOR, 3);
}
''')
    p='data/maps/OneIsland_Harbor_Frlg/scripts.inc';text=(s/p).read_text();text=text.replace('OneIsland_Harbor_Frlg_MapScripts::','OneIsland_Harbor_Frlg_MapScripts::\n\tmap_script MAP_SCRIPT_ON_TRANSITION, OneIsland_Harbor_SurfEntry',1)
    text+='\nOneIsland_Harbor_SurfEntry::\n\tcallnative JourneySeviiSurfEntry\n\tend\n';layer.stage(p,text)
    p='data/maps/OneIsland_Frlg/scripts.inc';text=(s/p).read_text().replace('OneIsland_OnTransition::','OneIsland_OnTransition::\n\tcallnative JourneySeviiSurfEntry',1);layer.stage(p,text)
    for n,m in maps.items():
        if m!=before[n]:
            assert m['object_events']==before[n]['object_events'] and m['warp_events']==before[n]['warp_events'],n
            layer.stage(f'data/maps/{n}/map.json',json.dumps(m,indent=2)+'\n')
    geometry=json.loads((s/'.journey-navigated-sea-atlas').read_text())
    header,gps=reconcile((s/'src/data/journey_world_position.h').read_text(),geometry['projections'],maps)
    layer.stage('src/data/journey_world_position.h',header)
    return layer.finish(seamless_connections=seams,redirected_redundant_edges=redirected,terrain=terrain,gps=gps,
                        port_buildings_boats_captains_and_warps_unchanged=True,sootopolis_and_pallet_untouched=True,
                        surf_arrival_skips_forced_first_ferry_warp=True,existing_route_maps_preserved=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);print(prepare(p.parse_args().source)['layer'])
