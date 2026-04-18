import unittest
from workflows.control_plane_state_ledger_pack import control_plane_state_ledger_pack

def make_outcome(**kwargs):
    return dict(kwargs)

class TestControlPlaneStateLedgerPack(unittest.TestCase):
    def setUp(self):
        self.outcome = make_outcome(
            control_plane_outcome_status='partial',
            event_count=3,
            ready_event_names=['E1'],
            blocked_event_names=['E3'],
            completed_actions=[
                {
                    'event_name': 'E1',
                    'event_status': 'ready',
                    'priority': 1,
                    'queue_action': 'queue_proceed',
                    'queue_reason': 'Event ready to proceed',
                    'dispatch_batch': 'dispatch_proceed_batch',
                    'dispatch_reason': 'Proceed batch for ready events',
                    'execution_batch': 'execution_proceed_batch',
                    'execution_reason': 'Proceed batch for ready events',
                    'outcome_batch': 'complete_proceed_batch',
                    'outcome_reason': 'Completed proceed batch',
                    'source_card': {'event_name': 'E1'},
                },
                {
                    'event_name': 'E2',
                    'event_status': 'partial',
                    'priority': 2,
                    'queue_action': 'queue_review',
                    'queue_reason': 'Event requires operator review',
                    'dispatch_batch': 'dispatch_review_batch',
                    'dispatch_reason': 'Review batch for operator review events',
                    'execution_batch': 'execution_review_batch',
                    'execution_reason': 'Review batch for operator review events',
                    'outcome_batch': 'complete_review_batch',
                    'outcome_reason': 'Completed review batch',
                    'source_card': {'event_name': 'E2'},
                }
            ],
            blocked_outcomes=[
                {
                    'event_name': 'E3',
                    'event_status': 'blocked',
                    'priority': 3,
                    'blocker_reason': 'Event is blocked',
                    'execution_snapshot': {'event_name': 'E3'}
                }
            ],
            outcome_batches={
                'complete_proceed_batch': [{'event_name': 'E1'}],
                'complete_review_batch': [{'event_name': 'E2'}],
                'complete_hold_batch': [],
                'complete_escalation_batch': []
            },
            priority_queue=['E1', 'E2'],
            escalation_queue=['E2', 'E3'],
            blocker_summary={'E3': 'Event is blocked'}
        )

    def test_ledger_ready(self):
        o = dict(self.outcome)
        o['completed_actions'] = [dict(self.outcome['completed_actions'][0])]
        o['blocked_outcomes'] = []
        o['ready_event_names'] = ['E1']
        o['blocked_event_names'] = []
        out = control_plane_state_ledger_pack(o)
        self.assertEqual(out['control_plane_state_ledger_status'], 'ready')
        self.assertEqual(len(out['ledger_entries']), 1)
        self.assertEqual(out['ledger_entries'][0]['ledger_status'], 'ledger_ready')
        self.assertEqual(out['ledger_entries'][0]['event_name'], 'E1')
        self.assertEqual(out['blocked_ledger_entries'], [])
        self.assertIn('control_plane_state_ledger_summary', out)

    def test_ledger_partial(self):
        out = control_plane_state_ledger_pack(self.outcome)
        self.assertEqual(out['control_plane_state_ledger_status'], 'partial')
        self.assertEqual(len(out['ledger_entries']), 2)
        self.assertEqual(out['ledger_entries'][0]['ledger_status'], 'ledger_ready')
        self.assertEqual(out['ledger_entries'][1]['ledger_status'], 'ledger_ready')
        self.assertEqual(len(out['blocked_ledger_entries']), 1)
        self.assertEqual(out['blocked_ledger_entries'][0]['event_name'], 'E3')
        self.assertEqual(out['blocked_ledger_entries'][0]['blocker_reason'], 'Event is blocked')
        self.assertIn('control_plane_state_ledger_summary', out)

    def test_ledger_blocked(self):
        o = dict(self.outcome)
        o['completed_actions'] = []
        o['blocked_outcomes'] = [dict(self.outcome['blocked_outcomes'][0])]
        o['ready_event_names'] = []
        o['blocked_event_names'] = ['E3']
        out = control_plane_state_ledger_pack(o)
        self.assertEqual(out['control_plane_state_ledger_status'], 'blocked')
        self.assertEqual(out['ledger_entries'], [])
        self.assertEqual(len(out['blocked_ledger_entries']), 1)
        self.assertEqual(out['blocked_ledger_entries'][0]['event_name'], 'E3')
        self.assertEqual(out['blocked_ledger_entries'][0]['blocker_reason'], 'Event is blocked')
        self.assertIn('control_plane_state_ledger_summary', out)

if __name__ == '__main__':
    unittest.main()
