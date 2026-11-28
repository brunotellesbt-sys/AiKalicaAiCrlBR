"""Continue a real Titan Cave battery, save through the menu and cold boot again."""
import argparse
import hashlib
import json
from pathlib import Path

from validate_cold_boot import validate


def verify_continue(source, library, output, archive):
    old = json.loads((archive / 'sootopolis-rescue.json').read_bytes())['titan_continue']
    battery = archive / 'titan-cave.sav'
    digest = hashlib.sha256(battery.read_bytes()).hexdigest()
    assert digest == old['bundled_save_sha256']
    previous = old['runs'][-1]
    saved = output / 'titan-resaved.sav'
    checks = dict(expected_geometry_version=9, expected_variables=((0x409B, 2), (0x40FF, 0)))
    first = validate(source, library, output / 'first', battery, save_output=saved, **checks)
    second = validate(source, library, output / 'second', saved, **checks)
    assert first['runs'][-1]['saved_battery_sha256'] == second['bundled_save_sha256']
    for report in (first, second):
        resumed = report['runs'][-1]
        assert resumed['field_map'] == previous['field_map']
        assert resumed['player_tile'] == previous['player_tile'] == [6, 7]
        assert resumed['player_surfing'] == previous['player_surfing'] is False
    proof = dict(rom_sha256=first['rom_sha256'], old_rom_sha256=old['rom_sha256'],
                 elf_sha256=hashlib.sha256((source / 'pokeemerald.elf').read_bytes()).hexdigest(),
                 continued=first, resaved=second)
    (output / 'continue.json').write_text(json.dumps(proof, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('source', 'library', 'output', 'archive'):
        parser.add_argument('--' + key, type=Path, required=True)
    verify_continue(**vars(parser.parse_args()))
