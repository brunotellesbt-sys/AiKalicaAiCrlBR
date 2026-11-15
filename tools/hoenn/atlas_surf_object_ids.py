"""Keep native object/clone IDs when whole scenery changes array indices.

``local_id`` is the native JSON macro name, not a numeric ID override. The
staged mapjson backend adds ``native_local_id`` for the actual emitted byte,
with the old index+1 default and one shared validation path for events/macros.
No game source is written until the integration layer is finished.
"""
import hashlib

from badge_story_layer import read


BACKEND_PATH = 'tools/mapjson/mapjson.cpp'
MARKER = '// Journey Atlas explicit native object IDs.'
_HELPER = r'''// Journey Atlas explicit native object IDs.
vector<unsigned int> journey_native_object_local_ids(const Json &map_data) {
    vector<unsigned int> result;
    bool seen[256] = {};
    unsigned int index = 0;
    for (const auto &event : map_data["object_events"].array_items()) {
        unsigned int local_id = index + 1;
        auto explicit_id = event.object_items().find("native_local_id");
        if (explicit_id != event.object_items().end()) {
            const Json &value = explicit_id->second;
            if (!value.is_number() || value.number_value() < 1 || value.number_value() > 255
                || value.number_value() != value.int_value())
                FATAL_ERROR("Invalid native_local_id in map %s at object index %u: expected integer 1..255.\n",
                            json_to_string(map_data, "name", true).c_str(), index);
            local_id = value.int_value();
        }
        if (local_id < 1 || local_id > 255 || seen[local_id])
            FATAL_ERROR("Invalid or duplicate native object ID %u in map %s at index %u.\n",
                        local_id, json_to_string(map_data, "name", true).c_str(), index);
        seen[local_id] = true;
        result.push_back(local_id);
        index++;
    }
    return result;
}

'''


def native_local_id(event,index):
    """Return the numeric ID that the patched native backend actually emits."""
    if type(index) is not int or index < 0:
        raise ValueError(('Invalid native object array index',index))
    value = event.get('native_local_id',index+1)
    # json11 represents every JSON number as double. Integral numbers such
    # as 2.0 are accepted consistently; strings, bools and fractions are not.
    if type(value) not in (int,float) or not 1 <= value <= 255 or int(value) != value:
        raise ValueError(('native_local_id must be numeric integer 1..255',value,index))
    return int(value)


def validate_object_ids(events):
    ids = [native_local_id(event,index) for index,event in enumerate(events)]
    if len(set(ids)) != len(ids):
        raise ValueError(('Duplicate native object local ID',ids))
    return ids


def render_backend(original):
    """Patch only the three native ID emissions, with strict shape checks."""
    event = 'text << "\\tobject_event " << i + 1 << ", "'
    clone = 'text << "\\tclone_event " << i + 1 << ", "'
    macro = 'map_ids_text << "#define " << json_to_string(obj_event, "local_id") << " " << i + 1 << "\\n";'
    events_head = 'string generate_map_events_text(Json map_data) {\n'
    constants_head = '        auto obj_events = map_data["object_events"].array_items();\n'
    target = [(event,event.replace('i + 1','local_ids[i]')),
              (clone,clone.replace('i + 1','local_ids[i]')),
              (macro,macro.replace('i + 1','local_ids[i]'))]
    if MARKER in original:
        if (_HELPER not in original or any(original.count(after)!=1 for _,after in target)
                or original.count('journey_native_object_local_ids(map_data)') != 2):
            raise ValueError('Existing native object-ID backend is incomplete or altered')
        return original
    insertion = 'string get_generated_warning(const string &filename, bool isAsm) {'
    for before in (insertion,events_head,constants_head,event,clone,macro):
        if original.count(before) != 1:
            raise ValueError(('Unsupported native mapjson object-ID backend shape',before))
    result = original.replace(insertion,_HELPER+insertion,1)
    result = result.replace(events_head,events_head+'    const vector<unsigned int> local_ids = journey_native_object_local_ids(map_data);\n',1)
    result = result.replace(constants_head,constants_head+'        const vector<unsigned int> local_ids = journey_native_object_local_ids(map_data);\n',1)
    for before,after in target:
        result = result.replace(before,after,1)
    return result


def stage_object_id_backend(layer):
    raw = read(layer,BACKEND_PATH)
    patched = render_backend(raw.decode()).encode()
    if patched != raw:
        layer.stage(BACKEND_PATH,patched)
    return dict(kind='native-object-id-json-backend',path=BACKEND_PATH,
                before_sha256=hashlib.sha256(raw).hexdigest(),
                prepared_sha256=hashlib.sha256(patched).hexdigest(),already_installed=patched==raw,
                numeric_field='native_local_id',macro_name_field='local_id',
                default_index_plus_one_preserved=True,object_clone_and_macro_share_ids=True,
                duplicate_and_byte_range_checks=True,native_rom_validation_pending=True)
