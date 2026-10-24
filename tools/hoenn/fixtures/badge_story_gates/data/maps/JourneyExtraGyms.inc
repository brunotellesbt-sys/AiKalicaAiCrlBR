JourneyLavenderGym_MapScripts::
	.byte 0
JourneyLavenderGym_Leader::
	goto_if_set FLAG_JOURNEY_BADGE_MORTY, JourneyLavenderGym_Gift
	trainerbattle_single TRAINER_JOURNEY_GYM_MORTY, JourneyLavenderGym_Intro, JourneyLavenderGym_Defeat, JourneyLavenderGym_Award, NO_MUSIC
	goto JourneyLavenderGym_Award
JourneyLavenderGym_Award:
	lock
	faceplayer
	goto_if_set FLAG_JOURNEY_BADGE_MORTY, JourneyLavenderGym_Gift
	message JourneyLavenderGym_Badge
	waitmessage
	call Common_EventScript_PlayGymBadgeFanfare
	setflag FLAG_JOURNEY_BADGE_MORTY
	call Journey_FirstBadgeReward
JourneyLavenderGym_Gift:
	lock
	faceplayer
	goto_if_set FLAG_JOURNEY_TM_MORTY, JourneyLavenderGym_After
	giveitem ITEM_TM_SHADOW_BALL, 1
	goto_if_eq VAR_RESULT, FALSE, JourneyLavenderGym_Full
	setflag FLAG_JOURNEY_TM_MORTY
JourneyLavenderGym_After:
	msgbox JourneyLavenderGym_Thanks, MSGBOX_DEFAULT
	release
	end
JourneyLavenderGym_Full:
	msgbox JourneyLavenderGym_BagFull, MSGBOX_DEFAULT
	release
	end
JourneyLavenderGym_Guide::
	msgbox JourneyLavenderGym_Advice, MSGBOX_NPC
	end
JourneyLavenderGym_Intro:
	.string "MORTY: Welcome to my GYM!\n"
	.string "Show me your GHOST strategy!$"
JourneyLavenderGym_Defeat:
	.string "A wonderful battle!\nYour bond has earned my BADGE.$"
JourneyLavenderGym_Badge:
	.string "You earned the FOG BADGE!$"
JourneyLavenderGym_Thanks:
	.string "Your BADGE is registered.\n"
	.string "All 24 are needed for the LEAGUES!$"
JourneyLavenderGym_BagFull:
	.string "Your BAG is full. Make room\n"
	.string "and return for your TM.$"
JourneyLavenderGym_Advice:
	.string "This GYM specializes in GHOST.\n"
	.string "Its team adapts to your progress.\p"
	.string "Win its BADGE for the 24-BADGE\n"
	.string "KANTO and HOENN LEAGUE challenge!$"
JourneyLavenderGym_Student0::
	trainerbattle_single TRAINER_JOURNEY_GYM_STUDENT_0, JourneyLavenderGym_StudentIntro, JourneyLavenderGym_StudentLose
	msgbox JourneyLavenderGym_StudentAfter, MSGBOX_AUTOCLOSE
	end
JourneyLavenderGym_Student1::
	trainerbattle_single TRAINER_JOURNEY_GYM_STUDENT_1, JourneyLavenderGym_StudentIntro, JourneyLavenderGym_StudentLose
	msgbox JourneyLavenderGym_StudentAfter, MSGBOX_AUTOCLOSE
	end
JourneyLavenderGym_Student2::
	trainerbattle_single TRAINER_JOURNEY_GYM_STUDENT_2, JourneyLavenderGym_StudentIntro, JourneyLavenderGym_StudentLose
	msgbox JourneyLavenderGym_StudentAfter, MSGBOX_AUTOCLOSE
	end
JourneyLavenderGym_Student3::
	trainerbattle_single TRAINER_JOURNEY_GYM_STUDENT_3, JourneyLavenderGym_StudentIntro, JourneyLavenderGym_StudentLose
	msgbox JourneyLavenderGym_StudentAfter, MSGBOX_AUTOCLOSE
	end
JourneyLavenderGym_StudentIntro:
	.string "Can you read our battle strategy?$"
JourneyLavenderGym_StudentLose:
	.string "You found the winning approach!$"
JourneyLavenderGym_StudentAfter:
	.string "Our LEADER is waiting ahead.$"

