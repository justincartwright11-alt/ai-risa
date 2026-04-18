import unittest
from workflows.control_plane_reconciliation_pack import control_plane_reconciliation_pack

def make_ledger(**kwargs):
    return dict(kwargs)

class TestControlPlaneReconciliationPack(unittest.TestCase):
    def setUp(self):
        self.ledger = make_ledger(
            control_plane_state_ledger_status='partial',
            event_count=3,
            ready_event_names=['E1'],
            blocked_event_names=['E3'],
            ledger_entries=[
                {
                    'event_name': 'E1',
                    'event_status': 'ready',
                    'priority': 1,
                    'queue_action': 'queue_proceed',
                    'dispatch_batch': 'dispatch_proceed_batch',
                    'execution_batch': 'execution_proceed_batch',
                    'outcome_batch': 'complete_proceed_batch',
                    'ledger_status': 'ledger_ready',
                    'source_card': {'event_name': 'E1'},
                },
                {
                    'event_name': 'E2',
                    'event_status': 'partial',
                    'priority': 2,
                    'queue_action': 'queue_review',
                    'dispatch_batch': 'dispatch_review_batch',
                    'execution_batch': 'execution_review_batch',
                    'outcome_batch': 'complete_review_batch',
                    'ledger_status': 'ledger_ready',
                    'source_card': {'event_name': 'E2'},
                }
            ],
            blocked_ledger_entries=[
                {
                    'event_name': 'E3',
                    'event_status': 'blocked',
                    'priority': 3,
                    'blocker_reason': 'Event is blocked',
                    'outcome_snapshot': {'event_name': 'E3'}
                }
            ],
            priority_queue=['E1', 'E2'],
            escalation_queue=['E2', 'E3'],
            blocker_summary={'E3': 'Event is blocked'},
            control_plane_state_ledger_summary={
                'ledger_status': 'partial',
                'event_count': 3,
                'ledger_count': 2,
                'blocked_ledger_count': 1,
                'ready_event_names': ['E1'],
                'blocked_event_names': ['E3'],
                'priority_queue': ['E1', 'E2'],
                'escalation_queue': ['E2', 'E3'],
                'blocker_summary': {'E3': 'Event is blocked'}
            }
        )

    def test_reconciliation_ready(self):
        o = dict(self.ledger)
        o['ledger_entries'] = [dict(self.ledger['ledger_entries'][0])]
        o['blocked_ledger_entries'] = []
        o['ready_event_names'] = ['E1']
        o['blocked_event_names'] = []
        out = control_plane_reconciliation_pack(o)
        self.assertEqual(out['control_plane_reconciliation_status'], 'ready')
        self.assertEqual(len(out['reconciled_entries']), 1)
        self.assertEqual(out['reconciled_entries'][0]['reconciliation_status'], 'reconciled')
        self.assertEqual(out['reconciled_entries'][0]['event_name'], 'E1')
        self.assertEqual(out['blocked_reconciliations'], [])
        self.assertIn('control_plane_reconciliation_summary', out)

    def test_reconciliation_partial(self):
        out = control_plane_reconciliation_pack(self.ledger)
        self.assertEqual(out['control_plane_reconciliation_status'], 'partial')
        self.assertEqual(len(out['reconciled_entries']), 2)
        self.assertEqual(out['reconciled_entries'][0]['reconciliation_status'], 'reconciled')
        self.assertEqual(out['reconciled_entries'][1]['reconciliation_status'], 'reconciled')
        self.assertEqual(len(out['blocked_reconciliations']), 1)
        self.assertEqual(out['blocked_reconciliations'][0]['event_name'], 'E3')
        self.assertEqual(out['blocked_reconciliations'][0]['blocker_reason'], 'Event is blocked')
        self.assertIn('control_plane_reconciliation_summary', out)

    def test_reconciliation_blocked(self):
        o = dict(self.ledger)
        o['ledger_entries'] = []
        o['blocked_ledger_entries'] = [dict(self.ledger['blocked_ledger_entries'][0])]
        o['ready_event_names'] = []
        o['blocked_event_names'] = ['E3']
        out = control_plane_reconciliation_pack(o)
        self.assertEqual(out['control_plane_reconciliation_status'], 'blocked')
        self.assertEqual(out['reconciled_entries'], [])
        self.assertEqual(len(out['blocked_reconciliations']), 1)
        self.assertEqual(out['blocked_reconciliations'][0]['event_name'], 'E3')
        self.assertEqual(out['blocked_reconciliations'][0]['blocker_reason'], 'Event is blocked')
        self.assertIn('control_plane_reconciliation_summary', out)

if __name__ == '__main__':
    unittest.main()
