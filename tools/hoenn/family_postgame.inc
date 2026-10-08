JourneyFamily_PostgameMother::
	msgbox JourneyFamily_Text_Champion
	special JourneyFamilyGiveSSTicket
	goto_if_eq VAR_RESULT, 2, JourneyFamily_PostgameBagFull
	call_if_eq VAR_RESULT, 1, JourneyFamily_PostgameTicket
	special JourneyFamilyPostgamePending
	goto_if_eq VAR_RESULT, 0, JourneyFamily_PostgameDone
	msgbox PlayersHouse_1F_Text_LatiEmergencyNewsFlash
	msgbox PlayersHouse_1F_Text_WhatColorDidTheySay
	multichoice 22, 8, MULTI_TV_LATI, TRUE
	copyvar VAR_ROAMER_POKEMON, VAR_RESULT
	setflag FLAG_LATIOS_OR_LATIAS_ROAMING
	msgbox JourneyFamily_Text_LatiSites
JourneyFamily_PostgameDone::
	releaseall
	end
JourneyFamily_PostgameTicket::
	playfanfare MUS_OBTAIN_ITEM
	msgbox JourneyFamily_Text_SSTicket
	waitfanfare
	return
JourneyFamily_PostgameBagFull::
	msgbox JourneyFamily_Text_BagFull
	releaseall
	end
JourneyFamily_Text_Champion::
	.string "MAE: Parabéns pela Liga de HOENN!\n"
	.string "Estou muito orgulhosa de você!$"
JourneyFamily_Text_SSTicket::
	.string "MAE: BRINEY mandou esta passagem.\n"
	.string "Você recebeu o S.S. TICKET!\p"
	.string "O navio sai dos portos de\n"
	.string "SLATEPORT e LILYCOVE.$"
JourneyFamily_Text_BagFull::
	.string "MAE: Guarde um item para abrir\n"
	.string "espaço e volte pela passagem.$"
JourneyFamily_Text_LatiSites::
	.string "MAE: Procure nos santuários.\n"
	.string "Eles ficam em lugares remotos!$"
