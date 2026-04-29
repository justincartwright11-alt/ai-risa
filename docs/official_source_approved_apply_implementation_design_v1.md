# official-source-approved-apply-implementation-design-v1

## 1. Purpose
Define a docs-only implementation plan for a future approved single-record official-source apply flow that executes only after explicit operator approval and authoritative server-side revalidation.

This slice is design-only and does not implement runtime behavior.

## 2. Non-goals
- No runtime code changes.
- No endpoint implementation or endpoint behavior changes.
- No backend behavior changes.
- No UI/runtime wiring.
- No write/apply implementation.
- No batch behavior.
- No page-load lookup or page-load apply behavior.
- No actual-results file mutation.
- No scoring formula or scoring semantics change.
- No external lookup execution in this slice.

## 3. Proposed implementation sequence
1. Contract lock and schema fixtures
- Lock request/response JSON fixtures for apply, deny, and manual-review outcomes.
- Lock deterministic reason-code map and state classification table.

2. Approval-token helper implementation (no file mutation)
- Implement token issue/validate/consume helpers.
- Implement token TTL, consumed-state, anti-replay, and binding digest verification.
- Keep helper integration non-mutating until guard stage is complete.

3. Non-mutating apply guard endpoint integration
- Add apply route with strict request validation and one-record enforcement.
- Perform server-side authoritative revalidation using current selected row and gate evaluator.
- Return deterministic deny/manual-review responses with write_performed=false.

4. Atomic single-record write layer
- Implement write planner and persistence wrapper for ops/accuracy/actual_results_manual.json only.
- Add pre-write hash capture, temporary write strategy, atomic replace, and rollback restore path.

5. Audit and observability hardening
- Persist and emit required audit envelope fields for success, deny, and rollback outcomes.
- Include pre_write_file_sha256 and rollback proof metadata.

6. Final integration and safety verification
- Confirm no batch mode, no page-load apply, no automatic apply, and no scoring changes.
- Execute full contract and rollback test plan before any UI wiring consideration.

## 4. Files likely to change later
These are future implementation targets only, not modified in this slice:
- operator_dashboard/app.py
- operator_dashboard/official_source_acceptance_gate.py
- operator_dashboard/official_source_lookup_provider.py (only if needed for shared citation normalization helpers)
- operator_dashboard/templates/advanced_dashboard.html (only after backend guardrails are locked)
- tests targeting apply endpoint contract and rollback safety (new or existing test modules)
- ops/accuracy/actual_results_manual.json (runtime write target only after implementation, never in this slice)

## 5. Apply endpoint name and route
Proposed route:
- POST /api/operator/actual-result-lookup/official-source-approved-apply

Boundary invariants:
- One-record only.
- Explicit apply intent only.
- Never callable from page load.
- Never callable as batch.
- Never implied by preview success alone.

## 6. Request schema
Proposed request body:

```json
{
  "mode": "official_source_approved_apply",
  "lookup_intent": "apply_write",
  "selected_key": "string",
  "approval_granted": true,
  "approval_token": "string",
  "approval_binding": {
    "selected_key": "string",
    "citation_fingerprint": "string",
    "source_url": "string",
    "source_date": "string",
    "extracted_winner": "string",
    "record_fight_id": "string|null",
    "selected_row_identity": {
      "fight_name": "string",
      "fight_id": "string|null"
    }
  },
  "preview_snapshot": {
    "selected_key": "string",
    "reason_code": "string",
    "manual_review_required": false,
    "source_citation": {
      "source_url": "string",
      "source_title": "string",
      "source_date": "string",
      "publisher_host": "string",
      "source_confidence": "string",
      "confidence_score": 0.0,
      "citation_fingerprint": "string",
      "extracted_winner": "string",
      "method": "string|null",
      "round_time": "string|null"
    },
    "acceptance_gate": {
      "state": "write_eligible",
      "write_eligible": true,
      "reason_code": "accepted_preview_write_eligible",
      "selected_key": "string",
      "citation_fingerprint": "string"
    },
    "audit": {
      "record_fight_id": "string|null",
      "provider_attempted": true,
      "attempted_sources": []
    }
  },
  "operator_note": "string"
}
```

