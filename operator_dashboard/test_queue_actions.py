import unittest
from operator_dashboard.queue_utils import safe_read_queue
from operator_dashboard.safe_path_utils import is_safe_artifact_path, EXTRA_ROOTS
from operator_dashboard.app import app
import os
import tempfile
import csv
import json

class TestQueueActions(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.tempdir = tempfile.TemporaryDirectory()
        self.queue_path = os.path.join(self.tempdir.name, 'event_coverage_queue.csv')
        self.orig_path = safe_read_queue.__globals__['QUEUE_PATH']
        safe_read_queue.__globals__['QUEUE_PATH'] = self.queue_path
        
        # Patch EXTRA_ROOTS in safe_path_utils
        EXTRA_ROOTS.append(self.tempdir.name)
        
        # Patch artifact roots
        self.artifact_file = os.path.join(self.tempdir.name, 'artifacts', 'test.txt')
        os.makedirs(os.path.dirname(self.artifact_file), exist_ok=True)
        with open(self.artifact_file, 'w') as f:
            f.write('artifact')

    def tearDown(self):
        safe_read_queue.__globals__['QUEUE_PATH'] = self.orig_path
        if self.tempdir.name in EXTRA_ROOTS:
            EXTRA_ROOTS.remove(self.tempdir.name)
        self.tempdir.cleanup()

    def write_queue(self, rows):
        with open(self.queue_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['event_id','status','artifact','blockers','completed_at','frozen_flag'])
            writer.writeheader()
            for r in rows:
                writer.writerow(r)

    def test_event_drilldown_hit(self):
        self.write_queue([{'event_id':'a','status':'queued','artifact':'artifacts/test.txt','blockers':'','completed_at':'','frozen_flag':''}])
        resp = self.client.get('/api/queue/event/a')
        data = json.loads(resp.data)
        self.assertTrue(data['ok'])
        self.assertTrue(data['event_found'])
        self.assertEqual(data['event_id'], 'a')
        self.assertEqual(data['status'], 'queued')
        self.assertEqual(data['artifact'], 'artifacts/test.txt')
        self.assertEqual(data['recommendation'], 'Eligible for next execution')

    def test_event_drilldown_miss(self):
        self.write_queue([{'event_id':'a','status':'queued','artifact':'','blockers':'','completed_at':'','frozen_flag':''}])
        resp = self.client.get('/api/queue/event/b')
        data = json.loads(resp.data)
        self.assertTrue(data['ok'])
        self.assertFalse(data['event_found'])
        self.assertEqual(data['event_id'], 'b')
        self.assertIn('not found', data['errors'][0])

    def test_artifact_resolution_safe(self):
        # Valid artifact
        safe, resolved = is_safe_artifact_path('artifacts/test.txt')
        self.assertTrue(safe)
        self.assertTrue(os.path.exists(resolved))
        # Traversal
        safe, msg = is_safe_artifact_path('../secrets.txt')
        self.assertFalse(safe)
        self.assertIn('traversal', msg)
        # Out of allowed dir
        safe, msg = is_safe_artifact_path('notallowed/test.txt')
        self.assertFalse(safe)
        self.assertIn('not under allowed', msg)
        # Nonexistent
        safe, msg = is_safe_artifact_path('artifacts/missing.txt')
        self.assertFalse(safe)
        self.assertIn('does not exist', msg)

    def test_open_event_artifact_invalid(self):
        self.write_queue([{'event_id':'a','status':'queued','artifact':'artifacts/missing.txt','blockers':'','completed_at':'','frozen_flag':''}])
        resp = self.client.post('/api/queue/event/a/open_artifact')
        data = json.loads(resp.data)
        self.assertFalse(data['ok'])
        self.assertIn('does not exist', data['error'])

if __name__ == '__main__':
    unittest.main()
