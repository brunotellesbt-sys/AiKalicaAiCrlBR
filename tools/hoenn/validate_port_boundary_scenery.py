"""Native controls and exact scanout proof for integrated-port reef repairs."""
import argparse
import hashlib
import json
from collections import deque
from pathlib import Path

from port_boundary_scenery import (BEACH, FIVE, FOUR, PORT_MAPS, REPAIRS,
    SEVEN_FRONT, SMALL, Terrain, boarding_census, census, current_ports)
from validate_coast_scenery_objects import bootstrap
from validate_sevii_route_boundaries_native import observe_cells
from verify_sevii_integrated_piers_update import verify_captures, verify_native_avatar_pixels
from verify_sevii_route_boundaries_native import verify_pixels

ROOT = Path(__file__).resolve().parents[2]
DIRECTIONS = ((1, 0, 16, 32), (-1, 0, 32, 16),
              (0, 1, 128, 64), (0, -1, 64, 128))
# Each target has a real, unobstructed adjacent water tile in the parent.
MOVEMENT_CASES = ((FOUR, (1, 26), (1, 27), 128, 64),
    (FOUR, (2, 26), (2, 27), 128, 64),
    (FOUR, (1, 29), (1, 28), 64, 128),
    (FOUR, (9, 35), (8, 35), 32, 16),
    (FIVE, (5, 13), (5, 14), 128, 64),
    (FIVE, (6, 13), (6, 14), 128, 64),
    (BEACH, (18, 7), (19, 7), 16, 32),
    (BEACH, (18, 8), (19, 8), 16, 32),
    (BEACH, (21, 8), (20, 8), 32, 16))
