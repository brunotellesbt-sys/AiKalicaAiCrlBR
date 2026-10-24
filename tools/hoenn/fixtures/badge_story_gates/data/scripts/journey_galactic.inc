JourneyGalactic_Gate::
	lock
	faceplayer
	special JourneyGalacticAvailable
	goto_if_eq VAR_RESULT, FALSE, JourneyGalactic_TooEarly
	callnative JourneyCrossoverMissing
	goto_if_eq VAR_RESULT, FALSE, JourneyGalactic_MissingRivals
	trainerbattle_single TRAINER_JOURNEY_GALACTIC_BULKHEAD_GUARD, JourneyGalactic_Text_GruntIntro, JourneyGalactic_Text_GruntDefeat, JourneyGalactic_GateDefeated
JourneyGalactic_GateDefeated::
	msgbox JourneyGalactic_Text_Entry, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, NO, JourneyGalactic_End
	fadescreen FADE_TO_BLACK
	warp MAP_JOURNEYGALACTICHALL, 15, 34
	waitstate
	releaseall
	end
JourneyGalactic_TooEarly::
	msgbox JourneyGalactic_Text_Badges
JourneyGalactic_End::
	releaseall
	end
JourneyGalactic_Text_Badges::
	.string "The sealed compartment opens\n"
	.string "only to a trainer with all\p"
	.string "16 BADGES from KANTO and HOENN.\n"
	.string "Come back after both circuits.$"
JourneyGalactic_Text_Entry::
	.string "Space is twisting beyond this\n"
	.string "door, beneath the old ship.\p"
	.string "Enter the GALACTIC prison?$"
JourneyGalacticHall_MapScripts::
	map_script MAP_SCRIPT_ON_TRANSITION, JourneyGalactic_OnTransition
	.byte 0
JourneyGalactic_OnTransition::
	callnative JourneyGalacticCellState
	goto_if_ge VAR_JOURNEY_GALACTIC_STATE, 7, JourneyGalactic_RemoveAll
	goto_if_eq VAR_JOURNEY_GALACTIC_STATE, 0, JourneyGalactic_TransitionDone
	removeobject 2
	removeobject 5
	setobjectxyperm 6, 13, 8
	goto_if_eq VAR_JOURNEY_GALACTIC_STATE, 1, JourneyGalactic_TransitionDone
	removeobject 3
	removeobject 4
	setobjectxyperm 7, 17, 8
JourneyGalactic_TransitionDone::
	end
JourneyGalactic_RemoveAll::
	removeobject 1
	removeobject 2
	removeobject 3
	removeobject 4
	removeobject 5
	removeobject 6
	removeobject 7
	removeobject 8
	removeobject 9
	removeobject 10
	end
JourneyGalactic_Cyrus::
	lockall
	faceplayer
	special JourneyGalacticAvailable
	goto_if_eq VAR_RESULT, FALSE, JourneyGalactic_TooEarly
	special JourneyGalacticGruntsCleared
	goto_if_eq VAR_RESULT, FALSE, JourneyGalactic_GruntsRemain
	goto_if_ge VAR_JOURNEY_GALACTIC_STATE, 7, JourneyGalactic_End
	goto_if_ge VAR_JOURNEY_GALACTIC_STATE, 4, JourneyGalactic_Rewards
	goto_if_eq VAR_JOURNEY_GALACTIC_STATE, 3, JourneyGalactic_Giratina
	goto_if_eq VAR_JOURNEY_GALACTIC_STATE, 2, JourneyGalactic_CyrusBattle
	goto_if_eq VAR_JOURNEY_GALACTIC_STATE, 1, JourneyGalactic_LuffyBattle
	msgbox JourneyGalactic_Text_CyrusIntro
	closemessage
	applymovement 2, JourneyGalactic_AdminLeft1
	applymovement 5, JourneyGalactic_AdminRight1
	waitmovement 0
	special JourneyGalacticBringEren
	applymovement 6, JourneyGalactic_ErenApproach
	waitmovement 0
	msgbox JourneyGalactic_Text_ErenHelp
	closemessage
	multi_fixed_2_vs_2 TRAINER_JOURNEY_MARS, JourneyGalactic_Text_AdminDefeat, TRAINER_JOURNEY_CHARON, JourneyGalactic_Text_AdminDefeat, PARTNER_EREN
	goto_if_ne VAR_RESULT, 1, JourneyGalactic_End
	setvar VAR_JOURNEY_GALACTIC_STATE, 1
	special JourneyGalacticSyncHeroes
	removeobject 2
	removeobject 5
