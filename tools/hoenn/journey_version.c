#include "global.h"
#include "pokemon.h"
#include "journey_version.h"
bool32 JourneySpeciesAllowed(u32 species)
{
    u32 dex=SpeciesToNationalPokedexNum(species);
    return dex>0 && dex<=gJourneyBuildRules.maxNational;
}
bool32 JourneyPerfectTrainerIvs(void) { return gJourneyBuildRules.perfectIvs; }
