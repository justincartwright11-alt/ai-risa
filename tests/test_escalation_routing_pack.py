import unittest
from workflows.escalation_routing_pack import escalation_routing_pack

class TestEscalationRoutingPack(unittest.TestCase):
    def test_all_routed(self):
        result = escalation_routing_pack({
            'event_name': 'event1',
            'automation_governance_status': 'ready',
            'governance_ready_entries': [
                {
                    'event_name': 'event1',
                    'bout_index': 0,
                    'governance_status': 'ready',
                    'delivery_key': 'dk0',
                    'publication_label': 'A',
                    'publication_order': 1,
                    'governance_action': 'proceed',
                    'governance_reason': 'default-proceed',
                    'escalation_level': 'none',
                },
                {
                    'event_name': 'event1',
                    'bout_index': 1,
                    'governance_status': 'ready',
                    'delivery_key': 'dk1',
                    'publication_label': 'B',
                    'publication_order': 2,
                    'governance_action': 'proceed',
                    'governance_reason': 'default-proceed',
                    'escalation_level': 'none',
                }
            ],
            'blocked_governance_entries': [],
            'ready_bout_indices': [0, 1],
            'blocked_bout_indices': [],
            'blocker_summary': {},
            'escalation_flags': {0: 'none', 1: 'none'},
            'automation_governance_summary': {'automation_governance_status': 'ready'}
        })
        self.assertEqual(result['escalation_routing_status'], 'ready')
        self.assertEqual(len(result['routed_actions']), 2)
        for action in result['routed_actions']:
            self.assertEqual(action['routing_status'], 'ready')
            self.assertEqual(action['route_target'], 'publish_path')
        self.assertEqual(len(result['blocked_routes']), 0)

    def test_partial(self):
        result = escalation_routing_pack({
            'event_name': 'event2',
            'automation_governance_status': 'partial',
            'governance_ready_entries': [
                {
                    'event_name': 'event2',
                    'bout_index': 0,
                    'governance_status': 'ready',
                    'delivery_key': 'dk0',
                    'publication_label': 'ESCALATE',
                    'publication_order': 1,
                    'governance_action': 'escalate',
                    'governance_reason': 'label-triggered escalation',
                    'escalation_level': 'operator_review',
                }
            ],
            'blocked_governance_entries': [
                {
                    'event_name': 'event2',
                    'bout_index': 1,
                    'governance_status': 'blocked',
                    'blocker_reason': 'fail',
                    'escalation_level': 'manual_intervention',
                }
            ],
            'ready_bout_indices': [0],
            'blocked_bout_indices': [1],
            'blocker_summary': {'blocker_reason': {1: 'fail'}},
            'escalation_flags': {0: 'operator_review', 1: 'manual_intervention'},
            'automation_governance_summary': {'automation_governance_status': 'partial'}
        })
        self.assertEqual(result['escalation_routing_status'], 'partial')
        self.assertEqual(len(result['routed_actions']), 1)
        self.assertEqual(len(result['blocked_routes']), 1)
        self.assertEqual(result['routed_actions'][0]['route_target'], 'operator_review')
        self.assertEqual(result['blocked_routes'][0]['blocker_reason'], 'fail')

    def test_all_blocked(self):
        result = escalation_routing_pack({
            'event_name': 'event3',
            'automation_governance_status': 'blocked',
            'governance_ready_entries': [],
            'blocked_governance_entries': [
                {
                    'event_name': 'event3',
                    'bout_index': 0,
                    'governance_status': 'blocked',
                    'blocker_reason': 'fail0',
                    'escalation_level': 'manual_intervention',
                },
                {
                    'event_name': 'event3',
                    'bout_index': 1,
                    'governance_status': 'blocked',
                    'blocker_reason': 'fail1',
                    'escalation_level': 'manual_intervention',
                }
            ],
            'ready_bout_indices': [],
            'blocked_bout_indices': [0, 1],
            'blocker_summary': {'blocker_reason': {0: 'fail0', 1: 'fail1'}},
            'escalation_flags': {0: 'manual_intervention', 1: 'manual_intervention'},
            'automation_governance_summary': {'automation_governance_status': 'blocked'}
        })
        self.assertEqual(result['escalation_routing_status'], 'blocked')
        self.assertEqual(len(result['routed_actions']), 0)
        self.assertEqual(len(result['blocked_routes']), 2)
        self.assertIn(result['blocked_routes'][0]['blocker_reason'], ['fail0', 'fail1'])
        self.assertIn(result['blocked_routes'][1]['blocker_reason'], ['fail0', 'fail1'])

if __name__ == '__main__':
    unittest.main()
