import unittest
import os
import tempfile
import json
from pathlib import Path
from operator_dashboard.app import app
from operator_dashboard.action_ledger_utils import append_ledger_entry, LEDGER_PATH

class TestEventEvidence(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.tempdir = tempfile.TemporaryDirectory()
        self.ledger_path = LEDGER_PATH
        self.ledger_backup = None
        if os.path.exists(self.ledger_path):
            with open(self.ledger_path, 'r', encoding='utf-8') as f:
                self.ledger_backup = f.read()
        # Write a known ledger
        with open(self.ledger_path, 'w', encoding='utf-8') as f:
            for i in range(7):
                entry = {
                    'timestamp': f'2026-04-19T12:0{i}:00Z',
                    'event_id': 'song_vs_figueiredo' if i < 5 else 'other_event',
                    'action': 'inspect',
                    'user_message': f'Inspect {i}',
                    'outcome_status': 'succeeded',
                    'response': f'Checked {i}',
                }
                f.write(json.dumps(entry) + '\n')
        # Write a known queue file
        self.queue_path = os.path.join(self.tempdir.name, 'event_coverage_queue.csv')
        with open(self.queue_path, 'w', encoding='utf-8') as f:
            f.write('event_id,status,artifact,blockers,completed_at,frozen_flag\n')
            f.write('song_vs_figueiredo,complete,artifacts/test.txt,,2026-01-01,false\n')
        # Patch queue_utils QUEUE_PATH
        from operator_dashboard import queue_utils
        queue_utils.QUEUE_PATH = self.queue_path
        # Patch evidence_utils QUEUE_PATH
        import operator_dashboard.evidence_utils as evidence_utils
        evidence_utils.QUEUE_PATH = self.queue_path
        # Patch safe_path_utils
        from operator_dashboard import safe_path_utils
        safe_path_utils.ALLOWED_ARTIFACT_DIRS.append('artifacts')
        safe_path_utils.EXTRA_ROOTS.append(Path(self.tempdir.name).resolve())
        # Create artifact
        art_dir = os.path.join(self.tempdir.name, 'artifacts')
        os.makedirs(art_dir, exist_ok=True)
        with open(os.path.join(art_dir, 'test.txt'), 'w') as f:
            f.write('artifact')

    def tearDown(self):
        if self.ledger_backup is not None:
            with open(self.ledger_path, 'w', encoding='utf-8') as f:
                f.write(self.ledger_backup)
        # Clear extra roots to avoid side effects
        from operator_dashboard import safe_path_utils
        safe_path_utils.EXTRA_ROOTS = []
        self.tempdir.cleanup()

    def test_evidence_hit(self):
        resp = self.client.get('/api/queue/event/song_vs_figueiredo/evidence')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data['ok'])
        self.assertTrue(data['event_found'])
        self.assertEqual(data['event_id'], 'song_vs_figueiredo')
        self.assertEqual(data['status'], 'complete')
        self.assertEqual(data['artifact_exists'], True)
        self.assertEqual(data['artifact_safe'], True)
        self.assertTrue(isinstance(data['recent_ledger_entries'], list))
        self.assertLessEqual(len(data['recent_ledger_entries']), 5)
        self.assertTrue(any('Inspect' in e['user_message'] for e in data['recent_ledger_entries']))
        self.assertTrue(isinstance(data['approved_record_links'], list))
        self.assertTrue(any('test.txt' in l['path'] for l in data['approved_record_links']))
        self.assertIn('recommendation', data)
        self.assertIn('errors', data)

    def test_evidence_miss(self):
        resp = self.client.get('/api/queue/event/zzz/evidence')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data['ok'])
        self.assertFalse(data['event_found'])
        self.assertEqual(data['event_id'], 'zzz')
        self.assertIn('errors', data)
        self.assertTrue(any('not found' in err for err in data['errors']))

    def test_missing_artifact(self):
        # Remove artifact
        art_path = os.path.join(self.tempdir.name, 'artifacts', 'test.txt')
        os.remove(art_path)
        resp = self.client.get('/api/queue/event/song_vs_figueiredo/evidence')
        data = json.loads(resp.data)
        self.assertFalse(data['artifact_exists'])
        self.assertIn('approved_record_links', data)

    def test_malformed_ledger(self):
        # Write malformed ledger
        with open(self.ledger_path, 'w', encoding='utf-8') as f:
            f.write('not json\n')
        resp = self.client.get('/api/queue/event/song_vs_figueiredo/evidence')
        data = json.loads(resp.data)
        self.assertTrue(data['ok'])
        self.assertTrue(data['event_found'])
        self.assertEqual(data['recent_ledger_entries'], [])

if __name__ == '__main__':
    unittest.main()
