"""Generate terrain-authenticated one-time save rescue for every retired ID.

Whole native stamp cores retain their exact translation when the resulting
cell is a safe foot/Surf destination. Other cells use the *already preserved*
legacy GPS RLE, solely to select a frozen rescue destination. Approximate
legacy positions never drive new travel or a live nearest-water search.
"""
from __future__ import annotations

from collections import defaultdict
import copy
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile

from atlas_surf_coasts import retirement_scope
from atlas_surf_legacy import (HEADER_PATH as LEGACY_HEADER, NAVIGATION_PATH, _navigation,
                               _retired as _legacy_retired, _tables as _legacy_tables,
                               _render as _legacy_render)
from atlas_surf_overlay import OverlaySource
from atlas_surface_batteries import stage as stage_batteries
from badge_story_layer import read

HEADER_PATH='src/data/journey_atlas_migration.h'
SAFE_FOOT=('MB_NORMAL','MB_TALL_GRASS','MB_LONG_GRASS','MB_SHORT_GRASS','MB_SAND',
           'MB_DEEP_SAND','MB_ASHGRASS','MB_NO_RUNNING','MB_FOOTPRINTS')
SAFE_SURF=('MB_POND_WATER','MB_INTERIOR_DEEP_WATER','MB_DEEP_WATER',
           'MB_SOOTOPOLIS_DEEP_WATER','MB_OCEAN_WATER','MB_SEAWEED')


def _sha(raw):return hashlib.sha256(raw).hexdigest()


def _load(value):
    if isinstance(value,(str,Path)):
        path=Path(value);raw=path.read_bytes()
        return json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)
    return value


def _safe_behaviors(inputs):
    """Compile the actual native enum, including any explicitly valued entries."""
    compiler=shutil.which('cc') or shutil.which('gcc')
    if compiler is None:raise RuntimeError('A native C compiler is required for migration terrain enums')
    inputs.read('include/constants/metatile_behaviors.h')
    names=SAFE_FOOT+SAFE_SURF
    code=('#include <stdio.h>\n#include <stdint.h>\n#include "constants/metatile_behaviors.h"\n'
          'static const uint16_t ids[]={'+','.join(names)+'};\n'
          'int main(void){return fwrite(ids,1,sizeof(ids),stdout)!=sizeof(ids);}\n')
    with tempfile.TemporaryDirectory(prefix='atlas-migration-enums-') as temporary:
        binary=Path(temporary)/'ids'
        subprocess.run([compiler,'-std=gnu17','-Wall','-Wextra','-Werror','-iquote',str(inputs.source/'include'),
                        '-x','c','-','-o',str(binary)],input=code,text=True,check=True,capture_output=True)
        raw=subprocess.check_output([str(binary)])
    if len(raw)!=2*len(names):raise ValueError('Native migration behavior probe returned truncated IDs')
    values=struct.unpack('<'+'H'*len(names),raw)
    return dict(foot=set(values[:len(SAFE_FOOT)]),surf=set(values[len(SAFE_FOOT):]),
                named_ids=dict(zip(names,values)),probe_sha256=_sha(raw))


def _mode(inputs,name,x,y,enums):
    word=inputs.word(name,x,y)
    if word&0xC00:return None
    behavior=inputs.behavior(name,word)
    if word>>12==1 and behavior in enums['surf'] and inputs.water(name,x,y):return 'surf'
    if word>>12==3 and behavior in enums['foot'] and not inputs.water(name,x,y):return 'walk'
    return None


def _occupied(mapping):
    blocked=set()
    for field in ('object_events','warp_events','coord_events','bg_events'):
        for event in mapping.get(field) or []:
            x,y=event.get('x'),event.get('y')
            if type(x) is not int or type(y) is not int:continue
            radius=0
            if field=='object_events':
                radius=max(int(event.get('movement_range_x',0)),int(event.get('movement_range_y',0)))
                if event.get('trainer_type') not in (None,'TRAINER_TYPE_NONE'):
                    try:radius=max(radius,int(event.get('trainer_sight_or_berry_tree_id',0))+1)
                    except (TypeError,ValueError):raise ValueError(('Non-numeric native trainer sight',event))
            elif field in ('warp_events','coord_events'):radius=1
            blocked.update((x+dx,y+dy) for dx in range(-radius,radius+1) for dy in range(-radius,radius+1))
    return blocked


