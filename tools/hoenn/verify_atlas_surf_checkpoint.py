"""Verify candidate 172 byte/evidence integrity; never certify a final release.

This read-only checkpoint checker does not run the final release validator and
never changes manifests, ROMs, frozen source or evidence. Native gameplay and
final publication remain pending even when checkpoint integrity passes.
"""
import argparse
import gzip
import json
from pathlib import Path
import struct
import zipfile

from package_review_rom import verify as verify_review
from publish_badge_story import CONTINUITY_FILES
from verify_versions import VARIANTS, digest

ROOT = Path(__file__).resolve().parents[2]
SCOPE = 'atlas-surf-layout-candidate'
PROOF = Path('docs/design/atlas-surf-layout')
BASELINE = 'mods/hoenn/atlas-surf-layout-validation/baseline/versions.json'
BASELINE_SHA256 = 'eca26adfcb0b15f9da78aadec1b8738f66288fcc58d4d727ee2ea2a6274e29ec'
ROM_BYTES = 32 * 1024 * 1024


def read_json(path):
    return json.loads(Path(path).read_bytes())


def confined(root, name):
    path = Path(name)
    assert not path.is_absolute() and '..' not in path.parts, ('Unsafe path', name)
    resolved = (root / path).resolve()
    assert resolved.is_relative_to(root.resolve()), ('Path leaves repository', name)
    return resolved


def verify_rocks103_evidence(root):
    """Bind the compact ZIP reference to the full repository review bytes."""
    root=Path(root).resolve()
    path=root/PROOF/'rocks103-checkpoint.json'
    if not path.exists():return None
    reference=read_json(path)
    assert reference['scope']=='native-General-103-rock-fragments'
    assert reference['final_release_validated'] is False
    files={}
    for key in ('summary','evidence_manifest'):
        row=reference[key];p=confined(root,row['file'])
        assert p.is_relative_to(root/'docs/design/native-rock-fragments-review')
        assert digest(p.read_bytes())==row['sha256'],('Changed rock review reference',key)
        files[key]=p
    summary=read_json(files['summary'])
    assert summary['source_repairs']==103 and summary['maps']==20
    assert summary['complete_large_boulders_preserved']==462 and summary['suspect_pieces_after']==0
    assert summary['final_release_validated'] is False
    assert summary['native_ROM_validation_complete']==reference['native_ROM_validation_complete']
    seen=set();base=files['evidence_manifest'].parent
    for line in files['evidence_manifest'].read_text().splitlines():
        expected,name=line.split('  ',1);relative=Path(name)
        assert not relative.is_absolute() and '..' not in relative.parts and name not in seen
        seen.add(name);p=(base/relative).resolve()
        assert p.is_relative_to(base.resolve())
        assert digest(p.read_bytes())==expected,('Changed rock review evidence',name)
    assert files['summary'].relative_to(base).as_posix() in seen
    return reference


def candidate_flags(info, *, proofs=False):
    assert info['candidate'] is True and info['validated'] is False
    assert info['final_release_validated'] is False and info['validation_scope'] == SCOPE
    if proofs:
        assert info['proofs'] == [], 'Candidate must not claim final native proofs'


def verify_history(root, info):
    ref = info['previous_port_validation']
    assert ref == dict(manifest=BASELINE, manifest_sha256=BASELINE_SHA256,
                       retested_on_current_rom=False), 'Layer-171 history pin changed'
    raw = confined(root, ref['manifest']).read_bytes()
    assert digest(raw) == BASELINE_SHA256, 'Layer-171 manifest bytes changed'
    old = json.loads(raw)
    assert old['validated'] is True and old['validation_scope'] == 'generated-area-review'
    assert len(old['integration_layers']) == 171
    assert info['integration_layers'] == old['integration_layers'] + ['atlas-surf-layout']
    return ref


def verify_profiles(directory, info):
    """Restore only declared header/rule bytes and require the identical raw parent."""
    rows = info['variants']
    assert len(rows) == 4 and {r['file'] for r in rows} == set(VARIANTS)
    at = info['build_rules_offset']
    assert type(at) is int and 192 <= at <= ROM_BYTES - 4
    header, rules = bytes.fromhex(info['parent_header_hex']), bytes.fromhex(info['parent_rules_hex'])
    assert len(header) == 30 and rules == struct.pack('<HBB', 1025, 1, 0)
    parent_raw = None
    for row in rows:
        cap, hard = VARIANTS[row['file']]
        raw = (directory / row['file']).read_bytes()
        assert row['max_national'] == cap and row['perfect_trainer_ivs'] is hard
        assert len(raw) == row['bytes'] == ROM_BYTES and digest(raw) == row['sha256']
        assert raw[at:at + 4] == struct.pack('<HBB', cap, hard, 0)
        assert raw[0xBD] == (-sum(raw[0xA0:0xBD]) - 0x19) & 255
        restored = bytearray(raw)
        restored[0xA0:0xBE], restored[at:at + 4] = header, rules
        assert digest(restored) == info['parent_rom_sha256'], 'Unapproved binary change'
        allowed = list(range(0xA0, 0xAC)) + [0xBD] + list(range(at, at + 4))
        differences = [i for i in range(0xA0, 0xBE) if raw[i] != restored[i]]
        differences += [i for i in range(at, at + 4) if raw[i] != restored[i]]
        assert all(i in allowed for i in differences), 'Forbidden header changes'
        assert differences == row['patched_byte_offsets'], 'Patch offset metadata changed'
        parent_raw = restored
    return parent_raw


