"""Controller entry, species appearance, approach and reciprocal return.

Each case starts from a declared adjacent-floor party/progress fixture.
Following that placement, only controls and read-only observation are allowed.
This is focused chamber validation, not a campaign playthrough.
"""
import argparse
from collections import deque
import ctypes
import hashlib
import json
from pathlib import Path

from render_sea_maps import MapRenderer
from validate_coast_scenery_objects import bootstrap


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def species_pixels(ns, renderer, actor, map_id):
    lib,s = ns['lib'],ns['s']
    slots=[]
    for i in range(16):
        at=s['gObjectEvents']+36*i
        if lib.read8(at)&1 and lib.read8(at+8)==1 and (lib.read8(at+10),lib.read8(at+9))==map_id:
            slots.append(at)
    assert len(slots)==1,('Missing unique species object',actor,slots)
    obj=slots[0]
    assert not lib.read8(obj+1)&32,'Hidden species object'
    sprite=s['gSprites']+68*lib.read8(obj+35)
    attr=lib.read16(sprite+4)&0xF3FF
    anim_num=lib.read8(sprite+0x2A)
    cmd_index=lib.read8(sprite+0x2B)
    anim_table=lib.read32(sprite+8)&0xFFFFFFFF
    anim=lib.read32(anim_table+4*anim_num)&0xFFFFFFFF
    assert 0x08000000<=anim<0x0A000000,('Foreign species animation pointer',hex(anim))
    frame_index=lib.read16(anim+4*cmd_index)&65535
    if frame_index>=0xFFFD:
        assert cmd_index>0,'Animation has no preceding native frame'
        frame_index=lib.read16(anim+4*(cmd_index-1))&65535
    assert frame_index<32,('Unsupported native species frame',anim_num,cmd_index,frame_index)
    expected=renderer.sprite(actor['graphics_id'],frame_index)
    width,height=expected.size
    dims=[[(8,8),(16,16),(32,32),(64,64)],[(16,8),(32,8),(32,16),(64,32)],[(8,16),(8,32),(16,32),(32,64)]]
    parts=[]
    base=attr&1023
    frame_tiles=width*height//64
    for i in range(128):
        a0,a1,a2=(lib.read16(0x07000000+8*i+2*j)&65535 for j in range(3))
        offset=(a2&1023)-base
        if a0&0x300==0x200 or a0>>14>2 or a2&0xF000!=attr&0xF000 or not 0<=offset<frame_tiles:
            continue
        pw,ph=dims[a0>>14][a1>>14]
        sx,sy=(offset%(width//8))*8,(offset//(width//8))*8
        if sx+pw>width or sy+ph>height:
            continue
        x,y=a1&511,a0&255
        x=x-512 if x>=256 else x
        y=y-256 if y>=160 else y
        assert not a0&0x2100,'Unexpected affine/8bpp species'
        parts.append(dict(index=i,attributes=[a0,a1,a2],screen=[x,y,pw,ph],source=[sx,sy]))
    assert parts,('Species hardware OAM missing',actor['graphics_id'])
    # Large native species use two 64x32 OAM pieces with different priorities.
    # Reassemble their complete source footprint instead of assuming one OBJ.
    positions={}
    for part in parts:
        a0,a1,a2=part['attributes'];x,y,pw,ph=part['screen'];sx,sy=part['source']
        for yy in range(ph):
            for xx in range(pw):
                point=(sx+(pw-1-xx if a1&0x1000 else xx),sy+(ph-1-yy if a1&0x2000 else yy))
                assert point not in positions,'Duplicate hardware species quarter'
                positions[point]=(x+xx,y+yy)
    frame=ctypes.string_at(lib.image(),240*160*4)
    palette=[]
    for color in range(16):
        word=lib.read16(0x05000200+2*(16*(attr>>12)+color))&32767
        palette.append(tuple(((word>>shift)&31)<<3 for shift in (0,5,10)))
    stride=width//8 if lib.read16(0x04000000)&64 else 32
    samples=[]
    source_matches=visible=opaque=0
    for py in range(height):
        for px in range(width):
            tile=base+(py//8)*stride+px//8
            byte=lib.read8(0x06010000+32*tile+4*(py%8)+(px%8)//2)
            color=(byte>>(4*(px&1)))&15
            wanted=expected.getpixel((px,py))
            if bool(color)!=bool(wanted[3]):
                raise AssertionError(('Species silhouette differs from its native frame',actor['graphics_id'],px,py))
            if not color:
                continue
            opaque+=1
            rgb=palette[color]
            source_matches+=all(abs(a-b)<=7 for a,b in zip(rgb,wanted[:3]))
            assert (px,py) in positions,'Missing opaque species quarter'
            screen_x,screen_y=positions[px,py]
            assert 0<=screen_x<240 and 0<=screen_y<160,'Species opaque body clipped off screen'
            at=4*(screen_y*240+screen_x)
            actual=frame[at:at+3]
            visible+=all(abs(a-b)<=7 for a,b in zip(actual,rgb))
            samples.append([screen_x,screen_y,*rgb])
    assert opaque>=40 and source_matches==opaque,('Wrong species palette/frame',source_matches,opaque,actor['graphics_id'])
    assert visible>=opaque*.95,('Species body covered by scenery',visible,opaque)
    return dict(graphics_id=actor['graphics_id'],hardware_oam_parts=parts,
                native_animation=anim_num,native_command=cmd_index,native_frame_index=frame_index,
                source_dimensions=[width,height],native_source_pixels=source_matches,
                opaque_pixels=opaque,visible_pixels=visible,expected_scanout_pixels=samples)


def run(source,library,output,limit=None,offset=0):
    source,library,output=map(lambda p:Path(p).resolve(),(source,library,output))
    output.mkdir(parents=True,exist_ok=True)
    artifacts={n:sha(source/n) for n in ('pokeemerald.gba','pokeemerald.elf','.journey-atlas-surf-layout')}
    metadata=json.loads((source/'.journey-atlas-surf-layout').read_text())
    records=metadata['legendary_individual_chambers']['rooms']
    records=records[offset:offset+limit if limit else None]
    names={r[k] for r in records for k in ('parent','room')}
    ns=bootstrap(source,library,output,names)
    renderer=MapRenderer(source)
    original={k:ns[k] for k in ('native','warp','step','script')}
    fixture=True
    depth=0
    controls=[]
    queries=[]
    checks=[]
    captures=[]
    def native(name,*args,**kwargs):
        nonlocal depth
        if not fixture:
            assert name.startswith(('MapGridGet','MetatileBehavior_Is')) or name in ('PlayerGetElevation','GetPlayerFacingDirection'),name
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
        assert fixture,'Travel fixture after placement'
        return original['warp'](*args,**kwargs)
    def step(frames,key=0):
        if not fixture and not depth:
            if controls and controls[-1]['key']==key:
                controls[-1]['frames']+=frames
            else:
                controls.append(dict(frames=frames,key=key))
        return original['step'](frames,key)
    ns.update(native=native,script=script,warp=warp,step=step)
    def state():
        return dict(map=ns['by_location'][ns['location']()],tile=list(ns['position']()),
                    mode=ns['lib'].read8(ns['s']['gPlayerAvatar'])&25)
    def picture(label):
        ns['picture'](label)
        result=dict(file=label+'.png',sha256=sha(output/(label+'.png')))
        captures.append(result)
        return result
    def walk(name,target,blocked=()):
        assert state()['map']==name,state()
        w,h,values=ns['blocks'][name]
        target=tuple(target)
        start=tuple(state()['tile'])
        banned=set(map(tuple,blocked))
        queue=deque([start]);parents={start:None}
        while queue and target not in parents:
            x,y=queue.popleft()
            for p in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                xx,yy=p
                if (0<=xx<w and 0<=yy<h and p not in parents and p not in banned
                        and not values[yy*w+xx]&0xC00 and values[yy*w+xx]>>12!=1):
                    parents[p]=(x,y);queue.append(p)
        assert target in parents,('No physical approach',name,start,target)
        route=[];p=target
        while p!=start:
            route.append(p);p=parents[p]
        for p in reversed(route):
            x,y=state()['tile'];tx,ty=p
            key=16 if tx>x else 32 if tx<x else 64 if ty<y else 128
            for _ in range(90):
                if state()['map']!=name or tuple(state()['tile'])==p:
                    break
                step(4,key)
            else:
                raise AssertionError(('Cannot walk',name,p,state()))
            step(24)
            if state()['map']!=name:
                return
    try:
        for r in records:
            fixture=True
            native('VarSet',0x40dc,8)
            for flag in ns['hoenn_flags']+ns['kanto_flags']:
                ns['rawflag'](flag,False)
            # Keep native low tide; no forced permanent layout or event script.
            flags=(source/'include/constants/flags.h').read_text()
            import re
            tide=re.search(r'^#define\s+FLAG_SYS_SHOAL_TIDE\s+(0x[0-9A-Fa-f]+|\d+)',flags,re.M)
            if tide:
                ns['rawflag'](int(tide[1],0),False)
            mapping=ns['all_maps'][r['parent']]
            w,h,values=ns['blocks'][r['parent']]
            px,py=r['entrance']
            occupied={(e['x'],e['y']) for k in ('object_events','warp_events','coord_events','bg_events') for e in mapping.get(k,[]) if isinstance(e.get('x'),int)}
            approaches=[(px,py+1),(px-1,py),(px+1,py),(px,py-1)]
            start=next((p for p in approaches if 0<=p[0]<w and 0<=p[1]<h and p not in occupied
                        and not values[p[1]*w+p[0]]&0xC00 and values[p[1]*w+p[0]]>>12!=1),None)
            assert start is not None,('No fixture approach',r)
            native('DisableWildEncounters',1)
            warp(r['parent'],*start)
            native('SetPlayerAvatarTransitionFlags',1)
            step(240)
            fixture=False
            before=state()
            assert before['mode']==1,before
            entry_capture=picture(r['room']+'-parent-entry')
            walk(r['parent'],r['entrance'])
            for _ in range(300):
                if state()['map']==r['room'] and ns['idle']():
                    break
                step(4)
            else:
                raise AssertionError(('Entrance did not warp',r,state()))
            step(240)
            entered=state()
            actor=ns['all_maps'][r['room']]['object_events'][0]
            walk(r['room'],[actor['x'],actor['y']+1],[(actor['x'],actor['y'])])
            # Observe the full species from two tiles away. At interaction
            # distance the player's hat naturally overlaps some small feet.
            rw,rh,rv=ns['blocks'][r['room']]
            ax,ay=actor['x'],actor['y']
            viewpoints=[(ax,ay+2),(ax-2,ay),(ax+2,ay),(ax,ay-2)]
            if renderer.sprite(actor['graphics_id']).height>32:
                viewpoints=[(ax-2,ay),(ax+2,ay),(ax,ay+2),(ax,ay-2)]
            vantage=next((p for p in viewpoints if 0<=p[0]<rw and 0<=p[1]<rh
                          and not rv[p[1]*rw+p[0]]&0xC00 and rv[p[1]*rw+p[0]]>>12!=1
                          and list(p)!=r['exit']),None)
            assert vantage is not None,('No unobstructed whole-sprite viewpoint',r)
            walk(r['room'],vantage,[(ax,ay),tuple(r['exit'])])
            step(240)
            pixels=species_pixels(ns,renderer,actor,ns['map_id'](r['room']))
            species_capture=picture(r['room']+'-species')
            walk(r['room'],r['exit'],[(actor['x'],actor['y'])])
            # Native arrow thresholds trigger when the player keeps walking
            # outwards from the threshold, rather than merely reaching it.
            if state()['map']==r['room']:
                x,y=state()['tile']
                width=ns['blocks'][r['room']][0]
                behavior=ns['behaviors'][r['room']][y*width+x]
                arrow_key={0x62:16,0x63:32,0x64:64,0x65:128}.get(behavior)
                if arrow_key:
                    step(12,arrow_key)
            for _ in range(300):
                if state()['map']==r['parent'] and ns['idle']():
                    break
                step(4)
            else:
                raise AssertionError(('Cannot return through own entrance',r,state()))
            step(240)
            returned=state()
            assert returned['mode']==1,returned
            checks.append(dict(national_dex=r['national_dex'],parent=r['parent'],room=r['room'],
                               fixture_start=list(start),before=before,entered=entered,returned=returned,
                               species_viewpoint=list(vantage),
                               entrance_capture=entry_capture,species_capture=species_capture,species_pixels=pixels,
                               native_controller_entry_and_return=True))
            print(r['national_dex'],r['room'],'entry/species/return PASS',flush=True)
        assert artifacts=={n:sha(source/n) for n in artifacts},'Source mutated during native run'
        report=dict(kind='legendary-chambers-native',passed=True,artifact_sha256=artifacts,
                    cases=checks,controls=controls,queries=queries,captures=captures,
                    initial_adjacent_floor_party_progress_and_position_fixtures_declared=True,
                    after_placement_controllers_and_readonly_getters_only=True,
                    first_case_offset=offset,
                    full_105_coverage=len(checks)==105,capture_battles_and_persistence_validated=False,
                    final_release_validated=False)
        (output/'legendary-chambers-native.json').write_text(json.dumps(report,indent=2)+'\n')
        return report
    except BaseException:
        ns['picture']('legendary-chambers-failure')
        raise
    finally:
        ns['lib'].stop()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('source','library','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--limit',type=int)
    parser.add_argument('--offset',type=int,default=0)
    a=parser.parse_args()
    run(a.source,a.library,a.output,a.limit,a.offset)
