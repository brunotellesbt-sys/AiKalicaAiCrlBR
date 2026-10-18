"""Finish native object footprints exposed by the extra-gym clearings.

These edits follow docs/design/proposta-gba-portos-ginasios.png. They never
move a door, NPC, connection or atlas pixel. Each replacement is a complete
native edge or object, rather than clearing a rectangle through its artwork.
"""
import json
import struct


def finish(layer):
    def raw(p): return layer.outputs[p] if p in layer.outputs else (layer.source/p).read_bytes()
    layouts={l['id']:l for l in json.loads(raw('data/layouts/layouts.json'))['layouts']}
    records=[]
    def edit(name, changes, reason):
        m=json.loads(raw(f'data/maps/{name}/map.json'));l=layouts[m['layout']];p=l['blockdata_filepath'];b=raw(p)
        v=list(struct.unpack('<'+'H'*(len(b)//2),b));cells=[]
        for x,y,value in changes:
            assert 0<=x<l['width'] and 0<=y<l['height']
            i=y*l['width']+x
            if v[i]!=value:cells.append([x,y,v[i],value]);v[i]=value
        if cells:layer.stage(p,struct.pack('<'+'H'*len(v),*v))
        records.append(dict(map=name,reason=reason,changed_cells=cells))
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
    # The original ferry art retained a roof below the town ramp after the
    # actual terminal moved to its own coastal map. Remove the entire obsolete
    # roof, retaining the native ramp warp and the single complete terminal.
    edit('SixIsland_Frlg',[(x,y,0x1273) for y in range(24,29) for x in range(8,15)],
         'Remove the obsolete ferry roof below the ramp; preserve access to the main terminal and its Surf network')
    # Its existing return warp was drawn as ordinary sand, so it could never
    # activate. Give only that pad a private copy with native north-arrow
    # behavior; retain the shared sand art and every other island's terrain.
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
    edit('SixIsland_Harbor_Frlg',[(8,2,0x3000|slot)],'Activate the existing northbound ramp return without changing its sand artwork')
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
