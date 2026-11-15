"""Numeric object/clone IDs and native mapjson C++ output equivalence."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from atlas_surf_object_ids import (BACKEND_PATH, native_local_id, render_backend,
                                    stage_object_id_backend, validate_object_ids)


def backend_fixture():
    """Small textual shape fixture; compiled tests below use actual mapjson."""
    return '''string get_generated_warning(const string &filename, bool isAsm) {
}
string generate_map_events_text(Json map_data) {
    text << "\\tobject_event " << i + 1 << ", "
    text << "\\tclone_event " << i + 1 << ", "
}
void process_event_constants() {
        auto obj_events = map_data["object_events"].array_items();
                map_ids_text << "#define " << json_to_string(obj_event, "local_id") << " " << i + 1 << "\\n";
}
'''


def map_fixture(ids=None):
    regular = dict(local_id='LOCAL_REGULAR',graphics_id='OBJ_EVENT_GFX_MAN_1',x=4,y=5,
        elevation=3,movement_type='MOVEMENT_TYPE_NONE',movement_range_x=0,movement_range_y=0,
        trainer_type='TRAINER_TYPE_NONE',trainer_sight_or_berry_tree_id=0,script='TestScript',flag='FLAG_TEST')
    clone = dict(type='clone',local_id='LOCAL_CLONE',graphics_id='OBJ_EVENT_GFX_MAN_1',x=6,y=7,
                 target_local_id='LOCAL_TARGET',target_map='MAP_TARGET')
    events = [regular,clone]
    if ids is not None:
        for event,value in zip(events,ids):
            if value != 'default': event['native_local_id'] = value
    return dict(name='Probe',id='MAP_PROBE',object_events=events,warp_events=[],coord_events=[],bg_events=[])


class NumericIdTests(unittest.TestCase):
    def test_numeric_field_differs_from_native_macro_name(self):
        self.assertEqual(native_local_id(dict(local_id='SOME_MACRO'),6),7)
        self.assertEqual(native_local_id(dict(local_id='SOME_MACRO',native_local_id=240),0),240)
        self.assertEqual(native_local_id(dict(native_local_id=2.0),0),2)
        self.assertEqual(validate_object_ids([{} for _ in range(255)]),list(range(1,256)))
        self.assertEqual(validate_object_ids([dict(native_local_id=255),dict(native_local_id=1)]),[255,1])

    def test_invalid_or_duplicate_effective_ids_fail_closed(self):
        for value in (None,True,False,0,256,-1,2.5,'2','SYMBOL',{},[]):
            with self.subTest(value=value),self.assertRaises(ValueError):
                native_local_id(dict(native_local_id=value),0)
        for events in ([dict(native_local_id=2),{}],
                       [dict(native_local_id=1),dict(native_local_id=1)],
                       [{} for _ in range(256)]):
            with self.subTest(events=len(events)),self.assertRaises(ValueError):
                validate_object_ids(events)

    def test_strict_backend_patch_is_idempotent_and_stage_only(self):
        original = backend_fixture();patched = render_backend(original)
        self.assertEqual(render_backend(patched),patched)
        self.assertIn('object_event " << local_ids[i]',patched)
        self.assertIn('clone_event " << local_ids[i]',patched)
        self.assertIn('json_to_string(obj_event, "local_id") << " " << local_ids[i]',patched)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            target = path/BACKEND_PATH;target.parent.mkdir(parents=True);target.write_text(original)
            class Layer:
                source = path
                outputs = {}
                expected = {BACKEND_PATH:hashlib.sha256(original.encode()).hexdigest()}
                def stage(self,name,raw): self.outputs[name] = raw
            layer = Layer()
            first = stage_object_id_backend(layer);second = stage_object_id_backend(layer)
            self.assertFalse(first['already_installed'])
            self.assertTrue(second['already_installed'])
            self.assertEqual(target.read_text(),original)
            self.assertEqual(layer.outputs[BACKEND_PATH].decode(),patched)
        for bad in (original.replace('clone_event','changed_event'),
                    patched.replace('local_ids[i]','i + 1',1)):
            with self.assertRaises(ValueError): render_backend(bad)


@unittest.skipUnless(shutil.which('g++'),'Native C++ compiler required')
class NativeMapjsonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Path(__file__).resolve().parents[2]
        cls.source = cls.repo/'.local/generated-area-review-src'
        if not (cls.source/BACKEND_PATH).exists():
            raise unittest.SkipTest('Immutable source171 mapjson is not available locally')
        cls.temporary = tempfile.TemporaryDirectory(prefix='atlas-native-object-ids-')
        cls.path = Path(cls.temporary.name)
        for name in ('tools/mapjson/json11.h','tools/mapjson/json11.cpp','tools/mapjson/mapjson.h','include/config/frlg.h'):
            output = cls.path/name;output.parent.mkdir(parents=True,exist_ok=True)
            output.write_bytes((cls.source/name).read_bytes())
        original = (cls.source/BACKEND_PATH).read_text()
        cls.original_sha256 = hashlib.sha256(original.encode()).hexdigest()
        cls.patched_sha256 = hashlib.sha256(render_backend(original).encode()).hexdigest()
        for label,code in [('original',original),('patched',render_backend(original))]:
            (cls.path/f'tools/mapjson/{label}.cpp').write_text(code)
            harness = '''#define main native_mapjson_main
#include "tools/mapjson/'''+label+'''.cpp"
#undef main
int main(int argc, char **argv) {
    if (argc<2) return 99;
    version="emerald";
    ostringstream input;input << std::cin.rdbuf();
    string error;Json value=Json::parse(input.str(),error);
    if (!error.empty()) return 98;
    string mode(argv[1]);
    if (mode=="events") cout << generate_map_events_text(value);
    else if (mode=="batch") {
        for (const auto &map : value.array_items()) cout << generate_map_events_text(map);
    } else if (mode=="constants" && argc==4) {
        write_text_file(argv[2],value.dump());
        process_event_constants(vector<string>{argv[2]},argv[3]);
        cout << read_text_file(argv[3]);
    } else return 97;
    return 0;
}
'''
            file = cls.path/f'{label}.cpp';file.write_text(harness)
            executable = cls.path/label
            subprocess.run(['g++','-std=c++17','-O1','-Wall',str(file),
                            str(cls.path/'tools/mapjson/json11.cpp'),'-o',str(executable)],
                           check=True,capture_output=True,text=True)

    @classmethod
    def tearDownClass(cls): cls.temporary.cleanup()

    def run_native(self,label,value,mode='events'):
        args = [str(self.path/label),mode]
        if mode == 'constants': args += [str(self.path/'probe.json'),str(self.path/'ids.h')]
        return subprocess.run(args,input=json.dumps(value),capture_output=True,text=True)

    def test_default_event_and_macro_output_are_byte_equivalent(self):
        for mode in ('events','constants'):
            old = self.run_native('original',map_fixture(),mode)
            new = self.run_native('patched',map_fixture(),mode)
            self.assertEqual(old.returncode,0,old.stderr)
            self.assertEqual(new.returncode,0,new.stderr)
            self.assertEqual(old.stdout,new.stdout)
        self.assertEqual(hashlib.sha256((self.source/BACKEND_PATH).read_bytes()).hexdigest(),self.original_sha256)

    def test_explicit_ids_reach_object_clone_and_symbolic_macros(self):
        value = map_fixture([7,240])
        events = self.run_native('patched',value)
        self.assertEqual(events.returncode,0,events.stderr)
        self.assertIn('\tobject_event 7, ',events.stdout)
        self.assertIn('\tclone_event 240, ',events.stdout)
        self.assertIn('LOCAL_TARGET, MAP_TARGET',events.stdout)
        ids = self.run_native('patched',value,'constants')
        self.assertEqual(ids.returncode,0,ids.stderr)
        self.assertIn('#define LOCAL_REGULAR 7\n',ids.stdout)
        self.assertIn('#define LOCAL_CLONE 240\n',ids.stdout)

    def test_every_valid_native_id_and_all_invalid_effective_ids(self):
        for local in range(1,256):
            value = map_fixture();value['object_events'] = value['object_events'][:1]
            value['object_events'][0]['native_local_id'] = local
            result = self.run_native('patched',value)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn(f'\tobject_event {local}, ',result.stdout)
        for explicit in ([2,'default'],[1,1],[0,2],[256,2],[-1,2],[True,2],['2',3],[None,2],[2.5,3]):
            for mode in ('events','constants'):
                with self.subTest(ids=explicit,mode=mode):
                    result = self.run_native('patched',map_fixture(explicit),mode)
                    self.assertNotEqual(result.returncode,0)
                    self.assertIn('native',result.stderr)

    def test_every_original_source171_event_stays_byte_equivalent(self):
        maps = [json.loads(path.read_bytes()) for path in sorted((self.source/'data/maps').glob('*/map.json'))]
        old = self.run_native('original',maps,'batch')
        new = self.run_native('patched',maps,'batch')
        self.assertEqual(old.returncode,0,old.stderr)
        self.assertEqual(new.returncode,0,new.stderr)
        self.assertEqual(old.stdout,new.stdout)


if __name__ == '__main__': unittest.main()
