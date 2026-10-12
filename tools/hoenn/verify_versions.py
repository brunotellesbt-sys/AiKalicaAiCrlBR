"""Verify four ROMs, their native test evidence and the restricted binary changes."""
import argparse, hashlib, json, struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
VARIANTS={f'Pokemon-Journey-Gen1-{generation}-{difficulty}.gba':(cap,hard)
          for generation,cap in [(4,493),(9,1025)]
          for difficulty,hard in [('Normal',False),('Hard',True)]}

def digest(raw):return hashlib.sha256(raw).hexdigest()

def verify_browser(release):
    report=json.loads((ROOT/'mods/hoenn/versions-validation/browser/browser-versions.json').read_text())
    assert report['passed'] is True and report['bundled_mgba'] is True
    assert report['invalid_manifest_rejected'] and report['incomplete_rom_rejected']
    expected={r['file']:r['sha256'] for r in release['variants']}
    checks=report['checks'];assert len(checks)==4 and {c['file'] for c in checks}==set(expected)
    for row in checks:
        assert row['rom_sha256']==expected[row['file']] and row['actual_game_name']==row['file']
        assert row['native_frames']>360 and row['exported_native_state_bytes']>1000
    sources=report['player_sources_sha256'];assert set(sources)=={'index.html','player.js','style.css'}
    for name,sha in sources.items():assert digest((ROOT/'web'/name).read_bytes())==sha,('Untested player source',name)
    print('Verified browser boot evidence and player sources for all four editions')

def verify(directory,require_seal=True):
    directory=Path(directory);info=json.loads((directory/'versions.json').read_text())
    if require_seal:assert info['validated'] is True,'Unvalidated release'
    assert len(info['variants'])==4 and {r['file'] for r in info['variants']}==set(VARIANTS)
    at=info['build_rules_offset'];assert isinstance(at,int) and 192<=at<33554428
    header=bytes.fromhex(info['parent_header_hex']);rules=bytes.fromhex(info['parent_rules_hex'])
    assert len(header)==30 and rules==struct.pack('<HBB',1025,1,0)
    for row in info['variants']:
        cap,hard=VARIANTS[row['file']];raw=(directory/row['file']).read_bytes()
        assert row['max_national']==cap and row['perfect_trainer_ivs'] is hard
        assert len(raw)==row['bytes']==33554432 and digest(raw)==row['sha256']
        assert raw[at:at+4]==struct.pack('<HBB',cap,hard,0)
        assert raw[0xBD]==(-sum(raw[0xA0:0xBD])-0x19)&255
        parent=bytearray(raw);parent[0xA0:0xBE]=header;parent[at:at+4]=rules
        assert digest(parent)==info['parent_rom_sha256'],'Unapproved binary change'
        differences=[i for i,(a,b) in enumerate(zip(raw,parent)) if a!=b]
        assert differences==row['patched_byte_offsets']
        assert all(at<=i<at+4 or 0xA0<=i<0xAC or i==0xBD for i in differences)
    proofs=info['proofs'];assert proofs,'Missing native evidence'
    tested=set();common=set()
    for proof in proofs:
        path=Path(proof['file']);assert not path.is_absolute() and '..' not in path.parts
        raw=(directory/path).read_bytes();assert digest(raw)==proof['sha256']
        report=json.loads(raw);assert report.get('passed') is True
        target=proof['target'];kind=proof['kind']
        expected=info['parent_rom_sha256'] if target=='common' else next(r['sha256'] for r in info['variants'] if r['file']==target)
        if kind=='reproduction':
            assert len(report['layers'])==100 and not report['differences']
        else:assert report['rom_sha256']==expected,(target,kind,'Stale evidence')
        if target=='common':common.add(kind)
        else:
            cap,hard=VARIANTS[target];assert report['max_national']==cap
            if kind=='gym-teams':
                assert len(report['checks'])==192
                assert len({c['leader'] for c in report['checks']})==16
                assert report['difficulty']==('Hard' if hard else 'Normal')
            elif kind=='variant-rules':assert report['perfect_ivs'] is hard and report['aquatic_samples']>0
            else:raise AssertionError(('Unknown variant proof',kind))
            tested.add((target,kind))
    assert tested=={(name,kind) for name in VARIANTS for kind in ['gym-teams','variant-rules']}
    assert {'galactic-chapter','league-kanto','league-hoenn','mega-reversion','surf-passages','sharp-map','birth-confirmation','reproduction',
            'badge-tabs','crossover-visits','protagonist-0','protagonist-1','protagonist-2','protagonist-3',
            'modern-bag','species-stats','ability-item-registry','player-evolutions','abilities-slot-2','field-rules'}<=common
    print('Verified four ROMs and',len(proofs),'native/reproduction reports')
    return info

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--directory',type=Path,default=ROOT/'mods/hoenn/versions')
    verify(p.parse_args().directory)
