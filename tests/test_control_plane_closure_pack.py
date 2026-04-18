import unittest
from workflows.control_plane_closure_pack import control_plane_closure_pack

def make_remediation_outcome(**kwargs):
    return dict(kwargs)

class TestControlPlaneClosurePack(unittest.TestCase):
    def setUp(self):
        self.remediation_outcome = make_remediation_outcome(
            control_plane_remediation_outcome_status='partial',
            event_count=3,
            ready_event_names=['E1'],
            blocked_event_names=['E3'],
            completed_remediations=[
                {
                    'event_name': 'E1',
                    'event_status': 'ready',
                    'priority': 1,
                    'followup_action': 'proceed_followup',
                    'remediation_action': 'remediate_proceed',
                    'execution_action': 'execute_remediate_proceed',
                    'outcome_action': 'complete_remediate_proceed',
                    'escalation_level': 0,
                    'source_card': {'event_name': 'E1'},
                },
                {
                    'event_name': 'E2',
                    'event_status': 'partial',
                    'priority': 2,
                    'followup_action': 'review_followup',
                    'remediation_action': 'remediate_review',
                    'execution_action': 'execute_remediate_review',
                    'outcome_action': 'complete_remediate_review',
                    'escalation_level': 1,
                    'source_card': {'event_name': 'E2'},
                }
            ],
            blocked_remediation_outcomes=[
                {
                    'event_name': 'E3',
                    'event_status': 'blocked',
                    'priority': 3,
                    'blocker_reason': 'Event is blocked',
                    'execution_snapshot': {'event_name': 'E3'}
                }
            ],
            priority_queue=['E1', 'E2'],
            escalation_queue=['E2', 'E3'],
            blocker_summary={'E3': 'Event is blocked'},
            control_plane_remediation_outcome_summary={
                'remediation_outcome_status': 'partial',
                'event_count': 3,
                'completed_count': 2,
                'blocked_count': 1,
                'ready_event_names': ['E1'],
                'blocked_event_names': ['E3'],
                'priority_queue': ['E1', 'E2'],
                'escalation_queue': ['E2', 'E3'],
                'blocker_summary': {'E3': 'Event is blocked'}
            }
        )

    def test_closure_ready(self):
        o = dict(self.remediation_outcome)
        o['completed_remediations'] = [dict(self.remediation_outcome['completed_remediations'][0])]
        o['blocked_remediation_outcomes'] = []
        o['ready_event_names'] = ['E1']
        o['blocked_event_names'] = []
        out = control_plane_closure_pack(o)
        self.assertEqual(out['control_plane_closure_status'], 'ready')
        self.assertEqual(len(out['closed_events']), 1)
        self.assertEqual(out['closed_events'][0]['closure_action'], 'close_event')
        self.assertEqual(out['closed_events'][0]['event_name'], 'E1')
        self.assertEqual(out['pending_events'], [])
        self.assertIn('control_plane_closure_summary', out)

    def test_closure_partial(self):
        out = control_plane_closure_pack(self.remediation_outcome)
        self.assertEqual(out['control_plane_closure_status'], 'partial')
        self.assertEqual(len(out['closed_events']), 2)
        self.assertEqual(out['closed_events'][0]['closure_action'], 'close_event')
        self.assertEqual(out['closed_events'][1]['closure_action'], 'hold_open')
        self.assertEqual(len(out['pending_events']), 1)
        self.assertEqual(out['pending_events'][0]['event_name'], 'E3')
        self.assertEqual(out['pending_events'][0]['blocker_reason'], 'Event is blocked')
        self.assertIn('control_plane_closure_summary', out)

    def test_closure_blocked(self):
        o = dict(self.remediation_outcome)
        o['completed_remediations'] = []
        o['blocked_remediation_outcomes'] = [dict(self.remediation_outcome['blocked_remediation_outcomes'][0])]
        o['ready_event_names'] = []
        o['blocked_event_names'] = ['E3']
        out = control_plane_closure_pack(o)
        self.assertEqual(out['control_plane_closure_status'], 'blocked')
        self.assertEqual(out['closed_events'], [])
        self.assertEqual(len(out['pending_events']), 1)
        self.assertEqual(out['pending_events'][0]['event_name'], 'E3')
        self.assertEqual(out['pending_events'][0]['blocker_reason'], 'Event is blocked')
        self.assertIn('control_plane_closure_summary', out)

if __name__ == '__main__':
    unittest.main()
