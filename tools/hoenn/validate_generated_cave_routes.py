"""Walk generated cave doorways, NPC approaches and returns in native mGBA.

Initial placement, party, Surf mode and already-defeated Rocket trainers are
fixtures. Subsequent travel uses controller input. Retired-lodge checks also
save and Continue inside the old room before walking out of its real door.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[2]
bootstrap = (ROOT/'tools/hoenn/validate_sootopolis_harbor.py').read_text().split('\n# Disable Sootopolis')[0]
exec(compile(bootstrap, __file__, 'exec'))

captures = []
native_picture = picture


def picture(name):
    native_picture(name)
    path = args.output / (name + '.png')
    # A planner diagnostic can reuse its filename for another NPC approach;
    # bind the final file once rather than retaining stale hashes of it.
    captures[:] = [row for row in captures if row['file'] != path.name]
    captures.append(dict(file=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest()))


def finish(limit=300):
    for _ in range(limit):
        if idle(): return
        press(1)
    picture('generated-cave-dialogue-stuck')
    raise AssertionError(('Field controls did not release', location(), position()))


all_maps = {}
for path in (source/'data/maps').glob('*/map.json'):
    mapping = json.loads(path.read_text())
    if 'layout' in mapping:
        all_maps[path.parent.name] = mapping
all_by_id = {row['id']: name for name, row in all_maps.items()}
originals = json.loads((source/'.source-acquired.json').read_text())['sha256']
caves = sorted(name for name, row in all_maps.items()
               if row.get('map_type') == 'MAP_TYPE_UNDERGROUND'
               and f'data/maps/{name}/map.json' not in originals
               and name != 'JourneyGalacticHall')
assert len(caves) == 26
incoming = {}
for cave in caves:
    candidates = [(name, w) for name, row in all_maps.items()
                  for w in row.get('warp_events', [])
                  if w['dest_map'] == all_maps[cave]['id']]
    # Prefer its direct exterior rather than a secondary cave's return warp.
    incoming[cave] = min(candidates, key=lambda item: (item[0] in caves, item[0]))
lodges = [f'Journey{island}IslandHarborPortLodge'
          for island in ('One','Two','Three','Four','Five','Six','Seven')]
dive_sites = [site for site in json.loads((source/'.journey-sanctuaries').read_text())['sites']
              if site['access'] == 'dive']
assert len(dive_sites) == 5
lodge_fixed = all(all_maps[all_by_id[all_maps[n]['warp_events'][0]['dest_map']]]
                  ['warp_events'] for n in lodges)
names = list(dict.fromkeys(caves + [p for p, _ in incoming.values()] +
                          ['NavelRock_Exterior_Frlg', 'NavelRock_Harbor_Frlg', 'NavelRock_1F_Frlg'] +
                          [n for site in dive_sites for n in
                           (site['surface'], 'JourneyDepth'+site['theme'])] +
                          (lodges + [all_by_id[all_maps[n]['warp_events'][0]['dest_map']]
                                     for n in lodges] if lodge_fixed else [])))
allowed = set()
walk_prefix = 'generated-cave'
walk_max_ticks = 1800
walk_transition_pictures = False
exec(compile((ROOT/'tools/hoenn/native_water_walk.py').read_text(), __file__, 'exec'))
# Movement is the subject of this fixture, rather than replaying these two
# previously completed Rocket episodes and their battles.
stories = json.loads((source/'.journey-team-stories').read_text())
for trainer in stories['trainers']:
    if trainer['map'].startswith('JourneyRocketBase'):
        native('FlagSet', 0x500 + trainer['id'])
assert native('ScriptGiveMon', 260, 50, 0) == 0
native('ScriptSetMonMoveSlot', 0, 57, 0)
native('ScriptSetMonMoveSlot', 0, 291, 1)
native('DisableWildEncounters', 1)
checks, save_checks, dive_checks, navel_checks = [], [], [], []
only = os.environ.get('GENERATED_CAVE_ONLY')


def free_near(name, anchor, *, exclude_objects=True):
    width, height, words = blocks[name]
    objects = {(o['x'], o['y']) for o in maps[name].get('object_events', [])}
    return min(((abs(x-anchor[0])+abs(y-anchor[1]), y, x)
                for y in range(height) for x in range(width)
                if y*width+x in passable[name] and (x,y) not in warps[name]
                and (not exclude_objects or (x,y) not in objects)), default=None)


def water_change(target, emerge=False):
    """Use the real field prompt; no direct field-effect or warp invocation."""
    assert native('TrySetDiveWarp') == (1 if emerge else 2)
    if emerge:
        press(2)
    for _ in range(160):
        press(1)
        if location() == map_id(target):
            break
    step(120)
    finish()
    assert location() == map_id(target), (target, location(), position())


for cave in caves:
    if only and cave != only: continue
    parent, entrance = incoming[cave]
    parent_width, _, _ = blocks[parent]
    _, sy, sx = free_near(parent, (entrance['x'], entrance['y']+1))
    start = (sx, sy)
    warp(parent, *start)
    mode = 16 if maps[parent]['map_type'] == 'MAP_TYPE_UNDERWATER' else (
        8 if water_behaviors[behaviors[parent][sy*parent_width+sx]] else 1)
    native('SetPlayerAvatarTransitionFlags', mode)
    step(30)
    refresh_loaded_warp_tiles()
    destination = maps[cave]['warp_events'][int(entrance['dest_warp_id'])]
    # Pick the interior side of a directional staircase. Rocket's northbound
    # exit lands the arriving player below (3,3); targeting (3,2) walks back
    # onto that exit instead of testing the room the player actually enters.
    dw = blocks[cave][0]
    exit_behavior = behaviors[cave][destination['y']*dw+destination['x']]
    exit_key = arrows[exit_behavior]
    default_side = (0,1) if native('MetatileBehavior_IsNonAnimDoor', exit_behavior) else (0,-1)
    dx, dy = {64:(0,1), 128:(0,-1), 16:(-1,0), 32:(1,0)}.get(exit_key,default_side)
    _, gy, gx = free_near(cave, (destination['x']+dx, destination['y']+dy))
    before_walk = walked
    before_transitions = len(transitions)
    walk((cave, gx, gy))
    assert location() == map_id(cave)
    refresh_loaded_warp_tiles()
    npc_approaches = []
    for index, obj in enumerate(maps[cave]['object_events'], 1):
        if obj['script'] in ('0', '0x0'):
            continue
        # Reach the NPC from any actual adjacent ordinary/Surf tile. Do not
        # interact with a legendary or award a synthetic capture.
        width, height, _ = blocks[cave]
        choices = [(x,y) for x,y in ((obj['x']-1,obj['y']), (obj['x']+1,obj['y']),
                                     (obj['x'],obj['y']-1), (obj['x'],obj['y']+1))
                   if 0 <= x < width and 0 <= y < height and y*width+x in passable[cave]
                   and (x,y) not in warps[cave]]
        assert choices, (cave, index)
        errors = []
        for point in sorted(choices, key=lambda p: abs(p[0]-position()[0])+abs(p[1]-position()[1])):
            try:
                walk((cave, *point))
                break
            except AssertionError as error:
                if str(error).startswith("('No native route'"):
                    errors.append(str(error))
                    continue
                raise
        else:
            raise AssertionError((cave, index, 'No native NPC approach', errors))
        npc_approaches.append(dict(local_index=index, object_position=[obj['x'],obj['y']],
                                   player_position=list(position()),
                                   mode=lib.read8(s['gPlayerAvatar']) & 25))
    picture(cave+'-native-approaches')
    walk((parent, *start))
    assert location() == map_id(parent) and position() == start
    checks.append(dict(map=cave, exterior=parent, initial_position=list(start),
                       initial_mode_fixture=mode, controller_entry_and_return=True,
                       npc_approaches=npc_approaches, walked_tiles=walked-before_walk,
                       transitions=transitions[before_transitions:]))
    (args.output/'generated-cave-routes-progress.json').write_text(json.dumps(checks,indent=2)+'\n')
    print('Generated cave entered, NPCs approached and returned:', cave, flush=True)

if not only and lodge_fixed:
    for lodge in lodges:
        warp(lodge, 4, 6)
        native('SetPlayerAvatarTransitionFlags', 1)
        step(30)
        assert native('TrySavingData', 0, max_frames=6000) == 1
        assert native('LoadGameSave', 0, max_frames=6000) == 1
        lib.write32(s['gMain']+4, s['CB2_ContinueSavedGame'] | 1)
        step(1500)
        finish()
        assert location() == map_id(lodge) and position() == (4,6)
        endpoint = maps[lodge]['warp_events'][0]
        target = all_by_id[endpoint['dest_map']]
        width, _, _ = blocks[target]
        target_warp = maps[target]['warp_events'][int(endpoint['dest_warp_id'])]
        _, y, x = free_near(target, (target_warp['x'], target_warp['y']-1))
        walk((target,x,y))
        assert location() == map_id(target)
        assert not lib.read8(s['gPlayerAvatar']) & 8
        picture(lodge+'-saved-room-exit')
        save_checks.append(dict(map=lodge, native_save_continue=True,
                               controller_exit=True, destination=target,
                               landing=list(position()), mode=lib.read8(s['gPlayerAvatar']) & 25))
        print('Retired lodge save/Continue and exit:', lodge, flush=True)

if not only:
    for site in dive_sites:
        surface, depth, cave = site['surface'], 'JourneyDepth'+site['theme'], site['map']
        cx, cy = site['entry']
        start = (cx+1, cy+1)
        warp(surface, *start)  # One declared surface placement per site.
        native('SetPlayerAvatarTransitionFlags', 8)
        step(30)
        assert native('MetatileBehavior_IsDiveable',
                      native('MapGridGetMetatileBehaviorAt', start[0]+7, start[1]+7))
        entry_steps, entry_transitions = walked, len(transitions)
        water_change(depth)
        assert position() == start
        assert lib.read8(s['gPlayerAvatar']) & 25 == 16
        picture(depth+'-native-dive-arrival')
        walk((cave, 14, 17))
        assert not lib.read8(s['gPlayerAvatar']) & 24
        walk((depth, *start))
        assert lib.read8(s['gPlayerAvatar']) & 25 == 16
        picture(depth+'-native-cave-return')
        water_change(surface, emerge=True)
        assert position() == start
        assert lib.read8(s['gPlayerAvatar']) & 25 == 8
        dive_checks.append(dict(surface=surface, depth=depth, cave=cave,
                                initial_position=list(start), returned_position=list(position()),
                                native_dive_and_emerge_prompts=True,
                                controller_cave_entry_and_return=True,
                                native_underwater_surf_and_walking_modes=True,
                                walked_tiles=walked-entry_steps,
                                transitions=transitions[entry_transitions:]))
        print('Native Dive, cave entry/return and emerge:', depth, flush=True)
    assert len(checks) == 26 and len(save_checks) == 7 and len(dive_checks) == 5
    harbor = 'NavelRock_Harbor_Frlg'
    warp(harbor, 8, 4)
    native('SetPlayerAvatarTransitionFlags', 1)
    step(30)
    start_steps = walked
    walk(('NavelRock_1F_Frlg', 8, 22))
    assert lib.read8(s['gPlayerAvatar']) & 25 == 1
    picture('navel-cave-native-entry')
    walk((harbor, 7, 5))
    assert lib.read8(s['gPlayerAvatar']) & 25 == 1
    picture('navel-harbor-native-return')
    walk((harbor, 6, 7))
    assert lib.read8(s['gPlayerAvatar']) & 25 == 8
    picture('navel-pier-native-surf-departure')
    walk((harbor, 7, 5))
    assert lib.read8(s['gPlayerAvatar']) & 25 == 1
    picture('navel-pier-native-surf-return')
    navel_checks.append(dict(harbor=harbor, cave='NavelRock_1F_Frlg',
                             initial_position=[8,4], final_position=list(position()),
                             controller_cave_entry_and_return=True,
                             controller_surf_departure_and_dry_pier_return=True,
                             walked_tiles=walked-start_steps))
    print('Navel Rock cave, exterior, dry pier and Surf roundtrip passed', flush=True)

lib.stop()
(args.output/'generated-cave-routes.json').write_text(json.dumps(dict(
    passed=True, kind='generated-cave-routes',
    rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
    caves=checks, retired_lodge_save_continue=save_checks,
    dive_roundtrips=dive_checks, all_cases_executed=not bool(only),
    navel_rock_roundtrip=navel_checks,
    retired_lodge_exits_fixed_in_selected_source=lodge_fixed,
    npc_approaches=sum(len(c['npc_approaches']) for c in checks),
    initial_party_positions_modes_and_defeated_rocket_trainers_are_fixtures=True,
    no_coordinate_writes_or_internal_warps_during_routes=True,
    wild_encounters_disabled=True, battles_and_capture_rules_validated=False,
    galactic_story_barriers_have_separate_validator=True,
    captures=captures), indent=2)+'\n')
