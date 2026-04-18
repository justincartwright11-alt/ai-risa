import unittest
from workflows.control_plane_action_queue_pack import control_plane_action_queue_pack

def make_dashboard(**kwargs):
    return dict(kwargs)

class TestControlPlaneActionQueuePack(unittest.TestCase):
    def setUp(self):
        self.dashboard = make_dashboard(
            control_plane_dashboard_status='partial',
            event_count=3,
            portfolio_status='ready',
            ready_events=['E1'],
            partial_events=['E2'],
            blocked_events=['E3'],
            dashboard_cards=[
                {
                    'event_name': 'E1',
                    'event_status': 'ready',
                    'priority': 1,
                    'next_action': 'proceed',
                    'next_reason': 'Ready to proceed',
                },
                {
                    'event_name': 'E2',
                    'event_status': 'partial',
                    'priority': 2,
                    'next_action': 'review',
                    'next_reason': 'Needs review',
                },
                {
                    'event_name': 'E3',
                    'event_status': 'blocked',
                    'priority': 3,
                    'next_action': 'manual_intervention',
                    'next_reason': 'Blocked',
                }
            ],
            priority_queue=['E1', 'E2'],
            escalation_queue=['E2', 'E3']
        )

    def test_queue_ready(self):
        d = dict(self.dashboard)
        d['dashboard_cards'] = [dict(self.dashboard['dashboard_cards'][0])]
        d['ready_events'] = ['E1']
        d['partial_events'] = []
        d['blocked_events'] = []
        out = control_plane_action_queue_pack(d)
        self.assertEqual(out['control_plane_action_queue_status'], 'ready')
        self.assertEqual(len(out['queued_actions']), 1)
        self.assertEqual(out['queued_actions'][0]['queue_action'], 'queue_proceed')
        self.assertEqual(out['queued_actions'][0]['event_name'], 'E1')
        self.assertEqual(out['blocked_actions'], [])

    def test_queue_partial(self):
        out = control_plane_action_queue_pack(self.dashboard)
        self.assertEqual(out['control_plane_action_queue_status'], 'partial')
        self.assertEqual(len(out['queued_actions']), 2)
        self.assertEqual(out['queued_actions'][0]['queue_action'], 'queue_proceed')
        self.assertEqual(out['queued_actions'][1]['queue_action'], 'queue_review')
        self.assertEqual(len(out['blocked_actions']), 1)
        self.assertEqual(out['blocked_actions'][0]['event_name'], 'E3')
        self.assertEqual(out['blocked_actions'][0]['blocker_reason'], 'Event is blocked')

    def test_queue_blocked(self):
        d = dict(self.dashboard)
        d['dashboard_cards'] = [dict(self.dashboard['dashboard_cards'][2])]
        d['ready_events'] = []
        d['partial_events'] = []
        d['blocked_events'] = ['E3']
        out = control_plane_action_queue_pack(d)
        self.assertEqual(out['control_plane_action_queue_status'], 'blocked')
        self.assertEqual(out['queued_actions'], [])
        self.assertEqual(len(out['blocked_actions']), 1)
        self.assertEqual(out['blocked_actions'][0]['event_name'], 'E3')
        self.assertEqual(out['blocked_actions'][0]['blocker_reason'], 'Event is blocked')

if __name__ == '__main__':
    unittest.main()
