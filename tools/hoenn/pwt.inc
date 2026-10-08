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
	msgbox JourneyPWT_Text_Kanto, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, YES, JourneyPWT_Kanto
	msgbox JourneyPWT_Text_Hoenn, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, YES, JourneyPWT_Hoenn
	msgbox JourneyPWT_Text_Mixed, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, NO, JourneyPWT_Cancel
	setvar VAR_0x8006, 2
	goto JourneyPWT_Select
JourneyPWT_Kanto::
	setvar VAR_0x8006, 0
	goto JourneyPWT_Select
JourneyPWT_Hoenn::
	setvar VAR_0x8006, 1
JourneyPWT_Select::
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
	special JourneyPWTBufferBracket
	message gStringVar4
	waitmessage
	waitbuttonpress
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
	.string "O PWT tem uma sala propria aqui.\n"
	.string "Quer visitar a recepcao?$"
JourneyPWT_Text_Welcome::
	.string "Bem-vindo ao PWT!\n"
	.string "Oito participantes, um campeao!$"
JourneyPWT_Text_Rules::
	.string "Singles: escolha tres POKeMON.\n"
	.string "Todos lutarao no nivel 50.\p"
	.string "Nao repita especies ou itens.\n"
	.string "Ovos e especies banidas nao entram.\p"
	.string "Itens da bolsa nao sao permitidos.\n"
	.string "Sua equipe e curada a cada rodada.\p"
	.string "Sao tres vitorias para o titulo.\n"
	.string "O campeao recebe 3 BP!\p"
	.string "Ao sair, niveis, itens e equipe\n"
	.string "voltam ao estado da inscricao.$"
JourneyPWT_Text_Kanto::
	.string "Quer disputar o torneio dos\n"
	.string "lideres de KANTO?$"
JourneyPWT_Text_Hoenn::
	.string "Quer disputar o torneio dos\n"
	.string "lideres de HOENN?$"
JourneyPWT_Text_Mixed::
	.string "Quer o torneio misto de lideres\n"
	.string "e campeoes de KANTO e HOENN?$"
JourneyPWT_Text_Select::
	.string "Escolha os tres POKeMON\n"
	.string "na ordem de entrada.$"
JourneyPWT_Text_Round::
	.string "Rodada: {STR_VAR_1}.\n"
	.string "Adversario: {STR_VAR_2}!$"
JourneyPWT_Text_Ready::
	.string "Podemos comecar a batalha?$"
JourneyPWT_Text_Heal::
	.string "Voce avancou! Sua equipe tera\n"
	.string "HP, PP e itens restaurados.$"
JourneyPWT_Text_Won::
	.string "Parabens! Voce venceu o torneio!\n"
	.string "Recebeu 3 BP.$"
JourneyPWT_Text_Lost::
	.string "Voce foi eliminado do torneio.\n"
	.string "Volte para uma nova tentativa!$"
JourneyPWT_Text_Retire::
	.string "Voce desistiu desta inscricao.\n"
	.string "Sua equipe sera restaurada.$"
