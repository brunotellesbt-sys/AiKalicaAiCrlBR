"""Optimize both PWT parties temporarily; preserve the player's selected moves."""
import argparse,hashlib,json
from pathlib import Path
from candidate_layer import Layer
from prepare_pwt_entrances import PRIOR,LAYER as PREVIOUS
HERE=Path(__file__).resolve().parent
LAYER='pwt-builds';PRIOR=PRIOR+[PREVIOUS]
def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if old:=layer.existing():return old
    source=layer.source
    reference=HERE/'data/pwt-builds.json';data=json.loads(reference.read_text());lines=[]
    for r in data['records']:
        moves=['{'+','.join(g+['MOVE_NONE']*(6-len(g)))+'}' for g in r['moves']]
        lines.append('{'+r['species']+',{'+','.join(moves)+'},{'+','.join(map(str,r['evs']))+'},'+r['nature']+','+str(r['priority'])+','+str(int(r['zero_attack']))+','+str(int(r['zero_speed']))+'}')
    layer.stage('src/data/journey_pwt_spreads.h','static const struct PWTSpread sPWTSpreads[] = {\n'+',\n'.join(lines)+'\n};\n')
    layer.stage('src/journey_pwt_builds.c',(HERE/'pwt_builds.c').read_bytes())
    p='include/journey_pwt.h';t=(source/p).read_text();layer.stage(p,t.replace('#endif','struct Pokemon;\nvoid JourneyPWTOptimizeMon(struct Pokemon *);\nvoid JourneyPWTOptimizeParty(struct Pokemon *,u32);\n#endif'))
    p='src/journey_pwt.c';t=(source/p).read_text()
    assert t.count('        Level50(&sPWT.selected[i]);')==1
    t=t.replace('    sPWT.rewarded = FALSE;', '    JourneyPWTOptimizeParty(sPWT.selected,PARTY_SIZE);\n    for (i=0;i<PARTY_SIZE;i++) Level50(&sPWT.selected[i]);\n    sPWT.rewarded = FALSE;')
    assert t.count('        Level50(mon);')==1
    t=t.replace('    gEnemyPartyCount = PARTY_SIZE;', '    JourneyPWTOptimizeParty(gEnemyParty,PARTY_SIZE);\n    for (u32 i=0;i<PARTY_SIZE;i++) Level50(&gEnemyParty[i]);\n    gEnemyPartyCount = PARTY_SIZE;')
    layer.stage(p,t)
    return layer.finish(reference_commit=data['reference_commit'],reference_sha256=hashlib.sha256(reference.read_bytes()).hexdigest(),
        published_spreads=len(lines),all_pwt_opponents_and_player_optimized=True,
        normal_edition_pwt_ivs_override=True,player_moves_items_ability_personality_preserved=True,
        exact_party_backup_restored_on_retirement_elimination_championship=True,
        zero_attack_only_for_attack_reducing_natures=True,zero_speed_for_appropriate_trick_room_gyro_ball_builds=True,
        trick_room_receivers_recognized_from_whole_party=True,
        fallback_for_species_without_analysis='moveset-aware singles role spread',
        full_campaign_playthrough=False)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True)
    print(prepare(p.parse_args().source)['layer'])
