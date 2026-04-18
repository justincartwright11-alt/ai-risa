import unittest
from copy import deepcopy
from workflows.cross_plane_status_pack import cross_plane_status_pack

def make_cp(**kwargs):
    return dict(kwargs)

def make_pf(**kwargs):
    return dict(kwargs)

def make_policy(**kwargs):
    return dict(kwargs)

class TestCrossPlaneStatusPack(unittest.TestCase):
    def setUp(self):
        self.cp = make_cp(control_plane_status='nominal')
        self.pf = make_pf(portfolio_status='nominal')
        self.cp_blocked = make_cp(control_plane_status='blocked')
        self.pf_blocked = make_pf(portfolio_status='blocked')
        self.cp_escalated = make_cp(control_plane_status='escalated')
        self.pf_escalated = make_pf(portfolio_status='escalated')
        self.cp_degraded = make_cp(control_plane_status='degraded')
        self.pf_degraded = make_pf(portfolio_status='degraded')
        self.cp_partial = make_cp(control_plane_status='partial')
        self.pf_partial = make_pf(portfolio_status='partial')
        self.policy_nominal = make_policy(cross_plane_policy_state='cross_nominal')
        self.policy_blocked = make_policy(cross_plane_policy_state='cross_blocked')
        self.policy_cp_blocked = make_policy(cross_plane_policy_state='control_plane_blocked')
        self.policy_pf_blocked = make_policy(cross_plane_policy_state='portfolio_blocked')

    def test_happy_path(self):
        out = cross_plane_status_pack(deepcopy(self.cp), deepcopy(self.pf), deepcopy(self.policy_nominal))
        self.assertEqual(out['cross_plane_status_state'], 'cross_nominal')
        self.assertEqual(out['cross_plane_status_source'], 'both')
        self.assertEqual(out['cross_plane_status_reason'], 'Both lanes nominal/clean')
        self.assertEqual(out['cross_plane_status_eligible'], True)
        self.assertEqual(out['cross_plane_status_blocked'], False)
        self.assertEqual(out['control_plane_status']['control_plane_status'], 'nominal')
        self.assertEqual(out['portfolio_status']['portfolio_status'], 'nominal')
        self.assertEqual(out['cross_plane_policy']['cross_plane_policy_state'], 'cross_nominal')

    def test_missing_required_upstream(self):
        with self.assertRaises(ValueError):
            cross_plane_status_pack(None, self.pf, self.policy_nominal)
        with self.assertRaises(ValueError):
            cross_plane_status_pack(self.cp, None, self.policy_nominal)
        with self.assertRaises(ValueError):
            cross_plane_status_pack(self.cp, self.pf, None)

    def test_precedence_both_blocked(self):
        out = cross_plane_status_pack(self.cp_blocked, self.pf_blocked, self.policy_nominal)
        self.assertEqual(out['cross_plane_status_state'], 'cross_blocked')
        self.assertEqual(out['cross_plane_status_source'], 'both')
        self.assertEqual(out['cross_plane_status_blocked'], True)
        self.assertEqual(out['cross_plane_status_reason'], 'Both lanes blocked/escalated/degraded/unresolved')

    def test_precedence_control_plane_blocked(self):
        out = cross_plane_status_pack(self.cp_blocked, self.pf, self.policy_nominal)
        self.assertEqual(out['cross_plane_status_state'], 'control_plane_blocked')
        self.assertEqual(out['cross_plane_status_source'], 'control_plane')
        self.assertEqual(out['cross_plane_status_blocked'], True)
        self.assertEqual(out['cross_plane_status_reason'], 'Control-plane blocked/escalated/degraded/unresolved')

    def test_precedence_portfolio_blocked(self):
        out = cross_plane_status_pack(self.cp, self.pf_blocked, self.policy_nominal)
        self.assertEqual(out['cross_plane_status_state'], 'portfolio_blocked')
        self.assertEqual(out['cross_plane_status_source'], 'portfolio')
        self.assertEqual(out['cross_plane_status_blocked'], True)
        self.assertEqual(out['cross_plane_status_reason'], 'Portfolio-plane blocked/escalated/degraded/unresolved')

    def test_precedence_escalated(self):
        out = cross_plane_status_pack(self.cp_escalated, self.pf, self.policy_nominal)
        self.assertEqual(out['cross_plane_status_state'], 'control_plane_blocked')
        out = cross_plane_status_pack(self.cp, self.pf_escalated, self.policy_nominal)
        self.assertEqual(out['cross_plane_status_state'], 'portfolio_blocked')
        out = cross_plane_status_pack(self.cp_escalated, self.pf_escalated, self.policy_nominal)
        self.assertEqual(out['cross_plane_status_state'], 'cross_blocked')

    def test_precedence_degraded(self):
        out = cross_plane_status_pack(self.cp_degraded, self.pf, self.policy_nominal)
        self.assertEqual(out['cross_plane_status_state'], 'control_plane_blocked')
        out = cross_plane_status_pack(self.cp, self.pf_degraded, self.policy_nominal)
        self.assertEqual(out['cross_plane_status_state'], 'portfolio_blocked')
        out = cross_plane_status_pack(self.cp_degraded, self.pf_degraded, self.policy_nominal)
        self.assertEqual(out['cross_plane_status_state'], 'cross_blocked')

    def test_precedence_partial(self):
        out = cross_plane_status_pack(self.cp_partial, self.pf, self.policy_nominal)
        self.assertEqual(out['cross_plane_status_state'], 'control_plane_blocked')
        out = cross_plane_status_pack(self.cp, self.pf_partial, self.policy_nominal)
        self.assertEqual(out['cross_plane_status_state'], 'portfolio_blocked')
        out = cross_plane_status_pack(self.cp_partial, self.pf_partial, self.policy_nominal)
        self.assertEqual(out['cross_plane_status_state'], 'cross_blocked')

    def test_policy_precedence(self):
        out = cross_plane_status_pack(self.cp, self.pf, self.policy_blocked)
        self.assertEqual(out['cross_plane_status_state'], 'cross_blocked')
        self.assertEqual(out['cross_plane_status_source'], 'policy')
        out = cross_plane_status_pack(self.cp, self.pf, self.policy_cp_blocked)
        self.assertEqual(out['cross_plane_status_state'], 'cross_blocked')
        self.assertEqual(out['cross_plane_status_source'], 'policy')
        out = cross_plane_status_pack(self.cp, self.pf, self.policy_pf_blocked)
        self.assertEqual(out['cross_plane_status_state'], 'cross_blocked')
        self.assertEqual(out['cross_plane_status_source'], 'policy')

    def test_stable_output(self):
        out1 = cross_plane_status_pack(self.cp, self.pf, self.policy_nominal)
        out2 = cross_plane_status_pack(self.cp, self.pf, self.policy_nominal)
        self.assertEqual(out1, out2)

    def test_no_input_mutation(self):
        cp = deepcopy(self.cp)
        pf = deepcopy(self.pf)
        pol = deepcopy(self.policy_nominal)
        _ = cross_plane_status_pack(cp, pf, pol)
        self.assertEqual(cp, self.cp)
        self.assertEqual(pf, self.pf)
        self.assertEqual(pol, self.policy_nominal)

    def test_blocking_remains_visible(self):
        out = cross_plane_status_pack(self.cp_blocked, self.pf, self.policy_nominal)
        self.assertEqual(out['cross_plane_status_blocked'], True)
        out = cross_plane_status_pack(self.cp, self.pf_blocked, self.policy_nominal)
        self.assertEqual(out['cross_plane_status_blocked'], True)
        out = cross_plane_status_pack(self.cp_blocked, self.pf_blocked, self.policy_nominal)
        self.assertEqual(out['cross_plane_status_blocked'], True)
        out = cross_plane_status_pack(self.cp, self.pf, self.policy_blocked)
        self.assertEqual(out['cross_plane_status_blocked'], True)

    def test_clean_nominal(self):
        cp = make_cp(control_plane_status='nominal')
        pf = make_pf(portfolio_status='nominal')
        pol = make_policy(cross_plane_policy_state='cross_nominal')
        out = cross_plane_status_pack(cp, pf, pol)
        self.assertEqual(out['cross_plane_status_state'], 'cross_nominal')
        self.assertEqual(out['cross_plane_status_eligible'], True)
        self.assertEqual(out['cross_plane_status_blocked'], False)

if __name__ == '__main__':
    unittest.main()
