"""Current Atlas town/terminal/ferry/Surf trips and real dry/wet cold saves.

One initial party/progress/position fixture per island is declared. After
departure, only controls and whitelisted read-only native getters are used.
Current compiled maps and Atlas arrivals replace historical pier coordinates.
"""
import argparse
import hashlib
import json
from pathlib import Path

from validate_atlas_candidate_batteries_native import save_menu
from validate_coast_scenery_objects import bootstrap
from validate_cold_boot import validate as cold_boot


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(source, library, output, islands=None):
    source, library, output = (Path(p).resolve() for p in (source, library, output))
    output.mkdir(parents=True, exist_ok=True)
    metadata = json.loads((source/'.journey-atlas-surf-layout').read_bytes())
    historical = json.loads((source/'.journey-sevii-integrated-piers').read_bytes())['harbors']['ports']
    arrivals = {p['island']: p for p in metadata['ports']['arrivals']}
    ports = [p for p in historical if islands is None or p['island'] in islands]
    assert len(arrivals) == len(historical) == 7 and ports
    artifacts = {n: sha(source/n) for n in ('pokeemerald.gba', 'pokeemerald.elf', '.journey-atlas-surf-layout')}
    names = {'JourneyPalletHarbor'}
    for p in ports:
        names.update((p['town'], p['interior'], p['start'][0], arrivals[p['island']]['destination'][0]))
    ns = bootstrap(source, library, output, names)
    lib, symbols = ns['lib'], ns['s']
    original = {k: ns[k] for k in ('step', 'native', 'script', 'warp', 'picture')}
    fixture = True
    depth = 0
    phase = 'fixture'
    controls, queries, captures, routes, cases, batteries = [], [], [], [], [], []

    def step(frames, key=0):
        if not fixture and not depth:
            controls.append(dict(phase=phase, frames=frames, key=key))
        original['step'](frames, key)

    def native(function, *args, **kwargs):
        nonlocal depth
        if not fixture:
            assert function.startswith(('MapGridGet', 'MetatileBehavior_Is')) or function in {
                'PlayerGetElevation', 'GetPlayerFacingDirection', 'GetPlayerFacingMovementDirection',
                'IsPlayerFacingSurfableFishableWater', 'IsDirectionalStairWarpMetatileBehavior'}, function
            queries.append(dict(phase=phase, function=function, arguments=list(args)))
        depth += 1
        try:
            return original['native'](function, *args, **kwargs)
        finally:
            depth -= 1

    def script(*args, **kwargs):
        assert fixture or depth, 'Gameplay script injected after departure'
        return original['script'](*args, **kwargs)

    def warp(*args, **kwargs):
        assert fixture, 'Position fixture during a port trip'
        return original['warp'](*args, **kwargs)

    def picture(label):
        original['picture'](label)
        captures.append(dict(file=label+'.png', sha256=sha(output/(label+'.png'))))

    def observe(before, after):
        routes.append(dict(phase=phase, before=list(before), after=list(after)))

    ns.update(step=step, native=native, script=script, warp=warp, picture=picture,
              walk_observer=observe, walk_transition_pictures=False)

    def battery(label):
        before = ns['player_state']()
        path = output/(label+'.sav')
        callbacks = save_menu(ns, path)
        picture(label)
        record = dict(file=path.name, sha256=sha(path), state=before, callbacks=callbacks,
                      geometry_version=8, saved_through_native_menu=True)
        batteries.append(record)
        return record

    try:
        for port in ports:
            island = port['island']
            prefix = island.lower()
            arrival = arrivals[island]
            dry = tuple(arrival['destination'])
            wet = (arrival['wet_return']['map'], *arrival['wet_return']['tile'])
            assert dry[0] == wet[0]
            dx, dy = wet[1]-dry[1], wet[2]-dry[2]
            direction = {(0, -1): 64, (0, 1): 128, (-1, 0): 32, (1, 0): 16}[dx, dy]
            fixture = True
            native('VarSet', 0x40DC, 8)
            native('DisableWildEncounters', 1)
            ns['set_passability'](dry_only=True)
            warp(*port['start'])
            native('SetPlayerAvatarTransitionFlags', 1)
            step(120)
            fixture = False
            phase = prefix+'-town-to-terminal'
            route_start = len(routes)
            prompt_start = len(ns['surf_prompts'])
            ns['walk'](dry)
            front = ns['assert_foot'](prefix+'-current-dry-arrival')
            ns['walk']((port['interior'], *port['arrival']))
            inside = ns['assert_foot'](prefix+'-current-terminal')
            assert len(ns['surf_prompts']) == prompt_start, 'Town terminal trip used Surf'
            phase = prefix+'-ferry-roundtrip'
            ns['talk_captain']()
            ns['choose'](0)
            ns['choose'](2)
            outward = ns['voyage']('JourneyPalletHarbor', (16, 13))
            picture(prefix+'-pallet-by-ferry')
            ns['talk_captain']()
            ns['choose'](2)
            ns['choose'](['One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven'].index(island))
            # The world ferry returns inside the current terminal. The
            # separate native Seagallop table uses the exterior Atlas arrival.
            returned = ns['voyage'](port['interior'], port['arrival'])
            terminal_return = ns['assert_foot'](prefix+'-world-ferry-terminal-arrival')
            ns['walk'](dry)
            returned_state = ns['assert_foot'](prefix+'-current-dry-return')
            phase = prefix+'-dry-save'
            dry_battery = battery(prefix+'-dry-controller-save')
            phase = prefix+'-surf-departure-and-return'
            before = ns['location'](), ns['position']()
            step(90, direction)
            step(45)
            assert (ns['location'](), ns['position']()) == before, 'Foot entered open water'
            ns['assert_foot']()
            assert native('IsPlayerFacingSurfableFishableWater')
            prompts = len(ns['surf_prompts'])
            ns['set_passability']()
            ns['walk'](wet)
            water_state = ns['assert_surf']()
            assert len(ns['surf_prompts']) > prompts, 'Missing native Surf prompt'
            picture(prefix+'-current-water-arrival')
            water_battery = battery(prefix+'-surf-controller-save')
            ns['walk'](dry)
            step(60)
            reboarded = ns['assert_foot'](prefix+'-reboarded-pier')
            ns['set_passability'](dry_only=True)
            ns['walk']((port['interior'], *port['arrival']))
            ns['assert_foot'](prefix+'-reentered-terminal')
            ns['walk'](tuple(port['start']))
            final = ns['assert_foot'](prefix+'-returned-town')
            assert (final['map'], *final['tile']) == tuple(port['start'])
            cases.append(dict(island=island, town_start=port['start'], terminal=port['interior'],
                dry=list(dry), water=list(wet), front=front, interior=inside, voyages=[outward, returned],
                world_ferry_arrival=terminal_return, current_dry_return=returned_state,
                surf=water_state, reboarded=reboarded, final=final,
                dry_battery=dry_battery, water_battery=water_battery, controlled_steps=len(routes)-route_start,
                town_terminal_trip_dry_only=True, world_ferry_returns_to_current_terminal=True,
                no_midtrip_position_or_mode_writes=True))
            print(island, 'current terminal/ferry/Surf/reboard/town SAVEs PASS', flush=True)
    except BaseException:
        picture('current-seven-ports-failure')
        raise
    finally:
        lib.stop()
        ns['emulator_workspace'].cleanup()
    for row in batteries:
        report = cold_boot(source, library, output/(row['file']+'.cold'), output/row['file'],
                           expected_geometry_version=8, verify_current_map_objects=True)
        state = report['runs'][-1]
        assert tuple(state['field_map']) == tuple(ns['map_id'](row['state']['map']))
        assert state['player_tile'] == row['state']['tile']
        assert state['player_surfing'] == row['state']['surfing']
        row['actual_cold_continue_preserves_map_position_mode'] = True
    assert artifacts == {n: sha(source/n) for n in artifacts}
    report = dict(kind='atlas-seven-current-sevii-ports-native', passed=True, artifact_sha256=artifacts,
        cases=cases, batteries=batteries, controls=controls, queries=queries, captures=captures, route=routes,
        initial_party_progress_and_per_island_start_are_fixtures=True,
        after_departure_controllers_and_readonly_getters_only=True,
        full_seven_coverage=len(cases)==7, final_release_validated=False)
    (output/'seven-current-ports-native.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'library', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--island', action='append')
    args = parser.parse_args()
    run(args.source, args.library, args.output, args.island)
