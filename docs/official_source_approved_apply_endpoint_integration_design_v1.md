# official-source-approved-apply-endpoint-integration-design-v1

## 1. Purpose
Define a docs-only integration design for a future approved single-record official-source apply endpoint that wires existing helpers into a non-mutating guard decision flow.

This slice is integration design only. It introduces no endpoint runtime behavior and no file mutation.

## 2. Non-goals
- No endpoint code implementation.
- No backend behavior changes.
- No UI/runtime wiring.
- No write/apply implementation.
- No batch behavior.
- No page-load apply behavior.
- No automatic apply behavior.
- No mutation of actual-results files.
- No scoring formula or scoring semantics changes.
- No external lookup execution.

## 3. Proposed endpoint route
Proposed future route:
- POST /api/operator/actual-result-lookup/official-source-approved-apply

Boundary rules for first endpoint slice:
- One-record only.
- Explicit operator-triggered request only.
- Guard-decision response only.
- Non-mutating outcome for all states.

## 4. Request flow
1. Receive apply request payload.
2. Parse JSON body and keep payload immutable for helper calls.
3. Build authoritative preview context from trusted server-side source (future integration detail), not client-only data.
4. Pass request payload and authoritative preview context to guard orchestration helper.
5. Return helper output envelope directly (with endpoint-specific HTTP status mapping) while preserving non-mutation flags.

## 5. Response flow
1. Start from guard helper response envelope.
2. Preserve invariant non-mutation flags in all outcomes.
3. For deny/manual-review outcomes, return deterministic reason_code and helper errors.
4. For allow outcomes in first endpoint slice, still return non-mutating guard decision only.
5. Include acceptance gate object and binding digest fields returned by guard/token helpers.

## 6. How schema validation is called
Call:
- validate_official_source_approved_apply_request(request_payload)

Expected behavior:
- Hard-fail invalid mode/intent/shape.
- Reject forbidden batch and override fields.
- Produce deterministic schema reason_code and errors.
- Return request_valid=false on failure with mutation_performed=false and write_performed=false.

## 7. How token validation is called
Call:
- validate_official_source_approved_apply_token(
    token=request_payload.approval_token,
    binding=request_payload.approval_binding,
    now_epoch=server_now_epoch,
    consumed_token_ids=simulated_or_runtime_state,
    replayed_token_ids=simulated_or_runtime_state,
    allowed_clock_skew_seconds=5,
    approval_granted=request_payload.approval_granted
  )

Expected behavior:
- Validate token format, expiry, future-issued, replayed, consumed, and binding digest.
- Return deterministic token_status and reason_code.
- Never mutate persistent token state in this endpoint-integration design slice.

## 8. How acceptance_gate is revalidated
Call:
- evaluate_official_source_acceptance_gate(authoritative_preview_result)

Revalidation policy:
- Use authoritative preview context only.
- Require state=write_eligible and write_eligible=true for allow path.
- Treat manual_review and rejected as non-mutating deny outcomes.
- Preserve identity_conflict as deny classification.

## 9. How the apply guard is called
Call:
- evaluate_official_source_approved_apply_guard(
    request_payload,
    authoritative_preview_result=authoritative_preview_result,
    now_epoch=server_now_epoch,
    consumed_token_ids=simulated_or_runtime_state,
    replayed_token_ids=simulated_or_runtime_state,
    allowed_clock_skew_seconds=5
  )

Guard orchestration order:
1. schema validation
2. token validation
3. request-vs-preview binding checks
4. preview snapshot match against authoritative preview
5. acceptance gate write_eligible check
6. manual_review/rejected handling
7. guard pass

## 10. How guard_allowed=false responses are returned
When guard_allowed=false:
- Return guard reason_code and errors.
- Return request_valid/token_valid/token_status/approval_binding_valid fields from guard envelope.
- Return acceptance_gate object when available.
- Keep mutation_performed=false.
- Keep write_performed=false.
- Keep bulk_lookup_performed=false.
- Keep scoring_semantics_changed=false.

