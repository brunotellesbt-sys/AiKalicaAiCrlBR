"""Expand PWT to independent identities, generation cups and a full World Cup.

This is a candidate overlay. Release validation and presentation completion are
reported separately; preparing source does not replace any shipped ROM.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
from candidate_layer import Layer
from prepare_modern_field_moves import PRIOR, LAYER as PREVIOUS
from pwt_catalog import load, eligible

HERE = Path(__file__).resolve().parent
LAYER = 'pwt-world-cup'; PRIOR = PRIOR + [PREVIOUS]

def prepare(source):
    layer = Layer(source,LAYER,PRIOR)
    if existing := layer.existing(): return existing
    source = layer.source; rows = load()
    assets = HERE/'data/pwt'
    provenance = json.loads((assets/'sources.json').read_text())
    portraits = {r['key']:r for r in provenance['portraits']}
    # Validate every offline input before changing a single source file.
    for record in portraits.values():
        if 'converted' in record:
            assert hashlib.sha256((assets/record['converted']).read_bytes()).hexdigest()==record['converted_sha256']
    opponents = 'include/constants/opponents.h'; text=(source/opponents).read_text()
    first = int(re.search(r'#define TRAINERS_COUNT\s+(\d+)\b',text)[1])
    assert first == 1589
    text = re.sub(r'(#define TRAINERS_COUNT\s+)\d+\b',lambda m:m[1]+str(first+len(rows)),text)
    text += '\n'+''.join(f'#define TRAINER_JOURNEY_PWT_{r["key"]} {first+r["id"]}\n' for r in rows)
    layer.stage(opponents,text)
    pictures = []
    for row in rows:
        key=row['key']; row['trainer_id']=first+row['id']
        if key in ('EREN','LUFFY'):
            row['picture']='TRAINER_PIC_JOURNEY_'+key
            continue
        pictures.append(key);row['picture']='TRAINER_PIC_JOURNEY_PWT_'+key
        layer.stage('graphics/trainers/front_pics/journey_pwt_'+key.lower()+'.png',(assets/portraits[key]['converted']).read_bytes())
    p='include/constants/trainers.h';text=(source/p).read_text()
    assert text.count('    TRAINER_PIC_COUNT,')==1
    layer.stage(p,text.replace('    TRAINER_PIC_COUNT,',''.join('    TRAINER_PIC_JOURNEY_PWT_'+n+',\n' for n in pictures)+'    TRAINER_PIC_COUNT,'))
    p='src/data/graphics/trainers.h';text=(source/p).read_text();start=text.index('#define TRAINER_FRONT_PIC')
    declarations=''.join('const u32 gTrainerFrontPic_JourneyPWT'+n+'[] = INCBIN_U32("graphics/trainers/front_pics/journey_pwt_'+n.lower()+'.4bpp.smol");\nconst u16 gTrainerPalette_JourneyPWT'+n+'[] = INCBIN_U16("graphics/trainers/front_pics/journey_pwt_'+n.lower()+'.gbapal");\n' for n in pictures)
    text=text[:start]+declarations+text[start:];end=text.rindex('};')
    text=text[:end]+''.join('    [TRAINER_PIC_JOURNEY_PWT_'+n+'] = {.frontPic = TRAINER_FRONT_PIC(gTrainerFrontPic_JourneyPWT'+n+', gTrainerPalette_JourneyPWT'+n+')},\n' for n in pictures)+text[end:]
    layer.stage(p,text)
    parties=[]; catalog=[]; names=[]
    for row in rows:
        key=row['key']; role=row['roles']; name=row['name']
        # The native battle-name field is ten characters. The board uses full
        # names in a separate table, without changing historical save fields.
        short='Wake' if key=='CRASHER_WAKE' else name[:10]
        cls='CHAMPION' if 'champion' in role else 'ELITE_FOUR' if 'elite' in role else 'LEADER' if 'leader' in role or 'captain' in role else 'RIVAL'
        mons=','.join('{.species=SPECIES_'+n+',.lvl=100,.iv=TRAINER_PARTY_IVS(20,20,20,20,20,20),.gender=TRAINER_MON_RANDOM_GENDER,.ball=POKEBALL_COUNT,.nature=NATURE_HARDY}' for n in row['species'])
        parties.append('[DIFFICULTY_NORMAL][TRAINER_JOURNEY_PWT_'+key+']={.trainerName=_("'+short+'"),.trainerClass=TRAINER_CLASS_'+cls+',.trainerPic='+row['picture']+',.gender=TRAINER_GENDER_MALE,.encounterMusic=TRAINER_ENCOUNTER_MUSIC_MALE,.aiFlags=AI_FLAG_BASIC_TRAINER,.partySize=6,.party=(const struct TrainerMon[]){'+mons+'}},\n')
        mask=sum(1<<(g-1) for g in row['generations'] if g)
        catalog.append('{TRAINER_JOURNEY_PWT_'+key+','+str(mask)+',{'+','.join('SPECIES_'+n for n in row['species'])+'}},\n')
        names.append('    COMPOUND_STRING("'+name+'"),\n')
    layer.stage('src/data/journey_pwt_trainers.h',''.join(parties))
    layer.stage('src/data/journey_pwt_catalog.h','static const struct PWTTrainer sPWTTrainers[] = {\n'+''.join(catalog)+'};\nstatic const u8 *const sPWTTrainerNames[] = {\n'+''.join(names)+'};\n'+''.join('#define JOURNEY_PWT_'+r['key']+' '+str(r['id'])+'\n' for r in rows))
    p='src/data.c';text=(source/p).read_text();assert text.count('#include "data/trainers.h"')==1
    layer.stage(p,text.replace('#include "data/trainers.h"','#include "data/trainers.h"\n#include "data/journey_pwt_trainers.h"'))
    for origin,target in [('pwt_world.c','src/journey_pwt.c'),('pwt_world.h','include/journey_pwt.h'),
                          ('pwt_world.inc','data/scripts/journey_pwt.inc'),('pwt_cup.c','src/journey_pwt_cup.c'),
                          ('pwt_cup.h','include/journey_pwt_cup.h'),('pwt_board.c','src/journey_pwt_board.c')]:
        layer.stage(target,(HERE/origin).read_bytes())
    p='data/specials.inc';text=(source/p).read_text();text+='\n\tdef_special JourneyPWTMenu\n\tdef_special JourneyPWTBoard\n'
    layer.stage(p,text)
    p='src/pokemon.c';text=(source/p).read_text()
    old='TRAINER_BATTLE_PARAM.opponentA == TRAINER_JOURNEY_EREN_6'
    assert text.count(old)==1
    layer.stage(p,text.replace(old,'(TRAINER_BATTLE_PARAM.opponentA == TRAINER_JOURNEY_EREN_6 || TRAINER_BATTLE_PARAM.opponentA == TRAINER_JOURNEY_PWT_EREN)'))
    return layer.finish(catalog=rows, portrait_count=len(rows), independent_shared_gym_entries=True,
        world_cup_entrants={str(cap):len(eligible(rows,cap))+1 for cap in (4,9)},
        format='Singles six; group round robin; top two; knockout; level 50 trained forms retained',
        group_size_range=[3,6], results_points=dict(win=3,draw=1,loss=0),
        native_battles_validated=False, walking_sprites_complete=False, presentation_complete=False,
        campaign_gym_battles_unchanged=True, unobserved_matches='strength-weighted NPC simulation')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True)
    print(prepare(p.parse_args().source)['layer'])
