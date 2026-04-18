"""
test_portfolio_dashboard_pack.py

Tests for portfolio_dashboard_pack workflow.
"""
import unittest
from workflows.portfolio_dashboard_pack import portfolio_dashboard_pack

class TestPortfolioDashboardPack(unittest.TestCase):
    def setUp(self):
        self.portfolio_summary = {
            'portfolio_status': 'partial',
            'total_events': 3,
            'ready_events': 1,
            'partial_events': 1,
            'blocked_events': 1,
            'event_names': ['EventA', 'EventB', 'EventC'],
            'ready_event_names': ['EventA'],
            'partial_event_names': ['EventB'],
            'blocked_event_names': ['EventC'],
            'portfolio_cards': [
                {
                    'event_name': 'EventA',
                    'event_status': 'ready',
                    'total_bouts': 3,
                    'publish_ready_count': 3,
                    'review_required_count': 0,
                    'manual_intervention_count': 0,
                    'blocked_count': 0,
                    'priority': 1,
                    'notes': 'All bouts ready.'
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
                    'notes': 'One bout needs review.'
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
                    'notes': 'Manual intervention required.'
                }
            ],
            'portfolio_summary': {}
        }

    def test_dashboard_status_partial(self):
        out = portfolio_dashboard_pack(self.portfolio_summary)
        self.assertEqual(out['portfolio_dashboard_status'], 'partial')
        self.assertEqual(out['total_events'], 3)
        self.assertEqual(out['ready_events'], 1)
        self.assertEqual(out['partial_events'], 1)
        self.assertEqual(out['blocked_events'], 1)
        self.assertEqual(len(out['dashboard_cards']), 3)
        self.assertEqual(len(out['priority_queue']), 3)
        self.assertEqual(out['blocked_event_names'], ['EventC'])
        self.assertIn('portfolio_dashboard_summary', out)
        # Check dashboard card structure
        card = out['dashboard_cards'][0]
        self.assertIn('source_summary', card)
        self.assertEqual(card['event_name'], 'EventA')

    def test_dashboard_status_ready(self):
        summary = dict(self.portfolio_summary)
        summary['portfolio_status'] = 'ready'
        summary['ready_events'] = 2
        summary['partial_events'] = 0
        summary['blocked_events'] = 0
        summary['total_events'] = 2
        summary['event_names'] = ['EventA', 'EventD']
        summary['ready_event_names'] = ['EventA', 'EventD']
        summary['partial_event_names'] = []
        summary['blocked_event_names'] = []
        summary['portfolio_cards'] = [
            {
                'event_name': 'EventA',
                'event_status': 'ready',
                'total_bouts': 3,
                'publish_ready_count': 3,
                'review_required_count': 0,
                'manual_intervention_count': 0,
                'blocked_count': 0,
                'priority': 1,
                'notes': 'All bouts ready.'
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
                'notes': 'All bouts ready.'
            }
        ]
        out = portfolio_dashboard_pack(summary)
        self.assertEqual(out['portfolio_dashboard_status'], 'ready')
        self.assertEqual(out['ready_events'], 2)
        self.assertEqual(out['blocked_events'], 0)
        self.assertEqual(out['partial_events'], 0)
        self.assertEqual(out['blocked_event_names'], [])

    def test_dashboard_status_blocked(self):
        summary = dict(self.portfolio_summary)
        summary['portfolio_status'] = 'blocked'
        summary['ready_events'] = 0
        summary['partial_events'] = 0
        summary['blocked_events'] = 2
        summary['total_events'] = 2
        summary['event_names'] = ['EventC', 'EventE']
        summary['ready_event_names'] = []
        summary['partial_event_names'] = []
        summary['blocked_event_names'] = ['EventC', 'EventE']
        summary['portfolio_cards'] = [
            {
                'event_name': 'EventC',
                'event_status': 'blocked',
                'total_bouts': 2,
                'publish_ready_count': 0,
                'review_required_count': 0,
                'manual_intervention_count': 1,
                'blocked_count': 1,
                'priority': 3,
                'notes': 'Manual intervention required.'
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
                'notes': 'Manual intervention required.'
            }
        ]
        out = portfolio_dashboard_pack(summary)
        self.assertEqual(out['portfolio_dashboard_status'], 'blocked')
        self.assertEqual(out['blocked_events'], 2)
        self.assertEqual(out['ready_events'], 0)
        self.assertEqual(out['partial_events'], 0)
        self.assertEqual(set(out['blocked_event_names']), {'EventC', 'EventE'})
        self.assertEqual(len(out['dashboard_cards']), 2)
        self.assertEqual(len(out['priority_queue']), 2)

    def test_empty(self):
        summary = {
            'portfolio_status': 'partial',
            'total_events': 0,
            'ready_events': 0,
            'partial_events': 0,
            'blocked_events': 0,
            'event_names': [],
            'ready_event_names': [],
            'partial_event_names': [],
            'blocked_event_names': [],
            'portfolio_cards': [],
            'portfolio_summary': {}
        }
        out = portfolio_dashboard_pack(summary)
        self.assertEqual(out['portfolio_dashboard_status'], 'partial')
        self.assertEqual(out['total_events'], 0)
        self.assertEqual(out['dashboard_cards'], [])
        self.assertEqual(out['priority_queue'], [])
        self.assertIn('portfolio_dashboard_summary', out)

if __name__ == '__main__':
    unittest.main()
