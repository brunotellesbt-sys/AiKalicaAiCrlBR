"""Repair only the damaged native rock quarters around edited ocean exits."""
import argparse,json,struct
from pathlib import Path
from candidate_layer import Layer
from prepare_diglett_galactic_scouts import PRIOR,LAYER as PREVIOUS
LAYER='native-coastal-fragments';PRIOR=PRIOR+[PREVIOUS]
REPAIRS=[('Route105',1,54,0x1558,0x1170),('Route108',34,1,0x551,0x1170),('Route17_Frlg',1,139,0x518,0x112B),('SixIsland_OutcastIsland_Frlg',1,47,0x518,0x112B),('SlateportCity',37,58,0x1170,0x1558)]
def prepare(source):
 layer=Layer(source,LAYER,PRIOR)
 if old:=layer.existing():return old
 s=layer.source;ls={l['id']:l for l in json.loads((s/'data/layouts/layouts.json').read_text())['layouts']};repairs=[]
 for name,x,y,old,new in REPAIRS:
  m=json.loads((s/f'data/maps/{name}/map.json').read_text());l=ls[m['layout']];p=l['blockdata_filepath'];raw=(s/p).read_bytes();v=list(struct.unpack('<'+'H'*(len(raw)//2),raw));at=y*l['width']+x;assert v[at]==old,(name,x,y,hex(v[at]));v[at]=new;layer.stage(p,struct.pack('<'+'H'*len(v),*v));repairs.append(dict(map=name,tile=[x,y],before=old,after=new))
 return layer.finish(repairs=repairs,only_damaged_native_quarters_changed=True,approved_port_tiles_preserved=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);print(prepare(p.parse_args().source)['layer'])
