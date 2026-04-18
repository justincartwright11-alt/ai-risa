import unittest
from copy import deepcopy
from workflows.cross_plane_summary_pack import cross_plane_summary_pack

def make_cp(**kwargs):
    return dict(kwargs)

def make_pf(**kwargs):
    return dict(kwargs)

def make_dash(**kwargs):
    return dict(kwargs)

def make_closure(**kwargs):
    return dict(kwargs)

def make_status(**kwargs):
    return dict(kwargs)

def make_policy(**kwargs):
    return dict(kwargs)

class TestCrossPlaneSummaryPack(unittest.TestCase):
    def setUp(self):
        self.cp = make_cp(control_plane_summary='nominal')
        self.pf = make_pf(portfolio_summary='nominal')
        self.cp_blocked = make_cp(control_plane_summary='blocked')
        self.pf_blocked = make_pf(portfolio_summary='blocked')
        self.cp_escalated = make_cp(control_plane_summary='escalated')
        self.pf_escalated = make_pf(portfolio_summary='escalated')
        self.cp_degraded = make_cp(control_plane_summary='degraded')
        self.pf_degraded = make_pf(portfolio_summary='degraded')
        self.cp_partial = make_cp(control_plane_summary='partial')
        self.pf_partial = make_pf(portfolio_summary='partial')
        self.dash_nominal = make_dash(cross_plane_dashboard_state='cross_nominal')
        self.dash_blocked = make_dash(cross_plane_dashboard_state='cross_blocked')
        self.dash_cp_blocked = make_dash(cross_plane_dashboard_state='control_plane_blocked')
        self.dash_pf_blocked = make_dash(cross_plane_dashboard_state='portfolio_blocked')
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
        out = cross_plane_summary_pack(deepcopy(self.cp), deepcopy(self.pf), deepcopy(self.dash_nominal), deepcopy(self.closure_nominal), deepcopy(self.status_nominal), deepcopy(self.policy_nominal))
        self.assertEqual(out['cross_plane_summary_state'], 'cross_nominal')
        self.assertEqual(out['cross_plane_summary_source'], 'both')
        self.assertEqual(out['cross_plane_summary_reason'], 'Both lanes nominal/clean')
        self.assertEqual(out['cross_plane_summary_blocked'], False)
        self.assertEqual(out['cross_plane_summary_escalated'], False)
        self.assertEqual(out['cross_plane_summary_nominal'], True)
        self.assertEqual(out['control_plane_summary']['control_plane_summary'], 'nominal')
        self.assertEqual(out['portfolio_summary']['portfolio_summary'], 'nominal')
        self.assertEqual(out['cross_plane_dashboard']['cross_plane_dashboard_state'], 'cross_nominal')
        self.assertEqual(out['cross_plane_closure']['cross_plane_closure_state'], 'cross_closure_ready')
        self.assertEqual(out['cross_plane_status']['cross_plane_status_state'], 'cross_nominal')
        self.assertEqual(out['cross_plane_policy']['cross_plane_policy_state'], 'cross_nominal')

    def test_missing_required_upstream(self):
        with self.assertRaises(ValueError):
            cross_plane_summary_pack(None, self.pf, self.dash_nominal, self.closure_nominal, self.status_nominal, self.policy_nominal)
        with self.assertRaises(ValueError):
            cross_plane_summary_pack(self.cp, None, self.dash_nominal, self.closure_nominal, self.status_nominal, self.policy_nominal)
        with self.assertRaises(ValueError):
            cross_plane_summary_pack(self.cp, self.pf, None, self.closure_nominal, self.status_nominal, self.policy_nominal)
        with self.assertRaises(ValueError):
            cross_plane_summary_pack(self.cp, self.pf, self.dash_nominal, None, self.status_nominal, self.policy_nominal)
        with self.assertRaises(ValueError):
            cross_plane_summary_pack(self.cp, self.pf, self.dash_nominal, self.closure_nominal, None, self.policy_nominal)
        with self.assertRaises(ValueError):
            cross_plane_summary_pack(self.cp, self.pf, self.dash_nominal, self.closure_nominal, self.status_nominal, None)

    def test_precedence_both_blocked(self):
        out = cross_plane_summary_pack(self.cp_blocked, self.pf_blocked, self.dash_nominal, self.closure_nominal, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_summary_state'], 'cross_blocked')
        self.assertEqual(out['cross_plane_summary_source'], 'both')
        self.assertEqual(out['cross_plane_summary_blocked'], True)
        self.assertEqual(out['cross_plane_summary_reason'], 'Both lanes blocked/escalated/unresolved/degraded/not_ready')

    def test_precedence_control_plane_blocked(self):
        out = cross_plane_summary_pack(self.cp_blocked, self.pf, self.dash_nominal, self.closure_nominal, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_summary_state'], 'control_plane_blocked')
        self.assertEqual(out['cross_plane_summary_source'], 'control_plane')
        self.assertEqual(out['cross_plane_summary_blocked'], True)
        self.assertEqual(out['cross_plane_summary_reason'], 'Control-plane blocked/escalated/unresolved/degraded/not_ready')

    def test_precedence_portfolio_blocked(self):
        out = cross_plane_summary_pack(self.cp, self.pf_blocked, self.dash_nominal, self.closure_nominal, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_summary_state'], 'portfolio_blocked')
        self.assertEqual(out['cross_plane_summary_source'], 'portfolio')
        self.assertEqual(out['cross_plane_summary_blocked'], True)
        self.assertEqual(out['cross_plane_summary_reason'], 'Portfolio-plane blocked/escalated/unresolved/degraded/not_ready')

    def test_precedence_escalated(self):
        out = cross_plane_summary_pack(self.cp_escalated, self.pf, self.dash_nominal, self.closure_nominal, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_summary_state'], 'control_plane_blocked')
        out = cross_plane_summary_pack(self.cp, self.pf_escalated, self.dash_nominal, self.closure_nominal, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_summary_state'], 'portfolio_blocked')
        out = cross_plane_summary_pack(self.cp_escalated, self.pf_escalated, self.dash_nominal, self.closure_nominal, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_summary_state'], 'cross_blocked')

    def test_precedence_degraded(self):
        out = cross_plane_summary_pack(self.cp_degraded, self.pf, self.dash_nominal, self.closure_nominal, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_summary_state'], 'control_plane_blocked')
        out = cross_plane_summary_pack(self.cp, self.pf_degraded, self.dash_nominal, self.closure_nominal, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_summary_state'], 'portfolio_blocked')
        out = cross_plane_summary_pack(self.cp_degraded, self.pf_degraded, self.dash_nominal, self.closure_nominal, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_summary_state'], 'cross_blocked')

    def test_precedence_partial(self):
        out = cross_plane_summary_pack(self.cp_partial, self.pf, self.dash_nominal, self.closure_nominal, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_summary_state'], 'control_plane_blocked')
        out = cross_plane_summary_pack(self.cp, self.pf_partial, self.dash_nominal, self.closure_nominal, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_summary_state'], 'portfolio_blocked')
        out = cross_plane_summary_pack(self.cp_partial, self.pf_partial, self.dash_nominal, self.closure_nominal, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_summary_state'], 'cross_blocked')

    def test_dashboard_closure_status_policy_precedence(self):
        out = cross_plane_summary_pack(self.cp, self.pf, self.dash_blocked, self.closure_nominal, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_summary_state'], 'cross_blocked')
        self.assertEqual(out['cross_plane_summary_source'], 'dashboard_closure_status_policy')
        out = cross_plane_summary_pack(self.cp, self.pf, self.dash_cp_blocked, self.closure_nominal, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_summary_state'], 'cross_blocked')
        self.assertEqual(out['cross_plane_summary_source'], 'dashboard_closure_status_policy')
        out = cross_plane_summary_pack(self.cp, self.pf, self.dash_pf_blocked, self.closure_nominal, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_summary_state'], 'cross_blocked')
        self.assertEqual(out['cross_plane_summary_source'], 'dashboard_closure_status_policy')
        out = cross_plane_summary_pack(self.cp, self.pf, self.dash_nominal, self.closure_blocked, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_summary_state'], 'cross_blocked')
        self.assertEqual(out['cross_plane_summary_source'], 'dashboard_closure_status_policy')
        out = cross_plane_summary_pack(self.cp, self.pf, self.dash_nominal, self.closure_cp_blocked, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_summary_state'], 'cross_blocked')
        self.assertEqual(out['cross_plane_summary_source'], 'dashboard_closure_status_policy')
        out = cross_plane_summary_pack(self.cp, self.pf, self.dash_nominal, self.closure_pf_blocked, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_summary_state'], 'cross_blocked')
        self.assertEqual(out['cross_plane_summary_source'], 'dashboard_closure_status_policy')
        out = cross_plane_summary_pack(self.cp, self.pf, self.dash_nominal, self.closure_nominal, self.status_blocked, self.policy_nominal)
        self.assertEqual(out['cross_plane_summary_state'], 'cross_blocked')
        self.assertEqual(out['cross_plane_summary_source'], 'dashboard_closure_status_policy')
        out = cross_plane_summary_pack(self.cp, self.pf, self.dash_nominal, self.closure_nominal, self.status_cp_blocked, self.policy_nominal)
        self.assertEqual(out['cross_plane_summary_state'], 'cross_blocked')
        self.assertEqual(out['cross_plane_summary_source'], 'dashboard_closure_status_policy')
        out = cross_plane_summary_pack(self.cp, self.pf, self.dash_nominal, self.closure_nominal, self.status_pf_blocked, self.policy_nominal)
        self.assertEqual(out['cross_plane_summary_state'], 'cross_blocked')
        self.assertEqual(out['cross_plane_summary_source'], 'dashboard_closure_status_policy')
        out = cross_plane_summary_pack(self.cp, self.pf, self.dash_nominal, self.closure_nominal, self.status_nominal, self.policy_blocked)
        self.assertEqual(out['cross_plane_summary_state'], 'cross_blocked')
        self.assertEqual(out['cross_plane_summary_source'], 'dashboard_closure_status_policy')
        out = cross_plane_summary_pack(self.cp, self.pf, self.dash_nominal, self.closure_nominal, self.status_nominal, self.policy_cp_blocked)
        self.assertEqual(out['cross_plane_summary_state'], 'cross_blocked')
        self.assertEqual(out['cross_plane_summary_source'], 'dashboard_closure_status_policy')
        out = cross_plane_summary_pack(self.cp, self.pf, self.dash_nominal, self.closure_nominal, self.status_nominal, self.policy_pf_blocked)
        self.assertEqual(out['cross_plane_summary_state'], 'cross_blocked')
        self.assertEqual(out['cross_plane_summary_source'], 'dashboard_closure_status_policy')

    def test_stable_output(self):
        out1 = cross_plane_summary_pack(self.cp, self.pf, self.dash_nominal, self.closure_nominal, self.status_nominal, self.policy_nominal)
        out2 = cross_plane_summary_pack(self.cp, self.pf, self.dash_nominal, self.closure_nominal, self.status_nominal, self.policy_nominal)
        self.assertEqual(out1, out2)

    def test_no_input_mutation(self):
        cp = deepcopy(self.cp)
        pf = deepcopy(self.pf)
        dash = deepcopy(self.dash_nominal)
        clo = deepcopy(self.closure_nominal)
        stat = deepcopy(self.status_nominal)
        pol = deepcopy(self.policy_nominal)
        _ = cross_plane_summary_pack(cp, pf, dash, clo, stat, pol)
        self.assertEqual(cp, self.cp)
        self.assertEqual(pf, self.pf)
        self.assertEqual(dash, self.dash_nominal)
        self.assertEqual(clo, self.closure_nominal)
        self.assertEqual(stat, self.status_nominal)
        self.assertEqual(pol, self.policy_nominal)

    def test_blocking_remains_visible(self):
        out = cross_plane_summary_pack(self.cp_blocked, self.pf, self.dash_nominal, self.closure_nominal, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_summary_blocked'], True)
        out = cross_plane_summary_pack(self.cp, self.pf_blocked, self.dash_nominal, self.closure_nominal, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_summary_blocked'], True)
        out = cross_plane_summary_pack(self.cp_blocked, self.pf_blocked, self.dash_nominal, self.closure_nominal, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_summary_blocked'], True)
        out = cross_plane_summary_pack(self.cp, self.pf, self.dash_blocked, self.closure_nominal, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_summary_blocked'], True)
        out = cross_plane_summary_pack(self.cp, self.pf, self.dash_nominal, self.closure_blocked, self.status_nominal, self.policy_nominal)
        self.assertEqual(out['cross_plane_summary_blocked'], True)
        out = cross_plane_summary_pack(self.cp, self.pf, self.dash_nominal, self.closure_nominal, self.status_blocked, self.policy_nominal)
        self.assertEqual(out['cross_plane_summary_blocked'], True)
        out = cross_plane_summary_pack(self.cp, self.pf, self.dash_nominal, self.closure_nominal, self.status_nominal, self.policy_blocked)
        self.assertEqual(out['cross_plane_summary_blocked'], True)

    def test_clean_nominal(self):
        cp = make_cp(control_plane_summary='nominal')
        pf = make_pf(portfolio_summary='nominal')
        dash = make_dash(cross_plane_dashboard_state='cross_nominal')
        clo = make_closure(cross_plane_closure_state='cross_closure_ready')
        stat = make_status(cross_plane_status_state='cross_nominal')
        pol = make_policy(cross_plane_policy_state='cross_nominal')
        out = cross_plane_summary_pack(cp, pf, dash, clo, stat, pol)
        self.assertEqual(out['cross_plane_summary_state'], 'cross_nominal')
        self.assertEqual(out['cross_plane_summary_blocked'], False)
        self.assertEqual(out['cross_plane_summary_nominal'], True)

if __name__ == '__main__':
    unittest.main()
