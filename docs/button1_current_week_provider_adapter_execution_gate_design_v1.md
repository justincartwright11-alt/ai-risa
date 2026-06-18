# Button 1 Provider Adapter Execution Gate Design v1

Slice: button1-current-week-provider-adapter-execution-gate-design-v1
Date: 2026-06-18
Status: Design-only (no runtime/UI behavior changes)

## Purpose

Define the provider adapter execution gate that must exist and be approved before any provider is enabled in the real runtime registry.

This document is contract/design only. It does not enable provider execution.

## Current Baseline

Current runtime registry state:
- Runtime file exists: ops/approved_sources/button1_live_provider_registry.json
- Providers configured: 2
- Providers enabled: 0

Current runtime preview status:
- registration_valid=True
- validation_valid=True
- registry_candidate_valid=True
- diagnostics=no_enabled_provider

Current governance status:
- provider_execution_performed=False
- network_calls_performed=False
- queue_write_performed=False
- database_write_performed=False

## Hard Boundary

Do not set any provider enabled=true until execution gate design is implemented and explicitly approved.

No execution path is permitted until all gate controls in this design are present and verified.

## Execution Gate Objectives

1. Block all provider execution by default.
2. Require explicit operator approval for any execution attempt.
3. Fail closed for missing/invalid gate inputs.
4. Emit deterministic telemetry for allow/deny reasons.
5. Prevent queue/database writes from execution-gate evaluation.
6. Preserve Button 2 and Button 3 isolation.

## Gate Inputs (Design Contract)

Required gate request inputs:
- source_button: must be button1_find_fights
- provider_id: requested provider candidate id
- execution_mode: must be execute_preview_only in first implementation stage
- operator_approval_token: required, non-empty, short-lived
- approval_reason: required, non-empty
- requested_at_utc: required ISO UTC timestamp

Required gate context inputs:
- registry_snapshot_hash: hash of runtime registry used for decision
- provider_registry_path: must match ops/approved_sources/button1_live_provider_registry.json
- candidate_metadata: provider tier/domain/scope details

## Gate Checks (Ordered)

Check 1: Runtime mode and feature gate
- If execution gate feature disabled, deny.
- Diagnostic: execution_gate_disabled

Check 2: Registry presence and validity
- Require valid parsed registry and provider candidate.
- If missing/invalid, deny.
- Diagnostic: execution_gate_registry_invalid

Check 3: Provider eligibility
- Provider must exist and be marked enabled=true in registry.
- If provider disabled/missing, deny.
- Diagnostic: execution_gate_provider_not_enabled

Check 4: Source tier policy
- Provider source_tier must be in approved tiers.
- If not approved, deny.
- Diagnostic: execution_gate_source_tier_denied

Check 5: Domain allowlist policy
- endpoint host must be within allowed_domains.
- If mismatch, deny.
- Diagnostic: execution_gate_domain_not_allowed

Check 6: Operator approval token policy
- Token required, unexpired, and bound to provider_id + source_button.
- If invalid, deny.
- Diagnostic: execution_gate_operator_approval_invalid

Check 7: Budget and cooldown policy
- Enforce per-provider rate/budget/cooldown controls.
- If exceeded, deny.
- Diagnostic: execution_gate_budget_or_cooldown_blocked

Check 8: Final allow decision
- Only allow when all prior checks pass.
- Emit execution_gate_allowed=true and decision metadata.

## Gate Outputs (Design Contract)

Decision payload fields:
- execution_gate_checked: bool
- execution_gate_allowed: bool
- execution_gate_decision: allow|deny
- execution_gate_reason_codes: list[str]
- provider_id: string
- source_button: string
- operator_approval_required: true
- provider_execution_performed: false during design stage
- network_calls_performed: false during design stage
- queue_write_performed: false
- database_write_performed: false

Audit payload fields (read-only preview surface):
- decision_id
- decision_timestamp_utc
- registry_snapshot_hash
- approval_token_hash_prefix
- deny_or_allow_reason_summary

## Fail-Closed Behavior

Deny execution when any required input is missing or malformed.

Mandatory fail-closed diagnostics:
- execution_gate_missing_input
- execution_gate_invalid_timestamp
- execution_gate_registry_invalid
- execution_gate_provider_not_enabled
- execution_gate_operator_approval_invalid
- execution_gate_domain_not_allowed

In all deny paths:
- execution_gate_allowed=false
- provider_execution_performed=false
- network_calls_performed=false
- queue_write_performed=false
- database_write_performed=false

## Stage Plan (Before Real Enablement)

Stage A: Design lock (this slice)
- Document gate contract and checks.

Stage B: Gate preview wiring (no execution)
- Compute allow/deny decisions in preview only.
- Keep provider/network/write flags false.

Stage C: Gate proof and policy hardening
- Add tests for all deny/allow branches.
- Validate telemetry and isolation.

Stage D: Controlled provider enablement proposal
- Separate approval slice required.
- Enable at most one provider with rollback plan.

## Required Test Coverage (Future Implementation)

1. Missing token -> deny (no execution)
2. Expired token -> deny (no execution)
3. Provider disabled -> deny (no execution)
4. Domain mismatch -> deny (no execution)
5. Source tier denied -> deny (no execution)
6. Budget exceeded -> deny (no execution)
7. All checks pass in preview mode -> allowed decision, still no execution in preview stage
8. Button 2 unaffected
9. Button 3 unaffected

## Non-Regression Requirements

Must remain true through gate design and preview stages:
- Runtime code changed for execution: not yet
- UI execution controls added: not yet
- Provider execution: false
- Network calls: false
- Queue writes: false
- Database writes: false
- Button 2 unaffected
- Button 3 unaffected

## Acceptance Criteria (Design Slice)

This slice is complete when:
- Execution gate contract is fully defined.
- Ordered checks and fail-closed diagnostics are specified.
- Required inputs/outputs are explicit.
- Stage plan clearly blocks provider enablement prior to gate approval.
- No runtime/UI behavior changes are introduced.

## Conclusion

Execution gate design is defined and must be approved before any provider is enabled.
Until that approval and implementation are complete, providers remain disabled and the system remains non-executing by governance policy.
