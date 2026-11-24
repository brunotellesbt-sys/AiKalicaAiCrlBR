JourneyTitanStory_Seabirds::
	applymovement 8, JourneyTitanStory_RaftDrift
	waitmovement 8
	msgbox JourneyTitanStory_DriftText, MSGBOX_DEFAULT
	closemessage
	clearflag FLAG_TEMP_5
	addobject 9
	playmoncry SPECIES_ARTICUNO, CRY_MODE_NORMAL
	playse SE_M_ICY_WIND
	applymovement 8, JourneyTitanStory_RaftAnchor
	waitmovement 8
	msgbox JourneyTitanStory_ArticunoText, MSGBOX_DEFAULT
	closemessage
	removeobject 9
	addobject 10
	playmoncry SPECIES_ZAPDOS, CRY_MODE_NORMAL
	playse SE_M_THUNDERBOLT
	fadescreen FADE_TO_WHITE
	fadescreen FADE_FROM_WHITE
	applymovement 8, JourneyTitanStory_RaftEnterChannel
	waitmovement 8
	msgbox JourneyTitanStory_ZapdosText, MSGBOX_DEFAULT
	closemessage
	removeobject 10
	addobject 11
	playmoncry SPECIES_MOLTRES, CRY_MODE_NORMAL
	setobjectxyperm 4, 7, 17
	setobjectxyperm 5, 8, 17
	clearflag FLAG_TEMP_3
	addobject 4
	addobject 5
	applymovement 2, Common_Movement_FaceUp
	waitmovement 2
	special HealPlayerParty
	playfanfare MUS_HEAL
	waitfanfare
	msgbox JourneyTitanStory_MoltresText, MSGBOX_DEFAULT
	closemessage
	removeobject 11
	setflag FLAG_TEMP_5
	return

JourneyTitanStory_RaftDrift:
	walk_down
	walk_down
	step_end
JourneyTitanStory_RaftAnchor:
	walk_up
	walk_up
	step_end
JourneyTitanStory_RaftEnterChannel:
	walk_up
	walk_up
	walk_up
	step_end

JourneyTitanStory_HarborClue::
	msgbox JourneyTitanStory_HarborText, MSGBOX_DEFAULT
	return

JourneyTitanStory_WishstarTransition::
	setflag FLAG_TEMP_5
	setflag FLAG_TEMP_6
	goto_if_ne VAR_JOURNEY_SOOTOPOLIS_RESCUE, 4, JourneySanctuary_Sync
	goto_if_ge VAR_JOURNEY_GALACTIC_STATE, 7, JourneySanctuary_Sync
	goto_if_ne VAR_JOURNEY_TITAN_STORY, 0, JourneySanctuary_Sync
	clearflag FLAG_TEMP_5
	goto JourneySanctuary_Sync

JourneyTitanStory_WishstarEren::
	lockall
	faceplayer
	msgbox JourneyTitanStory_WishstarText, MSGBOX_DEFAULT
	closemessage
	clearflag FLAG_TEMP_6
	addobject 3
	playmoncry SPECIES_JIRACHI, CRY_MODE_NORMAL
	msgbox JourneyTitanStory_JirachiText, MSGBOX_DEFAULT
	closemessage
	removeobject 3
	setflag FLAG_TEMP_6
	setvar VAR_JOURNEY_TITAN_STORY, TITAN_STORY_JIRACHI
	msgbox JourneyTitanStory_TitanDirections, MSGBOX_DEFAULT
	closemessage
	removeobject 2
	setflag FLAG_TEMP_5
	goto JourneyTitanStory_Done

JourneyTitanStory_CaveTransition::
	setflag FLAG_TEMP_5
	setflag FLAG_TEMP_6
	setflag FLAG_TEMP_7
	goto_if_ge VAR_JOURNEY_GALACTIC_STATE, 7, JourneySanctuary_Sync
	goto_if_lt VAR_JOURNEY_TITAN_STORY, TITAN_STORY_JIRACHI, JourneySanctuary_Sync
	goto_if_ge VAR_JOURNEY_TITAN_STORY, TITAN_STORY_COMPLETE, JourneySanctuary_Sync
	clearflag FLAG_TEMP_5
	callnative JourneyTitanStoryExpanded
	call_if_eq VAR_RESULT, TRUE, JourneyTitanStory_ShowExtra
	call_if_eq VAR_JOURNEY_TITAN_STORY, TITAN_STORY_FOUNDER, JourneyTitanStory_ShowGroudon
	goto JourneySanctuary_Sync

