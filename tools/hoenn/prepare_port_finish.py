"""Finish the approved vertical west-island port and collision-safe moorings."""
import argparse,io,json,re,struct,hashlib
from pathlib import Path
from PIL import Image
from candidate_layer import Layer
from prepare_briney_mossdeep import PRIOR,LAYER as PREVIOUS
from import_native_pier import import_pier
from pack_crossover_assets import fit,indexed
LAYER='port-finish';PRIOR=PRIOR+[PREVIOUS];ROOT=Path(__file__).resolve().parents[2]
def prepare(source):
 layer=Layer(source,LAYER,PRIOR)
 if old:=layer.existing():return old
 s=layer.source;layouts={x['id']:x for x in json.loads((s/'data/layouts/layouts.json').read_text())['layouts']}
 def read(p):return layer.outputs.get(p,(s/p).read_bytes() if (s/p).exists() else b'')
 def append(p,t):layer.stage(p,read(p).decode()+t)
 def mapdata(n):return json.loads(read(f'data/maps/{n}/map.json'))
 def terrain(m):
  l=layouts[m['layout']];return l,list(struct.unpack('<'+'H'*(l['width']*l['height']),read(l['blockdata_filepath'])))
 def save(m,l,v):layer.stage(f'data/maps/{m["name"]}/map.json',json.dumps(m,indent=2)+'\n');layer.stage(l['blockdata_filepath'],struct.pack('<'+'H'*len(v),*v))
 def destination(pid,x,y):
  p='data/scripts/journey_campaign_gates.inc';t=read(p).decode();a=t.index('LavenderNetwork_Destination'+str(pid)+'::');b=t.index('\n\n',a);chunk=t[a:b];chunk=re.sub(r'(setvar VAR_0x8009, )\d+',lambda z:z[1]+str(x),chunk);chunk=re.sub(r'(setvar VAR_0x800A, )\d+',lambda z:z[1]+str(y),chunk);layer.stage(p,t[:a]+chunk+t[b:])
 m=mapdata('MossdeepCity');l,v=terrain(m);w=l['width'];native=struct.unpack('<3200H',(ROOT/'tools/hoenn/data/mossdeep-before-dock.bin').read_bytes())
 for y in range(20,34):
  for x in range(16):
   value=native[y*w+x];v[y*w+x]=0x3124 if y>=25 and value in [0x3308,0x3309,0x3710,0x3711,0x0756,0x3001] else value
 # Four-column facade: the fifth column previously copied a neighboring tree.
 for dy in range(4):
  for dx in range(4):v[(27+dy)*w+3+dx]=native[(6+dy)*w+27+dx]
 # Vertical bridge, three rows, matching the approved preview's native boards.
 for y in range(31,34):v[y*w+4]=0x3000|972;v[y*w+5]=0x3000|974
 captain=next(o for o in m['object_events'] if o['script']=='Journey_FerryPort16');captain.update(x=5,y=32,elevation=3,movement_type='MOVEMENT_TYPE_FACE_RIGHT')
 boat=next(o for o in m['object_events'] if o['graphics_id']=='OBJ_EVENT_GFX_MR_BRINEYS_BOAT');boat.update(x=7,y=33,movement_type='MOVEMENT_TYPE_FACE_LEFT')
 for y in [32,33]:
  for x in [6,7,8]:
   assert native[y*w+x]>>12==1,(x,y);v[y*w+x]=0x1570
 # Only wet fringe beside the jetty becomes blue water, never terrestrial sand.
 for y in [32,33]:
  for x in [3,9]:
   if native[y*w+x]>>12==1:v[y*w+x]=0x1170
 save(m,l,v);destination(16,4,32)
 p='include/journey_birth_arrivals.h';layer.stage(p,read(p).decode().replace('{MAP_MOSSDEEP_CITY, 12, 31, 9, 31, TRUE}','{MAP_MOSSDEEP_CITY, 7, 33, 4, 32, TRUE}'))
 # Clear the earlier Cinnabar facade that obstructed the existing Mart's exit.
 m=mapdata('CinnabarIsland_Frlg');l,v=terrain(m);w=l['width'];native_c=struct.unpack('<480H',(ROOT/'tools/hoenn/data/cinnabar-original.bin').read_bytes())
 for y in range(12,19):
  for x in range(16,24):v[y*w+x]=native_c[y*w+x]
 facade=[native[(6+dy)*80+27+dx] for dy in range(4) for dx in range(4)];ids,files=import_pier(s,l['secondary_tileset'],donor='gTileset_Mossdeep',mids=sorted({t&1023 for t in facade}),donor_emerald=True)
 for p,data in files.items():layer.stage(p,data)
 for dy in range(4):
  for dx in range(4):t=facade[dy*4+dx];v[(12+dy)*w+8+dx]=(t&~1023)|ids[t&1023]
 # Use the already installed native wood IDs, keeping the front door accessible.
 previous=struct.unpack('<480H',(s/l['blockdata_filepath']).read_bytes());left,right=previous[16*w+19],previous[16*w+20]
 for y in range(16,19):v[y*w+9]=left;v[y*w+10]=right
 for o in m['object_events']:
  if o['script']=='Journey_FerryPort19':o.update(x=9,y=17)
  if o['graphics_id']=='OBJ_EVENT_GFX_MR_BRINEYS_BOAT':o.update(x=12,y=18,movement_type='MOVEMENT_TYPE_FACE_LEFT')
 for x in [8,10,12]:
  for yy in [18,19]:
   for xx in [x,x+1]:
    assert native_c[yy*w+xx] in [0x510,0x511,0x518,0x519,0x5CB,0x5CC,0x5D3,0x5D4];v[yy*w+xx]=0x112B
 for y in [17,18]:
  for x in [11,12,13]:v[y*w+x]|=0x400
 for y in range(16,19):v[y*w+9]=left;v[y*w+10]=right
 for warp in m['warp_events']:
  if warp['dest_map']=='MAP_JOURNEYCINNABARSAILORSLODGE':warp.update(x=9,y=15)
 save(m,l,v);destination(19,10,17)
 # Restore shipyard wood, and move complete hulls to adjacent existing water.
 m=mapdata('JourneyRoute12Shipyard');l,v=terrain(m);w=l['width'];baseline=ROOT/'tools/hoenn/data/shipyard-before-moorings.bin';raw=baseline.read_bytes();assert hashlib.sha256(raw).hexdigest()==json.loads((s/'.journey-compact-ports').read_text())['original_sha256'][l['blockdata_filepath']];v=list(struct.unpack('<3840H',raw));layer.stage('data/layouts/JourneyRoute12Shipyard/pre-moorings.bin',raw)
 boat_records=[];reserved=set();info=(s/'src/data/object_events/object_event_graphics_info.h').read_text();pointers=(s/'src/data/object_events/object_event_graphics_info_pointers.h').read_text()
 for o in m['object_events']:
  if o['graphics_id'] not in ['OBJ_EVENT_GFX_MR_BRINEYS_BOAT','OBJ_EVENT_GFX_SEAGALLOP']:continue
  symbol=re.search(r'\['+o['graphics_id']+r'\]\s*=\s*&([A-Za-z0-9_]+)',pointers)[1];body=re.search(r'const struct ObjectEventGraphicsInfo '+symbol+r'\s*=\s*\{(.*?)\};',info,re.S)[1];width=int(re.search(r'\.width = (\d+)',body)[1]);height=int(re.search(r'\.height = (\d+)',body)[1]);candidates=[]
  for yy in range(height//16-1,l['height']):
   for xx in range(width//32,w-width//32):
    cells={(x,y) for y in range(yy-height//16+1,yy+1) for x in range((xx*16+8-width//2)//16,(xx*16+8+width//2-1)//16+1)}
    if cells&reserved or any(v[y*w+x]!=0x112B for x,y in cells):continue
    if not any(0<=x+dx<w and 0<=y+dy<l['height'] and v[(y+dy)*w+x+dx]==0x32F3 for x,y in cells for dx,dy in [(0,-1),(0,1),(-1,0),(1,0)]):continue
    candidates.append((abs(xx-o['x'])+abs(yy-o['y']),xx,yy,cells))
  assert candidates,o;_,x,y,cells=min(candidates,key=lambda r:r[:3]);o.update(x=x,y=y,movement_type='MOVEMENT_TYPE_FACE_LEFT');reserved|=cells
  for xx,yy in cells:v[yy*w+xx]|=0x400
  boat_records.append(dict(anchor=[x,y],cells=sorted(cells),graphics=o['graphics_id']))
 save(m,l,v)
 # Compact generated submarine: at most 3x2 collision tiles, two water rows away.
 art=ROOT/'tools/hoenn/data/sootopolis-submarine-source.png';frame=indexed(fit(Image.open(art).convert('RGBA'),32,32));sheet=Image.new('P',(32,288));sheet.putpalette(frame.getpalette())
 for i in range(9):sheet.paste(frame,(0,i*32))
 data=io.BytesIO();sheet.save(data,format='PNG');path='graphics/object_events/pics/journey/submarine';layer.stage(path+'.png',data.getvalue());colors=frame.getpalette()[:48];layer.stage(path+'.pal','JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,colors[i:i+3])) for i in range(0,48,3))+'\n')
 p='include/constants/event_objects.h';text=read(p).decode();assert 'OBJ_EVENT_GFX_JOURNEY_SUBMARINE' not in text;layer.stage(p,text.replace('    NUM_OBJ_EVENT_GFX','    OBJ_EVENT_GFX_JOURNEY_SUBMARINE,\n    NUM_OBJ_EVENT_GFX')+'\n#define OBJ_EVENT_PAL_TAG_JOURNEY_SUBMARINE 0x1530\n')
 append('src/data/object_events/object_event_graphics.h','\nconst u32 gObjectEventPic_JourneySubmarine[]=INCBIN_U32("'+path+'.4bpp");\nconst u16 gObjectEventPal_JourneySubmarine[]=INCBIN_U16("'+path+'.gbapal");\n');append('src/data/object_events/object_event_pic_tables.h','\nstatic const struct SpriteFrameImage sPicTable_JourneySubmarine[]={overworld_ascending_frames(gObjectEventPic_JourneySubmarine,4,4)};\n');append('src/data/object_events/object_event_graphics_info.h','\nconst struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_JourneySubmarine={.tileTag=TAG_NONE,.paletteTag=OBJ_EVENT_PAL_TAG_JOURNEY_SUBMARINE,.reflectionPaletteTag=OBJ_EVENT_PAL_TAG_NONE,.size=512,.width=32,.height=32,.paletteSlot=10,.shadowSize=SHADOW_SIZE_M,.inanimate=TRUE,.compressed=FALSE,.tracks=TRACKS_NONE,.oam=&gObjectEventBaseOam_32x32,.subspriteTables=sOamTables_32x32,.anims=sAnimTable_Standard,.images=sPicTable_JourneySubmarine};\n')
 p='src/data/object_events/object_event_graphics_info_pointers.h';text=read(p).decode();layer.stage(p,'extern const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_JourneySubmarine;\n'+text.replace('const struct ObjectEventGraphicsInfo *const gObjectEventGraphicsInfoPointers[NUM_OBJ_EVENT_GFX] = {','const struct ObjectEventGraphicsInfo *const gObjectEventGraphicsInfoPointers[NUM_OBJ_EVENT_GFX] = {\n [OBJ_EVENT_GFX_JOURNEY_SUBMARINE]=&gObjectEventGraphicsInfo_JourneySubmarine,'))
 p='src/event_object_movement.c';text=read(p).decode();layer.stage(p,text.replace('static const struct SpritePalette sObjectEventSpritePalettes[] = {','static const struct SpritePalette sObjectEventSpritePalettes[] = {\n {gObjectEventPal_JourneySubmarine,OBJ_EVENT_PAL_TAG_JOURNEY_SUBMARINE},'))
 m=mapdata('SootopolisCity');l,v=terrain(m);captain=next(o for o in m['object_events'] if o['script']=='Journey_FerryPort17');boat=dict(captain);boat.update(x=21,y=41,elevation=1,graphics_id='OBJ_EVENT_GFX_JOURNEY_SUBMARINE',script='JourneyCompactPort_Boat');m['object_events'].append(boat)
 for y in [40,41]:
  for x in [20,21,22]:assert v[y*l['width']+x]>>12==1;v[y*l['width']+x]|=0x400
 save(m,l,v)
 return layer.finish(mossdeep=dict(house=[3,27,4,4],vertical_pier=[4,31,2,3],captain=[5,32],boat=[7,33],water_only_collision=True),cinnabar_existing_mart_exit_preserved=True,shipyard_moorings=boat_records,sootopolis_submarine=dict(anchor=[21,41],footprint_tiles=6,clear_water_rows=[38,39]),all_other_ports_preserved=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);print(prepare(p.parse_args().source)['layer'])
