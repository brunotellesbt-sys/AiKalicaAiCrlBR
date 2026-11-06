"""Native proof of permanent scenery before a seam and complete boundary rocks.

Initial party/progress/placement are declared fixtures. Every subsequent move
uses controllers. Read-only native getters inspect the loaded terrain; actual
BG/OAM/VRAM/palette pixels are matched to the exported native screenshots.
"""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import sys

from PIL import Image

from validate_sevii_route_boundaries_native import observe_cells
from verify_sevii_route_boundaries_native import verify_pixels
from verify_sevii_integrated_piers_update import verify_captures

ROOT = Path(__file__).resolve().parents[2]
ROCK_LOCAL_ID = 4
LINK = 'JourneySurfLink05000'
OWNER = 'OneIsland_Frlg'
# Representatives include four independently drawn complete native rocks.
BOULDERS = [('OneIsland_KindleRoad_Frlg', [0, 21]),
            ('TwoIsland_Harbor_Frlg', [2, 0])]
EDGES = [('west-cliff', LINK, [15,2], [16,-1], 0x274),
         ('kindle-sand', 'OneIsland_KindleRoad_Frlg', [21,20], [23,18], 0x20A)]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rock_objects(lib, symbols, owner_id):
    result = []
    for index in range(16):
        at = symbols['gObjectEvents']+36*index
        if (lib.read8(at)&1 and lib.read8(at+8) == ROCK_LOCAL_ID
                and (lib.read8(at+10), lib.read8(at+9)) == tuple(owner_id)):
            result.append(dict(slot=index, local_id=lib.read8(at+8),
                map_id=[lib.read8(at+10), lib.read8(at+9)],
                graphics_id=lib.read16(at+4)&65535,
                tile=[(lib.read16(at+16)&65535)-7, (lib.read16(at+18)&65535)-7],
                sprite_id=lib.read8(at+35)))
    return result


