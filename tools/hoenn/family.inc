Journey_ChooseCity::
	setvar VAR_JOURNEY_FAMILY_MENU_STATE, 1
	special JourneyFamilyCanChooseCity
	goto_if_eq VAR_RESULT, FALSE, Journey_KeepPallet
	lockall
	msgbox Journey_Text_ChooseCity
	closemessage
	multichoicegrid 0, 0, MULTI_JOURNEY_START_CITIES, 2, TRUE
	special JourneyFamilyChooseHome
	goto_if_eq VAR_RESULT, 0, Journey_KeepPallet
	msgbox Journey_Text_NewHome
	closemessage
	special JourneyFamilyWarpBedroom
	waitstate
	releaseall
	end
Journey_KeepPallet::
	releaseall
	end

Journey_Bedroom_MapScripts::
	map_script MAP_SCRIPT_ON_TRANSITION, Journey_Bedroom_Transition
	.byte 0
Journey_Bedroom_Transition::
	end

Journey_Living_MapScripts::
	map_script MAP_SCRIPT_ON_TRANSITION, Journey_Living_Transition
	.byte 0
Journey_Living_Transition::
	special JourneyFamilySetupVisitors
	end

Journey_Family::
	lock
	faceplayer
	special JourneyFamilyInfo
	copyvar VAR_0x8008, VAR_RESULT
	special JourneyFamilyGiveGift
	goto_if_eq VAR_RESULT, 2, Journey_BagFull
	goto_if_eq VAR_RESULT, 0, Journey_AfterGift
	call_if_eq VAR_0x8008, 1, Journey_MotherIntro
	call_if_eq VAR_0x8008, 2, Journey_FatherIntro
	call_if_eq VAR_0x8008, 3, Journey_BrotherIntro
	call_if_eq VAR_0x8008, 4, Journey_SisterIntro
	playfanfare MUS_OBTAIN_TMHM
	msgbox Journey_Text_Gift
	waitfanfare
Journey_AfterGift::
	goto_if_eq VAR_0x8008, 1, PalletTown_PlayersHouse_1F_EventScript_MomOriginal
	msgbox Journey_Text_FamilyGoodLuck
	release
	end
Journey_BagFull::
	msgbox Journey_Text_BagFull
	release
	end
Journey_SisterIntro::
	msgbox Journey_Text_Sister
	return
Journey_MotherIntro::
	msgbox Journey_Text_Mother
	return
Journey_FatherIntro::
	msgbox Journey_Text_Father
	return
Journey_BrotherIntro::
	msgbox Journey_Text_Brother
	return

Journey_Oak::
	lockall
	faceplayer
	goto_if_set FLAG_JOURNEY_FAMILY_STARTER_RECEIVED, Journey_OakAlreadyDone
	msgbox Journey_Text_OakVisit
	closemessage
Journey_OakChoose::
	multichoice 17, 0, MULTI_JOURNEY_STARTERS, TRUE
	copyvar VAR_0x8009, VAR_RESULT
	msgbox Journey_Text_ConfirmStarter
	yesnobox 20, 8
	goto_if_eq VAR_RESULT, NO, Journey_OakChoose
	copyvar VAR_RESULT, VAR_0x8009
	special JourneyFamilyGiveStarter
	goto_if_eq VAR_RESULT, 0, Journey_OakFailure
	special SetUnlockedPokedexFlags
	playfanfare MUS_OBTAIN_ITEM
	msgbox Journey_Text_StarterReceived
	waitfanfare
	playfanfare MUS_OBTAIN_ITEM
	msgbox Journey_Text_DexReceived
	waitfanfare
	giveitem ITEM_POKE_BALL, 5
	msgbox Journey_Text_OakReturn
	closemessage
	fadescreen FADE_TO_BLACK
	special JourneyFamilyVisitorIds
	removeobject VAR_0x8004
	removeobject VAR_0x8005
	delay 16
	fadescreen FADE_FROM_BLACK
	releaseall
	end
Journey_OakAlreadyDone::
	releaseall
	end
Journey_Case::
	msgbox Journey_Text_Case, MSGBOX_SIGN
	end
Journey_NeedStarter::
	lockall
	msgbox Journey_Text_NeedStarter
	closemessage
	applymovement LOCALID_PLAYER, Journey_MoveAwayFromDoor
	waitmovement 0
	releaseall
	end
Journey_MoveAwayFromDoor::
	walk_up
	step_end

Journey_Text_ChooseCity:
	.string "Escolha a cidade onde sua\njornada vai começar.$"
Journey_Text_NewHome:
	.string "Sua casa está pronta.\nVamos ao seu quarto!$"
Journey_Text_Mother:
	.string "Sou sua mae! Para sua viagem,\ntenho um presente para você.$"
Journey_Text_Father:
	.string "Sou seu pai! Guarde este\npresente para sua jornada.$"
Journey_Text_Brother:
	.string "Sou seu irmao! Aqui está meu\npresente. Boa aventura!$"
Journey_Text_Sister:
	.string "Sou sua irma! Aqui está meu\npresente. Boa aventura!$"
Journey_Text_Gift:
	.string "Você recebeu:\n{STR_VAR_1}!$"
Journey_Text_FamilyGoodLuck:
	.string "Pode voltar para casa quando\nquiser. Estaremos aqui!$"
Journey_Text_BagFull:
	.string "Abra espaço na bolsa e volte.\nVou guardar o que falta.$"
Journey_Text_OakVisit:
	.string "OAK: Sou amigo dos seus pais.\nVim visitar sua família!\pQuero ajudar você na jornada.\nNa maleta, trouxe três POKéMON\lde KANTO para você escolher.\pEscolha seu primeiro parceiro.\nTambém vou lhe dar a POKéDEX!$"
Journey_Text_ConfirmStarter:
	.string "Este será seu primeiro\nparceiro. Confirma a escolha?$"
Journey_Text_StarterReceived:
	.string "Você recebeu seu POKéMON\ninicial de KANTO, no nível 5!$"
Journey_Text_DexReceived:
	.string "OAK entregou a POKéDEX!\nRegistre os POKéMON de KANTO.$"
Journey_Text_OakReturn:
	.string "OAK: Agora vou voltar ao meu\nlaboratório em PALLET.\pPasse lá quando quiser.\nVou acompanhar sua jornada!$"
Journey_Text_Case:
	.string "Uma maleta com três POKéMON.\nFale com o professor OAK.$"
Journey_Text_NeedStarter:
	.string "Antes de sair, fale com OAK.\nVocê precisa de um parceiro!$"

Journey_OakFailure::
	msgbox Journey_Text_OakFailure
	releaseall
	end
Journey_Text_OakFailure::
	.string "Abra espaço na sua equipe.\n"
	.string "Vou guardar seu parceiro!$"
