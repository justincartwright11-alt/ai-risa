import unittest
from workflows.event_dashboard_pack import event_dashboard_pack

class TestEventDashboardPack(unittest.TestCase):
    def test_all_publish_ready(self):
        result = event_dashboard_pack({
            'event_name': 'event1',
            'event_control_status': 'ready',
            'total_bouts': 2,
            'publish_ready_count': 2,
            'review_required_count': 0,
            'manual_intervention_count': 0,
            'blocked_count': 0,
            'ready_bout_indices': [0, 1],
            'blocked_bout_indices': [],
            'blocker_summary': {},
            'decision_summary': {'publish_ready_count': 2},
            'event_control_summary': {'event_control_status': 'ready'}
        })
        self.assertEqual(result['event_dashboard_status'], 'ready')
        self.assertEqual(result['publish_ready_count'], 2)
        self.assertEqual(result['review_required_count'], 0)
        self.assertEqual(result['manual_intervention_count'], 0)
        self.assertEqual(result['blocked_count'], 0)
        self.assertEqual(result['total_bouts'], 2)
        self.assertEqual(len(result['dashboard_cards']), 2)
        for card in result['dashboard_cards']:
            self.assertEqual(card['status'], 'publish-ready')
            self.assertEqual(card['decision'], 'publish')

    def test_partial(self):
        result = event_dashboard_pack({
            'event_name': 'event2',
            'event_control_status': 'partial',
            'total_bouts': 3,
            'publish_ready_count': 1,
            'review_required_count': 1,
            'manual_intervention_count': 0,
            'blocked_count': 1,
            'ready_bout_indices': [0],
            'blocked_bout_indices': [2],
            'blocker_summary': {'blocker_reason': {2: 'fail'}},
            'decision_summary': {'publish_ready_count': 1, 'review_required_count': 1, 'blocked_count': 1},
            'event_control_summary': {'event_control_status': 'partial'}
        })
        self.assertEqual(result['event_dashboard_status'], 'partial')
        self.assertEqual(result['publish_ready_count'], 1)
        self.assertEqual(result['review_required_count'], 1)
        self.assertEqual(result['manual_intervention_count'], 0)
        self.assertEqual(result['blocked_count'], 1)
        self.assertEqual(result['total_bouts'], 3)
        self.assertEqual(len(result['dashboard_cards']), 3)
        self.assertEqual(result['dashboard_cards'][0]['status'], 'publish-ready')
        self.assertEqual(result['dashboard_cards'][0]['decision'], 'publish')
        self.assertEqual(result['dashboard_cards'][1]['status'], 'pending')
        self.assertEqual(result['dashboard_cards'][1]['decision'], 'review')
        self.assertEqual(result['dashboard_cards'][2]['status'], 'blocked')
        self.assertEqual(result['dashboard_cards'][2]['decision'], 'block')

    def test_all_blocked(self):
        result = event_dashboard_pack({
            'event_name': 'event3',
            'event_control_status': 'blocked',
            'total_bouts': 2,
            'publish_ready_count': 0,
            'review_required_count': 0,
            'manual_intervention_count': 0,
            'blocked_count': 2,
            'ready_bout_indices': [],
            'blocked_bout_indices': [0, 1],
            'blocker_summary': {'blocker_reason': {0: 'fail0', 1: 'fail1'}},
            'decision_summary': {'blocked_count': 2},
            'event_control_summary': {'event_control_status': 'blocked'}
        })
        self.assertEqual(result['event_dashboard_status'], 'blocked')
        self.assertEqual(result['publish_ready_count'], 0)
        self.assertEqual(result['review_required_count'], 0)
        self.assertEqual(result['manual_intervention_count'], 0)
        self.assertEqual(result['blocked_count'], 2)
        self.assertEqual(result['total_bouts'], 2)
        self.assertEqual(len(result['dashboard_cards']), 2)
        for card in result['dashboard_cards']:
            self.assertEqual(card['status'], 'blocked')
            self.assertEqual(card['decision'], 'block')

if __name__ == '__main__':
    unittest.main()
