"""Move Hoenn's first champion family reward to the selected residence."""
import argparse
import hashlib
import json
from pathlib import Path
from prepare_crossing import PIN
from prepare_family import LAYERS_BEFORE


def prepare(source):
    source = Path(source)
    marker = source / '.journey-family-postgame'
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
                                 'league-access', 'league-completion', 'league-history', 'league-display']:
        expected.update(json.loads((source / ('.journey-' + layer)).read_text())['prepared_sha256'])
    originals, inputs, outputs = {}, {}, {}

    def change(path, old, new):
        raw = outputs.get(path, (source / path).read_bytes())
        if path not in originals:
            assert hashlib.sha256(raw).hexdigest() == expected[path], path
            originals[path] = expected[path]
            if path in acquired['sha256']:
                inputs[path] = acquired['sha256'][path]
        body = raw.decode()
        assert body.count(old) == 1, (path, old)
        outputs[path] = body.replace(old, new).encode()

    change('include/journey_family.h', '#endif', '''void JourneyFamilyPostgamePending(void);
void JourneyFamilyGiveSSTicket(void);
#endif''')
    change('data/specials.inc', '\tdef_special JourneyBirthArrivalVehicle', '''\tdef_special JourneyBirthArrivalVehicle
\tdef_special JourneyFamilyPostgamePending
\tdef_special JourneyFamilyGiveSSTicket''')
    change('src/journey_family.c', '#include "journey_family_homes.h"', '''#include "journey_family_homes.h"

// Read Hoenn's bank directly: the selected family can live in Kanto.
void JourneyFamilyPostgamePending(void)
{
    gSpecialVar_Result = 0;
    if (JourneyFamilySelectedHome() == NULL
        || !(gSaveBlock1Ptr->flags[FLAG_SYS_GAME_CLEAR / 8] & (1 << (FLAG_SYS_GAME_CLEAR % 8))))
        return;
    if (!FlagGet(FLAG_RECEIVED_SS_TICKET)) gSpecialVar_Result |= 1;
    if (!FlagGet(FLAG_LATIOS_OR_LATIAS_ROAMING)) gSpecialVar_Result |= 2;
}

void JourneyFamilyGiveSSTicket(void)
{
    JourneyFamilyPostgamePending();
    if (!(gSpecialVar_Result & 1)) { gSpecialVar_Result = 0; return; }
    if (!CheckBagHasItem(ITEM_SS_TICKET, 1) && !AddBagItem(ITEM_SS_TICKET, 1))
    { gSpecialVar_Result = 2; return; }
    FlagSet(FLAG_RECEIVED_SS_TICKET);
    gSpecialVar_Result = 1;
}''')
    change('data/scripts/hall_of_fame.inc', '''EverGrandeCity_HallOfFame_EventScript_ReadyReceiveSSTicketEvent::
\tsetvar VAR_LITTLEROOT_HOUSES_STATE_MAY, 3''', '''EverGrandeCity_HallOfFame_EventScript_ReadyReceiveSSTicketEvent::
\tgoto_if_ne VAR_JOURNEY_FAMILY_HOME, 0, JourneyFamily_PostgameReady
\tsetvar VAR_LITTLEROOT_HOUSES_STATE_MAY, 3''')
    change('data/scripts/hall_of_fame.inc', 'EverGrandeCity_HallOfFame_EventScript_ReadyDexUpgradeEvent::', '''JourneyFamily_PostgameReady::
\tsetvar VAR_LITTLEROOT_HOUSES_STATE_MAY, 4
\tsetvar VAR_LITTLEROOT_HOUSES_STATE_BRENDAN, 4
\treturn

EverGrandeCity_HallOfFame_EventScript_ReadyDexUpgradeEvent::''')
    change('data/scripts/journey_family.inc', '''JourneyBirth_FamilyMother::
\tspecial JourneyBirthHomeRegion''', '''JourneyBirth_FamilyMother::
\tspecial JourneyFamilyPostgamePending
\tgoto_if_ne VAR_RESULT, 0, JourneyFamily_PostgameMother
\tspecial JourneyBirthHomeRegion''')
    change('data/scripts/journey_family.inc', 'JourneyBirth_FamilyMother::', (Path(__file__).with_name('family_postgame.inc').read_text() + '\nJourneyBirth_FamilyMother::'))
    # Every special species already has a dedicated 16-badge sanctuary.
    # Native roaming must not add random legendary encounters to ordinary routes.
    change('src/roamer.c', '''    u32 i;

    for (i = 0; i < ROAMER_COUNT; i++)
    {
        if (IsRoamerAt(i, gSaveBlock1Ptr->location.mapGroup, gSaveBlock1Ptr->location.mapNum) == TRUE && (Random() % 4) == 0)
        {
            CreateRoamerMonInstance(i);
            gEncounteredRoamerIndex = i;
            return TRUE;
        }
    }
    return FALSE;''', '''    // Legendary encounters belong to the dedicated sanctuaries, never routes.
    return FALSE;''')
    report = dict(status='selected_family_hoenn_postgame_candidate', source_commit=PIN,
                  selected_family_ss_ticket=True, hoenn_championship_required=True,
                  native_lati_news_choice_preserved=True, roaming_route_encounters_disabled=True,
                  save_layout_unchanged=True, full_campaign_validated=False,
                  input_sha256=inputs, original_sha256=originals,
                  prepared_sha256={p: hashlib.sha256(raw).hexdigest() for p, raw in outputs.items()})
    for path, raw in outputs.items():
        (source / path).write_bytes(raw)
    marker.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    print(json.dumps(prepare(parser.parse_args().source), indent=2))
