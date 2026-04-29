# official-source-approved-write-design-v1

## 1. Purpose
Define the future design for an approved single-record official-source write that can occur only after a successful official-source preview and acceptance-gate decision.

This document is design-only. It introduces no implementation, no runtime wiring, and no behavior change.

## 2. Non-goals
- No implementation of write/apply logic.
- No backend behavior changes.
- No UI/runtime wiring changes.
- No page-load lookup behavior.
- No batch behavior.
- No provider or evaluator behavior change.
- No mutation of actual-results files in this slice.
- No scoring formula or scoring semantics changes.
- No automatic approval, replay, or background processing.

## 3. Required input from official-source preview response
A future approved-write request must be derived from one official-source preview response and must require, at minimum:
- `mode=official_source_one_record_preview`
- `selected_key`
- `selected_row`
- `reason_code`
- `manual_review_required`
- `mutation_performed=false`
- `external_lookup_performed`
- `bulk_lookup_performed=false`
- `scoring_semantics_changed=false`
- `source_citation`
- `acceptance_gate`
- `audit.provider_attempted`
- `audit.attempted_sources`
- `audit.record_fight_id`

If any required input is absent, the future write path must deny the request.

## 4. Required acceptance_gate state
Future approved write can proceed only when all of the following are true:
- `acceptance_gate.state == write_eligible`
- `acceptance_gate.write_eligible == true`
- `acceptance_gate.reason_code == accepted_preview_write_eligible`
- `manual_review_required == false`
- `mutation_performed == false`
- `bulk_lookup_performed == false`
- `scoring_semantics_changed == false`

Blocking states:
- `acceptance_gate.state == manual_review` blocks write.
- `acceptance_gate.state == rejected` blocks write.
- Missing `acceptance_gate` blocks write.
- Missing or false `acceptance_gate.write_eligible` blocks write.

## 5. Required citation fields
The future write path must require a complete citation containing all of:
- `source_url`
- `source_title`
- `source_date`
- `publisher_host`
- `source_confidence`
- `confidence_score`
- `citation_fingerprint`
- `extracted_winner`

Recommended but not sufficient on their own:
- `method`
- `round_time`
- `identity_matches_selected_row`

Missing any required citation field blocks write.

## 6. Required selected_key binding
Future approval must bind to exactly one preview-selected record.

Binding rules:
- The approved write request must contain exactly one `selected_key`.
- The `selected_key` must match the preview response exactly.
- The `selected_key` must still resolve to the same waiting row identity at apply time.
- Any changed `selected_key` invalidates approval and blocks write.
- Preview success for one `selected_key` must never authorize a different record.

## 7. Required citation_fingerprint binding
Future approval must bind to the exact preview citation used to earn write eligibility.

Binding rules:
- `citation_fingerprint` is mandatory.
- Missing `citation_fingerprint` blocks write.
- The approved write request must present the same `citation_fingerprint` returned by preview.
- Any changed citation fingerprint invalidates approval and blocks write.
- Any changed citation data that would alter the fingerprint invalidates approval and blocks write.

Minimum bound fields:
- `selected_key`
- `citation_fingerprint`
- `source_url`
- `extracted_winner`

Recommended full binding set:
- `selected_key`
- `citation_fingerprint`
- `source_url`
- `source_title`
- `source_date`
- `publisher_host`
- `extracted_winner`
- `method`
- `round_time`

## 8. Operator approval model
Future approved write must require explicit operator approval.

Approval model:
- Preview phase remains non-mutating and advisory only.
- Approved-write phase must require an explicit operator action distinct from preview.
- Approval must be scoped to one record only.
- Approval must be bound to the selected key and citation binding fields.
- Approval cannot be inferred from a successful preview response.
- Approval must expire after a short TTL in the future implementation.
- Replay of consumed or expired approval must be denied.

Mandatory policy:
- Preview alone can never write.
- `acceptance_gate.write_eligible=true` is necessary but not sufficient; explicit operator approval is also required.

## 9. Write target path
The only allowed future write target in v1 design is the local manual actual-results path:
- `ops/accuracy/actual_results_manual.json`

Disallowed targets in this design:
- `ops/accuracy/actual_results.json`
- `ops/accuracy/actual_results_unresolved.json`
- Any batch queue artifact
- Any remote or external store

No alternate target is allowed unless a later design explicitly approves it.

## 10. Exact write schema
Future approved write must be single-record only and must append or upsert one manual actual-result record using a deterministic schema.

Required record fields:
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

Optional fields when present in bound citation:
- `method`
- `round_time`
- `event_name`
- `event_date`
- `notes`

