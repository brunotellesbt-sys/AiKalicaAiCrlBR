"""Verify actual camera words, RGB samples, animation and return on 16 maps."""
from functools import lru_cache
import hashlib
from io import BytesIO
from pathlib import Path

from PIL import Image

from game_continuity_coasts import ASSIGNMENTS
from verify_sevii_integrated_piers_update import require_true


@lru_cache(maxsize=384)
def decoded(raw):
    with Image.open(BytesIO(raw)) as image:
        assert image.size==(240,160)
        return image.convert('RGB')


def verify(report,directory):
    directory=Path(directory)
    assert report['kind']=='game-continuity-coasts'
    require_true(report,['passed','compiled_rom','native_validation_performed',
        'initial_placement_party_progress_encounter_suppression_are_fixtures',
        'no_midtrip_position_elevation_camera_palette_or_vram_writes'])
    assert report['full_campaign_playthrough'] is False
    assert report['source_compatible_directed_seams']==92
    rows=report['cases'];assert len(rows)==16 and [r['map'] for r in rows]==list(ASSIGNMENTS)
    assert len(report['fixtures'])==16 and report['walked_tiles']>32
    assert len(report['transitions'])>=32
    captures={}
    for row in report['captures']:
        path=Path(row['file']);assert not path.is_absolute() and '..' not in path.parts
        assert str(path) not in captures
        raw=(directory/path).read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256']
        captures[str(path)]=(row['sha256'],decoded(raw))
    assert len(captures)==16*19
    def camera(info,attachment):
        require_true(info,['canonical_neighbor_rom_bg_words_checked',
            'actual_hardware_bg_vram_palette_scanout_checked',
            'sprites_and_opaque_ui_explicitly_excluded','mismatches_not_discarded'])
        assert info['checked_scanout_samples']>=300 and info['water_samples']>=50 and info['palette']==4
        assert 0<=info['neighbor_scanout_samples']<=info['checked_scanout_samples']
        assert info['samples']
        sha,image=captures[attachment['file']];assert sha==attachment['sha256']
        for x,y,r,g,b,name,mid in info['samples']:
            assert 0<=x<240 and 0<=y<160 and 0<=mid<1024 and name
            assert all(abs(a-v)<=7 for a,v in zip(image.getpixel((x,y)),(r,g,b))),('Native camera picture mismatch',attachment['file'],x,y)
    for row,fixture in zip(rows,report['fixtures']):
        name=row['map'];primary,secondary=ASSIGNMENTS[name]
        assert fixture['map']==name and fixture['surfing'] is True
        require_true(row,['controlled_outbound_and_return'])
        for key in ('before','after','returned'):
            s=row[key];assert s['surfing'] is True and s['elevation']==1 and s['priority']==2
            assert s['sprite_visible'] is s['object_visible'] is True
        assert row['before']['tile']==row['returned']['tile']==fixture['tile']
        assert row['before']['map']==row['returned']['map']==name
        assert row['after']['map']==row['neighbor']
        assert row['before_bank']==row['return_bank']
        assert (row['before_bank']['primary'],row['before_bank']['secondary'])==(primary,secondary)
        for bank in (row['before_bank'],row['after_bank'],row['return_bank']):
            assert all(0x08000000<=bank[k]<0x0A000000 for k in ('primary_pointer','secondary_pointer'))
        camera(row['before_pixels'],row['before_capture'])
        camera(row['after_pixels'],row['after_capture'])
        camera(row['return_pixels'],row['return_capture'])
        if name in ('JourneySurfLink01000','JourneySurfLink05400','JourneySurfLink05301','JourneySurfLink05200'):
            assert any(mid>=640 for mid in row['before_pixels']['neighbor_metatiles']),('Terminal pieces absent from approach proof',name)
        phases=row['phases'];assert len(phases)==16 and [p['sample'] for p in phases]==list(range(16))
        seen={group:set() for group in ('ocean','upper_current','upper_sand')}
        for p in phases:
            assert set(p['valid_native_phases'])==set(seen)
            for group,values in p['valid_native_phases'].items():
                assert values and set(values)<=set(range(8));seen[group].update(values)
            assert p['camera']['map']==name
            camera(p['camera'],p['capture'])
        assert all(values==set(range(8)) for values in seen.values())
    return report