JourneyTitanStory_ShowExtra::
	clearflag FLAG_TEMP_6
	return

JourneyTitanStory_ShowGroudon::
	clearflag FLAG_TEMP_7
	return

JourneyTitanStory_TitanEren::
	lock
	faceplayer
	goto_if_eq VAR_JOURNEY_TITAN_STORY, TITAN_STORY_JIRACHI, JourneyTitanStory_NeedMaria
	goto_if_eq VAR_JOURNEY_TITAN_STORY, TITAN_STORY_MARIA, JourneyTitanStory_NeedRose
	goto_if_eq VAR_JOURNEY_TITAN_STORY, TITAN_STORY_ROSE, JourneyTitanStory_NeedSina
	goto_if_eq VAR_JOURNEY_TITAN_STORY, TITAN_STORY_REINER, JourneyTitanStory_NeedZeke
	goto_if_eq VAR_JOURNEY_TITAN_STORY, TITAN_STORY_FOUNDER, JourneyTitanStory_NeedGroudon
	callnative JourneyTitanStoryExpanded
	goto_if_eq VAR_RESULT, FALSE, JourneyTitanStory_NeedFounder
	goto_if_eq VAR_JOURNEY_TITAN_STORY, TITAN_STORY_ZEKE, JourneyTitanStory_NeedFounder
	msgbox JourneyTitanStory_ReinerHint, MSGBOX_DEFAULT
	goto JourneyTitanStory_Done

JourneyTitanStory_NeedMaria::
	msgbox JourneyTitanStory_MariaHint, MSGBOX_DEFAULT
	goto JourneyTitanStory_Done
JourneyTitanStory_NeedRose::
	msgbox JourneyTitanStory_RoseHint, MSGBOX_DEFAULT
	goto JourneyTitanStory_Done
JourneyTitanStory_NeedSina::
	msgbox JourneyTitanStory_SinaHint, MSGBOX_DEFAULT
	goto JourneyTitanStory_Done
JourneyTitanStory_NeedZeke::
	msgbox JourneyTitanStory_ZekeHint, MSGBOX_DEFAULT
	goto JourneyTitanStory_Done
JourneyTitanStory_NeedFounder::
	msgbox JourneyTitanStory_FounderHint, MSGBOX_DEFAULT
	goto JourneyTitanStory_Done
JourneyTitanStory_NeedGroudon::
	msgbox JourneyTitanStory_GroudonHint, MSGBOX_DEFAULT
	goto JourneyTitanStory_Done

JourneyTitanStory_Regirock::
	lockall
	goto_if_ne VAR_JOURNEY_TITAN_STORY, TITAN_STORY_JIRACHI, JourneyTitanStory_Waiting
	playmoncry SPECIES_REGIROCK, CRY_MODE_NORMAL
	msgbox JourneyTitanStory_MariaText, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, NO, JourneyTitanStory_Done
	setvar VAR_JOURNEY_TITAN_STORY, TITAN_STORY_MARIA
	msgbox JourneyTitanStory_MariaOpen, MSGBOX_DEFAULT
	goto JourneyTitanStory_Done

JourneyTitanStory_Regice::
	lockall
	goto_if_ne VAR_JOURNEY_TITAN_STORY, TITAN_STORY_MARIA, JourneyTitanStory_Waiting
	playmoncry SPECIES_REGICE, CRY_MODE_NORMAL
	msgbox JourneyTitanStory_RoseText, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, NO, JourneyTitanStory_Done
	setvar VAR_JOURNEY_TITAN_STORY, TITAN_STORY_ROSE
	msgbox JourneyTitanStory_RoseOpen, MSGBOX_DEFAULT
	goto JourneyTitanStory_Done

