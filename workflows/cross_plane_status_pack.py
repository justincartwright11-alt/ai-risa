"""
cross_plane_status_pack

Synthesizes the canonical cross-plane status view from control-plane, portfolio-plane, and cross-plane policy packs.
"""

def cross_plane_status_pack(
    control_plane_status_pack_result,
    portfolio_status_pack_result,
    cross_plane_policy_pack_result,
    control_plane_policy_pack_result=None,
    portfolio_policy_pack_result=None,
    control_plane_summary_pack_result=None,
    portfolio_summary_pack_result=None,
    control_plane_dashboard_pack_result=None,
    portfolio_dashboard_pack_result=None,
    control_plane_closure_pack_result=None,
    portfolio_closure_pack_result=None
):
    """
    Args:
        control_plane_status_pack_result (dict): Required
        portfolio_status_pack_result (dict): Required
        cross_plane_policy_pack_result (dict): Required
        control_plane_policy_pack_result (dict): Optional
        portfolio_policy_pack_result (dict): Optional
        control_plane_summary_pack_result (dict): Optional
        portfolio_summary_pack_result (dict): Optional
        control_plane_dashboard_pack_result (dict): Optional
        portfolio_dashboard_pack_result (dict): Optional
        control_plane_closure_pack_result (dict): Optional
        portfolio_closure_pack_result (dict): Optional
    Returns:
        dict: Canonical cross-plane status view
    """
    # --- Upstream validation ---
    def _validate_upstream():
        required = [
            ('control_plane_status_pack_result', control_plane_status_pack_result),
            ('portfolio_status_pack_result', portfolio_status_pack_result),
            ('cross_plane_policy_pack_result', cross_plane_policy_pack_result)
        ]
        for name, val in required:
            if not isinstance(val, dict):
                raise ValueError(f"Missing or invalid required upstream: {name}")
    _validate_upstream()

    # --- Lane-precedence and policy-precedence resolution ---
    def _precedence(cp_status, pf_status, cross_policy):
        cp_state = cp_status.get('control_plane_status', '')
        pf_state = pf_status.get('portfolio_status', '')
        cross_policy_state = cross_policy.get('cross_plane_policy_state', '')
        # Policy-driven blockers outrank nominal status
        if cross_policy_state in ('cross_blocked', 'control_plane_blocked', 'portfolio_blocked'):
            return 'cross_blocked', 'policy', 'Blocked by cross-plane policy', True, True
        # Lane status precedence
        cp_blocked = cp_state in ('blocked', 'escalated', 'degraded', 'unresolved', 'partial')
        pf_blocked = pf_state in ('blocked', 'escalated', 'degraded', 'unresolved', 'partial')
        if cp_blocked and pf_blocked:
            return 'cross_blocked', 'both', 'Both lanes blocked/escalated/degraded/unresolved', True, True
        if cp_blocked:
            return 'control_plane_blocked', 'control_plane', 'Control-plane blocked/escalated/degraded/unresolved', False, True
        if pf_blocked:
            return 'portfolio_blocked', 'portfolio', 'Portfolio-plane blocked/escalated/degraded/unresolved', False, True
        # Nominal
        if cp_state == 'nominal' and pf_state == 'nominal' and cross_policy_state == 'cross_nominal':
            return 'cross_nominal', 'both', 'Both lanes nominal/clean', True, False
        return 'cross_pending', 'default', 'Cross-plane status pending further action', False, False

    # --- Canonical cross-plane status derivation ---
    def _derive_status():
        cp = control_plane_status_pack_result
        pf = portfolio_status_pack_result
        cross_policy = cross_plane_policy_pack_result
        cp_pol = control_plane_policy_pack_result or {}
        pf_pol = portfolio_policy_pack_result or {}
        cp_sum = control_plane_summary_pack_result or {}
        pf_sum = portfolio_summary_pack_result or {}
        cp_dash = control_plane_dashboard_pack_result or {}
        pf_dash = portfolio_dashboard_pack_result or {}
        cp_clo = control_plane_closure_pack_result or {}
        pf_clo = portfolio_closure_pack_result or {}
        state, source, reason, eligible, blocked = _precedence(cp, pf, cross_policy)
        return {
            'cross_plane_status_state': state,
            'cross_plane_status_source': source,
            'cross_plane_status_reason': reason,
            'cross_plane_status_eligible': eligible,
            'cross_plane_status_blocked': blocked,
            'control_plane_status': cp,
            'portfolio_status': pf,
            'cross_plane_policy': cross_policy,
            'control_plane_policy': cp_pol,
            'portfolio_policy': pf_pol,
            'control_plane_summary': cp_sum,
            'portfolio_summary': pf_sum,
            'control_plane_dashboard': cp_dash,
            'portfolio_dashboard': pf_dash,
            'control_plane_closure': cp_clo,
            'portfolio_closure': pf_clo
        }

    # --- Final stable pack assembly ---
    def _assemble():
        state = _derive_status()
        # Stable field ordering
        return {
            'cross_plane_status_pack_name': 'cross_plane_status_pack',
            'cross_plane_status_pack_version': '1.0',
            'cross_plane_status_state': state['cross_plane_status_state'],
            'cross_plane_status_source': state['cross_plane_status_source'],
            'cross_plane_status_reason': state['cross_plane_status_reason'],
            'cross_plane_status_eligible': state['cross_plane_status_eligible'],
            'cross_plane_status_blocked': state['cross_plane_status_blocked'],
            'control_plane_status': state['control_plane_status'],
            'portfolio_status': state['portfolio_status'],
            'cross_plane_policy': state['cross_plane_policy'],
            'control_plane_policy': state['control_plane_policy'],
            'portfolio_policy': state['portfolio_policy'],
            'control_plane_summary': state['control_plane_summary'],
            'portfolio_summary': state['portfolio_summary'],
            'control_plane_dashboard': state['control_plane_dashboard'],
            'portfolio_dashboard': state['portfolio_dashboard'],
            'control_plane_closure': state['control_plane_closure'],
            'portfolio_closure': state['portfolio_closure']
        }

    return _assemble()
