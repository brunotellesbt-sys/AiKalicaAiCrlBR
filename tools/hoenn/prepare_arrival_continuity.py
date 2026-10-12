"""Show the native sailing scene on island starts and keep home professors unique."""
import argparse,hashlib,json
from pathlib import Path
from prepare_small_ports import PRIOR,LAYER as PREVIOUS
LAYER='arrival-continuity';PRIOR=PRIOR+[PREVIOUS]
def prepare(source):
 source=Path(source);marker=source/('.journey-'+LAYER)
 if marker.exists():
  r=json.loads(marker.read_text())
  for p,h in r['prepared_sha256'].items():assert hashlib.sha256((source/p).read_bytes()).hexdigest()==h,p
  return r
 expected=dict(json.loads((source/'.source-acquired.json').read_text())['sha256'])
 for layer in PRIOR:expected.update(json.loads((source/('.journey-'+layer)).read_text())['prepared_sha256'])
 outputs={};originals={}
 def stage(p,text):
  old=(source/p).read_bytes() if (source/p).exists() else None;h=hashlib.sha256(old).hexdigest() if old else None
  assert h==expected.get(p),p
  if h:originals[p]=h
  outputs[p]=text.encode()
 p='src/journey_birth.c';t=(source/p).read_text();t=t.replace('VarGet(VAR_JOURNEY_BIRTH_ARRIVAL) != 2 ||','(VarGet(VAR_JOURNEY_BIRTH_ARRIVAL) != 2 && VarGet(VAR_JOURNEY_BIRTH_ARRIVAL) != 4) ||').replace('VarSet(VAR_JOURNEY_BIRTH_ARRIVAL, 3);','VarSet(VAR_JOURNEY_BIRTH_ARRIVAL, VarGet(VAR_JOURNEY_BIRTH_ARRIVAL) == 4 ? 5 : 3);')
 t+='''
void JourneyBirthIntroVoyage(void)
{
    u16 index=VarGet(VAR_JOURNEY_FAMILY_HOME);
    gSpecialVar_Result=FALSE;
    if(!JourneyBirthIsBoat() || VarGet(VAR_JOURNEY_BIRTH_ARRIVAL)!=3 || index==0 || index>ARRAY_COUNT(sJourneyBirthArrivals))return;
    const struct JourneyBirthArrival *arrival=&sJourneyBirthArrivals[index-1];
    VarSet(VAR_JOURNEY_BIRTH_ARRIVAL,4);
    gSpecialVar_0x8004=MAP_GROUP(arrival->map);gSpecialVar_0x8005=MAP_NUM(arrival->map);
    gSpecialVar_0x8006=0xFFFF;gSpecialVar_0x8007=1;
    gSpecialVar_0x8009=arrival->landingX;gSpecialVar_0x800A=arrival->landingY;
    gSpecialVar_Result=TRUE;
}
void JourneyBirthSyncProfessor(void)
{
    u16 index=VarGet(VAR_JOURNEY_FAMILY_HOME);
    if(index==0 || index==1 || index==17 || FlagGet(FLAG_JOURNEY_FAMILY_STARTER_RECEIVED))return;
    if(index<=16)
    {
        FlagSet(FLAG_HIDE_OAK_IN_HIS_LAB);FlagSet(FLAG_HIDE_OAK_IN_PALLET_TOWN);
    }
    else
    {
        FlagSet(FLAG_HIDE_LITTLEROOT_TOWN_BIRCHS_LAB_BIRCH);
        FlagSet(FLAG_HIDE_ROUTE_101_BIRCH_ZIGZAGOON_BATTLE);
        FlagSet(FLAG_HIDE_ROUTE_101_BIRCH_STARTERS_BAG);
    }
}
''';stage(p,t)
 p='include/journey_birth.h';stage(p,(source/p).read_text().replace('#endif','void JourneyBirthIntroVoyage(void);\nvoid JourneyBirthSyncProfessor(void);\n#endif'))
 p='data/specials.inc';stage(p,(source/p).read_text()+'\n\tdef_special JourneyBirthIntroVoyage\n\tdef_special JourneyBirthSyncProfessor\n')
 p='data/scripts/journey_birth.inc';t=(source/p).read_text().replace('JourneyBirth_Arrival::\n\tlockall','JourneyBirth_Arrival::\n\tlockall\n\tspecial JourneyBirthIntroVoyage\n\tgoto_if_eq VAR_RESULT, TRUE, JourneyBirth_IntroSailing\n\tspecial JourneyBirthSyncProfessor')
 t+='''
JourneyBirth_IntroSailing::
\tfadescreen FADE_TO_BLACK
\tspecial DoSeagallopFerryScene
\twaitstate
\tend
''';stage(p,t)
 r=dict(layer=LAYER,island_starts_use_native_ferry_animation=True,mainland_truck_scene_preserved=True,home_professor_hidden_in_other_locations=True,oak_for_kanto_and_sevii=True,original_sha256=originals,prepared_sha256={p:hashlib.sha256(raw).hexdigest() for p,raw in outputs.items()})
 for p,raw in outputs.items():(source/p).write_bytes(raw)
 marker.write_text(json.dumps(r,indent=2)+'\n');return r
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);a=p.parse_args();print(json.dumps(prepare(a.source),indent=2))
