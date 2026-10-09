"""Open Sky Pillar while keeping its awakening in the original story sequence."""
import argparse
import hashlib
import json
from pathlib import Path
from prepare_crossing import PIN
from prepare_family import LAYERS_BEFORE

def prepare(source):
    source = Path(source)
    marker = source / '.journey-sky-pillar-access'
    if marker.exists():
        report = json.loads(marker.read_text())
        for path, digest in report['prepared_sha256'].items():
            if hashlib.sha256((source / path).read_bytes()).hexdigest() != digest:
                raise ValueError('Modified Sky Pillar access output: ' + path)
        return report
    acquired = json.loads((source / '.source-acquired.json').read_text())
    if acquired['commit'] != PIN: raise ValueError('Unexpected source revision')
    expected = dict(acquired['sha256'])
    for layer in LAYERS_BEFORE + ['family', 'travel-rules', 'birth', 'wild', 'habitats',
                                 'sanctuaries', 'ecology', 'abilities', 'mega-art', 'story-aftermath',
                                 'league-access', 'league-completion', 'league-history', 'league-display',
                                 'family-postgame', 'pwt', 'frontier-travel', 'story-puzzles', 'aqua-episodes',
                                 'seafloor-access', 'water-continue', 'cave-access']:
        expected.update(json.loads((source / ('.journey-' + layer)).read_text())['prepared_sha256'])
    def checked(path):
        raw = (source / path).read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected[path]:
            raise ValueError('Unreviewed Sky Pillar access input: ' + path)
        return raw
    outputs = {}
    path = 'data/maps/SkyPillar_Outside/scripts.inc'
    text = checked(path).decode()
    old = '\tcall_if_set FLAG_WALLACE_GOES_TO_SKY_PILLAR, SkyPillar_Outside_EventScript_OpenDoor\n'
    if text.count(old) != 1: raise ValueError('Ambiguous Sky Pillar door')
    outputs[path] = text.replace(old, '\tcall SkyPillar_Outside_EventScript_OpenDoor\n').encode()
    path = 'src/journey_campaign_gates.c'
    text = checked(path).decode()
    anchor = 'void JourneySilphCoPermission(void)\n'
    if text.count(anchor) != 1: raise ValueError('Ambiguous permission insertion')
    permission = '''bool32 JourneyCanAwakenRayquaza(void)
{
    // Exploring the tower must not start the crisis before Archie and the
    // original legendary clash in Sootopolis. Keep every prior mission.
    return JourneyCanStartArchieAlliance()
        && RegionalFlag(FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN)
        && RegionalFlag(FLAG_SYS_WEATHER_CTRL)
        && VarGet(VAR_SOOTOPOLIS_CITY_STATE) >= 2
        && VarGet(VAR_SOOTOPOLIS_CITY_STATE) <= 4
        && VarGet(VAR_SKY_PILLAR_STATE) == 0;
}

void JourneyRayquazaAwakeningPermission(void)
{
    gSpecialVar_Result = JourneyCanAwakenRayquaza();
}

'''
    outputs[path] = text.replace(anchor, permission + anchor).encode()
    path = 'data/maps/SkyPillar_Top/scripts.inc'
    text = checked(path).decode()
    anchor = 'SkyPillar_Top_EventScript_AwakenRayquaza::\n\tlockall\n'
    if text.count(anchor) != 1: raise ValueError('Ambiguous awakening script')
    text = text.replace(anchor, anchor + '\tcallnative JourneyRayquazaAwakeningPermission\n\tgoto_if_eq VAR_RESULT, FALSE, JourneySkyPillar_AwakeningNotReady\n')
    text += '''
JourneySkyPillar_AwakeningNotReady::
\tmsgbox JourneySkyPillar_SleepingText, MSGBOX_DEFAULT
\treleaseall
\tend

JourneySkyPillar_SleepingText:
\t.string "RAYQUAZA is sleeping peacefully.\\p"
\t.string "Return if a crisis threatens\\n"
\t.string "SOOTOPOLIS and HOENN.$"
'''
    outputs[path] = text.encode()
    preserved = {}
    for other in ['data/maps/SeafloorCavern_Room9/scripts.inc', 'data/maps/SootopolisCity/scripts.inc',
                  'data/maps/SkyPillar_Outside/map.json', 'data/maps/SkyPillar_Top/map.json',
                  'data/maps/SkyPillar_1F/scripts.inc', 'data/maps/SkyPillar_2F/scripts.inc',
                  'data/maps/SkyPillar_3F/scripts.inc', 'data/maps/SkyPillar_4F/scripts.inc',
                  'data/maps/SkyPillar_5F/scripts.inc', 'data/maps/CaveOfOrigin_B1F/scripts.inc',
                  'src/journey_special.c', 'src/journey_gym_scaling.c', 'src/field_player_avatar.c',
                  'include/constants/flags.h']:
        checked(other); preserved[other] = expected[other]
    report = dict(status='sky_pillar_free_access_candidate', source_commit=PIN,
                  tower_door_open_before_wallace=True,
                  awakening_requires_archie_silph_space_center_and_regional_missions=True,
                  awakening_requires_native_sootopolis_clash=True,
                  original_awakening_body_and_peace_scene_preserved=True,
                  capture_still_requires_sixteen_badges=True,
                  native_clean_and_cracked_layout_scripts_preserved=True,
                  new_flags_allocated=False, full_campaign_validated=False,
                  original_sha256={p: expected[p] for p in outputs}, preserved_native_sha256=preserved,
                  prepared_sha256={p: hashlib.sha256(v).hexdigest() for p, v in outputs.items()})
    for path, output in outputs.items(): (source / path).write_bytes(output)
    marker.write_text(json.dumps(report, indent=2) + '\n')
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source), indent=2))
