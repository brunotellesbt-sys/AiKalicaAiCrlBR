"""Reproducible Hidden Ability and classic Battle Bond overlay."""
import re
from import_catalog import matching


def catalog_raw(raw):
    # Self-target lets native TryFormChange restore the remembered species.
    start = raw.index('static const struct FormChange sGreninjaBattleBondFormChangeTable[]')
    begin = raw.index('{', start); end = matching(raw, begin)
    body, count = re.subn(r'(FORM_CHANGE_(?:FAINT|END_BATTLE),\s*)1112\b', r'\g<1>1113', raw[begin:end + 1])
    assert count == 2, 'Pinned Greninja reversion table changed'
    return raw[:begin] + body + raw[end + 1:]


def apply(source):
    def edit(file, old, new):
        p = source / file; text = p.read_text()
        if '\n' + new in text or (old not in text and new in text): return
        assert text.count(old) == 1, (file, old)
        p.write_text(text.replace(old, new, 1))

    p = source / 'include/config/battle.h'
    text, count = re.subn(r'(#define B_BATTLE_BOND\s+)\w+', r'\g<1>GEN_7', p.read_text())
    assert count == 1; p.write_text(text)
    edit('src/battle_script_commands.c', 'static bool32 HandleMoveEndAbilityBlock(', 'bool32 HandleMoveEndAbilityBlock(')
    edit('src/battle_script_commands.c',
         'GetGenConfig(GEN_CONFIG_BATTLE_BOND) < GEN_9 && gBattleMons[battlerAtk].species == SPECIES_GRENINJA_BATTLE_BOND',
         'GetGenConfig(GEN_CONFIG_BATTLE_BOND) < GEN_9 && (gBattleMons[battlerAtk].species == SPECIES_GRENINJA_BATTLE_BOND || gBattleMons[battlerAtk].species == SPECIES_GRENINJA)')
    # Pre-evolutions inherit Battle Bond but cannot transform or get Gen9 boosts.
    edit('src/battle_script_commands.c', 'else\n            {\n                u32 numStatBuffs = 0;',
         'else if (GetGenConfig(GEN_CONFIG_BATTLE_BOND) >= GEN_9)\n            {\n                u32 numStatBuffs = 0;')
    p = source / 'src/battle_util.c'; text = p.read_text()
    old = 'if (IsBattlerMegaEvolved(battler) || IsBattlerUltraBursted(battler) || IsBattlerInTeraForm(battler) || IsGigantamaxed(battler))'
    new = old.replace('if (', 'if (gBattleMons[battler].species == SPECIES_GRENINJA_ASH || ')
    if new not in text:
        assert text.count(old) == 2
        p.write_text(text.replace(old, new))
    edit('src/daycare.c', 'static void InheritAbility(', 'void InheritAbility(')
    # Native ability-number field: 0/1 normal, 2 Hidden. Gifts and scripted
    # encounters call CreateMon independently of CreateWildMon.
    edit('src/wild_encounter.c', 'void CreateWildMon(u16 species, u8 level, u8 unownSlot)',
         '''void HiddenAbilities_TryWild(struct Pokemon *mon)
{
    u16 species = GetMonData(mon, MON_DATA_SPECIES);
    if (gSpeciesInfo[species].abilities[2] != ABILITY_NONE && Random() % 100 < 5)
    {
        u8 abilityNum = 2;
        SetMonData(mon, MON_DATA_ABILITY_NUM, &abilityNum);
    }
}

void CreateWildMon(u16 species, u8 level, u8 unownSlot)''')
    p = source / 'src/wild_encounter.c'; text = p.read_text()
    start = text.index('void CreateWildMon('); begin = text.index('{', start); end = matching(text, begin)
    body = text[begin:end + 1]
    if 'HiddenAbilities_TryWild(&gEnemyParty[0]);' not in body:
        body = body.replace('        return;', '        HiddenAbilities_TryWild(&gEnemyParty[0]);\n        return;')
        body = body[:-1] + '    HiddenAbilities_TryWild(&gEnemyParty[0]);\n}'
        p.write_text(text[:begin] + body + text[end + 1:])
