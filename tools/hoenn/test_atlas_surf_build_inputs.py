"""A parallel map build must preserve the exact heal-location source bytes."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from atlas_surf_build_inputs import BODY

ROOT=Path(__file__).resolve().parents[2]
NATIVE=ROOT/'.local/generated-area-review-src/tools/mapjson'


@unittest.skipUnless((NATIVE/'json11.cpp').exists(),'Native immutable map generator required')
class ReadOnlyHealInputs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary=tempfile.TemporaryDirectory();cls.root=Path(cls.temporary.name)
        code='''#include <fstream>
#include <sstream>
#include <algorithm>
#include <vector>
#include <stdexcept>
#include "json11.h"
using namespace std;using json11::Json;
#define FATAL_ERROR(...) throw runtime_error("invalid input")
string read_text_file(string p){ifstream f(p);stringstream s;s<<f.rdbuf();return s.str();}
void clean_heal_locations(vector<string> &valid_map_ids){'''+BODY+'''}
int main(){vector<string> ids={"MAP_HOME","MAP_CENTER"};try{clean_heal_locations(ids);return 0;}catch(...){return 42;}}
'''
        (cls.root/'probe.cpp').write_text(code)
        subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror','-I',str(NATIVE),
            str(cls.root/'probe.cpp'),str(NATIVE/'json11.cpp'),'-o',str(cls.root/'probe')],check=True,capture_output=True)

    @classmethod
    def tearDownClass(cls):cls.temporary.cleanup()

    def check_input(self,raw,expected):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'src/data/heal_locations.json';path.parent.mkdir(parents=True);path.write_bytes(raw)
            def run(_):return subprocess.run([str(self.root/'probe')],cwd=folder,capture_output=True).returncode
            with ThreadPoolExecutor(max_workers=8) as pool:codes=list(pool.map(run,range(32)))
            self.assertEqual(codes,[expected]*32);self.assertEqual(path.read_bytes(),raw)

    def test_parallel_valid_build_preserves_whitespace_and_last_comma(self):
        raw=b'{\n "heal_locations": [\n  {"id":"HEAL_HOME","respawn_map":"MAP_HOME","respawn_npc":"LOCALID_MOM"},\n  {"id":"HEAL_CENTER","respawn_map":"MAP_CENTER","respawn_npc":"LOCALID_NURSE"}\n ]\n}'
        self.check_input(raw,0)

    def test_invalid_input_fails_without_silently_clearing_native_NPC(self):
        raw=json.dumps(dict(heal_locations=[dict(id='HEAL_BAD',respawn_map='MAP_MISSING',respawn_npc='LOCALID_NURSE')])).encode()
        self.check_input(raw,42)
        self.check_input(b'{"heal_locations":[{]}',42)


if __name__=='__main__':unittest.main()
