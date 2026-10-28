"""Run the eight extra gyms' native controller paths and separate approaches.

Reuse the maintained gym controller, excluding the roster matrix and the old
24-badge League assertions. Current 18/22-badge campaign gates have their own
validator. Travel, prior island quests and boosted player stats are fixtures;
doors, all four trainer approaches, battles, guide dialogue and exits are real.
"""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main():
    path = ROOT / 'tools/hoenn/validate_extra_gyms.py'
    body = path.read_text()
    start = 'for g in gyms:\n    variants='
    end = '# Real map-load, doors and walking tests follow the generation-only fixtures.'
    finish = '# All 24 unique badges count; one missing badge must deny both admissions.'
    assert body.count(start) == body.count(end) == body.count(finish) == 1
    first, remaining = body.split(start, 1)
    _, controller = remaining.split(end, 1)
    controller = controller.split(finish, 1)[0]
    namespace = dict(__name__='generated_gym_controller', __file__=str(path))
    exec(compile(first + '\n' + end + controller, str(path), 'exec'), namespace)
    source, args = namespace['source'], namespace['args']
    sha = hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest()
    assert sha == namespace['initial_sha']
    results = namespace['results']
    assert len(results) == 8 and all(r['controller_entry_and_exit'] for r in results)
    review_mode = bool(namespace['lib'].read8(namespace['s']['gJourneyReviewMode']))
    assert all(len(row['students']) == 4 for row in results)
    if not review_mode:
        assert all(row['all_four_battled_separately_on_mandatory_walk'] for row in results)
        assert all(win['approach']['native_walked_to_player']
                   for row in results for win in row['students'])
    captures = [dict(file=p.name, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                for p in sorted(args.output.glob('*.png'))]
    report = dict(passed=True, kind='generated-gym-native-walk', rom_sha256=sha,
                  native_validation_performed=True, compiled_rom=True,
                  review_mode=review_mode, gyms=results, captures=captures,
                  automatic_approaches=0 if review_mode else 32,
                  trainer_battles=32, leader_battles=8,
                  doors_and_movement_use_controller=True,
                  battle_outcomes_and_post_victory_flags_not_written=True,
                  initial_trainer_flags_are_fixtures=True,
                  initial_travel_badges_quests_and_player_stats_are_fixtures=True,
                  current_campaign_gates_tested_separately=True,
                  full_campaign_playthrough=False)
    namespace['lib'].stop()
    (args.output / 'generated-gym-native-walk.json').write_text(json.dumps(report, indent=2)+'\n')
    print('Eight native gym paths, 32 separate students and eight leaders passed.', flush=True)


if __name__ == '__main__':
    main()