JourneyTitanStory_Registeel::
	lockall
	goto_if_ne VAR_JOURNEY_TITAN_STORY, TITAN_STORY_ROSE, JourneyTitanStory_Waiting
	playmoncry SPECIES_REGISTEEL, CRY_MODE_NORMAL
	msgbox JourneyTitanStory_SinaText, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, NO, JourneyTitanStory_Done
	setvar VAR_JOURNEY_TITAN_STORY, TITAN_STORY_SINA
	msgbox JourneyTitanStory_SinaOpen, MSGBOX_DEFAULT
	goto JourneyTitanStory_Done

JourneyTitanStory_Regieleki::
	lockall
	goto_if_ne VAR_JOURNEY_TITAN_STORY, TITAN_STORY_SINA, JourneyTitanStory_Waiting
	playmoncry SPECIES_REGIELEKI, CRY_MODE_NORMAL
	msgbox JourneyTitanStory_ReinerText, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, NO, JourneyTitanStory_Done
	setvar VAR_JOURNEY_TITAN_STORY, TITAN_STORY_REINER
	msgbox JourneyTitanStory_ReinerOpen, MSGBOX_DEFAULT
	goto JourneyTitanStory_Done

JourneyTitanStory_Regidrago::
	lockall
	goto_if_ne VAR_JOURNEY_TITAN_STORY, TITAN_STORY_REINER, JourneyTitanStory_Waiting
	playmoncry SPECIES_REGIDRAGO, CRY_MODE_NORMAL
	msgbox JourneyTitanStory_ZekeText, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, NO, JourneyTitanStory_Done
	setvar VAR_JOURNEY_TITAN_STORY, TITAN_STORY_ZEKE
	msgbox JourneyTitanStory_ZekeOpen, MSGBOX_DEFAULT
	goto JourneyTitanStory_Done

JourneyTitanStory_Regigigas::
	lockall
	callnative JourneyTitanStoryExpanded
	goto_if_eq VAR_RESULT, TRUE, JourneyTitanStory_CheckZeke
	goto_if_ne VAR_JOURNEY_TITAN_STORY, TITAN_STORY_SINA, JourneyTitanStory_Waiting
	goto JourneyTitanStory_FounderOath
JourneyTitanStory_CheckZeke::
	goto_if_ne VAR_JOURNEY_TITAN_STORY, TITAN_STORY_ZEKE, JourneyTitanStory_Waiting
JourneyTitanStory_FounderOath::
	playmoncry SPECIES_REGIGIGAS, CRY_MODE_NORMAL
	msgbox JourneyTitanStory_FounderText, MSGBOX_DEFAULT
	closemessage
	setvar VAR_JOURNEY_TITAN_STORY, TITAN_STORY_FOUNDER
	call JourneyTitanStory_ShowGroudon
	addobject 8
	playmoncry SPECIES_GROUDON, CRY_MODE_NORMAL
	call JourneyTitanStory_Tremor
	msgbox JourneyTitanStory_GroudonHint, MSGBOX_DEFAULT
	goto JourneyTitanStory_Done

JourneyTitanStory_Groudon::
	lockall
	goto_if_ne VAR_JOURNEY_TITAN_STORY, TITAN_STORY_FOUNDER, JourneyTitanStory_Waiting
	playmoncry SPECIES_GROUDON, CRY_MODE_NORMAL
	call JourneyTitanStory_Tremor
	msgbox JourneyTitanStory_StopPulseText, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, NO, JourneyTitanStory_Done
	msgbox JourneyTitanStory_EndText, MSGBOX_DEFAULT
	closemessage
	setvar VAR_JOURNEY_TITAN_STORY, TITAN_STORY_COMPLETE
	setflag FLAG_TEMP_5
	setflag FLAG_TEMP_6
	setflag FLAG_TEMP_7
	removeobject 1
	removeobject 2
	removeobject 3
	removeobject 4
	removeobject 5
	removeobject 6
	removeobject 7
	removeobject 8
	goto JourneyTitanStory_Done

JourneyTitanStory_Tremor::
	setvar VAR_0x8004, 2
	setvar VAR_0x8005, 1
	setvar VAR_0x8006, 8
	setvar VAR_0x8007, 5
	special ShakeCamera
	waitstate
	return

