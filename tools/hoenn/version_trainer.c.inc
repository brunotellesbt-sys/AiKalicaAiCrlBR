// Map a later-generation opponent to a comparable eligible species, then
// respect the real level evolution requirements for every trainer class.
u16 JourneyTrainerSpecies(u16 species,u32 level)
{
    u32 pass,i;
    if(!JourneySpeciesAllowed(species))
    {
        u16 chosen=SPECIES_NONE;
        s32 best=-100000;
        const struct SpeciesInfo *original=&gSpeciesInfo[species];
        for(i=1;i<=493;i++)
        {
            const struct SpeciesInfo *p=&gSpeciesInfo[i];
            s32 score;
            if(!p->baseHP || !JourneySpeciesAllowed(i) || (p->isRestrictedLegendary || p->isSubLegendary) || p->isMythical)continue;
            score=(p->types[0]==original->types[0]?400:0)+(p->types[1]==original->types[1]?120:0);
            score-=abs((s32)p->baseAttack-original->baseAttack)+abs((s32)p->baseSpAttack-original->baseSpAttack)+abs((s32)p->baseSpeed-original->baseSpeed);
            if(score>best){best=score;chosen=i;}
        }
        species=chosen==SPECIES_NONE?SPECIES_RATTATA:chosen;
    }
    for(pass=0;pass<4;pass++)
    {
        u16 previous=GetSpeciesPreEvolution(species);
        const struct Evolution *e;
        bool32 changed=FALSE;
        if(previous==SPECIES_NONE)break;
        e=GetSpeciesEvolutions(previous);
        for(i=0;e[i].method!=EVOLUTIONS_END;i++)
            if(e[i].targetSpecies==species && (e[i].method==EVO_LEVEL || e[i].method==EVO_LEVEL_BATTLE_ONLY) && e[i].param>level)
            {species=previous;changed=TRUE;break;}
        if(!changed)break;
    }
    return species;
}
