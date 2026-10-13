JourneyPWT_Travel::
	lock
	faceplayer
	msgbox JourneyPWT_Text_Travel, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, NO, JourneyPWT_Cancel
	fadescreen FADE_TO_BLACK
	warp MAP_JOURNEY_PWT_LOBBY, 11, 14
	waitstate
	releaseall
	end
JourneyPWT_Attendant::
	lockall
	faceplayer
	msgbox JourneyPWT_Text_Welcome
	msgbox JourneyPWT_Text_Rules
	closemessage
	special JourneyPWTMenu
	waitstate
	goto_if_eq VAR_RESULT, 255, JourneyPWT_Cancel
	goto_if_eq VAR_RESULT, 127, JourneyPWT_Cancel
	copyvar VAR_0x8006, VAR_RESULT
	msgbox JourneyPWT_Text_Select
	closemessage
	special JourneyPWTChoose
	waitstate
	goto_if_eq VAR_RESULT, FALSE, JourneyPWT_RestoreCancel
	special JourneyPWTBegin
	goto_if_eq VAR_RESULT, FALSE, JourneyPWT_RestoreCancel
	fadescreen FADE_TO_BLACK
	warp MAP_JOURNEY_PWT_ARENA, 9, 6
	waitstate
	releaseall
	end
JourneyPWT_ArenaStart::
	setvar VAR_TEMP_1, 1
	lockall
	special JourneyPWTActive
	goto_if_eq VAR_RESULT, FALSE, JourneyPWT_Return
JourneyPWT_NextRound::
	closemessage
	special JourneyPWTBoard
	waitstate
	special JourneyPWTBufferRound
	msgbox JourneyPWT_Text_Round
	msgbox JourneyPWT_Text_Ready, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, NO, JourneyPWT_Retire
	closemessage
	special JourneyPWTPrepareBattle
	special BattleSetup_StartPWTBattle
	waitstate
	special JourneyPWTAdvance
	goto_if_eq VAR_RESULT, 0, JourneyPWT_Lost
	goto_if_eq VAR_RESULT, 2, JourneyPWT_Won
	msgbox JourneyPWT_Text_Heal
	goto JourneyPWT_NextRound
JourneyPWT_Won::
	special JourneyPWTFinish
	msgbox JourneyPWT_Text_Won
	goto JourneyPWT_Return
JourneyPWT_Lost::
	msgbox JourneyPWT_Text_Lost
	goto JourneyPWT_RetireFinish
JourneyPWT_Retire::
	msgbox JourneyPWT_Text_Retire
JourneyPWT_RetireFinish::
	special JourneyPWTFinish
JourneyPWT_Return::
	closemessage
	fadescreen FADE_TO_BLACK
	warp MAP_JOURNEY_PWT_LOBBY, 11, 14
	waitstate
	releaseall
	end
JourneyPWT_RestoreCancel::
	special JourneyPWTFinish
JourneyPWT_Cancel::
	releaseall
	end
JourneyPWT_Text_Travel::
	.string "The PWT has its own reception.\n"
	.string "Would you like to visit?$"
JourneyPWT_Text_Welcome::
	.string "Welcome to the PWT!\n"
	.string "Choose a generation or the World Cup.$"
JourneyPWT_Text_Rules::
	.string "Singles: six POKeMON at Level 50.\n"
	.string "No Bag items during battles.\p"
	.string "No duplicate species or held items.\n"
	.string "Eggs and banned species cannot enter.\p"
	.string "Win: 3 points. Draw: 1 point.\n"
	.string "The top two in each group qualify.\p"
	.string "Then comes the knockout bracket.\n"
	.string "Every eligible trainer takes part.\p"
	.string "Your original party is restored\n"
	.string "when you leave the tournament.$"
JourneyPWT_Text_Select::
	.string "Choose your six POKeMON\n"
	.string "in their entry order.$"
JourneyPWT_Text_Round::
	.string "{STR_VAR_1}\n"
	.string "Opponent: {STR_VAR_2}!$"
JourneyPWT_Text_Ready::
	.string "Are you ready to battle?$"
JourneyPWT_Text_Heal::
	.string "The next fixture is ready.\n"
	.string "Your party will be fully restored.$"
JourneyPWT_Text_Won::
	.string "Congratulations! You won the Cup!\n"
	.string "You received {STR_VAR_1} BP.$"
JourneyPWT_Text_Lost::
	.string "You have been eliminated.\n"
	.string "Come back for another tournament!$"
JourneyPWT_Text_Retire::
	.string "You have retired from this Cup.\n"
	.string "Your original party will be restored.$"
