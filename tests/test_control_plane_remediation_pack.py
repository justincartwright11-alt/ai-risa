import unittest
from workflows.control_plane_remediation_pack import control_plane_remediation_pack

def make_followup(**kwargs):
    return dict(kwargs)

class TestControlPlaneRemediationPack(unittest.TestCase):
    def setUp(self):
        self.followup = make_followup(
            control_plane_followup_status='partial',
            event_count=3,
            ready_event_names=['E1'],
            blocked_event_names=['E3'],
            followup_actions=[
                {
                    'event_name': 'E1',
                    'event_status': 'ready',
                    'priority': 1,
                    'followup_action': 'proceed_followup',
                    'followup_reason': 'Ready for follow-up proceed',
                    'escalation_level': 0,
                    'source_card': {'event_name': 'E1'},
                },
                {
                    'event_name': 'E2',
                    'event_status': 'partial',
                    'priority': 2,
                    'followup_action': 'review_followup',
                    'followup_reason': 'Requires operator review follow-up',
                    'escalation_level': 1,
                    'source_card': {'event_name': 'E2'},
                }
            ],
            blocked_followups=[
                {
                    'event_name': 'E3',
                    'event_status': 'blocked',
                    'priority': 3,
                    'blocker_reason': 'Event is blocked',
                    'reconciliation_snapshot': {'event_name': 'E3'}
                }
            ],
            priority_queue=['E1', 'E2'],
            escalation_queue=['E2', 'E3'],
            blocker_summary={'E3': 'Event is blocked'},
            control_plane_followup_summary={
                'followup_status': 'partial',
                'event_count': 3,
                'followup_count': 2,
                'blocked_followup_count': 1,
                'ready_event_names': ['E1'],
                'blocked_event_names': ['E3'],
                'priority_queue': ['E1', 'E2'],
                'escalation_queue': ['E2', 'E3'],
                'blocker_summary': {'E3': 'Event is blocked'}
            }
        )

    def test_remediation_ready(self):
        o = dict(self.followup)
        o['followup_actions'] = [dict(self.followup['followup_actions'][0])]
        o['blocked_followups'] = []
        o['ready_event_names'] = ['E1']
        o['blocked_event_names'] = []
        out = control_plane_remediation_pack(o)
        self.assertEqual(out['control_plane_remediation_status'], 'ready')
        self.assertEqual(len(out['remediation_actions']), 1)
        self.assertEqual(out['remediation_actions'][0]['remediation_action'], 'remediate_proceed')
        self.assertEqual(out['remediation_actions'][0]['event_name'], 'E1')
        self.assertEqual(out['blocked_remediations'], [])
        self.assertIn('control_plane_remediation_summary', out)

    def test_remediation_partial(self):
        out = control_plane_remediation_pack(self.followup)
        self.assertEqual(out['control_plane_remediation_status'], 'partial')
        self.assertEqual(len(out['remediation_actions']), 2)
        self.assertEqual(out['remediation_actions'][0]['remediation_action'], 'remediate_proceed')
        self.assertEqual(out['remediation_actions'][1]['remediation_action'], 'remediate_review')
        self.assertEqual(len(out['blocked_remediations']), 1)
        self.assertEqual(out['blocked_remediations'][0]['event_name'], 'E3')
        self.assertEqual(out['blocked_remediations'][0]['blocker_reason'], 'Event is blocked')
        self.assertIn('control_plane_remediation_summary', out)

    def test_remediation_blocked(self):
        o = dict(self.followup)
        o['followup_actions'] = []
        o['blocked_followups'] = [dict(self.followup['blocked_followups'][0])]
        o['ready_event_names'] = []
        o['blocked_event_names'] = ['E3']
        out = control_plane_remediation_pack(o)
        self.assertEqual(out['control_plane_remediation_status'], 'blocked')
        self.assertEqual(out['remediation_actions'], [])
        self.assertEqual(len(out['blocked_remediations']), 1)
        self.assertEqual(out['blocked_remediations'][0]['event_name'], 'E3')
        self.assertEqual(out['blocked_remediations'][0]['blocker_reason'], 'Event is blocked')
        self.assertIn('control_plane_remediation_summary', out)

if __name__ == '__main__':
    unittest.main()
