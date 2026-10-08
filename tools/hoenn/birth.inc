JourneyBirth_ChooseCity::
	fadescreen FADE_FROM_BLACK
	lockall
	msgbox JourneyBirth_Text_ChooseCity
	closemessage
	special JourneyBirthRegion
	goto_if_eq VAR_RESULT, TRUE, JourneyBirth_ChooseKanto
	multichoicegrid 0, 0, MULTI_JOURNEY_START_HOENN, 3, TRUE
	goto JourneyBirth_ConfirmCity
JourneyBirth_ChooseKanto::
	multichoicegrid 0, 0, MULTI_JOURNEY_START_CITIES, 2, TRUE
JourneyBirth_ConfirmCity::
	special JourneyBirthChooseCity
	releaseall
	end

JourneyBirth_Arrival::
	lockall
	special JourneyBirthSpawnArrival
	special JourneyBirthArrivalVehicle
	goto_if_eq VAR_RESULT, TRUE, JourneyBirth_ArrivalWelcome
	applymovement LOCALID_PLAYER, LittlerootTown_Movement_PlayerStepOffTruck
	waitmovement 0
JourneyBirth_ArrivalWelcome::
	msgbox JourneyBirth_Text_Welcome
	closemessage
	fadescreen FADE_TO_BLACK
	special JourneyBirthRemoveArrival
	special JourneyFamilyWarpBedroom
	waitstate
	releaseall
	end

JourneyBirth_HoennMother::
	goto PlayersHouse_1F_EventScript_MomOriginal

JourneyBirth_OakVisit::
	lockall
	faceplayer
	msgbox JourneyBirth_Text_OakOtherRegion
	closemessage
	multichoice 17, 0, MULTI_JOURNEY_STARTERS, TRUE
	special JourneyBirthGiveKantoVisitStarter
	goto_if_eq VAR_RESULT, FALSE, JourneyBirth_OakFull
	special SetUnlockedPokedexFlags
	playfanfare MUS_OBTAIN_ITEM
	msgbox JourneyBirth_Text_RegionalStarter
	waitfanfare
	releaseall
	end

JourneyBirth_TeamFull::
	msgbox Journey_Text_OakFailure, MSGBOX_NPC
	end

JourneyBirth_Text_ChooseCity::
	.string "Escolha sua cidade inicial.\n"
	.string "Vamos viajar para sua nova casa!$"
JourneyBirth_Text_Welcome::
	.string "MAE: Chegamos à nossa cidade!\n"
	.string "Vamos para sua nova casa.\p"
	.string "Seu quarto está pronto.\n"
	.string "Pode descer quando quiser!$"
JourneyBirth_Text_OakOtherRegion::
	.string "OAK: Você veio de HOENN!\n"
	.string "Bem-vindo a PALLET.\p"
	.string "Escolha um parceiro de KANTO.\n"
	.string "Ele estará no nível 5.$"
JourneyBirth_Text_RegionalStarter::
	.string "Você recebeu um inicial\n"
	.string "desta regiao, no nível 5!$"
JourneyBirth_Text_BirchVisit::
	.string "BIRCH: Sou amigo dos seus pais.\n"
	.string "Vim conhecer sua nova casa!\p"
	.string "Na bolsa, trouxe três POKéMON\n"
	.string "de HOENN para você escolher.\p"
	.string "Também vou dar a POKéDEX.\n"
	.string "Quero ajudar na sua jornada!$"
JourneyBirth_Text_BirchReturn::
	.string "BIRCH: Agora vou voltar ao\n"
	.string "laboratório em LITTLEROOT.\p"
	.string "Passe lá quando quiser!$"

JourneyBirth_Captain::
	lock
	faceplayer
	msgbox JourneyBirth_Text_Captain
	closemessage
	yesnobox 20, 8
	goto_if_eq VAR_RESULT, FALSE, JourneyBirth_CaptainCancel
	fadescreen FADE_TO_BLACK
	warp MAP_SLATEPORT_CITY, 21, 41
	waitstate
	release
	end
JourneyBirth_CaptainCancel::
	release
	end
JourneyBirth_Text_Captain::
	.string "Levo você a SLATEPORT de barco.\n"
	.string "A passagem é gratuita.\p"
	.string "Quer embarcar agora?$"

JourneyBirth_OakFull::
	msgbox Journey_Text_OakFailure
	releaseall
	end
