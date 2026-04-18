import unittest
from workflows.control_plane_status_pack import control_plane_status_pack

def make_closure(**kwargs):
    return dict(kwargs)

class TestControlPlaneStatusPack(unittest.TestCase):
    def setUp(self):
        self.closure = make_closure(
            control_plane_closure_status='partial',
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
                    'remediation_outcome_snapshot': {'event_name': 'E3'}
                }
            ],
            priority_queue=['E1', 'E2'],
            escalation_queue=['E2', 'E3'],
            blocker_summary={'E3': 'Event is blocked'},
            control_plane_closure_summary={
                'closure_status': 'partial',
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

    def test_status_ready(self):
        o = dict(self.closure)
        o['closed_events'] = [dict(self.closure['closed_events'][0])]
        o['pending_events'] = []
        o['ready_event_names'] = ['E1']
        o['blocked_event_names'] = []
        out = control_plane_status_pack(o)
        self.assertEqual(out['control_plane_status'], 'ready')
        self.assertEqual(len(out['status_cards']), 1)
        self.assertEqual(out['status_cards'][0]['final_status'], 'closed')
        self.assertEqual(out['status_cards'][0]['event_name'], 'E1')
        self.assertIn('control_plane_status_summary', out)

    def test_status_partial(self):
        out = control_plane_status_pack(self.closure)
        self.assertEqual(out['control_plane_status'], 'partial')
        self.assertEqual(len(out['status_cards']), 2)
        self.assertEqual(out['status_cards'][0]['final_status'], 'closed')
        self.assertEqual(out['status_cards'][1]['final_status'], 'pending_review')
        self.assertEqual(len(out['pending_events']), 1)
        self.assertEqual(out['pending_events'][0]['event_name'], 'E3')
        self.assertEqual(out['pending_events'][0]['blocker_reason'], 'Event is blocked')
        self.assertIn('control_plane_status_summary', out)

    def test_status_blocked(self):
        o = dict(self.closure)
        o['closed_events'] = []
        o['pending_events'] = [dict(self.closure['pending_events'][0])]
        o['ready_event_names'] = []
        o['blocked_event_names'] = ['E3']
        out = control_plane_status_pack(o)
        self.assertEqual(out['control_plane_status'], 'blocked')
        self.assertEqual(out['status_cards'], [])
        self.assertEqual(len(out['pending_events']), 1)
        self.assertEqual(out['pending_events'][0]['event_name'], 'E3')
        self.assertEqual(out['pending_events'][0]['blocker_reason'], 'Event is blocked')
        self.assertIn('control_plane_status_summary', out)

if __name__ == '__main__':
    unittest.main()
