import unittest
from workflows.portfolio_resolution_decision_pack import portfolio_resolution_decision_pack

class TestPortfolioResolutionDecisionPack(unittest.TestCase):
    def setUp(self):
        self.routed_event = {
            'event_name': 'EventA',
            'event_status': 'ready',
            'priority': 1,
            'governance_action': 'proceed_portfolio_event',
            'route_target': 'portfolio_proceed_path',
            'escalation_level': 'none',
        }
        self.blocked_event = {
            'event_name': 'EventB',
            'event_status': 'blocked',
            'priority': 2,
            'blocker_reason': 'Manual block',
        }
        self.base_input = {
            'portfolio_escalation_routing_status': 'partial',
            'total_events': 2,
            'routed_events': [self.routed_event],
            'blocked_routes': [self.blocked_event],
            'ready_event_names': ['EventA'],
            'blocked_event_names': ['EventB'],
            'route_targets': ['portfolio_proceed_path'],
            'blocker_summary': {'EventB': 'Manual block'},
            'portfolio_escalation_routing_summary': {'routed': 1, 'blocked': 1}
        }

    def test_ready_status(self):
        inp = dict(self.base_input)
        inp['routed_events'] = [self.routed_event]
        inp['blocked_routes'] = []
        inp['portfolio_escalation_routing_status'] = 'ready'
        out = portfolio_resolution_decision_pack(inp)
        self.assertEqual(out['portfolio_resolution_decision_status'], 'ready')
        self.assertEqual(len(out['resolved_events']), 1)
        self.assertEqual(len(out['blocked_resolutions']), 0)
        self.assertIn('resolution_action', out['resolved_events'][0])
        self.assertEqual(out['resolved_events'][0]['resolution_action'], 'proceed')

    def test_partial_status(self):
        inp = dict(self.base_input)
        out = portfolio_resolution_decision_pack(inp)
        self.assertEqual(out['portfolio_resolution_decision_status'], 'partial')
        self.assertEqual(len(out['resolved_events']), 1)
        self.assertEqual(len(out['blocked_resolutions']), 1)
        self.assertEqual(out['resolved_events'][0]['resolution_action'], 'proceed')
        self.assertEqual(out['blocked_resolutions'][0]['blocker_reason'], 'Manual block')

    def test_blocked_status(self):
        inp = dict(self.base_input)
        inp['routed_events'] = []
        inp['blocked_routes'] = [self.blocked_event]
        inp['portfolio_escalation_routing_status'] = 'blocked'
        out = portfolio_resolution_decision_pack(inp)
        self.assertEqual(out['portfolio_resolution_decision_status'], 'blocked')
        self.assertEqual(len(out['resolved_events']), 0)
        self.assertEqual(len(out['blocked_resolutions']), 1)
        self.assertEqual(out['blocked_resolutions'][0]['blocker_reason'], 'Manual block')

    def test_resolution_action_mapping(self):
        # review
        routed = dict(self.routed_event)
        routed['route_target'] = 'portfolio_operator_review'
        inp = dict(self.base_input)
        inp['routed_events'] = [routed]
        inp['blocked_routes'] = []
        inp['portfolio_escalation_routing_status'] = 'ready'
        out = portfolio_resolution_decision_pack(inp)
        self.assertEqual(out['resolved_events'][0]['resolution_action'], 'review')
        # manual_intervention
        routed['route_target'] = 'portfolio_manual_intervention'
        inp['routed_events'] = [routed]
        out = portfolio_resolution_decision_pack(inp)
        self.assertEqual(out['resolved_events'][0]['resolution_action'], 'manual_intervention')

if __name__ == '__main__':
    unittest.main()
