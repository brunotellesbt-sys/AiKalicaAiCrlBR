"""Compare one physical boulder before entry, after entry and on return.

Party/progress/position/Surf/encounter suppression are initial fixtures per
case. After placement, movement uses controllers and declared read-only
native getter trampolines. No map/layout/camera/VRAM setters are permitted.
"""
import argparse
from collections import deque
import hashlib
import json
from pathlib import Path

from validate_coast_scenery_objects import bootstrap
from validate_sevii_route_boundaries_native import observe_cells
from validate_atlas_candidate_batteries_native import save_menu
from atlas_surf_source import Source
from validate_atlas_103_rocks_native import strict_pool

CASES=[dict(label='Pacifidlog-Route131',origin='PacifidlogTown',start=[19,14],key=16,back=32,
            target=[2,14],cells=[[0,11,0x150],[1,11,0x151],[0,12,0x158],[1,12,0x159]],shift=20),
       dict(label='Route130-Route131',origin='Route130',start=[2,22],key=32,back=16,
            target=[59,22],cells=[[58,18,0x150],[59,18,0x151],[58,19,0x158],[59,19,0x159]],shift=-60)]

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def run(source,library,output,fixed,save_batteries=False):
    source,library,output=map(lambda p:Path(p).resolve(),(source,library,output));output.mkdir(parents=True,exist_ok=True)
    artifacts={n:sha(source/n) for n in ('pokeemerald.gba','pokeemerald.elf','.journey-atlas-surf-layout')}
    metadata=json.loads((source/'.journey-atlas-surf-layout').read_bytes())
    view=Source(source);ns=bootstrap(source,library,output,{'Route131','Route130','PacifidlogTown'})
    original={k:ns[k] for k in ('native','warp','script','step')};fixture=True;depth=0;controls=[];queries=[];results=[];captures=[]
    def native(name,*args,**kwargs):
        nonlocal depth
        if not fixture:
            assert name.startswith(('MapGridGet','MetatileBehavior_Is')) or name=='PlayerGetElevation',name
            queries.append(dict(function=name,args=list(args)))
        depth+=1
        try:return original['native'](name,*args,**kwargs)
        finally:depth-=1
    def warp(*args,**kwargs):
        assert fixture;return original['warp'](*args,**kwargs)
    def script(*args,**kwargs):
        assert fixture or depth;return original['script'](*args,**kwargs)
    def step(frames,key=0):
        if not fixture and not depth:controls.append(dict(frames=frames,key=key))
        original['step'](frames,key)
    def state():return dict(map=ns['by_location'][ns['location']()],tile=list(ns['position']()),surfing=bool(ns['lib'].read8(ns['s']['gPlayerAvatar'])&8),elevation=native('PlayerGetElevation'))
    def capture(label,cells):
        values=[]
        for x,y,_ in cells:
            values.append(dict(tile=[x,y],metatile=native('MapGridGetMetatileIdAt',x+7,y+7),collision=native('MapGridGetCollisionAt',x+7,y+7),elevation=native('MapGridGetElevationAt',x+7,y+7)))
        phases=[]
        for phase in range(3):
            if phase:step(24)
            observations=observe_cells(ns,[(x,y,value['metatile']) for (x,y,_),value in zip(cells,values)])
            filename=label+'-phase'+str(phase);ns['picture'](filename);p=output/(filename+'.png')
            captures.append(dict(file=p.name,sha256=sha(p)))
            phases.append(dict(frame=phase*24,pixels=observations,capture=captures[-1]))
        return dict(state=state(),cells=values,animation_observations=phases)
    ns.update(native=native,warp=warp,script=script,step=step)
    def walk_to(name,target):
        assert state()['map']==name
        start=tuple(state()['tile']);target=tuple(target)
        pool=strict_pool(view,name,True);queue=deque([start]);parents={start:None}
        while queue and target not in parents:
            x,y=queue.popleft()
            for p in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                if p in pool and p not in parents:parents[p]=(x,y);queue.append(p)
        assert target in parents,('No unchanged safe approach',name,start,target)
        route=[];p=target
        while p!=start:route.append(list(p));p=parents[p]
        route.reverse()
        for target in route:
            x,y=state()['tile'];tx,ty=target;assert abs(tx-x)+abs(ty-y)==1
            key=16 if tx>x else 32 if tx<x else 64 if ty<y else 128
            for _ in range(60):
                if state()['tile']==target:break
                step(4,key)
            else:raise AssertionError(('Cannot approach boundary rock',target,state()))
            step(24)
    def blocked(key):
        a=state();step(60,key);step(24);b=state();assert a==b
        return dict(before=a,after=b,frames=60)
    try:
        for case in CASES:
            fixture=True;native('VarSet',0x40dc,metadata['migration']['final_version']);warp(case['origin'],*case['start'])
            if not ns['lib'].read8(ns['s']['gPlayerAvatar'])&8:native('SetPlayerAvatarTransitionFlags',8)
            native('DisableWildEncounters',1);step(240)
            assert state()['map']==case['origin'] and state()['tile']==case['start'];fixture=False
            outside=[[x+case['shift'],y,mid] for x,y,mid in case['cells']]
            before=capture(case['label']+'-before-first-entry',outside)
            for _ in range(180):
                if state()['map']=='Route131' and state()['tile']==case['target']:break
                step(4,case['key'])
            else:raise AssertionError(('Cannot cross using controllers',case,state()))
            step(240);after=capture(case['label']+'-after-entry',case['cells'])
            assert ns['lib'].read32(ns['s']['gMapHeader'])==ns['s']['Route131_SkyPillar_Layout']
            bump=None
            if fixed and case['origin']=='Route130':
                walk_to('Route131',(59,20));bump=blocked(64)
                walk_to('Route131',case['target'])
            for _ in range(180):
                if state()['map']==case['origin'] and state()['tile']==case['start']:break
                step(4,case['back'])
            else:raise AssertionError(('Cannot return using controllers',case,state()))
            step(240);returned=capture(case['label']+'-returned',outside)
            expected=[c[2] for c in case['cells']]
            baseline_after=[0x170]*4 if case['origin']=='PacifidlogTown' else expected
            assert [p['metatile'] for p in after['cells']]==(expected if fixed else baseline_after)
            for observed in (before,returned):
                assert [p['metatile'] for p in observed['cells']]==(expected if fixed else [0x170]*4)
            if fixed and case['origin']=='PacifidlogTown':
                walk_to(case['origin'],(19,12));bump=blocked(case['key'])
            battery=None
            if save_batteries:
                path=output/(case['label']+'-controller-save.sav');callbacks=save_menu(ns,path)
                battery=dict(file=path.name,sha256=sha(path),callbacks=callbacks,geometry_version=metadata['migration']['final_version'])
            results.append(dict(case=case,before=before,after=after,returned=returned,defect_reproduced=not fixed,native_boundary_rock_bump=bump,battery=battery))
            print(case['label'],'fixed' if fixed else 'defect reproduced',flush=True)
        assert artifacts=={n:sha(source/n) for n in artifacts}
        view.assert_unchanged()
        report=dict(kind='neighbor-layout-camera-native',passed=True,fixed=fixed,artifact_sha256=artifacts,cases=results,captures=captures,controls=controls,queries=queries,
            fixtures_declared=True,after_placement_controllers_and_readonly_getters_only=True,final_release_validated=False)
        (output/'neighbor-camera-native.json').write_text(json.dumps(report,indent=2)+'\n');return report
    except BaseException:ns['picture']('neighbor-camera-failure');raise
    finally:ns['lib'].stop()

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('source','library','output'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--fixed',action='store_true');p.add_argument('--save-batteries',action='store_true')
    a=p.parse_args();run(a.source,a.library,a.output,a.fixed,a.save_batteries)
