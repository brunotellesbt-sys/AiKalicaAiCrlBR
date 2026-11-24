static void GivePWTZAMegaStone(void)
{
    // Keep a Mega Stone already selected by the competitive build.
    for (u32 slot = 0; slot < PARTY_SIZE; slot++)
    {
        struct Pokemon *mon = &gEnemyParty[slot];
        u16 item = GetMonData(mon, MON_DATA_HELD_ITEM);
        if (GetItemHoldEffect(item) != HOLD_EFFECT_MEGA_STONE)
            continue;
        u16 species = GetMonData(mon, MON_DATA_SPECIES);
        enum Species target = GetFormChangeTargetSpecies_Internal((struct FormChangeContext){
            .currentSpecies = species,
            .method = FORM_CHANGE_BATTLE_MEGA_EVOLUTION_ITEM,
            .heldItem = item,
        });
        if (target != species && JourneySpeciesAllowed(target))
            return;
    }

    // Prefer the ace end of the roster and give at most one stone per team.
    for (u32 remaining = PARTY_SIZE; remaining > 0; remaining--)
    {
        struct Pokemon *mon = &gEnemyParty[remaining - 1];
        u16 species = GetMonData(mon, MON_DATA_SPECIES);
        if (!JourneySpeciesAllowed(species))
            continue;
        const struct FormChange *form = GetSpeciesFormChanges(species);
        for (; form != NULL && form->method != FORM_CHANGE_TERMINATOR; form++)
        {
            u16 item = form->param1;
            if (form->method != FORM_CHANGE_BATTLE_MEGA_EVOLUTION_ITEM
             || item < ITEM_CLEFABLITE || item > ITEM_GLIMMORANITE
             || GetItemHoldEffect(item) != HOLD_EFFECT_MEGA_STONE
             || !JourneySpeciesAllowed(form->targetSpecies))
                continue;
            SetMonData(mon, MON_DATA_HELD_ITEM, &item);
            return;
        }
    }
}
