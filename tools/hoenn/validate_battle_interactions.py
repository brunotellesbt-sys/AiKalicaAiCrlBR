"""Exercise actual battle predicates, damage and held-item effects in mGBA.

Battle state is prepared explicitly. This is a mechanics regression suite, not
a controller playthrough or an exhaustive proof of every ability combination.
"""
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_pwt_world.py').read_text().split('for generation in range(cap+1):')[0]
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_pwt_world.py'),'exec'))
from battle_interaction_fixture import BattleFixture

called_functions=set()
original_native=native
def native(name,*values,**kwargs):
    called_functions.add(name)
    return original_native(name,*values,**kwargs)

types='NORMAL FIRE WATER ELECTRIC GRASS ICE FIGHTING POISON GROUND FLYING PSYCHIC BUG ROCK GHOST DRAGON DARK STEEL FAIRY'.split()
abilities='NONE IMMUNITY CORROSION LIMBER WATER_VEIL WATER_BUBBLE THERMAL_EXCHANGE INSOMNIA VITAL_SPIRIT MAGMA_ARMOR COMATOSE PURIFYING_SALT OWN_TEMPO SWEET_VEIL PASTEL_VEIL FLOWER_VEIL LEAF_GUARD LEVITATE MOLD_BREAKER NEUTRALIZING_GAS KLUTZ HUGE_POWER GUTS ADAPTABILITY TECHNICIAN SHEER_FORCE TOUGH_CLAWS PUNK_ROCK SOUNDPROOF BULLETPROOF GOOD_AS_GOLD VOLT_ABSORB WATER_ABSORB DRY_SKIN EARTH_EATER MOTOR_DRIVE LIGHTNING_ROD STORM_DRAIN SAP_SIPPER WELL_BAKED_BODY FLASH_FIRE PRANKSTER MULTISCALE SHADOW_SHIELD THICK_FAT FLUFFY FUR_COAT ICE_SCALES SOLID_ROCK FILTER PRISM_ARMOR SWIFT_SWIM CHLOROPHYLL SAND_RUSH SLUSH_RUSH QUICK_FEET SURGE_SURFER SLOW_START UNBURDEN PROTOSYNTHESIS QUARK_DRIVE BATTLE_ARMOR SHELL_ARMOR SUPER_LUCK MERCILESS STURDY MAGIC_GUARD UNNERVE RIPEN GLUTTONY'.split()
holds='NONE ABILITY_SHIELD AIR_BALLOON IRON_BALL RING_TARGET SAFETY_GOGGLES CHOICE_BAND CHOICE_SPECS CHOICE_SCARF LIFE_ORB ASSAULT_VEST EVIOLITE UTILITY_UMBRELLA MACHO_BRACE LEFTOVERS BLACK_SLUDGE CURE_PAR CURE_PSN CURE_BRN CURE_FRZ CURE_SLP CURE_STATUS TOXIC_ORB FLAME_ORB FOCUS_SASH MENTAL_HERB'.split()
items='NONE ABILITY_SHIELD CHOICE_BAND CHOICE_SCARF AIR_BALLOON LEFTOVERS BLACK_SLUDGE CHERI_BERRY PECHA_BERRY RAWST_BERRY ASPEAR_BERRY CHESTO_BERRY LUM_BERRY TOXIC_ORB FLAME_ORB FOCUS_SASH MENTAL_HERB'.split()
moves='TACKLE EARTHQUAKE THUNDERBOLT SURF FLAMETHROWER ICE_BEAM GIGA_DRAIN SHADOW_BALL HYPER_VOICE SPORE TOXIC GROWL QUICK_ATTACK PROTECT THOUSAND_ARROWS FACADE FALSE_SWIPE STORM_THROW'.split()
constants=set('TYPE_'+n for n in types+['MYSTERY'])
for prefix,names in [('ABILITY_',abilities),('HOLD_EFFECT_',holds),('ITEM_',items),('MOVE_',moves)]:constants.update(prefix+n for n in names)
constants.update('BATTLE_TYPE_FRONTIER BATTLE_TYPE_DOUBLE SPECIES_SNORLAX SPECIES_EEVEE STAT_SPEED STAT_ATK STAT_SPATK STATUS1_POISON STATUS1_TOXIC_POISON STATUS1_BURN STATUS1_PARALYSIS STATUS1_SLEEP STATUS1_FREEZE STATUS_FIELD_MISTY_TERRAIN STATUS_FIELD_ELECTRIC_TERRAIN STATUS_FIELD_PSYCHIC_TERRAIN STATUS_FIELD_GRAVITY STATUS_FIELD_MAGIC_ROOM SIDE_STATUS_SAFEGUARD SIDE_STATUS_TAILWIND SIDE_STATUS_REFLECT SIDE_STATUS_LIGHTSCREEN B_WEATHER_RAIN B_WEATHER_SUN B_WEATHER_SANDSTORM B_WEATHER_SNOW NOT_BLOCKED_BY_SLEEP_CLAUSE ITEM_NO_EFFECT'.split())
constants.update(['ABILITY_INFILTRATOR','ABILITY_OVERCOAT'])
constants.update('ABILITY_UNAWARE ABILITY_FRIEND_GUARD ABILITY_TELEPATHY ABILITY_WONDER_GUARD ABILITY_CLOUD_NINE ABILITY_AIR_LOCK HOLD_EFFECT_RESTORE_PP HOLD_EFFECT_RESTORE_HP HOLD_EFFECT_RESTORE_PCT_HP ITEM_LEPPA_BERRY ITEM_ORAN_BERRY ITEM_SITRUS_BERRY MON_DATA_MOVE1 MON_DATA_PP1 MON_DATA_PP_BONUSES MOVE_EARTH_POWER'.split())
constants.update('ITEM_HEAVY_DUTY_BOOTS HOLD_EFFECT_HEAVY_DUTY_BOOTS HAZARDS_SPIKES HAZARDS_TOXIC_SPIKES HAZARDS_STEALTH_ROCK STATUS_FIELD_TRICK_ROOM B_ACTION_USE_MOVE ABILITY_STALL'.split())
constants.update(['B_WEATHER_RAIN_NORMAL','B_WEATHER_SUN_NORMAL'])
f=BattleFixture(source,lib,s,native,party,constants)
checks=[]
def expect(group,name,actual,expected,**inputs):
    row=dict(group=group,case=name,inputs=inputs,actual=actual,expected=expected,passed=actual==expected)
    checks.append(row)
    assert row['passed'],row
