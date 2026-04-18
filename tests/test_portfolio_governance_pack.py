"""
test_portfolio_governance_pack.py

Tests for portfolio_governance_pack workflow.
"""
import unittest
from workflows.portfolio_governance_pack import portfolio_governance_pack

class TestPortfolioGovernancePack(unittest.TestCase):
    def setUp(self):
        self.portfolio_control = {
            'portfolio_control_status': 'partial',
            'total_events': 3,
            'ready_events': 1,
            'partial_events': 1,
            'blocked_events': 1,
            'ready_event_names': ['EventA'],
            'partial_event_names': ['EventB'],
            'blocked_event_names': ['EventC'],
            'priority_queue': [
                {'event_name': 'EventA', 'event_status': 'ready', 'priority': 1, 'reason': 'Event completed and ready for next phase'},
                {'event_name': 'EventB', 'event_status': 'partial', 'priority': 2, 'reason': 'Event completed with partial issues'},
                {'event_name': 'EventC', 'event_status': 'blocked', 'priority': 3, 'reason': 'Event completed but blocked'}
            ],
            'control_cards': [
                {
                    'event_name': 'EventA',
                    'event_status': 'ready',
                    'priority': 1,
                    'next_action': 'proceed_event',
                    'next_reason': 'Event completed and ready for next phase',
                    'publish_ready_count': 3,
                    'review_required_count': 0,
                    'manual_intervention_count': 0,
                    'blocked_count': 0,
                    'outcome_snapshot': {}
                },
                {
                    'event_name': 'EventB',
                    'event_status': 'partial',
                    'priority': 2,
                    'next_action': 'review_event',
                    'next_reason': 'Event completed with partial issues',
                    'publish_ready_count': 1,
                    'review_required_count': 1,
                    'manual_intervention_count': 0,
                    'blocked_count': 0,
                    'outcome_snapshot': {}
                },
                {
                    'event_name': 'EventC',
                    'event_status': 'blocked',
                    'priority': 3,
                    'next_action': 'hold_event',
                    'next_reason': 'Event completed but blocked',
                    'publish_ready_count': 0,
                    'review_required_count': 0,
                    'manual_intervention_count': 0,
                    'blocked_count': 0,
                    'outcome_snapshot': {}
                }
            ],
            'blocker_summary': [
                {'event_name': 'EventC', 'reason': 'Manual intervention required', 'priority': 3}
            ],
            'portfolio_control_summary': {}
        }

    def test_governance_partial(self):
        out = portfolio_governance_pack(self.portfolio_control)
        self.assertEqual(out['portfolio_governance_status'], 'partial')
        self.assertEqual(out['total_events'], 3)
        self.assertEqual(len(out['governance_cards']), 3)
        self.assertEqual(len(out['escalation_flags']), 2)
        self.assertIn('portfolio_governance_summary', out)
        # Check governance card structure
        card = out['governance_cards'][0]
        self.assertIn('governance_action', card)
        self.assertIn('governance_reason', card)
        self.assertIn('escalation_level', card)
        self.assertIn('next_action', card)
        self.assertIn('next_reason', card)
        self.assertIn('control_snapshot', card)
        blocked = out['governance_cards'][-1]
        self.assertIn('governance_action', blocked)
        self.assertIn('governance_reason', blocked)
        self.assertIn('escalation_level', blocked)
        self.assertIn('control_snapshot', blocked)

    def test_governance_ready(self):
        control = dict(self.portfolio_control)
        control['control_cards'] = [
            {
                'event_name': 'EventA',
                'event_status': 'ready',
                'priority': 1,
                'next_action': 'proceed_event',
                'next_reason': 'Event completed and ready for next phase',
                'publish_ready_count': 3,
                'review_required_count': 0,
                'manual_intervention_count': 0,
                'blocked_count': 0,
                'outcome_snapshot': {}
            },
            {
                'event_name': 'EventD',
                'event_status': 'ready',
                'priority': 2,
                'next_action': 'proceed_event',
                'next_reason': 'Event completed and ready for next phase',
                'publish_ready_count': 4,
                'review_required_count': 0,
                'manual_intervention_count': 0,
                'blocked_count': 0,
                'outcome_snapshot': {}
            }
        ]
        control['total_events'] = 2
        control['ready_event_names'] = ['EventA', 'EventD']
        control['blocked_event_names'] = []
        out = portfolio_governance_pack(control)
        self.assertEqual(out['portfolio_governance_status'], 'ready')
        self.assertEqual(len(out['governance_cards']), 2)
        self.assertEqual(len(out['escalation_flags']), 0)
        self.assertEqual(out['blocked_event_names'], [])

    def test_governance_blocked(self):
        control = dict(self.portfolio_control)
        control['control_cards'] = [
            {
                'event_name': 'EventC',
                'event_status': 'blocked',
                'priority': 3,
                'next_action': 'hold_event',
                'next_reason': 'Event completed but blocked',
                'publish_ready_count': 0,
                'review_required_count': 0,
                'manual_intervention_count': 0,
                'blocked_count': 0,
                'outcome_snapshot': {}
            },
            {
                'event_name': 'EventE',
                'event_status': 'blocked',
                'priority': 2,
                'next_action': 'hold_event',
                'next_reason': 'Event completed but blocked',
                'publish_ready_count': 0,
                'review_required_count': 0,
                'manual_intervention_count': 0,
                'blocked_count': 0,
                'outcome_snapshot': {}
            }
        ]
        control['total_events'] = 2
        control['ready_event_names'] = []
        control['blocked_event_names'] = ['EventC', 'EventE']
        out = portfolio_governance_pack(control)
        self.assertEqual(out['portfolio_governance_status'], 'blocked')
        self.assertEqual(len(out['governance_cards']), 2)
        self.assertEqual(len(out['escalation_flags']), 2)
        self.assertEqual(set(out['blocked_event_names']), {'EventC', 'EventE'})

    def test_empty(self):
        control = {
            'portfolio_control_status': 'blocked',
            'total_events': 0,
            'ready_events': 0,
            'partial_events': 0,
            'blocked_events': 0,
            'ready_event_names': [],
            'partial_event_names': [],
            'blocked_event_names': [],
            'priority_queue': [],
            'control_cards': [],
            'blocker_summary': [],
            'portfolio_control_summary': {}
        }
        out = portfolio_governance_pack(control)
        self.assertEqual(out['portfolio_governance_status'], 'blocked')
        self.assertEqual(out['total_events'], 0)
        self.assertEqual(out['governance_cards'], [])
        self.assertEqual(out['escalation_flags'], [])
        self.assertEqual(out['blocker_summary'], [])
        self.assertIn('portfolio_governance_summary', out)

if __name__ == '__main__':
    unittest.main()
