"""Reconstruct each Titan story edition and verify the corresponding controller evidence."""
import json
from pathlib import Path
import struct

from package_review_rom import NAME as TEST_EDITION
from prepare_titan_story import LAYER
from verify_atlas_route_pruning import apply
from verify_pwt_official_review import checked
from verify_sootopolis_rescue import DIRECTORY as RESCUE, NORMAL, ROOT, sha, verify as verify_rescue
from verify_versions import VARIANTS

DIRECTORY = ROOT / 'mods/hoenn/titan-story'
BIRDS = ('articuno', 'zapdos', 'moltres')
CAPTURES = {bird + '-with-lugia.png' for bird in BIRDS} | {
    'jirachi-and-eren.png', 'eren-in-titan-cave.png', 'regirock-maria.png',
    'regice-rose.png', 'registeel-sina.png', 'regigigas-and-groudon.png',
    'titan-cave-concluded.png',
    'galactic-waits-for-rescue.png', 'galactic-waits-for-titan-cave.png',
    'galactic-waits-for-frontier.png', 'galactic-finale-entry.png',
}


def verify(directory=DIRECTORY, *, output=None, base_directory=None):
    directory = Path(directory)
    manifest = json.loads((directory / 'validation.json').read_bytes())
    assert manifest['layer'] == LAYER
    prior = json.loads(checked(RESCUE / 'validation.json', manifest['rescue_manifest_sha256']))
    marker = json.loads(checked(directory / 'source-marker.json', manifest['source_marker_sha256']))
    assert marker['layer'] == LAYER and marker['complete_state'] == 8 and marker['rescue_state'] == 4
    assert marker['needs_qualifier_before_finale'] is True
    editions = manifest['editions']
    assert editions.keys() == prior['editions'].keys() == VARIANTS.keys() | {TEST_EDITION}

    def verify_edition(name, base):
        edition = editions[name]
        prefix = name.removesuffix('.gba')
        assert sha(base) == edition['base_sha256'] == prior['editions'][name]['rom_sha256'], name
        rom = apply(checked(directory / (prefix + '-titans.bps'), edition['patch_sha256']), base)
        assert len(rom) == 33554432 and sha(rom) == edition['rom_sha256'], name
        assert rom[0xbd] == (-sum(rom[0xa0:0xbd]) - 0x19) & 255
        national, hard = VARIANTS.get(name, (1025, False))
        rules = manifest['build_rules_offset']
        assert 192 <= rules <= len(rom) - 4 and rom[rules:rules + 4] == struct.pack('<HBB', national, hard, 0)
        restored = bytearray(rom)
        if name == TEST_EDITION:
            review = manifest['test_mode']
            at = review['review_mode_offset']
            assert 192 <= at < len(rom) and rom[at] == 1 and rom[0xa0:0xb0] == b'JOURNEY TESTJRTE'
            restored[at] = 0
            restored[0xa0:0xbe] = bytes.fromhex(review['base_header_hex'])
            assert sha(restored) == editions[NORMAL]['rom_sha256']
            saved = json.loads(checked(directory / 'published-teste-save.json', manifest['published_save_proof_sha256']))
            assert saved['passed'] and saved['rom_sha256'] == edition['rom_sha256']
            assert saved['controllers_only'] and saved['no_game_memory_writes']
            checked(ROOT / 'roms/rom-de-teste/Pokemon-Journey-TESTE.sav', saved['bundled_save_sha256'])
            continued = saved['runs'][-1]
            assert continued['field_map'] == [0, 6] and continued['player_tile'] == [28, 18]
            assert continued['geometry_version'] == 9 and continued['player_surfing'] is False
        else:
            restored[0xa0:0xbe] = bytes.fromhex(manifest['parent_header_hex'])
            restored[rules:rules + 4] = struct.pack('<HBB', 1025, 1, 0)
            assert sha(restored) == manifest['compiled_rom_sha256']

        folder = directory / prefix
        report = json.loads(checked(folder / 'sootopolis-rescue.json', edition['evidence_sha256']))
        assert report['rom_sha256'] == edition['rom_sha256']
        assert report['elf_sha256'] == manifest['compiled_elf_sha256']
        assert report['titan_marker_sha256'] == manifest['source_marker_sha256']
        for key in ('passed', 'native_surf_both_directions', 'lugia_and_kyogre_seen',
                    'eren_started_after_rescue', 'native_titan_complete', 'galactic_fixtures_and_physical_gate'):
            assert report[key] is True, (name, key)
        assert report['seabirds'] == dict(zip(BIRDS, (9, 10, 11)))
        assert report['titan_stage'] == 8 and report['region2_regs'] is (national == 1025)
        boot = report['titan_continue']
        assert boot['passed'] and boot['rom_sha256'] == edition['rom_sha256']
        assert boot['controllers_only'] and boot['no_game_memory_writes']
        resumed = boot['runs'][-1]
        assert resumed['bundled_save_continue_to_field'] and resumed['geometry_version'] == 9
        assert resumed['player_tile'] == [6, 7] and resumed['player_surfing'] is False
        checked(folder / 'titan-cave.sav', boot['bundled_save_sha256'])
        required = CAPTURES | ({'regieleki-reiner.png', 'regidrago-zeke.png'} if national == 1025 else set())
        assert required <= report['capture_sha256'].keys()
        for filename in required:
            png = checked(folder / filename, report['capture_sha256'][filename])
            assert png[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack_from('>II', png, 16) == (240, 160)

        if output is not None:
            (Path(output) / name).write_bytes(rom)

    if base_directory is None:
        verify_rescue(consume=verify_edition)
    else:
        for name in editions:
            verify_edition(name, (Path(base_directory) / name).read_bytes())
    return manifest


if __name__ == '__main__':
    verify()
    print('Verified five Titan story editions and their native evidence')
