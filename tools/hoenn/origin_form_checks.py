"""Verify original Orbs, modern rewards, real item menus and visible Origin sprites."""
CASES=[('Dialga','DIALGA','ADAMANT_ORB','ADAMANT_CRYSTAL'),
       ('Palkia','PALKIA','LUSTROUS_ORB','LUSTROUS_GLOBE'),
       ('Giratina','GIRATINA','GRISEOUS_ORB','GRISEOUS_CORE')]
EXPRESSIONS=['MON_DATA_SPECIES','MON_DATA_HELD_ITEM','MON_DATA_MOVE1','MON_DATA_ATK',
             'MON_DATA_DEF','MON_DATA_SPEED','MON_DATA_SPATK','MON_DATA_SPDEF',
             'FORM_CHANGE_ITEM_HOLD','FLAG_SYS_POKEMON_GET','offsetof(struct BagPosition,pocket)']
for _,species,orb,modern in CASES:
    EXPRESSIONS += ['SPECIES_'+species,'SPECIES_'+species+'_ORIGIN','ITEM_'+orb,'ITEM_'+modern]


def validate(e):
    lib,s,c,native,step,press,task,picture,party,size,scratch=[e[n] for n in
        ['lib','s','c','native','step','press','task','picture','party','mon_size','scratch']]
    def callback():return lib.read32(s['gMain']+4)&~1
    def field():return callback()==s['CB2_Overworld'] and not lib.read8(s['sLockFieldControls'])
    def wait(predicate,label):
        for _ in range(600):
            if predicate():step(30);return
            step(8)
        picture('origin-failure-'+label);raise AssertionError(label)
    def back():
        for _ in range(400):
            if field():step(60);return
            press(2)
        picture('origin-field-failure');raise AssertionError('Origin menus did not close')
    def start_menu(symbol):
        press(8);wait(lambda:lib.read8(s['sNumStartMenuActions'])>0,'start-menu');step(80)
        actions=[lib.read8(s['sCurrentStartMenuActions']+i) for i in range(lib.read8(s['sNumStartMenuActions']))]
        index=next(i for i,a in enumerate(actions) if lib.read32(s['sStartMenuItems']+a*8+4)&~1==s[symbol])
        for _ in range(12):
            pos=lib.read8(s['sStartMenuCursorPos'])
            if pos==index:break
            press(128 if pos<index else 64)
        assert lib.read8(s['sStartMenuCursorPos'])==index
        press(1)
    def setdata(field,value):
        lib.write32(scratch,value);native('SetMonData',party,c[field],scratch)
    def get(field):return native('GetMonData2',party,c[field])
    def fresh(species):
        for i in range(6*size):lib.write8(party+i,0)
        lib.write8(s['gPartiesCount'],0)
        assert native('ScriptGiveMon',c['SPECIES_'+species],70,0)==0
        for i in range(4):
            lib.write32(scratch,0);native('SetMonData',party,c['MON_DATA_MOVE1']+i,scratch)
        native('ClearBag')
    def stats():return [get(n) for n in ['MON_DATA_ATK','MON_DATA_DEF','MON_DATA_SPEED','MON_DATA_SPATK','MON_DATA_SPDEF']]
    native('FlagSet',c['FLAG_SYS_POKEMON_GET'])
    checks=[]
    for label,species,orb,modern in CASES:
        fresh(species);base=c['SPECIES_'+species];origin=c['SPECIES_'+species+'_ORIGIN'];base_stats=stats()
        # Modern story rewards remain valid; these run the same native method
        # as the party menu without touching story flags or species records.
        setdata('MON_DATA_HELD_ITEM',c['ITEM_'+modern])
        assert native('TryFormChange',party,c['FORM_CHANGE_ITEM_HOLD'],0)
        assert get('MON_DATA_SPECIES')==origin and get('MON_DATA_HELD_ITEM')==c['ITEM_'+modern]
        assert stats()!=base_stats
        assert not native('TryFormChange',party,c['FORM_CHANGE_ITEM_HOLD'],0)
        setdata('MON_DATA_HELD_ITEM',0);assert native('TryFormChange',party,c['FORM_CHANGE_ITEM_HOLD'],0)
        assert get('MON_DATA_SPECIES')==base and stats()==base_stats
        # Equip the original Orb through the real Bag GIVE action.
        assert native('AddBagItem',c['ITEM_'+orb],1)
        pocket=native('GetItemPocket',c['ITEM_'+orb]);start_menu('StartMenuBagCallback')
        wait(lambda:task('Task_BagMenu_HandleInput'),'bag')
        for _ in range(16):
            if lib.read8(s['gBagPosition']+c['offsetof(struct BagPosition,pocket)'])==pocket:break
            press(16);step(90)
        assert lib.read8(s['gBagPosition']+c['offsetof(struct BagPosition,pocket)'])==pocket
        press(1);wait(lambda:task('Task_ItemContext_MultipleRows'),'item-context')
        press(16);press(1);wait(lambda:task('Task_HandleChooseMonInput'),'give-to-mon')
        press(1);step(180);back()
        assert get('MON_DATA_SPECIES')==origin,(label,'original Orb did not transform')
        assert get('MON_DATA_HELD_ITEM')==c['ITEM_'+orb]
        assert native('CountTotalItemQuantityInBag',c['ITEM_'+orb])==0
        assert stats()!=base_stats
        assert native('TrySavingData',0,max_frames=6000)==1
        assert native('LoadGameSave',0,max_frames=6000)==1
        assert get('MON_DATA_SPECIES')==origin and get('MON_DATA_HELD_ITEM')==c['ITEM_'+orb]
        start_menu('StartMenuPokemonCallback');wait(lambda:task('Task_HandleChooseMonInput'),'party')
        press(1);wait(lambda:task('Task_HandleSelectionMenuInput'),'party-actions');press(1);step(600)
        assert lib.read32(s['sMonSummaryScreen']), 'Summary did not open'
        picture('origin-'+species.lower());press(16);step(180);picture('origin-'+species.lower()+'-item');back()
        # With one Pokémon and no field moves the Item action is second.
        start_menu('StartMenuPokemonCallback');wait(lambda:task('Task_HandleChooseMonInput'),'take-party')
        press(1);wait(lambda:task('Task_HandleSelectionMenuInput'),'take-actions');press(128);press(1);step(60)
        press(128);press(1);step(120);back()
        assert get('MON_DATA_SPECIES')==base,(label,'taking Orb did not revert')
        assert get('MON_DATA_HELD_ITEM')==0 and native('CountTotalItemQuantityInBag',c['ITEM_'+orb])==1
        assert stats()==base_stats
        checks.append(dict(pokemon=label,orb=orb,modern_item=modern,origin_species=origin,
                           original_orb_equipped_through_bag=True,summary_screenshot='origin-'+species.lower()+'.png',
                           item_taken_through_party_menu=True,stats_change_and_revert=True,
                           modern_reward_still_transforms=True,save_reload_preserves_form_and_item=True))
    # The item must never turn an unrelated Pokémon into a legendary.
    fresh('DIALGA');setdata('MON_DATA_HELD_ITEM',c['ITEM_LUSTROUS_ORB'])
    assert not native('TryFormChange',party,c['FORM_CHANGE_ITEM_HOLD'],0)
    assert get('MON_DATA_SPECIES')==c['SPECIES_DIALGA']
    return dict(checks=checks,wrong_species_orb_rejected=True,party_items_and_initial_position_are_fixtures=True,
                giving_and_taking_original_orbs_use_controller_input=True)
