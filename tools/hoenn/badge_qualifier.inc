@ A campaign qualifier with its own controller. Only the stadium is shared.
JourneyQualifier_Arrival::
	callnative JourneyQualifierAvailable
	goto_if_eq VAR_RESULT, FALSE, JourneyQualifier_End
	goto JourneyQualifier_Meet

JourneyQualifier_Contact::
	lockall
	faceplayer
	goto_if_set FLAG_JOURNEY_QUALIFIER_WON, JourneyQualifier_AfterVictory
	callnative JourneyQualifierAvailable
	goto_if_eq VAR_RESULT, FALSE, JourneyQualifier_TooEarly
	goto JourneyQualifier_Meet

JourneyQualifier_Meet::
	lockall
	callnative JourneyQualifierFieldNeedsGather
	goto_if_eq VAR_RESULT, FALSE, JourneyQualifier_Gathered
	fadescreen FADE_TO_BLACK
	setvar VAR_JOURNEY_QUALIFIER_STATE, 4
	warp MAP_BATTLE_FRONTIER_OUTSIDE_WEST, 26, 67
	waitstate
	end
JourneyQualifier_Gathered::
	lockall
	setvar VAR_JOURNEY_QUALIFIER_STATE, 0
	setvar VAR_TEMP_4, 1
	applymovement LOCALID_PLAYER, Common_Movement_FaceUp
	waitmovement LOCALID_PLAYER
	msgbox JourneyQualifier_Text_Meeting, MSGBOX_DEFAULT
	msgbox JourneyQualifier_Text_Rules, MSGBOX_DEFAULT
	msgbox JourneyQualifier_Text_PartyRules, MSGBOX_DEFAULT
	msgbox JourneyQualifier_Text_Start, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, NO, JourneyQualifier_Decline
	callnative JourneyQualifierBegin
	goto_if_eq VAR_RESULT, FALSE, JourneyQualifier_NoParty
	callnative JourneyQualifierBufferStandings
	message gStringVar4
	waitmessage
	waitbuttonpress
	closemessage
	fadescreen FADE_TO_BLACK
	warp MAP_JOURNEY_PWT_ARENA, 9, 6
	waitstate
	releaseall
	end

JourneyQualifier_ArenaDispatch::
	goto_if_eq VAR_JOURNEY_QUALIFIER_STATE, 1, JourneyQualifier_ArenaStart
	goto_if_eq VAR_JOURNEY_QUALIFIER_STATE, 2, JourneyQualifier_ReturnOutside
	goto JourneyPWT_ArenaStart

JourneyQualifier_ArenaStart::
	setvar VAR_TEMP_1, 1
	lockall
	callnative JourneyQualifierCheckActive
	goto_if_eq VAR_RESULT, FALSE, JourneyQualifier_Interrupted
JourneyQualifier_NextRound::
	callnative JourneyQualifierNext
	goto_if_eq VAR_RESULT, 2, JourneyQualifier_Won
	goto_if_eq VAR_RESULT, 3, JourneyQualifier_Eliminated
	callnative JourneyQualifierBufferStandings
	message gStringVar4
	waitmessage
	waitbuttonpress
	closemessage
	fadescreen FADE_TO_BLACK
	applymovement LOCALID_PLAYER, JourneyQualifier_PlayerSetupMovement
	waitmovement LOCALID_PLAYER
	callnative JourneyQualifierFieldOpponentEnter
	goto_if_eq VAR_RESULT, FALSE, JourneyQualifier_Interrupted
	fadescreen FADE_FROM_BLACK
	applymovement LOCALID_PLAYER, JourneyQualifier_PlayerEntranceMovement
	applymovement 14, JourneyQualifier_OpponentEntranceMovement
	waitmovement LOCALID_PLAYER
	waitmovement 14
	callnative JourneyQualifierFieldRound
	msgbox JourneyQualifier_Text_Round, MSGBOX_DEFAULT
JourneyQualifier_Ready::
	msgbox JourneyQualifier_Text_Ready, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, NO, JourneyQualifier_Retire
	closemessage
	callnative JourneyQualifierPrepareBattle
	goto_if_eq VAR_RESULT, FALSE, JourneyQualifier_Interrupted
	callnative BattleSetup_StartQualifierBattle
	waitstate
