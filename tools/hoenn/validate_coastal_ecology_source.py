"""Replay layer 166 independently and bind its narrow source scope to the ELF."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from coastal_ecology_contract import PARENT_ROM_SHA256, SCOPE
from prepare_coastal_ecology import PRIOR,prepare,verify_parent

ROOT=Path(__file__).resolve().parents[2]
ALLOWED_SOURCE_FILES=frozenset({
    'src/data/wild_encounters.json',
    'include/journey_wild_data.h',
    'include/journey_generation4_pools.h',
    'include/journey_habitat_data.h',
    'include/journey_generation4_habitats.h',
    'src/data/journey_world_dex_locations.h',
    'src/wild_encounter.c',
    'src/metatile_behavior.c',
    'src/overworld.c',
    'src/event_object_movement.c',
    'src/field_door.c',
    'include/tilesets.h',
    'src/data/tilesets/headers.h',
    'src/data/tilesets/metatiles.h',
    'data/layouts/layouts.json',
    'data/layouts/PalletTown_Frlg/map.bin',
    'data/layouts/OneIsland_TreasureBeach_Frlg/map.bin',
    'data/layouts/OneIsland_Frlg/map.bin',
    'data/layouts/OneIsland_KindleRoad_Frlg/map.bin',
    'data/layouts/Route12_Frlg/map.bin',
    'data/layouts/Route13_Frlg/map.bin',
    'data/layouts/Route17_Frlg/map.bin',
    'data/layouts/Route19_Frlg/map.bin',
    'data/layouts/Route21_North_Frlg/map.bin',
    'data/layouts/SevenIsland_TrainerTower_Frlg/map.bin',
    'data/layouts/SixIsland_WaterPath_Frlg/map.bin',
    'data/layouts/VermilionCity_Frlg/map.bin',
    'data/tilesets/primary/general_frlg/journey_sevii_sea_metatiles.bin',
    'data/tilesets/secondary/sevii_islands_123_frlg/journey_sevii_sea_metatiles.bin',
    'data/tilesets/secondary/journey_sevii_integrated_123/metatiles.bin',
    'data/tilesets/secondary/sevii_islands_45_frlg/journey_sevii_sea_metatiles.bin',
    'data/tilesets/secondary/journey_sevii_integrated_45/metatiles.bin',
    'data/tilesets/secondary/sevii_islands_67_frlg/journey_sevii_sea_metatiles.bin',
    'data/tilesets/secondary/journey_sevii_integrated_67/metatiles.bin',
    'data/tilesets/secondary/cinnabar_island_frlg/journey_kanto_sea_metatiles.bin',
    'data/tilesets/secondary/pallet_town_frlg/journey_kanto_sea_metatiles.bin',
    'data/tilesets/secondary/lavender_town_frlg/journey_kanto_sea_metatiles.bin',
    'data/tilesets/secondary/vermilion_city_frlg/journey_kanto_sea_metatiles.bin',
})


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def symbols(source):
    raw=subprocess.check_output([str(ROOT/'.local/arm-binutils/usr/bin/arm-none-eabi-nm'),
        '-S','--defined-only',str(source/'pokeemerald.elf')],text=True)
    return {name:(int(address,16),int(size,16) if size else 0)
            for address,size,name in re.findall(r'^([\da-fA-F]+)\s+(?:([\da-fA-F]+)\s+)?\w\s+(\S+)$',raw,re.M)}


def validate(source,baseline,output,preflight=False):
    source,baseline,output=map(Path,(source,baseline,output))
    assert source.resolve()!=baseline.resolve()
    expected=verify_parent(baseline)
    marker=json.loads((source/('.journey-'+SCOPE)).read_bytes())
    changes=marker['prepared_sha256']
    assert set(changes)==ALLOWED_SOURCE_FILES, ('Ecology source scope differs from the reviewed files',
        set(changes)-ALLOWED_SOURCE_FILES,ALLOWED_SOURCE_FILES-set(changes))
    assert marker['parent_rom_sha256']==PARENT_ROM_SHA256
    assert all(sha!=expected.get(name) for name,sha in changes.items()), 'No-op staged file'
    for name,sha in (expected|changes).items():
        assert digest(source/name)==sha, ('Unexpected source change',name)
    for name in ['.source-acquired.json',*['.journey-'+layer for layer in PRIOR]]:
        assert (source/name).read_bytes()==(baseline/name).read_bytes(),name
    # A geometry regression cannot hide behind an encounter-only release.
    preserved={}
    for name,sha in expected.items():
        if name.startswith(('data/maps/','data/layouts/','data/tilesets/')) or name in (
            'src/data/journey_world_map.h','src/data/journey_world_position.h',
            'include/global.h','include/constants/flags.h','include/constants/vars.h'):
            if name not in changes:
                assert name not in changes and digest(source/name)==sha,name
                preserved[name]=sha
    with tempfile.TemporaryDirectory(prefix='coastal-ecology-replay-',dir='/tmp') as directory:
        replay=Path(directory)
        for name in [*expected,'.source-acquired.json',*['.journey-'+layer for layer in PRIOR]]:
            path=replay/name;path.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(baseline/name,path)
        fresh=prepare(replay)
        assert fresh==marker and prepare(replay)==fresh, 'Independent repair replay or idempotence mismatch'
    compiled=[];compiled_blocks=[];rom_sha=elf_sha=None
    if not preflight:
        rom=(source/'pokeemerald.gba').read_bytes()
        assert len(rom)==33554432 and rom[-4096:]==b'\xff'*4096
        assert rom[0xBD]==(-sum(rom[0xA0:0xBD])-0x19)&255
        rom_sha=hashlib.sha256(rom).hexdigest();elf_sha=digest(source/'pokeemerald.elf')
        assert rom_sha!=PARENT_ROM_SHA256
        table=symbols(source)
        for name in ['gWildMonHeaders','sJourneyWildPools','sJourneyGeneration4Pools',
                     'StandardWildEncounter','MetatileBehavior_IsWaterWildEncounter']:
            assert name in table, ('Missing compiled ecology symbol',name)
            address,size=table[name]
            assert 0x08000000<=address<0x0A000000 and size>0,(name,address,size)
            raw=rom[address-0x08000000:address-0x08000000+size]
            assert len(raw)==size and raw!=b'\xff'*size,name
            compiled.append(dict(symbol=name,address=address,bytes=size,sha256=hashlib.sha256(raw).hexdigest()))
        layouts=json.loads((source/'data/layouts/layouts.json').read_text())['layouts']
        block_symbols={row['blockdata_filepath']:row['name']+'_Blockdata' for row in layouts}
        definitions=(source/'src/data/tilesets/metatiles.h').read_text()
        block_symbols.update({path:name for name,path in re.findall(
            r'const\s+u(?:8|16|32)\s+(\w+)\[\]\s*=\s*INCBIN_U(?:8|16|32)\("([^"]+)"\)',definitions)})
        for path in sorted(name for name in changes if name.endswith('.bin')):
            assert path in block_symbols, ('Changed binary needs an explicit compiled binding',path)
            name=block_symbols[path]
            assert name in table
            address,size=table[name];raw=(source/path).read_bytes()
            assert size in (0,len(raw)) and rom[address-0x08000000:address-0x08000000+len(raw)]==raw
            compiled_blocks.append(dict(file=path,symbol=name,bytes=len(raw),sha256=digest(source/path)))
    report=dict(passed=not preflight,preflight=bool(preflight),compiled_rom=not preflight,
        kind='coastal-ecology-source',rom_sha256=rom_sha,elf_sha256=elf_sha,
        parent_rom_sha256=PARENT_ROM_SHA256,layers=PRIOR+[SCOPE],
        changed_files=sorted(changes),prepared_sha256=changes,source_hashes_checked=len(expected|changes),
        independent_replay=True,idempotent=True,unrelated_source_files_unchanged=True,
        atlas_graphics_unchanged=True,unrelated_maps_layouts_and_tilesets_unchanged=True,
        campaign_and_save_abi_source_unchanged=True,preserved_spatial_inputs=len(preserved),
        preserved_spatial_inputs_sha256=hashlib.sha256(json.dumps(preserved,sort_keys=True).encode()).hexdigest(),
        compiled_symbols=compiled,compiled_blockdata=compiled_blocks,
        compiled_data_observations_have_separate_census=True,
        full_campaign_playthrough=False)
    verify_parent(baseline)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--baseline',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--preflight',action='store_true')
    args=parser.parse_args()
    print(json.dumps(validate(args.source,args.baseline,args.output,args.preflight),indent=2))
