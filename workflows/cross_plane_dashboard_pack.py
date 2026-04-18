"""
cross_plane_dashboard_pack

Synthesizes the canonical cross-plane dashboard view from control-plane, portfolio-plane, and cross-plane closure/status/policy packs.
"""

def cross_plane_dashboard_pack(
    control_plane_dashboard_pack_result,
    portfolio_dashboard_pack_result,
    cross_plane_closure_pack_result,
    cross_plane_status_pack_result,
    cross_plane_policy_pack_result,
    control_plane_summary_pack_result=None,
    portfolio_summary_pack_result=None,
    control_plane_closure_pack_result=None,
    portfolio_closure_pack_result=None,
    control_plane_status_pack_result=None,
    portfolio_status_pack_result=None,
    control_plane_policy_pack_result=None,
    portfolio_policy_pack_result=None
):
    """
    Args:
        control_plane_dashboard_pack_result (dict): Required
        portfolio_dashboard_pack_result (dict): Required
        cross_plane_closure_pack_result (dict): Required
        cross_plane_status_pack_result (dict): Required
        cross_plane_policy_pack_result (dict): Required
        control_plane_summary_pack_result (dict): Optional
        portfolio_summary_pack_result (dict): Optional
        control_plane_closure_pack_result (dict): Optional
        portfolio_closure_pack_result (dict): Optional
        control_plane_status_pack_result (dict): Optional
        portfolio_status_pack_result (dict): Optional
        control_plane_policy_pack_result (dict): Optional
        portfolio_policy_pack_result (dict): Optional
    Returns:
        dict: Canonical cross-plane dashboard view
    """
    # --- Upstream validation ---
    def _validate_upstream():
        required = [
            ('control_plane_dashboard_pack_result', control_plane_dashboard_pack_result),
            ('portfolio_dashboard_pack_result', portfolio_dashboard_pack_result),
            ('cross_plane_closure_pack_result', cross_plane_closure_pack_result),
            ('cross_plane_status_pack_result', cross_plane_status_pack_result),
            ('cross_plane_policy_pack_result', cross_plane_policy_pack_result)
        ]
        for name, val in required:
            if not isinstance(val, dict):
                raise ValueError(f"Missing or invalid required upstream: {name}")
    _validate_upstream()

    # --- Lane-precedence and closure/status/policy-precedence resolution ---
    def _precedence(cp_dash, pf_dash, cross_closure, cross_status, cross_policy):
        cp_state = cp_dash.get('control_plane_dashboard', '')
        pf_state = pf_dash.get('portfolio_dashboard', '')
        cross_closure_state = cross_closure.get('cross_plane_closure_state', '')
        cross_status_state = cross_status.get('cross_plane_status_state', '')
        cross_policy_state = cross_policy.get('cross_plane_policy_state', '')
        # Closure/status/policy-driven blockers outrank nominal dashboard
        if cross_closure_state in ('cross_blocked', 'control_plane_blocked', 'portfolio_blocked') or \
           cross_status_state in ('cross_blocked', 'control_plane_blocked', 'portfolio_blocked') or \
           cross_policy_state in ('cross_blocked', 'control_plane_blocked', 'portfolio_blocked'):
            return 'cross_blocked', 'closure_status_policy', 'Blocked by cross-plane closure/status/policy', True, True, False
        # Lane dashboard precedence
        cp_blocked = cp_state in ('blocked', 'escalated', 'unresolved', 'degraded', 'not_ready', 'partial')
        pf_blocked = pf_state in ('blocked', 'escalated', 'unresolved', 'degraded', 'not_ready', 'partial')
        if cp_blocked and pf_blocked:
            return 'cross_blocked', 'both', 'Both lanes blocked/escalated/unresolved/degraded/not_ready', True, True, False
        if cp_blocked:
            return 'control_plane_blocked', 'control_plane', 'Control-plane blocked/escalated/unresolved/degraded/not_ready', True, True, False
        if pf_blocked:
            return 'portfolio_blocked', 'portfolio', 'Portfolio-plane blocked/escalated/unresolved/degraded/not_ready', True, True, False
        # Nominal dashboard
        if cp_state == 'nominal' and pf_state == 'nominal' and \
           cross_closure_state == 'cross_closure_ready' and \
           cross_status_state == 'cross_nominal' and \
           cross_policy_state == 'cross_nominal':
            return 'cross_nominal', 'both', 'Both lanes nominal/clean', False, False, True
        return 'cross_pending', 'default', 'Cross-plane dashboard pending further action', False, False, False

    # --- Canonical cross-plane dashboard derivation ---
    def _derive_dashboard():
        cp = control_plane_dashboard_pack_result
        pf = portfolio_dashboard_pack_result
        cross_closure = cross_plane_closure_pack_result
        cross_status = cross_plane_status_pack_result
        cross_policy = cross_plane_policy_pack_result
        cp_sum = control_plane_summary_pack_result or {}
        pf_sum = portfolio_summary_pack_result or {}
        cp_clo = control_plane_closure_pack_result or {}
        pf_clo = portfolio_closure_pack_result or {}
        cp_stat = control_plane_status_pack_result or {}
        pf_stat = portfolio_status_pack_result or {}
        cp_pol = control_plane_policy_pack_result or {}
        pf_pol = portfolio_policy_pack_result or {}
        state, source, reason, blocked, escalated, nominal = _precedence(cp, pf, cross_closure, cross_status, cross_policy)
        return {
            'cross_plane_dashboard_state': state,
            'cross_plane_dashboard_source': source,
            'cross_plane_dashboard_reason': reason,
            'cross_plane_dashboard_blocked': blocked,
            'cross_plane_dashboard_escalated': escalated,
            'cross_plane_dashboard_nominal': nominal,
            'control_plane_dashboard': cp,
            'portfolio_dashboard': pf,
            'cross_plane_closure': cross_closure,
            'cross_plane_status': cross_status,
            'cross_plane_policy': cross_policy,
            'control_plane_summary': cp_sum,
            'portfolio_summary': pf_sum,
            'control_plane_closure': cp_clo,
            'portfolio_closure': pf_clo,
            'control_plane_status': cp_stat,
            'portfolio_status': pf_stat,
            'control_plane_policy': cp_pol,
            'portfolio_policy': pf_pol
        }

    # --- Final stable pack assembly ---
    def _assemble():
        state = _derive_dashboard()
        # Stable field ordering
        return {
            'cross_plane_dashboard_pack_name': 'cross_plane_dashboard_pack',
            'cross_plane_dashboard_pack_version': '1.0',
            'cross_plane_dashboard_state': state['cross_plane_dashboard_state'],
            'cross_plane_dashboard_source': state['cross_plane_dashboard_source'],
            'cross_plane_dashboard_reason': state['cross_plane_dashboard_reason'],
            'cross_plane_dashboard_blocked': state['cross_plane_dashboard_blocked'],
            'cross_plane_dashboard_escalated': state['cross_plane_dashboard_escalated'],
            'cross_plane_dashboard_nominal': state['cross_plane_dashboard_nominal'],
            'control_plane_dashboard': state['control_plane_dashboard'],
            'portfolio_dashboard': state['portfolio_dashboard'],
            'cross_plane_closure': state['cross_plane_closure'],
            'cross_plane_status': state['cross_plane_status'],
            'cross_plane_policy': state['cross_plane_policy'],
            'control_plane_summary': state['control_plane_summary'],
            'portfolio_summary': state['portfolio_summary'],
            'control_plane_closure': state['control_plane_closure'],
            'portfolio_closure': state['portfolio_closure'],
            'control_plane_status': state['control_plane_status'],
            'portfolio_status': state['portfolio_status'],
            'control_plane_policy': state['control_plane_policy'],
            'portfolio_policy': state['portfolio_policy']
        }

    return _assemble()