JourneyGalactic_LuffyBattle::
	applymovement 4, JourneyGalactic_AdminLeft2
	applymovement 3, JourneyGalactic_AdminRight2
	waitmovement 0
	special JourneyGalacticBringLuffy
	applymovement 7, JourneyGalactic_LuffyApproach
	waitmovement 0
	msgbox JourneyGalactic_Text_LuffyHelp
	closemessage
	multi_fixed_2_vs_2 TRAINER_JOURNEY_SATURN, JourneyGalactic_Text_AdminDefeat, TRAINER_JOURNEY_JUPITER, JourneyGalactic_Text_AdminDefeat, PARTNER_LUFFY
	goto_if_ne VAR_RESULT, 1, JourneyGalactic_End
	setvar VAR_JOURNEY_GALACTIC_STATE, 2
	special JourneyGalacticSyncHeroes
	removeobject 3
	removeobject 4
JourneyGalactic_CyrusBattle::
	trainerbattle_single TRAINER_JOURNEY_CYRUS, JourneyGalactic_Text_CyrusBattle, JourneyGalactic_Text_CyrusDefeat, JourneyGalactic_CyrusDefeated
	end
JourneyGalactic_CyrusDefeated::
	setvar VAR_JOURNEY_GALACTIC_STATE, 3
JourneyGalactic_Giratina::
	msgbox JourneyGalactic_Text_Giratina
	closemessage
	special HealPlayerParty
	setwildbattle SPECIES_GIRATINA, 70
	dowildbattle
	specialvar VAR_RESULT, GetBattleOutcome
	goto_if_ne VAR_RESULT, B_OUTCOME_WON, JourneyGalactic_End
	setvar VAR_JOURNEY_GALACTIC_STATE, 4
	playse SE_M_THUNDERBOLT
	callnative JourneyGalacticCellState
	msgbox JourneyGalactic_Text_CellsOpen
JourneyGalactic_Rewards::
	special JourneyGalacticSyncHeroes
	goto_if_ge VAR_JOURNEY_GALACTIC_STATE, 5, JourneyGalactic_LuffyReward
	msgbox JourneyGalactic_Text_Truth
	closemessage
	giveitem ITEM_ADAMANT_CRYSTAL
	goto_if_eq VAR_RESULT, FALSE, JourneyGalactic_FullBag
	setvar VAR_JOURNEY_GALACTIC_STATE, 5
JourneyGalactic_LuffyReward::
	goto_if_ge VAR_JOURNEY_GALACTIC_STATE, 6, JourneyGalactic_CyrusReward
	msgbox JourneyGalactic_Text_LuffyReward
	closemessage
	giveitem ITEM_LUSTROUS_GLOBE
	goto_if_eq VAR_RESULT, FALSE, JourneyGalactic_FullBag
	setvar VAR_JOURNEY_GALACTIC_STATE, 6
JourneyGalactic_CyrusReward::
	msgbox JourneyGalactic_Text_CyrusReward
	closemessage
	giveitem ITEM_GRISEOUS_CORE
	goto_if_eq VAR_RESULT, FALSE, JourneyGalactic_FullBag
	msgbox JourneyGalactic_Text_Farewell
	closemessage
	playse SE_M_TELEPORT
	dofieldeffectsparkle 13, 8, 0
	waitfieldeffect FLDEFF_SPARKLE
	removeobject 6
	dofieldeffectsparkle 17, 8, 0
	waitfieldeffect FLDEFF_SPARKLE
	removeobject 7
	removeobject 8
	removeobject 9
	removeobject 10
	removeobject 1
	setvar VAR_JOURNEY_GALACTIC_STATE, 7
	msgbox JourneyGalactic_Text_Complete
	closemessage
	releaseall
	end
