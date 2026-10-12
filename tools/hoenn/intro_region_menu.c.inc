static const u8 sJourneyOakWelcome[]=_("Hello! Welcome to the world of POKEMON!\pMy name is OAK.\nPeople call me the POKEMON PROFESSOR.\pYour journey can begin in KANTO\nor the SEVII ISLANDS.");
static void Task_JourneyIntroRegion(u8 taskId)
{
    DoScheduledBgTilemapCopiesToVram();
    if(gTasks[taskId].data[0]==0)
    {
        ShowBg(0);
        LoadPalette(gStandardMenuPalette,BG_PLTT_ID(15),PLTT_SIZE_4BPP);
        LoadUserWindowBorderGfx(0,1,BG_PLTT_ID(14));
        FillBgTilemapBufferRect(0,0,0,0,32,32,0);
        CopyBgTilemapBufferToVram(0);
        SetGpuReg(REG_OFFSET_WININ,0x3F3F);SetGpuReg(REG_OFFSET_WINOUT,0x3F3F);
        BeginNormalPaletteFade(PALETTES_ALL,0,16,0,RGB_BLACK);
        gTasks[taskId].data[0]=1;return;
    }
    if(gPaletteFade.active)return;
    if(gTasks[taskId].data[0]==1)
    {
        if(ScriptMenu_Multichoice(2,2,MULTI_JOURNEY_START_REGIONS,TRUE))gTasks[taskId].data[0]=2;
        return;
    }
    if(gSpecialVar_Result>2)return;
    gJourneyIntroRegion=gSpecialVar_Result;
    FreeAllWindowBuffers();
    gTasks[taskId].func=Task_NewGameBirchSpeech_Init;
}
