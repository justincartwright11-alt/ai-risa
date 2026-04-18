"""
Operator Runtime Entrypoint Layer
- Accepts canonical operator-facing runtime requests
- Validates required inputs
- Invokes runtime_dispatch_adapter deterministically
- Returns canonical operator-facing result
- Does not mutate input or underlying semantics
"""

from copy import deepcopy
from workflows.runtime_dispatch_adapter import runtime_dispatch_adapter

# --- Operator Request Validation ---
def _validate_operator_request(request):
    if not isinstance(request, dict):
        return False, 'Operator request must be a dict.'
    required_fields = ['operator_id', 'operator_action', 'operator_payload']
    for field in required_fields:
        if field not in request:
            return False, f'Missing required field: {field}'
    # Optionally, validate payload structure
    if not isinstance(request['operator_payload'], dict):
        return False, 'operator_payload must be a dict.'
    return True, None

# --- Canonical Adapter Invocation ---
def _invoke_adapter(operator_request):
    # Compose canonical dispatch input from operator_payload
    payload = deepcopy(operator_request['operator_payload'])
    # Expect canonical keys in operator_payload
    dispatch_input = {
        'control_plane_summary_input': payload.get('control_plane_summary_input'),
        'portfolio_summary_input': payload.get('portfolio_summary_input'),
    }
    adapter_result = runtime_dispatch_adapter(dispatch_input)
    return adapter_result

# --- Entrypoint Precedence Resolution ---
def _resolve_entrypoint_precedence(valid, validation_error, adapter_result):
    if not valid:
        return 'failed_precondition', validation_error, True, False
    if adapter_result.get('runtime_state') == 'blocked' or adapter_result.get('runtime_blocker_indicator', False) or adapter_result.get('dispatch_state') == 'blocked':
        return 'blocked', adapter_result.get('runtime_result', 'Blocked'), False, True
    if adapter_result.get('runtime_state') == 'success' or adapter_result.get('dispatch_state') == 'dispatched':
        return 'accepted', adapter_result.get('runtime_result', 'Accepted'), False, False
    # Fallback: treat as failed_precondition
    return 'failed_precondition', adapter_result.get('runtime_result', 'Failed precondition'), True, False

# --- Final Stable Entrypoint Payload Assembly ---
def operator_runtime_entrypoint(operator_request):
    # Defensive copy to avoid mutation
    request_copy = deepcopy(operator_request)
    valid, validation_error = _validate_operator_request(request_copy)
    adapter_result = None
    if valid:
        adapter_result = _invoke_adapter(request_copy)
    else:
        adapter_result = {}
    (operator_request_state, operator_request_result, operator_precondition_indicator, operator_blocker_indicator) = _resolve_entrypoint_precedence(valid, validation_error, adapter_result)
    # Compose canonical result
    result = {
        'operator_request_state': operator_request_state,
        'operator_request_result': operator_request_result,
        'operator_precondition_indicator': operator_precondition_indicator,
        'operator_blocker_indicator': operator_blocker_indicator,
        'operator_basis': adapter_result.get('runtime_basis') if adapter_result else None,
        'dispatch_state': adapter_result.get('runtime_state') if adapter_result else None,
        'dispatch_result': adapter_result.get('runtime_result') if adapter_result else None,
        'runtime_state': adapter_result.get('runtime_state') if adapter_result else None,
        'runtime_result': adapter_result.get('runtime_result') if adapter_result else None,
        'cross_plane_summary_indicator': adapter_result.get('cross_plane_summary_indicator') if adapter_result else None,
    }
    # Optionally include more indicators as needed
    return result
