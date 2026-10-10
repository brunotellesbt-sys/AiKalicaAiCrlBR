"""Audit coastal water components and walk from Mossdeep through the new sea."""
from pathlib import Path
import hashlib,json,struct
ROOT=Path(__file__).resolve().parents[2]
prefix=(ROOT/'tools/hoenn/validate_coast_connectivity.py').read_text().split('required={')[0]
exec(compile(prefix,str(ROOT/'tools/hoenn/validate_coast_connectivity.py'),'exec'))
active_seas={r['map'] for r in json.loads((source/'.journey-sea-landscapes').read_text())['maps']}
active_seas.update(r['map'] for r in json.loads((source/'.journey-kanto-open-sea').read_text())['landscape'])
active_seas.update(r['map'] for r in report['rectangles'] if r['map'].startswith('Journey'))
required=sorted(active_seas | {'MossdeepCity','Route124','Route125','Route126','Route127','Route128','Route129','Route130','Route131','Route105','Route106','Route107','Route108','Route109'})
# Dock water pockets connect by walking across the wooden piers and reusing
# Surf, covered by validate_kanto_open_sea, rather than pure-water adjacency.
components=[]
for n in required:
    w,h,_=blocks[n];left=set(passable[n]);sizes=[]
    while left:
        i=left.pop();area={i};q=deque([i])
        while q:
            t=q.popleft();x,y=t%w,t//w
            for dx,dy,_ in keys:
                xx,yy=x+dx,y+dy;u=yy*w+xx
                if 0<=xx<w and 0<=yy<h and u in left:left.remove(u);area.add(u);q.append(u)
        # Exclude tiny decoration pools and native Dive wells. Every actual
        # sea basin, not merely one tile per map, must join the shared network.
        if len(area)>=64:
            assert all((n,i%w,i//w) in reachable for i in area),('Enclosed coastal basin',n,len(area))
            sizes.append(len(area))
    components.append(dict(map=n,large_water_components=sizes,all_large_components_connected=True))
print('All navigable sea basins connected:',len(components),'maps',flush=True)
# Controller movement starts at the actual southwest coast of Mossdeep.
def place(name,x,y):
    g,num=map_id(name);script(b'\x39'+bytes([g,num,255])+struct.pack('<HH',x,y)+b'\x27\x6b\x02',frames=240)
    for _ in range(60):
        if idle():break
        step(8)
    assert idle() and location()==(g,num) and position()==(x,y)
w,h,_=blocks['MossdeepCity']
_,sy,sx=min((abs(x-30)+abs(y-30),y,x) for y in range(h) for x in range(w) if y*w+x in passable['MossdeepCity'])
start=('MossdeepCity',sx,sy);place(*start);native('SetPlayerAvatarTransitionFlags',8);step(30)
legs=[]
for n,x,y in [
    ('Route125',12,31),('Route124',10,50),('Route125',7,10),('Route125',77,22),
    ('JourneyHoennNorthSea',40,22),('JourneyMossdeepOuterSea',100,20),
    ('JourneyHoennMiddleSea',95,30),('JourneyEverGrandeBackSea',30,20),
    ('JourneyEverGrandeBackSouthSea',30,20),('JourneyHoennSouthSea',90,12),
    ('JourneyHoennSouthEastSea',40,12),('JourneyWorldSea06',12,20),
    ('JourneyWorldLane11',8,30),('JourneyWorldSea04',12,36),
    ('JourneyWorldSea01',50,22),('JourneyWorldSea02',44,22),('JourneyWorldSea03',10,22),
    ('JourneyWorldSea02',44,22),('JourneyWorldSea01',50,22),
    ('JourneyEverGrandeBackSea',80,20),('JourneyHoennMiddleSea',100,30),
    ('JourneyMossdeepOuterSea',100,20),('JourneyHoennNorthSea',40,22),start]:
    w,h,vals=blocks[n]
    if y*w+x not in passable[n]:
        _,y,x=min((abs(xx-x)+abs(yy-y),yy,xx) for yy in range(3,h-3) for xx in range(3,w-3) if yy*w+xx in passable[n])
    walk((n,x,y));legs.append(dict(map=n,position=list(position())))
    if n in ['Route125','JourneyHoennNorthSea','JourneyWorldSea02']:picture(n+'-open-surf')
    print('Continuous Mossdeep Surf arrival:',n,position(),flush=True)
assert location()==map_id(start[0]) and position()==start[1:]
lib.stop()
(args.output/'surf-passages.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),components=components,minimum_audited_basin_tiles=64,mossdeep_original_rock_enclosures_open=True,controller_surf_roundtrip=True,no_midroute_warps=True,legs=legs,transitions=transitions,initial_position_party_and_defeated_trainer_flags_are_fixtures=True,full_campaign_playthrough=False),indent=2)+'\n')
