"""Reproduce the five rival-progression ROMs and verify all eight encounters."""
import json
from pathlib import Path
import struct

from package_review_rom import NAME as TEST_EDITION
from prepare_crossover_badges import LAYER, OUTPUTS
from verify_atlas_route_pruning import apply
from verify_pwt_official_review import checked
from verify_sootopolis_rescue import NORMAL, ROOT, sha
from verify_titan_story import DIRECTORY as TITANS, verify as verify_titans
from verify_versions import VARIANTS

DIRECTORY = ROOT / 'mods/hoenn/crossover-badges'
ROUNDS = [
    ('Route4_Frlg', 0, 1, 1551), ('Route106', 9, 2, 1557),
    ('Route112', 3, 5, 1552), ('Route13_Frlg', 7, 7, 1558),
    ('AbandonedShip_Deck', 10, 11, 1559), ('Route17_Frlg', 2, 13, 1553),
    ('SixIsland_WaterPath_Frlg', 13, 15, 1560), ('Route123', 12, 20, 1554),
]
LATE = {
    13: (68, [62, 143, 272, 338, 395, 468]),
    12: (78, [208, 212, 248, 445, 477, 486]),
}


def verify_native(report, digest):
    assert report['rom_sha256'] == digest
    for key in ('passed','native_victories','normal_field_hook_and_approach','visit_flags_not_written',
                'ordered_by_badges','skipped_earlier_battle_refused','legacy_completed_visit_mask_accepted'):
        assert report[key] is True, key
    assert len(report['wins']) == len(ROUNDS)
    mask = 0
    for row, (name, bit, badges, opponent) in zip(report['wins'], ROUNDS):
        assert (row['map'], row['visit_bit'], row['opponent'], row['outcome']) == (name, bit, opponent, 1)
        mask |= 1 << bit
        assert row['visit_mask'] == mask and row['battle_controller_ticks'] > 0
        assert row['badge_scope'] == 'total' and row['battled_at'] == badges and row['blocked_at'] == badges-1
        if bit in LATE:
            mean, species = LATE[bit]
            assert row['party_mean'] == mean and row['enemy_species'] == species
            assert len(row['enemy_levels']) == 6 and all(mean-5 <= level <= mean+2 for level in row['enemy_levels'])
        if name == 'Route123':
            assert 0 <= row['approach'][0] < 40


def verify_continues(directory, edition_name, entry, elf):
    folder = directory / edition_name.removesuffix('.gba')
    previous = TITANS / folder.name
    old = json.loads((previous / 'sootopolis-rescue.json').read_bytes())['titan_continue']
    original_save = checked(previous / 'titan-cave.sav', old['bundled_save_sha256'])
    report = json.loads(checked(folder / 'continue.json', entry['continue_sha256']))
    assert report['elf_sha256'] == elf and report['rom_sha256'] == entry['rom_sha256']
    assert report['old_rom_sha256'] == old['rom_sha256'] == entry['base_sha256']
    first, second = report['continued'], report['resaved']
    assert first['bundled_save_sha256'] == sha(original_save)
    for boot in (first, second):
        assert boot['rom_sha256'] == entry['rom_sha256']
        assert all(boot[key] is True for key in ('passed', 'controllers_only', 'no_game_memory_writes'))
        resumed = boot['runs'][-1]
        assert resumed['field_map'] == old['runs'][-1]['field_map']
        assert resumed['player_tile'] == [6, 7] and not resumed['player_surfing']
        assert resumed['geometry_version'] == 9
        assert resumed['persistent_variables'] == {'0x409b': 2, '0x40ff': 0}
    saved = checked(folder / 'titan-resaved.sav', second['bundled_save_sha256'])
    assert len(saved) == 131072 and first['runs'][-1]['saved_battery_sha256'] == sha(saved)
    assert first['runs'][-1]['saved_after_continue_with_controllers'] is True


