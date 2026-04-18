"""
portfolio_status_pack

Projects the canonical portfolio status from all upstream portfolio packs.
"""

def portfolio_status_pack(
    portfolio_policy_pack_result,
    portfolio_control_summary_pack_result,
    portfolio_governance_pack_result,
    portfolio_escalation_routing_pack_result,
    portfolio_resolution_decision_pack_result,
    portfolio_execution_pack_result=None,
    portfolio_outcome_pack_result=None,
    portfolio_dispatch_pack_result=None,
    portfolio_action_queue_pack_result=None
):
    """
    Args:
        portfolio_policy_pack_result (dict): Required
        portfolio_control_summary_pack_result (dict): Required
        portfolio_governance_pack_result (dict): Required
        portfolio_escalation_routing_pack_result (dict): Required
        portfolio_resolution_decision_pack_result (dict): Required
        portfolio_execution_pack_result (dict): Optional
        portfolio_outcome_pack_result (dict): Optional
        portfolio_dispatch_pack_result (dict): Optional
        portfolio_action_queue_pack_result (dict): Optional
    Returns:
        dict: Canonical portfolio status view
    """
    # --- Upstream validation ---
    def _validate_upstream():
        required = [
            ('portfolio_policy_pack_result', portfolio_policy_pack_result),
            ('portfolio_control_summary_pack_result', portfolio_control_summary_pack_result),
            ('portfolio_governance_pack_result', portfolio_governance_pack_result),
            ('portfolio_escalation_routing_pack_result', portfolio_escalation_routing_pack_result),
            ('portfolio_resolution_decision_pack_result', portfolio_resolution_decision_pack_result)
        ]
        for name, val in required:
            if not isinstance(val, dict):
                raise ValueError(f"Missing or invalid required upstream: {name}")
    _validate_upstream()

    # --- Status precedence resolution ---
    def _precedence(policy, governance, escalation, resolution):
        # Blocking/escalation outranks nominal/stable
        if escalation.get('escalation_indicator', False):
            return 'escalated', 'escalation', escalation.get('escalation_reason', 'Escalation active')
        if policy.get('portfolio_policy_decision') == 'hold_policy':
            return 'blocked', 'policy', policy.get('portfolio_policy_decision_reason', 'Policy is hold')
        if governance.get('governance_indicator', False):
            return 'governed', 'governance', governance.get('governance_reason', 'Governance active')
        if resolution.get('resolution_indicator', False):
            return 'resolution', 'resolution', resolution.get('resolution_reason', 'Resolution active')
        return 'nominal', 'default', 'No blocking/escalation/governance/resolution condition present'

    # --- Canonical status derivation ---
    def _derive_status():
        policy = portfolio_policy_pack_result
        ctrl = portfolio_control_summary_pack_result
        gov = portfolio_governance_pack_result
        esc = portfolio_escalation_routing_pack_result
        res = portfolio_resolution_decision_pack_result
        execu = portfolio_execution_pack_result or {}
        outc = portfolio_outcome_pack_result or {}
        disp = portfolio_dispatch_pack_result or {}
        actq = portfolio_action_queue_pack_result or {}
        status, source, reason = _precedence(policy, gov, esc, res)
        return {
            'portfolio_status': status,
            'portfolio_status_source': source,
            'portfolio_status_reason': reason,
            'portfolio_policy': policy,
            'portfolio_control_summary': ctrl,
            'portfolio_governance': gov,
            'portfolio_escalation': esc,
            'portfolio_resolution': res,
            'portfolio_execution': execu,
            'portfolio_outcome': outc,
            'portfolio_dispatch': disp,
            'portfolio_action_queue': actq
        }

    # --- Final stable pack assembly ---
    def _assemble():
        state = _derive_status()
        # Stable field ordering
        return {
            'portfolio_status_pack_name': 'portfolio_status_pack',
            'portfolio_status_pack_version': '1.0',
            'portfolio_status': state['portfolio_status'],
            'portfolio_status_source': state['portfolio_status_source'],
            'portfolio_status_reason': state['portfolio_status_reason'],
            'portfolio_policy': state['portfolio_policy'],
            'portfolio_control_summary': state['portfolio_control_summary'],
            'portfolio_governance': state['portfolio_governance'],
            'portfolio_escalation': state['portfolio_escalation'],
            'portfolio_resolution': state['portfolio_resolution'],
            'portfolio_execution': state['portfolio_execution'],
            'portfolio_outcome': state['portfolio_outcome'],
            'portfolio_dispatch': state['portfolio_dispatch'],
            'portfolio_action_queue': state['portfolio_action_queue']
        }

    return _assemble()
