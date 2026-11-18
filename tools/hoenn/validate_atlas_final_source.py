"""Replay atlas172 independently and bind its source, maps and AREA to the ROM."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import tempfile

from atlas_dex_retired_habitats import relocate
from atlas_legendary_chambers import load_current,stage,refresh_saved_objects
from atlas_large_cave_exteriors import stage as stage_exteriors,stage_save_rescues
from atlas_surf_object_ids import native_local_id
from atlas_surf_truth import ART_ARRAYS,array_values
from audit_legendary_chambers import audit as audit_rooms
from badge_story_layer import read
from candidate_layer import Layer
from prepare_generated_area_review import PRIOR,LAYER
from prepare_atlas_surf_redesign import source_audit
from validate_generated_area_review_source import compiled_map_bindings
from validate_coast_scenery_review_source import compiled_bindings
from validate_sevii_route_boundaries_source import Inputs,symbols

ROOT=Path(__file__).resolve().parents[2]


def sha(raw):return hashlib.sha256(raw).hexdigest()
def load(path):
    path=Path(path);raw=path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)


def constants(source,expressions):
    expressions=sorted(set(map(str,expressions)))
    code=''.join('#include "'+h+'"\n' for h in ('global.h','constants/species.h','constants/maps.h',
        'constants/flags.h','constants/vars.h','constants/event_objects.h','constants/event_object_movement.h',
        'constants/trainers.h','constants/trainer_types.h'))
    code+='const u32 atlasConstants[]={'+','.join(expressions)+'};\n'
    with tempfile.TemporaryDirectory(prefix='atlas-constants-') as directory:
        p=Path(directory)/'values.c';p.write_text(code);out=p.with_suffix('.s')
        result=subprocess.run([str(ROOT/'.local/arm-gcc/usr/bin/arm-none-eabi-gcc'),'-S','-mthumb','-mcpu=arm7tdmi',
            '-mabi=apcs-gnu','-std=gnu17','-DMODERN=1','-DEMERALD','-iquote',str(source/'include'),str(p),'-o',str(out)],capture_output=True)
        if result.returncode:
            raise ValueError('\n'.join(line for line in result.stderr.decode().splitlines() if 'error:' in line or 'note:' in line)[:12000])
        raw=out.read_bytes();body=raw.decode().split('atlasConstants:',1)[1].split('.size',1)[0]
        values=[int(v)&0xFFFFFFFF for v in re.findall(r'^\s*\.word\s+(-?\d+)\s*$',body,re.M)]
    assert len(values)==len(expressions)
    return dict(zip(expressions,values)),sha(raw)


def validate(source,parent,reference,frozen,census,output):
    source,parent,reference,output=(Path(p).resolve() for p in (source,parent,reference,output))
    output.mkdir(parents=True,exist_ok=True);frozen=load(frozen);metadata=load(source/'.journey-atlas-surf-layout')
    expected=Layer(source,'atlas-surf-layout',PRIOR+[LAYER]).expected;expected.update(metadata['prepared_sha256'])
    for name,wanted in expected.items():assert sha((source/name).read_bytes())==wanted,name
    artifacts={n:sha((source/n).read_bytes()) for n in ('pokeemerald.gba','pokeemerald.elf','.journey-atlas-surf-layout')}
    assert artifacts=={'pokeemerald.gba':frozen['rom_sha256'],'pokeemerald.elf':frozen['elf_sha256'],'.journey-atlas-surf-layout':frozen['marker_sha256']}
    replay,meta=load_current(parent);rooms=stage(replay,reference);exteriors=stage_exteriors(replay,meta)
    meta['large_cave_exteriors']=exteriors;meta['legendary_individual_chambers']=rooms
    refresh_saved_objects(replay,rooms['changed_parent_maps']+['MAP_'+r['map'].upper() for r in exteriors['maps']])
    stage_save_rescues(replay,exteriors);meta['migration']['final_version']=8
    baseline=load(ROOT/'docs/design/atlas-surf-layout/ecology-parent-source.json.gz')
    catalog=load(ROOT/'tools/hoenn/catalog_metadata.json')['species'];after=load(census)
    path='src/data/journey_world_dex_locations.h'
    header,dex=relocate(read(replay,path).decode(),baseline,after,meta['geometry_plan'],catalog);replay.stage(path,header)
    assert {n:sha(raw) for n,raw in replay.outputs.items()}==frozen['prepared_sha256'],'Independent atlas replay differs'
    room_audit=audit_rooms(replay,reference,rooms)
    _,physical,_,banks=source_audit(replay,meta)
    print('All34396 inputs, independent2604-file replay, rooms and global physical graph PASS',flush=True)
    inputs=Inputs(source);groups=load(source/'data/maps/map_groups.json')
    names=sorted(n for group in groups['group_order'] for n in groups[group])
    layouts,runtime,gps,segments=compiled_bindings(source,inputs,names)
    maps,descriptors=compiled_map_bindings(source,inputs,names)
    rom=(source/'pokeemerald.gba').read_bytes();table=symbols(source);ranges=[]
    def data(at,size):
        offset=at-0x08000000;assert 0<=offset<=len(rom)-size;return rom[offset:offset+size]
    def bind(label,at,raw):
        assert data(at,len(raw))==raw,('Compiled data differs',label)
        row=dict(label=label,address=at,bytes=len(raw),sha256=sha(raw));ranges.append(row);return row
    expressions={'sizeof(struct WarpEvent)','sizeof(struct ObjectEventTemplate)',
        '__builtin_offsetof(struct ObjectEventTemplate,graphicsId)','__builtin_offsetof(struct MapEvents,warps)'}
    for name in names:
        for warp in inputs.maps[inputs.maps[name].get('shared_events_map',name)]['warp_events']:
            expressions.update((str(warp['dest_warp_id']),'MAP_NUM('+warp['dest_map']+')','MAP_GROUP('+warp['dest_map']+')'))
    affected={r['room'] for r in rooms['rooms']}|{r['parent'] for r in rooms['rooms']}
    affected.update(r['map'] for r in metadata['surf_trainer_redesign']['trainers'])
    affected.update(('PacifidlogTown','PacifidlogTown_House1'))
    ordinary=[]
    for name in sorted(affected):
        for index,event in enumerate(inputs.maps[name]['object_events']):
            if event.get('type','object')!='object':continue
            ordinary.append((name,index,event))
            expressions.update(str(event.get(k,0)) for k in ('graphics_id','movement_type','trainer_type','trainer_sight_or_berry_tree_id','flag'))
    dex_rows=re.findall(r'\{(SPECIES_\w+),(MAP_\w+),(\d+),(\d+),(\d+),(\d+)\}',header)
    expressions.update(v for row in dex_rows for v in row[:2])
    values,assembly_sha=constants(source,expressions)
    assert [values[e] for e in ('sizeof(struct WarpEvent)','sizeof(struct ObjectEventTemplate)',
        '__builtin_offsetof(struct ObjectEventTemplate,graphicsId)','__builtin_offsetof(struct MapEvents,warps)')]==[8,24,1,8]
    warps_checked=objects_checked=0;compiled_by_name={r['map']:r for r in maps}
    for name in names:
        events=compiled_by_name[name]['events_pointer'];pointer=struct.unpack('<I',data(events+8,4))[0]
        raw=b''
        for warp in inputs.maps[inputs.maps[name].get('shared_events_map',name)]['warp_events']:
            raw+=struct.pack('<hhBBBB',warp['x'],warp['y'],warp['elevation'],values[str(warp['dest_warp_id'])]&255,
                values['MAP_NUM('+warp['dest_map']+')']&255,values['MAP_GROUP('+warp['dest_map']+')']&255);warps_checked+=1
        if raw:bind(name+' warps',pointer,raw)
    for name,index,event in ordinary:
        events=compiled_by_name[name]['events_pointer'];pointer=struct.unpack('<I',data(events+4,4))[0]+24*index
        raw=bytearray(24);raw[0]=native_local_id(event,index)
        struct.pack_into('<H',raw,1,values[str(event.get('graphics_id',0))]);raw[3]=0
        struct.pack_into('<hh',raw,4,event['x'],event['y']);raw[8]=event.get('elevation',0)
        raw[9]=values[str(event.get('movement_type',0))]
        raw[10]=int(event.get('movement_range_x',0))|(int(event.get('movement_range_y',0))<<4)
        struct.pack_into('<HH',raw,12,values[str(event.get('trainer_type',0))],values[str(event.get('trainer_sight_or_berry_tree_id',0))])
        script=event.get('script','NULL')
        script_pointer=0 if str(script) in ('NULL','0','0x0') else table[script][0]
        struct.pack_into('<I',raw,16,script_pointer)
        struct.pack_into('<H',raw,20,values[str(event.get('flag',0))]);bind(name+' object '+str(raw[0]),pointer,raw);objects_checked+=1
    dex_raw=b''.join(struct.pack('<HHBBBB',values[r[0]],values[r[1]],*map(int,r[2:])) for r in dex_rows)
    at,size=table['sWorldDexLocations'];assert size==len(dex_raw);bind('current AREA locations',at,dex_raw)
    world=(source/'src/data/journey_world_map.h').read_text()
    for name in ART_ARRAYS:
        vals=array_values(world,name);fmt='H' if name in ('sWorldPalette','sWorldTilemap') else 'B'
        raw=struct.pack('<'+fmt*len(vals),*vals);assert sha(raw)==metadata['art_sha256'][name];bind(name,table[name][0],raw)
    for name in ('JourneyWorldMapPosition','JourneySpecialUnlocked','HasTrainerBeenFought','CreateNPCTrainerPartyFromTrainer',
                 'TrySetDiveWarp','GetMapBorderIdAt','CopyPartyAndObjectsFromSave','TrySpawnObjectEvents'):
        at,size=table[name];assert size;runtime.append(bind(name,at,data(at,size)))
    for name,wanted in expected.items():assert sha((source/name).read_bytes())==wanted,name
    assert artifacts=={n:sha((source/n).read_bytes()) for n in artifacts}
    report=dict(kind='atlas-surf-final-source',passed=True,rom_sha256=frozen['rom_sha256'],elf_sha256=frozen['elf_sha256'],
        marker_sha256=frozen['marker_sha256'],prepared_sha256=frozen['prepared_sha256'],source_inputs_checked=len(expected),
        complete_source_manifest_sha256=frozen['complete_source_manifest_sha256'],independent_replay=True,
        source_file_hashes_match_compiled_snapshot=True,physical=physical,banks=banks,rooms=room_audit,dex_relocation=dex,
        compiled_layouts=layouts,compiled_maps=maps,compiled_runtime=runtime,compiled_gps=[gps,descriptors],
        compiled_ranges=ranges,warps_checked=warps_checked,affected_actor_templates_checked=objects_checked,
        current_AREA_rows=len(dex_rows),ARM_constant_probe_sha256=assembly_sha,elf_rom_load_segments_checked=segments,
        immutable_atlas_art_matches=True,full_campaign_playthrough=False)
    (output/'atlas-surf-final-source.json.gz').write_bytes(gzip.compress(json.dumps(report,sort_keys=True,separators=(',',':')).encode(),mtime=0))
    print('Compiled source/maps/warps/actors/AREA/art PASS:',len(maps),warps_checked,objects_checked,len(dex_rows),flush=True)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','parent','reference','frozen','census','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();validate(a.source,a.parent,a.reference,a.frozen,a.census,a.output)
