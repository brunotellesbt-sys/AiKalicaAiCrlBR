@ Shared key-item reward. Badge banks and Snorlax story flags stay independent.
Journey_FirstBadgeReward::
	goto_if_set FLAG_GOT_POKE_FLUTE, Journey_FirstBadgeReward_Return
	special JourneyFirstBadgeRewardPermission
	goto_if_eq VAR_RESULT, FALSE, Journey_FirstBadgeReward_Return
	checkitem ITEM_POKE_FLUTE
	goto_if_eq VAR_RESULT, TRUE, Journey_FirstBadgeReward_Claimed
	checkitemspace ITEM_POKE_FLUTE
	goto_if_eq VAR_RESULT, FALSE, Journey_FirstBadgeReward_BagFull
	msgbox Journey_FirstBadgeReward_Text, MSGBOX_DEFAULT
	giveitem ITEM_POKE_FLUTE
	goto_if_eq VAR_RESULT, FALSE, Journey_FirstBadgeReward_BagFull
Journey_FirstBadgeReward_Claimed::
	setflag FLAG_GOT_POKE_FLUTE
Journey_FirstBadgeReward_Return::
	return

Journey_FirstBadgeReward_BagFull::
	msgbox Journey_FirstBadgeReward_BagFullText, MSGBOX_DEFAULT
	return

Journey_FirstBadgeReward_Text::
	.string "Your first badge! Take this\n"
	.string "POKé FLUTE to celebrate.\p"
	.string "Its melody wakes sleeping\n"
	.string "POKéMON, including SNORLAX!$"

Journey_FirstBadgeReward_BagFullText::
	.string "Make room for the POKé FLUTE.\n"
	.string "Then talk to a GYM LEADER!$"

Journey_FujiFirstBadgeText::
	.string "Win your first GYM badge.\n"
	.string "A LEADER will give you a flute!$"
