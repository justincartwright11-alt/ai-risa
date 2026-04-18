import unittest
from workflows.automation_outcome_pack import automation_outcome_pack

class TestAutomationOutcomePack(unittest.TestCase):
    def test_all_completed(self):
        result = automation_outcome_pack({
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
                    'queue_action': 'enqueue',
                    'queue_priority': 1,
                    'dispatch_batch': 1,
                    'dispatch_reason': 'dispatch-ready',
                    'execution_plan': {'plan': 'execute'},
                },
                {
                    'event_name': 'event1',
                    'bout_index': 1,
                    'execution_status': 'ready',
                    'delivery_key': 'dk1',
                    'publication_label': 'B',
                    'publication_order': 2,
                    'queue_action': 'enqueue',
                    'queue_priority': 1,
                    'dispatch_batch': 1,
                    'dispatch_reason': 'dispatch-ready',
                    'execution_plan': {'plan': 'execute'},
                }
            ],
            'blocked_executions': [],
            'ready_bout_indices': [0, 1],
            'blocked_bout_indices': [],
            'blocker_summary': {},
            'automation_execution_summary': {'automation_execution_status': 'ready'}
        })
        self.assertEqual(result['automation_outcome_status'], 'ready')
        self.assertEqual(len(result['completed_automation_actions']), 2)
        for action in result['completed_automation_actions']:
            self.assertEqual(action['automation_outcome_state'], 'completed')
            self.assertEqual(action['execution_snapshot']['execution_status'], 'ready')
        self.assertEqual(len(result['blocked_automation_outcomes']), 0)

    def test_partial(self):
        result = automation_outcome_pack({
            'event_name': 'event2',
            'automation_execution_status': 'partial',
            'execution_ready_actions': [
                {
                    'event_name': 'event2',
                    'bout_index': 0,
                    'execution_status': 'ready',
                    'delivery_key': 'dk0',
                    'publication_label': 'A',
                    'publication_order': 1,
                    'queue_action': 'enqueue',
                    'queue_priority': 1,
                    'dispatch_batch': 1,
                    'dispatch_reason': 'dispatch-ready',
                    'execution_plan': {'plan': 'execute'},
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
        self.assertEqual(result['automation_outcome_status'], 'partial')
        self.assertEqual(len(result['completed_automation_actions']), 1)
        self.assertEqual(len(result['blocked_automation_outcomes']), 1)
        self.assertEqual(result['blocked_automation_outcomes'][0]['blocker_reason'], 'fail')

    def test_all_blocked(self):
        result = automation_outcome_pack({
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
        self.assertEqual(result['automation_outcome_status'], 'blocked')
        self.assertEqual(len(result['completed_automation_actions']), 0)
        self.assertEqual(len(result['blocked_automation_outcomes']), 2)
        self.assertIn(result['blocked_automation_outcomes'][0]['blocker_reason'], ['fail0', 'fail1'])
        self.assertIn(result['blocked_automation_outcomes'][1]['blocker_reason'], ['fail0', 'fail1'])

if __name__ == '__main__':
    unittest.main()
