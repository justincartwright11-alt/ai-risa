import unittest
from workflows.automation_closure_pack import automation_closure_pack

class TestAutomationClosurePack(unittest.TestCase):
    def test_all_closed(self):
        result = automation_closure_pack({
            'event_name': 'event1',
            'automation_reconciliation_status': 'ready',
            'reconciled_actions': [
                {
                    'event_name': 'event1',
                    'bout_index': 0,
                    'reconciliation_status': 'ready',
                    'delivery_key': 'dk0',
                    'publication_label': 'A',
                    'publication_order': 1,
                },
                {
                    'event_name': 'event1',
                    'bout_index': 1,
                    'reconciliation_status': 'ready',
                    'delivery_key': 'dk1',
                    'publication_label': 'B',
                    'publication_order': 2,
                }
            ],
            'blocked_reconciliations': [],
            'ready_bout_indices': [0, 1],
            'blocked_bout_indices': [],
            'blocker_summary': {},
            'automation_reconciliation_summary': {'automation_reconciliation_status': 'ready'}
        })
        self.assertEqual(result['automation_closure_status'], 'ready')
        self.assertEqual(len(result['closed_entries']), 2)
        for entry in result['closed_entries']:
            self.assertEqual(entry['closure_status'], 'closed')
            self.assertEqual(entry['closure_action'], 'close')
        self.assertEqual(len(result['pending_entries']), 0)

    def test_partial_closure(self):
        result = automation_closure_pack({
            'event_name': 'event2',
            'automation_reconciliation_status': 'partial',
            'reconciled_actions': [
                {
                    'event_name': 'event2',
                    'bout_index': 0,
                    'reconciliation_status': 'ready',
                    'delivery_key': 'dk0',
                    'publication_label': 'ESCALATE',
                    'publication_order': 1,
                }
            ],
            'blocked_reconciliations': [
                {
                    'event_name': 'event2',
                    'bout_index': 1,
                    'reconciliation_status': 'blocked',
                    'blocker_reason': 'fail',
                }
            ],
            'ready_bout_indices': [0],
            'blocked_bout_indices': [1],
            'blocker_summary': {'blocker_reason': {1: 'fail'}},
            'automation_reconciliation_summary': {'automation_reconciliation_status': 'partial'}
        })
        self.assertEqual(result['automation_closure_status'], 'partial')
        self.assertEqual(len(result['closed_entries']), 1)
        self.assertEqual(len(result['pending_entries']), 1)
        self.assertEqual(result['pending_entries'][0]['blocker_reason'], 'fail')

    def test_all_pending(self):
        result = automation_closure_pack({
            'event_name': 'event3',
            'automation_reconciliation_status': 'blocked',
            'reconciled_actions': [],
            'blocked_reconciliations': [
                {
                    'event_name': 'event3',
                    'bout_index': 0,
                    'reconciliation_status': 'blocked',
                    'blocker_reason': 'fail0',
                },
                {
                    'event_name': 'event3',
                    'bout_index': 1,
                    'reconciliation_status': 'blocked',
                    'blocker_reason': 'fail1',
                }
            ],
            'ready_bout_indices': [],
            'blocked_bout_indices': [0, 1],
            'blocker_summary': {'blocker_reason': {0: 'fail0', 1: 'fail1'}},
            'automation_reconciliation_summary': {'automation_reconciliation_status': 'blocked'}
        })
        self.assertEqual(result['automation_closure_status'], 'blocked')
        self.assertEqual(len(result['closed_entries']), 0)
        self.assertEqual(len(result['pending_entries']), 2)
        self.assertIn(result['pending_entries'][0]['blocker_reason'], ['fail0', 'fail1'])
        self.assertIn(result['pending_entries'][1]['blocker_reason'], ['fail0', 'fail1'])

if __name__ == '__main__':
    unittest.main()
