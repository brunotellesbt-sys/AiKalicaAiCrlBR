"""Version4 refresh for changed NPCs and scenery, retaining the C8 geometry.

This batch does not move a single old traversable cell or change a map ID.
Only versions0/1/2 need the existing, unchanged geometry migration to C8.
"""
import re
from badge_story_layer import read
from atlas_surf_reachability import _function_body
from render_sea_maps import _braced


def wrapper(identities,rescues=()):
    rows=sorted(set(identities))
    if not rows or any(type(i) is not int or not 0<=i<0x8080 for i in rows):
        raise ValueError('Explicit changed map identities are required')
    rescue_code=''
    if rescues:
        rescue_code='''
    // An old save may stand on a newly added swimmer. Move one lateral
    // tile inside its authenticated three-wide Surf corridor, once only.
    {
        static const struct {u16 map;u8 x,y;s8 dx,dy;} rescues[]={'''+','.join(
            '{'+','.join(map(str,row))+'}' for row in sorted(rescues))+'''};
        struct WarpData *warps[]={&gSaveBlock1Ptr->continueGameWarp,&gSaveBlock1Ptr->dynamicWarp,
            &gSaveBlock1Ptr->lastHealLocation,&gSaveBlock1Ptr->escapeWarp};
        u32 r,j;
        for(r=0;r<ARRAY_COUNT(rescues);r++)
        {
            for(j=0;j<ARRAY_COUNT(warps);j++)
                if(warps[j]->warpId<0 && (((u16)(u8)warps[j]->mapGroup<<8)|(u8)warps[j]->mapNum)==rescues[r].map
                 && warps[j]->x==rescues[r].x && warps[j]->y==rescues[r].y)
                {warps[j]->x+=rescues[r].dx;warps[j]->y+=rescues[r].dy;}
            if(packed!=rescues[r].map || gSaveBlock1Ptr->pos.x!=rescues[r].x || gSaveBlock1Ptr->pos.y!=rescues[r].y) continue;
            gSaveBlock1Ptr->pos.x+=rescues[r].dx;gSaveBlock1Ptr->pos.y+=rescues[r].dy;
            gSaveBlock1Ptr->location.x=gSaveBlock1Ptr->pos.x;gSaveBlock1Ptr->location.y=gSaveBlock1Ptr->pos.y;
            gSaveBlock1Ptr->location.warpId=-1;
            for(j=0;j<OBJECT_EVENTS_COUNT;j++)
            {
                struct ObjectEvent *object=&gSaveBlock1Ptr->objectEvents[j];
                if(!object->isPlayer && object->localId!=OBJ_EVENT_ID_FOLLOWER && object->localId!=OBJ_EVENT_ID_NPC_FOLLOWER) continue;
                object->initialCoords.x+=rescues[r].dx;object->currentCoords.x+=rescues[r].dx;object->previousCoords.x+=rescues[r].dx;
                object->initialCoords.y+=rescues[r].dy;object->currentCoords.y+=rescues[r].dy;object->previousCoords.y+=rescues[r].dy;
                if(object->isPlayer)
                {
                    object->initialCoords.x=object->currentCoords.x=object->previousCoords.x=gSaveBlock1Ptr->pos.x+MAP_OFFSET;
                    object->initialCoords.y=object->currentCoords.y=object->previousCoords.y=gSaveBlock1Ptr->pos.y+MAP_OFFSET;
                }
            }
#if FNPC_ENABLE_NPC_FOLLOWERS
            if(gSaveBlock3Ptr->NPCfollower.inProgress)
            {gSaveBlock3Ptr->NPCfollower.log.x+=rescues[r].dx;gSaveBlock3Ptr->NPCfollower.log.y+=rescues[r].dy;}
#endif
            break;
        }
    }
'''
    return '''
static void JourneyMigrateSeviiSaveGeometry(void)
{
    static const u16 changedMaps[]={'''+','.join(map(str,rows))+'''};
    u16 version=VarGet(VAR_JOURNEY_SEVII_GEOMETRY_VERSION);
    u16 packed;
    u32 i;
    if(version>=4) return;
    JourneyMigrateSeviiSaveGeometryVersion3();
    packed=((u16)(u8)gSaveBlock1Ptr->location.mapGroup<<8)|(u8)gSaveBlock1Ptr->location.mapNum;
'''+rescue_code+'''    for(i=0;i<ARRAY_COUNT(changedMaps);i++)
        if(changedMaps[i]==packed)
        {
            u32 j;
            for(j=0;j<OBJECT_EVENTS_COUNT;j++)
                if(!gSaveBlock1Ptr->objectEvents[j].isPlayer
                 && gSaveBlock1Ptr->objectEvents[j].localId!=OBJ_EVENT_ID_FOLLOWER
                 && gSaveBlock1Ptr->objectEvents[j].localId!=OBJ_EVENT_ID_NPC_FOLLOWER)
                    gSaveBlock1Ptr->objectEvents[j].active=FALSE;
            CpuFill16(0,gSaveBlock1Ptr->objectEventTemplates,sizeof(gSaveBlock1Ptr->objectEventTemplates));
            gSaveBlock1Ptr->mapLayoutId=Overworld_GetMapHeaderByGroupAndId(packed>>8,packed&255)->mapLayoutId;
            sJourneyAtlasReloadSavedObjects=TRUE;
            break;
        }
    CpuFill16(0,gSaveBlock1Ptr->mapView,sizeof(gSaveBlock1Ptr->mapView));
    VarSet(VAR_JOURNEY_SEVII_GEOMETRY_VERSION,4);
}
'''


def stage(layer,changed_maps,identities,*,trainers=()):
    path='src/load_save.c';text=read(layer,path).decode()
    signature='static void JourneyMigrateSeviiSaveGeometry(void)\n{'
    body=_function_body(text,'JourneyMigrateSeviiSaveGeometry')
    old=signature+_braced(text,text.index(signature)+len(signature)-1)+'}'
    if text.count(old)!=1 or 'if (version >= 3)' not in body or 'VarSet(VAR_JOURNEY_SEVII_GEOMETRY_VERSION,3);' not in body:
        raise ValueError('Preserve the exact existing version3 restore wrapper')
    rows=[identities[n] for n in changed_maps]
    rescues=[(identities[r['map']],*r['tile'],-r['delta'][1],r['delta'][0]) for r in trainers]
    new=old.replace(signature,'static void JourneyMigrateSeviiSaveGeometryVersion3(void)\n{',1)+wrapper(rows,rescues)
    layer.stage(path,text.replace(old,new,1))
    path='include/constants/vars.h';text=read(layer,path).decode()
    text,n=re.subn(r'(#define\s+JOURNEY_SEVII_GEOMETRY_VERSION_CURRENT\s+)3\b',r'\g<1>4',text)
    if n!=1:raise ValueError('Expected exact version3 constant')
    layer.stage(path,text)
    return dict(version=4,changed_template_maps=sorted(changed_maps),
        new_swimmer_overlap_rescues=len(rescues),
        previous_geometry_and_numeric_identities_unchanged=True,previous_version3_migration_retained=True,
        capture_and_story_flags_unchanged=True,old_battery_native_validation_pending=True)
