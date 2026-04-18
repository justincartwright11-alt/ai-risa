import unittest
from workflows.control_plane_execution_pack import control_plane_execution_pack

def make_dispatch(**kwargs):
    return dict(kwargs)

class TestControlPlaneExecutionPack(unittest.TestCase):
    def setUp(self):
        self.dispatch = make_dispatch(
            control_plane_dispatch_status='partial',
            event_count=3,
            ready_event_names=['E1'],
            blocked_event_names=['E3'],
            dispatch_ready_actions=[
                {
                    'event_name': 'E1',
                    'event_status': 'ready',
                    'priority': 1,
                    'dispatch_batch': 'dispatch_proceed_batch',
                    'dispatch_reason': 'Proceed batch for ready events',
                    'next_action': 'proceed',
                    'next_reason': 'Ready to proceed',
                    'source_card': {'event_name': 'E1'},
                    'queue_snapshot': {'event_name': 'E1'}
                },
                {
                    'event_name': 'E2',
                    'event_status': 'partial',
                    'priority': 2,
                    'dispatch_batch': 'dispatch_review_batch',
                    'dispatch_reason': 'Review batch for operator review events',
                    'next_action': 'review',
                    'next_reason': 'Needs review',
                    'source_card': {'event_name': 'E2'},
                    'queue_snapshot': {'event_name': 'E2'}
                }
            ],
            blocked_dispatches=[
                {
                    'event_name': 'E3',
                    'event_status': 'blocked',
                    'priority': 3,
                    'blocker_reason': 'Event is blocked',
                    'queue_snapshot': {'event_name': 'E3'}
                }
            ],
            dispatch_batches={
                'dispatch_proceed_batch': [{'event_name': 'E1'}],
                'dispatch_review_batch': [{'event_name': 'E2'}],
                'dispatch_hold_batch': [],
                'dispatch_escalation_batch': []
            },
            priority_queue=['E1', 'E2'],
            escalation_queue=['E2', 'E3'],
            blocker_summary={'E3': 'Event is blocked'}
        )

    def test_execution_ready(self):
        d = dict(self.dispatch)
        d['dispatch_ready_actions'] = [dict(self.dispatch['dispatch_ready_actions'][0])]
        d['blocked_dispatches'] = []
        d['ready_event_names'] = ['E1']
        d['blocked_event_names'] = []
        out = control_plane_execution_pack(d)
        self.assertEqual(out['control_plane_execution_status'], 'ready')
        self.assertEqual(len(out['execution_ready_actions']), 1)
        self.assertEqual(out['execution_ready_actions'][0]['execution_batch'], 'execution_proceed_batch')
        self.assertEqual(out['execution_ready_actions'][0]['event_name'], 'E1')
        self.assertEqual(out['blocked_executions'], [])
        self.assertIn('execution_batches', out)
        self.assertIn('control_plane_execution_summary', out)

    def test_execution_partial(self):
        out = control_plane_execution_pack(self.dispatch)
        self.assertEqual(out['control_plane_execution_status'], 'partial')
        self.assertEqual(len(out['execution_ready_actions']), 2)
        self.assertEqual(out['execution_ready_actions'][0]['execution_batch'], 'execution_proceed_batch')
        self.assertEqual(out['execution_ready_actions'][1]['execution_batch'], 'execution_review_batch')
        self.assertEqual(len(out['blocked_executions']), 1)
        self.assertEqual(out['blocked_executions'][0]['event_name'], 'E3')
        self.assertEqual(out['blocked_executions'][0]['blocker_reason'], 'Event is blocked')
        self.assertIn('execution_batches', out)
        self.assertIn('control_plane_execution_summary', out)

    def test_execution_blocked(self):
        d = dict(self.dispatch)
        d['dispatch_ready_actions'] = []
        d['blocked_dispatches'] = [dict(self.dispatch['blocked_dispatches'][0])]
        d['ready_event_names'] = []
        d['blocked_event_names'] = ['E3']
        out = control_plane_execution_pack(d)
        self.assertEqual(out['control_plane_execution_status'], 'blocked')
        self.assertEqual(out['execution_ready_actions'], [])
        self.assertEqual(len(out['blocked_executions']), 1)
        self.assertEqual(out['blocked_executions'][0]['event_name'], 'E3')
        self.assertEqual(out['blocked_executions'][0]['blocker_reason'], 'Event is blocked')
        self.assertIn('execution_batches', out)
        self.assertIn('control_plane_execution_summary', out)

if __name__ == '__main__':
    unittest.main()
