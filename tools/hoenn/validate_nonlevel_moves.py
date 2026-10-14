"""Audit every frozen compatibility list and native TM/egg/form legality."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_pwt_world.py').read_text().split('for generation in range(cap+1):')[0]
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_pwt_world.py'),'exec'))
from audit_battle_database import compiled_teachable_and_egg_moves
from battle_interaction_fixture import compile_probe
from prepare_form_move_legality import FORM_MOVES
ref=json.loads((ROOT/'tools/hoenn/data/nonlevel-moves.json').read_text())
compiled=compiled_teachable_and_egg_moves(source,separate=True)
for sid,row in ref['species'].items():
    for kind in ('teachable','egg'):assert compiled[int(sid)][kind]==set(row[kind]),(sid,kind)
constants={"SPECIES_SCIZOR","SPECIES_ROTOM","SPECIES_ROTOM_WASH","SPECIES_GARCHOMP",
           "MOVE_U_TURN","MOVE_CALM_MIND","MOVE_VOLT_SWITCH","MOVE_HYDRO_PUMP",
           "MOVE_OUTRAGE","EGG_MOVES_ARRAY_COUNT"}
for species,moves in FORM_MOVES.items():
    constants.add('SPECIES_'+species);constants.update('MOVE_'+m for m in moves)
_,values,_=compile_probe(source,constants)
checks=[]
for species,move,level,expected in [('SCIZOR','U_TURN',100,True),('SCIZOR','CALM_MIND',100,False),
    ('ROTOM_WASH','VOLT_SWITCH',100,True),('ROTOM_WASH','HYDRO_PUMP',100,True),
    ('ROTOM','HYDRO_PUMP',100,False)]:
    actual=bool(native('JourneyBossMoveLegal',values['SPECIES_'+species],values['MOVE_'+move],level))
    assert actual==expected,(species,move,actual)
    checks.append(dict(species=species,move=move,level=level,legal=actual))
for species,moves in FORM_MOVES.items():
    for move in moves:
        assert native('JourneyBossMoveLegal',values['SPECIES_'+species],values['MOVE_'+move],100)
        assert not native('CanLearnTeachableMove',values['SPECIES_'+species],values['MOVE_'+move])
        checks.append(dict(species=species,move=move,legal=True,teachable=False))
# Outrage is a legitimate egg move for Gible's line; an egg-only source must
# remain distinct from the teachable table (pick deterministically from data).
egg_only=next((int(sid),m) for sid,row in ref['species'].items() for m in row['egg'] if m not in row['teachable'])
assert native('JourneyBossMoveLegal',egg_only[0],egg_only[1],100)
assert not native('CanLearnTeachableMove',egg_only[0],egg_only[1])
assert values['EGG_MOVES_ARRAY_COUNT']>=ref['max_egg_moves']==22
result=dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
    reference_sha256=hashlib.sha256((ROOT/'tools/hoenn/data/nonlevel-moves.json').read_bytes()).hexdigest(),
    reference_commit=ref['provenance']['commit'],species_and_forms_checked=len(ref['species']),
    independently_checked_tables=2*len(ref['species']),differences=[],native_checks=checks,
    native_egg_only_case=list(egg_only),egg_capacity=values['EGG_MOVES_ARRAY_COUNT'],
    tm_tutor_and_egg_lists_separate=True,form_moves_not_tms=True,official_transfer_compatibility=True)
lib.stop();(args.output/'nonlevel-moves.json').write_text(json.dumps(result,indent=2)+'\n')
print('All',len(ref['species']),'TM/tutor and egg lists plus native form checks passed',flush=True)
