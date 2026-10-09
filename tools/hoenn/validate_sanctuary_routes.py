"""Walk all sanctuary approaches, altars and returns with native water prompts.
Initial party/badges and one surface placement per site are fixtures.
No internal cave warps, field-effect entries or altar script entries are used.
"""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
exec(compile((ROOT / 'tools/hoenn/validate_team_missions.py').read_text().split('\nwins, completed =')[0],
             str(ROOT / 'tools/hoenn/validate_team_missions.py'), 'exec'))
for f in kanto_flags + hoenn_flags: rawflag(f, False)
native('ScriptSetMonMoveSlot', 0, 291, 2)
sanctuaries = json.loads((source / '.journey-sanctuaries').read_text())
names = list(dict.fromkeys(n for site in sanctuaries['sites'] for n in
    [site['surface'], site['map']] + (['JourneyDepth' + site['theme']] if site['access'] == 'dive' else [])))
allowed = set()
walk_prefix = 'sanctuary-route'
exec(compile((ROOT / 'tools/hoenn/native_water_walk.py').read_text(),
             str(ROOT / 'tools/hoenn/native_water_walk.py'), 'exec'))
checks, saves, altars = [], [], []

def snapshot():
    return dict(map=by_location[location()], position=list(position()), mode=lib.read8(s['gPlayerAvatar']) & 25,
                kanto_badges=native('JourneyGymBadgeCount', 1), hoenn_badges=native('JourneyGymBadgeCount', 0),
                special_capture_unlocked=bool(native('JourneySpecialUnlocked')))

def checkpoint(label, mode):
    before = snapshot()
    assert before['mode'] == mode, (label, before)
    assert before['kanto_badges'] == before['hoenn_badges'] == 0
    assert not before['special_capture_unlocked']
    assert native('TrySavingData', 0, max_frames=6000) == 1
    assert native('LoadGameSave', 0, max_frames=6000) == 1
    lib.write32(s['gMain'] + 4, s['CB2_ContinueSavedGame'] | 1)
    step(1500); finish()
    after = snapshot(); assert before == after, (label, before, after)
    saves.append(dict(label=label, before=before, after=after))
    picture(label + '-after-continue')

def water_change(target, emerge=False):
    assert native('TrySetDiveWarp') == (1 if emerge else 2)
    if emerge: press(2)
    for _ in range(160):
        press(1)
        if location() == map_id(target): break
    step(120); finish()
    assert location() == map_id(target), (target, location(), position())

for site in sanctuaries['sites']:
    theme, surface, chamber = site['theme'], site['surface'], site['map']
    cx, cy = site['entry']
    start = (cx, cy + 9) if site['access'] == 'surf' else (cx + 1, cy + 1)
    warp(surface, *start) # One initial travel fixture per site.
    native('SetPlayerAvatarTransitionFlags', 8); step(30)
    entry_steps, entry_transitions, entry_prompts = walked, len(transitions), len(surf_prompts)
    if site['access'] == 'dive': water_change('JourneyDepth' + theme)
    walk((chamber, 14, 17))
    picture(theme + '-native-chamber-entry')
    captures = [c for c in sanctuaries['captures'] if c['site'] == theme]
    for cap in captures:
        x, y = cap['position']
        walk((chamber, x, y + 1))
        assert not flag(cap['flag_id'])
        assert not native('GetSetPokedexFlag', cap['national_dex'], 1)
        step(4, 64); step(30)
        assert native('GetPlayerFacingDirection') == 2
        lib.write16(s['gSpecialVar_Result'], 0xFFFF) # Sentinel: the NPC must actually execute its permission.
        press(1)
        for _ in range(120):
            assert lib.read32(s['gMain'] + 4) & ~1 not in [s['CB2_InitBattle'], s['BattleMainCB2']], cap
            if idle(): break
            press(1)
        else: raise AssertionError(('Altar did not release controls', cap))
        assert lib.read16(s['gSpecialVar_Result']) == 0, cap
        assert not flag(cap['flag_id']) and not native('GetSetPokedexFlag', cap['national_dex'], 1)
        altars.append(dict(site=theme, national_dex=cap['national_dex'], species=cap['species'],
                           position=list(position()), native_interaction_refused=True,
                           captured_flag=False, caught_dex=False))
    checkpoint(theme + '-chamber', 1)
    walk(((surface if site['access'] == 'surf' else 'JourneyDepth' + theme), *start))
    if site['access'] == 'dive':
        checkpoint(theme + '-underwater-return', 16)
        water_change(surface, emerge=True)
    checkpoint(theme + '-surface-return', 8)
    checks.append(dict(site=theme, access=site['access'], surface=surface, chamber=chamber,
                       initial_position=list(start), final_position=list(position()),
                       position_changes=walked - entry_steps,
                       transitions=transitions[entry_transitions:],
                       native_surf_prompts=surf_prompts[entry_prompts:], altars=len(captures)))
    print('Native full sanctuary route:', theme, len(captures), flush=True)
assert len(checks) == 14 and len(altars) == 105 and len(saves) == 33
assert not wins
lib.stop()
(args.output / 'sanctuary-routes.json').write_text(json.dumps(dict(
    passed=True, rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
    sites=checks, altars=altars, save_continue=saves,
    position_changes=walked, native_dive_and_emerge_prompts=True,
    no_internal_warps_or_field_effect_or_script_entries=True,
    initial_party_badges_and_fourteen_surface_positions_are_fixtures=True,
    wild_encounters_disabled=True, full_campaign_playthrough=False,
    capture_or_balance_validated=False), indent=2) + '\n')
print('All fourteen sanctuary routes and 105 locked altars passed', flush=True)
