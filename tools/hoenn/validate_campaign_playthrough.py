"""Controller-only campaign runner. Reports actual progress, never fixture wins."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--source',type=Path,required=True);p.add_argument('--library',type=Path,required=True)
p.add_argument('--output',type=Path,required=True);p.add_argument('--region',choices=['kanto','hoenn'],required=True)
a=p.parse_args();region=a.region
sys.argv=[sys.argv[0],'--source',str(a.source),'--library',str(a.library),'--output',str(a.output)]
exec(compile((ROOT/'tools/hoenn/validate_crossing.py').read_text().split('\nstep(900)\n')[0],str(ROOT/'tools/hoenn/validate_crossing.py'),'exec'))
# Only reads and controller frames are used. No native calls, warps or RAM writes.
inputs=[];checkpoints=[];battles=[]
by_location={(g,i):n for g,label in enumerate(groups['group_order']) for i,n in enumerate(groups[label])}
def action(key=1,held=1,pause=45):
    inputs.append(dict(key=key,held_frames=held,pause_frames=pause))
    step(held,key);step(pause)
def valid_save():return 0x02000000<=save()<0x02040000
def map_name():return by_location.get(location()) if valid_save() else None
def badge_counts():
    bank=[lib.read16(s['gBadgeFlags']+i*2) for i in range(8)]
    def count(flags):return sum(bool(lib.read8(save()+4720+f//8)&(1<<(f&7))) for f in flags)
    return dict(kanto=count(range(0x1AB0,0x1AB8)),hoenn=count(bank))
def checkpoint(label):
    picture(label)
    checkpoints.append(dict(label=label,map=map_name(),position=list(position()) if valid_save() else None,badges=badge_counts(),party_count=lib.read8(s['gPartiesCount'])))
def callback():return lib.read32(s['gMain']+4)&~1
def locked():return bool(lib.read8(s['sLockFieldControls']))
step(600)
if region=='kanto':action(4,1,180)
for i in range(240):
    action(8 if i<3 else 1)
    if map_name()=='InsideOfTruck' and callback()==s['CB2_Overworld'] and not locked():break
checkpoint('01-truck')
assert map_name()=='InsideOfTruck', ('New Game not in truck',region,map_name())
# Cross the actual truck door; dialogue is advanced with A.
for _ in range(35):
    action(16,8,20)
    if map_name()!='InsideOfTruck':break
for _ in range(90):
    action()
    if callback()==s['CB2_Overworld'] and not locked():break
checkpoint('02-arrival')
expected='PalletTown_PlayersHouse_2F_Frlg' if region=='kanto' else 'LittlerootTown_BrendansHouse_1F'
assert map_name()==expected,(region,map_name(),position())
from collections import deque
import struct
map_data={}
for path in (source/'data/maps').glob('*/map.json'):
    d=json.loads(path.read_text());map_data[path.parent.name]=d

def task(name):
    if name not in s:return False
    return any(lib.read8(s['gTasks']+i*40+4) and lib.read32(s['gTasks']+i*40)&~1==s[name] for i in range(16))
def settle():
    active=False
    for i in range(1500):
        if callback()==s['BattleMainCB2']:
            active=True
        elif active and callback()==s['CB2_Overworld']:
            battles.append(dict(outcome=lib.read8(s['gBattleOutcome']),normal_stats=True))
            active=False
        if task('Task_SetClock_HandleConfirmInput'):
            action(64);action()
        elif callback()==s.get('CB2_NamingScreen'):
            action(8);action()
        else:action()
        if i>=15 and callback()==s['CB2_Overworld'] and not locked(): return
    picture('field-script-unfinished')
    raise AssertionError(('Field script did not settle',map_name(),position()))
def walk_local(goal):
    initial=map_name();layout=layouts[map_data[initial]['layout']]
    width,height=layout['width'],layout['height']
    rawtiles=(source/layout['blockdata_filepath']).read_bytes()
    tiles=struct.unpack('<'+'H'*(width*height),rawtiles)
    blocked_tiles=set()
    for _ in range(180):
        if map_name()!=initial:return
        start=position()
        if start==goal:return
        objects=set(blocked_tiles)
        for i in range(16):
            addr=s['gObjectEvents']+36*i
            if lib.read8(addr)&1 and lib.read8(addr+8)!=255:
                objects.add((lib.read16(addr+16)-7,lib.read16(addr+18)-7))
        queue=deque([start]);prev={start:None}
        while queue and goal not in prev:
            point=queue.popleft()
            for dx,dy,key in [(1,0,16),(-1,0,32),(0,1,128),(0,-1,64)]:
                nxt=(point[0]+dx,point[1]+dy)
                x,y=nxt
                if not(0<=x<width and 0<=y<height) or nxt in prev or nxt in objects:continue
                if tiles[y*width+x]&0xC00:continue
                prev[nxt]=(point,key);queue.append(nxt)
        if goal not in prev:raise AssertionError(('No walking path',initial,start,goal))
        point=goal
        while prev[point][0]!=start:point=prev[point][0]
        before=position();action(prev[point][1],8,30)
        if locked():settle()
        if map_name()==initial and position()==before:
            action(prev[point][1],24,30)
            if locked():settle()
            if map_name()==initial and position()==before:blocked_tiles.add(point)
    picture('walking-stalled')
    raise AssertionError(('Walking stalled',initial,position(),goal))
if region=='kanto':
    walk_local((10,2));action(32,24,180);settle()
    checkpoint('03-house-downstairs')
    walk_local((8,5));action(64,1,20);action();settle()
    checkpoint('04-family')
    walk_local((4,8));action(128,24,180);settle()
    assert map_name()=='PalletTown_Frlg',map_name()
    walk_local((12,1));step(180);settle()
    checkpoint('05-oak-introduction')
    assert map_name()=='PalletTown_ProfessorOaksLab_Frlg',map_name()
    walk_local((9,5));action(64,1,20);action();settle()
    checkpoint('06-starter')
    assert lib.read8(s['gPartiesCount'])==1
    walk_local((6,8));step(180);settle()
    checkpoint('07-first-rival-battle')
    assert battles and all(b['outcome']==1 for b in battles),battles

else:
    walk_local((8,2));action(16,24,180);settle()
    checkpoint('03-house-upstairs')
    walk_local((5,2));action(64,1,20);action();settle()
    checkpoint('04-clock-and-mother')
    walk_local((7,1));action(16,24,180);settle()
    checkpoint('05-tv-report')
    walk_local((8,8));action(128,24,180);settle()
    assert map_name()=='LittlerootTown',map_name()
    walk_local((14,9));action(64,24,180);settle()
    walk_local((2,2));action(32,24,180);settle()
    walk_local((4,4));action(16,1,20);action();settle()
    checkpoint('06-rival-introduction')
    walk_local((1,1));action(32,24,180);settle()
    walk_local((1,6));action(128,64,180);settle()
    assert map_name()=='LittlerootTown',map_name()
    walk_local((11,0));action(64,32,180);settle()
    assert map_name()=='Route101',map_name()
    checkpoint('07-birch-danger')
    walk_local((7,15));action(64,1,20);action();settle()
    checkpoint('08-birch-rescue-and-starter')
    assert lib.read8(s['gPartiesCount'])==1
    assert battles and all(b['outcome']==1 for b in battles),battles



report=dict(rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
    starting_region=region,controller_only=True,ram_writes=False,script_injection=False,
    synthetic_badges=False,boosted_stats=False,disabled_wild_encounters=False,
    checkpoints=checkpoints,battles=battles,input_log=inputs,full_campaign_playthrough=False,
    runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    status='initial_segment_passed_campaign_incomplete',next_required='Original starter, family gifts, regional missions, sixteen gyms and both Hall of Fame')
(args.output/'campaign-playthrough.json').write_text(json.dumps(report,indent=2)+'\n')
lib.stop()
print('Controller-only initial segment:',region,checkpoints,flush=True)
