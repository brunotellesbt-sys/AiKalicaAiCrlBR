"""Move all 20 canonical Paradox species to two visible, gated cave chambers."""
import argparse,copy,hashlib,json,re,struct
from pathlib import Path
from prepare_intro_region import PRIOR,LAYER as PREVIOUS
from refresh_ecology import compile_tables
LAYER='paradox-caves';PRIOR=PRIOR+[PREVIOUS];ROOT=Path(__file__).resolve().parents[2]
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
  old=(source/p).read_bytes() if (source/p).exists() else None;h=hashlib.sha256(old).hexdigest() if old else None
  assert h==expected.get(p),p
  if h:originals[p]=h
  outputs[p]=raw.encode() if isinstance(raw,str) else raw
 def js(p,d):stage(p,json.dumps(d,indent=2)+'\n')
 catalog=json.loads((ROOT/'tools/hoenn/catalog_metadata.json').read_text());canonical=set(catalog['canonical_species'].values());paradox=[s for s in catalog['species'].values() if s['id'] in canonical and s['flags']&16];assert len(paradox)==20;ids={s['id'] for s in paradox};names={s['name'] for s in paradox}
 locations=copy.deepcopy(json.loads((source/'.journey-five-island-habitat').read_text())['locations_data'])
 for h in locations:h['families']=[f for f in h['families'] if not any(s['id'] in ids for s in f['species'])]
 for h in locations:
  if h['families']:continue
  donors=[d for d in locations if len(d['families'])>1]
  choices=[(d,f) for d in donors for f in d['families'] if h['land'] or 12 in catalog['species'][str(f['root'])]['types']]
  assert choices,h['section'];d,f=max(choices,key=lambda df:(len(df[0]['families']),len(set(h.get('native_types',[]))&set(df[1]['types'])),-df[1]['root']));d['families'].remove(f);h['families'].append(f)
 tables,ecology=compile_tables(source,locations)
 for p,raw in tables.items():stage(p,raw)
 # Use actual Pokémon overworld graphics for every existing sanctuary inhabitant.
 sanctuaries=json.loads((source/'.journey-sanctuaries').read_text());by_map={}
 for c in sanctuaries['captures']:by_map.setdefault(c['map'],[]).append(c)
 for name,rows in by_map.items():
  p='data/maps/'+name+'/map.json';m=json.loads((source/p).read_text())
  for c in rows:
   o=next(o for o in m['object_events'] if o['script']=='JourneySanctuary_'+str(c['national_dex']));o['graphics_id']='OBJ_EVENT_GFX_SPECIES('+c['species'].removeprefix('SPECIES_')+')'
  js(p,m)
 layout_data=json.loads((source/'data/layouts/layouts.json').read_text());layout_index={l['id']:l for l in layout_data['layouts']}
 hub='JourneySanctuaryDimensoes';p='data/maps/'+hub+'/map.json';m=json.loads((source/p).read_text());groups=json.loads((source/'data/maps/map_groups.json').read_text());captures=[]
 for future,name,x in [(False,'JourneyParadoxPast',4),(True,'JourneyParadoxFuture',18)]:
  room=copy.deepcopy(m);room.update(name=name,id='MAP_'+name.upper(),object_events=[],warp_events=[],coord_events=[],bg_events=[],connections=None)
  old_layout=layout_index[room['layout']];new_layout=copy.deepcopy(old_layout);new_layout.update(id='LAYOUT_'+name.upper(),name=name+'_Layout',blockdata_filepath='data/layouts/'+name+'/map.bin',border_filepath='data/layouts/'+name+'/border.bin');layout_data['layouts'].append(new_layout);room['layout']=new_layout['id'];stage(new_layout['blockdata_filepath'],(source/old_layout['blockdata_filepath']).read_bytes());stage(new_layout['border_filepath'],(source/old_layout['border_filepath']).read_bytes())
  wid=len(m['warp_events']);m['warp_events'].append(dict(x=x,y=19,elevation=0,dest_map=room['id'],dest_warp_id='0'))
  room['warp_events']=[dict(x=14,y=19,elevation=0,dest_map=m['id'],dest_warp_id=str(wid))]
  members=sorted([s for s in paradox if s['name'].startswith('SPECIES_IRON_')==future],key=lambda s:s['national_dex']);assert len(members)==10
  scripts=[name+'_MapScripts::\n\tmap_script MAP_SCRIPT_ON_TRANSITION, JourneySanctuary_Sync\n\t.byte 0\n']
  for i,s in enumerate(members):
   flag='0';number=0;label='JourneyParadox_'+str(s['national_dex']);local='LOCALID_PARADOX_'+str(s['national_dex']);px,py=4+i%3*6,5+i//3*4
   room['object_events'].append(dict(local_id=local,graphics_id='OBJ_EVENT_GFX_SPECIES('+s['name'].removeprefix('SPECIES_')+')',x=px,y=py,elevation=0,movement_type='MOVEMENT_TYPE_FACE_DOWN',movement_range_x=0,movement_range_y=0,trainer_type='TRAINER_TYPE_NONE',trainer_sight_or_berry_tree_id='0',script=label,flag=flag))
   scripts.append(f'''{label}::
\tlock
\tfaceplayer
\tsetvar VAR_0x8004, {s['name']}
\tcallnative JourneySpecialStatus
\tgoto_if_eq VAR_RESULT, 0, JourneySanctuary_Locked
\tgoto_if_eq VAR_RESULT, 2, JourneySanctuary_AlreadyCaught
\tbufferspeciesname STR_VAR_1, {s['name']}
\tmsgbox JourneySanctuary_ChallengeText, MSGBOX_YESNO
\tgoto_if_eq VAR_RESULT, NO, JourneySanctuary_End
\tsetwildbattle {s['name']}, 70
\tdowildbattle
\tspecialvar VAR_RESULT, GetBattleOutcome
\tgoto_if_ne VAR_RESULT, B_OUTCOME_CAUGHT, JourneySanctuary_End
\tremoveobject {local}
\treleaseall
\tend
''');captures.append(dict(species=s['name'],id=s['id'],national_dex=s['national_dex'],map=name,flag=flag,flag_id=number,position=[px,py],parent=hub,level=70))
  groups['JourneySanctuaries'].append(name);js('data/maps/'+name+'/map.json',room);stage('data/maps/'+name+'/scripts.inc','\n'.join(scripts))
 js(p,m);js('data/maps/map_groups.json',groups);js('data/layouts/layouts.json',layout_data)
 p='data/event_scripts.s';stage(p,(source/p).read_text()+'\n\t.include \"data/maps/JourneyParadoxPast/scripts.inc\"\n\t.include \"data/maps/JourneyParadoxFuture/scripts.inc\"\n')
 hub_layout=layout_index[m['layout']];raw=(source/hub_layout['blockdata_filepath']).read_bytes();blocks=list(struct.unpack('<'+'H'*(len(raw)//2),raw));w=hub_layout['width'];floor=blocks[18*w+14];exit_tile=blocks[19*w+14]
 for x in range(4,19):blocks[18*w+x]=floor
 for x in [4,18]:blocks[19*w+x]=exit_tile
 stage(hub_layout['blockdata_filepath'],struct.pack('<'+'H'*len(blocks),*blocks))
 p='include/constants/flags.h';stage(p,(source/p).read_text())
 p='include/journey_special_data.h';t=(source/p).read_text();at=t.rindex('};');t=t[:at].rstrip()+',\n'+''.join('{'+c['species']+','+str(c['national_dex'])+','+c['flag']+'},\n' for c in captures)+t[at:];stage(p,t)
 # Add fixed habitat marks at the actual parent cave's world-map position.
 p='src/data/journey_world_dex_locations.h';t=(source/p).read_text();row=next(c for c in sanctuaries['captures'] if c['map']==hub);match=re.search(r'\{'+row['species']+r',MAP_\w+,(\d+),(\d+),1\}',t);assert match
 t=re.sub(r'^\{(?:'+ '|'.join(sorted(names))+r'),[^\n]+\n','',t,flags=re.M);at=t.rindex('};');t=t[:at]+''.join('{'+c['species']+',MAP_'+c['map'].upper()+','+match[1]+','+match[2]+',1},\n' for c in captures)+t[at:];stage(p,t)
 p='src/journey_special.c';t=(source/p).read_text().replace('if (GetSetPokedexFlag(sJourneySpecialCaptures[i].dex, FLAG_GET_CAUGHT))','if (sJourneySpecialCaptures[i].flag && GetSetPokedexFlag(sJourneySpecialCaptures[i].dex, FLAG_GET_CAUGHT))');stage(p,t)
 p='src/event_object_movement.c';t=(source/p).read_text().replace('#include "global.h"','#include "global.h"\n#include "journey_version.h"',1);needle='    if(!JourneyStoryObjectVisible(objectEventTemplate->script))return OBJECT_EVENTS_COUNT;';assert needle in t;t=t.replace('#include "journey_version.h"','#include "journey_version.h"\n#include "pokedex.h"');t=t.replace(needle,needle+'\n    if((graphicsId&OBJ_EVENT_MON) && !JourneySpeciesAllowed(graphicsId&OBJ_EVENT_MON_SPECIES_MASK))return OBJECT_EVENTS_COUNT;\n    if((graphicsId&OBJ_EVENT_MON) && mapGroup==MAP_GROUP(MAP_JOURNEYPARADOXPAST) && GetSetPokedexFlag(SpeciesToNationalPokedexNum(graphicsId&OBJ_EVENT_MON_SPECIES_MASK),FLAG_GET_CAUGHT))return OBJECT_EVENTS_COUNT;');stage(p,t)
 r=dict(layer=LAYER,paradox_captures=captures,ecology=ecology,all_sanctuaries_use_pokemon_overworld_sprites=True,requires_sixteen_badges=True,no_paradox_random_encounters=True,requires_new_save=True,original_sha256=originals,prepared_sha256={p:hashlib.sha256(raw).hexdigest() for p,raw in outputs.items()})
 for p,raw in outputs.items():(source/p).parent.mkdir(parents=True,exist_ok=True);(source/p).write_bytes(raw)
 marker.write_text(json.dumps(r,indent=2)+'\n');return r
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);a=p.parse_args();print(json.dumps(prepare(a.source),indent=2))
