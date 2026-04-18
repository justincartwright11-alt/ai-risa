"""
cross_plane_closure_pack

Synthesizes the canonical cross-plane closure view from control-plane, portfolio-plane, and cross-plane status/policy packs.
"""

def cross_plane_closure_pack(
    control_plane_closure_pack_result,
    portfolio_closure_pack_result,
    cross_plane_status_pack_result,
    cross_plane_policy_pack_result,
    control_plane_status_pack_result=None,
    portfolio_status_pack_result=None,
    control_plane_policy_pack_result=None,
    portfolio_policy_pack_result=None,
    control_plane_summary_pack_result=None,
    portfolio_summary_pack_result=None,
    control_plane_dashboard_pack_result=None,
    portfolio_dashboard_pack_result=None
):
    """
    Args:
        control_plane_closure_pack_result (dict): Required
        portfolio_closure_pack_result (dict): Required
        cross_plane_status_pack_result (dict): Required
        cross_plane_policy_pack_result (dict): Required
        control_plane_status_pack_result (dict): Optional
        portfolio_status_pack_result (dict): Optional
        control_plane_policy_pack_result (dict): Optional
        portfolio_policy_pack_result (dict): Optional
        control_plane_summary_pack_result (dict): Optional
        portfolio_summary_pack_result (dict): Optional
        control_plane_dashboard_pack_result (dict): Optional
        portfolio_dashboard_pack_result (dict): Optional
    Returns:
        dict: Canonical cross-plane closure view
    """
    # --- Upstream validation ---
    def _validate_upstream():
        required = [
            ('control_plane_closure_pack_result', control_plane_closure_pack_result),
            ('portfolio_closure_pack_result', portfolio_closure_pack_result),
            ('cross_plane_status_pack_result', cross_plane_status_pack_result),
            ('cross_plane_policy_pack_result', cross_plane_policy_pack_result)
        ]
        for name, val in required:
            if not isinstance(val, dict):
                raise ValueError(f"Missing or invalid required upstream: {name}")
    _validate_upstream()

    # --- Lane-precedence and status/policy-precedence resolution ---
    def _precedence(cp_closure, pf_closure, cross_status, cross_policy):
        cp_state = cp_closure.get('control_plane_closure', '')
        pf_state = pf_closure.get('portfolio_closure', '')
        cross_status_state = cross_status.get('cross_plane_status_state', '')
        cross_policy_state = cross_policy.get('cross_plane_policy_state', '')
        # Status/policy-driven blockers outrank closure-ready/closed
        if cross_status_state in ('cross_blocked', 'control_plane_blocked', 'portfolio_blocked') or \
           cross_policy_state in ('cross_blocked', 'control_plane_blocked', 'portfolio_blocked'):
            return 'cross_blocked', 'status_policy', 'Blocked by cross-plane status/policy', False, True
        # Lane closure precedence
        cp_blocked = cp_state in ('blocked', 'escalated', 'unresolved', 'not_ready', 'partial')
        pf_blocked = pf_state in ('blocked', 'escalated', 'unresolved', 'not_ready', 'partial')
        if cp_blocked and pf_blocked:
            return 'cross_blocked', 'both', 'Both lanes blocked/escalated/unresolved/not_ready', False, True
        if cp_blocked:
            return 'control_plane_blocked', 'control_plane', 'Control-plane blocked/escalated/unresolved/not_ready', False, True
        if pf_blocked:
            return 'portfolio_blocked', 'portfolio', 'Portfolio-plane blocked/escalated/unresolved/not_ready', False, True
        # Nominal closure-ready/closed
        if cp_state in ('closure_ready', 'closed') and pf_state in ('closure_ready', 'closed') and \
           cross_status_state == 'cross_nominal' and cross_policy_state == 'cross_nominal':
            return 'cross_closure_ready', 'both', 'Both lanes closure-ready/closed', True, False
        return 'cross_pending', 'default', 'Cross-plane closure pending further action', False, False

    # --- Canonical cross-plane closure derivation ---
    def _derive_closure():
        cp = control_plane_closure_pack_result
        pf = portfolio_closure_pack_result
        cross_status = cross_plane_status_pack_result
        cross_policy = cross_plane_policy_pack_result
        cp_stat = control_plane_status_pack_result or {}
        pf_stat = portfolio_status_pack_result or {}
        cp_pol = control_plane_policy_pack_result or {}
        pf_pol = portfolio_policy_pack_result or {}
        cp_sum = control_plane_summary_pack_result or {}
        pf_sum = portfolio_summary_pack_result or {}
        cp_dash = control_plane_dashboard_pack_result or {}
        pf_dash = portfolio_dashboard_pack_result or {}
        state, source, reason, eligible, blocked = _precedence(cp, pf, cross_status, cross_policy)
        return {
            'cross_plane_closure_state': state,
            'cross_plane_closure_source': source,
            'cross_plane_closure_reason': reason,
            'cross_plane_closure_eligible': eligible,
            'cross_plane_closure_blocked': blocked,
            'control_plane_closure': cp,
            'portfolio_closure': pf,
            'cross_plane_status': cross_status,
            'cross_plane_policy': cross_policy,
            'control_plane_status': cp_stat,
            'portfolio_status': pf_stat,
            'control_plane_policy': cp_pol,
            'portfolio_policy': pf_pol,
            'control_plane_summary': cp_sum,
            'portfolio_summary': pf_sum,
            'control_plane_dashboard': cp_dash,
            'portfolio_dashboard': pf_dash
        }

    # --- Final stable pack assembly ---
    def _assemble():
        state = _derive_closure()
        # Stable field ordering
        return {
            'cross_plane_closure_pack_name': 'cross_plane_closure_pack',
            'cross_plane_closure_pack_version': '1.0',
            'cross_plane_closure_state': state['cross_plane_closure_state'],
            'cross_plane_closure_source': state['cross_plane_closure_source'],
            'cross_plane_closure_reason': state['cross_plane_closure_reason'],
            'cross_plane_closure_eligible': state['cross_plane_closure_eligible'],
            'cross_plane_closure_blocked': state['cross_plane_closure_blocked'],
            'control_plane_closure': state['control_plane_closure'],
            'portfolio_closure': state['portfolio_closure'],
            'cross_plane_status': state['cross_plane_status'],
            'cross_plane_policy': state['cross_plane_policy'],
            'control_plane_status': state['control_plane_status'],
            'portfolio_status': state['portfolio_status'],
            'control_plane_policy': state['control_plane_policy'],
            'portfolio_policy': state['portfolio_policy'],
            'control_plane_summary': state['control_plane_summary'],
            'portfolio_summary': state['portfolio_summary'],
            'control_plane_dashboard': state['control_plane_dashboard'],
            'portfolio_dashboard': state['portfolio_dashboard']
        }

    return _assemble()
