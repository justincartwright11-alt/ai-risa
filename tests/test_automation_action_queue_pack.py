import unittest
from workflows.automation_action_queue_pack import automation_action_queue_pack

class TestAutomationActionQueuePack(unittest.TestCase):
    def test_all_queued(self):
        result = automation_action_queue_pack({
            'event_name': 'event1',
            'automation_trigger_status': 'ready',
            'ready_triggers': [
                {
                    'event_name': 'event1',
                    'bout_index': 0,
                    'trigger_status': 'ready',
                    'delivery_key': 'dk0',
                    'publication_label': 'A',
                    'publication_order': 1,
                    'trigger_action': 'proceed',
                    'trigger_reason': 'automation-ready',
                    'system_state': 'ready',
                    'system_status_snapshot': {'bout_index': 0}
                },
                {
                    'event_name': 'event1',
                    'bout_index': 1,
                    'trigger_status': 'ready',
                    'delivery_key': 'dk1',
                    'publication_label': 'B',
                    'publication_order': 2,
                    'trigger_action': 'proceed',
                    'trigger_reason': 'automation-ready',
                    'system_state': 'ready',
                    'system_status_snapshot': {'bout_index': 1}
                }
            ],
            'blocked_triggers': [],
            'ready_bout_indices': [0, 1],
            'blocked_bout_indices': [],
            'blocker_summary': {},
            'automation_trigger_summary': {'automation_trigger_status': 'ready'}
        })
        self.assertEqual(result['automation_action_queue_status'], 'ready')
        self.assertEqual(len(result['queued_actions']), 2)
        for action in result['queued_actions']:
            self.assertEqual(action['queue_status'], 'queued')
            self.assertEqual(action['queue_action'], 'enqueue')
            self.assertEqual(action['queue_priority'], 1)
        self.assertEqual(len(result['blocked_actions']), 0)

    def test_partial(self):
        result = automation_action_queue_pack({
            'event_name': 'event2',
            'automation_trigger_status': 'partial',
            'ready_triggers': [
                {
                    'event_name': 'event2',
                    'bout_index': 0,
                    'trigger_status': 'ready',
                    'delivery_key': 'dk0',
                    'publication_label': 'A',
                    'publication_order': 1,
                    'trigger_action': 'proceed',
                    'trigger_reason': 'automation-ready',
                    'system_state': 'ready',
                    'system_status_snapshot': {'bout_index': 0}
                }
            ],
            'blocked_triggers': [
                {
                    'event_name': 'event2',
                    'bout_index': 1,
                    'trigger_status': 'blocked',
                    'blocker_reason': 'fail',
                    'system_status_snapshot': {'bout_index': 1}
                }
            ],
            'ready_bout_indices': [0],
            'blocked_bout_indices': [1],
            'blocker_summary': {'blocker_reason': {1: 'fail'}},
            'automation_trigger_summary': {'automation_trigger_status': 'partial'}
        })
        self.assertEqual(result['automation_action_queue_status'], 'partial')
        self.assertEqual(len(result['queued_actions']), 1)
        self.assertEqual(len(result['blocked_actions']), 1)
        self.assertEqual(result['blocked_actions'][0]['blocker_reason'], 'fail')

    def test_all_blocked(self):
        result = automation_action_queue_pack({
            'event_name': 'event3',
            'automation_trigger_status': 'blocked',
            'ready_triggers': [],
            'blocked_triggers': [
                {
                    'event_name': 'event3',
                    'bout_index': 0,
                    'trigger_status': 'blocked',
                    'blocker_reason': 'fail0',
                    'system_status_snapshot': {'bout_index': 0}
                },
                {
                    'event_name': 'event3',
                    'bout_index': 1,
                    'trigger_status': 'blocked',
                    'blocker_reason': 'fail1',
                    'system_status_snapshot': {'bout_index': 1}
                }
            ],
            'ready_bout_indices': [],
            'blocked_bout_indices': [0, 1],
            'blocker_summary': {'blocker_reason': {0: 'fail0', 1: 'fail1'}},
            'automation_trigger_summary': {'automation_trigger_status': 'blocked'}
        })
        self.assertEqual(result['automation_action_queue_status'], 'blocked')
        self.assertEqual(len(result['queued_actions']), 0)
        self.assertEqual(len(result['blocked_actions']), 2)
        self.assertIn(result['blocked_actions'][0]['blocker_reason'], ['fail0', 'fail1'])
        self.assertIn(result['blocked_actions'][1]['blocker_reason'], ['fail0', 'fail1'])

if __name__ == '__main__':
    unittest.main()
