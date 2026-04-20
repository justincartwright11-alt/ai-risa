import unittest
from operator_dashboard.queue_utils import safe_read_queue, summarize_queue
import os
import tempfile
import csv

class TestQueueStatus(unittest.TestCase):
    def setUp(self):
        # Patch QUEUE_PATH to a temp file
        self.tempdir = tempfile.TemporaryDirectory()
        self.queue_path = os.path.join(self.tempdir.name, 'event_coverage_queue.csv')
        self.orig_path = safe_read_queue.__globals__['QUEUE_PATH']
        safe_read_queue.__globals__['QUEUE_PATH'] = self.queue_path

    def tearDown(self):
        safe_read_queue.__globals__['QUEUE_PATH'] = self.orig_path
        self.tempdir.cleanup()

    def write_queue(self, rows):
        with open(self.queue_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['event_id','status','artifact','blockers','completed_at','frozen_flag'])
            writer.writeheader()
            for r in rows:
                writer.writerow(r)

    def test_missing_queue_file(self):
        # No file present
        if os.path.exists(self.queue_path):
            os.remove(self.queue_path)
        q = safe_read_queue()
        self.assertTrue(q['ok'])
        self.assertFalse(q['queue_file_present'])
        self.assertEqual(q['total_rows'], 0)

    def test_malformed_queue_file(self):
        with open(self.queue_path, 'w', encoding='utf-8') as f:
            f.write('not,a,valid,csv\n1,2,3\n')
        q = safe_read_queue()
        self.assertFalse(q['ok'])
        self.assertTrue(q['queue_file_present'])
        self.assertIn('rows', q)
        self.assertEqual(q['total_rows'], 0)

    def test_queue_counts(self):
        rows = [
            {'event_id':'a','status':'queued','artifact':'','blockers':'','completed_at':'','frozen_flag':''},
            {'event_id':'b','status':'blocked','artifact':'','blockers':'x','completed_at':'','frozen_flag':''},
            {'event_id':'c','status':'in_progress','artifact':'','blockers':'','completed_at':'','frozen_flag':''},
            {'event_id':'d','status':'complete','artifact':'','blockers':'','completed_at':'2026-01-01','frozen_flag':'Y'}
        ]
        self.write_queue(rows)
        q = safe_read_queue()
        self.assertTrue(q['ok'])
        self.assertEqual(q['queued_count'], 1)
        self.assertEqual(q['blocked_count'], 1)
        self.assertEqual(q['in_progress_count'], 1)
        self.assertEqual(q['complete_count'], 1)
        self.assertEqual(q['total_rows'], 4)

    def test_recommendation(self):
        rows = [
            {'event_id':'a','status':'blocked','artifact':'','blockers':'x','completed_at':'','frozen_flag':''},
            {'event_id':'b','status':'queued','artifact':'','blockers':'','completed_at':'','frozen_flag':''}
        ]
        self.write_queue(rows)
        q = safe_read_queue()
        rec = summarize_queue(q['rows'])
        self.assertIn('Next eligible event', rec['recommendation'])
        self.assertIn('Blocked events', rec['recommendation'])

    def test_empty_queue(self):
        self.write_queue([])
        q = safe_read_queue()
        rec = summarize_queue(q['rows'])
        self.assertIn('No events in queue', rec['recommendation'])

if __name__ == '__main__':
    unittest.main()
