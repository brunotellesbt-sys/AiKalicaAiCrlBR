"""Register faithful generated portraits/overworld avatars and approved rival teams."""
import argparse, hashlib, json, re
from pathlib import Path
from prepare_birth_confirmation import PRIOR, LAYER as PREVIOUS
from pack_crossover_assets import encode, NAMES
ROOT=Path(__file__).resolve().parents[2]
LAYER='crossover-opponents'; PRIOR=PRIOR+[PREVIOUS]
def prepare(source):
 source=Path(source); marker=source/('.journey-'+LAYER)
 if marker.exists():
  r=json.loads(marker.read_text())
  for p,h in r['prepared_sha256'].items(): assert hashlib.sha256((source/p).read_bytes()).hexdigest()==h,p
  return r
 expected=dict(json.loads((source/'.source-acquired.json').read_text())['sha256'])
 for layer in PRIOR:expected.update(json.loads((source/('.journey-'+layer)).read_text())['prepared_sha256'])
 outputs={}; originals={}
 def stage(p,raw):
  old=(source/p).read_bytes() if (source/p).exists() else None; h=hashlib.sha256(old).hexdigest() if old else None
  assert h==expected.get(p),p
  if h:originals[p]=h
  outputs[p]=raw.encode() if isinstance(raw,str) else raw
 assets=encode(ROOT/'.local/crossover-assets')
 for a in assets:
  n=a['name']; stage('graphics/trainers/front_pics/journey_'+n.lower()+'.png',(ROOT/'.local/crossover-assets'/a['front']).read_bytes())
  if 'overworld' in a:stage('graphics/object_events/pics/people/journey_'+n.lower()+'.png',(ROOT/'.local/crossover-assets'/a['overworld']).read_bytes())
 p='include/constants/trainers.h'; t=(source/p).read_text(); stage(p,t.replace('    TRAINER_PIC_COUNT,',''.join('    TRAINER_PIC_JOURNEY_'+n+',\n' for n in NAMES+['EREN_TITAN'])+'    TRAINER_PIC_COUNT,'))
 p='src/data/graphics/trainers.h'; t=(source/p).read_text(); start=t.index('#define TRAINER_FRONT_PIC')
 declarations=''.join('const u32 gTrainerFrontPic_Journey'+n+'[] = INCBIN_U32("graphics/trainers/front_pics/journey_'+n.lower()+'.4bpp.smol");\nconst u16 gTrainerPalette_Journey'+n+'[] = INCBIN_U16("graphics/trainers/front_pics/journey_'+n.lower()+'.gbapal");\n' for n in NAMES+['EREN_TITAN'])
 t=t[:start]+declarations+t[start:]; end=t.rindex('};');t=t[:end]+''.join('    [TRAINER_PIC_JOURNEY_'+n+'] = {.frontPic = TRAINER_FRONT_PIC(gTrainerFrontPic_Journey'+n+', gTrainerPalette_Journey'+n+')},\n' for n in NAMES+['EREN_TITAN'])+t[end:]; stage(p,t)
 p='include/constants/event_objects.h';t=(source/p).read_text().replace('    NUM_OBJ_EVENT_GFX,',''.join('    OBJ_EVENT_GFX_JOURNEY_'+n+',\n' for n in NAMES)+'    NUM_OBJ_EVENT_GFX,');t+='\n'+''.join('#define OBJ_EVENT_PAL_TAG_JOURNEY_'+n+' '+hex(0x12e0+i)+'\n' for i,n in enumerate(NAMES));stage(p,t)
 p='src/data/object_events/object_event_graphics.h'; stage(p,(source/p).read_text()+'\n'+''.join('const u32 gObjectEventPic_Journey'+n+'[] = INCBIN_U32("graphics/object_events/pics/people/journey_'+n.lower()+'.4bpp");\nconst u16 gObjectEventPal_Journey'+n+'[] = INCBIN_U16("graphics/object_events/pics/people/journey_'+n.lower()+'.gbapal");\n' for n in NAMES))
 p='src/data/object_events/object_event_pic_tables.h';stage(p,(source/p).read_text()+'\n'+''.join('static const struct SpriteFrameImage sPicTable_Journey'+n+'[] = { overworld_ascending_frames(gObjectEventPic_Journey'+n+', 2, 4) };\n' for n in NAMES))
 p='src/data/object_events/object_event_graphics_info.h';stage(p,(source/p).read_text()+'\n'+''.join('const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_Journey'+n+' = { .tileTag=TAG_NONE, .paletteTag=OBJ_EVENT_PAL_TAG_JOURNEY_'+n+', .reflectionPaletteTag=OBJ_EVENT_PAL_TAG_NONE, .size=256, .width=16, .height=32, .paletteSlot='+str(i+2)+', .shadowSize=SHADOW_SIZE_M, .inanimate=FALSE, .compressed=FALSE, .tracks=TRACKS_FOOT, .oam=&gObjectEventBaseOam_16x32, .subspriteTables=sOamTables_16x32, .anims=sAnimTable_Standard, .images=sPicTable_Journey'+n+' };\n' for i,n in enumerate(NAMES)))
 p='src/data/object_events/object_event_graphics_info_pointers.h';t=(source/p).read_text();t=''.join('extern const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_Journey'+n+';\n' for n in NAMES)+t; start=t.index('const struct ObjectEventGraphicsInfo *const gObjectEventGraphicsInfoPointers');end=t.index('};',start);t=t[:end]+''.join('    [OBJ_EVENT_GFX_JOURNEY_'+n+'] = &gObjectEventGraphicsInfo_Journey'+n+',\n' for n in NAMES)+t[end:];stage(p,t)
 p='src/event_object_movement.c';t=(source/p).read_text();needle='static const struct SpritePalette sObjectEventSpritePalettes[] = {';assert needle in t;t=t.replace(needle,needle+'\n'+''.join('    {gObjectEventPal_Journey'+n+', OBJ_EVENT_PAL_TAG_JOURNEY_'+n+'},\n' for n in NAMES));stage(p,t)
 spec=json.loads((ROOT/'tools/hoenn/data/galactic-chapter.json').read_text());trainers=[]
 for hero in ['eren','luffy']:
  for i,team in enumerate(spec['rivals'][hero]['teams']):trainers.append(dict(name=hero.upper(),key=hero.upper()+'_'+str(i+1),pic='EREN_TITAN' if hero=='eren' and i==5 else hero.upper(),team=team,important=True,role='rival'))
 for name,team in spec['admins'].items():trainers.append(dict(name=name.upper(),key=name.upper(),pic=name.upper(),team=team,important=True,role='boss'))
 trainers += [dict(name='GALACTIC',key='GRUNT_M',pic='GALACTIC_GRUNT_M',team=['ZUBAT','GLAMEOW','CROAGUNK'],important=False,role='grunt'),dict(name='GALACTIC',key='GRUNT_F',pic='GALACTIC_GRUNT_F',team=['STUNKY','BRONZOR','GLAMEOW'],important=False,role='grunt')]
 p='include/constants/opponents.h';t=(source/p).read_text();assert re.search(r'#define TRAINERS_COUNT\s+1551\b',t);t=re.sub(r'(#define TRAINERS_COUNT\s+)1551\b',r'\g<1>'+str(1551+len(trainers)),t)
 for i,tr in enumerate(trainers):tr['id']=1551+i;t+='\n#define TRAINER_JOURNEY_'+tr['key']+' '+str(tr['id'])
 stage(p,t+'\n')
 rows=[]
 for tr in trainers:
  cls='TRAINER_CLASS_RIVAL' if tr['role']=='rival' else 'TRAINER_CLASS_BOSS_FRLG' if tr['key']=='CYRUS' else 'TRAINER_CLASS_PKMN_TRAINER_1'
  mons=',\n'.join('{ .species=SPECIES_'+n+', .lvl=50, .gender=TRAINER_MON_RANDOM_GENDER, .iv=TRAINER_PARTY_IVS(20,20,20,20,20,20), .ball=POKEBALL_COUNT, .nature=NATURE_HARDY }' for n in tr['team'])
  rows.append('[DIFFICULTY_NORMAL][TRAINER_JOURNEY_'+tr['key']+'] = { .trainerName=_("'+tr['name']+'"), .trainerClass='+cls+', .trainerPic=TRAINER_PIC_JOURNEY_'+tr['pic']+', .gender=TRAINER_GENDER_MALE, .encounterMusic=TRAINER_ENCOUNTER_MUSIC_MALE, .aiFlags=AI_FLAG_BASIC_TRAINER, .partySize='+str(len(tr['team']))+', .party=(const struct TrainerMon[]){'+mons+'} },\n')
 stage('src/data/journey_crossover_trainers.h',''.join(rows))
 p='src/data.c';stage(p,(source/p).read_text().replace('#include "data/trainers.h"','#include "data/trainers.h"\n#include "data/journey_crossover_trainers.h"'))
 p='src/journey_competitive.c';t=(source/p).read_text();needle='       || trainer == GetTrainerStructFromId(TRAINER_JOURNEY_TEAM_1505);';assert needle in t;t=t.replace(needle,'       || trainer == GetTrainerStructFromId(TRAINER_JOURNEY_TEAM_1505)\n'+''.join('       || trainer == GetTrainerStructFromId(TRAINER_JOURNEY_'+n.upper()+')\n' for n in spec['admins'])[:-1]+';');stage(p,t)
 r=dict(layer=LAYER,registered_trainers=trainers,registered_avatars=assets,eren_titan_full_body=True,scenes_connected=False,original_sha256=originals,prepared_sha256={p:hashlib.sha256(b).hexdigest() for p,b in outputs.items()})
 for p,b in outputs.items():(source/p).parent.mkdir(parents=True,exist_ok=True);(source/p).write_bytes(b)
 marker.write_text(json.dumps(r,indent=2)+'\n');return r
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);a=p.parse_args();print(json.dumps(prepare(a.source),indent=2))