JourneyGalactic_GruntsRemain::
	msgbox JourneyGalactic_Text_GruntsRemain
	goto JourneyGalactic_End
JourneyGalactic_FullBag::
	msgbox JourneyGalactic_Text_FullBag
	goto JourneyGalactic_End
JourneyGalactic_Observer::
	msgbox JourneyGalactic_Text_Prison, MSGBOX_NPC
	end
JourneyGalactic_LeagueDenied::
	callnative JourneyExtraLeagueBadges
	goto_if_eq VAR_RESULT, FALSE, JourneyGalactic_LeagueBadges
	msgbox JourneyGalactic_Text_LeagueDistortion
	callnative JourneyCrossoverMissing
	call_if_eq VAR_RESULT, FALSE, JourneyGalactic_LeagueRivals
	special JourneyGalacticOtherMissions
	call_if_eq VAR_RESULT, TRUE, JourneyGalactic_LeagueOtherMissions
	releaseall
	end
JourneyGalactic_LeagueOtherMissions::
	msgbox JourneyGalactic_Text_OtherMissions
	return
JourneyGalactic_LeagueBadges::
	msgbox Journey_LeagueSixteenBadgeText
	releaseall
	end
JourneyGalactic_Text_CyrusIntro::
	.string "CYRUS: Space and time are keys.\n"
	.string "With them, I can open a door\p"
	.string "to GIRATINA's world.\n"
	.string "These outsiders prove it works.$"
JourneyGalactic_Text_ErenHelp::
	.string "EREN: You brought us here?\n"
	.string "I blamed MAGMA... I was wrong.\p"
	.string "I am calm now. We can do this.\n"
	.string "I will fight beside you!$"
JourneyGalactic_Text_LuffyHelp::
	.string "LUFFY: So AQUA did not do this!\n"
	.string "You are sending us back home.\p"
	.string "No one keeps my crew from me!\n"
	.string "Let us beat these guys together!$"
JourneyGalactic_Text_AdminDefeat::
	.string "Our experiment... defeated!$"
JourneyGalactic_Text_CyrusBattle::
	.string "CYRUS: I have come too far.\n"
	.string "I will face you myself!$"
JourneyGalactic_Text_CyrusDefeat::
	.string "CYRUS: This power... I have lost\n"
	.string "control of everything.$"
JourneyGalactic_Text_Giratina::
	.string "GIRATINA is breaking free!\n"
	.string "EREN and LUFFY protect the room\p"
	.string "and restore your team's health.\n"
	.string "Defeat it to close the rift!\p"
	.string "The distortion prevents capture.\n"
	.string "It must return to its own cave.$"
JourneyGalactic_Text_Truth::
	.string "CYRUS: I am sorry. I tried to\n"
	.string "summon GIRATINA with DIALGA\p"
	.string "and PALKIA. Those distortions\n"
	.string "pulled you from your worlds.\p"
	.string "EREN touched a Titan and awakened\n"
	.string "a power that linked to DIALGA.\p"
	.string "LUFFY's scattered path crossed\n"
	.string "a tear held open by PALKIA.\p"
	.string "EREN: I finally understand.\n"
	.string "Take DIALGA's ADAMANT CRYSTAL.\p"
	.string "It reveals its ORIGIN form.\n"
	.string "Thank you for helping us.$"
JourneyGalactic_Text_LuffyReward::
	.string "LUFFY: This LUSTROUS GLOBE\n"
	.string "reveals PALKIA's ORIGIN form.\p"
	.string "Keep it! I am going back\n"
	.string "to find my crew.$"
JourneyGalactic_Text_CyrusReward::
	.string "CYRUS: Take the GRISEOUS CORE.\n"
	.string "It reveals GIRATINA's ORIGIN\p"
	.string "form. I must repair the harm\n"
	.string "I have caused. I am sorry.$"
