"""A freshly returned source contract must equal its persisted JSON value."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from candidate_layer import Layer
import prepare_coastal_ecology as prepare


class PreparedMetadata(unittest.TestCase):
    def test_integer_behavior_keys_survive_first_return_and_marker_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)
            (source/'.source-acquired.json').write_text(json.dumps(dict(sha256={})))
            with patch.object(prepare,'Layer',side_effect=lambda path,name,prior:Layer(path,name,[])), \
                 patch.object(prepare,'digest',return_value=prepare.PARENT_MARKER_SHA256), \
                 patch.object(prepare,'stage_repairs',return_value=dict(
                     generations={4:dict(water_behaviors={16:30}),9:dict(water_behaviors={25:2})})):
                first=prepare.prepare(source)
                second=prepare.prepare(source)
            persisted=json.loads((source/'.journey-coastal-ecology').read_text())
            self.assertEqual(first,persisted)
            self.assertEqual(second,persisted)
            self.assertEqual(first['generations']['4']['water_behaviors'],{'16':30})


if __name__=='__main__':unittest.main()
