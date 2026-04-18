import unittest
from copy import deepcopy
from workflows.cross_plane_policy_pack import cross_plane_policy_pack

def make_cp(**kwargs):
    return dict(kwargs)

def make_pf(**kwargs):
    return dict(kwargs)

class TestCrossPlanePolicyPack(unittest.TestCase):
    def setUp(self):
        self.cp = make_cp(control_plane_policy_status='ready')
        self.pf = make_pf(portfolio_policy_decision='proceed_policy')
        self.cp_blocked = make_cp(control_plane_policy_status='blocked')
        self.pf_blocked = make_pf(portfolio_policy_decision='blocked')
        self.cp_escalate = make_cp(control_plane_policy_status='escalate_policy')
        self.pf_escalate = make_pf(portfolio_policy_decision='escalate_policy')
        self.cp_partial = make_cp(control_plane_policy_status='partial')
        self.pf_partial = make_pf(portfolio_policy_decision='partial')

    def test_happy_path(self):
        out = cross_plane_policy_pack(deepcopy(self.cp), deepcopy(self.pf))
        self.assertEqual(out['cross_plane_policy_state'], 'cross_nominal')
        self.assertEqual(out['cross_plane_policy_source'], 'both')
        self.assertEqual(out['cross_plane_policy_reason'], 'Both lanes nominal/ready')
        self.assertEqual(out['cross_plane_policy_eligible'], True)
        self.assertEqual(out['cross_plane_policy_blocked'], False)
        self.assertEqual(out['control_plane_policy']['control_plane_policy_status'], 'ready')
        self.assertEqual(out['portfolio_policy']['portfolio_policy_decision'], 'proceed_policy')

    def test_missing_required_upstream(self):
        with self.assertRaises(ValueError):
            cross_plane_policy_pack(None, self.pf)
        with self.assertRaises(ValueError):
            cross_plane_policy_pack(self.cp, None)

    def test_precedence_both_blocked(self):
        out = cross_plane_policy_pack(self.cp_blocked, self.pf_blocked)
        self.assertEqual(out['cross_plane_policy_state'], 'cross_blocked')
        self.assertEqual(out['cross_plane_policy_source'], 'both')
        self.assertEqual(out['cross_plane_policy_blocked'], True)
        self.assertEqual(out['cross_plane_policy_reason'], 'Both lanes blocked or escalated')

    def test_precedence_control_plane_blocked(self):
        out = cross_plane_policy_pack(self.cp_blocked, self.pf)
        self.assertEqual(out['cross_plane_policy_state'], 'control_plane_blocked')
        self.assertEqual(out['cross_plane_policy_source'], 'control_plane')
        self.assertEqual(out['cross_plane_policy_blocked'], True)
        self.assertEqual(out['cross_plane_policy_reason'], 'Control-plane blocked or escalated')

    def test_precedence_portfolio_blocked(self):
        out = cross_plane_policy_pack(self.cp, self.pf_blocked)
        self.assertEqual(out['cross_plane_policy_state'], 'portfolio_blocked')
        self.assertEqual(out['cross_plane_policy_source'], 'portfolio')
        self.assertEqual(out['cross_plane_policy_blocked'], True)
        self.assertEqual(out['cross_plane_policy_reason'], 'Portfolio-plane blocked or escalated')

    def test_precedence_escalate(self):
        out = cross_plane_policy_pack(self.cp_escalate, self.pf)
        self.assertEqual(out['cross_plane_policy_state'], 'control_plane_blocked')
        out = cross_plane_policy_pack(self.cp, self.pf_escalate)
        self.assertEqual(out['cross_plane_policy_state'], 'portfolio_blocked')
        out = cross_plane_policy_pack(self.cp_escalate, self.pf_escalate)
        self.assertEqual(out['cross_plane_policy_state'], 'cross_blocked')

    def test_precedence_partial(self):
        out = cross_plane_policy_pack(self.cp_partial, self.pf)
        self.assertEqual(out['cross_plane_policy_state'], 'control_plane_blocked')
        out = cross_plane_policy_pack(self.cp, self.pf_partial)
        self.assertEqual(out['cross_plane_policy_state'], 'portfolio_blocked')
        out = cross_plane_policy_pack(self.cp_partial, self.pf_partial)
        self.assertEqual(out['cross_plane_policy_state'], 'cross_blocked')

    def test_stable_output(self):
        out1 = cross_plane_policy_pack(self.cp, self.pf)
        out2 = cross_plane_policy_pack(self.cp, self.pf)
        self.assertEqual(out1, out2)

    def test_no_input_mutation(self):
        cp = deepcopy(self.cp)
        pf = deepcopy(self.pf)
        _ = cross_plane_policy_pack(cp, pf)
        self.assertEqual(cp, self.cp)
        self.assertEqual(pf, self.pf)

    def test_blocking_remains_visible(self):
        out = cross_plane_policy_pack(self.cp_blocked, self.pf)
        self.assertEqual(out['cross_plane_policy_blocked'], True)
        out = cross_plane_policy_pack(self.cp, self.pf_blocked)
        self.assertEqual(out['cross_plane_policy_blocked'], True)
        out = cross_plane_policy_pack(self.cp_blocked, self.pf_blocked)
        self.assertEqual(out['cross_plane_policy_blocked'], True)

    def test_clean_nominal(self):
        cp = make_cp(control_plane_policy_status='ready')
        pf = make_pf(portfolio_policy_decision='proceed_policy')
        out = cross_plane_policy_pack(cp, pf)
        self.assertEqual(out['cross_plane_policy_state'], 'cross_nominal')
        self.assertEqual(out['cross_plane_policy_eligible'], True)
        self.assertEqual(out['cross_plane_policy_blocked'], False)

if __name__ == '__main__':
    unittest.main()
