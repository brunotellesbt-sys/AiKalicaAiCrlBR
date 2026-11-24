"""Controller checks shared with the native Sootopolis rescue validation."""

WISHSTAR = 'JourneyLegendRoom0385'
TITANS = 'JourneySanctuaryTitans'
EXTERIOR = 'JourneyAtlasCave11'
SHIP = 'AbandonedShip_HiddenFloorRooms'
HALL = 'JourneyGalacticHall'
MAPS = ['FieryPath', WISHSTAR, EXTERIOR, TITANS, SHIP, HALL]
STORY_VAR = 0x409B


def play_titan_story(ctx):
    walk, warp, step, press = (ctx[key] for key in ('walk', 'warp', 'step', 'press'))
    native, lib, symbols = (ctx[key] for key in ('native', 'lib', 's'))
    active, picture, finish, wait_for = (ctx[key] for key in ('active_actor', 'picture', 'finish', 'wait_for'))
    save_menu, position, location, map_id = (ctx[key] for key in ('save_menu', 'position', 'location', 'map_id'))
    var, rawflag, flag_id = (ctx[key] for key in ('var', 'rawflag', 'flag_id'))
    expanded = lib.read16(symbols['gJourneyBuildRules']) == 1025

    def state():
        return native('VarGet', STORY_VAR)

    def talk(name, x, y, facing=64):
        walk((name, x, y))
        step(1, facing)
        step(20)
        assert position() == (x, y), (name, position())
        press(1)

    def yes():
        wait_for(lambda: ctx['task']('Task_HandleYesNoInput'), 'titan-choice')
        step(12)
        press(1)
        finish()

    assert state() == 0 and ctx['stage']() == 4
    # Entry coordinates are fixtures. Both actual cave portals are crossed
    # with the D-pad and every story variable change comes from its NPC script.
    warp('FieryPath', 4, 7)
    ctx['refresh_loaded_warp_tiles']()
    talk(WISHSTAR, 17, 21)
    wait_for(lambda: active(3), 'wishstar-jirachi')
    step(42)
    picture('jirachi-and-eren')
    finish()
    assert state() == 1 and not active(2) and not active(3)
    walk(('FieryPath', 4, 7))
    warp(EXTERIOR, 20, 20)
    ctx['refresh_loaded_warp_tiles']()
    talk(TITANS, 14, 17)
    finish()
    assert state() == 1
    picture('eren-in-titan-cave')

    talk(TITANS, 15, 16)
    finish()
    assert state() == 1, 'Rose must wait for Maria'
    talk(TITANS, 6, 7)
    wait_for(lambda: ctx['task']('Task_HandleYesNoInput'), 'maria-choice')
    step(12)
    press(2)
    finish()
    assert state() == 1, 'Declining preserves the pending seal'
    talk(TITANS, 6, 7)
    yes()
    assert state() == 2
    picture('regirock-maria')
    checkpoint = ctx['args'].output / 'titan-cave.sav'
    save_menu(ctx, checkpoint)
    assert native('LoadGameSave', 0, max_frames=6000) == 1
    lib.write32(symbols['gMain'] + 4, symbols['CB2_ContinueSavedGame'] | 1)
    step(950)
    finish()
    assert location() == map_id(TITANS) and position() == (6, 7) and state() == 2

    for x, y, expected, capture in ((15, 16, 3, 'regice-rose'), (15, 7, 4, 'registeel-sina')):
        talk(TITANS, x, y)
        yes()
        assert state() == expected
        picture(capture)
    talk(TITANS, 6, 16)
    assert active(5) is expanded
    if expanded:
        yes()
        assert state() == 5
        picture('regieleki-reiner')
        talk(TITANS, 10, 17)
        yes()
        assert state() == 6
        picture('regidrago-zeke')

    talk(TITANS, 10, 8)
    wait_for(lambda: active(8), 'groudon-appears')
    picture('regigigas-and-groudon')
    finish()
    assert state() == 7
    talk(TITANS, 8, 10)
    yes()
    assert state() == 8 and not active(8)
    picture('titan-cave-concluded')
    walk((EXTERIOR, 20, 20))

    # Probe the normal in-game entrance, with campaign prerequisites seeded
    # independently so the relevant denial and the real portal are visible.
    for badge in ctx['kanto_flags'] + ctx['hoenn_flags']:
        rawflag(badge, True)
    for name in ('MORTY', 'WHITNEY', 'STEVEN', 'BUGSY', 'CANDICE', 'CLAIR'):
        rawflag(flag_id('FLAG_JOURNEY_BADGE_' + name), True)
    assert native('JourneyTotalBadgeCount') == 22
    qualifier = flag_id('FLAG_JOURNEY_QUALIFIER_WON')
    guard = next(actor for actor in ctx['maps'][SHIP]['object_events'] if actor['script'] == 'JourneyGalactic_Gate')
    x, y = guard['x'], guard['y'] + 1
    warp(SHIP, x, y)
    talk(SHIP, x, y)
    step(42)
    picture('galactic-waits-for-frontier')
    finish()
    assert location() == map_id(SHIP) and not ctx['task']('Task_HandleYesNoInput')
    rawflag(qualifier, True)
    native('VarSet', STORY_VAR, 1)
    talk(SHIP, x, y)
    step(42)
    picture('galactic-waits-for-titan-cave')
    finish()
    assert location() == map_id(SHIP)
    native('VarSet', STORY_VAR, 8)
    var('VAR_JOURNEY_GALACTIC_STATE', 0)
    var('VAR_JOURNEY_SOOTOPOLIS_RESCUE', 3)
    talk(SHIP, x, y)
    step(42)
    picture('galactic-waits-for-rescue')
    finish()
    assert location() == map_id(SHIP)
    var('VAR_JOURNEY_SOOTOPOLIS_RESCUE', 4)
    native('VarSet', 0x40FF, 0xFFF)
    # The bulkhead guard's battle is already won in this fixture. The portal
    # still uses the real NPC, check, YES menu and destination.
    opponents = (ctx['source'] / 'include/constants/opponents.h').read_text()
    rawflag(0x500 + ctx['constant'](opponents, 'TRAINER_JOURNEY_GALACTIC_BULKHEAD_GUARD'), True)
    talk(SHIP, x, y)
    wait_for(lambda: ctx['task']('Task_HandleYesNoInput'), 'galactic-finale-open')
    step(12)
    press(1)
    wait_for(lambda: location() == map_id(HALL), 'galactic-prison-entered')
    step(90)
    picture('galactic-finale-entry')
    return dict(eren_started_after_rescue=True, region2_regs=expanded, native_titan_complete=True,
                titan_stage=8, galactic_fixtures_and_physical_gate=True)