def ability(battler,name):f.mon(battler,'ability',f.c('ABILITY_'+name))
def held(battler,name):f.mon(battler,'item',f.c('ITEM_'+name))
def field(name):lib.write32(s['gFieldStatuses'],f.c('STATUS_FIELD_'+name))
def weather(name):
    # SUN/RAIN are masks containing ordinary and primal bits, not weather states.
    value_name=name+'_NORMAL' if name in ('SUN','RAIN') else name
    lib.write16(s['gBattleWeather'],f.c('B_WEATHER_'+value_name))
def side(name,battler=1):lib.write32(s['gSideStatuses']+(battler%2)*4,f.c('SIDE_STATUS_'+name))
def status(kind,ability_atk='NONE',ability_def='NONE',target=1):
    args=[0,target]
    if kind=='Poisoned':args.extend([f.c('ABILITY_'+ability_atk),f.c('ABILITY_'+ability_def)])
    else:args.append(f.c('ABILITY_'+ability_def))
    if kind=='Slept':args.append(f.c('NOT_BLOCKED_BY_SLEEP_CLAUSE'))
    return bool(native('CanBe'+kind,*args))

# Canonical Gen 6+ chart, independently expressed as attacker -> defender sets.
chart={
 'NORMAL':('', 'ROCK STEEL', 'GHOST'),
 'FIRE':('GRASS ICE BUG STEEL','FIRE WATER ROCK DRAGON',''),
 'WATER':('FIRE GROUND ROCK','WATER GRASS DRAGON',''),
 'ELECTRIC':('WATER FLYING','ELECTRIC GRASS DRAGON','GROUND'),
 'GRASS':('WATER GROUND ROCK','FIRE GRASS POISON FLYING BUG DRAGON STEEL',''),
 'ICE':('GRASS GROUND FLYING DRAGON','FIRE WATER ICE STEEL',''),
 'FIGHTING':('NORMAL ICE ROCK DARK STEEL','POISON FLYING PSYCHIC BUG FAIRY','GHOST'),
 'POISON':('GRASS FAIRY','POISON GROUND ROCK GHOST','STEEL'),
 'GROUND':('FIRE ELECTRIC POISON ROCK STEEL','GRASS BUG','FLYING'),
 'FLYING':('GRASS FIGHTING BUG','ELECTRIC ROCK STEEL',''),
 'PSYCHIC':('FIGHTING POISON','PSYCHIC STEEL','DARK'),
 'BUG':('GRASS PSYCHIC DARK','FIRE FIGHTING POISON FLYING GHOST STEEL FAIRY',''),
 'ROCK':('FIRE ICE FLYING BUG','FIGHTING GROUND STEEL',''),
 'GHOST':('PSYCHIC GHOST','DARK','NORMAL'),
 'DRAGON':('DRAGON','STEEL','FAIRY'),
 'DARK':('PSYCHIC GHOST','FIGHTING DARK FAIRY',''),
 'STEEL':('ICE ROCK FAIRY','FIRE WATER ELECTRIC STEEL',''),
 'FAIRY':('FIGHTING DRAGON DARK','FIRE POISON STEEL',''),
}
for atk in types:
    strong,resist,immune=map(str.split,chart[atk])
    for defender in types:
        expected=0 if defender in immune else 8192 if defender in strong else 2048 if defender in resist else 4096
        expect('type_chart',atk+'-'+defender,native('GetTypeModifier',f.c('TYPE_'+atk),f.c('TYPE_'+defender)),expected)
