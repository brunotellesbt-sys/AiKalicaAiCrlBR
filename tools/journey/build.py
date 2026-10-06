#!/usr/bin/env python3
"""Build the journey overlay and export the ROM with the existing terrestrial HM modification."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from prepare import COMMIT, FILES, ROOT, prepare
sys.path.insert(0, str(ROOT/'tools/rom_hacks'))
from remove_hm_walls import BASE, REFERENCE, bps, sha, transform


def export(source, nm, output):
    original=(ROOT/'Pokemon - Leaf Green Version (U) (V1.1).gba').read_bytes()
    reference=json.loads(REFERENCE.read_text())
    if sha(original)!=reference['source']['baseline_sha256']:
        raise ValueError('Original ROM does not match LeafGreen USA v1.1')
    built=(source/'pokeleafgreen_rev1.gba').read_bytes()
    symbols={parts[2]:int(parts[0],16) for line in subprocess.check_output([str(nm),str(source/'pokeleafgreen_rev1.elf')],text=True).splitlines() if len(parts:=line.split())==3}
    groups=json.loads((source/'data/maps/map_groups.json').read_text())
    layouts=json.loads((source/'data/layouts/layouts.json').read_text())['layouts']
    dynamic=copy.deepcopy(reference)
    dynamic['source']['baseline_sha256']=sha(built)
    dynamic['source']['baseline_sha1']=hashlib.sha1(built).hexdigest()
    dynamic['symbols']={name:symbols[name] for name in reference['symbols']}
    dynamic['debug_symbols']={name:symbols[name] for name in reference['debug_symbols']}
    dynamic['groups']=[groups[group] for group in groups['group_order']]
    dynamic['layouts']=[layout.get('name','UNUSED').removesuffix('_Layout') for layout in layouts]
    for table in dynamic['attribute_tables']:table['address']=symbols[table['symbol']]
    result,hm_report=transform(built,dynamic)
    output.mkdir(parents=True,exist_ok=True)
    (output/'LeafGreen-Choose-Starting-City.gba').write_bytes(result)
    patch=bps(original,result)
    (output/'LeafGreen-Choose-Starting-City.bps').write_bytes(patch)
    homes=json.loads((source/'.journey-prepared').read_text())
    manifest={'wild_world':json.loads((source/'.wild-world-prepared').read_text()),'open_world':json.loads((source/'.open-world-prepared').read_text()),'source_commit':COMMIT,'original_sha256':sha(original),'intermediate_sha256':sha(built),'target_sha256':sha(result),'patch_sha256':sha(patch),'size':len(result),'terrestrial_hm_changes':hm_report,'homes':homes['homes'],'excluded':homes['excluded'],'overlay_hashes':{p.name:sha(p.read_bytes()) for p in sorted(FILES.iterdir()) if p.is_file() and p.suffix in ('.py','.json','.c','.h','.inc','.s')}}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    needed=['gMapGroups','gStringVar4','gSpecials','CreateNPCTrainerParty','gEnemyParty','gBattleTypeFlags','OpenWorld_FirstBadgeReward','OpenWorld_BadgeCount','OpenWorld_TrainerPic','GetObjectEventGraphicsInfo','gObjectEventGraphicsInfo_Blue','gObjectEventGraphicsInfo_RedNormal','gObjectEventGraphicsInfo_GreenNormal','gTrainers','CB2_NewGame','gMain','gSaveBlock1Ptr','gSaveBlock2Ptr','gObjectEvents','gPlayerAvatar','gMapHeader','sGlobalScriptContext','sGlobalScriptContextStatus','sLockFieldControls','gScriptCmdTable','gScriptCmdTableEnd','gSpecialVar_Result','gSpecialVar_LastTalked','gSpecialVar_0x8004','gSpecialVar_0x8005','gSpecialVar_0x8006','EventScript_ChooseDestFromOneIsland','EventScript_ChooseDestFromTwoIsland','EventScript_ChooseDestFromIsland','VermilionCity_EventScript_FerrySailor','VermilionCity_EventScript_CheckTicket','gPlayerPartyCount','gPlayerParty','JourneyChooseHome','Journey_ChooseCity','Journey_Oak','Journey_Family','JourneyGiveStarter','JourneyGiveGift','sJourneyHomes','sMultichoiceLists','sJourneyCities','sJourneyStarters']
    needed += [t['victory_script'] for t in manifest['open_world']['trainers'] if t['leader']]
    needed += ['gRngValue','WildWorld_Mean','WildWorld_Level','WildWorld_Species','CreateScriptedWildMon','CreateRoamerMonInstance','CreateInitialRoamerMon','GetMonData2','SetMonData','gWildMonHeaders','TryGenerateWildMon','GenerateFishingEncounter']
    needed += ['LavenderTown_VolunteerPokemonHouse_EventScript_MrFuji']
    debug={'attribute_tables':dynamic['attribute_tables'],'symbols':{name:symbols[name] for name in needed},'groups':dynamic['groups'],'homes':homes['homes'],'map_symbols':{name:symbols[name] for names in dynamic['groups'] for name in names},'vars':{'city':0x40CB,'home':0x40CC,'gifts':0x40CD,'stage':0x40CE},'flags':{'hide_visitor':0x8E0,'starter':0x8E1,'early_ferry':0x8E3},'specials':{name:index for index,name in enumerate(re.findall(r'^\s*def_special\s+(\w+)',(source/'data/specials.inc').read_text(),re.M))}}
    (output/'debug-reference.json').write_text(json.dumps(debug,indent=2)+'\n')
    print(json.dumps({'target_sha256':sha(result),'houses':len(homes['homes']),'size':len(result),'bps_bytes':len(patch)},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True,help='Pinned source checkout, with agbcc installed')
    p.add_argument('--nm',type=Path,default=Path('arm-none-eabi-nm'))
    p.add_argument('--output',type=Path,default=ROOT/'mods/choose-starting-city')
    p.add_argument('--export-only',action='store_true')
    p.add_argument('--jobs',type=int,default=4)
    args=p.parse_args();source=args.source.resolve()
    if not (source/'.journey-prepared').exists():prepare(source)
    if not args.export_only:
        subprocess.run(['make','-j'+str(args.jobs),'leafgreen_rev1'],cwd=source,check=True)
    export(source,args.nm,args.output)
