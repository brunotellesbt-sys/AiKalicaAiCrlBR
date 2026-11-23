"""Check compiled held-item, move and ability behavior with mGBA battle fixtures."""
import hashlib
import json
from pathlib import Path

from battle_interaction_fixture import BattleFixture

ROOT = Path(__file__).resolve().parents[2]
bootstrap = ROOT / 'tools/hoenn/validate_abilities.py'
exec(compile(bootstrap.read_text().split('\nability_field,')[0], str(bootstrap), 'exec'))

constants = set('''
    TYPE_NORMAL TYPE_MYSTERY SPECIES_SNORLAX SPECIES_IRON_HANDS SPECIES_GREAT_TUSK
    BATTLE_TYPE_DOUBLE BATTLE_TYPE_FRONTIER MOVE_TACKLE MOVE_PSYCHO_CUT MOVE_ICE_PUNCH
    ABILITY_NONE ABILITY_SHARPNESS ABILITY_SHIELD_DUST ABILITY_KLUTZ
    ABILITY_PROTOSYNTHESIS ABILITY_QUARK_DRIVE ABILITY_CLOUD_NINE
    HOLD_EFFECT_NONE HOLD_EFFECT_PUNCHING_GLOVE ITEM_COVERT_CLOAK ITEM_BOOSTER_ENERGY
    STATUS_FIELD_MAGIC_ROOM STATUS_FIELD_ELECTRIC_TERRAIN B_WEATHER_SUN_NORMAL
    STAT_ATK STAT_SPEED ITEM_NO_EFFECT ITEM_EFFECT_OTHER
'''.split())
cap = native('JourneyPWTMaxGeneration')
hard = bool(native('JourneyPerfectTrainerIvs'))
f = BattleFixture(source, lib, s, native, s['gParties'], constants)
checks = []


def expect(case, actual, expected):
    assert actual == expected, (case, actual, expected)
    checks.append(dict(case=case, actual=actual, expected=expected))


def damage(move, **modifiers):
    f.reset()
    context = f.context(move, **modifiers)
    return native('ApplyModifiersAfterDmgRoll', context, native('CalculateMoveDamageVars', context))


for move, factor, modifiers in (
    ('PSYCHO_CUT', 1.5, {'ability_atk': 'ABILITY_SHARPNESS'}),
    ('ICE_PUNCH', 1.1, {'hold_atk': 'HOLD_EFFECT_PUNCHING_GLOVE'}),
):
    baseline = damage(move)
    boosted = damage(move, **modifiers)
    # Damage is integer-valued at each stage of the engine's calculation.
    tolerance = 2
    bounds = (baseline * factor - tolerance, baseline * factor + tolerance)
    assert boosted > baseline and bounds[0] <= boosted <= bounds[1], (move, baseline, boosted, bounds)
    checks.append(dict(case=move, baseline=baseline, actual=boosted, expected_ratio=factor, tolerance=tolerance))
    expect(move + '-nonmatching-move', damage('TACKLE', **modifiers), damage('TACKLE'))

for name, cloak, ability, magic_room, blocked in (
    ('no-protection', False, 'NONE', False, False),
    ('covert-cloak', True, 'NONE', False, True),
    ('covert-cloak-magic-room', True, 'NONE', True, False),
    ('covert-cloak-klutz', True, 'KLUTZ', False, False),
    ('shield-dust-magic-room', False, 'SHIELD_DUST', True, True),
):
    f.reset()
    f.mon(1, 'ability', f.c('ABILITY_' + ability))
    if cloak:
        f.mon(1, 'item', f.c('ITEM_COVERT_CLOAK'))
    if magic_room:
        lib.write32(s['gFieldStatuses'], f.c('STATUS_FIELD_MAGIC_ROOM'))
    expect(name, bool(native('IsMoveEffectBlockedByTarget', native('GetBattlerAbility', 1))), blocked)

if cap == 9:
    bearers = {'PROTOSYNTHESIS': 'GREAT_TUSK', 'QUARK_DRIVE': 'IRON_HANDS', 'NONE': 'SNORLAX'}
    for name, ability, weather, terrain, transformed, suppress_weather, activates in (
        ('protosynthesis', 'PROTOSYNTHESIS', False, False, False, False, True),
        ('protosynthesis-sun', 'PROTOSYNTHESIS', True, False, False, False, False),
        ('protosynthesis-cloud-nine', 'PROTOSYNTHESIS', True, False, False, True, True),
        ('quark-drive', 'QUARK_DRIVE', False, False, False, False, True),
        ('quark-drive-terrain', 'QUARK_DRIVE', False, True, False, False, False),
        ('quark-drive-transformed', 'QUARK_DRIVE', False, False, True, False, False),
        ('unrelated-ability', 'NONE', False, False, False, False, False),
    ):
        f.reset()
        f.mon(0, 'species', f.c('SPECIES_' + bearers[ability]))
        f.mon(0, 'ability', f.c('ABILITY_' + ability))
        f.mon(0, 'item', f.c('ITEM_BOOSTER_ENERGY'))
        f.mon(0, 'speed', 180)
        if weather:
            lib.write16(s['gBattleWeather'], f.c('B_WEATHER_SUN_NORMAL'))
        if terrain:
            lib.write32(s['gFieldStatuses'], f.c('STATUS_FIELD_ELECTRIC_TERRAIN'))
        if suppress_weather:
            f.mon(1, 'ability', f.c('ABILITY_CLOUD_NINE'))
        f.bits('mon_transformed', int(transformed))
        resolved = native('GetBattlerAbility', 0)
        no_effect = f.c('ITEM_NO_EFFECT')
        expect(name, native('TryBoosterEnergy', 0, resolved), f.c('ITEM_EFFECT_OTHER') if activates else no_effect)
        if activates:
            f.mon(0, 'attack', 200)
            expect(name + '-keeps-boosted-stat', native('GetParadoxBoostedStatId', 0), f.c('STAT_SPEED'))
            expect(name + '-no-second-activation', native('TryBoosterEnergy', 0, resolved), no_effect)

    f.reset()
    expect('paradox-stat-tie', native('GetParadoxHighestStatId', 0), f.c('STAT_ATK'))
    booster = f.c('ITEM_BOOSTER_ENERGY')
    expect('booster-transfer-ordinary', bool(native('CanBattlerGetOrLoseItem', 0, 1, booster)), True)
    f.mon(1, 'species', f.c('SPECIES_IRON_HANDS'))
    expect('booster-transfer-to-paradox', bool(native('CanBattlerGetOrLoseItem', 0, 1, booster)), False)
    expect('booster-transfer-from-paradox', bool(native('CanBattlerGetOrLoseItem', 1, 0, booster)), False)

lib.stop()
report = dict(passed=True, rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
              generation_cap=cap, difficulty='Hard' if hard else 'Normal', compiled_battle_fixtures=True,
              checks=checks)
(args.output / 'modern-battle-mechanics.json').write_text(json.dumps(report, indent=2) + '\n')
print('Native modern battle mechanics passed:', len(checks), flush=True)
