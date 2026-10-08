"""Build remote islands and Dive caves, with region-independent special capture gates."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import struct
from prepare_family import LAYERS_BEFORE, HERE
from prepare_crossing import PIN

# Placement avoids every original event and stays well inside Surf seams.
SITES = [
 ('Tempestades','JourneyWorldSea00','surf',[13,2],(44,14)),
 ('Aurora','JourneyWorldSea01','surf',[14,18],(44,14)),
 ('Vulcao','JourneyWorldSea02','surf',[10,4],(44,14)),
 ('Titans','JourneyWorldSea03','surf',[5,8],(44,14)),
 ('Floresta','JourneyWorldSea04','surf',[12,6],(44,14)),
 ('Eclipse','JourneyWorldSea05','surf',[17,7],(44,14)),
 ('Dragoes','JourneyWorldSea06','surf',[16,1],(44,14)),
 ('Estrelas','JourneyWorldSea07','surf',[14,18],(44,14)),
 ('Cristais','JourneyWorldSea08','surf',[15,5],(44,14)),
 ('Mares','JourneyHoennNorthSea','dive',[11],(38,10)),
 ('Origens','JourneyHoennMiddleSea','dive',[16,14],(38,10)),
 ('Profundezas','JourneyHoennSouthSea','dive',[11,17],(38,10)),
 ('Dimensoes','JourneyRustboroCoast','dive',[7,14],(32,64)),
 ('Abismo','JourneyDewfordCoast','dive',[3,6],(32,64)),
]

# The pinned enum starts TYPE_NORMAL at 1 (TYPE_NONE is 0).
SITES = [(name, surface, access, [t+1 for t in types], point) for name,surface,access,types,point in SITES]

def prepare(source):
 source=Path(source);marker=source/'.journey-sanctuaries'
 if marker.exists():
  r=json.loads(marker.read_text())
  for p,h in r['prepared_sha256'].items():assert hashlib.sha256((source/p).read_bytes()).hexdigest()==h,p
  return r
 acquired=json.loads((source/'.source-acquired.json').read_text());assert acquired['commit']==PIN
 expected=dict(acquired['sha256'])
 for layer in LAYERS_BEFORE+['family','travel-rules','birth','wild','habitats']:
  expected.update(json.loads((source/('.journey-'+layer)).read_text())['prepared_sha256'])
 outputs,originals,inputs={},{},{}
 def read(p):
  if p in outputs:return outputs[p]
  raw=(source/p).read_bytes();assert hashlib.sha256(raw).hexdigest()==expected[p],p
  if p in acquired['sha256']:inputs[p]=acquired['sha256'][p]
  return raw
 def stage(p,body):
  if p in expected and p not in originals:originals[p]=hashlib.sha256(read(p)).hexdigest()
  outputs[p]=body if isinstance(body,bytes) else body.encode()
 def js(p,obj):stage(p,json.dumps(obj,indent=2)+'\n')
 groups=json.loads(read('data/maps/map_groups.json'));layouts=json.loads(read('data/layouts/layouts.json'));by_layout={l['id']:l for l in layouts['layouts']}
 catalog=json.loads((HERE/'catalog_metadata.json').read_text());species={int(i):s for i,s in catalog['species'].items()}
 specials=[species[i] for i in catalog['special_species']];allocated={s[0]:[] for s in SITES}
 # Allocate by theme, spreading unpaired special Pokémon across the smaller chambers.
 for mon in sorted(specials,key=lambda m:(m['national_dex'],m['id'])):
  candidates=[s for s in SITES if len(allocated[s[0]])<9]
  chosen=max(candidates,key=lambda s:(4*len(set(s[3])&set(mon['types']))-len(allocated[s[0]]),-SITES.index(s)))
  allocated[chosen[0]].append(mon)
 new_maps=[];sites=[];captures=[];event_changes=[];preserved={};legacy=[]
 flags=['\n// Persistent sanctuary catches; the National Dex synchronizes native encounters.']
 cave_template=json.loads(read('data/maps/NavelRock_Bottom/map.json'));cave_layout=by_layout[cave_template['layout']]
 cave_blocks=list(struct.unpack('<'+'H'*484,read(cave_layout['blockdata_filepath'])))
 for y in range(4,18):
  for x in range(4,18):cave_blocks[y*22+x]=0x0364
 cave_border=read(cave_layout['border_filepath'])
 under_template=json.loads(read('data/maps/Underwater_Route128/map.json'));under_layout=by_layout[under_template['layout']]
 def new_map(name,template,layout,width,height,blocks,border):
  m=copy.deepcopy(template);l=copy.deepcopy(layout);base='data/layouts/'+name
  m.update(id='MAP_'+name.upper(),name=name,layout='LAYOUT_'+name.upper(),connections=None,object_events=[],warp_events=[],coord_events=[],bg_events=[],show_map_name=False)
  l.update(id=m['layout'],name=name+'_Layout',width=width,height=height,blockdata_filepath=base+'/map.bin',border_filepath=base+'/border.bin')
  layouts['layouts'].append(l);new_maps.append(name);stage(l['blockdata_filepath'],struct.pack('<'+'H'*len(blocks),*blocks));stage(l['border_filepath'],border)
  return m
 for index,(theme,surface_name,access,tags,(cx,cy)) in enumerate(SITES):
  p=f'data/maps/{surface_name}/map.json';surface=json.loads(read(p));before=copy.deepcopy(surface);sl=by_layout[surface['layout']]
  w,h=sl['width'],sl['height'];raw=read(sl['blockdata_filepath']);blocks=list(struct.unpack('<'+'H'*(w*h),raw))
  region=surface.get('region','REGION_HOENN');section=surface['region_map_section'];cname='JourneySanctuary'+theme
  chamber=new_map(cname,cave_template,cave_layout,22,22,cave_blocks,cave_border);chamber.update(region=region,region_map_section=section)
  if access=='surf':
   # A small island with beach, low foothills and a single mountain entrance.
   x0,y0=cx-8,cy-8;x1,y1=cx+8,cy+8
   assert 0<x0<x1<w-1 and 0<y0<y1<h-1
   assert not any(x0<=e.get('x',-1)<=x1 and y0<=e.get('y',-1)<=y1 for k in ['object_events','warp_events','coord_events','bg_events'] for e in surface[k]),surface_name
   # All graphics are primary FRLG tiles, matching the existing ocean layout.
   for y in range(y0,y1+1):
    for x in range(x0,x1+1):blocks[y*w+x]=0x3115
   for y in range(cy-4,cy+5):
    for x in range(cx-5,cx+6):blocks[y*w+x]=0x3001
   mountain=[[0x47B,0x4B3,0x471,0x471,0x471,0x4B2,0x47D],
             [0x4B3,0x47B,0x47C,0x47C,0x47C,0x47D,0x4B2],
             [0x4A8,0x479,0x479,0x30A9,0x479,0x479,0x4AA]]
   for dy,row in enumerate(mountain):
    for dx,tile in enumerate(row):blocks[(cy-6+dy)*w+cx-3+dx]=tile
   entrance_y=cy-4;warp_id=len(surface['warp_events'])
   surface['warp_events'].append(dict(x=cx,y=entrance_y,elevation=3,dest_map=chamber['id'],dest_warp_id='0'))
   chamber['warp_events']=[dict(x=14,y=19,elevation=0,dest_map=surface['id'],dest_warp_id=str(warp_id))]
   stage(sl['blockdata_filepath'],struct.pack('<'+'H'*len(blocks),*blocks))
  else:
   assert not any(c['direction']=='dive' for c in surface.get('connections') or []),surface_name
   candidates=[]
   events=[e for k in ['object_events','warp_events','coord_events','bg_events'] for e in surface[k]]
   for py in range(5,h-5):
    for px in range(5,w-5):
     if any(abs(px-e.get('x',-999))<=3 and abs(py-e.get('y',-999))<=3 for e in events):continue
     if all(blocks[y*w+x]==0x1170 for y in range(py-2,py+3) for x in range(px-2,px+3)):
      candidates.append(((px-cx)**2+(py-cy)**2,px,py))
   assert candidates,surface_name
   _,cx,cy=min(candidates)
   assert not any(cx-2<=e.get('x',-1)<=cx+2 and cy-2<=e.get('y',-1)<=cy+2 for k in ['object_events','warp_events','coord_events','bg_events'] for e in surface[k]),surface_name
   for y in range(cy-2,cy+3):
    for x in range(cx-2,cx+3):assert blocks[y*w+x]==0x1170,(surface_name,x,y,hex(blocks[y*w+x]));blocks[y*w+x]=0x114F
   uname='JourneyDepth'+theme;ub=[0x3254]*(w*h)
   for y in range(h):
    for x in range(w):
     if x in [0,w-1] or y in [0,h-1]:ub[y*w+x]=0x361E
   # Native underwater cave mouth: the upper half is decoration, the bottom warps.
   ub[(cy-1)*w+cx]=0x3666;ub[cy*w+cx]=0x326E
   under=new_map(uname,under_template,under_layout,w,h,ub,read(under_layout['border_filepath']))
   under.update(region=region,region_map_section=section,connections=[dict(direction='emerge',map=surface['id'],offset=0)],warp_events=[dict(x=cx,y=cy,elevation=3,dest_map=chamber['id'],dest_warp_id='0')])
   surface['connections']=(surface.get('connections') or [])+[dict(direction='dive',map=under['id'],offset=0)]
   chamber['warp_events']=[dict(x=14,y=19,elevation=0,dest_map=under['id'],dest_warp_id='0')]
   stage(f'data/maps/{uname}/scripts.inc',uname+'_MapScripts::\n\t.byte 0\n');js(f'data/maps/{uname}/map.json',under)
   stage(sl['blockdata_filepath'],struct.pack('<'+'H'*len(blocks),*blocks))
  entries=[cname+'_MapScripts::\n\tmap_script MAP_SCRIPT_ON_TRANSITION, JourneySanctuary_Sync\n\t.byte 0\n']
  for j,mon in enumerate(allocated[theme]):
   n=len(captures);flag=f'FLAG_JOURNEY_SPECIAL_{mon["national_dex"]}';flags.append(f'#define {flag} 0x{0x1AD0+n:04X}')
   x,y=5+(j%3)*5,6+(j//3)*5;label=f'JourneySanctuary_{mon["national_dex"]}'
   # A visible altar is used consistently; battle sprites are native species sprites.
   chamber['object_events'].append(dict(local_id='LOCALID_SPECIAL_'+str(mon['national_dex']),graphics_id='OBJ_EVENT_GFX_TRICK_HOUSE_STATUE',x=x,y=y,elevation=0,movement_type='MOVEMENT_TYPE_FACE_DOWN',movement_range_x=0,movement_range_y=0,trainer_type='TRAINER_TYPE_NONE',trainer_sight_or_berry_tree_id='0',script=label,flag=flag))
   entries.append(f'''{label}::
\tlock
\tfaceplayer
\tsetvar VAR_0x8004, {mon['name']}
\tcallnative JourneySpecialStatus
\tgoto_if_eq VAR_RESULT, 0, JourneySanctuary_Locked
\tgoto_if_eq VAR_RESULT, 2, JourneySanctuary_AlreadyCaught
\tbufferspeciesname STR_VAR_1, {mon['name']}
\tmsgbox JourneySanctuary_ChallengeText, MSGBOX_YESNO
\tgoto_if_eq VAR_RESULT, NO, JourneySanctuary_End
\tsetwildbattle {mon['name']}, 70
\tdowildbattle
\tspecialvar VAR_RESULT, GetBattleOutcome
\tgoto_if_ne VAR_RESULT, B_OUTCOME_CAUGHT, JourneySanctuary_End
\tsetflag {flag}
\tremoveobject LOCALID_SPECIAL_{mon['national_dex']}
\treleaseall
\tend
''')
   captures.append(dict(species=mon['name'],id=mon['id'],national_dex=mon['national_dex'],site=theme,map=cname,flag=flag,flag_id=0x1AD0+n,position=[x,y],access=access,surface=surface_name,section=section))
  stage(f'data/maps/{cname}/scripts.inc','\n'.join(entries));js(f'data/maps/{cname}/map.json',chamber)
  js(p,surface);event_changes.append(dict(map=surface_name,before=before,after=surface))
  sites.append(dict(theme=theme,map=cname,surface=surface_name,access=access,entry=[cx,cy],species_count=len(allocated[theme]),region=region,section=section))
 groups['group_order'].append('JourneySanctuaries');groups['JourneySanctuaries']=new_maps
 js('data/maps/map_groups.json',groups);js('data/layouts/layouts.json',layouts)
 p='include/constants/flags.h';body=read(p).decode();assert '#define JOURNEY_FLAGS_END 0x1ACF' in body
 stage(p,body.replace('#define JOURNEY_FLAGS_END 0x1ACF','#define JOURNEY_FLAGS_END 0x1B3F')+'\n'+'\n'.join(flags)+'\n')
 stage('include/journey_special_data.h','struct JourneySpecialCapture { u16 species, dex, flag; };\nstatic const struct JourneySpecialCapture sJourneySpecialCaptures[] = {\n'+',\n'.join('{'+r['species']+', '+str(r['national_dex'])+', '+r['flag']+'}' for r in captures)+'\n};\n')
 stage('src/journey_special.c','''#include "global.h"
#include "event_data.h"
#include "pokedex.h"
#include "pokemon.h"
#include "journey_gym_scaling.h"
#include "constants/flags.h"
#include "constants/species.h"
#include "constants/pokedex.h"
#include "journey_special_data.h"
u32 JourneySpecialUnlocked(void) { return JourneyGymBadgeCount(TRUE) == 8 && JourneyGymBadgeCount(FALSE) == 8; }
void JourneySpecialStatus(void *ctx)
{
    gSpecialVar_Result = !JourneySpecialUnlocked() ? 0 : GetSetPokedexFlag(SpeciesToNationalPokedexNum(gSpecialVar_0x8004), FLAG_GET_CAUGHT) ? 2 : 1;
}
void JourneySpecialSync(void *ctx)
{
    u32 i;
    for (i = 0; i < ARRAY_COUNT(sJourneySpecialCaptures); i++)
        if (GetSetPokedexFlag(sJourneySpecialCaptures[i].dex, FLAG_GET_CAUGHT)) FlagSet(sJourneySpecialCaptures[i].flag);
}
''')
 shared='''JourneySanctuary_Sync::
\tcallnative JourneySpecialSync
\tend
JourneySanctuary_Locked::
\tmsgbox JourneySanctuary_LockedText, MSGBOX_DEFAULT
\tgoto JourneySanctuary_End
JourneySanctuary_AlreadyCaught::
\tmsgbox JourneySanctuary_CaughtText, MSGBOX_DEFAULT
JourneySanctuary_End::
\treleaseall
\tend
JourneySanctuary_LockedText:
\t.string "Este altar exige as 16 insignias.\\nComplete os ginasios de Kanto e Hoenn.$"
JourneySanctuary_CaughtText:
\t.string "Este Pokemon ja esta registrado\\ncomo capturado na Pokedex.$"
JourneySanctuary_ChallengeText:
\t.string "{STR_VAR_1} responde ao altar.\\nDeseja iniciar o encontro?$"
JourneySanctuary_PassageText:
\t.string "Posso levar voce a ilha proxima.\\nQuer conhecer sua caverna?$"
'''
 stage('data/scripts/journey_sanctuaries.inc',shared)
 # Existing legendary battles also obey the gate. Story movement and plot actors remain.
 names={m['name'] for m in specials}
 for p in acquired['sha256']:
  if not p.startswith('data/maps/') or not p.endswith('/scripts.inc'):continue
  body=read(p).decode();hits=[]
  def guard(match):
   name=match[2]
   if name not in names:return match[0]
   hits.append(name)
   return f'\tsetvar VAR_0x8004, {name}\n\tcallnative JourneySpecialStatus\n\tgoto_if_eq VAR_RESULT, 0, JourneySanctuary_Locked\n\tgoto_if_eq VAR_RESULT, 2, JourneySanctuary_AlreadyCaught\n'+match[0]
  updated=re.sub(r'(\t(?:seteventmon|setwildbattle)\s+)(SPECIES_\w+)([^\n]*\n)',guard,body)
  if hits:stage(p,updated);legacy.append(dict(path=p,species=hits))
 p='data/event_scripts.s';body=read(p).decode()+'\n\t.include "data/scripts/journey_sanctuaries.inc"\n'
 for n in new_maps:body+=f'\t.include "data/maps/{n}/scripts.inc"\n'
 stage(p,body)
 p='src/pokedex_area_screen.c';body=read(p).decode();anchor='    // Add roamers to the area map'
 assert body.count(anchor)==1
 area=''
 for c in captures:
  ident='MAP_'+c['map'].upper()
  area+=f'    if (species == {c["species"]} && GetRegionMapType(Overworld_GetMapHeaderByGroupAndId(MAP_GROUP({ident}), MAP_NUM({ident}))->regionMapSectionId) == currentRegionMapType)\n        SetSpecialMapHasMon(MAP_GROUP({ident}), MAP_NUM({ident}));\n'
 stage(p,body.replace(anchor,area+'\n'+anchor))
 r=dict(status='remote_sanctuaries_candidate',source_commit=PIN,sites=sites,captures=captures,new_maps=new_maps,
  legacy_capture_gates=legacy,unlock='8 Kanto and 8 Hoenn badges; no League requirement',capture_retry_on_defeat_or_escape=True,
  event_changes=event_changes,input_sha256=inputs,original_sha256=originals,prepared_sha256={p:hashlib.sha256(v).hexdigest() for p,v in outputs.items()},
  cave_geometry='Native Navel Rock shell with expanded walkable interior',surf_island_access='Continuous native Surf landing and mountain cave doorway',map_complete=False)
 for p,raw in outputs.items():(source/p).parent.mkdir(parents=True,exist_ok=True);(source/p).write_bytes(raw)
 marker.write_text(json.dumps(r,indent=2)+'\n');return r

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True)
 print(json.dumps(prepare(p.parse_args().source),indent=2))
