JourneySootopolisRescue_MapScripts::
	map_script MAP_SCRIPT_ON_TRANSITION, JourneyRescue_Transition
	.byte 0

JourneyRescue_Transition::
	setflag FLAG_TEMP_1
	setflag FLAG_TEMP_2
	setflag FLAG_TEMP_4
	call_if_eq VAR_JOURNEY_SOOTOPOLIS_RESCUE, 2, JourneyRescue_ShowRaft
	goto_if_ge VAR_JOURNEY_SOOTOPOLIS_RESCUE, 2, JourneyRescue_RemoveCastaways
	end

JourneyRescue_ShowRaft::
	clearflag FLAG_TEMP_4
	return

JourneyRescue_RemoveCastaways::
	setflag FLAG_TEMP_3
	end

JourneyRescue_HarborCaptain::
	special JourneySootopolisRescueStatus
	goto_if_eq VAR_RESULT, 1, JourneyRescue_Offer
	goto Journey_FerryPort17

JourneyRescue_Offer::
	lock
	faceplayer
	msgbox JourneyRescue_MissingBoat, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, NO, JourneyRescue_RegularFerry
	goto_if_ne VAR_JOURNEY_SOOTOPOLIS_RESCUE, 0, JourneyRescue_Depart
	setvar VAR_JOURNEY_SOOTOPOLIS_RESCUE, 1
JourneyRescue_Depart::
	closemessage
	setvar VAR_0x8004, MAP_GROUP(MAP_JOURNEY_SOOTOPOLIS_RESCUE)
	setvar VAR_0x8005, MAP_NUM(MAP_JOURNEY_SOOTOPOLIS_RESCUE)
	setvar VAR_0x8006, WARP_ID_NONE
	setvar VAR_0x8007, 1
	setvar VAR_0x8009, 7
	setvar VAR_0x800A, 19
	fadescreen FADE_TO_BLACK
	special DoSeagallopFerryScene
	waitstate
	end

JourneyRescue_RegularFerry::
	release
	goto Journey_FerryPort17

JourneyRescue_Captain::
	lock
	faceplayer
	goto_if_eq VAR_JOURNEY_SOOTOPOLIS_RESCUE, 2, JourneyRescue_EscortHome
	msgbox JourneyRescue_ReturnWithoutThem, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, NO, JourneyRescue_Done
	goto JourneyRescue_HarborReturn

JourneyRescue_Luffy::
	lock
	faceplayer
	goto_if_ge VAR_JOURNEY_GALACTIC_STATE, 7, JourneyRescue_LuffyReturned
	msgbox JourneyRescue_LuffyText, MSGBOX_DEFAULT
	goto JourneyRescue_Done
JourneyRescue_LuffyReturned::
	msgbox JourneyRescue_LuffyReunionText, MSGBOX_DEFAULT
	goto JourneyRescue_Done

JourneyRescue_Manaphy::
	lockall
	playmoncry SPECIES_MANAPHY, CRY_MODE_NORMAL
	msgbox JourneyRescue_ManaphyText, MSGBOX_DEFAULT
	goto JourneyRescue_Done

JourneyRescue_Castaway::
	lockall
	goto_if_ge VAR_JOURNEY_SOOTOPOLIS_RESCUE, 2, JourneyRescue_Done
	msgbox JourneyRescue_CastawayText, MSGBOX_DEFAULT
	setvar VAR_JOURNEY_SOOTOPOLIS_RESCUE, 2
	fadescreen FADE_TO_BLACK
	removeobject 4
	removeobject 5
	setflag FLAG_TEMP_3
	clearflag FLAG_TEMP_4
	addobject 8
	fadescreen FADE_FROM_BLACK
	goto JourneyRescue_Done

