"""Keep moves acquired by changing form legal without making them teachable TMs."""
import argparse
from pathlib import Path
from candidate_layer import Layer
from prepare_nonlevel_moves import PRIOR, LAYER as PREVIOUS

LAYER = 'form-move-legality'
PRIOR = PRIOR + [PREVIOUS]
# Showdown 942cda71d14bf0618bd57991708a2e2734b6daba, learnsets.ts R sources.
# Pichu's special breeding and Shedinja's old evolution inheritance are not
# interchangeable with form acquisition and deliberately remain separate.
FORM_MOVES = {
    'ROTOM_HEAT': ['OVERHEAT'], 'ROTOM_WASH': ['HYDRO_PUMP'],
    'ROTOM_FROST': ['BLIZZARD'], 'ROTOM_FAN': ['AIR_SLASH'],
    'ROTOM_MOW': ['LEAF_STORM'],
    'PIKACHU_ROCK_STAR': ['METEOR_MASH'], 'PIKACHU_BELLE': ['ICICLE_CRASH'],
    'PIKACHU_POP_STAR': ['DRAINING_KISS'], 'PIKACHU_PHD': ['ELECTRIC_TERRAIN'],
    'PIKACHU_LIBRE': ['FLYING_PRESS'],
    'NECROZMA_DUSK_MANE': ['SUNSTEEL_STRIKE'],
    'NECROZMA_DAWN_WINGS': ['MOONGEIST_BEAM'],
    'NECROZMA_ULTRA': ['SUNSTEEL_STRIKE', 'MOONGEIST_BEAM'],
    'ZACIAN_CROWNED': ['BEHEMOTH_BLADE'],
    'ZAMAZENTA_CROWNED': ['BEHEMOTH_BASH'],
}

def prepare(source):
    layer = Layer(source, LAYER, PRIOR)
    if old := layer.existing(): return old
    path = 'src/journey_competitive.c'
    text = (layer.source / path).read_text()
    rows = ['static bool32 JourneyFormMoveLegal(u16 species, u16 move)', '{', '    switch (species)', '    {']
    for species, moves in FORM_MOVES.items():
        rows += ['    case SPECIES_' + species + ': return ' + ' || '.join('move == MOVE_' + m for m in moves) + ';']
    rows += ['    default: return FALSE;', '    }', '}', '']
    anchor = 'bool32 JourneyBossMoveLegal(u16 species,u16 move,u32 level)'
    assert text.count(anchor) == 1
    text = text.replace(anchor, '\n'.join(rows) + anchor)
    anchor = '    if(CanLearnTeachableMove(species,move))return TRUE;'
    assert text.count(anchor) == 1
    text = text.replace(anchor, '    if(JourneyFormMoveLegal(species,move))return TRUE;\n' + anchor)
    layer.stage(path, text)
    return layer.finish(form_moves=FORM_MOVES, level_gating_unchanged=True,
                        form_moves_are_not_added_to_tm_or_egg_lists=True)

if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--source', type=Path, required=True)
    print(prepare(p.parse_args().source)['layer'])
