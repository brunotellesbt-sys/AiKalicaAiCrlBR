"""Exercise badge-story permissions, physical League gates and Galactic access.

Badge banks, old quest flags, initial travel, the qualifier-win flag and a
previously defeated bulkhead guard are declared fixtures. The qualifier's
actual championship is tested separately by validate_badge_qualifier.py.
Here, all checkpoint/door/ship interactions use native controller input.
No complete campaign or battle is claimed by this focused gate report.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys


ROOT = Path(__file__).resolve().parents[2]
KIND = 'badge-gates'
PARENT_ROM_SHA256 = 'cd5187f43d33b80e5ba2130c9e4e31a4d5a9a0e2504d8b71517da7d13814d9c6'
WON_FLAG = 0x1050
GALACTIC_STATE = 0x40FE
CROSSOVER_VISITS = 0x40FF

# Both threshold boundaries and allocations without all eight regional badges.
DISTRIBUTIONS = [(0, 0, 0), (8, 8, 0), (8, 8, 1), (8, 8, 2), (7, 3, 8),
                 (3, 8, 7), (8, 5, 8), (8, 6, 8), (6, 8, 8), (8, 8, 8)]
CHECKPOINTS = [
    ('Route22_NorthEntrance_Frlg', 7, 2, 0, False),
    ('Route23_Frlg', 13, 149, 1, False),
    ('Route23_Frlg', 7, 140, 2, False),
    ('Route23_Frlg', 12, 123, 3, False),
    ('Route23_Frlg', 14, 112, 4, True),
    ('Route23_Frlg', 9, 94, 5, True),
    ('Route23_Frlg', 12, 61, 6, False),
    ('Route23_Frlg', 5, 35, 7, False),
]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def c_function(text, name):
    match = re.search(r'^(?:bool32|void) ' + re.escape(name) + r'\([^)]*\)\s*\{', text, re.M)
    assert match, name
    depth, end = 1, match.end()
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[match.start():end]


def source_contract(source, baseline):
    source, baseline = Path(source), Path(baseline)
    assert digest(baseline / 'pokeemerald.gba') == PARENT_ROM_SHA256
    galactic = (source / 'src/journey_galactic.c').read_text()
    assert 'return JourneyTotalBadgeCount() >= 18 && JourneyQualifierWon();' in galactic
    assert 'gSpecialVar_Result = JourneyTotalBadgeCount() >= 22;' in galactic
    assert 'return JourneyTotalBadgeCount() >= 22 && state<7;' in galactic
    assert 'JourneyGymBadgeCount(TRUE)==8' not in galactic
    chapter = (source / 'data/scripts/journey_galactic.inc').read_text()
    gate = chapter.split('JourneyGalactic_Gate::', 1)[1].split('JourneyGalactic_GateDefeated::', 1)[0]
    assert 'special JourneyGalacticAvailable' in gate
    assert 'callnative JourneyCrossoverMissing' in gate
    assert 'JourneyGalactic_MissingRivals' in gate
    original = (baseline / 'src/journey_galactic.c').read_text()
    for name in ['JourneyGalacticCaptureLocked', 'JourneyGalacticNoCatch',
                 'JourneyGalacticGruntsCleared', 'JourneyGalacticOtherMissions']:
        assert c_function(original, name) == c_function(galactic, name), name
    routes = (source / 'data/scripts/route23.inc').read_text()
    assert routes.count('goto_if_eq VAR_RESULT, TRUE, JourneyBadgeStory_Route23Qualified') == 3
    for region, path in [
        ('Kanto', 'data/maps/IndigoPlateau_PokemonCenter_1F_Frlg/scripts.inc'),
        ('Hoenn', 'data/maps/EverGrandeCity_PokemonLeague_1F/scripts.inc'),
    ]:
        body = (source / path).read_text()
        assert 'special Journey' + region + 'LeaguePermission' in body
        assert not re.search(r'goto_if_unset FLAG_(?:KANTO_)?BADGE0[1-8]_GET,', body), path
    # All physical event locations, terrain and connections remain native.
    for name in ['Route22_NorthEntrance_Frlg', 'Route23_Frlg',
                 'IndigoPlateau_PokemonCenter_1F_Frlg',
                 'EverGrandeCity_PokemonLeague_1F', 'AbandonedShip_HiddenFloorRooms']:
        path = 'data/maps/' + name + '/map.json'
        assert (source / path).read_bytes() == (baseline / path).read_bytes(), path
    return dict(source_gate_contract_checked=True,
                physical_gate_event_locations_and_warps_unchanged=True,
                galactic_crossover_and_capture_requirements_preserved=True,
                baseline_rom_sha256=PARENT_ROM_SHA256)


def run_native(options, report):
    # Bootstrap the established emulator adapter, fresh flash and compiled ABI.
    # The split excludes the campaign-matrix's own assertions and test loop.
    global source, args, lib, s, abi, save, raw, native, raw_flag, flag_id, bank
    global kanto_badges, hoenn_badges, step, press, warp, position, location
    global map_id, picture, task
    sys.argv = [sys.argv[0], '--source', str(options.source), '--library', str(options.library),
                '--output', str(options.output)]
    prefix = (ROOT / 'tools/hoenn/validate_campaign_matrix.py').read_text().split('\nchecks = []')[0]
    exec(compile(prefix, str(ROOT / 'tools/hoenn/validate_campaign_matrix.py'), 'exec'), globals())
    native('SetPlayerAvatarTransitionFlags', 1)
    step(30)
    for i in range(6 * abi[2]):
        lib.write8(s['gParties'] + i, 0)
    lib.write8(s['gPartiesCount'], 0)
    assert native('ScriptGiveMon', 7, 40, 0) == 0
    native('ScriptSetMonMoveSlot', 0, 57, 0)
    native('DisableWildEncounters', 1)

    extra_badges = [flag_id('FLAG_JOURNEY_BADGE_' + name)
                    for name in ['MORTY', 'WHITNEY', 'STEVEN', 'BUGSY',
                                 'CANDICE', 'CLAIR', 'KAREN', 'OAK']]
    route_scene = int(re.search(r'^#define\s+VAR_MAP_SCENE_ROUTE23\s+(0x\w+)',
                               (source / 'include/constants/vars.h').read_text(), re.M)[1], 16)

    def set_badges(kanto, hoenn, extras, won):
        for flags, count in [(kanto_badges, kanto), (hoenn_badges, hoenn), (extra_badges, extras)]:
            bank(flags, (1 << count) - 1)
        raw_flag(WON_FLAG, won)
        assert native('FlagGet', WON_FLAG) == int(won)
        assert native('JourneyTotalBadgeCount') == kanto + hoenn + extras

    def special(name):
        native(name)
        return lib.read16(s['gSpecialVar_Result'])

    def permissions():
        return [special('JourneyKantoLeaguePermission'), special('JourneyHoennLeaguePermission'),
                special('JourneyExtraLeagueBadges')]

    def idle():
        return ((lib.read32(s['gMain'] + 4) & ~1) == s['CB2_Overworld']
                and not lib.read8(s['sLockFieldControls']))

    def place(mapping, x, y):
        if x <= 127 and y <= 127:
            warp(mapping, x, y)
            return
        # SetWarpDestination's direct coordinates are signed bytes, whereas
        # native map-warp events hold full sixteen-bit coordinates. Initial
        # travel is a declared fixture: temporarily point one existing event
        # at the requested starting tile in the emulator's private ROM copy.
        # Restore it before any controller input or checkpoint observation.
        group, number = map_id(mapping)
        header = native('Overworld_GetMapHeaderByGroupAndId', group, number)
        events = lib.read32(header + 4)
        assert lib.read8(events + 1), ('No native warp available for travel fixture', mapping)
        event = lib.read32(events + 8)
        previous = bytes(lib.read8(event + i) for i in range(4))
        try:
            for i, value in enumerate(struct.pack('<HH', x, y)):
                lib.raw8(event + i, value)
            globals()['script'](b'\x39' + bytes([group, number, 0])
                                + b'\0\0\0\0\x27\x6b\x02')
        finally:
            for i, value in enumerate(previous):
                lib.raw8(event + i, value)
        assert location() == (group, number) and position() == (x, y), (mapping, position())
        assert bytes(lib.read8(event + i) for i in range(4)) == previous

    def finish(limit=240):
        for _ in range(limit):
            if idle():
                return
            press(1)
        picture('badge-gates-stuck-dialogue')
        raise AssertionError(('Gate dialogue did not end', location(), position()))

    def capture(label):
        picture(label)
        file = options.output / (label + '.png')
        report['captures'].append(dict(file=file.name, sha256=digest(file)))

    # Prior regional quests and visits are deliberately not granted. Their
    # former League prerequisites must not survive through a second branch.
    for name in ['FLAG_RESCUED_MR_FUJI', 'FLAG_HIDE_CELADON_ROCKETS',
                 'FLAG_HIDE_SAFFRON_ROCKETS', 'FLAG_DEFEATED_EVIL_TEAM_MT_CHIMNEY',
                 'FLAG_GROUDON_AWAKENED_MAGMA_HIDEOUT', 'FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN']:
        raw_flag(flag_id(name), False)
    native('VarSet', CROSSOVER_VISITS, 0)
    native('VarSet', 0x409F, 0)
    cases = []
    for kanto, hoenn, extras in DISTRIBUTIONS:
        total = kanto + hoenn + extras
        for won in [False, True]:
            set_badges(kanto, hoenn, extras, won)
            for state in [0, 7]:
                native('VarSet', GALACTIC_STATE, state)
                observed = permissions()
                allowed = total >= 18 and won
                available = special('JourneyGalacticAvailable')
                assert observed == [int(allowed)] * 3, (total, won, state, observed)
                assert available == int(total >= 22), (total, available)
                cases.append(dict(kanto=kanto, hoenn=hoenn, extras=extras, total=total,
                                  qualifier_won=won, galactic_state=state,
                                  league_permissions=observed, galactic_available=available))

    chapter = json.loads((source / '.journey-galactic-chapter').read_text())
    grunts = chapter['grunts']
    assert len(grunts) == 18
    templates = []
    for grunt in grunts:
        mapping = json.loads((source / 'data/maps' / grunt['map'] / 'map.json').read_text())
        script_name = 'JourneyGalactic_' + grunt['key']
        local_id = next(i + 1 for i, obj in enumerate(mapping['object_events']) if obj['script'] == script_name)
        group, number = map_id(grunt['map'])
        pointer = native('GetObjectEventTemplateByLocalIdAndMap', local_id, number, group)
        assert pointer and lib.read32(pointer + 16) == s[script_name]
        templates.append((grunt, pointer, group, number, local_id))
        # These pre-existing victories only prevent automatic approach while
        # observing visibility. They do not stand for battles in this report.
        raw_flag(0x500 + grunt['id'], True)
    visibility = []
    for total, kanto, hoenn, extras in [(21, 8, 5, 8), (22, 8, 6, 8)]:
        set_badges(kanto, hoenn, extras, False)
        for state in [0, 7]:
            native('VarSet', GALACTIC_STATE, state)
            for grunt, pointer, group, number, _ in templates:
                actual = native('JourneyGalacticObjectVisible', pointer, group, number)
                assert actual == int(total >= 22 and state < 7), (grunt, total, state, actual)
                visibility.append(dict(key=grunt['key'], total=total, galactic_state=state, visible=bool(actual)))

    # Observe a loaded template at the actual threshold, not only the C result.
    grunt, _, group, number, local_id = templates[0]
    loaded_visibility = []
    for total, kanto, hoenn, extras in [(21, 8, 5, 8), (22, 8, 6, 8)]:
        set_badges(kanto, hoenn, extras, False)
        native('VarSet', GALACTIC_STATE, 0)
        warp(grunt['map'], grunt['x'] + 1, grunt['y'])
        native('SetPlayerAvatarTransitionFlags', 1)
        step(30)
        obj = native('GetObjectEventIdByLocalIdAndMap', local_id, number, group)
        assert (obj < 16) == (total == 22), (total, obj)
        capture('badge-gates-galactic-' + str(total) + '-badges')
        loaded_visibility.append(dict(total=total, map=grunt['map'], local_id=local_id, object_loaded=obj < 16))

    checkpoints = []
    set_badges(6, 4, 8, True)
    native('VarSet', GALACTIC_STATE, 0)
    for index, (mapping, x, y, scene, surfing) in enumerate(CHECKPOINTS):
        print('Checking native checkpoint', index + 1, mapping, flush=True)
        native('VarSet', route_scene, scene)
        place(mapping, x, y + 1)
        native('VarSet', route_scene, scene)
        native('SetPlayerAvatarTransitionFlags', 8 if surfing else 1)
        step(30)
        before = position()
        assert before == (x, y + 1), (mapping, before)
        for _ in range(120):
            step(1, 64)
            if position() == (x, y):
                break
        assert position() == (x, y), (mapping, 'did not reach trigger', position())
        step(25)
        finish()
        assert native('VarGet', route_scene) == 8, (mapping, x, y, 'trigger did not recognize qualifier')
        assert position() == (x, y), ('Qualified player was pushed back', mapping, position())
        capture('badge-gates-checkpoint-' + str(index + 1))
        for _ in range(160):
            step(1, 64)
            # Object coordinates advance at the start of a walking animation.
            # The gatehouse warp executes only when that step finishes.
            if location() != map_id(mapping) or (index != 0 and position() == (x, y - 1)):
                break
        if index == 0:
            assert location() == map_id('Route23_Frlg'), ('Boulder guard did not permit native exit', location())
            step(45)
        else:
            assert location() == map_id(mapping) and position() == (x, y - 1), (mapping, x, y, position())
            step(18)
        checkpoints.append(dict(checkpoint=index + 1, map=mapping, trigger=[x, y],
                                fixture_start=list(before), initial_surf_fixture=surfing,
                                recognition_state=8, controller_crossing=True,
                                after_map=list(location()), after_position=list(position())))

    # A winner below18 and a nonwinner at18 cannot use the shortcut. Test the
    # Earth checkpoint with that badge absent from both regional banks: native
    # exploration still permits guards whose ordinary badge was already won.
    blocked = []
    for distribution, won in [((6, 3, 8), True), ((6, 4, 8), False)]:
        set_badges(*distribution, won)
        native('VarSet', route_scene, 7)
        place('Route23_Frlg', 5, 36)
        native('VarSet', route_scene, 7)
        native('SetPlayerAvatarTransitionFlags', 1)
        step(30)
        for _ in range(120):
            step(1, 64)
            if position() == (5, 35):
                break
        step(25)
        finish()
        assert position()[1] >= 36 and native('VarGet', route_scene) == 7
        capture('badge-gates-checkpoint-denied-' + str(sum(distribution)))
        blocked.append(dict(total=sum(distribution), qualifier_won=won, pushed_back=True,
                            after_position=list(position()), recognition_state=7))

    leagues = []
    for kanto in [True, False]:
        mapping = 'IndigoPlateau_PokemonCenter_1F_Frlg' if kanto else 'EverGrandeCity_PokemonLeague_1F'
        x = 4 if kanto else 9
        for distribution, won, entered in [((8, 8, 1), True, False), ((6, 4, 8), False, False),
                                            ((6, 4, 8), False, True), ((6, 4, 8), True, False)]:
            allowed = sum(distribution) >= 18 and won
            set_badges(*distribution, won)
            native('VarSet', GALACTIC_STATE, 0)
            native('VarSet', CROSSOVER_VISITS, 0)
            raw_flag(flag_id('FLAG_ENTERED_ELITE_FOUR'), entered)
            warp(mapping, x, 3)
            native('SetPlayerAvatarTransitionFlags', 1)
            step(30)
            step(8, 64); step(20)
            if not allowed or not kanto:
                press(1)
                finish()
            if allowed:
                for _ in range(240):
                    step(1, 64)
                    if location() != map_id(mapping):
                        break
                assert location() != map_id(mapping), ('Qualified mixed-bank player did not enter League', mapping)
                step(60)
            else:
                step(40, 64)
                assert location() == map_id(mapping) and position()[1] >= 3
            capture('badge-gates-' + ('kanto' if kanto else 'hoenn')
                    + ('-admitted' if allowed else '-denied-' + str(sum(distribution)) + '-' + str(int(entered))))
            leagues.append(dict(region='Kanto' if kanto else 'Hoenn', fixture_start_map=mapping,
                                kanto_badges=distribution[0], hoenn_badges=distribution[1], extras=distribution[2],
                                total=sum(distribution), qualifier_won=won, prior_elite_entry=entered,
                                galactic_state=0, crossover_visits=0,
                                allowed=allowed, physical_controller_entry=allowed,
                                physical_controller_denial=not allowed,
                                after_map=list(location()), after_position=list(position())))

    # The bulkhead stays a guide before22. Its scripted door must not use the
    # old eight-plus-eight threshold, and missing crossover visits still matter.
    continuity = json.loads((source / '.journey-galactic-continuity').read_text())
    guard = next(g for g in continuity['grunts'] if g['key'] == 'GALACTIC_BULKHEAD_GUARD')
    raw_flag(0x500 + guard['id'], True)
    chapter_entry = []
    for total, distribution, visits in [(21, (8, 5, 8), 4095), (22, (8, 6, 8), 0), (22, (8, 6, 8), 4095)]:
        set_badges(*distribution, True)
        native('VarSet', GALACTIC_STATE, 0)
        native('VarSet', CROSSOVER_VISITS, visits)
        warp(guard['map'], guard['x'], guard['y'] + 1)
        native('SetPlayerAvatarTransitionFlags', 1)
        step(8, 64); step(20); press(1)
        admitted = total == 22 and visits == 4095
        if admitted:
            for _ in range(180):
                if task('Task_HandleYesNoInput'):
                    break
                press(1)
            assert task('Task_HandleYesNoInput'), 'Galactic entry prompt missing at22'
            step(12)
            capture('badge-gates-galactic-22-entry-prompt')
            press(1)
            for _ in range(180):
                if location() == map_id('JourneyGalacticHall'):
                    break
                press(1)
            assert location() == map_id('JourneyGalacticHall')
            step(120)
        else:
            finish()
            assert location() == map_id(guard['map'])
        capture('badge-gates-galactic-entry-' + str(total) + '-' + str(visits))
        chapter_entry.append(dict(total=total, kanto=distribution[0], hoenn=distribution[1], extras=distribution[2],
                                  crossover_visits=visits, bulkhead_previously_defeated_fixture=True,
                                  physical_interaction=True, admitted=admitted, after_map=list(location())))

    set_badges(6, 4, 8, True)
    native('VarSet', GALACTIC_STATE, 0)
    native('VarSet', CROSSOVER_VISITS, 0)
    warp('Route23_Frlg', 5, 37)
    native('SetPlayerAvatarTransitionFlags', 1)
    step(30)
    assert native('TrySavingData', 0, max_frames=6000) == 1
    step(60)
    set_badges(8, 8, 1, False)
    assert permissions() == [0, 0, 0]
    assert native('LoadGameSave', 0, max_frames=6000) == 1
    step(30)
    assert native('JourneyTotalBadgeCount') == 18 and permissions() == [1, 1, 1]
    assert native('VarGet', GALACTIC_STATE) == native('VarGet', CROSSOVER_VISITS) == 0
    capture('badge-gates-native-save-qualification')

    report.update(passed=True, preflight=False, compiled_rom=True, native_validation_performed=True,
                  review_mode=bool(lib.read8(s['gJourneyReviewMode'])),
                  permission_cases=cases, grunt_visibility_cases=visibility,
                  loaded_grunt_visibility=loaded_visibility, physical_checkpoints=checkpoints,
                  physical_checkpoint_denials=blocked, physical_leagues=leagues,
                  physical_galactic_entry=chapter_entry, native_qualification_save_roundtrip=True,
                  qualifier_victory_flag_is_initial_fixture=True,
                  initial_badges_quests_party_surf_and_travel_are_fixtures=True,
                  high_coordinate_initial_travel_uses_restored_private_emulator_warp_fixture=True,
                  no_qualification_victory_or_galactic_battle_claimed=True,
                  controller_input_drives_all_crossings_and_interactions=True,
                  prior_missions_and_crossover_are_not_league_prerequisites=True,
                  full_campaign_playthrough=False)
    lib.stop()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, default=ROOT / '.local/coastal-closures-dma-src')
    parser.add_argument('--library', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--preflight', action='store_true')
    options = parser.parse_args()
    options.output.mkdir(parents=True, exist_ok=True)
    report = dict(kind=KIND, passed=False, preflight=True, compiled_rom=False,
                  native_validation_performed=False, captures=[])
    report.update(source_contract(options.source, options.baseline))
    if options.library and not options.preflight:
        report['rom_sha256'] = digest(options.source / 'pokeemerald.gba')
        before = report['rom_sha256']
        run_native(options, report)
        assert digest(options.source / 'pokeemerald.gba') == before
    else:
        report['native_validation_pending'] = True
    (options.output / 'badge-gates.json').write_text(json.dumps(report, indent=2) + '\n')
    print(KIND, 'native PASS' if report['passed'] else 'source preflight only')


if __name__ == '__main__':
    main()