Suggested status mapping (future implementation detail):
- 400 for malformed schema/token format errors.
- 403 for approval/binding denials.
- 409 for authoritative preview mismatch conflicts.
- 422 for gate/manual-review non-writeable states.

## 11. How guard_allowed=true remains non-mutating in first endpoint slice
For the first endpoint implementation slice:
- guard_allowed=true returns decision-only payload.
- No write planner invocation.
- No file writes.
- No token consume persistence.
- No actual_results_manual.json mutation.
- write_performed remains false.
- mutation_performed remains false.

## 12. Future mutation boundary
Mutation is explicitly deferred to a separate approved slice.

Future mutation slice prerequisites:
- Separate design approval for mutation path.
- Explicit write target constraints reaffirmed.
- Atomic write and rollback strategy finalized.
- Token consume semantics and persistence approved.
- Additional audit fields for mutation path approved.

No mutation behavior is authorized by this design note.

## 13. Required response invariants
All endpoint outcomes must include:
- mode=official_source_approved_apply
- phase=approved_apply
- approval_required=true
- mutation_performed=false (first endpoint slice)
- write_performed=false (first endpoint slice)
- bulk_lookup_performed=false
- scoring_semantics_changed=false
- reason_code present
- errors list present

If any schema/token/gate/guard check fails:
- guard_allowed=false
- mutation_performed=false
- write_performed=false

## 14. No-batch / no-page-load / no-auto-apply rules
Mandatory endpoint integration boundaries:
- No batch apply payload support.
- No selected_keys/targets/batch_size/execution_token apply path.
- No page-load invocation.
- No auto-apply on preview success.
- No implicit retries that alter state.
- No background job apply path.

## 15. Audit fields returned by the endpoint
For first endpoint slice (decision-only), return audit-compatible fields without mutation side effects:
- correlation_id (if generated by endpoint layer)
- phase
- selected_key
- approval_required
- approval_granted
- token_status
- approval_binding_valid
- reason_code
- acceptance_gate.state
- acceptance_gate.write_eligible
- acceptance_gate.reason_code
- binding_digest_expected
- binding_digest_actual
- write_performed=false
- mutation_performed=false
- scoring_semantics_changed=false

Carry-forward expectation from authoritative preview context:
- record_fight_id
- provider_attempted
- attempted_sources

## 16. Test plan before implementation
Before implementing endpoint code, tests must prove:
- Endpoint rejects invalid schema payloads deterministically.
- Endpoint rejects invalid token states deterministically.
- Endpoint rejects binding mismatches deterministically.
- Endpoint rejects preview snapshot mismatches vs authoritative preview.
- Endpoint rejects manual_review/rejected gate states.
- Endpoint returns guard_allowed=true only for fully valid guard pass inputs.
- All outcomes keep mutation_performed=false and write_performed=false.
- All outcomes keep bulk_lookup_performed=false and scoring_semantics_changed=false.
- No endpoint code path writes actual-results artifacts in first endpoint slice.
- No batch/page-load/auto-apply behavior exists.

## 17. Future implementation micro-slices
1. Slice A: endpoint skeleton integration (decision-only)
- Wire route to schema + token + guard + acceptance gate revalidation path.
- Keep all mutation flags false.

2. Slice B: endpoint contract hardening
- Lock HTTP status mapping and error-shape consistency.
- Expand audit carry-forward fields.

3. Slice C: observability and denial telemetry
- Add structured logs/metrics for deny categories and pass counts.
- No mutation behavior.

4. Slice D: mutation-boundary design review
- Separate docs-only review for write path enablement and rollback proof.

5. Slice E: mutation implementation (separate approved slice)
- Atomic write + rollback + token consume behavior.
- Guard and gate remain pre-write requirements.

6. Slice F: optional UI wiring (separate approved slice)
- Explicit operator action only.
- No auto-apply.

---

Design status: ready for review.
Implementation status: intentionally not started.
