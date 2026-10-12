"""Allow backing out to region selection and confirm the named destination."""
import argparse, hashlib, json
from pathlib import Path
from prepare_preferred_mossdeep_port import PRIOR, LAYER as PREVIOUS
LAYER = 'birth-confirmation'
PRIOR = PRIOR + [PREVIOUS]
def prepare(source):
    source = Path(source)
    marker = source / ('.journey-' + LAYER)
    if marker.exists():
        result = json.loads(marker.read_text())
        for path, digest in result['prepared_sha256'].items():
            assert hashlib.sha256((source / path).read_bytes()).hexdigest() == digest, path
        return result
    expected = dict(json.loads((source / '.source-acquired.json').read_text())['sha256'])
    for layer in PRIOR:
        expected.update(json.loads((source / ('.journey-' + layer)).read_text())['prepared_sha256'])
    outputs, originals = {}, {}
    def stage(path, text):
        old = (source / path).read_bytes()
        digest = hashlib.sha256(old).hexdigest()
        assert digest == expected[path], path
        originals[path] = digest
        outputs[path] = text.encode()
    path = 'data/scripts/journey_birth.inc'
    text = (source / path).read_text()
    end = text.index('JourneyBirth_Arrival::')
    text = '''JourneyBirth_ChooseCity::
\tfadescreen FADE_FROM_BLACK
\tlockall
\tmsgbox JourneyBirth_Text_ChooseCity
\tclosemessage
\tspecial JourneyBirthApplyIntroRegion
JourneyBirth_CityMenu::
\tgoto_if_eq VAR_JOURNEY_START_REGION, 2, JourneyBirth_ChooseSevii
\tgoto_if_eq VAR_JOURNEY_START_REGION, 1, JourneyBirth_ChooseKanto
\tmultichoicegrid 0, 0, MULTI_JOURNEY_START_HOENN, 3, FALSE
\tgoto JourneyBirth_ConfirmCity
JourneyBirth_ChooseKanto::
\tmultichoicegrid 0, 0, MULTI_JOURNEY_START_CITIES, 3, FALSE
\tgoto JourneyBirth_ConfirmCity
JourneyBirth_ChooseSevii::
\tmultichoice 0, 0, MULTI_JOURNEY_START_SEVII, FALSE
JourneyBirth_ConfirmCity::
\tgoto_if_eq VAR_RESULT, MULTI_B_PRESSED, JourneyBirth_ChooseRegionAgain
\tcopyvar VAR_0x8008, VAR_RESULT
\tspecial JourneyBirthPreviewCity
\tmsgbox JourneyBirth_Text_ConfirmDestination
\tclosemessage
\tyesnobox 20, 8
\tgoto_if_eq VAR_RESULT, FALSE, JourneyBirth_CityMenu
\tcopyvar VAR_RESULT, VAR_0x8008
\tspecial JourneyBirthChooseCity
\treleaseall
\tend
JourneyBirth_ChooseRegionAgain::
\tmultichoice 0, 0, MULTI_JOURNEY_START_REGIONS, TRUE
\tspecial JourneyBirthSelectRegion
\tgoto JourneyBirth_CityMenu
JourneyBirth_Text_ConfirmDestination::
\t.string "Start your journey in\\n"
\t.string "{STR_VAR_1}?$"

''' + text[end:]
    stage(path, text)
    path = 'src/journey_birth.c'
    text = (source / path).read_text().replace('#include "global.h"', '#include "global.h"\n#include "region_map.h"\n#include "string_util.h"\n#include "journey_intro.h"', 1)
    text = text.replace('    VarSet(VAR_JOURNEY_START_REGION, region);', '    gJourneyIntroRegion = region;\n    VarSet(VAR_JOURNEY_START_REGION, region);', 1)
    text += '''
void JourneyBirthPreviewCity(void)
{
    u16 choice = gSpecialVar_Result;
    bool32 hoenn = VarGet(VAR_JOURNEY_START_REGION) == 0;
    if (VarGet(VAR_JOURNEY_START_REGION) == 2)
        choice += 9;
    u16 index = choice + (hoenn ? 16 : 0);
    if (index >= ARRAY_COUNT(sJourneyBirthArrivals))
        index = 0;
    u16 map = sJourneyBirthArrivals[index].map;
    const struct MapHeader *header = Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(map), MAP_NUM(map));
    GetMapName(gStringVar1, header->regionMapSectionId, 0);
}
'''
    stage(path, text)
    path = 'data/specials.inc'
    stage(path, (source / path).read_text() + '\n\tdef_special JourneyBirthPreviewCity\n')
    result = dict(layer=LAYER, city_confirmation=True, city_cancel_returns_to_region=True,
                  original_sha256=originals,
                  prepared_sha256={p: hashlib.sha256(raw).hexdigest() for p, raw in outputs.items()})
    for path, raw in outputs.items():
        (source / path).write_bytes(raw)
    marker.write_text(json.dumps(result, indent=2) + '\n')
    return result
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    print(json.dumps(prepare(parser.parse_args().source), indent=2))
