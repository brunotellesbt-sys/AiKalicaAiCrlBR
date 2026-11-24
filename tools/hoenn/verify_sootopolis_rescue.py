"""Reproduce the five tested Sootopolis editions from the published PWT build."""
import hashlib
import json
from pathlib import Path
import struct

from package_review_rom import NAME as TEST_EDITION
from prepare_sootopolis_rescue import LAYER
from verify_atlas_route_pruning import DIRECTORY as ATLAS, ROOT, apply
from verify_pwt_complete_rosters import DIRECTORY as PWT
from verify_pwt_official_review import checked
from verify_versions import VARIANTS

DIRECTORY = ROOT / 'mods/hoenn/sootopolis-rescue'
PWT_PARENT = 'fd5604c47582071e753288e93b8900d9e04e8621'
NORMAL = 'Pokemon-Journey-Gen1-9-Normal.gba'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def verify(directory=DIRECTORY, *, base_directory=None, output=None):
    directory = Path(directory)
    manifest = json.loads((directory / 'validation.json').read_bytes())
    assert manifest['layer'] == LAYER and manifest['parent_commit'] == PWT_PARENT
    marker = json.loads(checked(directory / 'source-marker.json', manifest['source_marker_sha256']))
    assert marker['layer'] == LAYER and marker['mandatory'] is True
    assert marker['after_rayquaza'] is True and marker['before_final_hoenn_gym'] is True
    pwt = json.loads(checked(PWT / 'validation.json', manifest['pwt_manifest_sha256']))['editions']
    atlas = {row['edition']: row for row in json.loads((ATLAS / 'validation.json').read_bytes())['editions']}
    editions = manifest['editions']
    assert editions.keys() == pwt.keys() == VARIANTS.keys() | {TEST_EDITION}
    for name, edition in editions.items():
        prefix = name.removesuffix('.gba')
        parent = pwt[name]
        if base_directory is None:
            old = atlas[name]
            base = apply(checked(ATLAS / old['patch'], old['patch_sha256']),
                         checked(ROOT / old['base'], old['base_sha256']))
            assert sha(base) == parent['base_sha256']
            base = apply(checked(PWT / (prefix + '-pwt-complete.bps'), parent['patch_sha256']), base)
        else:
            base = (Path(base_directory) / name).read_bytes()
        assert sha(base) == parent['rom_sha256'] == edition['base_sha256'], name

        rom = apply(checked(directory / (prefix + '-rescue.bps'), edition['patch_sha256']), base)
        assert len(rom) == 33554432 and sha(rom) == edition['rom_sha256'], name
        assert rom[0xbd] == (-sum(rom[0xa0:0xbd]) - 0x19) & 255, name
        national, hard = VARIANTS.get(name, (1025, False))
        rules = manifest['build_rules_offset']
        assert 192 <= rules <= len(rom) - 4 and rom[rules:rules + 4] == struct.pack('<HBB', national, hard, 0)
        if name == TEST_EDITION:
            review = manifest['test_mode']
            at = review['review_mode_offset']
            assert 192 <= at < len(rom) and rom[at] == 1 and rom[0xa0:0xb0] == b'JOURNEY TESTJRTE'
            restored = bytearray(rom)
            restored[at] = 0
            restored[0xa0:0xbe] = bytes.fromhex(review['base_header_hex'])
            assert sha(restored) == review['base_normal_sha256'] == editions[NORMAL]['rom_sha256']
            saved = json.loads(checked(directory / 'published-teste-save.json', manifest['published_save_proof_sha256']))
            assert saved['passed'] is True and saved['rom_sha256'] == edition['rom_sha256']
            assert saved['controllers_only'] and saved['no_game_memory_writes']
            checked(ROOT / 'roms/rom-de-teste/Pokemon-Journey-TESTE.sav', saved['bundled_save_sha256'])
            continued = saved['runs'][-1]
            assert continued['field_map'] == [0, 6] and continued['player_tile'] == [28, 18]
            assert continued['geometry_version'] == 9 and continued['player_surfing'] is False
        else:
            restored = bytearray(rom)
            restored[0xa0:0xbe] = bytes.fromhex(manifest['parent_header_hex'])
            restored[rules:rules + 4] = struct.pack('<HBB', 1025, 1, 0)
            assert sha(restored) == manifest['compiled_rom_sha256'], name

        folder = directory / prefix
        proof = json.loads(checked(folder / 'sootopolis-rescue.json', edition['evidence_sha256']))
        assert proof['passed'] is True and proof['rom_sha256'] == edition['rom_sha256']
        assert proof['elf_sha256'] == manifest['compiled_elf_sha256']
        assert proof['marker_sha256'] == manifest['source_marker_sha256']
        for key in (
            'required_for_eight_last_gym_choices', 'native_port_entry_and_ferry',
            'native_surf_both_directions', 'manaphy_and_two_castaways_seen', 'lugia_and_kyogre_seen',
            'restored_from_save_during_escort', 'regular_ferry_still_available',
            'old_save_eight_badges_keep_access', 'offers_rescue_only_after_rayquaza',
            'blocks_leader_inside_unwon_gym',
        ):
            assert proof[key] is True, (name, key)
        assert proof['galactic_completed_before_rescue'] is hard
        assert proof['rescue_completion_state'] == 4
        before, after = proof['physical_gym_door_before_and_after']
        assert before['city'] == after['city'] == 'SootopolisCity'
        assert before['blocked'] is True and after['blocked'] is False
        assert before['physical_door'] and after['physical_door']
        boot = proof['controller_save_and_cold_continue']
        assert boot['passed'] and boot['rom_sha256'] == edition['rom_sha256']
        assert boot['controllers_only'] and boot['no_game_memory_writes'] and boot['bundled_save_continue_to_field']
        continued = boot['runs'][-1]
        assert continued['player_tile'] == [11, 14] and continued['player_surfing'] is True
        assert continued['geometry_version'] == 9
        captures = proof['capture_sha256']
        assert {'reach-castaways.png', 'raft-reaches-the-landing.png',
                'lugia-shields-the-raft.png', 'rescue-confirmed-at-the-harbor.png'} <= captures.keys()
        for filename, digest in captures.items():
            assert Path(filename).name == filename and Path(filename).suffix == '.png'
            png = checked(folder / filename, digest)
            assert png[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack_from('>II', png, 16) == (240, 160)

        if output is not None:
            (Path(output) / name).write_bytes(rom)
    return manifest


if __name__ == '__main__':
    verify()
    print('Verified five Sootopolis rescue editions from published PWT ROMs')
