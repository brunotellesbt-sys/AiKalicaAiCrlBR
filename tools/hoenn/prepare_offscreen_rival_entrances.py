"""Keep rival facing consistent and approach from outside the actual camera."""
import argparse,json,re
from pathlib import Path
from candidate_layer import Layer
from prepare_diglett_scout_battles import PRIOR,LAYER as PREVIOUS
LAYER='offscreen-rival-entrances';PRIOR=PRIOR+[PREVIOUS]
def prepare(source):
 layer=Layer(source,LAYER,PRIOR)
 if old:=layer.existing():return old
 s=layer.source
 p='src/data/object_events/object_event_anims.h';t=(s/p).read_text();table=re.search(r'static const union AnimCmd \*const sAnimTable_Standard\[\] = \{.*?\n\};',t,re.S)[0];extra=[]
 for direction in ['West','East']:
  for speed in ['','Fast','Faster','Fastest']:
   name='sAnim_Go'+speed+direction;pattern=r'static const union AnimCmd '+name+r'\[\] =\s*\{.*?\n\};';body=re.search(pattern,t,re.S)[0];clone=name+'_JourneyRivals';body=body.replace(name,clone)
   body,n=re.subn(r'ANIMCMD_FRAME\(8, (\d+)(?:, \.hFlip = TRUE)?\)',lambda m:'ANIMCMD_FRAME(8, '+m[1]+(', .hFlip = TRUE' if direction=='West' else '')+')',body);assert n==1
   extra.append(body);table=re.sub(r'\b'+name+r'\b',clone,table)
 table=table.replace('sAnimTable_Standard','sAnimTable_JourneyRivals');layer.stage(p,t+'\n'+'\n'.join(extra)+'\n'+table+'\n')
 p='src/data/object_events/object_event_pic_tables.h';t=(s/p).read_text();pinfo='src/data/object_events/object_event_graphics_info.h';info=(s/pinfo).read_text();avatars=[]
 for name in ['EREN','LUFFY','PWTEREN','PWTLUFFY']:
  prefix='gObjectEventPic_Journey'+name;needle='static const struct SpriteFrameImage sPicTable_Journey'+name+'[] = { overworld_ascending_frames('+prefix+', 2, 4) };';assert t.count(needle)==1
  # Existing index 2 was a front pose. Use the existing left-facing idle.
  mapping=[0,1,7,3,4,5,6,7,8]
  t=t.replace(needle,'static const struct SpriteFrameImage sPicTable_Journey'+name+'[] = { '+', '.join('overworld_frame('+prefix+', 2, 4, '+str(i)+')' for i in mapping)+' };')
  pattern=r'(const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_Journey'+name+r' = \{[^\n]*?\.anims=?)sAnimTable_Standard'
  # Original PWT declarations include a space after '='.
  pattern=r'(const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_Journey'+name+r' = \{[^\n]*?\.anims\s*=\s*)sAnimTable_Standard'
  info,n=re.subn(pattern,r'\1sAnimTable_JourneyRivals',info);assert n==1,name;avatars.append(name)
 layer.stage(p,t);layer.stage(pinfo,info)
 p='src/journey_crossover.c';t=(s/p).read_text().replace('#include "global.h"','#include "global.h"\n#include "malloc.h"\n#include "sprite.h"',1);start=t.index('bool8 JourneyCrossoverTryEncounter(void)');end=t.index('void JourneyCrossoverInfo(void)',start)
 t=t[:start]+Path(__file__).with_name('crossover_offscreen_path.c').read_text()+'\n'+t[end:];layer.stage(p,t)
 p='data/scripts/journey_crossover.inc';t=(s/p).read_text();start=t.index('JourneyCrossover_Encounter::');end=t.index('JourneyCrossover_StartBattle::',start);t=t[:start]+'JourneyCrossover_Encounter::\n\tlockall\n\tapplymovement 240, gJourneyCrossoverMovement\n'+t[end:];layer.stage(p,t)
 return layer.finish(avatars=avatars,sprite_pngs_and_palettes_unchanged=True,side_idle_source_frame=7,west_walk_frame8_mirrored=True,east_walk_frame8_not_mirrored=True,actual_camera_bounds_and_panning=True,only_fully_offscreen_spawns=True,path_search_radius_tiles=16,path_avoids_collision_water_ledge_warps_and_npcs=True,no_visible_spawn_fallback=True,retry_after_player_moves=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);print(prepare(p.parse_args().source)['layer'])