JourneyQualifier_AfterBattle::
	callnative JourneyQualifierFieldOpponentExit
	callnative JourneyQualifierFinishBattle
	goto_if_eq VAR_RESULT, 0, JourneyQualifier_DrawnBattle
JourneyQualifier_HealedMessage::
	msgbox JourneyQualifier_Text_Healed, MSGBOX_DEFAULT
	goto JourneyQualifier_NextRound

JourneyQualifier_DrawnBattle::
	msgbox JourneyQualifier_Text_Draw, MSGBOX_DEFAULT
	goto JourneyQualifier_NextRound

JourneyQualifier_Won::
	callnative JourneyQualifierBufferStandings
	message gStringVar4
	waitmessage
	waitbuttonpress
	callnative JourneyQualifierComplete
	goto_if_eq VAR_RESULT, FALSE, JourneyQualifier_Interrupted
	msgbox JourneyQualifier_Text_Won, MSGBOX_DEFAULT
	goto JourneyQualifier_ReturnOutside

JourneyQualifier_Eliminated::
	msgbox JourneyQualifier_Text_Eliminated, MSGBOX_DEFAULT
	goto JourneyQualifier_ReturnCenter

JourneyQualifier_Retire::
	msgbox JourneyQualifier_Text_Retired, MSGBOX_DEFAULT
	goto JourneyQualifier_ReturnCenter

JourneyQualifier_Interrupted::
	fadescreen FADE_FROM_BLACK
	msgbox JourneyQualifier_Text_Interrupted, MSGBOX_DEFAULT
JourneyQualifier_ReturnCenter::
	callnative JourneyQualifierFieldOpponentExit
	callnative JourneyQualifierAbort
	closemessage
	fadescreen FADE_TO_BLACK
	warp MAP_BATTLE_FRONTIER_POKEMON_CENTER_1F, 7, 4
	waitstate
	releaseall
	end

JourneyQualifier_ReturnOutside::
	closemessage
	fadescreen FADE_TO_BLACK
	warp MAP_BATTLE_FRONTIER_OUTSIDE_WEST, 26, 67
	waitstate
	releaseall
	end

JourneyQualifier_Celebration::
	lockall
	callnative JourneyQualifierFieldCanCelebrate
	goto_if_eq VAR_RESULT, FALSE, JourneyQualifier_Release
	setvar VAR_TEMP_4, 1
	setvar VAR_0x8004, 0
	call JourneyQualifier_Congratulate
	setvar VAR_0x8004, 1
	call JourneyQualifier_Congratulate
	setvar VAR_0x8004, 2
	call JourneyQualifier_Congratulate
	setvar VAR_0x8004, 3
	call JourneyQualifier_Congratulate
	setvar VAR_0x8004, 4
	call JourneyQualifier_Congratulate
	msgbox JourneyQualifier_Text_LeaguePermit, MSGBOX_DEFAULT
	callnative JourneyQualifierFieldFinishCelebration
	goto JourneyQualifier_Release

JourneyQualifier_Congratulate::
	callnative JourneyQualifierFieldSpeaker
	faceplayer
	goto_if_eq VAR_RESULT, 1, JourneyQualifier_CongratulateRed
	goto_if_eq VAR_RESULT, 2, JourneyQualifier_CongratulateLeaf
	goto_if_eq VAR_RESULT, 3, JourneyQualifier_CongratulateBrendan
	goto_if_eq VAR_RESULT, 4, JourneyQualifier_CongratulateMay
	goto_if_eq VAR_RESULT, 5, JourneyQualifier_CongratulateLuffy
	goto JourneyQualifier_CongratulateEren
JourneyQualifier_CongratulateRed::
	msgbox JourneyQualifier_Text_Red, MSGBOX_DEFAULT
	return
JourneyQualifier_CongratulateLeaf::
	msgbox JourneyQualifier_Text_Leaf, MSGBOX_DEFAULT
	return
JourneyQualifier_CongratulateBrendan::
	msgbox JourneyQualifier_Text_Brendan, MSGBOX_DEFAULT
	return
JourneyQualifier_CongratulateMay::
	msgbox JourneyQualifier_Text_May, MSGBOX_DEFAULT
	return
JourneyQualifier_CongratulateLuffy::
	msgbox JourneyQualifier_Text_Luffy, MSGBOX_DEFAULT
	return
