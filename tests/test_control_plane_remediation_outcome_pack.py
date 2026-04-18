import unittest
from workflows.control_plane_remediation_outcome_pack import control_plane_remediation_outcome_pack

def make_execution(**kwargs):
    return dict(kwargs)

class TestControlPlaneRemediationOutcomePack(unittest.TestCase):
    def setUp(self):
        self.execution = make_execution(
            control_plane_remediation_execution_status='partial',
            event_count=3,
            ready_event_names=['E1'],
            blocked_event_names=['E3'],
            execution_ready_remediations=[
                {
                    'event_name': 'E1',
                    'event_status': 'ready',
                    'priority': 1,
                    'followup_action': 'proceed_followup',
                    'followup_reason': 'Ready for follow-up proceed',
                    'remediation_action': 'remediate_proceed',
                    'remediation_reason': 'Proceed with remediation',
                    'execution_action': 'execute_remediate_proceed',
                    'execution_reason': 'Proceed with remediation execution',
                    'escalation_level': 0,
                    'source_card': {'event_name': 'E1'},
                },
                {
                    'event_name': 'E2',
                    'event_status': 'partial',
                    'priority': 2,
                    'followup_action': 'review_followup',
                    'followup_reason': 'Requires operator review follow-up',
                    'remediation_action': 'remediate_review',
                    'remediation_reason': 'Remediation requires operator review',
                    'execution_action': 'execute_remediate_review',
                    'execution_reason': 'Remediation execution requires operator review',
                    'escalation_level': 1,
                    'source_card': {'event_name': 'E2'},
                }
            ],
            blocked_remediation_executions=[
                {
                    'event_name': 'E3',
                    'event_status': 'blocked',
                    'priority': 3,
                    'blocker_reason': 'Event is blocked',
                    'remediation_snapshot': {'event_name': 'E3'}
                }
            ],
            priority_queue=['E1', 'E2'],
            escalation_queue=['E2', 'E3'],
            blocker_summary={'E3': 'Event is blocked'},
            control_plane_remediation_execution_summary={
                'remediation_execution_status': 'partial',
                'event_count': 3,
                'execution_ready_count': 2,
                'blocked_execution_count': 1,
                'ready_event_names': ['E1'],
                'blocked_event_names': ['E3'],
                'priority_queue': ['E1', 'E2'],
                'escalation_queue': ['E2', 'E3'],
                'blocker_summary': {'E3': 'Event is blocked'}
            }
        )

    def test_outcome_ready(self):
        o = dict(self.execution)
        o['execution_ready_remediations'] = [dict(self.execution['execution_ready_remediations'][0])]
        o['blocked_remediation_executions'] = []
        o['ready_event_names'] = ['E1']
        o['blocked_event_names'] = []
        out = control_plane_remediation_outcome_pack(o)
        self.assertEqual(out['control_plane_remediation_outcome_status'], 'ready')
        self.assertEqual(len(out['completed_remediations']), 1)
        self.assertEqual(out['completed_remediations'][0]['outcome_action'], 'complete_remediate_proceed')
        self.assertEqual(out['completed_remediations'][0]['event_name'], 'E1')
        self.assertEqual(out['blocked_remediation_outcomes'], [])
        self.assertIn('control_plane_remediation_outcome_summary', out)

    def test_outcome_partial(self):
        out = control_plane_remediation_outcome_pack(self.execution)
        self.assertEqual(out['control_plane_remediation_outcome_status'], 'partial')
        self.assertEqual(len(out['completed_remediations']), 2)
        self.assertEqual(out['completed_remediations'][0]['outcome_action'], 'complete_remediate_proceed')
        self.assertEqual(out['completed_remediations'][1]['outcome_action'], 'complete_remediate_review')
        self.assertEqual(len(out['blocked_remediation_outcomes']), 1)
        self.assertEqual(out['blocked_remediation_outcomes'][0]['event_name'], 'E3')
        self.assertEqual(out['blocked_remediation_outcomes'][0]['blocker_reason'], 'Event is blocked')
        self.assertIn('control_plane_remediation_outcome_summary', out)

    def test_outcome_blocked(self):
        o = dict(self.execution)
        o['execution_ready_remediations'] = []
        o['blocked_remediation_executions'] = [dict(self.execution['blocked_remediation_executions'][0])]
        o['ready_event_names'] = []
        o['blocked_event_names'] = ['E3']
        out = control_plane_remediation_outcome_pack(o)
        self.assertEqual(out['control_plane_remediation_outcome_status'], 'blocked')
        self.assertEqual(out['completed_remediations'], [])
        self.assertEqual(len(out['blocked_remediation_outcomes']), 1)
        self.assertEqual(out['blocked_remediation_outcomes'][0]['event_name'], 'E3')
        self.assertEqual(out['blocked_remediation_outcomes'][0]['blocker_reason'], 'Event is blocked')
        self.assertIn('control_plane_remediation_outcome_summary', out)

if __name__ == '__main__':
    unittest.main()
