"""Win the first Elite Four battle in either region with the other champion set.

Badges and the other region's championship are fixtures. Entry, battle victory,
progression door and flash save run natively; this is not a full league victory.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--library', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--region', choices=['kanto','hoenn'], required=True)
parser.add_argument('--rematch', action='store_true', help='Kanto championship fixture selects Lorelei rematch')
run_options = parser.parse_args()
if run_options.rematch and run_options.region != 'kanto':
    parser.error('--rematch only applies to Kanto')
sys.argv = [sys.argv[0], '--source', str(run_options.source), '--library', str(run_options.library),
            '--output', str(run_options.output)]
bootstrap = (ROOT / 'tools/hoenn/validate_abilities.py').read_text().split('\nability_field,')[0]
exec(compile(bootstrap, str(ROOT / 'tools/hoenn/validate_abilities.py'), 'exec'))
kanto = run_options.region == 'kanto'


def raw_flag(flag, enabled):
    address = save() + 4720 + flag // 8
    value, mask = lib.read8(address), 1 << (flag & 7)
    lib.write8(address, value | mask if enabled else value & ~mask)


for flags, enabled in [(range(0x1AB0,0x1AB8), kanto),
                       ([lib.read16(s['gBadgeFlags'] + 2*i) for i in range(8)], not kanto)]:
    for flag in flags:
        raw_flag(flag, enabled)
champion = abi[111] - 0x2A + 0x1F
game_clear = abi[111] - 0x2A + 4
for flag, enabled in [(champion,kanto), (game_clear,kanto), (0x1AC2,not kanto), (0x1AB8,not kanto)]:
    raw_flag(flag,enabled)
if run_options.rematch:
    raw_flag(0x1AC2,True)
    raw_flag(0x1AB8,True)
native('EnableNationalPokedex')
party, scratch = s['gParties'], s['gStringVar4'] + 800
for i in range(6*abi[2]):
    lib.write8(party+i,0)
lib.write8(s['gPartiesCount'],0)
for i in range(6):
    assert native('ScriptGiveMon',abi[68],100,0)==0
    lib.write8(scratch,5);native('SetMonData',party+i*abi[2],abi[96],scratch)
    lib.write8(scratch,2 if i==0 else 0);native('SetMonData',party+i*abi[2],abi[65],scratch)
    for slot in range(4):
        native('ScriptSetMonMoveSlot',i,(abi[104] if kanto else abi[76]) if slot==0 else 0,slot)
identity=[native('GetMonData2',party+i*abi[2],abi[105]) for i in range(6)]
entry = 'IndigoPlateau_PokemonCenter_1F_Frlg' if kanto else 'EverGrandeCity_PokemonLeague_1F'
room = 'PokemonLeague_LoreleisRoom_Frlg' if kanto else 'EverGrandeCity_SidneysRoom'
next_room = 'PokemonLeague_BrunosRoom_Frlg' if kanto else 'EverGrandeCity_Hall1'
defeated = abi[120] if kanto else abi[121]
expected_trainer = abi[118 if run_options.rematch else 117] if kanto else abi[119]
raw_flag(defeated,False)
warp(entry,4 if kanto else 9,4)
native('SetPlayerAvatarTransitionFlags',1);step(30)
if not kanto:
    step(40,64);press(1)
    for _ in range(150):
        if not lib.read8(s['sLockFieldControls']) and lib.read8(s['sGlobalScriptContextStatus'])==2:break
        press(1)
    else:raise AssertionError('League guard dialogue did not end')
for _ in range(200):
    step(4,64)
    if location()==map_id(room):break
else:raise AssertionError(('Cannot enter first room',location(),position()))
step(1000)
assert position()==(6,7),position()
step(16,64);step(30)
assert position()==(6,6),position()
picture(run_options.region+'-first-elite-room')
press(1)
actions={int(a,16) for a,kind,n in re.findall(r'^(\w+) (\w) (\S+)$',raw,re.M) if n=='HandleInputChooseAction'}
moves={int(a,16) for a,kind,n in re.findall(r'^(\w+) (\w) (\S+)$',raw,re.M) if n=='HandleInputChooseMove'}
started=ash_seen=False
attacks=0
for tick in range(2200):
    callback=lib.read32(s['gMain']+4)&~1
    if callback==s['BattleMainCB2']:
        started=True
        assert lib.read16(s['gTrainerBattleParameter']+abi[13])==expected_trainer
        ash_seen |= lib.read16(s['gBattleMons']+abi[75])==abi[69]
        controller=lib.read32(s['gBattlerControllerFuncs'])&~1
        if controller in actions or controller in moves:
            step(1,64);step(8);step(1,32);step(8)
            if controller in actions and ash_seen:picture(run_options.region+'-elite-ash-battle')
            press(1)
            attacks += controller in moves
        else:press(2)
    elif started and callback==s['CB2_Overworld']:
        break
    else:press(1)
else:
    picture(run_options.region+'-elite-incomplete')
    raise AssertionError(('Elite battle incomplete',attacks,hex(callback)))
for _ in range(150):
    press(1)
    if lib.read8(s['sGlobalScriptContextStatus'])==2 and not lib.read8(s['sLockFieldControls']):break
else:raise AssertionError('Elite aftermath did not end')
assert started and ash_seen and attacks>0 and native('FlagGet',defeated)
assert [native('GetMonData2',party+i*abi[2],abi[105]) for i in range(6)]==identity
assert native('GetMonData2',party,abi[7])==abi[68]
assert native('GetMonData2',party,abi[65])==2
assert bool(native('FlagGet',champion)) == run_options.rematch, 'Own championship changed after first Elite battle'
# The defeated trainer still occupies (6, 5); take the aisle to the open door.
step(16,32);step(30)
step(48,64);step(30)
step(16,16);step(30)
assert position()==(6,3),position()
for _ in range(80):
    step(4,64)
    if location()==map_id(next_room):break
else:raise AssertionError(('Progression door blocked after victory',location(),position()))
step(1000)
picture(run_options.region+'-elite-next-room')
warp(entry,4 if kanto else 9,4)
assert native('TrySavingData',0,max_frames=6000)==1
raw_flag(defeated,False)
assert native('LoadGameSave',0)==1
step(30)
assert native('FlagGet',defeated)
assert native('GetMonData2',party,abi[65])==2
assert bool(native('FlagGet',champion)) == run_options.rematch
lib.stop()
result=dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
            region=run_options.region,first_trainer_id=expected_trainer,real_first_elite_victory=True,
            other_region_champion_does_not_select_kanto_rematch=True if kanto and not run_options.rematch else None,
            own_kanto_champion_selects_rematch=run_options.rematch,
            attacks=attacks,ash_after_ko=ash_seen,party_identity_preserved=True,
            ash_reverted_after_battle=True,native_progression_door=True,native_flash_save_reload=True,
            badge_and_champion_states_are_fixtures=True,full_league_victory=False,full_campaign_playthrough=False)
(args.output/(run_options.region+('-elite-rematch.json' if run_options.rematch else '-elite-battle.json'))).write_text(json.dumps(result,indent=2)+'\n')
print(result,flush=True)
