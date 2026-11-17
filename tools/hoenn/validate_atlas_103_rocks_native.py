"""Observe all103 repaired cells in actual mGBA BG/VRAM/palette/scanout.

Each of52 local visual/collision cases has a declared initial party/progress,
position and movement-mode fixture. After placement,
only controllers and read-only native queries are used. This is not travel
through all20 maps, a campaign replay, or a final release certificate.
"""
import argparse
from collections import deque
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import struct

from PIL import Image

from atlas_surf_migration import _occupied
from atlas_surf_source import Source
from atlas_surf_rock_repairs import bank_paths
from audit_atlas_rock_fragments import with_layout
from candidate_layer import Layer
from prepare_generated_area_review import PRIOR,LAYER
from validate_coast_scenery_objects import bootstrap
from validate_sevii_route_boundaries_native import observe_cells
from verify_sevii_route_boundaries_native import verify_pixels


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def groups(rows):
    result=[]
    for name in sorted({r['map'] for r in rows}):
        points={tuple(r['tile']):r for r in rows if r['map']==name}
        while points:
            seed=min(points);todo=[seed];case=[points.pop(seed)]
            for x,y in todo:
                neighbors=[p for p in points if max(abs(p[0]-x),abs(p[1]-y))<=1]
                for p in neighbors:todo.append(p);case.append(points.pop(p))
            result.append(dict(map=name,rows=case))
    return result


def placements(view,case):
    name=case['map'];layout=view.layout(name);cells=[r['tile'] for r in case['rows']]
    left=min(p[0] for p in cells);right=max(p[0] for p in cells);top=min(p[1] for p in cells);bottom=max(p[1] for p in cells)
    occupied=_occupied(view.maps[name]);candidates=[]
    for y in range(max(0,top-4),min(layout['height'],bottom+5)):
        for x in range(max(0,left-5),min(layout['width'],right+6)):
            word=view.word(name,x,y)
            if word&0xc00 or (x,y) in occupied:continue
            water=view.water(name,x,y)
            if word>>12 not in (0,1 if water else 3):continue
            # Keep the avatar's complete OAM rectangle away from every cell.
            if not (x<=left-2 or x>=right+2 or y>=bottom+3):continue
            if max(abs(x-left),abs(x-right))>6 or max(abs(y-top),abs(y-bottom))>4:continue
            candidates.append(dict(tile=[x,y],surfing=water,score=abs(2*x-left-right)+abs(2*y-top-bottom)))
    return sorted(candidates,key=lambda p:(p['score'],not p['surfing'],p['tile'][1],p['tile'][0]))


def strict_pool(view,name,surfing):
    layout=view.layout(name);occupied=_occupied(view.maps[name]);result=set()
    for y in range(layout['height']):
        for x in range(layout['width']):
            word=view.word(name,x,y)
            if (not word&0xc00 and word>>12 in (0,1 if surfing else 3)
                and view.water(name,x,y)==surfing and (x,y) not in occupied):result.add((x,y))
    return result


def bump_route(view,case,start,surfing):
    pool=strict_pool(view,case['map'],surfing);start=tuple(start);pool.add(start)
    targets={}
    for row in case['rows']:
        x,y=row['tile']
        for dx,dy,key in [(1,0,32),(-1,0,16),(0,1,64),(0,-1,128)]:
            p=(x+dx,y+dy)
            if p in pool:targets[p]=(row['tile'],key)
    queue=deque([start]);parents={start:None}
    while queue:
        point=queue.popleft()
        if point in targets:
            path=[];p=point
            while p!=start:path.append(p);p=parents[p]
            return list(reversed(path)),point,targets[point],pool
        x,y=point
        for p in [(x+1,y),(x-1,y),(x,y+1),(x,y-1)]:
            if p in pool and p not in parents:parents[p]=point;queue.append(p)
    return None