JourneyLilycoveGym_MapScripts::
	map_script MAP_SCRIPT_ON_LOAD, JourneyLilycoveGym_Load
	.byte 0
JourneyLilycoveGym_Load:
	callnative JourneyExtraGymEdition
	end
JourneyLilycoveGym_Leader::
	goto_if_set FLAG_JOURNEY_BADGE_WHITNEY, JourneyLilycoveGym_Gift
	callnative JourneyExtraGymEdition
	goto_if_eq VAR_RESULT, TRUE, JourneyLilycoveGym_Valerie
	trainerbattle_single TRAINER_JOURNEY_GYM_WHITNEY, JourneyLilycoveGym_Intro, JourneyLilycoveGym_Defeat, JourneyLilycoveGym_Award, NO_MUSIC
	goto JourneyLilycoveGym_Award
JourneyLilycoveGym_Valerie:
	trainerbattle_single TRAINER_JOURNEY_GYM_VALERIE, JourneyLilycoveGym_ValerieIntro, JourneyLilycoveGym_Defeat, JourneyLilycoveGym_Award, NO_MUSIC
	goto JourneyLilycoveGym_Award
JourneyLilycoveGym_ValerieIntro:
	.string "VALERIE: FAIRY POKeMON turn\n"
	.string "every battle into a work of art!$"
JourneyLilycoveGym_Award:
	lock
	faceplayer
	goto_if_set FLAG_JOURNEY_BADGE_WHITNEY, JourneyLilycoveGym_Gift
	message JourneyLilycoveGym_Badge
	waitmessage
	call Common_EventScript_PlayGymBadgeFanfare
	setflag FLAG_JOURNEY_BADGE_WHITNEY
	call Journey_FirstBadgeReward
JourneyLilycoveGym_Gift:
	lock
	faceplayer
	goto_if_set FLAG_JOURNEY_TM_WHITNEY, JourneyLilycoveGym_After
	giveitem ITEM_TM_DAZZLING_GLEAM, 1
	goto_if_eq VAR_RESULT, FALSE, JourneyLilycoveGym_Full
	setflag FLAG_JOURNEY_TM_WHITNEY
JourneyLilycoveGym_After:
	msgbox JourneyLilycoveGym_Thanks, MSGBOX_DEFAULT
	release
	end
JourneyLilycoveGym_Full:
	msgbox JourneyLilycoveGym_BagFull, MSGBOX_DEFAULT
	release
	end
JourneyLilycoveGym_Guide::
	msgbox JourneyLilycoveGym_Advice, MSGBOX_NPC
	end
JourneyLilycoveGym_Intro:
	.string "WHITNEY: Welcome to my GYM!\n"
	.string "Show me your FAIRY strategy!$"
JourneyLilycoveGym_Defeat:
	.string "A wonderful battle!\nYour bond has earned my BADGE.$"
JourneyLilycoveGym_Badge:
	.string "You earned the CHARM BADGE!$"
JourneyLilycoveGym_Thanks:
	.string "Your BADGE is registered.\n"
	.string "All 24 are needed for the LEAGUES!$"
JourneyLilycoveGym_BagFull:
	.string "Your BAG is full. Make room\n"
	.string "and return for your TM.$"
JourneyLilycoveGym_Advice:
	.string "This GYM specializes in FAIRY.\n"
	.string "Its team adapts to your progress.\p"
	.string "Win its BADGE for the 24-BADGE\n"
	.string "KANTO and HOENN LEAGUE challenge!$"
JourneyLilycoveGym_Student0::
	trainerbattle_single TRAINER_JOURNEY_GYM_STUDENT_4, JourneyLilycoveGym_StudentIntro, JourneyLilycoveGym_StudentLose
	msgbox JourneyLilycoveGym_StudentAfter, MSGBOX_AUTOCLOSE
	end
JourneyLilycoveGym_Student1::
	trainerbattle_single TRAINER_JOURNEY_GYM_STUDENT_5, JourneyLilycoveGym_StudentIntro, JourneyLilycoveGym_StudentLose
	msgbox JourneyLilycoveGym_StudentAfter, MSGBOX_AUTOCLOSE
	end
JourneyLilycoveGym_Student2::
	trainerbattle_single TRAINER_JOURNEY_GYM_STUDENT_6, JourneyLilycoveGym_StudentIntro, JourneyLilycoveGym_StudentLose
	msgbox JourneyLilycoveGym_StudentAfter, MSGBOX_AUTOCLOSE
	end
