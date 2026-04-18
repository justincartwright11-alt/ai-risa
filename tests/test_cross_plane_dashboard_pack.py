import unittest
from copy import deepcopy
from workflows.cross_plane_dashboard_pack import cross_plane_dashboard_pack

def make_cp(**kwargs):
    return dict(kwargs)

def make_pf(**kwargs):
    return dict(kwargs)

def make_closure(**kwargs):
    return dict(kwargs)

def make_status(**kwargs):
    return dict(kwargs)

def make_policy(**kwargs):
    return dict(kwargs)

class TestCrossPlaneDashboardPack(unittest.TestCase):
    def setUp(self):
        self.cp = make_cp(control_plane_dashboard='nominal')
        self.pf = make_pf(portfolio_dashboard='nominal')
        self.cp_blocked = make_cp(control_plane_dashboard='blocked')
        self.pf_blocked = make_pf(portfolio_dashboard='blocked')
        self.cp_escalated = make_cp(control_plane_dashboard='escalated')
        self.pf_escalated = make_pf(portfolio_dashboard='escalated')
        self.cp_degraded = make_cp(control_plane_dashboard='degraded')
        self.pf_degraded = make_pf(portfolio_dashboard='degraded')
        self.cp_partial = make_cp(control_plane_dashboard='partial')
        self.pf_partial = make_pf(portfolio_dashboard='partial')
        self.closure_nominal = make_closure(cross_plane_closure_state='cross_closure_ready')
        self.closure_blocked = make_closure(cross_plane_closure_state='cross_blocked')
        self.closure_cp_blocked = make_closure(cross_plane_closure_state='control_plane_blocked')
        self.closure_pf_blocked = make_closure(cross_plane_closure_state='portfolio_blocked')
        self.status_nominal = make_status(cross_plane_status_state='cross_nominal')
        self.status_blocked = make_status(cross_plane_status_state='cross_blocked')
        self.status_cp_blocked = make_status(cross_plane_status_state='control_plane_blocked')
        self.status_pf_blocked = make_status(cross_plane_status_state='portfolio_blocked')
        self.policy_nominal = make_policy(cross_plane_policy_state='cross_nominal')
        self.policy_blocked = make_policy(cross_plane_policy_state='cross_blocked')
        self.policy_cp_blocked = make_policy(cross_plane_policy_state='control_plane_blocked')
        self.policy_pf_blocked = make_policy(cross_plane_policy_state='portfolio_blocked')

    def test_happy_path(self):
        out = cross_plane_dashboard_pack(deepcopy(self.cp), deepcopy(self.pf), deepcopy(self.closure_nominal), deepcopy(self.status_nominal), deepcopy(self.policy_nominal))
        self.assertEqual(out['cross_plane_dashboard_state'], 'cross_nominal')
        self.assertEqual(out['cross_plane_dashboard_source'], 'both')
        self.assertEqual(out['cross_plane_dashboard_reason'], 'Both lanes nominal/clean')
        self.assertEqual(out['cross_plane_dashboard_blocked'], False)
        self.assertEqual(out['cross_plane_dashboard_escalated'], False)
        self.assertEqual(out['cross_plane_dashboard_nominal'], True)
        self.assertEqual(out['control_plane_dashboard']['control_plane_dashboard'], 'nominal')
        self.assertEqual(out['portfolio_dashboard']['portfolio_dashboard'], 'nominal')
        self.assertEqual(out['cross_plane_closure']['cross_plane_closure_state'], 'cross_closure_ready')
        self.assertEqual(out['cross_plane_status']['cross_plane_status_state'], 'cross_nominal')
        self.assertEqual(out['cross_plane_policy']['cross_plane_policy_state'], 'cross_nominal')

    def test_missing_required_upstream(self):
        with self.assertRaises(ValueError):
            cross_plane_dashboard_pack(None, self.pf, self.closure_nominal, self.status_nominal, self.policy_nominal)
        with self.assertRaises(ValueError):
            cross_plane_dashboard_pack(self.cp, None, self.closure_nominal, self.status_nominal, self.policy_nominal)
        with self.assertRaises(ValueError):
            cross_plane_dashboard_pack(self.cp, self.pf, None, self.status_nominal, self.policy_nominal)
        with self.assertRaises(ValueError):
            cross_plane_dashboard_pack(self.cp, self.pf, self.closure_nominal, None, self.policy_nominal)
        with self.assertRaises(ValueError):
            cross_plane_dashboard_pack(self.cp, self.pf, self.closure_nominal, self.status_nominal, None)

    def test_precedence_both_blocked(self):
        out = cross_plane_dashboard_pack(self.cp_blocked, self.pf_blocked, self.closure_nominal, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_dashboard_state'], 'cross_blocked')
        self.assertEqual(out['cross_plane_dashboard_source'], 'both')
        self.assertEqual(out['cross_plane_dashboard_blocked'], True)
        self.assertEqual(out['cross_plane_dashboard_reason'], 'Both lanes blocked/escalated/unresolved/degraded/not_ready')

    def test_precedence_control_plane_blocked(self):
        out = cross_plane_dashboard_pack(self.cp_blocked, self.pf, self.closure_nominal, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_dashboard_state'], 'control_plane_blocked')
        self.assertEqual(out['cross_plane_dashboard_source'], 'control_plane')
        self.assertEqual(out['cross_plane_dashboard_blocked'], True)
        self.assertEqual(out['cross_plane_dashboard_reason'], 'Control-plane blocked/escalated/unresolved/degraded/not_ready')

    def test_precedence_portfolio_blocked(self):
        out = cross_plane_dashboard_pack(self.cp, self.pf_blocked, self.closure_nominal, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_dashboard_state'], 'portfolio_blocked')
        self.assertEqual(out['cross_plane_dashboard_source'], 'portfolio')
        self.assertEqual(out['cross_plane_dashboard_blocked'], True)
        self.assertEqual(out['cross_plane_dashboard_reason'], 'Portfolio-plane blocked/escalated/unresolved/degraded/not_ready')

    def test_precedence_escalated(self):
        out = cross_plane_dashboard_pack(self.cp_escalated, self.pf, self.closure_nominal, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_dashboard_state'], 'control_plane_blocked')
        out = cross_plane_dashboard_pack(self.cp, self.pf_escalated, self.closure_nominal, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_dashboard_state'], 'portfolio_blocked')
        out = cross_plane_dashboard_pack(self.cp_escalated, self.pf_escalated, self.closure_nominal, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_dashboard_state'], 'cross_blocked')

    def test_precedence_degraded(self):
        out = cross_plane_dashboard_pack(self.cp_degraded, self.pf, self.closure_nominal, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_dashboard_state'], 'control_plane_blocked')
        out = cross_plane_dashboard_pack(self.cp, self.pf_degraded, self.closure_nominal, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_dashboard_state'], 'portfolio_blocked')
        out = cross_plane_dashboard_pack(self.cp_degraded, self.pf_degraded, self.closure_nominal, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_dashboard_state'], 'cross_blocked')

    def test_precedence_partial(self):
        out = cross_plane_dashboard_pack(self.cp_partial, self.pf, self.closure_nominal, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_dashboard_state'], 'control_plane_blocked')
        out = cross_plane_dashboard_pack(self.cp, self.pf_partial, self.closure_nominal, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_dashboard_state'], 'portfolio_blocked')
        out = cross_plane_dashboard_pack(self.cp_partial, self.pf_partial, self.closure_nominal, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_dashboard_state'], 'cross_blocked')

    def test_closure_status_policy_precedence(self):
        out = cross_plane_dashboard_pack(self.cp, self.pf, self.closure_blocked, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_dashboard_state'], 'cross_blocked')
        self.assertEqual(out['cross_plane_dashboard_source'], 'closure_status_policy')
        out = cross_plane_dashboard_pack(self.cp, self.pf, self.closure_cp_blocked, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_dashboard_state'], 'cross_blocked')
        self.assertEqual(out['cross_plane_dashboard_source'], 'closure_status_policy')
        out = cross_plane_dashboard_pack(self.cp, self.pf, self.closure_pf_blocked, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_dashboard_state'], 'cross_blocked')
        self.assertEqual(out['cross_plane_dashboard_source'], 'closure_status_policy')
        out = cross_plane_dashboard_pack(self.cp, self.pf, self.closure_nominal, self.status_blocked, self.policy_nominal)
        self.assertEqual(out['cross_plane_dashboard_state'], 'cross_blocked')
        self.assertEqual(out['cross_plane_dashboard_source'], 'closure_status_policy')
        out = cross_plane_dashboard_pack(self.cp, self.pf, self.closure_nominal, self.status_cp_blocked, self.policy_nominal)
        self.assertEqual(out['cross_plane_dashboard_state'], 'cross_blocked')
        self.assertEqual(out['cross_plane_dashboard_source'], 'closure_status_policy')
        out = cross_plane_dashboard_pack(self.cp, self.pf, self.closure_nominal, self.status_pf_blocked, self.policy_nominal)
        self.assertEqual(out['cross_plane_dashboard_state'], 'cross_blocked')
        self.assertEqual(out['cross_plane_dashboard_source'], 'closure_status_policy')
        out = cross_plane_dashboard_pack(self.cp, self.pf, self.closure_nominal, self.status_nominal, self.policy_blocked)
        self.assertEqual(out['cross_plane_dashboard_state'], 'cross_blocked')
        self.assertEqual(out['cross_plane_dashboard_source'], 'closure_status_policy')
        out = cross_plane_dashboard_pack(self.cp, self.pf, self.closure_nominal, self.status_nominal, self.policy_cp_blocked)
        self.assertEqual(out['cross_plane_dashboard_state'], 'cross_blocked')
        self.assertEqual(out['cross_plane_dashboard_source'], 'closure_status_policy')
        out = cross_plane_dashboard_pack(self.cp, self.pf, self.closure_nominal, self.status_nominal, self.policy_pf_blocked)
        self.assertEqual(out['cross_plane_dashboard_state'], 'cross_blocked')
        self.assertEqual(out['cross_plane_dashboard_source'], 'closure_status_policy')

    def test_stable_output(self):
        out1 = cross_plane_dashboard_pack(self.cp, self.pf, self.closure_nominal, self.status_nominal, self.policy_nominal)
        out2 = cross_plane_dashboard_pack(self.cp, self.pf, self.closure_nominal, self.status_nominal, self.policy_nominal)
        self.assertEqual(out1, out2)

    def test_no_input_mutation(self):
        cp = deepcopy(self.cp)
        pf = deepcopy(self.pf)
        clo = deepcopy(self.closure_nominal)
        stat = deepcopy(self.status_nominal)
        pol = deepcopy(self.policy_nominal)
        _ = cross_plane_dashboard_pack(cp, pf, clo, stat, pol)
        self.assertEqual(cp, self.cp)
        self.assertEqual(pf, self.pf)
        self.assertEqual(clo, self.closure_nominal)
        self.assertEqual(stat, self.status_nominal)
        self.assertEqual(pol, self.policy_nominal)

    def test_blocking_remains_visible(self):
        out = cross_plane_dashboard_pack(self.cp_blocked, self.pf, self.closure_nominal, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_dashboard_blocked'], True)
        out = cross_plane_dashboard_pack(self.cp, self.pf_blocked, self.closure_nominal, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_dashboard_blocked'], True)
        out = cross_plane_dashboard_pack(self.cp_blocked, self.pf_blocked, self.closure_nominal, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_dashboard_blocked'], True)
        out = cross_plane_dashboard_pack(self.cp, self.pf, self.closure_blocked, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_dashboard_blocked'], True)
        out = cross_plane_dashboard_pack(self.cp, self.pf, self.closure_nominal, self.status_blocked, self.policy_nominal)
        self.assertEqual(out['cross_plane_dashboard_blocked'], True)
        out = cross_plane_dashboard_pack(self.cp, self.pf, self.closure_nominal, self.status_nominal, self.policy_blocked)
        self.assertEqual(out['cross_plane_dashboard_blocked'], True)

    def test_clean_nominal(self):
        cp = make_cp(control_plane_dashboard='nominal')
        pf = make_pf(portfolio_dashboard='nominal')
        clo = make_closure(cross_plane_closure_state='cross_closure_ready')
        stat = make_status(cross_plane_status_state='cross_nominal')
        pol = make_policy(cross_plane_policy_state='cross_nominal')
        out = cross_plane_dashboard_pack(cp, pf, clo, stat, pol)
        self.assertEqual(out['cross_plane_dashboard_state'], 'cross_nominal')
        self.assertEqual(out['cross_plane_dashboard_blocked'], False)
        self.assertEqual(out['cross_plane_dashboard_nominal'], True)

if __name__ == '__main__':
    unittest.main()