def run(source,library,output):
    source,library,output=map(lambda p:Path(p).resolve(),(source,library,output));output.mkdir(parents=True,exist_ok=True)
    metadata=json.loads((source/'.journey-atlas-surf-layout').read_bytes());repairs=metadata['native_General_rock_repairs']
    assert repairs['suspect_pieces_before']==103 and repairs['suspect_pieces_after']==0
    cases=groups(repairs['repairs']);assert len(cases)==52
    view=Source(source);bank=bank_paths(view,'gTileset_General');raw=view.read(bank['metatiles'])
    definitions=struct.unpack('<'+'H'*(len(raw)//2),raw)
    variants=repairs['runtime_variants'];bindings=variants['runtime_layout_bindings']
    for case in cases:
        name=case['map'];case['layout']=bindings.get(name,view.maps[name]['layout'])
        if case['layout']==view.maps[name]['layout']:continue
        projected=with_layout(view,name,case['layout'])
        proof=next(r for r in variants['after'] if (r['map'],r['layout'])==(name,case['layout']))
        required={tuple(r['tile']) for r in case['rows']};additional={}
        for row in case['rows']:
            x,y=row['tile'];word=projected.word(name,x,y)
            if word==row['after']:continue
            objects=[r for r in proof['census']['complete_objects'] if [name,x,y] in r['cells']]
            assert len(objects)==1,('Unexpected live-layout difference',case,row,word)
            row['primary_layout_after']=row['after'];row['after']=word
            row['resolution']='complete native boulder preserved in the authenticated alternate layout'
            for cell in objects[0]['cells']:
                point=tuple(cell[1:])
                if point not in required:
                    value=projected.word(name,*point)
                    additional[point]=dict(map=name,tile=list(point),before=value,after=value,preserved_object_witness=True)
        case['rows'].extend(additional.values())
    extra=groups(variants['repairs'])
    for case in extra:
        case['layout']=case['rows'][0]['layout'];case['additional_runtime_fragment_case']=True
    cases.extend(extra);assert len(cases)==54
    expected=Layer(source,'atlas-surf-layout',PRIOR+[LAYER]).expected;expected.update(metadata['prepared_sha256'])
    artifacts={n:sha(source/n) for n in ('pokeemerald.gba','pokeemerald.elf','.journey-atlas-surf-layout')}
    def unchanged():
        assert artifacts=={n:sha(source/n) for n in artifacts}
        for n,h in expected.items():assert sha(source/n)==h,n
    unchanged();ns=bootstrap(source,library,output,{c['map'] for c in cases})
    original={k:ns[k] for k in ('step','native','script','warp','picture')}
    fixture=True;depth=0;phase='fixture';controls=[];queries=[];captures=[];results=[]
    def step(frames,key=0):
        if not fixture and not depth:controls.append(dict(phase=phase,frames=frames,key=key))
        original['step'](frames,key)
    def native(name,*args,**kwargs):
        nonlocal depth
        if not fixture:
            assert name.startswith(('MapGridGet','MetatileBehavior_Is')) or name in {
                'GetPlayerFacingDirection','GetPlayerFacingMovementDirection','PlayerGetElevation','IsPlayerFacingSurfableFishableWater'},name
            queries.append(dict(phase=phase,function=name,args=list(args)))
        depth+=1
        try:return original['native'](name,*args,**kwargs)
        finally:depth-=1
    def script(*args,**kwargs):
        assert fixture or depth,'Gameplay script injected after case placement'
        return original['script'](*args,**kwargs)
    def warp(*args,**kwargs):
        assert fixture,'Travel fixture after case departure'
        return original['warp'](*args,**kwargs)
    def capture(label):
        original['picture'](label);row=dict(file=label+'.png',sha256=sha(output/(label+'.png')));captures.append(row);return row
    def state():
        return dict(map=ns['by_location'][ns['location']()],tile=list(ns['position']()),
            mode=ns['lib'].read8(ns['s']['gPlayerAvatar']),elevation=native('PlayerGetElevation'))
    ns.update(step=step,native=native,script=script,warp=warp,walk_transition_pictures=False)
    try:
        for number,case in enumerate(cases):
            fixture=True;name=case['map'];label=f'{number:02d}-{name}';phase=label+'-fixture'
            projected=with_layout(view,name,case['layout'])
            candidates=placements(projected,case)
            if not candidates:raise AssertionError(('No safe unobscured placement',case))
            chosen=candidates[0];warp(name,*chosen['tile']);native('SetPlayerAvatarTransitionFlags',8 if chosen['surfing'] else 1)
            native('DisableWildEncounters',1);step(120)
            assert state()['map']==name and state()['tile']==chosen['tile'],(label,state(),chosen)
            live_layout=ns['lib'].read32(ns['s']['gMapHeader'])
            assert live_layout==ns['s'][view.layouts[case['layout']]['name']],('Unexpected active native layout',label,hex(live_layout),case['layout'])
            ns['maps'][name]['layout']=case['layout']
            layout=projected.layout(name);ns['blocks'][name]=(layout['width'],layout['height'],tuple(projected.words(name)))
            ns['behaviors'][name]=[projected.behavior(name,w) for w in projected.words(name)]
            fixture=False;loaded=[];observations=[]
            for row in case['rows']:
                x,y=row['tile'];actual=dict(tile=[x,y],metatile=native('MapGridGetMetatileIdAt',x+7,y+7),
                    collision=native('MapGridGetCollisionAt',x+7,y+7),elevation=native('MapGridGetElevationAt',x+7,y+7))
                assert actual['metatile']==row['after']&1023 and actual['collision']==(row['before']>>10)&3,(label,row,actual,state())
                assert actual['elevation']==row['before']>>12,actual
                actual['preserved_object_witness']=row.get('preserved_object_witness',False)
                actual['primary_layout_after']=row.get('primary_layout_after')
                actual['resolution']=row.get('resolution','fragment repaired in the loaded layout')
                loaded.append(actual)
            for animation in range(3):
                phase=label+'-animation-'+str(animation)
                if animation:step(24)
                pixels=observe_cells(ns,[(r['tile'][0],r['tile'][1],r['after']&1023) for r in case['rows']])
                attachment=capture(phase);image=Image.open(output/attachment['file']).convert('RGB')
                for row in pixels['cells']:
                    mid=row['expected_metatile'];assert row['definition_words']==list(definitions[8*mid:8*mid+8])
                    single=dict(pixels,cells=[row]);verify_pixels(single,attachment,{attachment['file']:attachment['sha256']},
                        {attachment['file']:image},row['cell'],mid)
                observations.append(dict(frame=animation*24,capture=attachment,pixels=pixels))
            phase=label+'-native-collision';route=bump_route(projected,case,chosen['tile'],chosen['surfing']);bump=None
            if route:
                path,approach,(blocked,key),pool=route
                ns['passable'][name]={y*layout['width']+x for x,y in pool}
                for tile in path:ns['walk']((name,*tile))
                before=state();step(60,key);step(24);after=state()
                assert before['map']==after['map']==name and before['tile']==after['tile']==list(approach),(label,before,after)
                bump=dict(blocked_tile=blocked,key=key,before=before,after=after,controller_frames=60,
                    capture=capture(phase),placement_to_approach_path=[list(p) for p in path])
            results.append(dict(map=name,layout=case['layout'],case=number,initial_placement=chosen,loaded_cells=loaded,
                animation_observations=observations,native_collision_bump=bump,
                no_bump_reason=None if bump else 'No adjacent safe approach in this unchanged collision component'))
            print(json.dumps(dict(case=number,map=name,cells=len(loaded),phases=3,bump=bump is not None)),flush=True)
        unchanged();view.assert_unchanged()
        task_cells=sum(sum(not p['preserved_object_witness'] for p in r['loaded_cells']) for r in results)
        assert task_cells==109
        report=dict(kind='103-General-rock-fragments-native',passed=True,artifact_sha256=artifacts,
            source_inputs_checked=len(expected),prepared_source_sha256=metadata['prepared_sha256'],cases=results,
            checked_task_cells=109,original_reviewed_cells=103,additional_runtime_fragment_cells=6,
            preserved_native_variant_boulder_witness_cells=2,
            animation_phases_per_case=3,all_four_quadrants_BG_VRAM_palette_and_PNG_samples_checked=True,
            compiled_metatile_words_match_actual_source=True,old_collision_elevation_preserved_in_native_engine=True,
            fixture_per_case_party_progress_initial_position_and_movement_mode=True,
            after_placement_controllers_and_read_only_native_getters_only=True,
            native_getter_trampoline_declared=True,full_campaign_or_twenty_map_travel_not_certified=True,
            controls=controls,queries=queries,captures=captures,final_release_validated=False)
        (output/'rocks103-native.json').write_text(json.dumps(report,indent=2)+'\n');return report
    except BaseException:capture('rocks103-native-failure');raise
    finally:ns['lib'].stop()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','library','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();r=run(a.source,a.library,a.output)
    print(json.dumps(dict(passed=True,original_cells=103,additional_runtime_fragments=6,cases=len(r['cases']),captures=len(r['captures']))))
