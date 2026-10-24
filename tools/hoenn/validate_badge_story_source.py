"""Audit the literal campaign/sprite scope and reproduce layer 164 atomically."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
PARENT_ROM_SHA256 = 'cd5187f43d33b80e5ba2130c9e4e31a4d5a9a0e2504d8b71517da7d13814d9c6'
# Reviewed independently of the generated layer marker. In particular, no
# terrain, tileset, map dimensions, connections, or native trainer parties.
ALLOWED_SOURCE_FILES = frozenset({
    'data/event_scripts.s',
    'data/maps/BattleFrontier_OutsideWest/map.json',
    'data/maps/BattleFrontier_OutsideWest/scripts.inc',
    'data/maps/EverGrandeCity_ChampionsRoom/scripts.inc',
    'data/maps/EverGrandeCity_PokemonLeague_1F/scripts.inc',
    'data/maps/IndigoPlateau_PokemonCenter_1F_Frlg/scripts.inc',
    'data/maps/JourneyExtraGyms.inc',
    'data/maps/JourneyPWTArena/scripts.inc',
    'data/maps/LavaridgeTown/scripts.inc',
    'data/maps/LilycoveCity/scripts.inc',
    'data/maps/LittlerootTown_MaysHouse_2F/scripts.inc',
    'data/maps/LittlerootTown_ProfessorBirchsLab/scripts.inc',
    'data/maps/OldaleTown/scripts.inc',
    'data/maps/Route103/scripts.inc',
    'data/maps/Route104/scripts.inc',
    'data/maps/Route110/scripts.inc',
    'data/maps/Route119/scripts.inc',
    'data/maps/RustboroCity/scripts.inc',
    'data/scripts/journey_badge_qualifier.inc',
    'data/scripts/journey_campaign_gates.inc',
    'data/scripts/journey_galactic.inc',
    'data/scripts/route23.inc',
    'graphics/object_events/pics/people/journey_eren.png',
    'graphics/object_events/pics/people/journey_luffy.png',
    'graphics/object_events/pics/people/journey_pwt_eren.png',
    'graphics/object_events/pics/people/journey_pwt_luffy.png',
    'include/constants/flags.h',
    'include/constants/opponents.h',
    'include/constants/vars.h',
    'include/data.h',
    'include/journey_badge_qualifier.h',
    'include/journey_qualifier_core.h',
    'include/journey_qualifier_field.h',
    'include/journey_story_rivals.h',
    'src/battle_message.c',
    'src/battle_setup.c',
    'src/data.c',
    'src/data/journey_qualifier_trainers.h',
    'src/data/object_events/object_event_graphics_info.h',
    'src/data/object_events/object_event_pic_tables.h',
    'src/event_object_movement.c',
    'src/journey_badge_qualifier.c',
    'src/journey_extra_gyms.c',
    'src/journey_galactic.c',
    'src/journey_gym_scaling.c',
    'src/journey_qualifier_core.c',
    'src/journey_qualifier_field.c',
    'src/journey_rival.c',
    'src/journey_story_rivals.c',
    'src/string_util.c',
})


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def graphics_audit(source, baseline, rom, symbols):
    rows = []
    references = []
    for name in ('red', 'leaf', 'brendan', 'may'):
        image = Image.open(ROOT / 'tools/hoenn/data/badge-story/sprites' / (name+'-reference.png'))
        box = image.crop((0, 0, 16, 32)).getbbox()
        references.append(dict(name=name, visible_height=box[3]-box[1]))
    assert [row['visible_height'] for row in references] == [19, 19, 21, 20]
    for name, symbol in [('eren', 'EREN'), ('luffy', 'LUFFY'),
                         ('pwt_eren', 'PWTEREN'), ('pwt_luffy', 'PWTLUFFY')]:
        path = 'graphics/object_events/pics/people/journey_'+name+'.png'
        new, old = Image.open(source/path), Image.open(baseline/path)
        assert new.mode == old.mode == 'P' and new.size == old.size == (16, 288)
        assert new.getpalette() == old.getpalette() and new.info['transparency'] == 0
        frames = []
        for index in range(9):
            bounds = new.crop((0, index*32, 16, (index+1)*32)).getbbox()
            bottom = 31 if index < 3 else 32
            assert bounds == (1, bottom-20, 15, bottom), (name, index, bounds)
            frames.append(dict(frame=index, bounds=list(bounds), visible_height=20))
        binary = bytearray()
        for y in range(0, 288, 8):
            for x in range(0, 16, 8):
                for dy in range(8):
                    for dx in range(0, 8, 2):
                        low, high = new.getpixel((x+dx, y+dy)), new.getpixel((x+dx+1, y+dy))
                        assert 0 <= low < 16 and 0 <= high < 16
                        binary.append(low | high << 4)
        compiled = None
        if rom is not None:
            address, size = symbols['gObjectEventPic_Journey'+symbol]
            assert size == len(binary) == 2304
            assert rom[address-0x08000000:address-0x08000000+size] == binary
            compiled = dict(address=address, bytes=size, sha256=hashlib.sha256(binary).hexdigest())
        rows.append(dict(path=path, palette_unchanged=True, frames=frames, compiled=compiled))
    return dict(reference_rivals=references, avatars=rows,
                all_frames_whole_and_same_native_scale=True)


def audit_field(source, baseline):
    relative = 'data/maps/BattleFrontier_OutsideWest/map.json'
    old, new = (json.loads((tree/relative).read_text()) for tree in (baseline, source))
    assert set(new) == set(old)
    for key in old.keys()-{'object_events', 'coord_events'}:
        assert new[key] == old[key], key
    assert len(old['object_events']) == 25
    assert new['object_events'][:25] == old['object_events']
    assert len(new['object_events']) == 30
    assert [(index, o['x'], o['y']) for index,o in enumerate(new['object_events'][25:], 26)] == [
        (26, 22, 66), (27, 24, 66), (28, 28, 66), (29, 21, 67), (30, 29, 67)]
    assert new['coord_events'][:len(old['coord_events'])] == old['coord_events']
    assert len(new['coord_events']) == len(old['coord_events'])+3
    assert [(e['x'], e['y']) for e in new['coord_events'][len(old['coord_events']):]] == [(25,67),(26,66),(27,67)]
    # Sharing the stadium dispatch cannot replace the PWT implementation.
    path = 'data/maps/JourneyPWTArena/scripts.inc'
    before, after = ((tree/path).read_text() for tree in (baseline, source))
    assert after == before.replace('JourneyPWT_ArenaStart', 'JourneyQualifier_ArenaDispatch', 1)
    for relative in ('src/journey_pwt.c', 'data/scripts/journey_pwt.inc',
                     'src/data/trainers.party', 'src/data/trainers_frlg.party'):
        assert (source/relative).read_bytes() == (baseline/relative).read_bytes()
    return dict(original_outdoor_npcs_preserved=25, added_outdoor_actors=5,
                original_events_warps_and_connections_unchanged=True,
                native_pwt_implementation_unchanged=True, native_trainer_parties_unchanged=True)


def validate(source, baseline, output, preflight=False):
    # Release verification imports the literal scope without needing the ROM
    # generation toolchain or its optional numerical/image dependencies.
    from prepare_badge_story import LAYER, PRIOR, prepare
    from validate_dewford_coast_source import compiled_values

    source, baseline, output = map(Path, (source, baseline, output))
    assert source.resolve() != baseline.resolve()
    assert digest(baseline/'pokeemerald.gba') == PARENT_ROM_SHA256
    assert len(PRIOR) == 163
    marker = json.loads((source/('.journey-'+LAYER)).read_text())
    expected = dict(json.loads((baseline/'.source-acquired.json').read_text())['sha256'])
    history = ['.source-acquired.json']
    for layer in PRIOR:
        name = '.journey-'+layer
        history.append(name)
        expected.update(json.loads((baseline/name).read_text())['prepared_sha256'])
    outputs = marker['prepared_sha256']
    changed = {name for name, sha in outputs.items() if sha != expected.get(name)}
    assert changed == set(outputs) == ALLOWED_SOURCE_FILES and len(changed) == 50
    assert len(expected) > 30000
    for name, sha in expected.items():
        assert digest(baseline/name) == sha, ('Baseline changed', name)
    for name, sha in (expected | outputs).items():
        assert digest(source/name) == sha, ('Unexpected source change', name)
    for name in history:
        assert (source/name).read_bytes() == (baseline/name).read_bytes(), name
    for directory in ('src', 'include'):
        before = {p.relative_to(baseline).as_posix() for p in (baseline/directory).rglob('*') if p.is_file()}
        after = {p.relative_to(source).as_posix() for p in (source/directory).rglob('*') if p.is_file()}
        assert after-before <= ALLOWED_SOURCE_FILES and not before-after
        for name in (before & after)-expected.keys():
            assert (source/name).read_bytes() == (baseline/name).read_bytes(), name
    with tempfile.TemporaryDirectory(prefix='badge-story-replay-', dir='/tmp') as temporary:
        replay = Path(temporary)
        for name in [*expected, *history]:
            target = replay/name
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                os.link(baseline/name, target)
            except OSError:
                shutil.copyfile(baseline/name, target)
        fresh = prepare(replay)
        assert fresh == marker and prepare(replay) == fresh
        for name, sha in outputs.items():
            assert digest(replay/name) == sha
    for path in (baseline/'data/maps').glob('*/map.json'):
        relative = path.relative_to(baseline).as_posix()
        if relative != 'data/maps/BattleFrontier_OutsideWest/map.json':
            assert path.read_bytes() == (source/relative).read_bytes()
    # Every terrain/tileset/atlas file is outside the allowlist above and was
    # already compared against the entire pinned parent source contract.
    field = audit_field(source, baseline)
    abi_names = ['sizeof(struct SaveBlock1)', 'sizeof(struct SaveBlock2)',
                 'sizeof(struct ObjectEvent)', 'sizeof(struct LinkPlayer)',
                 'sizeof(struct LinkPlayerBlock)', 'FLAGS_COUNT', 'VARS_COUNT']
    includes = ['global.h', 'constants/flags.h', 'constants/vars.h', 'link.h']
    abi = compiled_values(source, abi_names, includes, baseline)
    assert abi == compiled_values(baseline, abi_names, includes, baseline)
    rom_sha, symbols, rom = None, {}, None
    if not preflight:
        rom = (source/'pokeemerald.gba').read_bytes()
        rom_sha = hashlib.sha256(rom).hexdigest()
        assert rom_sha != PARENT_ROM_SHA256 and len(rom) == 33554432
        assert rom[0xBD] == (-sum(rom[0xA0:0xBD])-0x19)&255
        raw = subprocess.check_output([str(ROOT/'.local/arm-binutils/usr/bin/arm-none-eabi-nm'),
                                       '-S', '--defined-only', str(source/'pokeemerald.elf')], text=True)
        symbols = {name: (int(address,16), int(size,16)) for address,size,name in
                   re.findall(r'^([\da-fA-F]+)\s+([\da-fA-F]+)\s+\w\s+(\S+)$', raw, re.M)}
        assert rom[-4096:] == b'\xff'*4096, 'Native fixture scratch overlaps compiled game'
    graphics = graphics_audit(source, baseline, rom, symbols)
    report = dict(passed=not preflight, kind='badge-story-source',
        compiled_rom=not preflight, preflight=bool(preflight), rom_sha256=rom_sha,
        elf_sha256=None if preflight else digest(source/'pokeemerald.elf'),
        parent_rom_sha256=PARENT_ROM_SHA256, layers=PRIOR+[LAYER],
        changed_files=sorted(changed), allowed_changed_files=sorted(ALLOWED_SOURCE_FILES),
        prepared_sha256=outputs, source_hashes_checked=len(expected | outputs),
        independent_replay=True, idempotent=True, unrelated_source_files_unchanged=True,
        save_and_link_abi_unchanged=True, compiled_abi=dict(zip(abi_names, abi)),
        atlas_graphics_unchanged=True, coastlines_and_gym_geometry_unchanged=True,
        native_trainer_parties_unchanged=True, field_event=field, avatars=graphics,
        full_campaign_playthrough=False)
    assert digest(baseline/'pokeemerald.gba') == PARENT_ROM_SHA256
    if not preflight:
        assert digest(source/'pokeemerald.gba') == rom_sha
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--preflight', action='store_true')
    a = p.parse_args()
    r = validate(a.source, a.baseline, a.output, a.preflight)
    print(json.dumps({k:r[k] for k in ['passed','preflight','rom_sha256','source_hashes_checked']}, indent=2))
