"""Audit compiled Mega form links, held items and asset references."""
import argparse
import json
from pathlib import Path
import re
import struct
import subprocess
import tempfile
from audit_native_catalog import audit, ROOT


def audit_megas(source):
    source = Path(source)
    catalog = audit(source)
    rom = (source / 'pokeemerald.gba').read_bytes()
    declarations = ['sizeof(struct SpeciesInfo)', 'offsetof(struct SpeciesInfo, formChangeTable)',
                    'sizeof(struct FormChange)', 'offsetof(struct FormChange, method)',
                    'offsetof(struct FormChange, targetSpecies)', 'offsetof(struct FormChange, param1)',
                    'FORM_CHANGE_TERMINATOR', 'FORM_CHANGE_BATTLE_MEGA_EVOLUTION_ITEM',
                    'FORM_CHANGE_BATTLE_MEGA_EVOLUTION_MOVE', 'sizeof(struct ItemInfo)',
                    'offsetof(struct ItemInfo, holdEffect)', 'HOLD_EFFECT_MEGA_STONE', 'ITEMS_COUNT']
    with tempfile.TemporaryDirectory(prefix='mega-abi-', dir='/tmp') as directory:
        temp = Path(directory)
        (temp / 'abi.c').write_text('#include "global.h"\n#include "pokemon.h"\n#include "item.h"\n'
                                  '#include "constants/hold_effects.h"\n#include <stddef.h>\n'
                                  'const unsigned fields[] = {' + ','.join(declarations) + '};\n')
        subprocess.run([str(ROOT / '.local/arm-gcc/usr/bin/arm-none-eabi-gcc'), '-S', '-iquote',
                        str(source / 'include'), '-DMODERN=1', '-DPOKEEMERALD', '-mthumb',
                        '-march=armv4t', '-mabi=apcs-gnu', str(temp / 'abi.c'), '-o', str(temp / 'abi.s')], check=True)
        abi = [int(n) for n in re.findall(r'\.word\s+(\d+)', (temp / 'abi.s').read_text())]
    symbols = subprocess.check_output([str(ROOT / '.local/arm-binutils/usr/bin/arm-none-eabi-nm'),
                                       '--defined-only', str(source / 'pokeemerald.elf')], text=True)
    def symbol(name):
        return int(re.search(r'^([0-9a-f]+) . ' + name + '$', symbols, re.M)[1], 16) - 0x08000000
    species_address, item_address = symbol('gSpeciesInfo'), symbol('gItemsInfo')
    items = {int(value): name for name, value in re.findall(r'\b(ITEM_\w+)\s*=\s*(\d+)',
                                                          (source / 'include/constants/items.h').read_text())}
    species = catalog['species']
    forms = {int(i) for i, row in species.items() if row['flags'] & (1 << 6)}
    links = []
    incomplete_assets = []
    for target in sorted(forms):
        assets = species[str(target)].get('assets', {})
        missing = sorted({'front', 'back', 'palette', 'shiny_palette'} - set(assets))
        if missing:
            incomplete_assets.append(dict(id=target, species=species[str(target)]['name'], missing=missing))
    for key, row in species.items():
        if row['flags'] & (1 << 6):
            continue
        pointer = struct.unpack_from('<I', rom, species_address + int(key) * abi[0] + abi[1])[0]
        if not pointer:
            continue
        offset = pointer - 0x08000000
        assert 0 <= offset < len(rom), row['name']
        for index in range(128):
            at = offset + index * abi[2]
            method = struct.unpack_from('<H', rom, at + abi[3])[0]
            if method == abi[6]:
                break
            if method not in abi[7:9]:
                continue
            target = struct.unpack_from('<H', rom, at + abi[4])[0]
            requirement = struct.unpack_from('<H', rom, at + abi[5])[0]
            assert target in forms, (row['name'], target)
            assets = species[str(target)].get('assets', {})
            is_item = method == abi[7]
            if is_item:
                assert 0 < requirement < abi[12]
                assert rom[item_address + requirement * abi[9] + abi[10]] == abi[11], requirement
            links.append(dict(species_id=int(key), species=row['name'], target_id=target,
                              target=species[str(target)]['name'], requirement_id=requirement,
                              requirement=items.get(requirement, str(requirement)) if is_item else 'move:' + str(requirement),
                              method='item' if is_item else 'move',
                              assets=assets))
        else:
            raise AssertionError(('Unterminated form table', row['name']))
    missing = sorted(forms - {link['target_id'] for link in links})
    return dict(passed=catalog['passed'] and not missing and not incomplete_assets, rom_sha256=catalog['rom_sha256'],
                enabled_mega_forms=len(forms), reachable_mega_forms=len(forms)-len(missing),
                missing_mega_targets=missing, incomplete_assets=incomplete_assets, links=links,
                all_sprites_rendered=False, stones_distributed=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit_megas(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print({k: v for k, v in result.items() if k != 'links'})
    assert result['passed']
