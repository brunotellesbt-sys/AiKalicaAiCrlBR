"""Authenticate whole parent scenery and stage explicit physical relocations.

Nothing here infers geography from the parent's interpolated GPS.  Terrain
components, full bank identities and events are extracted from immutable
native inputs.  The caller reserves non-overlapping rectangles in the affine
atlas mesh and supplies their explicit global placement before staging.
"""
from __future__ import annotations

from collections import Counter, deque
import copy
import hashlib
import json
from pathlib import Path
import re
import struct

from atlas_surf_source import CARDINAL
from atlas_surf_object_ids import native_local_id, validate_object_ids, stage_object_id_backend
from badge_story_layer import read

EVENT_FIELDS = ("object_events", "warp_events", "coord_events", "bg_events")


def _digest(value):
    return hashlib.sha256(value).hexdigest()


def _json_digest(value):
    return _digest(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def _runs(cells):
    rows = {}
    for x,y in cells:
        rows.setdefault(y,[]).append(x)
    result = []
    for y,points in sorted(rows.items()):
        points = sorted(set(points))
        if not points:
            continue
        start = previous = points[0]
        for x in points[1:]:
            if x != previous+1:
                result.append([y,start,previous+1])
                start=x
            previous=x
        result.append([y,start,previous+1])
    return result


def bank_provenance(inputs, name):
    """Bind metatile numbers to their full native bank, graphics and callbacks."""
    layout = inputs.layout(name)
    headers = inputs.read("src/data/tilesets/headers.h").decode()
    definitions = {path: inputs.read(path).decode() for path in
                   ("src/data/tilesets/metatiles.h", "src/data/tilesets/graphics.h", "src/data/tilesets/palettes.h", "src/graphics.c")
                   if (inputs.source / path).is_file()}
    records = []
    for bank in (layout["primary_tileset"], layout["secondary_tileset"]):
        match = re.search(r"const struct Tileset " + re.escape(bank) + r"\s*=\s*\{(.*?)\};", headers, re.S)
        if match is None:
            raise ValueError(("Scenery has no native tileset definition", name, bank))
        body = match[1]
        assets = {}
        for field in ("tiles", "palettes", "metatiles", "metatileAttributes"):
            symbol = re.search(r"\." + field + r"\s*=\s*(\w+)", body)
            if symbol is None:
                raise ValueError(("Native bank field missing", bank, field))
            found = False
            for text in definitions.values():
                declaration = re.search(r"\b" + re.escape(symbol[1]) + r"\s*\[[^;]*?;", text, re.S)
                if declaration is None:
                    continue
                found = True
                for relative in re.findall(r'"([^"\n]+)"', declaration[0]):
                    candidate = relative
                    # Generated .4bpp files are absent before builds. The PNG
                    # is the authenticated native input to that conversion.
                    if not (inputs.source / candidate).is_file():
                        candidate = re.sub(r"\.4bpp(?:\.\w+)*$", ".png", candidate)
                        candidate = re.sub(r"\.gbapal(?:\.\w+)*$", ".pal", candidate)
                    if not (inputs.source / candidate).is_file():
                        raise ValueError(("Missing native bank asset", bank, relative))
                    assets[candidate] = _digest(inputs.read(candidate))
            if not found:
                raise ValueError(("Cannot authenticate native bank symbol", bank, symbol[1]))
        callback = re.search(r"\.callback\s*=\s*(\w+)", body)
        callback_name = callback[1] if callback else "NULL"
        callback_inputs = {}
        if callback_name != "NULL":
            # Record both animation implementation and data references. This
            # prevents equal static metatile words from hiding a bank change.
            for relative in ("src/tileset_anims.c", "src/data/tilesets/tileset_anims.h"):
                if (inputs.source / relative).is_file():
                    callback_inputs[relative] = _digest(inputs.read(relative))
        records.append(dict(symbol=bank, header_sha256=_digest(body.encode()),
                            assets_sha256=assets, callback=callback_name,
                            callback_inputs_sha256=callback_inputs))
    value = dict(layout_version=layout["layout_version"],
                 primary=layout["primary_tileset"], secondary=layout["secondary_tileset"], banks=records)
    value["signature"] = _json_digest(value)
    return value


def _components(points):
    """Eight neighbors conservatively keep diagonal quarters in one object."""
    todo = set(points)
    result = []
    while todo:
        seed = min(todo, key=lambda point: (point[1], point[0]))
        todo.remove(seed)
        queue = deque([seed])
        cells = {seed}
        while queue:
            x, y = queue.popleft()
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    target = x + dx, y + dy
                    if target in todo:
                        todo.remove(target)
                        cells.add(target)
                        queue.append(target)
        result.append(cells)
    return result


def component_inventory(words, width, height, pure_water, events):
    """Separate whole terrain from perimeter reef without guessing metatile IDs.

    Distinct water-looking art remains in scenery: a Surf behavior alone is
    insufficient to call a beach, cliff or animated overlay plain ocean.
    """
    if len(words) != width * height:
        raise ValueError("Scenery grid does not match its dimensions")
    candidates = {(x, y) for y in range(height) for x in range(width)
                  if words[y * width + x] != pure_water}
    event_points = {(event["x"], event["y"]) for field in EVENT_FIELDS for event in events.get(field, [])}
    components, boundaries = [], []
    for cells in _components(candidates):
        touches_edge = any(x in (0, width-1) or y in (0, height-1) for x, y in cells)
        dry = any(words[y * width + x] >> 12 >= 3 for x, y in cells)
        event = bool(cells & event_points)
        if touches_edge and not dry and not event:
            boundaries.append(cells)
        else:
            components.append(dict(cells=cells, touches_parent_edge=touches_edge, has_dry_terrain=dry))
    return components, boundaries


def _sprite_provenance(inputs, renderer, event):
    graphic = event.get("graphics_id")
    if not graphic:
        raise ValueError("Native object event lacks graphics identity")
    sprite = renderer.sprite(graphic)
    record = copy.deepcopy(renderer.sprite_sources[graphic + "#0"])
    record["pixels_sha256"] = _digest(sprite.tobytes())
    record["offset"] = renderer.sprite_offset(graphic)
    paths = ["src/data/object_events/object_event_graphics_info.h",
             "src/data/object_events/object_event_graphics_info_pointers.h",
             "src/data/object_events/object_event_pic_tables.h",
             "src/data/object_events/object_event_graphics.h"]
    for field in ("graphic_source", "palette_source"):
        path = record[field]
        if ":" not in path:
            paths.append(path)
    record["input_sha256"] = {path: _digest(inputs.read(path)) for path in paths}
    return record


def extract_stamps(inputs, names, *, authenticate_sprites=True):
    """Extract every interior scenery component and every event exactly once.

    Water-only actors become explicit one-cell stamps. Boundary reef is
    inventoried separately for the new coherent perimeter. Cave interiors
    and native ports are not copied or regenerated here.
    """
    renderer = None
    if authenticate_sprites:
        from render_sea_maps import MapRenderer
        renderer = MapRenderer(inputs.source)
    banks, stamps, excluded_boundaries, maps = {}, [], [], []
    for name in sorted(names):
        mapping, layout = inputs.maps[name], inputs.layout(name)
        width, height = layout["width"], layout["height"]
        words = inputs.words(name)
        wet = Counter(word for at, word in enumerate(words)
                      if not word & 0xC00 and inputs.water(name, at % width, at // width))
        if not wet:
            raise ValueError(("Retired marine map has no witnessed plain water", name))
        pure_water = wet.most_common(1)[0][0]
        if pure_water >> 12 not in (0, 1):
            raise ValueError(("Unreviewed base-water height", name, pure_water))
        key = (layout["layout_version"], layout["primary_tileset"], layout["secondary_tileset"])
        if key not in banks:
            banks[key] = bank_provenance(inputs, name)
        provenance = banks[key]
        events = {field: copy.deepcopy(mapping.get(field) or []) for field in EVENT_FIELDS}
        components, boundaries = component_inventory(words, width, height, pure_water, events)
        # Attach each event to its terrain component. Ocean actors whose
        # anchor is plain water retain their exact full actor as a separate POI.
        assigned = set()
        for component in components:
            cells = component["cells"]
            component["events"] = []
            for field in EVENT_FIELDS:
                for index, event in enumerate(events[field]):
                    if (event["x"], event["y"]) in cells:
                        component["events"].append(dict(field=field, source_index=index, event=event))
                        assigned.add((field, index))
        for field in EVENT_FIELDS:
            for index, event in enumerate(events[field]):
                if (field, index) not in assigned:
                    components.append(dict(cells={(event["x"], event["y"])},
                                           touches_parent_edge=False, has_dry_terrain=False,
                                           events=[dict(field=field, source_index=index, event=event)],
                                           actor_only=True))
        for index, component in enumerate(components):
            core = component["cells"]
            left, top = min(x for x, _ in core), min(y for _, y in core)
            right, bottom = max(x for x, _ in core) + 1, max(y for _, y in core) + 1
            associated = component["events"]
            warps = [row for row in associated if row["field"] == "warp_events"]
            anchor = ((warps[0]["event"]["x"], warps[0]["event"]["y"]) if warps else
                      (associated[0]["event"]["x"], associated[0]["event"]["y"]) if associated else
                      min(core, key=lambda p: (abs(2*p[0]-(left+right-1))+abs(2*p[1]-(top+bottom-1)), p[1], p[0])))
            rows = []
            for row in associated:
                event = copy.deepcopy(row["event"])
                record = dict(field=row["field"], source_index=row["source_index"],
                              source_local_id=native_local_id(event,row["source_index"]) if row["field"] == "object_events" else None,
                              event=event, offset=[event["x"]-left, event["y"]-top])
                if row["field"] == "object_events":
                    record["sprite"] = _sprite_provenance(inputs, renderer, event) if renderer else None
                rows.append(record)
            rectangular_words = [words[y*width+x] for y in range(top, bottom) for x in range(left, right)]
            value = dict(key=f"{name}:{index:03}", parent_map=name, parent_map_id=mapping["id"],
                         source_rect=[left, top, right-left, bottom-top],
                         source_anchor=list(anchor), anchor_offset=[anchor[0]-left, anchor[1]-top],
                         bank_signature=provenance["signature"],
                         banks=[layout["primary_tileset"], layout["secondary_tileset"]],
                         layout_version=layout["layout_version"], pure_water_word=pure_water,
                         words=rectangular_words,
                         native_water_runs=_runs((x-left,y-top) for y in range(top,bottom)
                                                 for x in range(left,right) if inputs.water(name,x,y)),
                         words_sha256=_digest(struct.pack("<"+"H"*len(rectangular_words), *rectangular_words)),
                         core_cells=[[x-left,y-top] for x,y in sorted(core, key=lambda p:(p[1],p[0]))],
                         has_dry_terrain=component["has_dry_terrain"],
                         touches_parent_edge=component["touches_parent_edge"],
                         kind="water-actor" if component.get("actor_only") else "portal-scenery" if warps else
                              "land-scenery" if component["has_dry_terrain"] else "water-decoration",
                         events=rows, sprite_sources_authenticated=authenticate_sprites,
                         placement_assigned=False, native_validated=False)
            value["stamp_sha256"] = _json_digest(value)
            stamps.append(value)
        for cells in boundaries:
            excluded_boundaries.append(dict(map=name, cells=len(cells),
                                            component_sha256=_json_digest(sorted(cells)),
                                            reason="edge-connected reef, no dry terrain or event; regenerate coherent boundary"))
        maps.append(dict(map=name, bank_signature=provenance["signature"],
                         base_water_word=pure_water, terrain_components=len(components),
                         boundary_components=len(boundaries),
                         events={field: len(events[field]) for field in EVENT_FIELDS}))
    inputs.assert_unchanged()
    counts = Counter(stamp["kind"] for stamp in stamps)
    return dict(schema="atlas-parent-scenery/v1", stamps=stamps,
                banks={value["signature"]: value for value in banks.values()}, maps=maps,
                excluded_boundaries=excluded_boundaries,
                counts=dict(stamps=len(stamps), maps=len(maps), boundaries=len(excluded_boundaries), **counts),
                input_sha256=copy.deepcopy(inputs.inputs), source_unchanged=True,
                art_changed=False, placements_assigned=False, native_validated=False)


def placement(stamp, global_anchor, *, name, atlas_anchor=None, halo=9):
    """Describe an exclusive affine reservation preserving the *whole* stamp."""
    if len(global_anchor) != 2 or any(type(value) is not int for value in global_anchor):
        raise ValueError("Scenery anchor must be an explicit global game-tile pair")
    if type(halo) is not int or halo < 0:
        raise ValueError("Whole-scenery camera halo must be a non-negative tile count")
    width, height = (value+2*halo for value in stamp["source_rect"][2:])
    if max(width,height)>127:
        raise ValueError(("Whole scenery with camera halo exceeds native map dimensions",stamp["key"],width,height))
    origin = [global_anchor[axis]-stamp["anchor_offset"][axis]-halo for axis in range(2)]
    return dict(name=name, origin=origin, width=width, height=height,
                kind="cave" if stamp["kind"]=="portal-scenery" else "stamp",
                scenery_kind=stamp["kind"],camera_halo=halo,stamp_offset=[halo,halo],
                stamp=stamp["key"], stamp_sha256=stamp["stamp_sha256"],
                source_rect=stamp["source_rect"], ecology_owner=stamp["parent_map"],
                donor=stamp["parent_map"], bank_signature=stamp["bank_signature"],
                evidence=dict(parent_map=stamp["parent_map"],source_rect=stamp["source_rect"],
                              stamp_sha256=stamp["stamp_sha256"],word_sha256=stamp["words_sha256"]),
                global_anchor=list(global_anchor), fixed_atlas=atlas_anchor,
                whole_component_preserved=True, events=copy.deepcopy(stamp["events"]))


def bind_native_water(row, stamp, route_water):
    """Give a reservation its actual water mask, preserving the complete island.

    The nine-tile halo uses only the atlas corridor's water. The copied native
    rectangle uses its native terrain mask, including dry cave thresholds and
    beach fringe. Any obstruction of the main corridor remains explicit data
    for SCC/physical validation; this function never calls dry land water.
    """
    row = copy.deepcopy(row)
    ox,oy = row["origin"]
    sx,sy = row["stamp_offset"]
    w,h = stamp["source_rect"][2:]
    native = {(sx+x,sy+y) for y,start,end in stamp["native_water_runs"] for x in range(start,end)}
    cells = {(x-ox,y-oy) for x,y in route_water if ox<=x<ox+row["width"] and oy<=y<oy+row["height"]
             and not (sx<=x-ox<sx+w and sy<=y-oy<sy+h)} | native
    row["reserved_water_policy"] = "native"
    row["water_runs"] = _runs(cells)
    row["additional_water_runs"] = _runs(cells)
    row["native_water_evidence"] = dict(parent_map=stamp["parent_map"],source_rect=stamp["source_rect"],
                                        stamp_sha256=stamp["stamp_sha256"],native_water_runs=stamp["native_water_runs"],
                                        camera_halo_water_is_atlas_only=True)
    actual_global = {(ox+x,oy+y) for x,y in cells}
    row["route_water_obstructed"] = [list(point) for point in sorted(
        {point for point in route_water if ox<=point[0]<ox+row["width"] and oy<=point[1]<oy+row["height"]}
        - actual_global)]
    return row


def fixed_portal_placements(inputs, inventory, portals, route_water, *, existing=(), halo=9):
    """Create whole cave reservations inside their unchanged fixed atlas pixels.

    Each of the 64 subpixel tile phases is a legitimate affine location in the
    *same* icon. Pick the phase with least protected-corridor obstruction and
    reject rectangle overlap. Residual obstructions stay explicit for the
    integration's source/SCC/native proofs, never reclassified as water.
    """
    by_warp = {}
    for stamp in inventory["stamps"]:
        for row in stamp["events"]:
            if row["field"] == "warp_events":
                key = stamp["parent_map"],row["source_index"]
                if key in by_warp:
                    raise ValueError(("A portal belongs to multiple whole scenery stamps",key))
                by_warp[key]=stamp
    result, conflicts = [], []
    occupied = list(existing)
    for index,portal in enumerate(portals):
        key = portal["surface"],portal["surface_warp"]
        if key not in by_warp:
            raise ValueError(("Fixed portal has no authenticated scenery stamp",key))
        stamp = by_warp[key]
        anchor = inputs.anchors()[portal["interior"]]["atlas"]
        if anchor != portal["fixed_atlas"]:
            raise ValueError(("Portal atlas changed after parent inventory",key))
        if stamp["source_anchor"] != portal["surface_entry"]["tile"]:
            raise ValueError(("Whole stamp contains multiple/floating portal anchors",key))
        candidates = []
        for dy in range(8):
            for dx in range(8):
                row = placement(stamp,[8*anchor[0]+dx,8*anchor[1]+dy],
                                name=f"JourneyAtlasCave{index:02}",atlas_anchor=anchor,halo=halo)
                x,y=row["origin"];w,h=row["width"],row["height"]
                if any(max(x,old["origin"][0])<min(x+w,old["origin"][0]+old["width"])
                       and max(y,old["origin"][1])<min(y+h,old["origin"][1]+old["height"])
                       for old in occupied):
                    continue
                row=bind_native_water(row,stamp,route_water)
                row["evidence"]["fixed_portal"]=copy.deepcopy(portal)
                # Favor a centered phase only after minimizing real physical
                # obstruction. This changes neither icon nor atlas array.
                score=(len(row["route_water_obstructed"]),abs(dx-4)+abs(dy-4),dy,dx)
                candidates.append((score,row))
        if not candidates:
            raise ValueError(("Whole fixed cave and camera halo overlap another reservation",key))
        score,row=min(candidates,key=lambda item:item[0])
        result.append(row);occupied.append(row)
        if score[0]:
            conflicts.append(dict(stamp=stamp["key"],interior=portal["interior"],
                                  atlas=anchor,obstructed_route_water=score[0]))
    inputs.assert_unchanged()
    return dict(reservations=result,route_conflicts=conflicts,
                fixed_icon_anchors_preserved=True,art_changed=False,
                source_routing_proven=False,native_validated=False)


def check_placements(stamps, placements, *, core_corridor=(), allow_corridor_overrides=()):
    """Reject cropped scenery, overlaps and silently blocked six-tile corridors."""
    lookup = {stamp["key"]: stamp for stamp in stamps}
    occupied, seen, conflicts, groups, cores = {}, set(), [], {}, {}
    corridor = set(map(tuple, core_corridor))
    overrides = set(map(tuple, allow_corridor_overrides))
    for row in placements:
        if row["stamp"] not in lookup or row["stamp"] in seen:
            raise ValueError(("Unknown or duplicate scenery placement", row["stamp"]))
        stamp = lookup[row["stamp"]]
        seen.add(row["stamp"])
        frozen = {key:value for key,value in stamp.items() if key!="stamp_sha256"}
        if _json_digest(frozen) != stamp["stamp_sha256"]:
            raise ValueError(("Authenticated scenery content changed",row["stamp"]))
        if row["stamp_sha256"] != stamp["stamp_sha256"] or row["source_rect"] != stamp["source_rect"]:
            raise ValueError(("Scenery stamp changed/cropped after authentication", row["stamp"]))
        width, height = stamp["source_rect"][2:]
        halo = row.get("camera_halo",0)
        sx,sy=row.get("stamp_offset",[0,0])
        shared=row.get('shared_reservation') is True
        if shared:
            shape_ok=(row['kind']=='stamp' and 1<=row['width']<=127 and 1<=row['height']<=127
                      and sx>=halo and sy>=halo and sx+width+halo<=row['width']
                      and sy+height+halo<=row['height']
                      and row.get('component_global_rect')==[row['origin'][0]+sx,row['origin'][1]+sy,width,height])
            signature=(tuple(row['origin']),row['width'],row['height'],row['bank_signature'],row['ecology_owner'])
            if row['name'] in groups and groups[row['name']]!=signature:
                raise ValueError(('Shared scenery reservation identity or bank changed',row['name']))
            groups[row['name']]=signature
        else:
            shape_ok=((row["width"],row["height"])==(width+2*halo,height+2*halo) and [sx,sy]==[halo,halo])
        if not shape_ok or row["bank_signature"] != stamp["bank_signature"]:
            raise ValueError(("Scenery dimensions or bank changed", row["stamp"]))
        if row.get("fixed_atlas") is not None:
            if [value//8 for value in row["global_anchor"]] != row["fixed_atlas"]:
                raise ValueError(("Fixed cave anchor moved off original atlas icon", row["stamp"]))
        for y in range(sy,sy+height):
            for x in range(sx,sx+width):
                point=row['origin'][0]+x,row['origin'][1]+y
                if point in cores:
                    raise ValueError(('Native whole scenery cores overlap',row['stamp'],cores[point],point))
                cores[point]=row['stamp']
        for y in range(row["height"]):
            for x in range(row["width"]):
                point = row["origin"][0]+x, row["origin"][1]+y
                if point in occupied and not (shared and occupied[point]==row['name']):
                    raise ValueError(("Exclusive scenery rectangles overlap", row["stamp"], occupied[point], point))
                occupied[point] = row['name'] if shared else row["stamp"]
                local_x,local_y=x-sx,y-sy
                word = stamp["words"][local_y*width+local_x] if 0<=local_x<width and 0<=local_y<height else stamp["pure_water_word"]
                if point in corridor-overrides and word != stamp["pure_water_word"]:
                    conflicts.append(dict(stamp=row["stamp"], tile=list(point), word=word))
    if conflicts:
        raise ValueError(("Whole scenery conflicts with the protected six-tile corridor", conflicts[:12], len(conflicts)))
    return dict(placements=len(placements), exclusive_cells=len(occupied),
                unplaced_stamps=sorted(set(lookup)-seen), core_corridor_preserved=True,
                explicit_corridor_override_cells=sorted(map(list, overrides)),
                native_validated=False)


def stage_placements(layer, inputs, inventory, placements, *, allow_local_id_reindex=()):
    """Apply whole terrain/events to already-reserved maps with identical banks.

    Returns every old-to-new event identity for migration/script audits. Warp
    references across the entire source are repointed, including cave returns.
    Numeric object/clone IDs survive array reordering through native_local_id
    and the staged mapjson backend. ``local_id`` stays the native macro name.
    The old allow_local_id_reindex argument is accepted for compatibility but
    cannot authorize a numeric ID change. Script/flag identity is preserved.
    """
    stamps = {row["key"]: row for row in inventory["stamps"]}
    check_placements(inventory["stamps"], placements)
    layouts = {row["id"]: row for row in json.loads(read(layer,"data/layouts/layouts.json"))["layouts"]}
    mappings, values, old_to_new = {}, {}, {}
    deprecated_allowlist = tuple(allow_local_id_reindex)
    object_ids = []
    def mapping(name):
        if name not in mappings:
            mappings[name] = json.loads(read(layer,f"data/maps/{name}/map.json"))
        return mappings[name]
    for row in placements:
        stamp = stamps[row["stamp"]]
        target_name = row["name"]
        target = mapping(target_name)
        layout = layouts[target["layout"]]
        if [layout["primary_tileset"],layout["secondary_tileset"]] != stamp["banks"] or layout["layout_version"] != stamp["layout_version"]:
            raise ValueError(("Cannot copy metatile IDs into different native banks", stamp["key"], target_name))
        if (layout["width"],layout["height"]) != (row["width"],row["height"]):
            raise ValueError(("Reserved source map does not fit whole scenery rectangle", stamp["key"], target_name))
        path = layout["blockdata_filepath"]
        original_raw = values[path] if path in values else read(layer,path)
        original_words = list(struct.unpack("<"+"H"*(layout["width"]*layout["height"]),original_raw))
        sw,sh=stamp["source_rect"][2:]
        sx,sy=row.get("stamp_offset",[0,0])
        for y in range(sh):
            original_words[(y+sy)*layout["width"]+sx:(y+sy)*layout["width"]+sx+sw] = stamp["words"][y*sw:(y+1)*sw]
        values[path] = struct.pack("<"+"H"*len(original_words), *original_words)
        left, top = stamp["source_rect"][:2]
        for event_row in stamp["events"]:
            field, index = event_row["field"], event_row["source_index"]
            original = inputs.maps[stamp["parent_map"]].get(field,[])
            if not 0 <= index < len(original) or original[index] != event_row["event"]:
                raise ValueError(("Parent event changed since scenery extraction", stamp["key"], field, index))
            existing = target.setdefault(field,[])
            new_index = len(existing)
            event = copy.deepcopy(event_row["event"])
            numeric_id = None
            if field == "object_events":
                validate_object_ids(original)
                numeric_id = native_local_id(event,index)
                if event_row.get("source_local_id",numeric_id) != numeric_id:
                    raise ValueError(("Authenticated source object local ID changed",stamp["parent_map"],index))
                if numeric_id in validate_object_ids(existing):
                    raise ValueError(("Relocated native object local-ID collision",target_name,numeric_id))
                event["native_local_id"] = numeric_id
            event["x"] += sx-left
            event["y"] += sy-top
            existing.append(event)
            key = stamp["parent_map"],field,index
            if key in old_to_new:
                raise ValueError(("Parent event relocated twice", key))
            old_to_new[key] = dict(source_map=stamp["parent_map"],field=field,source_index=index,
                                   source_tile=[event_row["event"]["x"],event_row["event"]["y"]],
                                   target_map=target_name,target_map_id=target["id"],target_index=new_index,
                                   target_tile=[event["x"],event["y"]],
                                   global_tile=[row["origin"][0]+event["x"],row["origin"][1]+event["y"]])
            if numeric_id is not None:
                old_to_new[key].update(source_local_id=numeric_id,target_local_id=numeric_id)
                object_ids.append(dict(source_map=stamp["parent_map"],source_index=index,
                    target_map=target_name,target_index=new_index,native_local_id=numeric_id))
    # Apply reciprocal and other incoming warp references using the original
    # identities. Never assume a cave's sole return is numbered zero.
    by_id = inputs.by_id
    warp_references = []
    all_names = set(inputs.maps) | set(mappings)
    for name in sorted(all_names):
        current = mapping(name)
        for index, event in enumerate(current.get("warp_events") or []):
            parent_name = by_id.get(event["dest_map"])
            if not any(key[0] == parent_name and key[1] == "warp_events" for key in old_to_new):
                continue
            try:
                warp_index = int(event["dest_warp_id"])
            except (TypeError,ValueError) as error:
                raise ValueError(("Relocated warp has a non-numeric incoming reference",name,index,event)) from error
            key = parent_name,"warp_events",warp_index
            if key in old_to_new:
                replacement = old_to_new[key]
                before = copy.deepcopy(event)
                event["dest_map"] = replacement["target_map_id"]
                event["dest_warp_id"] = str(replacement["target_index"])
                warp_references.append(dict(map=name,index=index,before=before,after=copy.deepcopy(event)))
    inputs.assert_unchanged()
    backend = stage_object_id_backend(layer) if object_ids else None
    for path, blob in values.items():
        layer.stage(path,blob)
    for name, current in mappings.items():
        path = f"data/maps/{name}/map.json"
        original = read(layer,path)
        blob = (json.dumps(current,indent=2)+"\n").encode()
        if json.loads(original) != current:
            layer.stage(path,blob)
    return dict(kind="whole-scenery-and-event-relocation", placements=len(placements),
                relocated_events=list(old_to_new.values()), incoming_warps_repointed=warp_references,
                historical_source_preserved=True, source_events_cleared_by_retirement_stage=False,
                object_numeric_ids_preserved=True,relocated_object_ids=object_ids,
                source_index_is_not_local_id=True,native_object_id_backend=backend,
                deprecated_local_id_reindex_allowlist_ignored=bool(deprecated_allowlist),
                local_id_reindex_requires_native_regression=False, native_validated=False)