def rock_pixels(lib, symbols, row):
    """Match every opaque pixel of the actual stationary rock OBJ frame."""
    sprite = symbols['gSprites']+68*row['sprite_id']
    source_attr2 = lib.read16(sprite+4)&65535
    assert not lib.read8(symbols['gObjectEvents']+36*row['slot']+1)&32
    assert not (lib.read16(sprite+0x3E)&4), 'Permanent scenery sprite hidden'
    dimensions = [[(8,8),(16,16),(32,32),(64,64)],
                  [(16,8),(32,8),(32,16),(64,32)],
                  [(8,16),(8,32),(16,32),(32,64)]]
    candidates = []
    for index in range(128):
        at = 0x07000000+8*index
        a0, a1, a2 = (lib.read16(at+2*i)&65535 for i in range(3))
        if a0&0x300 == 0x200 or a0 >> 14 > 2 or a2&0xF3FF != source_attr2&0xF3FF:
            continue
        width, height = dimensions[a0 >> 14][a1 >> 14]
        if (width, height) != (16,16):
            continue
        x, y = a1&511, a0&255
        x = x-512 if x >= 256 else x
        y = y-256 if y >= 160 else y
        if 0 <= x <= 224 and 0 <= y <= 144:
            candidates.append((index,a0,a1,a2,x,y))
    assert len(candidates) == 1, ('Rock hardware OAM not unique/fully visible', candidates, row)
    index,a0,a1,a2,x,y = candidates[0]
    assert not a0&0x2100, 'Unexpected affine or 8bpp scenery'
    image = ctypes.string_at(lib.image(),240*160*4)
    palette = []
    for color in range(16):
        word = lib.read16(0x05000200+2*(16*(a2 >> 12)+color))&32767
        palette.append(tuple(((word >> shift)&31)<<3 for shift in (0,5,10)))
    stride = 2 if lib.read16(0x04000000)&64 else 32
    samples, expected, matched = [],0,0
    for py in range(16):
        yy = 15-py if a1&0x2000 else py
        for px in range(16):
            xx = 15-px if a1&0x1000 else px
            tile = (a2&1023)+(yy//8)*stride+xx//8
            byte = lib.read8(0x06010000+32*tile+4*(yy%8)+(xx%8)//2)
            color = (byte >> (4*(xx&1)))&15
            if not color:
                continue
            at = 4*((y+py)*240+x+px)
            actual = image[at:at+3]
            expected += 1
            visible = all(abs(a-b) <= 7 for a,b in zip(actual,palette[color]))
            matched += visible
            samples.append([x+px,y+py,*palette[color],visible])
    assert expected >= 100 and matched >= expected*.95, ('Rock hidden by terrain or UI',matched,expected)
    return dict(hardware_oam_index=index, screen_rectangle=[x,y,16,16],
        expected_opaque_pixels=expected,matching_scanout_pixels=matched,
        expected_scanout_pixels=samples,exact_current_vram_frame_compared=True)


def bootstrap(source, library, output, names):
    path = ROOT/'tools/hoenn/validate_integrated_piers.py'
    code = path.read_text().split('\nchecks = []\ntry:')[0]
    assert code.count('names = sorted(names)') == 1
    code = code.replace('names = sorted(names)', 'names = '+repr(sorted(names)))
    previous_argv = sys.argv
    sys.argv = [str(path),'--source',str(source),'--library',str(library),'--output',str(output)]
    ns = {'__file__':str(path),'__name__':'coast_scenery_objects_native'}
    try:
        exec(compile(code,str(path),'exec'),ns)
    finally:
        sys.argv = previous_argv
    ns['lib'].read16.restype = ctypes.c_uint16
    return ns


def _field_probe(source, library, output, *, broken_baseline=False):
    output.mkdir(parents=True,exist_ok=True)
    names = {LINK,OWNER}|{name for name,anchor in BOULDERS}
    ns = bootstrap(source,library,output,names)
    lib,s = ns['lib'],ns['s']
    original_step, original_native, original_warp, original_script = (ns[key] for key in ('step','native','warp','script'))
    owner_id = ns['map_id'](OWNER)
    fixtures,inputs,queries,captures,views,bumps,edges = [],[],[],[],[],[],[]
    active,depth,phase = True,0,'bootstrap'
    battery = None

    def step(count,key=0):
        if not active:
            if inputs and inputs[-1]['phase'] == phase and inputs[-1]['key'] == key:
                inputs[-1]['frames'] += count
            else:
                inputs.append(dict(phase=phase,frames=count,key=key))
        original_step(count,key)

    def native(name,*values,**kwargs):
        nonlocal depth
        if not active:
            assert name.startswith(('MapGridGet','MetatileBehavior_Is')) or name in {
                'GetPlayerFacingDirection','IsPlayerFacingSurfableFishableWater','PlayerGetElevation','TrySavingData'}, name
            queries.append(dict(phase=phase,function=name,arguments=list(values),
                purpose='native-save' if name == 'TrySavingData' else 'read-only-query'))
        depth += 1
        try:
            return original_native(name,*values,**kwargs)
        finally:
            depth -= 1

    def script(*values,**kwargs):
        assert active or depth, 'Gameplay script injected after initial placement'
        return original_script(*values,**kwargs)

    def warp(*values,**kwargs):
        assert active, 'Travel fixture used after case placement'
        return original_warp(*values,**kwargs)

    def capture(label):
        ns['picture'](label)
        row = dict(file=label+'.png',sha256=digest(output/(label+'.png')))
        captures.append(row)
        return row

    ns.update(step=step,native=native,script=script,warp=warp,walk_transition_pictures=False)

    def place(name,x,y,label):
        nonlocal active,phase
        active,phase = True,label
        original_warp(name,x,y)
        step(90)
        if not lib.read8(s['gPlayerAvatar'])&8:
            original_native('SetPlayerAvatarTransitionFlags',8)
            step(90)
        original_native('DisableWildEncounters',1)
        step(260)
        active = False
        fixtures.append(dict(case=label,map=name,tile=[x,y],surfing=True))

    def view(label,expected_count,expected_point):
        nonlocal phase
        phase = label
        step(260)
        player = ns['player_state']()
        assert [player['map'],*player['tile']] == list(expected_point)
        objects = rock_objects(lib,s,owner_id)
        assert len(objects) == expected_count, (label,objects,expected_count)
        row = dict(case=label,player=player,objects=objects,expected_count=expected_count)
        row['capture'] = capture(label)
        if expected_count:
            assert objects[0]['tile'] == ([0,7] if player['map'] == OWNER else [16,0])
            row['pixels'] = rock_pixels(lib,s,objects[0])
        views.append(row)
        return row

    try:
        place(LINK,15,2,'fresh-neighbor-approach')
        view('fresh-neighbor-approach',0 if broken_baseline else 1,(LINK,15,2))
        phase = 'enter-owner'
        ns['walk']((OWNER,0,9))
        view('enter-owner',1,(OWNER,0,9))
        phase = 'return-neighbor'
        ns['walk']((LINK,15,2))
        view('return-neighbor',1,(LINK,15,2))
        if not broken_baseline:
            phase = 'range-unload'
            ns['walk']((LINK,0,2))
            view('range-unload',0,(LINK,0,2))
            phase = 'fresh-reapproach'
            ns['walk']((LINK,15,2))
            view('fresh-reapproach',1,(LINK,15,2))
            place(OWNER,0,9,'fresh-owner-approach')
            view('fresh-owner-approach',1,(OWNER,0,9))
            phase = 'owner-to-neighbor'
            ns['walk']((LINK,15,2))
            view('owner-to-neighbor',1,(LINK,15,2))
            phase = 'save-neighbor'
            assert native('TrySavingData',0,max_frames=6000) == 1
            lib.export_save.argtypes = [ctypes.c_char_p]
            battery = output/'coast-scenery-neighbor.sav'
            assert lib.export_save(str(battery).encode())
            assert battery.stat().st_size == 131072
            for label,name,point,cell,mid in EDGES:
                place(name,*point,label)
                player = ns['player_state']()
                assert player['map'] == name and player['tile'] == point and player['surfing']
                pixels = observe_cells(ns,[(cell[0],cell[1],mid)])
                edges.append(dict(case=label,map=name,player=player,cell=cell,metatile=mid,
                    pixels=pixels,capture=capture(label)))
            for number,(name,anchor) in enumerate(BOULDERS):
                x,y = anchor
                width,height,words = ns['blocks'][name]
                cells = [(x+dx,y+dy) for dy in range(2) for dx in range(2)]
                expected = [(xx,yy,0x243) for xx,yy in cells]
                assert all(words[yy*width+xx]&1023 == 0x243 for xx,yy in cells)
                choices = []
                for cell in cells:
                    for dx,dy,key in [(1,0,32),(-1,0,16),(0,1,64),(0,-1,128)]:
                        px,py = cell[0]+dx,cell[1]+dy
                        if (0 <= px < width and 0 <= py < height and (px,py) not in cells
                                and not words[py*width+px]&0xC00
                                and ns['water_behaviors'][ns['behaviors'][name][py*width+px]]):
                            choices.append((px,py,key,cell))
                assert choices, ('No native Surf approach',name,anchor)
                # Keep all four tiles visible, and the avatar outside the footprint.
                px,py,key,target = choices[0]
                label = 'complete-reef-'+str(number+1)
                place(name,px,py,label)
                before = ns['player_state']()
                step(1,key);step(45)
                after = ns['player_state']()
                assert after['tile'] == before['tile'] and after['map'] == before['map']
                collision = native('MapGridGetCollisionAt',target[0]+7,target[1]+7)
                assert collision == 1
                # Surf's blob extends beyond its tile. Move through the real
                # water to keep every quadrant of the whole object unobscured.
                ns['walk']((name,x+4,y+3))
                step(90)
                observation_player = ns['player_state']()
                pixels = observe_cells(ns,expected)
                attachment = capture(label)
                bumps.append(dict(map=name,anchor=anchor,reef_cells=[list(cell) for cell in cells],
                    bumped_cell=list(target),direction_key=key,before=before,after=after,
                    collision=collision,observation_player=observation_player,pixels=pixels,capture=attachment))
    finally:
        lib.stop()
    return dict(kind='coast-scenery-objects-native',passed=True,rom_sha256=digest(source/'pokeemerald.gba'),
        elf_sha256=digest(source/'pokeemerald.elf'),
        native_validation_performed=True,expected_broken_baseline=broken_baseline,
        owner_map_id=list(owner_id),fixtures=fixtures,inputs=inputs,queries=queries,
        captures=captures,views=views,boulder_cases=bumps,edge_cases=edges,
        initial_party_progress_encounter_suppression_and_placement_are_fixtures=True,
        after_placement_movement_controllers_only=True,
        exact_current_oam_vram_palette_and_scanout_checked=True,
        save_file=None if battery is None else dict(file=battery.name,bytes=battery.stat().st_size,sha256=digest(battery)))


def _cold_continue(source, library, output, battery, owner_id):
    path = ROOT/'tools/hoenn/validate_cold_boot.py'
    code = path.read_text()
    anchor = "                    result = dict(bundled_save_continue_to_field=True, field_map=[lib.read8(save+4), lib.read8(save+5)])"
    assert code.count(anchor) == 1
    observer = '''
                    row = ROCK_OBJECTS(lib,symbols,OWNER_ID)
                    assert len(row)==1, ('Permanent scenery missing/duplicated on cold Continue',row)
                    obj=symbols['gObjectEvents']+36*lib.read8(symbols['gPlayerAvatar']+5)
                    result.update(player_tile=[(lib.read16(obj+16)&65535)-7,(lib.read16(obj+18)&65535)-7],
                        player_surfing=bool(lib.read8(symbols['gPlayerAvatar'])&8),
                        scenery=row[0],scenery_pixels=ROCK_PIXELS(lib,symbols,row[0]))
                    assert result['player_tile']==[15,2] and result['player_surfing']
                    assert row[0]['tile']==[16,0]
                    picture('battery-permanent-scenery')
'''
    ns = {'__file__':str(path),'__name__':'coast_scenery_cold_continue',
        'ROCK_OBJECTS':rock_objects,'ROCK_PIXELS':rock_pixels,'OWNER_ID':owner_id}
    exec(compile(code.replace(anchor,anchor+observer),str(path),'exec'),ns)
    report = ns['validate'](source,library,output,battery)
    report['captures'] = [dict(file=p.name,sha256=digest(p)) for p in sorted(output.glob('*.png'))]
    (output/'cold-boot.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def run(source, library, output, parent_source=None):
    source,library,output = map(lambda p:Path(p).resolve(),(source,library,output))
    expected_sha = digest(source/'pokeemerald.gba')
    report = _field_probe(source,library,output)
    if parent_source is not None:
        parent_source = Path(parent_source).resolve()
        baseline = _field_probe(parent_source,library,output/'parent',broken_baseline=True)
        report['parent_reproduction'] = baseline
        (output/'parent/objects-native.json').write_text(json.dumps(baseline,indent=2)+'\n')
    report['cold_continue'] = _cold_continue(source,library,output/'cold-continue',
        output/report['save_file']['file'],report['owner_map_id'])
    report['components'] = []
    if parent_source is not None:
        report['components'].append(dict(file='parent/objects-native.json',sha256=digest(output/'parent/objects-native.json')))
    report['components'].append(dict(file='cold-continue/cold-boot.json',sha256=digest(output/'cold-continue/cold-boot.json')))
    report['battery_saves'] = [report['save_file']]
    assert digest(source/'pokeemerald.gba') == expected_sha
    verify_report(report,output,expected_sha)
    (output/'objects-native.json').write_text(json.dumps(report,indent=2)+'\n')
    (output/'objects.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def _verify_obj_pixels(row, image):
    assert row['exact_current_vram_frame_compared'] is True
    assert row['expected_opaque_pixels'] >= 100
    assert row['matching_scanout_pixels'] >= row['expected_opaque_pixels']*.95
    samples = row['expected_scanout_pixels']
    assert len(samples) == row['expected_opaque_pixels']
    assert sum(bool(sample[5]) for sample in samples) == row['matching_scanout_pixels']
    assert len({tuple(sample[:2]) for sample in samples}) == len(samples)
    x,y,w,h = row['screen_rectangle']
    assert w == h == 16 and 0 <= x <= 224 and 0 <= y <= 144
    for sx,sy,r,g,b,visible in samples:
        assert x <= sx < x+16 and y <= sy < y+16
        assert all(type(v) is int and 0 <= v <= 248 and v%8 == 0 for v in (r,g,b))
        assert isinstance(visible,bool)
        if visible:
            assert all(abs(a-b) <= 7 for a,b in zip(image.getpixel((sx,sy)),(r,g,b)))


def verify_report(report, directory, romsha):
    directory = Path(directory)
    assert report['kind'] == 'coast-scenery-objects-native' and report['passed'] is True
    assert report['rom_sha256'] == romsha and len(romsha) == 64
    assert report['owner_map_id'] == [37,12]
    assert len(report['elf_sha256']) == 64
    for key in ['native_validation_performed','initial_party_progress_encounter_suppression_and_placement_are_fixtures',
                'after_placement_movement_controllers_only','exact_current_oam_vram_palette_and_scanout_checked']:
        assert report[key] is True
    images = verify_captures(report['captures'],directory)
    captures = {row['file']:row['sha256'] for row in report['captures']}
    broken = report['expected_broken_baseline']
    cases = [('fresh-neighbor-approach',LINK,[15,2],0 if broken else 1),
             ('enter-owner',OWNER,[0,9],1),('return-neighbor',LINK,[15,2],1)]
    if not broken:
        cases += [('range-unload',LINK,[0,2],0),('fresh-reapproach',LINK,[15,2],1),
                  ('fresh-owner-approach',OWNER,[0,9],1),('owner-to-neighbor',LINK,[15,2],1)]
    assert len(report['views']) == len(cases)
    for row,(case,name,tile,count) in zip(report['views'],cases):
        assert row['case'] == case and row['expected_count'] == len(row['objects']) == count
        assert row['capture']['file'] == case+'.png'
        assert captures[row['capture']['file']] == row['capture']['sha256']
        state = row['player']
        assert state['map'] == name and state['tile'] == tile
        assert state['surfing'] is True and state['elevation'] == 1
        if count:
            obj = row['objects'][0]
            assert obj['local_id'] == 4 and obj['graphics_id'] == 76 and obj['map_id'] == report['owner_map_id']
            assert obj['tile'] == ([0,7] if name == OWNER else [16,0])
            _verify_obj_pixels(row['pixels'],images[row['capture']['file']])
    assert set(images) == {row['capture']['file'] for row in report['views']+report['boulder_cases']+report['edge_cases']}
    expected_fixtures = [('fresh-neighbor-approach',LINK,[15,2])]
    if not broken:
        expected_fixtures += [('fresh-owner-approach',OWNER,[0,9])]
        expected_fixtures += [(case,name,point) for case,name,point,cell,mid in EDGES]
        expected_fixtures += [('complete-reef-'+str(i+1),name,report['boulder_cases'][i]['before']['tile']) for i,(name,anchor) in enumerate(BOULDERS)]
    assert [(row['case'],row['map'],row['tile']) for row in report['fixtures']] == expected_fixtures
    assert report['inputs'] and {16,32} <= {row['key'] for row in report['inputs']}
    for row in report['inputs']:
        assert isinstance(row['frames'],int) and row['frames'] > 0
        assert row['key'] in (0,1,2,8,16,32,64,128)
    assert report['queries']
    for row in report['queries']:
        assert row['function'].startswith(('MapGridGet','MetatileBehavior_Is')) or row['function'] in {
            'GetPlayerFacingDirection','IsPlayerFacingSurfableFishableWater','PlayerGetElevation','TrySavingData'}
        assert row['purpose'] == ('native-save' if row['function'] == 'TrySavingData' else 'read-only-query')
    if broken:
        assert not report['boulder_cases'] and not report['edge_cases'] and report['save_file'] is None
        return
    assert len(report['boulder_cases']) == len(BOULDERS)
    assert len(report['edge_cases']) == len(EDGES)
    for row,(case,name,point,cell,mid) in zip(report['edge_cases'],EDGES):
        assert row['case'] == case and row['map'] == name and row['cell'] == cell
        assert row['capture']['file'] == case+'.png'
        assert row['metatile'] == mid
        assert row['player']['map'] == name and row['player']['tile'] == point
        verify_pixels(row['pixels'],row['capture'],captures,images,cell,mid)
    for row,(name,anchor) in zip(report['boulder_cases'],BOULDERS):
        assert row['map'] == name and row['anchor'] == anchor
        assert row['collision'] == 1 and row['before']['tile'] == row['after']['tile']
        assert row['before']['map'] == row['after']['map'] == name
        assert row['direction_key'] in (16,32,64,128)
        assert row['observation_player']['map'] == name
        assert row['observation_player']['tile'] == [anchor[0]+4,anchor[1]+3]
        assert len(row['pixels']['cells']) == 4
        expected_cells = [[anchor[0]+dx,anchor[1]+dy] for dy in range(2) for dx in range(2)]
        assert row['reef_cells'] == expected_cells
        for cell,actual in zip(expected_cells,row['pixels']['cells']):
            info = dict(row['pixels'],cells=[actual])
            verify_pixels(info,row['capture'],captures,images,cell,0x243)
    battery = report['save_file']
    assert report['battery_saves'] == [battery]
    expected_components = ['cold-continue/cold-boot.json']
    if 'parent_reproduction' in report:
        expected_components.insert(0,'parent/objects-native.json')
    assert [row['file'] for row in report['components']] == expected_components
    for component in report['components']:
        path = directory/component['file']
        assert digest(path) == component['sha256']
        expected_child = report['parent_reproduction'] if component['file'].startswith('parent/') else report['cold_continue']
        assert json.loads(path.read_bytes()) == expected_child
    assert battery['bytes'] == 131072 and digest(directory/battery['file']) == battery['sha256']
    cold = report['cold_continue']
    assert cold['passed'] is True and cold['rom_sha256'] == romsha
    assert cold['controllers_only'] is cold['no_game_memory_writes'] is True
    assert cold['bundled_save_sha256'] == battery['sha256']
    assert len(cold['runs']) == 2 and [row['battery'] for row in cold['runs']] == [False,True]
    continued = cold['runs'][1]
    assert continued['bundled_save_continue_to_field'] is True
    assert continued['player_tile'] == [15,2] and continued['player_surfing'] is True
    assert continued['scenery']['tile'] == [16,0]
    assert continued['scenery']['local_id'] == 4 and continued['scenery']['map_id'] == report['owner_map_id']
    cold_images = verify_captures(cold['captures'],directory/'cold-continue')
    assert set(cold_images) == {'fresh-title.png','fresh-main-menu.png','fresh-new-game.png',
        'battery-title.png','battery-main-menu.png','battery-continued-to-field.png','battery-permanent-scenery.png'}
    _verify_obj_pixels(continued['scenery_pixels'],cold_images['battery-permanent-scenery.png'])
    if 'parent_reproduction' in report:
        parent = report['parent_reproduction']
        assert parent['expected_broken_baseline'] is True and parent['rom_sha256'] != romsha
        verify_report(parent,directory/'parent',parent['rom_sha256'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--library',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--parent-source',type=Path)
    args = parser.parse_args()
    run(args.source,args.library,args.output,args.parent_source)
