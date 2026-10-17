JourneyCompetitive_Seller::
	lock
	faceplayer
	msgbox JourneyCompetitive_Welcome
JourneyCompetitive_SellerMenu:
	callnative JourneyCompetitiveShopMenu
	waitstate
	goto_if_eq VAR_RESULT, 0, JourneyCompetitive_Buy0
	goto_if_eq VAR_RESULT, 1, JourneyCompetitive_Buy1
	goto_if_eq VAR_RESULT, 2, JourneyCompetitive_Buy2
	goto_if_eq VAR_RESULT, 3, JourneyCompetitive_Buy3
	goto_if_eq VAR_RESULT, 4, JourneyCompetitive_Buy4
	goto JourneyCompetitive_End
JourneyCompetitive_Buy0:
	pokemart JourneyCompetitive_Stock0
	goto JourneyCompetitive_SellerMenu
JourneyCompetitive_Buy1:
	pokemart JourneyCompetitive_Stock1
	goto JourneyCompetitive_SellerMenu
JourneyCompetitive_Buy2:
	pokemart JourneyCompetitive_Stock2
	goto JourneyCompetitive_SellerMenu
JourneyCompetitive_Buy3:
	pokemart JourneyCompetitive_Stock3
	goto JourneyCompetitive_SellerMenu
JourneyCompetitive_Buy4:
	pokemart JourneyCompetitive_Stock4
	goto JourneyCompetitive_SellerMenu

JourneyCompetitive_Trainer::
	lock
	faceplayer
	msgbox JourneyCompetitive_HyperIntro
	special ChoosePartyMon
	waitstate
	goto_if_ge VAR_0x8004, PARTY_SIZE, JourneyCompetitive_End
	copyvar VAR_0x8008, VAR_0x8004
	callnative JourneyHyperCapMenu
	waitstate
	goto_if_ge VAR_RESULT, 2, JourneyCompetitive_End
	copyvar VAR_0x8006, VAR_RESULT
	setvar VAR_0x8007, 0
	goto_if_eq VAR_0x8006, 1, JourneyCompetitive_Preview
	callnative JourneyHyperStatMenu
	waitstate
	goto_if_ge VAR_RESULT, 6, JourneyCompetitive_End
	copyvar VAR_0x8007, VAR_RESULT
JourneyCompetitive_Preview:
	callnative JourneyHyperPreview
	goto_if_eq VAR_RESULT, 2, JourneyCompetitive_TooYoung
	goto_if_eq VAR_RESULT, 3, JourneyCompetitive_Perfect
	goto_if_eq VAR_RESULT, 4, JourneyCompetitive_Invalid
	goto_if_eq VAR_RESULT, 5, JourneyCompetitive_NoCap
	msgbox JourneyCompetitive_Confirm, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, NO, JourneyCompetitive_End
	callnative JourneyHyperApply
	goto_if_ne VAR_RESULT, 1, JourneyCompetitive_End
	msgbox JourneyCompetitive_Trained
	goto JourneyCompetitive_End
JourneyCompetitive_TooYoung:
	msgbox JourneyCompetitive_TooYoungText
	goto JourneyCompetitive_End
JourneyCompetitive_Perfect:
	msgbox JourneyCompetitive_PerfectText
	goto JourneyCompetitive_End
JourneyCompetitive_Invalid:
	msgbox JourneyCompetitive_InvalidText
	goto JourneyCompetitive_End
JourneyCompetitive_NoCap:
	msgbox JourneyCompetitive_NoCapText
JourneyCompetitive_End:
	releaseall
	end

JourneyCompetitive_FullRestore::
	finditem ITEM_FULL_RESTORE
	end
JourneyCompetitive_PlayRough::
	finditem ITEM_TM_PLAY_ROUGH
	end

JourneyCompetitive_Welcome:
	.string "Welcome to the Frontier market!\nWe import premium battle supplies.\pThe finest equipment costs more.\nFor Hyper Training, visit the\ntrainer at Dewford's stall.$"
JourneyCompetitive_HyperIntro:
	.string "I offer Hyper Training for Pokemon\nat level 50 or above.\pOne Bottle Cap improves one stat.\nA Gold Bottle Cap improves all six.\pTraining does not change the IVs\npassed down through breeding.\nChoose a Pokemon to train.$"
JourneyCompetitive_Confirm:
	.string "Train {STR_VAR_1}:\n{STR_VAR_2}?\pThis will use one\n{STR_VAR_3}.$"
JourneyCompetitive_Trained:
	.string "Hyper Training is complete!\nThe trained stats now perform\nas though their IVs were 31.$"
JourneyCompetitive_TooYoungText:
	.string "Bring this Pokemon back when\nit reaches level 50.$"
JourneyCompetitive_PerfectText:
	.string "Those stats are already perfect\nor have been Hyper Trained.\nNo Bottle Cap was used.$"
JourneyCompetitive_InvalidText:
	.string "I cannot train an Egg.\nPlease choose another Pokemon.$"
JourneyCompetitive_NoCapText:
	.string "You do not have the required cap.\nThe Frontier market stocks\nboth types of Bottle Cap.$"
