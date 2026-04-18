"""
test_portfolio_action_queue_pack.py

Tests for portfolio_action_queue_pack workflow.
"""
import unittest
from workflows.portfolio_action_queue_pack import portfolio_action_queue_pack

class TestPortfolioActionQueuePack(unittest.TestCase):
    def setUp(self):
        self.portfolio_dashboard = {
            'portfolio_dashboard_status': 'partial',
            'total_events': 3,
            'ready_events': 1,
            'partial_events': 1,
            'blocked_events': 1,
            'dashboard_cards': [
                {
                    'event_name': 'EventA',
                    'event_status': 'ready',
                    'total_bouts': 3,
                    'publish_ready_count': 3,
                    'review_required_count': 0,
                    'manual_intervention_count': 0,
                    'blocked_count': 0,
                    'priority': 1,
                    'notes': 'All bouts ready.',
                    'source_summary': {}
                },
                {
                    'event_name': 'EventB',
                    'event_status': 'partial',
                    'total_bouts': 2,
                    'publish_ready_count': 1,
                    'review_required_count': 1,
                    'manual_intervention_count': 0,
                    'blocked_count': 0,
                    'priority': 2,
                    'notes': 'One bout needs review.',
                    'source_summary': {}
                },
                {
                    'event_name': 'EventC',
                    'event_status': 'blocked',
                    'total_bouts': 2,
                    'publish_ready_count': 0,
                    'review_required_count': 0,
                    'manual_intervention_count': 1,
                    'blocked_count': 1,
                    'priority': 3,
                    'notes': 'Manual intervention required.',
                    'source_summary': {}
                }
            ],
            'priority_queue': [
                {'event_name': 'EventA', 'event_status': 'ready', 'priority': 1, 'reason': 'Ready for publication'},
                {'event_name': 'EventB', 'event_status': 'partial', 'priority': 2, 'reason': 'Partial event needs review'},
                {'event_name': 'EventC', 'event_status': 'blocked', 'priority': 3, 'reason': 'Blocked event requires intervention'}
            ],
            'blocked_event_names': ['EventC'],
            'portfolio_dashboard_summary': {}
        }

    def test_action_queue_partial(self):
        out = portfolio_action_queue_pack(self.portfolio_dashboard)
        self.assertEqual(out['portfolio_action_queue_status'], 'partial')
        self.assertEqual(out['total_events'], 3)
        self.assertEqual(len(out['queued_event_actions']), 2)
        self.assertEqual(len(out['blocked_event_actions']), 1)
        self.assertEqual(out['ready_event_names'], ['EventA'])
        self.assertEqual(out['blocked_event_names'], ['EventC'])
        self.assertEqual(len(out['priority_queue']), 3)
        self.assertEqual(len(out['blocker_summary']), 1)
        self.assertIn('portfolio_action_queue_summary', out)
        # Check action structure
        action = out['queued_event_actions'][0]
        self.assertIn('queue_action', action)
        self.assertIn('queue_reason', action)
        self.assertIn('dashboard_snapshot', action)
        blocked = out['blocked_event_actions'][0]
        self.assertIn('blocker_reason', blocked)
        self.assertIn('dashboard_snapshot', blocked)

    def test_action_queue_ready(self):
        dashboard = dict(self.portfolio_dashboard)
        dashboard['dashboard_cards'] = [
            {
                'event_name': 'EventA',
                'event_status': 'ready',
                'total_bouts': 3,
                'publish_ready_count': 3,
                'review_required_count': 0,
                'manual_intervention_count': 0,
                'blocked_count': 0,
                'priority': 1,
                'notes': 'All bouts ready.',
                'source_summary': {}
            },
            {
                'event_name': 'EventD',
                'event_status': 'ready',
                'total_bouts': 4,
                'publish_ready_count': 4,
                'review_required_count': 0,
                'manual_intervention_count': 0,
                'blocked_count': 0,
                'priority': 2,
                'notes': 'All bouts ready.',
                'source_summary': {}
            }
        ]
        dashboard['total_events'] = 2
        dashboard['ready_events'] = 2
        dashboard['partial_events'] = 0
        dashboard['blocked_events'] = 0
        dashboard['blocked_event_names'] = []
        out = portfolio_action_queue_pack(dashboard)
        self.assertEqual(out['portfolio_action_queue_status'], 'ready')
        self.assertEqual(len(out['queued_event_actions']), 2)
        self.assertEqual(len(out['blocked_event_actions']), 0)
        self.assertEqual(out['blocked_event_names'], [])

    def test_action_queue_blocked(self):
        dashboard = dict(self.portfolio_dashboard)
        dashboard['dashboard_cards'] = [
            {
                'event_name': 'EventC',
                'event_status': 'blocked',
                'total_bouts': 2,
                'publish_ready_count': 0,
                'review_required_count': 0,
                'manual_intervention_count': 1,
                'blocked_count': 1,
                'priority': 3,
                'notes': 'Manual intervention required.',
                'source_summary': {}
            },
            {
                'event_name': 'EventE',
                'event_status': 'blocked',
                'total_bouts': 1,
                'publish_ready_count': 0,
                'review_required_count': 0,
                'manual_intervention_count': 1,
                'blocked_count': 1,
                'priority': 2,
                'notes': 'Manual intervention required.',
                'source_summary': {}
            }
        ]
        dashboard['total_events'] = 2
        dashboard['ready_events'] = 0
        dashboard['partial_events'] = 0
        dashboard['blocked_events'] = 2
        dashboard['blocked_event_names'] = ['EventC', 'EventE']
        out = portfolio_action_queue_pack(dashboard)
        self.assertEqual(out['portfolio_action_queue_status'], 'blocked')
        self.assertEqual(len(out['queued_event_actions']), 0)
        self.assertEqual(len(out['blocked_event_actions']), 2)
        self.assertEqual(set(out['blocked_event_names']), {'EventC', 'EventE'})
        self.assertEqual(len(out['blocker_summary']), 2)

    def test_empty(self):
        dashboard = {
            'portfolio_dashboard_status': 'partial',
            'total_events': 0,
            'ready_events': 0,
            'partial_events': 0,
            'blocked_events': 0,
            'dashboard_cards': [],
            'priority_queue': [],
            'blocked_event_names': [],
            'portfolio_dashboard_summary': {}
        }
        out = portfolio_action_queue_pack(dashboard)
        self.assertEqual(out['portfolio_action_queue_status'], 'blocked')
        self.assertEqual(out['total_events'], 0)
        self.assertEqual(out['queued_event_actions'], [])
        self.assertEqual(out['blocked_event_actions'], [])
        self.assertEqual(out['blocker_summary'], [])
        self.assertIn('portfolio_action_queue_summary', out)

if __name__ == '__main__':
    unittest.main()