JourneyLilycoveGym_Student3::
	trainerbattle_single TRAINER_JOURNEY_GYM_STUDENT_7, JourneyLilycoveGym_StudentIntro, JourneyLilycoveGym_StudentLose
	msgbox JourneyLilycoveGym_StudentAfter, MSGBOX_AUTOCLOSE
	end
JourneyLilycoveGym_StudentIntro:
	.string "Can you read our battle strategy?$"
JourneyLilycoveGym_StudentLose:
	.string "You found the winning approach!$"
JourneyLilycoveGym_StudentAfter:
	.string "Our LEADER is waiting ahead.$"

JourneyEverGrandeGym_MapScripts::
	.byte 0
JourneyEverGrandeGym_Leader::
	goto_if_set FLAG_JOURNEY_BADGE_STEVEN, JourneyEverGrandeGym_Gift
	trainerbattle_single TRAINER_JOURNEY_GYM_STEVEN, JourneyEverGrandeGym_Intro, JourneyEverGrandeGym_Defeat, JourneyEverGrandeGym_Award, NO_MUSIC
	goto JourneyEverGrandeGym_Award
JourneyEverGrandeGym_Award:
	lock
	faceplayer
	goto_if_set FLAG_JOURNEY_BADGE_STEVEN, JourneyEverGrandeGym_Gift
	message JourneyEverGrandeGym_Badge
	waitmessage
	call Common_EventScript_PlayGymBadgeFanfare
	setflag FLAG_JOURNEY_BADGE_STEVEN
	call Journey_FirstBadgeReward
JourneyEverGrandeGym_Gift:
	lock
	faceplayer
	goto_if_set FLAG_JOURNEY_TM_STEVEN, JourneyEverGrandeGym_After
	giveitem ITEM_TM_FLASH_CANNON, 1
	goto_if_eq VAR_RESULT, FALSE, JourneyEverGrandeGym_Full
	setflag FLAG_JOURNEY_TM_STEVEN
JourneyEverGrandeGym_After:
	msgbox JourneyEverGrandeGym_Thanks, MSGBOX_DEFAULT
	release
	end
JourneyEverGrandeGym_Full:
	msgbox JourneyEverGrandeGym_BagFull, MSGBOX_DEFAULT
	release
	end
JourneyEverGrandeGym_Guide::
	msgbox JourneyEverGrandeGym_Advice, MSGBOX_NPC
	end
JourneyEverGrandeGym_Intro:
	.string "STEVEN: Welcome to my GYM!\n"
	.string "Show me your STEEL strategy!$"
JourneyEverGrandeGym_Defeat:
	.string "A wonderful battle!\nYour bond has earned my BADGE.$"
JourneyEverGrandeGym_Badge:
	.string "You earned the ALLOY BADGE!$"
JourneyEverGrandeGym_Thanks:
	.string "Your BADGE is registered.\n"
	.string "All 24 are needed for the LEAGUES!$"
JourneyEverGrandeGym_BagFull:
	.string "Your BAG is full. Make room\n"
	.string "and return for your TM.$"
JourneyEverGrandeGym_Advice:
	.string "This GYM specializes in STEEL.\n"
	.string "Its team adapts to your progress.\p"
	.string "Win its BADGE for the 24-BADGE\n"
	.string "KANTO and HOENN LEAGUE challenge!$"
JourneyEverGrandeGym_Student0::
	trainerbattle_single TRAINER_JOURNEY_GYM_STUDENT_8, JourneyEverGrandeGym_StudentIntro, JourneyEverGrandeGym_StudentLose
	msgbox JourneyEverGrandeGym_StudentAfter, MSGBOX_AUTOCLOSE
	end
JourneyEverGrandeGym_Student1::
	trainerbattle_single TRAINER_JOURNEY_GYM_STUDENT_9, JourneyEverGrandeGym_StudentIntro, JourneyEverGrandeGym_StudentLose
	msgbox JourneyEverGrandeGym_StudentAfter, MSGBOX_AUTOCLOSE
	end
JourneyEverGrandeGym_Student2::
	trainerbattle_single TRAINER_JOURNEY_GYM_STUDENT_10, JourneyEverGrandeGym_StudentIntro, JourneyEverGrandeGym_StudentLose
	msgbox JourneyEverGrandeGym_StudentAfter, MSGBOX_AUTOCLOSE
	end
