# Button 1 Current Week Provider Enablement Readiness Checklist v1

Slice: button1-current-week-provider-enablement-readiness-checklist-v1
Date: 2026-06-18
Status: Docs-only checklist

## Purpose

Define the mandatory readiness checklist that must pass before any Button 1 provider is enabled for execution.

## Scope

This checklist governs only the transition from provider disabled state to provider enabled state for Button 1.

It does not authorize production execution by itself. It is a precondition checklist that must be fully passed and explicitly approved.

## Hard Boundary (Still Active)

Until this checklist is fully passed and signed off:
- Provider enabling remains blocked.
- Provider execution remains blocked.
- Source/network calls remain blocked.
- Scraping remains blocked.
- Queue/database writes remain blocked.
- Button 2 promotion remains blocked.

## Pass Rule

All sections below are mandatory and fail-closed.

If any single item is FAIL, MISSING, or UNVERIFIED, provider enablement decision is DENY.

## Readiness Checklist

### 1. Governance and Approval Controls

1. Operator approval gate is explicitly defined for provider enablement action.
2. Approval actor, timestamp, and rationale fields are required and non-optional.
3. Deny-by-default behavior is documented for missing or invalid approval payload.
4. Rollback authority and emergency disable procedure are documented.
5. Governance sign-off is recorded for this enablement decision.

Evidence required:
- Signed governance note for this slice.
- Approval payload contract doc with required fields.
- Rollback/disable runbook section.

### 2. Provider Registry Integrity

1. Registry schema validation passes for all configured providers.
2. Only approved provider IDs can be referenced (no ad hoc runtime IDs).
3. Provider metadata includes provenance owner and review date.
4. Registry parser/validator fail-closed behavior is covered by tests.
5. Default state remains enabled=false unless explicit approved flip.

Evidence required:
- Registry schema validation output.
- Parser/validator test report.
- Registry diff showing exact intended provider change only.

### 3. Execution Gate Contract Completeness

1. Execution gate decision model includes checked, allowed, decision, preview_only, and reason_codes.
2. Gate deny reasons include operator approval missing and provider not enabled.
3. Side-effect flags are explicit and independently asserted:
   - provider_execution_started
   - source_network_call_started
   - scraping_started
   - queue_write_started
   - button2_promotion_started
4. Gate remains fail-closed on malformed inputs and unknown sources.
5. Non-preview path behavior is explicitly specified and tested.

Evidence required:
- Gate contract/design reference.
- Unit test results for deny paths and malformed input.
- Runtime payload examples for preview and non-preview modes.

### 4. Safety and Side-Effect Guardrails

1. No side effects occur when gate decision is deny.
2. No source/network calls occur before gate allow decision.
3. No scraping activity can start before gate allow decision.
4. No queue/database writes can occur before gate allow decision.
5. No Button 2 promotion can occur from Button 1 gate path unless separately approved.

Evidence required:
- Negative-path integration test log.
- Telemetry/event trace proving zero side effects on deny.
- Explicit assertion report for all side-effect flags false on deny.

### 5. Runtime and API Verification

1. Workflow preview endpoint returns gate status payload consistently.
2. Payload contract includes expected decision and reason fields.
3. Preview mode clearly marked as preview_only=true.
4. Error handling paths return deterministic deny state, not partial success.
5. API smoke proofs are captured and archived.

Evidence required:
- API smoke proof summary artifact.
- Example request/response pair for deny and allow-shape preview.
- Contract assertion checklist output.

### 6. UI Visibility and Non-Interactive Safety

1. UI status panel accurately reflects gate decision fields.
2. UI panel remains read-only and non-interactive during blocked state.
3. No hidden actions/buttons/toggles can trigger provider enablement.
4. Reason codes are visible to operator for deny diagnostics.
5. Browser UI proof confirms blocked posture.

Evidence required:
- UI contract test report.
- Browser snapshot/proof summary.
- Static template check confirming no actionable controls in blocked panel.

### 7. Observability and Auditability

1. Enablement decision attempts are logged with decision outcome.
2. Deny reason codes are logged for all denied attempts.
3. Approval metadata is logged when present.
4. Telemetry includes correlation IDs for traceability.
5. Audit export path for review package is defined.

Evidence required:
- Logging schema reference.
- Sample audit log entries.
- Correlation ID trace example from request to gate decision.

### 8. Test and Proof Minimums

1. Unit tests: all gate deny-path and malformed-input tests pass.
2. Integration tests: preview/runtime contract tests pass.
3. UI tests: status panel contract and non-interactive checks pass.
4. Browser/API smokes: latest evidence captured with PASS verdict.
5. No unresolved critical severity defects related to enablement path.

Evidence required:
- Consolidated test summary.
- Browser/API smoke summaries.
- Open-defect report filtered to enablement scope.

### 9. Controlled Rollout and Reversibility

1. Enablement is scoped to a single named provider in first rollout.
2. Instant disable switch and documented rollback command are verified.
3. Post-enable observation window and owner are defined.
4. Success/failure thresholds for continuation are documented.
5. Re-disable criteria are explicit and tested.

Evidence required:
- Rollout plan note.
- Rollback rehearsal proof.
- Threshold table with owner sign-off.

## Enablement Decision Template

Final decision can only be one of:
- DENY: One or more checklist items failed, missing, or unverified.
- APPROVE_FOR_NEXT_SLICE_ONLY: All checklist items passed and governance sign-off complete.

Required decision record fields:
- decision
- provider_id
- approver
- approval_timestamp_utc
- checklist_version
- evidence_bundle_uri
- residual_risks
- rollback_owner

## Exit Criteria for This Checklist Slice

This docs-only slice is complete when:
1. Checklist content is locked in version control.
2. Checklist is referenced as mandatory precondition for provider enablement.
3. No runtime behavior changes are introduced by this slice.

## Conclusion

Provider enablement remains blocked until this entire checklist is passed with explicit governance approval and auditable evidence.
