# official-source-approved-apply-contract-v1

## 1. Purpose
Define a docs-only request/response contract for a future approved single-record official-source apply endpoint.

This contract exists to describe how a future write request would be validated against a previously previewed, approval-bound official-source result without implementing any runtime behavior.

## 2. Non-goals
- No endpoint implementation.
- No backend behavior changes.
- No UI or runtime wiring changes.
- No write/apply implementation.
- No batch behavior.
- No page-load apply behavior.
- No mutation of any actual-results files in this slice.
- No provider or evaluator behavior change.
- No scoring formula or scoring semantics changes.
- No external lookup execution.

## 3. Endpoint name proposal
Proposed future endpoint name:
- `POST /api/operator/actual-result-lookup/official-source-approved-apply`

Endpoint boundary rules:
- One-record only.
- Explicit operator action only.
- Never callable from page load.
- Never callable as part of a batch flow.
- Never implied by preview success alone.

## 4. Request schema
Proposed future request body:

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
    "extracted_winner": "string"
  },
  "preview_snapshot": {
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
      "citation_fingerprint": "string"
    }
  },
  "operator_note": "string"
}
```

Request rules:
- `mode` must be exactly `official_source_approved_apply`.
- `lookup_intent` must be exactly `apply_write`.
- `selected_key` is required and must contain exactly one record key.
- `approval_granted` is required and must be `true`.
- `approval_token` is required.
- `approval_binding` is required.
- `preview_snapshot` is required.
- `operator_note` is optional and informational only.

## 5. Response schema
Proposed future response body:

```json
{
  "ok": true,
  "mode": "official_source_approved_apply",
  "phase": "approved_apply",
  "selected_key": "string",
  "approval_required": true,
  "approval_granted": true,
  "approval_binding_valid": true,
  "manual_review_required": false,
  "mutation_performed": false,
  "bulk_lookup_performed": false,
  "external_lookup_performed": false,
  "scoring_semantics_changed": false,
  "write_performed": false,
  "write_target": "ops/accuracy/actual_results_manual.json",
  "selected_row": {},
  "source_citation": {
    "source_url": "string",
    "source_title": "string",
    "source_date": "string",
    "publisher_host": "string",
    "source_confidence": "string",
    "confidence_score": 0.0,
    "citation_fingerprint": "string",
    "extracted_winner": "string"
  },
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
    "operator_id": "string",
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
    "reason_code": "string"
  },
  "message": "string"
}
```

Response rules:
- `write_target` must always be the manual actual-results path.
- `bulk_lookup_performed` must remain `false`.
- `scoring_semantics_changed` must remain `false`.
- On any denied or manual-review outcome, `write_performed=false` and `mutation_performed=false`.
- `proposed_write` is contract data only in this slice and does not imply a file mutation.

## 6. Required selected_key binding
The future apply request must be bound to exactly one preview-selected record.

Binding requirements:
- The request must contain exactly one `selected_key`.
- The request `selected_key` must equal the `approval_binding.selected_key` value.
- The request `selected_key` must equal `preview_snapshot.acceptance_gate.selected_key` when present.
- The request `selected_key` must still resolve to the same waiting-row identity during future implementation.
- Any changed `selected_key` invalidates approval and blocks write.

## 7. Required citation_fingerprint binding
The future apply request must be bound to exactly one previewed citation fingerprint.

Binding requirements:
- `approval_binding.citation_fingerprint` is required.
- `preview_snapshot.source_citation.citation_fingerprint` is required.
- `preview_snapshot.acceptance_gate.citation_fingerprint` is required.
- All fingerprint values must match exactly.
- Missing fingerprint blocks write.
- Any changed fingerprint invalidates approval and blocks write.

## 8. Required source_url binding
The future apply request must bind to the exact previewed `source_url`.

Binding requirements:
- `approval_binding.source_url` is required.
- `preview_snapshot.source_citation.source_url` is required.
- Both values must match exactly.
- The URL must remain HTTPS and policy-compliant.
- Any changed `source_url` invalidates approval and blocks write.

## 9. Required extracted_winner binding
The future apply request must bind to the exact previewed extracted winner.

Binding requirements:
- `approval_binding.extracted_winner` is required.
- `preview_snapshot.source_citation.extracted_winner` is required.
- `proposed_write.actual_winner` must equal the previewed extracted winner.
- Any changed winner value invalidates approval and blocks write.

## 10. Required acceptance_gate state
The future apply contract permits write only when all of the following are true:
- `preview_snapshot.acceptance_gate.state == write_eligible`
- `preview_snapshot.acceptance_gate.write_eligible == true`
- `preview_snapshot.acceptance_gate.reason_code == accepted_preview_write_eligible`
- `preview_snapshot.manual_review_required == false`

Blocking rules:
- `manual_review` blocks write.
- `rejected` blocks write.
- Missing `acceptance_gate` blocks write.
- Missing or false `write_eligible` blocks write.
- Tier B alone must never write.

## 11. Operator approval token model
The future apply contract must require explicit operator approval via a single-use approval token.

Approval token requirements:
- Issued only after a preview result is present.
- Bound to one `selected_key` only.
- Bound to one `citation_fingerprint` only.
- Bound to one `source_url` only.
- Bound to one `extracted_winner` only.
- Short TTL only.
- Replay-safe and single-use only.

Validation requirements:
- Missing token returns denial.
- Expired token returns denial.
- Replayed token returns denial.
- Token-binding mismatch returns denial.
- Preview success alone cannot substitute for approval.

## 12. Write target constraints
The future apply contract may target only:
- `ops/accuracy/actual_results_manual.json`

Disallowed targets:
- `ops/accuracy/actual_results.json`
- `ops/accuracy/actual_results_unresolved.json`
- Any queue file
- Any batch output file
- Any external store

Target invariants:
- One-record write only.
- No batch apply.
- No alternate destination in this version.

## 13. Exact proposed write schema
The future apply contract must describe a deterministic proposed-write payload.

Required fields:
- `fight_id`
- `fight_name`
- `actual_winner`
- `source`
- `source_url`
- `source_title`
- `source_date`
- `publisher_host`
- `source_confidence`
- `confidence_score`
- `citation_fingerprint`
- `selected_key`
- `write_mode`
- `approval_type`
- `operator_id`
- `approved_at_utc`

Optional fields:
- `method`
- `round_time`
- `event_name`
- `event_date`
- `notes`

Schema rules:
- `source` should be `official_source_manual_approved`.
- `write_mode` should be `official_source_approved_apply`.
- `approval_type` should be `explicit_operator_approval`.
- `actual_winner` must equal previewed `extracted_winner`.
- The schema must preserve preview-selected identity context.

## 14. Deny states
The future apply contract must return deterministic deny states for at least:
- `approval_missing`
- `approval_expired`
- `approval_binding_mismatch`
- `selected_key_not_found`
- `selected_key_binding_mismatch`
- `missing_citation_fingerprint`
- `citation_binding_mismatch`
- `source_url_binding_mismatch`
- `extracted_winner_binding_mismatch`
- `citation_incomplete`
- `source_url_not_allowed`
- `publisher_host_mismatch`
- `identity_conflict`
- `preview_only_boundary_violation`
- `invalid_apply_mode`
- `invalid_lookup_intent`
- `single_record_required`
- `internal_apply_error`

Denied outcomes must return:
- `write_performed=false`
- `mutation_performed=false`
- `bulk_lookup_performed=false`
- `scoring_semantics_changed=false`

## 15. Manual-review states
The future apply contract must preserve manual-review blocking states for at least:
- `source_conflict`
- `source_conflict_same_tier`
- `stale_source_date`
- `confidence_below_threshold`
- `tier_b_without_corroboration`
- `identity_conflict` when the future implementation chooses review instead of hard deny

Manual-review outcomes must:
- block write
- set `manual_review_required=true`
- keep `write_performed=false`
- keep `mutation_performed=false`

## 16. Audit fields
The future apply contract must require an audit envelope containing, at minimum:
- `correlation_id`
- `phase`
- `selected_key`
- `record_fight_id`
- `approval_required`
- `approval_granted`
- `approval_binding_valid`
- `operator_id`
- `approved_at_utc`
- `source_url`
- `source_title`
- `source_date`
- `publisher_host`
- `source_confidence`
- `confidence_score`
- `citation_fingerprint`
- `actual_winner`
- `write_target`
- `write_performed`
- `mutation_performed`
- `scoring_semantics_changed`
- `reason_code`

Audit rules:
- Missing required audit fields must block write.
- Audit data must be available for success, denial, and rollback outcomes.

## 17. Rollback requirements
Future implementation must treat rollback as mandatory, not optional.

Rollback requirements:
- If an approved write fails after write-start, the manual actual-results file must be restored to its exact pre-write state.
- Rollback must apply only to `ops/accuracy/actual_results_manual.json`.
- Rollback outcome must be recorded in audit data.
- No partial write may survive a failure.
- Any internal error must fail closed.

## 18. No-mutation preview boundary
The current preview boundary remains unchanged:
- Preview is read-only.
- Preview alone must never write.
- Preview alone must never apply.
- Preview must never change actual-results artifacts.
- Preview must never change scoring semantics.
- Preview must never imply approval.

## 19. Approved-write boundary
The future apply boundary must remain explicit and narrow:
- One-record only.
- Explicit operator action only.
- Explicit approval token required.
- Fresh binding validation required.
- Fresh acceptance-gate validation required.
- Write target limited to the manual actual-results file only.
- No batch mode.
- No page-load apply.
- No automatic apply.
- No scoring semantics change.

## 20. Pre-implementation test requirements
Before any implementation, tests must cover at least:
- request schema validation
- response contract validation
- one-record-only enforcement
- denial when `acceptance_gate.write_eligible != true`
- denial when `acceptance_gate.state != write_eligible`
- denial when `selected_key` changes after preview
- denial when `citation_fingerprint` changes after preview
- denial when `source_url` changes after preview
- denial when `extracted_winner` changes after preview
- denial when approval token is missing, expired, or replayed
- denial for Tier B-only evidence
- denial or manual-review for stale/conflict states
- no preview mutation
- no batch apply
- no page-load apply
- no scoring semantics change
- rollback restoring exact pre-write manual-results file state

## 21. Future implementation slices
Recommended safe sequence after this contract lock:
1. Review and lock the apply request/response contract.
2. Add approval-token and binding validation helpers with no file mutation.
3. Add a non-mutating apply guard that returns deterministic denials and manual-review outcomes.
4. Add atomic single-record manual actual-results apply with rollback.
5. Add audit and observability hardening for apply attempts, denials, and rollbacks.
6. Add optional explicit-approval UI only after backend guardrails are locked.

---

Design status: ready for review.
Implementation status: intentionally not started.