"""Finish native object footprints exposed by the extra-gym clearings.

These edits follow docs/design/proposta-gba-portos-ginasios.png. They never
move a door, NPC, connection or atlas pixel. Each replacement is a complete
native edge or object, rather than clearing a rectangle through its artwork.
"""
import json
import struct


# Complete obsolete roof footprints and their surrounding foreign-water pads.
# One Island's old terminal straddles the native town/Treasure Beach seam:
# its remaining roof, walls and flagposts must be removed on both maps.
OBSOLETE_FERRIES = [
    dict(island='One', town='OneIsland_Frlg', ramp=[12,18], ramp_warp=3,
         roof=[10,19,5,1], clear=[9,19,7,1], water=0x112b,
         connected_remnants=[dict(map='OneIsland_TreasureBeach_Frlg',footprint=[9,0,7,4],water=0x112b)]),
    dict(island='Two', town='TwoIsland_Frlg', ramp=[10,8], ramp_warp=3,
         roof=[8,9,5,3], clear=[8,9,5,3], water=0x112b),
    dict(island='Three', town='ThreeIsland_Port_Frlg', ramp=[12,13], ramp_warp=2,
         roof=[10,14,5,3], clear=[9,14,7,5], water=0x1273),
    dict(island='Four', town='FourIsland_Frlg', ramp=[10,28], ramp_warp=6,
         roof=[8,29,5,3], clear=[7,29,7,5], water=0x1273),
    dict(island='Five', town='FiveIsland_Frlg', ramp=[12,14], ramp_warp=0,
         roof=[10,15,5,3], clear=[10,15,5,3], water=0x112b),
    dict(island='Six', town='SixIsland_Frlg', ramp=[11,23], ramp_warp=0,
         roof=[9,24,5,3], clear=[8,24,7,5], water=0x1273),
    dict(island='Seven', town='SevenIsland_Frlg', ramp=[16,13], ramp_warp=3,
         roof=[14,14,5,3], clear=[13,14,7,5], water=0x1273),
]

# The native plain-ocean cliff family joins the western grass tongue to the
# existing southern mountain. Keep all three dry corridor columns intact.
TWO_RAMP_COAST = [(12,7,0x1523),(13,7,0x1523),(14,7,0x1521)] \
    + [(14,y,0x1528) for y in range(8,14)] \
    + [(14,14,0x1530),(15,14,0x1528)]


