# Operator Runtime Usage Contract

## 1. Scope of the Frozen Runtime Surface
- **Three-lane governed pack stack**: All core event, portfolio, and cross-plane packs are frozen and validated.
- **Runtime orchestrator**: Deterministic, audit-ready orchestrator for all packs.
- **Runtime dispatch adapter**: Thin, deterministic adapter for orchestrator dispatch.
- **Operator runtime entrypoint**: Canonical, operator-facing interface for runtime execution.

## 2. Canonical Execution Flow
1. **Operator request**: Operator submits a canonical request payload to the entrypoint.
2. **Entrypoint validation**: Checks for required fields and payload structure.
3. **Dispatch adapter validation**: Validates dispatch input structure and types.
4. **Runtime orchestrator execution**: Executes the full pack stack deterministically.
5. **Cross-plane evaluation**: All cross-plane packs are evaluated in deterministic order.
6. **Returned operator-facing result**: Entrypoint returns a stable, canonical result payload.

## 3. Canonical Payload Contracts
### Operator Request Structure
```
{
  "operator_id": "...",                # required
  "operator_action": "...",            # required
  "operator_payload": {
    "control_plane_summary_input": {...}, # required, see below
    "portfolio_summary_input": [...]      # required, see below
  }
}
```

### Dispatch Input Structure
```
{
  "control_plane_summary_input": {...},  # required dict
  "portfolio_summary_input": [...]       # required list
}
```

### Runtime Upstream Structure
- `control_plane_summary_input`: Dict with all required upstreams for control_plane_summary_pack and cross-plane packs.
- `portfolio_summary_input`: List of event_dashboard_pack dicts for portfolio_summary_pack and cross-plane packs.

### Canonical Output/Result Fields (by layer)
- **Operator Entrypoint**:
  - `operator_request_state`: accepted / blocked / failed_precondition
  - `operator_request_result`: canonical result string
  - `operator_precondition_indicator`: bool
  - `operator_blocker_indicator`: bool
  - `operator_basis`: string or None
  - `dispatch_state`: dispatched / blocked / failed_precondition
  - `dispatch_result`: string
  - `runtime_state`: success / blocked / failed_precondition
  - `runtime_result`: string
  - `cross_plane_summary_indicator`: string or None
- **Dispatch Adapter**:
  - `dispatch_state`, `dispatch_result`, `dispatch_precondition_indicator`, `dispatch_blocker_indicator`, `dispatch_basis`, plus all orchestrator fields
- **Runtime Orchestrator**:
  - `runtime_state`, `runtime_result`, `runtime_blocker_indicator`, `runtime_precondition_indicator`, `runtime_basis`, `cross_plane_summary_indicator`, etc.

## 4. Allowed Top-Level Outcomes by Layer
| Layer                | Success         | Blocked | Failed Precondition |
|----------------------|----------------|---------|---------------------|
| Operator Entrypoint  | accepted       | blocked | failed_precondition |
| Dispatch Adapter     | dispatched     | blocked | failed_precondition |
| Runtime Orchestrator | success        | blocked | failed_precondition |

## 5. Precedence Rules
- `failed_precondition` outranks `blocked` and `success`/`dispatched`/`accepted`.
- `blocked` outranks `success`/`dispatched`/`accepted`.
- Nominal/ready inputs cannot erase a higher-precedence blocker or failed precondition.

## 6. Field Glossary
- `operator_request_state`: Top-level entrypoint outcome (accepted/blocked/failed_precondition)
- `dispatch_state`: Adapter outcome (dispatched/blocked/failed_precondition)
- `runtime_state`: Orchestrator outcome (success/blocked/failed_precondition)
- `runtime_result`: Canonical result string from orchestrator
- `cross_plane_summary_indicator`: Cross-plane summary state (e.g., cross_nominal)
- `operator_precondition_indicator`, `dispatch_precondition_indicator`, `runtime_precondition_indicator`: True if failed precondition
- `operator_blocker_indicator`, `dispatch_blocker_indicator`, `runtime_blocker_indicator`: True if blocked
- `operator_basis`, `dispatch_basis`, `runtime_basis`: Canonical basis string (e.g., nominal, unresolved)

## 7. Operator Interpretation Rules
- **accepted**: All required structure and upstreams present, no blockers, execution succeeded.
- **blocked**: Upstream or cross-plane pack blocked; operator action not completed.
- **failed_precondition**: Required structure or upstream missing/malformed; must correct input before retry.
- **When to retry**: Only after correcting failed_precondition or resolving a blocker.
- **When to correct inputs**: On any failed_precondition result.

## 8. Non-Goals
- No new orchestration logic.
- No hidden mutation of inputs or outputs.
- No out-of-band overrides or speculative features.
