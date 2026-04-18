import unittest
from workflows.automation_dispatch_pack import automation_dispatch_pack

class TestAutomationDispatchPack(unittest.TestCase):
    def test_all_dispatch_ready(self):
        result = automation_dispatch_pack({
            'event_name': 'event1',
            'automation_action_queue_status': 'ready',
            'queued_actions': [
                {
                    'event_name': 'event1',
                    'bout_index': 0,
                    'queue_status': 'queued',
                    'delivery_key': 'dk0',
                    'publication_label': 'A',
                    'publication_order': 1,
                    'queue_action': 'enqueue',
                    'queue_priority': 1,
                    'automation_trigger_snapshot': {'bout_index': 0}
                },
                {
                    'event_name': 'event1',
                    'bout_index': 1,
                    'queue_status': 'queued',
                    'delivery_key': 'dk1',
                    'publication_label': 'B',
                    'publication_order': 2,
                    'queue_action': 'enqueue',
                    'queue_priority': 1,
                    'automation_trigger_snapshot': {'bout_index': 1}
                }
            ],
            'blocked_actions': [],
            'ready_bout_indices': [0, 1],
            'blocked_bout_indices': [],
            'blocker_summary': {},
            'automation_action_queue_summary': {'automation_action_queue_status': 'ready'}
        })
        self.assertEqual(result['automation_dispatch_status'], 'ready')
        self.assertEqual(len(result['dispatch_ready_actions']), 2)
        for action in result['dispatch_ready_actions']:
            self.assertEqual(action['dispatch_status'], 'ready')
            self.assertEqual(action['dispatch_batch'], 1)
            self.assertEqual(action['dispatch_reason'], 'dispatch-ready')
        self.assertEqual(len(result['blocked_dispatches']), 0)

    def test_partial(self):
        result = automation_dispatch_pack({
            'event_name': 'event2',
            'automation_action_queue_status': 'partial',
            'queued_actions': [
                {
                    'event_name': 'event2',
                    'bout_index': 0,
                    'queue_status': 'queued',
                    'delivery_key': 'dk0',
                    'publication_label': 'A',
                    'publication_order': 1,
                    'queue_action': 'enqueue',
                    'queue_priority': 1,
                    'automation_trigger_snapshot': {'bout_index': 0}
                }
            ],
            'blocked_actions': [
                {
                    'event_name': 'event2',
                    'bout_index': 1,
                    'queue_status': 'blocked',
                    'blocker_reason': 'fail',
                    'automation_trigger_snapshot': {'bout_index': 1}
                }
            ],
            'ready_bout_indices': [0],
            'blocked_bout_indices': [1],
            'blocker_summary': {'blocker_reason': {1: 'fail'}},
            'automation_action_queue_summary': {'automation_action_queue_status': 'partial'}
        })
        self.assertEqual(result['automation_dispatch_status'], 'partial')
        self.assertEqual(len(result['dispatch_ready_actions']), 1)
        self.assertEqual(len(result['blocked_dispatches']), 1)
        self.assertEqual(result['blocked_dispatches'][0]['blocker_reason'], 'fail')

    def test_all_blocked(self):
        result = automation_dispatch_pack({
            'event_name': 'event3',
            'automation_action_queue_status': 'blocked',
            'queued_actions': [],
            'blocked_actions': [
                {
                    'event_name': 'event3',
                    'bout_index': 0,
                    'queue_status': 'blocked',
                    'blocker_reason': 'fail0',
                    'automation_trigger_snapshot': {'bout_index': 0}
                },
                {
                    'event_name': 'event3',
                    'bout_index': 1,
                    'queue_status': 'blocked',
                    'blocker_reason': 'fail1',
                    'automation_trigger_snapshot': {'bout_index': 1}
                }
            ],
            'ready_bout_indices': [],
            'blocked_bout_indices': [0, 1],
            'blocker_summary': {'blocker_reason': {0: 'fail0', 1: 'fail1'}},
            'automation_action_queue_summary': {'automation_action_queue_status': 'blocked'}
        })
        self.assertEqual(result['automation_dispatch_status'], 'blocked')
        self.assertEqual(len(result['dispatch_ready_actions']), 0)
        self.assertEqual(len(result['blocked_dispatches']), 2)
        self.assertIn(result['blocked_dispatches'][0]['blocker_reason'], ['fail0', 'fail1'])
        self.assertIn(result['blocked_dispatches'][1]['blocker_reason'], ['fail0', 'fail1'])

if __name__ == '__main__':
    unittest.main()