JourneyTitanStory_CheckFinale::
	goto_if_ge VAR_JOURNEY_GALACTIC_STATE, 1, JourneyTitanStory_FinalReady
	goto_if_ne VAR_JOURNEY_SOOTOPOLIS_RESCUE, 4, JourneyTitanStory_FinalNeedsRescue
	goto_if_ne VAR_JOURNEY_TITAN_STORY, TITAN_STORY_COMPLETE, JourneyTitanStory_FinalNeedsTitan
	goto_if_unset FLAG_JOURNEY_QUALIFIER_WON, JourneyTitanStory_FinalNeedsQualifier
JourneyTitanStory_FinalReady::
	return
JourneyTitanStory_FinalNeedsRescue::
	msgbox JourneyTitanStory_FinalRescueText, MSGBOX_DEFAULT
	goto JourneyTitanStory_Done
JourneyTitanStory_FinalNeedsTitan::
	goto_if_eq VAR_JOURNEY_TITAN_STORY, 0, JourneyTitanStory_FinalNeedsWishstar
	msgbox JourneyTitanStory_FinalTitanText, MSGBOX_DEFAULT
	goto JourneyTitanStory_Done
JourneyTitanStory_FinalNeedsWishstar::
	msgbox JourneyTitanStory_HarborText, MSGBOX_DEFAULT
	goto JourneyTitanStory_Done
JourneyTitanStory_FinalNeedsQualifier::
	msgbox JourneyTitanStory_FinalQualifierText, MSGBOX_DEFAULT
	goto JourneyTitanStory_Done

JourneyTitanStory_Waiting::
	msgbox JourneyTitanStory_WaitText, MSGBOX_DEFAULT
JourneyTitanStory_Done::
	releaseall
JourneyTitanStory_Idle::
	end

JourneyTitanStory_SignalText:
	.string "Luffy has the raft in sight.\n"
	.string "Signal Lugia to cover it?$"
JourneyTitanStory_DriftText:
	.string "The current pulls the raft\n"
	.string "away. Lugia calls to the birds\l"
	.string "over the sound of the waves.$"
JourneyTitanStory_ArticunoText:
	.string "Articuno freezes the spray.\n"
	.string "The raft steadies, and Luffy\l"
	.string "pulls it back into line.$"
JourneyTitanStory_ZapdosText:
	.string "Zapdos lights the narrow\n"
	.string "channel along the sandbar.\p"
	.string "Luffy guides the raft through.$"
JourneyTitanStory_MoltresText:
	.string "Luffy brings them ashore.\n"
	.string "Moltres warms the survivors\l"
	.string "and revives your team.$"
JourneyTitanStory_HarborText:
	.string "Reports say the ground moved\n"
	.string "again near ROUTE 112.\p"
	.string "Eren is looking into it at\n"
	.string "the WISHSTAR CHAMBER, inside\l"
	.string "FIERY PATH.$"
JourneyTitanStory_WishstarText:
	.string "EREN: The sound is the same\n"
	.string "as when Groudon woke up.\p"
	.string "I used to wonder how far I\n"
	.string "could walk without a wall\l"
	.string "telling me to stop.$"
JourneyTitanStory_JirachiText:
	.string "Jirachi answers. Three lights\n"
	.string "reveal a hidden escape route\l"
	.string "in the carving.\p"
	.string "One wish reads: Let us find\n"
	.string "our families beyond the walls.$"
JourneyTitanStory_TitanDirections:
	.string "EREN: Three seals, then the\n"
	.string "giant holding them together.\p"
	.string "Meet me inside TITAN CAVE.\n"
	.string "Its entrance is off the coast\l"
	.string "of THREE ISLAND.$"
JourneyTitanStory_MariaHint:
	.string "EREN: Look northwest.\n"
	.string "Regirock watches over Maria.$"
JourneyTitanStory_RoseHint:
	.string "EREN: Rose is to the east.\n"
	.string "Listen to Regice.$"
JourneyTitanStory_SinaHint:
	.string "EREN: Registeel keeps Sina's\n"
	.string "seal in the northeast.$"
JourneyTitanStory_ReinerHint:
	.string "EREN: Something is drawing\n"
	.string "power from the seals. Look\l"
	.string "near the southwest chamber.$"
JourneyTitanStory_ZekeHint:
	.string "EREN: There is a second voice\n"
	.string "near the southern chambers.$"
