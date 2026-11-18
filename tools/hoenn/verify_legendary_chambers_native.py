"""Check all 105 controller trips and opaque species pixels on one frozen ROM."""
import hashlib
import gzip
import json
from pathlib import Path

from PIL import Image


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def confined(root,name):
    root=Path(root).resolve()
    p=Path(name)
    if p.is_absolute() or '..' in p.parts or not p.parts:
        raise ValueError('Native attachment escapes its proof directory')
    target=root/p
    if not target.resolve().is_relative_to(root) or any((root/Path(*p.parts[:i])).is_symlink() for i in range(1,len(p.parts)+1)):
        raise ValueError('Native attachment is a symlink or outside the proof directory')
    return target


def verify(frozen,folder,rooms):
    if isinstance(frozen,(str,Path)):
        frozen=json.loads(Path(frozen).read_bytes())
    folder=Path(folder)
    matrix=json.loads((folder/'legendary-chambers-native-matrix.json').read_bytes())
    expected={r['national_dex']:r for r in rooms}
    artifacts={'pokeemerald.gba':frozen['rom_sha256'],'pokeemerald.elf':frozen['elf_sha256'],
               '.journey-atlas-surf-layout':frozen['marker_sha256']}
    if len(expected)!=105 or not matrix['passed'] or matrix['artifact_sha256']!=artifacts:
        raise ValueError('Chamber proof has incomplete coverage or a stale ROM identity')
    seen=set();captures=0;body_pixels=0
    for component in matrix['components']:
        path=confined(folder,component['report'])
        if digest(path)!=component['sha256']:
            raise ValueError('Native chamber component changed')
        raw=path.read_bytes()
        report=json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)
        if not report['passed'] or report['artifact_sha256']!=artifacts:
            raise ValueError('Native chamber component belongs to another ROM')
        for flag in ('initial_adjacent_floor_party_progress_and_position_fixtures_declared',
                     'after_placement_controllers_and_readonly_getters_only'):
            if report.get(flag) is not True:
                raise ValueError('Controller provenance is missing')
        if not report['controls'] or any(c['frames']<=0 or c['key'] not in (0,1,2,4,8,16,32,64,128) for c in report['controls']):
            raise ValueError('Native chamber input log is missing or invalid')
        for query in report['queries']:
            name=query['function']
            if not (name.startswith(('MapGridGet','MetatileBehavior_Is')) or name in ('PlayerGetElevation','GetPlayerFacingDirection')):
                raise ValueError('Gameplay mutation cannot be a read-only observation')
        for case in report['cases']:
            dex=case['national_dex']
            if dex in seen or dex not in expected:
                raise ValueError('A chamber is duplicated or replaces another species')
            seen.add(dex);row=expected[dex]
            if (case['parent'],case['room'])!=(row['parent'],row['room']):
                raise ValueError('Native trip used the wrong individual entrance')
            if (case['before']['map'],case['entered']['map'],case['returned']['map'])!=(row['parent'],row['room'],row['parent']):
                raise ValueError('Native chamber entry or return is absent')
            if case['before']['tile']!=case['fixture_start'] or any(case[k]['mode']!=1 for k in ('before','entered','returned')):
                raise ValueError('Chamber trip did not retain pedestrian mode')
            if sum(abs(a-b) for a,b in zip(case['returned']['tile'],row['entrance']))>1:
                raise ValueError('Chamber returned through a different entrance')
            if case.get('native_controller_entry_and_return') is not True:
                raise ValueError('Missing actual native controller trip')
            pixel=case['species_pixels']
            if pixel['opaque_pixels']<40 or pixel['native_source_pixels']!=pixel['opaque_pixels']:
                raise ValueError('The species frame is incomplete or belongs to another sprite')
            if pixel['visible_pixels']<pixel['opaque_pixels']*.95 or len(pixel['expected_scanout_pixels'])!=pixel['opaque_pixels']:
                raise ValueError('The species body is covered or missing pixels')
            if pixel['graphics_id']!='OBJ_EVENT_GFX_SPECIES('+row['species'].removeprefix('SPECIES_')+')':
                raise ValueError('A statue or another species replaced the Pokémon')
            for label in ('entrance_capture','species_capture'):
                attachment=case[label];capture=confined(path.parent,attachment['file'])
                if digest(capture)!=attachment['sha256']:
                    raise ValueError('Native chamber capture changed')
                with Image.open(capture) as image:
                    if image.format!='PNG' or image.size!=(240,160):
                        raise ValueError('A native 240x160 PNG capture is required')
                    if label=='species_capture':
                        rgb=image.convert('RGB');matches=0;points=set()
                        for x,y,r,g,b in pixel['expected_scanout_pixels']:
                            if (x,y) in points or not (0<=x<240 and 0<=y<160):
                                raise ValueError('Duplicate or clipped species pixel')
                            points.add((x,y))
                            matches+=all(abs(a-c)<=7 for a,c in zip(rgb.getpixel((x,y)),(r,g,b)))
                        if matches<pixel['opaque_pixels']*.95 or matches!=pixel['visible_pixels']:
                            raise ValueError('PNG pixels do not reproduce the observed whole species')
                        body_pixels+=matches
                captures+=1
    if seen!=set(expected):
        raise ValueError('Not every one of the 105 chambers has a native trip')
    return dict(passed=True,ROM_sha256=frozen['rom_sha256'],rooms=105,captures=captures,
                visible_native_species_pixels=body_pixels,
                capture_battles_and_saves_validated=False,final_release_validated=False)
