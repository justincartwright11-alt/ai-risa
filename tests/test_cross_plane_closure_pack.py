import unittest
from copy import deepcopy
from workflows.cross_plane_closure_pack import cross_plane_closure_pack

def make_cp(**kwargs):
    return dict(kwargs)

def make_pf(**kwargs):
    return dict(kwargs)

def make_status(**kwargs):
    return dict(kwargs)

def make_policy(**kwargs):
    return dict(kwargs)

class TestCrossPlaneClosurePack(unittest.TestCase):
    def setUp(self):
        self.cp = make_cp(control_plane_closure='closure_ready')
        self.pf = make_pf(portfolio_closure='closure_ready')
        self.cp_closed = make_cp(control_plane_closure='closed')
        self.pf_closed = make_pf(portfolio_closure='closed')
        self.cp_blocked = make_cp(control_plane_closure='blocked')
        self.pf_blocked = make_pf(portfolio_closure='blocked')
        self.cp_escalated = make_cp(control_plane_closure='escalated')
        self.pf_escalated = make_pf(portfolio_closure='escalated')
        self.cp_unresolved = make_cp(control_plane_closure='unresolved')
        self.pf_unresolved = make_pf(portfolio_closure='unresolved')
        self.cp_partial = make_cp(control_plane_closure='partial')
        self.pf_partial = make_pf(portfolio_closure='partial')
        self.status_nominal = make_status(cross_plane_status_state='cross_nominal')
        self.status_blocked = make_status(cross_plane_status_state='cross_blocked')
        self.status_cp_blocked = make_status(cross_plane_status_state='control_plane_blocked')
        self.status_pf_blocked = make_status(cross_plane_status_state='portfolio_blocked')
        self.policy_nominal = make_policy(cross_plane_policy_state='cross_nominal')
        self.policy_blocked = make_policy(cross_plane_policy_state='cross_blocked')
        self.policy_cp_blocked = make_policy(cross_plane_policy_state='control_plane_blocked')
        self.policy_pf_blocked = make_policy(cross_plane_policy_state='portfolio_blocked')

    def test_happy_path(self):
        out = cross_plane_closure_pack(deepcopy(self.cp), deepcopy(self.pf), deepcopy(self.status_nominal), deepcopy(self.policy_nominal))
        self.assertEqual(out['cross_plane_closure_state'], 'cross_closure_ready')
        self.assertEqual(out['cross_plane_closure_source'], 'both')
        self.assertEqual(out['cross_plane_closure_reason'], 'Both lanes closure-ready/closed')
        self.assertEqual(out['cross_plane_closure_eligible'], True)
        self.assertEqual(out['cross_plane_closure_blocked'], False)
        self.assertEqual(out['control_plane_closure']['control_plane_closure'], 'closure_ready')
        self.assertEqual(out['portfolio_closure']['portfolio_closure'], 'closure_ready')
        self.assertEqual(out['cross_plane_status']['cross_plane_status_state'], 'cross_nominal')
        self.assertEqual(out['cross_plane_policy']['cross_plane_policy_state'], 'cross_nominal')

    def test_missing_required_upstream(self):
        with self.assertRaises(ValueError):
            cross_plane_closure_pack(None, self.pf, self.status_nominal, self.policy_nominal)
        with self.assertRaises(ValueError):
            cross_plane_closure_pack(self.cp, None, self.status_nominal, self.policy_nominal)
        with self.assertRaises(ValueError):
            cross_plane_closure_pack(self.cp, self.pf, None, self.policy_nominal)
        with self.assertRaises(ValueError):
            cross_plane_closure_pack(self.cp, self.pf, self.status_nominal, None)

    def test_precedence_both_blocked(self):
        out = cross_plane_closure_pack(self.cp_blocked, self.pf_blocked, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_closure_state'], 'cross_blocked')
        self.assertEqual(out['cross_plane_closure_source'], 'both')
        self.assertEqual(out['cross_plane_closure_blocked'], True)
        self.assertEqual(out['cross_plane_closure_reason'], 'Both lanes blocked/escalated/unresolved/not_ready')

    def test_precedence_control_plane_blocked(self):
        out = cross_plane_closure_pack(self.cp_blocked, self.pf, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_closure_state'], 'control_plane_blocked')
        self.assertEqual(out['cross_plane_closure_source'], 'control_plane')
        self.assertEqual(out['cross_plane_closure_blocked'], True)
        self.assertEqual(out['cross_plane_closure_reason'], 'Control-plane blocked/escalated/unresolved/not_ready')

    def test_precedence_portfolio_blocked(self):
        out = cross_plane_closure_pack(self.cp, self.pf_blocked, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_closure_state'], 'portfolio_blocked')
        self.assertEqual(out['cross_plane_closure_source'], 'portfolio')
        self.assertEqual(out['cross_plane_closure_blocked'], True)
        self.assertEqual(out['cross_plane_closure_reason'], 'Portfolio-plane blocked/escalated/unresolved/not_ready')

    def test_precedence_escalated(self):
        out = cross_plane_closure_pack(self.cp_escalated, self.pf, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_closure_state'], 'control_plane_blocked')
        out = cross_plane_closure_pack(self.cp, self.pf_escalated, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_closure_state'], 'portfolio_blocked')
        out = cross_plane_closure_pack(self.cp_escalated, self.pf_escalated, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_closure_state'], 'cross_blocked')

    def test_precedence_unresolved(self):
        out = cross_plane_closure_pack(self.cp_unresolved, self.pf, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_closure_state'], 'control_plane_blocked')
        out = cross_plane_closure_pack(self.cp, self.pf_unresolved, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_closure_state'], 'portfolio_blocked')
        out = cross_plane_closure_pack(self.cp_unresolved, self.pf_unresolved, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_closure_state'], 'cross_blocked')

    def test_precedence_partial(self):
        out = cross_plane_closure_pack(self.cp_partial, self.pf, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_closure_state'], 'control_plane_blocked')
        out = cross_plane_closure_pack(self.cp, self.pf_partial, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_closure_state'], 'portfolio_blocked')
        out = cross_plane_closure_pack(self.cp_partial, self.pf_partial, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_closure_state'], 'cross_blocked')

    def test_status_policy_precedence(self):
        out = cross_plane_closure_pack(self.cp, self.pf, self.status_blocked, self.policy_nominal)
        self.assertEqual(out['cross_plane_closure_state'], 'cross_blocked')
        self.assertEqual(out['cross_plane_closure_source'], 'status_policy')
        out = cross_plane_closure_pack(self.cp, self.pf, self.status_cp_blocked, self.policy_nominal)
        self.assertEqual(out['cross_plane_closure_state'], 'cross_blocked')
        self.assertEqual(out['cross_plane_closure_source'], 'status_policy')
        out = cross_plane_closure_pack(self.cp, self.pf, self.status_pf_blocked, self.policy_nominal)
        self.assertEqual(out['cross_plane_closure_state'], 'cross_blocked')
        self.assertEqual(out['cross_plane_closure_source'], 'status_policy')
        out = cross_plane_closure_pack(self.cp, self.pf, self.status_nominal, self.policy_blocked)
        self.assertEqual(out['cross_plane_closure_state'], 'cross_blocked')
        self.assertEqual(out['cross_plane_closure_source'], 'status_policy')
        out = cross_plane_closure_pack(self.cp, self.pf, self.status_nominal, self.policy_cp_blocked)
        self.assertEqual(out['cross_plane_closure_state'], 'cross_blocked')
        self.assertEqual(out['cross_plane_closure_source'], 'status_policy')
        out = cross_plane_closure_pack(self.cp, self.pf, self.status_nominal, self.policy_pf_blocked)
        self.assertEqual(out['cross_plane_closure_state'], 'cross_blocked')
        self.assertEqual(out['cross_plane_closure_source'], 'status_policy')

    def test_stable_output(self):
        out1 = cross_plane_closure_pack(self.cp, self.pf, self.status_nominal, self.policy_nominal)
        out2 = cross_plane_closure_pack(self.cp, self.pf, self.status_nominal, self.policy_nominal)
        self.assertEqual(out1, out2)

    def test_no_input_mutation(self):
        cp = deepcopy(self.cp)
        pf = deepcopy(self.pf)
        stat = deepcopy(self.status_nominal)
        pol = deepcopy(self.policy_nominal)
        _ = cross_plane_closure_pack(cp, pf, stat, pol)
        self.assertEqual(cp, self.cp)
        self.assertEqual(pf, self.pf)
        self.assertEqual(stat, self.status_nominal)
        self.assertEqual(pol, self.policy_nominal)

    def test_blocking_remains_visible(self):
        out = cross_plane_closure_pack(self.cp_blocked, self.pf, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_closure_blocked'], True)
        out = cross_plane_closure_pack(self.cp, self.pf_blocked, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_closure_blocked'], True)
        out = cross_plane_closure_pack(self.cp_blocked, self.pf_blocked, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_closure_blocked'], True)
        out = cross_plane_closure_pack(self.cp, self.pf, self.status_blocked, self.policy_nominal)
        self.assertEqual(out['cross_plane_closure_blocked'], True)
        out = cross_plane_closure_pack(self.cp, self.pf, self.status_nominal, self.policy_blocked)
        self.assertEqual(out['cross_plane_closure_blocked'], True)

    def test_clean_closure_ready(self):
        cp = make_cp(control_plane_closure='closure_ready')
        pf = make_pf(portfolio_closure='closure_ready')
        stat = make_status(cross_plane_status_state='cross_nominal')
        pol = make_policy(cross_plane_policy_state='cross_nominal')
        out = cross_plane_closure_pack(cp, pf, stat, pol)
        self.assertEqual(out['cross_plane_closure_state'], 'cross_closure_ready')
        self.assertEqual(out['cross_plane_closure_eligible'], True)
        self.assertEqual(out['cross_plane_closure_blocked'], False)

if __name__ == '__main__':
    unittest.main()