JourneyTitanStory_FounderHint:
	.string "EREN: Regigigas is in the\n"
	.string "north, past the center door.$"
JourneyTitanStory_GroudonHint:
	.string "EREN: The ground sounds like\n"
	.string "a thousand feet marching.\p"
	.string "Groudon is near Regigigas.\n"
	.string "Break the echo at its source!$"
JourneyTitanStory_MariaText:
	.string "Regirock braces a fallen wall.\n"
	.string "The old exit is underneath.\p"
	.string "Help it support the wall\n"
	.string "while opening the exit?$"
JourneyTitanStory_MariaOpen:
	.string "The way opens. Someone scratched\n"
	.string "the names of missing families\l"
	.string "into the rock beyond the seal.$"
JourneyTitanStory_RoseText:
	.string "Regice shows a road held still\n"
	.string "in ice. The ice protects the\l"
	.string "writing, but blocks the road.\p"
	.string "Copy the names before asking\n"
	.string "Regice to thaw the seal?$"
JourneyTitanStory_RoseOpen:
	.string "Regice lets the seal melt.\n"
	.string "The names travel with you.$"
JourneyTitanStory_SinaText:
	.string "Registeel guards a switch.\n"
	.string "It once opened the inner gates\l"
	.string "only for the ruling families.\p"
	.string "Turn it toward the common\n"
	.string "passage?$"
JourneyTitanStory_SinaOpen:
	.string "Registeel backs away. The\n"
	.string "passage can open from either\l"
	.string "side now.$"
JourneyTitanStory_ReinerText:
	.string "Regieleki feeds a circuit. A\n"
	.string "memory of Marley flickers.\p"
	.string "REINER: They called it progress.\n"
	.string "They turned us into weapons.\p"
	.string "Cut the line to the weapon\n"
	.string "and keep the exits lit?$"
JourneyTitanStory_ReinerOpen:
	.string "Regieleki redirects the power.\n"
	.string "In the memory, Reiner takes\l"
	.string "the other end of the line.$"
JourneyTitanStory_ZekeText:
	.string "Regidrago echoes a voice.\p"
	.string "ZEKE: Eren, I can end our pain.\n"
	.string "Help me reach the Founder.\p"
	.string "A second memory shows his aim.\n"
	.string "He would end their bloodline\l"
	.string "without asking their consent.\p"
	.string "Cut the relay to the Founder?$"
JourneyTitanStory_ZekeOpen:
	.string "EREN: You offered me freedom\n"
	.string "and made the choice for us.\p"
	.string "Regidrago stops the relay.$"
JourneyTitanStory_FounderText:
	.string "Regigigas reveals the oath\n"
	.string "carved in the inner wall.\p"
	.string "KING: My descendants shall\n"
	.string "never use these walls to\l"
	.string "wage another war.\p"
	.string "The three seals answer. The\n"
	.string "Founder grants safe passage\l"
	.string "without raising an army.$"
JourneyTitanStory_StopPulseText:
	.string "Groudon answers the vibration.\n"
	.string "The seals make it stronger.\p"
	.string "Take the load off the seals\n"
	.string "so Groudon can leave?$"
JourneyTitanStory_EndText:
	.string "Regigigas steadies the walls.\n"
	.string "Groudon's last step falls\l"
	.string "silent. The exit stays open.\p"
	.string "EREN: When it shook, I could\n"
	.string "almost see a road all the way\l"
	.string "past the sea.\p"
	.string "EREN: That tear in the air.\n"
	.string "I've seen its light before.\l"
	.string "We'll follow it soon.$"
JourneyTitanStory_WaitText:
	.string "The seal holds. Eren can tell\n"
	.string "you which one answers next.$"
JourneyTitanStory_FinalRescueText:
	.string "A crew is still missing.\n"
	.string "After Rayquaza calms the sea,\l"
	.string "help Luffy at SOOTOPOLIS.$"
JourneyTitanStory_FinalTitanText:
	.string "Eren is still at TITAN CAVE.\n"
	.string "Help him stop the tremors\l"
	.string "before boarding.$"
JourneyTitanStory_FinalQualifierText:
	.string "Eren and Luffy are due at\n"
	.string "the BATTLE FRONTIER. Win the\l"
	.string "campaign tournament first.$"
