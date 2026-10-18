"""User-reported Dewford coast, Luffy and trainer-move corrections."""
import json
import re
import struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]


def repair(layer):
    s=layer.source
    def raw(p):return layer.outputs[p] if p in layer.outputs else (s/p).read_bytes()
    def js(p):return json.loads(raw(p))
    def put(p,value):layer.stage(p,json.dumps(value,indent=2)+'\n')
    # Keep the Frontier shop introduced in PR95; restore the requested second
    # Dewford attendant with the same native, stock-scoped battle-item menu.
    p='data/maps/Route107/map.json';m=js(p)
    assert not any(o.get('script')=='JourneyCompetitive_Seller' for o in m['object_events'])
    m['object_events'].append(dict(type='object',graphics_id='OBJ_EVENT_GFX_MART_EMPLOYEE',x=2,y=15,elevation=3,
        movement_type='MOVEMENT_TYPE_FACE_DOWN',movement_range_x=0,movement_range_y=0,trainer_type='TRAINER_TYPE_NONE',trainer_sight_or_berry_tree_id='0',script='JourneyCompetitive_Seller',flag='0'))
    put(p,m)
    for name in ['journey_luffy','journey_pwt_luffy']:
        layer.stage('graphics/object_events/pics/people/'+name+'.png',(ROOT/'tools/hoenn/data/luffy-overworld.png').read_bytes())
        layer.stage('graphics/object_events/pics/people/'+name+'.pal',(ROOT/'tools/hoenn/data/luffy-overworld.pal').read_bytes())
    p='src/data/object_events/object_event_pic_tables.h';t=raw(p).decode()
    for name in ['LUFFY','PWTLUFFY']:
        pattern=r'static const struct SpriteFrameImage sPicTable_Journey'+name+r'\[\] = \{[^\n]+\};'
        t,count=re.subn(pattern,'static const struct SpriteFrameImage sPicTable_Journey'+name+'[] = { overworld_ascending_frames(gObjectEventPic_Journey'+name+', 2, 4) };',t)
        assert count==1,name
    layer.stage(p,t)
    p='src/data/object_events/object_event_graphics_info.h';t=raw(p).decode()
    for name in ['LUFFY','PWTLUFFY']:
        pattern=r'(gObjectEventGraphicsInfo_Journey'+name+r' = \{[^\n]*?\.anims\s*=\s*)sAnimTable_JourneyRivals'
        t,count=re.subn(pattern,r'\1sAnimTable_Standard',t);assert count==1
    layer.stage(p,t)
    # Preserve the species database: the modern Solrock learnset legitimately
    # contains Flare Blitz. The requested change is to trainer loadouts only.
    p='src/battle_main.c';t=raw(p).decode();anchor='            CustomTrainerPartyAssignMoves(&party[i], &partyData[monIndex]);'
    assert t.count(anchor)==1;t=t.replace(anchor,anchor+'\n            JourneySolrockTrainerMoves(&party[i]);')
    t=t.replace('#include "global.h"','#include "global.h"\nvoid JourneySolrockTrainerMoves(struct Pokemon *mon);',1)
    layer.stage(p,t)
    layer.stage('src/journey_coastal_fixes.c','''#include "global.h"
#include "pokemon.h"
#include "move.h"
#include "constants/species.h"
#include "constants/moves.h"
#include "constants/pokemon.h"
void JourneySolrockTrainerMoves(struct Pokemon *mon)
{
    u32 slot, j, i, best, level;
    const struct LevelUpMove *learnset;
    if (GetMonData(mon, MON_DATA_SPECIES) != SPECIES_SOLROCK) return;
    level = GetMonData(mon, MON_DATA_LEVEL);
    learnset = GetSpeciesLevelUpLearnset(SPECIES_SOLROCK);
    for (slot = 0; slot < MAX_MON_MOVES; slot++)
    {
        u16 replacement = MOVE_HARDEN;
        if (GetMonData(mon, MON_DATA_MOVE1 + slot) != MOVE_FLARE_BLITZ) continue;
        best = 0;
        for (i = 0; learnset[i].move != LEVEL_UP_MOVE_END; i++)
        {
            u16 move = learnset[i].move;
            bool32 duplicate = FALSE;
            if (learnset[i].level > level || gMovesInfo[move].power < 2
                || (gMovesInfo[move].type != TYPE_ROCK && gMovesInfo[move].type != TYPE_PSYCHIC)) continue;
            for (j = 0; j < MAX_MON_MOVES; j++)
                if (GetMonData(mon, MON_DATA_MOVE1 + j) == move) duplicate = TRUE;
            if (!duplicate && gMovesInfo[move].power > best)
            { best = gMovesInfo[move].power; replacement = move; }
        }
        SetMonMoveSlot(mon, replacement, slot);
    }
}
''')
    # Walking ashore changes the avatar state before the map ID can change.
    # A cache invalidation conditional on Surf leaves old secondary-bank IDs
    # behind on foot. Refresh on every primary OR secondary bank change.
    p='src/fieldmap.c';t=raw(p).decode();before='''        if (gPlayerAvatar.flags & PLAYER_AVATAR_FLAG_SURFING)
        {
            const struct MapLayout *next = GetMapHeaderFromConnection(connection)->mapLayout;
            freshCoastView |= next->primaryTileset != gMapHeader.mapLayout->primaryTileset
                           || next->secondaryTileset != gMapHeader.mapLayout->secondaryTileset;
        }'''
    after='''        {
            const struct MapLayout *next = GetMapHeaderFromConnection(connection)->mapLayout;
            freshCoastView |= next->primaryTileset != gMapHeader.mapLayout->primaryTileset
                           || next->secondaryTileset != gMapHeader.mapLayout->secondaryTileset
                           || gSaveBlock1Ptr->location.mapGroup >= MAP_GROUP(MAP_JOURNEYSURFLINK00000)
                           || connection->mapGroup >= MAP_GROUP(MAP_JOURNEYSURFLINK00000);
        }'''
    assert t.count(before)==1;layer.stage(p,t.replace(before,after))
    # Imported low piers connect to ordinary elevation-3 land. Multi-level
    # bridge tiles must retain that collision level, while drawing pedestrians
    # above their top layer. Surf objects retain elevation 1 and stay below it.
    p='src/event_object_movement.c';t=raw(p).decode()
    anchor='static void UpdateObjectEventElevationAndPriority(struct ObjectEvent *objEvent, struct Sprite *sprite)\n{'
    assert t.count(anchor)==1
    t=t.replace(anchor,anchor+'\n    u8 displayElevation;')
    before='    sprite->subspriteTableNum = sElevationToSubspriteTableNum[objEvent->previousElevation];\n    sprite->oam.priority = sElevationToPriority[objEvent->previousElevation];'
    after='    displayElevation = objEvent->previousElevation;\n    if (displayElevation == ELEVATION_DEFAULT\n        && MapGridGetElevationAt(objEvent->currentCoords.x, objEvent->currentCoords.y) == ELEVATION_MULTI_LEVEL\n        && MetatileBehavior_IsBridgeOverWater(objEvent->currentMetatileBehavior))\n        displayElevation = 4;\n    sprite->subspriteTableNum = sElevationToSubspriteTableNum[displayElevation];\n    sprite->oam.priority = sElevationToPriority[displayElevation];'
    assert t.count(before)==1;layer.stage(p,t.replace(before,after))
    # The old cave crown accidentally used a metatile with a vertical water
    # channel. Use a continuous native rock centre and retain the same door.
    ld=js('data/layouts/layouts.json');ls={l['id']:l for l in ld['layouts']};caves=[]
    names={q['surface'] for q in js('.journey-sanctuaries')['sites'] if q['access']=='surf'}
    names.update(q['surface'] for q in js('.journey-surf-review')['branches'])
    for name in sorted(names):
        m=js(f'data/maps/{name}/map.json');l=ls[m['layout']]
        if l['layout_version']!='frlg':continue
        p=l['blockdata_filepath'];b=raw(p);v=list(struct.unpack('<'+'H'*(len(b)//2),b));changed=[]
        for i,tile in enumerate(v):
            if tile not in [0x499,0x4A1]:continue
            # Match complete three-by-three cave shells, never native cliffs.
            w=l['width'];above=i-w if tile==0x4A1 else i
            if above%w==0 or above%w==w-1:continue
            if v[above-1]&1023!=0x98 or v[above+1]&1023!=0x9A:continue
            if above+2*w>=len(v) or v[above+2*w]&1023!=0xA9:continue
            v[above]=0x471;v[above+w]=0x471;changed.append([above%w,above//w])
        if changed:layer.stage(p,struct.pack('<'+'H'*len(v),*v));caves.append(dict(map=name,repaired_crowns=changed))
    # Restore the native southern terrain requested by the author. Keep the
    # original twenty-row town/route and their native border tiles; do not
    # expose the forest edge by adding ocean underneath it. The two sellers
    # above remain independent of this terrain restoration.
    import hashlib
    dewford_edges=[]
    for name in ['DewfordTown','Route107']:
        m=js(f'data/maps/{name}/map.json');l=ls[m['layout']];w,h=l['width'],l['height'];assert h==20
        terrain=raw(l['blockdata_filepath'])
        south=struct.unpack('<'+'H'*(4*w),terrain[-4*w*2:])
        dewford_edges.append(dict(map=name,old_height=20,new_height=20,native_southern_terrain_restored=True,
            original_border_retained=True,southern_art_and_elevations_sha256=hashlib.sha256(struct.pack('<'+'H'*(4*w),*[t&~0xc00 for t in south])).hexdigest(),
            border_sha256=hashlib.sha256(raw(l['border_filepath'])).hexdigest()))
    put('data/layouts/layouts.json',ld)
    from repair_surf_geometry import repair as repair_geometry
    geography=repair_geometry(layer)
    return dict(dewford_attendants=2,frontier_shop_preserved=True,luffy_frames=9,luffy_visible_height=28,
        luffy_standard_directional_animation=True,solrock_trainer_flare_blitz_removed=True,
        solrock_species_database_preserved=True,bank_cache_refreshed_on_foot_and_surf=True,
        cave_crowns=caves,dewford_coast=dewford_edges,geography=geography)
