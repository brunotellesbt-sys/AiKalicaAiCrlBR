"""Give story encounter tools early without completing their original quests."""
import argparse
import hashlib
import json
from pathlib import Path
from prepare_crossing import PIN
from prepare_english_text import PRIOR

LAYER = 'early-story-tools'
PRECEDING = PRIOR + ['english-text', 'special-ball', 'route131-sea-access', 'lostelle-habitats', 'tower-habitats']
FAMILY = 'data/scripts/journey_family.inc'
ROCKET = 'data/maps/RocketHideout_B4F_Frlg/scripts.inc'
PAIL = 'data/maps/Route104_PrettyPetalFlowerShop/scripts.inc'
STEVEN = 'data/maps/Route120/scripts.inc'

C_GIFT = '''// Ownership, including PC storage, is independent of the original quest flags.
void JourneyFamilyGiveStoryTool(void)
{
    static const u16 items[] = {ITEM_SILPH_SCOPE, ITEM_DEVON_SCOPE, ITEM_WAILMER_PAIL};
    u32 i;
    gSpecialVar_Result = 0;
    if (JourneyFamilySelectedHome() == NULL || gSpecialVar_LastTalked != 1)
        return;
    for (i = 0; i < ARRAY_COUNT(items); i++)
    {
        if (CheckBagHasItem(items[i], 1) || CheckPCHasItem(items[i], 1))
            continue;
        if (!AddBagItem(items[i], 1)) { gSpecialVar_Result = 2; return; }
        CopyItemName(items[i], gStringVar1);
        gSpecialVar_Result = 1;
        return;
    }
}

'''

TOOLS_SCRIPT = '''
JourneyEarlyStoryTools_Give::
	special JourneyFamilyGiveStoryTool
	goto_if_eq VAR_RESULT, 0, JourneyEarlyStoryTools_Return
	goto_if_eq VAR_RESULT, 2, JourneyEarlyStoryTools_BagFull
	playfanfare MUS_OBTAIN_ITEM
	msgbox JourneyEarlyStoryTools_Text_Gift
	waitfanfare
	goto JourneyEarlyStoryTools_Give
JourneyEarlyStoryTools_BagFull::
	msgbox Journey_Text_BagFull
JourneyEarlyStoryTools_Return::
	return
JourneyEarlyStoryTools_HasSilphScope::
	checkitem ITEM_SILPH_SCOPE
	goto_if_eq VAR_RESULT, TRUE, JourneyEarlyStoryTools_Return
	checkpcitem ITEM_SILPH_SCOPE, 1
	return
JourneyEarlyStoryTools_HasDevonScope::
	checkitem ITEM_DEVON_SCOPE
	goto_if_eq VAR_RESULT, TRUE, JourneyEarlyStoryTools_Return
	checkpcitem ITEM_DEVON_SCOPE, 1
	return
JourneyEarlyStoryTools_HasWailmerPail::
	checkitem ITEM_WAILMER_PAIL
	goto_if_eq VAR_RESULT, TRUE, JourneyEarlyStoryTools_Return
	checkpcitem ITEM_WAILMER_PAIL, 1
	return
JourneyEarlyStoryTools_Text_Gift::
	.string "MOM: Take this on your journey.\\n"
	.string "You received the {STR_VAR_1}!\\p"
	.string "Visit its original owner, too.\\n"
	.string "Their story still awaits you!$"
JourneyEarlyStoryTools_Text_AlreadyOwned::
	.string "You already have this tool.\\n"
	.string "Keep it safe on your journey!$"
'''