def verify(directory=DIRECTORY, *, output=None, base_directory=None):
    directory = Path(directory)
    info = json.loads((directory / 'validation.json').read_bytes())
    assert info['layer'] == LAYER
    previous = json.loads(checked(TITANS / 'validation.json', info['titan_manifest_sha256']))
    marker = json.loads(checked(directory / 'source-marker.json', info['source_marker_sha256']))
    assert marker['layer'] == LAYER and marker['total_badges'] == {'Eren':[1,5,13,20],'Luffy':[2,7,11,15]}
    assert marker['visit_bits_preserved'] is True and marker['prepared_sha256'].keys() == OUTPUTS
    assert marker['route108_site'] == 'AbandonedShip_Deck'
    deck = json.loads(checked(directory / 'route108-entry.json', info['route108_proof_sha256']))
    assert deck['passed'] is True and deck['rom_sha256'] == info['compiled_rom_sha256']
    assert deck['source'] == ['Route108', 28, 6] and deck['deck_arrival'] == [13, 15]
    assert deck['battle']['outcome'] == 1 and deck['battle']['opponent'] == 1559
    screenshot = checked(directory / 'luffy-on-the-deck.png', deck['screenshot_sha256'])
    assert screenshot[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack_from('>II', screenshot, 16) == (240, 160)
    dialogue = json.loads(checked(directory / 'dialogue.json', info['dialogue_sha256']))
    assert dialogue['rom_sha256'] == info['compiled_rom_sha256'] and dialogue['elf_sha256'] == info['elf_sha256']
    expected_speeches = {'JourneyCrossover_Text_' + prefix + hero + str(rank)
                         for hero in ('EREN','LUFFY') for rank in range(1,5) for prefix in ('','After')}
    assert set(dialogue['speeches']) == expected_speeches | {'JourneyGalactic_Text_MissingRivals', 'JourneyCrossover_Text_Defeat'}
    editions = info['editions']
    assert editions.keys() == previous['editions'].keys() == VARIANTS.keys() | {TEST_EDITION}

    def verify_edition(name, base):
        entry = editions[name]
        assert sha(base) == entry['base_sha256'] == previous['editions'][name]['rom_sha256'], name
        prefix = name.removesuffix('.gba')
        rom = apply(checked(directory / (prefix + '-crossover.bps'), entry['patch_sha256']), base)
        assert len(rom) == 33554432 and sha(rom) == entry['rom_sha256']
        assert rom[0xBD] == (-sum(rom[0xA0:0xBD]) - 0x19) & 255
        national, hard = VARIANTS.get(name, (1025, False))
        offset = info['build_rules_offset']
        assert 192 <= offset <= len(rom) - 4 and rom[offset:offset + 4] == struct.pack('<HBB', national, hard, 0)
        restored = bytearray(rom)
        if name == TEST_EDITION:
            review = info['test_mode']
            at = review['review_mode_offset']
            assert 192 <= at < len(rom) and rom[at] == 1 and rom[0xA0:0xB0] == b'JOURNEY TESTJRTE'
            restored[at] = 0
            restored[0xA0:0xBE] = bytes.fromhex(review['base_header_hex'])
            assert sha(restored) == editions[NORMAL]['rom_sha256']
        else:
            restored[0xA0:0xBE] = bytes.fromhex(info['parent_header_hex'])
            restored[offset:offset + 4] = struct.pack('<HBB', 1025, 1, 0)
            assert sha(restored) == info['compiled_rom_sha256']

        for speech in dialogue['speeches'].values():
            assert 0 < speech['max_pixels'] <= 208 and speech['lines'] > 0
            at, size = speech['offset'], speech['bytes']
            assert 192 <= at and 0 < size <= len(rom) - at
            assert sha(rom[at:at+size]) == speech['text_sha256'] and rom[at+size-1] == 0xff
        verify_continues(directory, name, entry, info['elf_sha256'])
        report = json.loads(checked(directory / (prefix + '-visits.json'), entry['evidence_sha256']))
        verify_native(report, entry['rom_sha256'])
        assert report['elf_sha256'] == info['elf_sha256']
        assert report['marker_sha256'] == info['source_marker_sha256']
        for row in report['wins']:
            capture = 'approach-' + row['map'] + '.png'
            assert row['capture'] == capture
            image = checked(directory / prefix / capture, row['capture_sha256'])
            assert image[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack_from('>II', image, 16) == (240, 160)
        if output is not None:
            (Path(output) / name).write_bytes(rom)

    if base_directory is None:
        verify_titans(consume=verify_edition)
    else:
        for name in editions:
            verify_edition(name, (Path(base_directory) / name).read_bytes())
    return info


if __name__ == '__main__':
    verify()
    print('Verified the five rival progression editions and every badge milestone')
