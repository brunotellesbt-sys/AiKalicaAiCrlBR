"""Choose Sevii and an island with controller input, from a fresh game."""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--source',type=Path,required=True);p.add_argument('--library',type=Path,required=True)
p.add_argument('--output',type=Path,required=True);p.add_argument('--island',type=int,choices=range(7),default=0)
p.add_argument('--start-region',choices=['hoenn','kanto','sevii'],default='sevii')
p.add_argument('--city',type=int)
p.add_argument('--avatar',type=int,choices=range(4),default=0)
options=p.parse_args();island=options.island
destination_region=options.start_region;choice=options.city if options.city is not None else island
assert 0<=choice<{'hoenn':15,'kanto':9,'sevii':7}[destination_region]
sys.argv=[sys.argv[0],'--source',str(options.source),'--library',str(options.library),'--output',str(options.output),'--region','kanto']
bootstrap=(ROOT/'tools/hoenn/validate_campaign_playthrough.py').read_text().split('step(600)')[0].replace('4720','FLAG_OFFSET')
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_campaign_playthrough.py'),'exec'))
region_chosen=city_chosen=False
avatar_chosen=not (source/'.journey-player-choice').exists()
def active(name):
    return any(lib.read8(s['gTasks']+j*40+4) and lib.read32(s['gTasks']+j*40)&~1==s[name] for j in range(16))
step(600)
picture('journey-title')
for i in range(360):
    if not region_chosen and active('Task_HandleMultichoiceInput'):
        step(30);picture('choose-hoenn-kanto-sevii')
        for _ in range({'hoenn':0,'kanto':1,'sevii':2}[destination_region]):action(128)
        action();region_chosen=True
        continue
    if map_name()=='InsideOfTruck':
        if not avatar_chosen and active('Task_HandleMultichoiceInput'):
            step(30);picture('choose-red-leaf-brendan-may')
            for _ in range(options.avatar):action(128)
            action();avatar_chosen=True
            continue
        if region_chosen and not city_chosen and active('Task_HandleMultichoiceInput' if destination_region=='sevii' else 'Task_HandleMultichoiceGridInput'):
            step(30);picture('choose-home-town')
            for _ in range(choice if destination_region=='sevii' else choice//3):action(128)
            if destination_region!='sevii':
                for _ in range(choice%3):action(16)
            action();city_chosen=True
    action(8 if i<3 else 1)
    if region_chosen and city_chosen and map_name()=='InsideOfTruck' and callback()==s['CB2_Overworld'] and not locked():break
assert region_chosen and city_chosen,(region_chosen,city_chosen,map_name())
for _ in range(35):
    action(16,8,20)
    if map_name()!='InsideOfTruck':break
for _ in range(120):
    action()
    if callback()==s['CB2_Overworld'] and not locked():break
home_index=choice+{'kanto':0,'hoenn':16,'sevii':9}[destination_region]
home_id=json.loads((source/'.journey-birth').read_text())['homes'][home_index]['bedroom_map']
expected=next(p.parent.name for p in (source/'data/maps').glob('*/map.json') if json.loads(p.read_text())['id']==home_id)
assert map_name()==expected,(island,map_name(),position())
checkpoint('selected-sevii-home-arrival')
assert lib.read8(s['gPartiesCount'])==0
if (source/'.journey-player-choice').exists():
    import subprocess,tempfile,re
    with tempfile.TemporaryDirectory(dir='/tmp') as temp:
        out=Path(temp)/'probe.s'
        probe='#include "global.h"\n#include <stddef.h>\n#include "constants/event_objects.h"\nconst u32 probe[]={offsetof(struct SaveBlock1,vars),offsetof(struct SaveBlock2,playerGender),offsetof(struct ObjectEvent,graphicsId),OBJ_EVENT_GFX_RED_NORMAL,OBJ_EVENT_GFX_GREEN_NORMAL,OBJ_EVENT_GFX_BRENDAN_NORMAL,OBJ_EVENT_GFX_MAY_NORMAL};'
        subprocess.run([str(ROOT/'.local/arm-gcc/usr/bin/arm-none-eabi-gcc'),'-S','-mabi=apcs-gnu','-iquote',str(source/'include'),'-x','c','-','-o',str(out)],input=probe,text=True,check=True)
        var_offset,gender_offset,gfx_offset,*graphics=[int(n) for n in re.findall(r'\.word\s+(\d+)',out.read_text())]
    assert lib.read16(save()+var_offset+(0x405F-0x4000)*2)==options.avatar+1
    assert lib.read8(lib.read32(s['gSaveBlock2Ptr'])+gender_offset)==options.avatar%2
    player=s['gObjectEvents']+lib.read8(s['gPlayerAvatar']+5)*36
    assert lib.read16(player+gfx_offset)==graphics[options.avatar],('Wrong overworld protagonist',options.avatar,lib.read16(player+gfx_offset),graphics)
home=map_name();lib.stop()
(args.output/'sevii-opening.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),starting_region=destination_region,protagonist=['Red','Leaf','Brendan','May'][options.avatar],protagonist_choice_and_overworld_match=avatar_chosen,city_index=choice,island=island+1 if destination_region=='sevii' else None,home=home,explicit_region_and_island_choice=True,controller_only=True,ram_writes=False,script_injection=False,checkpoints=checkpoints,input_log=inputs,full_campaign_playthrough=False),indent=2)+'\n')
print('Controller-only starting home passed:',destination_region,choice,expected,flush=True)
