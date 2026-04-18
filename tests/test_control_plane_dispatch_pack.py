import unittest
from workflows.control_plane_dispatch_pack import control_plane_dispatch_pack

def make_queue(**kwargs):
    return dict(kwargs)

class TestControlPlaneDispatchPack(unittest.TestCase):
    def setUp(self):
        self.queue = make_queue(
            control_plane_action_queue_status='partial',
            event_count=3,
            ready_event_names=['E1'],
            blocked_event_names=['E3'],
            queued_actions=[
                {
                    'event_name': 'E1',
                    'event_status': 'ready',
                    'priority': 1,
                    'queue_action': 'queue_proceed',
                    'queue_reason': 'Event ready to proceed',
                    'next_action': 'proceed',
                    'next_reason': 'Ready to proceed',
                    'source_card': {'event_name': 'E1'},
                },
                {
                    'event_name': 'E2',
                    'event_status': 'partial',
                    'priority': 2,
                    'queue_action': 'queue_review',
                    'queue_reason': 'Event requires operator review',
                    'next_action': 'review',
                    'next_reason': 'Needs review',
                    'source_card': {'event_name': 'E2'},
                }
            ],
            blocked_actions=[
                {
                    'event_name': 'E3',
                    'event_status': 'blocked',
                    'priority': 3,
                    'blocker_reason': 'Event is blocked',
                    'source_card': {'event_name': 'E3'},
                }
            ],
            priority_queue=['E1', 'E2'],
            escalation_queue=['E2', 'E3'],
            blocker_summary={'E3': 'Event is blocked'}
        )

    def test_dispatch_ready(self):
        q = dict(self.queue)
        q['queued_actions'] = [dict(self.queue['queued_actions'][0])]
        q['blocked_actions'] = []
        q['ready_event_names'] = ['E1']
        q['blocked_event_names'] = []
        out = control_plane_dispatch_pack(q)
        self.assertEqual(out['control_plane_dispatch_status'], 'ready')
        self.assertEqual(len(out['dispatch_ready_actions']), 1)
        self.assertEqual(out['dispatch_ready_actions'][0]['dispatch_batch'], 'dispatch_proceed_batch')
        self.assertEqual(out['dispatch_ready_actions'][0]['event_name'], 'E1')
        self.assertEqual(out['blocked_dispatches'], [])
        self.assertIn('dispatch_batches', out)
        self.assertIn('control_plane_dispatch_summary', out)

    def test_dispatch_partial(self):
        out = control_plane_dispatch_pack(self.queue)
        self.assertEqual(out['control_plane_dispatch_status'], 'partial')
        self.assertEqual(len(out['dispatch_ready_actions']), 2)
        self.assertEqual(out['dispatch_ready_actions'][0]['dispatch_batch'], 'dispatch_proceed_batch')
        self.assertEqual(out['dispatch_ready_actions'][1]['dispatch_batch'], 'dispatch_review_batch')
        self.assertEqual(len(out['blocked_dispatches']), 1)
        self.assertEqual(out['blocked_dispatches'][0]['event_name'], 'E3')
        self.assertEqual(out['blocked_dispatches'][0]['blocker_reason'], 'Event is blocked')
        self.assertIn('dispatch_batches', out)
        self.assertIn('control_plane_dispatch_summary', out)

    def test_dispatch_blocked(self):
        q = dict(self.queue)
        q['queued_actions'] = []
        q['blocked_actions'] = [dict(self.queue['blocked_actions'][0])]
        q['ready_event_names'] = []
        q['blocked_event_names'] = ['E3']
        out = control_plane_dispatch_pack(q)
        self.assertEqual(out['control_plane_dispatch_status'], 'blocked')
        self.assertEqual(out['dispatch_ready_actions'], [])
        self.assertEqual(len(out['blocked_dispatches']), 1)
        self.assertEqual(out['blocked_dispatches'][0]['event_name'], 'E3')
        self.assertEqual(out['blocked_dispatches'][0]['blocker_reason'], 'Event is blocked')
        self.assertIn('dispatch_batches', out)
        self.assertIn('control_plane_dispatch_summary', out)

if __name__ == '__main__':
    unittest.main()
