"""Reject clipped avatars, missing approaches and broken Surf underpasses."""
import copy
from pathlib import Path
import unittest
from unittest.mock import patch

from PIL import Image
from verify_coastal_ecology_update import verify_pier_visibility


def fixture():
    images={}
    report=dict(compiled_rom=True,native_validation_performed=True,
        all_sixteen_dry_approach_cells_both_directions_verified=True,
        full_head_body_feet_actual_vram_scanout_compared=True,
        both_existing_lower_surf_routes_preserved=True,
        native_surf_departure_and_reboard_both_ports=True,
        initial_placements_party_and_progress_are_fixtures=True,
        movement_fixture_random_encounters_disabled=True,controller_only_after_initial_placement=True,
        no_midtrip_coordinate_elevation_or_avatar_writes=True,pixel_failures=[],
        dry_approach_cells=16,dry_approach_directional_samples=32)
    projection=[[x,y,248,0,0,min(2,(y-64)*3//16),True]
        for y in range(64,80) for x in range(112,128)]
    bands=[dict(expected=sum(p[5]==i for p in projection),matched=sum(p[5]==i for p in projection))
        for i in range(3)]
    pixels=dict(exact_current_vram_frame_compared=True,background_color_coincidence_not_used=True,
        hardware_oam_index=0,screen_rectangle=[112,64,16,16],expected_scanout_pixels=projection,
        expected_opaque_pixels=256,matching_scanout_pixels=256,head_body_feet_bands=bands,
        exclusive_obj_palette_pixels=256,exclusive_obj_palette_pixels_visible=256)
    def sample(name,xy,surfing=False,priority=1,direction=None):
        label='frame-'+str(len(images))+'.png'
        image=Image.new('RGB',(240,160),(0,80,192))
        image.paste((248,0,0),(112,64,128,80));images[label]=image
        row=dict(map=name,tile=list(xy),surfing=surfing,elevation=1 if surfing else 3,
            priority=priority,sprite_visible=True,object_visible=True,capture_file=label)
        if not surfing:row['native_avatar_pixels']=copy.deepcopy(pixels)
        if direction:row['direction']=direction
        return row
    report['approaches']=[]
    for name,bounds,cells in [('CinnabarIsland_Frlg',[9,16,10,17],[(x,y) for y in (16,17) for x in (9,10)]),
        ('PalletTown_Frlg',[11,26,22,26],[(x,26) for x in range(11,23)])]:
        report['approaches'].append(dict(map=name,bounds=bounds,expected_cells=list(map(list,cells)),
            both_directions=True,samples=[sample(name,xy,direction=d) for d in ('outbound','return') for xy in cells]))
    report['bridge_foot_samples']=[sample('CinnabarIsland_Frlg',(x,15),direction=d)
        for d in ('outbound','return') for x in range(6,12)]
    report['bridge_foot_samples'] += [sample('PalletTown_Frlg',(18,y),priority=2 if y==24 else 1,direction=d)
        for d,y in [('outbound',25),('outbound',24),('return',25),('return',26)]]
    report['underpasses']=[]
    for name,start,route in [
        ('CinnabarIsland_Frlg',(16,16),[(16,15)]+[(x,15) for x in range(11,5,-1)]
            +[(x,15) for x in range(6,12)]+[(16,15),(16,16)]),
        ('PalletTown_Frlg',(17,25),[(18,25),(19,25),(18,25),(17,25)])]:
        report['underpasses'].append(dict(map=name,start=list(start),route=list(map(list,route)),
            both_directions=True,continuous_native_surf=True,full_multilevel_bridge_crossed=True,
            native_lower_priority2_preserved=True,
            samples=[sample(name,xy,True,2) for xy in [start,*route]]))
    report['surf_transitions']=[]
    for name,dry,water in [('CinnabarIsland_Frlg',[9,17],[9,18]),('PalletTown_Frlg',[17,26],[17,25])]:
        row=dict(map=name,dry=dry,water=water,surf_departure=sample(name,water,True,2),
            reboarded=sample(name,dry),native_surf_prompt=True,native_controller_departure_and_reboard=True)
        if name=='PalletTown_Frlg':row['initial_reboarded']=sample(name,dry)
        report['surf_transitions'].append(row)
    sample('CinnabarIsland_Frlg',(11,14),priority=2)
    report['captures']=[dict(file=name,sha256='a'*64) for name in images]
    return report,images


class PierContract(unittest.TestCase):
    def check(self,report,images):
        with patch('verify_coastal_ecology_update.verify_captures',return_value=images):
            verify_pier_visibility(report,Path('.'))

    def test_full_pixel_matrix_and_both_surf_underpasses_pass(self):
        self.check(*fixture())

    def test_one_missing_dry_approach_direction_cannot_hide_behind_counters(self):
        report,images=fixture();report['approaches'][0]['samples'].pop()
        with self.assertRaises(AssertionError):self.check(report,images)

    def test_priority_claim_must_match_each_observed_foot_state(self):
        report,images=fixture();report['approaches'][0]['samples'][0]['priority']=2
        with self.assertRaises(AssertionError):self.check(report,images)

    def test_clipped_head_rejected_even_when_avatar_visible_flag_is_true(self):
        report,images=fixture();row=report['approaches'][0]['samples'][0]
        images[row['capture_file']].paste((0,80,192),(112,64,128,70))
        with self.assertRaises(AssertionError):self.check(report,images)

    def test_lower_surf_cannot_be_replaced_by_on_foot_bridge_crossing(self):
        report,images=fixture();report['underpasses'][0]['samples'][2]['surfing']=False
        with self.assertRaises(AssertionError):self.check(report,images)

    def test_reboard_cannot_remain_surfing_or_hide_player_under_planks(self):
        for key,value in [('surfing',True),('elevation',1),('priority',2)]:
            report,images=fixture();report['surf_transitions'][0]['reboarded'][key]=value
            with self.assertRaises(AssertionError):self.check(report,images)


if __name__=='__main__':unittest.main()
