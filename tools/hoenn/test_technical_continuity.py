"""Ensure the actual game archive plan carries its persistent technical handoff."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import publish_badge_story as publisher


class TechnicalContinuityBundleTests(unittest.TestCase):
    def test_archive_plan_includes_readable_guide_history_and_current_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            for name in ('versions.json', 'SHA256SUMS', 'START-HERE.md'):
                (output/name).write_text('{}\n')
            # The fixture has no ROM/proof/history. Actual publication still
            # executes all existing proof and history checks before this step.
            info = dict(validation_scope=publisher.SCOPE, variants=[], proofs=[])
            with patch.object(publisher, 'LEGACY_MEDIA', {}):
                entries, _ = publisher.archive_plan(info, output, include_roms=False)
            self.assertTrue(set(publisher.CONTINUITY_FILES) <= entries.keys())
            archive = output/'handoff-only.zip'
            with zipfile.ZipFile(archive, 'w') as bundle:
                for name in publisher.CONTINUITY_FILES:
                    bundle.write(entries[name], name)
            with zipfile.ZipFile(archive) as bundle:
                record = json.loads(bundle.read('docs/RETOMADA_TECNICA_POKEMON_JOURNEY.json'))
                self.assertEqual(record['schema'], 'codex-project-handoff/v1')
                self.assertEqual(len(record['recovery_plan']), 5)
                self.assertEqual(len(record['completion_order']), 16)
                self.assertIsNone(record['project_identity']['original_task_id'])
                self.assertIsNone(record['project_identity']['original_environment_id'])
                delta = json.loads(bundle.read('docs/ULTIMO_PEDIDO_POS_PR108.json'))
                self.assertEqual(delta['schema'], 'codex-task-delta/v1')
                self.assertEqual(len(delta['non_negotiable_requirements']), 9)
                self.assertEqual(delta['pending_final_delivery']['release_proofs']['total'], 12)
                guide = bundle.read('docs/CONTINUIDADE-TECNICA-IA.md').decode()
                self.assertIn('Últimos pedidos resolvidos', guide)
                self.assertIn('Pedido principal incompleto', guide)
                self.assertIn('Como manter este documento', guide)
                self.assertIn('Abra um pr de verdade, e não um em rascunho.', guide)


if __name__ == '__main__':
    unittest.main()
