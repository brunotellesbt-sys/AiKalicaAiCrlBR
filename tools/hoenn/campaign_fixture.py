"""Declared completed-story fixture for isolated League tests, not a playthrough."""
import json,re,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]


def complete_campaign(source,native):
    source=Path(source)
    quests=json.loads((source/'.journey-mandatory-native-missions').read_text())['quests']
    stories=json.loads((source/'.journey-team-stories').read_text())
    flags={'FLAG_HIDE_CELADON_ROCKETS','FLAG_HIDE_SAFFRON_ROCKETS','FLAG_DEFEATED_EVIL_TEAM_MT_CHIMNEY',
           'FLAG_GROUDON_AWAKENED_MAGMA_HIDEOUT','FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN','FLAG_TEAM_AQUA_ESCAPED_IN_SUBMARINE'}
    trainers={'TRAINER_SHELLY_WEATHER_INSTITUTE','TRAINER_MATT'}
    variables={'VAR_MOSSDEEP_SPACE_CENTER_STATE':3,'VAR_WEATHER_INSTITUTE_STATE':1}
    for q in quests:
        flags.update(q['flags']);trainers.update(q['trainers']);variables.update(dict(q['variables']))
    names=sorted(flags|trainers|variables.keys()|{'FLAG_SYS_WEATHER_CTRL'})
    with tempfile.TemporaryDirectory(dir='/tmp') as temporary:
        p=Path(temporary)
        (p/'probe.c').write_text('#include "global.h"\n#include "constants/flags.h"\n#include "constants/vars.h"\n#include "constants/opponents.h"\nconst u32 probe[]={'+','.join(names)+'};\n')
        subprocess.run([str(ROOT/'.local/arm-gcc/usr/bin/arm-none-eabi-gcc'),'-S','-iquote',str(source/'include'),'-mabi=apcs-gnu',str(p/'probe.c'),'-o',str(p/'probe.s')],check=True)
        ids=dict(zip(names,map(int,re.findall(r'\.word\s+(\d+)',(p/'probe.s').read_text()))))
    for name in flags:native('FlagSet',ids[name])
    for name in trainers:native('FlagSet',0x500+ids[name])
    for t in stories['trainers']:native('FlagSet',0x500+t['id'])
    for name,value in variables.items():native('VarSet',ids[name],value)
    native('FlagClear',ids['FLAG_SYS_WEATHER_CTRL'])
    native('VarSet',0x40FE,7);native('VarSet',0x40FF,4095)
    assert native('JourneyPendingCampaignEvent',1)==0
    assert native('JourneyPendingCampaignEvent',0)==0
    return dict(earlier_missions_seeded=True,galactic_and_crossover_completion_seeded=True,
                full_campaign_playthrough=False)