JourneyEverGrandeGym_Student3::
	trainerbattle_single TRAINER_JOURNEY_GYM_STUDENT_11, JourneyEverGrandeGym_StudentIntro, JourneyEverGrandeGym_StudentLose
	msgbox JourneyEverGrandeGym_StudentAfter, MSGBOX_AUTOCLOSE
	end
JourneyEverGrandeGym_StudentIntro:
	.string "Can you read our battle strategy?$"
JourneyEverGrandeGym_StudentLose:
	.string "You found the winning approach!$"
JourneyEverGrandeGym_StudentAfter:
	.string "Our LEADER is waiting ahead.$"

JourneyFallarborGym_MapScripts::
	.byte 0
JourneyFallarborGym_Leader::
	goto_if_set FLAG_JOURNEY_BADGE_BUGSY, JourneyFallarborGym_Gift
	trainerbattle_single TRAINER_JOURNEY_GYM_BUGSY, JourneyFallarborGym_Intro, JourneyFallarborGym_Defeat, JourneyFallarborGym_Award, NO_MUSIC
	goto JourneyFallarborGym_Award
JourneyFallarborGym_Award:
	lock
	faceplayer
	goto_if_set FLAG_JOURNEY_BADGE_BUGSY, JourneyFallarborGym_Gift
	message JourneyFallarborGym_Badge
	waitmessage
	call Common_EventScript_PlayGymBadgeFanfare
	setflag FLAG_JOURNEY_BADGE_BUGSY
	call Journey_FirstBadgeReward
JourneyFallarborGym_Gift:
	lock
	faceplayer
	goto_if_set FLAG_JOURNEY_TM_BUGSY, JourneyFallarborGym_After
	giveitem ITEM_TM_X_SCISSOR, 1
	goto_if_eq VAR_RESULT, FALSE, JourneyFallarborGym_Full
	setflag FLAG_JOURNEY_TM_BUGSY
JourneyFallarborGym_After:
	msgbox JourneyFallarborGym_Thanks, MSGBOX_DEFAULT
	release
	end
JourneyFallarborGym_Full:
	msgbox JourneyFallarborGym_BagFull, MSGBOX_DEFAULT
	release
	end
JourneyFallarborGym_Guide::
	msgbox JourneyFallarborGym_Advice, MSGBOX_NPC
	end
JourneyFallarborGym_Intro:
	.string "BUGSY: Welcome to my GYM!\n"
	.string "Show me your BUG strategy!$"
JourneyFallarborGym_Defeat:
	.string "A wonderful battle!\nYour bond has earned my BADGE.$"
JourneyFallarborGym_Badge:
	.string "You earned the HIVE BADGE!$"
JourneyFallarborGym_Thanks:
	.string "Your BADGE is registered.\n"
	.string "All 24 are needed for the LEAGUES!$"
JourneyFallarborGym_BagFull:
	.string "Your BAG is full. Make room\n"
	.string "and return for your TM.$"
JourneyFallarborGym_Advice:
	.string "This GYM specializes in BUG.\n"
	.string "Its team adapts to your progress.\p"
	.string "Win its BADGE for the 24-BADGE\n"
	.string "KANTO and HOENN LEAGUE challenge!$"
JourneyFallarborGym_Student0::
	trainerbattle_single TRAINER_JOURNEY_GYM_STUDENT_12, JourneyFallarborGym_StudentIntro, JourneyFallarborGym_StudentLose
	msgbox JourneyFallarborGym_StudentAfter, MSGBOX_AUTOCLOSE
	end
JourneyFallarborGym_Student1::
	trainerbattle_single TRAINER_JOURNEY_GYM_STUDENT_13, JourneyFallarborGym_StudentIntro, JourneyFallarborGym_StudentLose
	msgbox JourneyFallarborGym_StudentAfter, MSGBOX_AUTOCLOSE
	end
JourneyFallarborGym_Student2::
	trainerbattle_single TRAINER_JOURNEY_GYM_STUDENT_14, JourneyFallarborGym_StudentIntro, JourneyFallarborGym_StudentLose
	msgbox JourneyFallarborGym_StudentAfter, MSGBOX_AUTOCLOSE
	end
