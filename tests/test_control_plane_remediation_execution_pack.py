import unittest
from workflows.control_plane_remediation_execution_pack import control_plane_remediation_execution_pack

def make_remediation(**kwargs):
    return dict(kwargs)

class TestControlPlaneRemediationExecutionPack(unittest.TestCase):
    def setUp(self):
        self.remediation = make_remediation(
            control_plane_remediation_status='partial',
            event_count=3,
            ready_event_names=['E1'],
            blocked_event_names=['E3'],
            remediation_actions=[
                {
                    'event_name': 'E1',
                    'event_status': 'ready',
                    'priority': 1,
                    'followup_action': 'proceed_followup',
                    'followup_reason': 'Ready for follow-up proceed',
                    'remediation_action': 'remediate_proceed',
                    'remediation_reason': 'Proceed with remediation',
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
                    'escalation_level': 1,
                    'source_card': {'event_name': 'E2'},
                }
            ],
            blocked_remediations=[
                {
                    'event_name': 'E3',
                    'event_status': 'blocked',
                    'priority': 3,
                    'blocker_reason': 'Event is blocked',
                    'followup_snapshot': {'event_name': 'E3'}
                }
            ],
            priority_queue=['E1', 'E2'],
            escalation_queue=['E2', 'E3'],
            blocker_summary={'E3': 'Event is blocked'},
            control_plane_remediation_summary={
                'remediation_status': 'partial',
                'event_count': 3,
                'remediation_count': 2,
                'blocked_remediation_count': 1,
                'ready_event_names': ['E1'],
                'blocked_event_names': ['E3'],
                'priority_queue': ['E1', 'E2'],
                'escalation_queue': ['E2', 'E3'],
                'blocker_summary': {'E3': 'Event is blocked'}
            }
        )

    def test_execution_ready(self):
        o = dict(self.remediation)
        o['remediation_actions'] = [dict(self.remediation['remediation_actions'][0])]
        o['blocked_remediations'] = []
        o['ready_event_names'] = ['E1']
        o['blocked_event_names'] = []
        out = control_plane_remediation_execution_pack(o)
        self.assertEqual(out['control_plane_remediation_execution_status'], 'ready')
        self.assertEqual(len(out['execution_ready_remediations']), 1)
        self.assertEqual(out['execution_ready_remediations'][0]['execution_action'], 'execute_remediate_proceed')
        self.assertEqual(out['execution_ready_remediations'][0]['event_name'], 'E1')
        self.assertEqual(out['blocked_remediation_executions'], [])
        self.assertIn('control_plane_remediation_execution_summary', out)

    def test_execution_partial(self):
        out = control_plane_remediation_execution_pack(self.remediation)
        self.assertEqual(out['control_plane_remediation_execution_status'], 'partial')
        self.assertEqual(len(out['execution_ready_remediations']), 2)
        self.assertEqual(out['execution_ready_remediations'][0]['execution_action'], 'execute_remediate_proceed')
        self.assertEqual(out['execution_ready_remediations'][1]['execution_action'], 'execute_remediate_review')
        self.assertEqual(len(out['blocked_remediation_executions']), 1)
        self.assertEqual(out['blocked_remediation_executions'][0]['event_name'], 'E3')
        self.assertEqual(out['blocked_remediation_executions'][0]['blocker_reason'], 'Event is blocked')
        self.assertIn('control_plane_remediation_execution_summary', out)

    def test_execution_blocked(self):
        o = dict(self.remediation)
        o['remediation_actions'] = []
        o['blocked_remediations'] = [dict(self.remediation['blocked_remediations'][0])]
        o['ready_event_names'] = []
        o['blocked_event_names'] = ['E3']
        out = control_plane_remediation_execution_pack(o)
        self.assertEqual(out['control_plane_remediation_execution_status'], 'blocked')
        self.assertEqual(out['execution_ready_remediations'], [])
        self.assertEqual(len(out['blocked_remediation_executions']), 1)
        self.assertEqual(out['blocked_remediation_executions'][0]['event_name'], 'E3')
        self.assertEqual(out['blocked_remediation_executions'][0]['blocker_reason'], 'Event is blocked')
        self.assertIn('control_plane_remediation_execution_summary', out)

if __name__ == '__main__':
    unittest.main()
