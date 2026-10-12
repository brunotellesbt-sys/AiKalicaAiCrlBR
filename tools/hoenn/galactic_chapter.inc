JourneyGalactic_Gate::
	lock
	faceplayer
	special JourneyGalacticAvailable
	goto_if_eq VAR_RESULT, FALSE, JourneyGalactic_TooEarly
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
	applymovement 6, JourneyGalactic_ErenApproach
	waitmovement 0
	msgbox JourneyGalactic_Text_ErenHelp
	closemessage
	multi_fixed_2_vs_2 TRAINER_JOURNEY_MARS, JourneyGalactic_Text_AdminDefeat, TRAINER_JOURNEY_CHARON, JourneyGalactic_Text_AdminDefeat, PARTNER_EREN
	goto_if_ne VAR_RESULT, 1, JourneyGalactic_End
	setvar VAR_JOURNEY_GALACTIC_STATE, 1
	removeobject 2
	removeobject 5
JourneyGalactic_LuffyBattle::
	applymovement 4, JourneyGalactic_AdminLeft2
	applymovement 3, JourneyGalactic_AdminRight2
	waitmovement 0
	applymovement 7, JourneyGalactic_LuffyApproach
	waitmovement 0
	msgbox JourneyGalactic_Text_LuffyHelp
	closemessage
	multi_fixed_2_vs_2 TRAINER_JOURNEY_SATURN, JourneyGalactic_Text_AdminDefeat, TRAINER_JOURNEY_JUPITER, JourneyGalactic_Text_AdminDefeat, PARTNER_LUFFY
	goto_if_ne VAR_RESULT, 1, JourneyGalactic_End
	setvar VAR_JOURNEY_GALACTIC_STATE, 2
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
JourneyGalactic_Rewards::
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
	special JourneyGalacticAvailable
	goto_if_eq VAR_RESULT, FALSE, JourneyGalactic_LeagueBadges
	msgbox JourneyGalactic_Text_LeagueDistortion
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
