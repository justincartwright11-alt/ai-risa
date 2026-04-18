import unittest
from workflows.resolution_decision_pack import resolution_decision_pack

class TestResolutionDecisionPack(unittest.TestCase):
    def test_all_resolved(self):
        result = resolution_decision_pack({
            'event_name': 'event1',
            'escalation_routing_status': 'ready',
            'routed_actions': [
                {
                    'event_name': 'event1',
                    'bout_index': 0,
                    'routing_status': 'ready',
                    'delivery_key': 'dk0',
                    'publication_label': 'A',
                    'publication_order': 1,
                    'governance_action': 'proceed',
                    'route_target': 'publish_path',
                },
                {
                    'event_name': 'event1',
                    'bout_index': 1,
                    'routing_status': 'ready',
                    'delivery_key': 'dk1',
                    'publication_label': 'B',
                    'publication_order': 2,
                    'governance_action': 'proceed',
                    'route_target': 'publish_path',
                }
            ],
            'blocked_routes': [],
            'ready_bout_indices': [0, 1],
            'blocked_bout_indices': [],
            'blocker_summary': {},
            'escalation_summary': {'escalation_routing_status': 'ready'}
        })
        self.assertEqual(result['resolution_decision_status'], 'ready')
        self.assertEqual(len(result['resolved_entries']), 2)
        for entry in result['resolved_entries']:
            self.assertEqual(entry['resolution_status'], 'ready')
            self.assertEqual(entry['resolution_action'], 'publish')
        self.assertEqual(len(result['blocked_resolutions']), 0)

    def test_partial(self):
        result = resolution_decision_pack({
            'event_name': 'event2',
            'escalation_routing_status': 'partial',
            'routed_actions': [
                {
                    'event_name': 'event2',
                    'bout_index': 0,
                    'routing_status': 'ready',
                    'delivery_key': 'dk0',
                    'publication_label': 'ESCALATE',
                    'publication_order': 1,
                    'governance_action': 'escalate',
                    'route_target': 'operator_review',
                }
            ],
            'blocked_routes': [
                {
                    'event_name': 'event2',
                    'bout_index': 1,
                    'routing_status': 'blocked',
                    'blocker_reason': 'fail',
                }
            ],
            'ready_bout_indices': [0],
            'blocked_bout_indices': [1],
            'blocker_summary': {'blocker_reason': {1: 'fail'}},
            'escalation_summary': {'escalation_routing_status': 'partial'}
        })
        self.assertEqual(result['resolution_decision_status'], 'partial')
        self.assertEqual(len(result['resolved_entries']), 1)
        self.assertEqual(len(result['blocked_resolutions']), 1)
        self.assertEqual(result['resolved_entries'][0]['resolution_action'], 'review')
        self.assertEqual(result['blocked_resolutions'][0]['blocker_reason'], 'fail')

    def test_all_blocked(self):
        result = resolution_decision_pack({
            'event_name': 'event3',
            'escalation_routing_status': 'blocked',
            'routed_actions': [],
            'blocked_routes': [
                {
                    'event_name': 'event3',
                    'bout_index': 0,
                    'routing_status': 'blocked',
                    'blocker_reason': 'fail0',
                },
                {
                    'event_name': 'event3',
                    'bout_index': 1,
                    'routing_status': 'blocked',
                    'blocker_reason': 'fail1',
                }
            ],
            'ready_bout_indices': [],
            'blocked_bout_indices': [0, 1],
            'blocker_summary': {'blocker_reason': {0: 'fail0', 1: 'fail1'}},
            'escalation_summary': {'escalation_routing_status': 'blocked'}
        })
        self.assertEqual(result['resolution_decision_status'], 'blocked')
        self.assertEqual(len(result['resolved_entries']), 0)
        self.assertEqual(len(result['blocked_resolutions']), 2)
        self.assertIn(result['blocked_resolutions'][0]['blocker_reason'], ['fail0', 'fail1'])
        self.assertIn(result['blocked_resolutions'][1]['blocker_reason'], ['fail0', 'fail1'])

if __name__ == '__main__':
    unittest.main()
