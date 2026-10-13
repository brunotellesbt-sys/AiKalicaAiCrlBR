"""Choose any of the four protagonists independently of the starting campaign."""
import argparse
from pathlib import Path
from candidate_layer import Layer
from prepare_named_character_presence import PRIOR,LAYER as PREVIOUS
LAYER='player-choice';PRIOR=PRIOR+[PREVIOUS]

def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if result:=layer.existing():return result
    source=layer.source
    # This variable is unused by both original campaigns. Zero preserves the
    # original appearance for a save made before the protagonist selector.
    for folder in ['src','data']:
        assert not any('VAR_EVER_GRANDE_CITY_STATE' in p.read_text(errors='ignore') for p in (source/folder).rglob('*.c' if folder=='src' else '*.inc'))
    p='include/journey_birth.h';text=(source/p).read_text().replace('#endif','bool32 JourneyAvatarIsKanto(void);\nvoid JourneyBirthChooseAvatar(void);\n#endif')
    layer.stage(p,text)
    p='src/journey_birth.c';text=(source/p).read_text()
    text=text.replace('#include "global.h"','#include "global.h"\n#include "field_player_avatar.h"',1)
    text+='''
bool32 JourneyAvatarIsKanto(void)
{
    u16 choice=VarGet(VAR_EVER_GRANDE_CITY_STATE);
    if(choice>=1 && choice<=4)return choice<=2;
    return gSaveBlock2Ptr->playerRegion==REGION_KANTO;
}
void JourneyBirthChooseAvatar(void)
{
    u16 choice=gSpecialVar_Result;
    if(choice>3)choice=0;
    VarSet(VAR_EVER_GRANDE_CITY_STATE,choice+1);
    gSaveBlock2Ptr->playerGender=choice&1;
    gPlayerAvatar.gender=choice&1;
    SetPlayerAvatarTransitionFlags(PLAYER_AVATAR_FLAG_ON_FOOT);
}
'''
    layer.stage(p,text)
    p='data/specials.inc';layer.stage(p,(source/p).read_text()+'\n\tdef_special JourneyBirthChooseAvatar\n')
    p='include/constants/script_menu.h';text=(source/p).read_text().replace('    MULTI_JOURNEY_START_SEVII,','    MULTI_JOURNEY_START_SEVII,\n    MULTI_JOURNEY_PLAYER_AVATAR,\n    MULTI_JOURNEY_EVOLUTION_REGION,').replace('#define MULTI_JOURNEY_EVOLUTION_REGION 256\n','')
    layer.stage(p,text)
    p='src/data/script_menu.h';text=(source/p).read_text()
    anchor='const struct MultichoiceList gMultichoiceLists[]'
    # Use the existing designated menu table; its storage type is unchanged.
    anchor=text[text.index('sMultichoiceLists[]'):].split('{',1)[0] if 'sMultichoiceLists[]' in text else anchor
    table=text.rfind('\n',0,text.index(anchor))
    text=text[:table]+'''
static const struct MenuAction sJourneyPlayerAvatars[]={
    {.text=COMPOUND_STRING("RED - KANTO BOY")},
    {.text=COMPOUND_STRING("LEAF - KANTO GIRL")},
    {.text=COMPOUND_STRING("BRENDAN - HOENN BOY")},
    {.text=COMPOUND_STRING("MAY - HOENN GIRL")},
};
'''+text[table:]
    text=text.replace('    [MULTI_JOURNEY_START_REGIONS]', '    [MULTI_JOURNEY_PLAYER_AVATAR] = MULTICHOICE(sJourneyPlayerAvatars),\n    [MULTI_JOURNEY_START_REGIONS]',1)
    layer.stage(p,text)
    p='data/scripts/journey_birth.inc';text=(source/p).read_text()
    text=text.replace('\tlockall\n\tmsgbox JourneyBirth_Text_ChooseCity','''\tlockall
\tmsgbox JourneyBirth_Text_ChooseAvatar
\tclosemessage
\tmultichoice 0, 0, MULTI_JOURNEY_PLAYER_AVATAR, TRUE
\tspecial JourneyBirthChooseAvatar
\tmsgbox JourneyBirth_Text_ChooseCity''',1)
    text+='''
JourneyBirth_Text_ChooseAvatar::
\t.string "Choose your protagonist.\\n"
\t.string "Your home region is independent.$"
'''
    layer.stage(p,text)
    for p in ['src/trainer.c','src/region_map.c']:
        text=(source/p).read_text().replace('#include "global.h"','#include "global.h"\n#include "journey_birth.h"',1)
        text=text.replace('gSaveBlock2Ptr->playerRegion == REGION_KANTO','JourneyAvatarIsKanto()')
        layer.stage(p,text)
    p='src/field_player_avatar.c';text=(source/p).read_text().replace('#include "global.h"','#include "global.h"\n#include "journey_birth.h"',1)
    # Preserve the native rival region decision, while replacing all player
    # walking, cycling, surfing and diving appearance decisions.
    start=text.index('u16 GetPlayerAvatarGraphicsIdByStateIdAndGender(')
    text=text[:start]+text[start:].replace('gSaveBlock2Ptr->playerRegion == REGION_KANTO','JourneyAvatarIsKanto()')
    layer.stage(p,text)
    p='src/trainer_card.c';text=(source/p).read_text().replace('#include "global.h"','#include "global.h"\n#include "journey_birth.h"',1)
    start=text.index('static u8 GetPlayerTrainerCardFacilityClass(void)\n{')
    text=text[:start]+text[start:].replace('gSaveBlock2Ptr->playerRegion == REGION_KANTO','JourneyAvatarIsKanto()')
    text=text.replace('"KANTO  L/R: HOENN"','"KANTO 8/16  L/R: HOENN"').replace('"HOENN  L/R: KANTO"','"HOENN 8/16  L/R: KANTO"')
    layer.stage(p,text)
    return layer.finish(protagonists=['Red','Leaf','Brendan','May'],appearance_independent_of_birth_region=True,
                        saved_variable='VAR_EVER_GRANDE_CITY_STATE',badge_banks=2,badges_per_bank=8,total_badges=16)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    print(prepare(p.parse_args().source)['layer'])
