"""Run the actual field glue against independent boundary and recovery fixtures."""
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
import importlib.util

HERE = Path(__file__).resolve().parent


class FieldBehaviorTest(unittest.TestCase):
    def test_gather_warp_has_a_fresh_map_script_continuation(self):
        # A field warp abandons its script context. Observe the persistent
        # state written before it, then dispatch the *new* map's frame table.
        # Moving these messages after `waitstate` reproduces the native bug.
        script = (HERE / 'badge_qualifier.inc').read_text()
        meet = script.split('JourneyQualifier_Meet::\n', 1)[1].split('JourneyQualifier_Gathered::\n', 1)[0]
        before_warp = meet.split('\twarp ', 1)[0]
        state = int(re.findall(r'setvar VAR_JOURNEY_QUALIFIER_STATE, (\d+)', before_warp)[-1])
        self.assertNotEqual(state, 0)
        spec = importlib.util.spec_from_file_location('field_event', HERE / 'badge_story_event.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        handlers = {int(value): label for value, label in re.findall(
            r'map_script_2 VAR_JOURNEY_QUALIFIER_STATE, (\d+), (\w+)', module.OUTSIDE_FRAME_TABLE)}
        target = handlers[state]
        resumed = script.split(target + '::\n', 1)[1].split('JourneyQualifier_ArenaDispatch::\n', 1)[0]
        self.assertLess(resumed.index('lockall'), resumed.index('JourneyQualifier_Text_Meeting'))
        self.assertLess(resumed.index('setvar VAR_JOURNEY_QUALIFIER_STATE, 0'), resumed.index('JourneyQualifierBegin'))
        self.assertIn('JourneyQualifier_Text_Start', resumed)
        self.assertIn('JourneyQualifierBegin', resumed)

    def test_visibility_notices_and_recovery(self):
        implementation = (HERE / 'badge_qualifier_field.c').read_text()
        implementation = re.sub(r'^#include .*\n', '', implementation, flags=re.M)
        fixture = (HERE / 'fixture_badge_qualifier_field.c').read_text()
        # StringVar2 belongs to the game; retain its independent storage here.
        fixture = fixture.replace('/* FIELD_IMPLEMENTATION */',
            'static u8 gStringVar2[100];\n' + implementation)
        with tempfile.TemporaryDirectory(prefix='qualifier-field-') as temporary:
            source = Path(temporary) / 'field.c'
            executable = Path(temporary) / 'field'
            source.write_text(fixture)
            subprocess.run([os.environ.get('CC', 'cc'), '-std=gnu99', '-O1',
                '-Wall', '-Wextra', '-Werror', '-fsanitize=undefined',
                str(source), '-o', str(executable)], check=True, capture_output=True, text=True)
            subprocess.run([str(executable)], check=True, capture_output=True, text=True)


if __name__ == '__main__':
    unittest.main()
