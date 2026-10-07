"""Use Giovanni's native portrait safely; the upstream has no back sprite for him."""

def patch(body):
    old='    if (TESTING)\n    {\n        trainerPicId = TRAINER_PIC_STEVEN;'
    new='''    if (gPartnerTrainerId == TRAINER_PARTNER(PARTNER_GIOVANNI))
    {
        // Giovanni has a native front portrait, but no back-frame table.
        // The existing Frontier path supports a mirrored front portrait.
        trainerPicId = TRAINER_PIC_LEADER_GIOVANNI_FRLG;
        xPos = 90;
        yPos = 80;
    }
    else if (TESTING)
    {
        trainerPicId = TRAINER_PIC_STEVEN;'''
    assert body.count(old)==1;body=body.replace(old,new)
    old='    if (gPartnerTrainerId > TRAINER_PARTNER(PARTNER_NONE))\n        isFrontPic = FALSE;'
    new='    if (gPartnerTrainerId > TRAINER_PARTNER(PARTNER_NONE)\n        && gPartnerTrainerId != TRAINER_PARTNER(PARTNER_GIOVANNI))\n        isFrontPic = FALSE;'
    assert body.count(old)==1;body=body.replace(old,new)
    old='    BtlController_HandleTrainerSlide(battler, trainerPicId);'
    new='''    if (gPartnerTrainerId == TRAINER_PARTNER(PARTNER_GIOVANNI))
        BtlController_HandleDrawTrainerPic(battler, trainerPicId, TRUE, 90, 80, -1);
    else
        BtlController_HandleTrainerSlide(battler, trainerPicId);'''
    assert body.count(old)==1;body=body.replace(old,new)
    old='    if (gPartnerTrainerId > TRAINER_PARTNER(PARTNER_NONE))\n        trainerPal = GetTrainerBackPicPalette('
    new='''    if (gPartnerTrainerId == TRAINER_PARTNER(PARTNER_GIOVANNI))
        trainerPal = GetTrainerFrontPicPalette(TRAINER_PIC_LEADER_GIOVANNI_FRLG);
    else if (gPartnerTrainerId > TRAINER_PARTNER(PARTNER_NONE))
        trainerPal = GetTrainerBackPicPalette('''
    assert body.count(old)==1;return body.replace(old,new)