print('Native type chart passed: 324 pairs',flush=True)

for target_type in types:
    for kind,blocked in [('Poisoned',{'POISON','STEEL'}),('Burned',{'FIRE'}),('Paralyzed',{'ELECTRIC'}),('Frozen',{'ICE'}),('Slept',set())]:
        f.reset();f.types(1,'TYPE_'+target_type)
        expect('status_type',kind+'-'+target_type,status(kind),target_type not in blocked)
for kind,names in [('Poisoned',['IMMUNITY']),('Burned',['WATER_VEIL','WATER_BUBBLE','THERMAL_EXCHANGE']),
                   ('Paralyzed',['LIMBER']),('Frozen',['MAGMA_ARMOR']),('Slept',['INSOMNIA','VITAL_SPIRIT'])]:
    for name in names+['COMATOSE','PURIFYING_SALT']:
        f.reset();ability(1,name)
        expect('status_ability',kind+'-'+name,status(kind,ability_def=name),False)
for type_name in ['POISON','STEEL']:
    f.reset();f.types(1,'TYPE_'+type_name);ability(0,'CORROSION')
    expect('status_ability','corrosion-'+type_name,status('Poisoned','CORROSION'),True)
for kind in ['Poisoned','Burned','Paralyzed','Frozen','Slept']:
    f.reset();field('MISTY_TERRAIN')
    expect('terrain','misty-'+kind,status(kind),False)
    f.types(1,'TYPE_FLYING')
    expect('terrain','airborne-misty-'+kind,status(kind),True)
f.reset();field('ELECTRIC_TERRAIN');expect('terrain','electric-sleep',status('Slept'),False)
f.types(1,'TYPE_FLYING');expect('terrain','airborne-electric-sleep',status('Slept'),True)
for kind in ['Poisoned','Burned','Paralyzed','Frozen','Slept']:
    f.reset();side('SAFEGUARD');expect('status_side','safeguard-'+kind,status(kind),False)
f.reset();side('SAFEGUARD');expect('status_side','infiltrator-poison',status('Poisoned','INFILTRATOR'),True)
for protect_ability,kind in [('PASTEL_VEIL','Poisoned'),('SWEET_VEIL','Slept'),('FLOWER_VEIL','Burned')]:
    f.reset(double=True);ability(3,protect_ability)
    if protect_ability=='FLOWER_VEIL':f.types(1,'TYPE_GRASS')
    expect('double_partner',protect_ability,status(kind),False)
    f.mon(3,'hp',0);expect('double_partner',protect_ability+'-fainted',status(kind),True)
for name in ['NONE','OWN_TEMPO']:
    f.reset();ability(1,name)
    expect('confusion',name,bool(native('CanBeConfused',0,1)),name=='NONE')
f.reset();field('MISTY_TERRAIN');expect('confusion','misty',bool(native('CanBeConfused',0,1)),False)

for target_type,def_ability,hold,gravity,expected in [
 ('NORMAL','NONE','NONE',False,True),('FLYING','NONE','NONE',False,False),
 ('NORMAL','LEVITATE','NONE',False,False),('NORMAL','NONE','AIR_BALLOON',False,False),
 ('FLYING','LEVITATE','IRON_BALL',False,True),('FLYING','LEVITATE','AIR_BALLOON',True,True)]:
    f.reset();f.types(1,'TYPE_'+target_type)
    if gravity:field('GRAVITY')
    expect('grounding',f'{target_type}-{def_ability}-{hold}-{gravity}',bool(native('IsBattlerGrounded',1,f.c('ABILITY_'+def_ability),f.c('HOLD_EFFECT_'+hold))),expected)
for volatile in ['root','smackDown']:
    f.reset();f.types(1,'TYPE_FLYING');f.bits('mon_'+volatile,1,1)
    expect('grounding',volatile,bool(native('IsBattlerGrounded',1,f.c('ABILITY_LEVITATE'),f.c('HOLD_EFFECT_AIR_BALLOON'))),True)
for volatile in ['magnetRise','telekinesis']:
    f.reset();f.bits('mon_'+volatile,1,1)
    expect('grounding',volatile,bool(native('IsBattlerGrounded',1,0,0)),False)