Request validation rules:
- mode must equal official_source_approved_apply.
- lookup_intent must equal apply_write.
- selected_key must be present and represent exactly one record.
- approval_granted must be true.
- approval_token, approval_binding, and preview_snapshot are required.
- Any schema failure returns deterministic deny with no mutation.

## 7. Response schema
Proposed response body:

```json
{
  "ok": true,
  "mode": "official_source_approved_apply",
  "phase": "approved_apply",
  "selected_key": "string",
  "approval_required": true,
  "approval_granted": true,
  "approval_binding_valid": true,
  "approval_token_status": "valid | missing | expired | replayed | consumed | binding_mismatch",
  "manual_review_required": false,
  "write_performed": false,
  "mutation_performed": false,
  "bulk_lookup_performed": false,
  "external_lookup_performed": false,
  "scoring_semantics_changed": false,
  "write_target": "ops/accuracy/actual_results_manual.json",
  "acceptance_gate": {
    "state": "write_eligible | manual_review | rejected",
    "write_eligible": true,
    "reason_code": "string",
    "reasons": [],
    "checks": {},
    "selected_key": "string",
    "citation_fingerprint": "string"
  },
  "proposed_write": {
    "fight_id": "string",
    "fight_name": "string",
    "actual_winner": "string",
    "source": "official_source_manual_approved",
    "source_url": "string",
    "source_title": "string",
    "source_date": "string",
    "publisher_host": "string",
    "source_confidence": "string",
    "confidence_score": 0.0,
    "citation_fingerprint": "string",
    "selected_key": "string",
    "write_mode": "official_source_approved_apply",
    "approval_type": "explicit_operator_approval",
    "operator_id": "string",
    "approved_at_utc": "string",
    "method": "string|null",
    "round_time": "string|null"
  },
  "audit": {
    "correlation_id": "string",
    "phase": "approved_apply",
    "selected_key": "string",
    "record_fight_id": "string|null",
    "approval_required": true,
    "approval_granted": true,
    "approval_binding_valid": true,
    "approval_token_id": "string",
    "approval_token_issued_at_utc": "string",
    "approval_token_expires_at_utc": "string",
    "approval_token_consumed": false,
    "operator_id": "string",
    "approved_at_utc": "string",
    "provider_attempted": true,
    "attempted_sources": [],
    "source_url": "string",
    "source_title": "string",
    "source_date": "string",
    "publisher_host": "string",
    "source_confidence": "string",
    "confidence_score": 0.0,
    "citation_fingerprint": "string",
    "actual_winner": "string",
    "write_target": "ops/accuracy/actual_results_manual.json",
    "write_performed": false,
    "mutation_performed": false,
    "scoring_semantics_changed": false,
    "pre_write_file_sha256": "string|null",
    "rollback_attempted": false,
    "rollback_succeeded": false,
    "post_rollback_file_sha256": "string|null",
    "reason_code": "string"
  },
  "message": "string"
}
```

Response invariants:
- write_target fixed to ops/accuracy/actual_results_manual.json.
- write_performed=false and mutation_performed=false for deny/manual-review outcomes.
- bulk_lookup_performed=false in all outcomes.
- scoring_semantics_changed=false in all outcomes.

## 8. Approval-token helper design
Helper responsibilities:
- issue_approval_token(preview_context, operator_id) -> token envelope
- validate_approval_token(token, request_binding, now_utc) -> status and normalized binding
- consume_approval_token(token_id) -> consumed marker for one-time-use

Token payload model:
- token_id
- issued_at_utc
- expires_at_utc
- consumed
- selected_key
- citation_fingerprint
- source_url
- source_date
- extracted_winner
- record_fight_id (nullable)
- selected_row_identity.fight_name
- selected_row_identity.fight_id (nullable)

Validation outcomes:
- valid
- missing
- expired
- replayed
- consumed
- binding_mismatch

## 9. Token one-time-use model
One-time-use requirements:
- Token starts unconsumed when issued.
- Successful apply path consumes token exactly once.
- Any reused token id returns approval_replayed or approval_token_consumed.
- Consumed tokens never authorize another apply.

