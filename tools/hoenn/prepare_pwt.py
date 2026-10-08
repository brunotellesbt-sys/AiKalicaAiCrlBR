"""Add an independent eight-player Singles PWT module at the Battle Frontier."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
from prepare_crossing import PIN
from prepare_family import LAYERS_BEFORE

HERE = Path(__file__).resolve().parent

def prepare(source):
    source = Path(source)
    marker = source / '.journey-pwt'
    if marker.exists():
        report = json.loads(marker.read_text())
        for path, digest in report['prepared_sha256'].items():
            assert hashlib.sha256((source / path).read_bytes()).hexdigest() == digest, path
        return report
    acquired = json.loads((source / '.source-acquired.json').read_text())
    assert acquired['commit'] == PIN
    expected = dict(acquired['sha256'])
    for layer in LAYERS_BEFORE + ['family', 'travel-rules', 'birth', 'wild', 'habitats',
                                 'sanctuaries', 'ecology', 'abilities', 'mega-art', 'story-aftermath',
                                 'league-access', 'league-completion', 'league-history', 'league-display', 'family-postgame']:
        expected.update(json.loads((source / ('.journey-' + layer)).read_text())['prepared_sha256'])
    originals, inputs, outputs, preserved = {}, {}, {}, {}

    def read(path):
        if path in outputs: return outputs[path].decode()
        raw = (source / path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected[path], path
        preserved[path] = expected[path]
        return raw.decode()

    def write(path, body):
        if path in expected:
            originals[path] = expected[path]
            read(path)
            preserved.pop(path, None)
            if path in acquired['sha256']: inputs[path] = acquired['sha256'][path]
        else:
            assert not (source / path).exists(), path
        outputs[path] = body.encode()

    def change(path, old, new):
        body = read(path)
        assert body.count(old) == 1, (path, old)
        write(path, body.replace(old, new))

    for filename, path in [('pwt.h', 'include/journey_pwt.h'), ('pwt.c', 'src/journey_pwt.c'), ('pwt.inc', 'data/scripts/journey_pwt.inc')]:
        write(path, (HERE / filename).read_text())
    change('data/event_scripts.s', '\t.include "data/scripts/journey_family.inc"', '\t.include "data/scripts/journey_family.inc"\n\t.include "data/scripts/journey_pwt.inc"\n\t.include "data/maps/JourneyPWTLobby/scripts.inc"\n\t.include "data/maps/JourneyPWTArena/scripts.inc"')
    path = 'data/specials.inc'
    write(path, read(path) + ''.join('\tdef_special ' + name + '\n' for name in ['JourneyPWTChoose', 'JourneyPWTBegin', 'JourneyPWTBufferBracket', 'JourneyPWTBufferRound', 'JourneyPWTPrepareBattle', 'BattleSetup_StartPWTBattle', 'JourneyPWTAdvance', 'JourneyPWTFinish', 'JourneyPWTActive']))
    change('include/constants/battle.h', '#define BATTLE_TYPE_14                 (1 << 14)', '#define BATTLE_TYPE_14                 (1 << 14)\n#define BATTLE_TYPE_PWT                BATTLE_TYPE_14')
    change('src/battle_main.c', '''static u8 CreateNPCTrainerParty(struct Pokemon *party, u16 trainerNum)
{''', '''static u8 CreateNPCTrainerParty(struct Pokemon *party, u16 trainerNum)
{
    if (gBattleTypeFlags & BATTLE_TYPE_PWT) return PARTY_SIZE; // Module prepared the opponent's copies.''')
    # Facility rules, while retaining native trainer names/portraits and parties
    # in all existing Frontier facilities. PWT is not part of FRONTIER's mask.
    path = 'src/battle_main.c'
    body = read(path)
    body = body.replace('BATTLE_TYPE_FRONTIER | BATTLE_TYPE_TRAINER_HILL', 'BATTLE_TYPE_FRONTIER | BATTLE_TYPE_PWT | BATTLE_TYPE_TRAINER_HILL')
    body = body.replace('| BATTLE_TYPE_FRONTIER_NO_PYRAMID', '| BATTLE_TYPE_FRONTIER_NO_PYRAMID\n                                            | BATTLE_TYPE_PWT')
    body = body.replace('else if (gBattleTypeFlags & BATTLE_TYPE_TRAINER_HILL)', 'else if (gBattleTypeFlags & (BATTLE_TYPE_TRAINER_HILL | BATTLE_TYPE_PWT))')
    # This mask also suppresses ordinary item removal at battle end.
    write(path, body)
    path = 'src/battle_ai_main.c'
    body = read(path).replace('| BATTLE_TYPE_SECRET_BASE | BATTLE_TYPE_FRONTIER', '| BATTLE_TYPE_SECRET_BASE | BATTLE_TYPE_FRONTIER | BATTLE_TYPE_PWT')
    body = body.replace('BATTLE_TYPE_FRONTIER | BATTLE_TYPE_EREADER_TRAINER', 'BATTLE_TYPE_FRONTIER | BATTLE_TYPE_PWT | BATTLE_TYPE_EREADER_TRAINER')
    write(path, body)
    change('src/battle_script_commands.c', '| BATTLE_TYPE_TRAINER_HILL\n              | BATTLE_TYPE_FRONTIER', '| BATTLE_TYPE_TRAINER_HILL\n              | BATTLE_TYPE_PWT\n              | BATTLE_TYPE_FRONTIER')
    path = 'src/battle_script_commands.c'
    body = read(path)
    start = body.index('static void Cmd_tryswapitems(void)\n{')
    end = body.index('\nstatic void ', start + 1)
    body = body[:start] + body[start:end].replace('| BATTLE_TYPE_FRONTIER', '| BATTLE_TYPE_FRONTIER\n                                  | BATTLE_TYPE_PWT') + body[end:]
    write(path, body)
    # Only enlarge the RAM selection order; Frontier save arrays and its 3/4
    # entry limits stay unchanged. Six-entry PWT labels need their own IDs.
    change('include/party_menu.h', 'gSelectedOrderFromParty[MAX_FRONTIER_PARTY_SIZE]', 'gSelectedOrderFromParty[PARTY_SIZE]')
    change('src/party_menu.c', 'gSelectedOrderFromParty[MAX_FRONTIER_PARTY_SIZE]', 'gSelectedOrderFromParty[PARTY_SIZE]')
    change('include/constants/party_menu.h', '#define PARTYBOX_DESC_DONT_HAVE   12', '#define PARTYBOX_DESC_DONT_HAVE   12\n#define PARTYBOX_DESC_PWT_FIFTH   13\n#define PARTYBOX_DESC_PWT_SIXTH   14')
    change('src/data/party_menu.h', 'static const u8 *const sDescriptionStringTable[] =', 'static const u8 sPWTEntryFifth[] = _(\"5th\");\nstatic const u8 sPWTEntrySixth[] = _(\"6th\");\nstatic const u8 *const sDescriptionStringTable[] =')
    change('src/data/party_menu.h', '    [PARTYBOX_DESC_DONT_HAVE]  = gText_DontHave,', '    [PARTYBOX_DESC_DONT_HAVE]  = gText_DontHave,\n    [PARTYBOX_DESC_PWT_FIFTH]  = sPWTEntryFifth,\n    [PARTYBOX_DESC_PWT_SIXTH]  = sPWTEntrySixth,')
    path = 'src/party_menu.c'
    body = read(path)
    body = body.replace('i + PARTYBOX_DESC_FIRST', 'GetBattleEntryDescription(i)')
    body = body.replace('static u8 GetMaxBattleEntries(void);', 'static u8 GetBattleEntryDescription(u8 rank);\nstatic u8 GetMaxBattleEntries(void);')
    body = body.replace('static u8 GetMaxBattleEntries(void)\n{', 'static u8 GetBattleEntryDescription(u8 rank)\n{\n    if (JourneyPWTSelectionActive() && rank >= 4)\n        return rank == 4 ? PARTYBOX_DESC_PWT_FIFTH : PARTYBOX_DESC_PWT_SIXTH;\n    return rank + PARTYBOX_DESC_FIRST;\n}\n\nstatic u8 GetMaxBattleEntries(void)\n{')
    write(path, body)
    change('src/party_menu.c', '#include "global.h"', '#include "global.h"\n#include "journey_pwt.h"\n#include "pokedex.h"')
    change('src/party_menu.c', '''if (species == GetMonData(&party[order[j] - 1], MON_DATA_SPECIES))''', '''if (species == GetMonData(&party[order[j] - 1], MON_DATA_SPECIES)
                || (JourneyPWTSelectionActive() && SpeciesToNationalPokedexNum(species) == SpeciesToNationalPokedexNum(GetMonData(&party[order[j] - 1], MON_DATA_SPECIES))))''')
    path = 'src/battle_util.c'
    body = read(path).replace('BATTLE_TYPE_FRONTIER | BATTLE_TYPE_TRAINER_HILL', 'BATTLE_TYPE_FRONTIER | BATTLE_TYPE_PWT | BATTLE_TYPE_TRAINER_HILL')
    write(path, body)

    for path in ['src/battle_dome.c', 'src/journey_gym_scaling.c', 'data/maps/BattleFrontier_BattleDomeLobby/scripts.inc']:
        read(path) # Explicitly preserve the existing facility and gym rules.
    path = 'data/battle_scripts_1.s'
    body = read(path).replace('jumpifbattletype BATTLE_TYPE_FRONTIER, BattleScript_FaintedMonSendOutNew', 'jumpifbattletype BATTLE_TYPE_FRONTIER | BATTLE_TYPE_PWT, BattleScript_FaintedMonSendOutNew')
    body = body.replace('jumpifbattletype BATTLE_TYPE_FRONTIER, BattleScript_LocalBattleLostPrintTrainersWinText', 'jumpifbattletype BATTLE_TYPE_FRONTIER, BattleScript_LocalBattleLostPrintTrainersWinText\n\tjumpifbattletype BATTLE_TYPE_PWT, BattleScript_LocalBattleLostEnd')
    write(path, body)
    change('src/battle_setup.c', '#include "global.h"', '#include "global.h"\n#include "journey_pwt.h"')
    change('src/battle_setup.c', 'void BattleSetup_StartTrainerBattle(void)', '''static void CB2_EndPWTBattle(void)
{
    // The script owns elimination and party restoration, with no trainer flags
    // or whiteout. A tournament victory is never a gym/story victory.
    SetMainCallback2(CB2_ReturnToFieldContinueScriptPlayMapMusic);
}

void BattleSetup_StartPWTBattle(void)
{
    gMain.savedCallback = CB2_EndPWTBattle;
    CreateBattleStartTask(GetTrainerBattleTransition(), 0);
    ScriptContext_Stop();
}

void BattleSetup_StartTrainerBattle(void)''')

    groups_path = 'data/maps/map_groups.json'
    groups = json.loads(read(groups_path))
    group = 'gMapGroup_JourneyPWT'
    assert group not in groups
    groups['group_order'].append(group)
    groups[group] = ['JourneyPWTLobby', 'JourneyPWTArena']
    write(groups_path, json.dumps(groups, indent=2) + '\n')
    lobby_path = 'data/maps/BattleFrontier_BattleDomeLobby/map.json'
    original_lobby = json.loads(read(lobby_path))
    native_lobby = copy.deepcopy(original_lobby)
    guide = next(o for o in native_lobby['object_events'] if o['script'].endswith('EventScript_Maniac'))
    guide.update(script='JourneyPWT_Travel', movement_type='MOVEMENT_TYPE_FACE_DOWN')
    write(lobby_path, json.dumps(native_lobby, indent=2) + '\n')
    lobby = copy.deepcopy(original_lobby)
    lobby.update(id='MAP_JOURNEY_PWT_LOBBY', name='JourneyPWTLobby')
    lobby['object_events'] = [copy.deepcopy(original_lobby['object_events'][0])]
    lobby['object_events'][0].update(local_id='LOCALID_PWT_ATTENDANT', script='JourneyPWT_Attendant')
    lobby['bg_events'] = []
    for warp in lobby['warp_events']:
        warp.update(dest_map='MAP_BATTLE_FRONTIER_BATTLE_DOME_LOBBY', dest_warp_id=255)
        # Map warp events require a target warp index. Match the native entrance.
        warp['dest_warp_id'] = 0
    arena = json.loads(read('data/maps/BattleFrontier_BattleDomeBattleRoom/map.json'))
    arena.update(id='MAP_JOURNEY_PWT_ARENA', name='JourneyPWTArena')
    arena['object_events'] = [o for o in arena['object_events'] if o.get('local_id') not in ['LOCALID_DOME_PLAYER', 'LOCALID_DOME_OPPONENT']]
    for obj in arena['object_events']:
        obj.pop('local_id', None)
        obj['script'] = '0x0'; obj['flag'] = '0'
        if 'VAR' in obj['graphics_id']: obj['graphics_id'] = 'OBJ_EVENT_GFX_MAN_3'
    for name, data in [('JourneyPWTLobby', lobby), ('JourneyPWTArena', arena)]:
        write(f'data/maps/{name}/map.json', json.dumps(data, indent=2) + '\n')
        script = f'{name}_MapScripts::\n\t.byte 0\n'
        if name == 'JourneyPWTArena':
            script = '''JourneyPWTArena_MapScripts::
\tmap_script MAP_SCRIPT_ON_FRAME_TABLE, JourneyPWTArena_OnFrame
\t.byte 0
JourneyPWTArena_OnFrame:
\tmap_script_2 VAR_TEMP_1, 0, JourneyPWT_ArenaStart
\t.2byte 0
'''
        write(f'data/maps/{name}/scripts.inc', script)
    report = dict(status='independent_frontier_singles_pwt_candidate', source_commit=PIN,
                  participants=8, rounds=3, team_size=6, level=50, reward_bp=3,
                  doubles_enabled=False, trainer_pool_size=18, save_layout_unchanged=True,
                  existing_dome_retained=True, full_campaign_validated=False,
                  input_sha256=inputs, original_sha256=originals,
                  preserved_native_sha256=preserved,
                  prepared_sha256={p: hashlib.sha256(raw).hexdigest() for p, raw in outputs.items()})
    for path, raw in outputs.items():
        (source / path).parent.mkdir(parents=True, exist_ok=True)
        (source / path).write_bytes(raw)
    marker.write_text(json.dumps(report, indent=2) + '\n')
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    print(json.dumps(prepare(parser.parse_args().source), indent=2))
