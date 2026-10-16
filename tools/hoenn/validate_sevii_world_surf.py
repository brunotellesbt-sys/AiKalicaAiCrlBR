"""Sail One Island to Kanto and Hoenn and back using continuous native Surf."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_sevii_surf_connections.py').read_text().split('\nstart=nearest(')[0]
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_sevii_surf_connections.py'),'exec'))
for n,valid in passable.items():
    passable[n]={i for i in valid if water_behaviors[behaviors[n][i]] and not blocks[n][2][i]&0xC00
        and (blocks[n][2][i]>>12==1 or blocks[n][2][i]>>12==0 and bridge_behaviors[behaviors[n][i]])}
origin=nearest('OneIsland_Harbor_Frlg',2,10,True)
native('VarSet',scene,3)
warp(*origin);native('SetPlayerAvatarTransitionFlags',8);step(30)
trips=[]
for region,name,x,y in [('KANTO','JourneyRoute12Shipyard',45,45),('HOENN','Route124',32,20)]:
    goal=nearest(name,x,y,True);before=walked;old_transitions=len(transitions)
    walk(goal);assert lib.read8(s['gPlayerAvatar'])&8
    picture('one-island-to-'+region.lower())
    walk(origin);assert lib.read8(s['gPlayerAvatar'])&8
    picture(region.lower()+'-return-to-one-island')
    trips.append(dict(region=region,destination=name,controller_roundtrip=True,surf_preserved=True,
                      walked_tiles=walked-before,transitions=len(transitions)-old_transitions,
                      no_midroute_warps_or_coordinate_writes=True))
    print('Continuous Surf roundtrip:',region,walked-before,'tiles',flush=True)
proof=dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
           trips=trips,one_starting_placement_and_story_state_are_fixtures=True,full_campaign_playthrough=False)
lib.stop();(args.output/'sevii-world-surf.json').write_text(json.dumps(proof,indent=2)+'\n')
