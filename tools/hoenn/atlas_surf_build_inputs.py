"""Make map generation read-only for authenticated heal-location inputs.

Parallel process_groups invocations used to truncate/rewrite the same source
JSON, even when all42 respawn destinations were valid. Fail an invalid input
explicitly instead of silently editing a verified source during the build.
"""
from badge_story_layer import read
from render_sea_maps import _braced

PATH='tools/mapjson/mapjson.cpp'
BODY=r'''
    const string path="src/data/heal_locations.json";
    string error;
    const Json data=Json::parse(read_text_file(path),error);
    if(!error.empty())
        FATAL_ERROR("Invalid heal locations source: %s\n",error.c_str());
    for(const Json &entry : data["heal_locations"].array_items())
    {
        const string map=entry["respawn_map"].string_value();
        const string npc=entry["respawn_npc"].string_value();
        if(!npc.empty() && find(valid_map_ids.begin(),valid_map_ids.end(),map)==valid_map_ids.end())
            FATAL_ERROR("Heal location %s references an uncompiled respawn map %s; repair the source explicitly\n",
                entry["id"].string_value().c_str(),map.c_str());
    }
'''


def repair(text):
    signature='void clean_heal_locations(vector<string> &valid_map_ids)\n{'
    if text.count(signature)!=1:raise ValueError('Map generator function changed')
    start=text.index(signature)+len(signature)-1;body=_braced(text,start)
    if 'write_text_file("src/data/heal_locations.json", new_json.str());' not in body:
        raise ValueError('Expected the original destructive heal-location cleaner')
    return text.replace(signature+body+'}',signature+BODY+'}',1)


def stage(layer):
    layer.stage(PATH,repair(read(layer,PATH).decode()))
    return dict(map_generator_heal_source_read_only=True,
        invalid_respawn_references_fail_explicitly=True,
        native_heal_location_records_and_numeric_IDs_unchanged=True)
