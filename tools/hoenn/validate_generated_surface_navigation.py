"""Inventory compiled surface connectivity and cross generated seams in mGBA.

Graph reachability is reported separately from controller evidence. Every native
case begins with a declared placement/party/trainer-state fixture; the border
crossing itself uses directional input and observes native map/Surf state.
"""
from collections import deque
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]


def place_fixture(namespace, mapping, x, y, frames=240):
    """Place a case before crossing, through a native sixteen-bit warp event.

    SetWarpDestination's direct x/y parameters are signed bytes. Large maps
    require the map-event form, whose coordinates are s16. Only this private
    emulator's ROM table is replaced, and it is restored before directional
    input. No avatar coordinate or elevation is written.
    """
    group, number = namespace['map_id'](mapping)
    script = namespace['script']
    if x <= 127 and y <= 127:
        script(b'\x39'+bytes([group, number, 255])+struct.pack('<HH', x, y)+b'\x27\x6b\x02', frames=frames)
        return False
    lib = namespace['lib']
    header = namespace['native']('Overworld_GetMapHeaderByGroupAndId', group, number)
    events = lib.read32(header+4)
    assert events, ('Map has no event header for travel fixture', mapping)
    # Script bytecode uses the first 0x200 bytes and is at most eleven bytes
    # here; native-call code begins at +0x200. This slot never touches either.
    event = namespace['FIXTURE_ROM_BASE']+0x180
    old_count = lib.read8(events+1)
    old_pointer = bytes(lib.read8(events+8+i) for i in range(4))
    old_event = bytes(lib.read8(event+i) for i in range(8))
    try:
        for i, value in enumerate(struct.pack('<hhBBBB', x, y, 0, 255, 0, 0)):
            lib.raw8(event+i, value)
        lib.raw8(events+1, 1)
        for i, value in enumerate(struct.pack('<I', event)):
            lib.raw8(events+8+i, value)
        script(b'\x39'+bytes([group, number, 0])+b'\0\0\0\0\x27\x6b\x02', frames=frames)
    finally:
        lib.raw8(events+1, old_count)
        for i, value in enumerate(old_pointer):
            lib.raw8(events+8+i, value)
        for i, value in enumerate(old_event):
            lib.raw8(event+i, value)
    assert lib.read8(events+1) == old_count
    assert bytes(lib.read8(events+8+i) for i in range(4)) == old_pointer
    assert bytes(lib.read8(event+i) for i in range(8)) == old_event
    return True


def edge_pairs(direction, offset, aw, ah, bw, bh):
    """Native signed connection offsets, including negative overlaps."""
    if direction in ('right', 'left'):
        return [((aw-1 if direction == 'right' else 0, y),
                 (0 if direction == 'right' else bw-1, y-offset))
                for y in range(max(0, offset), min(ah, offset+bh))]
    return [((x, ah-1 if direction == 'down' else 0),
             (x-offset, 0 if direction == 'down' else bh-1))
            for x in range(max(0, offset), min(aw, offset+bw))]


