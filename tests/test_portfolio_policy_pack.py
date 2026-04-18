import unittest
from copy import deepcopy
from workflows.portfolio_policy_pack import portfolio_policy_pack

def make_pack(**kwargs):
    return dict(kwargs)

class TestPortfolioPolicyPack(unittest.TestCase):
    def setUp(self):
        self.gov = make_pack(policy_decision='proceed_policy', policy_reason='Governance allows proceed')
        self.esc = make_pack(policy_decision='hold_policy', policy_reason='Escalation holds')
        self.res = make_pack(policy_decision='escalate_policy', policy_reason='Resolution escalates')
        self.ctrl = make_pack(summary_field='summary')
        self.execu = make_pack(execution_field='exec')
        self.outc = make_pack(outcome_field='outc')
        self.disp = make_pack(dispatch_field='disp')
        self.actq = make_pack(action_queue_field='actq')

    def test_happy_path(self):
        out = portfolio_policy_pack(
            deepcopy(self.gov), deepcopy(self.esc), deepcopy(self.res), deepcopy(self.ctrl),
            deepcopy(self.execu), deepcopy(self.outc), deepcopy(self.disp), deepcopy(self.actq)
        )
        self.assertEqual(out['portfolio_policy_decision'], 'proceed_policy')
        self.assertEqual(out['portfolio_policy_decision_source'], 'governance')
        self.assertEqual(out['portfolio_policy_decision_reason'], 'Governance allows proceed')
        self.assertEqual(out['portfolio_governance']['policy_decision'], 'proceed_policy')
        self.assertEqual(out['portfolio_escalation']['policy_decision'], 'hold_policy')
        self.assertEqual(out['portfolio_resolution']['policy_decision'], 'escalate_policy')
        self.assertEqual(out['portfolio_control_summary']['summary_field'], 'summary')
        self.assertEqual(out['portfolio_execution']['execution_field'], 'exec')
        self.assertEqual(out['portfolio_outcome']['outcome_field'], 'outc')
        self.assertEqual(out['portfolio_dispatch']['dispatch_field'], 'disp')
        self.assertEqual(out['portfolio_action_queue']['action_queue_field'], 'actq')

    def test_missing_required_upstream(self):
        with self.assertRaises(ValueError):
            portfolio_policy_pack(None, self.esc, self.res, self.ctrl)
        with self.assertRaises(ValueError):
            portfolio_policy_pack(self.gov, None, self.res, self.ctrl)
        with self.assertRaises(ValueError):
            portfolio_policy_pack(self.gov, self.esc, None, self.ctrl)
        with self.assertRaises(ValueError):
            portfolio_policy_pack(self.gov, self.esc, self.res, None)

    def test_precedence_governance(self):
        gov = make_pack(policy_decision='hold_policy', policy_reason='Governance holds')
        esc = make_pack(policy_decision='proceed_policy', policy_reason='Escalation allows proceed')
        res = make_pack(policy_decision='escalate_policy', policy_reason='Resolution escalates')
        out = portfolio_policy_pack(gov, esc, res, self.ctrl)
        self.assertEqual(out['portfolio_policy_decision'], 'hold_policy')
        self.assertEqual(out['portfolio_policy_decision_source'], 'governance')

    def test_precedence_escalation(self):
        gov = make_pack()
        esc = make_pack(policy_decision='review_policy', policy_reason='Escalation review')
        res = make_pack(policy_decision='escalate_policy', policy_reason='Resolution escalates')
        out = portfolio_policy_pack(gov, esc, res, self.ctrl)
        self.assertEqual(out['portfolio_policy_decision'], 'review_policy')
        self.assertEqual(out['portfolio_policy_decision_source'], 'escalation')

    def test_precedence_resolution(self):
        gov = make_pack()
        esc = make_pack()
        res = make_pack(policy_decision='escalate_policy', policy_reason='Resolution escalates')
        out = portfolio_policy_pack(gov, esc, res, self.ctrl)
        self.assertEqual(out['portfolio_policy_decision'], 'escalate_policy')
        self.assertEqual(out['portfolio_policy_decision_source'], 'resolution')

    def test_precedence_default(self):
        gov = make_pack()
        esc = make_pack()
        res = make_pack()
        out = portfolio_policy_pack(gov, esc, res, self.ctrl)
        self.assertEqual(out['portfolio_policy_decision'], 'hold_policy')
        self.assertEqual(out['portfolio_policy_decision_source'], 'default')

    def test_stable_output(self):
        out1 = portfolio_policy_pack(self.gov, self.esc, self.res, self.ctrl, self.execu, self.outc, self.disp, self.actq)
        out2 = portfolio_policy_pack(self.gov, self.esc, self.res, self.ctrl, self.execu, self.outc, self.disp, self.actq)
        self.assertEqual(out1, out2)

    def test_no_input_mutation(self):
        gov = deepcopy(self.gov)
        esc = deepcopy(self.esc)
        res = deepcopy(self.res)
        ctrl = deepcopy(self.ctrl)
        execu = deepcopy(self.execu)
        outc = deepcopy(self.outc)
        disp = deepcopy(self.disp)
        actq = deepcopy(self.actq)
        _ = portfolio_policy_pack(gov, esc, res, ctrl, execu, outc, disp, actq)
        self.assertEqual(gov, self.gov)
        self.assertEqual(esc, self.esc)
        self.assertEqual(res, self.res)
        self.assertEqual(ctrl, self.ctrl)
        self.assertEqual(execu, self.execu)
        self.assertEqual(outc, self.outc)
        self.assertEqual(disp, self.disp)
        self.assertEqual(actq, self.actq)

if __name__ == '__main__':
    unittest.main()
