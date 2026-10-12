"""Complete all twelve crossover encounters through normal field/controller input.

Prior travel/badges and a boosted player team are fixtures; no rival victory or
visit flags are written. This is not a New Game to credits playthrough.
"""
import hashlib,json,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_galactic_chapter.py').read_text().split('\nwins=[]')[0]
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_galactic_chapter.py'),'exec'))
native('VarSet',0x40FF,0)
native('VarSet',0x40FE,0)
rawflag(lib.read16(s['gBadgeFlags'])-7,True) # SYSTEM_FLAGS + 0, calibrated from the compiled badge table.
headers=(source/'src/data/tilesets/headers.h').read_text()
metas=(source/'src/data/tilesets/metatiles.h').read_text()

def attributes(tileset,frlg):
    body=re.search(r'const struct Tileset '+tileset+r'\s*=\s*\{(.*?)\};',headers,re.S)[1]
    symbol=re.search(r'\.metatileAttributes = (\w+)',body)[1]
    path=re.search(r'\b'+symbol+r'\[\].*?"([^"]+)"',metas)[1]
    raw=(source/path).read_bytes()
    return struct.unpack('<'+('I' if frlg else 'H')*(len(raw)//(4 if frlg else 2)),raw)

routes=['Route4_Frlg','Route10_Frlg','Route17_Frlg','Route112','Route113','PetalburgWoods',
        'Route6_Frlg','Route13_Frlg','Route20_Frlg','Route106','Route108','Route125']
wins=[]
# Visit each hero's locations in a different order to exercise independent
# party progression rather than binding the team to a particular route.
for index in [2,8,5,9,1,7,3,11,0,10,4,6]:
    name=routes[index];mapdata=json.loads((source/'data/maps'/name/'map.json').read_text())
    layout=layouts[mapdata['layout']];w,h=layout['width'],layout['height']
    raw=(source/layout['blockdata_filepath']).read_bytes();blocks=struct.unpack('<'+'H'*(len(raw)//2),raw)
    primary=attributes(layout['primary_tileset'],layout['layout_version']=='frlg');secondary=attributes(layout['secondary_tileset'],layout['layout_version']=='frlg')
    cutoff=640 if layout['layout_version']=='frlg' else 512
    behaviors={(primary[value&1023] if value&1023<cutoff else secondary[(value&1023)-cutoff])&255 for value in blocks if not(value>>10&3)}
    ground={behavior for behavior in behaviors if not native('MetatileBehavior_IsSurfableWaterOrUnderwater',behavior)}
    def suitable(x,y):
        value=blocks[y*w+x];mid=value&1023
        behavior=(primary[mid] if mid<cutoff else secondary[mid-cutoff])&255
        return value>>10&3==0 and behavior in ground
    occupied={(o['x'],o['y']) for o in mapdata['object_events']}
    occupied.update((o['x'],o['y']) for o in mapdata.get('coord_events',[]))
    trainers=[o for o in mapdata['object_events'] if o.get('trainer_type') not in [None,'TRAINER_TYPE_NONE']]
    candidates=[]
    for y in range(1,h-1):
        for x in range(1,w-1):
            for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                line=[(x+dx*i,y+dy*i) for i in range(3)]
                if all(0<=xx<w and 0<=yy<h and suitable(xx,yy) and (xx,yy) not in occupied for xx,yy in line) and len({blocks[yy*w+xx]>>12 for xx,yy in line})==1 and all(abs(x-o['x'])+abs(y-o['y'])>int(o.get('trainer_sight_or_berry_tree_id',0))+2 for o in trainers):
                    candidates.append((x,y))
    assert candidates,('No walkable approach for mandatory rival',name)
    # Ending the warp fixture lets the normal on-frame hook spawn and approach.
    x,y=candidates[len(candidates)//2]
    native('HealPlayerParty')
    for member,move in enumerate([57,337,309]):
        for slot in range(4):native('ScriptSetMonMoveSlot',member,move if slot==0 else 0,slot)
    warp(name,x,y)
    step(50)
    win=one_battle(name)
    expected=native('VarGet',0x40FF)
    assert expected&(1<<index),(name,expected)
    win.update(map=name,visit_bit=index,visit_mask=expected,approach=[x,y])
    wins.append(win);print('Crossover visit complete:',name,flush=True)
assert native('JourneyCrossoverComplete')==1
assert native('VarGet',0x40FF)==4095
assert hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest()==sha
lib.stop()
(args.output/'crossover-visits.json').write_text(json.dumps(dict(passed=True,rom_sha256=sha,wins=wins,
    native_victories=True,normal_field_hook_and_approach=True,visit_flags_not_written=True,
    initial_badges_travel_and_team_are_fixtures=True,player_battle_stats_boosted=True,
    full_campaign_playthrough=False),indent=2)+'\n')
