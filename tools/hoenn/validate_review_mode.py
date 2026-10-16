"""Compare native encounter/approach behavior in review and normal ROMs."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
prefix=(ROOT/'tools/hoenn/validate_team_missions.py').read_text().split('\nassert pending(True) == 7')[0]
exec(compile(prefix,__file__,'exec'))
mode=lib.read8(s['gJourneyReviewMode']);assert mode in [0,1]
native('DisableWildEncounters',0)
# No Repel or defeated-trainer fixture may supply the review behavior.
native('VarSet',0x4021,0);native('VarSet',0x4120,0)
i=json.loads((source/'.journey-surf-cave-coasts').read_text())['islands'][0];t=i['trainer'];native('SetTrainerFlag',t['id'])
warp(i['map'],t['x'],t['y']+2);step(30)
rawflag(t['flag'],False)
result=0
for tick in range(600):
    step(1)
    result=lib.read8(s['gNoOfApproachingTrainers'])
    if result:break
assert bool(result)==(not bool(mode)),('Native trainer approach',mode,result)
checks=dict(trainer_approach_result=result,undefeated_trainer_in_sight=True)
if not mode:
    # The positive trainer control deliberately schedules an encounter;
    # stop this isolated emulator before its dialogue advances.
    lib.stop()
else:
    step(600);assert idle();assert lib.read32(s['gMain']+4)&~1 not in [s['CB2_InitBattle'],s['BattleMainCB2']]
    checks['no_automatic_approach_after_600_frames']=True
    warp('Route104',24,20);step(60)
    assert not native('DoesCurrentMapHaveFishingMons')
    assert not native('SweetScentWildEncounter')
    native('RockSmashWildEncounter');assert lib.read16(s['gSpecialVar_Result'])==0
    attempts=0
    for behavior in [2,3,16,17,18]:
        for _ in range(40):
            assert not native('StandardWildEncounter',behavior,behavior);attempts+=1
    checks.update(random_wild_attempts=attempts,no_random_encounters=True,no_fishing_encounters=True,no_sweet_scent_encounters=True,no_rock_smash_encounters=True)
    picture('review-mode-no-approaches')
    for f in kanto_flags+hoenn_flags:rawflag(f,True)
    for slot,move in enumerate([57,19,291,127]):native('ScriptSetMonMoveSlot',0,move,slot)
    warp('MossdeepCity',28,18);native('SetPlayerAvatarTransitionFlags',1);step(60);finish()
    assert native('JourneyGymBadgeCount',1)==native('JourneyGymBadgeCount',0)==8
    assert native('TrySavingData',0,max_frames=6000)==1
    assert native('LoadGameSave',0,max_frames=6000)==1
    import ctypes
    lib.export_save.argtypes=[ctypes.c_char_p];lib.export_save.restype=ctypes.c_int
    destination=ROOT/'roms/rom-de-teste/Pokemon-Journey-TESTE.sav'
    assert lib.export_save(str(destination).encode());assert destination.stat().st_size==131072
    picture('review-save-mossdeep');checks['native_flash_save_exported']=True
    checks['save_sha256']=hashlib.sha256(destination.read_bytes()).hexdigest();lib.stop()
(args.output/'review-mode.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),review_mode=bool(mode),checks=checks,fixture_wild_encounters_disabled=False,fixture_repel_steps=0),indent=2)+'\n')
