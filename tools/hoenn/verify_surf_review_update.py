"""Verify the eight cave release, all Surf links and its isolated review ROM."""
import hashlib,json
from pathlib import Path
from verify_fuchsia_update import previous_release
ROOT=Path(__file__).resolve().parents[2]
def verify_update(directory,info,*,historical_review=None):
    directory=Path(directory);old=previous_release(info)
    assert old['validated'] and old['integration_layers']+['surf-review']==info['integration_layers']
    from package_review_rom import verify as verify_review
    if historical_review is None:
        test=verify_review(ROOT/'roms/rom-de-teste',directory/'Pokemon-Journey-Gen1-9-Normal.gba')
    else:
        # A later release keeps these reports bound to the old ROM hashes.
        # Its own verifier checks the newly shipped ROM and review derivative.
        test=historical_review
        normal=next(r for r in info['variants'] if r['file']==test['base_normal_file'])
        assert test['base_normal_sha256']==normal['sha256'] and test['bytes']==33554432
        assert test['separate_save_identity'] and not test['random_wild_encounters']
    expected={'common':info['parent_rom_sha256'],'test':test['sha256'],**{r['file']:r['sha256'] for r in info['variants']}}
    covered=set()
    for p in info['proofs']:
        path=Path(p['file']);assert not path.is_absolute() and '..' not in path.parts
        raw=(directory/path).read_bytes();assert hashlib.sha256(raw).hexdigest()==p['sha256']
        r=json.loads(raw);assert r['passed'] and r['rom_sha256']==expected[p['target']],p
        kind=p['kind'];covered.add((p['target'],kind))
        if kind=='surf-review-source':
            assert r['layers']==info['integration_layers'] and r['independent_source_reproduced'] and r['idempotent'] and r['all_source_hashes_verified']>30000
            assert r['foreign_rock_and_beach_aprons'] and r['all_relocated_available_in_four_editions'] and r['popup_buffer_bytes']>=96
            assert r['total_special_species']==105 and len(r['redistributed_from_fullest'])==8 and r['legendary_capture_flags_and_species_preserved']
            assert r['all_exposed_route_limits_blocked'] and len(r['boundaries'])>=96
            assert len(r['branches'])==9 and len({b['interior_template'] for b in r['branches'] if not b['existing_cave']})==8
            assert r['gps']['maximum_neighbor_pixel_step']<=2 and r['gps']['maximum_seam_delta']==0
        elif kind=='surf-review':
            assert r['compiled_atlas_pixels_match_source'] and r['compiled_zoom_pixels_match_source']
            assert len(r['caves'])==9 and r['eight_new_caves'] and r['existing_artisan_cave_connected'] and r['all_edges_match_native_map_connections']
            assert r['no_midroute_warps_or_coordinate_writes']
            assert sum(c['relocated_altar_interacted'] for c in r['caves'])==8
            assert all(c['controller_entry_and_return'] and c['surf_restored_on_return'] and c['native_map_open_zoom_return'] and c['cursor']==c['position'] for c in r['caves'])
        elif kind=='review-mode':
            assert r['review_mode']==(p['target']=='test') and r['fixture_wild_encounters_disabled'] is False
            assert bool(r['checks']['trainer_approach_result'])==(p['target']!='test')
            if p['target']=='test':
                c=r['checks'];assert c['random_wild_attempts']>=200 and c['no_automatic_approach_after_600_frames'] and c['no_random_encounters'] and c['no_fishing_encounters'] and c['no_sweet_scent_encounters'] and c['no_rock_smash_encounters']
                assert c['native_flash_save_exported']
                if historical_review is None:
                    assert hashlib.sha256((ROOT/'roms/rom-de-teste/Pokemon-Journey-TESTE.sav').read_bytes()).hexdigest()==c['save_sha256']
        elif kind=='all-surf-links':
            assert r['all_usable_outdoor_surf_connections_covered'] and len(r['links'])>=235 and r['crossings']==2*len(r['links'])+len(r['native_current_links'])
        elif kind=='ocean-aprons':
            assert len(r['checks'])==3 and r['no_midroute_warps_or_coordinate_writes']
            assert all(c['foreign_rock_rendered_before_map_transition'] and c['apron_collision_blocks_rock'] and c['rock_graphics_unchanged_over_256_frames_in_both_banks'] and c['controller_roundtrip'] for c in r['checks'])
        elif kind=='ocean-seams':assert len(r['seams'])>=13 and all(c['outbound_and_return'] and c['colors_identical'] for c in r['seams'])
        elif kind=='coastal-cave-access':assert len(r['caves'])==15 and r['native_controller_entries_and_returns']
        elif kind=='coast-connectivity':assert r['all_integrated_surface_seas_reachable'] and r['unconnected_outer_borders_blocked']
        elif kind=='sevii-surf-connections':assert len(r['islands'])==7 and r['controller_roundtrip'] and r['active_screen_fade_frames']==0
        elif kind=='continuous-ocean':
            assert r['native_surf_and_disembark'] and r['continuous_video'] and r['all_seam_ocean_colors_identical']
            assert hashlib.sha256((ROOT/'docs/videos/mossdeep-one-island-surf.mp4').read_bytes()).hexdigest()==r['video_sha256']
        else:raise AssertionError(kind)
    assert {('common',k) for k in ['surf-review-source','surf-review','all-surf-links','coastal-cave-access','coast-connectivity','ocean-seams','ocean-aprons','sevii-surf-connections','continuous-ocean']}<=covered
    assert {(t,k) for t in expected if t!='common' for k in ['surf-review','review-mode']}<=covered
    if historical_review is None:
        offset=test['review_mode_offset'];assert all((directory/r['file']).read_bytes()[offset]==0 for r in info['variants'])
    from verify_continuous_ocean_update import verify_update as verify_previous
    verify_previous(directory,old)