JourneyRescue_EscortHome::
	msgbox JourneyRescue_RaftText, MSGBOX_DEFAULT
	closemessage
	clearflag FLAG_TEMP_1
	addobject 6
	playmoncry SPECIES_LUGIA, CRY_MODE_NORMAL
	applymovement 6, JourneyRescue_LugiaFly
	waitmovement 6
	msgbox JourneyRescue_LugiaText, MSGBOX_DEFAULT
	closemessage
	removeobject 6
	setflag FLAG_TEMP_1
	clearflag FLAG_TEMP_2
	addobject 7
	playmoncry SPECIES_KYOGRE, CRY_MODE_NORMAL
	msgbox JourneyRescue_KyogreText, MSGBOX_DEFAULT
	closemessage
	removeobject 7
	setflag FLAG_TEMP_2
	setvar VAR_JOURNEY_SOOTOPOLIS_RESCUE, 3
JourneyRescue_HarborReturn::
	closemessage
	warp MAP_JOURNEY_SOOTOPOLIS_HARBOR, 8, 12
	waitstate
	end

JourneyRescue_HarborOnFrame::
	map_script_2 VAR_JOURNEY_SOOTOPOLIS_RESCUE, 3, JourneyRescue_Finalize
	.2byte 0

JourneyRescue_Finalize::
	lockall
	msgbox JourneyRescue_HomeText, MSGBOX_DEFAULT
	setvar VAR_JOURNEY_SOOTOPOLIS_RESCUE, 4
JourneyRescue_Done::
	releaseall
	end

JourneyRescue_LugiaFly:
	walk_down
	walk_down
	step_end

JourneyRescue_MissingBoat:
	.string "CAPTAIN: The sky cleared, but\n"
	.string "the tide rose again. A boat\l"
	.string "went out to bring people home.\p"
	.string "We lost contact. Luffy went\n"
	.string "ahead to the landing.\p"
	.string "Will you join the rescue?$"

JourneyRescue_ReturnWithoutThem:
	.string "CAPTAIN: We can take you back\n"
	.string "to port for supplies.\p"
	.string "Sail back now?$"

JourneyRescue_LuffyText:
	.string "LUFFY: I'm staying with the\n"
	.string "captain to keep the boat ready.\p"
	.string "Manaphy saw the missing boat.\n"
	.string "Follow it across the water!$"

JourneyRescue_LuffyReunionText:
	.string "LUFFY: A gap opened over the\n"
	.string "water and brought me back.\p"
	.string "I'll help the captain here.\n"
	.string "Manaphy can show you the way!$"

JourneyRescue_ManaphyText:
	.string "Manaphy calls toward the\n"
	.string "sandbar to the north.$"

JourneyRescue_CastawayText:
	.string "The boat broke up in the tide.\n"
	.string "We made it here on this raft.\p"
	.string "We'll follow you back to the\n"
	.string "captain. Stay where we can\l"
	.string "see you!$"

JourneyRescue_RaftText:
	.string "CAPTAIN: They're alongside!\n"
	.string "Luffy, take their line!$"

JourneyRescue_LugiaText:
	.string "Lugia turns the wave away\n"
	.string "as Luffy pulls the raft in.$"

JourneyRescue_KyogreText:
	.string "A pulse rises from the floor.\n"
	.string "Kyogre surges toward it.\p"
	.string "CAPTAIN: Something's down there.\n"
	.string "I'll mark the spot. First,\l"
	.string "we're taking everyone home.$"

JourneyRescue_HomeText:
	.string "CAPTAIN: Everyone is ashore.\n"
	.string "I'll let the GYM know we're safe.\p"
	.string "Keep an eye on the tide, kid.$"

JourneyRescue_IndoorGymRedirect::
	lock
	faceplayer
	goto Journey_GymGuide_Dispatch

JourneyRescue_GymGuide::
	msgbox JourneyRescue_GymText, MSGBOX_DEFAULT
	release
	end

JourneyRescue_GymText:
	.string "A rescue is under way in\n"
	.string "SOOTOPOLIS CITY.\p"
	.string "Talk to the captain inside\n"
	.string "the harbor. The GYM will open\l"
	.string "when everyone is back.$"
