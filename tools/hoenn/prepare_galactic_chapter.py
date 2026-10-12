"""Integrate the underwater Galactic prison, tag battles and both League gates."""
import argparse,copy,hashlib,json,re,struct
from pathlib import Path
from prepare_crossover_partners import PRIOR,LAYER as PREVIOUS
ROOT=Path(__file__).resolve().parents[2];LAYER='galactic-chapter';PRIOR=PRIOR+[PREVIOUS]
def prepare(source):
 source=Path(source);marker=source/('.journey-'+LAYER)
 if marker.exists():
  r=json.loads(marker.read_text())
  for p,h in r['prepared_sha256'].items():assert hashlib.sha256((source/p).read_bytes()).hexdigest()==h,p
  return r
 expected=dict(json.loads((source/'.source-acquired.json').read_text())['sha256'])
 for layer in PRIOR:expected.update(json.loads((source/('.journey-'+layer)).read_text())['prepared_sha256'])
 outputs={};originals={}
 def stage(p,raw):
  old=(source/p).read_bytes() if (source/p).exists() else None;h=hashlib.sha256(old).hexdigest() if old else None;assert h==expected.get(p),p
  if h:originals[p]=h
  outputs[p]=raw.encode() if isinstance(raw,str) else raw
 def js(p,r):stage(p,json.dumps(r,indent=2)+'\n')
 groups=json.loads((source/'data/maps/map_groups.json').read_text());group=next(g for g in groups['group_order'] if 'JourneyParadoxPast' in groups[g]);groups[group].append('JourneyGalacticHall');js('data/maps/map_groups.json',groups)
 layouts=json.loads((source/'data/layouts/layouts.json').read_text());li={l['id']:l for l in layouts['layouts']}
 floor=0x3238;w=31;h=37;blocks=[floor]*(w*h)
 for y in range(h):
  for x in range(w):
   if x==0 or x==w-1 or y==h-1:blocks[y*w+x]=0x063f
   elif y==0:blocks[y*w+x]=0x0627
   elif y==1:blocks[y*w+x]=0x062f
 for y in [8,16,24]:
  for x in list(range(3,10))+list(range(21,28)):blocks[y*w+x]=0x062f
 for y in range(3,31):
  if y in [6,7,14,15,22,23,29,30]:continue
  for x in [3,9,21,27]:blocks[y*w+x]=0x063f
 # Central aisle stays open; native exit tiles lead to the hidden sixth cabin.
 origin=json.loads((source/'data/maps/AbandonedShip_HiddenFloorRooms/map.json').read_text());oldlayout=li[origin['layout']];raw=(source/oldlayout['blockdata_filepath']).read_bytes();oldblocks=struct.unpack('<'+'H'*(len(raw)//2),raw);exitTile=oldblocks[14*44+6]
 blocks[35*w+15]=exitTile
 layout=dict(id='LAYOUT_JOURNEYGALACTICHALL',name='JourneyGalacticHall_Layout',width=w,height=h,primary_tileset='gTileset_General',secondary_tileset='gTileset_JourneyGalacticShip',border_filepath='data/layouts/JourneyGalacticHall/border.bin',blockdata_filepath='data/layouts/JourneyGalacticHall/map.bin',layout_version='emerald')
 layouts['layouts'].append(layout);js('data/layouts/layouts.json',layouts);stage(layout['border_filepath'],struct.pack('<4H',*([0x063f]*4)));stage(layout['blockdata_filepath'],struct.pack('<'+'H'*len(blocks),*blocks))
 # Reuse native ship graphics with a cool underwater/space-prison palette.
 palettes=[]
 for i in range(16):
  text=(source/f'data/tilesets/secondary/inside_ship/palettes/{i:02}.pal').read_text();lines=text.splitlines();out=lines[:3]
  for line in lines[3:]:
   r,g,b=map(int,line.split());lum=(r+g+b)//3
   out.append(f'{round(lum*.62)} {min(255,round(lum*.88))} {min(255,round(lum*1.12))}')
  path=f'data/tilesets/secondary/journey_galactic_ship/palettes/{i:02}.pal';stage(path,'\n'.join(out)+'\n');palettes.append(path.removesuffix('.pal')+'.gbapal')
 p='src/data/tilesets/graphics.h';stage(p,(source/p).read_text()+'\nconst u16 gTilesetPalettes_JourneyGalacticShip[][16] = {\n'+''.join(' INCBIN_U16("'+p+'"),\n' for p in palettes)+'};\n')
 p='src/data/tilesets/headers.h';stage(p,(source/p).read_text()+'\nconst struct Tileset gTileset_JourneyGalacticShip={.isCompressed=TRUE,.isSecondary=TRUE,.tiles=gTilesetTiles_InsideShip,.palettes=gTilesetPalettes_JourneyGalacticShip,.metatiles=gMetatiles_InsideShip,.metatileAttributes=gMetatileAttributes_InsideShip,.callback=NULL};\n')
 p='include/tilesets.h';stage(p,(source/p).read_text().replace('#endif','extern const struct Tileset gTileset_JourneyGalacticShip;\n#endif'))
 p='include/constants/vars.h';stage(p,(source/p).read_text()+'\n#define VAR_JOURNEY_GALACTIC_STATE 0x40FE\n#define VAR_JOURNEY_CROSSOVER_VISITS 0x40FF\n')
 hall=copy.deepcopy(origin);hall.update(id='MAP_JOURNEYGALACTICHALL',name='JourneyGalacticHall',layout=layout['id'],music='MUS_ABANDONED_SHIP',object_events=[],warp_events=[dict(x=15,y=35,elevation=3,dest_map=origin['id'],dest_warp_id='255')],coord_events=[],bg_events=[],connections=None)
 # Set return coordinates directly via a transition script, because the new
 # cabin entrance is an interactive bulkhead rather than a second room exit.
 hall['warp_events'][0]=dict(x=15,y=35,elevation=3,dest_map=origin['id'],dest_warp_id='10')
 assert origin['warp_events'], 'Hidden cabin must retain its native exits'
 # Sixth cabin's original two exits are indices 10/11 and lead to its corridor.
 # Add a dedicated reciprocal door inside that cabin instead of changing them.
 hall['warp_events'][0]['dest_warp_id']=str(len(origin['warp_events']))
 origin['warp_events'].append(dict(x=36,y=3,elevation=3,dest_map=hall['id'],dest_warp_id='0'))
 # This tile is not a warp metatile: only the gate NPC calls the entrance warp.
 def actor(gfx,x,y,script,localid=None,trainer=False):
  row=dict(graphics_id=gfx,x=x,y=y,elevation=3,movement_type='MOVEMENT_TYPE_FACE_DOWN',movement_range_x=0,movement_range_y=0,trainer_type='TRAINER_TYPE_NORMAL' if trainer else 'TRAINER_TYPE_NONE',trainer_sight_or_berry_tree_id='3' if trainer else '0',script=script,flag='0')
  if localid:row['local_id']=localid
  return row
 origin['object_events'].append(actor('OBJ_EVENT_GFX_JOURNEY_GALACTIC_GRUNT_M',37,3,'JourneyGalactic_Gate'))
 js('data/maps/AbandonedShip_HiddenFloorRooms/map.json',origin)
 for n,gfx,x,y,script in [(1,'CYRUS',15,6,'JourneyGalactic_Cyrus'),(2,'MARS',12,12,'JourneyGalactic_Observer'),(3,'JUPITER',18,19,'JourneyGalactic_Observer'),(4,'SATURN',12,19,'JourneyGalactic_Observer'),(5,'CHARON',18,12,'JourneyGalactic_Observer'),(6,'EREN',10,26,'JourneyGalactic_Observer'),(7,'LUFFY',20,26,'JourneyGalactic_Observer')]:hall['object_events'].append(actor('OBJ_EVENT_GFX_JOURNEY_'+gfx,x,y,script))
 for n,species,x in [(8,'DIALGA',9),(9,'PALKIA',21),(10,'GIRATINA',15)]:hall['object_events'].append(actor('OBJ_EVENT_GFX_SPECIES('+species+')',x,4,'JourneyGalactic_Observer'))
 # Relocate every original person, retaining their existing dialogue/trainer
 # scripts. Place them only on walkable land in quiet stretches of routes.
 routes=['Route18_Frlg','Route16_Frlg','Route9_Frlg','Route112','Route113'];routeMaps={n:json.loads((source/'data/maps'/n/'map.json').read_text()) for n in routes};relocated=[];grunts=[]
 def placement(m):
  l=li[m['layout']];a=struct.unpack('<'+'H'*(l['width']*l['height']),(source/l['blockdata_filepath']).read_bytes());used={(o['x'],o['y']) for o in m['object_events']}|{(o['x'],o['y']) for o in m['warp_events']+m['coord_events']}
  anchors=[(o['x'],o['y']) for o in m['object_events'] if o['graphics_id']!='OBJ_EVENT_GFX_ITEM_BALL']
  for distance in range(2,9):
   for ax,ay in anchors:
    for dx,dy in [(distance,0),(-distance,0),(0,distance),(0,-distance)]:
     x,y=ax+dx,ay+dy
     if 1<=x<l['width']-1 and 1<=y<l['height']-1 and (x,y) not in used:
      tile=a[y*l['width']+x]
      if (tile>>10)&3==0 and tile>>12 in [3,4]:return x,y,tile>>12
  raise ValueError('No uncrowded land position in '+m['name'])
 for path in sorted((source/'data/maps').glob('AbandonedShip*/map.json')):
  if path.parent.name=='AbandonedShip_HiddenFloorRooms':continue
  m=json.loads(path.read_text());changed=False
  for idx,o in enumerate(m['object_events']):
   if o['graphics_id']=='OBJ_EVENT_GFX_ITEM_BALL':continue
   destination=routes[len(relocated)%len(routes)];rm=routeMaps[destination];x,y,elevation=placement(rm);copyrow=copy.deepcopy(o);copyrow.pop('local_id',None);copyrow.update(x=x,y=y,elevation=elevation);rm['object_events'].append(copyrow)
   relocated.append(dict(original_map=path.parent.name,script=o['script'],destination=destination,position=[x,y]))
   key='GALACTIC_GRUNT_'+str(len(grunts));gfx='GALACTIC_GRUNT_F' if len(grunts)%2 else 'GALACTIC_GRUNT_M';o.update(graphics_id='OBJ_EVENT_GFX_JOURNEY_'+gfx,script='JourneyGalactic_'+key,flag='0',trainer_type='TRAINER_TYPE_NORMAL',trainer_sight_or_berry_tree_id='3',movement_type='MOVEMENT_TYPE_FACE_DOWN');grunts.append(dict(key=key,map=path.parent.name,x=o['x'],y=o['y'],female=gfx.endswith('_F')));changed=True
  if changed:js(str(path.relative_to(source)),m)
 for n,m in routeMaps.items():assert len(m['object_events'])<=32,(n,len(m['object_events']));js('data/maps/'+n+'/map.json',m)
 for x,y in [(8,30),(22,30),(8,22),(22,22)]:
  key='GALACTIC_GRUNT_'+str(len(grunts));female=len(grunts)%2;hall['object_events'].append(actor('OBJ_EVENT_GFX_JOURNEY_GALACTIC_GRUNT_'+('F' if female else 'M'),x,y,'JourneyGalactic_'+key,trainer=True));grunts.append(dict(key=key,map='JourneyGalacticHall',x=x,y=y,female=bool(female)))
 js('data/maps/JourneyGalacticHall/map.json',hall)
 p='include/constants/opponents.h';t=(source/p).read_text();assert re.search(r'#define TRAINERS_COUNT\s+1570\b',t);t=re.sub(r'(#define TRAINERS_COUNT\s+)1570\b',r'\g<1>'+str(1570+len(grunts)),t)
 for i,g in enumerate(grunts):g['id']=1570+i;t+='\n#define TRAINER_JOURNEY_'+g['key']+' '+str(g['id'])
 stage(p,t+'\n')
 p='src/data/journey_crossover_trainers.h';t=(source/p).read_text()
 for g in grunts:
  team=['ZUBAT','GLAMEOW','CROAGUNK'] if not g['female'] else ['STUNKY','BRONZOR','GLAMEOW'];mons=','.join('{.species=SPECIES_'+n+',.lvl=40,.gender=TRAINER_MON_RANDOM_GENDER,.iv=TRAINER_PARTY_IVS(15,15,15,15,15,15),.ball=POKEBALL_COUNT,.nature=NATURE_HARDY}' for n in team)
  t+='\n[DIFFICULTY_NORMAL][TRAINER_JOURNEY_'+g['key']+']={.trainerName=_("GALACTIC"),.trainerClass=TRAINER_CLASS_PKMN_TRAINER_1,.trainerPic=TRAINER_PIC_JOURNEY_GALACTIC_GRUNT_'+('F' if g['female'] else 'M')+',.gender=TRAINER_GENDER_'+('FEMALE' if g['female'] else 'MALE')+',.encounterMusic=TRAINER_ENCOUNTER_MUSIC_MALE,.aiFlags=AI_FLAG_BASIC_TRAINER,.partySize=3,.party=(const struct TrainerMon[]){'+mons+'}},\n'
 stage(p,t)
 stage('include/journey_galactic.h','#ifndef GUARD_JOURNEY_GALACTIC_H\n#define GUARD_JOURNEY_GALACTIC_H\nbool32 JourneyGalacticLeagueReady(void);\nbool32 JourneyGalacticCaptureLocked(u32 species);\nbool32 JourneyGalacticNoCatch(void);\nvoid JourneyGalacticAvailable(void);\nvoid JourneyGalacticGruntsCleared(void);\nvoid JourneyGalacticOtherMissions(void);\n#endif\n')
 code='''#include "global.h"
#include "journey_galactic.h"
#include "journey_gym_scaling.h"
#include "journey_team_missions.h"
#include "journey_story_continuity.h"
#include "event_data.h"
#include "constants/vars.h"
#include "constants/flags.h"
#include "constants/species.h"
#include "constants/opponents.h"
#include "constants/maps.h"
bool32 JourneyGalacticLeagueReady(void) { return JourneyGymBadgeCount(TRUE)==8 && JourneyGymBadgeCount(FALSE)==8 && VarGet(VAR_JOURNEY_GALACTIC_STATE)>=7 && JourneyPendingCampaignEvent(TRUE)==0 && JourneyPendingCampaignEvent(FALSE)==0; }
void JourneyGalacticAvailable(void) { gSpecialVar_Result=JourneyGymBadgeCount(TRUE)==8 && JourneyGymBadgeCount(FALSE)==8; }
void JourneyGalacticOtherMissions(void) { gSpecialVar_Result=JourneyPendingCampaignEvent(TRUE)!=0 || JourneyPendingCampaignEvent(FALSE)!=0; }
bool32 JourneyGalacticCaptureLocked(u32 species) { return (species==SPECIES_DIALGA || species==SPECIES_PALKIA || species==SPECIES_GIRATINA || species==SPECIES_GIRATINA_ORIGIN) && VarGet(VAR_JOURNEY_GALACTIC_STATE)<7; }
bool32 JourneyGalacticNoCatch(void) { return gSaveBlock1Ptr->location.mapGroup==MAP_GROUP(MAP_JOURNEYGALACTICHALL) && gSaveBlock1Ptr->location.mapNum==MAP_NUM(MAP_JOURNEYGALACTICHALL) && VarGet(VAR_JOURNEY_GALACTIC_STATE)==3; }
void JourneyGalacticGruntsCleared(void) {
 static const u16 ids[]={GRUNT_IDS};
 gSpecialVar_Result=TRUE;
 for(u32 i=0;i<ARRAY_COUNT(ids);i++) { u16 flag=TRAINER_FLAGS_START+ids[i]; if(!(gSaveBlock1Ptr->flags[flag/8]&(1<<(flag&7))))gSpecialVar_Result=FALSE; }
}
'''.replace('GRUNT_IDS',','.join('TRAINER_JOURNEY_'+g['key'] for g in grunts))
 stage('src/journey_galactic.c',code)
 script=(ROOT/'tools/hoenn/galactic_chapter.inc').read_text()
 for label,dx,dy,count in [('AdminLeft1','right','up',4),('AdminRight1','left','up',4),('AdminLeft2','right','up',11),('AdminRight2','left','up',11)]:script+='JourneyGalactic_'+label+'::\n'+('\twalk_'+dx+'\n')*2+('\twalk_'+dy+'\n')*count+'\tstep_end\n'
 for hero,dx in [('Eren','right'),('Luffy','left')]:script+='JourneyGalactic_'+hero+'Approach::\n'+('\twalk_up\n')*18+('\twalk_'+dx+'\n')*3+'\tstep_end\n'
 for g in grunts:script+='JourneyGalactic_'+g['key']+'::\n\ttrainerbattle_single TRAINER_JOURNEY_'+g['key']+', JourneyGalactic_Text_GruntIntro, JourneyGalactic_Text_GruntDefeat\n\tmsgbox JourneyGalactic_Text_GruntAfter, MSGBOX_NPC\n\tend\n'
 script+='JourneyGalactic_Text_GruntIntro::\n\t.string "TEAM GALACTIC controls this ship!\\n"\n\t.string "You will not stop our experiment!$"\nJourneyGalactic_Text_GruntDefeat::\n\t.string "Our plans are coming apart!$"\nJourneyGalactic_Text_GruntAfter::\n\t.string "CYRUS is in the hidden prison,\\n"\n\t.string "beyond ROOM 6 in the lower floor.$"\n'
 stage('data/scripts/journey_galactic.inc',script)
 stage('data/maps/JourneyGalacticHall/scripts.inc','@ Map scripts are included in data/scripts/journey_galactic.inc.\n')
 p='data/event_scripts.s';stage(p,(source/p).read_text()+'\n\t.include "data/scripts/journey_galactic.inc"\n')
 p='data/specials.inc';stage(p,(source/p).read_text()+'\n\tdef_special JourneyGalacticAvailable\n\tdef_special JourneyGalacticGruntsCleared\n\tdef_special JourneyGalacticOtherMissions\n')
 p='src/journey_campaign_gates.c';t=(source/p).read_text().replace('#include "global.h"','#include "global.h"\n#include "journey_galactic.h"',1)
 for name in ['JourneyKantoLeaguePermission','JourneyHoennLeaguePermission']:
  needle='void '+name+'(void)\n{\n    gSpecialVar_Result = JourneyGymBadgeCount(TRUE) == 8\n        && JourneyGymBadgeCount(FALSE) == 8;\n}';assert needle in t;t=t.replace(needle,'void '+name+'(void)\n{\n    gSpecialVar_Result = JourneyGalacticLeagueReady();\n}')
 stage(p,t)
 for p,label in [('data/maps/IndigoPlateau_PokemonCenter_1F_Frlg/scripts.inc','IndigoPlateau_Journey_Denied'),('data/maps/EverGrandeCity_PokemonLeague_1F/scripts.inc','Journey_HoennLeagueSixteenBadgesDenied')]:
  t=(source/p).read_text();start=t.index(label+'::');end=t.index('\n\n',start);t=t[:start]+label+'::\n\tgoto JourneyGalactic_LeagueDenied'+t[end:];stage(p,t)
 p='src/journey_special.c';t=(source/p).read_text().replace('#include "global.h"','#include "global.h"\n#include "journey_galactic.h"',1);needle='    if(!JourneySpeciesAllowed(gSpecialVar_0x8004)){gSpecialVar_Result=0;return;}';assert needle in t;t=t.replace(needle,needle+'\n    if(JourneyGalacticCaptureLocked(gSpecialVar_0x8004)){gSpecialVar_Result=0;return;}');stage(p,t)
 p='src/item_use.c';t=(source/p).read_text().replace('#include "global.h"','#include "global.h"\n#include "journey_galactic.h"',1);needle='else if (FlagGet(B_FLAG_NO_CATCHING) || !IsAllowedToUseBag())';assert needle in t;t=t.replace(needle,'else if (JourneyGalacticNoCatch() || FlagGet(B_FLAG_NO_CATCHING) || !IsAllowedToUseBag())');stage(p,t)
 p='src/journey_crossover.c';t=(source/p).read_text().replace('#include "global.h"','#include "global.h"\n#include "journey_gym_scaling.h"',1).replace('VarGet(JOURNEY_GALACTIC_STATE)>=4','VarGet(JOURNEY_GALACTIC_STATE)>=7');needle='    PlayerGetDestCoords(&x,&y);';t=t.replace(needle,'    if (JourneyGymBadgeCount(TRUE)==8 && JourneyGymBadgeCount(FALSE)==8) return FALSE;\n'+needle);stage(p,t)
 r=dict(layer=LAYER,grunts=grunts,relocated_original_people=relocated,required_badges=16,mandatory_before_both_leagues=True,states={'0':'Mars+Charon with Eren','1':'Saturn+Jupiter with Luffy','2':'Cyrus alone','3':'Defeat uncapturable Giratina','4':'Adamant Crystal','5':'Lustrous Globe','6':'Griseous Core and farewells','7':'Complete'},original_sha256=originals,prepared_sha256={p:hashlib.sha256(raw).hexdigest() for p,raw in outputs.items()},native_validation_pending=True)
 for p,raw in outputs.items():(source/p).parent.mkdir(parents=True,exist_ok=True);(source/p).write_bytes(raw)
 marker.write_text(json.dumps(r,indent=2)+'\n');return r
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);a=p.parse_args();print(json.dumps(prepare(a.source),indent=2))