# Ability resolution must happen before status/damage predicates receive it.
for mode,item,expected in [('plain','NONE','LEVITATE'),('mold','NONE','NONE'),
 ('mold','ABILITY_SHIELD','LEVITATE'),('gas','NONE','NONE'),('gas','ABILITY_SHIELD','LEVITATE'),
 ('acid','NONE','NONE')]:
    f.reset();ability(1,'LEVITATE');held(1,item)
    if mode=='mold':ability(0,'MOLD_BREAKER');f.bits('battle_moldBreakerActive',1)
    if mode=='gas':ability(0,'NEUTRALIZING_GAS');f.bits('mon_neutralizingGas',1)
    if mode=='acid':f.bits('mon_gastroAcid',1,1)
    resolved=native('GetBattlerAbility',1)
    expect('ability_resolution',mode+'-'+item,resolved,f.c('ABILITY_'+expected))
    ctx=f.context('EARTHQUAKE',ability_def='ABILITY_'+expected)
    expect('ability_resolution',mode+'-'+item+'-ground-immunity',native('CalcTypeEffectivenessMultiplier',ctx),0 if expected=='LEVITATE' else 4096)
for mode in ['plain','embargo','magic-room','klutz','gas-klutz']:
    f.reset();held(1,'CHOICE_BAND')
    if mode=='embargo':f.bits('mon_embargo',1,1)
    if mode=='magic-room':field('MAGIC_ROOM')
    if 'klutz' in mode:ability(1,'KLUTZ')
    if mode=='gas-klutz':ability(0,'NEUTRALIZING_GAS');f.bits('mon_neutralizingGas',1)
    expect('item_negation',mode,native('GetBattlerHoldEffect',1),f.c('HOLD_EFFECT_CHOICE_BAND') if mode in ['plain','gas-klutz'] else 0)
for name,move in [('VOLT_ABSORB','THUNDERBOLT'),('WATER_ABSORB','SURF'),('DRY_SKIN','SURF'),
 ('EARTH_EATER','EARTHQUAKE'),('MOTOR_DRIVE','THUNDERBOLT'),('LIGHTNING_ROD','THUNDERBOLT'),
 ('STORM_DRAIN','SURF'),('SAP_SIPPER','GIGA_DRAIN'),('WELL_BAKED_BODY','FLAMETHROWER'),
 ('FLASH_FIRE','FLAMETHROWER'),('SOUNDPROOF','HYPER_VOICE'),('BULLETPROOF','SHADOW_BALL'),('GOOD_AS_GOLD','TOXIC')]:
    for attack,expected in [(move,True),('TACKLE',False)]:
        f.reset();ctx=f.context(attack,ability_def='ABILITY_'+name)
        expect('move_block',name+'-'+attack,bool(native('CanMoveBeBlockedByTarget',ctx,0)),expected)
for target_type,item,def_ability,expected in [('NORMAL','NONE','NONE',False),('GRASS','NONE','NONE',True),
 ('NORMAL','SAFETY_GOGGLES','NONE',True),('NORMAL','NONE','OVERCOAT',True)]:
    f.reset();f.types(1,'TYPE_'+target_type)
    ctx=f.context('SPORE',ability_def='ABILITY_'+def_ability,hold_def='HOLD_EFFECT_'+item)
    expect('powder',target_type+'-'+item+'-'+def_ability,bool(native('CanMoveBeBlockedByTarget',ctx,0)),expected)
for target_type,priority,expected in [('NORMAL',1,True),('FLYING',1,False),('NORMAL',0,False)]:
    f.reset();field('PSYCHIC_TERRAIN');f.types(1,'TYPE_'+target_type);ctx=f.context('QUICK_ATTACK')
    expect('priority','psychic-'+target_type+'-'+str(priority),bool(native('CanMoveBeBlockedByTarget',ctx,priority)),expected)
f.reset();f.types(1,'TYPE_DARK');f.bits('protect_pranksterElevated',1)
ctx=f.context('GROWL',ability_atk='ABILITY_PRANKSTER')
expect('priority','prankster-dark',bool(native('CanMoveBeBlockedByTarget',ctx,1)),True)
print('Native status, immunity and suppression checks passed',flush=True)

# Deterministic damage: no critical/random rolls unless explicitly requested.
def damage(move='TACKLE',atk='NONE',defender='NONE',hold_atk='NONE',hold_def='NONE',crit=False):
    ctx=f.context(move,'ABILITY_'+atk,'ABILITY_'+defender,'HOLD_EFFECT_'+hold_atk,'HOLD_EFFECT_'+hold_def,
        weather=lib.read16(s['gBattleWeather']),crit=crit)
    before_roll=native('CalculateMoveDamageVars',ctx)
    return native('ApplyModifiersAfterDmgRoll',ctx,before_roll)
def damage_ratio(name,move,factor,**kwargs):
    f.reset();baseline=damage(move)
    for key,value in kwargs.pop('fixture',{}).items():
        if key=='burn':f.mon(0,'status1',f.c('STATUS1_BURN'),4)
        if key=='weather':weather(value)
        if key=='hp':f.mon(1,'hp',value)
        if key=='screen':side(value)
        if key=='species':f.mon(1,'species',f.c('SPECIES_'+value))
    observed=damage(move,**kwargs);expected=baseline*factor
    row=dict(group='damage',case=name,baseline=baseline,actual=observed,expected_ratio=factor,
             tolerance=3,passed=abs(observed-expected)<=3)
    if not row['passed']:
        row['fixture_debug']={'weather':lib.read16(s['gBattleWeather']),
            'context':bytes(lib.read8(f.addresses['ctx']+i) for i in range(f.abi['ctx_size'])).hex(),
            'weather_mask':f.packed['ctx_weather']}
    checks.append(row);assert row['passed'],row
