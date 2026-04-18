"""
test_portfolio_summary_pack.py

Tests for portfolio_summary_pack workflow.
"""
import unittest
from workflows.portfolio_summary_pack import portfolio_summary_pack

class TestPortfolioSummaryPack(unittest.TestCase):
    def setUp(self):
        self.ready_event = {
            'event_name': 'EventA',
            'event_status': 'ready',
            'total_bouts': 3,
            'publish_ready_count': 3,
            'review_required_count': 0,
            'manual_intervention_count': 0,
            'blocked_count': 0,
            'priority': 1,
            'notes': 'All bouts ready.'
        }
        self.partial_event = {
            'event_name': 'EventB',
            'event_status': 'partial',
            'total_bouts': 2,
            'publish_ready_count': 1,
            'review_required_count': 1,
            'manual_intervention_count': 0,
            'blocked_count': 0,
            'priority': 2,
            'notes': 'One bout needs review.'
        }
        self.blocked_event = {
            'event_name': 'EventC',
            'event_status': 'blocked',
            'total_bouts': 2,
            'publish_ready_count': 0,
            'review_required_count': 0,
            'manual_intervention_count': 1,
            'blocked_count': 1,
            'priority': 3,
            'notes': 'Manual intervention required.'
        }

    def test_all_ready(self):
        results = [self.ready_event, self.ready_event]
        out = portfolio_summary_pack(results)
        self.assertEqual(out['portfolio_status'], 'ready')
        self.assertEqual(out['total_events'], 2)
        self.assertEqual(out['ready_events'], 2)
        self.assertEqual(out['partial_events'], 0)
        self.assertEqual(out['blocked_events'], 0)
        self.assertEqual(out['ready_event_names'], ['EventA', 'EventA'])
        self.assertEqual(out['portfolio_cards'][0]['event_status'], 'ready')
        self.assertIn('portfolio_summary', out)

    def test_all_blocked(self):
        results = [self.blocked_event, self.blocked_event]
        out = portfolio_summary_pack(results)
        self.assertEqual(out['portfolio_status'], 'blocked')
        self.assertEqual(out['blocked_events'], 2)
        self.assertEqual(out['ready_events'], 0)
        self.assertEqual(out['partial_events'], 0)
        self.assertEqual(out['blocked_event_names'], ['EventC', 'EventC'])

    def test_mixed(self):
        results = [self.ready_event, self.partial_event, self.blocked_event]
        out = portfolio_summary_pack(results)
        self.assertEqual(out['portfolio_status'], 'partial')
        self.assertEqual(out['total_events'], 3)
        self.assertEqual(out['ready_events'], 1)
        self.assertEqual(out['partial_events'], 1)
        self.assertEqual(out['blocked_events'], 1)
        self.assertEqual(set(out['event_names']), {'EventA', 'EventB', 'EventC'})
        self.assertEqual(out['ready_event_names'], ['EventA'])
        self.assertEqual(out['partial_event_names'], ['EventB'])
        self.assertEqual(out['blocked_event_names'], ['EventC'])
        self.assertEqual(len(out['portfolio_cards']), 3)
        self.assertIn('portfolio_summary', out)

    def test_empty(self):
        out = portfolio_summary_pack([])
        self.assertEqual(out['portfolio_status'], 'partial')
        self.assertEqual(out['total_events'], 0)
        self.assertEqual(out['ready_events'], 0)
        self.assertEqual(out['partial_events'], 0)
        self.assertEqual(out['blocked_events'], 0)
        self.assertEqual(out['event_names'], [])
        self.assertEqual(out['portfolio_cards'], [])
        self.assertIn('portfolio_summary', out)

if __name__ == '__main__':
    unittest.main()
