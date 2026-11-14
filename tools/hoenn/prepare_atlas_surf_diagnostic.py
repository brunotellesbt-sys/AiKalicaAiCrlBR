"""Prepare a private three-map diagnostic, never a releasable Surf network.

The synthetic five-pixel L fixture tests a four-tile-wide map, two seams,
diagonal terrain, affine heading and performance. It does not classify or
replace the real atlas routes. Existing destinations are always preserved.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct

from atlas_surf_geometry import chunk_water, rasterize
from atlas_surf_layer import stage_geometry
from atlas_surf_runtime import stage as stage_runtime
from atlas_surf_physical import stage as stage_physical
from atlas_surf_ecology import stage as stage_ecology
from atlas_surf_native_scenery import repair as stage_scenery
from atlas_surf_source import Source
from atlas_surface_batteries import stage as stage_migration
from candidate_layer import Layer
from prepare_generated_area_review import PRIOR, LAYER
from restore_generated_area_review import verify_prefix


def diagnostic_plan():
    pixels = [(140,70), (141,70), (142,70), (142,71), (142,72)]
    water = rasterize(pixels)
    rectangles = [(1120,560,4,8), (1124,560,20,8), (1124,568,20,16)]
    chunks = []
    covered = set()
    for i, (left,top,width,height) in enumerate(rectangles):
        name = f'JourneyAtlasProbe{i}'
        cells = {(x,y) for x,y in water if left<=x<left+width and top<=y<top+height}
        if covered & cells or not cells:
            raise AssertionError('Diagnostic partition lost its independent ownership')
        covered.update(cells)
        runs = []
        for y in range(top,top+height):
            xs = sorted(x-left for x,yy in cells if yy==y)
            if xs:
                if xs != list(range(xs[0],xs[-1]+1)):
                    raise AssertionError('Diagnostic row is not contiguous')
                runs.append([y-top,xs[0],xs[-1]+1])
        chunks.append(dict(name=name,id='MAP_'+name.upper(),group='JourneyAtlasDiagnosticSeas',
                           number=i,origin=[left,top],width=width,height=height,
                           water_runs=runs,connections=[]))
    if covered != water:
        raise AssertionError('Diagnostic partition does not cover the source raster')
    for a,direction,b,reverse in [(0,'right',1,'left'),(1,'down',2,'up')]:
        chunks[a]['connections'].append(dict(direction=direction,map=chunks[b]['id'],offset=0))
        chunks[b]['connections'].append(dict(direction=reverse,map=chunks[a]['id'],offset=0))
    return dict(schema='atlas-surf-three-map-diagnostic/v1',scale=8,corridor_width=6,
                route_pixels=pixels,water_tiles=len(water),chunks=chunks,
                diagnostic_only=True,real_route_classification=False,release_eligible=False)


def prepare(source, clone_from):
    source, clone_from = Path(source).resolve(), Path(clone_from).resolve()
    if source.exists():
        raise ValueError('Preserve existing or partial diagnostic; choose a new private destination')
    parent = verify_prefix(clone_from, complete=True)
    source.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(clone_from, source, copy_function=shutil.copy2, symlinks=False)
    if verify_prefix(source, complete=True) != parent:
        raise ValueError('Copied parent differs; preserve it for diagnosis')
    layer = Layer(source,'atlas-stage-smoke',PRIOR+[LAYER])
    plan = diagnostic_plan()
    mapping = json.loads((source/'data/maps/JourneyWorldSea00/map.json').read_text())
    layouts = {row['id']:row for row in json.loads((source/'data/layouts/layouts.json').read_text())['layouts']}
    layout = layouts[mapping['layout']]
    words = struct.unpack('<'+'H'*(layout['width']*layout['height']), (source/layout['blockdata_filepath']).read_bytes())
    if (layout['primary_tileset'], layout['secondary_tileset'], layout['layout_version']) != (
            'gTileset_General_Frlg','gTileset_IslandHarbor_Frlg','frlg'):
        raise ValueError('Diagnostic donor bank changed')
    wet, reef = words.index(0x112B), words.index(0x1643)
    terrain = Source(source)
    if not terrain.water('JourneyWorldSea00',wet%layout['width'],wet//layout['width']):
        raise ValueError('Diagnostic donor no longer has native Surf behavior')
    terrain.assert_unchanged()
    donors = {row['name']:dict(map='JourneyWorldSea00',water_tile=[wet%layout['width'],wet//layout['width']],
                               reef_tile=[reef%layout['width'],reef//layout['width']]) for row in plan['chunks']}
    plan, geometry = stage_geometry(layer,plan,donors)
    runtime = stage_runtime(layer,plan)
    physical = stage_physical(layer,plan)
    ecology = stage_ecology(layer,{row['name']:'JourneyWorldSea00' for row in plan['chunks']})
    first = plan['chunks'][0]
    x,y = min(chunk_water(first))
    old = json.loads((source/'data/maps/JourneySurfLink00000/map.json').read_text())
    if old['warp_events']:
        raise ValueError('Synthetic diagnostic relocation fixture no longer event-free')
    migration = stage_migration(layer,[dict(old_map=old['id'],destination_map=first['id'],
                                          source_rect=[1,1,2,2],destination_origin=[x,y],mode='surf',elevation=1)])
    scenery = stage_scenery(layer)
    if verify_prefix(clone_from,complete=True) != parent:
        raise ValueError('Parent changed while preparing diagnostic; preserve output for diagnosis')
    report = layer.finish(diagnostic_only=True,release_eligible=False,
                          synthetic_migration_fixture_not_release_mapping=True,
                          parent=parent,geometry_plan=plan,geometry=geometry,runtime=runtime,
                          physical=physical,ecology=ecology,migration=migration,scenery=scenery)
    return dict(prepared_files=len(report['prepared_sha256']),diagnostic_maps=len(plan['chunks']),
                marker_sha256=hashlib.sha256(layer.marker.read_bytes()).hexdigest(),
                diagnostic_only=True,release_eligible=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--clone-from',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(prepare(args.source,args.clone_from),indent=2))