for name,move,factor,kwargs in [
 ('huge-power','TACKLE',2,{'atk':'HUGE_POWER'}),('choice-band','TACKLE',1.5,{'hold_atk':'CHOICE_BAND'}),
 ('choice-specs','FLAMETHROWER',1.5,{'hold_atk':'CHOICE_SPECS'}),('life-orb','TACKLE',1.3,{'hold_atk':'LIFE_ORB'}),
 ('adaptability-stab','TACKLE',4/3,{'atk':'ADAPTABILITY'}),('technician','TACKLE',1.5,{'atk':'TECHNICIAN'}),
 ('tough-claws-contact','TACKLE',1.3,{'atk':'TOUGH_CLAWS'}),('sheer-force','FLAMETHROWER',1.3,{'atk':'SHEER_FORCE'}),
 ('punk-rock','HYPER_VOICE',1.3,{'atk':'PUNK_ROCK'}),('burn','TACKLE',.5,{'fixture':{'burn':True}}),
 ('guts-burn','TACKLE',1.5,{'atk':'GUTS','fixture':{'burn':True}}),
 ('facade-burn','FACADE',2,{'fixture':{'burn':True}}),
 ('multiscale-full','TACKLE',.5,{'defender':'MULTISCALE'}),('multiscale-damaged','TACKLE',1,{'defender':'MULTISCALE','fixture':{'hp':99}}),
 ('shadow-shield','TACKLE',.5,{'defender':'SHADOW_SHIELD'}),('fur-coat','TACKLE',.5,{'defender':'FUR_COAT'}),
 ('ice-scales','FLAMETHROWER',.5,{'defender':'ICE_SCALES'}),('thick-fat-fire','FLAMETHROWER',.5,{'defender':'THICK_FAT'}),
 ('fluffy-contact','TACKLE',.5,{'defender':'FLUFFY'}),('fluffy-fire','FLAMETHROWER',2,{'defender':'FLUFFY'}),
 ('assault-vest','FLAMETHROWER',2/3,{'hold_def':'ASSAULT_VEST'}),
 ('eviolite-unevolved','TACKLE',2/3,{'hold_def':'EVIOLITE','fixture':{'species':'EEVEE'}}),
 ('eviolite-fully-evolved','TACKLE',1,{'hold_def':'EVIOLITE'}),
 ('sun-fire','FLAMETHROWER',1.5,{'fixture':{'weather':'SUN'}}),('rain-fire','FLAMETHROWER',.5,{'fixture':{'weather':'RAIN'}}),
 ('sun-water','SURF',.5,{'fixture':{'weather':'SUN'}}),('rain-water','SURF',1.5,{'fixture':{'weather':'RAIN'}}),
 ('reflect','TACKLE',.5,{'fixture':{'screen':'REFLECT'}}),('light-screen','FLAMETHROWER',.5,{'fixture':{'screen':'LIGHTSCREEN'}}),
 ('critical-reflect','TACKLE',1.5,{'crit':True,'fixture':{'screen':'REFLECT'}}),
 ('infiltrator-reflect','TACKLE',1,{'atk':'INFILTRATOR','fixture':{'screen':'REFLECT'}}),
]:damage_ratio(name,move,factor,**kwargs)
for ability_name,weather_name in [('SWIFT_SWIM','RAIN'),('CHLOROPHYLL','SUN'),('SAND_RUSH','SANDSTORM'),('SLUSH_RUSH','SNOW')]:
    f.reset();weather(weather_name)
    expect('speed',ability_name,native('GetBattlerTotalSpeedStat',0,f.c('ABILITY_'+ability_name),0),200)
for ability_name,hold_name,condition,expected in [
 ('NONE','NONE','none',100),('NONE','CHOICE_SCARF','none',150),('NONE','IRON_BALL','none',50),
 ('NONE','MACHO_BRACE','none',50),('NONE','NONE','paralysis',50),('QUICK_FEET','NONE','paralysis',150),
 ('SWIFT_SWIM','UTILITY_UMBRELLA','rain',100),('SWIFT_SWIM','CHOICE_SCARF','rain',300),
 ('SURGE_SURFER','NONE','electric',200),('SLOW_START','NONE','slow-start',50),('UNBURDEN','NONE','unburden',200),
 ('NONE','CHOICE_SCARF','tailwind-paralysis',150)]:
    f.reset()
    if 'paralysis' in condition:f.mon(0,'status1',f.c('STATUS1_PARALYSIS'),4)
    if condition=='rain':weather('RAIN')
    if condition=='electric':field('ELECTRIC_TERRAIN')
    if condition=='slow-start':f.bits('mon_slowStartTimer',5)
    if condition=='unburden':f.bits('mon_unburdenActive',1)
    if 'tailwind' in condition:side('TAILWIND',0)
    expect('speed',ability_name+'-'+hold_name+'-'+condition,native('GetBattlerTotalSpeedStat',0,f.c('ABILITY_'+ability_name),f.c('HOLD_EFFECT_'+hold_name)),expected)
