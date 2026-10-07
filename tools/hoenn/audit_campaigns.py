#!/usr/bin/env python3
"""Record native campaign dependencies before adapting free-order gyms.

This is a source audit, not proof that either campaign is playable end to end.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

BOSSES = (
    ('kanto', 'RocketHideout_B4F_Frlg', 'TRAINER_BOSS_GIOVANNI', 'Giovanni', 'Surge → Erika (usual route)'),
    ('kanto', 'SilphCo_11F_Frlg', 'TRAINER_BOSS_GIOVANNI_2', 'Giovanni', 'Erika → Sabrina; Koga order varies'),
    ('kanto', 'ViridianCity_Gym_Frlg', 'TRAINER_LEADER_GIOVANNI', 'Giovanni', 'Eighth gym after the other seven'),
    ('hoenn', 'MtChimney', 'TRAINER_MAXIE_MT_CHIMNEY', 'Maxie', 'Wattson → Flannery'),
    ('hoenn', 'MagmaHideout_4F', 'TRAINER_MAXIE_MAGMA_HIDEOUT', 'Maxie', 'Winona → Tate & Liza'),
    ('hoenn', 'MossdeepCity_SpaceCenter_2F', 'TRAINER_MAXIE_MOSSDEEP', 'Maxie + Tabitha, alongside Steven', 'Tate & Liza → Juan'),
    ('hoenn', 'SeafloorCavern_Room9', 'TRAINER_ARCHIE', 'Archie', 'Tate & Liza → Juan'),
)


def audit(source):
    evidence = {}

    def read(path):
        raw = (source / path).read_bytes()
        evidence[path] = hashlib.sha256(raw).hexdigest()
        return raw.decode()

    bosses = []
    for region, name, trainer, boss, interval in BOSSES:
        path = f'data/maps/{name}/scripts.inc'
        script = read(path)
        matches = [dict(line=i, script=line.strip())
                   for i, line in enumerate(script.splitlines(), 1)
                   if re.search(r'\b' + trainer + r'\b', line)]
        if len(matches) != 1:
            raise ValueError(f'Expected one native boss battle: {trainer}')
        bosses.append(dict(region=region, map=name, trainer=trainer, boss=boss,
                           original_usual_interval=interval, evidence=matches[0]))

    leagues = {}
    for region, path, command in (
        ('kanto', 'data/scripts/route23.inc', 'goto_if_set'),
        ('hoenn', 'data/maps/EverGrandeCity_PokemonLeague_1F/scripts.inc', 'goto_if_unset'),
    ):
        script = read(path)
        found = sorted(set(int(x) for x in re.findall(
            rf'{command} FLAG_BADGE0([1-8])_GET', script)))
        if found != list(range(1, 9)):
            raise ValueError(f'Missing native league badge checks: {region}')
        leagues[region] = dict(path=path, required_badges=found,
                               other_region_badges_count=False,
                               validation='source guards; regional flag bank tested separately')

    flags = read('src/event_data.c')
    if 'FLAG_KANTO_BADGE01_GET + id - FLAG_BADGE01_GET' not in flags:
        raise ValueError('Missing active-region badge resolution')

    catalog = json.loads((source / '.journey-gym-scaling').read_text())
    # Keep all gym/story scripts in the audit, rather than assuming that removing
    # a badge check also removes door, NPC, puzzle or event dependencies.
    dependencies = []
    for path in sorted(catalog['input_sha256']):
        if not path.endswith('/scripts.inc'):
            continue
        script = read(path)
        references = [dict(line=i, script=line.strip())
                      for i, line in enumerate(script.splitlines(), 1)
                      if re.search(r'^\s*(?:goto_if|call_if|case|switch|map_script_2)', line)
                      and re.search(r'FLAG_|VAR_', line)]
        dependencies.append(dict(path=path, conditions=references))

    return dict(status='campaign_dependency_audit_not_complete_integration',
                original_games=['LeafGreen', 'Emerald'], bosses=bosses,
                league_guards=leagues, gym_conditions=dependencies,
                policy=dict(independent_campaigns=True, independent_leagues=True,
                            free_choice_of_gym_order=True,
                            boss_badge_thresholds=dict(kanto_before_gym=[3,4], hoenn_before_gym=[3,6,7,7]),
                            gym_door_guide_explains_team_and_location=True,
                            preserve_team_story_sequence=True,
                            viridian_leader_target='Blue'),
                full_campaign_runtime_validated=False, input_sha256=evidence)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(boss_battles=len(result['bosses']),
                          gym_scripts=len(result['gym_conditions']),
                          league_guards=result['league_guards']), indent=2))
