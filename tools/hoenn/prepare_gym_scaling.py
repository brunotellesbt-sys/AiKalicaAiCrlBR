"""Migrate order-based gym level scaling to both regions; not free-order access."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from prepare_crossing import PIN

HOENN = ['RustboroCity_Gym','DewfordTown_Gym','MauvilleCity_Gym','LavaridgeTown_Gym_1F','LavaridgeTown_Gym_B1F',
         'PetalburgCity_Gym','FortreeCity_Gym','MossdeepCity_Gym','SootopolisCity_Gym_1F','SootopolisCity_Gym_B1F']
KANTO = ['PewterCity_Gym_Frlg','CeruleanCity_Gym_Frlg','VermilionCity_Gym_Frlg','CeladonCity_Gym_Frlg',
         'FuchsiaCity_Gym_Frlg','SaffronCity_Gym_Frlg','CinnabarIsland_Gym_Frlg','ViridianCity_Gym_Frlg']


def prepare(source, refresh_helpers=False):
    source=Path(source); marker=source/'.journey-gym-scaling'
    if marker.exists():
        report=json.loads(marker.read_text())
        for p,d in report['prepared_sha256'].items():
            if hashlib.sha256((source/p).read_bytes()).hexdigest()!=d: raise ValueError('Modified gym output: '+p)
        if refresh_helpers:
            helpers=Path(__file__).resolve().parent
            for p,name in [('src/journey_gym_scaling.c','gym_scaling.c'),('include/journey_gym_scaling.h','gym_scaling.h')]:
                raw=(helpers/name).read_bytes(); (source/p).write_bytes(raw)
                report['prepared_sha256'][p]=hashlib.sha256(raw).hexdigest()
            acquired=json.loads((source/'.source-acquired.json').read_text())
            report['input_sha256']={f'data/maps/{g["map"]}/{name}':acquired['sha256'][f'data/maps/{g["map"]}/{name}']
                                    for g in report['gyms'] for name in ['map.json','scripts.inc']}
            marker.write_text(json.dumps(report,indent=2)+'\n')
        return report
    acquired=json.loads((source/'.source-acquired.json').read_text())
    if acquired['commit']!=PIN: raise ValueError('Unexpected base')
    expected=dict(acquired['sha256'])
    for p in ['.journey-hoenn-crossing','.journey-worldsea','.journey-westsea','.journey-region-state','.journey-east-coast']:
        expected.update(json.loads((source/p).read_text())['prepared_sha256'])
    outputs, originals = {}, {}
    def stage(p,value):
        target=source/p; digest=hashlib.sha256(target.read_bytes()).hexdigest() if target.exists() else None
        if digest is not None and digest!=expected.get(p): raise ValueError('Unreviewed modification: '+p)
        originals[p]=digest; outputs[p]=value.encode()
    rows, gyms, inputs = [], [], {}
    for kanto,names in [(False,HOENN),(True,KANTO)]:
        for name in names:
            path=f'data/maps/{name}/map.json'
            data=json.loads((source/path).read_text())
            inputs[path] = acquired['sha256'][path]
            if hashlib.sha256((source/path).read_bytes()).hexdigest()!=acquired['sha256'][path]:
                raise ValueError('Modified gym map: '+name)
            scripts=(source/f'data/maps/{name}/scripts.inc').read_text()
            inputs[f'data/maps/{name}/scripts.inc'] = acquired['sha256'][f'data/maps/{name}/scripts.inc']
            trainers=list(dict.fromkeys(re.findall(r'trainerbattle_(?:single|double)\s+(TRAINER_\w+)',scripts)))
            if not trainers and not name.endswith('_B1F'): raise ValueError('Missing gym battles: '+name)
            rows.append(f'    {{{data["id"]}, {"TRUE" if kanto else "FALSE"}}},')
            gyms.append(dict(map=name,id=data['id'],kanto=kanto,trainers=trainers))
    stage('include/journey_gym_maps.h','static const struct JourneyGym sJourneyGyms[] = {\n'+'\n'.join(rows)+'\n};\n')
    helpers=Path(__file__).resolve().parent
    stage('src/journey_gym_scaling.c',(helpers/'gym_scaling.c').read_text())
    stage('include/journey_gym_scaling.h',(helpers/'gym_scaling.h').read_text())
    p='src/battle_main.c'; text=(source/p).read_text()
    anchor='CreateMon(&party[i], partyData[monIndex].species, partyData[monIndex].lvl, personalityValue, otId);'
    if text.count(anchor)!=1: raise ValueError('Unexpected modern trainer generation')
    text=text.replace('#include "global.h"','#include "global.h"\n#include "journey_gym_scaling.h"',1)
    text=text.replace(anchor,'CreateMon(&party[i], partyData[monIndex].species, JourneyGymLevel(trainer, partyData[monIndex].lvl), personalityValue, otId);')
    stage(p,text)
    for p,raw in outputs.items():
        target=source/p; target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(raw)
    report=dict(source_commit=PIN,status='gym_levels_migrated_access_and_story_still_pending',gyms=gyms,
        ace_levels=[14,21,28,35,42,48,54,60],regular_trainer_offset=2,max_party_gap=6,
        original_sha256=originals,input_sha256=inputs,prepared_sha256={p:hashlib.sha256(raw).hexdigest() for p,raw in outputs.items()},
        free_order_access_validated=False,full_story_validated=False)
    marker.write_text(json.dumps(report,indent=2)+'\n'); return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--refresh-helpers',action='store_true',help='Refresh local gym helper edits only after all existing output hashes match')
    args=parser.parse_args(); print(json.dumps(prepare(args.source,args.refresh_helpers),indent=2))
