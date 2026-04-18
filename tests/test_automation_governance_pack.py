import unittest
from workflows.automation_governance_pack import automation_governance_pack

class TestAutomationGovernancePack(unittest.TestCase):
    def test_all_governance_ready(self):
        result = automation_governance_pack({
            'event_name': 'event1',
            'automation_state_ledger_status': 'ready',
            'ledger_entries': [
                {
                    'event_name': 'event1',
                    'bout_index': 0,
                    'ledger_status': 'ready',
                    'delivery_key': 'dk0',
                    'publication_label': 'A',
                    'publication_order': 1,
                },
                {
                    'event_name': 'event1',
                    'bout_index': 1,
                    'ledger_status': 'ready',
                    'delivery_key': 'dk1',
                    'publication_label': 'B',
                    'publication_order': 2,
                }
            ],
            'blocked_ledger_entries': [],
            'ready_bout_indices': [0, 1],
            'blocked_bout_indices': [],
            'blocker_summary': {},
            'automation_state_ledger_summary': {'automation_state_ledger_status': 'ready'}
        })
        self.assertEqual(result['automation_governance_status'], 'ready')
        self.assertEqual(len(result['governance_ready_entries']), 2)
        for entry in result['governance_ready_entries']:
            self.assertEqual(entry['governance_status'], 'ready')
            self.assertEqual(entry['governance_action'], 'proceed')
            self.assertEqual(entry['escalation_level'], 'none')
        self.assertEqual(len(result['blocked_governance_entries']), 0)
        self.assertTrue(all(v == 'none' for v in result['escalation_flags'].values()))

    def test_partial(self):
        result = automation_governance_pack({
            'event_name': 'event2',
            'automation_state_ledger_status': 'partial',
            'ledger_entries': [
                {
                    'event_name': 'event2',
                    'bout_index': 0,
                    'ledger_status': 'ready',
                    'delivery_key': 'dk0',
                    'publication_label': 'ESCALATE',
                    'publication_order': 1,
                }
            ],
            'blocked_ledger_entries': [
                {
                    'event_name': 'event2',
                    'bout_index': 1,
                    'ledger_status': 'blocked',
                    'blocker_reason': 'fail',
                }
            ],
            'ready_bout_indices': [0],
            'blocked_bout_indices': [1],
            'blocker_summary': {'blocker_reason': {1: 'fail'}},
            'automation_state_ledger_summary': {'automation_state_ledger_status': 'partial'}
        })
        self.assertEqual(result['automation_governance_status'], 'partial')
        self.assertEqual(len(result['governance_ready_entries']), 1)
        self.assertEqual(len(result['blocked_governance_entries']), 1)
        self.assertEqual(result['governance_ready_entries'][0]['governance_action'], 'escalate')
        self.assertEqual(result['governance_ready_entries'][0]['escalation_level'], 'operator_review')
        self.assertEqual(result['blocked_governance_entries'][0]['escalation_level'], 'manual_intervention')
        self.assertEqual(result['blocked_governance_entries'][0]['blocker_reason'], 'fail')
        self.assertEqual(result['escalation_flags'][0], 'operator_review')
        self.assertEqual(result['escalation_flags'][1], 'manual_intervention')

    def test_all_blocked(self):
        result = automation_governance_pack({
            'event_name': 'event3',
            'automation_state_ledger_status': 'blocked',
            'ledger_entries': [],
            'blocked_ledger_entries': [
                {
                    'event_name': 'event3',
                    'bout_index': 0,
                    'ledger_status': 'blocked',
                    'blocker_reason': 'fail0',
                },
                {
                    'event_name': 'event3',
                    'bout_index': 1,
                    'ledger_status': 'blocked',
                    'blocker_reason': 'fail1',
                }
            ],
            'ready_bout_indices': [],
            'blocked_bout_indices': [0, 1],
            'blocker_summary': {'blocker_reason': {0: 'fail0', 1: 'fail1'}},
            'automation_state_ledger_summary': {'automation_state_ledger_status': 'blocked'}
        })
        self.assertEqual(result['automation_governance_status'], 'blocked')
        self.assertEqual(len(result['governance_ready_entries']), 0)
        self.assertEqual(len(result['blocked_governance_entries']), 2)
        self.assertIn(result['blocked_governance_entries'][0]['blocker_reason'], ['fail0', 'fail1'])
        self.assertIn(result['blocked_governance_entries'][1]['blocker_reason'], ['fail0', 'fail1'])
        self.assertEqual(result['escalation_flags'][0], 'manual_intervention')
        self.assertEqual(result['escalation_flags'][1], 'manual_intervention')

if __name__ == '__main__':
    unittest.main()