JourneyFallarborGym_Student3::
	trainerbattle_single TRAINER_JOURNEY_GYM_STUDENT_15, JourneyFallarborGym_StudentIntro, JourneyFallarborGym_StudentLose
	msgbox JourneyFallarborGym_StudentAfter, MSGBOX_AUTOCLOSE
	end
JourneyFallarborGym_StudentIntro:
	.string "Can you read our battle strategy?$"
JourneyFallarborGym_StudentLose:
	.string "You found the winning approach!$"
JourneyFallarborGym_StudentAfter:
	.string "Our LEADER is waiting ahead.$"

JourneySlateportGym_MapScripts::
	.byte 0
JourneySlateportGym_Leader::
	goto_if_set FLAG_JOURNEY_BADGE_CANDICE, JourneySlateportGym_Gift
	trainerbattle_single TRAINER_JOURNEY_GYM_CANDICE, JourneySlateportGym_Intro, JourneySlateportGym_Defeat, JourneySlateportGym_Award, NO_MUSIC
	goto JourneySlateportGym_Award
JourneySlateportGym_Award:
	lock
	faceplayer
	goto_if_set FLAG_JOURNEY_BADGE_CANDICE, JourneySlateportGym_Gift
	message JourneySlateportGym_Badge
	waitmessage
	call Common_EventScript_PlayGymBadgeFanfare
	setflag FLAG_JOURNEY_BADGE_CANDICE
	call Journey_FirstBadgeReward
JourneySlateportGym_Gift:
	lock
	faceplayer
	goto_if_set FLAG_JOURNEY_TM_CANDICE, JourneySlateportGym_After
	giveitem ITEM_TM_ICE_BEAM, 1
	goto_if_eq VAR_RESULT, FALSE, JourneySlateportGym_Full
	setflag FLAG_JOURNEY_TM_CANDICE
JourneySlateportGym_After:
	msgbox JourneySlateportGym_Thanks, MSGBOX_DEFAULT
	release
	end
JourneySlateportGym_Full:
	msgbox JourneySlateportGym_BagFull, MSGBOX_DEFAULT
	release
	end
JourneySlateportGym_Guide::
	msgbox JourneySlateportGym_Advice, MSGBOX_NPC
	end
JourneySlateportGym_Intro:
	.string "CANDICE: Welcome to my GYM!\n"
	.string "Show me your ICE strategy!$"
JourneySlateportGym_Defeat:
	.string "A wonderful battle!\nYour bond has earned my BADGE.$"
JourneySlateportGym_Badge:
	.string "You earned the ICICLE BADGE!$"
JourneySlateportGym_Thanks:
	.string "Your BADGE is registered.\n"
	.string "All 24 are needed for the LEAGUES!$"
JourneySlateportGym_BagFull:
	.string "Your BAG is full. Make room\n"
	.string "and return for your TM.$"
JourneySlateportGym_Advice:
	.string "This GYM specializes in ICE.\n"
	.string "Its team adapts to your progress.\p"
	.string "Win its BADGE for the 24-BADGE\n"
	.string "KANTO and HOENN LEAGUE challenge!$"
JourneySlateportGym_Student0::
	trainerbattle_single TRAINER_JOURNEY_GYM_STUDENT_16, JourneySlateportGym_StudentIntro, JourneySlateportGym_StudentLose
	msgbox JourneySlateportGym_StudentAfter, MSGBOX_AUTOCLOSE
	end
JourneySlateportGym_Student1::
	trainerbattle_single TRAINER_JOURNEY_GYM_STUDENT_17, JourneySlateportGym_StudentIntro, JourneySlateportGym_StudentLose
	msgbox JourneySlateportGym_StudentAfter, MSGBOX_AUTOCLOSE
	end
JourneySlateportGym_Student2::
	trainerbattle_single TRAINER_JOURNEY_GYM_STUDENT_18, JourneySlateportGym_StudentIntro, JourneySlateportGym_StudentLose
	msgbox JourneySlateportGym_StudentAfter, MSGBOX_AUTOCLOSE
	end
JourneySlateportGym_Student3::
	trainerbattle_single TRAINER_JOURNEY_GYM_STUDENT_19, JourneySlateportGym_StudentIntro, JourneySlateportGym_StudentLose
	msgbox JourneySlateportGym_StudentAfter, MSGBOX_AUTOCLOSE
	end
