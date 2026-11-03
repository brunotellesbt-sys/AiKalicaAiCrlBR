"""Cold boot through the real menus, voyage, mother welcome and home entry.

Only controller input and read-only emulator observations are used. Diagnostic
mode reports invalid old landings without treating them as a passing proof.
"""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
BOAT_STARTS = [('sevii',i) for i in range(7)] + [('hoenn',4),('hoenn',12),('hoenn',14)]
CUSTOM_STARTS = BOAT_STARTS + [(region,city) for region,count in [('kanto',9),('hoenn',15)]
    for city in range(count) if not (region == 'hoenn' and city == 0)
    and (region,city) not in BOAT_STARTS]
assert len(CUSTOM_STARTS)==30 and len(set(CUSTOM_STARTS))==30


def compiled_arrival_census(source):
    """Read all arrival rows and both standing cells from the compiled ROM."""
    source=Path(source).resolve();rom=(source/'pokeemerald.gba').read_bytes()
    nm=subprocess.check_output([str(ROOT/'.local/arm-binutils/usr/bin/arm-none-eabi-nm'),
        '-n',str(source/'pokeemerald.elf')],text=True)
    symbols={n:int(a,16) for a,k,n in re.findall(r'^(\w+) (\w) (\S+)$',nm,re.M)}
    def u8(address):return rom[address-0x08000000]
    def u16(address):return struct.unpack_from('<H',rom,address-0x08000000)[0]
    def u32(address):return struct.unpack_from('<I',rom,address-0x08000000)[0]
    groups=json.loads((source/'data/maps/map_groups.json').read_text())
    by_location={(g,i):n for g,label in enumerate(groups['group_order']) for i,n in enumerate(groups[label])}
    by_name={name:(g,i) for (g,i),name in by_location.items()}
    map_ids={json.loads(p.read_text())['id']:p.parent.name for p in (source/'data/maps').glob('*/map.json')}
    header=(source/'include/journey_birth_arrivals.h').read_text()
    source_rows=re.findall(r'\{(MAP_\w+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(TRUE|FALSE)\}',header)
    assert len(source_rows)==31
    rows=[];raw_table=b''
    for index,record in enumerate(source_rows):
        source_map,tx,ty,lx,ly,boat=record
        tx,ty,lx,ly=map(int,(tx,ty,lx,ly));g,n=by_name[map_ids[source_map]]
        expected=struct.pack('<HhhhhBx',(g<<8)|n,tx,ty,lx,ly,boat=='TRUE')
        offset=symbols['sJourneyBirthArrivals']-0x08000000+12*index
        actual=rom[offset:offset+12];assert actual==expected,('Compiled arrival table differs',index+1)
        raw_table+=actual
        map_header=u32(u32(symbols['gMapGroups']+g*4)+n*4)
        layout=u32(map_header);width,height=u32(layout),u32(layout+4)
        frlg=bool(u8(layout+24));cutoff=640 if frlg else 512
        def cell(x,y):
            assert 0<=x<width and 0<=y<height
            value=u16(u32(layout+12)+2*(y*width+x));mid=value&1023
            bank=u32(layout+(16 if mid<cutoff else 20));attribute=u32(bank+16)
            number=mid if mid<cutoff else mid-cutoff
            behavior=u32(attribute+4*number)&511 if frlg else u16(attribute+2*number)&255
            surfable=bool(u8(symbols['sTileBitAttributes']+behavior)&2)
            return dict(tile=[x,y],block=value,elevation=value>>12,collision=(value>>10)&3,
                behavior=behavior,surfable=surfable,
                dry=(value>>12)>=3 and not value&0xC00 and not surfable)
        mother=(lx,ly-1) if boat=='TRUE' else (tx+2,ty-1)
        rows.append(dict(home_index=index+1,map=map_ids[source_map],map_id=[g,n],
            truck=[tx,ty],boat=boat=='TRUE',player=cell(lx,ly),mother=cell(*mother)))
    return dict(rows=rows,row_count=31,compiled_table_sha256=hashlib.sha256(raw_table).hexdigest(),
        compiled_source_table_equal=True,all_player_and_mother_cells_dry=all(
            row['player']['dry'] and row['mother']['dry'] for row in rows),
        direct_compiled_map_layout_blockdata_and_attribute_reads=True)


