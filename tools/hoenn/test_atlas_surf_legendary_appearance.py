"""Appearance changes keep battle/catch identity and unrelated statues intact."""
from copy import deepcopy
import unittest

from atlas_surf_legendary_appearance import repair_objects


class LegendaryAppearanceTests(unittest.TestCase):
    def test_only_the_special_statue_graphic_changes(self):
        event=dict(local_id='LOCALID_SPECIAL_481',native_local_id=7,graphics_id='OBJ_EVENT_GFX_TRICK_HOUSE_STATUE',
            x=4,y=6,elevation=3,movement_type='MOVEMENT_TYPE_FACE_DOWN',movement_range_x=0,movement_range_y=0,
            script='JourneySanctuary_481',flag='FLAG_JOURNEY_SPECIAL_481',trainer_type='TRAINER_TYPE_NONE')
        original=dict(name='Cave',warp_events=[dict(x=4,y=9,dest_map='MAP_SEA',dest_warp_id='0')],
            object_events=[event,dict(event,script='NativeDecoration',flag='0'),
                           dict(event,graphics_id='OBJ_EVENT_GFX_SPECIES(MESPRIT)')])
        saved=deepcopy(original)
        result,changes=repair_objects(original,[dict(national_dex=481,species='SPECIES_MESPRIT',flag=event['flag'])])
        self.assertEqual(original,saved)
        self.assertEqual(result['object_events'][0],dict(event,graphics_id='OBJ_EVENT_GFX_SPECIES(MESPRIT)'))
        self.assertEqual(result['object_events'][1:],original['object_events'][1:])
        self.assertEqual(result['warp_events'],original['warp_events']);self.assertEqual(len(changes),1)
        self.assertEqual(changes[0]['native_local_id'],7)

    def test_wrong_capture_flag_is_rejected(self):
        mapping=dict(name='Cave',object_events=[dict(graphics_id='OBJ_EVENT_GFX_TRICK_HOUSE_STATUE',
            script='JourneySanctuary_481',flag='FLAG_OTHER')])
        with self.assertRaisesRegex(ValueError,'capture flag'):
            repair_objects(mapping,[dict(national_dex=481,species='SPECIES_MESPRIT',flag='FLAG_JOURNEY_SPECIAL_481')])

    def test_reapplying_does_not_change_existing_species_appearance(self):
        mapping=dict(name='Cave',object_events=[dict(graphics_id='OBJ_EVENT_GFX_SPECIES(MESPRIT)',
            script='JourneySanctuary_481',flag='FLAG_JOURNEY_SPECIAL_481')])
        result,changes=repair_objects(mapping,[dict(national_dex=481,species='SPECIES_MESPRIT',flag='FLAG_JOURNEY_SPECIAL_481')])
        self.assertEqual(result,mapping);self.assertEqual(changes,[])


if __name__=='__main__':unittest.main()
