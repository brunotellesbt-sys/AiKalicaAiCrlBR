"""Reproduce the five rival-progression ROMs and verify all twelve encounters."""
import json
from pathlib import Path
import struct

from package_review_rom import NAME as TEST_EDITION
from prepare_crossover_badges import LAYER, RIVAL_SOURCE
from verify_atlas_route_pruning import apply
from verify_pwt_official_review import checked
from verify_sootopolis_rescue import NORMAL, ROOT, sha
from verify_titan_story import DIRECTORY as TITANS, verify as verify_titans
from verify_versions import VARIANTS

DIRECTORY = ROOT / 'mods/hoenn/crossover-badges'
KANTO = [('Route4_Frlg', 0), ('Route6_Frlg', 6), ('Route10_Frlg', 1),
         ('Route13_Frlg', 7), ('Route17_Frlg', 2), ('Route20_Frlg', 8)]
HOENN = [('PetalburgWoods', 5), ('Route106', 9), ('Route112', 3),
         ('AbandonedShip_Deck', 10), ('Route113', 4), ('Route125', 11)]


def verify_native(report, digest):
    assert report['rom_sha256'] == digest
    for key in ('passed', 'native_victories', 'normal_field_hook_and_approach', 'visit_flags_not_written',
                'ordered_by_badges', 'skipped_earlier_battle_refused'):
        assert report[key] is True, key

    wins = report['wins']
    assert len(wins) == 12
    visits = 0
    for step, row in enumerate(wins):
        kanto = step % 2 == 0
        badges = step // 2 + 1
        route, bit = (KANTO if kanto else HOENN)[badges - 1]
        assert row['map'] == route and row['visit_bit'] == bit
        assert row['region'] == ('Kanto' if kanto else 'Hoenn')
        assert row['battled_at'] == badges and row['blocked_at'] == badges - 1
        assert row['other_region_badges'] == 8 and row['outcome'] == 1
        visits |= 1 << bit
        assert row['visit_mask'] == visits
    assert visits == 0xFFF


def verify(directory=DIRECTORY, *, output=None, base_directory=None):
    directory = Path(directory)
    info = json.loads((directory / 'validation.json').read_bytes())
    assert info['layer'] == LAYER
    previous = json.loads(checked(TITANS / 'validation.json', info['titan_manifest_sha256']))
    marker = json.loads(checked(directory / 'source-marker.json', info['source_marker_sha256']))
    assert marker['layer'] == LAYER and marker['regional_milestones'] == [1, 2, 3, 4, 5, 6]
    assert marker['visit_bits_preserved'] is True and marker['prepared_sha256'].keys() == {RIVAL_SOURCE}
    assert marker['route108_site'] == 'AbandonedShip_Deck'
    deck = json.loads(checked(directory / 'route108-entry.json', info['route108_proof_sha256']))
    assert deck['passed'] is True and deck['rom_sha256'] == info['compiled_rom_sha256']
    assert deck['source'] == ['Route108', 28, 6] and deck['deck_arrival'] == [13, 15]
    assert deck['battle']['outcome'] == 1 and deck['battle']['opponent'] == 1558
    screenshot = checked(directory / 'luffy-on-the-deck.png', deck['screenshot_sha256'])
    assert screenshot[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack_from('>II', screenshot, 16) == (240, 160)
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

        report = json.loads(checked(directory / (prefix + '-visits.json'), entry['evidence_sha256']))
        verify_native(report, entry['rom_sha256'])
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