for ability_name,move,expected in [('NONE','TACKLE',False),('NONE','STORM_THROW',True),('BATTLE_ARMOR','STORM_THROW',False),('SHELL_ARMOR','STORM_THROW',False)]:
    f.reset();ctx=f.context(move,ability_def='ABILITY_'+ability_name)
    result=native('CalcCritChanceStage',ctx)
    expect('critical',ability_name+'-'+move,result==0xfffffffe,expected)
for ability_name,item,hp,expected in [('NONE','NONE',100,1000),('STURDY','NONE',100,99),('STURDY','NONE',99,1000),('NONE','FOCUS_SASH',100,99),('NONE','FOCUS_SASH',99,1000)]:
    f.reset();f.mon(1,'hp',hp);held(1,item)
    ctx=f.context('TACKLE',ability_def='ABILITY_'+ability_name,hold_def='HOLD_EFFECT_'+item)
    expect('survival',ability_name+'-'+item+'-'+str(hp),native('GetAdjustedDamage',ctx,1000),expected)
f.reset();ctx=f.context('FALSE_SWIPE');expect('survival','false-swipe',native('GetAdjustedDamage',ctx,1000),99)

# Held-item effects perform status writes directly; animation/consumption
# scripts are scheduled by the real dispatcher, not simulated by the fixture.
def item_effect(item,hold,timing):
    held(1,item)
    return native('ItemBattleEffects',1,1,f.c('HOLD_EFFECT_'+hold),s[timing]|1)
for item,hold,condition in [('CHERI_BERRY','CURE_PAR','PARALYSIS'),('PECHA_BERRY','CURE_PSN','TOXIC_POISON'),
 ('RAWST_BERRY','CURE_BRN','BURN'),('ASPEAR_BERRY','CURE_FRZ','FREEZE'),('CHESTO_BERRY','CURE_SLP','SLEEP'),('LUM_BERRY','CURE_STATUS','POISON')]:
    for unnerve,expected in [(False,True),(True,False)]:
        f.reset();f.mon(1,'status1',f.c('STATUS1_'+condition),4)
        if unnerve:ability(0,'UNNERVE')
        result=item_effect(item,hold,'IsOnStatusChangeActivation')
        expect('berry',item+'-unnerve-'+str(unnerve),bool(result),expected)
        expect('berry',item+'-status-cleared-'+str(unnerve),f.read_mon(1,'status1',4)==0,expected)
for item,hold,status_name,target_type,expected in [('TOXIC_ORB','TOXIC_ORB','TOXIC_POISON','NORMAL',True),
 ('TOXIC_ORB','TOXIC_ORB','TOXIC_POISON','STEEL',False),('FLAME_ORB','FLAME_ORB','BURN','NORMAL',True),('FLAME_ORB','FLAME_ORB','BURN','FIRE',False)]:
    f.reset();f.types(1,'TYPE_'+target_type)
    result=item_effect(item,hold,'IsOrbsActivation')
    expect('orbs',item+'-'+target_type,bool(result),expected)
    expect('orbs',item+'-status-'+target_type,f.read_mon(1,'status1',4),f.c('STATUS1_'+status_name) if expected else 0)
for item,hold,target_type,def_ability,heal_block,expected in [('LEFTOVERS','LEFTOVERS','NORMAL','NONE',False,True),
 ('LEFTOVERS','LEFTOVERS','NORMAL','NONE',True,False),('BLACK_SLUDGE','BLACK_SLUDGE','POISON','NONE',False,True),
 ('BLACK_SLUDGE','BLACK_SLUDGE','NORMAL','NONE',False,True),('BLACK_SLUDGE','BLACK_SLUDGE','NORMAL','MAGIC_GUARD',False,False)]:
    f.reset();f.types(1,'TYPE_'+target_type);f.mon(1,'hp',50);ability(1,def_ability)
    if heal_block:f.bits('mon_healBlock',1,1)
    result=item_effect(item,hold,'IsLeftoversActivation')
    expect('residual_item',item+'-'+target_type+'-'+def_ability+'-'+str(heal_block),bool(result),expected)
for volatile in ['tauntTimer','encoreTimer','healBlock','disableTimer','torment','infatuation']:
    f.reset();f.bits('mon_'+volatile,1,1)
    if volatile=='encoreTimer':f.bits('mon_encoredMove',f.c('MOVE_TACKLE'),1)
    result=item_effect('MENTAL_HERB','MENTAL_HERB','IsOnTargetHitActivation')
    expect('mental_herb',volatile,bool(result),True)
    base,off,shift,width,size=f.packed['mon_'+volatile]
    raw=int.from_bytes(bytes(lib.read8(s['gBattleMons']+f.abi['mon_size']+off+i) for i in range(size)),'little')
    expect('mental_herb',volatile+'-cleared',(raw>>shift)&((1<<width)-1),0)

