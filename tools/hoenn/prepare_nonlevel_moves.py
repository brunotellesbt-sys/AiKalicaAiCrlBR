"""Use pinned modern TM/tutor and egg compatibility for players and opponents."""
import argparse
import json
import re
from pathlib import Path
from candidate_layer import Layer
from prepare_battle_interactions import PRIOR,LAYER as PREVIOUS
from audit_battle_database import move_constants

ROOT=Path(__file__).resolve().parents[2]
REFERENCE=ROOT/'tools/hoenn/data/nonlevel-moves.json'
LAYER='nonlevel-moves';PRIOR=PRIOR+[PREVIOUS]

def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if old:=layer.existing():return old
    ref=json.loads(REFERENCE.read_text());names=move_constants(layer.source)
    lines=['// Pinned official TM/tutor and egg compatibility; level-up remains separate.']
    tables={};pointers={'teachable':[],'egg':[]}
    for sid,row in sorted(ref['species'].items(),key=lambda pair:int(pair[0])):
        for kind in pointers:
            moves=tuple(row[kind])
            if moves not in tables:
                symbol='sJourneyNonlevel'+str(len(tables));tables[moves]=symbol
                lines.append('static const u16 '+symbol+'[]={'+','.join(names[m] for m in moves)+(',' if moves else '')+'MOVE_UNAVAILABLE};')
            pointers[kind].append('['+row['species']+']='+tables[moves]+',')
    for kind,symbol in [('teachable','gJourneyTeachable'),('egg','gJourneyEgg')]:
        lines+=['const u16 *const '+symbol+'[NUM_SPECIES]={',*pointers[kind],'};']
    layer.stage('src/data/journey_nonlevel_moves.h','\n'.join(lines)+'\n')
    p='src/pokemon.c';text=(layer.source/p).read_text()
    anchor='#include "data/pokemon/trainer_class_lookups.h"';assert text.count(anchor)==1
    text=text.replace(anchor,'#include "data/journey_nonlevel_moves.h"\n'+anchor)
    for field,symbol in [('teachableLearnset','gJourneyTeachable'),('eggMoveLearnset','gJourneyEgg')]:
        old='    const u16 *learnset = gSpeciesInfo[SanitizeSpeciesId(species)].'+field+';'
        new='    enum Species safeSpecies = SanitizeSpeciesId(species);\n    const u16 *learnset = '+symbol+'[safeSpecies];\n    if (learnset == NULL)\n        learnset = gSpeciesInfo[safeSpecies].'+field+';'
        assert text.count(old)==1;text=text.replace(old,new)
    layer.stage(p,text)
    p='include/constants/daycare.h';text=(layer.source/p).read_text()
    match=re.search(r'(#define EGG_MOVES_ARRAY_COUNT\s+)(\d+)',text);assert match
    count=max(int(match[2]),ref['max_egg_moves'])
    assert count<=255
    text=text[:match.start(2)]+str(count)+text[match.end(2):]
    layer.stage(p,text)
    return layer.finish(reference_species_and_forms=len(ref['species']),reference_missing_forms=ref['missing_forms'],
        egg_move_capacity=count,tm_tutor_separate_from_egg_moves=True,level_gating_unchanged=True,
        official_transfer_compatibility_retained=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    print(prepare(p.parse_args().source)['layer'])