def verify_cold_report(report, sha):
    assert report['rom_sha256'] == sha, 'Cold boot belongs to another ROM'
    for key in ('passed', 'controllers_only', 'no_game_memory_writes',
                'fresh_rom_boot_to_title', 'fresh_rom_title_to_new_game', 'no_assert_screen'):
        assert report[key] is True, ('Incomplete cold boot', key)
    fresh = [run for run in report['runs'] if run['battery'] is False]
    assert fresh and any(run['fresh_rom_boot_to_title'] is True
                         and run['fresh_rom_title_to_new_game'] is True
                         and run['frames'] > 0 for run in fresh), 'Missing fresh boot run'


def verify_boots(root, info, review, summary):
    expected = {row['file'].removeprefix('Pokemon-Journey-').removesuffix('.gba'): row['sha256']
                for row in info['variants']}
    expected['TESTE'] = review['sha256']
    refs = info['native_cold_boot']
    assert set(refs) == set(expected) and summary['cold_boot'] == refs
    reports = {}
    for edition, sha in expected.items():
        ref = refs[edition]
        folder = 'TESTE-continued-after-save' if edition == 'TESTE' else edition
        assert ref['report'] == (PROOF / 'candidate-cold-boot' / folder / 'cold-boot.json').as_posix()
        raw = confined(root, ref['report']).read_bytes()
        assert digest(raw) == ref['sha256'], ('Changed cold boot report', edition)
        report = json.loads(raw)
        verify_cold_report(report, sha)
        reports[edition] = report
    assert review['cold_boot'] == refs['TESTE']
    continued = reports['TESTE']
    assert continued['bundled_save_tested'] is True and continued['bundled_save_continue_to_field'] is True
    assert continued['bundled_save_sha256'] == review['bundled_save_sha256']
    saved = read_json(root / PROOF / 'candidate-cold-boot/TESTE-save-menu-v2/cold-boot.json')
    verify_cold_report(saved, review['sha256'])
    before, after = saved['runs'][-1], continued['runs'][-1]
    assert before['battery'] is True and after['battery'] is True
    assert before['saved_after_continue_with_controllers'] is True
    assert before['saved_battery_sha256'] == review['bundled_save_sha256']
    assert {'SaveDoSaveCallback', 'SaveSuccessCallback'} <= set(before['save_menu_callbacks'])
    assert after['bundled_save_continue_to_field'] is True
    roundtrip = review['native_battery_roundtrip']
    assert roundtrip['continue_save_menu_continue'] is True
    assert roundtrip['all_retired_save_positions_natively_proven'] is False
    for key in ('field_map', 'player_tile', 'player_elevation', 'player_surfing'):
        assert before[key] == after[key] == roundtrip[key], ('Battery state changed', key)


def verify_compiled(root, info, review, summary, parent):
    frozen = json.loads(gzip.decompress((root / PROOF / 'candidate-compiled-freeze.json.gz').read_bytes()))
    assert frozen['schema'] == 'atlas-candidate-compiled-freeze/v1'
    assert frozen['final_release_validated'] is False and frozen['global_source_validation_passed'] is False
    assert frozen['rom_sha256'] == info['parent_rom_sha256'] == summary['source_raw_rom_sha256']
    assert frozen['elf_sha256'] == info['parent_elf_sha256'] == summary['elf_sha256']
    assert frozen['marker_sha256'] == info['layer_marker_sha256'] == info['source_marker_sha256'] == summary['marker_sha256']
    assert 0 < frozen['rom_used_bytes'] == info['rom_used_bytes'] == summary['ROM_used_bytes'] <= ROM_BYTES
    assert frozen['rom_limit_bytes'] == info['rom_limit_bytes'] == ROM_BYTES
    expected = {row['file']: row['sha256'] for row in info['variants']}
    expected[review['file']] = review['sha256']
    editions = frozen['editions']
    assert len(editions) == 5 and {Path(r['rom']).name: r['sha256'] for r in editions} == expected
    tables = read_json(root / PROOF / 'candidate-compiled-tables.json')
    assert tables['passed'] is True and tables['native_travel_proven'] is False
    assert tables['ROM_sha256'] == frozen['rom_sha256'] and tables['ELF_sha256'] == frozen['elf_sha256']
    assert tables['maps'] > 0 and tables['stride'] == 8 and len(tables['copies']) == 3
    for copy in tables['copies']:
        offset, size = int(copy['address'], 16) - 0x08000000, copy['bytes']
        assert size == tables['maps'] * 8 and 0 <= offset <= ROM_BYTES - size
        assert digest(parent[offset:offset + size]) == copy['sha256'], 'Compiled table bytes changed'


