"""
cross_plane_summary_pack

Synthesizes the canonical cross-plane summary view from control-plane, portfolio-plane, and cross-plane dashboard/closure/status/policy packs.
"""

def cross_plane_summary_pack(
    control_plane_summary_pack_result,
    portfolio_summary_pack_result,
    cross_plane_dashboard_pack_result,
    cross_plane_closure_pack_result,
    cross_plane_status_pack_result,
    cross_plane_policy_pack_result,
    control_plane_dashboard_pack_result=None,
    portfolio_dashboard_pack_result=None,
    control_plane_closure_pack_result=None,
    portfolio_closure_pack_result=None,
    control_plane_status_pack_result=None,
    portfolio_status_pack_result=None,
    control_plane_policy_pack_result=None,
    portfolio_policy_pack_result=None
):
    """
    Args:
        control_plane_summary_pack_result (dict): Required
        portfolio_summary_pack_result (dict): Required
        cross_plane_dashboard_pack_result (dict): Required
        cross_plane_closure_pack_result (dict): Required
        cross_plane_status_pack_result (dict): Required
        cross_plane_policy_pack_result (dict): Required
        control_plane_dashboard_pack_result (dict): Optional
        portfolio_dashboard_pack_result (dict): Optional
        control_plane_closure_pack_result (dict): Optional
        portfolio_closure_pack_result (dict): Optional
        control_plane_status_pack_result (dict): Optional
        portfolio_status_pack_result (dict): Optional
        control_plane_policy_pack_result (dict): Optional
        portfolio_policy_pack_result (dict): Optional
    Returns:
        dict: Canonical cross-plane summary view
    """
    # --- Upstream validation ---
    def _validate_upstream():
        required = [
            ('control_plane_summary_pack_result', control_plane_summary_pack_result),
            ('portfolio_summary_pack_result', portfolio_summary_pack_result),
            ('cross_plane_dashboard_pack_result', cross_plane_dashboard_pack_result),
            ('cross_plane_closure_pack_result', cross_plane_closure_pack_result),
            ('cross_plane_status_pack_result', cross_plane_status_pack_result),
            ('cross_plane_policy_pack_result', cross_plane_policy_pack_result)
        ]
        for name, val in required:
            if not isinstance(val, dict):
                raise ValueError(f"Missing or invalid required upstream: {name}")
    _validate_upstream()

    # --- Lane-precedence and dashboard/closure/status/policy-precedence resolution ---
    def _precedence(cp_sum, pf_sum, cross_dash, cross_closure, cross_status, cross_policy):
        cp_state = cp_sum.get('control_plane_summary', '')
        pf_state = pf_sum.get('portfolio_summary', '')
        cross_dash_state = cross_dash.get('cross_plane_dashboard_state', '')
        cross_closure_state = cross_closure.get('cross_plane_closure_state', '')
        cross_status_state = cross_status.get('cross_plane_status_state', '')
        cross_policy_state = cross_policy.get('cross_plane_policy_state', '')
        # Dashboard/closure/status/policy-driven blockers outrank nominal summary
        if cross_dash_state in ('cross_blocked', 'control_plane_blocked', 'portfolio_blocked') or \
           cross_closure_state in ('cross_blocked', 'control_plane_blocked', 'portfolio_blocked') or \
           cross_status_state in ('cross_blocked', 'control_plane_blocked', 'portfolio_blocked') or \
           cross_policy_state in ('cross_blocked', 'control_plane_blocked', 'portfolio_blocked'):
            return 'cross_blocked', 'dashboard_closure_status_policy', 'Blocked by cross-plane dashboard/closure/status/policy', True, True, False
        # Lane summary precedence
        cp_blocked = cp_state in ('blocked', 'escalated', 'unresolved', 'degraded', 'not_ready', 'partial')
        pf_blocked = pf_state in ('blocked', 'escalated', 'unresolved', 'degraded', 'not_ready', 'partial')
        if cp_blocked and pf_blocked:
            return 'cross_blocked', 'both', 'Both lanes blocked/escalated/unresolved/degraded/not_ready', True, True, False
        if cp_blocked:
            return 'control_plane_blocked', 'control_plane', 'Control-plane blocked/escalated/unresolved/degraded/not_ready', True, True, False
        if pf_blocked:
            return 'portfolio_blocked', 'portfolio', 'Portfolio-plane blocked/escalated/unresolved/degraded/not_ready', True, True, False
        # Nominal summary
        if cp_state == 'nominal' and pf_state == 'nominal' and \
           cross_dash_state == 'cross_nominal' and \
           cross_closure_state == 'cross_closure_ready' and \
           cross_status_state == 'cross_nominal' and \
           cross_policy_state == 'cross_nominal':
            return 'cross_nominal', 'both', 'Both lanes nominal/clean', False, False, True
        return 'cross_pending', 'default', 'Cross-plane summary pending further action', False, False, False

    # --- Canonical cross-plane summary derivation ---
    def _derive_summary():
        cp = control_plane_summary_pack_result
        pf = portfolio_summary_pack_result
        cross_dash = cross_plane_dashboard_pack_result
        cross_closure = cross_plane_closure_pack_result
        cross_status = cross_plane_status_pack_result
        cross_policy = cross_plane_policy_pack_result
        cp_dash = control_plane_dashboard_pack_result or {}
        pf_dash = portfolio_dashboard_pack_result or {}
        cp_clo = control_plane_closure_pack_result or {}
        pf_clo = portfolio_closure_pack_result or {}
        cp_stat = control_plane_status_pack_result or {}
        pf_stat = portfolio_status_pack_result or {}
        cp_pol = control_plane_policy_pack_result or {}
        pf_pol = portfolio_policy_pack_result or {}
        state, source, reason, blocked, escalated, nominal = _precedence(cp, pf, cross_dash, cross_closure, cross_status, cross_policy)
        return {
            'cross_plane_summary_state': state,
            'cross_plane_summary_source': source,
            'cross_plane_summary_reason': reason,
            'cross_plane_summary_blocked': blocked,
            'cross_plane_summary_escalated': escalated,
            'cross_plane_summary_nominal': nominal,
            'control_plane_summary': cp,
            'portfolio_summary': pf,
            'cross_plane_dashboard': cross_dash,
            'cross_plane_closure': cross_closure,
            'cross_plane_status': cross_status,
            'cross_plane_policy': cross_policy,
            'control_plane_dashboard': cp_dash,
            'portfolio_dashboard': pf_dash,
            'control_plane_closure': cp_clo,
            'portfolio_closure': pf_clo,
            'control_plane_status': cp_stat,
            'portfolio_status': pf_stat,
            'control_plane_policy': cp_pol,
            'portfolio_policy': pf_pol
        }

    # --- Final stable pack assembly ---
    def _assemble():
        state = _derive_summary()
        # Stable field ordering
        return {
            'cross_plane_summary_pack_name': 'cross_plane_summary_pack',
            'cross_plane_summary_pack_version': '1.0',
            'cross_plane_summary_state': state['cross_plane_summary_state'],
            'cross_plane_summary_source': state['cross_plane_summary_source'],
            'cross_plane_summary_reason': state['cross_plane_summary_reason'],
            'cross_plane_summary_blocked': state['cross_plane_summary_blocked'],
            'cross_plane_summary_escalated': state['cross_plane_summary_escalated'],
            'cross_plane_summary_nominal': state['cross_plane_summary_nominal'],
            'control_plane_summary': state['control_plane_summary'],
            'portfolio_summary': state['portfolio_summary'],
            'cross_plane_dashboard': state['cross_plane_dashboard'],
            'cross_plane_closure': state['cross_plane_closure'],
            'cross_plane_status': state['cross_plane_status'],
            'cross_plane_policy': state['cross_plane_policy'],
            'control_plane_dashboard': state['control_plane_dashboard'],
            'portfolio_dashboard': state['portfolio_dashboard'],
            'control_plane_closure': state['control_plane_closure'],
            'portfolio_closure': state['portfolio_closure'],
            'control_plane_status': state['control_plane_status'],
            'portfolio_status': state['portfolio_status'],
            'control_plane_policy': state['control_plane_policy'],
            'portfolio_policy': state['portfolio_policy']
        }

    return _assemble()
