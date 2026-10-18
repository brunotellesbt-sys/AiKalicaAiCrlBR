"""Walk every repaired marine link in both directions, with actual Surf state.

Inter-trip placements, party/story flags, native encounter suppression and noon
are fixtures. Travel within each trip uses only directional/controller input.
"""
import ctypes
import os
import hashlib
import json
import re
import struct
import subprocess
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
prefix=(ROOT/'tools/hoenn/validate_team_missions.py').read_text().split('\nassert pending(True) == 7')[0]
exec(compile(prefix,__file__,'exec'))
report=json.loads((source/'.journey-extra-gyms').read_text())['coastal_fixes']
allmaps={p.parent.name:json.loads(p.read_text()) for p in (source/'data/maps').glob('*/map.json')}
names=sorted(n for n,m in allmaps.items() if m['map_type'] in ['MAP_TYPE_ROUTE','MAP_TYPE_CITY','MAP_TYPE_TOWN','MAP_TYPE_OCEAN_ROUTE'] or m.get('connections'))
allowed=set();walk_prefix='surf-repair';walk_cache_paths=True;walk_transition_pictures=False;walk_max_ticks=6000
walk_surf_under_bridges=True
native('VarSet',0x40FE,7)
for tid in range(1,1589):rawflag(0x500+tid,True)
for i in range(25):rawflag(0x1000+i,True)
for i in range(9):rawflag(0x1AC3+i,True)
native('RtcInitLocalTimeOffset',12,0)
native('VarSet',0x4021,65535);native('VarSet',0x4120,65535)
scene=int(re.search(r'#define\s+VAR_MAP_SCENE_ONE_ISLAND_HARBOR\s+(0x\w+)',(source/'include/constants/vars.h').read_text())[1],16)
native('VarSet',scene,3)
vars_text=(source/'include/constants/vars.h').read_text()
for scene_name in ['VAR_MAP_SCENE_FOUR_ISLAND','VAR_JOURNEY_RIVAL_VISITS']:
    match=re.search(r'^#define\s+'+scene_name+r'\s+(0x\w+)',vars_text,re.M)
    if match:native('VarSet',int(match[1],16),4095 if 'VISITS' in scene_name else 1)
exec(compile((ROOT/'tools/hoenn/native_water_walk.py').read_text(),'surf-repair-native-walker','exec'))
for n,(w,h,tiles) in blocks.items():
    passable[n]={i for i in passable[n] if not tiles[i]&0xC00 and water_behaviors[behaviors[n][i]]}
    warps[n]={}
water_passable={n:v.copy() for n,v in passable.items()}
# Faster input cadence, still waiting on native steps. Preserve valid local
# coordinates while a camera seam publishes its new map ID.
walker=(ROOT/'tools/hoenn/native_water_walk.py').read_text().split('\ndef walk(goal):',1)[1]
walker='def walk(goal):'+walker
walker=walker.replace('step(30)','step(2)').replace('step(12)','step(1)')
walker=walker.replace('        now = (by_location[location()], *position())', '        now = (by_location[location()], *position())\n        if now[0] != last[0]:\n            step(30)\n            now = (by_location[location()], *position())')
walker=walker.replace('        if tick % 100 == 0:',
    '        width,height,_=blocks[now[0]]\n'
    '        if not (0<=now[1]<width and 0<=now[2]<height):\n'
    '            step(1)\n'
    '            continue\n'
    '        if tick % 100 == 0:')
exec(compile(walker,'surf-repair-controller-walker','exec'))
nav=(source/'src/data/journey_world_position.h').read_text()
grids={}
for index,m in enumerate(re.findall(r'\{\d+, \(MAP_GROUP\((MAP_\w+)\)<<8\)\|MAP_NUM\(MAP_\w+\), \d+, \d+\}',nav)):
    if m not in by_id:continue
    at=s['sWorldTileGrids']+index*12;name=by_id[m]
    grids[name]=(lib.read32(at),lib.read16(at+6),lib.read16(at+8))
last_map=None;visited=[];samples=[];aprons=0

def marker(n,x,y):
    first,w,h=grids[n];p=lib.read16(s['sWorldNavigationPixels']+2*(first+y*w+x));return [p&255,p>>8]
def loaded_word(x,y):
    width=lib.read32(s['gBackupMapLayout']);ptr=lib.read32(s['gBackupMapLayout']+8)
    return lib.read16(ptr+(x+7+(y+7)*width)*2)
def observe(before,after):
    global last_map,aprons
    n,x,y=after;w,h,tiles=blocks[n]
    if not(0<=x<w and 0<=y<h):return
    assert lib.read8(s['gPlayerAvatar'])&8,('Surf lost on water',after)
    expected=tiles[y*w+x];actual=loaded_word(x,y)
    assert actual==expected,('Foreign-bank tile survived map transition',after,hex(actual),hex(expected))
    assert water_behaviors[behaviors[n][y*w+x]],('Surf on land',after)
    p=marker(n,x,y)
    if samples:assert max(abs(a-b) for a,b in zip(p,samples[-1]['marker']))<=4,('Cursor jump at a physical seam',samples[-1],after,p)
    samples.append(dict(map=n,tile=[x,y],marker=p))
    if last_map!=n:
        visited.append(n);last_map=n
        # A screenshot records the real loaded bank, not a source-map render.
        if len(visited)<=12:picture('seam-'+str(len(visited)))
    aprons+=1