JourneySlateportGym_StudentIntro:
	.string "Can you read our battle strategy?$"
JourneySlateportGym_StudentLose:
	.string "You found the winning approach!$"
JourneySlateportGym_StudentAfter:
	.string "Our LEADER is waiting ahead.$"

JourneySixIslandGym_MapScripts::
	.byte 0
JourneySixIslandGym_Leader::
	goto_if_set FLAG_JOURNEY_BADGE_CLAIR, JourneySixIslandGym_Gift
	trainerbattle_single TRAINER_JOURNEY_GYM_CLAIR, JourneySixIslandGym_Intro, JourneySixIslandGym_Defeat, JourneySixIslandGym_Award, NO_MUSIC
	goto JourneySixIslandGym_Award
JourneySixIslandGym_Award:
	lock
	faceplayer
	goto_if_set FLAG_JOURNEY_BADGE_CLAIR, JourneySixIslandGym_Gift
	message JourneySixIslandGym_Badge
	waitmessage
	call Common_EventScript_PlayGymBadgeFanfare
	setflag FLAG_JOURNEY_BADGE_CLAIR
	call Journey_FirstBadgeReward
JourneySixIslandGym_Gift:
	lock
	faceplayer
	goto_if_set FLAG_JOURNEY_TM_CLAIR, JourneySixIslandGym_After
	giveitem ITEM_TM_DRAGON_PULSE, 1
	goto_if_eq VAR_RESULT, FALSE, JourneySixIslandGym_Full
	setflag FLAG_JOURNEY_TM_CLAIR
JourneySixIslandGym_After:
	msgbox JourneySixIslandGym_Thanks, MSGBOX_DEFAULT
	release
	end
JourneySixIslandGym_Full:
	msgbox JourneySixIslandGym_BagFull, MSGBOX_DEFAULT
	release
	end
JourneySixIslandGym_Guide::
	msgbox JourneySixIslandGym_Advice, MSGBOX_NPC
	end
JourneySixIslandGym_Intro:
	.string "CLAIR: Welcome to my GYM!\n"
	.string "Show me your DRAGON strategy!$"
JourneySixIslandGym_Defeat:
	.string "A wonderful battle!\nYour bond has earned my BADGE.$"
JourneySixIslandGym_Badge:
	.string "You earned the RISING BADGE!$"
JourneySixIslandGym_Thanks:
	.string "Your BADGE is registered.\n"
	.string "All 24 are needed for the LEAGUES!$"
JourneySixIslandGym_BagFull:
	.string "Your BAG is full. Make room\n"
	.string "and return for your TM.$"
JourneySixIslandGym_Advice:
	.string "This GYM specializes in DRAGON.\n"
	.string "Its team adapts to your progress.\p"
	.string "Win its BADGE for the 24-BADGE\n"
	.string "KANTO and HOENN LEAGUE challenge!$"
JourneySixIslandGym_Student0::
	trainerbattle_single TRAINER_JOURNEY_GYM_STUDENT_20, JourneySixIslandGym_StudentIntro, JourneySixIslandGym_StudentLose
	msgbox JourneySixIslandGym_StudentAfter, MSGBOX_AUTOCLOSE
	end
JourneySixIslandGym_Student1::
	trainerbattle_single TRAINER_JOURNEY_GYM_STUDENT_21, JourneySixIslandGym_StudentIntro, JourneySixIslandGym_StudentLose
	msgbox JourneySixIslandGym_StudentAfter, MSGBOX_AUTOCLOSE
	end
JourneySixIslandGym_Student2::
	trainerbattle_single TRAINER_JOURNEY_GYM_STUDENT_22, JourneySixIslandGym_StudentIntro, JourneySixIslandGym_StudentLose
	msgbox JourneySixIslandGym_StudentAfter, MSGBOX_AUTOCLOSE
	end
JourneySixIslandGym_Student3::
	trainerbattle_single TRAINER_JOURNEY_GYM_STUDENT_23, JourneySixIslandGym_StudentIntro, JourneySixIslandGym_StudentLose
	msgbox JourneySixIslandGym_StudentAfter, MSGBOX_AUTOCLOSE
	end
JourneySixIslandGym_StudentIntro:
	.string "Can you read our battle strategy?$"
JourneySixIslandGym_StudentLose:
	.string "You found the winning approach!$"
