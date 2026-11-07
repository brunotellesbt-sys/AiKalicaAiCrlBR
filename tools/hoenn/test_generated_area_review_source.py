"""Negative controls for layer-171 source geometry, navigation and ROM bindings."""
import copy
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
import generated_area_review_contract as contract
import validate_generated_area_review_source as source
from verify_generated_area_review_source import verify_report
from test_coast_scenery_review_source import World


class IndependentSourceChecks(unittest.TestCase):
    def setUp(self):
        directory=tempfile.TemporaryDirectory(prefix='generated-source-unit-',dir='/tmp')
        self.addCleanup(directory.cleanup)
        self.root=Path(directory.name)

    def world(self,grids):
        world=World(self.root,grids)
        for layout in world.layouts.values():layout['secondary_tileset']='gTileset_Cave'
        return world

    def test_whole_native_port_objects_reject_one_remaining_quarter(self):
        grids={}
        for name,(x,y),family,quarters,target,block in source.PORT_QUARTERS:
            grids.setdefault(name,(40,40,[0x112B]*1600))
            for q,mid in enumerate(family):grids[name][2][(y+q//2)*40+x+q%2]=0x1000|mid
        old=self.world(grids);current=copy.deepcopy(old)
        for name,(x,y),family,quarters,target,block in source.PORT_QUARTERS:
            for q in quarters:
                at=(y+q//2)*40+x+q%2
                current.words[name][at]=0x1000|target|(0x400 if block else 0)
        report,_=source.check_port_objects(current,old)
        self.assertEqual((report['whole_objects'],report['changed_art_cells']),(4,9))
        current.words[source.BEACH][8*40+19]=old.words[source.BEACH][8*40+19]
        with self.assertRaisesRegex(AssertionError,'Partial port scenery'):
            source.check_port_objects(current,old)

    def cave(self):
        old=self.world({source.HORIZONTE:(48,40,[0x4211]*(48*40)),
                        'ShoalCave_LowTideInnerRoom':(48,40,[0x4211]*(48*40))})
        old.maps[source.HORIZONTE].update(warp_events=[],object_events=[],coord_events=[],bg_events=[])
        for cells,donor,(x,y),word in source.HORIZONTE_CLOSURES:
            old.words[donor][y*48+x]=word
        old.words[source.HORIZONTE][14*48+19]=0x4210
        current=copy.deepcopy(old)
        for cells,donor,point,word in source.HORIZONTE_CLOSURES:
            for x,y in cells:current.words[source.HORIZONTE][y*48+x]=word
        return old,current

    def test_unused_cave_closures_keep_native_donor_and_active_events(self):
        old,current=self.cave()
        report,cells=source.check_portals(current,old)
        self.assertEqual(report['changed_cells'],20)
        self.assertEqual(len(cells),20)
        current.words[source.HORIZONTE][18*48+14]=0x4211
        with self.assertRaisesRegex(AssertionError,'Incomplete unused portal'):
            source.check_portals(current,old)
        old,current=self.cave()
        old.maps[source.HORIZONTE]['warp_events']=[dict(x=14,y=18)]
        with self.assertRaisesRegex(AssertionError,'Active event overwritten'):
            source.check_portals(current,old)
        old,current=self.cave()
        old.words['ShoalCave_LowTideInnerRoom'][7]=0x0618
        with self.assertRaisesRegex(AssertionError,'Native closure donor'):
            source.check_portals(current,old)

    def detour(self):
        water,reef=0x112B,0x1643
        old=self.world({'A':(3,3,[water,reef,water,water,water,water,water,reef,water]),
                        'B':(3,1,[water]*3)})
        old.maps['A']['connections']=[dict(direction='down',offset=0,map='MAP_B')]
        old.maps['B']['connections']=[dict(direction='up',offset=0,map='MAP_A')]
        return old,copy.deepcopy(old)

    def test_global_bfs_accepts_neighbor_detour_but_rejects_split_and_closed_seam(self):
        old,current=self.detour()
        current.words['A'][4]=0x1643
        report=source.check_navigation(current,old,['A'],source.water,{('A',1,1)})
        self.assertEqual(report['global_components_before'],report['global_components_after'])
        current.words['B'][1]=0x1643
        with self.assertRaisesRegex(AssertionError,'component split'):
            source.check_navigation(current,old,['A'],source.water,{('A',1,1),('B',1,0)})
        old,current=self.detour()
        current.words['A'][6]=0x1643
        with self.assertRaisesRegex(AssertionError,'Physical connection opening changed'):
            source.check_navigation(current,old,['A'],source.water,{('A',0,2)})

    def test_disabled_native_connections_cannot_supply_a_return_detour(self):
        old,current=self.detour()
        old.maps['B']['connections_no_include']=current.maps['B']['connections_no_include']=True
        current.words['A'][4]=0x1643
        self.assertIsNone(source.physical_target(old,'B','up',0,-1))
        with self.assertRaisesRegex(AssertionError,'Directed navigation component split'):
            source.check_navigation(current,old,['A'],source.water,{('A',1,1)})

    def test_only_declared_south_link_can_merge_old_components(self):
        old=self.world({'A':(1,1,[0x112B]),'B':(1,1,[0x112B])})
        current=self.world({'A':(1,1,[0x112B]),'B':(1,1,[0x112B]),source.PASSAGE:(1,1,[0x112B])})
        current.maps['A']['connections']=[dict(direction='down',offset=0,map='MAP_'+source.PASSAGE)]
        current.maps['B']['connections']=[dict(direction='up',offset=0,map='MAP_'+source.PASSAGE)]
        current.maps[source.PASSAGE]['connections']=[dict(direction='up',offset=0,map='MAP_A'),dict(direction='down',offset=0,map='MAP_B')]
        with self.assertRaisesRegex(AssertionError,'components merged'):
            source.check_navigation(current,old,['A','B'],source.water,allowed_added={(source.PASSAGE,0,0)})
        report=source.check_navigation(current,old,['A','B'],source.water,allowed_added={(source.PASSAGE,0,0)},allowed_merge_maps=('A','B'))
        self.assertEqual(report['old_component_merges'],1)
        current.maps[source.PASSAGE]['connections']=[]
        current.maps['A']['connections']=current.maps['B']['connections']=[]
        with self.assertRaisesRegex(AssertionError,'isolated navigation component'):
            source.check_navigation(current,old,['A','B'],source.water,allowed_added={(source.PASSAGE,0,0)})

    def guarded_ports(self):
        old=self.world({name:(48,48,[0x112B]*(48*48)) for name in source.PORT_MAPS})
        old.behavior=lambda name,word:int(word&1023 in (0x12B,0x273))
        ports=[]
        for island,(name,dry,wet) in source.BOARDING_POINTS.items():
            points={kind:[name,point[0]-(8 if name==source.BEACH else 0),point[1]] for kind,point in (('dry',dry),('water',wet))}
            ports.append(dict(island=island,boarding=points))
            old.words[name][dry[1]*48+dry[0]]=0x3280
        old.words['SixIsland_Frlg'][29*48+2]=0x1673
        for name,x,y,gfx in source.BOAT_EVENTS:
            old.maps[name].setdefault('object_events',[]).append(dict(x=x,y=y,graphics_id=gfx))
        (self.root/'.journey-sevii-integrated-piers').write_text(json.dumps(dict(harbors=dict(ports=ports))))
        (self.root/'.journey-sevii-route-boundaries').write_text(json.dumps(dict(boundaries=dict(approach=dict(map=source.BEACH,original_terrain_offset=[8,0])))))
        path=self.root/'src/data/object_events/object_event_graphics_info.h';path.parent.mkdir(parents=True)
        path.write_text('const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_Seagallop = { .width = 64, .height = 64 };\n'
                        'const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_JourneySeviiBoat = { .width = 32, .height = 32 };\n')
        current=copy.deepcopy(old);current.words['SixIsland_Frlg'][29*48+2]=0x1273
        return old,current

    def test_independent_guards_cover_boarding_water_and_outer_boat_pixels(self):
        old,current=self.guarded_ports()
        report=source.check_port_guards(current,old,{})
        self.assertEqual((report['boarding_pairs_checked'],report['boat_footprints_checked']),(7,12))
        # This lies at the left edge of the 32 px sprite, outside its event tile.
        current.words[source.BEACH][9*48+16]=0x1643
        with self.assertRaisesRegex(AssertionError,'Boat footprint terrain changed'):
            source.check_port_guards(current,old,{})
        current.words[source.BEACH][9*48+16]=0x112B
        current.words['SixIsland_Frlg'][29*48+2]=0x1673
        with self.assertRaisesRegex(AssertionError,'Boarding cell changed'):
            source.check_port_guards(current,old,{})

    def test_compiled_map_reader_rejects_stale_connection_id_and_gps_descriptor_bytes(self):
        names=['A','B'];world=self.world({name:(1,1,[0x112B]) for name in names})
        world.maps['A']['connections']=[dict(direction='down',offset=62,map='MAP_B')]
        groups=self.root/'data/maps/map_groups.json';groups.parent.mkdir(parents=True)
        groups.write_text(json.dumps(dict(group_order=['G'],G=names)))
        gps=self.root/'src/data/journey_world_position.h';gps.parent.mkdir(parents=True)
        gps.write_text(''.join('{'+f'{i}, (MAP_GROUP(MAP_{n})<<8)|MAP_NUM(MAP_{n}), 1, 1'+'},\n' for i,n in enumerate(names)))
        rom=bytearray(4096);base=0x08000000
        table={'gMapGroups':(base+16,4),'sWorldTileGrids':(base+2000,24)}
        struct.pack_into('<I',rom,16,base+32)
        for i,name in enumerate(names):
            layout=base+256+32*i;header=base+512+32*i;events=base+768+20*i;scripts=base+896+i
            world.layouts[name]['name']=name+'_Layout'
            table.update({name:(header,28),name+'_Layout':(layout,28),name+'_MapEvents':(events,20),name+'_MapScripts':(scripts,1)})
            struct.pack_into('<I',rom,32+4*i,header)
            struct.pack_into('<4I',rom,header-base,layout,events,scripts,base+1024 if i==0 else 0)
            struct.pack_into('<IHHH2x',rom,2000+12*i,i,i,1,1)
        table['A_MapConnections']=(base+1024,8)
        struct.pack_into('<iI',rom,1024,1,base+1040)
        struct.pack_into('<B3xiBB2x',rom,1040,1,62,0,1)
        path=self.root/'pokeemerald.gba'
        path.write_bytes(rom)
        with patch.object(source,'symbols',return_value=table):
            headers,projection=source.compiled_map_bindings(self.root,world,names)
            self.assertEqual(headers[0]['connections'][0]['offset'],62)
            self.assertEqual(projection['grids'],2)
            for offset,raw,message in ((1044,struct.pack('<i',61),'physical connection'),
                                       (32,struct.pack('<I',base+544),'map ID/table'),
                                       (2004,struct.pack('<H',1),'GPS descriptors')):
                with self.subTest(offset=offset):
                    broken=bytearray(rom);broken[offset:offset+len(raw)]=raw;path.write_bytes(broken)
                    with self.assertRaisesRegex(AssertionError,message):
                        source.compiled_map_bindings(self.root,world,names)
            world.maps['A']['connections_no_include']=True
            struct.pack_into('<I',rom,512+12,0);path.write_bytes(rom)
            headers,_=source.compiled_map_bindings(self.root,world,names)
            self.assertTrue(headers[0]['connections_disabled'])
            self.assertEqual(headers[0]['connections'],[])


class SourceReportControls(unittest.TestCase):
    def setUp(self):
        directory=tempfile.TemporaryDirectory(prefix='generated-source-proof-',dir='/tmp')
        self.addCleanup(directory.cleanup)
        self.root=Path(directory.name)
        self.prepared={'src/fieldmap.c':'a'*64,'data/layouts/'+source.PASSAGE+'/map.bin':'b'*64}
        pin=patch.object(contract,'PREPARED_SHA256',self.prepared);pin.start();self.addCleanup(pin.stop)
        self.romsha='c'*64
        self.report=self.fixture()

    def fixture(self):
        from prepare_generated_area_review import PRIOR
        from generated_coast_cameras import SCOPED_MAPS,REPRO_CASES,CONTROL_CASES,OPENING_MAP,OPENING_NEIGHBOR
        changed={source.HORIZONTE,source.BEACH,source.SEA,source.PASSAGE,'FourIsland_Frlg','FiveIsland_Frlg',
                 'SixIsland_Frlg','ThreeIsland_Port_Frlg','SevenIsland_SevaultCanyon_Entrance_Frlg'}
        camera_names=sorted(set(SCOPED_MAPS)|{OPENING_MAP,OPENING_NEIGHBOR})
        names=sorted(changed|set(camera_names)|source.PORT_MAPS)
        dimensions={source.PASSAGE:(8,32)}
        layouts=[]
        for index,name in enumerate(names):
            width,height=dimensions.get(name,(48,48))
            layouts.append(dict(map=name,layout=name+'_Layout',symbol=name+'_Layout',address=0x08001000+32*index,
                width=width,height=height,primary_pointer=0x08010000,secondary_pointer=0x08010040,
                is_frlg=True,border_width=2,border_height=2,stored_border_width=2,stored_border_height=2,
                compiled_layout_bytes_match=True,
                blockdata=dict(file='data/layouts/'+name+'/map.bin',bytes=2*width*height,
                    sha256=self.prepared.get('data/layouts/'+name+'/map.bin','d'*64),address=0x08100000+index*8192),
                borderdata=dict(file='data/layouts/'+name+'/border.bin',bytes=8,sha256='e'*64,address=0x08200000+8*index)))
        observed={}
        portal_rows=[]
        for cells,donor,donor_cell,word in source.HORIZONTE_CLOSURES:
            rows=[]
            for x,y in cells:
                before=0x4211 if word!=0x4211 else 0x4210
                observed[source.HORIZONTE,x,y]=(before,word)
                rows.append(dict(cell=[x,y],before=before,after=word))
            portal_rows.append(dict(map=source.HORIZONTE,cells=rows,native_donor_map=donor,native_donor_cell=list(donor_cell),
                                    native_word=word,whole_footprint=True,active_events_unchanged=True))
        ports=[]
        for name,anchor,family,quarters,target,block in source.PORT_QUARTERS:
            before=[0x1000|mid for mid in family];after=list(before)
            for q in quarters:
                after[q]=0x1000|target|(0x400 if block else 0)
                observed[name,anchor[0]+q%2,anchor[1]+q//2]=(before[q],after[q])
            ports.append(dict(map=name,anchor=list(anchor),before=before,after=after,whole_footprint=True))
        observed.update({key:(0x1643,0x112B) for key in source.MOUTHS})
        observed.update(source.CLIFF)
        observed['SixIsland_Frlg',2,29]=(0x1673,0x1273)
        outer=[]
        for name,x,y in sorted(source.VISIBLE_LIMITS):
            before,after=source.OUTER_WORDS[name,x,y]
            observed[name,x,y]=(before,after)
            outer.append(dict(map=name,cell=[x,y],before=before,after=after,pure_water_words=[0x41C6,0x41C7,0x41C7,0x41C6,0,0,0,0]))
        cells=[dict(map=n,cell=[x,y],before=a,after=b) for (n,x,y),(a,b) in sorted(observed.items())]
        boarding=[]
        for island,(name,dry,wet) in source.BOARDING_POINTS.items():
            pair=dict(island=island)
            for kind,point,word in (('dry',dry,0x3280),('water',wet,0x1273)):
                before,after=observed.get((name,*point),(word,word))
                pair[kind]=dict(map=name,cell=list(point),before=before,after=after)
            boarding.append(pair)
        boats=[]
        for name,x,y,gfx in sorted(source.BOAT_EVENTS):
            width,height=source.BOAT_SIZES[gfx];left,top=16*x+8-width//2,16*y+16-height
            footprint=[[xx,yy] for yy in range(top//16,(top+height-1)//16+1) for xx in range(left//16,(left+width-1)//16+1)]
            changes=[dict(cell=[xx,yy],before=observed[name,xx,yy][0],after=observed[name,xx,yy][1]) for xx,yy in footprint if (name,xx,yy) in observed]
            boats.append(dict(map=name,event_cell=[x,y],graphics_id=gfx,source_sprite_size=[width,height],pixel_bounds=[left,top,width,height],
                              all_intersected_cells=footprint,reviewed_art_changes=changes))
        def navigation(added=(),removed=(),merge_maps=()):
            return dict(network_maps=names,network_maps_checked=len(names),global_components_before=2,global_components_after=2,
                all_surviving_cells_retain_global_connectivity=True,only_explicitly_reviewed_new_passages=True,
                every_physical_opening_preserved=True,old_component_merges=0,allowed_merge_maps=sorted(merge_maps),
                directed_connectivity_preserved=True,native_disabled_connection_flags_honored=True,
                directed_components_before=2,directed_components_after=2,
                added_cells=[list(c) for c in sorted(added)],removed_cells=[list(c) for c in sorted(removed)],
                physical_connections=[],physical_connections_checked=0)
        headers=[]
        ids={name:(0,67 if name==source.PASSAGE else i) for i,name in enumerate(names)}
        for index,name in enumerate(names):
            connections={source.PASSAGE:[('up',0,source.BEACH),('down',-62,source.SEA)],
                         source.BEACH:[('down',0,source.PASSAGE)],source.SEA:[('up',62,source.PASSAGE)]}.get(name,[])
            rows=[dict(direction=d,offset=o,target=t,map_group=ids[t][0],map_number=ids[t][1]) for d,o,t in connections]
            headers.append(dict(map=name,map_group=ids[name][0],map_number=ids[name][1],map_table_address=0x08080000+4*index,
                address=0x08090000+28*index,layout_pointer=layouts[index]['address'],events_pointer=0x080A0000+20*index,
                scripts_pointer=0x080B0000+index,event_counts=[0]*4,connection_pointer=0x080C0000+8*index if rows else 0,
                connection_list_pointer=0x080D0000+100*index if rows else 0,connection_bytes=12*len(rows),connection_sha256='2'*64,
                connections=rows,connections_disabled=False,compiled_header_and_connections_match=True))
        captures=[]
        for phase in ('before','after'):
            for name in names:
                layout=next(r for r in layouts if r['map']==name)
                path=self.root/(phase+'-'+name+'.png')
                Image.new('RGB',(max(480,16*layout['width']),16*layout['height']+38)).save(path)
                exists=not(phase=='before' and name==source.PASSAGE)
                captures.append(dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),map=name,phase=phase,
                    width_tiles=layout['width'],height_tiles=layout['height'],full_map=True,npcs=True,source_render_not_emulator=True,
                    label_present=True,map_exists=exists,absent_parent_panel=not exists))
        return dict(kind='generated-area-review-source',passed=True,preflight=False,compiled_rom=True,independent_replay=True,
            prefix_markers_unchanged=True,unrelated_source_files_unchanged=True,scripts_and_atlas_art_unchanged=True,
            source_gallery_not_emulator=True,stable_source_rechecked=True,stable_rom_elf_rechecked=True,
            full_campaign_playthrough=False,
            layers=PRIOR+[contract.SCOPE],parent_rom_sha256=contract.PARENT_ROM_SHA256,
            prepared_sha256=copy.deepcopy(self.prepared),changed_files=sorted(self.prepared),rom_sha256=self.romsha,elf_sha256='f'*64,
            source_hashes_checked=32000,elf_rom_load_segments_checked=3,
            south_passage_audit=dict(map=source.PASSAGE,dimensions=[8,32],old_map_count=len(names)-1,new_map_count=len(names),
                map_group='JourneyWorldOcean',appended_map_number=67,existing_mouth_cells=18,native_cliff_cells=4,gps_values_appended=256,
                new_water_cells=192,maximum_gps_step=1,old_gps_values_unchanged=True,
                old_map_ids_events_warps_coordinates_and_atlas_art_preserved=True,two_reciprocal_connections=True,
                shared_gps_seams_exact=True,only_empty_map_script_added=True,native_encounter_family_preserved=True,
                native_cliff_donors=[dict(map=n,cell=[x,y],word=w) for n,x,y,w in source.CLIFF_DONORS],
                complete_cliff_context=[dict(cell=list(c),word=w) for c,w in sorted({(7,37):0x0517,(7,38):0x0473,(7,39):0x0473,
                    (6,38):0x1128,(6,39):0x112C,(32,37):0x051F,(32,38):0x0475,(32,39):0x0475,(33,38):0x1129,(33,39):0x112A}.items())]),
            geometry_audit=dict(maps=len(names),map_names=names,changed_maps=sorted(changed),changed_cells=len(cells),cells=cells,
                outer_boundary_cells=outer,all_old_map_metadata_preserved_except_two_appended_connections=True,
                all_old_layout_metadata_unchanged=True,all_old_borders_unchanged=True,only_reviewed_native_geometry_changed=True),
            portal_audit=dict(objects=portal_rows,reviewed_maps=[source.HORIZONTE],changed_cells=20,complete_native_closures=True,
                active_entry_exit_events_preserved=True,active_exit_and_all_npc_approaches_connected=True),
            port_object_audit=dict(objects=ports,whole_objects=4,changed_art_cells=9,whole_native_objects=True),
            port_guards=dict(boarding_pairs=boarding,boarding_pairs_checked=7,boat_footprints=boats,boat_footprints_checked=12,
                boarding_water_and_dry_elevations_valid=True,only_six_blocked_boarding_water_restored=True,
                complete_native_sprite_bounds_checked=True,no_new_boat_obstacles=True),
            camera_runtime=dict(modified_functions=['JourneyMarineCornerMetatile','JourneyMarineRectangleDistance','JourneyMarineApronMetatile'],
                visual_queries_only=True,collision_elevation_movement_and_undefined_grid_unchanged=True,native_compatibility_checks_preserved=True),
            camera_audit=dict(map_names=camera_names,changed_camera_maps=sorted(SCOPED_MAPS),unresolved_cells=0,
                unresolved_scope='reviewed-aperture-policy',full_world_camera_certified=False,raw_conflicting_cells=30,
                previous_raw_conflicting_cells=30,raw_conflicting_maps={'JourneyWorldFill21Right':13,'JourneyWorldSea02':17},
                raw_source_conflicts_unchanged=True,scoped_policy_cases=[dict(case=c,before=0x243,after=c['expected_metatile'],
                    expected=c['expected_metatile'],passed=True,owner_evidence={'accepted':True}) for c in REPRO_CASES+CONTROL_CASES],
                expanded_census=dict(raw_conflicting_cells=30,raw_conflicting_maps={'JourneyWorldFill21Right':13,'JourneyWorldSea02':17},
                    conflicts=[{} for _ in range(30)],raw_conflicts_are_not_claimed_eliminated=True),
                seven_east_openings_source_unchanged=True,seven_east_openings=[dict(map=OPENING_MAP,neighbor=OPENING_NEIGHBOR,
                    player=[16,y],target=[0,y],direction='right') for y in range(1,12)]),
            boulder_census=dict(maps=len(source.PORT_MAPS|set(SCOPED_MAPS)),map_names=sorted(source.PORT_MAPS|set(SCOPED_MAPS)),new_partial_objects=0,mixed_small_and_large_objects=0,
                inherited_context_patterns_preserved=True,source_census_not_native_camera_proof=True,objects=[],classifications={}),
            surface_navigation=navigation(source.MOUTHS|{(source.PASSAGE,x,y) for y in range(32) for x in range(1,7)}|{('SixIsland_Frlg',2,29)},merge_maps=(source.BEACH,source.SEA)),
            land_navigation=navigation(removed={(source.HORIZONTE,15,19),(source.HORIZONTE,30,25)}),
            compiled_map_names=names,reviewed_maps=names,compiled_layouts=layouts,compiled_map_headers=headers,
            compiled_gps=dict(symbol='sWorldNavigationPixels',address=0x08300000,bytes=1024,sha256='3'*64),
            compiled_gps_grids=dict(symbol='sWorldTileGrids',address=0x08301000,bytes=12*len(names),sha256='4'*64,
                grids=len(names),compiled_all_map_ids_dimensions_and_offsets_match=True),
            runtime_export_names=list(source.RUNTIME_SYMBOLS),compiled_runtime=[dict(symbol=n,address=0x08020000+32*i,bytes=16,sha256='1'*64) for i,n in enumerate(source.RUNTIME_SYMBOLS)],
            captures=captures,source_gallery_rendered=True)

    def verify(self,report=None):return verify_report(self.report if report is None else report,self.root,self.romsha)

    def rejects(self,change):
        report=copy.deepcopy(self.report);change(report)
        with self.assertRaises((AssertionError,KeyError)):
            self.verify(report)

    def test_complete_compiled_source_report_passes(self):self.assertIs(self.verify(),self.report)

    def test_unpinned_stale_or_preflight_source_cannot_certify(self):
        with patch.object(contract,'PREPARED_SHA256',{}):
            with self.assertRaisesRegex(AssertionError,'not pinned'):self.verify()
        for key,value in [('preflight',True),('rom_sha256',contract.PARENT_ROM_SHA256),('elf_sha256',contract.PARENT_ELF_SHA256),
                          ('source_hashes_checked',0),('stable_rom_elf_rechecked',False)]:
            with self.subTest(key=key):self.rejects(lambda r:r.update({key:value}))

    def test_partial_objects_native_donor_and_unreviewed_geometry_are_rejected(self):
        self.rejects(lambda r:r['portal_audit']['objects'][0]['cells'].pop())
        self.rejects(lambda r:r['portal_audit']['objects'][0].update(native_word=0x0618))
        self.rejects(lambda r:r['port_object_audit']['objects'][0]['after'].__setitem__(0,0x11CB))
        self.rejects(lambda r:r['south_passage_audit']['complete_cliff_context'].pop())
        self.rejects(lambda r:r['geometry_audit']['cells'].append(dict(map=source.BEACH,cell=[15,40],before=0x112B,after=0x1643)))
        self.rejects(lambda r:r['geometry_audit']['outer_boundary_cells'][0]['pure_water_words'].__setitem__(4,1))

    def test_every_boarding_pair_and_full_boat_sprite_is_required(self):
        self.rejects(lambda r:r['port_guards']['boarding_pairs'].pop())
        self.rejects(lambda r:r['port_guards']['boarding_pairs'][5]['water'].update(after=0x1673))
        self.rejects(lambda r:r['port_guards']['boat_footprints'][0]['all_intersected_cells'].pop())
        self.rejects(lambda r:r['port_guards']['boat_footprints'][0].update(pixel_bounds=[0,0,32,32]))
        self.rejects(lambda r:r['port_guards'].update(no_new_boat_obstacles=False))

    def test_scoped_camera_proof_cannot_claim_all_raw_contradictions_resolved(self):
        self.rejects(lambda r:r['camera_audit'].update(full_world_camera_certified=True))
        self.rejects(lambda r:r['camera_audit'].update(raw_conflicting_cells=0))
        self.rejects(lambda r:r['camera_audit'].update(unresolved_scope='all-world-cameras'))
        self.rejects(lambda r:r.update(full_campaign_playthrough=True))
        self.rejects(lambda r:r['camera_audit']['scoped_policy_cases'][0].update(after=0x243))
        self.rejects(lambda r:r['camera_audit']['seven_east_openings'].pop())

    def test_navigation_cannot_add_unreviewed_openings_or_drop_old_connectivity(self):
        self.rejects(lambda r:r['surface_navigation'].update(global_components_after=3))
        self.rejects(lambda r:r['surface_navigation']['added_cells'].append([source.BEACH,15,40]))
        self.rejects(lambda r:r['land_navigation'].update(old_component_merges=1))
        self.rejects(lambda r:r['surface_navigation'].update(every_physical_opening_preserved=False))

    def test_current_compiled_map_ids_connections_gps_and_runtime_are_required(self):
        self.rejects(lambda r:r['compiled_map_headers'].pop())
        self.rejects(lambda r:next(h for h in r['compiled_map_headers'] if h['map']==source.PASSAGE).update(map_number=66))
        self.rejects(lambda r:next(h for h in r['compiled_map_headers'] if h['map']==source.SEA)['connections'][0].update(offset=61))
        self.rejects(lambda r:r['compiled_gps_grids'].update(compiled_all_map_ids_dimensions_and_offsets_match=False))
        self.rejects(lambda r:r['compiled_gps_grids'].update(bytes=1))
        self.rejects(lambda r:r['compiled_runtime'].pop())
        self.rejects(lambda r:next(h for h in r['compiled_layouts'] if h['map']==source.PASSAGE)['blockdata'].update(sha256='0'*64))

    def test_complete_gallery_cannot_fake_the_absent_parent_map_or_changed_png(self):
        self.rejects(lambda r:r['captures'].pop())
        self.rejects(lambda r:next(c for c in r['captures'] if c['phase']=='before' and c['map']==source.PASSAGE).update(map_exists=True))
        self.rejects(lambda r:r['captures'][0].update(label_present=False))
        row=self.report['captures'][0]
        path=self.root/row['file'];path.write_bytes(b'changed')
        with self.assertRaisesRegex(AssertionError,'attachment changed'):self.verify()


if __name__=='__main__':unittest.main()