JourneyGalactic_Text_Farewell::
	.string "EREN: Mikasa. Armin. I am coming.\n"
	.string "Thank you, my friend. Goodbye.\p"
	.string "LUFFY: We will never forget you!\n"
	.string "Thanks for everything!\p"
	.string "DIALGA bends time for EREN.\n"
	.string "PALKIA folds space for LUFFY.\p"
	.string "Both return to their own worlds.\n"
	.string "The three POKEMON leave the ship.$"
JourneyGalactic_Text_Complete::
	.string "The distortion is gone.\n"
	.string "Both LEAGUES can now admit you.\p"
	.string "DIALGA, PALKIA and GIRATINA\n"
	.string "can be met in their own caves.$"
JourneyGalactic_Text_GruntsRemain::
	.string "Free the ship from every\n"
	.string "GALACTIC GRUNT first.\p"
	.string "Check the upper cabins, both\n"
	.string "corridors and this final hall.$"
JourneyGalactic_Text_FullBag::
	.string "Make room in your BAG.\n"
	.string "Your remaining gifts are safe.\p"
	.string "Speak to CYRUS again to finish.$"
JourneyGalactic_Text_Prison::
	.string "Space and time twist around\n"
	.string "the imprisoned POKEMON.\p"
	.string "Speak to CYRUS at the far end\n"
	.string "after defeating every GRUNT.$"
JourneyGalactic_Text_LeagueDistortion::
	.string "A space-time distortion has\n"
	.string "appeared in the ABANDONED SHIP.\p"
	.string "Go to ROUTE 108 in HOENN.\n"
	.string "DIVE into the ship's lower floor\p"
	.string "and enter ROOM 6, northeast.\n"
	.string "Stop TEAM GALACTIC before entry.$"
JourneyGalactic_Text_OtherMissions::
	.string "Your regional team missions\n"
	.string "also need to be completed.\p"
	.string "Your GYM guides can explain\n"
	.string "each remaining place and task.$"
JourneyGalactic_AdminLeft1::
	walk_right
	walk_right
	walk_up
	walk_up
	walk_up
	walk_up
	step_end
JourneyGalactic_AdminRight1::
	walk_left
	walk_left
	walk_up
	walk_up
	walk_up
	walk_up
	step_end
JourneyGalactic_AdminLeft2::
	walk_right
	walk_right
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	step_end
JourneyGalactic_AdminRight2::
	walk_left
	walk_left
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	step_end
JourneyGalactic_ErenApproach::
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_right
	walk_right
	walk_right
	step_end
JourneyGalactic_LuffyApproach::
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_left
	walk_left
	walk_left
	step_end
JourneyGalactic_GALACTIC_GRUNT_0::
	trainerbattle_single TRAINER_JOURNEY_GALACTIC_GRUNT_0, JourneyGalactic_Text_GruntIntro, JourneyGalactic_Text_GruntDefeat
	msgbox JourneyGalactic_Text_GruntAfter, MSGBOX_NPC
	end
JourneyGalactic_GALACTIC_GRUNT_1::
	trainerbattle_single TRAINER_JOURNEY_GALACTIC_GRUNT_1, JourneyGalactic_Text_GruntIntro, JourneyGalactic_Text_GruntDefeat
	msgbox JourneyGalactic_Text_GruntAfter, MSGBOX_NPC
	end
JourneyGalactic_GALACTIC_GRUNT_2::
	trainerbattle_single TRAINER_JOURNEY_GALACTIC_GRUNT_2, JourneyGalactic_Text_GruntIntro, JourneyGalactic_Text_GruntDefeat
	msgbox JourneyGalactic_Text_GruntAfter, MSGBOX_NPC
	end
JourneyGalactic_GALACTIC_GRUNT_3::
	trainerbattle_single TRAINER_JOURNEY_GALACTIC_GRUNT_3, JourneyGalactic_Text_GruntIntro, JourneyGalactic_Text_GruntDefeat
	msgbox JourneyGalactic_Text_GruntAfter, MSGBOX_NPC
	end
