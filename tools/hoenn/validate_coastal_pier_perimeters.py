"""Exercise every exposed dry/wet edge of the seven integrated Sevii piers.

Initial map placement, party, completed trainer flags and disabled random
encounters are movement fixtures. The actual blocked walking, native Surf
prompt, departure and dismount use controller input. No coordinate, elevation
or avatar-state writes occur between departure and return.
"""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]


def legacy_cold_boot(source, library, output, battery, expected):
    """Extend the existing real cold boot observer with read-only avatar data."""
    path = ROOT/'tools/hoenn/validate_cold_boot.py'
    code = path.read_text()
    anchor = '                    result = dict(bundled_save_continue_to_field=True, field_map=[lib.read8(save+4), lib.read8(save+5)])'
    assert code.count(anchor) == 1
    observer = '''
                    obj = symbols['gObjectEvents'] + 36 * lib.read8(symbols['gPlayerAvatar'] + 5)
                    result.update(player_tile=[lib.read16(obj+16)-7, lib.read16(obj+18)-7],
                                  avatar_surfing=bool(lib.read8(symbols['gPlayerAvatar']) & 8),
                                  elevation=lib.read8(obj+11) & 15)
                    assert result['field_map'] == LEGACY_EXPECTED['map_id'], result
                    assert result['player_tile'] == LEGACY_EXPECTED['tile'], result
                    assert result['avatar_surfing'] and result['elevation'] == 1, result
                    def legacy_state():
                        player = symbols['gObjectEvents'] + 36 * lib.read8(symbols['gPlayerAvatar'] + 5)
                        return dict(player_tile=[lib.read16(player+16)-7, lib.read16(player+18)-7],
                                    avatar_surfing=bool(lib.read8(symbols['gPlayerAvatar']) & 8),
                                    elevation=lib.read8(player+11) & 15)
                    movements = []
                    for goal, key, surfing, elevation in [([21,6],64,True,1),([20,6],32,False,3)]:
                        initial = legacy_state()
                        for held in range(120):
                            if legacy_state()['player_tile'] == goal:
                                break
                            step(1, key)
                        else:
                            raise AssertionError(('Legacy controller reboard failed', goal, legacy_state()))
                        step(60)
                        returned = legacy_state()
                        assert returned['player_tile'] == goal, returned
                        assert returned['avatar_surfing'] is surfing and returned['elevation'] == elevation, returned
                        movements.append(dict(initial=initial, returned=returned, direction_key=key,
                                              held_input_frames=held, controller_input_only=True))
                    picture('legacy-reboarded-to-pier')
                    result.update(legacy_controller_returned_to_pier=True,
                                  legacy_controller_movements=movements,
                                  legacy_final_state=legacy_state())
'''
    namespace = {'__file__':str(path), '__name__':'coastal_legacy_cold_boot',
                 'LEGACY_EXPECTED':expected}
    exec(compile(code.replace(anchor, anchor+observer), str(path), 'exec'), namespace)
    report = namespace['validate'](source, library, output, battery)
    report['legacy_walking_water_save_recovers_native_surf'] = True
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--library',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--legacy-battery',type=Path)
    parser.add_argument('--legacy-manifest',type=Path)
    parser.add_argument('--coldboot-library',type=Path)
    options=parser.parse_args()
    assert bool(options.legacy_battery)==bool(options.legacy_manifest)==bool(options.coldboot_library)
    path=ROOT/'tools/hoenn/validate_integrated_piers.py'
    code=path.read_text().split('\nchecks = []\ntry:')[0]
    sys.argv=[sys.argv[0],'--source',str(options.source),'--library',str(options.library),
              '--output',str(options.output)]
    ns={'__file__':str(path),'__name__':'coastal_pier_perimeters_native'}
    exec(compile(code,str(path),'exec'),ns)
    lib,native,step,warp,walk=(ns[key] for key in ('lib','native','step','warp','walk'))
    blocks,behaviors=ns['blocks'],ns['behaviors']
    native('DisableWildEncounters',1)
    initial_sha=hashlib.sha256((options.source/'pokeemerald.gba').read_bytes()).hexdigest()
    port_results=[]
    all_cases=[]
    captures=[]
    try:
        for port in ns['ports']:
            cases=[]
            deck={tuple(cell) for cell in port['deck_cells']}
            for name,x,y in sorted(deck):
                width,height,words=blocks[name]
                dry=words[y*width+x]
                assert dry>>12==3 and not dry&0xC00, (port['island'],name,x,y,hex(dry))
                for dx,dy,key in ns['keys']:
                    xx,yy=x+dx,y+dy
                    if 0<=xx<width and 0<=yy<height:
                        destination=(name,xx,yy)
                    else:
                        destination=ns['connection_step'](name,x,y,key)
                    if destination is None or destination in deck:
                        continue
                    other,wx,wy=destination
                    ww,wh,wet_words=blocks[other]
                    word=wet_words[wy*ww+wx]
                    behavior=behaviors[other][wy*ww+wx]
                    if word&0xC00 or not ns['water_behaviors'][behavior]:
                        continue
                    cases.append(dict(dry=[name,x,y],water=list(destination),key=key,
                                      water_block=word,water_behavior=behavior))
            assert cases, (port['island'],'No perimeter edges planned')
            assert len({(tuple(row['dry']),tuple(row['water'])) for row in cases})==len(cases)
            for index,row in enumerate(cases):
                dry,water=tuple(row['dry']),tuple(row['water'])
                warp(*dry)
                # Only initial placement may set the starting walking state.
                native('SetPlayerAvatarTransitionFlags',1)
                step(90)
                before=ns['assert_foot']()
                assert ns['position']()==dry[1:]
                assert native('MapGridGetElevationAt',water[1]+7,water[2]+7)==1, (
                    'Unsafe water elevation at exposed pier edge',row)
                step(90,row['key']);step(45)
                blocked=ns['assert_foot']()
                assert (ns['by_location'][ns['location']()],*ns['position']())==dry, (
                    'Foot walked into ocean without Surf',port['island'],row,blocked)
                assert native('IsPlayerFacingSurfableFishableWater'), (port['island'],row)
                prior=len(ns['surf_prompts'])
                ns['set_passability']()
                walk(water)
                step(45)
                departed=ns['assert_surf']()
                assert len(ns['surf_prompts'])>prior, ('Native Surf prompt absent',row)
                assert (ns['by_location'][ns['location']()],*ns['position']())==water
                walk(dry);step(60)
                reboarded=ns['assert_foot']()
                assert (ns['by_location'][ns['location']()],*ns['position']())==dry
                result=dict(**row,initial=before,blocked_walk=blocked,
                            surf_departure=departed,reboarded=reboarded,
                            walking_without_surf_blocked=True,native_surf_prompt=True,
                            native_controller_departure_and_reboard=True,
                            no_midtrip_coordinate_elevation_or_avatar_writes=True)
                if index==0 or (dry==('OneIsland_TreasureBeach_Frlg',20,6)
                                and water==('OneIsland_TreasureBeach_Frlg',21,6)):
                    label=port['island'].lower()+'-perimeter-'+str(index)+'-reboarded'
                    ns['picture'](label)
                    result['capture_file']=label+'.png'
                    captures.append(dict(file=label+'.png',sha256=hashlib.sha256(
                        (options.output/(label+'.png')).read_bytes()).hexdigest()))
                all_cases.append(dict(island=port['island'],**result))
            port_results.append(dict(island=port['island'],perimeter_edges=len(cases),
                                     all_exposed_edges_tested=True,
                                     walking_without_surf_blocked=True,
                                     native_controller_departure_and_reboard=True))
            print('Native complete pier perimeter passed:',port['island'],len(cases),flush=True)
        assert len(port_results)==7
        assert any(row['dry']==['OneIsland_TreasureBeach_Frlg',20,6]
                   and row['water']==['OneIsland_TreasureBeach_Frlg',21,6] for row in all_cases)
        assert any(row['dry']==['OneIsland_TreasureBeach_Frlg',16,6]
                   and row['water']==['OneIsland_TreasureBeach_Frlg',16,7] for row in all_cases)
    finally:
        lib.stop()
    report=dict(kind='coastal-pier-perimeters',passed=True,rom_sha256=initial_sha,
                compiled_rom=True,native_validation_performed=True,
                elf_sha256=hashlib.sha256((options.source/'pokeemerald.elf').read_bytes()).hexdigest(),
                ports=port_results,cases=all_cases,perimeter_edges=len(all_cases),captures=captures,
                all_seven_ports_verified=True,all_exposed_dry_water_edges_tested=True,
                previous_video_defect_edges_included=True,
                initial_placements_party_and_progress_are_fixtures=True,
                movement_fixture_random_encounters_disabled=True,
                controller_only_after_initial_placement=True,
                no_midtrip_coordinate_elevation_or_avatar_writes=True,
                legacy_save_recovery_tested=False)
    if options.legacy_battery:
        expected=json.loads(options.legacy_manifest.read_text())
        assert expected['walking_water_reproduced_by_controller']
        assert hashlib.sha256(options.legacy_battery.read_bytes()).hexdigest()==expected['battery_sha256']
        legacy=legacy_cold_boot(options.source,options.coldboot_library,
                                options.output/'legacy-continue',options.legacy_battery,expected)
        legacy_captures=[]
        for name in ('battery-continued-to-field.png','legacy-reboarded-to-pier.png'):
            path=options.output/'legacy-continue'/name
            legacy_captures.append(dict(file='legacy-continue/'+name,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        report['captures'].extend(legacy_captures)
        report.update(legacy_save_recovery_tested=True,legacy_save_recovery=legacy,
                      legacy_source_rom_sha256=expected['rom_sha256'],
                      legacy_save_recovery_captures=legacy_captures)
    assert hashlib.sha256((options.source/'pokeemerald.gba').read_bytes()).hexdigest()==initial_sha
    (options.output/'coastal-pier-perimeters.json').write_text(json.dumps(report,indent=2)+'\n')
    print('All seven pier perimeters passed:',len(all_cases),'dry/water edges',flush=True)


if __name__=='__main__':
    main()
