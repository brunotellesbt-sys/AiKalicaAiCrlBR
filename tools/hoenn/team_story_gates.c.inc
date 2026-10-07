static bool32 JourneyMissionComplete(const struct JourneyTeamMission *mission)
{
    u32 i;
    for (i = 0; i < mission->count; i++)
        if (!RegionalFlag(TRAINER_FLAGS_START + mission->trainers[i]))
            return FALSE;
    return TRUE;
}

bool32 JourneyRegionalMissionsComplete(bool32 kanto)
{
    u32 i;
    for (i = 0; i < ARRAY_COUNT(sJourneyTeamMissions); i++)
        if (sJourneyTeamMissions[i].kanto == kanto
            && !JourneyMissionComplete(&sJourneyTeamMissions[i]))
            return FALSE;
    return TRUE;
}

u32 JourneyPendingCampaignEvent(bool32 kanto)
{
    u32 i, count = JourneyGymBadgeCount(kanto);
    if (count >= 2)
    {
        if (kanto && !RegionalFlag(FLAG_HIDE_CELADON_ROCKETS))
            return 1;
        if (!kanto && !RegionalFlag(FLAG_DEFEATED_EVIL_TEAM_MT_CHIMNEY))
            return 3;
    }
    for (i = 0; i < ARRAY_COUNT(sJourneyTeamMissions); i++)
        if (sJourneyTeamMissions[i].kanto == kanto
            && count >= sJourneyTeamMissions[i].badges
            && !JourneyMissionComplete(&sJourneyTeamMissions[i]))
            return sJourneyTeamMissions[i].event;
    if (kanto)
    {
        if (count >= 6 && !RegionalFlag(FLAG_HIDE_SAFFRON_ROCKETS))
            return 2;
    }
    else
    {
        if (count >= 5 && !RegionalFlag(FLAG_GROUDON_AWAKENED_MAGMA_HIDEOUT))
            return 4;
        if (count >= 7 && !RegionalFlag(FLAG_DEFEATED_MAGMA_SPACE_CENTER))
            return 5;
        if (count >= 7 && !RegionalFlag(FLAG_HIDE_SAFFRON_ROCKETS))
            return 13;
        if (count >= 7 && !RegionalFlag(FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN))
            return 6;
    }
    return 0;
}

bool32 JourneyCanChallengeSilph(void)
{
    return JourneyGymBadgeCount(TRUE) >= 6
        && RegionalFlag(FLAG_HIDE_CELADON_ROCKETS)
        && JourneyRegionalMissionsComplete(TRUE);
}

bool32 JourneyCanStartArchieAlliance(void)
{
    return JourneyGymBadgeCount(FALSE) >= 7
        && RegionalFlag(FLAG_HIDE_SAFFRON_ROCKETS)
        && RegionalFlag(FLAG_DEFEATED_MAGMA_SPACE_CENTER)
        && JourneyRegionalMissionsComplete(FALSE);
}

void JourneySilphCoPermission(void)
{
    gSpecialVar_Result = JourneyCanChallengeSilph();
}

void JourneyArchiePermission(void)
{
    gSpecialVar_Result = JourneyCanStartArchieAlliance();
}