Design notes:
- Consumption must be committed atomically with successful write completion semantics.
- Failed applies before write commit must not produce ambiguous token state.

## 10. Token expiry model
Expiry requirements:
- Token TTL maximum 300 seconds.
- Validation compares current UTC against expires_at_utc.
- Expired tokens deny with approval_expired.

Design notes:
- Expiry check runs before write planning.
- Expiry outcome must be surfaced in approval_token_status and reason_code.

## 11. Binding digest model
Digest purpose:
- Ensure apply request remains bound to the exact approved preview payload.

Canonical bound fields:
- selected_key
- citation_fingerprint
- source_url (canonical post-normalization)
- source_date
- extracted_winner (normalized exactly as preview)
- stable identity fields:
  - record_fight_id
  - selected_row_identity.fight_name
  - selected_row_identity.fight_id

Design requirements:
- Build deterministic digest over canonical normalized field tuple.
- Compare request binding, token binding, preview snapshot, and authoritative server-side recomputation.
- Any mismatch denies with specific reason:
  - selected_key_binding_mismatch
  - citation_binding_mismatch
  - source_url_binding_mismatch
  - source_date_binding_mismatch
  - extracted_winner_binding_mismatch
  - record_identity_binding_mismatch

## 12. Server-side acceptance_gate revalidation flow
Revalidation flow:
1. Resolve selected_key from authoritative waiting-row context.
2. Recompute or reevaluate citation completeness and gate state using server logic.
3. Require acceptance_gate.state == write_eligible.
4. Require acceptance_gate.write_eligible == true.
5. Require acceptance_gate.reason_code == accepted_preview_write_eligible.
6. Compare authoritative result against preview_snapshot and approval binding.
7. Deny on any mismatch or degraded state.

State handling:
- manual_review state blocks write and returns manual_review_required=true.
- rejected state blocks write and returns deterministic deny reason.
- identity_conflict is deny in apply, not manual-review.

## 13. Write target flow
Allowed target only:
- ops/accuracy/actual_results_manual.json

Flow:
1. Validate request and token.
2. Revalidate acceptance gate and binding digest.
3. Build proposed_write record.
4. Read current manual actual-results file.
5. Apply deterministic one-record append/upsert policy.
6. Perform atomic file replace with rollback guard.

Disallowed:
- Any write to ops/accuracy/actual_results.json.
- Any write to ops/accuracy/actual_results_unresolved.json.
- Any queue mutation.
- Any batch write.

## 14. Exact write schema
Required fields:
- fight_id
- fight_name
- actual_winner
- source
- source_url
- source_title
- source_date
- publisher_host
- source_confidence
- confidence_score
- citation_fingerprint
- selected_key
- write_mode
- approval_type
- operator_id
- approved_at_utc

Optional fields:
- method
- round_time
- event_name
- event_date
- notes

Field invariants:
- source == official_source_manual_approved.
- write_mode == official_source_approved_apply.
- approval_type == explicit_operator_approval.
- actual_winner equals bound extracted_winner.
- source_date equals bound source_date.

## 15. Rollback strategy
Rollback objective:
- Restore ops/accuracy/actual_results_manual.json to exact pre-write bytes on any failure after write-start.

Strategy:
1. Compute pre_write_file_sha256 before mutation.
2. Write candidate output to temporary file.
3. Atomic replace target file.
4. On any post-start failure, restore pre-write file content.
5. Compute post_rollback_file_sha256 and compare to pre_write_file_sha256.

Rollback invariants:
- rollback_attempted and rollback_succeeded always auditable.
- No partial write survives a failed apply.
- Internal errors fail closed with no mutation.

## 16. Audit response shape
Audit envelope must include:
- correlation_id
- phase
- selected_key
- record_fight_id
- approval_required
- approval_granted
- approval_binding_valid
- approval_token_id
- approval_token_issued_at_utc
- approval_token_expires_at_utc
- approval_token_consumed
- operator_id
- approved_at_utc
- provider_attempted
- attempted_sources
- source_url
- source_title
- source_date
- publisher_host
- source_confidence
- confidence_score
- citation_fingerprint
- actual_winner
- write_target
- write_performed
- mutation_performed
- scoring_semantics_changed
- pre_write_file_sha256
- rollback_attempted
- rollback_succeeded
- post_rollback_file_sha256
- reason_code

