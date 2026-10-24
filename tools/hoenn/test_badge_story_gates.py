"""Exercise emitted C gates and actual checkpoint script paths on host fixtures.

These tests are not emulator proof. Native controller walks are recorded by
validate_badge_story_gates.py on each final ROM.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

from badge_story_gates import CHAPTER, EVER_GRANDE, EXTRA, GALACTIC, GYMS, INDIGO, PATHS, ROUTE, repair

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / 'fixtures/badge_story_gates'


class RecordingLayer:
    def __init__(self):
        self.source = FIXTURE
        self.expected = json.loads((FIXTURE / 'source-manifest.json').read_text())['sha256']
        self.outputs = {}

    def stage(self, path, value):
        self.outputs[path] = value.encode() if isinstance(value, str) else value


def function(text, name):
    match = re.search(r'^(?:bool32|u32|void) ' + re.escape(name) + r'\([^)]*\)\s*\{', text, re.M)
    assert match, name
    depth = 1
    end = match.end()
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[match.start():end]


def compiled_contract(output):
    galactic, extra = output[GALACTIC].decode(), output[EXTRA].decode()
    grunt = re.search(r'if\(script==gruntScripts\[i\]\)return ([^;]+);', galactic)[1]
    emitted = '\n'.join([function(extra, 'JourneyTotalBadgeCount'),
                          function(galactic, 'JourneyGalacticLeagueReady'),
                          function(galactic, 'JourneyGalacticAvailable'),
                          function(extra, 'JourneyExtraLeagueBadges'),
                          'bool32 GruntVisible(u32 state) { return ' + grunt + '; }'])
    fixture = '''#include <stdint.h>
#include <stdio.h>
typedef uint32_t u32, bool32;
typedef uint16_t u16;
#define TRUE 1
#define FALSE 0
#define VAR_JOURNEY_GALACTIC_STATE 0x40FE
u32 kanto, hoenn, extras, won;
u16 gSpecialVar_Result;
u32 JourneyGymBadgeCount(bool32 k) { return k ? kanto : hoenn; }
u32 JourneyExtraBadgeCount(void) { return extras; }
bool32 JourneyQualifierWon(void) { return won; }
bool32 JourneyCrossoverComplete(void) { return FALSE; }
u16 VarGet(u16 var) { (void)var; return 0; }
u32 JourneyPendingCampaignEvent(bool32 k) { (void)k; return 1; }
''' + emitted + '''
int main(void) {
 unsigned cases=0, phases=0;
 for(kanto=0;kanto<=8;kanto++)for(hoenn=0;hoenn<=8;hoenn++)for(extras=0;extras<=8;extras++)for(won=0;won<=1;won++) {
  unsigned total=kanto+hoenn+extras, allowed=total>=18 && won;
  if(JourneyGalacticLeagueReady()!=allowed) return 1;
  JourneyExtraLeagueBadges(); if(gSpecialVar_Result!=allowed) return 2;
  JourneyGalacticAvailable(); if(gSpecialVar_Result!=(total>=22)) return 3;
  for(unsigned state=0;state<=7;state++) {
   if(GruntVisible(state)!=(total>=22 && state<7)) return 4;
   phases++;
  }
  cases++;
 }
 printf("%u badge distributions and %u grunt phases passed\\n",cases,phases);
 return 0;
}
'''
    with tempfile.TemporaryDirectory(prefix='badge-gates-c-') as temporary:
        source = Path(temporary) / 'gates.c'
        binary = Path(temporary) / 'gates'
        source.write_text(fixture)
        subprocess.run(['cc', '-std=c99', '-O2', '-Wall', '-Wextra', '-Werror',
                        '-fsanitize=undefined', '-fno-sanitize-recover=all', str(source), '-o', str(binary)],
                       capture_output=True, text=True, check=True)
        return subprocess.run([str(binary)], capture_output=True, text=True)


def walk_script(text, entry, *, qualified, badges=0, checkpoint=1, entered=False):
    """Evaluate actual assembly control flow; ignore only waits and presentation."""
    lines = text.splitlines()
    labels = {match[1]: i + 1 for i, line in enumerate(lines)
              if (match := re.match(r'^([A-Za-z_][A-Za-z_0-9]*)::?$', line))}
    variables = {'VAR_RESULT': 0, 'VAR_TEMP_0': 9, 'VAR_TEMP_1': checkpoint,
                 'VAR_MAP_SCENE_ROUTE23': 0, 'VAR_0x8009': checkpoint}
    flags = {'FLAG_ENTERED_ELITE_FOUR'} if entered else set()
    flags.update('FLAG_BADGE0' + str(i + 1) + '_GET' for i in range(8) if badges & (1 << i))
    flags.update('FLAG_KANTO_BADGE0' + str(i + 1) + '_GET' for i in range(8) if badges & (1 << i))
    pc, stack, movements, messages, object_positions = labels[entry], [], [], [], []
    release = None

    def value(token):
        return variables.get(token, {'TRUE': 1, 'FALSE': 0}.get(token, int(token) if token.isdecimal() else 0))

    for _ in range(500):
        line = lines[pc].strip(); pc += 1
        if not line or line.startswith(('@', '.', '#')) or re.fullmatch(r'\w+::?', line):
            continue
        opcode, _, rest = line.partition(' ')
        args = [arg.strip() for arg in rest.split(',')]
        if opcode == 'special':
            assert args[0] in {'JourneyKantoLeaguePermission', 'JourneyHoennLeaguePermission'}, line
            variables['VAR_RESULT'] = int(qualified)
        elif opcode == 'goto':
            pc = labels[args[0]]
        elif opcode in {'call', 'return'}:
            if opcode == 'return':
                if not stack:
                    break
                pc = stack.pop()
            else:
                stack.append(pc); pc = labels[args[0]]
        elif opcode.startswith(('goto_if_', 'call_if_')):
            condition = opcode.split('_if_', 1)[1]
            if condition in {'set', 'unset'}:
                take = (args[0] in flags) == (condition == 'set')
            else:
                left, right = value(args[0]), value(args[1])
                take = {'eq': left == right, 'ne': left != right,
                        'ge': left >= right, 'le': left <= right}[condition]
            if take:
                if opcode.startswith('call_'):
                    stack.append(pc)
                pc = labels[args[-1]]
        elif opcode == 'switch':
            variables['_switch'] = value(args[0])
        elif opcode == 'case':
            if value(args[0]) == variables['_switch']:
                pc = labels[args[1]]
        elif opcode in {'setvar', 'copyvar'}:
            variables[args[0]] = value(args[1])
        elif opcode in {'setflag', 'clearflag'}:
            if opcode == 'setflag': flags.add(args[0])
            else: flags.discard(args[0])
        elif opcode == 'applymovement':
            movements.append(args)
        elif opcode == 'setobjectxyperm':
            object_positions.append(args)
        elif opcode in {'message', 'msgbox'}:
            messages.append(args[0])
        elif opcode == 'getplayerxy':
            variables[args[0]], variables[args[1]] = 9, 3
        elif opcode in {'release', 'releaseall'}:
            release = opcode
        elif opcode == 'end':
            break
        elif opcode not in {'lock', 'lockall', 'faceplayer', 'setrespawn', 'waitmessage', 'delay',
                            'waitmovement', 'waitfanfare', 'waitbuttonpress', 'closemessage', 'playfanfare',
                            'playse', 'waitse', 'textcolor', 'copyobjectxytoperm'}:
            raise AssertionError(('Unsupported control-flow opcode', line))
    else:
        raise AssertionError(('Script did not terminate', entry))
    return dict(variables=variables, flags=flags, movements=movements, messages=messages,
                positions=object_positions, release=release)


class BadgeStoryGates(unittest.TestCase):
    def setUp(self):
        self.layer = RecordingLayer()
        self.report = repair(self.layer)
        self.output = self.layer.outputs

    def test_reviewed_inputs_and_emitted_c_cover_mixed_badge_distributions(self):
        for path, expected in self.layer.expected.items():
            self.assertEqual(hashlib.sha256((FIXTURE / path).read_bytes()).hexdigest(), expected)
        manifest = json.loads((FIXTURE / 'source-manifest.json').read_text())
        for path, original in manifest['parent_sha256'].items():
            self.assertEqual(hashlib.sha256((FIXTURE / path).read_bytes() + b'\n').hexdigest(), original)
        result = compiled_contract(self.output)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('1458 badge distributions and 11664 grunt phases passed', result.stdout)

    def test_regression_controls_reject_old_24_and_regional_galactic_rules(self):
        for before, after in [
            ('JourneyTotalBadgeCount() >= 18', 'JourneyTotalBadgeCount() == 24'),
            ('JourneyTotalBadgeCount() >= 22', 'JourneyGymBadgeCount(TRUE)==8 && JourneyGymBadgeCount(FALSE)==8'),
        ]:
            mutant = dict(self.output)
            mutant[GALACTIC] = mutant[GALACTIC].replace(before.encode(), after.encode(), 1)
            self.assertNotEqual(compiled_contract(mutant).returncode, 0)

    def test_all_eight_physical_checkpoint_trigger_and_dialogue_paths(self):
        route = self.output[ROUTE].decode()
        for checkpoint in range(1, 9):
            for entry in ['Route23_EventScript_BadgeGuard', 'Route23_EventScript_BadgeGuardTrigger']:
                state = walk_script(route, entry, qualified=True, badges=0b11, checkpoint=checkpoint)
                self.assertEqual(state['variables']['VAR_MAP_SCENE_ROUTE23'], 8)
                self.assertEqual(state['messages'], ['JourneyBadgeStory_Route23QualifiedText'])
                self.assertNotIn(['LOCALID_PLAYER', 'Route23_Movement_WalkDown'], state['movements'])
                self.assertEqual(state['release'], 'releaseall' if entry.endswith('Trigger') else 'release')
        self.assertEqual(walk_script(route, 'Route22_NorthEntrance_EventScript_BadgeGuard',
                                    qualified=True)['variables']['VAR_MAP_SCENE_ROUTE23'], 8)
        denied = walk_script(route, 'Route23_EventScript_BadgeGuardTrigger',
                             qualified=False, badges=0b11, checkpoint=3)
        self.assertIn(['LOCALID_PLAYER', 'Route23_Movement_WalkDown'], denied['movements'])
        # The previous script demonstrably rejected this same mixed-badge winner.
        prior = (FIXTURE / ROUTE).read_text()
        self.assertIn(['LOCALID_PLAYER', 'Route23_Movement_WalkDown'],
                      walk_script(prior, 'Route23_EventScript_BadgeGuardTrigger',
                                  qualified=True, badges=0b11, checkpoint=3)['movements'])

    def test_both_actual_league_scripts_admit_winner_with_incomplete_regional_bank(self):
        shared = self.output[CHAPTER].decode()
        indigo = self.output[INDIGO].decode() + '\n' + shared
        approved = walk_script(indigo, 'IndigoPlateau_Journey_CheckBadges', qualified=True, badges=0b11)
        self.assertEqual(approved['variables']['VAR_RESULT'], 1)
        old = walk_script((FIXTURE / INDIGO).read_text(), 'IndigoPlateau_Journey_CheckBadges', qualified=True, badges=0b11)
        self.assertEqual(old['variables']['VAR_RESULT'], 0)
        for won in [False, True]:
            ever = walk_script(self.output[EVER_GRANDE].decode() + '\n' + shared,
                               'EverGrandeCity_PokemonLeague_1F_EventScript_DoorGuard',
                               qualified=won, badges=0b11)
            self.assertEqual('FLAG_ENTERED_ELITE_FOUR' in ever['flags'], won)
            self.assertEqual(any('EverGrandeCity_PokemonLeague_1F_Movement_LeftGuardOutOfWay' in row
                                 for row in ever['movements']), won)
            if not won:
                self.assertEqual(ever['messages'], ['JourneyBadgeStory_LeagueRequiredText'])

    def test_chapter_prerequisites_capture_locks_and_all_gyms_remain(self):
        before = (FIXTURE / GALACTIC).read_text()
        after = self.output[GALACTIC].decode()
        for name in ['JourneyGalacticCaptureLocked', 'JourneyGalacticNoCatch',
                     'JourneyGalacticGruntsCleared', 'JourneyGalacticOtherMissions',
                     'JourneyGalacticCellState']:
            self.assertEqual(function(before, name), function(after, name))
        chapter = self.output[CHAPTER].decode()
        gate = chapter.split('JourneyGalactic_Gate::', 1)[1].split('JourneyGalactic_GateDefeated::', 1)[0]
        self.assertIn('special JourneyGalacticAvailable', gate)
        self.assertIn('callnative JourneyCrossoverMissing', gate)
        denied = walk_script(chapter, 'JourneyGalactic_LeagueDenied', qualified=False)
        self.assertEqual(denied['messages'], ['JourneyBadgeStory_LeagueRequiredText'])
        old_gyms = (FIXTURE / GYMS).read_text()
        new_gyms = self.output[GYMS].decode()
        self.assertEqual(re.findall(r'^\s*(?:trainerbattle_single|setflag FLAG_JOURNEY_BADGE_).*$', old_gyms, re.M),
                         re.findall(r'^\s*(?:trainerbattle_single|setflag FLAG_JOURNEY_BADGE_).*$', new_gyms, re.M))
        self.assertNotIn('24-BADGE', new_gyms)
        self.assertNotIn('Both LEAGUES can now admit you', chapter)

    def test_composes_with_staged_visibility_and_is_idempotent(self):
        original = self.layer.outputs[GALACTIC].decode()
        augmented = original.replace(' const u8 *script=o->script;',
                                     ' const u8 *script=o->script;\n if(!JourneyQualifierFieldObjectVisible(o,group,num))return FALSE;')
        self.layer.outputs[GALACTIC] = augmented.encode()
        repair(self.layer)
        self.assertIn('if(!JourneyQualifierFieldObjectVisible(o,group,num))return FALSE;', self.layer.outputs[GALACTIC].decode())
        expected = dict(self.layer.outputs)
        repair(self.layer)
        self.assertEqual(self.layer.outputs, expected)
        self.assertEqual(set(expected), set(PATHS))


if __name__ == '__main__':
    unittest.main()
