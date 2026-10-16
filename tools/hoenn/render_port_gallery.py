"""Render native map blocks and permanent ferry actors, with no concept artwork."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from render_sea_maps import MapRenderer
BOXES={
 'PalletTown_Frlg':('Pallet',(0,12,26,30)), 'Route19_Frlg':('Fuchsia / Route 19',(0,7,18,23)),
 'VermilionCity_Frlg':('Vermilion',(29,23,40,36)),
 'MossdeepCity':('Mossdeep - ilha oeste',(0,23,12,36)), 'CinnabarIsland_Frlg':('Cinnabar',(0,7,24,20)),
 'Route25_Frlg':('Route 25',(50,1,72,20)), 'JourneyRoute12Shipyard':('Lavender',(16,32,40,46)),
 'SootopolisCity':('Sootopolis',(17,33,26,44)), 'DewfordTown':('Dewford',(8,5,19,14)),
 'Route104':('Petalburg coast',(3,44,24,59)), 'PacifidlogTown':('Pacifidlog',(6,22,18,33)),
 'BattleFrontier_OutsideWest':('Battle Frontier',(14,64,30,74)),
 'SlateportCity_Harbor':('Slateport',(0,0,24,15)), 'LilycoveCity_Harbor':('Lilycove',(0,0,24,15)),
 **{i+'Island_Harbor_Frlg':(i+' Island',(4,0,17,9)) for i in ['One','Two','Three','Four','Five','Six','Seven']}}

def gallery(source,output):
 source=Path(source);output=Path(output);output.mkdir(parents=True,exist_ok=True);r=MapRenderer(source);records=[]
 boats={'OBJ_EVENT_GFX_SEAGALLOP','OBJ_EVENT_GFX_MR_BRINEYS_BOAT','OBJ_EVENT_GFX_SS_TIDAL','OBJ_EVENT_GFX_SEAGALLOP','OBJ_EVENT_GFX_JOURNEY_SUBMARINE','OBJ_EVENT_GFX_JOURNEYSEVIIBOAT','OBJ_EVENT_GFX_JOURNEYPETALBURGBOAT'}
 for n,(title,box) in BOXES.items():
  im,m=r.render(n,npcs=False)
  for o in sorted(m['object_events'],key=lambda o:o['y']):
   if str(o['flag'])!='0' or not ('FerryPort' in o['script'] or 'LavenderNetwork_Service' in o['script'] or o['graphics_id'] in boats):continue
   frame=2 if o['graphics_id']=='OBJ_EVENT_GFX_MR_BRINEYS_BOAT' and o['movement_type'] in ['MOVEMENT_TYPE_FACE_LEFT','MOVEMENT_TYPE_FACE_RIGHT'] else 0
   sprite=r.sprite(o['graphics_id'],frame);dx,dy=r.sprite_offset(o['graphics_id']);im.paste(sprite,(o['x']*16+8-sprite.width//2+dx,o['y']*16+16-sprite.height+dy),sprite)
  im=im.crop(tuple(x*16 for x in box));im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST).save(output/(n+'.png'))
  records.append(dict(map=n,title=title,file=n+'.png',crop=list(box),blockdata_sha256=hashlib.sha256((source/r.layouts[m['layout']]['blockdata_filepath']).read_bytes()).hexdigest(),actors='permanent ferry actors; story flags are not simulated'))
 font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',19)
 groups={'kanto':['PalletTown_Frlg','Route19_Frlg','VermilionCity_Frlg','CinnabarIsland_Frlg','Route25_Frlg','JourneyRoute12Shipyard'],
 'hoenn-casas':['MossdeepCity','SootopolisCity','DewfordTown','Route104','PacifidlogTown','BattleFrontier_OutsideWest'],
 'hoenn-navios':['SlateportCity_Harbor','LilycoveCity_Harbor'], 'sevii':['OneIsland_Harbor_Frlg']}
 for label,names in groups.items():
  page=Image.new('RGB',(800,390*((len(names)+1)//2)),(24,32,48));d=ImageDraw.Draw(page)
  for i,n in enumerate(names):
   x=(i%2)*400;y=(i//2)*390;d.text((x+10,y+8),BOXES[n][0],font=font,fill='white');im=Image.open(output/(n+'.png'));scale=min(380/im.width,345/im.height);im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST);page.paste(im,(x+(400-im.width)//2,y+40+(345-im.height)//2))
  page.save(output/(label+'.png'))
 (output/'index.json').write_text(json.dumps(records,indent=2)+'\n')
 body='# Portos: galeria atual\n\nImagens renderizadas dos tiles e sprites utilizados na ROM. Exibem os atores permanentes do transporte; NPCs condicionados pela história não são simulados.\n\n'
 for row in records:body+='## '+row['title']+'\n\n!['+row['title']+'](images/port-update/'+row['file']+')\n\n'
 body+='## Sala do Rotom\n\nMantida com o visual nativo da Torre de Lavender.\n\n![Sala do Rotom](images/stage-one/Rotom-final.png)\n'
 (output.parents[1]/'PORTOS-GALERIA.md').write_text(body)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();gallery(a.source,a.output)
