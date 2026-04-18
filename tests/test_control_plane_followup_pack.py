import unittest
from workflows.control_plane_followup_pack import control_plane_followup_pack

def make_reconciliation(**kwargs):
    return dict(kwargs)

class TestControlPlaneFollowupPack(unittest.TestCase):
    def setUp(self):
        self.reconciliation = make_reconciliation(
            control_plane_reconciliation_status='partial',
            event_count=3,
            ready_event_names=['E1'],
            blocked_event_names=['E3'],
            reconciled_entries=[
                {
                    'event_name': 'E1',
                    'event_status': 'ready',
                    'priority': 1,
                    'reconciliation_status': 'reconciled',
                    'source_card': {'event_name': 'E1'},
                },
                {
                    'event_name': 'E2',
                    'event_status': 'partial',
                    'priority': 2,
                    'reconciliation_status': 'reconciled',
                    'source_card': {'event_name': 'E2'},
                }
            ],
            blocked_reconciliations=[
                {
                    'event_name': 'E3',
                    'event_status': 'blocked',
                    'priority': 3,
                    'blocker_reason': 'Event is blocked',
                    'ledger_snapshot': {'event_name': 'E3'}
                }
            ],
            priority_queue=['E1', 'E2'],
            escalation_queue=['E2', 'E3'],
            blocker_summary={'E3': 'Event is blocked'},
            control_plane_reconciliation_summary={
                'reconciliation_status': 'partial',
                'event_count': 3,
                'reconciled_count': 2,
                'blocked_reconciled_count': 1,
                'ready_event_names': ['E1'],
                'blocked_event_names': ['E3'],
                'priority_queue': ['E1', 'E2'],
                'escalation_queue': ['E2', 'E3'],
                'blocker_summary': {'E3': 'Event is blocked'}
            }
        )

    def test_followup_ready(self):
        o = dict(self.reconciliation)
        o['reconciled_entries'] = [dict(self.reconciliation['reconciled_entries'][0])]
        o['blocked_reconciliations'] = []
        o['ready_event_names'] = ['E1']
        o['blocked_event_names'] = []
        out = control_plane_followup_pack(o)
        self.assertEqual(out['control_plane_followup_status'], 'ready')
        self.assertEqual(len(out['followup_actions']), 1)
        self.assertEqual(out['followup_actions'][0]['followup_action'], 'proceed_followup')
        self.assertEqual(out['followup_actions'][0]['event_name'], 'E1')
        self.assertEqual(out['blocked_followups'], [])
        self.assertIn('control_plane_followup_summary', out)

    def test_followup_partial(self):
        out = control_plane_followup_pack(self.reconciliation)
        self.assertEqual(out['control_plane_followup_status'], 'partial')
        self.assertEqual(len(out['followup_actions']), 2)
        self.assertEqual(out['followup_actions'][0]['followup_action'], 'proceed_followup')
        self.assertEqual(out['followup_actions'][1]['followup_action'], 'review_followup')
        self.assertEqual(len(out['blocked_followups']), 1)
        self.assertEqual(out['blocked_followups'][0]['event_name'], 'E3')
        self.assertEqual(out['blocked_followups'][0]['blocker_reason'], 'Event is blocked')
        self.assertIn('control_plane_followup_summary', out)

    def test_followup_blocked(self):
        o = dict(self.reconciliation)
        o['reconciled_entries'] = []
        o['blocked_reconciliations'] = [dict(self.reconciliation['blocked_reconciliations'][0])]
        o['ready_event_names'] = []
        o['blocked_event_names'] = ['E3']
        out = control_plane_followup_pack(o)
        self.assertEqual(out['control_plane_followup_status'], 'blocked')
        self.assertEqual(out['followup_actions'], [])
        self.assertEqual(len(out['blocked_followups']), 1)
        self.assertEqual(out['blocked_followups'][0]['event_name'], 'E3')
        self.assertEqual(out['blocked_followups'][0]['blocker_reason'], 'Event is blocked')
        self.assertIn('control_plane_followup_summary', out)

if __name__ == '__main__':
    unittest.main()