JourneyQualifier_CongratulateEren::
	msgbox JourneyQualifier_Text_Eren, MSGBOX_DEFAULT
	return

JourneyQualifier_AfterVictory::
	goto_if_unset FLAG_JOURNEY_QUALIFIER_CELEBRATED, JourneyQualifier_Celebration
	callnative JourneyQualifierFieldGalacticPending
	goto_if_eq VAR_RESULT, TRUE, JourneyQualifier_GalacticHint
	msgbox JourneyQualifier_Text_AfterVictory, MSGBOX_DEFAULT
	goto JourneyQualifier_Release
JourneyQualifier_GalacticHint::
	msgbox JourneyBadgeStory_Text_TwentyTwo, MSGBOX_DEFAULT
	goto JourneyQualifier_Release
JourneyQualifier_TooEarly::
	msgbox JourneyQualifier_Text_TooEarly, MSGBOX_DEFAULT
	goto JourneyQualifier_Release
JourneyQualifier_NoParty::
	msgbox JourneyQualifier_Text_NoParty, MSGBOX_DEFAULT
	goto JourneyQualifier_Release
JourneyQualifier_Decline::
	msgbox JourneyQualifier_Text_Decline, MSGBOX_DEFAULT
JourneyQualifier_Release::
	releaseall
JourneyQualifier_End::
	end

JourneyBadgeStory_Notify::
	callnative JourneyBadgeStoryNotice
	goto_if_eq VAR_RESULT, 3, JourneyBadgeStory_NotifyBoth
	goto_if_eq VAR_RESULT, 2, JourneyBadgeStory_NotifyTwentyTwo
	goto_if_eq VAR_RESULT, 1, JourneyBadgeStory_NotifyEighteen
	return
JourneyBadgeStory_NotifyBoth::
	msgbox JourneyBadgeStory_Text_Eighteen, MSGBOX_DEFAULT
JourneyBadgeStory_NotifyTwentyTwo::
	msgbox JourneyBadgeStory_Text_TwentyTwo, MSGBOX_DEFAULT
	return
JourneyBadgeStory_NotifyEighteen::
	msgbox JourneyBadgeStory_Text_Eighteen, MSGBOX_DEFAULT
	return

JourneyQualifier_PlayerSetupMovement:
	walk_left
	walk_left
	walk_left
	walk_left
	walk_left
	walk_left
	walk_left
	step_end
JourneyQualifier_PlayerEntranceMovement:
	walk_right
	walk_right
	walk_right
	walk_right
	walk_right
	walk_right
	walk_right
	step_end
JourneyQualifier_OpponentEntranceMovement:
	walk_left
	walk_left
	walk_left
	walk_left
	step_end

JourneyQualifier_Text_Meeting::
	.string "Your three rivals, Luffy and Eren\n"
	.string "are waiting here for you!\p"
	.string "Together, the six of you will\n"
	.string "contest the FRONTIER QUALIFIER.\p"
	.string "The champion earns admission to\n"
	.string "both the KANTO and HOENN LEAGUES.$"
JourneyQualifier_Text_Rules::
	.string "Two groups of three will be drawn.\n"
	.string "Each pair meets once.\p"
	.string "The most wins wins the group.\n"
	.string "Both group winners meet in a final.\p"
	.string "Ties use POKeMON balance, then\n"
	.string "total surviving POKeMON.\p"
	.string "If still tied, the registration\n"
	.string "draw settles it fairly.\p"
	.string "A group loss does not eliminate\n"
	.string "you while qualification is possible.$"
JourneyQualifier_Text_PartyRules::
	.string "Your party is healed between\n"
	.string "matches, including HP and PP.\p"
	.string "Held items are restored. Bag\n"
	.string "items follow normal battle use.\p"
	.string "Failure to qualify or a final loss\n"
	.string "sends you to the POKeMON CENTER.\p"
	.string "Come back here to retry.\n"
	.string "There is no entry fee.$"
JourneyQualifier_Text_Start::
	.string "Ready to enter the stadium\n"
	.string "and start your qualifying run?$"
JourneyQualifier_Text_Round::
	.string "{STR_VAR_2}!\n"
	.string "Your opponent is {STR_VAR_1}!$"
