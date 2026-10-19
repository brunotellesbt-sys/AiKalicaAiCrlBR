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


def validate(source, library, output, battery=None):
    source, library, output = map(Path, (source, library, output))
    output.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest()
    nm = subprocess.check_output([str(ROOT/'.local/arm-binutils/usr/bin/arm-none-eabi-nm'), '-n', str(source/'pokeemerald.elf')], text=True)
    symbols = {n: int(a, 16) for a, k, n in re.findall(r'^(\w+) (\w) (\S+)$', nm, re.M)}
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
    a = parser.parse_args()
    validate(a.source, a.library, a.output, a.battery)
