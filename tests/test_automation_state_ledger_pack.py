import unittest
from workflows.automation_state_ledger_pack import automation_state_ledger_pack

class TestAutomationStateLedgerPack(unittest.TestCase):
    def test_all_ledger_ready(self):
        result = automation_state_ledger_pack({
            'event_name': 'event1',
            'automation_outcome_status': 'ready',
            'completed_automation_actions': [
                {
                    'event_name': 'event1',
                    'bout_index': 0,
                    'automation_outcome_state': 'completed',
                    'delivery_key': 'dk0',
                    'publication_label': 'A',
                    'publication_order': 1,
                    'queue_action': 'enqueue',
                    'dispatch_batch': 1,
                    'execution_plan': {'plan': 'execute'},
                    'execution_snapshot': {'execution_status': 'ready'},
                },
                {
                    'event_name': 'event1',
                    'bout_index': 1,
                    'automation_outcome_state': 'completed',
                    'delivery_key': 'dk1',
                    'publication_label': 'B',
                    'publication_order': 2,
                    'queue_action': 'enqueue',
                    'dispatch_batch': 1,
                    'execution_plan': {'plan': 'execute'},
                    'execution_snapshot': {'execution_status': 'ready'},
                }
            ],
            'blocked_automation_outcomes': [],
            'ready_bout_indices': [0, 1],
            'blocked_bout_indices': [],
            'blocker_summary': {},
            'automation_outcome_summary': {'automation_outcome_status': 'ready'}
        })
        self.assertEqual(result['automation_state_ledger_status'], 'ready')
        self.assertEqual(len(result['ledger_entries']), 2)
        for entry in result['ledger_entries']:
            self.assertEqual(entry['ledger_status'], 'ready')
            self.assertEqual(entry['execution_snapshot']['execution_status'], 'ready')
        self.assertEqual(len(result['blocked_ledger_entries']), 0)

    def test_partial(self):
        result = automation_state_ledger_pack({
            'event_name': 'event2',
            'automation_outcome_status': 'partial',
            'completed_automation_actions': [
                {
                    'event_name': 'event2',
                    'bout_index': 0,
                    'automation_outcome_state': 'completed',
                    'delivery_key': 'dk0',
                    'publication_label': 'A',
                    'publication_order': 1,
                    'queue_action': 'enqueue',
                    'dispatch_batch': 1,
                    'execution_plan': {'plan': 'execute'},
                    'execution_snapshot': {'execution_status': 'ready'},
                }
            ],
            'blocked_automation_outcomes': [
                {
                    'event_name': 'event2',
                    'bout_index': 1,
                    'automation_outcome_state': 'blocked',
                    'blocker_reason': 'fail',
                }
            ],
            'ready_bout_indices': [0],
            'blocked_bout_indices': [1],
            'blocker_summary': {'blocker_reason': {1: 'fail'}},
            'automation_outcome_summary': {'automation_outcome_status': 'partial'}
        })
        self.assertEqual(result['automation_state_ledger_status'], 'partial')
        self.assertEqual(len(result['ledger_entries']), 1)
        self.assertEqual(len(result['blocked_ledger_entries']), 1)
        self.assertEqual(result['blocked_ledger_entries'][0]['blocker_reason'], 'fail')

    def test_all_blocked(self):
        result = automation_state_ledger_pack({
            'event_name': 'event3',
            'automation_outcome_status': 'blocked',
            'completed_automation_actions': [],
            'blocked_automation_outcomes': [
                {
                    'event_name': 'event3',
                    'bout_index': 0,
                    'automation_outcome_state': 'blocked',
                    'blocker_reason': 'fail0',
                },
                {
                    'event_name': 'event3',
                    'bout_index': 1,
                    'automation_outcome_state': 'blocked',
                    'blocker_reason': 'fail1',
                }
            ],
            'ready_bout_indices': [],
            'blocked_bout_indices': [0, 1],
            'blocker_summary': {'blocker_reason': {0: 'fail0', 1: 'fail1'}},
            'automation_outcome_summary': {'automation_outcome_status': 'blocked'}
        })
        self.assertEqual(result['automation_state_ledger_status'], 'blocked')
        self.assertEqual(len(result['ledger_entries']), 0)
        self.assertEqual(len(result['blocked_ledger_entries']), 2)
        self.assertIn(result['blocked_ledger_entries'][0]['blocker_reason'], ['fail0', 'fail1'])
        self.assertIn(result['blocked_ledger_entries'][1]['blocker_reason'], ['fail0', 'fail1'])

if __name__ == '__main__':
    unittest.main()