Schema rules:
- `actual_winner` must equal `source_citation.extracted_winner`.
- `source` should be a deterministic literal such as `official_source_manual_approved`.
- `write_mode` should identify single-record approved write only.
- The record must preserve the preview-selected identity context.
- Scoring semantics must remain unchanged.

## 11. Manual-review / denied states
Write must be blocked for any manual-review or denied state.

Manual-review blockers:
- `acceptance_gate.state == manual_review`
- `reason_code == stale_source_date`
- `reason_code == source_conflict`
- `reason_code == source_conflict_same_tier`
- `reason_code == confidence_below_threshold`
- `reason_code == tier_b_without_corroboration`

Rejected blockers:
- `acceptance_gate.state == rejected`
- `reason_code == citation_incomplete`
- `reason_code == identity_conflict`
- `reason_code == publisher_host_mismatch`
- `reason_code == source_url_not_allowed`
- `reason_code == preview_only_boundary_violation`
- `reason_code == missing_citation_fingerprint`
- `reason_code == approval_missing`
- `reason_code == approval_binding_mismatch`
- `reason_code == selected_key_not_found`

Mandatory policy:
- Tier B alone can never write.
- Any manual-review or rejected acceptance-gate state blocks write.

## 12. Audit fields
Future approved write must emit an audit envelope with, at minimum:
- `correlation_id`
- `phase`
- `selected_key`
- `record_fight_id`
- `approval_required`
- `approval_granted`
- `operator_id`
- `approved_at_utc`
- `provider_attempted`
- `attempted_sources`
- `source_url`
- `source_title`
- `source_date`
- `publisher_host`
- `source_confidence`
- `confidence_score`
- `citation_fingerprint`
- `actual_winner`
- `reason_code`
- `write_target`
- `write_performed`
- `mutation_performed`
- `scoring_semantics_changed`

Audit invariants:
- Missing required audit fields blocks write.
- `write_performed` and `mutation_performed` must remain false on denial.
- `scoring_semantics_changed` must remain false in all outcomes.

## 13. No-mutation preview boundary
The current official-source preview boundary remains strict:
- Preview is read-only.
- Preview computes eligibility only.
- Preview must never write or apply.
- Preview must never change queue state.
- Preview must never change actual-results artifacts.
- Preview must never change scoring semantics.

Any future implementation must preserve this boundary fully.

## 14. Approved-write boundary
The future approved-write phase must be a distinct boundary from preview.

Approved-write rules:
- Single-record only.
- Explicit apply intent required.
- Explicit operator approval required.
- Fresh binding validation required before write.
- Fresh gate validation required before write.
- Write target limited to manual actual-results path only.
- No batch mode.
- No implicit fallback to weaker evidence.
- No scoring semantics change.

If any rule fails, the future write must deny safely with no mutation.

## 15. Failure and rollback rules
Future implementation must default to safe denial.

Failure rules:
- Any failed validation returns a deterministic deny reason.
- Any failed approval or binding check returns a deterministic deny reason.
- Any failed write preparation returns `write_performed=false`.
- No partial write may survive an error.
- Any internal error must fail closed and preserve all actual-results files unchanged.

Rollback rules for future implementation:
- If a write attempt begins and cannot complete atomically, the target file must be restored to its exact pre-write state.
- Rollback outcome must be auditable.
- No silent retry, auto-repair, or fallback write is permitted.

## 16. Test requirements before implementation
Future implementation must include tests for at least:
- allowing write only when `acceptance_gate.write_eligible=true`
- denying write for any `manual_review` state
- denying write for any `rejected` state
- denying write when `citation_fingerprint` is missing
- denying write when `selected_key` changes after preview
- denying write when bound citation data changes after preview
- denying write without explicit operator approval
- denying Tier B-only evidence
- preserving preview no-mutation behavior
- preserving no batch behavior
- preserving no page-load lookup behavior
- preserving no scoring semantics change
- proving write target is limited to `ops/accuracy/actual_results_manual.json`
- proving rollback restores exact pre-write state on failure

## 17. Future implementation slices
Recommended safe sequence after this design lock:
1. Add a docs-reviewed request/response contract for approved single-record apply, still with no write implementation.
2. Add approval-binding validation helpers, still with no file mutation.
3. Add denied-state and binding checks to a non-mutating apply guard.
4. Add atomic single-record manual actual-results write with rollback guarantees.
5. Add audit and observability coverage for approved-write attempts and denials.
6. Add focused UI affordance for explicit operator approval only after backend guardrails are locked.

---

Design status: ready for review.
Implementation status: intentionally not started.