def validate_all(source,library,output,diagnose=False,all_custom=False):
    source,library,output=(Path(x).resolve() for x in (source,library,output))
    output.mkdir(parents=True,exist_ok=True)
    census=compiled_arrival_census(source);cases=[];reports=[];captures=[]
    for region,city in (CUSTOM_STARTS if all_custom else BOAT_STARTS):
        folder=f'{region}-{city:02d}';destination=output/folder
        command=[str(Path(__file__).resolve()),'--source',str(source),'--library',str(library),
                 '--output',str(destination),'--region',region,'--city-index',str(city)]
        if region == 'sevii' and city == 0:
            command += ['--avatar-index', '3']
        if diagnose:command.append('--diagnose')
        import sys
        child=subprocess.run([sys.executable,*command],capture_output=True,text=True)
        assert child.returncode==0,child.stdout+child.stderr
        path=destination/'arrival-coast-landing-case.json';case=json.loads(path.read_bytes())
        reports.append(dict(file=f'{folder}/{path.name}',sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        for capture in case['captures']:
            row=dict(capture,file=f'{folder}/{capture["file"]}');captures.append(row)
        cases.append({key:value for key,value in case.items() if key not in ('captures','input_log','callback_transitions')})
        print('Actual full-start case:',region,city,case['passed'],flush=True)
    result=dict(kind='arrival-coast-landing',passed=bool(census['all_player_and_mother_cells_dry']
        and all(row['passed'] for row in cases)),diagnostic=bool(diagnose),
        rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
        elf_sha256=hashlib.sha256((source/'pokeemerald.elf').read_bytes()).hexdigest(),
        compiled_arrival_census=census,cases=cases,case_reports=reports,
        components=reports,captures=captures,
        full_new_game_controller_cases=len(cases),all_ten_modified_boat_starts_tested=True,
        all_thirty_custom_start_cities_tested=bool(all_custom),
        original_littleroot_scene_covered_by_compiled_census_only=True,
        actual_cold_boot=True,controllers_only=True,no_game_memory_writes=True,
        no_callback_or_script_injection=True)
    (output/'arrival-coast-landing.json').write_text(json.dumps(result,indent=2)+'\n')
    assert diagnose or result['passed']
    return result


def validate(source, library, output, region, city_index, diagnose=False, avatar_index=0):
    source, library, output = (Path(x).resolve() for x in (source, library, output))
    output.mkdir(parents=True, exist_ok=True)
    assert avatar_index in range(4)
    rom_sha = hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest()
    elf_sha = hashlib.sha256((source/'pokeemerald.elf').read_bytes()).hexdigest()
    nm = subprocess.check_output([str(ROOT/'.local/arm-binutils/usr/bin/arm-none-eabi-nm'),
        '-n', str(source/'pokeemerald.elf')], text=True)
    symbols = {n:int(a,16) for a,k,n in re.findall(r'^(\w+) (\w) (\S+)$',nm,re.M)}
    names = {v:k for k,v in symbols.items()}
    groups = json.loads((source/'data/maps/map_groups.json').read_text())
    by_location = {(g,i):n for g,label in enumerate(groups['group_order']) for i,n in enumerate(groups[label])}
    maps = {json.loads(p.read_text())['id']:p.parent.name for p in (source/'data/maps').glob('*/map.json')}
    home_index = city_index + {'kanto':1,'sevii':10,'hoenn':17}[region]
    homes = re.findall(r'\{(MAP_\w+),\s*(MAP_\w+),\s*(MAP_\w+),',
                       (source/'include/journey_family_homes.h').read_text())
    assert 1 <= home_index <= len(homes)
    expected_bedroom = maps[homes[home_index-1][2]]
    expected_arrival = compiled_arrival_census(source)['rows'][home_index-1]
    expected_welcome_player = list(expected_arrival['player']['tile'])
    # The real truck script jumps one tile right before the welcome message;
    # boat arrivals stand directly on their compiled landing coordinate.
    if not expected_arrival['boat']:
        expected_welcome_player[0] += 1
    lib = ctypes.CDLL(str(library))
    lib.start.argtypes = [ctypes.c_char_p]
    lib.image.restype = ctypes.c_void_p
    lib.read32.restype = ctypes.c_uint32
    inputs, transitions, captures = [], [], []
    frames = 0
    previous_callback = None

    def callback(): return lib.read32(symbols['gMain']+4)&~1
    def save(): return lib.read32(symbols['gSaveBlock1Ptr'])
    def map_name():
        pointer = save()
        if not 0x02000000 <= pointer < 0x02040000: return None
        return by_location.get((lib.read8(pointer+4),lib.read8(pointer+5)))
    def step(count,key=0):
        nonlocal frames,previous_callback
        while count:
            n=min(count,30);lib.frames(n,key);frames+=n;count-=n
            cb=callback()
            if cb!=previous_callback:
                transitions.append(dict(frame=frames,callback=names.get(cb,hex(cb))))
                previous_callback=cb
    def press(key=1,pause=45):
        inputs.append(dict(frame=frames,key=key,held_frames=1,pause_frames=pause))
        step(1,key);step(pause)
    def active(name):
        return [i for i in range(16) if lib.read8(symbols['gTasks']+i*40+4)
                and lib.read32(symbols['gTasks']+i*40)&~1==symbols.get(name)]
    def task_names():
        return [names.get(lib.read32(symbols['gTasks']+i*40)&~1,'?')
                for i in range(16) if lib.read8(symbols['gTasks']+i*40+4)]
    def picture(label):
        path=output/(label+'.png')
        Image.frombytes('RGBA',(240,160),ctypes.string_at(lib.image(),240*160*4)).convert('RGB').save(path)
        captures.append(dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    def until(predicate,label,advance=False,limit=900):
        for _ in range(limit):
            if predicate(): return
            if advance: press()
            else: step(30)
        picture('failed-'+label)
        raise AssertionError((label,frames,map_name(),task_names(),names.get(callback())))
    def object_state(index):
        pointer=symbols['gObjectEvents']+36*index
        return dict(index=index,local_id=lib.read8(pointer+8),
            tile=[lib.read16(pointer+16)-7,lib.read16(pointer+18)-7],
            elevation=lib.read8(pointer+11)&15)
    def object_indices(local_id):
        return [i for i in range(16) if lib.read8(symbols['gObjectEvents']+36*i)&1
                and lib.read8(symbols['gObjectEvents']+36*i+8)==local_id]
    def terrain(tile):
        x,y=tile;x+=7;y+=7
        grid=symbols['gBackupMapLayout'];width=lib.read32(grid)
        value=lib.read16(lib.read32(grid+8)+2*(y*width+x))
        layout=lib.read32(symbols['gMapHeader']);frlg=bool(lib.read8(layout+24))
        mid=value&1023;cutoff=640 if frlg else 512
        bank=lib.read32(layout+(16 if mid<cutoff else 20))
        attr=lib.read32(bank+16);index=mid if mid<cutoff else mid-cutoff
        behavior=(lib.read32(attr+4*index)&511) if frlg else (lib.read16(attr+2*index)&255)
        surfable=bool(lib.read8(symbols['sTileBitAttributes']+behavior)&2)
        return dict(block=value,elevation=value>>12,collision=(value>>10)&3,
                    behavior=behavior,surfable=surfable,
                    dry=(value>>12)>=3 and not value&0xC00 and not surfable)

    with tempfile.TemporaryDirectory(prefix='coastal-arrival-coldboot-',dir='/tmp') as temporary:
        rom=Path(temporary)/'arrival.gba';shutil.copyfile(source/'pokeemerald.gba',rom)
        assert lib.start(str(rom).encode())
        try:
            step(1200);press(8,300)
            until(lambda:callback()==symbols['CB2_MainMenu'],'main-menu',advance=True)
            step(300)
            press()
            until(lambda:bool(active('Task_JourneyIntroRegion')) and bool(active('Task_HandleMultichoiceInput')),
                  'region-menu')
            step(60);picture('01-region-menu')
            for _ in range({'hoenn':0,'kanto':1,'sevii':2}[region]):press(128)
            press()
            naming_confirmed=False
            for _ in range(1200):
                if callback()==symbols.get('CB2_NamingScreen'):
                    step(120);press(8);press();naming_confirmed=True
                elif map_name()=='InsideOfTruck' and active('Task_HandleMultichoiceInput'):
                    break
                else:press()
            else:raise AssertionError(('No avatar menu',map_name(),task_names()))
            assert naming_confirmed
            picture('02-avatar-menu')
            for _ in range(avatar_index):press(128)
            press()
            wanted='Task_HandleMultichoiceInput' if region=='sevii' else 'Task_HandleMultichoiceGridInput'
            # The selected avatar task is destroyed by the previous A press;
            # advance only the intervening choose-town text until the next menu.
            until(lambda:bool(active(wanted)),'city-menu',advance=True)
            step(60);picture('03-city-menu')
            for _ in range(city_index if region=='sevii' else city_index//3):press(128)
            if region!='sevii':
                for _ in range(city_index%3):press(16)
            press()
            until(lambda:bool(active('Task_HandleYesNoInput')),'city-confirmation',advance=True)
            picture('04-city-confirmation');press()
            until(lambda:map_name()=='InsideOfTruck' and callback()==symbols['CB2_Overworld']
                  and not lib.read8(symbols['sLockFieldControls']), 'unlocked-truck',advance=True)
            picture('05-truck')
            for _ in range(80):
                if map_name()!='InsideOfTruck':break
                inputs.append(dict(frame=frames,key=16,held_frames=8,pause_frames=20))
                step(8,16);step(20)
            else:raise AssertionError('Cannot leave truck through native door')
            until(lambda:callback()==symbols['CB2_Overworld'] and bool(object_indices(251)),
                  'mother-welcome',advance=True)
            step(90)
            player=object_state(lib.read8(symbols['gPlayerAvatar']+5))
            mother=object_state(object_indices(251)[0])
            player['terrain']=terrain(player['tile']);mother['terrain']=terrain(mother['tile'])
            player['surfing']=bool(lib.read8(symbols['gPlayerAvatar'])&8)
            other=[object_state(i) for i in range(16) if lib.read8(symbols['gObjectEvents']+36*i)&1
                   and i not in [player['index'],mother['index']]
                   and lib.read8(symbols['gObjectEvents']+36*i+8)!=250]
            overlaps=[row for row in other if row['tile'] in [player['tile'],mother['tile']]]
            welcome=dict(map=map_name(),player=player,mother=mother,other_npc_overlaps=overlaps)
            picture('06-mother-welcome')
            selected_destination_observed=(welcome['map']==expected_arrival['map']
                and player['tile']==expected_welcome_player
                and mother['tile']==expected_arrival['mother']['tile'])
            dry=player['terrain']['dry'] and mother['terrain']['dry']
            coherent=(player['elevation']==player['terrain']['elevation']
                      and mother['elevation']==mother['terrain']['elevation'])
            surface_valid=(dry and coherent and not player['surfing'] and not overlaps
                           and selected_destination_observed)
            until(lambda:map_name()==expected_bedroom and callback()==symbols['CB2_Overworld']
                  and not lib.read8(symbols['sLockFieldControls']), 'home-bedroom',advance=True)
            picture('07-home-bedroom')
            bedroom_player=object_state(lib.read8(symbols['gPlayerAvatar']+5))
            bedroom=dict(map=map_name(),player=bedroom_player,surfing=bool(lib.read8(symbols['gPlayerAvatar'])&8))
            assert not bedroom['surfing']
            report=dict(kind='arrival-coast-landing-case',passed=bool(surface_valid),
                diagnostic=bool(diagnose),rom_sha256=rom_sha,elf_sha256=elf_sha,
                starting_region=region,city_index=city_index,home_index=home_index,
                avatar_index=avatar_index,
                controllers_only=True,no_game_memory_writes=True,no_callback_or_script_injection=True,
                actual_cold_boot=True,actual_city_selection_and_confirmation=True,
                native_truck_door_crossed=True,native_boat_scene_observed=any(
                    'SeaGallop' in x['callback'] or 'Seagallop' in x['callback'] for x in transitions),
                welcome=welcome,arrival_player_and_mother_dry=dry,
                compiled_selected_destination_observed=selected_destination_observed,
                expected_welcome_map=expected_arrival['map'],
                expected_welcome_player_tile=expected_welcome_player,
                expected_welcome_mother_tile=expected_arrival['mother']['tile'],
                actor_elevations_match_physical_ground=coherent,
                no_existing_npc_overlap=not overlaps,native_home_bedroom_reached=True,
                bedroom=bedroom,frames=frames,input_log=inputs,callback_transitions=transitions,captures=captures)
            assert hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest()==rom_sha
            assert hashlib.sha256((source/'pokeemerald.elf').read_bytes()).hexdigest()==elf_sha
            (output/'arrival-coast-landing-case.json').write_text(json.dumps(report,indent=2)+'\n')
            assert diagnose or surface_valid, welcome
            return report
        finally:lib.stop()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--library',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--region',choices=['hoenn','kanto','sevii'])
    parser.add_argument('--city-index',type=int)
    parser.add_argument('--avatar-index',type=int,default=0,choices=range(4))
    parser.add_argument('--all-boat-starts',action='store_true')
    parser.add_argument('--all-custom-starts',action='store_true')
    parser.add_argument('--diagnose',action='store_true')
    args=parser.parse_args()
    if args.all_boat_starts or args.all_custom_starts:
        result=validate_all(args.source,args.library,args.output,args.diagnose,args.all_custom_starts)
        print('Actual full-start arrivals:',result['full_new_game_controller_cases'],result['passed'])
    else:
        assert args.region is not None and args.city_index is not None
        result=validate(args.source,args.library,args.output,args.region,args.city_index,args.diagnose,args.avatar_index)
        print('Arrival cold boot:',result['starting_region'],result['city_index'],
              'passed',result['passed'],'welcome',result['welcome']['map'])