for item,hold,hp,ability_name,blocked,expected_heal in [
 ('ORAN_BERRY','RESTORE_HP',50,'NONE',False,10),('ORAN_BERRY','RESTORE_HP',50,'RIPEN',False,20),
 ('SITRUS_BERRY','RESTORE_PCT_HP',50,'NONE',False,25),('SITRUS_BERRY','RESTORE_PCT_HP',50,'RIPEN',False,50),
 ('SITRUS_BERRY','RESTORE_PCT_HP',51,'NONE',False,0),('SITRUS_BERRY','RESTORE_PCT_HP',50,'NONE',True,0)]:
    f.reset();f.mon(1,'hp',hp);ability(1,ability_name)
    if blocked:f.bits('mon_healBlock',1,1)
    result=item_effect(item,hold,'IsOnHpThresholdActivation')
    expect('berry_heal',item+'-'+ability_name+'-'+str(hp)+'-'+str(blocked),bool(result),expected_heal>0)
    size=f.abi['battle_hp_delta_size']
    at=f.addresses['battle']+f.abi['battle_passiveHpUpdate']+size
    delta=int.from_bytes(bytes(lib.read8(at+i) for i in range(size)),'little',signed=True)
    expect('berry_heal',item+'-scheduled-heal-'+ability_name+'-'+str(hp)+'-'+str(blocked),delta,-expected_heal)
for ability_name,hp,expected in [('NONE',26,False),('NONE',25,True),('GLUTTONY',50,True),('GLUTTONY',51,False)]:
    f.reset();f.mon(1,'hp',hp);ability(1,ability_name)
    expect('berry_threshold',ability_name+'-'+str(hp),bool(native('HasEnoughHpToEatBerry',1,f.c('ABILITY_'+ability_name),4,f.c('ITEM_SITRUS_BERRY'))),expected)

# Leppa reads party data and publishes a controller update, while battle PP
# changes immediately. Do not claim persistence/animation without that controller.
for move,max_pp in [('TACKLE',35),('EARTH_POWER',10)]:
    for ability_name,unnerve,expected_restore in [('NONE',False,10),('RIPEN',False,20),('NONE',True,0)]:
        f.reset();ability(1,ability_name)
        if unnerve:ability(0,'UNNERVE')
        # Clone a valid encrypted party record, then use the native data setters.
        f.write(enemy,bytes(lib.read8(party+i) for i in range(abi[2])))
        lib.write8(s['gBattlerPartyIndexes']+1,0)
        scratch=s['gStringVar4']+800
        for slot in range(4):
            f.write(scratch,f.c('MOVE_'+move).to_bytes(2,'little') if slot==0 else bytes(2))
            native('SetMonData',enemy,f.c('MON_DATA_MOVE1')+slot,scratch)
            f.write(scratch,bytes([0]));native('SetMonData',enemy,f.c('MON_DATA_PP1')+slot,scratch)
        f.write(scratch,bytes([0]));native('SetMonData',enemy,f.c('MON_DATA_PP_BONUSES'),scratch)
        f.mon(1,'moves',f.c('MOVE_'+move));f.mon(1,'pp',0,1)
        result=item_effect('LEPPA_BERRY','RESTORE_PP','IsSprayLeppaBlunderActivation')
        label=move+'-'+ability_name+'-'+str(unnerve)
        expect('leppa',label+'-activated',bool(result),expected_restore>0)
        expect('leppa',label+'-pp',f.read_mon(1,'pp',1),min(max_pp,expected_restore))

for def_ability,atk_stage,expected_factor in [('NONE',8,2),('UNAWARE',8,1)]:
    f.reset();baseline=damage('EARTHQUAKE')
    lib.write8(s['gBattleMons']+f.abi['mon_statStages']+f.c('STAT_ATK'),atk_stage)
    actual=damage('EARTHQUAKE',defender=def_ability)
    checks.append(dict(group='stat_stages',case=def_ability+'-attack-boost',baseline=baseline,actual=actual,
        expected_ratio=expected_factor,tolerance=3,passed=abs(actual-baseline*expected_factor)<=3))
    assert checks[-1]['passed'],checks[-1]
for partner_ability,expected_ratio in [('NONE',1),('FRIEND_GUARD',.75)]:
    f.reset(double=True);baseline=damage('TACKLE');ability(3,partner_ability)
    actual=damage('TACKLE')
    checks.append(dict(group='double_damage',case=partner_ability,baseline=baseline,actual=actual,
        expected_ratio=expected_ratio,tolerance=2,passed=abs(actual-baseline*expected_ratio)<=2))
    assert checks[-1]['passed'],checks[-1]
