import unittest
from workflows.automation_reconciliation_pack import automation_reconciliation_pack

class TestAutomationReconciliationPack(unittest.TestCase):
    def test_all_reconciled(self):
        result = automation_reconciliation_pack({
            'event_name': 'event1',
            'automation_execution_status': 'ready',
            'execution_ready_actions': [
                {
                    'event_name': 'event1',
                    'bout_index': 0,
                    'execution_status': 'ready',
                    'delivery_key': 'dk0',
                    'publication_label': 'A',
                    'publication_order': 1,
                    'queue_action': 'run',
                    'dispatch_batch': 1,
                    'execution_plan': {'plan_type': 'default', 'steps': ['execute']},
                },
                {
                    'event_name': 'event1',
                    'bout_index': 1,
                    'execution_status': 'ready',
                    'delivery_key': 'dk1',
                    'publication_label': 'B',
                    'publication_order': 2,
                    'queue_action': 'run',
                    'dispatch_batch': 1,
                    'execution_plan': {'plan_type': 'default', 'steps': ['execute']},
                }
            ],
            'blocked_executions': [],
            'ready_bout_indices': [0, 1],
            'blocked_bout_indices': [],
            'blocker_summary': {},
            'automation_execution_summary': {'automation_execution_status': 'ready'}
        })
        self.assertEqual(result['automation_reconciliation_status'], 'ready')
        self.assertEqual(len(result['reconciled_actions']), 2)
        for entry in result['reconciled_actions']:
            self.assertEqual(entry['reconciliation_status'], 'ready')
            self.assertEqual(entry['execution_status'], 'ready')
        self.assertEqual(len(result['blocked_reconciliations']), 0)

    def test_partial_reconciliation(self):
        result = automation_reconciliation_pack({
            'event_name': 'event2',
            'automation_execution_status': 'partial',
            'execution_ready_actions': [
                {
                    'event_name': 'event2',
                    'bout_index': 0,
                    'execution_status': 'ready',
                    'delivery_key': 'dk0',
                    'publication_label': 'ESCALATE',
                    'publication_order': 1,
                    'queue_action': 'run',
                    'dispatch_batch': 1,
                    'execution_plan': {'plan_type': 'default', 'steps': ['execute']},
                }
            ],
            'blocked_executions': [
                {
                    'event_name': 'event2',
                    'bout_index': 1,
                    'execution_status': 'blocked',
                    'blocker_reason': 'fail',
                }
            ],
            'ready_bout_indices': [0],
            'blocked_bout_indices': [1],
            'blocker_summary': {'blocker_reason': {1: 'fail'}},
            'automation_execution_summary': {'automation_execution_status': 'partial'}
        })
        self.assertEqual(result['automation_reconciliation_status'], 'partial')
        self.assertEqual(len(result['reconciled_actions']), 1)
        self.assertEqual(len(result['blocked_reconciliations']), 1)
        self.assertEqual(result['blocked_reconciliations'][0]['blocker_reason'], 'fail')

    def test_all_blocked(self):
        result = automation_reconciliation_pack({
            'event_name': 'event3',
            'automation_execution_status': 'blocked',
            'execution_ready_actions': [],
            'blocked_executions': [
                {
                    'event_name': 'event3',
                    'bout_index': 0,
                    'execution_status': 'blocked',
                    'blocker_reason': 'fail0',
                },
                {
                    'event_name': 'event3',
                    'bout_index': 1,
                    'execution_status': 'blocked',
                    'blocker_reason': 'fail1',
                }
            ],
            'ready_bout_indices': [],
            'blocked_bout_indices': [0, 1],
            'blocker_summary': {'blocker_reason': {0: 'fail0', 1: 'fail1'}},
            'automation_execution_summary': {'automation_execution_status': 'blocked'}
        })
        self.assertEqual(result['automation_reconciliation_status'], 'blocked')
        self.assertEqual(len(result['reconciled_actions']), 0)
        self.assertEqual(len(result['blocked_reconciliations']), 2)
        self.assertIn(result['blocked_reconciliations'][0]['blocker_reason'], ['fail0', 'fail1'])
        self.assertIn(result['blocked_reconciliations'][1]['blocker_reason'], ['fail0', 'fail1'])

if __name__ == '__main__':
    unittest.main()
