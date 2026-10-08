"""Use regional badges for Indigo access and separate champion/rematch flags."""
import argparse
import hashlib
import json
from pathlib import Path

from prepare_crossing import PIN
from prepare_family import LAYERS_BEFORE


def prepare(source):
    source = Path(source)
    marker = source / '.journey-league-access'
    if marker.exists():
        report = json.loads(marker.read_text())
        for path, digest in report['prepared_sha256'].items():
            assert hashlib.sha256((source / path).read_bytes()).hexdigest() == digest, path
        return report
    acquired = json.loads((source / '.source-acquired.json').read_text())
    assert acquired['commit'] == PIN
    expected = dict(acquired['sha256'])
    for layer in LAYERS_BEFORE + ['family', 'travel-rules', 'birth', 'wild', 'habitats',
                                 'sanctuaries', 'ecology', 'abilities', 'mega-art', 'story-aftermath']:
        expected.update(json.loads((source / ('.journey-' + layer)).read_text())['prepared_sha256'])
    originals, inputs, outputs = {}, {}, {}

    def read(path):
        raw = (source / path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected[path], path
        originals[path] = expected[path]
        if path in acquired['sha256']:
            inputs[path] = acquired['sha256'][path]
        return raw.decode()

    path = 'include/constants/flags.h'
    body = read(path)
    assert '0X1AC2' not in body.upper()  # Slot is inside the already allocated save flag bank.
    needle = '#define FLAG_JOURNEY_HOENN_STARTER_GIVEN 0x1AC1\n'
    assert body.count(needle) == 1
    outputs[path] = body.replace(needle, needle + '#define FLAG_KANTO_IS_CHAMPION 0x1AC2\n').encode()
    path = 'src/event_data.c'
    body = read(path)
    needle = '        if (id == FLAG_SYS_GAME_CLEAR)\n            return FLAG_KANTO_GAME_CLEAR;'
    assert body.count(needle) == 1
    outputs[path] = body.replace(needle, needle + '\n        if (id == FLAG_IS_CHAMPION)\n            return FLAG_KANTO_IS_CHAMPION;').encode()

    path = 'data/maps/IndigoPlateau_PokemonCenter_1F_Frlg/scripts.inc'
    body = read(path)
    start = body.index('IndigoPlateau_PokemonCenter_1F_OnTransition::')
    end = body.index('IndigoPlateau_PokemonCenter_1F_EventScript_GymGuy::')
    checks = ''.join(f'\tgoto_if_unset FLAG_KANTO_BADGE{i:02d}_GET, IndigoPlateau_Journey_NotAllBadges\n' for i in range(1,9))
    replacement = '''IndigoPlateau_PokemonCenter_1F_OnTransition::
\tsetrespawn HEAL_LOCATION_INDIGO_PLATEAU
\tcall IndigoPlateau_Journey_CheckBadges
\tgoto_if_eq VAR_RESULT, FALSE, IndigoPlateau_Journey_BlockDoor
\tsetobjectxyperm LOCALID_LEAGUE_DOOR_GUARD, 5, 3
\tend

IndigoPlateau_Journey_BlockDoor::
\tsetobjectxyperm LOCALID_LEAGUE_DOOR_GUARD, 4, 2
\tend

IndigoPlateau_Journey_CheckBadges::
''' + checks + '''\tsetvar VAR_RESULT, TRUE
\treturn

IndigoPlateau_Journey_NotAllBadges::
\tsetvar VAR_RESULT, FALSE
\treturn

IndigoPlateau_PokemonCenter_1F_EventScript_DoorGuard::
\tlock
\tfaceplayer
\tcall IndigoPlateau_Journey_CheckBadges
\tgoto_if_eq VAR_RESULT, FALSE, IndigoPlateau_Journey_Denied
\tmsgbox IndigoPlateau_PokemonCenter_1F_Text_FaceEliteFourGoodLuck
\trelease
\tend

IndigoPlateau_Journey_Denied::
\tmsgbox IndigoPlateau_Journey_TextNeedKantoBadges, MSGBOX_DEFAULT
\trelease
\tend

IndigoPlateau_Journey_TextNeedKantoBadges::
\t.string "The KANTO LEAGUE requires all\\n"
\t.string "eight KANTO GYM BADGES.\\p"
\t.string "HOENN BADGES count toward\\n"
\t.string "the HOENN LEAGUE instead.$"

'''
    outputs[path] = (body[:start] + replacement + body[end:]).encode()
    path = 'data/scripts/hall_of_fame_frlg.inc'
    body = read(path)
    needle = 'EventScript_SetDefeatedEliteFourFlagsVars::\n'
    assert body.count(needle) == 1
    outputs[path] = body.replace(needle, needle + '\tsetflag FLAG_KANTO_IS_CHAMPION\n').encode()
    preserved = {}
    for path in ['data/maps/EverGrandeCity_PokemonLeague_1F/scripts.inc', 'data/scripts/hall_of_fame.inc']:
        assert hashlib.sha256((source / path).read_bytes()).hexdigest() == expected[path], path
        preserved[path] = expected[path]
    report = dict(status='independent_regional_league_access_candidate', source_commit=PIN,
                  kanto_entry='all eight Kanto badges; no National Dex or champion prerequisite',
                  hoenn_guard_preserved=True, kanto_champion_flag=0x1AC2,
                  champion_rematches_independent=True, save_layout_unchanged=True,
                  full_campaign_validated=False, preserved_native_sha256=preserved,
                  input_sha256=inputs, original_sha256=originals,
                  prepared_sha256={p: hashlib.sha256(raw).hexdigest() for p,raw in outputs.items()})
    for path, raw in outputs.items():
        (source / path).write_bytes(raw)
    marker.write_text(json.dumps(report,indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    print(json.dumps(prepare(parser.parse_args().source),indent=2))
