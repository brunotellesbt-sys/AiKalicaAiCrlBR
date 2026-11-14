"""Drive Birth's repaired landing in a frozen ROM; never certify a release.

Initial placement, progress, party and encounter suppression are fixtures.
After placement, travel uses controls; the private query trampoline only runs
read-only getters. A smoke-build result remains explicitly diagnostic and must
be repeated on the final five-edition source/ELF/ROM where applicable.
"""
import argparse
import hashlib
import json
from pathlib import Path

from validate_coast_scenery_objects import bootstrap

OUTSIDE = 'BirthIsland_Exterior_Frlg'
INSIDE = 'BirthIsland_Harbor_Frlg'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(source, library, output):
    source, library, output = map(lambda p: Path(p).resolve(), (source, library, output))
    output.mkdir(parents=True, exist_ok=True)
    frozen = {name: digest(source/name) for name in ('pokeemerald.gba', 'pokeemerald.elf')}
    ns = bootstrap(source, library, output, [OUTSIDE, INSIDE])
    original = {key: ns[key] for key in ('step', 'native', 'script', 'warp', 'picture')}
    fixture, depth, phase = True, 0, 'placement'
    controls, queries, route, states, captures = [], [], [], [], []

    def step(frames, key=0):
        if not fixture and not depth:
            if controls and controls[-1]['phase'] == phase and controls[-1]['key'] == key:
                controls[-1]['frames'] += frames
            else:
                controls.append(dict(phase=phase, frames=frames, key=key))
        original['step'](frames, key)

    def native(name, *args, **kwargs):
        nonlocal depth
        if not fixture:
            assert name.startswith(('MapGridGet', 'MetatileBehavior_Is')) or name in {
                'GetPlayerFacingDirection', 'IsPlayerFacingSurfableFishableWater',
                'PlayerGetElevation'}, ('Mutable native call after placement', name)
            queries.append(dict(phase=phase, function=name, arguments=list(args)))
        depth += 1
        try:
            return original['native'](name, *args, **kwargs)
        finally:
            depth -= 1

    def script(*args, **kwargs):
        assert fixture or depth, 'Gameplay script injection after placement'
        return original['script'](*args, **kwargs)

    def warp(*args, **kwargs):
        assert fixture, 'Warp fixture used during controller trip'
        return original['warp'](*args, **kwargs)

    def picture(label):
        original['picture'](label)
        row = dict(file=label+'.png', sha256=digest(output/(label+'.png')))
        captures.append(row)
        return row

    def observe(before, after):
        route.append(dict(phase=phase, before=list(before), after=list(after)))

    ns.update(step=step, native=native, script=script, warp=warp, picture=picture,
              walk_observer=observe, walk_transition_pictures=False, walk_max_ticks=600)

    def foot(label):
        state = ns['assert_foot'](label)
        states.append(dict(phase=phase, kind='foot', **state))
        return state

    def surf(label):
        state = ns['assert_surf']()
        picture(label)
        states.append(dict(phase=phase, kind='surf', **state))
        return state

    try:
        # Every gameplay fixture ends here; no midtrip position/mode writes.
        warp(OUTSIDE, 15, 23)
        native('SetPlayerAvatarTransitionFlags', 1)
        native('DisableWildEncounters', 1)
        step(90)
        assert ns['by_location'][ns['location']()] == OUTSIDE and ns['position']() == (15, 23)
        fixture = False
        phase = 'wooden-tip-and-side-block'
        ns['walk']((OUTSIDE, 15, 24))
        foot('birth-wood-tip')
        ns['walk']((OUTSIDE, 16, 24))
        step(90, 16)  # No A: a pedestrian cannot walk off into the ocean.
        step(30)
        blocked = foot('birth-wood-side-blocked')
        assert blocked['tile'] == [16, 24]
        phase = 'surf-departure'
        ns['walk']((OUTSIDE, 18, 26))
        surf('birth-water-beside-native-dock')
        step(90, 32)
        step(30)
        blocked_body = surf('birth-dock-body-blocked')
        assert blocked_body['tile'] == [18, 26]
        phase = 'return-from-surf-to-warp'
        ns['walk']((INSIDE, 8, 3))
        foot('birth-harbor-arrival')
        phase = 'harbor-to-island-return'
        ns['walk']((OUTSIDE, 15, 23))
        foot('birth-island-returned')
        assert any(row['before'][0] == OUTSIDE and row['after'][0] == INSIDE for row in route)
        assert any(row['before'][0] == INSIDE and row['after'][0] == OUTSIDE for row in route)
        assert frozen == {name: digest(source/name) for name in frozen}
        report = dict(kind='atlas-birth-native-component', passed=True,
                      rom_sha256=frozen['pokeemerald.gba'], elf_sha256=frozen['pokeemerald.elf'],
                      diagnostic_build=(source/'.journey-atlas-stage-smoke').exists(),
                      final_release_validated=False,
                      initial_party_progress_encounters_and_placement_are_fixtures=True,
                      after_placement_movement_controllers_only=True,
                      private_read_only_query_trampoline_declared=True,
                      native_avatar_pixels_checked=True,
                      wood_side_blocks_pedestrian=True, surf_departure_and_return=True,
                      dock_body_blocks_surf=True,
                      harbor_roundtrip=True, controls=controls, queries=queries,
                      route=route, states=states, captures=captures,
                      frozen_rom_and_elf_unchanged=True)
        (output/'birth-native.json').write_text(json.dumps(report, indent=2)+'\n')
        return report
    except BaseException:
        picture('birth-native-failure')
        raise
    finally:
        ns['lib'].stop()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--library', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = run(args.source, args.library, args.output)
    print(json.dumps({key: report[key] for key in ('kind', 'passed', 'rom_sha256', 'diagnostic_build')}, indent=2))