VIEWS = ((BEACH, (22, 11), ((19, 7), (19, 8), (20, 8))),
    (FOUR, (4, 25), ((1, 27), (2, 27), (1, 28))),
    (FOUR, (10, 37), ((8, 35),)),
    (FIVE, (3, 12), ((5, 14), (6, 14))))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _probe(source, library, output, *, baseline=False):
    output.mkdir(parents=True, exist_ok=True)
    ns = bootstrap(source, library, output, set(PORT_MAPS)|{'JourneySurfLink05200'})
    lib, symbols = ns['lib'], ns['s']
    original = {key:ns[key] for key in ('native', 'step', 'warp', 'script')}
    fixture, phase, depth = True, 'bootstrap', 0
    inputs, queries, fixtures, captures = [], [], [], []
    movements, views, boarding, boundary = [], [], [], []

    def step(frames, key=0):
        if not fixture:
            if inputs and inputs[-1]['case'] == phase and inputs[-1]['key'] == key:
                inputs[-1]['frames'] += frames
            else:
                inputs.append(dict(case=phase, frames=frames, key=key))
        original['step'](frames, key)

    def native(name, *args, **kwargs):
        nonlocal depth
        if not fixture:
            assert name.startswith(('MapGridGet', 'MetatileBehavior_Is')) or name in {
                'GetPlayerFacingDirection', 'IsPlayerFacingSurfableFishableWater',
                'PlayerGetElevation'}, ('Post-placement native mutation', name)
            queries.append(dict(case=phase, function=name, arguments=list(args), read_only=True))
        depth += 1
        try:
            return original['native'](name, *args, **kwargs)
        finally:
            depth -= 1

    def script(*args, **kwargs):
        assert fixture or depth, 'Gameplay script injected after placement'
        return original['script'](*args, **kwargs)

    def warp(*args, **kwargs):
        assert fixture, 'Midtrip placement fixture'
        return original['warp'](*args, **kwargs)

    ns.update(native=native, step=step, script=script, warp=warp,
              walk_transition_pictures=False)

    def place(name, point, label, surfing=True):
        nonlocal fixture, phase
        fixture, phase = True, label
        original['warp'](name, *point)
        step(100)
        if bool(lib.read8(symbols['gPlayerAvatar']) & 8) != surfing:
            original['native']('SetPlayerAvatarTransitionFlags', 8 if surfing else 1)
            step(100)
        original['native']('DisableWildEncounters', 1)
        step(120)
        fixture = False
        state = ns['player_state']()
        assert [state['map'], *state['tile']] == [name, *point] and state['surfing'] is surfing, state
        fixtures.append(dict(case=label, map=name, cell=list(point), surfing=surfing))

    def capture(label):
        ns['picture'](label)
        row = dict(file=label+'.png', sha256=digest(output/(label+'.png')))
        captures.append(row)
        return row

    def move_to(point, key, *, limit=100):
        for _ in range(limit):
            step(1, key)
            if ns['position']() == tuple(point):
                break
        step(80)
        return ns['player_state']()

    try:
        for number, (name, start, target, key, reverse) in enumerate(MOVEMENT_CASES):
            label = 'reef-movement-'+str(number+1)
            place(name, start, label)
            before = ns['assert_surf']()
            collision = native('MapGridGetCollisionAt', target[0]+7, target[1]+7)
            should_enter = name == FOUR or (baseline and name == FIVE)
            after = move_to(target, key)
            assert after['tile'] == list(target if should_enter else start), (label, before, after)
            assert collision == (0 if should_enter else 1), (label, collision)
            returned = move_to(start, reverse) if should_enter else after
            assert returned['tile'] == list(start) and returned['surfing'], (label, returned)
            movements.append(dict(case=label, map=name, target=list(target),
                before=before, attempted=after, returned=returned, native_collision=collision,
                entered_target=should_enter, native_controller_return=True, capture=capture(label)))

        for number, (name, point, cells) in enumerate(VIEWS):
            label = 'whole-reef-art-'+str(number+1)
            place(name, point, label)
            width, height, words = ns['blocks'][name]
            requested = [(x, y, words[y*width+x] & 1023) for x, y in cells]
            pixels = observe_cells(ns, requested)
            views.append(dict(case=label, map=name, point=list(point), pixels=pixels,
                              capture=capture(label)))

        if not baseline:
            for port in current_ports(source):
                label = 'boarding-'+port['island'].lower()
                dry, water = (tuple(port['boarding'][key]) for key in ('dry', 'water'))
                place(dry[0], dry[1:], label, surfing=False)
                before = ns['assert_foot']()
                dry_capture = capture(label+'-dry')
                step(90, port['boarding']['outward_key']); step(45)
                assert ns['player_state']()['tile'] == list(dry[1:])
                assert native('IsPlayerFacingSurfableFishableWater'), (label, 'Surf prompt unavailable')
                prompt_before = len(ns['surf_prompts'])
                ns['set_passability']()
                ns['walk'](water)
                water_state = ns['assert_surf']()
                assert len(ns['surf_prompts']) == prompt_before+1, (label, ns['surf_prompts'])
                water_capture = capture(label+'-surf')
                ns['set_passability'](water_only=True)
                if port['island']=='Six':
                    cruise=('JourneySurfLink05200',12,10)
                else:
                    width,height,words=ns['blocks'][water[0]]
                    queue=deque([(water[1],water[2],0)]);seen={(water[1],water[2])};choices=[]
                    while queue:
                        x,y,distance=queue.popleft()
                        if distance>=6:choices.append((distance,y,x));continue
                        for dx,dy,key,reverse in DIRECTIONS:
                            xx,yy=x+dx,y+dy;index=yy*width+xx
                            if (0<=xx<width and 0<=yy<height and (xx,yy) not in seen
                                    and index in ns['passable'][water[0]]):
                                seen.add((xx,yy));queue.append((xx,yy,distance+1))
                    assert choices, (label,'No six-tile offshore cruise')
                    distance,y,x=min(choices)
                    cruise=(water[0],x,y)
                ns['walk'](cruise);step(80)
                cruise_state=ns['assert_surf']()
                assert [cruise_state['map'],*cruise_state['tile']]==list(cruise)
                cruise_capture=capture(label+'-offshore')
                ns['walk'](water);step(80)
                return_water=ns['assert_surf']()
                assert return_water['tile']==list(water[1:])
                ns['set_passability']()
                ns['walk'](dry); step(80)
                returned = ns['assert_foot']()
                assert returned['tile'] == list(dry[1:])
                boarding.append(dict(island=port['island'], dry=list(dry), water=list(water),
                    before=before, water_state=water_state, returned=returned,
                    cruise=list(cruise),cruise_state=cruise_state,return_water=return_water,
                    offshore_controller_cruise_and_return=True,cruise_capture=cruise_capture,
                    native_surf_prompt=True, controllers_only_roundtrip=True,
                    dry_capture=dry_capture, water_capture=water_capture,
                    return_capture=capture(label+'-return')))

            terrain = Terrain(source)
            for port in current_ports(source):
                name, bx, by = port['boarding']['water']
                layout, words = terrain.layout(name), terrain.grid(name)
                width, height = layout['width'], layout['height']
                openings = {(x,y) for x,y,d,xx,yy in terrain.perimeter(name)
                            if terrain.neighbor(name,xx,yy,d) is not None}
                choices = []
                for x,y,d,xx,yy in terrain.perimeter(name):
                    if (x,y) in openings or words[y*width+x]&1023 != SMALL:
                        continue
                    for dx,dy,key,reverse in DIRECTIONS:
                        start, retreat = (x-dx,y-dy), (x-2*dx,y-2*dy)
                        if all(0<=px<width and 0<=py<height and not words[py*width+px]&0xC00
                               and terrain.water(name,words[py*width+px]) for px,py in (start,retreat)):
                            choices.append((abs(x-bx)+abs(y-by),x,y,start,retreat,key,reverse))
                assert choices, ('No actual outer-limit native approach', port['island'], name)
                _,x,y,start,retreat,key,reverse = min(choices)
                label = 'outer-limit-'+port['island'].lower()
                place(name,start,label)
                before = ns['assert_surf']()
                after = move_to((x,y),key)
                assert after['tile'] == list(start) and after['map'] == name, (label,after)
                collision = native('MapGridGetCollisionAt',x+7,y+7)
                assert collision == 1
                returned = move_to(retreat,reverse)
                assert returned['tile'] == list(retreat) and returned['surfing'], (label,returned)
                # Two tiles of clearance keep all four BG quadrants outside
                # the Surf blob's hardware OAM bounding rectangle.
                pixels = observe_cells(ns,[(x,y,SMALL)])
                boundary.append(dict(island=port['island'], map=name, cell=[x,y],
                    start=list(start), retreat=list(retreat), before=before, attempted=after,
                    returned=returned, native_collision=collision, pixels=pixels,
                    controller_bump_and_return=True, capture=capture(label)))

            # Both ends of the new Seven boundary have water to their west.
            # The north/south neighbors are legitimate wood/land, so test the
            # two ends from water and navigate around the unaltered boat.
            for y in (2,8):
                label = 'seven-new-limit-'+str(y)
                place(SEVEN_FRONT,(22,y),label)
                before=ns['assert_surf'](); after=move_to((23,y),16)
                assert after['tile']==[22,y]
                ns['set_passability'](water_only=True)
                ns['walk']((SEVEN_FRONT,22,8 if y==2 else 2)); step(80)
                returned=ns['assert_surf']()
                boundary.append(dict(case=label,map=SEVEN_FRONT,cell=[23,y],before=before,
                    attempted=after,returned=returned,controllers_only_inner_water_route=True,
                    capture=capture(label)))
    finally:
        lib.stop()
    return dict(kind='port-boundary-scenery-native', passed=True,
        rom_sha256=digest(source/'pokeemerald.gba'), elf_sha256=digest(source/'pokeemerald.elf'),
        expected_broken_baseline=baseline, source_census=boarding_census(source),
        fixtures=fixtures, inputs=inputs, read_only_queries=queries, captures=captures,
        movement_cases=movements, whole_object_art=views, boarding=boarding, outer_limits=boundary,
        native_validation_performed=True, initial_party_progress_and_placement_are_fixtures=True,
        post_placement_movement_controllers_only=True, no_midtrip_map_grid_or_avatar_writes=True,
        exact_bg_oam_vram_palette_and_scanout_verified=True, full_campaign_playthrough=False)


