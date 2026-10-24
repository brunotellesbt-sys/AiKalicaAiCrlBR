"""Check canonical story identities in a frozen compiled ROM with native mGBA.

The API matrix uses explicit avatar/birthplace and unloaded map fixtures. Four
representative existing encounters are then entered through controller input,
observing their field dialogue, loaded sprite, battle portrait and battle name.
Party/progress/travel and stronger player battle stats are declared fixtures;
trainer teams, enemy stats, battle outcomes and native event progression are
never written. This is focused integration evidence, not a full campaign run.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

from story_rival_contract import (HERO_NAMES, HERO_GRAPHICS, HERO_PICTURES,
                                 MAPS, NATIVE_TRAINERS, ROLES, expected_trainer)
from validate_badge_qualifier import compiled_probe

ROOT = Path(__file__).resolve().parents[2]
KIND = 'rival-identities'
CONTROLS = ('TRAINER_WALLY_VR_1', 'TRAINER_JOURNEY_BLUE')
FIXED_GRAPHICS = (*HERO_GRAPHICS.values(), 'OBJ_EVENT_GFX_WALLY',
                  'OBJ_EVENT_GFX_JOURNEY_GYM_BLUE')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class RivalNative:
    def __init__(self, options):
        self.options = options
        self.source = options.source.resolve()
        self.output = options.output.resolve()
        self.rom_sha = digest(self.source / 'pokeemerald.gba')
        self.elf_sha = digest(self.source / 'pokeemerald.elf')
        bootstrap = (ROOT / 'tools/hoenn/validate_abilities.py').read_text().split('\nability_field,')[0]
        namespace = {'__file__': str(ROOT / 'tools/hoenn/validate_abilities.py')}
        arguments = sys.argv
        try:
            sys.argv = [sys.argv[0], '--source', str(self.source), '--library',
                        str(options.library), '--output', str(self.output)]
            exec(compile(bootstrap, namespace['__file__'], 'exec'), namespace)
        finally:
            sys.argv = arguments
        self.ns = namespace
        self.lib, self.s = namespace['lib'], namespace['s']
        for name in ['native', 'step', 'press', 'warp', 'map_id', 'position', 'location', 'save']:
            setattr(self, name, namespace[name])
        self.captures = []
        self.char_map = {int(value, 16): character for character, value in re.findall(
            r"^'([^']+)'\s*=\s*([0-9A-F]{2})\s*$", (self.source / 'charmap.txt').read_text().split('@ Hiragana')[0], re.M)}
        self.char_map.update({0: ' ', 0xFA: '\n', 0xFB: '\n\n', 0xFE: '\n'})
        headers = ['global.h', 'data.h', 'pokemon.h', 'battle.h', 'battle_setup.h',
                   'sprite.h', 'event_object_movement.h', 'constants/event_objects.h',
                   'constants/characters.h', 'constants/opponents.h', 'constants/vars.h',
                   'constants/flags.h', 'constants/moves.h', 'constants/map_event_ids.h']
        expressions = [
            'offsetof(struct SaveBlock1, vars)', 'offsetof(struct SaveBlock2, playerGender)',
            'sizeof(struct Trainer)', 'offsetof(struct Trainer, trainerName)',
            'offsetof(struct Trainer, trainerPic)', 'sizeof(enum TrainerPicID)', 'TRAINERS_COUNT',
            'sizeof(struct ObjectEvent)', 'offsetof(struct ObjectEvent, graphicsId)',
            'offsetof(struct ObjectEvent, spriteId)', 'offsetof(struct ObjectEvent, localId)',
            'offsetof(struct ObjectEvent, mapNum)', 'offsetof(struct ObjectEvent, mapGroup)',
            'sizeof(struct Sprite)', 'offsetof(struct Sprite, images)', 'offsetof(struct Sprite, x2)',
            'offsetof(struct ObjectEventGraphicsInfo, images)',
            'offsetof(struct BattleStruct, trainerSlideSpriteIds)',
            'offsetof(TrainerBattleParameter, params.opponentA)',
            'VAR_EVER_GRANDE_CITY_STATE', 'VAR_JOURNEY_START_REGION', 'VAR_MAP_SCENE_ROUTE22',
            'VAR_MAP_SCENE_CERULEAN_CITY_RIVAL', 'VAR_STARTER_MON_FRLG', 'VAR_STARTER_MON',
            'FLAG_HIDE_ROUTE_103_RIVAL', 'PLACEHOLDER_ID_RIVAL',
            'LOCALID_ROUTE22_RIVAL', 'LOCALID_CERULEAN_RIVAL', 'LOCALID_ROUTE103_RIVAL',
            'SPECIES_SWAMPERT', 'MOVE_AERIAL_ACE', 'MON_DATA_MET_LEVEL',
            'sizeof(struct Pokemon)', 'offsetof(struct Pokemon, hp)',
            'offsetof(struct Pokemon, maxHP)', 'offsetof(struct Pokemon, status)',
            'offsetof(struct BattlePokemon, hp)', 'offsetof(struct BattlePokemon, maxHP)',
            'offsetof(struct BattlePokemon, attack)', 'offsetof(struct BattlePokemon, spAttack)',
            'offsetof(struct BattlePokemon, defense)', 'offsetof(struct BattlePokemon, spDefense)',
            'offsetof(struct BattlePokemon, speed)',
            *HERO_GRAPHICS.values(), *HERO_PICTURES.values(), *CONTROLS,
            'OBJ_EVENT_GFX_BLUE', 'OBJ_EVENT_GFX_RIVAL_BRENDAN_NORMAL',
            'OBJ_EVENT_GFX_RIVAL_MAY_NORMAL', 'OBJ_EVENT_GFX_WALLY',
            'OBJ_EVENT_GFX_JOURNEY_GYM_BLUE',
            *(name for name, _, _ in NATIVE_TRAINERS),
        ]
        self.p = compiled_probe(self.source, '\n'.join('#include "' + h + '"' for h in headers)
                                + '\n#include <stddef.h>\n', list(dict.fromkeys(expressions)))
        self.actions = {int(a, 16) for a, _, name in re.findall(
            r'^(\w+) (\w) (\S+)$', namespace['raw'], re.M) if name == 'HandleInputChooseAction'}
        self.moves = {int(a, 16) for a, _, name in re.findall(
            r'^(\w+) (\w) (\S+)$', namespace['raw'], re.M) if name == 'HandleInputChooseMove'}

    def text(self, address, length=1000):
        result, index = [], 0
        control_arguments = {1: 1, 2: 1, 3: 1, 4: 3, 5: 1, 6: 1, 8: 1,
                             11: 2, 12: 1, 13: 1, 14: 1, 16: 2, 17: 1,
                             18: 1, 19: 1, 20: 1, 25: 1, 26: 1, 27: 1, 28: 3}
        while index < length:
            byte = self.lib.read8(address + index)
            index += 1
            if byte == 255:
                break
            if byte == 0xFC:
                control = self.lib.read8(address + index)
                index += 1 + control_arguments.get(control, 0)
                continue
            result.append(self.char_map.get(byte, ''))
        return ''.join(result)

    def var(self, name, value):
        # All writes are declared progress fixtures, never native event outcomes.
        address = self.save() + self.p['offsetof(struct SaveBlock1, vars)']
        self.lib.write16(address + (self.p[name] - 0x4000) * 2, value)

    def identity(self, hero, birth):
        self.var('VAR_EVER_GRANDE_CITY_STATE', hero)
        self.var('VAR_JOURNEY_START_REGION', birth)
        save2 = self.lib.read32(self.s['gSaveBlock2Ptr'])
        self.lib.write8(save2 + self.p['offsetof(struct SaveBlock2, playerGender)'], (hero - 1) & 1)
        alphabet = {value: key for key, value in self.char_map.items() if len(value) == 1}
        for index, byte in enumerate(bytes(alphabet[letter] for letter in HERO_NAMES[hero]) + b'\xff'):
            self.lib.write8(save2 + index, byte)
        assert self.native('JourneyStoryPlayerHero') == hero
        actual = [self.native('JourneyStoryRivalHero', slot) for slot in range(3)]
        assert tuple(actual) == ROLES[hero, birth], (hero, birth, actual)
        return actual

    def capture(self, name):
        self.ns['picture'](name)
        path = self.output / (name + '.png')
        result = dict(file=path.name, sha256=digest(path))
        self.captures.append(result)
        return result

    def matrices(self):
        contexts, trainers, maps, late, controls = [], [], [], [], []
        original_map = self.location()
        original_frlg = self.lib.read8(self.s['isFrlg'])
        control_baselines = {}
        for name in CONTROLS:
            trainer = self.p[name]
            difficulty = self.native('GetTrainerDifficultyLevel', trainer)
            row = self.s['gTrainers'] + (difficulty * self.p['TRAINERS_COUNT'] + trainer) * self.p['sizeof(struct Trainer)']
            control_baselines[name] = (self.text(row + self.p['offsetof(struct Trainer, trainerName)'], 16),
                                      self.lib.read16(row + self.p['offsetof(struct Trainer, trainerPic)']))
        for birth in range(3):
            for hero in HERO_NAMES:
                roles = self.identity(hero, birth)
                contexts.append(dict(player_hero=hero, start_region=birth, roles=roles))
                for name, kanto, slot in NATIVE_TRAINERS:
                    trainer, expected = self.p[name], expected_trainer(hero, birth, kanto, slot)
                    observed = self.native('JourneyStoryNativeTrainerHero', trainer)
                    observed_name = self.text(self.native('JourneyStoryTrainerName', trainer), 16)
                    picture = self.native('JourneyStoryTrainerPic', trainer)
                    compatibility = self.native('JourneyRivalTrainerPic', trainer)
                    assert (observed, observed_name, picture, compatibility) == (
                        expected, HERO_NAMES[expected], self.p[HERO_PICTURES[expected]], self.p[HERO_PICTURES[expected]])
                    trainers.append(dict(player_hero=hero, start_region=birth, trainer=name, trainer_id=trainer,
                                         expected_hero=expected, observed_hero=observed, name=observed_name,
                                         trainer_pic=picture, compatibility_pic=compatibility))
                for name, _, kanto, slot in MAPS:
                    group, number = self.map_id(name)
                    self.lib.write8(self.save() + 4, group)
                    self.lib.write8(self.save() + 5, number)
                    self.lib.write8(self.s['isFrlg'], kanto)
                    self.var('VAR_MAP_SCENE_ROUTE22', 1)
                    expected = expected_trainer(hero, birth, kanto, slot)
                    current = self.native('JourneyStoryCurrentRivalHero')
                    placeholder = self.text(self.native('GetExpandedPlaceholder', self.p['PLACEHOLDER_ID_RIVAL']), 16)
                    legacy = self.p['OBJ_EVENT_GFX_BLUE' if kanto else 'OBJ_EVENT_GFX_RIVAL_MAY_NORMAL']
                    graphics = self.native('JourneyStoryRivalGraphics', legacy)
                    expected_graphics = self.p[HERO_GRAPHICS[expected]]
                    actual_info = self.native('GetObjectEventGraphicsInfo', legacy)
                    expected_info = self.native('GetObjectEventGraphicsInfo', expected_graphics)
                    assert (current, placeholder, graphics, actual_info) == (
                        expected, HERO_NAMES[expected], expected_graphics, expected_info)
                    for fixed in FIXED_GRAPHICS:
                        assert self.native('JourneyStoryRivalGraphics', self.p[fixed]) == self.p[fixed], fixed
                    maps.append(dict(player_hero=hero, start_region=birth, map=name, expected_hero=expected,
                                     observed_hero=current, placeholder=placeholder, graphics=graphics,
                                     native_graphics_info=actual_info))
                    if name == 'Route22_Frlg':
                        self.var('VAR_MAP_SCENE_ROUTE22', 3)
                        expected_late = expected_trainer(hero, birth, True, 1)
                        observed_late = self.native('JourneyStoryCurrentRivalHero')
                        assert observed_late == expected_late
                        late.append(dict(player_hero=hero, start_region=birth,
                                         expected_hero=expected_late, observed_hero=observed_late))
                for name, (expected_name, expected_pic) in control_baselines.items():
                    trainer = self.p[name]
                    observed = self.native('JourneyStoryNativeTrainerHero', trainer)
                    observed_name = self.text(self.native('JourneyStoryTrainerName', trainer), 16)
                    observed_pic = self.native('JourneyRivalTrainerPic', trainer)
                    assert (observed, observed_name, observed_pic) == (0, expected_name, expected_pic)
                    controls.append(dict(player_hero=hero, start_region=birth, trainer=name,
                                         trainer_id=trainer, observed_hero=observed, name=observed_name,
                                         trainer_pic=observed_pic, raw_name=expected_name, raw_pic=expected_pic))
                print('Native rival matrix:', hero, birth, flush=True)
        self.lib.write8(self.save() + 4, original_map[0])
        self.lib.write8(self.save() + 5, original_map[1])
        self.lib.write8(self.s['isFrlg'], original_frlg)
        assert (len(trainers), len(maps), len(late), len(controls)) == (684, 300, 12, 24)
        return dict(identity_contexts=contexts, trainer_observations=trainers, map_observations=maps,
                    route22_late_observations=late, negative_controls=controls,
                    fixed_graphics_controls=list(FIXED_GRAPHICS), api_maps_are_unloaded_fixtures=True)

    def field_actor(self, local_id, expected_images):
        group, number = self.location()
        for index in range(16):
            obj = self.s['gObjectEvents'] + index * self.p['sizeof(struct ObjectEvent)']
            if not self.lib.read8(obj) & 1:
                continue
            if (self.lib.read8(obj + self.p['offsetof(struct ObjectEvent, localId)']),
                self.lib.read8(obj + self.p['offsetof(struct ObjectEvent, mapNum)']),
                self.lib.read8(obj + self.p['offsetof(struct ObjectEvent, mapGroup)'])) != (local_id, number, group):
                continue
            sprite_id = self.lib.read8(obj + self.p['offsetof(struct ObjectEvent, spriteId)'])
            assert sprite_id < 64
            sprite = self.s['gSprites'] + sprite_id * self.p['sizeof(struct Sprite)']
            images = self.lib.read32(sprite + self.p['offsetof(struct Sprite, images)'])
            assert images == expected_images, (local_id, images, expected_images)
            return dict(local_id=local_id, sprite_id=sprite_id, images=images,
                        native_graphics=self.lib.read16(obj + self.p['offsetof(struct ObjectEvent, graphicsId)']))
        return None

    def encounter(self, label, hero, birth, mapping, expected, trainer_names):
        self.identity(hero, birth)
        self.var('VAR_STARTER_MON_FRLG', 0)
        self.var('VAR_STARTER_MON', 0)
        self.var('VAR_MAP_SCENE_ROUTE22', 1)
        self.var('VAR_MAP_SCENE_CERULEAN_CITY_RIVAL', 0)
        self.native('FlagClear', self.p['FLAG_HIDE_ROUTE_103_RIVAL'])
        self.native('SetPlayerAvatarTransitionFlags', 1)
        self.step(30)
        for i in range(6 * self.p['sizeof(struct Pokemon)']):
            self.lib.write8(self.s['gParties'] + i, 0)
        self.lib.write8(self.s['gPartiesCount'], 0)
        assert self.native('ScriptGiveMon', self.p['SPECIES_SWAMPERT'], 40, 0) == 0
        scratch = self.s['gStringVar4'] + 800
        self.lib.write8(scratch, 5)
        self.native('SetMonData', self.s['gParties'], self.p['MON_DATA_MET_LEVEL'], scratch)
        self.native('ScriptSetMonMoveSlot', 0, self.p['MOVE_AERIAL_ACE'], 0)
        expected_pic = self.p[HERO_PICTURES[expected]]
        info = self.native('GetObjectEventGraphicsInfo', self.p[HERO_GRAPHICS[expected]])
        expected_images = self.lib.read32(info + self.p['offsetof(struct ObjectEventGraphicsInfo, images)'])
        if mapping == 'Route22_Frlg':
            self.warp(mapping, 32, 5)
            local_id, trigger_key = self.p['LOCALID_ROUTE22_RIVAL'], 16
        elif mapping == 'CeruleanCity_Frlg':
            self.warp(mapping, 23, 7)
            local_id, trigger_key = self.p['LOCALID_CERULEAN_RIVAL'], 64
        else:
            self.warp(mapping, 11, 3)
            local_id, trigger_key = self.p['LOCALID_ROUTE103_RIVAL'], 32
        # No native-call trampoline is used after this controller trigger.
        self.step(24, trigger_key)
        self.step(25)
        if mapping == 'Route103':
            self.step(1, 1)
        actor, dialogue, field_capture = None, None, None
        for _ in range(450):
            actor = self.field_actor(local_id, expected_images) or actor
            text = self.text(self.s['gStringVar4'])
            if self.lib.read8(self.s['sLockFieldControls']) and HERO_NAMES[expected] + ':' in text and actor:
                self.step(80)
                dialogue = text
                field_capture = self.capture(label + '-field-dialogue')
                break
            self.step(4)
        if not (actor and dialogue):
            self.capture(label + '-field-failed')
        assert actor and dialogue, ('Native rival field dialogue absent', label, self.position(), actor, self.text(self.s['gStringVar4']), self.lib.read8(self.s['sLockFieldControls']))
        started, portrait, battle_name, attacks, opponent = False, None, None, 0, None
        for _ in range(1800):
            battle = (self.lib.read32(self.s['gMain'] + 4) & ~1) == self.s['BattleMainCB2']
            if battle:
                started = True
                opponent = self.lib.read16(self.s['gTrainerBattleParameter'] + self.p['offsetof(TrainerBattleParameter, params.opponentA)'])
                assert opponent in [self.p[name] for name in trainer_names], (label, opponent)
                text = self.text(self.s['gDisplayedStringBattle'])
                if HERO_NAMES[expected] in text:
                    battle_name = text
                struct_ptr = self.lib.read32(self.s['gBattleStruct'])
                if struct_ptr and portrait is None:
                    slide = self.lib.read8(struct_ptr + self.p['offsetof(struct BattleStruct, trainerSlideSpriteIds)'] + 1)
                    if slide < 64:
                        sprite = self.s['gSprites'] + slide * self.p['sizeof(struct Sprite)']
                        pic = self.lib.read16(sprite + 6)
                        x2 = self.lib.read16(sprite + self.p['offsetof(struct Sprite, x2)'])
                        if x2 >= 32768:
                            x2 -= 65536
                        if pic == expected_pic and -100 <= x2 <= 0:
                            portrait = dict(sprite_id=slide, trainer_pic=pic,
                                            capture=self.capture(label + '-battle-portrait'))
                for field, value in [('hp', 999), ('maxHP', 999), ('attack', 2500), ('spAttack', 2500),
                                     ('defense', 2000), ('spDefense', 2000), ('speed', 2000)]:
                    self.lib.write16(self.s['gBattleMons'] + self.p[f'offsetof(struct BattlePokemon, {field})'], value)
                controller = self.lib.read32(self.s['gBattlerControllerFuncs']) & ~1
                if controller in self.actions or controller in self.moves:
                    self.step(1, 64); self.step(8); self.step(1, 32); self.step(8)
                    self.press(1)
                    attacks += controller in self.moves
                else:
                    # Small increments retain the transient opponent portrait.
                    self.step(1, 2); self.step(3)
            elif started and (self.lib.read32(self.s['gMain'] + 4) & ~1) == self.s['CB2_Overworld']:
                break
            else:
                self.press(1)
        assert started and attacks > 0 and portrait and battle_name, (label, started, attacks, portrait, battle_name)
        outcome = self.lib.read8(self.s['gBattleOutcome'])
        assert outcome == 1, (label, outcome)
        for _ in range(450):
            if not self.lib.read8(self.s['sLockFieldControls']):
                break
            self.press(1)
        assert not self.lib.read8(self.s['sLockFieldControls']), ('Native scene did not end', label)
        result = dict(label=label, player_hero=hero, start_region=birth, map=mapping,
                      expected_hero=expected, observed_name=HERO_NAMES[expected], field_actor=actor,
                      field_dialogue=dialogue, field_capture=field_capture, opponent_id=opponent,
                      portrait=portrait, battle_name=battle_name, actual_attacks=attacks,
                      battle_outcome=outcome, controller_triggered=True, native_scene_completed=True)
        print('Native encounter passed:', label, flush=True)
        return result

    def run(self):
        try:
            matrices = self.matrices()
            encounters = [
                self.encounter('red-hoenn-kanto-brendan', 1, 0, 'Route22_Frlg', 3,
                               [name for name, _, _ in NATIVE_TRAINERS if 'RIVAL_ROUTE22_EARLY_' in name]),
                self.encounter('red-hoenn-kanto-leaf', 1, 0, 'CeruleanCity_Frlg', 2,
                               [name for name, _, _ in NATIVE_TRAINERS if 'RIVAL_CERULEAN_' in name]),
                self.encounter('red-hoenn-home-may', 1, 0, 'Route103', 4,
                               [name for name, _, _ in NATIVE_TRAINERS if 'MAY_ROUTE_103_' in name]),
                self.encounter('leaf-kanto-home-red', 2, 1, 'Route22_Frlg', 1,
                               [name for name, _, _ in NATIVE_TRAINERS if 'RIVAL_ROUTE22_EARLY_' in name]),
            ]
            assert digest(self.source / 'pokeemerald.gba') == self.rom_sha
            assert digest(self.source / 'pokeemerald.elf') == self.elf_sha
            return dict(kind=KIND, passed=True, preflight=False, compiled_rom=True,
                        native_validation_performed=True, rom_sha256=self.rom_sha, elf_sha256=self.elf_sha,
                        review_mode=bool(self.lib.read8(self.s['gJourneyReviewMode'])),
                        max_national=self.lib.read16(self.s['gJourneyBuildRules']),
                        perfect_trainer_ivs=bool(self.lib.read8(self.s['gJourneyBuildRules'] + 2)),
                        fixtures=dict(avatar_and_birthplace=True, canonical_player_names=True, unloaded_api_map_contexts=True,
                                      initial_party_and_progress=True, initial_map_placement=True,
                                      encounters_disabled=True, player_battle_stats_boosted=True,
                                      enemy_stats_and_outcomes_not_written=True,
                                      event_progression_not_written_after_trigger=True),
                        actual_encounters=encounters, captures=self.captures,
                        full_campaign_playthrough=False, **matrices)
        finally:
            self.lib.stop()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--library', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--preflight', action='store_true')
    options = parser.parse_args()
    options.output.mkdir(parents=True, exist_ok=True)
    report_path = options.output / (KIND + '.json')
    report_path.unlink(missing_ok=True)
    report = dict(kind=KIND, passed=False, preflight=True, compiled_rom=False,
                  native_validation_performed=False, source_prepared=(options.source / '.journey-badge-story').exists(),
                  required_native_identity_observations=684, required_native_map_observations=300,
                  required_actual_encounters=4)
    if options.library and not options.preflight:
        report = RivalNative(options).run()
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: report.get(key) for key in ['kind', 'passed', 'preflight', 'rom_sha256']}))


if __name__ == '__main__':
    main()
