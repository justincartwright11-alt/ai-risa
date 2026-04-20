import unittest
import os
import tempfile
import csv
from operator_dashboard.app import app

class TestQueueReadOnly(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.tempdir = tempfile.TemporaryDirectory()
        self.queue_path = os.path.join(self.tempdir.name, 'event_coverage_queue.csv')
        self.orig_path = os.environ.get('QUEUE_PATH')
        # Write a known queue file
        with open(self.queue_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['event_id','status','artifact','blockers','completed_at','frozen_flag'])
            writer.writeheader()
            writer.writerow({'event_id':'a','status':'queued','artifact':'','blockers':'','completed_at':'','frozen_flag':''})
        # Patch app/queue_utils to use temp queue
        from operator_dashboard import queue_utils
        queue_utils.QUEUE_PATH = self.queue_path

    def tearDown(self):
        self.tempdir.cleanup()

    def test_run_event_does_not_mutate_queue(self):
        # Read original contents
        with open(self.queue_path, 'r', encoding='utf-8') as f:
            orig = f.read()
        # Call run_event via chat
        resp = self.client.post('/chat/send', json={"message": "run Song vs Figueiredo tonight"})
        self.assertEqual(resp.status_code, 200)
        # Read contents again
        with open(self.queue_path, 'r', encoding='utf-8') as f:
            after = f.read()
        self.assertEqual(orig, after, 'Queue file was mutated by run_event!')

if __name__ == '__main__':
    unittest.main()