def prepare(source):
    source = Path(source)
    marker = source / ('.journey-' + LAYER)
    if marker.exists():
        report = json.loads(marker.read_text())
        for path, digest in (report['prepared_sha256'] | report['preserved_native_sha256']).items():
            if hashlib.sha256((source / path).read_bytes()).hexdigest() != digest:
                raise ValueError('Modified early story tools output: ' + path)
        return report
    acquired = json.loads((source / '.source-acquired.json').read_text())
    if acquired['commit'] != PIN:
        raise ValueError('Unexpected source revision')
    expected = dict(acquired['sha256'])
    for layer in PRECEDING:
        expected.update(json.loads((source / ('.journey-' + layer)).read_text())['prepared_sha256'])
    paths = ['src/journey_family.c', 'include/journey_family.h', 'data/specials.inc', FAMILY, ROCKET, PAIL, STEVEN]
    preserved_paths = ['data/scripts/journey_campaign_gates.inc', 'data/maps/Route12_Frlg/scripts.inc',
        'data/maps/Route16_Frlg/scripts.inc', 'data/maps/PokemonTower_6F_Frlg/scripts.inc',
        'data/scripts/kecleon.inc', 'data/maps/BattleFrontier_OutsideEast/scripts.inc',
        'src/data/wild_encounters.json', 'include/journey_wild_data.h', 'include/journey_habitat_data.h',
        'src/journey_wild.c']
    original, preserved = {}, {}
    for path in paths + preserved_paths:
        digest = hashlib.sha256((source / path).read_bytes()).hexdigest()
        if digest != expected[path]:
            raise ValueError('Unreviewed early story tools input: ' + path)
        (original if path in paths else preserved)[path] = digest
    outputs = {p: (source / p).read_text() for p in paths}
    edits = []
    def replace(path, before, after):
        if outputs[path].count(before) != 1:
            raise ValueError('Ambiguous early story tools anchor: ' + path)
        outputs[path] = outputs[path].replace(before, after)
        edits.append(dict(path=path, before=before, after=after))
    replace(paths[0], 'void JourneyFamilyGiveStarter(void)', C_GIFT + 'void JourneyFamilyGiveStarter(void)')
    replace(paths[1], 'void JourneyFamilyGiveGift(void);', 'void JourneyFamilyGiveGift(void);\nvoid JourneyFamilyGiveStoryTool(void);')
    replace(paths[2], '\tdef_special JourneyFamilyGiveGift', '\tdef_special JourneyFamilyGiveGift\n\tdef_special JourneyFamilyGiveStoryTool')
    replace(FAMILY, 'Journey_AfterGift::\n', 'Journey_AfterGift::\n\tcall_if_eq VAR_0x8008, 1, JourneyEarlyStoryTools_Give\n')
    replace(FAMILY, 'JourneyBirth_FamilyMother::', TOOLS_SCRIPT + '\nJourneyBirth_FamilyMother::')
    replace(ROCKET, '\tremoveobject LOCALID_SILPH_SCOPE\n\tgiveitem ITEM_SILPH_SCOPE\n\tgoto_if_eq VAR_RESULT, FALSE, EventScript_BagIsFull\n',
        '\tcall JourneyEarlyStoryTools_HasSilphScope\n\tgoto_if_eq VAR_RESULT, TRUE, JourneyEarlyStoryTools_SilphOwned\n'
        '\tgiveitem ITEM_SILPH_SCOPE\n\tgoto_if_eq VAR_RESULT, FALSE, EventScript_BagIsFull\n'
        '\tgoto JourneyEarlyStoryTools_SilphCollected\nJourneyEarlyStoryTools_SilphOwned::\n'
        '\tmsgbox JourneyEarlyStoryTools_Text_AlreadyOwned, MSGBOX_DEFAULT\nJourneyEarlyStoryTools_SilphCollected::\n'
        '\tsetflag FLAG_HIDE_SILPH_SCOPE\n\tremoveobject LOCALID_SILPH_SCOPE\n')
    replace(PAIL, '\tgiveitem ITEM_WAILMER_PAIL\n\tgoto_if_eq VAR_RESULT, FALSE, Common_EventScript_ShowBagIsFull\n',
        '\tcall JourneyEarlyStoryTools_HasWailmerPail\n\tgoto_if_eq VAR_RESULT, TRUE, JourneyEarlyStoryTools_PailOwned\n'
        '\tgiveitem ITEM_WAILMER_PAIL\n\tgoto_if_eq VAR_RESULT, FALSE, Common_EventScript_ShowBagIsFull\n'
        '\tgoto JourneyEarlyStoryTools_PailExplained\nJourneyEarlyStoryTools_PailOwned::\n'
        '\tmsgbox JourneyEarlyStoryTools_Text_AlreadyOwned, MSGBOX_DEFAULT\nJourneyEarlyStoryTools_PailExplained::\n')
    replace(STEVEN, '\tgiveitem ITEM_DEVON_SCOPE\n\tsetflag FLAG_RECEIVED_DEVON_SCOPE\n',
        '\tcall JourneyEarlyStoryTools_HasDevonScope\n\tgoto_if_eq VAR_RESULT, TRUE, JourneyEarlyStoryTools_DevonOwned\n'
        '\tgiveitem ITEM_DEVON_SCOPE\n\tgoto JourneyEarlyStoryTools_DevonReceived\nJourneyEarlyStoryTools_DevonOwned::\n'
        '\tmsgbox JourneyEarlyStoryTools_Text_AlreadyOwned, MSGBOX_DEFAULT\nJourneyEarlyStoryTools_DevonReceived::\n'
        '\tsetflag FLAG_RECEIVED_DEVON_SCOPE\n')
    report = dict(status='early_story_tools_candidate', source_commit=PIN,
        tools=['ITEM_SILPH_SCOPE', 'ITEM_DEVON_SCOPE', 'ITEM_WAILMER_PAIL'],
        giver='selected mother in all 31 homes', required_badges=0,
        poke_flute='first badge in either region, unchanged', original_quest_flags_not_set_by_mother=True,
        original_fixed_encounters_preserved=True, bag_and_pc_ownership_checked=True,
        new_save_fields=False, full_campaign_validated=False,
        original_sha256=original, preserved_native_sha256=preserved, edits=edits,
        prepared_sha256={p: hashlib.sha256(t.encode()).hexdigest() for p, t in outputs.items()})
    for path, text in outputs.items():
        (source / path).write_text(text)
    marker.write_text(json.dumps(report, indent=2) + '\n')
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    print(json.dumps(prepare(parser.parse_args().source), indent=2))
