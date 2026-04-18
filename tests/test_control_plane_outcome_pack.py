import unittest
from workflows.control_plane_outcome_pack import control_plane_outcome_pack

def make_execution(**kwargs):
    return dict(kwargs)

class TestControlPlaneOutcomePack(unittest.TestCase):
    def setUp(self):
        self.execution = make_execution(
            control_plane_execution_status='partial',
            event_count=3,
            ready_event_names=['E1'],
            blocked_event_names=['E3'],
            execution_ready_actions=[
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
                    'source_card': {'event_name': 'E2'},
                }
            ],
            blocked_executions=[
                {
                    'event_name': 'E3',
                    'event_status': 'blocked',
                    'priority': 3,
                    'blocker_reason': 'Event is blocked',
                    'queue_snapshot': {'event_name': 'E3'}
                }
            ],
            execution_batches={
                'execution_proceed_batch': [{'event_name': 'E1'}],
                'execution_review_batch': [{'event_name': 'E2'}],
                'execution_hold_batch': [],
                'execution_escalation_batch': []
            },
            priority_queue=['E1', 'E2'],
            escalation_queue=['E2', 'E3'],
            blocker_summary={'E3': 'Event is blocked'}
        )

    def test_outcome_ready(self):
        e = dict(self.execution)
        e['execution_ready_actions'] = [dict(self.execution['execution_ready_actions'][0])]
        e['blocked_executions'] = []
        e['ready_event_names'] = ['E1']
        e['blocked_event_names'] = []
        out = control_plane_outcome_pack(e)
        self.assertEqual(out['control_plane_outcome_status'], 'ready')
        self.assertEqual(len(out['completed_actions']), 1)
        self.assertEqual(out['completed_actions'][0]['outcome_batch'], 'complete_proceed_batch')
        self.assertEqual(out['completed_actions'][0]['event_name'], 'E1')
        self.assertEqual(out['blocked_outcomes'], [])
        self.assertIn('outcome_batches', out)
        self.assertIn('control_plane_outcome_summary', out)

    def test_outcome_partial(self):
        out = control_plane_outcome_pack(self.execution)
        self.assertEqual(out['control_plane_outcome_status'], 'partial')
        self.assertEqual(len(out['completed_actions']), 2)
        self.assertEqual(out['completed_actions'][0]['outcome_batch'], 'complete_proceed_batch')
        self.assertEqual(out['completed_actions'][1]['outcome_batch'], 'complete_review_batch')
        self.assertEqual(len(out['blocked_outcomes']), 1)
        self.assertEqual(out['blocked_outcomes'][0]['event_name'], 'E3')
        self.assertEqual(out['blocked_outcomes'][0]['blocker_reason'], 'Event is blocked')
        self.assertIn('outcome_batches', out)
        self.assertIn('control_plane_outcome_summary', out)

    def test_outcome_blocked(self):
        e = dict(self.execution)
        e['execution_ready_actions'] = []
        e['blocked_executions'] = [dict(self.execution['blocked_executions'][0])]
        e['ready_event_names'] = []
        e['blocked_event_names'] = ['E3']
        out = control_plane_outcome_pack(e)
        self.assertEqual(out['control_plane_outcome_status'], 'blocked')
        self.assertEqual(out['completed_actions'], [])
        self.assertEqual(len(out['blocked_outcomes']), 1)
        self.assertEqual(out['blocked_outcomes'][0]['event_name'], 'E3')
        self.assertEqual(out['blocked_outcomes'][0]['blocker_reason'], 'Event is blocked')
        self.assertIn('outcome_batches', out)
        self.assertIn('control_plane_outcome_summary', out)

if __name__ == '__main__':
    unittest.main()
