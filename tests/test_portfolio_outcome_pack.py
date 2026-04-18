"""
test_portfolio_outcome_pack.py

Tests for portfolio_outcome_pack workflow.
"""
import unittest
from workflows.portfolio_outcome_pack import portfolio_outcome_pack

class TestPortfolioOutcomePack(unittest.TestCase):
    def setUp(self):
        self.portfolio_execution = {
            'portfolio_execution_status': 'partial',
            'total_events': 3,
            'execution_ready_events': [
                {
                    'event_name': 'EventA',
                    'event_status': 'ready',
                    'priority': 1,
                    'queue_action': 'proceed_event',
                    'queue_reason': 'All bouts ready for publication',
                    'dispatch_batch': 'dispatch_publish_batch',
                    'dispatch_reason': 'Ready for publication dispatch',
                    'execution_batch': 'execute_publish_batch',
                    'execution_reason': 'Ready for publication execution',
                    'publish_ready_count': 3,
                    'review_required_count': 0,
                    'manual_intervention_count': 0,
                    'blocked_count': 0,
                    'dispatch_snapshot': {}
                },
                {
                    'event_name': 'EventB',
                    'event_status': 'partial',
                    'priority': 2,
                    'queue_action': 'review_event',
                    'queue_reason': 'Some bouts require review or intervention',
                    'dispatch_batch': 'dispatch_review_batch',
                    'dispatch_reason': 'Requires review before dispatch',
                    'execution_batch': 'execute_review_batch',
                    'execution_reason': 'Requires review before execution',
                    'publish_ready_count': 1,
                    'review_required_count': 1,
                    'manual_intervention_count': 0,
                    'blocked_count': 0,
                    'dispatch_snapshot': {}
                }
            ],
            'blocked_executions': [
                {
                    'event_name': 'EventC',
                    'event_status': 'blocked',
                    'priority': 3,
                    'blocker_reason': 'Manual intervention required',
                    'dispatch_snapshot': {}
                }
            ],
            'ready_event_names': ['EventA', 'EventB'],
            'blocked_event_names': ['EventC'],
            'execution_batches': ['execute_publish_batch', 'execute_review_batch'],
            'blocker_summary': [
                {'event_name': 'EventC', 'reason': 'Manual intervention required', 'priority': 3}
            ],
            'portfolio_execution_summary': {}
        }

    def test_outcome_partial(self):
        out = portfolio_outcome_pack(self.portfolio_execution)
        self.assertEqual(out['portfolio_outcome_status'], 'partial')
        self.assertEqual(out['total_events'], 3)
        self.assertEqual(len(out['completed_events']), 2)
        self.assertEqual(len(out['blocked_outcomes']), 1)
        self.assertEqual(out['ready_event_names'], ['EventA', 'EventB'])
        self.assertEqual(out['blocked_event_names'], ['EventC'])
        self.assertEqual(len(out['outcome_batches']), 2)
        self.assertEqual(len(out['blocker_summary']), 1)
        self.assertIn('portfolio_outcome_summary', out)
        # Check outcome structure
        outcome = out['completed_events'][0]
        self.assertIn('outcome_batch', outcome)
        self.assertIn('outcome_reason', outcome)
        self.assertIn('execution_snapshot', outcome)
        blocked = out['blocked_outcomes'][0]
        self.assertIn('blocker_reason', blocked)
        self.assertIn('execution_snapshot', blocked)

    def test_outcome_ready(self):
        execution = dict(self.portfolio_execution)
        execution['execution_ready_events'] = [
            {
                'event_name': 'EventA',
                'event_status': 'ready',
                'priority': 1,
                'queue_action': 'proceed_event',
                'queue_reason': 'All bouts ready for publication',
                'dispatch_batch': 'dispatch_publish_batch',
                'dispatch_reason': 'Ready for publication dispatch',
                'execution_batch': 'execute_publish_batch',
                'execution_reason': 'Ready for publication execution',
                'publish_ready_count': 3,
                'review_required_count': 0,
                'manual_intervention_count': 0,
                'blocked_count': 0,
                'dispatch_snapshot': {}
            },
            {
                'event_name': 'EventD',
                'event_status': 'ready',
                'priority': 2,
                'queue_action': 'proceed_event',
                'queue_reason': 'All bouts ready for publication',
                'dispatch_batch': 'dispatch_publish_batch',
                'dispatch_reason': 'Ready for publication dispatch',
                'execution_batch': 'execute_publish_batch',
                'execution_reason': 'Ready for publication execution',
                'publish_ready_count': 4,
                'review_required_count': 0,
                'manual_intervention_count': 0,
                'blocked_count': 0,
                'dispatch_snapshot': {}
            }
        ]
        execution['blocked_executions'] = []
        execution['total_events'] = 2
        execution['ready_event_names'] = ['EventA', 'EventD']
        execution['blocked_event_names'] = []
        out = portfolio_outcome_pack(execution)
        self.assertEqual(out['portfolio_outcome_status'], 'ready')
        self.assertEqual(len(out['completed_events']), 2)
        self.assertEqual(len(out['blocked_outcomes']), 0)
        self.assertEqual(out['blocked_event_names'], [])

    def test_outcome_blocked(self):
        execution = dict(self.portfolio_execution)
        execution['execution_ready_events'] = []
        execution['blocked_executions'] = [
            {
                'event_name': 'EventC',
                'event_status': 'blocked',
                'priority': 3,
                'blocker_reason': 'Manual intervention required',
                'dispatch_snapshot': {}
            },
            {
                'event_name': 'EventE',
                'event_status': 'blocked',
                'priority': 2,
                'blocker_reason': 'Manual intervention required',
                'dispatch_snapshot': {}
            }
        ]
        execution['total_events'] = 2
        execution['ready_event_names'] = []
        execution['blocked_event_names'] = ['EventC', 'EventE']
        out = portfolio_outcome_pack(execution)
        self.assertEqual(out['portfolio_outcome_status'], 'blocked')
        self.assertEqual(len(out['completed_events']), 0)
        self.assertEqual(len(out['blocked_outcomes']), 2)
        self.assertEqual(set(out['blocked_event_names']), {'EventC', 'EventE'})
        self.assertEqual(len(out['blocker_summary']), 1)

    def test_empty(self):
        execution = {
            'portfolio_execution_status': 'blocked',
            'total_events': 0,
            'execution_ready_events': [],
            'blocked_executions': [],
            'ready_event_names': [],
            'blocked_event_names': [],
            'execution_batches': [],
            'blocker_summary': [],
            'portfolio_execution_summary': {}
        }
        out = portfolio_outcome_pack(execution)
        self.assertEqual(out['portfolio_outcome_status'], 'blocked')
        self.assertEqual(out['total_events'], 0)
        self.assertEqual(out['completed_events'], [])
        self.assertEqual(out['blocked_outcomes'], [])
        self.assertEqual(out['blocker_summary'], [])
        self.assertIn('portfolio_outcome_summary', out)

if __name__ == '__main__':
    unittest.main()
