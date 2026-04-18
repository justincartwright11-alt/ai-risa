"""
portfolio_policy_pack

Deterministically consolidates portfolio-level policy from all upstream portfolio packs.
"""

def portfolio_policy_pack(
    portfolio_governance_pack_result,
    portfolio_escalation_routing_pack_result,
    portfolio_resolution_decision_pack_result,
    portfolio_control_summary_pack_result,
    portfolio_execution_pack_result=None,
    portfolio_outcome_pack_result=None,
    portfolio_dispatch_pack_result=None,
    portfolio_action_queue_pack_result=None
):
    """
    Args:
        portfolio_governance_pack_result (dict): Required
        portfolio_escalation_routing_pack_result (dict): Required
        portfolio_resolution_decision_pack_result (dict): Required
        portfolio_control_summary_pack_result (dict): Required
        portfolio_execution_pack_result (dict): Optional
        portfolio_outcome_pack_result (dict): Optional
        portfolio_dispatch_pack_result (dict): Optional
        portfolio_action_queue_pack_result (dict): Optional
    Returns:
        dict: Canonical portfolio policy view
    """
    # --- Upstream validation ---
    def _validate_upstream():
        required = [
            ('portfolio_governance_pack_result', portfolio_governance_pack_result),
            ('portfolio_escalation_routing_pack_result', portfolio_escalation_routing_pack_result),
            ('portfolio_resolution_decision_pack_result', portfolio_resolution_decision_pack_result),
            ('portfolio_control_summary_pack_result', portfolio_control_summary_pack_result)
        ]
        for name, val in required:
            if not isinstance(val, dict):
                raise ValueError(f"Missing or invalid required upstream: {name}")
    _validate_upstream()

    # --- Precedence resolution ---
    def _precedence(governance, escalation, resolution):
        # Governance > Escalation > Resolution
        if governance.get('policy_decision'):
            return governance['policy_decision'], 'governance', governance.get('policy_reason', '')
        if escalation.get('policy_decision'):
            return escalation['policy_decision'], 'escalation', escalation.get('policy_reason', '')
        if resolution.get('policy_decision'):
            return resolution['policy_decision'], 'resolution', resolution.get('policy_reason', '')
        return 'hold_policy', 'default', 'No explicit policy_decision upstream; default hold.'

    # --- Policy-state derivation ---
    def _derive_policy_state():
        gov = portfolio_governance_pack_result
        esc = portfolio_escalation_routing_pack_result
        res = portfolio_resolution_decision_pack_result
        ctrl = portfolio_control_summary_pack_result
        execu = portfolio_execution_pack_result or {}
        outc = portfolio_outcome_pack_result or {}
        disp = portfolio_dispatch_pack_result or {}
        actq = portfolio_action_queue_pack_result or {}
        decision, source, reason = _precedence(gov, esc, res)
        return {
            'portfolio_policy_decision': decision,
            'portfolio_policy_decision_source': source,
            'portfolio_policy_decision_reason': reason,
            'portfolio_governance': gov,
            'portfolio_escalation': esc,
            'portfolio_resolution': res,
            'portfolio_control_summary': ctrl,
            'portfolio_execution': execu,
            'portfolio_outcome': outc,
            'portfolio_dispatch': disp,
            'portfolio_action_queue': actq
        }

    # --- Canonical pack assembly ---
    def _assemble():
        state = _derive_policy_state()
        # Stable field ordering
        return {
            'portfolio_policy_decision': state['portfolio_policy_decision'],
            'portfolio_policy_decision_source': state['portfolio_policy_decision_source'],
            'portfolio_policy_decision_reason': state['portfolio_policy_decision_reason'],
            'portfolio_governance': state['portfolio_governance'],
            'portfolio_escalation': state['portfolio_escalation'],
            'portfolio_resolution': state['portfolio_resolution'],
            'portfolio_control_summary': state['portfolio_control_summary'],
            'portfolio_execution': state['portfolio_execution'],
            'portfolio_outcome': state['portfolio_outcome'],
            'portfolio_dispatch': state['portfolio_dispatch'],
            'portfolio_action_queue': state['portfolio_action_queue']
        }

    return _assemble()