def finish(layer):
    def raw(p): return layer.outputs[p] if p in layer.outputs else (layer.source/p).read_bytes()
    layouts={l['id']:l for l in json.loads(raw('data/layouts/layouts.json'))['layouts']}
    records=[]
    def edit(name, changes, reason, **details):
        m=json.loads(raw(f'data/maps/{name}/map.json'));l=layouts[m['layout']];p=l['blockdata_filepath'];b=raw(p)
        v=list(struct.unpack('<'+'H'*(len(b)//2),b));cells=[]
        for x,y,value in changes:
            assert 0<=x<l['width'] and 0<=y<l['height']
            i=y*l['width']+x
            if v[i]!=value:cells.append([x,y,v[i],value]);v[i]=value
        if cells:layer.stage(p,struct.pack('<'+'H'*len(v),*v))
        records.append(dict(map=name,reason=reason,changed_cells=cells,**details))
    # Replant complete 2x2 FRLG trees, including both halves and the ground base.
    # The original dense forest used odd-column pairs; retaining x0/x1 after
    # clearing x2 therefore retained two unrelated halves, not one tree.
    def tree(x,y):
        return [(x+dx,y+dy,0x400+tile) for dy,pair in enumerate(
            [(0x1e,0x1f),(0x26,0x27)]) for dx,tile in enumerate(pair)]
    six=[(x,y,0x3001) for y in range(3,10) for x in range(9)]
    six += [(x,y,0x3001) for y in range(10,20) for x in range(2)]
    for y in [3,6]:
        for x in [0,2,4,6]:six.extend(tree(x,y))
    for x in [0,2,4]:six.extend(tree(x,9))
    for y in [12,16,20]:six.extend(tree(0,y))
    six += [(6,10,0x3001),(6,11,0x3001),(5,22,0x427),(6,22,0x426)]
    edit('SixIsland_Frlg',six,'Replant whole native trees around Clair with complete trunks and bases')
    edit('SixIsland_Frlg',[(23,10,0x427)],'Complete the right base of the isolated tree beside the Mart')
    # The terminal moved to its own coastal map, but every native town kept
    # obsolete roof art below its ramp. Remove each complete remnant and the
    # mismatched water pad where present, matching that coast's own texture.
    for ferry in OBSOLETE_FERRIES:
        town=ferry['town'];harbor=ferry['island']+'Island_Harbor_Frlg'
        city=json.loads(raw(f'data/maps/{town}/map.json'))
        terminal=json.loads(raw(f'data/maps/{harbor}/map.json'))
        ramp=city['warp_events'][ferry['ramp_warp']]
        assert [ramp['x'],ramp['y']]==ferry['ramp'] and ramp['elevation']==3
        assert ramp['dest_map']==terminal['id'] and ramp['dest_warp_id']=='0'
        back=terminal['warp_events'][0]
        assert [back['x'],back['y']]==[8,2] and back['elevation']==3
        assert back['dest_map']==city['id'] and back['dest_warp_id']==str(ferry['ramp_warp'])
        layout=layouts[city['layout']];width=layout['width']
        values=struct.unpack('<'+'H'*(width*layout['height']),raw(layout['blockdata_filepath']))
        rx,ry=ferry['ramp'];ramp_tiles=list(values[ry*width+rx-1:ry*width+rx+2])
        assert ramp_tiles==([0x32b4,0x32b5,0x32b6] if ferry['island'] in ['One','Two','Three']
                            else [0x32f8,0x32f9,0x32fa] if ferry['island'] in ['Four','Five']
                            else [0x32e3,0x32e4,0x32e5])
        x,y,w,h=ferry['clear']
        edit(town,[(xx,yy,ferry['water']) for yy in range(y,y+h) for xx in range(x,x+w)],
             'Remove the complete obsolete ferry roof and match the surrounding ocean; preserve the native ramp to the main terminal',
             obsolete_ferry_roof_removed=True,island=ferry['island'],roof_footprint=ferry['roof'],
             cleared_footprint=ferry['clear'],replacement_water_metatile=ferry['water'],
             ramp=ferry['ramp'],ramp_warp_id=ferry['ramp_warp'],ramp_metatiles=ramp_tiles,
             ramp_warp_unchanged=True,harbor=harbor,harbor_return=[8,2],harbor_return_warp_id=0,
             connected_remnants=ferry.get('connected_remnants',[]))
        for extension in ferry.get('connected_remnants',[]):
            neighbor=json.loads(raw(f'data/maps/{extension["map"]}/map.json'))
            assert dict(map=neighbor['id'],offset=0,direction='down') in city['connections']
            assert dict(map=city['id'],offset=0,direction='up') in neighbor['connections']
            x,y,w,h=extension['footprint']
            assert all(not(x<=event['x']<x+w and y<=event['y']<y+h)
                       for kind in ['object_events','warp_events','coord_events','bg_events'] for event in neighbor[kind])
            edit(extension['map'],[(xx,yy,extension['water']) for yy in range(y,y+h) for xx in range(x,x+w)],
                 'Remove the remaining obsolete terminal roof, walls and whole flagposts across the existing Treasure Beach seam',
                 obsolete_ferry_extension_removed=True,island=ferry['island'],parent_town=town,
                 cleared_footprint=extension['footprint'],replacement_water_metatile=extension['water'],
                 original_water_connection_preserved=True,events_and_warps_unchanged=True)
    # Close Two's exposed grass edge with a whole native cliff outline. These
    # are blocked ocean-edge tiles outside the dry corridor, with the same
    # plain-ocean palette as the surrounding 0x12B water (not the 0x273 bank).
    from collections import deque
    two=json.loads(raw('data/maps/TwoIsland_Frlg/map.json'));layout=layouts[two['layout']]
    width=layout['width'];before=list(struct.unpack('<'+'H'*(width*layout['height']),raw(layout['blockdata_filepath'])))
    after=before.copy()
    assert all(before[y*width+x]==0x112b for x,y,_ in TWO_RAMP_COAST)
    assert all(not any(o['x']==x and o['y']==y for o in two[kind])
               for x,y,_ in TWO_RAMP_COAST for kind in ['object_events','warp_events','coord_events','bg_events'])
    for x,y,tile in TWO_RAMP_COAST:after[y*width+x]=tile
    def model_path(values,start,goal,ocean=False):
        valid={i for i,t in enumerate(values) if not t&0xc00
               and (t==0x112b if ocean else t>>12==3)}
        first=start[1]*width+start[0];last=goal[1]*width+goal[0]
        assert first in valid and last in valid
        todo=deque([first]);parents={first:None}
        while todo and last not in parents:
            at=todo.popleft();xx,yy=at%width,at//width
            for nx,ny in [(xx-1,yy),(xx+1,yy),(xx,yy-1),(xx,yy+1)]:
                nxt=ny*width+nx
                if 0<=nx<width and 0<=ny<layout['height'] and nxt in valid and nxt not in parents:
                    parents[nxt]=at;todo.append(nxt)
        assert last in parents,('Two Island coast disconnects native access',start,goal)
        route=[];at=last
        while at is not None:route.append([at%width,at//width]);at=parents[at]
        return route[::-1]
    before_route=model_path(before,(10,7),(21,8));after_route=model_path(after,(10,7),(21,8))
    for goal in [(0,10),(8,19)]:model_path(after,(10,11),goal,ocean=True)
    assert all(after[y*width+x]==before[y*width+x] for y in range(7,14) for x in range(15,18))
    edit('TwoIsland_Frlg',TWO_RAMP_COAST,'Close the complete western ramp-side cliff without narrowing the native town corridor',
         two_ramp_coast_finished=True,native_plain_ocean_cliff_family=True,
         dry_corridor=[15,7,3,7],dry_corridor_unchanged=True,
         model_ramp_to_center_before=before_route,model_ramp_to_center_after=after_route,
         western_and_southern_surf_connected=True,events_and_warps_unchanged=True)
    # All seven existing return warps were ordinary sand and could never
    # activate. Give only those pads a private native north-arrow behavior,
    # retaining the exact sand artwork and every original warp destination.
    from render_sea_maps import MapRenderer
    renderer=MapRenderer(layer.source);slot=0x3fa
    for layout in layouts.values():
        if layout['secondary_tileset']!='gTileset_IslandHarbor_Frlg':continue
        values=struct.unpack('<'+'H'*(layout['width']*layout['height']),raw(layout['blockdata_filepath']))
        assert not any(t&1023==slot for t in values)
    folder='data/tilesets/secondary/island_harbor_frlg/'
    metas=bytearray(raw(folder+'metatiles.bin'));attrs=bytearray(raw(folder+'metatile_attributes.bin'))
    metas[(slot-640)*16:(slot-639)*16]=struct.pack('<8H',*renderer.tileset('gTileset_General_Frlg')[2][0x115*8:0x116*8])
    attrs[(slot-640)*4:(slot-639)*4]=struct.pack('<I',0x64) # MB_NORTH_ARROW_WARP, paired with the town's native 0x65 south arrow.
    layer.stage(folder+'metatiles.bin',metas);layer.stage(folder+'metatile_attributes.bin',attrs)
    for ferry in OBSOLETE_FERRIES:
        edit(ferry['island']+'Island_Harbor_Frlg',[(8,2,0x3000|slot)],
             'Activate the existing northbound ramp return without changing its sand artwork or warp destination',
             northbound_return_activated=True,island=ferry['island'],return_pad=[8,2],return_warp_id=0,
             native_north_arrow_metatile=slot,town=ferry['town'],town_ramp_warp_id=ferry['ramp_warp'])
    # Extend the grass apron to the existing eastern cliff, then close its
    # exposed side and bottom using the adjacent city's own contour pieces.
    lily=[(x,y,0x3001) for y in range(24,27) for x in [50,51]]
    lily += [(52,y,0x472) for y in range(24,27)]
    lily += [(x,27,0x479) for x in range(45,52)]+[(52,27,0x492)]
    edit('LilycoveCity',lily,'Close the gym courtyard eastern cliff and lower beach corner')
    # Lavender's former eastern mountain was moved to the new map edge,
    # exposing a raw cut beside the Tower. Keep the Tower's west-facing rock
    # side and join a solid mountain mass to the new boundary, closing its
    # entire front above Morty's courtyard. The gym starts two rows lower.
    lavender=[(x,y,0x475 if x==22 else 0x471) for y in range(7) for x in range(22,32)]
    lavender += [(22,7,0x47d),*[(x,7,0x479) for x in range(23,30)],(30,7,0x4b3),(31,7,0x471)]
    lavender += [(30,5,0x471),(30,6,0x471)]
    edit('LavenderTown_Frlg',lavender,'Restore the entire mountain beside the Tower and close its front above the gym')
    # The old rectangular clearing also touched the Center's left facade.
    # Restore its full original footprint, including the two lower wall tiles.
    # The two missing native wall/base cells are a complete vertical edge.
    edit('SixIsland_Frlg',[(9,11,0x460),(9,12,0x300f)],'Restore the Center left wall and ground; keep its entire facade clear')
    # Carve a coherent, one-level courtyard for Steven instead of inserting a
    # facade directly through the original diagonal mountain textures. Native
    # contour pieces close all three exposed sides; the eastern flower path
    # stays connected to the homes and Center.
    courtyard=[]
    for y in range(49,56):
        courtyard.append((6,y,0x485))
        for x in range(7,15):
            if not(8<=x<14 and 50<=y<55):courtyard.append((x,y,0x5001))
    courtyard.extend([(6,48,0x48b),*[(x,48,0x47c) for x in range(7,12)],(12,48,0x47a),
        (6,56,0x48d),*[(x,56,0x487) for x in range(7,14)],(14,56,0x48f)])
    edit('EverGrandeCity',courtyard,'Complete a level gym courtyard with continuous native cliff corners and an eastern access')
    # The first row of the lower forest was an interior overlap metatile. Give
    # all three new exposed trees their actual northern crown pair instead.
    edit('ThreeIsland_Frlg',[(x,20,0x41e+(x%2)) for x in range(0,6)],'Complete crowns below Karen\'s gym')
    # A single dense-forest fragment remained beside the new cliff corner.
    edit('SixIsland_Frlg',[(2,20,0x4b2),(3,20,0x4b4),(2,21,0x472),(2,22,0x47a)],'Finish the left cliff corner instead of leaving half a tree')
    # Two Island's older Surf layer overpainted the upper roof with its reef.
    # Restore the entire 7x6 terminal from the intact native One Island donor;
    # all seven terminals share precisely the same secondary bank.
    m=json.loads(raw('data/maps/OneIsland_Harbor_Frlg/map.json'));l=layouts[m['layout']]
    v=struct.unpack('<'+'H'*(l['width']*l['height']),raw(l['blockdata_filepath']))
    terminal=[(x,y,v[y*l['width']+x]) for y in range(6) for x in range(10,17)]
    for island in ['One','Two','Three','Four','Five','Six','Seven']:
        edit(island+'Island_Harbor_Frlg',terminal,'Retain the complete native terminal roof, walls and door')
    # The old reef was reversed: lower halves on row 11 and upper halves
    # on the final row. It also overpainted both occupied boat footprints.
    # Retain the same closed map edge with complete one-tile boulders, and
    # restore open water between the boats and the end of the pier.
    n='TwoIsland_Harbor_Frlg';m=json.loads(raw(f'data/maps/{n}/map.json'));l=layouts[m['layout']]
    port=next(p for p in json.loads(raw('.journey-sevii-harbors'))['ports'] if p['island']=='Two')
    hull={tuple(cell) for footprint in port['outside_hulls'] for cell in footprint}
    changes=[]
    for x in range(l['width']):
        changes.append((x,11,0x152b if (x,11) in hull else 0x1643 if x in [0,l['width']-1] else 0x112b))
        changes.append((x,12,0x1643))
    edit(n,changes,'Replace reversed half-rock borders with whole boulders and water under both complete boat hulls')
    return records