JourneyGalactic_GALACTIC_GRUNT_4::
	trainerbattle_single TRAINER_JOURNEY_GALACTIC_GRUNT_4, JourneyGalactic_Text_GruntIntro, JourneyGalactic_Text_GruntDefeat
	msgbox JourneyGalactic_Text_GruntAfter, MSGBOX_NPC
	end
JourneyGalactic_GALACTIC_GRUNT_5::
	trainerbattle_single TRAINER_JOURNEY_GALACTIC_GRUNT_5, JourneyGalactic_Text_GruntIntro, JourneyGalactic_Text_GruntDefeat
	msgbox JourneyGalactic_Text_GruntAfter, MSGBOX_NPC
	end
JourneyGalactic_GALACTIC_GRUNT_6::
	trainerbattle_single TRAINER_JOURNEY_GALACTIC_GRUNT_6, JourneyGalactic_Text_GruntIntro, JourneyGalactic_Text_GruntDefeat
	msgbox JourneyGalactic_Text_GruntAfter, MSGBOX_NPC
	end
JourneyGalactic_GALACTIC_GRUNT_7::
	trainerbattle_single TRAINER_JOURNEY_GALACTIC_GRUNT_7, JourneyGalactic_Text_GruntIntro, JourneyGalactic_Text_GruntDefeat
	msgbox JourneyGalactic_Text_GruntAfter, MSGBOX_NPC
	end
JourneyGalactic_GALACTIC_GRUNT_8::
	trainerbattle_single TRAINER_JOURNEY_GALACTIC_GRUNT_8, JourneyGalactic_Text_GruntIntro, JourneyGalactic_Text_GruntDefeat
	msgbox JourneyGalactic_Text_GruntAfter, MSGBOX_NPC
	end
JourneyGalactic_GALACTIC_GRUNT_9::
	trainerbattle_single TRAINER_JOURNEY_GALACTIC_GRUNT_9, JourneyGalactic_Text_GruntIntro, JourneyGalactic_Text_GruntDefeat
	msgbox JourneyGalactic_Text_GruntAfter, MSGBOX_NPC
	end
JourneyGalactic_GALACTIC_GRUNT_10::
	trainerbattle_single TRAINER_JOURNEY_GALACTIC_GRUNT_10, JourneyGalactic_Text_GruntIntro, JourneyGalactic_Text_GruntDefeat
	msgbox JourneyGalactic_Text_GruntAfter, MSGBOX_NPC
	end
JourneyGalactic_GALACTIC_GRUNT_11::
	trainerbattle_single TRAINER_JOURNEY_GALACTIC_GRUNT_11, JourneyGalactic_Text_GruntIntro, JourneyGalactic_Text_GruntDefeat
	msgbox JourneyGalactic_Text_GruntAfter, MSGBOX_NPC
	end
JourneyGalactic_GALACTIC_GRUNT_12::
	trainerbattle_single TRAINER_JOURNEY_GALACTIC_GRUNT_12, JourneyGalactic_Text_GruntIntro, JourneyGalactic_Text_GruntDefeat
	msgbox JourneyGalactic_Text_GruntAfter, MSGBOX_NPC
	end
JourneyGalactic_GALACTIC_GRUNT_13::
	trainerbattle_single TRAINER_JOURNEY_GALACTIC_GRUNT_13, JourneyGalactic_Text_GruntIntro, JourneyGalactic_Text_GruntDefeat
	msgbox JourneyGalactic_Text_GruntAfter, MSGBOX_NPC
	end
JourneyGalactic_GALACTIC_GRUNT_14::
	trainerbattle_single TRAINER_JOURNEY_GALACTIC_GRUNT_14, JourneyGalactic_Text_GruntIntro, JourneyGalactic_Text_GruntDefeat
	msgbox JourneyGalactic_Text_GruntAfter, MSGBOX_NPC
	end
JourneyGalactic_GALACTIC_GRUNT_15::
	trainerbattle_single TRAINER_JOURNEY_GALACTIC_GRUNT_15, JourneyGalactic_Text_GruntIntro, JourneyGalactic_Text_GruntDefeat
	msgbox JourneyGalactic_Text_GruntAfter, MSGBOX_NPC
	end
