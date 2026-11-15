"""Retire the obsolete mesh only after exact whole-event relocation coverage.

Map IDs, layouts, old scripts and source files remain available for save
migration and history. Only active connection/event arrays are cleared. An
unresolved incoming native connection/warp blocks the operation; unresolved
C/script references are reported verbatim and can be made a release gate.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re

from badge_story_layer import read
from atlas_surf_object_ids import native_local_id, validate_object_ids

EVENT_FIELDS = ("object_events", "warp_events", "coord_events", "bg_events")
CODE_RESOLUTION_KINDS = {"historical-id-table", "migration-table", "ecology-alias",
                         "repointed-runtime-policy", "unreachable-retired-map-script"}


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _js(layer, path):
    return json.loads(read(layer, path))


class RetirementBlocked(ValueError):
    """A checked report is available even when no mutation was staged."""
    def __init__(self, reason, report):
        super().__init__(reason)
        self.report = report


def _all_maps(layer):
    paths = {path.relative_to(layer.source).as_posix()
             for path in (layer.source / "data/maps").glob("*/map.json")}
    paths.update(path for path in layer.outputs if re.fullmatch(r"data/maps/[^/]+/map\.json",path))
    result,by_id = {},{}
    for path in sorted(paths):
        name=Path(path).parent.name
        value=_js(layer,path)
        if value["id"] in by_id:
            raise ValueError(("Duplicate map identity while retiring oceans",value["id"]))
        result[name]=value
        by_id[value["id"]]=name
    return result,by_id


def _identities(groups):
    result={}
    for group,label in enumerate(groups["group_order"]):
        if not 0<=group<=255:
            raise ValueError("Native map group overflows byte identity")
        for number,name in enumerate(groups[label]):
            if name in result or not 0<=number<=255:
                raise ValueError(("Invalid append-only map identity",name))
            result[name]=(group<<8)|number
    return result


def _retired(layer, rows, maps, identities):
    result={}
    for row in rows:
        record=dict(map=row) if isinstance(row,str) else copy.deepcopy(row)
        name=record["map"]
        if name in result or name not in maps:
            raise ValueError(("Duplicate or absent retired map",name))
        current=maps[name]
        if name not in identities:
            raise ValueError(("Retired map lost its historical group entry",name))
        if record.get("id",current["id"]) != current["id"]:
            raise ValueError(("Retired symbolic identity changed",name))
        if record.get("packed_id",identities[name]) != identities[name]:
            raise ValueError(("Retired numeric identity changed",name))
        if record.get("layout",current["layout"]) != current["layout"]:
            raise ValueError(("Retired historical layout changed",name))
        if "events" in record:
            for field in EVENT_FIELDS:
                if record["events"].get(field,[]) != current.get(field,[]):
                    raise ValueError(("Parent event inventory changed before retirement",name,field))
        record.update(id=current["id"],packed_id=identities[name],layout=current["layout"])
        result[name]=record
    if not result:
        raise ValueError("No obsolete ocean identities were supplied")
    return result


def _code_references(layer, retired_ids, resolutions):
    """A resolution is bound to exact file bytes plus one old identity."""
    policy={}
    for row in resolutions:
        key=row["path"],row["symbol"]
        if key in policy or row.get("kind") not in CODE_RESOLUTION_KINDS or not row.get("evidence"):
            raise ValueError(("Code reference resolution lacks unique explicit evidence",key))
        policy[key]=row
    paths=set()
    for root in ("src","include","data/scripts"):
        directory=layer.source/root
        if directory.exists():
            paths.update(path.relative_to(layer.source).as_posix() for path in directory.rglob("*")
                         if path.suffix in (".c",".h",".inc",".s"))
    paths.update(path.relative_to(layer.source).as_posix()
                 for path in (layer.source/"data/maps").glob("*.inc"))
    if (layer.source/"data/event_scripts.s").is_file():
        paths.add("data/event_scripts.s")
    paths.update(path for path in layer.outputs if Path(path).suffix in (".c",".h",".inc",".s")
                 and path.startswith(("src/","include/","data/")))
    pattern=re.compile(r"\b(?:"+"|".join(re.escape(value) for value in sorted(retired_ids))+r")\b")
    found,resolved,unresolved=[],[],[]
    seen_policy=set()
    for path in sorted(paths):
        raw=read(layer,path)
        text=raw.decode()
        # Strip C comments while preserving line numbers. Assembly @ comments
        # are removed line-by-line; #define remains active code.
        text=re.sub(r"/\*.*?\*/|//[^\n]*",lambda match:"\n"*match[0].count("\n"),text,flags=re.S)
        by_symbol={}
        for number,line in enumerate(text.splitlines(),1):
            if Path(path).suffix in (".s",".inc"):
                line=line.split("@",1)[0]
            for symbol in set(pattern.findall(line)):
                by_symbol.setdefault(symbol,[]).append(dict(line=number,context=line.strip()))
        digest=_sha(raw)
        for symbol,locations in sorted(by_symbol.items()):
            row=dict(path=path,symbol=symbol,file_sha256=digest,locations=locations)
            key=path,symbol
            if key in policy:
                resolution=policy[key]
                if resolution.get("file_sha256") != digest:
                    raise ValueError(("Code reference resolution is stale",key))
                row["resolution"]=copy.deepcopy(resolution)
                resolved.append(row);seen_policy.add(key)
            else:
                unresolved.append(row)
            found.append(row)
    unused=sorted(set(policy)-seen_policy)
    if unused:
        raise ValueError(("Code reference resolution does not match a remaining reference",unused[:12]))
    return dict(references=found,resolved=resolved,unresolved=unresolved,
                files_scanned=len(paths),files_with_references=len({row["path"] for row in found}))


def audit_references(layer, retired_maps, *, code_reference_resolutions=()):
    """Read-only preflight usable before event relocation has been completed."""
    maps,by_id=_all_maps(layer)
    identities=_identities(_js(layer,"data/maps/map_groups.json"))
    retired=_retired(layer,retired_maps,maps,identities)
    connections,warps=[],[]
    for name,current in sorted(maps.items()):
        if name in retired:
            continue
        for index,connection in enumerate(current.get("connections") or []):
            if by_id.get(connection["map"]) in retired:
                connections.append(dict(map=name,index=index,connection=copy.deepcopy(connection)))
        for index,event in enumerate(current.get("warp_events") or []):
            if by_id.get(event["dest_map"]) in retired:
                warps.append(dict(map=name,index=index,event=copy.deepcopy(event)))
    return dict(kind="atlas-retired-reference-preflight",retired_maps=len(retired),
                incoming_connections=connections,incoming_warps=warps,
                code_references=_code_references(layer,{row["id"] for row in retired.values()},code_reference_resolutions),
                event_relocation_coverage_checked=False,source_staged=False,native_validated=False)


def audit(layer, retired_maps, event_relocations, *, code_reference_resolutions=()):
    """Validate a complete old-to-new event mapping and audit incoming travel."""
    maps,by_id=_all_maps(layer)
    groups=_js(layer,"data/maps/map_groups.json")
    identities=_identities(groups)
    layouts={row["id"]:row for row in _js(layer,"data/layouts/layouts.json")["layouts"]}
    retired=_retired(layer,retired_maps,maps,identities)
    expected={(name,field,index) for name in retired for field in EVENT_FIELDS
              for index,_ in enumerate(maps[name].get(field) or [])}
    relocations,target_keys={},set()
    external=[]
    for row in event_relocations:
        row=copy.deepcopy(row)
        source_name,field,index=row["source_map"],row["field"],row["source_index"]
        if field not in EVENT_FIELDS or type(index) is not int or index<0:
            raise ValueError(("Invalid source event identity",source_name,field,index))
        if source_name not in retired:
            if source_name not in maps:
                raise ValueError(("Event relocation names an unknown source map",source_name))
            external.append(row)
            continue
        key=source_name,field,index
        if key not in expected or key in relocations:
            raise ValueError(("Duplicate or invented retired event relocation",key))
        source=maps[source_name][field][index]
        if row.get("source_tile") != [source["x"],source["y"]]:
            raise ValueError(("Old event coordinate is not its complete source record",key))
        if "source_event" in row and row["source_event"] != source:
            raise ValueError(("Whole old event changed in relocation manifest",key))
        target_name,target_index=row["target_map"],row["target_index"]
        if target_name not in maps or target_name in retired or type(target_index) is not int or target_index<0:
            raise ValueError(("Event relocation has no active new target",key,target_name,target_index))
        if row.get("target_map_id",maps[target_name]["id"]) != maps[target_name]["id"]:
            raise ValueError(("New event symbolic identity changed",key))
        target_key=target_name,field,target_index
        if target_key in target_keys:
            raise ValueError(("Two old events collapsed into one replacement event",target_key))
        target_keys.add(target_key)
        events=maps[target_name].get(field) or []
        if not 0<=target_index<len(events):
            raise ValueError(("Relocated event missing from replacement map",target_key))
        target=events[target_index]
        if row.get("target_tile") != [target["x"],target["y"]]:
            raise ValueError(("New event position changed after placement",target_key))
        layout=layouts[maps[target_name]["layout"]]
        if not 0<=target["x"]<layout["width"] or not 0<=target["y"]<layout["height"]:
            raise ValueError(("Replacement event lies outside its complete map",target_key))
        translated_fields=("x","y","dest_map","dest_warp_id") if field=="warp_events" else ("x","y")
        if field=="object_events":
            # native_local_id is an emitted-byte override, while local_id is
            # the original macro name and remains part of exact identity.
            validate_object_ids(events)
            old_local_id=native_local_id(source,index)
            new_local_id=native_local_id(target,target_index)
            if old_local_id != new_local_id:
                raise ValueError(("Native object local ID changed during retirement",key,old_local_id,new_local_id))
            translated_fields += ("native_local_id",)
            row.update(source_native_local_id=old_local_id,target_native_local_id=new_local_id)
        old_identity={k:v for k,v in source.items() if k not in translated_fields}
        new_identity={k:v for k,v in target.items() if k not in translated_fields}
        if old_identity != new_identity:
            raise ValueError(("Trainer/script/flag/behavior identity was altered during event relocation",key,target_key))
        row.update(source_event=copy.deepcopy(source),target_event=copy.deepcopy(target),
                   source_packed_id=identities[source_name],target_packed_id=identities[target_name])
        relocations[key]=row
    missing=sorted(expected-set(relocations))
    if missing:
        raise ValueError(("Cannot clear old events without exact complete relocation coverage",missing[:20],len(missing)))
    # Validate the destination half of *every* copied warp. Moving an entry
    # does not authorize changing where that entry leads.
    for key,row in relocations.items():
        if key[1] != "warp_events":
            continue
        source,target=row["source_event"],row["target_event"]
        old_dest=by_id.get(source["dest_map"])
        dest_key=(old_dest,"warp_events",int(source["dest_warp_id"])) if old_dest in retired else None
        if dest_key in relocations:
            replacement=relocations[dest_key]
            actual=(target["dest_map"],int(target["dest_warp_id"]))
            desired=(maps[replacement["target_map"]]["id"],replacement["target_index"])
            if actual != desired:
                raise ValueError(("Copied warp did not follow the exact destination relocation",key,actual,desired))
        elif (source["dest_map"],str(source["dest_warp_id"])) != (target["dest_map"],str(target["dest_warp_id"])):
            raise ValueError(("Copied warp silently changed its interior/destination",key))
    incoming_connections,incoming_warps=[],[]
    for name,current in sorted(maps.items()):
        if name in retired:
            continue
        for index,connection in enumerate(current.get("connections") or []):
            if by_id.get(connection["map"]) in retired:
                incoming_connections.append(dict(map=name,index=index,connection=copy.deepcopy(connection)))
        for index,event in enumerate(current.get("warp_events") or []):
            if by_id.get(event["dest_map"]) in retired:
                incoming_warps.append(dict(map=name,index=index,event=copy.deepcopy(event)))
    code=_code_references(layer,{row["id"] for row in retired.values()},code_reference_resolutions)
    legacy=[]
    for key,row in sorted(relocations.items()):
        if key[1] == "warp_events":
            legacy.append(dict(old_map=row["source_map"],old_map_id=maps[row["source_map"]]["id"],
                               old_packed_id=row["source_packed_id"],old_warp_id=row["source_index"],
                               old_event=row["source_event"],new_map=row["target_map"],
                               new_map_id=maps[row["target_map"]]["id"],new_packed_id=row["target_packed_id"],
                               new_warp_id=row["target_index"],new_event=row["target_event"]))
    return dict(kind="atlas-retired-network-audit",retired_maps=list(retired.values()),
                relocated_events=list(relocations.values()),external_event_relocations=external,
                expected_event_count=len(expected),exact_event_coverage=True,
                incoming_connections=incoming_connections,incoming_warps=incoming_warps,
                code_references=code,legacy_dest_warp_table=legacy,
                old_connections={name:copy.deepcopy(maps[name].get("connections") or []) for name in retired},
                old_events={name:{field:copy.deepcopy(maps[name].get(field) or []) for field in EVENT_FIELDS}
                            for name in retired},
                historical_ids_and_layouts_preserved=True,save_migration_applied=False,
                source_staged=False,native_validated=False,final_release_validated=False)


def stage(layer, retired_maps, event_relocations, *, code_reference_resolutions=(),
          require_code_resolution=False):
    """Atomically stage disconnection after complete coverage; preserve history."""
    report=audit(layer,retired_maps,event_relocations,
                 code_reference_resolutions=code_reference_resolutions)
    if report["incoming_connections"] or report["incoming_warps"]:
        raise RetirementBlocked("Native connections/warps still enter an obsolete ocean; no retirement staged",report)
    if require_code_resolution and report["code_references"]["unresolved"]:
        raise RetirementBlocked("Unresolved C/script references remain; no retirement staged",report)
    for row in report["retired_maps"]:
        path=f"data/maps/{row['map']}/map.json"
        current=_js(layer,path)
        current["connections"]=[]
        for field in EVENT_FIELDS:
            current[field]=[]
        layer.stage(path,json.dumps(current,indent=2)+"\n")
    report["source_staged"]=True
    report["unresolved_code_reference_count"]=len(report["code_references"]["unresolved"])
    report["code_reference_audit_complete"]=not bool(report["code_references"]["unresolved"])
    return report
