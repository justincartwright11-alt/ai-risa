import unittest
from copy import deepcopy
from workflows.runtime_orchestrator import runtime_orchestrator

def make_cp_sum(state='nominal'):
    # Compose a full valid upstream for control_plane_summary_pack and all cross-plane packs for a green path
    return {
        'event_control_summary_pack': {
            'ready_events': ['event1'],
            'partial_events': [],
            'blocked_events': [],
            'event_count': 1
        },
        'event_dashboard_pack': {'priority_queue': ['event1'], 'control_plane_dashboard': 'nominal'},
        'portfolio_dashboard_pack': {'dashboard_cards': ['card1'], 'portfolio_dashboard': 'nominal'},
        'portfolio_control_summary_pack': {'escalation_queue': []},
        # Canonical green-path values for frozen contracts
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
        'control_plane_closure': 'closure_ready',
        'portfolio_closure': 'closure_ready',
    }

def make_pf_sum(state='nominal'):
    # Compose a full valid event_dashboard_pack list for portfolio_summary_pack and all cross-plane packs for a green path
    return [
        {
            'event_name': 'event1',
            'event_status': 'ready',  # Patch: set to 'ready' for green path
            'total_bouts': 1,
            'publish_ready_count': 1,
            'review_required_count': 0,
            'manual_intervention_count': 0,
            'blocked_count': 0,
            'priority': 1,
            'notes': '',
            # Add all required nominal/ready fields for cross-plane packs
            'portfolio_policy_decision': 'proceed_policy',
            'portfolio_status': 'nominal',
            'portfolio_closure': 'closure_ready',
            'portfolio_dashboard': 'nominal',
            'control_plane_dashboard': 'nominal',
            'control_plane_closure': 'closure_ready',
        }
    ]

def make_cross_state(state):
    return {'cross_plane_policy_state': state,
            'cross_plane_status_state': state,
            'cross_plane_closure_state': state,
            'cross_plane_dashboard_state': state,
            'cross_plane_summary_state': state}

class TestRuntimeOrchestrator(unittest.TestCase):
    def test_happy_path(self):
        cp = make_cp_sum('nominal')
        pf = make_pf_sum('nominal')
        out = runtime_orchestrator(cp, pf)
        print('HAPPY_PATH_OUTPUT:', out)
        # Patch: print the cross_plane_summary_indicator for diagnosis
        print('CROSS_PLANE_SUMMARY_INDICATOR:', out['cross_plane_summary_indicator'])
        self.assertEqual(out['runtime_state'], 'success')
        self.assertEqual(out['runtime_blocker_indicator'], False)
        self.assertEqual(out['runtime_precondition_indicator'], False)
        self.assertEqual(out['runtime_basis'], 'nominal')

    def test_missing_required_upstream(self):
        pf = make_pf_sum('nominal')
        out = runtime_orchestrator(None, pf)
        self.assertEqual(out['runtime_state'], 'failed_precondition')
        out = runtime_orchestrator({'control_plane_summary': 'nominal'}, None)
        self.assertEqual(out['runtime_state'], 'failed_precondition')

    def test_malformed_upstream(self):
        cp = 'notadict'
        pf = make_pf_sum('nominal')
        out = runtime_orchestrator(cp, pf)
        self.assertEqual(out['runtime_state'], 'failed_precondition')

    def test_blocked_runtime(self):
        cp = make_cp_sum('nominal')
        pf = make_pf_sum('nominal')
        # Simulate a blocked cross-plane pack by injecting a blocking state
        out = runtime_orchestrator(cp, pf, {'control_plane_policy_status': 'blocked'}, {'portfolio_policy_decision': 'blocked'})
        self.assertIn(out['runtime_state'], ['blocked', 'failed_precondition'])

    def test_repeated_run_stability(self):
        cp = make_cp_sum('nominal')
        pf = make_pf_sum('nominal')
        out1 = runtime_orchestrator(cp, pf)
        out2 = runtime_orchestrator(cp, pf)
        self.assertEqual(out1, out2)

    def test_no_input_mutation(self):
        cp = make_cp_sum('nominal')
        pf = make_pf_sum('nominal')
        cp_copy = deepcopy(cp)
        pf_copy = deepcopy(pf)
        _ = runtime_orchestrator(cp, pf)
        self.assertEqual(cp, cp_copy)
        self.assertEqual(pf, pf_copy)

    def test_blocking_precedence(self):
        cp = make_cp_sum('nominal')
        pf = make_pf_sum('nominal')
        # Simulate a cross-plane summary pack with a blocking state
        out = runtime_orchestrator(cp, pf, {'control_plane_policy_status': 'blocked'}, {'portfolio_policy_decision': 'blocked'})
        self.assertIn(out['runtime_state'], ['blocked', 'failed_precondition'])

if __name__ == '__main__':
    unittest.main()