def _destinations(view,plan,enums):
    by_mode={'walk':{},'surf':{}}
    all_points={}
    plan_names=set()
    for chunk in plan['chunks']:
        name=chunk['name'];plan_names.add(name)
        if name not in view.maps or name not in view.identities:raise ValueError(('Migration target is not compiled',name))
        packed=view.identities[name]
        if packed>>8>=128 or packed&255>=128:raise ValueError(('Migration target exceeds signed WarpData identity',name))
        layout=view.layout(name)
        if [layout['width'],layout['height']]!=[chunk['width'],chunk['height']]:
            raise ValueError(('Migration target dimensions differ from frozen physical plan',name))
        blocked=_occupied(view.maps[name]);ox,oy=chunk['origin']
        for y in range(layout['height']):
            for x in range(layout['width']):
                if (x,y) in blocked:continue
                mode=_mode(view,name,x,y,enums)
                if mode is None:continue
                pixel=((ox+x)//8)|(((oy+y)//8)<<8)
                if not 0<=((ox+x)//8)<224 or not 0<=((oy+y)//8)<112:
                    continue
                point=dict(map=name,map_id=view.maps[name]['id'],packed_id=packed,tile=[x,y],
                           global_tile=[ox+x,oy+y],atlas_pixel=pixel,mode=mode,elevation=1 if mode=='surf' else 3,
                           word=view.word(name,x,y),behavior=view.behavior(name,view.word(name,x,y)))
                all_points[name,x,y]=point
                score=(abs((ox+x)%8-4)+abs((oy+y)%8-4),packed,y,x)
                old=by_mode[mode].get(pixel)
                if old is None or score<old[0]:by_mode[mode][pixel]=(score,point)
    if not by_mode['walk'] or not by_mode['surf']:
        raise ValueError('Both real walkable land and real Surf water are required for safe save fallback')
    return {mode:{pixel:row[1] for pixel,row in points.items()} for mode,points in by_mode.items()},all_points,plan_names


def _old_pixels(parent,retired):
    header=parent.read(NAVIGATION_PATH).decode()
    _,_,_,pixels,grids=_navigation(header,parent)
    by_name={row['map']:row for row in grids}
    result=set()
    for record in retired:
        name=record['map'] if isinstance(record,dict) else record
        if name not in by_name:raise ValueError(('Retired save map missing exact legacy GPS',name))
        row=by_name[name];layout=parent.layout(name)
        if [row['width'],row['height']] != [layout['width'],layout['height']]:
            raise ValueError(('Legacy migration bounds changed',name))
        if isinstance(record,dict) and record.get('packed_id',row['packed_id'])!=row['packed_id']:
            raise ValueError(('Legacy numeric save identity changed',name))
        if isinstance(record,dict):
            mapping=parent.maps[name]
            expected=dict(id=mapping['id'],layout=mapping['layout'],dimensions=[layout['width'],layout['height']],
                          banks=[layout['primary_tileset'],layout['secondary_tileset']])
            for key,value in expected.items():
                if key in record and record[key]!=value:raise ValueError(('Retired migration inventory differs',name,key))
            for key,path in [('map_sha256',f'data/maps/{name}/map.json'),('blockdata_sha256',layout['blockdata_filepath'])]:
                if key in record and _sha(parent.read(path))!=record[key]:
                    raise ValueError(('Retired migration input hash differs',name,key))
        result.update(pixels[row['first']:row['first']+row['width']*row['height']])
    return sorted(result)


def _verify_legacy_header(parent,retired,actual):
    """Recompute host evidence without emitting another copy of the ROM data."""
    _,_,_,values,grids=_navigation(parent.read(NAVIGATION_PATH).decode(),parent)
    records=[dict(map=row) if isinstance(row,str) else row for row in retired]
    normalized=_legacy_retired(parent,records,grids)
    expected=_legacy_render(_legacy_tables(parent,normalized,values))
    if actual!=expected:
        raise ValueError('Existing legacy GPS/water header is not the exact immutable-parent RLE')
    return _sha(actual.encode())


def _distance(a,b):return abs((a&255)-(b&255))+abs((a>>8)-(b>>8))


def fallback_tables(old_pixels,candidates):
    """Freeze deterministic targets; there is no runtime search through terrain."""
    targets,indices,rows,evidence=[],{},[],[]
    for pixel in sorted(set(old_pixels)):
        slots=[]
        for mode in ('walk','surf'):
            available=candidates[mode]
            chosen=pixel if pixel in available else min(available,key=lambda value:(_distance(pixel,value),value))
            point=available[chosen]
            key=(point['packed_id'],*point['tile'],1 if mode=='walk' else 2,point['elevation'])
            if key not in indices:
                if len(targets)>=65535:raise ValueError('Save fallback target index exceeds u16')
                indices[key]=len(targets);targets.append(key)
                evidence.append(copy.deepcopy(point))
            slots.append(indices[key])
        rows.append((pixel,*slots))
    return dict(targets=targets,rows=rows,target_evidence=evidence,
                table_bytes=6*len(targets)+6*len(rows),
                same_pixel_preferences=sum(1 for pixel,_,_ in rows for mode in ('walk','surf') if pixel in candidates[mode]),
                maximum_rescue_distance=max((_distance(pixel,evidence[target]['atlas_pixel'])
                                             for pixel,a,b in rows for target in (a,b)),default=0))


def _exact_rectangles(parent,view,placements,inventory,retired_names,all_safe):
    by_stamp={row['key']:row for row in inventory['stamps']}
    assigned={};unsafe=0
    for placement in placements:
        stamp=by_stamp[placement['stamp']]
        old=stamp['parent_map'];new=placement['name']
        if old not in retired_names:continue
        if new not in view.maps:raise ValueError(('Placed scenery missing from candidate',new))
        left,top,width,height=stamp['source_rect'];sx,sy=placement.get('stamp_offset',[0,0])
        for x,y in stamp['core_cells']:
            if not 0<=x<width or not 0<=y<height:raise ValueError(('Scenery core outside authenticated stamp',stamp['key']))
            source_x,source_y=left+x,top+y;target_x,target_y=sx+x,sy+y
            if parent.word(old,source_x,source_y)!=view.word(new,target_x,target_y):
                raise ValueError(('Exact save translation would enter altered scenery',stamp['key'],x,y))
            target=all_safe.get((new,target_x,target_y))
            if target is None:
                unsafe+=1;continue
            key=old,source_x,source_y
            value=(new,target_x-source_x,target_y-source_y,target['mode'],target['elevation'])
            if key in assigned and assigned[key]!=value:
                raise ValueError(('One old native stamp cell has conflicting exact migrations',key))
            assigned[key]=value
    # Merge horizontal runs and then identical adjacent rows. Rectangle tables
    # remain affine and disjoint; unsafe/occupied/warp cells use safe fallback.
    rows=defaultdict(list)
    for (name,x,y),target in assigned.items():rows[name,y,target].append(x)
    horizontal=[]
    for (name,y,target),points in sorted(rows.items()):
        points.sort();start=previous=points[0]
        for x in points[1:]:
            if x!=previous+1:
                horizontal.append((name,start,y,previous+1,y+1,target));start=x
            previous=x
        horizontal.append((name,start,y,previous+1,y+1,target))
    grouped=defaultdict(list)
    for old,left,top,right,bottom,target in horizontal:grouped[old,left,right,target].append((top,bottom))
    result=[]
    for (old,left,right,target),intervals in sorted(grouped.items()):
        intervals.sort();top,bottom=intervals[0]
        chunks=[]
        for a,b in intervals[1:]:
            if a==bottom:bottom=b
            else:chunks.append((top,bottom));top,bottom=a,b
        chunks.append((top,bottom))
        new,dx,dy,mode,elevation=target
        for top,bottom in chunks:
            result.append(dict(old_map=parent.maps[old]['id'],destination_map=view.maps[new]['id'],
                               source_rect=[left,top,right,bottom],destination_origin=[left+dx,top+dy],
                               mode=mode,elevation=elevation))
    return result,dict(exact_safe_core_cells=len(assigned),unsafe_or_occupied_core_cells_using_fallback=unsafe)


def _attach_warps(rows,parent,view,event_relocations,retired_names):
    expected={(name,index) for name in retired_names for index,_ in enumerate(parent.maps[name].get('warp_events') or [])}
    found={}
    for relocation in event_relocations:
        if relocation['field']!='warp_events' or relocation['source_map'] not in retired_names:continue
        key=relocation['source_map'],relocation['source_index']
        if key in found or key not in expected:raise ValueError(('Duplicate/invented legacy event warp migration',key))
        target=relocation['target_map'];index=relocation['target_index']
        if target not in view.maps or not 0<=index<len(view.maps[target].get('warp_events') or []):
            raise ValueError(('Legacy event warp has no real candidate destination',key,target,index))
        found[key]=dict(old_warp_id=key[1],destination_map=view.maps[target]['id'],destination_warp_id=index)
    if set(found)!=expected:raise ValueError(('Missing exact legacy event warp migrations',sorted(expected-set(found))))
    for (name,index),entry in sorted(found.items()):
        old_id=parent.maps[name]['id']
        candidates=[row for row in rows if row['old_map']==old_id]
        if not candidates:raise ValueError(('Legacy portal has no safe exact stamp rectangle for its warp table',name,index))
        candidates[0].setdefault('warp_relocations',[]).append(entry)
    return len(found)


def render_fallback(tables):
    code='''// One-time save fallback only. Legacy GPS is never used for active travel.
#ifndef GUARD_JOURNEY_ATLAS_MIGRATION_H
#define GUARD_JOURNEY_ATLAS_MIGRATION_H
#include "journey_atlas_legacy.h"
struct JourneyAtlasMigrationTarget { u16 map; u8 x,y,mode,elevation; };
struct JourneyAtlasMigrationPixel { u16 pixel,foot,surf; };
typedef char JourneyAtlasMigrationTargetSixBytes[(sizeof(struct JourneyAtlasMigrationTarget)==6)?1:-1];
typedef char JourneyAtlasMigrationPixelSixBytes[(sizeof(struct JourneyAtlasMigrationPixel)==6)?1:-1];
static const struct JourneyAtlasMigrationTarget sAtlasMigrationTargets[]={
'''
    code+=''.join('    {'+','.join(map(str,row))+'},\n' for row in tables['targets'])+'};\n'
    code+='static const struct JourneyAtlasMigrationPixel sAtlasMigrationPixels[]={\n'
    code+=''.join('    {'+','.join(map(str,row))+'},\n' for row in tables['rows'])+'};\n'
    return code+r'''
static EWRAM_DATA struct JourneyAtlasSaveMove sAtlasMigrationResolvedMove;
static const struct JourneyAtlasSaveMove *JourneyAtlasMigrationFallback(u8 group,u8 num,s16 x,s16 y)
{
    u16 pixel, packed=((u16)group<<8)|num;
    bool8 water=FALSE;
    u32 lo=0,hi=ARRAY_COUNT(sAtlasMigrationPixels),mid;
    const struct JourneyAtlasMigrationPixel *row;
    const struct JourneyAtlasMigrationTarget *target;
    if (!JourneyAtlasLegacyWorldPosition(packed,x,y,&pixel)) return NULL;
    while(lo<hi)
    {
        mid=lo+(hi-lo)/2;
        if(sAtlasMigrationPixels[mid].pixel<pixel) lo=mid+1;
        else hi=mid;
    }
    if(lo==ARRAY_COUNT(sAtlasMigrationPixels)||sAtlasMigrationPixels[lo].pixel!=pixel) return NULL;
    // A clear legacy water bit is only a preference, not evidence of land.
    // Both possible destinations are separately authenticated native terrain.
    JourneyAtlasLegacyWater(packed,x,y,&water);
    row=&sAtlasMigrationPixels[lo];
    target=&sAtlasMigrationTargets[water?row->surf:row->foot];
    sAtlasMigrationResolvedMove.oldGroup=group;
    sAtlasMigrationResolvedMove.oldNum=num;
    sAtlasMigrationResolvedMove.newGroup=target->map>>8;
    sAtlasMigrationResolvedMove.newNum=target->map&255;
    sAtlasMigrationResolvedMove.left=x;sAtlasMigrationResolvedMove.top=y;
    sAtlasMigrationResolvedMove.right=x;sAtlasMigrationResolvedMove.bottom=y;
    sAtlasMigrationResolvedMove.dx=(s16)target->x-x;
    sAtlasMigrationResolvedMove.dy=(s16)target->y-y;
    sAtlasMigrationResolvedMove.mode=target->mode;
    sAtlasMigrationResolvedMove.elevation=target->elevation;
    return &sAtlasMigrationResolvedMove;
}
#endif
'''


def stage(layer,parent,plan,placements,event_relocations,*,retired_maps=None,scenery_inventory):
    """Install exact-core priority plus safe fallback for the complete old mesh."""
    if HEADER_PATH in layer.outputs or (layer.source/HEADER_PATH).exists():
        raise ValueError('Atlas save fallback is already installed; preserve existing preparation')
    legacy=read(layer,LEGACY_HEADER).decode()
    if 'JourneyAtlasLegacyWorldPosition' not in legacy or 'JourneyAtlasLegacyWater' not in legacy:
        raise ValueError('Exact legacy GPS/water header must be installed before save fallback')
    inventory=_load(scenery_inventory)
    if retired_maps is None:
        names,_,_=retirement_scope(parent)
        retired_maps=[dict(map=name,packed_id=parent.identities[name]) for name in names]
    retired_names={row['map'] if isinstance(row,dict) else row for row in retired_maps}
    if len(retired_names)!=len(retired_maps):raise ValueError('Duplicate retired save identity supplied')
    legacy_sha256=_verify_legacy_header(parent,retired_maps,legacy)
    view=OverlaySource(layer)
    enums=_safe_behaviors(parent)
    candidates,all_safe,plan_names=_destinations(view,plan,enums)
    if plan_names & retired_names:raise ValueError('A fallback destination is itself retired')
    pixels=_old_pixels(parent,retired_maps)
    tables=fallback_tables(pixels,candidates)
    rows,exact=_exact_rectangles(parent,view,placements,inventory,retired_names,all_safe)
    event_warps=_attach_warps(rows,parent,view,event_relocations,retired_names)
    header=render_fallback(tables)
    parent.assert_unchanged();view.assert_unchanged()
    layer.stage(HEADER_PATH,header)
    migration=stage_batteries(layer,rows,fallback_header='data/journey_atlas_migration.h')
    return dict(kind='atlas-complete-save-fallback',version=2,retired_maps=len(retired_names),
                retired_names=sorted(retired_names),legacy_header=LEGACY_HEADER,
                exact_parent_legacy_header_sha256=legacy_sha256,
                legacy_data_duplicated=False,runtime_header_overwritten=False,
                fallback_header=HEADER_PATH,fallback_header_sha256=_sha(header.encode()),
                fallback_pixels=len(tables['rows']),fallback_targets=len(tables['targets']),
                fallback_data_bytes=tables['table_bytes'],
                maximum_approximate_legacy_rescue_distance=tables['maximum_rescue_distance'],
                same_pixel_mode_preferences=tables['same_pixel_preferences'],
                target_terrain_evidence=tables['target_evidence'],
                exact_core_priority=exact,event_warp_relocations=event_warps,
                terrain_behavior_enum=enums['named_ids'],native_enum_probe_sha256=enums['probe_sha256'],
                candidate_input_sha256=dict(view.inputs),parent_input_sha256=dict(parent.inputs),
                installed_migration=migration,legacy_clear_water_bit_is_not_land_evidence=True,
                unmatched_legacy_event_ids_use_declared_map_center_rescue=True,
                native_save_continue_validated=False,final_release_validated=False)
