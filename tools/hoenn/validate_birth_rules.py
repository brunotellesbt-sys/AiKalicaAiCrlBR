"""Native bike receipts, cross-region starters and island departure checks.

Each scenario has its own mGBA process. Script entry fixtures shorten travel;
menus, gifts and Birch's starter battle execute native game code.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
ROOT = Path(__file__).resolve().parents[2]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--source', type=Path, required=True)
p.add_argument('--library', type=Path, required=True)
p.add_argument('--output', type=Path, default=ROOT / 'mods/hoenn/integration-validation')
p.add_argument('--scenario', choices=['bike-kanto', 'bike-hoenn', 'oak', 'birch', 'boat'])
options = p.parse_args()
if options.scenario is None:
    checks = []
    with tempfile.TemporaryDirectory(prefix='birth-rules-', dir='/tmp') as directory:
        for scenario in ['bike-kanto', 'bike-hoenn', 'oak', 'birch', 'boat']:
            out = Path(directory) / scenario
            child = subprocess.run([sys.executable, __file__, '--source', str(options.source.resolve()),
                '--library', str(options.library.resolve()), '--output', str(out), '--scenario', scenario], capture_output=True, text=True)
            assert child.returncode == 0, child.stdout + child.stderr
            checks.append(json.loads((out / 'birth-rules.json').read_text()))
            options.output.mkdir(parents=True, exist_ok=True)
            for pic in out.glob('birth-*.png'): (options.output / pic.name).write_bytes(pic.read_bytes())
            print('Native birth rule passed:', scenario, flush=True)
    (options.output / 'birth-rules.json').write_text(json.dumps(dict(passed=True, checks=checks,
        rom_sha256=hashlib.sha256((options.source/'pokeemerald.gba').read_bytes()).hexdigest(), full_story_validated=False), indent=2)+'\n')
    sys.exit(0)
scenario = options.scenario
sys.argv = [sys.argv[0], '--source', str(options.source), '--library', str(options.library), '--output', str(options.output), '--water-hms', '--westsea']
common = (ROOT/'tools/hoenn/validate_crossing.py').read_text().split('\nstep(900)\n')[0]
exec(compile(common, str(ROOT/'tools/hoenn/validate_crossing.py'), 'exec'))
def press(key=1, pause=30): step(1,key); step(pause)
def task(name):
    return any(lib.read8(s['gTasks']+i*40+4) and lib.read32(s['gTasks']+i*40)&~1 == s[name] for i in range(16))
def until(predicate, limit=180):
    for _ in range(limit):
        if predicate(): return
        press(1,40)
    picture('birth-'+scenario+'-failure')
    raise AssertionError(('Dialogue timeout', scenario, location(), position()))
def event(label, talked=1):
    lib.write16(s['gSpecialVar_LastTalked'],talked)
    script(b'\x05'+struct.pack('<I',s[label]),45)
def finish(): until(lambda: not lib.read8(s['sLockFieldControls']))
def quantity(item): return native('CountTotalItemQuantityInBag', item)
def var(number): return native('VarGet',number)
step(900)
save2=lib.read32(s['gSaveBlock2Ptr'])
lib.write8(save2,255);lib.write8(save2+8,255)
lib.write8(save2+abi[45],abi[51] if scenario=='oak' else abi[46])
lib.write32(s['gMain'],0);lib.write8(s['gMain']+0x438,0);lib.write32(s['gMain']+4,s['CB2_NewGame']|1)
step(300);until(lambda:task('Task_HandleMultichoiceGridInput'));press();step(1500)
warp('MauvilleCity_BikeShop',4,5)
# Initial city menu completed before test warps; no task from the opening survives.
result=dict(passed=True, scenario=scenario, script_entry_fixture=True, full_story_validated=False)
if scenario.startswith('bike'):
    mach,voucher,got,received=abi[56:60]
    first='CeruleanCity_BikeShop_EventScript_ExchangeBikeVoucher' if scenario=='bike-kanto' else 'MauvilleCity_BikeShop_EventScript_GetMachBike'
    second='MauvilleCity_BikeShop_EventScript_Rydel' if scenario=='bike-kanto' else 'CeruleanCity_BikeShop_EventScript_Clerk'
    assert native('AddBagItem',voucher,1)
    native('FlagSet',abi[60])
    # Fill the key-item pocket, leaving the voucher untouched when delivery fails.
    pocket=s['gBagPockets']+4*8; slots=lib.read32(pocket);capacity=lib.read16(pocket+4)&1023
    saved=bytes(lib.read8(slots+i) for i in range(capacity*4))
    filler=bytes(lib.read8(slots+i) for i in range(4))
    for index in range(capacity):
        for i,b in enumerate(filler):lib.write8(slots+index*4+i,b)
    event(first);finish()
    assert var(0x40FB)==0 and not native('FlagGet',got) and not native('FlagGet',received)
    assert quantity(mach)==0 and quantity(voucher)>0
    for i,b in enumerate(saved):lib.write8(slots+i,b)
    event(first);finish()
    assert quantity(mach)==1 and var(0x40FB)==1
    event(second);finish()
    assert quantity(mach)==1
    # A bag-independent receipt prevents another bike even when it is stored.
    assert native('RemoveBagItem',mach,1)
    assert native('AddPCItem',mach,1)
    native('VarSet',0x40FB,0)
    event(second);finish()
    assert quantity(mach)==0 and var(0x40FB)==1
    assert native('TrySavingData',0,max_frames=6000)==1
    native('VarSet',0x40FB,0);assert native('LoadGameSave',0)==1
    assert var(0x40FB)==1
    result.update(full_bag_retry=True, both_supplier_orders=True, pc_bike_no_duplicate=True, saved_shared_receipt=True)
elif scenario=='oak':
    assert native('ScriptGiveMon',abi[52],5,0)==0
    warp('PalletTown_ProfessorOaksLab_Frlg',4,3)
    # Full party leaves this visit gift available for a later visit.
    for _ in range(5): assert native('ScriptGiveMon',abi[52],5,0)==0
    event('PalletTown_ProfessorOaksLab_EventScript_ProfOak');until(lambda:task('Task_HandleMultichoiceInput'));press();finish()
    assert lib.read8(s['gPartiesCount'])==6 and not native('FlagGet',0x1AC0)
    # Keep the original first party member, release fixture filler slots.
    for i in range(abi[2], 6*abi[2]): lib.write8(s['gParties']+i,0)
    lib.write8(s['gPartiesCount'],1)
    before=bytes(lib.read8(s['gParties']+i) for i in range(abi[2]))
    event('PalletTown_ProfessorOaksLab_EventScript_ProfOak');until(lambda:task('Task_HandleMultichoiceInput'));press(128);press(128);press();finish()
    assert lib.read8(s['gPartiesCount'])==2 and native('FlagGet',0x1AC0)
    assert bytes(lib.read8(s['gParties']+i) for i in range(abi[2]))==before
    assert native('GetMonData3',s['gParties']+abi[2],abi[7],0)==7
    assert native('GetMonData3',s['gParties']+abi[2],abi[6],0)==5
    event('PalletTown_ProfessorOaksLab_EventScript_ProfOak');finish()
    assert lib.read8(s['gPartiesCount'])==2
    result.update(original_team_preserved=True, once_per_region=True, starter_species=7, starter_level=5, full_party_can_retry=True)
elif scenario=='boat':
    warp('PacifidlogTown',16,14)
    event('JourneyBirth_Captain');until(lambda:task('Task_HandleYesNoInput'));press();step(500);finish()
    assert location()==map_id('SlateportCity')
    assert lib.read8(s['gPartiesCount'])==0
    result.update(island_exit_without_surf_or_pokemon=True)
else:
    assert native('ScriptGiveMon',1,5,0)==0
    before=bytes(lib.read8(s['gParties']+i) for i in range(abi[2]))
    warp('Route101',6,13)
    event('Route101_EventScript_BirchsBag')
    # Native three-starter bag screen and its confirmation dialog.
    step(500);press();step(120);press();step(1400)
    assert lib.read8(s['gPartiesCount'])==2, ('Birch did not add starter',lib.read8(s['gPartiesCount']))
    assert bytes(lib.read8(s['gParties']+i) for i in range(abi[2]))==before
    flags=lib.read32(s['gBattleTypeFlags'])
    assert flags & abi[61], ('Not the native rescue battle',flags)
    picture('birth-birch-second-region-wild-battle')
    result.update(original_team_preserved=True, native_birch_bag=True, native_wild_battle_started=True, battle_victory_validated=False)
if scenario!='birch':
    assert native('GetFollowerObject')==0
    assert native('JourneyGymBadgeCount',0)==native('JourneyGymBadgeCount',1)==0
    result['following_pokemon_removed']=True
lib.stop()
(args.output/'birth-rules.json').write_text(json.dumps(result,indent=2)+'\n')