walk_observer=observe

def boundary(n,d,t,depth=0):
    w,h,_=blocks[n];return (depth if d=='left' else w-1-depth,t) if d in ['left','right'] else (t,depth if d=='up' else h-1-depth)
def palette():return [lib.read16(0x05000000+(64+i)*2) for i in [3,4,5,7]]
checks=[]
for index,link in enumerate(report['geography']['repaired_links']):
    if os.environ.get('SURF_DEBUG_LINK') and index!=int(os.environ['SURF_DEBUG_LINK']):continue
    n,o,d=link['source'],link['destination'],link['direction'];off=link['old_offset']
    choices=[]
    for t in range(link['start'],link['start']+link['span']):
        a=boundary(n,d,t,1);b=boundary(o,{'left':'right','right':'left','up':'down','down':'up'}[d],t-off,1)
        if a[1]*blocks[n][0]+a[0] in water_passable[n] and b[1]*blocks[o][0]+b[0] in water_passable[o]:choices.append((a,b))
    assert choices,('No water crossing remains',link)
    a,b=choices[len(choices)//2];chain={n,o,*link['segments']}
    passable={name:v.copy() if name in chain else set() for name,v in water_passable.items()}
    warp(n,*a);native('SetPlayerAvatarTransitionFlags',8);step(60)
    before_palette=palette();last_map=n;visited=[n];samples=[];observe(None,(n,*a))
    walk((o,*b));step(60);observe(None,(o,*b))
    assert set(link['segments'])<=set(visited),('A route skipped its physical water rectangles',link,visited)
    assert palette()==before_palette,('Ocean palette cut at repaired link',n,o,before_palette,palette())
    outbound=visited.copy()
    try:walk((n,*a))
    except AssertionError:
        print('Native blocked edge details',location(),position(),[(x,native('MapGridGetMetatileIdAt',x+7,6),native('MapGridGetCollisionAt',x+7,6)) for x in range(blocks[by_location[location()]][0])],flush=True)
        raise
    step(60);observe(None,(n,*a))
    assert lib.read8(s['gPlayerAvatar'])&8
    assert palette()==before_palette
    # The real reef next to a new passage must block held directional input.
    first=link['segments'][0];ww,hh,tiles=blocks[first]
    blocked_edge=next(((x,y,key,xx,yy) for x,y,key,xx,yy in [(1,hh//2,32,0,hh//2),(ww-2,hh//2,16,ww-1,hh//2),(ww//2,1,64,ww//2,0),(ww//2,hh-2,128,ww//2,hh-1)] if tiles[yy*ww+xx]&0xC00 and y*ww+x in passable[first]),None)
    reef=False
    if blocked_edge:
        x,y,key,xx,yy=blocked_edge;walk((first,x,y));step(60);pos=position();step(90,key);step(60);assert position()==pos,(first,'Reef crossed');reef=True
    checks.append(dict(source=n,destination=o,outbound_maps=outbound,returned_to_departure=True,
        all_segments_walked=True,surf_continuous=True,loaded_tiles_match_current_bank=True,ocean_colors_identical=True,
        whole_reef_blocks_controller=reef,old_center_steps=link['old_center_steps'],new_water_steps=link['new_real_center_steps'],chart_pixels=link['chart_pixels']))
    print('Repaired Surf link passed',index+1,n,'->',o,flush=True)
# Inspect generated Solrock parties through the same function that builds all
# trainer battles. The species learnset itself remains unchanged.
from audit_battle_database import compiled
base=s['gTrainers']+abi[12]*abi[11]*abi[0]
# Force the vanilla Tate/Liza Solrock seed via its real trainer record.
tid=int(re.search(r'#define TRAINER_TATE_AND_LIZA_1\s+(\d+)',(source/'include/constants/opponents.h').read_text())[1])
solrock_checks=[]
for level in [6,25,50,80]:
    for i in range(6*abi[2]):lib.write8(party+i,0)
    lib.write8(s['gPartiesCount'],0);native('ScriptGiveMon',6,level,0)
    warp('MossdeepCity_Gym',14,17)
    count=native('CreateNPCTrainerPartyFromTrainer',enemy,base+tid*abi[0],0,abi[10])
    for i in range(count):
        mon=enemy+i*abi[2]
        if native('GetMonData3',mon,abi[7],0)!=338:continue
        moveset=[native('GetMonData3',mon,pabi[19]+j,0) for j in range(4)]
        assert 394 not in moveset
        solrock_checks.append(dict(level=level,moves=moveset))
assert solrock_checks
lib.stop()
(args.output/'surf-repairs.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
    checks=checks,links=len(checks),crossings=len(checks)*2,apron_samples=aprons,
    all_repaired_links_walked_bidirectionally=True,no_midtrip_warps_or_coordinate_writes=True,
    surf_and_current_bank_checked_at_each_step=True,initial_progress_party_and_travel_are_fixtures=True,
    actual_controller_movement=True,solrock_loadout_checks=solrock_checks,
    atlas_graphics_changed=False,full_campaign_playthrough=False),indent=2)+'\n')
