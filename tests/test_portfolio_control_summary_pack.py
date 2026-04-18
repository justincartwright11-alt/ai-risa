"""
test_portfolio_control_summary_pack.py

Tests for portfolio_control_summary_pack workflow.
"""
import unittest
from workflows.portfolio_control_summary_pack import portfolio_control_summary_pack

class TestPortfolioControlSummaryPack(unittest.TestCase):
    def setUp(self):
        self.portfolio_outcome = {
            'portfolio_outcome_status': 'partial',
            'total_events': 3,
            'completed_events': [
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
                    'outcome_batch': 'complete_publish_batch',
                    'outcome_reason': 'Event completed and published',
                    'publish_ready_count': 3,
                    'review_required_count': 0,
                    'manual_intervention_count': 0,
                    'blocked_count': 0,
                    'execution_snapshot': {}
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
                    'outcome_batch': 'complete_review_batch',
                    'outcome_reason': 'Event completed after review',
                    'publish_ready_count': 1,
                    'review_required_count': 1,
                    'manual_intervention_count': 0,
                    'blocked_count': 0,
                    'execution_snapshot': {}
                }
            ],
            'blocked_outcomes': [
                {
                    'event_name': 'EventC',
                    'event_status': 'blocked',
                    'priority': 3,
                    'blocker_reason': 'Manual intervention required',
                    'execution_snapshot': {}
                }
            ],
            'ready_event_names': ['EventA'],
            'blocked_event_names': ['EventC'],
            'outcome_batches': ['complete_publish_batch', 'complete_review_batch'],
            'blocker_summary': [
                {'event_name': 'EventC', 'reason': 'Manual intervention required', 'priority': 3}
            ],
            'portfolio_outcome_summary': {}
        }

    def test_control_partial(self):
        out = portfolio_control_summary_pack(self.portfolio_outcome)
        self.assertEqual(out['portfolio_control_status'], 'partial')
        self.assertEqual(out['total_events'], 3)
        self.assertEqual(out['ready_events'], 1)
        self.assertEqual(out['partial_events'], 1)
        self.assertEqual(out['blocked_events'], 1)
        self.assertEqual(len(out['control_cards']), 3)
        self.assertEqual(len(out['priority_queue']), 3)
        self.assertEqual(out['ready_event_names'], ['EventA'])
        self.assertEqual(out['blocked_event_names'], ['EventC', 'EventC'])
        self.assertEqual(len(out['blocker_summary']), 1)
        self.assertIn('portfolio_control_summary', out)
        # Check control card structure
        card = out['control_cards'][0]
        self.assertIn('next_action', card)
        self.assertIn('next_reason', card)
        self.assertIn('outcome_snapshot', card)
        blocked = out['control_cards'][-1]
        self.assertIn('next_action', blocked)
        self.assertIn('next_reason', blocked)
        self.assertIn('outcome_snapshot', blocked)

    def test_control_ready(self):
        outcome = dict(self.portfolio_outcome)
        outcome['completed_events'] = [
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
                'outcome_batch': 'complete_publish_batch',
                'outcome_reason': 'Event completed and published',
                'publish_ready_count': 3,
                'review_required_count': 0,
                'manual_intervention_count': 0,
                'blocked_count': 0,
                'execution_snapshot': {}
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
                'outcome_batch': 'complete_publish_batch',
                'outcome_reason': 'Event completed and published',
                'publish_ready_count': 4,
                'review_required_count': 0,
                'manual_intervention_count': 0,
                'blocked_count': 0,
                'execution_snapshot': {}
            }
        ]
        outcome['blocked_outcomes'] = []
        outcome['total_events'] = 2
        outcome['ready_event_names'] = ['EventA', 'EventD']
        outcome['blocked_event_names'] = []
        out = portfolio_control_summary_pack(outcome)
        self.assertEqual(out['portfolio_control_status'], 'ready')
        self.assertEqual(out['ready_events'], 2)
        self.assertEqual(out['blocked_events'], 0)
        self.assertEqual(out['partial_events'], 0)
        self.assertEqual(out['blocked_event_names'], [])

    def test_control_blocked(self):
        outcome = dict(self.portfolio_outcome)
        outcome['completed_events'] = []
        outcome['blocked_outcomes'] = [
            {
                'event_name': 'EventC',
                'event_status': 'blocked',
                'priority': 3,
                'blocker_reason': 'Manual intervention required',
                'execution_snapshot': {}
            },
            {
                'event_name': 'EventE',
                'event_status': 'blocked',
                'priority': 2,
                'blocker_reason': 'Manual intervention required',
                'execution_snapshot': {}
            }
        ]
        outcome['total_events'] = 2
        outcome['ready_event_names'] = []
        outcome['blocked_event_names'] = ['EventC', 'EventE']
        out = portfolio_control_summary_pack(outcome)
        self.assertEqual(out['portfolio_control_status'], 'blocked')
        self.assertEqual(out['ready_events'], 0)
        self.assertEqual(out['blocked_events'], 2)
        self.assertEqual(out['partial_events'], 0)
        self.assertEqual(set(out['blocked_event_names']), {'EventC', 'EventE'})
        self.assertEqual(len(out['blocker_summary']), 1)

    def test_empty(self):
        outcome = {
            'portfolio_outcome_status': 'blocked',
            'total_events': 0,
            'completed_events': [],
            'blocked_outcomes': [],
            'ready_event_names': [],
            'blocked_event_names': [],
            'outcome_batches': [],
            'blocker_summary': [],
            'portfolio_outcome_summary': {}
        }
        out = portfolio_control_summary_pack(outcome)
        self.assertEqual(out['portfolio_control_status'], 'blocked')
        self.assertEqual(out['total_events'], 0)
        self.assertEqual(out['control_cards'], [])
        self.assertEqual(out['priority_queue'], [])
        self.assertEqual(out['blocker_summary'], [])
        self.assertIn('portfolio_control_summary', out)

if __name__ == '__main__':
    unittest.main()
