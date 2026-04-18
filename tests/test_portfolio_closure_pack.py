import unittest
from copy import deepcopy
from workflows.portfolio_closure_pack import portfolio_closure_pack

def make_pack(**kwargs):
    return dict(kwargs)

class TestPortfolioClosurePack(unittest.TestCase):
    def setUp(self):
        self.status = make_pack(portfolio_status='nominal', portfolio_status_reason='Nominal', portfolio_status_source='default')
        self.policy = make_pack(portfolio_policy_decision='proceed_policy', portfolio_policy_decision_reason='Proceed', portfolio_policy_decision_source='governance')
        self.res = make_pack(resolution_indicator=False, resolution_ready=True)
        self.esc = make_pack(escalation_indicator=False)
        self.gov = make_pack(governance_indicator=False)
        self.ctrl = make_pack(summary_field='summary')
        self.outc = make_pack(outcome_field='outc')
        self.execu = make_pack(execution_field='exec')
        self.disp = make_pack(dispatch_field='disp')
        self.actq = make_pack(action_queue_field='actq')

    def test_happy_path(self):
        out = portfolio_closure_pack(
            deepcopy(self.status), deepcopy(self.policy), deepcopy(self.res), deepcopy(self.esc), deepcopy(self.gov), deepcopy(self.ctrl),
            deepcopy(self.outc), deepcopy(self.execu), deepcopy(self.disp), deepcopy(self.actq)
        )
        self.assertEqual(out['portfolio_closure_state'], 'closed')
        self.assertEqual(out['portfolio_closure_eligible'], True)
        self.assertEqual(out['portfolio_closure_blocked'], False)
        self.assertEqual(out['portfolio_closure_source'], 'nominal')
        self.assertEqual(out['portfolio_closure_reason'], 'All closure conditions satisfied')
        self.assertEqual(out['portfolio_status']['portfolio_status'], 'nominal')
        self.assertEqual(out['portfolio_policy']['portfolio_policy_decision'], 'proceed_policy')
        self.assertEqual(out['portfolio_resolution']['resolution_ready'], True)
        self.assertEqual(out['portfolio_execution']['execution_field'], 'exec')
        self.assertEqual(out['portfolio_outcome']['outcome_field'], 'outc')
        self.assertEqual(out['portfolio_dispatch']['dispatch_field'], 'disp')
        self.assertEqual(out['portfolio_action_queue']['action_queue_field'], 'actq')

    def test_missing_required_upstream(self):
        with self.assertRaises(ValueError):
            portfolio_closure_pack(None, self.policy, self.res, self.esc, self.gov, self.ctrl)
        with self.assertRaises(ValueError):
            portfolio_closure_pack(self.status, None, self.res, self.esc, self.gov, self.ctrl)
        with self.assertRaises(ValueError):
            portfolio_closure_pack(self.status, self.policy, None, self.esc, self.gov, self.ctrl)
        with self.assertRaises(ValueError):
            portfolio_closure_pack(self.status, self.policy, self.res, None, self.gov, self.ctrl)
        with self.assertRaises(ValueError):
            portfolio_closure_pack(self.status, self.policy, self.res, self.esc, None, self.ctrl)
        with self.assertRaises(ValueError):
            portfolio_closure_pack(self.status, self.policy, self.res, self.esc, self.gov, None)

    def test_precedence_escalation_blocks(self):
        esc = make_pack(escalation_indicator=True, escalation_reason='Escalation active')
        out = portfolio_closure_pack(self.status, self.policy, self.res, esc, self.gov, self.ctrl)
        self.assertEqual(out['portfolio_closure_state'], 'blocked')
        self.assertEqual(out['portfolio_closure_blocked'], True)
        self.assertEqual(out['portfolio_closure_source'], 'escalation')
        self.assertEqual(out['portfolio_closure_reason'], 'Escalation active')

    def test_precedence_status_escalated_blocks(self):
        status = make_pack(portfolio_status='escalated', portfolio_status_reason='Escalation in status', portfolio_status_source='escalation')
        out = portfolio_closure_pack(status, self.policy, self.res, self.esc, self.gov, self.ctrl)
        self.assertEqual(out['portfolio_closure_state'], 'blocked')
        self.assertEqual(out['portfolio_closure_blocked'], True)
        self.assertEqual(out['portfolio_closure_source'], 'status')
        self.assertEqual(out['portfolio_closure_reason'], 'Escalation in status')

    def test_precedence_policy_hold_blocks(self):
        policy = make_pack(portfolio_policy_decision='hold_policy', portfolio_policy_decision_reason='Policy is hold', portfolio_policy_decision_source='policy')
        out = portfolio_closure_pack(self.status, policy, self.res, self.esc, self.gov, self.ctrl)
        self.assertEqual(out['portfolio_closure_state'], 'blocked')
        self.assertEqual(out['portfolio_closure_blocked'], True)
        self.assertEqual(out['portfolio_closure_source'], 'policy')
        self.assertEqual(out['portfolio_closure_reason'], 'Policy is hold')

    def test_precedence_governance_blocks(self):
        gov = make_pack(governance_indicator=True, governance_reason='Governance active')
        out = portfolio_closure_pack(self.status, self.policy, self.res, self.esc, gov, self.ctrl)
        self.assertEqual(out['portfolio_closure_state'], 'blocked')
        self.assertEqual(out['portfolio_closure_blocked'], True)
        self.assertEqual(out['portfolio_closure_source'], 'governance')
        self.assertEqual(out['portfolio_closure_reason'], 'Governance active')

    def test_precedence_resolution_not_ready_blocks(self):
        res = make_pack(resolution_indicator=True, resolution_ready=False, resolution_reason='Resolution not ready')
        out = portfolio_closure_pack(self.status, self.policy, res, self.esc, self.gov, self.ctrl)
        self.assertEqual(out['portfolio_closure_state'], 'blocked')
        self.assertEqual(out['portfolio_closure_blocked'], True)
        self.assertEqual(out['portfolio_closure_source'], 'resolution')
        self.assertEqual(out['portfolio_closure_reason'], 'Resolution not ready')

    def test_stable_output(self):
        out1 = portfolio_closure_pack(self.status, self.policy, self.res, self.esc, self.gov, self.ctrl, self.outc, self.execu, self.disp, self.actq)
        out2 = portfolio_closure_pack(self.status, self.policy, self.res, self.esc, self.gov, self.ctrl, self.outc, self.execu, self.disp, self.actq)
        self.assertEqual(out1, out2)

    def test_no_input_mutation(self):
        status = deepcopy(self.status)
        policy = deepcopy(self.policy)
        res = deepcopy(self.res)
        esc = deepcopy(self.esc)
        gov = deepcopy(self.gov)
        ctrl = deepcopy(self.ctrl)
        outc = deepcopy(self.outc)
        execu = deepcopy(self.execu)
        disp = deepcopy(self.disp)
        actq = deepcopy(self.actq)
        _ = portfolio_closure_pack(status, policy, res, esc, gov, ctrl, outc, execu, disp, actq)
        self.assertEqual(status, self.status)
        self.assertEqual(policy, self.policy)
        self.assertEqual(res, self.res)
        self.assertEqual(esc, self.esc)
        self.assertEqual(gov, self.gov)
        self.assertEqual(ctrl, self.ctrl)
        self.assertEqual(outc, self.outc)
        self.assertEqual(execu, self.execu)
        self.assertEqual(disp, self.disp)
        self.assertEqual(actq, self.actq)

    def test_closure_pending(self):
        status = make_pack(portfolio_status='pending', portfolio_status_reason='Pending', portfolio_status_source='default')
        policy = make_pack(portfolio_policy_decision='review_policy', portfolio_policy_decision_reason='Review', portfolio_policy_decision_source='policy')
        res = make_pack(resolution_indicator=False, resolution_ready=False)
        out = portfolio_closure_pack(status, policy, res, self.esc, self.gov, self.ctrl)
        self.assertEqual(out['portfolio_closure_state'], 'pending')
        self.assertEqual(out['portfolio_closure_eligible'], False)
        self.assertEqual(out['portfolio_closure_blocked'], False)
        self.assertEqual(out['portfolio_closure_source'], 'default')
        self.assertEqual(out['portfolio_closure_reason'], 'Closure pending further action')

if __name__ == '__main__':
    unittest.main()
