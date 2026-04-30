# official-source-approved-apply-operation-id-endpoint-binding-design-v1

Status: DRAFT (docs-only)
Owner: operator-dashboard
Date: 2026-04-30
Predecessor lock: official-source-approved-apply-operation-id-schema-v1 (fce25bf)

## 1) Objective
Define the endpoint-level request/response binding model for `operation_id` for future implementation slices, while preserving all currently locked behavior.

This design is intentionally scoped to endpoint contract definition only.

## 2) Scope
In scope (design only):
- Define where `operation_id` appears in endpoint request payload.
- Define where `operation_id` appears in endpoint response payload(s).
- Define normalization and pass-through expectations at endpoint boundary.
- Define retry/idempotency contract expectations that align with existing schema+guard support.

Out of scope:
- No code changes.
- No endpoint handler logic changes.
- No mutation-path wiring changes.
- No token digest changes.
- No token consume persistence changes.
- No UI changes.
- No batch changes.
- No scoring, prediction, or intake changes.
- No external lookup behavior changes.

## 3) Current Locked Baseline
The currently locked schema+guard slice established:
- Optional top-level `operation_id`.
- Schema normalization via trim.
- Schema format validation when present.
- Guard additive surfacing only.
- No allow/deny behavioral dependency on `operation_id` presence.

This document extends that baseline at endpoint contract level only.

## 4) Endpoint Request Contract (Design)
### 4.1 Field location
`operation_id` remains a top-level field in approved-apply endpoint requests.

### 4.2 Optionality
`operation_id` is optional for initial endpoint-binding implementation.
- Absent: endpoint behavior remains backward compatible.
- Present: endpoint must pass through schema+guard validated normalized value.

### 4.3 Validation source of truth
Schema remains the source of truth for format/type validation.
Endpoint should not introduce divergent format rules.

### 4.4 Binding boundary
`operation_id` is not added into `approval_binding` in this design phase.

## 5) Endpoint Response Contract (Design)
### 5.1 Additive response surfacing
All approved-apply endpoint responses should include top-level `operation_id` field:
- `null` when absent from request.
- normalized string when present and valid.

### 5.2 Error and deny responses
For schema/token/guard deny responses, include `operation_id` additively where available from schema/guard outputs.
No new deny code is introduced solely because `operation_id` is absent.

### 5.3 Success responses
For guard-allowed and endpoint-complete responses, include `operation_id` unchanged from normalized schema value.

## 6) Sequencing Model (Future Implementation Guidance)
Planned boundary order for endpoint slice implementation:
1. Parse request.
2. Run schema validation (normalizes `operation_id` when present).
3. Run token/guard evaluation.
4. Surface `operation_id` in endpoint response envelope from guard result.
5. Keep all existing mutation gating and consume sequencing unchanged unless explicitly authorized by a later slice.

## 7) Retry/Idempotency Alignment (Design-only)
`operation_id` is intended to support explicit operator retry identity in future slices.
For endpoint-binding slice only:
- Surface only; do not enforce persistence-backed deduplication yet.
- Do not alter token digest semantics.
- Do not alter token consume semantics.

Future slice (not this one) may define operation-store lookup/registration behavior.

## 8) Compatibility and Risk Controls
Compatibility expectations:
- Existing clients without `operation_id` continue to work unchanged.
- Existing reason codes and allow/deny behavior remain unchanged.

Risk controls:
- Additive-only contract update.
- No batch-path touch.
- No mutation side-effect expansion.
- No actual-results file mutation introduced by this design.

## 9) Test Design for Future Endpoint-Binding Implementation
When implementing endpoint-binding code (future slice), require tests proving:
1. Request without `operation_id` preserves legacy pass/deny outcomes.
2. Request with valid `operation_id` returns normalized `operation_id` in endpoint response.
3. Schema format-invalid `operation_id` is rejected with existing schema reasoning.
4. Guard deny responses still include non-mutation invariants unchanged.
5. Backend suite confirms no changes to mutation gating/consume ordering.

## 10) Acceptance Criteria for This Design Artifact
This docs-only slice is complete when:
- Request placement of `operation_id` is explicitly defined as top-level optional.
- Response surfacing rules are explicitly defined as additive.
- Non-goals clearly prohibit code, mutation, and token-digest changes.
- Future implementation test requirements are listed.

## 11) Follow-on Slice Recommendation
Recommended next implementation slice after design review:
- official-source-approved-apply-operation-id-endpoint-binding-implementation-v1

Guardrails for that future slice:
- Endpoint response plumbing only.
- No mutation-path behavior changes.
- No token digest or consume semantic changes.
- No UI/batch/scoring changes.
