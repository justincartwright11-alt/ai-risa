import unittest
from workflows.automation_trigger_pack import automation_trigger_pack

class TestAutomationTriggerPack(unittest.TestCase):
    def test_all_ready(self):
        result = automation_trigger_pack({
            'event_name': 'event1',
            'system_status': 'ready',
            'ready_bout_indices': [0, 1],
            'blocked_bout_indices': [],
            'completed_bout_indices': [0, 1],
            'blocked_bout_count': 0,
            'completed_bout_count': 2,
            'blocker_summary': {},
            'system_status_summary': {'system_status': 'ready'},
            'system_status_entries': [
                {
                    'event_name': 'event1',
                    'bout_index': 0,
                    'system_state': 'ready',
                    'delivery_key': 'dk0',
                    'publication_label': 'A',
                    'publication_order': 1,
                    'outcome_state': 'completed',
                    'final_resolution': 'ok',
                    'remediation_snapshot': {'x': 1}
                },
                {
                    'event_name': 'event1',
                    'bout_index': 1,
                    'system_state': 'ready',
                    'delivery_key': 'dk1',
                    'publication_label': 'B',
                    'publication_order': 2,
                    'outcome_state': 'completed',
                    'final_resolution': 'ok',
                    'remediation_snapshot': {'x': 2}
                }
            ]
        })
        self.assertEqual(result['automation_trigger_status'], 'ready')
        self.assertEqual(len(result['ready_triggers']), 2)
        for trig in result['ready_triggers']:
            self.assertEqual(trig['trigger_status'], 'ready')
            self.assertEqual(trig['trigger_action'], 'proceed')
            self.assertEqual(trig['trigger_reason'], 'automation-ready')
        self.assertEqual(len(result['blocked_triggers']), 0)

    def test_partial(self):
        result = automation_trigger_pack({
            'event_name': 'event2',
            'system_status': 'partial',
            'ready_bout_indices': [0],
            'blocked_bout_indices': [1],
            'completed_bout_indices': [0],
            'blocked_bout_count': 1,
            'completed_bout_count': 1,
            'blocker_summary': {'blocker_reason': {1: 'fail'}},
            'system_status_summary': {'system_status': 'partial'},
            'system_status_entries': [
                {
                    'event_name': 'event2',
                    'bout_index': 0,
                    'system_state': 'ready',
                    'delivery_key': 'dk0',
                    'publication_label': 'A',
                    'publication_order': 1,
                    'outcome_state': 'completed',
                    'final_resolution': 'ok',
                    'remediation_snapshot': {'x': 1}
                },
                {
                    'event_name': 'event2',
                    'bout_index': 1,
                    'system_state': 'blocked',
                    'blocker_reason': 'fail',
                    'remediation_snapshot': {'x': 2}
                }
            ]
        })
        self.assertEqual(result['automation_trigger_status'], 'partial')
        self.assertEqual(len(result['ready_triggers']), 1)
        self.assertEqual(len(result['blocked_triggers']), 1)
        self.assertEqual(result['blocked_triggers'][0]['blocker_reason'], 'fail')

    def test_all_blocked(self):
        result = automation_trigger_pack({
            'event_name': 'event3',
            'system_status': 'blocked',
            'ready_bout_indices': [],
            'blocked_bout_indices': [0, 1],
            'completed_bout_indices': [],
            'blocked_bout_count': 2,
            'completed_bout_count': 0,
            'blocker_summary': {'blocker_reason': {0: 'fail0', 1: 'fail1'}},
            'system_status_summary': {'system_status': 'blocked'},
            'system_status_entries': [
                {
                    'event_name': 'event3',
                    'bout_index': 0,
                    'system_state': 'blocked',
                    'blocker_reason': 'fail0',
                    'remediation_snapshot': {'x': 1}
                },
                {
                    'event_name': 'event3',
                    'bout_index': 1,
                    'system_state': 'blocked',
                    'blocker_reason': 'fail1',
                    'remediation_snapshot': {'x': 2}
                }
            ]
        })
        self.assertEqual(result['automation_trigger_status'], 'blocked')
        self.assertEqual(len(result['ready_triggers']), 0)
        self.assertEqual(len(result['blocked_triggers']), 2)
        self.assertIn(result['blocked_triggers'][0]['blocker_reason'], ['fail0', 'fail1'])
        self.assertIn(result['blocked_triggers'][1]['blocker_reason'], ['fail0', 'fail1'])

if __name__ == '__main__':
    unittest.main()
