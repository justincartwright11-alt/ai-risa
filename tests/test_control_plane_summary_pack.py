import unittest
from workflows.control_plane_summary_pack import control_plane_summary_pack

def make_pack(**kwargs):
    return dict(kwargs)

class TestControlPlaneSummaryPack(unittest.TestCase):
    def setUp(self):
        self.event_control_summary_pack = make_pack(
            ready_events=['E1'],
            partial_events=['E2'],
            blocked_events=['E3'],
            event_count=3
        )
        self.event_dashboard_pack = make_pack(priority_queue=['E1', 'E2'])
        self.portfolio_summary_pack = make_pack(portfolio_status='ready')
        self.portfolio_dashboard_pack = make_pack(dashboard_cards=['C1', 'C2'])
        self.portfolio_control_summary_pack = make_pack(escalation_queue=['E2', 'E3'])
        self.portfolio_governance_pack = make_pack(portfolio_governance_status='governed')
        self.portfolio_resolution_decision_pack = make_pack(portfolio_resolution_decision_status='ready')

    def test_composed_summary(self):
        out = control_plane_summary_pack(
            self.event_control_summary_pack,
            self.event_dashboard_pack,
            self.portfolio_summary_pack,
            self.portfolio_dashboard_pack,
            self.portfolio_control_summary_pack,
            self.portfolio_governance_pack,
            self.portfolio_resolution_decision_pack
        )
        self.assertEqual(out['control_plane_status'], 'ready')
        self.assertEqual(out['event_count'], 3)
        self.assertEqual(out['portfolio_status'], 'ready')
        self.assertEqual(out['ready_events'], ['E1'])
        self.assertEqual(out['partial_events'], ['E2'])
        self.assertEqual(out['blocked_events'], ['E3'])
        self.assertEqual(out['priority_queue'], ['E1', 'E2'])
        self.assertEqual(out['escalation_queue'], ['E2', 'E3'])
        self.assertEqual(out['dashboard_cards'], ['C1', 'C2'])
        self.assertIn('control_plane_summary', out)
        summary = out['control_plane_summary']
        self.assertEqual(summary['portfolio_status'], 'ready')
        self.assertEqual(summary['portfolio_resolution_decision'], 'ready')
        self.assertEqual(summary['portfolio_governance'], 'governed')

if __name__ == '__main__':
    unittest.main()
