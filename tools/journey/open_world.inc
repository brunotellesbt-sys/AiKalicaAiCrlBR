OpenWorld_FirstBadgeReward::
	special OpenWorld_CountBadges
	goto_if_eq VAR_RESULT, 8, OpenWorld_ReadyLateRival
OpenWorld_TryFlute::
	goto_if_eq VAR_RESULT, 0, EventScript_Return
	goto_if_set FLAG_GOT_POKE_FLUTE, EventScript_Return
	lock
	faceplayer
	checkitemspace ITEM_POKE_FLUTE
	goto_if_eq VAR_RESULT, FALSE, OpenWorld_FluteBagFull
	giveitem_msg OpenWorld_Text_ReceivedFlute, ITEM_POKE_FLUTE, 1, MUS_OBTAIN_KEY_ITEM
	setflag FLAG_GOT_POKE_FLUTE
	msgbox OpenWorld_Text_FluteExplained
	return
OpenWorld_ReadyLateRival::
	goto_if_ge VAR_MAP_SCENE_ROUTE22, 3, OpenWorld_TryFlute
	setvar VAR_MAP_SCENE_ROUTE22, 3
	goto OpenWorld_TryFlute
OpenWorld_FluteBagFull::
	msgbox OpenWorld_Text_FluteBagFull
	return
OpenWorld_FujiNoFlute::
	msgbox OpenWorld_Text_FujiNoFlute
	release
	end
OpenWorld_LeagueBlocked::
	msgbox OpenWorld_Text_LeagueLocked
	release
	end
OpenWorld_LeagueTransition::
	setobjectxyperm LOCALID_LEAGUE_DOOR_GUARD, 5, 3
	special OpenWorld_CountBadges
	goto_if_eq VAR_RESULT, 8, EventScript_Return
	setobjectxyperm LOCALID_LEAGUE_DOOR_GUARD, 4, 2
	return
OpenWorld_Text_ReceivedFlute:
	.string "{PLAYER} recebeu a POKé FLUTE!$"
OpenWorld_Text_FluteExplained:
	.string "Sua primeira insígnia merece\neste presente.\pUse a POKé FLUTE para acordar\nos SNORLAX nas estradas!$"
OpenWorld_Text_FluteBagFull:
	.string "Libere espaço para a POKé FLUTE.\nDepois, fale com um líder.$"
OpenWorld_Text_FujiNoFlute:
	.string "A POKé FLUTE é um presente\npela sua primeira insígnia.$"
OpenWorld_Text_LeagueLocked:
	.string "A LIGA exige as oito insígnias.\nVença todos os ginásios primeiro!$"
