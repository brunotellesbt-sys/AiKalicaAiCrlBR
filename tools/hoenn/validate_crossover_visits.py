"""Complete all eight crossover encounters through normal field/controller input.

Prior travel/badges and a boosted player team are fixtures; no rival victory or
visit flags are written. This is not a New Game to credits playthrough.
"""
import hashlib,json,re,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
deck_only = '--deck-entry' in sys.argv
if deck_only:
    sys.argv.remove('--deck-entry')
galactic=(ROOT/'tools/hoenn/validate_galactic_chapter.py').read_text()
# Reuse the field and battle fixtures without preparing Galactic prerequisites.
bootstrap=galactic.split('\nchapter=json.loads')[0] + '\n' + galactic[galactic.index('\ntargets='):galactic.index('\nwins=[]')]
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_galactic_chapter.py'),'exec'))
# Use the game's fast text, Set battle style and disabled battle animations
# so the controller proof can cover all five editions.
settings = lib.read32(s['gSaveBlock2Ptr']) + 0x14
lib.write16(settings, (lib.read16(settings) & ~7) | 2 | 0x200 | 0x400)
native('VarSet',0x40FF,0)
native('VarSet',0x40FE,0)
rawflag(lib.read16(s['gBadgeFlags'])-7,True) # SYSTEM_FLAGS + 0, calibrated from the compiled badge table.
headers=(source/'src/data/tilesets/headers.h').read_text()
metas=(source/'src/data/tilesets/metatiles.h').read_text()