JourneyGalactic_GALACTIC_GRUNT_16::
	trainerbattle_single TRAINER_JOURNEY_GALACTIC_GRUNT_16, JourneyGalactic_Text_GruntIntro, JourneyGalactic_Text_GruntDefeat
	msgbox JourneyGalactic_Text_GruntAfter, MSGBOX_NPC
	end
JourneyGalactic_GALACTIC_GRUNT_17::
	trainerbattle_single TRAINER_JOURNEY_GALACTIC_GRUNT_17, JourneyGalactic_Text_GruntIntro, JourneyGalactic_Text_GruntDefeat
	msgbox JourneyGalactic_Text_GruntAfter, MSGBOX_NPC
	end
JourneyGalactic_Text_GruntIntro::
	.string "TEAM GALACTIC controls this ship!\n"
	.string "You will not stop our experiment!$"
JourneyGalactic_Text_GruntDefeat::
	.string "Our plans are coming apart!$"
JourneyGalactic_Text_GruntAfter::
	.string "CYRUS is in the hidden prison,\n"
	.string "beyond ROOM 6 in the lower floor.$"

JourneyGalactic_MissingRivals::
	msgbox JourneyGalactic_Text_MissingRivals
	goto JourneyGalactic_End
JourneyGalactic_Text_MissingRivals::
	.string "Before entering, find {STR_VAR_1}\n"
	.string "on {STR_VAR_2}.\p"
	.string "Finish all six encounters with\n"
	.string "each stranded traveler first.$"

JourneyGalactic_LeagueRivals::
	msgbox JourneyGalactic_Text_MissingRivals
	return

JourneyGalactic_Text_CellsOpen::
	.string "The containment fields shut down!\nDIALGA, PALKIA and GIRATINA are free.$"

JourneyDiglettGalactic_Scout0::
	trainerbattle_single TRAINER_JOURNEY_GRUNT_M, JourneyDiglettGalactic_Text0, JourneyDiglettGalactic_Defeat
	msgbox JourneyDiglettGalactic_After0, MSGBOX_NPC
	end
JourneyDiglettGalactic_Text0::
	.string "We are TEAM GALACTIC.\n"
	.string "We are exploring the KANTO region.\p"
	.string "This tunnel connects ROUTE 11\n"
	.string "to ROUTE 2. A useful passage.\p"
	.string "We are mapping underground routes.\n"
	.string "You can pass. Stay out of our work!$"

JourneyDiglettGalactic_Scout1::
	trainerbattle_single TRAINER_JOURNEY_GRUNT_F, JourneyDiglettGalactic_Text1, JourneyDiglettGalactic_Defeat
	msgbox JourneyDiglettGalactic_After1, MSGBOX_NPC
	end
JourneyDiglettGalactic_Text1::
	.string "The DIGLETT made this tunnel.\n"
	.string "Their burrows reach across KANTO.\p"
	.string "Our orders are to explore the area\n"
	.string "and report unusual readings.\p"
	.string "Do not disturb the POKEMON.\n"
	.string "We need this passage intact.$"

JourneyDiglettGalactic_Scout2::
	msgbox JourneyDiglettGalactic_Text2, MSGBOX_NPC
	end
JourneyDiglettGalactic_Text2::
	.string "We came to explore KANTO.\n"
	.string "The commander wants a full report.\p"
	.string "This end leads toward ROUTE 2.\n"
	.string "VERMILION is at the other end.\p"
	.string "Strange energy has been detected.\n"
	.string "That is all I am allowed to say.$"

JourneyDiglettGalactic_Defeat::
	.string "Our exploration continues...$"
JourneyDiglettGalactic_After0::
	.string "We are exploring KANTO, not\nblocking its roads. You can pass.\p"
	.string "Our report will include your\nbattle. You are worth watching.$"
JourneyDiglettGalactic_After1::
	.string "Your POKEMON know this region\nbetter than our equipment does.\p"
	.string "We will continue our survey.\nDo not disturb the DIGLETT.$"
