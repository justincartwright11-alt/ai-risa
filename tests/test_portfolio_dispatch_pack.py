"""
test_portfolio_dispatch_pack.py

Tests for portfolio_dispatch_pack workflow.
"""
import unittest
from workflows.portfolio_dispatch_pack import portfolio_dispatch_pack

class TestPortfolioDispatchPack(unittest.TestCase):
    def setUp(self):
        self.portfolio_action_queue = {
            'portfolio_action_queue_status': 'partial',
            'total_events': 3,
            'queued_event_actions': [
                {
                    'event_name': 'EventA',
                    'event_status': 'ready',
                    'priority': 1,
                    'queue_action': 'proceed_event',
                    'queue_reason': 'All bouts ready for publication',
                    'publish_ready_count': 3,
                    'review_required_count': 0,
                    'manual_intervention_count': 0,
                    'blocked_count': 0,
                    'dashboard_snapshot': {}
                },
                {
                    'event_name': 'EventB',
                    'event_status': 'partial',
                    'priority': 2,
                    'queue_action': 'review_event',
                    'queue_reason': 'Some bouts require review or intervention',
                    'publish_ready_count': 1,
                    'review_required_count': 1,
                    'manual_intervention_count': 0,
                    'blocked_count': 0,
                    'dashboard_snapshot': {}
                }
            ],
            'blocked_event_actions': [
                {
                    'event_name': 'EventC',
                    'event_status': 'blocked',
                    'priority': 3,
                    'blocker_reason': 'Manual intervention required',
                    'dashboard_snapshot': {}
                }
            ],
            'ready_event_names': ['EventA'],
            'blocked_event_names': ['EventC'],
            'priority_queue': [
                {'event_name': 'EventA', 'event_status': 'ready', 'priority': 1, 'reason': 'Ready for publication'},
                {'event_name': 'EventB', 'event_status': 'partial', 'priority': 2, 'reason': 'Partial event needs review'},
                {'event_name': 'EventC', 'event_status': 'blocked', 'priority': 3, 'reason': 'Blocked event requires intervention'}
            ],
            'blocker_summary': [
                {'event_name': 'EventC', 'reason': 'Manual intervention required', 'priority': 3}
            ],
            'portfolio_action_queue_summary': {}
        }

    def test_dispatch_partial(self):
        out = portfolio_dispatch_pack(self.portfolio_action_queue)
        self.assertEqual(out['portfolio_dispatch_status'], 'partial')
        self.assertEqual(out['total_events'], 3)
        self.assertEqual(len(out['dispatch_ready_events']), 2)
        self.assertEqual(len(out['blocked_dispatches']), 1)
        self.assertEqual(out['ready_event_names'], ['EventA', 'EventB'])
        self.assertEqual(out['blocked_event_names'], ['EventC'])
        self.assertEqual(len(out['dispatch_batches']), 2)
        self.assertEqual(len(out['blocker_summary']), 1)
        self.assertIn('portfolio_dispatch_summary', out)
        # Check dispatch structure
        dispatch = out['dispatch_ready_events'][0]
        self.assertIn('dispatch_batch', dispatch)
        self.assertIn('dispatch_reason', dispatch)
        self.assertIn('queue_snapshot', dispatch)
        blocked = out['blocked_dispatches'][0]
        self.assertIn('blocker_reason', blocked)
        self.assertIn('queue_snapshot', blocked)

    def test_dispatch_ready(self):
        queue = dict(self.portfolio_action_queue)
        queue['queued_event_actions'] = [
            {
                'event_name': 'EventA',
                'event_status': 'ready',
                'priority': 1,
                'queue_action': 'proceed_event',
                'queue_reason': 'All bouts ready for publication',
                'publish_ready_count': 3,
                'review_required_count': 0,
                'manual_intervention_count': 0,
                'blocked_count': 0,
                'dashboard_snapshot': {}
            },
            {
                'event_name': 'EventD',
                'event_status': 'ready',
                'priority': 2,
                'queue_action': 'proceed_event',
                'queue_reason': 'All bouts ready for publication',
                'publish_ready_count': 4,
                'review_required_count': 0,
                'manual_intervention_count': 0,
                'blocked_count': 0,
                'dashboard_snapshot': {}
            }
        ]
        queue['blocked_event_actions'] = []
        queue['total_events'] = 2
        queue['ready_event_names'] = ['EventA', 'EventD']
        queue['blocked_event_names'] = []
        out = portfolio_dispatch_pack(queue)
        self.assertEqual(out['portfolio_dispatch_status'], 'ready')
        self.assertEqual(len(out['dispatch_ready_events']), 2)
        self.assertEqual(len(out['blocked_dispatches']), 0)
        self.assertEqual(out['blocked_event_names'], [])

    def test_dispatch_blocked(self):
        queue = dict(self.portfolio_action_queue)
        queue['queued_event_actions'] = []
        queue['blocked_event_actions'] = [
            {
                'event_name': 'EventC',
                'event_status': 'blocked',
                'priority': 3,
                'blocker_reason': 'Manual intervention required',
                'dashboard_snapshot': {}
            },
            {
                'event_name': 'EventE',
                'event_status': 'blocked',
                'priority': 2,
                'blocker_reason': 'Manual intervention required',
                'dashboard_snapshot': {}
            }
        ]
        queue['total_events'] = 2
        queue['ready_event_names'] = []
        queue['blocked_event_names'] = ['EventC', 'EventE']
        out = portfolio_dispatch_pack(queue)
        self.assertEqual(out['portfolio_dispatch_status'], 'blocked')
        self.assertEqual(len(out['dispatch_ready_events']), 0)
        self.assertEqual(len(out['blocked_dispatches']), 2)
        self.assertEqual(set(out['blocked_event_names']), {'EventC', 'EventE'})
        self.assertEqual(len(out['blocker_summary']), 1)

    def test_empty(self):
        queue = {
            'portfolio_action_queue_status': 'blocked',
            'total_events': 0,
            'queued_event_actions': [],
            'blocked_event_actions': [],
            'ready_event_names': [],
            'blocked_event_names': [],
            'priority_queue': [],
            'blocker_summary': [],
            'portfolio_action_queue_summary': {}
        }
        out = portfolio_dispatch_pack(queue)
        self.assertEqual(out['portfolio_dispatch_status'], 'blocked')
        self.assertEqual(out['total_events'], 0)
        self.assertEqual(out['dispatch_ready_events'], [])
        self.assertEqual(out['blocked_dispatches'], [])
        self.assertEqual(out['blocker_summary'], [])
        self.assertIn('portfolio_dispatch_summary', out)

if __name__ == '__main__':
    unittest.main()
