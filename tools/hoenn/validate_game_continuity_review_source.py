"""Replay layer 168 and bind the campaign guard and camera banks to the ROM."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile

import game_continuity_review_contract as contract

ROOT = Path(__file__).resolve().parents[2]
RUNTIME_SYMBOLS = ('JourneyPendingCampaignEvent', 'JourneyStoryObjectVisible', 'JourneyCurrentGymGate')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def symbols(source):
    raw = subprocess.check_output([str(ROOT/'.local/arm-binutils/usr/bin/arm-none-eabi-nm'),
        '-S', '--defined-only', str(source/'pokeemerald.elf')], text=True)
    return {name: (int(address,16), int(size,16) if size else 0)
            for address,size,name in re.findall(r'^([\da-fA-F]+)\s+(?:([\da-fA-F]+)\s+)?\w\s+(\S+)$',raw,re.M)}


def validate(source, baseline, output, preflight=False):
    from prepare_game_continuity_review import PRIOR, prepare, verify_parent
    source,baseline,output = map(Path,(source,baseline,output))
    assert source.resolve() != baseline.resolve()
    expected = verify_parent(baseline)
    marker = json.loads((source/('.journey-'+contract.SCOPE)).read_bytes())
    changes = marker['prepared_sha256']
    assert contract.PREPARED_SHA256, 'Pin reviewed follow-up paths and hashes before source validation'
    assert changes == contract.PREPARED_SHA256, 'Game-continuity source scope or bytes differ from the review'
    assert marker['parent_rom_sha256'] == contract.PARENT_ROM_SHA256
    assert all(sha != expected.get(name) for name,sha in changes.items()), 'No-op staged file'
    for name,sha in (expected|changes).items():
        assert digest(source/name) == sha, ('Unexpected source change',name)
    for name in ['.source-acquired.json', *['.journey-'+layer for layer in PRIOR]]:
        assert (source/name).read_bytes() == (baseline/name).read_bytes(), name
    preserved = {name:sha for name,sha in expected.items()
                 if name.startswith(('data/maps/','data/layouts/','data/tilesets/')) and name not in changes}
    protected = {
        'src/journey_birth.c', 'include/journey_birth_arrivals.h', 'src/overworld.c', 'src/event_object_movement.c',
        'src/wild_encounter.c', 'src/metatile_behavior.c', 'src/data/wild_encounters.json',
        'include/journey_wild_data.h', 'include/journey_generation4_pools.h', 'include/journey_habitat_data.h',
        'include/journey_generation4_habitats.h', 'src/data/journey_world_dex_locations.h',
        'include/global.h', 'include/constants/flags.h', 'include/constants/vars.h',
        'src/data/journey_world_map.h', 'src/data/journey_world_position.h'}
    assert not protected.intersection(changes), ('Protected arrival/pier/ecology/save/atlas source changed',protected.intersection(changes))
    assert not any(name.startswith('data/maps/') and name.endswith('/scripts.inc') for name in changes)
    with tempfile.TemporaryDirectory(prefix='game-continuity-replay-',dir='/tmp') as directory:
        replay = Path(directory)
        for name in [*expected,'.source-acquired.json',*['.journey-'+layer for layer in PRIOR]]:
            path = replay/name
            path.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(baseline/name,path)
        fresh = prepare(replay)
        assert fresh == marker and prepare(replay) == fresh, 'Independent repair replay or idempotence mismatch'

    compiled_blocks,compiled_banks,runtime = [],[],[]
    rom_sha = elf_sha = None
    if not preflight:
        rom = (source/'pokeemerald.gba').read_bytes()
        assert len(rom) == 33554432 and rom[-4096:] == b'\xff'*4096
        assert rom[0xBD] == (-sum(rom[0xA0:0xBD])-0x19)&255
        rom_sha,elf_sha = hashlib.sha256(rom).hexdigest(),digest(source/'pokeemerald.elf')
        assert rom_sha != contract.PARENT_ROM_SHA256
        table = symbols(source)
        for name in RUNTIME_SYMBOLS:
            assert name in table, ('Missing compiled campaign path',name)
            address,size = table[name]
            assert 0x08000000 <= address < 0x0A000000 and size > 0
            code = rom[address-0x08000000:address-0x08000000+size]
            assert len(code) == size and code != b'\xff'*size
            runtime.append(dict(symbol=name,address=address,bytes=size,sha256=hashlib.sha256(code).hexdigest()))
        layouts = json.loads((source/'data/layouts/layouts.json').read_bytes())['layouts']
        old_layouts = {row['id']:row for row in json.loads((baseline/'data/layouts/layouts.json').read_bytes())['layouts']}
        assert {row['id'] for row in layouts} == set(old_layouts), 'Camera fix must not create/delete layouts'
        for row in layouts:
            old = old_layouts[row['id']]
            if row == old:
                continue
            assert {k:v for k,v in row.items() if k not in ('primary_tileset','secondary_tileset')} == {
                k:v for k,v in old.items() if k not in ('primary_tileset','secondary_tileset')}, row['id']
            assert all(name in table for name in (row['name'],row['primary_tileset'],row['secondary_tileset']))
            address,_ = table[row['name']]
            offset = address-0x08000000
            width,height = struct.unpack_from('<II',rom,offset)
            primary,secondary = struct.unpack_from('<II',rom,offset+16)
            assert (width,height) == (row['width'],row['height'])
            assert primary == table[row['primary_tileset']][0] and secondary == table[row['secondary_tileset']][0]
            compiled_banks.append(dict(layout=row['id'],symbol=row['name'],address=address,
                primary_symbol=row['primary_tileset'],secondary_symbol=row['secondary_tileset'],
                primary_pointer=primary,secondary_pointer=secondary,compiled_bank_pointers_match=True))
        assert compiled_banks, 'The reviewed coastal camera assignments need compiled bindings'
        block_symbols = {row['blockdata_filepath']:row['name']+'_Blockdata' for row in layouts}
        definitions = (source/'src/data/tilesets/metatiles.h').read_text()
        block_symbols.update({path:name for name,path in re.findall(
            r'const\s+u(?:8|16|32)\s+(\w+)\[\]\s*=\s*INCBIN_U(?:8|16|32)\("([^"]+)"\)',definitions)})
        for path in sorted(name for name in changes if name.endswith('.bin')):
            assert path in block_symbols, ('Changed binary needs an explicit compiled binding',path)
            name = block_symbols[path]
            assert name in table
            address,size = table[name]
            raw = (source/path).read_bytes()
            assert size in (0,len(raw)) and rom[address-0x08000000:address-0x08000000+len(raw)] == raw
            compiled_blocks.append(dict(file=path,symbol=name,bytes=len(raw),sha256=digest(source/path)))
    report = dict(kind='game-continuity-source',passed=not preflight,preflight=bool(preflight),compiled_rom=not preflight,
        rom_sha256=rom_sha,elf_sha256=elf_sha,parent_rom_sha256=contract.PARENT_ROM_SHA256,layers=PRIOR+[contract.SCOPE],
        changed_files=sorted(changes),prepared_sha256=changes,source_hashes_checked=len(expected|changes),
        independent_replay=True,idempotent=True,unrelated_source_files_unchanged=True,
        atlas_graphics_unchanged=True,unrelated_maps_layouts_and_tilesets_unchanged=True,
        ecology_and_battle_source_unchanged=True,arrival_and_pier_source_unchanged=True,
        event_scripts_and_save_abi_unchanged=True,preserved_spatial_inputs=len(preserved),
        preserved_spatial_inputs_sha256=hashlib.sha256(json.dumps(preserved,sort_keys=True).encode()).hexdigest(),
        compiled_blockdata=compiled_blocks,compiled_layout_banks=compiled_banks,compiled_runtime_symbols=runtime,
        compiled_campaign_and_camera_observations_have_separate_native_proofs=True,full_campaign_playthrough=False)
    verify_parent(baseline)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--baseline',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--preflight',action='store_true')
    args = parser.parse_args()
    print(json.dumps(validate(args.source,args.baseline,args.output,args.preflight),indent=2))
