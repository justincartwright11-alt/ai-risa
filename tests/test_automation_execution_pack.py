import unittest
from workflows.automation_execution_pack import automation_execution_pack

class TestAutomationExecutionPack(unittest.TestCase):
    def test_all_execution_ready(self):
        result = automation_execution_pack({
            'event_name': 'event1',
            'automation_dispatch_status': 'ready',
            'dispatch_ready_actions': [
                {
                    'event_name': 'event1',
                    'bout_index': 0,
                    'dispatch_status': 'ready',
                    'delivery_key': 'dk0',
                    'publication_label': 'A',
                    'publication_order': 1,
                    'queue_action': 'enqueue',
                    'queue_priority': 1,
                    'dispatch_batch': 1,
                    'dispatch_reason': 'dispatch-ready',
                    'automation_trigger_snapshot': {'bout_index': 0}
                },
                {
                    'event_name': 'event1',
                    'bout_index': 1,
                    'dispatch_status': 'ready',
                    'delivery_key': 'dk1',
                    'publication_label': 'B',
                    'publication_order': 2,
                    'queue_action': 'enqueue',
                    'queue_priority': 1,
                    'dispatch_batch': 1,
                    'dispatch_reason': 'dispatch-ready',
                    'automation_trigger_snapshot': {'bout_index': 1}
                }
            ],
            'blocked_dispatches': [],
            'ready_bout_indices': [0, 1],
            'blocked_bout_indices': [],
            'blocker_summary': {},
            'automation_dispatch_summary': {'automation_dispatch_status': 'ready'}
        })
        self.assertEqual(result['automation_execution_status'], 'ready')
        self.assertEqual(len(result['execution_ready_actions']), 2)
        for action in result['execution_ready_actions']:
            self.assertEqual(action['execution_status'], 'ready')
            self.assertEqual(action['execution_plan'], {'plan_type': 'default', 'steps': ['execute']})
        self.assertEqual(len(result['blocked_executions']), 0)

    def test_partial(self):
        result = automation_execution_pack({
            'event_name': 'event2',
            'automation_dispatch_status': 'partial',
            'dispatch_ready_actions': [
                {
                    'event_name': 'event2',
                    'bout_index': 0,
                    'dispatch_status': 'ready',
                    'delivery_key': 'dk0',
                    'publication_label': 'A',
                    'publication_order': 1,
                    'queue_action': 'enqueue',
                    'queue_priority': 1,
                    'dispatch_batch': 1,
                    'dispatch_reason': 'dispatch-ready',
                    'automation_trigger_snapshot': {'bout_index': 0}
                }
            ],
            'blocked_dispatches': [
                {
                    'event_name': 'event2',
                    'bout_index': 1,
                    'dispatch_status': 'blocked',
                    'blocker_reason': 'fail',
                    'automation_trigger_snapshot': {'bout_index': 1}
                }
            ],
            'ready_bout_indices': [0],
            'blocked_bout_indices': [1],
            'blocker_summary': {'blocker_reason': {1: 'fail'}},
            'automation_dispatch_summary': {'automation_dispatch_status': 'partial'}
        })
        self.assertEqual(result['automation_execution_status'], 'partial')
        self.assertEqual(len(result['execution_ready_actions']), 1)
        self.assertEqual(len(result['blocked_executions']), 1)
        self.assertEqual(result['blocked_executions'][0]['blocker_reason'], 'fail')

    def test_all_blocked(self):
        result = automation_execution_pack({
            'event_name': 'event3',
            'automation_dispatch_status': 'blocked',
            'dispatch_ready_actions': [],
            'blocked_dispatches': [
                {
                    'event_name': 'event3',
                    'bout_index': 0,
                    'dispatch_status': 'blocked',
                    'blocker_reason': 'fail0',
                    'automation_trigger_snapshot': {'bout_index': 0}
                },
                {
                    'event_name': 'event3',
                    'bout_index': 1,
                    'dispatch_status': 'blocked',
                    'blocker_reason': 'fail1',
                    'automation_trigger_snapshot': {'bout_index': 1}
                }
            ],
            'ready_bout_indices': [],
            'blocked_bout_indices': [0, 1],
            'blocker_summary': {'blocker_reason': {0: 'fail0', 1: 'fail1'}},
            'automation_dispatch_summary': {'automation_dispatch_status': 'blocked'}
        })
        self.assertEqual(result['automation_execution_status'], 'blocked')
        self.assertEqual(len(result['execution_ready_actions']), 0)
        self.assertEqual(len(result['blocked_executions']), 2)
        self.assertIn(result['blocked_executions'][0]['blocker_reason'], ['fail0', 'fail1'])
        self.assertIn(result['blocked_executions'][1]['blocker_reason'], ['fail0', 'fail1'])

if __name__ == '__main__':
    unittest.main()
