import unittest
from copy import deepcopy
from workflows.portfolio_status_pack import portfolio_status_pack

def make_pack(**kwargs):
    return dict(kwargs)

class TestPortfolioStatusPack(unittest.TestCase):
    def setUp(self):
        self.policy = make_pack(portfolio_policy_decision='proceed_policy', portfolio_policy_decision_reason='Proceed', portfolio_policy_decision_source='governance')
        self.ctrl = make_pack(summary_field='summary')
        self.gov = make_pack(governance_indicator=False)
        self.esc = make_pack(escalation_indicator=False)
        self.res = make_pack(resolution_indicator=False)
        self.execu = make_pack(execution_field='exec')
        self.outc = make_pack(outcome_field='outc')
        self.disp = make_pack(dispatch_field='disp')
        self.actq = make_pack(action_queue_field='actq')

    def test_happy_path(self):
        out = portfolio_status_pack(
            deepcopy(self.policy), deepcopy(self.ctrl), deepcopy(self.gov), deepcopy(self.esc), deepcopy(self.res),
            deepcopy(self.execu), deepcopy(self.outc), deepcopy(self.disp), deepcopy(self.actq)
        )
        self.assertEqual(out['portfolio_status'], 'nominal')
        self.assertEqual(out['portfolio_status_source'], 'default')
        self.assertEqual(out['portfolio_status_reason'], 'No blocking/escalation/governance/resolution condition present')
        self.assertEqual(out['portfolio_policy']['portfolio_policy_decision'], 'proceed_policy')
        self.assertEqual(out['portfolio_control_summary']['summary_field'], 'summary')
        self.assertEqual(out['portfolio_execution']['execution_field'], 'exec')
        self.assertEqual(out['portfolio_outcome']['outcome_field'], 'outc')
        self.assertEqual(out['portfolio_dispatch']['dispatch_field'], 'disp')
        self.assertEqual(out['portfolio_action_queue']['action_queue_field'], 'actq')

    def test_missing_required_upstream(self):
        with self.assertRaises(ValueError):
            portfolio_status_pack(None, self.ctrl, self.gov, self.esc, self.res)
        with self.assertRaises(ValueError):
            portfolio_status_pack(self.policy, None, self.gov, self.esc, self.res)
        with self.assertRaises(ValueError):
            portfolio_status_pack(self.policy, self.ctrl, None, self.esc, self.res)
        with self.assertRaises(ValueError):
            portfolio_status_pack(self.policy, self.ctrl, self.gov, None, self.res)
        with self.assertRaises(ValueError):
            portfolio_status_pack(self.policy, self.ctrl, self.gov, self.esc, None)

    def test_precedence_escalation(self):
        esc = make_pack(escalation_indicator=True, escalation_reason='Escalation active')
        out = portfolio_status_pack(self.policy, self.ctrl, self.gov, esc, self.res)
        self.assertEqual(out['portfolio_status'], 'escalated')
        self.assertEqual(out['portfolio_status_source'], 'escalation')
        self.assertEqual(out['portfolio_status_reason'], 'Escalation active')

    def test_precedence_policy_blocked(self):
        policy = make_pack(portfolio_policy_decision='hold_policy', portfolio_policy_decision_reason='Policy is hold', portfolio_policy_decision_source='policy')
        out = portfolio_status_pack(policy, self.ctrl, self.gov, self.esc, self.res)
        self.assertEqual(out['portfolio_status'], 'blocked')
        self.assertEqual(out['portfolio_status_source'], 'policy')
        self.assertEqual(out['portfolio_status_reason'], 'Policy is hold')

    def test_precedence_governance(self):
        gov = make_pack(governance_indicator=True, governance_reason='Governance active')
        out = portfolio_status_pack(self.policy, self.ctrl, gov, self.esc, self.res)
        self.assertEqual(out['portfolio_status'], 'governed')
        self.assertEqual(out['portfolio_status_source'], 'governance')
        self.assertEqual(out['portfolio_status_reason'], 'Governance active')

    def test_precedence_resolution(self):
        res = make_pack(resolution_indicator=True, resolution_reason='Resolution active')
        out = portfolio_status_pack(self.policy, self.ctrl, self.gov, self.esc, res)
        self.assertEqual(out['portfolio_status'], 'resolution')
        self.assertEqual(out['portfolio_status_source'], 'resolution')
        self.assertEqual(out['portfolio_status_reason'], 'Resolution active')

    def test_stable_output(self):
        out1 = portfolio_status_pack(self.policy, self.ctrl, self.gov, self.esc, self.res, self.execu, self.outc, self.disp, self.actq)
        out2 = portfolio_status_pack(self.policy, self.ctrl, self.gov, self.esc, self.res, self.execu, self.outc, self.disp, self.actq)
        self.assertEqual(out1, out2)

    def test_no_input_mutation(self):
        policy = deepcopy(self.policy)
        ctrl = deepcopy(self.ctrl)
        gov = deepcopy(self.gov)
        esc = deepcopy(self.esc)
        res = deepcopy(self.res)
        execu = deepcopy(self.execu)
        outc = deepcopy(self.outc)
        disp = deepcopy(self.disp)
        actq = deepcopy(self.actq)
        _ = portfolio_status_pack(policy, ctrl, gov, esc, res, execu, outc, disp, actq)
        self.assertEqual(policy, self.policy)
        self.assertEqual(ctrl, self.ctrl)
        self.assertEqual(gov, self.gov)
        self.assertEqual(esc, self.esc)
        self.assertEqual(res, self.res)
        self.assertEqual(execu, self.execu)
        self.assertEqual(outc, self.outc)
        self.assertEqual(disp, self.disp)
        self.assertEqual(actq, self.actq)

    def test_blocking_escalation_outranks_nominal(self):
        policy = make_pack(portfolio_policy_decision='proceed_policy', portfolio_policy_decision_reason='Proceed', portfolio_policy_decision_source='governance')
        esc = make_pack(escalation_indicator=True, escalation_reason='Escalation active')
        out = portfolio_status_pack(policy, self.ctrl, self.gov, esc, self.res)
        self.assertEqual(out['portfolio_status'], 'escalated')
        self.assertEqual(out['portfolio_status_source'], 'escalation')
        self.assertEqual(out['portfolio_status_reason'], 'Escalation active')

if __name__ == '__main__':
    unittest.main()
