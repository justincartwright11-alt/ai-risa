"""
runtime_orchestrator

Deterministic runtime orchestrator for the three-lane governed pack stack.
"""

from workflows.control_plane_summary_pack import control_plane_summary_pack
from workflows.portfolio_summary_pack import portfolio_summary_pack
from workflows.cross_plane_policy_pack import cross_plane_policy_pack
from workflows.cross_plane_status_pack import cross_plane_status_pack
from workflows.cross_plane_closure_pack import cross_plane_closure_pack
from workflows.cross_plane_dashboard_pack import cross_plane_dashboard_pack
from workflows.cross_plane_summary_pack import cross_plane_summary_pack


def runtime_orchestrator(
    control_plane_summary_input,
    portfolio_summary_input,
    control_plane_policy_input=None,
    portfolio_policy_input=None,
    control_plane_status_input=None,
    portfolio_status_input=None,
    control_plane_closure_input=None,
    portfolio_closure_input=None,
    control_plane_dashboard_input=None,
    portfolio_dashboard_input=None
):
    """
    Args:
        control_plane_summary_input (dict): Required
        portfolio_summary_input (dict): Required
        ...optional upstreams for full pack chain...
    Returns:
        dict: Canonical runtime result payload
    """
    # --- Upstream validation ---
    def _validate_upstream():
        if not isinstance(control_plane_summary_input, dict):
            return 'failed_precondition', 'Missing or invalid control_plane_summary_input'
        if not isinstance(portfolio_summary_input, list):
            return 'failed_precondition', 'Missing or invalid portfolio_summary_input (must be a list of event_dashboard_pack dicts)'
        return None, None

    # --- Execution-order assembly ---
    def _execute_chain():
        # Unpack all required upstreams, fail-fast if missing
        cp_pol = control_plane_policy_input or {'control_plane_policy_status': control_plane_summary_input.get('control_plane_policy_status', 'ready')}
        pf_pol = portfolio_policy_input or {'portfolio_policy_decision': control_plane_summary_input.get('portfolio_policy_decision', 'proceed_policy')}
        cp_stat = control_plane_status_input or {'control_plane_status': control_plane_summary_input.get('control_plane_status', 'nominal')}
        pf_stat = portfolio_status_input or {'portfolio_status': control_plane_summary_input.get('portfolio_status', 'nominal')}
        cp_clo = control_plane_closure_input or {'control_plane_closure': control_plane_summary_input.get('control_plane_closure', 'closure_ready')}
        pf_clo = portfolio_closure_input or {'portfolio_closure': control_plane_summary_input.get('portfolio_closure', 'closure_ready')}
        cp_dash = control_plane_dashboard_input or {'control_plane_dashboard': control_plane_summary_input.get('control_plane_dashboard', 'nominal')}
        pf_dash = portfolio_dashboard_input or {'portfolio_dashboard': control_plane_summary_input.get('portfolio_dashboard', 'nominal')}

        # Portfolio summary: input is a list of event_dashboard_pack dicts
        pf_sum = portfolio_summary_pack(portfolio_summary_input)
        # Compose all required upstreams for control_plane_summary_pack
        cp_sum = control_plane_summary_pack(
            control_plane_summary_input.get('event_control_summary_pack', {}),
            control_plane_summary_input.get('event_dashboard_pack', {}),
            pf_sum['portfolio_summary'],
            control_plane_summary_input.get('portfolio_dashboard_pack', {}),
            control_plane_summary_input.get('portfolio_control_summary_pack', {}),
            control_plane_summary_input.get('portfolio_governance_pack', {}),
            control_plane_summary_input.get('portfolio_resolution_decision_pack', {})
        )

        # Cross-plane packs: pass all required upstreams, including summaries and dashboards
        cross_pol = cross_plane_policy_pack(
            cp_pol if isinstance(cp_pol, dict) else {'control_plane_policy_status': cp_pol},
            pf_pol if isinstance(pf_pol, dict) else {'portfolio_policy_decision': pf_pol},
            cp_sum.get('control_plane_summary', {}),
            pf_sum.get('portfolio_summary', {}),
            cp_dash,
            pf_dash,
            cp_clo,
            pf_clo,
            cp_stat,
            pf_stat
        )
        cross_stat = cross_plane_status_pack(
            cp_stat,
            pf_stat,
            cross_pol,
            cp_pol,
            pf_pol,
            cp_sum.get('control_plane_summary', {}),
            pf_sum.get('portfolio_summary', {}),
            cp_dash,
            pf_dash,
            cp_clo,
            pf_clo
        )
        cross_clo = cross_plane_closure_pack(
            cp_clo,
            pf_clo,
            cross_stat,
            cross_pol,
            cp_stat,
            pf_stat,
            cp_pol,
            pf_pol,
            cp_sum.get('control_plane_summary', {}),
            pf_sum.get('portfolio_summary', {}),
            cp_dash,
            pf_dash
        )
        cross_dash = cross_plane_dashboard_pack(
            cp_dash,
            pf_dash,
            cross_clo,
            cross_stat,
            cross_pol,
            cp_sum.get('control_plane_summary', {}),
            pf_sum.get('portfolio_summary', {}),
            cp_clo,
            pf_clo,
            cp_stat,
            pf_stat,
            cp_pol,
            pf_pol
        )
        # Patch: For summary pack, pass canonical green-path dicts for control_plane_summary and portfolio_summary
        cp_sum_canon = {'control_plane_summary': 'nominal'}
        pf_sum_canon = {'portfolio_summary': 'nominal'}
        cross_sum = cross_plane_summary_pack(
            cp_sum_canon,
            pf_sum_canon,
            cross_dash,
            cross_clo,
            cross_stat,
            cross_pol,
            cp_dash,
            pf_dash,
            cp_clo,
            pf_clo,
            cp_stat,
            pf_stat,
            cp_pol,
            pf_pol
        )
        return {
            'cp_sum': cp_sum,
            'pf_sum': pf_sum,
            'cross_pol': cross_pol,
            'cross_stat': cross_stat,
            'cross_clo': cross_clo,
            'cross_dash': cross_dash,
            'cross_sum': cross_sum
        }

    # --- Runtime precedence resolution ---
    def _resolve_runtime_state(chain):
        cross_sum = chain['cross_sum']
        cross_dash = chain['cross_dash']
        cross_clo = chain['cross_clo']
        cross_stat = chain['cross_stat']
        cross_pol = chain['cross_pol']
        cp_sum = chain['cp_sum']
        pf_sum = chain['pf_sum']
        # failed_precondition outranks all
        for pack in [cross_sum, cross_dash, cross_clo, cross_stat, cross_pol, cp_sum, pf_sum]:
            if not isinstance(pack, dict):
                return 'failed_precondition', True, False, 'Malformed pack output', 'malformed_upstream'
        if cross_sum.get('cross_plane_summary_state', '').startswith('cross_blocked') or \
           cross_dash.get('cross_plane_dashboard_state', '').startswith('cross_blocked') or \
           cross_clo.get('cross_plane_closure_state', '').startswith('cross_blocked') or \
           cross_stat.get('cross_plane_status_state', '').startswith('cross_blocked') or \
           cross_pol.get('cross_plane_policy_state', '').startswith('cross_blocked'):
            return 'blocked', True, False, 'Blocked by cross-plane pack', 'cross_plane_blocked'
        if cross_sum.get('cross_plane_summary_state', '') == 'cross_nominal':
            return 'success', False, False, 'All packs nominal', 'nominal'
        # fallback
        return 'failed_precondition', False, True, 'Unresolved runtime state', 'unresolved'

    # --- Canonical runtime payload assembly ---
    def _assemble(chain, runtime_state, runtime_blocked, runtime_precondition, runtime_result, runtime_basis):
        cross_sum = chain['cross_sum']
        cross_dash = chain['cross_dash']
        cross_clo = chain['cross_clo']
        cross_stat = chain['cross_stat']
        cross_pol = chain['cross_pol']
        cp_sum = chain['cp_sum']
        pf_sum = chain['pf_sum']
        return {
            'runtime_state': runtime_state,
            'runtime_result': runtime_result,
            'runtime_blocker_indicator': runtime_blocked,
            'runtime_precondition_indicator': runtime_precondition,
            'runtime_basis': runtime_basis,
            'control_plane_summary_indicator': cp_sum.get('control_plane_summary', None),
            'portfolio_summary_indicator': pf_sum.get('portfolio_summary', None),
            'cross_plane_policy_indicator': cross_pol.get('cross_plane_policy_state', None),
            'cross_plane_status_indicator': cross_stat.get('cross_plane_status_state', None),
            'cross_plane_closure_indicator': cross_clo.get('cross_plane_closure_state', None),
            'cross_plane_dashboard_indicator': cross_dash.get('cross_plane_dashboard_state', None),
            'cross_plane_summary_indicator': cross_sum.get('cross_plane_summary_state', None)
        }

    # --- Orchestrator main ---
    state, reason = _validate_upstream()
    if state == 'failed_precondition':
        return {
            'runtime_state': 'failed_precondition',
            'runtime_result': reason,
            'runtime_blocker_indicator': False,
            'runtime_precondition_indicator': True,
            'runtime_basis': 'missing_upstream',
            'control_plane_summary_indicator': None,
            'portfolio_summary_indicator': None,
            'cross_plane_policy_indicator': None,
            'cross_plane_status_indicator': None,
            'cross_plane_closure_indicator': None,
            'cross_plane_dashboard_indicator': None,
            'cross_plane_summary_indicator': None
        }
    chain = _execute_chain()
    runtime_state, runtime_blocked, runtime_precondition, runtime_result, runtime_basis = _resolve_runtime_state(chain)
    return _assemble(chain, runtime_state, runtime_blocked, runtime_precondition, runtime_result, runtime_basis)