JourneyQualifier_Text_Ready::
	.string "Your party is ready.\n"
	.string "Shall the match begin?$"
JourneyQualifier_Text_Healed::
	.string "HP, PP and status are restored.\n"
	.string "Your held items are ready again.\p"
	.string "The standings will show how\n"
	.string "both groups are progressing.$"
JourneyQualifier_Text_Draw::
	.string "A drawn battle! Both teams heal.\n"
	.string "This match must be replayed.$"
JourneyQualifier_Text_Won::
	.string "You are the QUALIFIER CHAMPION!\n"
	.string "Your League admission is earned.\p"
	.string "Everyone is waiting outside\n"
	.string "to celebrate with you!$"
JourneyQualifier_Text_Eliminated::
	.string "Your qualifying run ends here.\n"
	.string "Your POKeMON will be cared for.\p"
	.string "Return to the meeting outside\n"
	.string "when you are ready to retry.$"
JourneyQualifier_Text_Retired::
	.string "You have withdrawn from this run.\n"
	.string "Rest, regroup, then try again.$"
JourneyQualifier_Text_Interrupted::
	.string "This run could not be resumed.\n"
	.string "Your party will recover safely.\p"
	.string "Meet your friends outside the\n"
	.string "FRONTIER reception to start again.$"
JourneyQualifier_Text_Red::
	.string "{STR_VAR_1}: ...Well fought.\n"
	.string "You earned this.\p"
	.string "Let your team speak for itself\n"
	.string "at both LEAGUES. I will be waiting.$"
JourneyQualifier_Text_Leaf::
	.string "{STR_VAR_1}: Congratulations!\n"
	.string "You kept reading our next move.\p"
	.string "Keep that clear head when the\n"
	.string "LEAGUE puts you under pressure.$"
JourneyQualifier_Text_Brendan::
	.string "{STR_VAR_1}: What a finish!\n"
	.string "Every journey made us stronger.\p"
	.string "We have more trails to explore,\n"
	.string "but your next stop is the LEAGUE!$"
JourneyQualifier_Text_May::
	.string "{STR_VAR_1}: You did it!\n"
	.string "You trusted every POKeMON.\p"
	.string "That bond carried you through.\n"
	.string "Take it to both LEAGUES!$"
JourneyQualifier_Text_Luffy::
	.string "{STR_VAR_1}: That was awesome!\n"
	.string "You never gave up on your crew!\p"
	.string "I am chasing my own big dream.\n"
	.string "Go chase those LEAGUE titles!$"
JourneyQualifier_Text_Eren::
	.string "{STR_VAR_1}: Congratulations.\n"
	.string "You chose your path and held on.\p"
	.string "The next challenge is your choice.\n"
	.string "Keep moving forward, freely.$"
JourneyQualifier_Text_LeaguePermit::
	.string "Both LEAGUES recognize your\n"
	.string "18 BADGES and qualifying victory.\p"
	.string "You may challenge KANTO, HOENN\n"
	.string "or complete both journeys.$"
JourneyQualifier_Text_AfterVictory::
	.string "You earned your place at both\n"
	.string "LEAGUES. Keep your team ready!$"
JourneyQualifier_Text_TooEarly::
	.string "Collect 18 BADGES, then meet us\n"
	.string "outside the FRONTIER reception.$"
JourneyQualifier_Text_NoParty::
	.string "Bring at least one POKeMON\n"
	.string "that can battle, then try again.$"
JourneyQualifier_Text_Decline::
	.string "We will wait here. Talk to any\n"
	.string "of us when your party is ready.$"
JourneyBadgeStory_Text_Eighteen::
	.string "Your 18th BADGE opens a new trial!\n"
	.string "Meet your three rivals, Luffy\p"
	.string "and Eren outside the BATTLE\n"
	.string "FRONTIER island reception.\p"
	.string "Win the six-person QUALIFIER\n"
	.string "to earn admission to both LEAGUES.$"
JourneyBadgeStory_Text_TwentyTwo::
	.string "With 22 BADGES, investigate the\n"
	.string "GALACTIC disturbance at sea.\p"
	.string "Find the ABANDONED SHIP on\n"
	.string "ROUTE 108 and inspect ROOM 6.\p"
	.string "If your friends are not ready,\n"
	.string "finish your earlier meetings.$"
