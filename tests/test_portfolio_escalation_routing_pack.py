"""
test_portfolio_escalation_routing_pack.py

Tests for portfolio_escalation_routing_pack workflow.
"""
import unittest
from workflows.portfolio_escalation_routing_pack import portfolio_escalation_routing_pack

class TestPortfolioEscalationRoutingPack(unittest.TestCase):
    def setUp(self):
        self.portfolio_governance = {
            'portfolio_governance_status': 'partial',
            'total_events': 3,
            'governance_ready_events': ['EventA'],
            'blocked_governance_events': ['EventC'],
            'ready_event_names': ['EventA'],
            'blocked_event_names': ['EventC'],
            'escalation_flags': [
                {'event_name': 'EventB', 'escalation_level': 'operator_review'},
                {'event_name': 'EventC', 'escalation_level': 'manual_intervention'}
            ],
            'governance_cards': [
                {
                    'event_name': 'EventA',
                    'event_status': 'ready',
                    'priority': 1,
                    'governance_action': 'proceed_portfolio_event',
                    'governance_reason': 'Event ready for portfolio proceed',
                    'escalation_level': 'none',
                    'next_action': 'proceed_event',
                    'next_reason': 'Event completed and ready for next phase',
                    'control_snapshot': {}
                },
                {
                    'event_name': 'EventB',
                    'event_status': 'partial',
                    'priority': 2,
                    'governance_action': 'review_portfolio_event',
                    'governance_reason': 'Event requires operator review',
                    'escalation_level': 'operator_review',
                    'next_action': 'review_event',
                    'next_reason': 'Event completed with partial issues',
                    'control_snapshot': {}
                },
                {
                    'event_name': 'EventC',
                    'event_status': 'blocked',
                    'priority': 3,
                    'governance_action': 'escalate_portfolio_event',
                    'governance_reason': 'Event requires manual intervention',
                    'escalation_level': 'manual_intervention',
                    'next_action': 'hold_event',
                    'next_reason': 'Event completed but blocked',
                    'control_snapshot': {}
                }
            ],
            'blocker_summary': [
                {'event_name': 'EventC', 'reason': 'Manual intervention required', 'priority': 3}
            ],
            'portfolio_governance_summary': {}
        }

    def test_routing_partial(self):
        # Partial: some routed, some blocked (regardless of route_target)
        gov = dict(self.portfolio_governance)
        gov['governance_cards'] = [
            {
                'event_name': 'EventA',
                'event_status': 'ready',
                'priority': 1,
                'governance_action': 'proceed_portfolio_event',
                'governance_reason': 'Event ready for portfolio proceed',
                'escalation_level': 'none',
                'next_action': 'proceed_event',
                'next_reason': 'Event completed and ready for next phase',
                'control_snapshot': {}
            },
            {
                'event_name': 'EventB',
                'event_status': 'ready',
                'priority': 2,
                'governance_action': 'review_portfolio_event',
                'governance_reason': 'Event requires operator review',
                'escalation_level': 'operator_review',
                'next_action': 'review_event',
                'next_reason': 'Event completed with partial issues',
                'control_snapshot': {}
            }
        ]
        gov['total_events'] = 3
        gov['ready_event_names'] = ['EventA', 'EventB']
        gov['blocked_event_names'] = ['EventC']
        out = portfolio_escalation_routing_pack(gov)
        self.assertEqual(out['portfolio_escalation_routing_status'], 'partial')
        self.assertEqual(out['total_events'], 3)
        self.assertEqual(len(out['routed_events']), 2)
        self.assertEqual(len(out['route_targets']), 2)
        self.assertIn('portfolio_escalation_routing_summary', out)
        routed = out['routed_events'][0]
        self.assertIn('route_target', routed)
        self.assertIn('route_reason', routed)
        self.assertIn('governance_snapshot', routed)

    def test_routing_ready(self):
        gov = dict(self.portfolio_governance)
        gov['governance_cards'] = [
            {
                'event_name': 'EventA',
                'event_status': 'ready',
                'priority': 1,
                'governance_action': 'proceed_portfolio_event',
                'governance_reason': 'Event ready for portfolio proceed',
                'escalation_level': 'none',
                'next_action': 'proceed_event',
                'next_reason': 'Event completed and ready for next phase',
                'control_snapshot': {}
            },
            {
                'event_name': 'EventD',
                'event_status': 'ready',
                'priority': 2,
                'governance_action': 'proceed_portfolio_event',
                'governance_reason': 'Event ready for portfolio proceed',
                'escalation_level': 'none',
                'next_action': 'proceed_event',
                'next_reason': 'Event completed and ready for next phase',
                'control_snapshot': {}
            }
        ]
        gov['total_events'] = 2
        gov['ready_event_names'] = ['EventA', 'EventD']
        gov['blocked_event_names'] = []
        out = portfolio_escalation_routing_pack(gov)
        self.assertEqual(out['portfolio_escalation_routing_status'], 'ready')
        self.assertEqual(len(out['routed_events']), 2)
        self.assertEqual(len(out['route_targets']), 2)
        self.assertEqual(out['blocked_event_names'], [])

    def test_routing_blocked(self):
        gov = dict(self.portfolio_governance)
        gov['governance_cards'] = [
            {
                'event_name': 'EventC',
                'event_status': 'blocked',
                'priority': 3,
                'governance_action': 'escalate_portfolio_event',
                'governance_reason': 'Event requires manual intervention',
                'escalation_level': 'manual_intervention',
                'next_action': 'hold_event',
                'next_reason': 'Event completed but blocked',
                'control_snapshot': {}
            },
            {
                'event_name': 'EventE',
                'event_status': 'blocked',
                'priority': 2,
                'governance_action': 'escalate_portfolio_event',
                'governance_reason': 'Event requires manual intervention',
                'escalation_level': 'manual_intervention',
                'next_action': 'hold_event',
                'next_reason': 'Event completed but blocked',
                'control_snapshot': {}
            }
        ]
        gov['total_events'] = 2
        gov['ready_event_names'] = []
        gov['blocked_event_names'] = ['EventC', 'EventE']
        out = portfolio_escalation_routing_pack(gov)
        self.assertEqual(out['portfolio_escalation_routing_status'], 'ready')
        self.assertEqual(len(out['routed_events']), 2)
        self.assertEqual(len(out['route_targets']), 2)
        self.assertEqual(set(out['blocked_event_names']), {'EventC', 'EventE'})

    def test_empty(self):
        gov = {
            'portfolio_governance_status': 'blocked',
            'total_events': 0,
            'governance_ready_events': [],
            'blocked_governance_events': [],
            'ready_event_names': [],
            'blocked_event_names': [],
            'escalation_flags': [],
            'governance_cards': [],
            'blocker_summary': [],
            'portfolio_governance_summary': {}
        }
        out = portfolio_escalation_routing_pack(gov)
        self.assertEqual(out['portfolio_escalation_routing_status'], 'blocked')
        self.assertEqual(out['total_events'], 0)
        self.assertEqual(out['routed_events'], [])
        self.assertEqual(out['route_targets'], [])
        self.assertEqual(out['blocker_summary'], [])
        self.assertIn('portfolio_escalation_routing_summary', out)

if __name__ == '__main__':
    unittest.main()
