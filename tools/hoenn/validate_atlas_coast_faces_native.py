"""Cross every registered native coast, its adapter and the actual outer route.

One initial Surf placement per case is a declared fixture. Crossing, return,
reef bumps and camera samples then use controllers and read-only queries.
"""
import argparse
import hashlib
import json
from pathlib import Path

from validate_coast_scenery_objects import bootstrap
from validate_large_cave_exteriors_native import fully_visible,translated_mid
from validate_sevii_route_boundaries_native import observe_cells

VECTORS={'left':(-1,0,32),'right':(1,0,16),'up':(0,-1,64),'down':(0,1,128)}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(source,library,output,offset=0,limit=None):
    source,library,output=(Path(p).resolve() for p in (source,library,output));output.mkdir(parents=True,exist_ok=True)
    metadata=json.loads((source/'.journey-atlas-surf-layout').read_bytes())
    selected=metadata['adapter_plan']['bindings'][offset:offset+limit if limit else None]
    maps={p.parent.name:json.loads(p.read_bytes()) for p in (source/'data/maps').glob('*/map.json')}
    by_id={r['id']:n for n,r in maps.items()};names=set()
    for row in selected:
        names.update((row['native_map'],row['adapter']))
        names.update(by_id[c['map']] for c in maps[row['adapter']]['connections'])
    ns=bootstrap(source,library,output,names);lib,s=ns['lib'],ns['s']
    original={k:ns[k] for k in ('native','warp','script','step')}
    fixture=True;depth=0;controls=[];queries=[];captures=[];results=[]
    artifacts={n:sha(source/n) for n in ('pokeemerald.gba','pokeemerald.elf','.journey-atlas-surf-layout')}
    chunks={r['name']:r for r in metadata['geometry_plan']['chunks']}
    def step(frames,key=0):
        if not fixture and not depth:controls.append(dict(frames=frames,key=key))
        original['step'](frames,key)
    def native(function,*args,**kwargs):
        nonlocal depth
        if not fixture:
            assert ns['idle'](),'Read-only query during a field script'
            assert function.startswith(('MapGridGet','MetatileBehavior_Is')) or function in {
                'PlayerGetElevation','GetPlayerFacingDirection','IsPlayerFacingSurfableFishableWater',
                'IsDirectionalStairWarpMetatileBehavior','JourneyWorldMapPosition'},function
            queries.append(dict(function=function,args=list(args)))
        depth+=1
        try:return original['native'](function,*args,**kwargs)
        finally:depth-=1
    def script(*args,**kwargs):
        assert fixture or depth,'Injected script during coast trip'
        return original['script'](*args,**kwargs)
    def warp(*args,**kwargs):
        assert fixture,'Warp fixture after departure'
        return original['warp'](*args,**kwargs)
    ns.update(native=native,warp=warp,script=script,step=step,walk_transition_pictures=False,walk_max_ticks=3000)
    def state():
        name=ns['by_location'][ns['location']()];x,y=ns['position']()
        at=s['gObjectEvents']+36*lib.read8(s['gPlayerAvatar']+5)
        atlas=native('JourneyWorldMapPosition')
        result=dict(map=name,tile=[x,y],mode=lib.read8(s['gPlayerAvatar'])&25,elevation=lib.read8(at+11)&15,
                    atlas=[atlas&255,(atlas>>8)&255])
        assert result['mode']==8,result
        if name in chunks:
            ox,oy=chunks[name]['origin'];assert result['atlas']==[(ox+x)//8,(oy+y)//8],result
        return result
    def picture(label):
        ns['picture'](label);r=dict(file=label+'.png',sha256=sha(output/(label+'.png')));captures.append(r);return r
    def walk(name,tile):
        ns['walk']((name,*tile));step(180);r=state();assert r['map']==name and r['tile']==list(tile);return r
    def neighbor_point(name,c,t):
        w,h,_=ns['blocks'][name];dest=by_id[c['map']];dw,dh,_=ns['blocks'][dest];off=int(c['offset'])
        if c['direction']=='left':return dest,(dw-1,t-off),(0,t)
        if c['direction']=='right':return dest,(0,t-off),(w-1,t)
        if c['direction']=='up':return dest,(t-off,dh-1),(t,0)
        return dest,(t-off,0),(t,h-1)
    def water(name,p):
        w,h,v=ns['blocks'][name];x,y=p
        return 0<=x<w and 0<=y<h and not v[y*w+x]&0xC00 and ns['water_behaviors'][ns['behaviors'][name][y*w+x]]
    try:
        for trainer in metadata['surf_trainer_redesign']['trainers']:ns['rawflag'](trainer['flag'],True)
        for row in selected:
            native_name,adapter=row['native_map'],row['adapter'];fixture=True
            native('VarSet',0x40DC,8);native('DisableWildEncounters',1)
            nx,ny=row['native_tile'];dx,dy,key=VECTORS[row['direction']]
            warp(native_name,nx,ny);native('SetPlayerAvatarTransitionFlags',8);step(180)
            fixture=False;before=state();assert before['tile']==[nx,ny]
            aw,ah,av=ns['blocks'][adapter];offset0=int(row['native_connection']['offset'])
            first=(aw-1,ny-offset0) if dx<0 else (0,ny-offset0) if dx>0 else (nx-offset0,ah-1) if dy<0 else (nx-offset0,0)
            candidates={}
            for side in (-1,0,1):
                p=(first[0]+dx-dy*side,first[1]+dy+dx*side)
                if water(adapter,p):candidates[(nx+2*dx-dy*side,ny+2*dy+dx*side)]=av[p[1]*aw+p[0]]
            visible=fully_visible(ns,candidates);assert visible,('No visible real adapter water',row)
            layout=ns['layouts'][maps[adapter]['layout']];phases=[]
            for phase in range(3):
                if phase:step(24)
                pixels=observe_cells(ns,[(x,y,translated_mid(ns,layout,candidates[x,y])) for x,y in visible])
                phases.append(dict(frame=24*phase,pixels=pixels,capture=picture(adapter+f'-before-entry-phase{phase}')))
            outlets=[]
            for c in maps[adapter]['connections']:
                if by_id[c['map']]==native_name:continue
                for t in range(ah if c['direction'] in ('left','right') else aw):
                    dest,p,q=neighbor_point(adapter,c,t)
                    if water(adapter,q) and water(dest,p):outlets.append((dest,p,q))
            assert outlets,('Adapter has no physical outer water connection',row)
            outer,target,approach=outlets[len(outlets)//2]
            ns['set_passability']({native_name,adapter,outer})
            for name in (adapter,outer):
                w=ns['blocks'][name][0]
                ns['passable'][name]-={y*w+x for y,a,b in chunks[name].get('decorative_water_runs',[]) for x in range(a,b)}
            reached=walk(adapter,approach);crossed=walk(outer,target)
            crossing_capture=picture(adapter+'-outer-route')
            w,h,values=ns['blocks'][outer];bumps=[]
            for y in range(h):
                for x in range(w):
                    if not water(outer,(x,y)):continue
                    for bx,by,bkey in VECTORS.values():
                        xx,yy=x+bx,y+by
                        if 0<=xx<w and 0<=yy<h and values[yy*w+xx]&0xC00:
                            bumps.append((abs(x-target[0])+abs(y-target[1]),(x,y),(xx,yy),bkey))
            assert bumps,('No real outer reef collision control',adapter)
            _,safe,blocked,bkey=min(bumps)
            walk(outer,safe);a=state();step(60,bkey);step(30);b=state();assert a==b,('Reef failed to block',adapter,a,b)
            bump=dict(before=a,after=b,blocked_tile=list(blocked),key=bkey,frames=60,capture=picture(adapter+'-reef-bump'))
            back=walk(native_name,(nx,ny));assert back==before,('Native roundtrip drifted',adapter,before,back)
            results.append(dict(adapter=adapter,native_map=native_name,binding=row,before=before,
                neighbor_camera_phases=phases,adapter_reached=reached,outer_reached=crossed,
                outer_capture=crossing_capture,native_reef_bump=bump,returned=back,
                all_travel_controllers_and_readonly_queries=True))
            print(adapter,native_name,'native/adapter/outer/reef/return PASS',flush=True)
            (output/'partial-cases.json').write_text(json.dumps(results,indent=2)+'\n')
        assert artifacts=={n:sha(source/n) for n in artifacts}
        report=dict(kind='atlas-native-coast-faces',passed=True,artifact_sha256=artifacts,cases=results,
            controls=controls,queries=queries,captures=captures,initial_progress_and_per_case_Surf_placement_are_fixtures=True,
            all34coverage=len(results)==34,after_departure_controllers_and_readonly_queries_only=True,
            final_release_validated=False)
        (output/'coast-faces-native.json').write_text(json.dumps(report,indent=2)+'\n');return report
    except BaseException:picture('coast-face-failure');raise
    finally:lib.stop();ns['emulator_workspace'].cleanup()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','library','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--offset',type=int,default=0);p.add_argument('--limit',type=int)
    a=p.parse_args();run(a.source,a.library,a.output,a.offset,a.limit)
