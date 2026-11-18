"""Recheck nine complete mountains and native camera pixels on one frozen ROM."""
import gzip
import json
from pathlib import Path

from PIL import Image
from verify_legendary_chambers_native import confined,digest
from verify_sevii_route_boundaries_native import verify_pixels


def load(path):
    path=Path(path);raw=path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)


def verify(frozen,folder,exteriors):
    frozen=load(frozen) if isinstance(frozen,(str,Path)) else frozen
    exteriors=load(exteriors) if isinstance(exteriors,(str,Path)) else exteriors
    folder=Path(folder);matrix=load(folder/'large-cave-exteriors-native-matrix.json')
    wanted={r['map']:r for r in exteriors['maps']}
    artifacts={'pokeemerald.gba':frozen['rom_sha256'],'pokeemerald.elf':frozen['elf_sha256'],
               '.journey-atlas-surf-layout':frozen['marker_sha256']}
    assert len(wanted)==9 and matrix['artifact_sha256']==artifacts and matrix['passed'] is True
    seen=set();captures_checked=0;mountain_total=0
    for part in matrix['components']:
        path=confined(folder,part['report']);assert digest(path)==part['sha256']
        report=load(path);base=path.parent
        assert report['passed'] is True and report['artifact_sha256']==artifacts
        assert report['after_placement_controllers_and_readonly_getters_only'] is True
        captures={r['file']:r['sha256'] for r in report['captures']}
        assert len(captures)==len(report['captures'])
        images={}
        for name,sha in captures.items():
            p=confined(base,name);assert digest(p)==sha
            image=Image.open(p).convert('RGB');assert image.size==(240,160)
            images[name]=image;captures_checked+=1
        for case in report['cases']:
            name=case['map'];assert name in wanted and name not in seen;seen.add(name)
            expected={(16+dx,17+dy):word&1023 for dx,dy,word in wanted[name]['mountain_cells']}
            assert len(expected)==case['whole_mountain_cells']==81
            observed=set()
            for view in case['mountain_views']:
                assert view['state']['map']==name
                phases=view['phases'];assert [p['frame'] for p in phases]==[0,24,48]
                for phase in phases:
                    observation=phase['pixels'];assert observation['map']==name
                    for cell in observation['cells']:
                        tile=tuple(cell['cell']);assert tile in expected
                        assert cell['native_metatile']==cell['expected_metatile']==expected[tile]
                        verify_pixels(dict(observation,cells=[cell]),phase['capture'],captures,images,cell['cell'],expected[tile])
                        observed.add(tile)
            assert observed==set(expected),'Missing mountain quarter'
            mountain_total+=len(observed)
            for key in ('before_entry_pixels','returned_neighbor_pixels'):
                phases=case[key];assert [p['frame'] for p in phases]==[0,24,48]
                for phase in phases:
                    observation=phase['pixels'];assert observation['map']==case['neighbor'] and observation['cells']
                    for cell in observation['cells']:
                        verify_pixels(dict(observation,cells=[cell]),phase['capture'],captures,images,
                                      cell['cell'],cell['expected_metatile'])
            bump=case['native_front_bump'];assert bump['before']==bump['after']
            assert bump['before']['map']==name and bump['key']==64 and bump['frames']>=60
            assert case['before']['map']==case['sea_return']['map']==case['neighbor']
            assert case['before']['tile']==case['sea_return']['tile']==case['fixture_start']
            assert case['before']['mode']==case['sea_return']['mode']==8
            assert case['returned']==dict(map=name,tile=[16,19],mode=1)
            # Alvorada retains its native flooded entrance; its first interior
            # step uses Surf. The other eight entrances land on dry cave floor.
            assert case['interior']['mode']==(8 if name=='JourneyAtlasCave00' else 1)
            assert case['interior']['map']!=name
            assert case['native_connected_route_beach_cave_and_reciprocal_return'] is True
        for query in report['queries']:
            assert query['function'].startswith(('MapGridGet','MetatileBehavior_Is')) or query['function'] in {
                'PlayerGetElevation','GetPlayerFacingDirection','IsPlayerFacingSurfableFishableWater',
                'IsDirectionalStairWarpMetatileBehavior'}
        assert report['controls'] and any(r['key'] for r in report['controls'])
    assert seen==set(wanted)
    return dict(passed=True,ROM_sha256=frozen['rom_sha256'],maps=9,complete_mountain_cells=mountain_total,
                captures=captures_checked,final_release_validated=False)
