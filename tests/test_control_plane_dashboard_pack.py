import unittest
from workflows.control_plane_dashboard_pack import control_plane_dashboard_pack

def make_summary(**kwargs):
    return dict(kwargs)

class TestControlPlaneDashboardPack(unittest.TestCase):
    def setUp(self):
        self.summary = make_summary(
            control_plane_status='ready',
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
                    'source_summary': {'foo': 'bar'}
                },
                {
                    'event_name': 'E2',
                    'event_status': 'partial',
                    'priority': 2,
                    'next_action': 'review',
                    'next_reason': 'Needs review',
                    'source_summary': {'foo': 'baz'}
                },
                {
                    'event_name': 'E3',
                    'event_status': 'blocked',
                    'priority': 3,
                    'next_action': 'manual_intervention',
                    'next_reason': 'Blocked',
                    'source_summary': {'foo': 'qux'}
                }
            ],
            priority_queue=['E1', 'E2'],
            escalation_queue=['E2', 'E3']
        )

    def test_dashboard_ready(self):
        s = dict(self.summary)
        s['ready_events'] = ['E1', 'E2', 'E3']
        s['partial_events'] = []
        s['blocked_events'] = []
        out = control_plane_dashboard_pack(s)
        self.assertEqual(out['control_plane_dashboard_status'], 'ready')
        self.assertEqual(out['event_count'], 3)
        self.assertEqual(out['portfolio_status'], 'ready')
        self.assertEqual(len(out['dashboard_cards']), 3)
        self.assertEqual(out['dashboard_cards'][0]['publish_ready_count'], 1)
        self.assertEqual(out['dashboard_cards'][1]['review_required_count'], 1)
        self.assertEqual(out['dashboard_cards'][2]['blocked_count'], 1)
        self.assertIn('dashboard_sections', out)
        self.assertIn('control_plane_dashboard_summary', out)

    def test_dashboard_partial(self):
        s = dict(self.summary)
        out = control_plane_dashboard_pack(s)
        self.assertEqual(out['control_plane_dashboard_status'], 'partial')
        self.assertEqual(out['event_count'], 3)
        self.assertEqual(out['portfolio_status'], 'ready')
        self.assertEqual(len(out['dashboard_cards']), 3)
        self.assertEqual(out['dashboard_cards'][0]['publish_ready_count'], 1)
        self.assertEqual(out['dashboard_cards'][1]['review_required_count'], 1)
        self.assertEqual(out['dashboard_cards'][2]['blocked_count'], 1)
        self.assertIn('dashboard_sections', out)
        self.assertIn('control_plane_dashboard_summary', out)

    def test_dashboard_blocked(self):
        s = dict(self.summary)
        s['ready_events'] = []
        s['partial_events'] = []
        s['blocked_events'] = ['E1', 'E2', 'E3']
        out = control_plane_dashboard_pack(s)
        self.assertEqual(out['control_plane_dashboard_status'], 'blocked')
        self.assertEqual(out['event_count'], 3)
        self.assertEqual(out['portfolio_status'], 'ready')
        self.assertEqual(len(out['dashboard_cards']), 3)
        self.assertEqual(out['dashboard_cards'][2]['blocked_count'], 1)
        self.assertIn('dashboard_sections', out)
        self.assertIn('control_plane_dashboard_summary', out)

if __name__ == '__main__':
    unittest.main()
