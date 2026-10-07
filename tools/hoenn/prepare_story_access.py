"""Connect the first badge reward and the Magma Emblem quest to free-order gyms."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from prepare_crossing import PIN
from prepare_free_access import LAYERS
from prepare_gym_scaling import HOENN, KANTO


def prepare(source):
    source = Path(source)
    marker = source / '.journey-story-access'
    if marker.exists():
        report = json.loads(marker.read_text())
        for path, digest in report['prepared_sha256'].items():
            assert hashlib.sha256((source / path).read_bytes()).hexdigest() == digest, path
        return report
    acquired = json.loads((source / '.source-acquired.json').read_text())
    assert acquired['commit'] == PIN
    expected = dict(acquired['sha256'])
    for layer in LAYERS + ['free-access', 'blue-gym', 'road-access', 'mach-bike', 'yellow-stairs']:
        expected.update(json.loads((source / f'.journey-{layer}').read_text())['prepared_sha256'])
    inputs, originals, outputs = {}, {}, {}

    def read(path):
        if path in outputs:
            return outputs[path]
        raw = (source / path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected[path], path
        if path in acquired['sha256']:
            inputs[path] = acquired['sha256'][path]
        return raw

    def stage(path, body):
        if path not in originals:
            originals[path] = hashlib.sha256(read(path)).hexdigest()
        outputs[path] = body.encode()

    gyms = []
    for name in HOENN + KANTO:
        path = f'data/maps/{name}/scripts.inc'
        body = read(path).decode()
        matches = list(re.finditer(r'^\tsetflag FLAG_BADGE(\d+)_GET\n', body, re.M))
        if not matches:
            continue  # Basement floors without a leader.
        assert len(matches) == 1, name
        badge = int(matches[0][1])
        victory_label = re.findall(r'^(\w+)::?$', body[:matches[0].start()], re.M)[-1]
        body = body[:matches[0].end()] + '\tcall Journey_FirstBadgeReward\n' + body[matches[0].end():]
        # trainerbattle locks/faces the player and branches to the victory
        # script on a win. On revisits it falls through here, allowing a retry
        # without altering rematches, TM rewards or post-battle event chains.
        if name == 'PetalburgCity_Gym':
            retry_label = 'PetalburgCity_Gym_EventScript_Norman'
            anchor = 'PetalburgCity_Gym_EventScript_Norman::\n\tvsseeker_rematchid TRAINER_NORMAN_1\n\tlock\n\tfaceplayer\n'
            assert body.count(anchor) == 1
            body = body.replace(anchor, anchor + '\tcall Journey_FirstBadgeReward\n')
        else:
            battle = re.search(r'^\ttrainerbattle_(?:single|double) [^\n]+\n', body, re.M)
            assert battle, name
            retry_label = re.findall(r'^(\w+)::?$', body[:battle.start()], re.M)[-1]
            body, count = re.subn(r'(^\ttrainerbattle_(?:single|double) [^\n]+\n)',
                                 r'\1\tcall Journey_FirstBadgeReward\n', body, count=1, flags=re.M)
            assert count == 1, name
        stage(path, body)
        gyms.append(dict(map=name, badge=badge, kanto=name in KANTO,
                         victory_label=victory_label, retry_label=retry_label))
    assert len(gyms) == 16
    path = 'src/journey_campaign_gates.c'
    stage(path, read(path).decode() + '''
void JourneyFirstBadgeRewardPermission(void)
{
    gSpecialVar_Result = JourneyGymBadgeCount(TRUE) > 0
        || JourneyGymBadgeCount(FALSE) > 0;
}
''')
    path = 'data/specials.inc'
    stage(path, read(path).decode() + '\tdef_special JourneyFirstBadgeRewardPermission\n')
    path = 'data/scripts/journey_campaign_gates.inc'
    body = read(path).decode()
    old = '\t.string "Help inside MAGMA HIDEOUT!$"'
    assert body.count(old) == 1
    body = body.replace(old, '''\t.string "Help inside MAGMA HIDEOUT!\\p"
\t.string "If the entrance is closed,\\n"
\t.string "visit MT. PYRE on ROUTE 122.\\p"
\t.string "The elders there can give you\\n"
\t.string "the MAGMA EMBLEM to open it!$"''')
    stage(path, body + '\n' + Path(__file__).with_name('first_badge_reward.inc').read_text())
    path = 'data/maps/LavenderTown_VolunteerPokemonHouse_Frlg/scripts.inc'
    body = read(path).decode()
    anchor = '\tgoto_if_set FLAG_GOT_POKE_FLUTE, LavenderTown_VolunteerPokemonHouse_EventScript_AlreadyHavePokeFlute\n'
    assert body.count(anchor) == 1
    body = body.replace(anchor, anchor + '''\tspecial JourneyFirstBadgeRewardPermission
\tgoto_if_eq VAR_RESULT, FALSE, Journey_FujiNeedsFirstBadge
''')
    stage(path, body + '''
Journey_FujiNeedsFirstBadge::
\tmsgbox Journey_FujiFirstBadgeText, MSGBOX_DEFAULT
\trelease
\tend
''')
    for path, raw in outputs.items():
        (source / path).write_bytes(raw)
    report = dict(status='first_badge_and_magma_quest_access_candidate', source_commit=PIN,
                  gyms=gyms, first_badge_region='either', reward='ITEM_POKE_FLUTE',
                  shared_receipt_flag='FLAG_GOT_POKE_FLUTE', bag_full_retry=True,
                  mr_fuji_rescue_preserved=True, snorlax_encounters_unchanged=True,
                  magma_emblem_quest_preserved=True, full_story_validated=False,
                  input_sha256=inputs, original_sha256=originals,
                  prepared_sha256={p: hashlib.sha256(v).hexdigest() for p, v in outputs.items()})
    marker.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source), indent=2))
