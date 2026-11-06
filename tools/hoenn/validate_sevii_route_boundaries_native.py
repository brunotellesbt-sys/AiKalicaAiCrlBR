"""Inspect marine corner scanout, bump reefs and sail the southern One circuit.

Each independent case has one declared initial placement. After placement the
walker uses controllers; the existing private-ROM query trampoline may call
read-only native getters, and the final battery uses native TrySavingData.
Continue boots a fresh core and follows title/menu input without a callback fix.
"""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import sys

from sevii_boundary_camera import REPRO_CASES, audit_camera_holes

ROOT = Path(__file__).resolve().parents[2]
BEACH = 'OneIsland_TreasureBeach_Frlg'
START = ['JourneySurfLink03505', 8, 14]
BUMP_MAPS = ['OneIsland_Frlg', 'TwoIsland_Frlg', 'ThreeIsland_Port_Frlg',
             'FourIsland_Frlg', 'FiveIsland_Frlg', 'SixIsland_Frlg', 'SevenIsland_Frlg',
             'JourneySurfLink03502']
DIRECTIONS = {(1, 0): 16, (-1, 0): 32, (0, 1): 128, (0, -1): 64}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def observe_cells(ns, requested):
    """Compare requested cells even when no connection owns their grid block.

    Getters run before sampling. The sampler then reads hardware BG/OAM/VRAM,
    palette and scanout without advancing a frame, and records RGB witnesses
    which the exported PNG verifier checks again.
    """
    lib, symbols, native = ns['lib'], ns['s'], ns['native']
    name = ns['by_location'][ns['location']()]
    layout = ns['layouts'][ns['maps'][name]['layout']]
    frlg = layout['layout_version'] == 'frlg'
    cutoff = 640 if frlg else 512
    definitions = {}
    for x, y, expected in requested:
        mid = native('MapGridGetMetatileIdAt', x+7, y+7)
        assert mid == expected, ('Corner artwork differs from canonical final source', name, x, y, mid, expected)
        layer = native('MapGridGetMetatileLayerTypeAt', x+7, y+7)
        assert layer in (0, 1, 2)
        bank = symbols[layout['primary_tileset' if mid < cutoff else 'secondary_tileset']]
        index = mid if mid < cutoff else mid-cutoff
        words = [lib.read16(lib.read32(bank+12)+16*index+2*i) for i in range(8)]
        definitions[x, y] = dict(cell=[x, y], expected_metatile=expected, native_metatile=mid,
            layer=layer, definition_words=words, quadrants=set(), actual_bg_words={}, samples=[], checked_pixels=0)
    vram = bytes(lib.read8(0x06000000+i) for i in range(65536))
    image = ctypes.string_at(lib.image(), 240*160*4)
    palette = [lib.read16(0x05000000+2*i)&32767 for i in range(256)]
    rgb = [tuple(((word >> shift)&31)<<3 for shift in (0, 5, 10)) for word in palette]
    save = lib.read32(symbols['gSaveBlock1Ptr'])
    origin = [lib.read16(save+i) for i in (0, 2)]
    ring = [lib.read8(symbols['sFieldCameraOffset']+i) for i in (2, 3)]
    controls = {bg: lib.read16(0x04000008+2*bg) for bg in range(4)}
    scroll = {bg: [lib.read16(symbols['sGpuRegBuffer']+0x10+4*bg)&511,
                   lib.read16(symbols['sGpuRegBuffer']+0x12+4*bg)&511] for bg in range(4)}
    display = lib.read16(0x04000000)
    assert display&7 == 0
    dimensions = [[(8, 8), (16, 16), (32, 32), (64, 64)],
                  [(16, 8), (32, 8), (32, 16), (64, 32)],
                  [(8, 16), (8, 32), (16, 32), (32, 64)]]
    sprites = []
    for i in range(128):
        a0, a1 = lib.read16(0x07000000+8*i), lib.read16(0x07000002+8*i)
        if a0&0x300 == 0x200 or a0 >> 14 > 2:
            continue
        width, height = dimensions[a0 >> 14][a1 >> 14]
        x, y = a1&511, a0&255
        sprites.append((x-512 if x >= 256 else x, y-256 if y >= 160 else y, width, height))

    def bg_word(bg, x, y):
        control = controls[bg]
        assert not control&128
        size = control >> 14
        width, height = (512 if size in (1, 3) else 256), (512 if size in (2, 3) else 256)
        xx, yy = (x+scroll[bg][0])%width, (y+scroll[bg][1])%height
        tx, ty = xx//8, yy//8
        at = ((control >> 8)&31)*2048+((ty//32)*(width//256)+tx//32)*2048+((ty%32)*32+tx%32)*2
        return int.from_bytes(vram[at:at+2], 'little'), xx%8, yy%8

    def color(bg, word, x, y):
        if word&1024:
            x = 7-x
        if word&2048:
            y = 7-y
        at = ((controls[bg] >> 2)&3)*16384+(word&1023)*32+y*4+x//2
        value = (vram[at] >> (4*(x&1)))&15
        return None if value == 0 else rgb[(word >> 12)*16+value]

    for y in range(1, 160, 2):
        for x in range(1, 240, 2):
            xx, yy = (x+scroll[1][0])%256, (y+scroll[1][1])%256
            dx, dy = ((xx//8-ring[0])%32)//2, ((yy//8-ring[1])%32)//2
            row = definitions.get((origin[0]+dx-7, origin[1]+dy-7))
            if row is None:
                continue
            if any(sx <= x < sx+w and sy <= y < sy+h for sx, sy, w, h in sprites):
                continue
            if display&256:
                word, px, py = bg_word(0, x, y)
                if color(0, word, px, py) is not None:
                    continue
            q = (((yy//8-ring[1])%32)%2)*2+(((xx//8-ring[0])%32)%2)
            words = row['definition_words']
            expected = {0: {1: words[4+q], 2: words[q], 3: 0x3014},
                        1: {1: 0, 2: words[4+q], 3: words[q]},
                        2: {1: words[4+q], 2: 0, 3: words[q]}}[row['layer']]
            for bg, value in expected.items():
                actual, _, _ = bg_word(bg, x, y)
                assert actual == value, ('Corner BG word mismatch', name, row['cell'], bg, actual, value)
            row['actual_bg_words'][q] = [bg_word(bg, x, y)[0] for bg in (1, 2, 3)]
            top = None
            for bg in sorted(expected, key=lambda bg: (controls[bg]&3, bg)):
                actual, px, py = bg_word(bg, x, y)
                top = color(bg, actual, px, py)
                if top is not None:
                    break
            assert top is not None, ('No opaque terrain pixel', name, row['cell'])
            actual = image[(y*240+x)*4:(y*240+x)*4+3]
            assert all(abs(a-b) <= 7 for a, b in zip(actual, top)), ('Corner scanout mismatch', name, row['cell'], x, y)
            row['checked_pixels'] += 1
            row['quadrants'].add(q)
            if sum(sample[5] == q for sample in row['samples']) < 4:
                row['samples'].append([x, y, *top, q])
    rows = list(definitions.values())
    for row in rows:
        assert row['checked_pixels'] >= 32 and row['quadrants'] == set(range(4)), ('Corner not fully visible', name, row)
        row['quadrants'] = sorted(row['quadrants'])
        row['actual_bg_words'] = [dict(quadrant=q, words=values) for q, values in sorted(row['actual_bg_words'].items())]
    return dict(map=name, cells=rows, undefined_cells_included=True,
                actual_hardware_bg_words_and_scanout_checked=True,
                sprites_and_opaque_ui_explicitly_excluded=True, mismatches_not_discarded=True)


def cold_continue(source, library, output, battery, expected, export_after=None):
    """Use the existing title/menu cold boot with read-only position assertions."""
    path = ROOT/'tools/hoenn/validate_cold_boot.py'
    code = path.read_text()
    anchor = '                    result = dict(bundled_save_continue_to_field=True, field_map=[lib.read8(save+4), lib.read8(save+5)])'
    assert code.count(anchor) == 1
    observer = '''
                    obj = symbols['gObjectEvents']+36*lib.read8(symbols['gPlayerAvatar']+5)
                    result.update(player_tile=[lib.read16(obj+16)-7,lib.read16(obj+18)-7],
                        player_surfing=bool(lib.read8(symbols['gPlayerAvatar'])&8),
                        player_elevation=lib.read8(obj+11)&15,
                        no_callback_script_or_native_call_injection=True)
                    assert result['field_map']==EXPECT['map_id']
                    assert result['player_tile']==EXPECT['tile']
                    assert result['player_surfing'] is EXPECT['surfing']
                    assert result['player_elevation']==EXPECT['elevation']
                    if not EXPECT['surfing']:
                        pixelns={'lib':lib,'s':symbols,'ctypes':ctypes}
                        exec(compile(AVATAR_CODE,'native-avatar-scanout-observer','exec'),pixelns)
                        result['native_avatar_pixels']=pixelns['visible_avatar_pixels']()
                        picture('battery-avatar-visible')
                    if EXPORT_AFTER is not None:
                        press(8)
                        step(90)
                        count=lib.read8(symbols['sNumStartMenuActions'])
                        actions=[lib.read8(symbols['sCurrentStartMenuActions']+i) for i in range(count)]
                        assert actions.count(5)==1, ('SAVE absent from native start menu',actions)
                        target=actions.index(5)
                        for _ in range(12):
                            if lib.read8(symbols['sStartMenuCursorPos'])==target:break
                            press(128)
                        assert lib.read8(symbols['sStartMenuCursorPos'])==target
                        press(1)
                        seen=set()
                        for _ in range(120):
                            callback=lib.read32(symbols['sSaveDialogCallback'])&~1
                            seen.add(callbacks.get(callback,hex(callback)))
                            if callback==symbols['SaveOverwriteInputCallback']:
                                press(64)
                            if 'SaveReturnSuccessCallback' in seen and not lib.read8(symbols['sLockFieldControls']):
                                break
                            press(1)
                        else:raise AssertionError(('Native controller save did not finish',seen))
                        assert 'SaveDoSaveCallback' in seen or 'SaveReturnSuccessCallback' in seen
                        lib.export_save.argtypes=[ctypes.c_char_p]
                        lib.export_save.restype=ctypes.c_int
                        assert lib.export_save(str(EXPORT_AFTER).encode())
                        assert Path(EXPORT_AFTER).stat().st_size==131072
                        picture('migrated-dock-saved-through-menu')
                        result.update(saved_after_continue_with_controllers=True,
                            save_menu_callbacks=sorted(seen),saved_battery_sha256=hashlib.sha256(Path(EXPORT_AFTER).read_bytes()).hexdigest())
'''
    avatar_code = (ROOT/'tools/hoenn/validate_integrated_piers.py').read_text().split('def visible_avatar_pixels():', 1)[1].split('\n\ndef assert_foot', 1)[0]
    ns = {'__file__': str(path), '__name__': 'sevii_boundary_cold_continue', 'EXPECT': expected,
          'EXPORT_AFTER': export_after, 'AVATAR_CODE': 'def visible_avatar_pixels():'+avatar_code}
    exec(compile(code.replace(anchor, anchor+observer), str(path), 'exec'), ns)
    report = ns['validate'](source, library, output, battery)
    report['captures'] = [dict(file=p.name, sha256=digest(p)) for p in sorted(output.glob('*.png'))]
    if export_after is not None:
        report['battery_saves'] = [dict(file=Path(export_after).name, sha256=digest(export_after), bytes=131072)]
    (output/'cold-boot.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


def legacy_dock_battery(source, library, output):
    """Export a genuine layer168 flash save before its geometry is migrated."""
    import sevii_route_boundaries_contract as contract
    assert digest(source/'pokeemerald.gba') == contract.PARENT_ROM_SHA256
    assert digest(source/'pokeemerald.elf') == contract.PARENT_ELF_SHA256
    output.mkdir(parents=True, exist_ok=True)
    path = ROOT/'tools/hoenn/validate_integrated_piers.py'
    code = path.read_text().split('\nchecks = []\ntry:')[0]
    assert code.count('names = sorted(names)') == 1
    code = code.replace('names = sorted(names)', 'names = '+repr([BEACH]))
    sys.argv = [str(path), '--source', str(source), '--library', str(library), '--output', str(output)]
    ns = {'__file__': str(path), '__name__': 'sevii_boundary_legacy_dock_fixture'}
    exec(compile(code, str(path), 'exec'), ns)
    lib = ns['lib']
    try:
        ns['native']('DisableWildEncounters', 1)
        ns['warp'](BEACH, 12, 2)
        ns['native']('SetPlayerAvatarTransitionFlags', 1)
        ns['step'](90)
        before = ns['assert_foot']()
        assert before['map'] == BEACH and before['tile'] == [12, 2]
        ns['picture']('legacy-168-dock')
        assert ns['native']('TrySavingData', 0, max_frames=6000) == 1
        battery = output/'layer168-treasure-dock.sav'
        lib.export_save.argtypes = [ctypes.c_char_p]
        lib.export_save.restype = ctypes.c_int
        assert lib.export_save(str(battery).encode()) and battery.stat().st_size == 131072
        map_id = list(ns['map_id'](BEACH))
    finally:
        lib.stop()
    report = dict(kind='sevii-route-boundaries-legacy-save-fixture', passed=True,
        rom_sha256=contract.PARENT_ROM_SHA256, elf_sha256=contract.PARENT_ELF_SHA256,
        player=before, map_id=map_id, initial_party_progress_and_placement_are_fixtures=True,
        actual_native_flash_export=True,
        captures=[dict(file='legacy-168-dock.png', sha256=digest(output/'legacy-168-dock.png'))],
        battery_saves=[dict(file=battery.name, sha256=digest(battery), bytes=131072)])
    path = output/'legacy-dock-fixture.json'
    path.write_text(json.dumps(report, indent=2)+'\n')
    return battery, report


def baseline_camera_reproduction(source, library, output):
    """Observe the two conflicting layer168 views in a separate native core."""
    import sevii_route_boundaries_contract as contract
    assert digest(source/'pokeemerald.gba') == contract.PARENT_ROM_SHA256
    assert digest(source/'pokeemerald.elf') == contract.PARENT_ELF_SHA256
    output.mkdir(parents=True, exist_ok=True)
    names = sorted({case[key] for case in REPRO_CASES for key in ('map', 'neighbor', 'source_map')})
    path = ROOT/'tools/hoenn/validate_integrated_piers.py'
    code = path.read_text().split('\nchecks = []\ntry:')[0]
    assert code.count('names = sorted(names)') == 1
    code = code.replace('names = sorted(names)', 'names = '+repr(names))
    sys.argv = [str(path), '--source', str(source), '--library', str(library), '--output', str(output)]
    ns = {'__file__': str(path), '__name__': 'sevii_boundary_168_camera_reproduction'}
    exec(compile(code, str(path), 'exec'), ns)
    lib, native = ns['lib'], ns['native']
    captures, cases = [], []
    try:
        native('DisableWildEncounters', 1)
        for index, case in enumerate(REPRO_CASES):
            views = []
            for label, name, point, cell in [('before', case['map'], case['player'], case['cell']),
                                             ('after', case['neighbor'], case['target'], case['neighbor_cell'])]:
                ns['warp'](name, *point)
                ns['step'](90)
                if not lib.read8(ns['s']['gPlayerAvatar'])&8:
                    native('SetPlayerAvatarTransitionFlags', 8)
                    ns['step'](90)
                state = ns['player_state']()
                mid = native('MapGridGetMetatileIdAt', cell[0]+7, cell[1]+7)
                collision = native('MapGridGetCollisionAt', cell[0]+7, cell[1]+7)
                elevation = native('MapGridGetElevationAt', cell[0]+7, cell[1]+7)
                border = native('GetMapBorderIdAt', cell[0]+7, cell[1]+7)
                if label == 'after':
                    assert collision == 1 and elevation == 0 and border == 0xFFFFFFFF
                else:
                    assert collision == 0 and elevation == 1 and border in (1,2,3,4)
                pixels = observe_cells(ns, [(*cell, mid)])
                filename = 'baseline-corner-%d-%s'%(index, label)
                ns['picture'](filename)
                capture = dict(file=filename+'.png', sha256=digest(output/(filename+'.png')))
                captures.append(capture)
                views.append(dict(state=state, cell=cell, metatile=mid, collision=collision,
                    elevation=elevation, border_id=border, pixels=pixels, capture=capture,
                    initial_view_placement_is_a_fixture=True))
            assert [view['metatile'] for view in views] == [299, 579], ('Layer168 camera defect not reproduced', case, views)
            cases.append(dict(case=case, before=views[0], after=views[1],
                same_world_cell=True, reproduced_metatile_disagreement=True))
    finally:
        lib.stop()
    assert digest(source/'pokeemerald.gba') == contract.PARENT_ROM_SHA256
    assert digest(source/'pokeemerald.elf') == contract.PARENT_ELF_SHA256
    result = dict(kind='sevii-route-boundaries-camera-baseline', passed=True,
        expected_broken_baseline=True, bug_reproduced=True, native_validation_performed=True,
        rom_sha256=contract.PARENT_ROM_SHA256, elf_sha256=contract.PARENT_ELF_SHA256,
        initial_views_party_progress_and_encounter_suppression_are_fixtures=True,
        cases=cases, captures=captures)
    (output/'camera-baseline.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--library', type=Path, required=True)
    parser.add_argument('--coldboot-library', type=Path)
    parser.add_argument('--parent-source', type=Path, default=ROOT/'.local/game-continuity-review-src')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    rom_sha, elf_sha = digest(source/'pokeemerald.gba'), digest(source/'pokeemerald.elf')
    marker = json.loads((source/'.journey-sevii-route-boundaries').read_bytes())
    approach = marker['boundaries']['approach']
    assert approach['after_dimensions'] == [40, 48]
    camera_baseline = baseline_camera_reproduction(args.parent_source.resolve(), args.library.resolve(), output/'camera-baseline')
    all_maps = {p.parent.name: json.loads(p.read_bytes()) for p in (source/'data/maps').glob('*/map.json')}
    by_id = {row['id']: name for name, row in all_maps.items()}
    forward = [['OneIsland_Harbor_Frlg', 8, 6], ['JourneySurfLink05001', 8, 6],
               *approach['native_controller_waypoints'], ['OneIsland_Frlg', 12, 17]]
    names = set(BUMP_MAPS)|{START[0]}|{point[0] for point in forward}
    for case in REPRO_CASES:
        names.update([case['map'], case['neighbor'], case['source_map']])
    # The graph is deliberately limited to the requested circuit and bump maps.
    # It cannot substitute a distant ferry or ocean shortcut for the new coast.
    path = ROOT/'tools/hoenn/validate_integrated_piers.py'
    code = path.read_text().split('\nchecks = []\ntry:')[0]
    assert code.count('names = sorted(names)') == 1
    code = code.replace('names = sorted(names)', 'names = '+repr(sorted(names)))
    sys.argv = [str(path), '--source', str(source), '--library', str(args.library.resolve()), '--output', str(output)]
    ns = {'__file__': str(path), '__name__': 'sevii_route_boundaries_native'}
    exec(compile(code, str(path), 'exec'), ns)
    lib, original_native, original_step, original_warp, original_script = (ns[key] for key in ('lib', 'native', 'step', 'warp', 'script'))
    captures, fixtures, inputs, queries, corner_cases, bump_cases = [], [], [], [], [], []
    shoreline_animation = None
    fixture_active, query_depth, phase = True, 0, 'bootstrap'
    native_picture = ns['picture']

    def picture(label):
        native_picture(label)
        capture = dict(file=label+'.png', sha256=digest(output/(label+'.png')))
        captures.append(capture)
        return capture

    def step(count, key=0):
        if not fixture_active:
            if inputs and inputs[-1]['key'] == key and inputs[-1]['phase'] == phase:
                inputs[-1]['frames'] += count
            else:
                inputs.append(dict(phase=phase, frames=count, key=key))
        original_step(count, key)

    def native(name, *values, **kwargs):
        nonlocal query_depth
        if not fixture_active:
            assert name.startswith(('MapGridGet', 'MetatileBehavior_Is')) or name in {
                'GetMapBorderIdAt', 'GetPlayerFacingDirection', 'IsPlayerFacingSurfableFishableWater',
                'PlayerGetElevation', 'JourneyWorldMapPosition', 'TrySavingData'}, ('Forbidden postfixture native call', name)
            queries.append(dict(phase=phase, function=name, arguments=list(values),
                                purpose='native-save' if name == 'TrySavingData' else 'read-only-query'))
        query_depth += 1
        try:
            return original_native(name, *values, **kwargs)
        finally:
            query_depth -= 1

    def guarded_script(*values, **kwargs):
        assert fixture_active or query_depth, 'A gameplay script was injected after placement'
        return original_script(*values, **kwargs)

    def guarded_warp(*values, **kwargs):
        assert fixture_active, 'A midtrip warp was attempted'
        return original_warp(*values, **kwargs)

    ns.update(step=step, native=native, script=guarded_script, warp=guarded_warp,
              walk_transition_pictures=False, walk_max_ticks=4000)

    def state():
        row = ns['player_state']()
        assert row['sprite_visible'] is row['object_visible'] is True
        assert row['elevation'] == (1 if row['surfing'] else 3), row
        # Reapplying a Surf transition to an already surfing fixture creates
        # a second blob. Such a fixture can look like Surf on land even after
        # the genuine dismount destroys its own effect. Count real sprites.
        player_id=lib.read8(ns['s']['gPlayerAvatar']+5)
        row['active_surf_blobs']=sum(bool(lib.read8(ns['s']['gSprites']+68*i+0x3E)&1)
            and (lib.read32(ns['s']['gSprites']+68*i+0x1C)&~1)==ns['s']['UpdateSurfBlobFieldEffect']
            and lib.read16(ns['s']['gSprites']+68*i+0x32)==player_id for i in range(64))
        assert row['active_surf_blobs']==int(row['surfing']),row
        return row

    def place(name, x, y, label):
        nonlocal fixture_active, phase
        fixture_active, phase = True, label
        original_warp(name, x, y)
        step(90)
        if not lib.read8(ns['s']['gPlayerAvatar'])&8:
            original_native('SetPlayerAvatarTransitionFlags', 8)
            step(90)
        fixture_active = False
        row = state()
        assert row['map'] == name and row['tile'] == [x, y] and row['surfing'], row
        fixtures.append(dict(case=label, map=name, tile=[x, y], surfing=True))
        return row

    def grid(cell):
        x, y = cell
        backup = ns['s']['gBackupMapLayout']
        width, height, address = lib.read32(backup), lib.read32(backup+4), lib.read32(backup+8)
        gx, gy = x+7, y+7
        assert 0 <= gx < width and 0 <= gy < height
        return dict(cell=list(cell), grid_block=lib.read16(address+2*(gy*width+gx)),
            metatile=native('MapGridGetMetatileIdAt', gx, gy),
            collision=native('MapGridGetCollisionAt', gx, gy),
            elevation=native('MapGridGetElevationAt', gx, gy),
            border_id=native('GetMapBorderIdAt', gx, gy))

    def corner_view(case, cell, label):
        observed = grid(cell)
        if cell == case['neighbor_cell']:
            assert observed['grid_block'] == 1023 and observed['collision'] == 1
            assert observed['elevation'] == 0 and observed['border_id'] == 0xFFFFFFFF
        else:
            assert observed['grid_block'] == case['source_block']
            assert observed['collision'] == (case['source_block']>>10)&3
            assert observed['elevation'] == case['source_block']>>12
            assert observed['border_id'] in (1,2,3,4)
        assert observed['metatile'] == case['expected_metatile']
        current = state()
        pixels = observe_cells(ns, [(*cell, case['expected_metatile'])])
        return dict(state=current, grid=observed, pixels=pixels, capture=picture(label))

    try:
        original_native('DisableWildEncounters', 1)
        # Prevent a pathfinder detour through terminal events. Connections and
        # Surf dismounts still execute in the unmodified native engine.
        for name in ns['maps']:
            width = ns['blocks'][name][0]
            for event in ns['maps'][name]['warp_events']:
                ns['full_passable'][name].discard(event['y']*width+event['x'])
        ns['warps'] = {name: {} for name in ns['maps']}
        ns['set_passability'](water_only=True)
        for index, case in enumerate(audit_camera_holes(source)['cases']):
            place(case['map'], *case['player'], label='corner-'+str(index))
            before = corner_view(case, case['cell'], 'corner-%d-before'%index)
            ns['walk']((case['neighbor'], *case['target']))
            step(90)
            after = corner_view(case, case['neighbor_cell'], 'corner-%d-after'%index)
            ns['walk']((case['map'], *case['player']))
            step(90)
            returned = corner_view(case, case['cell'], 'corner-%d-return'%index)
            corner_cases.append(dict(case=case, before=before, after=after, returned=returned,
                                     controlled_outbound_and_return=True))
            print('Native undefined corner and controlled return:', case['map'], case['neighbor'], flush=True)
        for index, name in enumerate(BUMP_MAPS):
            width, height, words = ns['blocks'][name]
            layout = ns['layouts'][ns['maps'][name]['layout']]
            small = 0x243 if layout['layout_version'] == 'frlg' else 0x1F9
            choices = []
            for y in range(height):
                for x in range(width):
                    if x not in (0, width-1) and y not in (0, height-1):
                        continue
                    if words[y*width+x] != 0x1400|small:
                        continue
                    for (dx, dy), key in DIRECTIONS.items():
                        sx, sy = x-dx, y-dy
                        rx, ry = sx-dx,sy-dy
                        if 0 <= sx < width and 0 <= sy < height and sy*width+sx in ns['passable'][name] and 0<=rx<width and 0<=ry<height and ry*width+rx in ns['passable'][name]:
                            choices.append((abs(x-width//2)+abs(y-height//2), x, y, sx, sy, key))
            assert choices, ('No reef with an actual Surf approach', name)
            _, x, y, sx, sy, key = min(choices)
            before = place(name, sx, sy, label='boundary-'+str(index))
            collision = native('MapGridGetCollisionAt', x+7, y+7)
            assert collision == 1
            step(120, key)
            step(60)
            after = state()
            assert after['map'] == name and after['tile'] == [sx, sy] and after['surfing'], after
            dx,dy = next(delta for delta,direction in DIRECTIONS.items() if direction==key)
            ns['walk']((name,sx-dx,sy-dy))
            step(60)
            viewpoint = state()
            assert viewpoint['map']==name and viewpoint['tile']==[sx-dx,sy-dy]
            pixels = observe_cells(ns, [(x, y, small)])
            bump_cases.append(dict(map=name, reef_cell=[x, y], reef_metatile=small,
                before=before, after=after, collision=collision, direction_key=key,
                scanout_viewpoint=viewpoint,one_tile_controller_retreat=True,
                held_input_frames=120, pixels=pixels, capture=picture('boundary-%02d-blocked'%index),
                actual_directional_input_blocked=True))
        ns['set_passability']()
        loop_initial = place(*START, label='continuous-south-loop')
        loop_first_transition = len(ns['transitions'])
        loop_first_walked = ns['walked']
        loop_first_prompt = len(ns['surf_prompts'])
        gps = []

        def gps_sample(point, seam=False):
            packed = native('JourneyWorldMapPosition')
            marker_xy = [packed&255, packed >> 8]
            row = dict(map=point[0], tile=list(point[1:]), marker=marker_xy, seam=seam)
            if gps:
                delta = max(abs(a-b) for a, b in zip(marker_xy, gps[-1]['marker']))
                assert delta <= 2, ('Native GPS jumped', gps[-1], row, delta)
                if seam:
                    assert delta == 0, ('Native GPS discontinuity at seam', gps[-1], row)
                row['delta'] = delta
            gps.append(row)

        gps_sample(START)
        ns['walk_observer'] = lambda before, after: gps_sample(after, before[0] != after[0])
        goals = [*forward, *reversed([START, *forward[:-1]])]
        arrivals = []
        for index, goal in enumerate(goals):
            ns['walk'](tuple(goal))
            step(60)
            arrived = state()
            assert [arrived['map'], *arrived['tile']] == goal
            arrivals.append(dict(goal=goal, state=arrived, capture=picture('loop-%02d-arrival'%index)))
            if goal == [BEACH,4,43] and shoreline_animation is None:
                from integrated_ocean_seams import _animation_frames
                from validate_arrival_coast_photos import animation_frames
                frames = {'ocean':_animation_frames(source),
                    'upper_current':animation_frames(source,'water_current_landwatersedge',416,(430,431,432,433)),
                    'upper_sand':animation_frames(source,'sandwatersedge',464,(478,479,480,481))}
                slots = {'ocean':(454,455),'upper_current':(430,431,432,433),
                         'upper_sand':(478,479,480,481)}
                seen = {group:set() for group in frames}
                samples = []
                for sample in range(16):
                    step(8)
                    groups = {}
                    for group,locations in slots.items():
                        raw = b''.join(bytes(lib.read8(0x06000000+slot*32+i) for i in range(32)) for slot in locations)
                        matches = [i for i,data in enumerate(frames[group]) if data==raw]
                        assert matches, ('New southern shore lost native water animation',group,sample)
                        seen[group].update(matches)
                        groups[group] = dict(matches=matches,vram_sha256=hashlib.sha256(raw).hexdigest())
                    samples.append(dict(groups=groups,capture=picture('southern-shore-phase-%02d'%sample)))
                assert all(values==set(range(8)) for values in seen.values()),seen
                shoreline_animation = dict(map=BEACH,tile=[4,43],samples=samples,
                    source_frames_sha256={group:[hashlib.sha256(raw).hexdigest() for raw in values]
                                          for group,values in frames.items()},
                    phases_observed={group:sorted(values) for group,values in seen.items()},
                    callbacks_clocks_palettes_and_vram_not_written=True)
            print('Continuous One southern circuit:', index, goal, flush=True)
        loop_final = state()
        assert loop_final['map'] == START[0] and loop_final['tile'] == START[1:] and loop_final['surfing']
        assert ns['walked']-loop_first_walked > 250
        assert len(gps) > 250
        assert native('TrySavingData', 0, max_frames=6000) == 1
        battery = output/'southern-surf-loop.sav'
        lib.export_save.argtypes = [ctypes.c_char_p]
        lib.export_save.restype = ctypes.c_int
        assert lib.export_save(str(battery).encode()) and battery.stat().st_size == 131072
        expectation = dict(map_id=list(ns['map_id'](START[0])), tile=START[1:], surfing=True, elevation=1)
        loop = dict(initial=loop_initial, final=loop_final, forward_waypoints=forward,
            arrivals=arrivals, gps_samples=gps, maximum_gps_step=max(row.get('delta', 0) for row in gps),
            maximum_seam_delta=max(row.get('delta', 0) for row in gps if row['seam']),
            transitions=ns['transitions'][loop_first_transition:], walked_tiles=ns['walked']-loop_first_walked,
            surf_prompts=ns['surf_prompts'][loop_first_prompt:],
            no_midtrip_warps_or_player_state_writes=True, original_endpoint_roundtrip=True)
    finally:
        lib.stop()
    cold_output = output/'cold-continue'
    cold = cold_continue(source, (args.coldboot_library or args.library).resolve(), cold_output, battery, expectation)
    cold_library = (args.coldboot_library or args.library).resolve()
    legacy_battery, legacy = legacy_dock_battery(args.parent_source.resolve(), args.library.resolve(), output/'legacy-parent')
    migrated_expectation = dict(map_id=legacy['map_id'], tile=[20, 2], surfing=False, elevation=3)
    migration_output = output/'migration-first-continue'
    migration_output.mkdir(parents=True, exist_ok=True)
    migrated_battery = migration_output/'layer169-migrated-dock.sav'
    first_migration = cold_continue(source, cold_library, migration_output, legacy_battery,
                                    migrated_expectation, export_after=migrated_battery)
    repeated_migration = cold_continue(source, cold_library, output/'migration-second-continue',
                                       migrated_battery, migrated_expectation)
    components = []
    for kind, file in [('cold-boot', 'cold-continue/cold-boot.json'),
                       ('camera-baseline', 'camera-baseline/camera-baseline.json'),
                       ('legacy-save-fixture', 'legacy-parent/legacy-dock-fixture.json'),
                       ('migration-first-continue', 'migration-first-continue/cold-boot.json'),
                       ('migration-second-continue', 'migration-second-continue/cold-boot.json')]:
        components.append(dict(kind=kind, file=file, sha256=digest(output/file)))
    assert digest(source/'pokeemerald.gba') == rom_sha and digest(source/'pokeemerald.elf') == elf_sha
    report = dict(kind='sevii-route-boundaries-native', passed=True, rom_sha256=rom_sha, elf_sha256=elf_sha,
        compiled_rom=True, native_validation_performed=True, preflight=False,
        corner_cases=corner_cases, boundary_bumps=bump_cases, southern_loop=loop,
        shoreline_animation=shoreline_animation,
        inputs=inputs, native_calls=queries, fixtures=fixtures, captures=captures,
        initial_party_badges_progress_and_encounter_suppression_are_fixtures=True,
        no_midtrip_position_elevation_camera_palette_or_vram_writes=True,
        no_callback_replacement=True, gameplay_scripts_not_injected_after_placement=True,
        native_getter_trampoline_and_final_save_are_declared=True,
        battery_saves=[dict(file=battery.name, sha256=digest(battery), bytes=131072)],
        camera_baseline=camera_baseline, cold_continue=cold, save_migration=dict(legacy=legacy, first_continue=first_migration,
            second_continue=repeated_migration, old_tile=[12, 2], migrated_tile=[20, 2],
            translation_applied_exactly_once=True, controller_save_between_cold_boots=True),
        components=components, full_campaign_playthrough=False)
    # The arrival coordinates moved with the preserved terrain. Exercise the
    # real New Game/city selection, mother welcome and bedroom as well.
    from validate_coastal_followup_arrivals import validate as validate_arrival, compiled_arrival_census
    arrival_folder=output/'one-island-newgame'
    arrival=validate_arrival(source,cold_library,arrival_folder,'sevii',0,avatar_index=3)
    report['one_island_newgame']=dict(case=arrival,compiled_arrival_census=compiled_arrival_census(source))
    arrival_file=arrival_folder/'arrival-coast-landing-case.json'
    report['components'].append(dict(kind='one-island-newgame',file='one-island-newgame/'+arrival_file.name,
                                     sha256=digest(arrival_file)))
    from verify_sevii_route_boundaries_native import verify_report
    verify_report(report, output, rom_sha)
    destination = output/'sevii-route-boundaries-native.json'
    destination.write_text(json.dumps(report, indent=2)+'\n')
    print('Native Sevii corner, reef, south Surf circuit and cold Continue passed.', flush=True)


if __name__ == '__main__':
    main()
