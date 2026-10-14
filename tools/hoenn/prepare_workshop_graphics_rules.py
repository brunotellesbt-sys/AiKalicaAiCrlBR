"""Use a true house floor and normal appliance layers in the new workshop."""
import argparse,struct
from pathlib import Path
from candidate_layer import Layer
from prepare_pwt_score_retention import PRIOR,LAYER as PREVIOUS
LAYER='workshop-graphics-rules';PRIOR=PRIOR+[PREVIOUS]
def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if old:=layer.existing():return old
    p='data/layouts/JourneyLavenderWorkshop/map.bin';raw=(layer.source/p).read_bytes()
    values=list(struct.unpack('<'+'H'*(len(raw)//2),raw))
    values=[(tile&~1023)|0x223 if tile&1023==0x246 else (tile&~1023)|0x205 if tile&1023==0x286 else tile for tile in values]
    layer.stage(p,struct.pack('<'+'H'*len(values),*values))
    layer.stage('data/layouts/JourneyLavenderWorkshop/border.bin',struct.pack('<4H',*([0x3E05]*4)))
    p='data/tilesets/secondary/journey_appliances/metatile_attributes.bin'
    raw=bytearray((layer.source/p).read_bytes());raw[400*2:412*2]=bytes(24);layer.stage(p,raw)
    p='src/journey_pwt.c';text=(layer.source/p).read_text()
    anchor='    sPWT.active = sPWT.selecting = sPWT.registration = FALSE; gBattleTypeFlags = 0;'
    assert text.count(anchor)==1
    layer.stage(p,text.replace(anchor,'    ZeroEnemyPartyMons(); // Scores have been resolved; leave no stale opponents.\n'+anchor))
    return layer.finish(native_house_floor=True,appliance_layers_normal=True,pwt_enemy_cleanup_after_scoring=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    print(prepare(p.parse_args().source)['layer'])
