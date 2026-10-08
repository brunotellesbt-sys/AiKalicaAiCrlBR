"""Return from either League to the selected family home after credits."""
import argparse
import hashlib
import json
from pathlib import Path

from prepare_crossing import PIN
from prepare_family import LAYERS_BEFORE


def prepare(source):
    source = Path(source)
    marker = source / '.journey-league-completion'
    if marker.exists():
        report = json.loads(marker.read_text())
        for path, digest in report['prepared_sha256'].items():
            assert hashlib.sha256((source / path).read_bytes()).hexdigest() == digest, path
        return report
    acquired = json.loads((source / '.source-acquired.json').read_text())
    assert acquired['commit'] == PIN
    expected = dict(acquired['sha256'])
    for layer in LAYERS_BEFORE + ['family', 'travel-rules', 'birth', 'wild', 'habitats',
                                 'sanctuaries', 'ecology', 'abilities', 'mega-art', 'story-aftermath', 'league-access']:
        expected.update(json.loads((source / ('.journey-' + layer)).read_text())['prepared_sha256'])
    originals, inputs, outputs = {}, {}, {}

    def read(path):
        raw = (source / path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected[path], path
        originals[path] = expected[path]
        if path in acquired['sha256']:
            inputs[path] = acquired['sha256'][path]
        return raw.decode()

    path = 'include/overworld.h'
    body = read(path)
    needle = 'void SetContinueGameWarpToHealLocation(u8 healLocationId);'
    assert body.count(needle) == 1
    outputs[path] = body.replace(needle, 'void SetContinueGameWarp(s8 mapGroup, s8 mapNum, s8 warpId, s8 x, s8 y);\n' + needle).encode()
    path = 'include/journey_family.h'
    body = read(path)
    needle = 'void JourneyFamilyWarpBedroom(void);'
    assert body.count(needle) == 1
    outputs[path] = body.replace(needle, needle + '\nbool8 JourneyFamilySetContinueWarp(void);').encode()
    path = 'src/journey_family.c'
    body = read(path)
    body += """
// Store the home warp before Hall of Fame saves; resume after credits uses it.
bool8 JourneyFamilySetContinueWarp(void)
{
    const struct JourneyFamilyHome *home = JourneyFamilySelectedHome();
    if (home == NULL) return FALSE;
    // Littleroot uses a different native house for each player gender.
    if (VarGet(VAR_JOURNEY_FAMILY_HOME) == 17 && gSaveBlock2Ptr->playerGender == FEMALE)
    {
        SetContinueGameWarp(MAP_GROUP(MAP_LITTLEROOT_TOWN_MAYS_HOUSE_2F), MAP_NUM(MAP_LITTLEROOT_TOWN_MAYS_HOUSE_2F), -1, 6, 6);
        SetLastHealLocationWarp(HEAL_LOCATION_LITTLEROOT_TOWN_MAYS_HOUSE_2F);
    }
    else
    {
        SetContinueGameWarp(MAP_GROUP(home->bedroomMap), MAP_NUM(home->bedroomMap), -1, 6, 6);
        SetLastHealLocationWarp(home->healLocation);
    }
    return TRUE;
}
"""
    outputs[path] = body.encode()
    path = 'src/post_battle_event_funcs.c'
    body = read(path)
    needle = '#include "global.h"\n'
    assert body.count(needle) == 1
    body = body.replace(needle, needle + '#include "journey_family.h"\n')
    needle = """    if (gSaveBlock2Ptr->playerGender == MALE)
        SetContinueGameWarpToHealLocation(HEAL_LOCATION_LITTLEROOT_TOWN_BRENDANS_HOUSE_2F);
    else
        SetContinueGameWarpToHealLocation(HEAL_LOCATION_LITTLEROOT_TOWN_MAYS_HOUSE_2F);"""
    assert body.count(needle) == 1
    body = body.replace(needle, """    if (!JourneyFamilySetContinueWarp())
    {
        if (gSaveBlock2Ptr->playerGender == MALE)
            SetContinueGameWarpToHealLocation(HEAL_LOCATION_LITTLEROOT_TOWN_BRENDANS_HOUSE_2F);
        else
            SetContinueGameWarpToHealLocation(HEAL_LOCATION_LITTLEROOT_TOWN_MAYS_HOUSE_2F);
    }""")
    needle = '    SetContinueGameWarpToHealLocation(HEAL_LOCATION_PALLET_TOWN);'
    assert body.count(needle) == 1
    body = body.replace(needle, '    if (!JourneyFamilySetContinueWarp())\n    ' + needle)
    outputs[path] = body.encode()
    preserved = {}
    for path in ['data/maps/EverGrandeCity_PokemonLeague_1F/scripts.inc', 'data/scripts/hall_of_fame.inc']:
        assert hashlib.sha256((source / path).read_bytes()).hexdigest() == expected[path], path
        preserved[path] = expected[path]
    report = dict(status='selected_home_after_both_leagues_candidate', source_commit=PIN,
                  both_leagues_return_to_selected_bedroom=True, no_home_preserves_original_fallback=True,
                  save_layout_unchanged=True, badges_and_champion_flags_unchanged=True,
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