def middle_run(pairs):
    """Choose the center of the widest usable contiguous border interval."""
    runs = []
    for pair in pairs:
        if not runs or sum(abs(a-b) for a, b in zip(runs[-1][-1][0], pair[0])) != 1:
            runs.append([])
        runs[-1].append(pair)
    return max(runs, key=len)[len(max(runs, key=len))//2] if runs else None


def merge_reports(paths, output):
    """Combine disjoint shards only when they tested one identical ROM/plan."""
    reports = [json.loads(Path(p).read_text()) for p in paths]
    assert reports, 'No native shards supplied'
    result = dict(reports[0])
    expected = result['planned_native_cases']
    collected = {}
    for report in reports:
        assert report['rom_sha256'] == result['rom_sha256'], 'Native shards belong to different ROMs'
        assert report['planned_native_cases'] == expected, 'Native shard plans differ'
        assert report['graph_passed'], 'A native shard has a failed static graph'
        for row in report['native_cases']:
            index = row['index']
            assert index not in collected, ('Duplicate native case',index)
            assert {k:row[k] for k in expected[index]} == expected[index], ('Mismatched native case',index)
            collected[index] = row
    assert set(collected) == set(range(len(expected))), ('Incomplete native seam coverage',sorted(set(range(len(expected)))-set(collected)))
    result['native_cases'] = [collected[i] for i in range(len(expected))]
    result['native_all_planned_cases_executed'] = True
    result['native_passed'] = all(r['passed'] for r in result['native_cases'])
    result['passed'] = result['graph_passed'] and result['native_passed']
    result['merged_native_shards'] = len(reports)
    result['native_case_count'] = len(result['native_cases'])
    result['native_surf_case_count'] = sum(r['mode']=='surf' for r in result['native_cases'])
    result['native_walk_case_count'] = sum(r['mode']=='walk' for r in result['native_cases'])
    high = [row for row in result['native_cases'] if any(v > 127 for v in row.get('start', []))]
    assert all(row.get('restored_private_16bit_initial_warp_fixture') is True for row in high), 'Unverified large-coordinate fixture'
    result['high_coordinate_initial_placements_use_restored_private_warp_events'] = True
    result['high_coordinate_initial_fixture_cases'] = len(high)
    captures = []
    destination = Path(output).parent
    for path, report in zip(paths, reports):
        for row in report['native_cases']:
            if row['index'] % 40:
                continue
            name = 'surface-seam-'+str(row['index'])+'-arrival.png'
            original = Path(path).parent/name
            if not original.exists():
                continue
            target = destination/'captures'/name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(original, target)
            captures.append(dict(file=target.relative_to(destination).as_posix(),
                sha256=hashlib.sha256(target.read_bytes()).hexdigest(), case_index=row['index'],
                destination=row['destination'], position=row['end'], native_emulator_capture=True))
    result['captures'] = sorted(captures, key=lambda row:row['case_index'])
    Path(output).parent.mkdir(parents=True,exist_ok=True)
    Path(output).write_text(json.dumps(result,indent=2)+'\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--library', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--inventory', type=Path, default=ROOT/'docs/design/generated-world-audit/inventory.json')
    parser.add_argument('--original-inputs', type=Path, default=ROOT/'.local/generated-world-original-inputs')
    parser.add_argument('--native', action='store_true')
    parser.add_argument('--start-case', type=int, default=0)
    parser.add_argument('--limit', type=int)
    options = parser.parse_args()
    namespace = globals()
    namespace['__file__'] = str(Path(__file__).resolve())
    sys.argv = [sys.argv[0], '--source', str(options.source), '--library', str(options.library), '--output', str(options.output)]
    bootstrap = (ROOT/'tools/hoenn/validate_team_missions.py').read_text().split('\nassert pending(True) == 7')[0]
    exec(compile(bootstrap, str(ROOT/'tools/hoenn/validate_team_missions.py'), 'exec'), namespace)
    source, lib, s = namespace['source'], namespace['lib'], namespace['s']
    native, step = namespace['native'], namespace['step']
    inventory = json.loads(options.inventory.read_text())
    direct = {r['map']: r for r in inventory['maps']}
    # Include original neighbors to resolve every actual native connection.
    namespace['names'] = [p.parent.name for p in (source/'data/maps').glob('*/map.json')
        if (m := json.loads(p.read_text()))['map_type'] in
           ['MAP_TYPE_ROUTE','MAP_TYPE_CITY','MAP_TYPE_TOWN','MAP_TYPE_OCEAN_ROUTE']
        or ('Harbor' in p.parent.name and m.get('connections'))]
    namespace['walk_surf_under_bridges'] = True
    namespace['walk_layout_overrides'] = {'Route131': 'LAYOUT_ROUTE131_SKY_PILLAR'}
    namespace['allowed'] = set()
    namespace['walk_prefix'] = 'generated-navigation'
    exec(compile((ROOT/'tools/hoenn/native_water_walk.py').read_text(), str(ROOT/'tools/hoenn/native_water_walk.py'), 'exec'), namespace)
    maps, blocks, behaviors = namespace['maps'], namespace['blocks'], namespace['behaviors']
    by_id, water, currents = namespace['by_id'], namespace['water_behaviors'], namespace['currents']
    # MB_FAST_WATER is deliberately Surf water only on the integrated Sevii
    # coast. The native predicate is map-dependent; a global behavior cache
    # built on the initial Hoenn map must not classify it as ordinary ground.
    coast_source = (source/'src/journey_sevii_surf.c').read_text()
    coast_function = re.search(r'static bool32 IsConnectedSeviiCoast\([^)]*\)\s*\{(.*?)\n\}',
                               coast_source, re.S)[1]
    coast_ids = set(re.findall(r'case\s*\(MAP_GROUP\((MAP_\w+)\)', coast_function))
    assert coast_ids and coast_ids <= set(by_id)
    open_coast_maps = {by_id[value] for value in coast_ids}

    def wet(name, behavior):
        return name in open_coast_maps if behavior == 0x2C else water[behavior]

    opposite = dict(right='left', left='right', up='down', down='up')
    key_for = dict(right=16,left=32,up=64,down=128)

    def mode(name, xy):
        w, h, values = blocks[name]
        i = xy[1]*w+xy[0]
        tile, behavior = values[i], behaviors[name][i]
        if tile & 0xC00 or currents[behavior] is not None:
            return None
        if wet(name, behavior):
            return 'surf'
        if xy not in namespace['warps'][name] and behavior != 0x2C:
            return 'walk'
        return None

    def compatible(a,b,pair):
        elevations=[]
        for name,xy in zip((a,b),pair):
            w,_,values=blocks[name]
            elevations.append(values[xy[1]*w+xy[0]]>>12)
        return elevations[0]==elevations[1] or any(e in (0,15) for e in elevations)

    edges, cases, closed, inconsistent = [], [], [], []
    visited_edges = set()
    for a in sorted(maps):
        for c in maps[a].get('connections') or []:
            b = by_id.get(c['map'])
            if b is None:
                continue
            d, off = c['direction'], c['offset']
            canonical = tuple(sorted(((a,d,off),(b,opposite[d],-off))))
            if canonical in visited_edges:
                continue
            visited_edges.add(canonical)
            if not any(n in direct and (direct[n]['created'] or direct[n]['terrain']['changed'] or
                       'connections' in direct[n]['changed_header_fields']) for n in (a,b)):
                continue
            reciprocal = any(x['map'] == maps[a]['id'] and x['direction'] == opposite[d] and x['offset'] == -off
                             for x in maps[b].get('connections') or [])
            pairs = edge_pairs(d,off,*blocks[a][:2],*blocks[b][:2])
            usable = {kind: [p for p in pairs if mode(a,p[0]) == mode(b,p[1]) == kind and compatible(a,b,p)]
                      for kind in ('surf','walk')}
            row = dict(source=a,destination=b,direction=d,offset=off,reciprocal=reciprocal,
                       overlap_cells=len(pairs),surf_cells=len(usable['surf']),walk_cells=len(usable['walk']))
            edges.append(row)
            if not reciprocal:
                inconsistent.append(row)
            if not any(usable.values()):
                original_sides=[]
                for name,side in [(a,0),(b,1)]:
                    layout=namespace['layouts'][namespace['walk_layout_overrides'].get(name,maps[name]['layout'])]
                    original_path=options.original_inputs/layout['blockdata_filepath']
                    w,h,values=blocks[name]
                    if original_path.exists() and original_path.stat().st_size==w*h*2:
                        original_values=struct.unpack('<'+'H'*(w*h),original_path.read_bytes())
                        indices=[pair[side][1]*w+pair[side][0] for pair in pairs]
                        original_sides.append(dict(map=name,border_cells=len(indices),
                            unchanged_border_cells=sum(values[i]==original_values[i] for i in indices),
                            all_border_cells_unchanged=all(values[i]==original_values[i] for i in indices)))
                closed.append(row | dict(reason='Preserved upstream cliff/tree boundary; no ordinary compatible-height border passage',
                    original_border_comparisons=original_sides,
                    upstream_boundary_preserved=any(x['all_border_cells_unchanged'] for x in original_sides)))
            for kind, available in usable.items():
                selected = middle_run(available)
                if selected:
                    p,q = selected
                    for first,last,start,end,direction in [(a,b,p,q,d),(b,a,q,p,opposite[d])]:
                        cases.append(dict(source=first,destination=last,start=list(start),end=list(end),
                                          direction=direction,mode=kind))

    # The static ocean graph uses real compiled behavior tables and source
    # collision/elevation. It never treats an elevated dry beach as Surf water.
    sea = {n: {i for i,t in enumerate(values) if not t & 0xC00 and
             t >> 12 in (0,1,15) and wet(n,behaviors[n][i])}
           for n,(_,_,values) in blocks.items()}
    namespace['passable'] = sea
    start = ('Route19_Frlg',15,50)
    queue, reachable = deque([start]), {start}
    while queue:
        n,x,y = queue.popleft(); w,h,_ = blocks[n]
        forced = currents[behaviors[n][y*w+x]]
        for dx,dy,key in namespace['keys']:
            if forced is not None and (dx,dy) != forced:
                continue
            xx,yy = x+dx,y+dy
            nxt = ((n,xx,yy) if yy*w+xx in sea[n] else None) if 0<=xx<w and 0<=yy<h else namespace['connection_step'](n,x,y,key)
            if nxt is not None and nxt not in reachable:
                reachable.add(nxt);queue.append(nxt)
    reached_maps = {n for n,_,_ in reachable}
    required = {n for n in maps if n in direct and direct[n]['created'] and
                maps[n]['map_type']=='MAP_TYPE_OCEAN_ROUTE'}
    # The original prototype is explicitly retired by the atlas and has no
    # incoming references. Preserve its map ID for old saves, not as a route.
    atlas_path = source/'.journey-navigated-sea-atlas'
    retired = {json.loads(atlas_path.read_text()).get('obsolete_unconnected_route_removed')} if atlas_path.exists() else set()
    retired.discard(None)
    for name in retired:
        assert not maps[name].get('connections')
        assert not any(c['map']==maps[name]['id'] for m in maps.values() for c in m.get('connections') or [])
        assert not any(w['dest_map']==maps[name]['id'] for m in maps.values() for w in m.get('warp_events',[]))
    required -= retired
    disconnected = sorted(required-reached_maps)
    sha = hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest()
    result = dict(kind='generated-navigation',rom_sha256=sha,compiled_behavior_and_collision_graph=True,forced_ocean_currents_respected=True,
        graph_audit_not_controller_playthrough=True,surface_maps=len(maps),reviewed_edges=edges,
        source_surface_cells=sum(w*h for w,h,_ in blocks.values()),reviewed_edge_count=len(edges),
        planned_native_case_count=len(cases),native_directional_input=True,
        conditional_fast_water_coast_maps=sorted(open_coast_maps),
        closed_edges_requiring_visual_context=closed,nonreciprocal_edges=inconsistent,
        required_generated_ocean_maps=sorted(required),explicitly_retired_maps=sorted(retired),disconnected_generated_ocean_maps=disconnected,
        reached_surface_maps=sorted(reached_maps),reachable_water_cells=len(reachable),
        planned_native_cases=cases,native_cases=[],native_requested=options.native,
        initial_placements_party_and_defeated_trainer_flags_are_fixtures=True)
    path = options.output/'generated-surface-navigation.json'; path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2)+'\n')
    print('Compiled surface graph:',len(maps),'maps;',len(edges),'edges;',len(cases),'native cases; disconnected:',disconnected,flush=True)
    if options.native:
        # Suppress trainer encounters without enabling Safari or other system flags.
        count = int(re.search(r'^#define\s+TRAINER_JOURNEY_PWT_BROCK\s+(\d+)',
                    (source/'include/constants/opponents.h').read_text(),re.M)[1])
        for index in range(1,count): namespace['rawflag'](0x500+index,True)
        assert native('GetSafariZoneFlag') == 0
        # The seam fixture is a free-roaming visit after the native Sevii
        # arrival scenes. Otherwise Four Island immediately starts the
        # rival's dialogue instead of accepting directional crossing input.
        # These are declared setup variables, never writes during a crossing.
        constants = (source/'include/constants/vars.h').read_text()
        progress = {'VAR_MAP_SCENE_ONE_ISLAND_HARBOR': 3,
                    'VAR_MAP_SCENE_FOUR_ISLAND': 1}
        for name,value in progress.items():
            address = int(re.search(r'^#define\s+'+name+r'\s+(0x\w+)', constants, re.M)[1],16)
            native('VarSet', address, value)
        result['completed_arrival_scene_setup_variables'] = progress
        result['high_coordinate_initial_placements_use_restored_private_warp_events'] = True
        selected = list(enumerate(cases))[options.start_case:]
        if options.limit is not None: selected=selected[:options.limit]
        for index,case in selected:
            a,b=case['source'],case['destination']; x,y=case['start']
            g,n=namespace['map_id'](a)
            high_coordinate_fixture = place_fixture(namespace, a, x, y)
            for _ in range(60):
                if namespace['idle']():break
                step(8)
            assert namespace['idle']() and namespace['location']()==(g,n) and namespace['position']()==(x,y),('Fixture placement',case,namespace['location'](),namespace['position']())
            native('SetPlayerAvatarTransitionFlags',8 if case['mode']=='surf' else 1);step(30)
            arrived=False
            for _ in range(240):
                step(1,key_for[case['direction']])
                if namespace['location']()==namespace['map_id'](b):
                    step(60);arrived=True;break
            actual=dict(location=list(namespace['location']()),position=list(namespace['position']()),
                        surf=bool(lib.read8(s['gPlayerAvatar'])&8),
                        kanto_region_presentation=bool(lib.read8(s['isFrlg'])))
            target_layout=namespace['layouts'][namespace['walk_layout_overrides'].get(b,maps[b]['layout'])]
            loaded_layout = lib.read32(s['gMapHeader'])
            # Global isFrlg follows the current *region* (overworld.c), while
            # mixed-region routes deliberately use either tileset format.
            # Read the native layout flag that selects metatile decoding.
            actual['layout_frlg'] = bool(lib.read8(loaded_layout+0x18))
            actual['primary_bank'] = lib.read32(loaded_layout+0x10)
            actual['secondary_bank'] = lib.read32(loaded_layout+0x14)
            banks_match = (actual['primary_bank'] == s[target_layout['primary_tileset']] and
                           actual['secondary_bank'] == s[target_layout['secondary_tileset']])
            block_matches = False
            if arrived and actual['position'] == case['end']:
                xx,yy = actual['position']
                width = lib.read32(s['gBackupMapLayout'])
                pointer = lib.read32(s['gBackupMapLayout']+8)
                actual['loaded_block'] = lib.read16(pointer+2*(xx+7+(yy+7)*width))
                target_width = blocks[b][0]
                actual['expected_block'] = blocks[b][2][yy*target_width+xx]
                block_matches = actual['loaded_block'] == actual['expected_block']
            passed=(arrived and actual['position']==case['end'] and actual['surf']==(case['mode']=='surf') and
                    actual['layout_frlg']==(target_layout['layout_version']=='frlg') and banks_match and block_matches)
            row=dict(index=index,**case,observed=actual,passed=passed,
                     restored_private_16bit_initial_warp_fixture=high_coordinate_fixture)
            result['native_cases'].append(row)
            if not passed or index % 40 == 0: namespace['picture']('surface-seam-'+str(index)+('-failure' if not passed else '-arrival'))
            path.write_text(json.dumps(result,indent=2)+'\n')
            print('Native surface seam',index,'PASS' if passed else 'FAIL',a,b,case['mode'],actual,flush=True)
    result['graph_passed']=not inconsistent and not disconnected
    result['native_passed']=(all(r['passed'] for r in result['native_cases']) if options.native else None)
    result['native_all_planned_cases_executed']=len(result['native_cases'])==len(cases)
    result['native_case_count']=len(result['native_cases'])
    result['native_surf_case_count']=sum(r['mode']=='surf' for r in result['native_cases'])
    result['native_walk_case_count']=sum(r['mode']=='walk' for r in result['native_cases'])
    result['passed']=result['graph_passed'] and (result['native_passed'] if options.native else True)
    path.write_text(json.dumps(result,indent=2)+'\n')
    lib.stop();namespace['emulator_workspace'].cleanup()
    return result


if __name__ == '__main__':
    sys.exit(0 if main()['passed'] else 1)