def attributes(tileset,frlg):
    body=re.search(r'const struct Tileset '+tileset+r'\s*=\s*\{(.*?)\};',headers,re.S)[1]
    symbol=re.search(r'\.metatileAttributes = (\w+)',body)[1]
    path=re.search(r'\b'+symbol+r'\[\].*?"([^"]+)"',metas)[1]
    raw=(source/path).read_bytes()
    return struct.unpack('<'+('I' if frlg else 'H')*(len(raw)//(4 if frlg else 2)),raw)

routes=['Route4_Frlg','Route10_Frlg','Route17_Frlg','Route112','Route113','PetalburgWoods',
        'Route6_Frlg','Route13_Frlg','Route20_Frlg','Route106','Route108','Route125']
marker=source/'.journey-crossover-badges'
late_routes = {13: ('SixIsland_WaterPath_Frlg', 15, 68, {62, 143, 272, 338, 395, 468}),
               12: ('Route123', 20, 78, {208, 212, 248, 445, 477, 486})}
modern = marker.exists()
normal9 = (source/'pokeemerald.gba').read_bytes()[0xA0:0xAC].rstrip() == b'JOURNEY G9 N'
if modern:
    routes[10]='AbandonedShip_Deck'
    routes.extend(late_routes[index][0] for index in (12, 13))
extra_flags = list(range(0x1040, 0x1048))


def route_start(index):
    name=routes[index];mapdata=json.loads((source/'data/maps'/name/'map.json').read_text())
    layout=layouts[mapdata['layout']];w,h=layout['width'],layout['height']
    raw=(source/layout['blockdata_filepath']).read_bytes();blocks=struct.unpack('<'+'H'*(len(raw)//2),raw)
    primary=attributes(layout['primary_tileset'],layout['layout_version']=='frlg');secondary=attributes(layout['secondary_tileset'],layout['layout_version']=='frlg')
    cutoff=640 if layout['layout_version']=='frlg' else 512
    behaviors={(primary[value&1023] if value&1023<cutoff else secondary[(value&1023)-cutoff])&255 for value in blocks if not(value>>10&3)}
    ground={behavior for behavior in behaviors if not native('MetatileBehavior_IsSurfableWaterOrUnderwater',behavior)}
    def suitable(x,y):
        value=blocks[y*w+x];mid=value&1023
        behavior=(primary[mid] if mid<cutoff else secondary[mid-cutoff])&255
        return value>>10&3==0 and behavior in ground
    occupied={(o['x'],o['y']) for o in mapdata['object_events']}
    occupied.update((o['x'],o['y']) for o in mapdata.get('coord_events',[]))
    trainers=[o for o in mapdata['object_events'] if o.get('trainer_type') not in [None,'TRAINER_TYPE_NONE']]
    if name == 'AbandonedShip_Deck':
        assert suitable(13, 14) and (13, 14) not in occupied
        assert any(warp['dest_map']=='MAP_ROUTE108' and (warp['x'],warp['y'])==(13,15)
                   for warp in mapdata['warp_events'])
        return 13, 14
    candidates=[]
    for y in range(1,h-1):
        if name == 'SixIsland_WaterPath_Frlg' and not 40 <= y < 63:
            continue
        for x in range(1,w-1):
            if name == 'Route123' and x >= 40:
                break
            for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                line=[(x+dx*i,y+dy*i) for i in range(3)]
                if all(0<=xx<w and 0<=yy<h and suitable(xx,yy) and (xx,yy) not in occupied for xx,yy in line) and len({blocks[yy*w+xx]>>12 for xx,yy in line})==1 and all(abs(x-o['x'])+abs(y-o['y'])>int(o.get('trainer_sight_or_berry_tree_id',0))+2 for o in trainers):
                    candidates.append((x,y))
    assert candidates,('No walkable approach for mandatory rival',name)
    # Ending the warp fixture lets the normal on-frame hook spawn and approach.
    return candidates[len(candidates)//2]


def set_badges(flags, count):
    for index, own_flag in enumerate(flags):
        rawflag(own_flag, index < count)


def assert_idle_on_route(name, before):
    step(100)
    assert idle() and location() == map_id(name), ('Unexpected approach', name, position())
    assert native('VarGet', 0x40FF) == before
    assert all(not lib.read8(s['gObjectEvents'] + 36 * i) & 1
               or lib.read8(s['gObjectEvents'] + 36 * i + 8) != 240 for i in range(16))


def set_total_badges(count):
    # Alternate Hoenn and Kanto before filling the extra circuit.
    flags = [flag for pair in zip(hoenn_flags,kanto_flags) for flag in pair] + extra_flags
    set_badges(flags, count)


def prepare_team(level):
    for i in range(6 * abi[2]):
        lib.write8(party + i, 0)
    lib.write8(s['gPartiesCount'], 0)
    for species in (260, 149, 376):
        assert native('ScriptGiveMon', species, level, 0) == 0
    assert native('JourneyWildMean') == level


def observe_late_team(observation, original_input):
    def read_team():
        levels = [lib.read8(enemy + slot * abi[2] + pabi[17]) for slot in range(6)]
        accepting_commands = any(lib.read32(s['gBattlerControllerFuncs'] + slot * 4) & ~1 in actions | moves | targets
                                 for slot in range(4))
        if all(levels) and accepting_commands:
            observation.setdefault('enemy_levels', levels)
        species = lib.read16(s['gBattleMons'] + abi[74] + abi[75])
        if species and accepting_commands:
            observation['enemy_species'].add(species)
        original_input()
    return read_team


def equip_fixture_moves():
    native('HealPlayerParty')
    for member, move in enumerate((332, 337, 309)):
        for slot in range(4):
            native('ScriptSetMonMoveSlot', member, move if slot == 0 else 0, slot)


if deck_only:
    set_total_badges(11)
    earlier = (1 << 9) | (1 << 7)
    native('VarSet', 0x40FF, earlier)
    prepare_team(100)
    equip_fixture_moves()
    warp('Route108', 28, 6)
    step(20, 16)
    step(20)
    assert position() == (29, 6)
    step(20, 64)
    step(130)
    assert location() == map_id('AbandonedShip_Deck') and position() == (13, 15)
    step(12, 64)
    step(40)
    picture('luffy-on-the-deck')
    battle = one_battle('Luffy at the ship deck', limit=4800)
    assert battle['opponent'] == 1559 and native('VarGet', 0x40FF) == earlier | (1 << 10)
    lib.stop()
    frame = (args.output / 'luffy-on-the-deck.png').read_bytes()
    (args.output / 'route108-entry.json').write_text(json.dumps(dict(
        passed=True, rom_sha256=sha, source=['Route108', 28, 6], deck_arrival=[13, 15],
        battle=battle, screenshot_sha256=hashlib.sha256(frame).hexdigest(),
        prior_badges_and_wins_are_fixtures=True), indent=2) + '\n')
    sys.exit(0)


if modern:
    order = [(0,1), (9,2), (3,5), (7,7), (10,11), (2,13), (13,15), (12,20)]
    # A legacy visit mask may have won four battles at entirely different sites.
    # Exercise the query separately and reset the fixture before the native trip.
    native('VarSet',0x40FF,0xFFF)
    assert native('JourneyCrossoverComplete') and special('JourneyCrossoverMissing')
    native('VarSet',0x40FF,0)
    set_total_badges(24)
    for later in (3,7):
        warp(routes[later], *route_start(later))
        assert_idle_on_route(routes[later],0)
else:
    set_badges(kanto_flags,8)
    set_badges(hoenn_flags,8)
    order=[(index,None) for index in [2,8,5,9,1,7,3,11,0,10,4,6]]

wins=[]
visited=0
for index, badges in order:
    name=routes[index]
    x,y=route_start(index)
    print('Checking crossover encounter:',name,flush=True)
    late = index in late_routes
    observed = {}
    if index == order[0][0] and modern:
        prepare_team(100)
    if late:
        _, _, level, roster = late_routes[index]
        prepare_team(level)
        observed.update(party_mean=level, enemy_species=set())
    equip_fixture_moves()
    if modern:
        assert not native('JourneyCrossoverComplete')
        set_total_badges(badges-1)
        assert native('JourneyTotalBadgeCount')==badges-1
        warp(name,x,y)
        assert_idle_on_route(name,visited)
        set_total_badges(badges)
    else:
        warp(name,x,y)
    step(50)
    if modern:
        assert any(lib.read8(s['gObjectEvents']+36*i)&1
                   and lib.read8(s['gObjectEvents']+36*i+8)==240 for i in range(16)),(name,x,y)
        picture('approach-'+name)
        if normal9:
            step(240)
            picture('dialogue-'+name)
    original_input=battle_input
    if late:
        battle_input=observe_late_team(observed,original_input)
    try:
        win=one_battle(name,limit=4800)
    finally:
        battle_input=original_input
    visited |= 1<<index
    assert native('VarGet',0x40FF)==visited
    win.update(map=name,visit_bit=index,visit_mask=visited,approach=[x,y])
    if modern:
        assert native('FlagGet',0x500+win['opponent'])
        assert native('JourneyTotalBadgeCount')==badges
        capture = 'approach-' + name + '.png'
        win.update(capture=capture, capture_sha256=hashlib.sha256((args.output / capture).read_bytes()).hexdigest())
        win.update(battled_at=badges,blocked_at=badges-1,badge_scope='total')
    if late:
        assert len(observed['enemy_levels'])==6 and all(level-5<=v<=level+2 for v in observed['enemy_levels']),observed
        assert observed['enemy_species']==roster,observed
        win.update(observed,enemy_species=sorted(roster))
    assert_idle_on_route(name,visited)
    wins.append(win)
    print('Won:',name,win['opponent'],flush=True)
assert native('JourneyCrossoverComplete')==1
assert hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest()==sha
# On the expanded Normal edition, follow the recorded wins up to the ship.
# Only the independent plot chapters, qualifier and bulkhead guard are seeded.
if modern and normal9:
    from validate_atlas_candidate_batteries_native import save_menu
    from validate_cold_boot import validate as cold_boot
    set_total_badges(22)
    native('VarSet', 0x409B, 8)
    native('VarSet', 0x40E5, 4)
    rawflag(flag_id('FLAG_JOURNEY_QUALIFIER_WON'), True)
    opponent_defs = (source/'include/constants/opponents.h').read_text()
    guard = int(re.search(r'#define TRAINER_JOURNEY_GALACTIC_BULKHEAD_GUARD (\d+)', opponent_defs)[1])
    rawflag(0x500 + guard, True)
    ship = 'AbandonedShip_HiddenFloorRooms'
    actor, = [npc for npc in json.loads((source/'data/maps'/ship/'map.json').read_bytes())['object_events']
              if npc['script'] == 'JourneyGalactic_Gate']
    start = (actor['x'], actor['y'] + 1)
    warp(ship, *start)
    assert position() == start and native('JourneyCrossoverComplete')
    battery = args.output/'eight-wins.sav'
    save_menu(globals(), battery)
    step(1, 64)
    step(20)
    press(1)
    for _ in range(60):
        if task('Task_HandleYesNoInput'):
            break
        press(1)
    assert task('Task_HandleYesNoInput')
    step(12)
    press(1)
    until(lambda: location() == map_id('JourneyGalacticHall'))
    step(120)
    picture('eight-wins-galactic-entry')
    assert native('VarGet', 0x40FF) == visited
    # Exercise the three real pages on the Trainer Card using 22 earned flags.
    exec(compile((ROOT/'tools/hoenn/validate_extra_gym_card.py').read_text(), 'extra-gym-card','exec'))
lib.stop()
if modern and normal9:
    resumed = cold_boot(source, args.library, args.output/'eight-wins-continue', battery,
                        expected_geometry_version=9, expected_variables=((0x40FF, visited),(0x409B,8),(0x40E5,4)))
    assert resumed['runs'][-1]['field_map'] == list(map_id(ship))
    assert resumed['runs'][-1]['player_tile'] == list(start)
(args.output/'crossover-visits.json').write_text(json.dumps(dict(passed=True,rom_sha256=sha,wins=wins,
    native_victories=True,normal_field_hook_and_approach=True,visit_flags_not_written=True,
    initial_badges_travel_and_team_are_fixtures=True,player_battle_stats_boosted=True,
    ordered_by_badges=modern, skipped_earlier_battle_refused=modern,
    legacy_completed_visit_mask_accepted=modern,full_campaign_playthrough=False,
    elf_sha256=hashlib.sha256((source/'pokeemerald.elf').read_bytes()).hexdigest(),
    marker_sha256=hashlib.sha256(marker.read_bytes()).hexdigest() if modern else None),indent=2)+'\n')
