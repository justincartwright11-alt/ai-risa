"""
portfolio_closure_pack

Projects the canonical portfolio closure state from all upstream portfolio packs.
"""

def portfolio_closure_pack(
    portfolio_status_pack_result,
    portfolio_policy_pack_result,
    portfolio_resolution_decision_pack_result,
    portfolio_escalation_routing_pack_result,
    portfolio_governance_pack_result,
    portfolio_control_summary_pack_result,
    portfolio_outcome_pack_result=None,
    portfolio_execution_pack_result=None,
    portfolio_dispatch_pack_result=None,
    portfolio_action_queue_pack_result=None
):
    """
    Args:
        portfolio_status_pack_result (dict): Required
        portfolio_policy_pack_result (dict): Required
        portfolio_resolution_decision_pack_result (dict): Required
        portfolio_escalation_routing_pack_result (dict): Required
        portfolio_governance_pack_result (dict): Required
        portfolio_control_summary_pack_result (dict): Required
        portfolio_outcome_pack_result (dict): Optional
        portfolio_execution_pack_result (dict): Optional
        portfolio_dispatch_pack_result (dict): Optional
        portfolio_action_queue_pack_result (dict): Optional
    Returns:
        dict: Canonical portfolio closure view
    """
    # --- Upstream validation ---
    def _validate_upstream():
        required = [
            ('portfolio_status_pack_result', portfolio_status_pack_result),
            ('portfolio_policy_pack_result', portfolio_policy_pack_result),
            ('portfolio_resolution_decision_pack_result', portfolio_resolution_decision_pack_result),
            ('portfolio_escalation_routing_pack_result', portfolio_escalation_routing_pack_result),
            ('portfolio_governance_pack_result', portfolio_governance_pack_result),
            ('portfolio_control_summary_pack_result', portfolio_control_summary_pack_result)
        ]
        for name, val in required:
            if not isinstance(val, dict):
                raise ValueError(f"Missing or invalid required upstream: {name}")
    _validate_upstream()

    # --- Closure precedence resolution ---
    def _precedence(status, policy, escalation, governance, resolution):
        # Blockers / escalation / unresolved governance outrank closure-ready
        if escalation.get('escalation_indicator', False):
            return 'blocked', 'escalation', escalation.get('escalation_reason', 'Escalation active'), False, True
        if status.get('portfolio_status') == 'escalated':
            return 'blocked', 'status', status.get('portfolio_status_reason', 'Escalation in status'), False, True
        if policy.get('portfolio_policy_decision') == 'hold_policy':
            return 'blocked', 'policy', policy.get('portfolio_policy_decision_reason', 'Policy is hold'), False, True
        if governance.get('governance_indicator', False):
            return 'blocked', 'governance', governance.get('governance_reason', 'Governance active'), False, True
        if resolution.get('resolution_indicator', False) and not resolution.get('resolution_ready', False):
            return 'blocked', 'resolution', resolution.get('resolution_reason', 'Resolution not ready'), False, True
        if status.get('portfolio_status') == 'nominal' and policy.get('portfolio_policy_decision') == 'proceed_policy' and resolution.get('resolution_ready', True):
            return 'closed', 'nominal', 'All closure conditions satisfied', True, False
        return 'pending', 'default', 'Closure pending further action', False, False

    # --- Closure eligibility derivation ---
    def _derive_closure():
        status = portfolio_status_pack_result
        policy = portfolio_policy_pack_result
        escalation = portfolio_escalation_routing_pack_result
        governance = portfolio_governance_pack_result
        resolution = portfolio_resolution_decision_pack_result
        ctrl = portfolio_control_summary_pack_result
        outc = portfolio_outcome_pack_result or {}
        execu = portfolio_execution_pack_result or {}
        disp = portfolio_dispatch_pack_result or {}
        actq = portfolio_action_queue_pack_result or {}
        closure_state, source, reason, eligible, blocked = _precedence(status, policy, escalation, governance, resolution)
        return {
            'portfolio_closure_state': closure_state,
            'portfolio_closure_source': source,
            'portfolio_closure_reason': reason,
            'portfolio_closure_eligible': eligible,
            'portfolio_closure_blocked': blocked,
            'portfolio_status': status,
            'portfolio_policy': policy,
            'portfolio_resolution': resolution,
            'portfolio_escalation': escalation,
            'portfolio_governance': governance,
            'portfolio_control_summary': ctrl,
            'portfolio_outcome': outc,
            'portfolio_execution': execu,
            'portfolio_dispatch': disp,
            'portfolio_action_queue': actq
        }

    # --- Final stable pack assembly ---
    def _assemble():
        state = _derive_closure()
        # Stable field ordering
        return {
            'portfolio_closure_pack_name': 'portfolio_closure_pack',
            'portfolio_closure_pack_version': '1.0',
            'portfolio_closure_state': state['portfolio_closure_state'],
            'portfolio_closure_source': state['portfolio_closure_source'],
            'portfolio_closure_reason': state['portfolio_closure_reason'],
            'portfolio_closure_eligible': state['portfolio_closure_eligible'],
            'portfolio_closure_blocked': state['portfolio_closure_blocked'],
            'portfolio_status': state['portfolio_status'],
            'portfolio_policy': state['portfolio_policy'],
            'portfolio_resolution': state['portfolio_resolution'],
            'portfolio_escalation': state['portfolio_escalation'],
            'portfolio_governance': state['portfolio_governance'],
            'portfolio_control_summary': state['portfolio_control_summary'],
            'portfolio_outcome': state['portfolio_outcome'],
            'portfolio_execution': state['portfolio_execution'],
            'portfolio_dispatch': state['portfolio_dispatch'],
            'portfolio_action_queue': state['portfolio_action_queue']
        }

    return _assemble()
