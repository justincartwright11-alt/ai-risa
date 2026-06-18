# Button 1 Provider Adapter Execution Gate Runtime Preview Status Design v1

Slice: button1-current-week-provider-adapter-execution-gate-runtime-preview-status-design-v1
Date: 2026-06-18
Status: Design-only

## Purpose

Define how execution-gate decisions should appear in runtime preview status before any gate wiring is added to preview/runtime flows.

This slice is specification-only and must not change runtime behavior.

## Scope

In scope:
- Runtime preview status contract for gate decisions
- Display semantics for allow/deny and reason codes
- Fail-closed status behavior
- Governance telemetry requirements in preview output

Out of scope:
- Wiring gate evaluator into runtime loader
- Wiring gate status into UI rendering logic
- Enabling provider execution
- Source calls or scraping
- Queue/database writes
- Button 2 promotion paths

## Baseline (Current)

Current runtime preview includes registry adapter status and remains non-executing.
Execution gate scaffold exists as standalone module only.
No runtime integration currently exists for gate decisions.

## Design Goals

1. Keep preview deterministic and fail-closed.
2. Make gate status explicit and operator-readable.
3. Preserve zero side effects in all preview states.
4. Allow future wiring with minimal contract churn.

## Proposed Runtime Preview Payload Section

Add a nested preview-only section in Button 1 payload:

- execution_gate_status
  - gate_checked: bool
  - gate_allowed: bool
  - gate_decision: allow | deny
  - gate_reason_codes: list[str]
  - source_button: string
  - provider_id: string
  - provider_enabled: bool
  - operator_approval_required: bool
  - preview_only: bool
  - decision_timestamp_utc: string
  - provider_execution_performed: bool
  - network_calls_performed: bool
  - source_calls_performed: bool
  - scraping_performed: bool
  - queue_write_performed: bool
  - database_write_performed: bool
  - button2_promotion_performed: bool

## Default Preview State (Before Wiring)

Until runtime wiring is implemented, the design baseline for status semantics is:
- gate_checked=false
- gate_allowed=false
- gate_decision=deny
- gate_reason_codes includes execution_gate_not_wired_runtime_preview
- operator_approval_required=true
- preview_only=true
- all side-effect flags=false

This prevents ambiguity and keeps the preview explicitly fail-closed.

## Wired Preview State (Future, Still Non-Executing)

After future runtime wiring (separate slice), expected semantics:
- gate_checked=true
- gate_allowed derived from scaffold evaluator output
- gate_decision reflect allow/deny evaluator decision
- gate_reason_codes include deterministic deny/allow reasons
- all side-effect flags remain false in preview

Important: even if gate_allowed=true in preview status, preview must not execute providers.

## UI Display Design (Preview Panel Contract)

When eventually surfaced in Button 1 runtime status panel, show:
- Execution Gate: Checked / Not Checked
- Decision: Allow / Deny
- Provider: provider_id (or Unknown)
- Source Button: button1_find_fights
- Reason Codes: comma-separated compact list
- Operator Approval Required: Yes
- Preview-Only Badge: visible
- Side-Effect Flags:
  - Provider Execution: NO
  - Network/Source Calls: NO
  - Scraping: NO
  - Queue/DB Writes: NO
  - Button 2 Promotion: NO

Display color semantics:
- Deny: amber/red informational state
- Allow (preview only): neutral/green with explicit non-executing notice
- Not checked: muted/gray

## Fail-Closed Rules

Runtime preview must emit deny state when:
- Gate status absent
- Gate payload malformed
- Any required gate field missing
- Unknown decision enum

Required fallback reason code:
- execution_gate_status_unavailable_fail_closed

Fallback side-effect flags in all fail-closed paths:
- provider_execution_performed=false
- network_calls_performed=false
- source_calls_performed=false
- scraping_performed=false
- queue_write_performed=false
- database_write_performed=false
- button2_promotion_performed=false

## Backward Compatibility Requirements

- Existing registry_adapter_status payload remains unchanged.
- Existing Button 1 UI behavior remains unchanged until separate wiring slice.
- Existing tests for non-executing preview behavior must continue to pass.

## Future Wiring Acceptance Criteria (Separate Slice)

When runtime preview wiring is implemented later, that slice must prove:
1. execution_gate_status appears in runtime payload with stable keys.
2. Missing/malformed gate status fails closed with required reason code.
3. Preview deny-by-default still holds when gate not explicitly checked.
4. All side-effect flags remain false in preview deny and preview allow states.
5. Button 2 unaffected.
6. Button 3 unaffected.

## Governance Commitments

This design-only slice preserves:
- Runtime behavior changed: false
- UI behavior changed: false
- Provider execution: false
- Network/source calls: false
- Scraping: false
- Queue/database writes: false
- Button 2 unaffected
- Button 3 unaffected

## Conclusion

The runtime-preview status contract for execution gate decisions is now defined.
Integration remains intentionally deferred to a future isolated wiring slice, with fail-closed semantics and non-executing preview guarantees as mandatory constraints.