JourneySixIslandGym_StudentAfter:
	.string "Our LEADER is waiting ahead.$"

JourneyThreeIslandGym_MapScripts::
	.byte 0
JourneyThreeIslandGym_Leader::
	goto_if_set FLAG_JOURNEY_BADGE_KAREN, JourneyThreeIslandGym_Gift
	trainerbattle_single TRAINER_JOURNEY_GYM_KAREN, JourneyThreeIslandGym_Intro, JourneyThreeIslandGym_Defeat, JourneyThreeIslandGym_Award, NO_MUSIC
	goto JourneyThreeIslandGym_Award
JourneyThreeIslandGym_Award:
	lock
	faceplayer
	goto_if_set FLAG_JOURNEY_BADGE_KAREN, JourneyThreeIslandGym_Gift
	message JourneyThreeIslandGym_Badge
	waitmessage
	call Common_EventScript_PlayGymBadgeFanfare
	setflag FLAG_JOURNEY_BADGE_KAREN
	call Journey_FirstBadgeReward
JourneyThreeIslandGym_Gift:
	lock
	faceplayer
	goto_if_set FLAG_JOURNEY_TM_KAREN, JourneyThreeIslandGym_After
	giveitem ITEM_TM_DARK_PULSE, 1
	goto_if_eq VAR_RESULT, FALSE, JourneyThreeIslandGym_Full
	setflag FLAG_JOURNEY_TM_KAREN
JourneyThreeIslandGym_After:
	msgbox JourneyThreeIslandGym_Thanks, MSGBOX_DEFAULT
	release
	end
JourneyThreeIslandGym_Full:
	msgbox JourneyThreeIslandGym_BagFull, MSGBOX_DEFAULT
	release
	end
JourneyThreeIslandGym_Guide::
	msgbox JourneyThreeIslandGym_Advice, MSGBOX_NPC
	end
JourneyThreeIslandGym_Intro:
	.string "KAREN: Welcome to my GYM!\n"
	.string "Show me your DARK strategy!$"
JourneyThreeIslandGym_Defeat:
	.string "A wonderful battle!\nYour bond has earned my BADGE.$"
JourneyThreeIslandGym_Badge:
	.string "You earned the DUSK BADGE!$"
JourneyThreeIslandGym_Thanks:
	.string "Your BADGE is registered.\n"
	.string "All 24 are needed for the LEAGUES!$"
JourneyThreeIslandGym_BagFull:
	.string "Your BAG is full. Make room\n"
	.string "and return for your TM.$"
JourneyThreeIslandGym_Advice:
	.string "This GYM specializes in DARK.\n"
	.string "Its team adapts to your progress.\p"
	.string "Win its BADGE for the 24-BADGE\n"
	.string "KANTO and HOENN LEAGUE challenge!$"
JourneyThreeIslandGym_Student0::
	trainerbattle_single TRAINER_JOURNEY_GYM_STUDENT_24, JourneyThreeIslandGym_StudentIntro, JourneyThreeIslandGym_StudentLose
	msgbox JourneyThreeIslandGym_StudentAfter, MSGBOX_AUTOCLOSE
	end
JourneyThreeIslandGym_Student1::
	trainerbattle_single TRAINER_JOURNEY_GYM_STUDENT_25, JourneyThreeIslandGym_StudentIntro, JourneyThreeIslandGym_StudentLose
	msgbox JourneyThreeIslandGym_StudentAfter, MSGBOX_AUTOCLOSE
	end
JourneyThreeIslandGym_Student2::
	trainerbattle_single TRAINER_JOURNEY_GYM_STUDENT_26, JourneyThreeIslandGym_StudentIntro, JourneyThreeIslandGym_StudentLose
	msgbox JourneyThreeIslandGym_StudentAfter, MSGBOX_AUTOCLOSE
	end
JourneyThreeIslandGym_Student3::
	trainerbattle_single TRAINER_JOURNEY_GYM_STUDENT_27, JourneyThreeIslandGym_StudentIntro, JourneyThreeIslandGym_StudentLose
	msgbox JourneyThreeIslandGym_StudentAfter, MSGBOX_AUTOCLOSE
	end
JourneyThreeIslandGym_StudentIntro:
	.string "Can you read our battle strategy?$"
JourneyThreeIslandGym_StudentLose:
	.string "You found the winning approach!$"