Carry-forward requirement:
- provider_attempted, attempted_sources, and record_fight_id must carry forward from authoritative preview context.

## 17. Deny/manual-review response behavior
Deterministic deny reasons include at minimum:
- approval_missing
- approval_expired
- approval_replayed
- approval_token_consumed
- approval_binding_mismatch
- selected_key_not_found
- selected_key_binding_mismatch
- missing_citation_fingerprint
- citation_binding_mismatch
- source_url_binding_mismatch
- source_date_binding_mismatch
- extracted_winner_binding_mismatch
- record_identity_binding_mismatch
- citation_incomplete
- source_url_not_allowed
- publisher_host_mismatch
- identity_conflict
- preview_snapshot_mismatch
- preview_only_boundary_violation
- invalid_apply_mode
- invalid_lookup_intent
- single_record_required
- internal_apply_error

Manual-review blocking reasons include at minimum:
- source_conflict
- source_conflict_same_tier
- stale_source_date
- confidence_below_threshold
- tier_b_without_corroboration

Behavior invariants:
- Deny and manual-review outcomes never write.
- write_performed=false and mutation_performed=false.
- scoring_semantics_changed=false.

## 18. Test plan
Contract validation tests:
- Reject invalid mode, invalid intent, missing required fields, and multi-record payloads.

Token tests:
- Reject missing, expired, replayed, and consumed tokens.
- Reject any token-binding mismatch across bound fields.

Binding tests:
- selected_key mismatch.
- citation_fingerprint mismatch.
- source_url mismatch (including canonical normalization mismatch).
- source_date mismatch.
- extracted_winner mismatch.
- stable identity mismatch.

Revalidation tests:
- Deny when acceptance_gate.state != write_eligible.
- Deny when acceptance_gate.write_eligible != true.
- Deny when authoritative revalidation diverges from preview snapshot.
- Ensure identity_conflict is deny.

Mutation safety tests:
- Confirm write target restricted to ops/accuracy/actual_results_manual.json.
- Confirm no mutation on deny/manual-review.
- Confirm rollback restores exact pre-write hash on failure.

Boundary tests:
- No batch apply.
- No page-load apply.
- No automatic apply.
- No scoring semantics change.

## 19. Runtime safety checklist
Pre-enable checklist for future implementation:
- One-record-only enforcement is hard-fail.
- approval_granted true required.
- Valid token required (unexpired, unconsumed, unreplayed).
- Digest binding required for selected_key, citation_fingerprint, source_url, source_date, extracted_winner, and stable identity fields.
- Authoritative acceptance_gate revalidation required.
- acceptance_gate.state == write_eligible and write_eligible == true required.
- Write target fixed to ops/accuracy/actual_results_manual.json only.
- Atomic write plus rollback proof metadata required.
- write_performed=false on all deny/manual-review outcomes.
- scoring_semantics_changed=false for all outcomes.

## 20. Future implementation micro-slices
1. Slice A: apply request/response schema enforcement
- Add strict request parser and deterministic response envelope.
- Keep mutation disabled.

2. Slice B: approval token service and binding digest
- Add issue/validate/consume helpers with TTL and anti-replay.
- Keep mutation disabled.

3. Slice C: apply guard with authoritative revalidation
- Integrate selected_key resolution, gate revalidation, and deterministic deny/manual-review mapping.
- Keep mutation disabled.

4. Slice D: atomic manual actual-results write and rollback
- Enable single-record write to ops/accuracy/actual_results_manual.json.
- Add rollback and hash proof logic.

5. Slice E: audit/observability hardening
- Finalize audit envelope coverage and error-path metadata.
- Verify denial and rollback traceability.

6. Slice F: optional operator UI wiring
- Expose explicit apply control only after backend guardrails are proven.
- No automatic apply behavior.

---

Design status: ready for review.
Implementation status: intentionally not started.
