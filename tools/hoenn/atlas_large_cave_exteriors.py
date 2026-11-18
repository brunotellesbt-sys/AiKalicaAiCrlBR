"""Expand nine compact cave islands using complete native shoreline stripes.

The original three-by-three entrances are replaced as complete objects by the
81-cell Seafoam mountain. Reef limits and connection mouths stay untouched.
"""
import copy
import hashlib
import json
import struct

from badge_story_layer import read
from atlas_legendary_chambers import stretch
from render_sea_maps import _braced


def runs(cells,width,height):
    result=[]
    for y in range(height):
        x=0
        while x<width:
            if (x,y) not in cells:
                x+=1
                continue
            end=x+1
            while end<width and (end,y) in cells:
                end+=1
            result.append([y,x,end]);x=end
    return result


def stage(layer,metadata):
    layouts={l['id']:l for l in json.loads(read(layer,'data/layouts/layouts.json'))['layouts']}
    chunks={r['name']:r for r in metadata['geometry_plan']['chunks']}
    native=json.loads(read(layer,'.journey-sea-landscapes'))['seafoam_mountain']
    mountain=native['cells']
    if len(mountain)!=81 or native['source_map']!='Route20_Frlg':
        raise ValueError('Changed complete Seafoam donor')
    source_map=json.loads(read(layer,'data/maps/Route20_Frlg/map.json'))
    dl=layouts[source_map['layout']]
    dv=struct.unpack('<'+'H'*(dl['width']*dl['height']),read(layer,dl['blockdata_filepath']))
    for dx,dy,word in mountain:
        if dv[(14+dy)*dl['width']+72+dx]!=word:
            raise ValueError('Mountain donor is not the authenticated native object')
    reports=[]
    rescues=[]
    for index,num in enumerate([0,1,2,3,4,5,6,7,14]):
        name=f'JourneyAtlasCave{num:02d}'
        mapping=json.loads(read(layer,f'data/maps/{name}/map.json'))
        layout=layouts[mapping['layout']]
        if (layout['width'],layout['height'])!=(33,33) or layout['primary_tileset']!='gTileset_General_Frlg':
            raise ValueError(('Unreviewed compact island',name))
        old=list(struct.unpack('<1089H',read(layer,layout['blockdata_filepath'])))
        if len(mapping['warp_events'])!=1 or [mapping['warp_events'][0][k] for k in ('x','y')]!=[16,14] or mapping['object_events']:
            raise ValueError('Changed compact cave events')
        core=[old[(9+y)*33+9+x] for y in range(15) for x in range(15)]
        small={(x,y) for y in range(12,15) for x in range(15,18)}
        recipe=[[0x498,0x471,0x49A],[0x4A0,0x471,0x4A2],[0x4A8,0x30A9,0x4AA]]
        for dy in range(3):
            for dx in range(3):
                if core[(3+dy)*15+6+dx]!=recipe[dy][dx]:
                    raise ValueError('The small cave is not the complete reviewed object')
                core[(3+dy)*15+6+dx]=0x3115
        # Extend along the sea corridor; its perpendicular bypass keeps its
        # old width. Identical full stripes conserve every beach corner.
        candidates=[]
        for axis in ('horizontal','vertical'):
            extra=6+2*(index%3)
            sv,sw,sh=stretch(core,15,15,7,extra if axis=='horizontal' else 0,
                             7,extra if axis=='vertical' else 0)
            for shift in (index%3-1,0,-1,1):
                ox=9-(extra//2 if axis=='horizontal' else 0)+(shift if axis=='horizontal' else 0)
                oy=9-(extra//2 if axis=='vertical' else 0)+(shift if axis=='vertical' else 0)
                cells={(ox+x,oy+y) for y in range(sh) for x in range(sw) if sv[y*sw+x]!=0x112B}
                if any(not(2<=x<31 and 2<=y<31) or (old[y*33+x]&0xC00 and (x,y) not in small) for x,y in cells):
                    continue
                candidates.append((axis,shift,sv,sw,sh,ox,oy,cells))
        if not candidates:
            raise ValueError(('No whole island expansion preserves reef limits',name))
        # Use the route orientation that permits the larger real dry footprint.
        horizontal_reefs=sum(bool(old[y*33+x]&0xC00) for y in (5,26) for x in range(33))
        vertical_reefs=sum(bool(old[y*33+x]&0xC00) for x in (5,26) for y in range(33))
        preferred='horizontal' if horizontal_reefs>vertical_reefs else 'vertical'
        chosen=next((r for r in candidates if r[0]==preferred),candidates[0])
        axis,shift,sv,sw,sh,ox,oy,cells=chosen
        new=old.copy()
        for y in range(sh):
            for x in range(sw):
                if sv[y*sw+x]!=0x112B:
                    new[(oy+y)*33+ox+x]=sv[y*sw+x]
        # Remove the complete old object even where a stretched stripe moved
        # its former centre; never leave one of its corners behind.
        for x,y in small:
            new[y*33+x]=0x3115
        entrance=[16,17]
        for dx,dy,word in mountain:
            x,y=entrance[0]+dx,entrance[1]+dy
            if (x,y) not in cells:
                raise ValueError(('Large mountain exceeds its island',name,x,y))
            new[y*33+x]=word
        changed=[i for i,(a,b) in enumerate(zip(old,new)) if a!=b]
        if any(old[i]&0xC00 and (i%33,i//33) not in small for i in changed):
            raise ValueError('A reef boundary was overwritten')
        row=chunks[name]
        before=copy.deepcopy(row)
        water={(x,y) for y,a,b in row['water_runs'] for x in range(a,b)
               if not new[y*33+x]&0xC00 and new[y*33+x]>>12==1}
        row['water_runs']=runs(water,33,33)
        row['whole_component_preserved']=False
        row['authored_cave_redesign']=dict(complete_native_mountain_cells=81,
            shoreline_extended_only_by_identical_whole_stripes=True,old_small_cave_removed_whole=True)
        row['global_anchor']=[row['origin'][0]+entrance[0],row['origin'][1]+entrance[1]]
        if [v//8 for v in row['global_anchor']]!=row['fixed_atlas']:
            raise ValueError('Cave entrance moved off its fixed atlas pixel')
        mapping['warp_events'][0].update(x=entrance[0],y=entrance[1])
        layer.stage(f'data/maps/{name}/map.json',json.dumps(mapping,indent=2)+'\n')
        raw=struct.pack('<1089H',*new)
        layer.stage(layout['blockdata_filepath'],raw)
        # Persisted direct positions need a same-mode local refuge once only.
        dry={i for i,v in enumerate(new) if not v&0xC00 and v>>12==3 and (i%33,i//33)!=tuple(entrance)}
        wet={y*33+x for x,y in water}
        for i in changed:
            if old[i]&0xC00:
                continue
            surfing=old[i]>>12==1
            if not new[i]&0xC00 and (new[i]>>12==1)==surfing:
                continue
            options=wet if surfing else dry
            if not options:
                raise ValueError('No same-mode old-save refuge')
            x,y=i%33,i//33
            dest=min(options,key=lambda j:(abs(j%33-x)+abs(j//33-y),abs(j%33-16),-j//33))
            rescues.append(dict(map=mapping['id'],from_tile=[x,y],to_tile=[dest%33,dest//33],surfing=surfing))
        reports.append(dict(map=name,axis=axis,asymmetric_shift=shift,shoreline_dimensions=[sw,sh],
            old_entrance=[16,14],entrance=entrance,old_small_object_cells=9,
            complete_mountain_cells=81,mountain_cells=mountain,
            fixed_atlas=row['fixed_atlas'],all_reef_cells_and_connection_mouths_preserved=True,
            changed_cells=[[i%33,i//33,old[i],new[i]] for i in changed],
            previous_native_stamp_evidence=before,blockdata_sha256=hashlib.sha256(raw).hexdigest()))
    return dict(maps=reports,save_rescues=rescues,source_audited=False,native_validated=False)


def stage_save_rescues(layer,report):
    path='src/load_save.c'
    text=read(layer,path).decode()
    signature='static void JourneyMigrateSeviiSaveGeometry(void)\n{'
    body=_braced(text,text.index(signature)+len(signature)-1)
    anchor='    JourneyMigrateSeviiSaveGeometryVersion7();'
    if body.count(anchor)!=1 or '>=8' not in body:
        raise ValueError('Expected the new version8 wrapper')
    rows=[]
    for row in report['save_rescues']:
        name=row['map'];x,y=row['from_tile'];tx,ty=row['to_tile']
        rows.append(f'{{(MAP_GROUP({name})<<8)|MAP_NUM({name}),{x},{y},{tx},{ty}}},')
    helper='''static void JourneyRescueExpandedCavePositions(void)
{
    static const struct {u16 map;u8 x,y,toX,toY;} rescues[]={
ROWS
    };
    struct WarpData *warps[]={&gSaveBlock1Ptr->continueGameWarp,&gSaveBlock1Ptr->dynamicWarp,
        &gSaveBlock1Ptr->lastHealLocation,&gSaveBlock1Ptr->escapeWarp};
    u16 packed=((u16)(u8)gSaveBlock1Ptr->location.mapGroup<<8)|(u8)gSaveBlock1Ptr->location.mapNum;
    u32 r,j;
    for(j=0;j<ARRAY_COUNT(warps);j++)
        for(r=0;r<ARRAY_COUNT(rescues);r++)
            if(warps[j]->warpId<0 && (((u16)(u8)warps[j]->mapGroup<<8)|(u8)warps[j]->mapNum)==rescues[r].map
             && warps[j]->x==rescues[r].x && warps[j]->y==rescues[r].y)
            {warps[j]->x=rescues[r].toX;warps[j]->y=rescues[r].toY;break;}
    for(r=0;r<ARRAY_COUNT(rescues);r++)
    {
        s16 dx,dy;
        if(packed!=rescues[r].map || gSaveBlock1Ptr->pos.x!=rescues[r].x || gSaveBlock1Ptr->pos.y!=rescues[r].y) continue;
        dx=rescues[r].toX-gSaveBlock1Ptr->pos.x;dy=rescues[r].toY-gSaveBlock1Ptr->pos.y;
        gSaveBlock1Ptr->pos.x=rescues[r].toX;gSaveBlock1Ptr->pos.y=rescues[r].toY;
        gSaveBlock1Ptr->location.x=rescues[r].toX;gSaveBlock1Ptr->location.y=rescues[r].toY;
        gSaveBlock1Ptr->location.warpId=-1;
        for(j=0;j<OBJECT_EVENTS_COUNT;j++)
        {
            struct ObjectEvent *object=&gSaveBlock1Ptr->objectEvents[j];
            if(!object->isPlayer && object->localId!=OBJ_EVENT_ID_FOLLOWER && object->localId!=OBJ_EVENT_ID_NPC_FOLLOWER) continue;
            object->initialCoords.x+=dx;object->currentCoords.x+=dx;object->previousCoords.x+=dx;
            object->initialCoords.y+=dy;object->currentCoords.y+=dy;object->previousCoords.y+=dy;
            if(object->isPlayer)
            {
                object->initialCoords.x=object->currentCoords.x=object->previousCoords.x=gSaveBlock1Ptr->pos.x+MAP_OFFSET;
                object->initialCoords.y=object->currentCoords.y=object->previousCoords.y=gSaveBlock1Ptr->pos.y+MAP_OFFSET;
            }
        }
#if FNPC_ENABLE_NPC_FOLLOWERS
        if(gSaveBlock3Ptr->NPCfollower.inProgress)
        {gSaveBlock3Ptr->NPCfollower.log.x+=dx;gSaveBlock3Ptr->NPCfollower.log.y+=dy;}
#endif
        break;
    }
}
'''.replace('ROWS','\n'.join(rows))
    updated=body.replace(anchor,anchor+'\n    JourneyRescueExpandedCavePositions();',1)
    layer.stage(path,text.replace(signature+body+'}',helper+'\n'+signature+updated+'}',1))
