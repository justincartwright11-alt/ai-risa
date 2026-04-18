import unittest
from copy import deepcopy
from workflows.operator_runtime_entrypoint import operator_runtime_entrypoint

class TestOperatorRuntimeEntrypoint(unittest.TestCase):
    def setUp(self):
        # Canonical payload for dispatch adapter happy path
        self.valid_request = {
            'operator_id': 'op123',
            'operator_action': 'run',
            'operator_payload': {
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
        }

    def test_happy_path_accepted(self):
        req = deepcopy(self.valid_request)
        result = operator_runtime_entrypoint(req)
        self.assertEqual(result['operator_request_state'], 'accepted')
        self.assertFalse(result['operator_precondition_indicator'])
        self.assertFalse(result['operator_blocker_indicator'])
        self.assertIn('runtime_state', result)
        self.assertIn('runtime_result', result)
        self.assertIn('cross_plane_summary_indicator', result)

    def test_missing_required_input_failed_precondition(self):
        req = deepcopy(self.valid_request)
        del req['operator_id']
        result = operator_runtime_entrypoint(req)
        self.assertEqual(result['operator_request_state'], 'failed_precondition')
        self.assertTrue(result['operator_precondition_indicator'])
        self.assertFalse(result['operator_blocker_indicator'])

    def test_malformed_input_failed_precondition(self):
        req = 'not a dict'
        result = operator_runtime_entrypoint(req)
        self.assertEqual(result['operator_request_state'], 'failed_precondition')
        self.assertTrue(result['operator_precondition_indicator'])
        self.assertFalse(result['operator_blocker_indicator'])

    def test_blocked_entrypoint_result(self):
        req = deepcopy(self.valid_request)
        req['operator_payload']['force_blocked'] = True
        # Patch the adapter to simulate blocked
        from workflows import operator_runtime_entrypoint as entry_mod
        orig_invoke_adapter = entry_mod._invoke_adapter
        def fake_blocked_adapter(_):
            return {'runtime_state': 'blocked', 'runtime_result': 'Blocked by test', 'runtime_blocker_indicator': True}
        entry_mod._invoke_adapter = fake_blocked_adapter
        result = operator_runtime_entrypoint(req)
        self.assertEqual(result['operator_request_state'], 'blocked')
        self.assertFalse(result['operator_precondition_indicator'])
        self.assertTrue(result['operator_blocker_indicator'])
        entry_mod._invoke_adapter = orig_invoke_adapter

    def test_repeated_run_stability(self):
        req = deepcopy(self.valid_request)
        result1 = operator_runtime_entrypoint(req)
        result2 = operator_runtime_entrypoint(req)
        self.assertEqual(result1, result2)

    def test_no_mutation_of_caller_input(self):
        req = deepcopy(self.valid_request)
        req_copy = deepcopy(req)
        operator_runtime_entrypoint(req)
        self.assertEqual(req, req_copy)

    def test_semantic_preservation(self):
        req = deepcopy(self.valid_request)
        # Patch the adapter to simulate failed_precondition
        from workflows import operator_runtime_entrypoint as entry_mod
        orig_invoke_adapter = entry_mod._invoke_adapter
        def fake_precond_adapter(_):
            return {'runtime_state': 'failed_precondition', 'runtime_result': 'Adapter precondition fail'}
        entry_mod._invoke_adapter = fake_precond_adapter
        result = operator_runtime_entrypoint(req)
        self.assertEqual(result['operator_request_state'], 'failed_precondition')
        self.assertTrue(result['operator_precondition_indicator'])
        self.assertFalse(result['operator_blocker_indicator'])
        entry_mod._invoke_adapter = orig_invoke_adapter

if __name__ == '__main__':
    unittest.main()
