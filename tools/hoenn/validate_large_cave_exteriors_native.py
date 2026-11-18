"""Approach nine larger islands from their actual connected sea route.

After one declared Surf/progress placement per case, all travel, beach mode
changes, cave entries, returns and collision attempts use controller input.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from validate_coast_scenery_objects import bootstrap
from validate_sevii_route_boundaries_native import observe_cells


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fully_visible(ns,candidates):
    lib,s=ns['lib'],ns['s']
    save=lib.read32(s['gSaveBlock1Ptr'])
    origin=[lib.read16(save+i) for i in (0,2)]
    ring=[lib.read8(s['sFieldCameraOffset']+i) for i in (2,3)]
    scroll=[lib.read16(s['sGpuRegBuffer']+0x14+i)&511 for i in (0,2)]
    dims=[[(8,8),(16,16),(32,32),(64,64)],[(16,8),(32,8),(32,16),(64,32)],[(8,16),(8,32),(16,32),(32,64)]]
    sprites=[]
    for i in range(128):
        a0,a1=lib.read16(0x07000000+8*i),lib.read16(0x07000002+8*i)
        if a0&0x300==0x200 or a0>>14>2:
            continue
        w,h=dims[a0>>14][a1>>14];x,y=a1&511,a0&255
        sprites.append((x-512 if x>=256 else x,y-256 if y>=160 else y,w,h))
    wanted=set(candidates);counts=Counter()
    for y in range(1,160,2):
        for x in range(1,240,2):
            if any(sx<=x<sx+w and sy<=y<sy+h for sx,sy,w,h in sprites):
                continue
            xx,yy=(x+scroll[0])%256,(y+scroll[1])%256
            dx,dy=((xx//8-ring[0])%32)//2,((yy//8-ring[1])%32)//2
            point=(origin[0]+dx-7,origin[1]+dy-7)
            if point in wanted:
                counts[point]+=1
    return [p for p in sorted(wanted) if counts[p]>=64]


def translated_mid(ns,from_layout,word):
    current=ns['layouts'][ns['maps'][ns['by_location'][ns['location']()]]['layout']]
    mid=word&1023
    if from_layout['layout_version']==current['layout_version']:
        return mid
    if from_layout['layout_version']=='frlg' and mid==0x12B:
        return 0x170
    if current['layout_version']=='frlg' and mid==0x170:
        return 0x12B
    beach={0x10C,0x10D,0x10E,0x114,0x115,0x116,0x11C,0x11D,0x11E}
    if from_layout['layout_version']=='frlg' and mid in beach:
        return mid+15
    if current['layout_version']=='frlg' and mid-15 in beach:
        return mid-15
    raise ValueError(('Unreviewed camera translation',hex(mid)))


def run(source,library,output,limit=None,offset=0):
    source,library,output=map(lambda p:Path(p).resolve(),(source,library,output))
    output.mkdir(parents=True,exist_ok=True)
    artifacts={n:sha(source/n) for n in ('pokeemerald.gba','pokeemerald.elf','.journey-atlas-surf-layout')}
    metadata=json.loads((source/'.journey-atlas-surf-layout').read_bytes())
    cases=metadata['large_cave_exteriors']['maps'][offset:offset+limit if limit else None]
    background={r['name']:{(x,y) for y,a,b in r.get('decorative_water_runs',[]) for x in range(a,b)}
                for r in metadata['geometry_plan']['chunks']}
    all_maps={p.parent.name:json.loads(p.read_text()) for p in (source/'data/maps').glob('*/map.json')}
    by_id={m['id']:n for n,m in all_maps.items()}
    names=set()
    for row in cases:
        exterior=row['map'];names.add(exterior)
        names.add(by_id[all_maps[exterior]['warp_events'][0]['dest_map']])
        names.update(by_id[c['map']] for c in all_maps[exterior].get('connections') or [])
    ns=bootstrap(source,library,output,names)
    original={k:ns[k] for k in ('native','warp','script','step')}
    fixture=True;depth=0;controls=[];queries=[];captures=[];results=[]
    def native(name,*args,**kwargs):
        nonlocal depth
        if not fixture:
            assert (name.startswith(('MapGridGet','MetatileBehavior_Is')) or name in
                    ('PlayerGetElevation','GetPlayerFacingDirection','IsPlayerFacingSurfableFishableWater','IsDirectionalStairWarpMetatileBehavior')),name
            queries.append(dict(function=name,args=list(args)))
        depth+=1
        try:
            return original['native'](name,*args,**kwargs)
        finally:
            depth-=1
    def script(*args,**kwargs):
        assert fixture or depth,'Injected gameplay script after placement'
        return original['script'](*args,**kwargs)
    def warp(*args,**kwargs):
        assert fixture,'Travel fixture after departure'
        return original['warp'](*args,**kwargs)
    def step(frames,key=0):
        if not fixture and not depth:
            controls.append(dict(frames=frames,key=key))
        original['step'](frames,key)
    ns.update(native=native,script=script,warp=warp,step=step,walk_transition_pictures=False,
              walk_max_ticks=3000,walk_prefix='large-cave')
    def state():
        return dict(map=ns['by_location'][ns['location']()],tile=list(ns['position']()),
                    mode=ns['lib'].read8(ns['s']['gPlayerAvatar'])&25)
    def picture(label):
        ns['picture'](label);row=dict(file=label+'.png',sha256=sha(output/(label+'.png')));captures.append(row)
        return row
    def sample(label,points):
        phases=[]
        for phase in range(3):
            if phase:
                step(24)
            pixels=observe_cells(ns,points)
            phases.append(dict(frame=phase*24,pixels=pixels,capture=picture(label+f'-phase{phase}')))
        return phases
    def face(exterior):
        m=all_maps[exterior];ew,eh,ev=ns['blocks'][exterior]
        for c in m.get('connections') or []:
            if c['direction'] not in ('left','right','up','down'):
                continue
            neighbor=by_id[c['map']];nw,nh,nv=ns['blocks'][neighbor];off=int(c['offset'])
            span=eh if c['direction'] in ('left','right') else ew
            for t in sorted(range(span),key=lambda i:abs(i-16)):
                if c['direction']=='left':
                    ep=(0,t);np=(nw-2,t-off);edge=(nw-1,t-off);shift=(nw,-off)
                elif c['direction']=='right':
                    ep=(ew-1,t);np=(1,t-off);edge=(0,t-off);shift=(-ew,-off)
                elif c['direction']=='up':
                    ep=(t,0);np=(t-off,nh-2);edge=(t-off,nh-1);shift=(-off,nh)
                else:
                    ep=(t,eh-1);np=(t-off,1);edge=(t-off,0);shift=(-off,-eh)
                nx,ny=np
                if not(0<=nx<nw and 0<=ny<nh):
                    continue
                if ep in background.get(exterior,set()) or np in background.get(neighbor,set()) or edge in background.get(neighbor,set()):
                    continue
                a,b,d=ev[ep[1]*ew+ep[0]],nv[ny*nw+nx],nv[edge[1]*nw+edge[0]]
                if not(a&0xC00 or b&0xC00 or d&0xC00) and a>>12==b>>12==d>>12==1:
                    return neighbor,np,shift,c
        raise AssertionError(('No actual connected sea face',exterior))
    def walk(name,tile):
        ns['walk']((name,*tile));step(240)
        assert state()['map']==name and state()['tile']==list(tile),state()
    try:
        for row in cases:
            exterior=row['map'];mapping=all_maps[exterior]
            entry=mapping['warp_events'][0];interior=by_id[entry['dest_map']]
            interior_warp=int(entry['dest_warp_id']);return_event=all_maps[interior]['warp_events'][interior_warp]
            neighbor,start,shift,connection=face(exterior)
            fixture=True
            native('VarSet',0x40DC,8);native('DisableWildEncounters',1)
            # Isolate scenery from swimmer/campaign battle tests.
            # New trainer IDs use a private defeat-flag resolver. Adding an
            # ID to TRAINER_FLAGS_START beyond the native bank corrupts system
            # flags (including SS Tidal cruise mode), freezing later walking
            # behind a repeatedly scheduled voyage script. Use reviewed flags.
            for trainer in metadata['surf_trainer_redesign']['trainers']:
                ns['rawflag'](trainer['flag'],True)
            ns['set_passability']({exterior,interior,neighbor})
            for name in (exterior,interior,neighbor):
                width=ns['blocks'][name][0]
                ns['passable'][name]-={y*width+x for x,y in background.get(name,set())}
            iw,ih,iv=ns['blocks'][interior]
            for i,event in enumerate(all_maps[interior]['warp_events']):
                if i!=interior_warp:
                    ns['passable'][interior].discard(event['y']*iw+event['x'])
            warp(neighbor,*start);native('SetPlayerAvatarTransitionFlags',8);step(240)
            fixture=False
            assert state()['map']==neighbor and state()['tile']==list(start) and state()['mode']==8,state()
            before=state();dx,dy=shift
            from_layout=ns['layouts'][mapping['layout']]
            changed={(x+dx,y+dy):new for x,y,old,new in row['changed_cells'] if new>>12==3 and not new&0xC00}
            changed_visible=fully_visible(ns,changed)
            ew,eh,ev=ns['blocks'][exterior]
            shore_ids={0x12B,0x10C,0x10D,0x10E,0x114,0x115,0x116,0x11C,0x11D,0x11E}
            apron={(x+dx,y+dy):ev[y*ew+x] for y in range(eh) for x in range(ew) if ev[y*ew+x]&1023 in shore_ids}
            available=changed_visible or fully_visible(ns,apron)
            assert available,('Connected exterior has no visible apron',exterior,neighbor,start)
            before_pixels=sample(exterior+'-neighbor-before-entry',[(x,y,translated_mid(ns,from_layout,apron[x,y])) for x,y in available])
            walk(exterior,[16,19]);landed=ns['assert_foot']();landed_capture=picture(exterior+'-landed')
            mountain={(16+dx,17+dy):word for dx,dy,word in row['mountain_cells']}
            observed=set();views=[]
            for label,target in [('south',[16,19]),('west',[9,14]),('north',[16,7]),('east',[23,14])]:
                walk(exterior,target)
                available=fully_visible(ns,mountain)
                if not available:
                    continue
                phases=sample(exterior+'-mountain-'+label,[(x,y,mountain[x,y]&1023) for x,y in available])
                observed.update(available);views.append(dict(side=label,state=state(),phases=phases))
            assert observed==set(mountain),('Complete mountain has unobserved quarters',exterior,sorted(set(mountain)-observed))
            walk(exterior,[15,18]);before_bump=state();step(60,64);step(24);after_bump=state()
            assert before_bump==after_bump,('Player passed through cave front',exterior,before_bump,after_bump)
            bump=dict(before=before_bump,after=after_bump,key=64,frames=60,capture=picture(exterior+'-front-bump'))
            ex,ey=return_event['x'],return_event['y']
            occupied={(e['x'],e['y']) for e in all_maps[interior]['warp_events']}
            inside=next(p for p in [(ex,ey+1),(ex+1,ey),(ex-1,ey),(ex,ey-1)]
                        if 0<=p[0]<iw and 0<=p[1]<ih and p not in occupied and not iv[p[1]*iw+p[0]]&0xC00)
            walk(interior,inside);inside_state=state();inside_capture=picture(exterior+'-native-interior')
            walk(exterior,[16,19]);returned=state();ns['assert_foot']()
            walk(neighbor,start);sea_return=state();assert sea_return['mode']==8,sea_return
            available=fully_visible(ns,changed) or fully_visible(ns,apron)
            returned_pixels=sample(exterior+'-neighbor-after-return',[(x,y,translated_mid(ns,from_layout,apron[x,y])) for x,y in available])
            results.append(dict(map=exterior,neighbor=neighbor,fixture_start=list(start),connection=connection,
                before=before,before_entry_pixels=before_pixels,landed=landed,landed_capture=landed_capture,
                changed_shore_cells_visible_before_first_entry=len(changed_visible),
                whole_mountain_cells=len(observed),mountain_views=views,native_front_bump=bump,
                interior=inside_state,interior_capture=inside_capture,returned=returned,
                sea_return=sea_return,returned_neighbor_pixels=returned_pixels,
                native_connected_route_beach_cave_and_reciprocal_return=True))
            (output/'partial-cases.json').write_text(json.dumps(dict(artifact_sha256=artifacts,cases=results,
                controls=controls,queries=queries,captures=captures,passed=False),indent=2)+'\n')
            print(exterior,'neighbor/81-cell mountain/foot/surf/inside/return PASS',flush=True)
        assert artifacts=={n:sha(source/n) for n in artifacts}
        report=dict(kind='large-cave-exteriors-native',passed=True,artifact_sha256=artifacts,cases=results,
                    controls=controls,queries=queries,captures=captures,
                    initial_party_badges_trainer_flags_and_connected_Surf_placement_are_fixtures=True,
                    after_placement_controllers_and_readonly_getters_only=True,
                    full_nine_coverage=len(results)==9,save_batteries_validated=False,final_release_validated=False)
        (output/'large-cave-exteriors-native.json').write_text(json.dumps(report,indent=2)+'\n')
        return report
    except BaseException:
        ns['picture']('large-cave-exteriors-failure')
        (output/'failure-state.json').write_text(json.dumps(state(),indent=2)+'\n')
        raise
    finally:
        ns['lib'].stop()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('source','library','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--limit',type=int)
    parser.add_argument('--offset',type=int,default=0)
    args=parser.parse_args();run(args.source,args.library,args.output,args.limit,args.offset)