f.reset(double=True);ctx=f.context('SURF',ability_def='ABILITY_TELEPATHY',defender=2)
expect('double_damage','telepathy-ally',native('CalcTypeEffectivenessMultiplier',ctx),0)
f.reset();ctx=f.context('TACKLE',ability_def='ABILITY_WONDER_GUARD')
expect('wonder_guard','neutral',native('CalcTypeEffectivenessMultiplier',ctx),0)
f.types(1,'TYPE_GRASS');ctx=f.context('FLAMETHROWER',ability_def='ABILITY_WONDER_GUARD')
expect('wonder_guard','super-effective',native('CalcTypeEffectivenessMultiplier',ctx),8192)
for suppression in ['CLOUD_NINE','AIR_LOCK']:
    f.reset();weather('RAIN');ability(1,suppression)
    expect('weather_suppression',suppression+'-get-weather',native('GetWeather'),0)
    expect('weather_suppression',suppression+'-swift-swim',native('GetBattlerTotalSpeedStat',0,f.c('ABILITY_SWIFT_SWIM'),0),100)

for trick_room,move0,move1,atk_ability,item,expected in [
 (False,'TACKLE','TACKLE','NONE','NONE',0xffffffff),
 (True,'TACKLE','TACKLE','NONE','NONE',1),
 (True,'QUICK_ATTACK','TACKLE','NONE','NONE',1),
 (True,'TACKLE','QUICK_ATTACK','NONE','NONE',0xffffffff),
 (False,'TACKLE','TACKLE','NONE','CHOICE_SCARF',1),
 (True,'TACKLE','TACKLE','NONE','CHOICE_SCARF',0xffffffff),
 (True,'TACKLE','TACKLE','STALL','NONE',0xffffffff)]:
    f.reset();f.mon(0,'speed',80);f.mon(1,'speed',100);ability(0,atk_ability);held(0,item)
    if trick_room:field('TRICK_ROOM')
    for battler,move in enumerate([move0,move1]):
        f.mon(battler,'moves',f.c('MOVE_'+move))
        lib.write8(s['gChosenActionByBattler']+battler,f.c('B_ACTION_USE_MOVE'))
    cv=f.calc_values()
    expect('turn_order',f'{trick_room}-{move0}-{move1}-{atk_ability}-{item}',native('GetWhichBattlerFasterOrTies',cv,0),expected)

for hazard,item,def_ability,condition,expected in [
 ('SPIKES','NONE','NONE','plain',12),('SPIKES','HEAVY_DUTY_BOOTS','NONE','plain',0),
 ('SPIKES','NONE','MAGIC_GUARD','plain',0),('SPIKES','HEAVY_DUTY_BOOTS','NONE','magic-room',12),
 ('SPIKES','HEAVY_DUTY_BOOTS','KLUTZ','plain',12),('SPIKES','NONE','LEVITATE','plain',0),
 ('TOXIC_SPIKES','NONE','NONE','plain',12),('TOXIC_SPIKES','HEAVY_DUTY_BOOTS','NONE','plain',0),
 ('STEALTH_ROCK','NONE','NONE','plain',12),('STEALTH_ROCK','HEAVY_DUTY_BOOTS','NONE','plain',0)]:
    f.reset();ability(1,def_ability);held(1,item)
    if condition=='magic-room':field('MAGIC_ROOM')
    native('PushHazardTypeToQueue',1,f.c('HAZARDS_'+hazard))
    if hazard=='SPIKES':f.bits('side_spikesAmount',1,1)
    if hazard=='TOXIC_SPIKES':f.bits('side_toxicSpikesAmount',1,1)
    f.ai_cache()
    actual=native('GetSwitchinHazardsDamage',1)
    label=hazard+'-'+item+'-'+def_ability+'-'+condition
    if actual!=expected:
        failure=dict(passed=False,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
            group='ai_hazards',case=label,actual=actual,expected=expected,native_function='GetSwitchinHazardsDamage')
        (args.output/'battle-interaction-failure.json').write_text(json.dumps(failure,indent=2)+'\n')
    expect('ai_hazards',label,actual,expected)

report=dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
    version_generation_cap=cap,max_national=493 if cap==4 else 1025,perfect_ivs=bool(hard),
    cases=len(checks),checks=checks,groups={name:sum(c['group']==name for c in checks) for name in sorted({c['group'] for c in checks})},
    engine_functions_native=True,called_functions=sorted(called_functions),
    battle_state_is_prepared_fixture=True,damage_random_rolls_disabled=True,
    item_animation_and_consumption_scripts_not_played=True,full_campaign_playthrough=False,
    exhaustive_ability_item_coverage=False)
lib.stop()
(args.output/'battle-interactions.json').write_text(json.dumps(report,indent=2)+'\n')
print('Native battle interactions passed:',len(checks),'cases',flush=True)
