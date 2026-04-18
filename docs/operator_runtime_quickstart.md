# Operator Runtime Quickstart

## Overview
This quickstart guides operators through invoking the frozen runtime execution surface and interpreting results using the canonical contract.

## Minimal Happy-Path Example
### Operator Request
```
{
  "operator_id": "op123",
  "operator_action": "run",
  "operator_payload": {
    "control_plane_summary_input": {
      "event_control_summary_pack": {"ready_events": ["event1"], "partial_events": [], "blocked_events": [], "event_count": 1},
      "event_dashboard_pack": {"priority_queue": ["event1"], "control_plane_dashboard": "nominal"},
      "portfolio_dashboard_pack": {"dashboard_cards": ["card1"], "portfolio_dashboard": "nominal"},
      "portfolio_control_summary_pack": {"escalation_queue": []},
      "portfolio_governance_pack": {"portfolio_governance_status": "nominal"},
      "portfolio_resolution_decision_pack": {"portfolio_resolution_decision_status": "nominal"},
      "control_plane_policy_status": "ready",
      "portfolio_policy_decision": "proceed_policy",
      "control_plane_status": "nominal",
      "portfolio_status": "nominal",
      "control_plane_closure": "closure_ready",
      "portfolio_closure": "closure_ready",
      "control_plane_dashboard": "nominal",
      "portfolio_dashboard": "nominal"
    },
    "portfolio_summary_input": [
      {
        "event_name": "event1",
        "event_status": "ready",
        "total_bouts": 1,
        "publish_ready_count": 1,
        "review_required_count": 0,
        "manual_intervention_count": 0,
        "blocked_count": 0,
        "priority": 1,
        "notes": "",
        "portfolio_policy_decision": "proceed_policy",
        "portfolio_status": "nominal",
        "portfolio_closure": "closure_ready",
        "portfolio_dashboard": "nominal",
        "control_plane_dashboard": "nominal",
        "control_plane_closure": "closure_ready"
      }
    ]
  }
}
```
### Expected Result
```
{
  "operator_request_state": "accepted",
  "operator_request_result": "All packs nominal",
  "operator_precondition_indicator": false,
  "operator_blocker_indicator": false,
  "operator_basis": "nominal",
  "dispatch_state": "dispatched",
  "dispatch_result": "All packs nominal",
  "runtime_state": "success",
  "runtime_result": "All packs nominal",
  "cross_plane_summary_indicator": "cross_nominal"
}
```

## Minimal Blocked Example
### Operator Request
```
{
  "operator_id": "op123",
  "operator_action": "run",
  "operator_payload": {
    "control_plane_summary_input": {
      ...
      "control_plane_policy_status": "blocked"
    },
    "portfolio_summary_input": [ ... ]
  }
}
```
### Expected Result
```
{
  "operator_request_state": "blocked",
  "operator_request_result": "Blocked by cross-plane pack",
  "operator_precondition_indicator": false,
  "operator_blocker_indicator": true,
  ...
}
```

## Minimal Failed Precondition Example
### Operator Request
```
{
  "operator_id": "op123",
  "operator_action": "run",
  "operator_payload": {
    "portfolio_summary_input": [ ... ]
    // missing control_plane_summary_input
  }
}
```
### Expected Result
```
{
  "operator_request_state": "failed_precondition",
  "operator_request_result": "Missing required dispatch input(s)",
  "operator_precondition_indicator": true,
  "operator_blocker_indicator": false,
  ...
}
```

## Step-by-Step Operator Checklist
1. Assemble a canonical operator request as shown above.
2. Ensure all required fields and upstreams are present and well-formed.
3. Submit the request to the operator runtime entrypoint.
4. Inspect the returned result for `operator_request_state` and indicators.
5. If `accepted`, proceed as normal.
6. If `blocked`, review blockers and resolve before retrying.
7. If `failed_precondition`, correct input structure and retry.

## Troubleshooting
- **If you receive `failed_precondition`**: Check for missing or malformed required fields in your request or upstreams.
- **If you receive `blocked`**: Review all cross-plane and upstream pack states for blockers.
- **If you receive unexpected results**: Ensure you are using the exact canonical field names and payload structure as documented.
- **Never mutate input payloads in place.** Always use fresh copies for each invocation.
- **Do not add speculative or undocumented fields.**
