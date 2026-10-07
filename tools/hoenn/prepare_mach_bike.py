"""Single obtainable Mach Bike; native stairs/wood bridges replace Acro terrain."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
from prepare_crossing import PIN
from prepare_free_access import LAYERS


def prepare(source):
    source = Path(source)
    marker = source / '.journey-mach-bike'
    if marker.exists():
        report = json.loads(marker.read_text())
        for path, digest in report['prepared_sha256'].items():
            if hashlib.sha256((source / path).read_bytes()).hexdigest() != digest:
                raise ValueError('Modified bicycle output: ' + path)
        return report
    acquired = json.loads((source / '.source-acquired.json').read_text())
    assert acquired['commit'] == PIN
    expected = dict(acquired['sha256'])
    for layer in LAYERS + ['free-access', 'blue-gym', 'road-access']:
        expected.update(json.loads((source / f'.journey-{layer}').read_text())['prepared_sha256'])
    outputs, originals, inputs = {}, {}, {}

    def read(path):
        if path in outputs:
            return outputs[path]
        raw = (source / path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected[path], path
        if path in acquired['sha256']:
            inputs[path] = acquired['sha256'][path]
        return raw

    def stage(path, body):
        if path not in originals:
            originals[path] = hashlib.sha256(read(path)).hexdigest()
        outputs[path] = body if isinstance(body, bytes) else body.encode()

    layouts = json.loads(read('data/layouts/layouts.json'))['layouts']
    constants = read('include/constants/metatile_behaviors.h').decode()
    names = re.findall(r'^\s*(MB_\w+)', constants, re.M)
    targets = {i: n for i, n in enumerate(names) if n in
               ['MB_BUMPY_SLOPE', 'MB_ISOLATED_VERTICAL_RAIL', 'MB_ISOLATED_HORIZONTAL_RAIL',
                'MB_VERTICAL_RAIL', 'MB_HORIZONTAL_RAIL']}
    declarations = read('src/data/tilesets/metatiles.h').decode()
    attributes = dict(re.findall(r'const u(?:16|32) (\w+)\[\] = INCBIN_U(?:16|32)\("([^"]+)"\)', declarations))
    graphics = dict(re.findall(r'const u16 (\w+)\[\] = INCBIN_U16\("([^"]+/metatiles.bin)"\)', declarations))
    tilesets = {}
    for name, body in re.findall(r'const struct Tileset (\w+) =\s*\{(.*?)\};', read('src/data/tilesets/headers.h').decode(), re.S):
        tilesets[name] = (attributes[re.search(r'\.metatileAttributes = (\w+)', body)[1]],
                          graphics[re.search(r'\.metatiles = (\w+)', body)[1]])
    native_bridge = read('data/tilesets/secondary/fortree/metatiles.bin')[0x97 * 16:0x98 * 16]
    native_stairs = read('data/tilesets/primary/general/metatiles.bin')[0xE7 * 16:0xE8 * 16]
    # The bridge references only primary General tiles/palettes, so it can be
    # used by Safari and Jagged Pass without copying incompatible secondary art.
    assert all((v & 1023) < 512 and v >> 12 < 7 for v in struct.unpack('<8H', native_bridge))
    replacements, tile_definitions, audits, decorative = [], {}, [], []
    for layout in layouts:
        if layout['layout_version'] != 'emerald' or any(layout[k] not in tilesets for k in ['primary_tileset', 'secondary_tileset']):
            continue
        ap = [tilesets[layout[k]] for k in ['primary_tileset', 'secondary_tileset']]
        attrs = [struct.unpack('<' + 'H' * (len(read(a)) // 2), read(a)) for a, _ in ap]
        path = layout['blockdata_filepath']
        raw = read(path)
        values = list(struct.unpack('<' + 'H' * (len(raw) // 2), raw))
        audits.append(path)
        changed = False
        for i, tile in enumerate(values):
            mid = tile & 1023
            secondary = mid >= 512
            index = mid - (512 if secondary else 0)
            if index >= len(attrs[secondary]):
                continue
            behavior = attrs[secondary][index] & 255
            if behavior not in targets:
                continue
            x, y = i % layout['width'], i // layout['width']
            if behavior != names.index('MB_BUMPY_SLOPE') and (tile & 0xC00 or tile >> 12 == 1):
                decorative.append(dict(layout=layout['id'], x=x, y=y, tile=tile))
                continue
            kind = 'stairs' if targets[behavior] == 'MB_BUMPY_SLOPE' else 'wood_bridge'
            surface = None
            if kind == 'stairs' and layout['id'] == 'LAYOUT_JAGGED_PASS':
                # Acro hopping posts include a decoration on the upper floor.
                # Do not put a stair there. Use the actual yellow lateral stair
                # (Lavaridge 0x2AF) only on the cliff cells below that landing.
                surface = 'landing' if mid in [0x303, 0x2FE] else 'yellow_stair'
                new = 0x3271 if surface == 'landing' else 0x02AF
            else:
                tile_definitions[(ap[secondary][0], ap[secondary][1], index)] = kind
                # Elevation zero lets a staircase join original ledge levels.
                new = mid if kind == 'stairs' else tile & ~0xC00
            values[i] = new
            changed |= new != tile
            entry = dict(layout=layout['id'], x=x, y=y, before=tile, after=new, kind=kind)
            if surface:
                entry['surface'] = surface
            replacements.append(entry)
        if changed:
            stage(path, struct.pack('<' + 'H' * len(values), *values))
    for (attribute_path, graphics_path, index), kind in sorted(tile_definitions.items()):
        graphic = bytearray(read(graphics_path))
        graphic[index * 16:(index + 1) * 16] = native_stairs if kind == 'stairs' else native_bridge
        stage(graphics_path, bytes(graphic))
        attr = bytearray(read(attribute_path))
        # Stairs must draw below sprites, like the yellow native lateral stairs.
        # A normal top layer would paint the upper tread over the player's head.
        struct.pack_into('<H', attr, index * 2, 0x1000 if kind == 'stairs' else 0)
        stage(attribute_path, bytes(attr))
    # A one-tile gap formerly needed a side-hop. Complete the actual walkway.
    path = 'data/layouts/Route119/map.bin'
    data = bytearray(read(path))
    offset = (10 * 40 + 10) * 2
    before = struct.unpack_from('<H', data, offset)[0]
    assert before == 0x1606
    struct.pack_into('<H', data, offset, 0x40F1)
    stage(path, bytes(data))
    gap = dict(layout='LAYOUT_ROUTE119', x=10, y=10, before=before, after=0x40F1)
    # Both original bicycle quests now award the same item. No new mission is
    # invented, and possession works in either region's cycling entrance.
    path = 'data/maps/MauvilleCity_BikeShop/scripts.inc'
    body = read(path).decode()
    body = body.replace('MauvilleCity_BikeShop_EventScript_Rydel::\n\tlock\n\tfaceplayer\n',
                        'MauvilleCity_BikeShop_EventScript_Rydel::\n\tlock\n\tfaceplayer\n\tcheckitem ITEM_MACH_BIKE\n\tgoto_if_eq VAR_RESULT, TRUE, MauvilleCity_BikeShop_EventScript_KeepBike\n')
    start = body.index('MauvilleCity_BikeShop_EventScript_ChooseBike::')
    end = body.index('MauvilleCity_BikeShop_EventScript_NotFar::', start)
    body = body[:start] + 'MauvilleCity_BikeShop_EventScript_ChooseBike::\n\tgoto MauvilleCity_BikeShop_EventScript_GetMachBike\n\tend\n\n' + body[end:]
    body = body.replace('\tgoto_if_set FLAG_RECEIVED_BIKE, MauvilleCity_BikeShop_EventScript_AskSwitchBikes',
                        '\tgoto_if_set FLAG_RECEIVED_BIKE, MauvilleCity_BikeShop_EventScript_KeepBike')
    body = body.replace('ITEM_ACRO_BIKE', 'ITEM_MACH_BIKE')
    body = body.replace('\tspecial SwapRegisteredBike\n', '')
    start = body.index('MauvilleCity_BikeShop_EventScript_AcroBikeHandbook::')
    end = body.index('\n\n', start)
    body = body[:start] + 'MauvilleCity_BikeShop_EventScript_AcroBikeHandbook::\n\tgoto MauvilleCity_BikeShop_EventScript_MachBikeHandbook\n\tend' + body[end:]
    for label, text in {
        'ComeBackToSwitchBikes': ['This MACH BIKE works in both regions.', 'The old rails are now safe bridges!'],
        'HandbooksAreInBack': ['The MACH BIKE handbook is in back.', 'Stairs replace the old jumping paths.'],
        'HappyYouLikeIt': ['Keep enjoying your MACH BIKE!', 'Ride safely in KANTO and HOENN.'],
    }.items():
        key = 'MauvilleCity_BikeShop_Text_' + label
        replacement = key + ':\n' + ''.join('\t.string "' + line + ('\\n' if i == 0 else '$') + '"\n' for i, line in enumerate(text)) + '\n'
        body, n = re.subn(key + r':\n.*?(?=\n\w+:|\Z)', lambda m: replacement, body, flags=re.S)
        assert n == 1, key
    stage(path, body)
    path = 'data/maps/CeruleanCity_BikeShop_Frlg/scripts.inc'
    body = read(path).decode().replace('ITEM_BICYCLE', 'ITEM_MACH_BIKE')
    body = body.replace('CeruleanCity_BikeShop_EventScript_Clerk::\n\tlock\n\tfaceplayer\n',
                        'CeruleanCity_BikeShop_EventScript_Clerk::\n\tlock\n\tfaceplayer\n\tcheckitem ITEM_MACH_BIKE\n\tgoto_if_eq VAR_RESULT, TRUE, CeruleanCity_BikeShop_EventScript_AlreadyGotBicycle\n')
    stage(path, body)
    path = 'data/maps/JaggedPass/scripts.inc'
    body = read(path).decode().replace("If I had an ACRO BIKE, I'd be able to", 'The new stairs let everyone').replace('jump ledges.$', 'climb these ledges safely.$').replace('I should get an ACRO BIKE from RYDEL', 'RYDEL gives out a speedy MACH BIKE')
    stage(path, body)
    entrances = []
    def quest_text(body, label):
        text = label + '::\n\t.string "Get a MACH BIKE from RYDEL\\n"\n\t.string "in MAUVILLE, or exchange a\\p"\n\t.string "BIKE VOUCHER in CERULEAN.\\n"\n\t.string "Then this road will be open!$"\n\n'
        body, n = re.subn(label + r'::?\n.*?(?=\n\w+:|\Z)', lambda m: text, body, flags=re.S)
        assert n == 1, label
        return body
    for prefix in ['Route16_NorthEntrance_1F', 'Route18_EastEntrance_1F']:
        path = f'data/maps/{prefix}_Frlg/scripts.inc'
        body = read(path).decode()
        old = f'\tcall_if_set FLAG_GOT_BICYCLE, {prefix}_EventScript_DisableNeedBikeTrigger'
        assert body.count(old) == 1
        body = body.replace(old, '\tcheckitem ITEM_MACH_BIKE\n' + f'\tcall_if_eq VAR_RESULT, TRUE, {prefix}_EventScript_DisableNeedBikeTrigger')
        label = prefix + '_Text_' + ('NoPedestriansOnCyclingRoad' if prefix.startswith('Route16') else 'NeedBicycleForCyclingRoad')
        stage(path, quest_text(body, label))
        entrances.append(prefix + '_Frlg')
    for side in ['North', 'South']:
        name = f'Route110_SeasideCyclingRoad{side}Entrance'
        path = f'data/maps/{name}/scripts.inc'
        body = read(path).decode()
        old = f'\tgoto_if_eq VAR_RESULT, 0, {name}_EventScript_NoBike'
        assert body.count(old) == 1
        body = body.replace(old, f'\tgoto_if_eq VAR_RESULT, 0, {name}_EventScript_CheckOwnedBike')
        body += f'''\n{name}_EventScript_CheckOwnedBike::
\tcheckitem ITEM_MACH_BIKE
\tgoto_if_eq VAR_RESULT, FALSE, {name}_EventScript_NoBike
\tclearflag FLAG_SYS_CYCLING_ROAD
\tsetvar VAR_TEMP_1, 1
\treleaseall
\tend
'''
        stage(path, quest_text(body, name + '_Text_TooDangerousToWalk'))
        entrances.append(name)
    # Compatibility-only item IDs must also ride as Mach, never as Acro.
    path = 'src/data/items.h'
    body = read(path).decode()
    for item in ['ITEM_BICYCLE', 'ITEM_ACRO_BIKE']:
        pattern = r'(\[' + item + r'\] =\s*\{.*?\.secondaryId = )\w+(,)'
        body, n = re.subn(pattern, r'\g<1>MACH_BIKE\2', body, flags=re.S)
        assert n == 1
    stage(path, body)
    for path, raw in outputs.items():
        (source / path).write_bytes(raw)
    report = dict(status='mach_only_bicycle_candidate', source_commit=PIN, replacements=replacements,
                  completed_bridge_gaps=[gap], decorative_under_bridge_tiles_preserved=decorative,
                  audited_layouts=audits, cycling_entrances=entrances,
                  bicycle_quests=['Rydel in Mauville', 'Bike Voucher exchange in Cerulean'],
                  only_obtainable_bike='ITEM_MACH_BIKE', stairs_draw_below_player=True,
                  jagged_pass_stair_reference=0x2AF, jagged_pass_landing_reference=0x271,
                  upper_floor_stair_decorations_removed=5,
                  regional_gym_scaling_unchanged=True,
                  requires_new_save=True, full_story_validated=False, input_sha256=inputs,
                  original_sha256=originals, prepared_sha256={p: hashlib.sha256(v).hexdigest() for p, v in outputs.items()})
    marker.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    report = prepare(args.source)
    print(json.dumps(dict(replacements=len(report['replacements']), outputs=len(report['prepared_sha256']))))
