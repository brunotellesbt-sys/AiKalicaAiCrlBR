"""Independently replay the eight-gym overlay and audit flags, maps and saves."""
import argparse
import hashlib
import json
import re
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path
from prepare_extra_gyms import prepare, PRIOR, LAYER
ROOT=Path(__file__).resolve().parents[2]


def validate(source,baseline,output):
    source,baseline,output=map(Path,[source,baseline,output])
    report=json.loads((source/('.journey-'+LAYER)).read_text())
    expected=dict(json.loads((baseline/'.source-acquired.json').read_text())['sha256'])
    for name in PRIOR:expected.update(json.loads((baseline/('.journey-'+name)).read_text())['prepared_sha256'])
    outputs=report['prepared_sha256']
    for name,digest in (expected|outputs).items():assert hashlib.sha256((source/name).read_bytes()).hexdigest()==digest,name
    with tempfile.TemporaryDirectory(prefix='extra-gyms-replay-',dir='/tmp') as tmp:
        replay=Path(tmp)
        for name in expected:
            p=replay/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(baseline/name,p)
        for name in ['.source-acquired.json',*['.journey-'+n for n in PRIOR]]:shutil.copyfile(baseline/name,replay/name)
        fresh=json.loads(json.dumps(prepare(replay)))
        if fresh!=report:
            def differences(a,b,path=''):
                if type(a)!=type(b):return [(path,'type mismatch')]
                if isinstance(a,dict):return [v for k in a.keys()|b.keys() for v in (differences(a.get(k),b.get(k),path+'/'+k))]
                if isinstance(a,list):
                    if len(a)!=len(b):return [(path,len(a),len(b))]
                    return [v for i,(aa,bb) in enumerate(zip(a,b)) for v in differences(aa,bb,path+'/'+str(i))]
                return [] if a==b else [(path,a,b)]
            raise AssertionError(differences(fresh,report)[:12])
        assert prepare(replay)==fresh
    # Compile macros rather than guessing from literal hex definitions: aliases
    # and arithmetic flag definitions also reserve save bits.
    oldnames=list(dict.fromkeys(re.findall(r'^#define (FLAG_\w+)\s',(baseline/'include/constants/flags.h').read_text(),re.M)))
    code='#include "constants/flags.h"\nconst unsigned short probe[]={'+','.join(oldnames)+'};\n'
    asm=subprocess.check_output([str(ROOT/'.local/arm-gcc/usr/bin/arm-none-eabi-gcc'),'-S','-iquote',str(baseline/'include'),'-x','c','-','-o','-'],input=code,text=True)
    used={int(v) for v in re.findall(r'\.short\s+(\d+)',asm)}|set(range(0x500,0x500+1622))
    assert not used.intersection(report['allocated_flags'])
    assert max(report['allocated_flags'])<872*8
    layouts={l['id']:l for l in json.loads((source/'data/layouts/layouts.json').read_text())['layouts']}
    preserved=0;room_checks=[]
    for g in report['gyms']:
        path=f'data/maps/{g["city"]}/map.json';new=json.loads((source/path).read_text());old=json.loads((baseline/path).read_text())
        assert new['object_events']==old['object_events']
        repaired=report['coastal_fixes']['geography']['repaired_links']
        for c in old['connections'] or []:
            if c in (new['connections'] or []):continue
            assert any(g['city'] in [q['source'],q['destination']] for q in repaired), (g['city'],c)

        for key in ['warp_events','coord_events','bg_events']:assert new[key][:len(old[key])]==old[key]
        assert len(new['warp_events'])==len(old['warp_events'])+1
        preserved+=sum(len(old[k]) for k in ['warp_events','coord_events','bg_events','object_events'])
        m=json.loads((source/f'data/maps/{g["name"]}/map.json').read_text());l=layouts[m['layout']]
        v=struct.unpack('<'+'H'*(l['width']*l['height']),(source/l['blockdata_filepath']).read_bytes())
        assert len(m['object_events'])==6 and len(m['warp_events'])==2
        assert all(not v[o['y']*l['width']+o['x']]&0xC00 for o in m['object_events'])
        assert len({o['script'] for o in m['object_events']})==6
        # Every room is an open walking space; decor cannot silently erase
        # a whole object to make a sightline or create a sliding/warp puzzle.
        room=g['room'];assert (l['width'],l['height'])==(room['width'],room['height'])
        assert room['no_puzzles'] and room['ordinary_walking_floor'] and room['complete_native_props']
        # Arrival and the three-tile central entrance corridor stay empty.
        assert all(not(abs(o['x']-room['entry'][0])<=1 and o['y']>=room['height']-4) for o in m['object_events'])
        assert room['guide']==[1,3]
        from extra_gyms import STUDENT_PROFILES
        trainer_data=(source/'src/data/journey_extra_gym_trainers.h').read_text()
        for j,profile in enumerate(STUDENT_PROFILES[g['key']]):
            assert m['object_events'][j+2]['graphics_id']=='OBJ_EVENT_GFX_'+profile[2]
            number=g['students'][j]-1769
            record=re.search(r'\[TRAINER_JOURNEY_GYM_STUDENT_'+str(number)+r'\]=(.*?)(?:\n|$)',trainer_data)[1]
            assert '.trainerClass=TRAINER_CLASS_'+profile[0]+',' in record and '.trainerPic=TRAINER_PIC_'+profile[1]+',' in record
        walkable={i for i,t in enumerate(v) if not t&0xc00};start=room['entry'][1]*l['width']+room['entry'][0]
        seen={start};todo=[start]
        while todo:
            i=todo.pop();xx,yy=i%l['width'],i//l['width']
            for x,y in [(xx-1,yy),(xx+1,yy),(xx,yy-1),(xx,yy+1)]:
                j=y*l['width']+x
                if 0<=x<l['width'] and 0<=y<l['height'] and j in walkable and j not in seen:seen.add(j);todo.append(j)
        assert seen==walkable,(g['key'],'disconnected floor')
        folder=source/'data/tilesets/secondary'/g['key'].lower()
        attrs=struct.unpack('<'+'H'*((folder/'metatile_attributes.bin').stat().st_size//2),(folder/'metatile_attributes.bin').read_bytes())
        exits={(q['x'],q['y']) for q in m['warp_events']}
        for i in walkable:
            if (i%l['width'],i//l['width']) not in exits:assert attrs[(v[i]&1023)-512]&255==0,(g['key'],'nonstandard floor behavior',i)
        for j,student in enumerate(room['students']):
            actor=m['object_events'][j+2];x,y=student['position'];assert int(actor['trainer_sight_or_berry_tree_id'])>=5
            assert actor['movement_type']=='MOVEMENT_TYPE_FACE_'+student['facing']
            dx,dy={'RIGHT':(1,0),'LEFT':(-1,0),'DOWN':(0,1),'UP':(0,-1)}[student['facing']]
            for distance in range(7):
                xx,yy=x+dx*distance,y+dy*distance;assert yy*l['width']+xx in walkable
                assert all([xx,yy]!=other['position'] for other in room['students'] if other is not student)
                # Independently inspect the built map: a full three-wide
                # approach, not an actor in a one-tile slot between walls.
                for side in [-1,1]:
                    assert (yy+dx*side)*l['width']+xx+dy*side in walkable,(g['key'],'narrow trainer recess',student,distance)
        assert len(room['students'])==4 and {student['facing'] for student in room['students']}=={'RIGHT','DOWN','LEFT','UP'}
        mandatory=[]
        for student in room['students']:
            x,y=student['position'];dx,dy={'RIGHT':(1,0),'LEFT':(-1,0),'DOWN':(0,1),'UP':(0,-1)}[student['facing']]
            cut={(y+dy*d)*l['width']+x+dx*d for d in range(7)}
            reached={start};pending=[start]
            while pending:
                i=pending.pop();xx,yy=i%l['width'],i//l['width']
                for xxx,yyy in [(xx-1,yy),(xx+1,yy),(xx,yy-1),(xx,yy+1)]:
                    q=yyy*l['width']+xxx
                    if 0<=xxx<l['width'] and 0<=yyy<l['height'] and q in walkable and q not in cut and q not in reached:reached.add(q);pending.append(q)
            target=room['leader_approach'][1]*l['width']+room['leader_approach'][0]
            assert target not in reached,(g['key'],'trainer can be bypassed',student)
            mandatory.append(dict(position=student['position'],facing=student['facing'],removing_sightline_disconnects_leader=True))
        room_checks.append(dict(map=g['name'],theme=room['theme'],size=[l['width'],l['height']],connected_floor=True,no_puzzle_floor_behaviors=True,long_clear_sightlines=True,three_wide_clear_trainer_approaches=True,mandatory_checkpoints=mandatory))
    assert len({tuple(q['size']) for q in room_checks})>=7 and len({q['theme'] for q in room_checks})==8
    from PIL import Image
    sprites=[]
    info=(source/'src/data/object_events/object_event_graphics_info.h').read_text()
    tables=(source/'src/data/object_events/object_event_pic_tables.h').read_text()
    for key in ['MORTY','WHITNEY','VALERIE','STEVEN','BUGSY','CANDICE','CLAIR','KAREN']:
        image=Image.open(source/f'graphics/object_events/pics/people/journey_pwt_{key.lower()}.png')
        assert image.mode=='P' and image.height==288 and image.width in [16,32]
        assert image.getextrema()[1]<16
        for frame in range(9):
            for x,y in [(0,0),(image.width-1,0),(0,31),(image.width-1,31)]:assert image.getpixel((x,frame*32+y))==0,(key,'opaque matte',frame,x,y)
        native=re.search(r'gObjectEventGraphicsInfo_JourneyPWT'+key+r' = \{(.*?)\};',info,re.S)[1]
        assert int(re.search(r'\.width=(\d+)',native)[1])==image.width
        assert int(re.search(r'\.size=(\d+)',native)[1])==image.width*32//2
        assert re.search(r'sPicTable_JourneyPWT'+key+r'\[\] = \{ overworld_ascending_frames\(gObjectEventPic_JourneyPWT'+key+', '+str(image.width//8)+r', 4\) \};',tables)
        sprites.append(dict(leader=key,transparent_index_zero=True,native_frame_dimensions_match=True,width=image.width,height=32,frames=9))
    # No Surf route or cave changed, including the latest Frontier market and
    # the 105 legendary placements merged in PR95.
    preserved_routes=[p for p in expected if p.startswith(('data/maps/Route','data/layouts/Route')) and p not in outputs]
    assert len(preserved_routes)>100
    for p in ['src/journey_campaign_gates.c','src/journey_crossover.c','include/journey_team_missions.h','src/data/journey_pwt_trainers.h','include/constants/vars.h','include/trainer_card.h','include/global.h']:
        assert (source/p).read_bytes()==(baseline/p).read_bytes(),p
    def compiled_values(tree,names,include):
        code='#include "global.h"\n#include "'+include+'"\nconst u32 probe[]={'+','.join(names)+'};'
        asm=subprocess.check_output([str(ROOT/'.local/arm-gcc/usr/bin/arm-none-eabi-gcc'),'-S','-mabi=apcs-gnu','-iquote',str(tree/'include'),'-iquote',str(source/'include'),'-iquote',str(source/'include/constants'),'-x','c','-','-o','-'],input=code,text=True)
        return [int(n) for n in re.findall(r'\.word\s+(\d+)',asm)]
    items=['ITEM_TM_'+m for m in re.findall(r'F\((\w+)\)',(baseline/'include/constants/tms_hms.h').read_text().split('#define FOREACH_HM')[0])]+['ITEM_HM_SURF','ITEM_HM_DIVE','ITEM_HM_WATERFALL','ITEM_HM_FLY']
    assert compiled_values(source,items,'constants/items.h')==compiled_values(baseline,items,'constants/items.h')
    sizes=['sizeof(struct SaveBlock1)','sizeof(struct SaveBlock2)','FLAGS_COUNT']
    assert compiled_values(source,sizes,'constants/flags.h')==compiled_values(baseline,sizes,'constants/flags.h')
    for symbol in ['sWorldTiles','sWorldTilemap','sWorldPalette','sWorldDetailPixels']:
        pattern=symbol+r'\[\].*?=\s*\{([^}]+)'
        assert re.search(pattern,(source/'src/data/journey_world_map.h').read_text(),re.S)[1]==re.search(pattern,(baseline/'src/data/journey_world_map.h').read_text(),re.S)[1],symbol
    # Replaced marine links retain every object, cave door and story event.
    for p in (baseline/'data/maps').glob('*/map.json'):
        n=p.parent.name
        if n in [g['city'] for g in report['gyms']]:continue
        old=json.loads(p.read_text());new=json.loads((source/p.relative_to(baseline)).read_text())
        for key in ['warp_events','coord_events','bg_events']:assert old.get(key)==new.get(key),(n,key)
        if n!='Route107':assert old.get('object_events')==new.get('object_events'),n
        else:assert new['object_events'][:-1]==old['object_events'] and new['object_events'][-1]['script']=='JourneyCompetitive_Seller'
    r=dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),layers=PRIOR+[LAYER],
        independent_replay=True,idempotent=True,source_hashes_checked=len(expected|outputs),unrelated_files_preserved=len(expected.keys()-outputs.keys()),
        original_city_events_preserved=preserved,flag_macros_compiled=len(oldnames),allocated_flags_disjoint=True,save_and_link_abi_unchanged=True,
        original_tm_hm_numbers_preserved=True,old_campaign_and_pwt_preserved=True,all_legendary_encounters_and_cave_doors_preserved=True,atlas_graphics_unchanged=True,coastal_fixes=report['coastal_fixes'],
        gyms=report['gyms'],room_checks=room_checks,gym_leader_sprites=sprites,interior_themes_distinct=True,all_room_floors_connected=True,long_clear_trainer_sightlines=True,non_puzzle_rooms=True,total_badges=24,pending_story_milestones=[18,22],pending_story_events_implemented=False)
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(r,indent=2)+'\n');return r

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--baseline',required=True);p.add_argument('--output',required=True);a=p.parse_args();validate(a.source,a.baseline,a.output)
