import unittest
from workflows.event_control_summary_pack import event_control_summary_pack

class TestEventControlSummaryPack(unittest.TestCase):
    def test_all_publish_ready(self):
        result = event_control_summary_pack({
            'event_name': 'event1',
            'automation_closure_status': 'ready',
            'closed_entries': [
                {
                    'event_name': 'event1',
                    'bout_index': 0,
                    'closure_status': 'closed',
                    'closure_action': 'close',
                },
                {
                    'event_name': 'event1',
                    'bout_index': 1,
                    'closure_status': 'closed',
                    'closure_action': 'close',
                }
            ],
            'pending_entries': [],
            'ready_bout_indices': [0, 1],
            'blocked_bout_indices': [],
            'blocker_summary': {},
            'automation_closure_summary': {'automation_closure_status': 'ready'}
        })
        self.assertEqual(result['event_control_status'], 'ready')
        self.assertEqual(result['publish_ready_count'], 2)
        self.assertEqual(result['review_required_count'], 0)
        self.assertEqual(result['manual_intervention_count'], 0)
        self.assertEqual(result['blocked_count'], 0)
        self.assertEqual(result['total_bouts'], 2)

    def test_partial(self):
        result = event_control_summary_pack({
            'event_name': 'event2',
            'automation_closure_status': 'partial',
            'closed_entries': [
                {
                    'event_name': 'event2',
                    'bout_index': 0,
                    'closure_status': 'closed',
                    'closure_action': 'close',
                },
                {
                    'event_name': 'event2',
                    'bout_index': 1,
                    'closure_status': 'closed',
                    'closure_action': 'hold_open',
                }
            ],
            'pending_entries': [
                {
                    'event_name': 'event2',
                    'bout_index': 2,
                    'closure_status': 'pending',
                    'blocker_reason': 'fail',
                }
            ],
            'ready_bout_indices': [0, 1],
            'blocked_bout_indices': [2],
            'blocker_summary': {'blocker_reason': {2: 'fail'}},
            'automation_closure_summary': {'automation_closure_status': 'partial'}
        })
        self.assertEqual(result['event_control_status'], 'partial')
        self.assertEqual(result['publish_ready_count'], 1)
        self.assertEqual(result['review_required_count'], 1)
        self.assertEqual(result['manual_intervention_count'], 0)
        self.assertEqual(result['blocked_count'], 1)
        self.assertEqual(result['total_bouts'], 3)

    def test_all_blocked(self):
        result = event_control_summary_pack({
            'event_name': 'event3',
            'automation_closure_status': 'blocked',
            'closed_entries': [],
            'pending_entries': [
                {
                    'event_name': 'event3',
                    'bout_index': 0,
                    'closure_status': 'pending',
                    'blocker_reason': 'fail0',
                },
                {
                    'event_name': 'event3',
                    'bout_index': 1,
                    'closure_status': 'pending',
                    'blocker_reason': 'fail1',
                }
            ],
            'ready_bout_indices': [],
            'blocked_bout_indices': [0, 1],
            'blocker_summary': {'blocker_reason': {0: 'fail0', 1: 'fail1'}},
            'automation_closure_summary': {'automation_closure_status': 'blocked'}
        })
        self.assertEqual(result['event_control_status'], 'blocked')
        self.assertEqual(result['publish_ready_count'], 0)
        self.assertEqual(result['review_required_count'], 0)
        self.assertEqual(result['manual_intervention_count'], 0)
        self.assertEqual(result['blocked_count'], 2)
        self.assertEqual(result['total_bouts'], 2)

if __name__ == '__main__':
    unittest.main()
