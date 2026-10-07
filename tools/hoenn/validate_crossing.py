#!/usr/bin/env python3
"""Real mGBA seam checks for the experimental multiregion crossing, not a campaign test."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import tempfile
import zlib

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--library', type=Path, required=True)
parser.add_argument('--worldsea', action='store_true', help='Also exercise every edge of the experimental eastern ocean grid')
parser.add_argument('--westsea', action='store_true', help='Use the revised Cinnabar/Route114 crossing and validate the western coast')
parser.add_argument('--region-state', action='store_true', help='Exercise separate badge/champion/story banks and native flash save/reload')
parser.add_argument('--east-coast', action='store_true', help='Exercise the three eastern Hoenn exits and Fuchsia sea connection')
parser.add_argument('--gym-scaling', action='store_true', help='Generate actual gym parties at every regional badge count')
parser.add_argument('--free-access', action='store_true', help='Exercise terrestrial obstacle removal and free-order gym doors')
parser.add_argument('--road-access', action='store_true', help='Exercise bike quest gates, former Acro terrain and relocated Aqua roadblocks')
parser.add_argument('--team-stories', action='store_true', help='Validate regional incursions, casino stairs and actual Giovanni tag-battle startup')
parser.add_argument('--campaign-gates', action='store_true', help='Exercise regional story checkpoints and gym-door guide objects')
parser.add_argument('--output', type=Path, default=ROOT / 'mods/hoenn/integration-validation')
args = parser.parse_args(); source = args.source.resolve(); args.output.mkdir(parents=True, exist_ok=True)
raw = subprocess.check_output([str(ROOT / '.local/arm-binutils/usr/bin/arm-none-eabi-nm'), '-n', str(source / 'pokeemerald.elf')], text=True)
s = {name: int(address, 16) for address, kind, name in re.findall(r'^(\w+) (\w) (\S+)$', raw, re.M)}
groups = json.loads((source / 'data/maps/map_groups.json').read_text())
layouts = {l['id']: l for l in json.loads((source / 'data/layouts/layouts.json').read_text())['layouts']}
lib = ctypes.CDLL(str(args.library.resolve())); lib.start.argtypes = [ctypes.c_char_p]
lib.image.restype = ctypes.c_void_p; lib.read32.restype = ctypes.c_uint32
assert lib.start(str(source / 'pokeemerald.gba').encode())
results = []
call4 = None
abi = None
if args.gym_scaling or args.team_stories:
    toolchain = ROOT / '.local/arm-gcc/usr/bin/arm-none-eabi-gcc'
    with tempfile.TemporaryDirectory(prefix='gym-fixture-', dir='/tmp') as directory:
        temp = Path(directory)
        subprocess.run([str(ROOT / '.local/arm-binutils/usr/bin/arm-none-eabi-as'), '-mthumb', '-march=armv4t', str(ROOT / 'tools/hoenn/fixture_call4.s'), '-o', str(temp / 'call.o')], check=True)
        subprocess.run([str(ROOT / '.local/arm-binutils/usr/bin/arm-none-eabi-objcopy'), '-O', 'binary', '-j', '.text', str(temp / 'call.o'), str(temp / 'call.bin')], check=True)
        call4 = (temp / 'call.bin').read_bytes()
        subprocess.run([str(toolchain), '-S', '-iquote', str(source / 'include'), '-DMODERN=1', '-DPOKEEMERALD', '-mthumb', '-march=armv4t', '-mabi=apcs-gnu', str(ROOT / 'tools/hoenn/fixture_gym_abi.c'), '-o', str(temp / 'abi.s')], check=True)
        abi = [int(n) for n in re.findall(r'\.word\s+(\d+)', (temp / 'abi.s').read_text())]

def step(n, keys=0): lib.frames(n, keys)
def save(): return lib.read32(s['gSaveBlock1Ptr'])
def location(): return lib.read8(save() + 4), lib.read8(save() + 5)
def map_id(name): return next((g, groups[label].index(name)) for g, label in enumerate(groups['group_order']) if name in groups[label])
def position():
    obj = s['gObjectEvents'] + lib.read8(s['gPlayerAvatar'] + 5) * 36
    return lib.read16(obj + 16) - 7, lib.read16(obj + 18) - 7

def picture(name):
    pixels = ctypes.string_at(lib.image(), 240 * 160 * 4)
    rgb = b''.join(b'\0' + bytes(v for i, v in enumerate(pixels[y*960:(y+1)*960]) if i % 4 != 3) for y in range(160))
    def chunk(kind, data): return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    (args.output / (name + '.png')).write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 240, 160, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(rgb)) + chunk(b'IEND', b''))

def script(code, frames=900):
    for i, byte in enumerate(code): lib.raw8(0x09f00000 + i, byte)
    context = s['sGlobalScriptContext']
    for i in range(116): lib.write8(context + i, 0)
    lib.write8(context + 1, 1); lib.write32(context + 8, 0x09f00000)
    lib.write32(context + 92, s['gScriptCmdTable']); lib.write32(context + 96, s['gScriptCmdTableEnd'])
    lib.write8(s['sGlobalScriptContextStatus'], 0); lib.write8(s['sLockFieldControls'], 1)
    step(frames)

def warp(name, x, y):
    g, n = map_id(name)
    script(b'\x39' + bytes([g, n, 255]) + struct.pack('<HH', x, y) + b'\x27\x6b\x02')
    assert location() == (g, n), (name, location())

def raw32(addr, value):
    for i, b in enumerate(struct.pack('<I', value)): lib.raw8(addr + i, b)

def native(name, *values, max_frames=200):
    code = bytearray(call4) if len(values) == 4 else bytearray.fromhex('00b505480549064a064b00f003f80649086000bd1847c0461111111122222222333333334444444455555555')
    scratch = s['gStringVar4'] + 960
    sentinels = [0x11111111, 0x22222222, 0x33333333, 0x44444444, 0x55555555]
    params = [*(list(values) + [0]*3)[:3], s[name] | 1, scratch]
    if len(values) == 4:
        sentinels += [0x66666666]; params = [*values, s[name] | 1, scratch]
    for sentinel, value in zip(sentinels, params):
        struct.pack_into('<I', code, code.index(struct.pack('<I', sentinel)), value)
    for i, b in enumerate(code): lib.raw8(0x09f00200 + i, b)
    hook = s['gSpecials']; original = lib.read32(hook); raw32(hook, 0x09f00201)
    lib.write32(scratch, 0xdeadc0de)
    try:
        script(b'\x25\0\0\x6b\x02', 3)
        for _ in range(max_frames):
            if lib.read32(scratch) != 0xdeadc0de: break
            step(1)
        assert lib.read32(scratch) != 0xdeadc0de, ('Native fixture failed', name)
        return lib.read32(scratch)
    finally: raw32(hook, original)

def cross(name, key):
    before = location()
    for _ in range(240):
        step(4, key)
        if location() == map_id(name):
            step(20)
            assert lib.read8(s['gPlayerAvatar']) & 8, ('Lost Surf', name, position())
            target_data = json.loads((source / f'data/maps/{name}/map.json').read_text())
            expected_frlg = layouts[target_data['layout']]['layout_version'] == 'frlg'
            assert lib.read8(s['isFrlg']) == expected_frlg, ('Wrong region format', name)
            results.append(dict(check='physical_surf_seam', source=before, target=name, passed=True))
            picture(name + '-arrival')
            print('Physical Surf seam passed:', name, flush=True)
            return
    picture('failed-' + name)
    raise AssertionError(('No seam transition', name, location(), position()))

step(900)
save2 = lib.read32(s['gSaveBlock2Ptr']); lib.write8(save2,255);lib.write8(save2+8,255)
lib.write32(s['gMain'], 0); lib.write8(s['gMain'] + 0x438, 0)
lib.write32(s['gMain'] + 4, s['CB2_NewGame'] | 1); step(300)
warp('Route127', 79, 42)
assert native('ScriptGiveMon', 7, 30, 0) == 0
native('ScriptSetMonMoveSlot', 0, 57, 0)
# The native candidate's badge gates are unchanged at this stage. This test
# isolates the camera/map seam, NOT early-HM unlocking or the custom story.
native('SetPlayerAvatarTransitionFlags', 8); step(30)
assert lib.read8(s['gPlayerAvatar']) & 8
if not args.westsea and not args.campaign_gates:
    cross('JourneyHoennCrossing', 16)
    warp('JourneyHoennCrossing', 47, 12)
    cross('Route21_South_Frlg', 16)
    cross('JourneyHoennCrossing', 32)
    warp('JourneyHoennCrossing', 0, 12)
    cross('Route127', 32)
warp('Route21_South_Frlg', 1, 22)
picture('Route21-direct-warp-control')
if args.region_state:
    regional = json.loads((source / '.journey-region-state').read_text())
    badges = [lib.read16(s['gBadgeFlags'] + i * 2) for i in range(8)]
    champion = 0xB5A  # compiled probe: SYSTEM_FLAGS + 4 on the pinned base
    event = regional['frlg_flags']['FLAG_HIDE_BULBASAUR_BALL']
    warp('VermilionCity_Frlg', 33, 39)
    trainer_before = native('FlagGet', event['original'])
    for badge in badges: native('FlagSet', badge)
    native('FlagSet', champion)
    native('FlagSet', event['allocated'])
    assert all(native('FlagGet', b) for b in badges)
    assert native('FlagGet', champion)
    assert native('FlagGet', event['original']) == trainer_before
    warp('Route131', 50, 35)
    assert all(not native('FlagGet', b) for b in badges), 'Kanto badge leaked into Hoenn'
    assert not native('FlagGet', champion), 'Kanto championship leaked into Hoenn'
    native('FlagSet', badges[0]); native('FlagSet', champion)
    warp('VermilionCity_Frlg', 33, 39)
    native('FlagClear', badges[0]); native('FlagToggle', badges[1])
    assert not native('FlagGet', badges[0]) and not native('FlagGet', badges[1])
    warp('Route131', 50, 35)
    assert native('FlagGet', badges[0]) and not native('FlagGet', badges[1])
    assert native('FlagGet', champion)
    # Save/reload only the emulator's own flash; no user save is loaded.
    assert native('TrySavingData', 0, max_frames=6000) == 1, 'Native flash save failed'
    native('FlagClear', badges[0]); native('FlagClear', champion)
    native('FlagClear', event['allocated'])
    assert native('LoadGameSave', 0) == 1, 'Native flash reload failed'
    assert native('FlagGet', badges[0]) and native('FlagGet', champion)
    assert native('FlagGet', event['allocated'])
    warp('VermilionCity_Frlg', 33, 39)
    assert not native('FlagGet', badges[0]) and not native('FlagGet', badges[1])
    assert all(native('FlagGet', b) for b in badges[2:])
    assert native('FlagGet', champion)
    results.append(dict(check='regional_flags_and_native_save_roundtrip', passed=True,
        kanto_badges_independent=True, champion_independent=True, trainer_flag_unchanged=True))
    print('Regional badges/champion/story bank and native flash roundtrip passed', flush=True)
if args.campaign_gates:
    gating = json.loads((source / '.journey-campaign-gates').read_text())
    constants = (source / 'include/constants/flags.h').read_text()
    event_names = ['FLAG_HIDE_CELADON_ROCKETS', 'FLAG_HIDE_SAFFRON_ROCKETS',
        'FLAG_DEFEATED_EVIL_TEAM_MT_CHIMNEY', 'FLAG_GROUDON_AWAKENED_MAGMA_HIDEOUT',
        'FLAG_DEFEATED_MAGMA_SPACE_CENTER', 'FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN']
    event_flags = [int(re.search(r'^#define\s+' + name + r'\s+(0x[0-9A-Fa-f]+)', constants, re.M)[1], 16)
                   for name in event_names]
    hoenn_badges = [lib.read16(s['gBadgeFlags'] + i*2) for i in range(8)]
    kanto_badges = list(range(0x1AB0, 0x1AB8))
    def write_flag(flag, enabled):
        address = save()+4720+flag//8
        value = lib.read8(address); mask = 1 << (flag & 7)
        lib.write8(address, value | mask if enabled else value & ~mask)
    def write_badges(flags, indices):
        for index, flag in enumerate(flags): write_flag(flag, index in indices)
    stories = json.loads((source / '.journey-team-stories').read_text()) if (source / '.journey-team-stories').exists() else None
    mission_trainers = {t['key']: t['id'] for t in stories['trainers']} if stories else {}
    if stories:
        for trainer in stories['trainers']: write_flag(0x500+trainer['id'],True)
    cases = 0
    for kanto, thresholds, events in [(True, [2,6] if stories else [2,3], [0,1]), (False, [2,5,7,7] if stories else [2,5,6,6], [2,3,4,5])]:
        for count in range(9):
            write_badges(kanto_badges if kanto else hoenn_badges, range(count))
            write_badges(hoenn_badges if kanto else kanto_badges, range(8-count))
            for completed in range(1 << len(events)):
                for flag in event_flags: write_flag(flag, False)
                if stories and not kanto: write_flag(event_flags[1],True)
                for i,event in enumerate(events): write_flag(event_flags[event], bool(completed & (1 << i)))
                expected = next((event+1 for i,(event,threshold) in enumerate(zip(events,thresholds))
                                 if count >= threshold and not completed & (1 << i)), 0)
                assert native('JourneyPendingCampaignEvent',int(kanto)) == expected, (kanto,count,completed,expected)
                cases += 1
    # Prepare invasion at the current checkpoint, preserve in-progress/completed
    # scenes and never grant the next badge to satisfy the story dependency.
    write_badges(hoenn_badges, range(7 if stories else 6)); lib.write8(s['isFrlg'],0)
    write_flag(event_flags[3],True); write_flag(event_flags[4],False)
    native('VarSet',0x409F,0); native('JourneyStartSpaceCenterInvasion')
    assert native('VarGet',0x409F) == 1
    assert not native('FlagGet',hoenn_badges[7 if stories else 6])
    native('VarSet',0x409F,2); native('JourneyStartSpaceCenterInvasion')
    assert native('VarGet',0x409F) == 2
    write_flag(hoenn_badges[6],False)
    assert native('IsFieldMoveUnlocked_Dive') == 0
    write_flag(event_flags[4],True); native('VarSet',0x409F,3)
    native('JourneyStartSpaceCenterInvasion'); assert native('VarGet',0x409F) == 3
    assert native('IsFieldMoveUnlocked_Dive') == 1
    guides = 0
    for city in gating['cities']:
        own = kanto_badges if city['kanto'] else hoenn_badges
        other = hoenn_badges if city['kanto'] else kanto_badges
        write_badges(own, [i for i in range(8) if i != city['badge']][:2])
        write_badges(other, range(8))
        for flag in event_flags: write_flag(flag,False)
        door = city['door']
        warp(city['map'],door['x'],door['y']+1)
        native('SetPlayerAvatarTransitionFlags',1); step(30)
        before_position = position()
        assert native('JourneyCurrentGymGate') == (1 if city['kanto'] else 3)
        objects = [s['gObjectEvents']+36*i for i in range(16)]
        def guide_objects():
            return [p for p in objects if lib.read8(p) & 1
                    and lib.read8(p+8) == city['guide_local_id']
                    and (lib.read8(p+10),lib.read8(p+9)) == map_id(city['map'])]
        found = guide_objects()
        assert len(found) == 1, ('Guide not spawned',city['map'],city['guide_local_id'])
        assert (lib.read16(found[0]+16)-7,lib.read16(found[0]+18)-7) == (door['x'],door['y'])
        lib.write16(s['gSpecialVar_Result'],0)
        step(80,64)
        print('Guide movement fixture:',city['map'],before_position,position(),
              'avatar',lib.read8(s['gPlayerAvatar']),flush=True)
        assert location() == map_id(city['map']), ('Guide did not block entrance',city['map'])
        assert position() == before_position, ('Player walked through the guide',city['map'],position())
        # Some native doors are still closed by their original story. The
        # trainer must also explain the checkpoint when spoken to with A.
        step(1,1); step(80)
        assert lib.read16(s['gSpecialVar_Result']) == (1 if city['kanto'] else 3), ('Guide dialogue did not start',city['map'])
        if city['map'] in ['PewterCity_Frlg','RustboroCity']:
            step(1,1); step(180); picture(city['map']+'-checkpoint-dialogue')
            step(1,1); step(180); picture(city['map']+'-checkpoint-location')
        for flag in event_flags: write_flag(flag,True)
        # Finish the actual message task before injecting another fixture
        # script. Replacing a context does not cancel asynchronous message UI.
        for _ in range(12):
            step(16,1); step(16)
        # Completing the scene naturally hides the guide on returning to town.
        warp(city['map'],door['x'],door['y']+1)
        assert native('JourneyCurrentGymGate') == 0
        assert not guide_objects(), ('Guide stayed after completion',city['map'])
        if city['map'] in ['PewterCity_Frlg','RustboroCity']:
            gym = city['map'].replace('_Frlg','')+'_Gym'+('_Frlg' if city['kanto'] else '')
            step(160,64); step(90)
            assert location() == map_id(gym), ('Completed checkpoint still blocks entry',city['map'],location())
            warp(city['map'],door['x'],door['y']+1)
        # Already defeated gyms never acquire a story blockade on revisits.
        for flag in event_flags: write_flag(flag,False)
        write_flag(own[city['badge']],True)
        assert native('JourneyCurrentGymGate') == 0
        guides += 1
        print('Native gym-door guide passed:',city['map'],flush=True)
    results.append(dict(check='regional_campaign_checkpoints_and_guides',passed=True,
        state_combinations=cases,city_guides=guides,blocked_door_movement=True,
        completion_hides_guides=True,won_gyms_exempt=True,
        all_guide_dialogues_triggered=True,
        invasion_before_gym=8 if stories else 7,invasion_does_not_restart=True,
        dive_after_space_center_without_seventh_badge=True,
        representative_completed_door_warps=2,
        full_story_or_free_order_access_validated=False))
if args.free_access:
    access=json.loads((source/'.journey-free-access').read_text())
    def rawflag(flag,enabled):
        p=save()+4720+flag//8;mask=1<<(flag&7);v=lib.read8(p)
        lib.write8(p,v|mask if enabled else v&~mask)
    hb=[lib.read16(s['gBadgeFlags']+i*2)for i in range(8)];kb=list(range(0x1AB0,0x1AB8))
    for b in hb+kb:rawflag(b,False)
    rawflag(0xB5A,False);rawflag(0x1AB8,False)
    assert native('FlagGet',0x1ABB)==1
    for region in [0,1]:
        lib.write8(s['isFrlg'],region)
        assert native('IsFieldMoveUnlocked_Surf')==1
        assert native('IsFieldMoveUnlocked_Waterfall')==1
        assert native('IsFieldMoveUnlocked_Dive')==0
    gating=json.loads((source/'.journey-campaign-gates').read_text())
    # Retain the tutorial, and exercise Norman's formerly fixed-badge states.
    for state in [2,3,4,5]:
        native('VarSet',0x4085,state)
        warp('PetalburgCity_Gym',4,106)
        assert native('VarGet',0x4085)==6, ('Norman rank gate',state)
    doors=0
    for city in gating['cities']:
        native('VarSet',0x4085,6)
        door=city['door'];warp(city['map'],door['x'],door['y']+1)
        native('SetPlayerAvatarTransitionFlags',1);step(30)
        assert native('JourneyCurrentGymGate')==0
        gym=next(json.loads(p.read_text())['name'] for p in (source/'data/maps').glob('*/map.json')
                 if json.loads(p.read_text())['id']==door['dest_map'])
        step(100,64);step(60)
        assert location()==map_id(gym), ('Free gym door',city['map'],location(),position())
        print('Free gym door passed:',city['map'],flush=True)
        picture(city['map']+'-free-gym-entry');doors+=1
    samples=[]
    for script_name in ['EventScript_CutTree','EventScript_RockSmash','EventScript_StrengthBoulder']:
        # Verify representative objects absent in each engine format.
        for frlg in [False,True]:
            obstacle=next(o for o in access['obstacles']if o['script']==script_name and o['map'].endswith('_Frlg')==frlg)
            warp(obstacle['map'],obstacle['x'],obstacle['y'])
            native('SetPlayerAvatarTransitionFlags',1);step(30)
            assert native('MapGridGetCollisionAt',obstacle['x']+7,obstacle['y']+7)==0,obstacle
            active=[s['gObjectEvents']+36*i for i in range(16)]
            assert not any(lib.read8(p)&1 and lib.read8(p+8)==obstacle['local_id']
                           and (lib.read8(p+10),lib.read8(p+9))==map_id(obstacle['map'])for p in active),obstacle
            samples.append(obstacle);picture(obstacle['map']+'-cleared-'+script_name)
    # Use Surf through the real A-button prompt with no badges, not just the
    # forced-avatar helper used to isolate the ocean seam tests.
    beach=json.loads((source/'data/maps/Route109/map.json').read_text())
    bl=layouts[beach['layout']];raw=(source/bl['blockdata_filepath']).read_bytes()
    tiles=struct.unpack('<'+'H'*(len(raw)//2),raw);w,h=bl['width'],bl['height']
    occupied={(o['x'],o['y'])for o in beach['object_events']}
    choices=[]
    for y in range(2,h-2):
        for x in range(2,w-2):
            v=tiles[y*w+x]
            if v&0xC00 or v>>12!=3 or any(abs(x-a)+abs(y-b)<4 for a,b in occupied):continue
            for dx,dy,key in [(0,1,128),(1,0,16),(-1,0,32),(0,-1,64)]:
                water=tiles[(y+dy)*w+x+dx]
                if not water&0xC00 and water>>12==1:choices.append((x,y,key))
    assert choices,'No native beach fixture'
    x,y,key=choices[0];warp('Route109',x,y)
    native('SetPlayerAvatarTransitionFlags',1);step(30);step(16,key);step(16)
    assert not lib.read8(s['gPlayerAvatar'])&8
    step(1,1);step(100);picture('Surf-without-badges-prompt')
    for _ in range(6):step(1,1);step(100)
    assert lib.read8(s['gPlayerAvatar'])&8,('Surf prompt did not mount',x,y,position())
    picture('Surf-without-badges-active')
    barriers=0
    for name,points in [('VictoryRoad_1F_Frlg',[(12,14),(12,15)]),
        ('VictoryRoad_2F_Frlg',[(13,10),(13,11),(33,16),(33,17)]),
        ('VictoryRoad_3F_Frlg',[(12,12),(12,13)])]:
        warp(name,points[0][0],points[0][1])
        for x,y in points:
            assert native('MapGridGetCollisionAt',x+7,y+7)==0,(name,x,y)
            barriers+=1
        picture(name+'-open-boulder-barriers')
    # Exercise Blue's actual reward script without faking a Rocket victory.
    constants=(source/'include/constants/flags.h').read_text()
    def flagid(name):return int(re.search(r'^#define\s+'+name+r'\s+(0x[0-9A-Fa-f]+)',constants,re.M)[1],16)
    rocket=[flagid(n)for n in ['FLAG_HIDE_MISC_KANTO_ROCKETS','FLAG_HIDE_SAFFRON_ROCKETS','FLAG_HIDE_CELADON_ROCKETS']]
    for f in rocket:rawflag(f,False)
    for f in kb:rawflag(f,False)
    # VAR_MAP_SCENE_ROUTE22 is generated from the pinned native header.
    vc=(source/'include/constants/vars.h').read_text()
    route22=int(re.search(r'^#define\s+VAR_MAP_SCENE_ROUTE22\s+(0x[0-9A-Fa-f]+)',vc,re.M)[1],16)
    native('VarSet',route22,0);warp('ViridianCity_Gym_Frlg',2,3)
    script(b'\x05'+struct.pack('<I',s['ViridianCity_Gym_EventScript_DefeatedGiovanni']),30)
    for _ in range(30):step(16,1);step(16)
    assert all(not native('FlagGet',f)for f in rocket),'Blue cleared Rocket story'
    assert native('FlagGet',kb[7])==1
    assert sum(native('FlagGet',f)for f in kb)==1
    assert native('VarGet',route22)==0,'Blue triggered final rival before all gyms'
    for f in kb:rawflag(f,True)
    warp('ViridianCity_Frlg',34,14)
    assert native('VarGet',route22)==3
    native('VarSet',route22,4);native('JourneyUpdateGymGate')
    assert native('VarGet',route22)==4
    for f in kb:rawflag(f,False)
    results.append(dict(check='blue_regular_gym_reward',passed=True,rocket_flags_unchanged=True,
        regional_badge_only=True,route22_after_all_eight=True,completed_final_rival_not_restarted=True,
        battle_victory_simulated=True))
    results.append(dict(check='free_gym_doors_and_land_hms',passed=True,physical_gym_entries=doors,
        norman_old_badge_states=4,opened_boulder_barrier_tiles=barriers,obstacle_samples=samples,all_obstacles_catalogued=len(access['obstacles']),
        surf_waterfall_without_badges=True,real_surf_prompt_without_badges=True,dive_rule_preserved=True,full_campaign_validated=False))
    print('Free gym entries and terrestrial HM samples passed',flush=True)
if args.road_access:
    road=json.loads((source/'.journey-road-access').read_text())
    bike=json.loads((source/'.journey-mach-bike').read_text())
    yellow=json.loads((source/'.journey-yellow-stairs').read_text()) if (source/'.journey-yellow-stairs').exists() else None
    overrides={(c['layout'],c['x'],c['y']):c for c in yellow['replacements']}if yellow else {}
    constants=(source/'include/constants/flags.h').read_text()
    def roadflag(name,enabled):
        f=int(re.search(r'^#define\s+'+name+r'\s+(0x[0-9A-Fa-f]+)',constants,re.M)[1],16)
        address=save()+4720+f//8;mask=1<<(f&7);v=lib.read8(address)
        lib.write8(address,v|mask if enabled else v&~mask)
        return f
    flags=[roadflag('FLAG_HIDE_ROUTE_110_TEAM_AQUA',False),roadflag('FLAG_HIDE_ROUTE_119_TEAM_AQUA',False)]
    for name,x,y,key,axis,threshold in [('Route110',9,81,128,1,84),('Route119',11,33,16,0,13)]:
        warp(name,x,y);native('SetPlayerAvatarTransitionFlags',1);step(30)
        step(72 if name=='Route110' else 55,key);step(30)
        assert position()[axis]>threshold, ('Still blocked by Aqua',name,position())
        assert all(not native('FlagGet',f)for f in flags), 'Walking completed an Aqua mission'
        picture(name+'-Aqua-passage-open')
    # Audit the engine's behavior/collision at every converted tile after OnLoad.
    by_layout={}
    for path in (source/'data/maps').glob('*/map.json'):
        m=json.loads(path.read_text());by_layout.setdefault(m['layout'],m['name'])
    checked=0
    for layout in sorted({v['layout']for v in bike['replacements']}):
        cells=[v for v in bike['replacements']if v['layout']==layout]
        warp(by_layout[layout],cells[0]['x'],cells[0]['y'])
        for cell in cells:
            x,y=cell['x']+7,cell['y']+7
            assert native('MapGridGetCollisionAt',x,y)==0,cell
            override=overrides.get((cell['layout'],cell['x'],cell['y']))
            if override:
                assert native('MapGridGetMetatileIdAt',x,y)==override['after']&1023,override
                assert native('MapGridGetMetatileBehaviorAt',x,y)==0,override
                assert native('MapGridGetMetatileLayerTypeAt',x,y)==(0 if override['surface']=='landing' else 1),override
                checked+=1
                continue
            landing=cell.get('surface')=='landing'
            assert native('MapGridGetMetatileBehaviorAt',x,y)==(12 if landing else 0),cell
            if cell['layout']=='LAYOUT_JAGGED_PASS':
                assert native('MapGridGetMetatileIdAt',x,y)==(0x271 if landing else 0x2AF), ('Wrong stair/landing sprite',cell)
            if cell['kind']=='stairs' and not landing:
                assert native('MapGridGetMetatileLayerTypeAt',x,y)==1, ('Stair overlays player',cell)
            checked+=1
    # Real movement across formerly restricted rails, a filled side-hop gap,
    # and both high/low stair elevations. No Acro avatar is used.
    walks=[('Route119',8,5,16,0,9),('Route119',9,10,16,0,10),
           ('SafariZone_South',22,3,16,0,23),('SafariZone_North',22,24,64,1,23),
           ('JaggedPass',18,10,64,1,9)]
    for name,x,y,key,axis,threshold in walks:
        warp(name,x,y);native('SetPlayerAvatarTransitionFlags',1);step(30)
        step(40,key);step(30)
        assert (position()[axis]>threshold if key==16 else position()[axis]<threshold), ('Acro replacement still blocked',name,position())
        assert lib.read8(s['gPlayerAvatar'])&1,('Not walking',name)
        picture(name+'-walkable-Acro-replacement-'+str(y))
    warp('JaggedPass',17,10);native('SetPlayerAvatarTransitionFlags',1);step(30)
    picture('JaggedPass-yellow-stair-and-clear-landing')
    if yellow:
        # Exercise every former cliff-jump passage in both directions with an
        # on-foot avatar. Riding any bicycle would invalidate this check.
        native('DisableWildEncounters',1)
        passage_cases=0
        for name,x,bottom,top in [('JaggedPass',18,10,8),('JaggedPass',21,12,10),
                                ('JaggedPass',22,19,16),('JaggedPass',21,31,27),
                                ('JaggedPass',9,33,30),('SafariZone_North',22,24,20)]:
            for y,key,target in [(bottom,64,top),(top,128,bottom)]:
                warp(name,x,y);native('SetPlayerAvatarTransitionFlags',1);step(30)
                for _ in range(12):
                    step(16,key)
                    if position()[1]<=target if key==64 else position()[1]>=target:break
                assert position()[1]<=target if key==64 else position()[1]>=target,(name,x,y,key,position())
                assert lib.read8(s['gPlayerAvatar'])&1,('Used bicycle on yellow stairs',name)
                if name=='SafariZone_North':
                    for color in range(1,16):
                        assert lib.read16(s['gPlttBufferUnfaded']+12*32+color*2)==lib.read16(s['gTilesetPalettes_Lavaridge']+8*32+color*2),('Yellow stair palette was not loaded',color)
                passage_cases+=1
            picture(name+'-yellow-stairs-'+str(x)+'-'+str(bottom))
        native('DisableWildEncounters',0)
        results.append(dict(check='all_acro_cliff_passages_yellow',passed=True,
            passages=6,on_foot_traversals=passage_cases,yellow_stair_cells=11,clear_landings=6,
            foreground_pixels_identical=yellow['foreground_pixels_identical'],
            foreground_palette_identical=yellow['foreground_palette_identical'],
            native_loaded_palette_matches_yellow_reference=True,
            original_lilycove_pixels_preserved=yellow['original_lilycove_pixels_preserved'],
            encounters_disabled_only_for_geometry_fixture=True,
            full_campaign_validated=False))
    items=(source/'include/constants/items.h').read_text()
    def itemid(name):return int(re.search(r'^\s*'+name+r'\s*=\s*(\d+)',items,re.M)[1])
    mach=itemid('ITEM_MACH_BIKE');acro=itemid('ITEM_ACRO_BIKE');voucher=itemid('ITEM_BIKE_VOUCHER')
    native('RemoveBagItem',mach,1)
    gates=[('Route16_NorthEntrance_1F_Frlg',7,12,32),('Route18_EastEntrance_1F_Frlg',7,6,32),
           ('Route110_SeasideCyclingRoadNorthEntrance',6,4,16),('Route110_SeasideCyclingRoadSouthEntrance',6,4,16)]
    gate_cases=0
    for owned in [False,True]:
        if owned:assert native('AddBagItem',mach,1)
        for name,x,y,key in gates:
            warp(name,x,y);native('SetPlayerAvatarTransitionFlags',1);step(30)
            step(40,key)
            for _ in range(80):
                step(1,1);step(30)
                if not lib.read8(s['sLockFieldControls']):break
            assert not lib.read8(s['sLockFieldControls']),('Bicycle guard did not release controls',name,owned)
            step(30)
            after=position()[0]
            assert (after<6 if owned else after>=6) if key==32 else (after>7 if owned else after<=7), (name,owned,position())
            picture(name+('-bike-mission-complete'if owned else '-bike-mission-pending'))
            gate_cases+=1
    native('RemoveBagItem',mach,1)
    # Execute both native reward branches; dialogue/choice preceding the reward
    # is not a full end-to-end quest test.
    rewards=[]
    for name,label in [('MauvilleCity_BikeShop','MauvilleCity_BikeShop_EventScript_GetMachBike'),
                       ('CeruleanCity_BikeShop_Frlg','CeruleanCity_BikeShop_EventScript_ExchangeBikeVoucher')]:
        if name.endswith('_Frlg'):assert native('AddBagItem',voucher,1)
        warp(name,3,3)
        lib.write16(save()+0x496,mach)
        script(b'\x05'+struct.pack('<I',s[label]),30)
        for _ in range(30):step(16,1);step(16)
        assert native('CheckBagHasItem',mach,1)
        assert not native('CheckBagHasItem',acro,1)
        assert lib.read16(save()+0x496)==mach,'Shop changed the registered bike'
        if name.endswith('_Frlg'):assert not native('CheckBagHasItem',voucher,1)
        rewards.append(name);picture(name+'-Mach-Bike-reward')
        native('RemoveBagItem',mach,1)
    results.append(dict(check='bike_quests_and_acro_replacements',passed=True,
        converted_tiles=checked,physical_replacement_walks=len(walks),bike_gate_cases=gate_cases,
        cycling_locked_without_bike=True,cycling_open_after_bike=True,reward_scripts=rewards,
        full_bicycle_quests_validated=False,only_mach_awarded=True,registered_bike_preserved=True,
        stairs_draw_below_player=True,aqua_missions_unchanged=True,
        yellow_stair_matches_native_lateral=True,upper_landings_have_no_stair=True,
        physical_aqua_passages=2,full_campaign_validated=False))
    print('Bicycle mission gates, Acro replacements and Aqua road passages passed',flush=True)
if args.team_stories:
    stories = json.loads((source / '.journey-team-stories').read_text())
    ids = {t['key']:t['id'] for t in stories['trainers']}
    def team_flag(flag, enabled):
        address=save()+4720+flag//8; value=lib.read8(address);mask=1<<(flag&7)
        lib.write8(address,value|mask if enabled else value&~mask)
    def bank(flags,count):
        for i,flag in enumerate(flags):team_flag(flag,i<count)
    hb=[lib.read16(s['gBadgeFlags']+i*2)for i in range(8)];kb=list(range(0x1AB0,0x1AB8))
    constants=(source/'include/constants/flags.h').read_text()
    def flag_id(name):return int(re.search(r'^#define\s+'+name+r'\s+(0x[0-9A-Fa-f]+)',constants,re.M)[1],16)
    for name in ['FLAG_HIDE_CELADON_ROCKETS','FLAG_HIDE_SAFFRON_ROCKETS','FLAG_DEFEATED_EVIL_TEAM_MT_CHIMNEY',
                 'FLAG_GROUDON_AWAKENED_MAGMA_HIDEOUT','FLAG_DEFEATED_MAGMA_SPACE_CENTER','FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN']:
        team_flag(flag_id(name),True)
    bank(hb,4);bank(kb,4)
    for t in stories['trainers']:team_flag(0x500+t['id'],True)
    cases=0
    for mission in stories['missions']:
        for name in mission['trainers']:
            team_flag(0x500+ids[name],False)
            assert native('JourneyPendingCampaignEvent',int(mission['kanto']))==mission['event'],(mission,name)
            assert native('JourneyPendingCampaignEvent',int(not mission['kanto']))==0
            assert native('JourneyRegionalMissionsComplete',int(mission['kanto']))==0
            team_flag(0x500+ids[name],True);cases+=1
        assert native('JourneyPendingCampaignEvent',int(mission['kanto']))==0
    # Silph and the alliance require their exact regional rank and completed missions.
    bank(kb,5);assert native('JourneyCanChallengeSilph')==0
    bank(kb,6);assert native('JourneyCanChallengeSilph')==1
    bank(hb,6);assert native('JourneyCanStartArchieAlliance')==0
    bank(hb,7);assert native('JourneyCanStartArchieAlliance')==1
    team_flag(flag_id('FLAG_HIDE_SAFFRON_ROCKETS'),False)
    assert native('JourneyCanStartArchieAlliance')==0
    assert native('JourneyPendingCampaignEvent',0)==13
    team_flag(flag_id('FLAG_HIDE_SAFFRON_ROCKETS'),True)
    # Walk on the actual stairs instead of invoking destination warps directly.
    for origin,x,y,key,target in [
        ('MauvilleCity_GameCorner',19,6,128,'JourneyRocketBaseB1F'),
        ('JourneyRocketBaseB1F',18,15,128,'JourneyRocketBaseB2F'),
        ('JourneyRocketBaseB2F',3,2,128,'JourneyRocketBaseB1F'),
        ('JourneyRocketBaseB1F',3,2,128,'MauvilleCity_GameCorner')]:
        warp(origin,x,y);native('SetPlayerAvatarTransitionFlags',1);step(30)
        step(120,key);step(90)
        assert location()==map_id(target),('Casino stairs',origin,target,location(),position(),lib.read8(s['gPlayerAvatar']))
        picture(target+'-rocket-basement')
    results.append(dict(check='regional_incursions_and_casino',passed=True,
        individually_required_trainers=cases,regions_independent=True,physical_stair_warps=4,
        silph_after_six=True,alliance_after_seven=True,giovanni_requires_silph=True))
    print('Regional incursions and four casino stair warps passed',flush=True)
if args.gym_scaling:
    scaling = json.loads((source / '.journey-gym-scaling').read_text())
    if (source / '.journey-blue-gym').exists():
        for gym in scaling['gyms']:
            if gym['map']=='ViridianCity_Gym_Frlg':
                gym['trainers']=['TRAINER_JOURNEY_BLUE' if n=='TRAINER_LEADER_GIOVANNI' else n for n in gym['trainers']]
    trainer_size, mon_size, pokemon_size, party_offset, class_offset, lvl_offset, level_data, species_data, leader, frlg_leader, battle_trainer, trainers_count, difficulty_normal = abi[:13]
    trainers_base = s['gTrainers'] + difficulty_normal * trainers_count * trainer_size
    ids = {}
    for path in ['include/constants/opponents.h', 'include/constants/opponents_frlg.h']:
        ids.update({n:int(v) for n,v in re.findall(r'#define\s+(TRAINER_\w+)\s+(\d+)\b', (source / path).read_text())})
    native_badges = [lib.read16(s['gBadgeFlags'] + 2*i) for i in range(8)]
    kanto_badges = list(range(0x1AB0,0x1AB8))
    def set_bank(flags, count):
        for i, flag in enumerate(flags):
            address = save()+4720+flag//8
            byte = lib.read8(address); mask = 1 << (flag & 7)
            lib.write8(address, byte | mask if i < count else byte & ~mask)
    parties_tested = 0
    # Avoid gym on-entry story scripts: fixtures set the current map identity
    # only. This isolates real party generation, not accessibility or battles.
    for gym in scaling['gyms']:
        group, number = map_id(gym['map'])
        lib.write8(save()+4,group); lib.write8(save()+5,number)
        lib.write8(s['isFrlg'], int(gym['kanto']))
        for count in range(8):
            set_bank(kanto_badges if gym['kanto'] else native_badges,count)
            set_bank(native_badges if gym['kanto'] else kanto_badges,7-count)
            assert native('JourneyGymBadgeCount',int(gym['kanto'])) == count
            for name in gym['trainers']:
                trainer = trainers_base+ids[name]*trainer_size
                party_ptr = lib.read32(trainer+party_offset)
                target_party = s['gParties']+6*pokemon_size
                size = native('CreateNPCTrainerPartyFromTrainer',target_party,trainer,0,battle_trainer)
                assert 1 <= size <= 6, (name,size)
                original = [lib.read8(party_ptr+i*mon_size+lvl_offset) for i in range(size)]
                highest = max(original)
                is_leader = lib.read8(trainer+class_offset) in [leader,frlg_leader]
                for i, level in enumerate(original):
                    expected = scaling['ace_levels'][count] - min(6,highest-level) - (0 if is_leader else 2)
                    actual = native('GetMonData3',target_party+i*pokemon_size,level_data,0)
                    assert actual == expected,(gym['map'],name,count,i,actual,expected)
                parties_tested += 1
        print('Gym generated parties passed:',gym['map'],flush=True)
    # Non-gym battles retain original levels.
    group,number=map_id('Route131'); lib.write8(save()+4,group); lib.write8(save()+5,number)
    trainer=trainers_base+ids['TRAINER_ROXANNE_1']*trainer_size
    assert native('JourneyGymLevel',trainer,15) == 15
    results.append(dict(check='native_gym_party_levels',passed=True,parties=parties_tested,
        maps=len(scaling['gyms']),badge_counts=list(range(8)),non_gym_level_preserved=True,
        access_or_free_order_validated=False))
if args.worldsea or args.westsea or args.east_coast:
    ocean = dict(connections={})
    if args.worldsea:
        ocean['connections'].update(json.loads((source / '.journey-worldsea').read_text())['connections'])
    if args.westsea:
        ocean['connections'].update(json.loads((source / '.journey-westsea').read_text())['connections'])
    if args.east_coast:
        ocean['connections'].update(json.loads((source / '.journey-east-coast').read_text())['connections'])
    by_id = {json.loads((source / f'data/maps/{name}/map.json').read_text())['id']: name
             for name in ocean['connections']}
    keys = dict(up=64, down=128, left=32, right=16)
    for origin, links in ocean['connections'].items():
        origin_data = json.loads((source / f'data/maps/{origin}/map.json').read_text())
        layout = layouts[origin_data['layout']]
        for link in links:
            if link['map'] not in by_id: continue  # native routes are not modified here
            target = by_id[link['map']]
            if not origin.startswith('Journey') and not target.startswith('Journey'):
                continue  # preserved land seams are not new Surf passages
            direction, offset = link['direction'], link['offset']
            target_data = json.loads((source / f'data/maps/{target}/map.json').read_text())
            target_layout = layouts[target_data['layout']]
            if direction in ['up', 'down']:
                low, high = max(0, offset), min(layout['width'], offset + target_layout['width'])
                x = (low + high) // 2
                # Safe opened lane beside the pier; Vermilion's ocean channel
                # is x33/34, not the midpoint of its city-wide connection.
                if origin == 'VermilionCity_Frlg': x = 33
                elif target == 'VermilionCity_Frlg': x = 33
                elif origin.endswith('_Harbor_Frlg'): x = 4
                elif target.endswith('_Harbor_Frlg'): x = offset + 4
                y = 0 if direction == 'up' else layout['height'] - 1
            else:
                low, high = max(0, offset), min(layout['height'], offset + target_layout['height'])
                y = (low + high) // 2
                x = 0 if direction == 'left' else layout['width'] - 1
            warp(origin, x, y)
            native('SetPlayerAvatarTransitionFlags', 8); step(30)
            cross(target, keys[direction])
if args.team_stories:
    bank(kb,6);bank(hb,7)
    team_flag(flag_id('FLAG_HIDE_SAFFRON_ROCKETS'),True)
    team_flag(flag_id('FLAG_DEFEATED_MAGMA_SPACE_CENTER'),True)
    team_flag(flag_id('FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN'),False)
    for trainer in stories['trainers']:team_flag(0x500+trainer['id'],True)
    warp('SeafloorCavern_Room9',17,43)
    native('SetPlayerAvatarTransitionFlags',1);step(30)
    # Execute the real scene including Archie approach and Giovanni's dialogue.
    lib.write32(s['gBattleTypeFlags'],0)
    script(b'\x05'+struct.pack('<I',s['SeafloorCavern_Room9_EventScript_ArchieAwakenKyogre']),30)
    for _ in range(600):
        if lib.read32(s['gBattleTypeFlags'])&0x8000:break
        step(16,1);step(16)
    flags=lib.read32(s['gBattleTypeFlags'])
    assert flags&0x8000 and flags&0x40,('No two-opponent multi battle',hex(flags))
    assert lib.read16(s['gTrainerBattleParameter']+abi[13])==ids['TRAINER_JOURNEY_ARCHIE_ALLIANCE']
    opponent_b=s['gTrainerBattleParameter']+abi[14]
    assert lib.read8(opponent_b)|(lib.read8(opponent_b+1)<<8)==ids['TRAINER_JOURNEY_SHELLY_ALLIANCE']
    assert lib.read16(s['gPartnerTrainerId'])==abi[15],(lib.read16(s['gPartnerTrainerId']),abi[15])
    step(600)
    picture('Giovanni-Archie-Shelly-intro')
    for _ in range(40):
        step(16,1);step(16)
    assert lib.read8(s['gBattlersCount'])==4
    assert lib.read32(s['gMain']+4)&~1==s['BattleMainCB2']
    pixels=ctypes.string_at(lib.image(),240*160*4)
    assert len({pixels[i:i+3]for i in range(0,len(pixels),4)})>12, 'Battle never rendered'
    picture('Giovanni-Archie-Shelly-tag-battle')
    results.append(dict(check='real_giovanni_tag_battle_start',passed=True,partner_id=2,
        opponents=['ARCHIE','SHELLY'],battle_type_flags=flags,rendered_battlers=4,
        native_battle_screen_rendered=True,victory_aftermath_validated=False))
    print('Real Giovanni/Archie/Shelly tag battle started',flush=True)
lib.stop()
(args.output / ('connected-world.json' if args.westsea else 'worldsea.json' if args.worldsea else 'campaign-gates.json' if args.campaign_gates else 'crossing.json')).write_text(json.dumps(dict(status='experimental_not_full_integration',
    rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
    checks=results, full_story_validated=False, custom_journey_migrated=False), indent=2) + '\n')
print(f'{sum(r["check"] == "physical_surf_seam" for r in results)} physical Surf seams passed', flush=True)