def verify_report(report, output, expected_rom_sha256=None):
    output=Path(output)
    assert report['kind']=='port-boundary-scenery-native' and report['passed'] is True
    if expected_rom_sha256 is not None: assert report['rom_sha256']==expected_rom_sha256
    for key in ('native_validation_performed','initial_party_progress_and_placement_are_fixtures',
                'post_placement_movement_controllers_only','no_midtrip_map_grid_or_avatar_writes',
                'exact_bg_oam_vram_palette_and_scanout_verified'):
        assert report[key] is True
    images=verify_captures(report['captures'],output)
    captures={row['file']:row['sha256'] for row in report['captures']}
    assert len(captures)==len(report['captures'])
    baseline=report['expected_broken_baseline']
    assert len(report['movement_cases'])==9 and len(report['whole_object_art'])==4
    assert len(report['source_census']['all_port_maps']['incomplete'])==(4 if baseline else 0)
    for row,expected in zip(report['movement_cases'],MOVEMENT_CASES):
        name,start,target,key,reverse=expected
        entered=name==FOUR or (baseline and name==FIVE)
        assert row['map']==name and row['target']==list(target) and row['entered_target'] is entered
        assert row['before']['tile']==row['returned']['tile']==list(start)
        assert row['attempted']['tile']==list(target if entered else start)
        assert row['native_collision']==(0 if entered else 1) and row['native_controller_return'] is True
    for row in report['whole_object_art']+ [r for r in report['outer_limits'] if 'pixels' in r]:
        info=row['pixels']
        for cell in info['cells']:
            one=dict(info,cells=[cell])
            verify_pixels(one,row['capture'],captures,images,cell['cell'],cell['expected_metatile'])
    assert len(report['boarding'])==(0 if baseline else 7)
    if not baseline:
        assert {row['island'] for row in report['boarding']}=={'One','Two','Three','Four','Five','Six','Seven'}
        assert len(report['outer_limits'])==9
        for row in report['boarding']:
            assert row['native_surf_prompt'] is row['controllers_only_roundtrip'] is True
            for key,attachment in (('before','dry_capture'),('returned','return_capture')):
                state=row[key]
                assert state['surfing'] is False and state['elevation']==3
                verify_native_avatar_pixels(state['native_avatar_pixels'],images[row[attachment]['file']])
            assert row['water_state']['surfing'] is True and row['water_state']['elevation']==1
            assert row['offshore_controller_cruise_and_return'] is True
            assert [row['cruise_state']['map'],*row['cruise_state']['tile']]==row['cruise']
            assert row['return_water']['tile']==row['water'][1:]
        six=next(row for row in report['boarding'] if row['island']=='Six')
        assert six['cruise']==['JourneySurfLink05200',12,10]
    if 'parent_reproduction' in report:
        verify_report(report['parent_reproduction'],output/'parent')


def run(source, library, output, parent_source=None):
    source,library,output=[Path(p).resolve() for p in (source,library,output)]
    sha,elfsha=digest(source/'pokeemerald.gba'),digest(source/'pokeemerald.elf')
    report=_probe(source,library,output)
    if parent_source is not None:
        baseline=_probe(Path(parent_source).resolve(),library,output/'parent',baseline=True)
        (output/'parent/ports.json').write_text(json.dumps(baseline,indent=2)+'\n')
        report['parent_reproduction']=baseline
        report['components']=[dict(file='parent/ports.json',sha256=digest(output/'parent/ports.json'))]
    assert sha==digest(source/'pokeemerald.gba') and elfsha==digest(source/'pokeemerald.elf')
    verify_report(report,output,sha)
    (output/'ports.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--library',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--parent-source',type=Path)
    parser.add_argument('--baseline-only',action='store_true')
    args=parser.parse_args()
    if args.baseline_only:
        result=_probe(args.source.resolve(),args.library.resolve(),args.output.resolve(),baseline=True)
        verify_report(result,args.output)
        (args.output/'ports.json').write_text(json.dumps(result,indent=2)+'\n')
    else:
        run(args.source,args.library,args.output,args.parent_source)
