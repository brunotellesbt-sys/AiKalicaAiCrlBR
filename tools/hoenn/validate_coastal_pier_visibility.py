"""Compare actual avatar pixels on both complete custom quay approaches.

First placements, party/progress and encounter suppression are explicit
fixtures. Thereafter every approach, crossing and Surf transition uses
controller input. This proof is separate from the Sevii perimeter proof.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from coastal_ecology_pier_priority import APPROACHES


ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--library', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--diagnose', action='store_true', help='Collect all pixel failures; still exits nonzero')
    options = parser.parse_args()
    path = ROOT/'tools/hoenn/validate_integrated_piers.py'
    code = path.read_text().split('\nchecks = []\ntry:')[0]
    assert code.count('names = sorted(names)') == 1
    code = code.replace('names = sorted(names)', "names = ['CinnabarIsland_Frlg', 'JourneyCinnabarHarbor', 'PalletTown_Frlg', 'JourneyPalletHarbor']")
    sys.argv = [str(path), '--source', str(options.source), '--library', str(options.library), '--output', str(options.output)]
    ns = {'__file__': str(path), '__name__': 'coastal_pier_visibility_native'}
    exec(compile(code, str(path), 'exec'), ns)
    lib, native, step, walk, warp = (ns[key] for key in ('lib','native','step','walk','warp'))
    initial_sha = hashlib.sha256((options.source/'pokeemerald.gba').read_bytes()).hexdigest()
    failures, approaches, bridge_samples, underpasses, transitions = [], [], [], [], []

    def foot(label, priority=1, direction=None):
        state = ns['player_state']()
        assert not state['surfing'] and state['elevation'] == 3, state
        if state['priority'] != priority and options.diagnose:
            failures.append(dict(map=state['map'],tile=state['tile'],reason='Unexpected native draw priority',
                actual_priority=state['priority'],expected_priority=priority))
        else:
            assert state['priority'] == priority, state
        assert state['sprite_visible'] and state['object_visible'], state
        try:
            state['native_avatar_pixels'] = ns['visible_avatar_pixels']()
        except AssertionError as error:
            if not options.diagnose:
                ns['picture'](label+'-failure')
                raise
            state['native_avatar_pixel_failure'] = str(error)
            failures.append(dict(map=state['map'], tile=state['tile'], reason=str(error)))
        ns['picture'](label)
        state['capture_file'] = label+'.png'
        if direction is not None:
            state['direction'] = direction
        return state

    def dry_paths():
        # A high bridge is water to the Surf planner, but dry to pedestrians.
        for name, valid in ns['full_passable'].items():
            words = ns['blocks'][name][2]
            ns['passable'][name] = {i for i in valid if words[i] >> 12 == 15
                or not ns['water_behaviors'][ns['behaviors'][name][i]]}
        ns['_planned_goal'], ns['_planned_keys'] = None, {}

    def arrive(name, xy):
        walk((name, *xy)); step(60)
        assert (ns['by_location'][ns['location']()], *ns['position']()) == (name, *xy)

    def surfing(label):
        state = ns['assert_surf']()
        ns['picture'](label)
        state['capture_file'] = label+'.png'
        return state

    try:
        native('DisableWildEncounters', 1)
        name = 'CinnabarIsland_Frlg'
        warp(name,11,14);native('SetPlayerAvatarTransitionFlags',1);step(90)
        foot('cinnabar-dry-land-start',2)
        dry_paths()
        for direction, xs in [('outbound',range(11,5,-1)),('return',range(6,12))]:
            for x in xs:
                arrive(name,(x,15))
                bridge_samples.append(foot(f'cinnabar-bridge-foot-{direction}-{x}',direction=direction))
        samples = []
        for direction, route in [
            ('outbound',[(9,16),(9,17),(10,17),(10,16)]),
            ('return',[(10,16),(10,17),(9,17),(9,16)]),
        ]:
            for x,y in route:
                arrive(name,(x,y))
                samples.append(foot(f'cinnabar-approach-{direction}-{x}-{y}',direction=direction))
        approaches.append(dict(map=name,bounds=[9,16,10,17],samples=samples,
            expected_cells=[[x,y] for y in (16,17) for x in (9,10)],both_directions=True))
        # Leave and reboard the complete lower appendage using the native prompt.
        arrive(name,(9,17));ns['set_passability']()
        prompt_before = len(ns['surf_prompts'])
        arrive(name,(9,18));departed=surfing('cinnabar-low-pier-native-surf')
        assert len(ns['surf_prompts']) > prompt_before
        arrive(name,(9,17));reboarded=foot('cinnabar-low-pier-native-reboard')
        transitions.append(dict(map=name,dry=[9,17],water=[9,18],surf_departure=departed,
            reboarded=reboarded,native_surf_prompt=True,native_controller_departure_and_reboard=True))

        name = 'PalletTown_Frlg'
        warp(name,23,26);native('SetPlayerAvatarTransitionFlags',1);step(90)
        dry_paths();samples=[]
        for direction, xs in [('outbound',range(22,10,-1)),('return',range(11,23))]:
            for x in xs:
                arrive(name,(x,26))
                samples.append(foot(f'pallet-approach-{direction}-{x}-26',direction=direction))
        approaches.append(dict(map=name,bounds=[11,26,22,26],samples=samples,
            expected_cells=[[x,26] for x in range(11,23)],both_directions=True))
        for direction, xy, priority in [('outbound',(18,25),1),('outbound',(18,24),2),
                                        ('return',(18,25),1),('return',(18,26),1)]:
            arrive(name,xy)
            bridge_samples.append(foot(f'pallet-bridge-foot-{direction}-{xy[0]}-{xy[1]}',priority,direction))

        for name, start, route in [
            ('CinnabarIsland_Frlg',(16,16),[(16,15)]+[(x,15) for x in range(11,5,-1)]
                +[(x,15) for x in range(6,12)]+[(16,15),(16,16)]),
            ('PalletTown_Frlg',(17,25),[(18,25),(19,25),(18,25),(17,25)]),
        ]:
            ns['set_passability'](water_only=True)
            warp(name,*start);native('SetPlayerAvatarTransitionFlags',8);step(90)
            samples=[surfing(name.lower()+'-underpass-start')]
            for index,xy in enumerate(route):
                arrive(name,xy)
                samples.append(surfing(name.lower()+f'-underpass-{index}'))
            assert ns['position']()==start
            underpasses.append(dict(map=name,start=list(start),route=[list(xy) for xy in route],
                samples=samples,both_directions=True,continuous_native_surf=True,
                full_multilevel_bridge_crossed=True,native_lower_priority2_preserved=True))
        # Pallet's south bank still supports the ordinary native Surf transition.
        ns['set_passability']();arrive('PalletTown_Frlg',(17,26))
        reboarded=foot('pallet-native-surf-reboard')
        prompt_before=len(ns['surf_prompts'])
        arrive('PalletTown_Frlg',(17,25));departed=surfing('pallet-native-surf-departure')
        assert len(ns['surf_prompts']) > prompt_before
        arrive('PalletTown_Frlg',(17,26));returned=foot('pallet-native-surf-return')
        transitions.append(dict(map='PalletTown_Frlg',dry=[17,26],water=[17,25],
            initial_reboarded=reboarded,surf_departure=departed,reboarded=returned,
            native_surf_prompt=True,native_controller_departure_and_reboard=True))
    finally:
        lib.stop()
    assert [row['bounds'] for row in approaches] == [list(row[2]) for row in APPROACHES]
    assert hashlib.sha256((options.source/'pokeemerald.gba').read_bytes()).hexdigest() == initial_sha
    captures=list(ns['captures'].values())
    result=dict(kind='coastal-pier-visibility',passed=not failures,rom_sha256=initial_sha,
        elf_sha256=hashlib.sha256((options.source/'pokeemerald.elf').read_bytes()).hexdigest(),
        compiled_rom=True,native_validation_performed=True,approaches=approaches,
        dry_approach_cells=16,dry_approach_directional_samples=32,
        bridge_foot_samples=bridge_samples,underpasses=underpasses,surf_transitions=transitions,
        captures=captures,pixel_failures=failures,
        all_sixteen_dry_approach_cells_both_directions_verified=not failures,
        full_head_body_feet_actual_vram_scanout_compared=not failures,
        both_existing_lower_surf_routes_preserved=True,
        native_surf_departure_and_reboard_both_ports=True,
        initial_placements_party_and_progress_are_fixtures=True,
        movement_fixture_random_encounters_disabled=True,controller_only_after_initial_placement=True,
        no_midtrip_coordinate_elevation_or_avatar_writes=True)
    (options.output/'coastal-pier-visibility.json').write_text(json.dumps(result,indent=2)+'\n')
    if failures:
        raise AssertionError(('Native approach visibility defects',failures))
    print('Native Cinnabar/Pallet full-avatar visibility passed: 16 cells in both directions; both lower Surf routes',flush=True)


if __name__=='__main__':main()
