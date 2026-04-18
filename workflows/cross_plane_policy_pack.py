"""
cross_plane_policy_pack

Synthesizes the canonical cross-plane policy view from control-plane and portfolio-plane policy packs.
"""

def cross_plane_policy_pack(
    control_plane_policy_pack_result,
    portfolio_policy_pack_result,
    control_plane_summary_pack_result=None,
    portfolio_summary_pack_result=None,
    control_plane_dashboard_pack_result=None,
    portfolio_dashboard_pack_result=None,
    control_plane_closure_pack_result=None,
    portfolio_closure_pack_result=None,
    control_plane_status_pack_result=None,
    portfolio_status_pack_result=None
):
    """
    Args:
        control_plane_policy_pack_result (dict): Required
        portfolio_policy_pack_result (dict): Required
        control_plane_summary_pack_result (dict): Optional
        portfolio_summary_pack_result (dict): Optional
        control_plane_dashboard_pack_result (dict): Optional
        portfolio_dashboard_pack_result (dict): Optional
        control_plane_closure_pack_result (dict): Optional
        portfolio_closure_pack_result (dict): Optional
        control_plane_status_pack_result (dict): Optional
        portfolio_status_pack_result (dict): Optional
    Returns:
        dict: Canonical cross-plane policy view
    """
    # --- Upstream validation ---
    def _validate_upstream():
        required = [
            ('control_plane_policy_pack_result', control_plane_policy_pack_result),
            ('portfolio_policy_pack_result', portfolio_policy_pack_result)
        ]
        for name, val in required:
            if not isinstance(val, dict):
                raise ValueError(f"Missing or invalid required upstream: {name}")
    _validate_upstream()

    # --- Lane-precedence resolution ---
    def _precedence(control_policy, portfolio_policy):
        # Blockers/escalation/unresolved outrank nominal
        cp_state = control_policy.get('control_plane_policy_status', '')
        pf_state = portfolio_policy.get('portfolio_policy_decision', '') or portfolio_policy.get('portfolio_policy_status', '')
        cp_blocked = cp_state in ('blocked', 'escalate_policy', 'hold_policy', 'review_policy', 'partial')
        pf_blocked = pf_state in ('blocked', 'escalate_policy', 'hold_policy', 'review_policy', 'partial')
        if cp_blocked and pf_blocked:
            return 'cross_blocked', 'both', 'Both lanes blocked or escalated', True, True
        if cp_blocked:
            return 'control_plane_blocked', 'control_plane', 'Control-plane blocked or escalated', False, True
        if pf_blocked:
            return 'portfolio_blocked', 'portfolio', 'Portfolio-plane blocked or escalated', False, True
        if cp_state == 'ready' and pf_state == 'proceed_policy':
            return 'cross_nominal', 'both', 'Both lanes nominal/ready', True, False
        return 'cross_pending', 'default', 'Cross-plane policy pending further action', False, False

    # --- Canonical cross-plane policy derivation ---
    def _derive_policy():
        cp = control_plane_policy_pack_result
        pf = portfolio_policy_pack_result
        cp_sum = control_plane_summary_pack_result or {}
        pf_sum = portfolio_summary_pack_result or {}
        cp_dash = control_plane_dashboard_pack_result or {}
        pf_dash = portfolio_dashboard_pack_result or {}
        cp_clo = control_plane_closure_pack_result or {}
        pf_clo = portfolio_closure_pack_result or {}
        cp_stat = control_plane_status_pack_result or {}
        pf_stat = portfolio_status_pack_result or {}
        state, source, reason, eligible, blocked = _precedence(cp, pf)
        return {
            'cross_plane_policy_state': state,
            'cross_plane_policy_source': source,
            'cross_plane_policy_reason': reason,
            'cross_plane_policy_eligible': eligible,
            'cross_plane_policy_blocked': blocked,
            'control_plane_policy': cp,
            'portfolio_policy': pf,
            'control_plane_summary': cp_sum,
            'portfolio_summary': pf_sum,
            'control_plane_dashboard': cp_dash,
            'portfolio_dashboard': pf_dash,
            'control_plane_closure': cp_clo,
            'portfolio_closure': pf_clo,
            'control_plane_status': cp_stat,
            'portfolio_status': pf_stat
        }

    # --- Final stable pack assembly ---
    def _assemble():
        state = _derive_policy()
        # Stable field ordering
        return {
            'cross_plane_policy_pack_name': 'cross_plane_policy_pack',
            'cross_plane_policy_pack_version': '1.0',
            'cross_plane_policy_state': state['cross_plane_policy_state'],
            'cross_plane_policy_source': state['cross_plane_policy_source'],
            'cross_plane_policy_reason': state['cross_plane_policy_reason'],
            'cross_plane_policy_eligible': state['cross_plane_policy_eligible'],
            'cross_plane_policy_blocked': state['cross_plane_policy_blocked'],
            'control_plane_policy': state['control_plane_policy'],
            'portfolio_policy': state['portfolio_policy'],
            'control_plane_summary': state['control_plane_summary'],
            'portfolio_summary': state['portfolio_summary'],
            'control_plane_dashboard': state['control_plane_dashboard'],
            'portfolio_dashboard': state['portfolio_dashboard'],
            'control_plane_closure': state['control_plane_closure'],
            'portfolio_closure': state['portfolio_closure'],
            'control_plane_status': state['control_plane_status'],
            'portfolio_status': state['portfolio_status']
        }

    return _assemble()
