"""Add a small Galactic scouting party to the actual Vermilion/Pewter tunnel."""
import argparse,json
from pathlib import Path
from candidate_layer import Layer
from prepare_connected_sea_chart import PRIOR,LAYER as PREVIOUS
LAYER='diglett-galactic-scouts';PRIOR=PRIOR+[PREVIOUS]
SPEECHES=[
 [('We are TEAM GALACTIC.','We are exploring the KANTO region.'),('This tunnel connects ROUTE 11','to ROUTE 2. A useful passage.'),('We are mapping underground routes.','You can pass. Stay out of our work!')],
 [('The DIGLETT made this tunnel.','Their burrows reach across KANTO.'),('Our orders are to explore the area','and report unusual readings.'),('Do not disturb the POKEMON.','We need this passage intact.')],
 [('We came to explore KANTO.','The commander wants a full report.'),('This end leads toward ROUTE 2.','VERMILION is at the other end.'),('Strange energy has been detected.','That is all I am allowed to say.')],
]
def prepare(source):
 layer=Layer(source,LAYER,PRIOR)
 if old:=layer.existing():return old
 s=layer.source;n='DiglettsCave_B1F_Frlg';p=f'data/maps/{n}/map.json';m=json.loads((s/p).read_text());assert not m['object_events'];objects=[]
 for i,(x,y) in enumerate([(70,60),(45,38),(15,19)]):
  obj=dict(graphics_id='OBJ_EVENT_GFX_JOURNEY_GALACTIC_GRUNT_'+('F' if i==1 else 'M'),x=x,y=y,elevation=3,movement_type='MOVEMENT_TYPE_FACE_DOWN',movement_range_x=0,movement_range_y=0,trainer_type='TRAINER_TYPE_NONE',trainer_sight_or_berry_tree_id='0',script='JourneyDiglettGalactic_Scout'+str(i),flag='0');m['object_events'].append(obj);objects.append(obj)
 layer.stage(p,json.dumps(m,indent=2)+'\n')
 p='data/scripts/journey_galactic.inc';t=(s/p).read_text()
 for i,pages in enumerate(SPEECHES):
  t+='\nJourneyDiglettGalactic_Scout'+str(i)+'::\n\tmsgbox JourneyDiglettGalactic_Text'+str(i)+', MSGBOX_NPC\n\tend\nJourneyDiglettGalactic_Text'+str(i)+'::\n'
  for j,(a,b) in enumerate(pages):t+='\t.string "'+a+'\\n"\n\t.string "'+b+('\\p' if j<len(pages)-1 else '$')+'"\n'
 layer.stage(p,t)
 return layer.finish(map=n,scouts=objects,role='Kanto exploration dialogue',native_tunnel_tiles_and_exits_preserved=True,rock_tunnel_magma_mission_preserved=True,not_a_new_mandatory_mission=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);print(prepare(p.parse_args().source)['layer'])
