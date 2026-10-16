#include "global.h"
#include "pokemon.h"
#include "item.h"
#include "event_data.h"
#include "script_menu.h"
#include "malloc.h"
#include "string_util.h"
#include "constants/items.h"
#include "constants/species.h"

static void OpenChoices(const u8 *const *labels, u32 count)
{
    struct ListMenuItem *items = AllocZeroed(count * sizeof(*items));
    for (u32 i = 0; i < count; i++)
    {
        u8 *name = AllocZeroed(StringLength(labels[i]) + 1);
        StringCopy(name, labels[i]);
        items[i].name = name;
        items[i].id = i;
    }
    ScriptMenu_MultichoiceDynamic(1, 1, count, items, FALSE, 6, 0, DYN_MULTICHOICE_CB_NONE);
}

void JourneyCompetitiveShopMenu(void)
{
    static const u8 *const labels[] = {
        COMPOUND_STRING("Battle items"), COMPOUND_STRING("Ability supplies"),
        COMPOUND_STRING("Nature mints"), COMPOUND_STRING("EV training"),
        COMPOUND_STRING("Bottle Caps"), COMPOUND_STRING("Exit")
    };
    OpenChoices(labels, ARRAY_COUNT(labels));
}

void JourneyHyperCapMenu(void)
{
    static const u8 *const labels[] = {
        COMPOUND_STRING("Bottle Cap: one stat"),
        COMPOUND_STRING("Gold Cap: all six"), COMPOUND_STRING("Cancel")
    };
    OpenChoices(labels, ARRAY_COUNT(labels));
}

static const u8 *const sStatNames[] = {
    COMPOUND_STRING("HP"), COMPOUND_STRING("Attack"),
    COMPOUND_STRING("Defense"), COMPOUND_STRING("Speed"),
    COMPOUND_STRING("Sp. Atk"), COMPOUND_STRING("Sp. Def")
};

void JourneyHyperStatMenu(void)
{
    OpenChoices(sStatNames, ARRAY_COUNT(sStatNames));
}

static bool32 CanImprove(struct Pokemon *mon, u32 stat)
{
    return GetMonData(mon, MON_DATA_HP_IV + stat) < MAX_PER_STAT_IVS
        && !GetMonData(mon, MON_DATA_HYPER_TRAINED_HP + stat);
}

// Return codes are shared by preview and commit, so cancellation cannot spend
// a cap and a full/invalid stat cannot silently consume one either.
static u32 Eligibility(void)
{
    u32 slot = gSpecialVar_0x8008;
    u32 first = gSpecialVar_0x8006 ? 0 : gSpecialVar_0x8007;
    u32 end = gSpecialVar_0x8006 ? NUM_STATS : first + 1;
    u32 item = gSpecialVar_0x8006 ? ITEM_GOLD_BOTTLE_CAP : ITEM_BOTTLE_CAP;
    bool32 improved = FALSE;
    if (slot >= PARTY_SIZE || GetMonData(&gPlayerParty[slot], MON_DATA_SPECIES) == SPECIES_NONE
        || GetMonData(&gPlayerParty[slot], MON_DATA_IS_EGG)) return 4;
    if (GetMonData(&gPlayerParty[slot], MON_DATA_LEVEL) < 50) return 2;
    if (first >= NUM_STATS || end > NUM_STATS) return 3;
    for (u32 stat = first; stat < end; stat++) improved |= CanImprove(&gPlayerParty[slot], stat);
    if (!improved) return 3;
    if (!CheckBagHasItem(item, 1)) return 5;
    return 1;
}

void JourneyHyperPreview(void)
{
    gSpecialVar_Result = Eligibility();
    if (gSpecialVar_Result != 1) return;
    GetMonData(&gPlayerParty[gSpecialVar_0x8008], MON_DATA_NICKNAME, gStringVar1);
    StringCopy(gStringVar2, gSpecialVar_0x8006 ? COMPOUND_STRING("all six stats") : sStatNames[gSpecialVar_0x8007]);
    CopyItemName(gSpecialVar_0x8006 ? ITEM_GOLD_BOTTLE_CAP : ITEM_BOTTLE_CAP, gStringVar3);
}

void JourneyHyperApply(void)
{
    gSpecialVar_Result = Eligibility();
    if (gSpecialVar_Result != 1) return;
    struct Pokemon *mon = &gPlayerParty[gSpecialVar_0x8008];
    u32 first = gSpecialVar_0x8006 ? 0 : gSpecialVar_0x8007;
    u32 end = gSpecialVar_0x8006 ? NUM_STATS : first + 1;
    bool32 trained = TRUE;
    u32 item = gSpecialVar_0x8006 ? ITEM_GOLD_BOTTLE_CAP : ITEM_BOTTLE_CAP;
    if (!RemoveBagItem(item, 1)) { gSpecialVar_Result = 5; return; }
    for (u32 stat = first; stat < end; stat++)
        if (CanImprove(mon, stat)) SetMonData(mon, MON_DATA_HYPER_TRAINED_HP + stat, &trained);
    CalculateMonStats(mon);
}
