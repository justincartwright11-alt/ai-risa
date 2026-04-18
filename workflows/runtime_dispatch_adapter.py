"""
runtime_dispatch_adapter

Thin deterministic adapter for runtime orchestrator dispatch.
"""

from workflows.runtime_orchestrator import runtime_orchestrator
from copy import deepcopy

# --- Adapter ---
def runtime_dispatch_adapter(dispatch_input):
    """
    Args:
        dispatch_input (dict): Canonical runtime dispatch input
    Returns:
        dict: Canonical adapter result
    """
    # 1. Dispatch input validation
    def _validate_dispatch_input():
        if not isinstance(dispatch_input, dict):
            return 'failed_precondition', 'Dispatch input must be a dict', True, False, 'malformed_dispatch_input'
        if 'control_plane_summary_input' not in dispatch_input or 'portfolio_summary_input' not in dispatch_input:
            return 'failed_precondition', 'Missing required dispatch input(s)', True, False, 'missing_dispatch_input'
        if not isinstance(dispatch_input['control_plane_summary_input'], dict):
            return 'failed_precondition', 'control_plane_summary_input must be a dict', True, False, 'malformed_control_plane_summary_input'
        if not isinstance(dispatch_input['portfolio_summary_input'], list):
            return 'failed_precondition', 'portfolio_summary_input must be a list', True, False, 'malformed_portfolio_summary_input'
        return None, None, False, False, None

    # 2. Canonical orchestrator invocation
    def _invoke_orchestrator():
        # Deepcopy to guarantee no mutation
        cp = deepcopy(dispatch_input['control_plane_summary_input'])
        pf = deepcopy(dispatch_input['portfolio_summary_input'])
        return runtime_orchestrator(cp, pf)

    # 3. Adapter precedence resolution
    def _resolve_adapter_state(orchestrator_result, precondition, blocker, reason, basis):
        if precondition:
            return 'failed_precondition', reason, precondition, blocker, basis
        if orchestrator_result['runtime_state'] == 'blocked':
            return 'blocked', orchestrator_result['runtime_result'], False, True, orchestrator_result['runtime_basis']
        if orchestrator_result['runtime_state'] == 'success':
            return 'dispatched', orchestrator_result['runtime_result'], False, False, orchestrator_result['runtime_basis']
        # fallback
        return 'failed_precondition', orchestrator_result['runtime_result'], True, False, orchestrator_result['runtime_basis']

    # 4. Final stable adapter payload assembly
    state, reason, precondition, blocker, basis = _validate_dispatch_input()
    orchestrator_result = None
    if state is None:
        orchestrator_result = _invoke_orchestrator()
        state, reason, precondition, blocker, basis = _resolve_adapter_state(orchestrator_result, False, False, None, None)
    else:
        orchestrator_result = {
            'runtime_state': 'failed_precondition',
            'runtime_result': reason,
            'runtime_blocker_indicator': blocker,
            'runtime_precondition_indicator': precondition,
            'runtime_basis': basis,
            'control_plane_summary_indicator': None,
            'portfolio_summary_indicator': None,
            'cross_plane_policy_indicator': None,
            'cross_plane_status_indicator': None,
            'cross_plane_closure_indicator': None,
            'cross_plane_dashboard_indicator': None,
            'cross_plane_summary_indicator': None
        }
    return {
        'dispatch_state': state,
        'dispatch_result': reason,
        'dispatch_precondition_indicator': precondition,
        'dispatch_blocker_indicator': blocker,
        'dispatch_basis': basis,
        'runtime_state': orchestrator_result['runtime_state'],
        'runtime_result': orchestrator_result['runtime_result'],
        'runtime_basis': orchestrator_result['runtime_basis'],
        'cross_plane_summary_indicator': orchestrator_result['cross_plane_summary_indicator'],
        'control_plane_summary_indicator': orchestrator_result['control_plane_summary_indicator'],
        'portfolio_summary_indicator': orchestrator_result['portfolio_summary_indicator'],
        'cross_plane_policy_indicator': orchestrator_result['cross_plane_policy_indicator'],
        'cross_plane_status_indicator': orchestrator_result['cross_plane_status_indicator'],
        'cross_plane_closure_indicator': orchestrator_result['cross_plane_closure_indicator'],
        'cross_plane_dashboard_indicator': orchestrator_result['cross_plane_dashboard_indicator'],
    }
