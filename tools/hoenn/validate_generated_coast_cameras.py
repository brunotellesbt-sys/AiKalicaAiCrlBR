"""Prove two scoped ocean aprons against layer 170 with native controllers."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import generated_area_review_contract as contract
from generated_coast_cameras import (REPRO_CASES, CONTROL_CASES, SCOPED_MAPS,
    OPENING_MAP, OPENING_NEIGHBOR, seven_east_openings)
from marine_corner_coherence import Source
from validate_sevii_route_boundaries_native import observe_cells
from verify_sevii_route_boundaries_native import verify_pixels
from verify_sevii_integrated_piers_update import verify_captures

ROOT = Path(__file__).resolve().parents[2]
KEY = {'left': 32, 'right': 16, 'up': 64, 'down': 128}
OPPOSITE = {'left': 'right', 'right': 'left', 'up': 'down', 'down': 'up'}
CASES = REPRO_CASES+CONTROL_CASES
BUMPS = [dict(label='sea02-undefined-north', map=SCOPED_MAPS[0], player=[20,0],
              direction='up', cell=[20,-1], expected_metatile=0x243),
         dict(label='fill21-undefined-west', map=SCOPED_MAPS[1], player=[0,47],
              direction='left', cell=[-1,47], expected_metatile=0x12B)]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_inputs(source):
    inputs = Source(source)
    names = {row['map'] for row in CASES}|{row['neighbor'] for row in CASES}
    names.update((OPENING_MAP, OPENING_NEIGHBOR))
    paths = {'src/fieldmap.c'}
    for name in names:
        layout = inputs.layout(name)
        paths.update((f'data/maps/{name}/map.json', layout['blockdata_filepath'], layout['border_filepath']))
    return {name:digest(Path(source)/name) for name in sorted(paths)}


def _run(source, library, output, *, baseline):
    source, library, output = [Path(p).resolve() for p in (source,library,output)]
    output.mkdir(parents=True, exist_ok=True)
    romsha, elfsha = [digest(source/name) for name in ('pokeemerald.gba','pokeemerald.elf')]
    if baseline:
        assert (romsha,elfsha) == (contract.PARENT_ROM_SHA256,contract.PARENT_ELF_SHA256)
    initial_inputs = source_inputs(source)
    openings = seven_east_openings(Source(source))
    assert [(r['neighbor'],r['player'],r['target']) for r in openings] == [(OPENING_NEIGHBOR,[16,y],[0,y]) for y in range(1,12)]
    bootstrap = ROOT/'tools/hoenn/validate_abilities.py'
    code = bootstrap.read_text().split('\nability_field,')[0]
    argv = sys.argv
    ns = {'__file__':str(bootstrap),'__name__':'generated_coast_camera_native'}
    try:
        sys.argv = [str(bootstrap),'--source',str(source),'--library',str(library),'--output',str(output)]
        exec(compile(code,str(bootstrap),'exec'),ns)
    finally:
        sys.argv = argv
    lib, original_native, original_step, original_warp, original_script = [ns[k] for k in ('lib','native','step','warp','script')]
    ns['maps'] = {p.parent.name:json.loads(p.read_bytes()) for p in (source/'data/maps').glob('*/map.json')}
    ns['by_location'] = {(g,i):n for g,label in enumerate(ns['groups']['group_order']) for i,n in enumerate(ns['groups'][label])}
    captures, fixtures, controls, queries, cases, rounds, bumps = [],[],[],[],[],[],[]
    fixture, depth, label = True, 0, 'bootstrap'

    def native(name, *values, **kwargs):
        nonlocal depth
        if not fixture:
            assert name.startswith('MapGridGet') or name == 'GetMapBorderIdAt', ('Forbidden midtrip call',name)
            queries.append(dict(label=label,function=name,arguments=list(values)))
        depth += 1
        try:
            return original_native(name,*values,**kwargs)
        finally:
            depth -= 1

    def script(*values, **kwargs):
        assert fixture or depth, 'Gameplay script injected after placement'
        return original_script(*values, **kwargs)

    def warp(*values, **kwargs):
        assert fixture, 'Midtrip placement attempted'
        return original_warp(*values, **kwargs)

    def step(count, key=0):
        if not fixture and not depth and key:
            if controls and controls[-1]['label'] == label and controls[-1]['key'] == key:
                controls[-1]['frames'] += count
            else:
                controls.append(dict(label=label,key=key,frames=count))
        original_step(count,key)

    ns.update(native=native,script=script,warp=warp,step=step)

    def state():
        return dict(map=ns['by_location'][ns['location']()],tile=list(ns['position']()),
                    surfing=bool(lib.read8(ns['s']['gPlayerAvatar']) & 8))

    def place(name, player, case_label):
        nonlocal fixture,label
        fixture, label = True, case_label
        warp(name,*player)
        step(60)
        if not state()['surfing']:
            original_native('SetPlayerAvatarTransitionFlags',8)
            step(60)
        assert state() == dict(map=name,tile=list(player),surfing=True), state()
        fixtures.append(dict(label=label,**state()))
        fixture = False

    def cross(direction, neighbor, target):
        for frame in range(240):
            step(1,KEY[direction])
            if ns['location']() == ns['map_id'](neighbor):
                break
        else:
            raise AssertionError(('Controller seam blocked',state(),direction,neighbor))
        step(30)
        assert state() == dict(map=neighbor,tile=list(target),surfing=True), state()

    def grid(cell):
        x,y = cell
        backup = ns['s']['gBackupMapLayout']
        w,h,address = [lib.read32(backup+4*i) for i in range(3)]
        gx,gy = x+7,y+7
        assert 0 <= gx < w and 0 <= gy < h
        return dict(cell=list(cell),block=lib.read16(address+2*(gy*w+gx)),
            metatile=native('MapGridGetMetatileIdAt',gx,gy),
            collision=native('MapGridGetCollisionAt',gx,gy),
            elevation=native('MapGridGetElevationAt',gx,gy),border_id=native('GetMapBorderIdAt',gx,gy))

    def picture(name):
        ns['picture'](name)
        row = dict(file=name+'.png',sha256=digest(output/(name+'.png')))
        captures.append(row)
        return row

    def view(cell, name, expected):
        observed = grid(cell)
        assert observed['metatile'] == expected, (state(),observed,expected)
        pixels = observe_cells(ns,[(*cell,expected)])
        return dict(state=state(),grid=observed,pixels=pixels,capture=picture(name))

    try:
        original_native('DisableWildEncounters',1)
        for case in CASES:
            place(case['map'],case['player'],case['label'])
            before_expected = 0x243 if baseline else case['expected_metatile']
            before = view(case['cell'],label+'-before',before_expected)
            cross(case['direction'],case['neighbor'],case['target'])
            after = view(case['neighbor_cell'],label+'-after',case['expected_metatile'])
            cross(OPPOSITE[case['direction']],case['map'],case['player'])
            returned = view(case['cell'],label+'-returned',before_expected)
            cases.append(dict(case=case,before=before,after=after,returned=returned,
                outbound_and_return_with_controllers=True,
                parent_pop_observed=before['grid']['metatile'] != after['grid']['metatile']))
        for opening in openings:
            name = 'seven-east-'+str(opening['player'][1]).zfill(2)
            place(opening['map'],opening['player'],name)
            before = dict(state=state(),grid=grid(opening['player']))
            cross('right',opening['neighbor'],opening['target'])
            after = dict(state=state(),grid=grid(opening['target']))
            cross('left',opening['map'],opening['player'])
            returned = dict(state=state(),grid=grid(opening['player']),capture=picture(name+'-returned'))
            rounds.append(dict(opening=opening,before=before,after=after,returned=returned,
                outbound_and_return_with_controllers=True))
        for case in BUMPS:
            place(case['map'],case['player'],case['label'])
            expected = 0x243 if baseline else case['expected_metatile']
            before = state()
            target = grid(case['cell'])
            assert (target['block'],target['collision'],target['elevation'],target['border_id']) == (1023,1,0,0xFFFFFFFF)
            step(48,KEY[case['direction']])
            step(30)
            assert state() == before, ('Undefined apron became traversable',case,before,state())
            # The adjacent Surf sprite covers this target at the bump point.
            # Its full hardware pixel proof is already recorded above from
            # the unobstructed seam fixture; this frame proves the movement.
            observed = dict(state=state(),grid=grid(case['cell']),capture=picture(label+'-blocked'))
            assert observed['grid']['metatile'] == expected
            assert observed['grid'] == target
            bumps.append(dict(case=case,before=before,after=state(),target=target,
                              held_frames=48,native_directional_input_blocked=True,view=observed))
    finally:
        lib.stop()
        ns['emulator_workspace'].cleanup()
    assert initial_inputs == source_inputs(source)
    assert (romsha,elfsha) == tuple(digest(source/name) for name in ('pokeemerald.gba','pokeemerald.elf'))
    return dict(kind='generated-coast-cameras-native',passed=True,baseline=baseline,
        rom_sha256=romsha,elf_sha256=elfsha,native_validation_performed=True,
        initial_placements_and_surf_state_are_fixtures=True,private_query_trampoline_declared=True,
        only_read_only_queries_after_placement=True,gameplay_scripts_not_injected_after_placement=True,
        no_midtrip_position_collision_elevation_camera_palette_or_vram_writes=True,
        source_and_rom_unchanged=True,source_inputs_sha256=initial_inputs,
        scoped_maps=list(SCOPED_MAPS),full_world_camera_certified=False,full_campaign_playthrough=False,
        corner_cases=cases,seven_east_openings=rounds,undefined_boundary_bumps=bumps,
        fixtures=fixtures,controls=controls,queries=queries,captures=captures,components=[])


def run(source, library, output, parent_source=None):
    output = Path(output).resolve()
    parent_source = Path(parent_source or ROOT/'.local/coast-scenery-review-src').resolve()
    assert Path(source).resolve() != parent_source, 'Candidate must be separate from immutable parent'
    parent_directory = output/'parent170'
    parent = _run(parent_source,library,parent_directory,baseline=True)
    parent_path = parent_directory/'coast.json'
    parent_path.write_text(json.dumps(parent,indent=2)+'\n')
    verify_report(parent,parent_directory,contract.PARENT_ROM_SHA256)
    report = _run(source,library,output,baseline=False)
    report['parent_baseline'] = parent
    report['components'] = [dict(kind=parent['kind'],file='parent170/coast.json',sha256=digest(parent_path))]
    verify_report(report,output,report['rom_sha256'])
    (output/'coast.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def verify_grid(grid, cell, expected):
    assert grid['cell'] == cell and grid['metatile'] == expected
    if grid['block'] == 1023:
        assert (grid['collision'],grid['elevation'],grid['border_id']) == (1,0,0xFFFFFFFF)
    else:
        assert grid['metatile'] == grid['block'] & 1023
        assert grid['collision'] == (grid['block'] >> 10) & 3
        assert grid['elevation'] == grid['block'] >> 12


def verify_report(report, directory, romsha=None):
    directory = Path(directory)
    assert report['kind'] == 'generated-coast-cameras-native' and report['passed'] is True
    assert type(report['baseline']) is bool
    for key in ('rom_sha256','elf_sha256'):
        value = report[key]
        assert isinstance(value,str) and len(value) == 64 and set(value) <= set('0123456789abcdef')
    if romsha is not None:
        assert report['rom_sha256'] == romsha
    if report['baseline']:
        assert (report['rom_sha256'],report['elf_sha256']) == (contract.PARENT_ROM_SHA256,contract.PARENT_ELF_SHA256)
    for key in ('native_validation_performed','initial_placements_and_surf_state_are_fixtures',
                'private_query_trampoline_declared','only_read_only_queries_after_placement',
                'gameplay_scripts_not_injected_after_placement',
                'no_midtrip_position_collision_elevation_camera_palette_or_vram_writes','source_and_rom_unchanged'):
        assert report[key] is True, key
    assert report['full_world_camera_certified'] is report['full_campaign_playthrough'] is False
    assert report['scoped_maps'] == list(SCOPED_MAPS)
    assert 'src/fieldmap.c' in report['source_inputs_sha256'] and len(report['source_inputs_sha256']) >= 18
    for value in report['source_inputs_sha256'].values():
        assert isinstance(value,str) and len(value) == 64 and set(value) <= set('0123456789abcdef')
    images = verify_captures(report['captures'],directory)
    captures = {row['file']:row['sha256'] for row in report['captures']}
    assert len(captures) == len(report['captures'])
    used,fixtures,controls = set(),[],[]
    assert len(report['corner_cases']) == len(CASES)
    for row,case in zip(report['corner_cases'],CASES):
        assert row['case'] == case and row['outbound_and_return_with_controllers'] is True
        fixtures.append(dict(label=case['label'],map=case['map'],tile=case['player'],surfing=True))
        controls.extend((dict(label=case['label'],key=KEY[case['direction']]),dict(label=case['label'],key=KEY[OPPOSITE[case['direction']]])))
        for phase,name,tile,cell in (('before',case['map'],case['player'],case['cell']),
                ('after',case['neighbor'],case['target'],case['neighbor_cell']),
                ('returned',case['map'],case['player'],case['cell'])):
            view = row[phase]
            expected = 0x243 if report['baseline'] and phase != 'after' else case['expected_metatile']
            assert view['state'] == dict(map=name,tile=tile,surfing=True)
            verify_grid(view['grid'],cell,expected)
            verify_pixels(view['pixels'],view['capture'],captures,images,cell,expected)
            used.add(view['capture']['file'])
        assert row['before']['grid'] == row['returned']['grid']
        assert row['parent_pop_observed'] is (report['baseline'] and case in REPRO_CASES)
    assert sum(row['parent_pop_observed'] for row in report['corner_cases']) == (2 if report['baseline'] else 0)
    assert len(report['seven_east_openings']) == 11
    for y,row in enumerate(report['seven_east_openings'],1):
        opening = dict(map=OPENING_MAP,player=[16,y],direction='right',neighbor=OPENING_NEIGHBOR,target=[0,y],blocks=[0x112B,0x112B])
        assert row['opening'] == opening and row['outbound_and_return_with_controllers'] is True
        label = 'seven-east-'+str(y).zfill(2)
        fixtures.append(dict(label=label,map=OPENING_MAP,tile=[16,y],surfing=True))
        controls.extend((dict(label=label,key=16),dict(label=label,key=32)))
        for phase,name,tile in (('before',OPENING_MAP,[16,y]),('after',OPENING_NEIGHBOR,[0,y]),('returned',OPENING_MAP,[16,y])):
            view = row[phase]
            assert view['state'] == dict(map=name,tile=tile,surfing=True)
            verify_grid(view['grid'],tile,0x12B)
            assert view['grid']['block'] == 0x112B
        attachment = row['returned']['capture']
        assert captures[attachment['file']] == attachment['sha256']
        used.add(attachment['file'])
    assert len(report['undefined_boundary_bumps']) == len(BUMPS)
    for row,case in zip(report['undefined_boundary_bumps'],BUMPS):
        assert row['case'] == case
        assert row['before'] == row['after'] == dict(map=case['map'],tile=case['player'],surfing=True)
        assert row['held_frames'] == 48 and row['native_directional_input_blocked'] is True
        expected = 0x243 if report['baseline'] else case['expected_metatile']
        verify_grid(row['target'],case['cell'],expected)
        assert row['target']['block'] == 1023 and row['target'] == row['view']['grid']
        assert row['view']['state'] == row['after']
        assert captures[row['view']['capture']['file']] == row['view']['capture']['sha256']
        used.add(row['view']['capture']['file'])
        fixtures.append(dict(label=case['label'],map=case['map'],tile=case['player'],surfing=True))
        controls.append(dict(label=case['label'],key=KEY[case['direction']]))
    assert report['fixtures'] == fixtures
    assert len(report['controls']) == len(controls)
    for observed,expected in zip(report['controls'],controls):
        assert {k:observed[k] for k in ('label','key')} == expected
        assert type(observed['frames']) is int and observed['frames'] >= 1
    assert report['queries'] and all(row['function'].startswith('MapGridGet') or row['function'] == 'GetMapBorderIdAt' for row in report['queries'])
    assert used == set(captures)
    if report['baseline']:
        assert report['components'] == [] and 'parent_baseline' not in report
    else:
        parent = report['parent_baseline']
        assert parent['baseline'] is True
        path = directory/'parent170/coast.json'
        assert report['components'] == [dict(kind=parent['kind'],file='parent170/coast.json',sha256=digest(path))]
        assert json.loads(path.read_bytes()) == parent
        verify_report(parent,path.parent,contract.PARENT_ROM_SHA256)
        for current,previous in zip(report['corner_cases'],parent['corner_cases']):
            for phase in ('before','after','returned'):
                assert {k:v for k,v in current[phase]['grid'].items() if k != 'metatile'} == {k:v for k,v in previous[phase]['grid'].items() if k != 'metatile'}
        for current,previous in zip(report['seven_east_openings'],parent['seven_east_openings']):
            assert current['opening'] == previous['opening']
            for phase in ('before','after','returned'):
                for key in ('state','grid'):
                    assert current[phase][key] == previous[phase][key], 'The eleven physical openings must remain unchanged'
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--library',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--parent-source',type=Path)
    args = parser.parse_args()
    run(args.source,args.library,args.output,args.parent_source)