JourneyThreeIslandGym_StudentAfter:
	.string "Our LEADER is waiting ahead.$"

JourneyOakBasementGym_MapScripts::
	.byte 0
JourneyOakBasementGym_Leader::
	goto_if_set FLAG_JOURNEY_BADGE_OAK, JourneyOakBasementGym_Gift
	trainerbattle_single TRAINER_JOURNEY_GYM_OAK, JourneyOakBasementGym_Intro, JourneyOakBasementGym_Defeat, JourneyOakBasementGym_Award, NO_MUSIC
	goto JourneyOakBasementGym_Award
JourneyOakBasementGym_Award:
	lock
	faceplayer
	goto_if_set FLAG_JOURNEY_BADGE_OAK, JourneyOakBasementGym_Gift
	message JourneyOakBasementGym_Badge
	waitmessage
	call Common_EventScript_PlayGymBadgeFanfare
	setflag FLAG_JOURNEY_BADGE_OAK
	call Journey_FirstBadgeReward
JourneyOakBasementGym_Gift:
	lock
	faceplayer
	goto_if_set FLAG_JOURNEY_TM_OAK, JourneyOakBasementGym_After
	giveitem ITEM_TM_RETURN, 1
	goto_if_eq VAR_RESULT, FALSE, JourneyOakBasementGym_Full
	setflag FLAG_JOURNEY_TM_OAK
JourneyOakBasementGym_After:
	msgbox JourneyOakBasementGym_Thanks, MSGBOX_DEFAULT
	release
	end
JourneyOakBasementGym_Full:
	msgbox JourneyOakBasementGym_BagFull, MSGBOX_DEFAULT
	release
	end
JourneyOakBasementGym_Guide::
	msgbox JourneyOakBasementGym_Advice, MSGBOX_NPC
	end
JourneyOakBasementGym_Intro:
	.string "OAK: Welcome to my GYM!\n"
	.string "Show me your MIXED strategy!$"
JourneyOakBasementGym_Defeat:
	.string "A wonderful battle!\nYour bond has earned my BADGE.$"
JourneyOakBasementGym_Badge:
	.string "You earned the RESEARCH BADGE!$"
JourneyOakBasementGym_Thanks:
	.string "Your BADGE is registered.\n"
	.string "All 24 are needed for the LEAGUES!$"
JourneyOakBasementGym_BagFull:
	.string "Your BAG is full. Make room\n"
	.string "and return for your TM.$"
JourneyOakBasementGym_Advice:
	.string "This GYM specializes in MIXED.\n"
	.string "Its team adapts to your progress.\p"
	.string "Win its BADGE for the 24-BADGE\n"
	.string "KANTO and HOENN LEAGUE challenge!$"
JourneyOakBasementGym_Student0::
	trainerbattle_single TRAINER_JOURNEY_GYM_STUDENT_28, JourneyOakBasementGym_StudentIntro, JourneyOakBasementGym_StudentLose
	msgbox JourneyOakBasementGym_StudentAfter, MSGBOX_AUTOCLOSE
	end
JourneyOakBasementGym_Student1::
	trainerbattle_single TRAINER_JOURNEY_GYM_STUDENT_29, JourneyOakBasementGym_StudentIntro, JourneyOakBasementGym_StudentLose
	msgbox JourneyOakBasementGym_StudentAfter, MSGBOX_AUTOCLOSE
	end
JourneyOakBasementGym_Student2::
	trainerbattle_single TRAINER_JOURNEY_GYM_STUDENT_30, JourneyOakBasementGym_StudentIntro, JourneyOakBasementGym_StudentLose
	msgbox JourneyOakBasementGym_StudentAfter, MSGBOX_AUTOCLOSE
	end
JourneyOakBasementGym_Student3::
	trainerbattle_single TRAINER_JOURNEY_GYM_STUDENT_31, JourneyOakBasementGym_StudentIntro, JourneyOakBasementGym_StudentLose
	msgbox JourneyOakBasementGym_StudentAfter, MSGBOX_AUTOCLOSE
	end
JourneyOakBasementGym_StudentIntro:
	.string "Can you read our battle strategy?$"
JourneyOakBasementGym_StudentLose:
	.string "You found the winning approach!$"
JourneyOakBasementGym_StudentAfter:
	.string "Our LEADER is waiting ahead.$"
