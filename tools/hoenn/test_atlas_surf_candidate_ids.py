"""Published map slots remain stable even when the active ocean is repartitioned."""
from copy import deepcopy
import unittest

from atlas_surf_candidate_ids import bind,load_history


def old_fixture(count=3):
    names=['JourneyAtlasSea%03d'%i for i in range(count)]
    rows=[dict(name=n,id='MAP_'+n.upper(),group='JourneyAtlasSeas0',group_index=90,number=i,
               origin=[i*8,0],width=8,height=8) for i,n in enumerate(names)]
    return dict(geometry_plan=dict(chunks=rows),geometry=dict(chunks=[dict(map=n,donor=dict(map='Native',water_tile=[0,0],reef_tile=[1,0])) for n in names]))


class CandidateIdentityTests(unittest.TestCase):
    def test_old_slots_are_stable_and_removed_names_have_blocked_placeholders(self):
        old=old_fixture();rows=deepcopy(old['geometry_plan']['chunks'])
        rows=[rows[2],dict(rows[0],name='JourneyAtlasNew'),rows[0]]
        result=bind(dict(chunks=rows),old)
        ids={r['name']:(r['group_index'],r['number']) for r in result['chunks']}
        self.assertEqual(ids,{'JourneyAtlasSea002':(90,2),'JourneyAtlasNew':(90,3),'JourneyAtlasSea000':(90,0)})
        tomb=result['retired_candidate_placeholders'][0]
        self.assertEqual((tomb['name'],tomb['group_index'],tomb['number']),('JourneyAtlasSea001',90,1))
        self.assertEqual(tomb['water_runs'],[]);self.assertEqual(tomb['connections'],[])
        self.assertTrue(tomb['retired_candidate_placeholder'])
        self.assertEqual(result['candidate_registry'][0]['members'],['JourneyAtlasSea000','JourneyAtlasSea001','JourneyAtlasSea002','JourneyAtlasNew'])

    def test_a_full_group_appends_a_new_group_without_renumbering_any_old_slot(self):
        old=old_fixture(100);row=dict(old['geometry_plan']['chunks'][0],name='JourneyAtlasNew')
        result=bind(dict(chunks=[row]),old)
        self.assertEqual((result['chunks'][0]['group_index'],result['chunks'][0]['number']),(91,0))
        self.assertEqual(len(result['retired_candidate_placeholders']),100)
        self.assertEqual(result['candidate_registry'][1]['name'],'JourneyAtlasSeas1')

    def test_duplicate_or_noncontiguous_historical_slots_are_rejected(self):
        old=old_fixture();old['geometry_plan']['chunks'][1]['number']=7
        with self.assertRaisesRegex(ValueError,'contiguous'):bind(dict(chunks=[]),old)

    def test_real_baseline_matches_the_compiled_published533_rows(self):
        history=load_history();plan=bind(history['geometry_plan'],history)
        self.assertEqual(plan['retired_candidate_placeholders'],[])
        self.assertEqual(plan['candidate_identity_history']['appended_names'],[])
        old={r['name']:(r['group_index'],r['number']) for r in history['geometry_plan']['chunks']}
        self.assertEqual(old,{r['name']:(r['group_index'],r['number']) for r in plan['chunks']})


if __name__=='__main__':unittest.main()
