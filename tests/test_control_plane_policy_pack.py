import unittest
from workflows.control_plane_policy_pack import control_plane_policy_pack

def make_status(**kwargs):
    return dict(kwargs)

class TestControlPlanePolicyPack(unittest.TestCase):
    def setUp(self):
        self.status = make_status(
            control_plane_status='partial',
            event_count=3,
            ready_event_names=['E1'],
            blocked_event_names=['E3'],
            closed_events=[
                {
                    'event_name': 'E1',
                    'event_status': 'ready',
                    'priority': 1,
                    'closure_action': 'close_event',
                    'closure_reason': 'Event closed after successful remediation',
                    'escalation_level': 0,
                    'source_card': {'event_name': 'E1'},
                },
                {
                    'event_name': 'E2',
                    'event_status': 'partial',
                    'priority': 2,
                    'closure_action': 'hold_open',
                    'closure_reason': 'Event held open for operator review',
                    'escalation_level': 1,
                    'source_card': {'event_name': 'E2'},
                }
            ],
            pending_events=[
                {
                    'event_name': 'E3',
                    'event_status': 'blocked',
                    'priority': 3,
                    'blocker_reason': 'Event is blocked',
                    'closure_snapshot': {'event_name': 'E3'}
                }
            ],
            status_cards=[
                {
                    'event_name': 'E1',
                    'event_status': 'ready',
                    'priority': 1,
                    'closure_action': 'close_event',
                    'closure_reason': 'Event closed after successful remediation',
                    'final_status': 'closed',
                    'escalation_level': 0,
                    'source_card': {'event_name': 'E1'},
                },
                {
                    'event_name': 'E2',
                    'event_status': 'partial',
                    'priority': 2,
                    'closure_action': 'hold_open',
                    'closure_reason': 'Event held open for operator review',
                    'final_status': 'pending_review',
                    'escalation_level': 1,
                    'source_card': {'event_name': 'E2'},
                }
            ],
            priority_queue=['E1', 'E2'],
            escalation_queue=['E2', 'E3'],
            blocker_summary={'E3': 'Event is blocked'},
            control_plane_status_summary={
                'status': 'partial',
                'event_count': 3,
                'closed_count': 2,
                'pending_count': 1,
                'ready_event_names': ['E1'],
                'blocked_event_names': ['E3'],
                'priority_queue': ['E1', 'E2'],
                'escalation_queue': ['E2', 'E3'],
                'blocker_summary': {'E3': 'Event is blocked'}
            }
        )

    def test_policy_ready(self):
        o = dict(self.status)
        o['status_cards'] = [dict(self.status['status_cards'][0])]
        o['pending_events'] = []
        o['ready_event_names'] = ['E1']
        o['blocked_event_names'] = []
        out = control_plane_policy_pack(o)
        self.assertEqual(out['control_plane_policy_status'], 'ready')
        self.assertEqual(len(out['policy_ready_events']), 1)
        self.assertEqual(out['policy_ready_events'][0]['policy_action'], 'proceed_policy')
        self.assertEqual(out['policy_ready_events'][0]['event_name'], 'E1')
        self.assertEqual(out['blocked_policy_events'], [])
        self.assertIn('control_plane_policy_summary', out)

    def test_policy_partial(self):
        out = control_plane_policy_pack(self.status)
        self.assertEqual(out['control_plane_policy_status'], 'partial')
        self.assertEqual(len(out['policy_ready_events']), 2)
        self.assertEqual(out['policy_ready_events'][0]['policy_action'], 'proceed_policy')
        self.assertEqual(out['policy_ready_events'][1]['policy_action'], 'review_policy')
        self.assertEqual(len(out['blocked_policy_events']), 1)
        self.assertEqual(out['blocked_policy_events'][0]['event_name'], 'E3')
        self.assertEqual(out['blocked_policy_events'][0]['blocker_reason'], 'Event is blocked')
        self.assertIn('control_plane_policy_summary', out)

    def test_policy_blocked(self):
        o = dict(self.status)
        o['status_cards'] = []
        o['pending_events'] = [dict(self.status['pending_events'][0])]
        o['ready_event_names'] = []
        o['blocked_event_names'] = ['E3']
        out = control_plane_policy_pack(o)
        self.assertEqual(out['control_plane_policy_status'], 'blocked')
        self.assertEqual(out['policy_ready_events'], [])
        self.assertEqual(len(out['blocked_policy_events']), 1)
        self.assertEqual(out['blocked_policy_events'][0]['event_name'], 'E3')
        self.assertEqual(out['blocked_policy_events'][0]['blocker_reason'], 'Event is blocked')
        self.assertIn('control_plane_policy_summary', out)

if __name__ == '__main__':
    unittest.main()
