import unittest
from copy import deepcopy
from workflows.runtime_dispatch_adapter import runtime_dispatch_adapter

def make_dispatch_input():
    return {
        'control_plane_summary_input': {
            'event_control_summary_pack': {
                'ready_events': ['event1'],
                'partial_events': [],
                'blocked_events': [],
                'event_count': 1
            },
            'event_dashboard_pack': {'priority_queue': ['event1'], 'control_plane_dashboard': 'nominal'},
            'portfolio_dashboard_pack': {'dashboard_cards': ['card1'], 'portfolio_dashboard': 'nominal'},
            'portfolio_control_summary_pack': {'escalation_queue': []},
            'portfolio_governance_pack': {'portfolio_governance_status': 'nominal'},
            'portfolio_resolution_decision_pack': {'portfolio_resolution_decision_status': 'nominal'},
            'control_plane_policy_status': 'ready',
            'portfolio_policy_decision': 'proceed_policy',
            'control_plane_status': 'nominal',
            'portfolio_status': 'nominal',
            'control_plane_closure': 'closure_ready',
            'portfolio_closure': 'closure_ready',
            'control_plane_dashboard': 'nominal',
            'portfolio_dashboard': 'nominal',
        },
        'portfolio_summary_input': [
            {
                'event_name': 'event1',
                'event_status': 'ready',
                'total_bouts': 1,
                'publish_ready_count': 1,
                'review_required_count': 0,
                'manual_intervention_count': 0,
                'blocked_count': 0,
                'priority': 1,
                'notes': '',
                'portfolio_policy_decision': 'proceed_policy',
                'portfolio_status': 'nominal',
                'portfolio_closure': 'closure_ready',
                'portfolio_dashboard': 'nominal',
                'control_plane_dashboard': 'nominal',
                'control_plane_closure': 'closure_ready',
            }
        ]
    }

class TestRuntimeDispatchAdapter(unittest.TestCase):
    def test_happy_path(self):
        inp = make_dispatch_input()
        out = runtime_dispatch_adapter(inp)
        self.assertEqual(out['dispatch_state'], 'dispatched')
        self.assertEqual(out['runtime_state'], 'success')
        self.assertEqual(out['cross_plane_summary_indicator'], 'cross_nominal')
        self.assertFalse(out['dispatch_precondition_indicator'])
        self.assertFalse(out['dispatch_blocker_indicator'])
        self.assertEqual(out['dispatch_basis'], 'nominal')

    def test_missing_required_input(self):
        inp = {}
        out = runtime_dispatch_adapter(inp)
        self.assertEqual(out['dispatch_state'], 'failed_precondition')
        self.assertTrue(out['dispatch_precondition_indicator'])

    def test_malformed_input(self):
        inp = {'control_plane_summary_input': [], 'portfolio_summary_input': {}}
        out = runtime_dispatch_adapter(inp)
        self.assertEqual(out['dispatch_state'], 'failed_precondition')
        self.assertTrue(out['dispatch_precondition_indicator'])

    def test_blocked_adapter_result(self):
        inp = make_dispatch_input()
        # Block by injecting a blocked control_plane_policy_status
        inp2 = deepcopy(inp)
        inp2['control_plane_summary_input']['control_plane_policy_status'] = 'blocked'
        out = runtime_dispatch_adapter(inp2)
        self.assertEqual(out['dispatch_state'], 'blocked')
        self.assertEqual(out['runtime_state'], 'blocked')
        self.assertTrue(out['dispatch_blocker_indicator'])

    def test_repeated_run_stability(self):
        inp = make_dispatch_input()
        out1 = runtime_dispatch_adapter(inp)
        out2 = runtime_dispatch_adapter(inp)
        self.assertEqual(out1, out2)

    def test_no_input_mutation(self):
        inp = make_dispatch_input()
        inp_copy = deepcopy(inp)
        _ = runtime_dispatch_adapter(inp)
        self.assertEqual(inp, inp_copy)

    def test_semantic_preservation(self):
        inp = make_dispatch_input()
        # Blocked
        inp2 = deepcopy(inp)
        inp2['control_plane_summary_input']['control_plane_policy_status'] = 'blocked'
        out = runtime_dispatch_adapter(inp2)
        self.assertEqual(out['dispatch_state'], 'blocked')
        # Success
        out2 = runtime_dispatch_adapter(inp)
        self.assertEqual(out2['dispatch_state'], 'dispatched')
        # Precondition
        out3 = runtime_dispatch_adapter({'foo': 'bar'})
        self.assertEqual(out3['dispatch_state'], 'failed_precondition')

if __name__ == '__main__':
    unittest.main()
