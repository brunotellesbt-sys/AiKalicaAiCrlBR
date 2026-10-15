"""Move vertical hulls one tile nearer the piers, using native sprite placement."""
import argparse,json,re,struct
from pathlib import Path
from candidate_layer import Layer
from render_sea_maps import MapRenderer
from prepare_port_orientation_finish import PRIOR,LAYER as PREVIOUS
LAYER='close-vertical-boats';PRIOR=PRIOR+[PREVIOUS]
def prepare(source):
 layer=Layer(source,LAYER,PRIOR)
 if old:=layer.existing():return old
 s=layer.source;r=MapRenderer(s);ls=r.layouts;maps={};blocks={};boats=[];offsets={}
 p='src/data/object_events/object_event_subsprites.h';text=(s/p).read_text();start=text.index('static const struct Subsprite sOamTable_32x32_0');end=re.search(r'const struct SubspriteTable sOamTables_32x32\[\].*?\n\};',text,re.S).end();base=text[start:end];subs=text
 pinfo='src/data/object_events/object_event_graphics_info.h';info=(s/pinfo).read_text();body=re.search(r'const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_MrBrineysBoat\s*=\s*\{(.*?)\};',info,re.S)[1]
 ptr='src/data/object_events/object_event_graphics_info_pointers.h';pointers=(s/ptr).read_text();hdr='include/constants/event_objects.h';header=(s/hdr).read_text()
 for name,dx in [('JourneySeviiBoat',2),('JourneyPetalburgBoat',-2)]:
  gfx='OBJ_EVENT_GFX_'+name.upper();offsets[gfx]=[dx,0]
  clone=base.replace('sOamTable_32x32','sOamTable_'+name).replace('sOamTables_32x32','sOamTables_'+name).replace('.x = -16,','.x = '+str(-16+dx)+',');subs+='\n'+clone+'\n'
  info+='\nconst struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_'+name+' = {'+body.replace('sOamTables_32x32','sOamTables_'+name)+'};\n'
  header=header.replace('    NUM_OBJ_EVENT_GFX','    '+gfx+',\n    NUM_OBJ_EVENT_GFX')
  pointers='extern const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_'+name+';\n'+pointers
  pointers=pointers.replace('const struct ObjectEventGraphicsInfo *const gObjectEventGraphicsInfoPointers[NUM_OBJ_EVENT_GFX] = {','const struct ObjectEventGraphicsInfo *const gObjectEventGraphicsInfoPointers[NUM_OBJ_EVENT_GFX] = {\n ['+gfx+']=&gObjectEventGraphicsInfo_'+name+',')
 layer.stage(p,subs);layer.stage(pinfo,info);layer.stage(ptr,pointers);layer.stage(hdr,header)
 def load(n):
  if n not in maps:maps[n]=json.loads((s/f'data/maps/{n}/map.json').read_text())
  m=maps[n];l=ls[m['layout']];p=l['blockdata_filepath']
  if p not in blocks:
   raw=(s/p).read_bytes();blocks[p]=list(struct.unpack('<'+'H'*(len(raw)//2),raw))
  return m,l,blocks[p]
 def align(n,x,y,gfx):
  m,l,v=load(n);o=next(o for o in m['object_events'] if o['graphics_id']=='OBJ_EVENT_GFX_MR_BRINEYS_BOAT' and o['flag']=='0');old=[o['x'],o['y']]
  for yy in [old[1]-1,old[1]]:
   for xx in [old[0]-1,old[0],old[0]+1]:
    at=yy*l['width']+xx;assert v[at]>>12==1;v[at]&=~0x400
  o.update(x=x,y=y,graphics_id=gfx);sprite=r.sprite('OBJ_EVENT_GFX_MR_BRINEYS_BOAT',0);dx,dy=offsets[gfx];ox=x*16+8-16+dx;oy=y*16+16-32+dy
  cells=sorted({((ox+xx)//16,(oy+yy)//16) for yy in range(32) for xx in range(32) if sprite.getpixel((xx,yy))[3]})
  for xx,yy in cells:
   at=yy*l['width']+xx;assert v[at]>>12==1,(n,xx,yy,'Visible hull on dry pier');v[at]|=0x400
  boats.append(dict(map=n,old=old,anchor=[x,y],graphics=gfx,pixel_offset=[dx,dy],visible_hull_tiles=cells))
 for island in ['One','Two','Three','Four','Five','Six','Seven']:align(island+'Island_Harbor_Frlg',9,6,'OBJ_EVENT_GFX_JOURNEYSEVIIBOAT')
 align('Route104',10,52,'OBJ_EVENT_GFX_JOURNEYPETALBURGBOAT')
 for n,m in maps.items():layer.stage(f'data/maps/{n}/map.json',json.dumps(m,indent=2)+'\n')
 for p,v in blocks.items():layer.stage(p,struct.pack('<'+'H'*len(v),*v))
 return layer.finish(boats=boats,render_pixel_offsets=offsets,native_sprite_art_unchanged=True,one_tile_toward_pier=True,entire_visible_hull_blocked=True,pier_tiles_preserved=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);print(prepare(p.parse_args().source)['layer'])
