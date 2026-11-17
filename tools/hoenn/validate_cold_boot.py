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


def validate(source, library, output, battery=None, save_output=None, expected_geometry_version=None):
    source, library, output = map(Path, (source, library, output))
    output.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest()
    nm = subprocess.check_output([str(ROOT/'.local/arm-binutils/usr/bin/arm-none-eabi-nm'), '-n', str(source/'pokeemerald.elf')], text=True)
    symbols = {n: int(a, 16) for a, k, n in re.findall(r'^(\w+) (\w) (\S+)$', nm, re.M)}
    layout=geometry_layout(source) if expected_geometry_version is not None else None
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
                    if layout is not None:
                        actual=lib.read16(save+layout['vars_offset']+2*(layout['variable']-layout['vars_start']))
                        assert actual==expected_geometry_version,('Saved geometry migration did not finish',actual,expected_geometry_version)
                        result['geometry_version']=actual
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
    a = parser.parse_args()
    validate(a.source, a.library, a.output, a.battery,a.save_output,a.expected_geometry_version)
