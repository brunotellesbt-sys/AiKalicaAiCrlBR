"""Cold boot actual edition bytes with controller input, including TESTE battery save.

Unlike field fixtures, this runner never replaces callbacks, player coordinates,
flags, or EWRAM. Battery saves are loaded explicitly via mCoreLoadSaveFile.
"""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]


def geometry_layout(source):
    """Compile the actual ARM save-field offset, then bind it to the ELF.

    Struct comments contain upstream offsets and are stale in this expanded
    game. The GetVarPointer literal must agree with the compiled layout.
    """
    compiler=ROOT/'.local/arm-gcc/usr/bin/arm-none-eabi-gcc'
    code=('#include "global.h"\n#include "constants/vars.h"\n'
          'const unsigned int journeySaveLayout[]={__builtin_offsetof(struct SaveBlock1,vars),'
          'VAR_JOURNEY_SEVII_GEOMETRY_VERSION,VARS_START,JOURNEY_SEVII_GEOMETRY_VERSION_CURRENT};\n')
    with tempfile.TemporaryDirectory(prefix='journey-save-layout-') as directory:
        path=Path(directory)/'layout.c';assembly=path.with_suffix('.s');path.write_text(code)
        subprocess.run([str(compiler),'-mabi=apcs-gnu','-mcpu=arm7tdmi','-mthumb','-std=gnu17',
            '-DMODERN=1','-DTESTING=0','-DEMERALD','-iquote',str(source/'include'),'-S',str(path),'-o',str(assembly)],
            check=True,capture_output=True)
        raw=assembly.read_bytes();values=[int(v) for v in re.findall(r'^\s*\.word\s+(-?\d+)\s*$',raw.decode(),re.M)]
    assert len(values)==4,('Save layout compiler returned unexpected initializer',values)
    offset,variable,start,current=values
    assert offset%2==0 and start<=variable<0x8000
    disassembly=subprocess.check_output([str(ROOT/'.local/arm-binutils/usr/bin/arm-none-eabi-objdump'),
        '-d','--disassemble=GetVarPointer',str(source/'pokeemerald.elf')],text=True)
    constants={int(v,16) for v in re.findall(r'\.word\s+0x([a-fA-F0-9]+)',disassembly)}
    assert ((offset//2-start)&0xffffffff) in constants,'GetVarPointer differs from the actual compiled save layout'
    return dict(vars_offset=offset,variable=variable,vars_start=start,current_version=current,
        actual_ARM_APCS_struct_compiled=True,GetVarPointer_ELF_literal_matches=True,
        probe_assembly_sha256=hashlib.sha256(raw).hexdigest(),
        global_header_sha256=hashlib.sha256((source/'include/global.h').read_bytes()).hexdigest())


def backup_grid_layout(source):
    code=('#include "global.h"\nconst unsigned int gridLayout[]={'
          '__builtin_offsetof(struct BackupMapLayout,width),'
          '__builtin_offsetof(struct BackupMapLayout,height),'
          '__builtin_offsetof(struct BackupMapLayout,map)};\n')
    with tempfile.TemporaryDirectory(prefix='journey-grid-layout-') as directory:
        p=Path(directory)/'grid.c';p.write_text(code);out=p.with_suffix('.s')
        subprocess.run([str(ROOT/'.local/arm-gcc/usr/bin/arm-none-eabi-gcc'),'-mabi=apcs-gnu',
            '-mcpu=arm7tdmi','-mthumb','-std=gnu17','-DMODERN=1','-DTESTING=0','-DEMERALD',
            '-iquote',str(source/'include'),'-S',str(p),'-o',str(out)],check=True,capture_output=True)
        raw=out.read_bytes();values=[int(v) for v in re.findall(r'^\s*\.word\s+(-?\d+)\s*$',raw.decode(),re.M)]
    assert len(values)==3
    return dict(zip(('width','height','map'),values)),hashlib.sha256(raw).hexdigest()


def field_state_layout(source):
    fields={
        'flags':'__builtin_offsetof(struct SaveBlock1,flags)',
        'flags_size':'sizeof(((struct SaveBlock1*)0)->flags)',
        'saved_templates':'__builtin_offsetof(struct SaveBlock1,objectEventTemplates)',
        'template_size':'sizeof(struct ObjectEventTemplate)',
        'template_local_id':'__builtin_offsetof(struct ObjectEventTemplate,localId)',
        'template_count':'sizeof(((struct SaveBlock1*)0)->objectEventTemplates)/sizeof(struct ObjectEventTemplate)',
        'object_size':'sizeof(struct ObjectEvent)',
        'object_local_id':'__builtin_offsetof(struct ObjectEvent,localId)',
        'object_map_num':'__builtin_offsetof(struct ObjectEvent,mapNum)',
        'object_map_group':'__builtin_offsetof(struct ObjectEvent,mapGroup)',
        'object_x':'__builtin_offsetof(struct ObjectEvent,currentCoords.x)',
        'object_y':'__builtin_offsetof(struct ObjectEvent,currentCoords.y)',
        'object_count':'OBJECT_EVENTS_COUNT',
        'header_events':'__builtin_offsetof(struct MapHeader,events)',
        'event_object_count':'__builtin_offsetof(struct MapEvents,objectEventCount)',
        'event_objects':'__builtin_offsetof(struct MapEvents,objectEvents)',
    }
    code='#include "global.h"\n#include "event_object_movement.h"\nconst unsigned int fieldLayout[]={'+','.join(fields.values())+'};\n'
    with tempfile.TemporaryDirectory(prefix='journey-cold-field-layout-') as directory:
        path=Path(directory)/'field.c';path.write_text(code);assembly=path.with_suffix('.s')
        subprocess.run([str(ROOT/'.local/arm-gcc/usr/bin/arm-none-eabi-gcc'),'-mabi=apcs-gnu','-mcpu=arm7tdmi','-mthumb',
            '-std=gnu17','-DMODERN=1','-DTESTING=0','-DEMERALD','-iquote',str(source/'include'),'-S',str(path),'-o',str(assembly)],check=True,capture_output=True)
        raw=assembly.read_bytes();values=[int(v) for v in re.findall(r'^\s*\.word\s+(-?\d+)\s*$',raw.decode(),re.M)]
    assert len(values)==len(fields),('Unexpected field-state ABI',values)
    return dict(offsets=dict(zip(fields,values)),actual_ARM_APCS_struct_compiled=True,
                assembly_sha256=hashlib.sha256(raw).hexdigest(),read_only_RAM_observation=True)


def validate(source, library, output, battery=None, save_output=None, expected_geometry_version=None, expected_map_cells=(),
             *, expected_flags=(), verify_current_map_objects=False, require_cleared_template_tail=False):
    source, library, output = map(Path, (source, library, output))
    output.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest()
    nm = subprocess.check_output([str(ROOT/'.local/arm-binutils/usr/bin/arm-none-eabi-nm'), '-n', str(source/'pokeemerald.elf')], text=True)
    symbols = {n: int(a, 16) for a, k, n in re.findall(r'^(\w+) (\w) (\S+)$', nm, re.M)}
    layout=geometry_layout(source) if expected_geometry_version is not None else None
    grid_layout,grid_probe_sha=backup_grid_layout(source) if expected_map_cells else (None,None)
    field_layout=field_state_layout(source) if expected_flags or verify_current_map_objects else None
    callbacks = {v: k for k, v in symbols.items()}
    lib = ctypes.CDLL(str(library.resolve()))
    lib.start.argtypes = [ctypes.c_char_p]
    lib.load_save.argtypes = [ctypes.c_char_p]
    lib.image.restype = ctypes.c_void_p
    lib.read32.restype = ctypes.c_uint32
    runs = []

    def run(save_file):
        with tempfile.TemporaryDirectory(prefix='journey-cold-boot-', dir='/tmp') as directory:
            rom = Path(directory)/'cold-boot.gba'
            shutil.copyfile(source/'pokeemerald.gba', rom)
            assert lib.start(str(rom).encode())
            try:
                if save_file:
                    assert lib.load_save(str(Path(save_file).resolve()).encode()), 'Battery save not loaded'
                samples = []
                frames = 0
                def step(count, key=0):
                    nonlocal frames
                    while count:
                        n = min(count, 30)
                        lib.frames(n, key)
                        frames += n
                        count -= n
                        rgba = ctypes.string_at(lib.image(), 240*160*4)
                        blue = sum(rgba[i] < 32 and rgba[i+1] < 32 and rgba[i+2] > 220 for i in range(0, len(rgba), 4))
                        assert blue < 240*160*.7, ('Blue assertion screen on cold boot', save_file, frames)
                    cb = lib.read32(symbols['gMain']+4) & ~1
                    samples.append(dict(frame=frames, callback=callbacks.get(cb, hex(cb))))
                def press(key=1):
                    step(1, key)
                    step(90)
                def picture(name):
                    Image.frombytes('RGBA', (240,160), ctypes.string_at(lib.image(), 240*160*4)).convert('RGB').save(output/(name+'.png'))
                def tasks():
                    return {callbacks.get(lib.read32(symbols['gTasks']+i*40)&~1, '') for i in range(16) if lib.read8(symbols['gTasks']+i*40+4)}
                step(1200)
                press(8)  # Skip the opening animation through the real title path.
                step(300)
                picture('battery-title' if save_file else 'fresh-title')
                assert (lib.read32(symbols['gMain']+4)&~1) == symbols['MainCB2'], samples
                for _ in range(12):
                    press()
                    if (lib.read32(symbols['gMain']+4)&~1) == symbols['CB2_MainMenu']:
                        break
                step(300)
                assert (lib.read32(symbols['gMain']+4)&~1) == symbols['CB2_MainMenu'], samples
                picture('battery-main-menu' if save_file else 'fresh-main-menu')
                press()
                if save_file:
                    step(900)
                    assert (lib.read32(symbols['gMain']+4)&~1) == symbols['CB2_Overworld'], samples
                    step(600)
                    picture('battery-continued-to-field')
                    save = lib.read32(symbols['gSaveBlock1Ptr'])
                    result = dict(bundled_save_continue_to_field=True, field_map=[lib.read8(save+4), lib.read8(save+5)])
                    obj=symbols['gObjectEvents']+36*lib.read8(symbols['gPlayerAvatar']+5)
                    result.update(player_tile=[lib.read16(obj+16)-7,lib.read16(obj+18)-7],
                                  player_surfing=bool(lib.read8(symbols['gPlayerAvatar'])&8),
                                  player_elevation=lib.read8(obj+11)&15)
                    if expected_map_cells:
                        base=symbols['gBackupMapLayout'];width=lib.read32(base+grid_layout['width'])
                        height=lib.read32(base+grid_layout['height']);data=lib.read32(base+grid_layout['map'])
                        observed=[]
                        for x,y,word in expected_map_cells:
                            assert 0<=x+7<width and 0<=y+7<height
                            actual=lib.read16(data+2*((y+7)*width+x+7))
                            assert actual==word,('Continued native map grid differs',x,y,actual,word)
                            observed.append(dict(tile=[x,y],word=actual))
                        result['continued_native_map_grid_cells']=observed
                    if layout is not None:
                        actual=lib.read16(save+layout['vars_offset']+2*(layout['variable']-layout['vars_start']))
                        assert actual==expected_geometry_version,('Saved geometry migration did not finish',actual,expected_geometry_version)
                        result['geometry_version']=actual
                    if field_layout is not None:
                        fields=field_layout['offsets']
                        flag_values=[]
                        for flag,wanted in dict(expected_flags).items():
                            assert 0<flag<fields['flags_size']*8,('Flag outside actual persisted array',flag)
                            actual=bool(lib.read8(save+fields['flags']+flag//8)&(1<<(flag&7)))
                            assert actual==bool(wanted),('Continue changed a persistent capture/progress flag',flag,actual,wanted)
                            flag_values.append(dict(flag=flag,value=actual))
                        result['persistent_flags_checked']=flag_values
                        if verify_current_map_objects:
                            events=lib.read32(symbols['gMapHeader']+fields['header_events'])
                            count=lib.read8(events+fields['event_object_count'])
                            templates=lib.read32(events+fields['event_objects'])
                            expected_ids=[lib.read8(templates+i*fields['template_size']+fields['template_local_id']) for i in range(count)]
                            saved_all=[lib.read8(save+fields['saved_templates']+i*fields['template_size']+fields['template_local_id']) for i in range(fields['template_count'])]
                            saved_ids=saved_all[:count]
                            unused=[v for v in saved_all[count:] if v]
                            assert saved_ids==expected_ids,('Continue retained old actor templates',saved_ids,expected_ids)
                            if require_cleared_template_tail:
                                assert not unused,('Removed actor templates remain in the saved tail',unused)
                            active=[]
                            for i in range(fields['object_count']):
                                at=symbols['gObjectEvents']+i*fields['object_size']
                                if not lib.read8(at)&1:
                                    continue
                                local_id=lib.read8(at+fields['object_local_id'])
                                if local_id>=0xFD:
                                    continue
                                identity=[lib.read8(at+fields['object_map_group']),lib.read8(at+fields['object_map_num'])]
                                if identity!=result['field_map']:
                                    continue
                                assert local_id in expected_ids,('Old actor remains active after Continue',local_id,expected_ids)
                                active.append(dict(local_id=local_id,tile=[lib.read16(at+fields['object_x'])-7,lib.read16(at+fields['object_y'])-7]))
                            result['native_object_templates']=dict(compiled_local_ids=expected_ids,saved_local_ids=saved_ids,
                                active_current_map_objects=active,unused_saved_template_local_ids=unused,
                                all_active_objects_are_current_templates=True,unused_templates_cleared=not unused)
                    if save_output is not None:
                        press(8);step(90)
                        count=lib.read8(symbols['sNumStartMenuActions'])
                        actions=[lib.read8(symbols['sCurrentStartMenuActions']+i) for i in range(count)]
                        assert actions.count(5)==1,('SAVE absent from native start menu',actions)
                        target=actions.index(5)
                        for _ in range(12):
                            if lib.read8(symbols['sStartMenuCursorPos'])==target:break
                            press(128)
                        assert lib.read8(symbols['sStartMenuCursorPos'])==target
                        press(1);seen=set()
                        for _ in range(120):
                            callback=lib.read32(symbols['sSaveDialogCallback'])&~1
                            seen.add(callbacks.get(callback,hex(callback)))
                            if callback==symbols['SaveOverwriteInputCallback']:press(64)
                            if 'SaveReturnSuccessCallback' in seen and not lib.read8(symbols['sLockFieldControls']):break
                            press(1)
                        else:raise AssertionError(('Native controller save did not finish',seen))
                        assert 'SaveReturnSuccessCallback' in seen
                        destination=Path(save_output).resolve();destination.parent.mkdir(parents=True,exist_ok=True)
                        lib.export_save.argtypes=[ctypes.c_char_p];lib.export_save.restype=ctypes.c_int
                        assert lib.export_save(str(destination).encode())
                        assert destination.stat().st_size==131072
                        picture('battery-saved-through-menu')
                        result.update(saved_after_continue_with_controllers=True,
                                      save_menu_callbacks=sorted(seen),
                                      saved_battery_sha256=hashlib.sha256(destination.read_bytes()).hexdigest())
                else:
                    step(300)
                    active = tasks()
                    assert any('NewGameBirchSpeech' in name or name in ('Task_HandleMultichoiceGridInput', 'Task_JourneyIntroRegion') for name in active), (active, samples)
                    picture('fresh-new-game')
                    result = dict(fresh_rom_boot_to_title=True, fresh_rom_title_to_new_game=True, new_game_tasks=sorted(active))
                runs.append(dict(battery=bool(save_file), frames=frames, samples=samples, **result))
            finally:
                lib.stop()
    run(None)
    if battery:
        run(battery)
    assert hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest() == sha
    report = dict(passed=True, rom_sha256=sha, fresh_rom_boot_to_title=True,
                  fresh_rom_title_to_new_game=True, no_assert_screen=True,
                  controllers_only=True, no_game_memory_writes=True,
                  bundled_save_tested=bool(battery), runs=runs)
    if layout is not None:
        report['geometry_layout_proof']=layout
    if grid_layout is not None:
        report['backup_grid_layout_proof']=dict(offsets=grid_layout,actual_ARM_APCS_struct_compiled=True,
                                               assembly_sha256=grid_probe_sha,read_only_RAM_observation=True)
    if field_layout is not None:
        report['field_state_layout_proof']=field_layout
    if battery:
        report.update(bundled_save_continue_to_field=True,
                      bundled_save_sha256=hashlib.sha256(Path(battery).read_bytes()).hexdigest())
    (output/'cold-boot.json').write_text(json.dumps(report, indent=2)+'\n')
    print('Cold boot, title and '+('battery Continue' if battery else 'New Game')+' passed:', source.name, flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--library', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--battery', type=Path)
    parser.add_argument('--save-output',type=Path)
    parser.add_argument('--expected-geometry-version',type=int)
    parser.add_argument('--expect-cell',nargs=3,type=lambda v:int(v,0),action='append',default=[],metavar=('X','Y','WORD'))
    a = parser.parse_args()
    validate(a.source, a.library, a.output, a.battery,a.save_output,a.expected_geometry_version,a.expect_cell)
