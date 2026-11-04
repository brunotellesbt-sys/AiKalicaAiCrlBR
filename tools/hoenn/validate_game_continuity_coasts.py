"""Cross each changed coastal camera by controls and inspect real BG scanout."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from game_continuity_coasts import ASSIGNMENTS
from integrated_ocean_seams import _animation_frames
from validate_arrival_coast_photos import animation_frames
from native_coast_camera import observe

ROOT=Path(__file__).resolve().parents[2]
PREFERRED={'JourneySurfLink01000':'FourIsland_Frlg',
 'JourneySurfLink05400':'TwoIsland_Frlg','JourneySurfLink05301':'ThreeIsland_Port_Frlg',
 'JourneySurfLink05200':'SixIsland_Frlg','JourneySurfLink00600':'FiveIsland_Frlg',
 'JourneySurfLink00000':'BirthIsland_Exterior_Frlg','JourneyCinnabarSouthSea':'CinnabarIsland_Frlg',
 'JourneyLavenderApproach':'Route13_Frlg','JourneySurfLink02901':'Route19_Frlg',
 'JourneyFuchsiaSea':'Route19_Frlg','JourneyFuchsiaInlet':'FuchsiaCity_Frlg',
 'JourneyTwoThreePassage':'TwoIsland_Frlg','JourneyKantoSouthWestSea':'JourneyFuchsiaInlet'}


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--library',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    marker=json.loads((args.source/'.journey-game-continuity-review').read_bytes())['coasts']
    maps={p.parent.name:json.loads(p.read_bytes()) for p in (args.source/'data/maps').glob('*/map.json')}
    by_id={m['id']:n for n,m in maps.items()};names=set(ASSIGNMENTS)
    for n in ASSIGNMENTS:names.update(by_id[c['map']] for c in maps[n].get('connections') or [] if c['direction'] in ('left','right','up','down'))
    path=ROOT/'tools/hoenn/validate_integrated_piers.py'
    code=path.read_text().split('\nchecks = []\ntry:')[0]
    assert code.count('names = sorted(names)')==1
    code=code.replace('names = sorted(names)','names = '+repr(sorted(names)))
    sys.argv=[str(path),'--source',str(args.source),'--library',str(args.library),'--output',str(args.output)]
    ns={'__file__':str(path),'__name__':'game_continuity_coasts_native'}
    exec(compile(code,str(path),'exec'),ns)
    lib,native,step,warp,walk=(ns[k] for k in ('lib','native','step','warp','walk'))
    initial_sha,elf_sha=digest(args.source/'pokeemerald.gba'),digest(args.source/'pokeemerald.elf')
    captures=[];cases=[];fixtures=[]
    frames={'ocean':_animation_frames(args.source),
            'upper_current':animation_frames(args.source,'water_current_landwatersedge',416,(430,431,432,433)),
            'upper_sand':animation_frames(args.source,'sandwatersedge',464,(478,479,480,481))}
    slots={'ocean':(454,455),'upper_current':(430,431,432,433),'upper_sand':(478,479,480,481)}
    def state():
        r=ns['player_state']();assert r['surfing'] and r['elevation']==1 and r['priority']==2,r
        assert r['sprite_visible'] and r['object_visible'],r
        return r
    def picture(label):
        ns['picture'](label);row=dict(file=label+'.png',sha256=digest(args.output/(label+'.png')));captures.append(row);return row
    def bank():
        r=state();l=ns['layouts'][ns['maps'][r['map']]['layout']];at=lib.read32(ns['s']['gMapHeader'])
        p,q=lib.read32(at+16),lib.read32(at+20)
        assert p==ns['s'][l['primary_tileset']] and q==ns['s'][l['secondary_tileset']]
        return dict(map=r['map'],primary=l['primary_tileset'],secondary=l['secondary_tileset'],primary_pointer=p,secondary_pointer=q)
    def options(name):
        w,h,words=ns['blocks'][name];choices=[]
        for c in maps[name].get('connections') or []:
            if c['direction'] not in ('left','right','up','down'):continue
            neighbor=by_id[c['map']];tw,th,other=ns['blocks'][neighbor];d,off=c['direction'],c['offset']
            limit=h if d in ('left','right') else w
            for t in range(limit):
                if d=='right':edge=(w-1,t);target=(0,t-off);start=(w-2,t)
                elif d=='left':edge=(0,t);target=(tw-1,t-off);start=(1,t)
                elif d=='down':edge=(t,h-1);target=(t-off,0);start=(t,h-2)
                else:edge=(t,0);target=(t-off,th-1);start=(t,1)
                if not (0<=target[0]<tw and 0<=target[1]<th):continue
                points=[(name,start),(name,edge),(neighbor,target)]
                if not all(ns['blocks'][n][2][y*ns['blocks'][n][0]+x]>>12==1
                    and not ns['blocks'][n][2][y*ns['blocks'][n][0]+x]&0xC00
                    and ns['water_behaviors'][ns['behaviors'][n][y*ns['blocks'][n][0]+x]] for n,(x,y) in points):continue
                score=(0 if neighbor==PREFERRED.get(name) else 1,abs(t-limit//2),neighbor,t)
                choices.append((score,neighbor,start,target,c))
        assert choices,('No actual water crossing for changed camera',name)
        return min(choices)
    try:
        native('DisableWildEncounters',1);ns['set_passability'](water_only=True)
        for index,name in enumerate(ASSIGNMENTS):
            _,neighbor,start,target,connection=options(name)
            warp(name,*start);native('SetPlayerAvatarTransitionFlags',8);step(90)
            fixtures.append(dict(map=name,tile=list(start),surfing=True))
            before=state();before_bank=bank();before_pixels=observe(ns)
            before_capture=picture('camera-%02d-before'%index)
            phases=[];seen={group:set() for group in frames}
            for sample in range(16):
                step(8);matches={}
                for group,values in slots.items():
                    actual=b''.join(bytes(lib.read8(0x06000000+slot*32+i) for i in range(32)) for slot in values)
                    matches[group]=[p for p,data in enumerate(frames[group]) if data==actual]
                    assert matches[group],(name,group,sample)
                    seen[group].update(matches[group])
                pixels=observe(ns);capture=picture('camera-%02d-phase-%02d'%(index,sample))
                phases.append(dict(sample=sample,valid_native_phases=matches,camera=pixels,capture=capture))
            assert all(v==set(range(8)) for v in seen.values()),(name,seen)
            walk((neighbor,*target));step(90);after=state();after_bank=bank();after_pixels=observe(ns)
            after_capture=picture('camera-%02d-after'%index)
            walk((name,*start));step(90);returned=state();return_bank=bank();return_pixels=observe(ns)
            return_capture=picture('camera-%02d-return'%index)
            assert returned['map']==name and returned['tile']==list(start)
            cases.append(dict(map=name,neighbor=neighbor,connection=connection,
                before=before,before_bank=before_bank,before_pixels=before_pixels,before_capture=before_capture,
                phases=phases,after=after,after_bank=after_bank,after_pixels=after_pixels,after_capture=after_capture,
                returned=returned,return_bank=return_bank,return_pixels=return_pixels,return_capture=return_capture,
                controlled_outbound_and_return=True))
            print('Camera bank and controlled return passed:',name,neighbor,flush=True)
        transitions=list(ns['transitions']);walked=ns['walked']
    finally:lib.stop()
    assert digest(args.source/'pokeemerald.gba')==initial_sha and digest(args.source/'pokeemerald.elf')==elf_sha
    result=dict(kind='game-continuity-coasts',passed=True,rom_sha256=initial_sha,elf_sha256=elf_sha,
        compiled_rom=True,native_validation_performed=True,cases=cases,captures=captures,fixtures=fixtures,
        transitions=transitions,walked_tiles=walked,source_assignments=marker['assignments'],
        source_compatible_directed_seams=len(marker['affected_cardinal_seams']),
        initial_placement_party_progress_encounter_suppression_are_fixtures=True,
        no_midtrip_position_elevation_camera_palette_or_vram_writes=True,full_campaign_playthrough=False)
    (args.output/'game-continuity-coasts.json').write_text(json.dumps(result,indent=2)+'\n')
    print('All sixteen coastal camera banks, 8-phase animation groups and controller returns passed.',flush=True)


if __name__=='__main__':main()
