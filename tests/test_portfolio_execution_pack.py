"""
test_portfolio_execution_pack.py

Tests for portfolio_execution_pack workflow.
"""
import unittest
from workflows.portfolio_execution_pack import portfolio_execution_pack

class TestPortfolioExecutionPack(unittest.TestCase):
    def setUp(self):
        self.portfolio_dispatch = {
            'portfolio_dispatch_status': 'partial',
            'total_events': 3,
            'dispatch_ready_events': [
                {
                    'event_name': 'EventA',
                    'event_status': 'ready',
                    'priority': 1,
                    'queue_action': 'proceed_event',
                    'queue_reason': 'All bouts ready for publication',
                    'dispatch_batch': 'dispatch_publish_batch',
                    'dispatch_reason': 'Ready for publication dispatch',
                    'publish_ready_count': 3,
                    'review_required_count': 0,
                    'manual_intervention_count': 0,
                    'blocked_count': 0,
                    'queue_snapshot': {}
                },
                {
                    'event_name': 'EventB',
                    'event_status': 'partial',
                    'priority': 2,
                    'queue_action': 'review_event',
                    'queue_reason': 'Some bouts require review or intervention',
                    'dispatch_batch': 'dispatch_review_batch',
                    'dispatch_reason': 'Requires review before dispatch',
                    'publish_ready_count': 1,
                    'review_required_count': 1,
                    'manual_intervention_count': 0,
                    'blocked_count': 0,
                    'queue_snapshot': {}
                }
            ],
            'blocked_dispatches': [
                {
                    'event_name': 'EventC',
                    'event_status': 'blocked',
                    'priority': 3,
                    'blocker_reason': 'Manual intervention required',
                    'queue_snapshot': {}
                }
            ],
            'ready_event_names': ['EventA', 'EventB'],
            'blocked_event_names': ['EventC'],
            'dispatch_batches': ['dispatch_publish_batch', 'dispatch_review_batch'],
            'blocker_summary': [
                {'event_name': 'EventC', 'reason': 'Manual intervention required', 'priority': 3}
            ],
            'portfolio_dispatch_summary': {}
        }

    def test_execution_partial(self):
        out = portfolio_execution_pack(self.portfolio_dispatch)
        self.assertEqual(out['portfolio_execution_status'], 'partial')
        self.assertEqual(out['total_events'], 3)
        self.assertEqual(len(out['execution_ready_events']), 2)
        self.assertEqual(len(out['blocked_executions']), 1)
        self.assertEqual(out['ready_event_names'], ['EventA', 'EventB'])
        self.assertEqual(out['blocked_event_names'], ['EventC'])
        self.assertEqual(len(out['execution_batches']), 2)
        self.assertEqual(len(out['blocker_summary']), 1)
        self.assertIn('portfolio_execution_summary', out)
        # Check execution structure
        exe = out['execution_ready_events'][0]
        self.assertIn('execution_batch', exe)
        self.assertIn('execution_reason', exe)
        self.assertIn('dispatch_snapshot', exe)
        blocked = out['blocked_executions'][0]
        self.assertIn('blocker_reason', blocked)
        self.assertIn('dispatch_snapshot', blocked)

    def test_execution_ready(self):
        dispatch = dict(self.portfolio_dispatch)
        dispatch['dispatch_ready_events'] = [
            {
                'event_name': 'EventA',
                'event_status': 'ready',
                'priority': 1,
                'queue_action': 'proceed_event',
                'queue_reason': 'All bouts ready for publication',
                'dispatch_batch': 'dispatch_publish_batch',
                'dispatch_reason': 'Ready for publication dispatch',
                'publish_ready_count': 3,
                'review_required_count': 0,
                'manual_intervention_count': 0,
                'blocked_count': 0,
                'queue_snapshot': {}
            },
            {
                'event_name': 'EventD',
                'event_status': 'ready',
                'priority': 2,
                'queue_action': 'proceed_event',
                'queue_reason': 'All bouts ready for publication',
                'dispatch_batch': 'dispatch_publish_batch',
                'dispatch_reason': 'Ready for publication dispatch',
                'publish_ready_count': 4,
                'review_required_count': 0,
                'manual_intervention_count': 0,
                'blocked_count': 0,
                'queue_snapshot': {}
            }
        ]
        dispatch['blocked_dispatches'] = []
        dispatch['total_events'] = 2
        dispatch['ready_event_names'] = ['EventA', 'EventD']
        dispatch['blocked_event_names'] = []
        out = portfolio_execution_pack(dispatch)
        self.assertEqual(out['portfolio_execution_status'], 'ready')
        self.assertEqual(len(out['execution_ready_events']), 2)
        self.assertEqual(len(out['blocked_executions']), 0)
        self.assertEqual(out['blocked_event_names'], [])

    def test_execution_blocked(self):
        dispatch = dict(self.portfolio_dispatch)
        dispatch['dispatch_ready_events'] = []
        dispatch['blocked_dispatches'] = [
            {
                'event_name': 'EventC',
                'event_status': 'blocked',
                'priority': 3,
                'blocker_reason': 'Manual intervention required',
                'queue_snapshot': {}
            },
            {
                'event_name': 'EventE',
                'event_status': 'blocked',
                'priority': 2,
                'blocker_reason': 'Manual intervention required',
                'queue_snapshot': {}
            }
        ]
        dispatch['total_events'] = 2
        dispatch['ready_event_names'] = []
        dispatch['blocked_event_names'] = ['EventC', 'EventE']
        out = portfolio_execution_pack(dispatch)
        self.assertEqual(out['portfolio_execution_status'], 'blocked')
        self.assertEqual(len(out['execution_ready_events']), 0)
        self.assertEqual(len(out['blocked_executions']), 2)
        self.assertEqual(set(out['blocked_event_names']), {'EventC', 'EventE'})
        self.assertEqual(len(out['blocker_summary']), 1)

    def test_empty(self):
        dispatch = {
            'portfolio_dispatch_status': 'blocked',
            'total_events': 0,
            'dispatch_ready_events': [],
            'blocked_dispatches': [],
            'ready_event_names': [],
            'blocked_event_names': [],
            'dispatch_batches': [],
            'blocker_summary': [],
            'portfolio_dispatch_summary': {}
        }
        out = portfolio_execution_pack(dispatch)
        self.assertEqual(out['portfolio_execution_status'], 'blocked')
        self.assertEqual(out['total_events'], 0)
        self.assertEqual(out['execution_ready_events'], [])
        self.assertEqual(out['blocked_executions'], [])
        self.assertEqual(out['blocker_summary'], [])
        self.assertIn('portfolio_execution_summary', out)

if __name__ == '__main__':
    unittest.main()
