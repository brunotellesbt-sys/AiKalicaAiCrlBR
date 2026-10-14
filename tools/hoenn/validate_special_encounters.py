"""Exercise the new encounter objects, form UI, fossil recipes and Dex habitats."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_pwt_world.py').read_text().split('for generation in range(cap+1):')[0]
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_pwt_world.py'),'exec'))
from battle_interaction_fixture import compile_probe
from special_encounters import FOSSILS,FORM_TOOLS
constants={'SPECIES_ROTOM','SPECIES_SPIRITOMB','SPECIES_DEOXYS_NORMAL','SPECIES_DEOXYS_ATTACK','SPECIES_DEOXYS_DEFENSE','SPECIES_DEOXYS_SPEED',
 'ITEM_MASTER_BALL','ITEM_ODD_KEYSTONE','FLAG_GET_CAUGHT','FLAG_JOURNEY_SPIRITOMB_KEYSTONE','FLAG_JOURNEY_EXCAVATION_RELICS',
 'MON_DATA_SPECIES','MON_DATA_LEVEL','MON_DATA_MOVE1','POCKET_POKE_BALLS'}
for name in ['HEAT','WASH','FROST','FAN','MOW']:constants.add('SPECIES_ROTOM_'+name)
constants.update('ITEM_'+item for item in FORM_TOOLS)
for species,item,other in FOSSILS:
    constants.add('SPECIES_'+species);constants.add('ITEM_'+item)
    if other:constants.add('ITEM_'+other)
layout,v,_=compile_probe(source,constants)
marker=json.loads((source/'.journey-special-encounter-workshop').read_text())
actions={int(at,16) for at,_,name in re.findall(r'^(\w+) (\w) (\S+)$',raw,re.M) if name=='HandleInputChooseAction'}
def cb():return lib.read32(s['gMain']+4)&~1
def wait(predicate,label,limit=500):
    for _ in range(limit):
        if predicate():return
        step(8)
    picture('failure-'+label);raise AssertionError(label)
def settle(limit=150):
    for _ in range(limit):
        if cb()==s['CB2_Overworld'] and not lib.read8(s['sLockFieldControls']):return
        press(2)
    picture('failure-settle');raise AssertionError(('Field did not resume',hex(cb())))
def face_up():step(1,64);step(15)
def start_script(label):
    # Used for the fossil menu cancellation check; object/UI captures below
    # use real interactions instead of injecting their event scripts.
    script(b'\x0f\x00'+(s[label]|1).to_bytes(4,'little')+b'\x04'+(s[label]|1).to_bytes(4,'little')+b'\x02',3)
checks=[]
native('ZeroPlayerPartyMons');native('ScriptGiveMon',1,20,0)
native('SetDexPokemonPokenavFlags');native('AddBagItem',v['ITEM_MASTER_BALL'],1)
# Native workshop entrance and exit, keeping the existing tower's stairs.
warp('PokemonTower_1F_Frlg',21,10);face_up();step(24,64);step(200)
if location()!=map_id('JourneyLavenderWorkshop'):
    step(24,16);step(200)
assert location()==map_id('JourneyLavenderWorkshop'),('Workshop entry',location(),position())
warp('JourneyLavenderWorkshop',8,5);step(60);picture('lavender-workshop')
warp('JourneyLavenderWorkshop',8,9);step(24,128);step(200)
assert location()==map_id('PokemonTower_1F_Frlg'),('Workshop exit',location(),position())
checks.append(dict(case='workshop_entry_and_exit',controller_warps=True))
warp('JourneyLavenderWorkshop',2,5);face_up();press(1)
for _ in range(120):
    if cb() in (s['CB2_InitBattle'],s['BattleMainCB2']):break
    press(1)
step(400)
for _ in range(180):
    if (lib.read32(s['gBattlerControllerFuncs'])&~1) in actions:break
    press(2)
assert (lib.read32(s['gBattlerControllerFuncs'])&~1) in actions

assert lib.read8(enemy+offsets[37]) in range(15,23)
picture('rotom-tv-battle')
step(1,64);step(10);step(1,32);step(10);step(1,16);step(10);press(1);step(150)
wait(lambda:task('Task_BagMenu_HandleInput'),'ball-bag')
for _ in range(6):
    if lib.read8(s['gBagPosition']+layout['bag_pocket'])==v['POCKET_POKE_BALLS']:break
    press(16);step(120)
assert lib.read8(s['gBagPosition']+layout['bag_pocket'])==v['POCKET_POKE_BALLS']
press(1);step(60);press(1);step(350)
for _ in range(250):
    if cb()==s['CB2_Overworld']:break
    press(2)
settle();assert native('GetSetPokedexFlag',479,v['FLAG_GET_CAUGHT'])
assert native('GetMonData2',party+abi[2],v['MON_DATA_SPECIES'])==v['SPECIES_ROTOM']
lib.write16(s['gSpecialVar_0x8004'],0);native('JourneyEventEncounterReady');assert lib.read16(s['gSpecialVar_Result'])==2
checks.append(dict(case='rotom_tv_capture',actual_master_ball_capture=True,captured_base_form=True,repeat_capture_blocked=True))
# Give the owned Rotom two empty slots to test the native appliance move flow.
for i in range(4):native('ScriptSetMonMoveSlot',1,85 if i==0 else 0,i)
forms=[]
for choice,species,move in [(1,'ROTOM_HEAT',315),(2,'ROTOM_WASH',56),(3,'ROTOM_FROST',59),(4,'ROTOM_FAN',403),(5,'ROTOM_MOW',437),(0,'ROTOM',84)]:
    warp('JourneyLavenderWorkshop',5,5);face_up();press(1)
    for _ in range(150):
        if task('Task_HandleChooseMonInput'):break
        press(1)
    assert task('Task_HandleChooseMonInput');step(50)
    press(128);press(1)
    wait(lambda:task('Task_HandleSelectionMenuInput'),'rotom-catalog');step(50)
    for _ in range(choice):press(128)
    press(1)
    for _ in range(250):
        if cb()==s['CB2_Overworld']:break
        press(1)
    settle()
    actual=native('GetMonData2',party+abi[2],v['MON_DATA_SPECIES']);assert actual==v['SPECIES_'+species],(choice,actual)
    moves=[native('GetMonData2',party+abi[2],v['MON_DATA_MOVE1']+i) for i in range(4)]
    assert 85 in moves and (choice==0 or move in moves),(species,moves)
    forms.append(dict(appliance_choice=choice,species=actual,moves=moves,controller_native_animation=True))
checks.append(dict(case='rotom_appliances',changes=forms,owned_non_appliance_move_preserved=True))
# Four genuine Deoxys form animations through the meteorite object; the
# story's portable Meteorite is neither granted nor consumed by this service.
native('ZeroPlayerPartyMons');native('ScriptGiveMon',v['SPECIES_DEOXYS_NORMAL'],20,0)
deoxys_forms=[]
for species in ['DEOXYS_ATTACK','DEOXYS_DEFENSE','DEOXYS_SPEED','DEOXYS_NORMAL']:
    warp('JourneyLavenderWorkshop',12,9);face_up();press(1)
    for _ in range(150):
        if task('Task_HandleChooseMonInput'):break
        press(1)
    assert task('Task_HandleChooseMonInput');step(50);press(1)
    for _ in range(250):
        if cb()==s['CB2_Overworld']:break
        press(1)
    settle()
    actual=native('GetMonData2',party,v['MON_DATA_SPECIES'])
    assert actual==v['SPECIES_'+species],(species,actual)
    deoxys_forms.append(actual)
checks.append(dict(case='deoxys_meteorite',four_forms=deoxys_forms,controller_native_animation=True))
# The well consumes one Keystone on installation; fleeing does not consume a
# second one. Capture suppression uses the persistent native Pokédex flag.
native('FlagClear',v['FLAG_JOURNEY_SPIRITOMB_KEYSTONE'])
lib.write16(s['gSpecialVar_0x8004'],1);native('JourneyEventEncounterReady');assert lib.read16(s['gSpecialVar_Result'])==0
native('AddBagItem',v['ITEM_ODD_KEYSTONE'],1);native('JourneyEventEncounterReady')
assert lib.read16(s['gSpecialVar_Result'])==1 and native('FlagGet',v['FLAG_JOURNEY_SPIRITOMB_KEYSTONE'])
assert not native('CheckBagHasItem',v['ITEM_ODD_KEYSTONE'],1)
native('JourneyEventEncounterReady');assert lib.read16(s['gSpecialVar_Result'])==1
checks.append(dict(case='keystone_installation',missing_item_blocks=True,consumed_once=True,retry_without_second_item=True))
native('JourneyGiveFormTools')
assert all(native('CheckBagHasItem',v['ITEM_'+item],1) for item in FORM_TOOLS)
native('JourneyGiveExcavationRelics');assert native('FlagGet',v['FLAG_JOURNEY_EXCAVATION_RELICS'])
fossils=[]
for index,(species,item,other) in enumerate(FOSSILS):
    lib.write16(s['gSpecialVar_0x8004'],index)
    before=native('CheckBagHasItem',v['ITEM_'+item],1)
    native('JourneyReviveModernFossil');result=lib.read16(s['gSpecialVar_Result'])
    allowed=native('JourneySpeciesAllowed',v['SPECIES_'+species])
    assert result==(1 if allowed else 3),(species,result)
    if not allowed:assert native('CheckBagHasItem',v['ITEM_'+item],1)==before
    fossils.append(dict(species=species,allowed=bool(allowed),result=result))
checks.append(dict(case='fossil_restoration',recipes=fossils,unavailable_species_do_not_consume_items=True))
# Dex lookup must contain every moved family and hide all its old grass areas.
dex_checks=[]
catalog=json.loads((ROOT/'tools/hoenn/catalog_metadata.json').read_text())['species']
for dest in marker['destinations']:
    mname=next(p.parent.name for p in (source/'data/maps').glob('*/map.json') if json.loads(p.read_text())['id']==dest['map'])
    group,number=map_id(mname)
    allowed=bool(native('JourneySpeciesAllowed',dest['root']))
    assert bool(native('JourneyHabitatHasSpecies',group,number,dest['root']))==allowed
    for old in marker['random_removed_maps']:
        oldname=next(p.parent.name for p in (source/'data/maps').glob('*/map.json') if json.loads(p.read_text())['id']==old)
        g,n=map_id(oldname);assert not native('JourneyHabitatHasSpecies',g,n,dest['root'])
    dex_checks.append(dict(species=catalog[str(dest['root'])]['name'],destination=mname,available=allowed))
for obj in marker['placed_objects']:
    warp(obj['map'],obj['x'],obj['y']+1);step(60);picture('object-'+obj['script'])
assert native('TrySavingData',0,max_frames=6000)==1
native('FlagClear',v['FLAG_JOURNEY_SPIRITOMB_KEYSTONE']);assert native('LoadGameSave',0)==1
assert native('FlagGet',v['FLAG_JOURNEY_SPIRITOMB_KEYSTONE'])
lib.stop()
r=dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),max_national=493 if cap==4 else 1025,
    version_generation_cap=cap,checks=checks,rotom_changes=forms,dex_locations=dex_checks,event_only_families=21,
    form_tools_available=len(FORM_TOOLS),helper_party_travel_items_are_fixtures=True,actual_tv_capture_and_form_ui=True,
    full_campaign_playthrough=False)
(args.output/'special-encounters.json').write_text(json.dumps(r,indent=2)+'\n')
print('Special encounter and workshop validation passed',flush=True)
