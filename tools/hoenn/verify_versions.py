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
    if release.get('validation_scope')=='extra-gyms':
        assert report['stale_test_edition_rejected']
        from package_review_rom import verify as verify_review
        review=verify_review(ROOT/'roms/rom-de-teste',ROOT/'mods/hoenn/versions/Pokemon-Journey-Gen1-9-Normal.gba')
        expected[review['file']]=review['sha256']
    checks=report['checks'];assert len(checks)==len(expected) and {c['file'] for c in checks}==set(expected)
    for row in checks:
        assert row['rom_sha256']==expected[row['file']] and row['actual_game_name']==row['file'], ('Stale browser evidence; rerun validate_versions_browser.cjs', row['file'])
        assert row['native_frames']>360 and row['exported_native_state_bytes']>1000
    sources=report['player_sources_sha256'];assert set(sources)=={'index.html','player.js','style.css'}
    for name,sha in sources.items():assert digest((ROOT/'web'/name).read_bytes())==sha,('Untested player source',name)
    print('Verified browser boot evidence and player sources for',len(expected),'editions')

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
    if directory.resolve()==(ROOT/'mods/hoenn/versions').resolve():
        assert {p.name for p in (ROOT/'roms').glob('*.gba')}==set(VARIANTS), 'roms/ must contain exactly four current editions'
        for row in info['variants']:
            assert digest((ROOT/'roms'/row['file']).read_bytes())==row['sha256'], ('Outdated roms/ download',row['file'])
        assert (ROOT/'roms/SHA256SUMS').read_bytes()==(directory/'SHA256SUMS').read_bytes()
    if info.get('validation_scope')=='extra-gyms':
        from verify_extra_gyms_update import verify_update
        verify_update(directory,info)
        print('Verified 24-badge circuit, native Surf repairs and isolated test ROM')
        return info
    if info.get('validation_scope')=='ever-grande-market':
        from verify_ever_grande_update import verify_update
        verify_update(directory,info)
        print('Verified Ever Grande homes, Mega market, gifts and red Sootopolis with PR93 preserved')
        return info
    if info.get('validation_scope')=='dewford-competitive-shop':
        from verify_dewford_shop_update import verify_update
        verify_update(directory,info)
        print('Verified four normal editions and test ROM with the Dewford training stall')
        return info
    if info.get('validation_scope')=='surf-review':
        from verify_surf_review_update import verify_update
        verify_update(directory,info)
        print('Verified four normal ROMs, eight cave branches and isolated test ROM')
        return info
    if info.get('validation_scope')=='annotated-world-links':
        from verify_continuous_ocean_update import verify_update
        verify_update(directory,info)
        print('Verified annotated world links, continuous water and preserved PR90 ports')
        return info
    if info.get('validation_scope')=='island-harbors':
        from verify_island_harbor_update import verify_update
        verify_update(directory,info)
        print('Verified four editions with Mossdeep terminal, Dewford bridge and authored island terrain')
        return info
    if info.get('validation_scope')=='sevii-harbors':
        from verify_sevii_harbor_update import verify_update
        verify_update(directory,info)
        print('Verified seven Sevii terminals, current Surf lanes and preserved prior ports')
        return info
    if info.get('validation_scope')=='three-harbor-terminals':
        from verify_three_harbor_update import verify_update
        verify_update(directory,info)
        print('Verified four editions with the three positioned harbor terminals')
        return info
    if info.get('validation_scope')=='fuchsia-harbor':
        from verify_fuchsia_update import verify_update
        verify_update(directory,info)
        print('Verified four Fuchsia terminal ROMs and preserved prior validation history')
        return info
    if info.get('validation_scope')=='sevii-surf-connections':
        from verify_sevii_update import verify_update
        verify_update(directory,info)
        print('Verified four continuous Sevii Surf ROMs and preserved port history')
        return info
    if info.get('validation_scope')=='sootopolis-harbor':
        from verify_sootopolis_update import verify_update
        verify_update(directory,info)
        print('Verified four Sootopolis harbor ROMs and preserved previous coastal evidence')
        return info
    if info.get('validation_scope')=='campaign-coastal-update':
        from verify_campaign_update import verify_update
        verify_update(directory,info)
        print('Verified four current coastal ROMs and separately preserved historical evidence')
        return info
    proofs=info['proofs'];assert proofs,'Missing native evidence'
    tested=set();common=set()
    for proof in proofs:
        path=Path(proof['file']);assert not path.is_absolute() and '..' not in path.parts
        raw=(directory/path).read_bytes();assert digest(raw)==proof['sha256']
        report=json.loads(raw);assert report.get('passed') is True
        target=proof['target'];kind=proof['kind']
        expected=info['parent_rom_sha256'] if target=='common' else next(r['sha256'] for r in info['variants'] if r['file']==target)
        if kind=='reproduction':
            if 'integration_layers' in info:assert report['layers']==info['integration_layers']
            else:assert len(report['layers'])==100
            assert not report['differences']
        else:assert report['rom_sha256']==expected,(target,kind,'Stale evidence')
        if target=='common':
            common.add(kind)
            if kind=='battle-interactions':
                from verify_battle_interactions import verify_report
                verify_report(report,expected)
            elif kind=='item-menu-actions':
                assert report['stone_animation_completed'] and report['stone_consumed_once']
                assert report['reusable_tm_taught_to_two_pokemon'] and len(report['learned'])==2
                assert report['item_activation_and_confirmation_are_controller_input']
                assert report['flash_reload_preserves_evolved_species_and_item_quantities']
            elif kind.startswith('item-menu-'):
                assert report['animation_completed'] and report['used_item_consumed_once']
                assert report['item_activation_and_confirmation_are_controller_input']
                assert report['flash_reload_preserves_evolved_species_and_item_quantities']
                if report['case']=='onix':assert report['held_item_after']==0 and report['level']==30
            elif kind.startswith('initial-campaign-'):
                assert kind=='initial-campaign-'+report['starting_region']
                assert report['controller_only'] and not report['full_campaign_playthrough']
                assert not any(report[key] for key in ['ram_writes','script_injection','synthetic_badges','boosted_stats','disabled_wild_encounters'])
                assert len(report['checkpoints'])>=9 and report['battles']
        else:
            cap,hard=VARIANTS[target]
            if kind!='pwt-world' and not kind.startswith(('generation-cup-','pwt-unboosted-')):assert report['max_national']==cap
            if kind=='gym-teams':
                assert len(report['checks'])==192
                assert len({c['leader'] for c in report['checks']})==16
                assert report['difficulty']==('Hard' if hard else 'Normal')
            elif kind=='variant-rules':assert report['perfect_ivs'] is hard and report['aquatic_samples']>0
            elif kind=='pwt-world':
                assert report['version_generation_cap']==(4 if cap==493 else 9)
                assert report['perfect_ivs'] is hard
                assert len(report['catalog_teams'])==(61 if cap==493 else 162)
                assert report['party_restored_byte_exact'] and report['player_moves_items_ability_personality_preserved']
                assert report['pwt_perfect_stats_override_normal_edition']
                if cap==1025:
                    assert report['complete_tournament_playthrough'] and len(report['actual_battles'])>=5
            elif kind.startswith('generation-cup-'):
                assert cap==493 and report['version_generation_cap']==4
                assert report['difficulty']==('Hard' if hard else 'Normal')
                assert report['cup_generation']==int(kind.rsplit('-',1)[1]) in range(1,5)
                assert report['complete_tournament_playthrough'] and report['champion']
                assert report['returned_to_lobby'] and report['party_restored_byte_exact'] and report['bp_reward']==10
                assert {b['stage'] for b in report['actual_battles']}=={0,1}
                assert all(b['outcome']==1 and b['level']==50 and b['player_team_size']==b['enemy_team_size']==6 for b in report['actual_battles'])
            elif kind=='battle-interactions':
                from verify_battle_interactions import verify_report
                verify_report(report,expected,cap,hard)
            elif kind.startswith('pwt-unboosted-'):
                from verify_pwt_balance import verify_report
                verify_report(report,expected,4 if cap==493 else 9,hard,int(kind.rsplit('-',1)[1]))
            elif kind=='special-encounters':
                assert report['event_only_families']==21 and report['actual_tv_capture_and_form_ui']
                assert len(report['rotom_changes'])==6 and len(report['dex_locations'])==21
                checks={c['case']:c for c in report['checks']}
                assert checks['rotom_tv_capture']['captured_base_form']
                assert checks['rotom_tv_capture']['repeat_capture_blocked']
                assert len(checks['deoxys_meteorite']['four_forms'])==4
                assert checks['keystone_installation']['consumed_once'] and checks['keystone_installation']['retry_without_second_item']
                assert len(checks['fossil_restoration']['recipes'])==15
            else:raise AssertionError(('Unknown variant proof',kind))
            tested.add((target,kind))
    kinds=['gym-teams','variant-rules']
    if 'integration_layers' in info:
        kinds.append('pwt-world')
        assert {'pwt-stadium','pwt-retirement'}<=common
        report=next(json.loads((directory/p['file']).read_text()) for p in proofs if p['kind']=='pwt-stadium')
        assert len(report['checks'])==162 and report['all_eligible_identities_spawned']
        assert report['nine_frames_per_identity'] and report['entrance_lane_unblocked']
        report=next(json.loads((directory/p['file']).read_text()) for p in proofs if p['kind']=='pwt-retirement')
        assert report['declined_round_with_controller'] and report['original_party_restored_byte_exact']
        assert report['no_bp_reward_for_retirement'] and report['player_ready_position']==[9,6]
    expected={(name,kind) for name in VARIANTS for kind in kinds}
    if info.get('validation_scope') in ('pwt-update','pwt-and-special-encounters'):
        expected={(name,'pwt-world') for name in VARIANTS}
    if info.get('generation_cups_validated'):
        expected|={(name,f'generation-cup-{generation}') for name,(cap,_) in VARIANTS.items() if cap==493 for generation in range(1,5)}
        assert {'pwt-encore','move-restrictions'}<=common
        report=next(json.loads((directory/p['file']).read_text()) for p in proofs if p['kind']=='move-restrictions')
        assert report['cases']>=60 and report['native_engine_functions']
    if info.get('battle_interactions_validated'):
        expected|={(name,'battle-interactions') for name in VARIANTS}
        assert 'battle-interactions' in common
    if info.get('pwt_balance_validated'):
        coverage=info['pwt_balance_tested_pools']
        assert set(coverage)==set(VARIANTS)
        for name,(cap,_) in VARIANTS.items():
            pools=coverage[name]
            assert pools and pools==sorted(set(pools))
            assert all(0<=pool<=(4 if cap==493 else 9) for pool in pools)
            expected|={(name,f'pwt-unboosted-{pool}') for pool in pools}
        assert {'pwt-registration','nonlevel-moves','pwt-obedience'}<=common
    if info.get('special_encounters_validated'):
        expected|={(name,'special-encounters') for name in VARIANTS}
    assert expected<=tested
    assert tested-expected<={(name,kind) for name in VARIANTS for kind in ['gym-teams','variant-rules']}
    required={'galactic-chapter','league-kanto','league-hoenn','mega-reversion','surf-passages','sharp-map','birth-confirmation','reproduction',
            'badge-tabs','crossover-visits','protagonist-0','protagonist-1','protagonist-2','protagonist-3',
            'modern-bag','species-stats','ability-item-registry','player-evolutions','abilities-slot-2','field-rules',
            'item-menu-actions','item-menu-alola-stone','item-menu-kadabra','item-menu-onix',
            'item-menu-pawmo','item-menu-gimmighoul','initial-campaign-kanto','initial-campaign-hoenn'}
    if info.get('validation_scope') in ('pwt-update','pwt-and-special-encounters'):
        assert 'integration_layers' in info and info['full_campaign_playthrough'] is False
        required={'reproduction','pwt-stadium','pwt-retirement'}
    assert required<=common
    print('Verified four ROMs and',len(proofs),'native/reproduction reports')
    return info

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--directory',type=Path,default=ROOT/'mods/hoenn/versions')
    verify(p.parse_args().directory)