def verify_archive(root, directory, info, summary):
    archive = directory / 'Pokemon-Journey-Four-Editions.zip'
    assert archive.stat().st_size == summary['archive_bytes']
    assert digest(archive.read_bytes()) == summary['archive_sha256'], 'Archive hash changed'
    files = {row['file']: directory / row['file'] for row in info['variants']}
    files.update({name: root / name for name in CONTINUITY_FILES})
    for path in (root / 'Aqui').rglob('*'):
        if path.is_file():
            files[path.relative_to(root).as_posix()] = path
    for path in (root / PROOF).rglob('*'):
        if path.is_file() and path.name != 'candidate-ROM-checkpoint.json':
            files[path.relative_to(root).as_posix()] = path
    for name in ('roms/README.md', 'roms/CANDIDATA-172.json', 'roms/rom-de-teste/LEIA-ME.md',
                 'roms/rom-de-teste/review.json', 'roms/rom-de-teste/SHA256SUMS',
                 'roms/rom-de-teste/Pokemon-Journey-TESTE.sav'):
        files[name] = root / name
    files.update({'versions.json': directory / 'versions.json', 'SHA256SUMS': directory / 'SHA256SUMS'})
    with zipfile.ZipFile(archive) as bundle:
        assert len(bundle.namelist()) == len(set(bundle.namelist())), 'Duplicate ZIP entries'
        assert bundle.testzip() is None
        for name, path in files.items():
            assert digest(bundle.read(name)) == digest(path.read_bytes()), ('Stale archive entry', name)
        assert 'CANDIDATA-EM-VALIDACAO.txt' in bundle.namelist()


def verify(root=ROOT, *, if_candidate=False):
    root = Path(root)
    verify_rocks103_evidence(root)
    directory = root / 'mods/hoenn/versions'
    info = read_json(directory / 'versions.json')
    if if_candidate and info.get('validation_scope') != SCOPE:
        return None
    candidate_flags(info, proofs=True)
    history = verify_history(root, info)
    parent = verify_profiles(directory, info)
    assert {p.name for p in (root / 'roms').glob('*.gba')} == set(VARIANTS)
    sums = ''.join(row['sha256'] + '  ' + row['file'] + '\n' for row in info['variants']).encode()
    assert (directory / 'SHA256SUMS').read_bytes() == (root / 'roms/SHA256SUMS').read_bytes() == sums
    for row in info['variants']:
        assert digest((root / 'roms' / row['file']).read_bytes()) == row['sha256']
    test_dir = root / 'roms/rom-de-teste'
    review = verify_review(test_dir, directory / 'Pokemon-Journey-Gen1-9-Normal.gba')
    candidate_flags(review)
    battery = test_dir / 'Pokemon-Journey-TESTE.sav'
    assert battery.stat().st_size == 131072 and digest(battery.read_bytes()) == review['bundled_save_sha256']
    assert (test_dir / 'SHA256SUMS').read_text() == review['sha256'] + '  ' + review['file'] + '\n'
    summary = read_json(root / PROOF / 'candidate-ROM-checkpoint.json')
    public = read_json(root / 'roms/CANDIDATA-172.json')
    assert {k: v for k, v in summary.items() if k not in ('archive_sha256', 'archive_bytes')} == public
    assert summary['final_release_validated'] is False and summary['global_gameplay_validation_complete'] is False
    assert summary['compiled_roms_updated'] is True and summary['previous_port_validation'] == history
    assert summary['pending_obligations'] == info['pending_obligations'] and info['pending_obligations']
    assert summary['variants'] == [dict(file=r['file'], sha256=r['sha256']) for r in info['variants']]
    assert summary['TESTE'] == dict(file='rom-de-teste/' + review['file'], sha256=review['sha256'],
                                    battery_sha256=review['bundled_save_sha256'])
    verify_boots(root, info, review, summary)
    verify_compiled(root, info, review, summary, parent)
    verify_archive(root, directory, info, summary)
    return dict(checkpoint_integrity=True, ROMs=5, final_release_validated=False,
                native_gameplay_validation='pending')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--if-candidate', action='store_true', help='Skip when another validation scope is active')
    args = parser.parse_args()
    result = verify(args.root, if_candidate=args.if_candidate)
    print(json.dumps(result, indent=2) if result else 'Other scope: candidate checkpoint check skipped.')
    if result:
        print('Checkpoint íntegro. Release final e validação nativa de gameplay permanecem pendentes.')
