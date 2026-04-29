# official-source-one-record-acceptance-gate-design-v1

## 1. Purpose
Define a design-only acceptance gate for determining when an official-source preview result can become eligible for a future approved single-record write.

This document defines policy and contract boundaries only.

## 2. Non-goals
- No implementation of write/apply logic.
- No backend behavior change.
- No UI/runtime wiring change.
- No batch behavior.
- No page-load lookup behavior.
- No mutation of actual-results files.
- No scoring formula or scoring semantics changes.
- No prediction logic, intake logic, or report pipeline changes.

## 3. Required input from preview result
A future write gate evaluation must consume a preview result object that includes, at minimum:
- selected_key
- selected_row (identity context, including fight_name and fight_id when present)
- source_citation
- reason_code
- manual_review_required
- candidate_urls_supplied
- candidate_url_count
- audit.provider_attempted
- audit.attempted_sources
- mutation_performed=false (preview boundary)
- external_lookup_performed (true/false)

If any required input is absent, write eligibility is denied.

## 4. Write-eligibility criteria
A preview result is write-eligible only when all of the following are true:
- Phase is preview outcome and mutation_performed is false.
- selected_key is present and resolves to exactly one waiting row.
- source_citation is present and complete (see Section 5).
- identity match passes between selected row and citation evidence.
- publisher host check passes (no host mismatch).
- source date is not stale per policy.
- source confidence tier and confidence score satisfy threshold policy.
- no source conflict exists (same-tier or cross-tier conflict).
- reason_code corresponds to accepted preview outcome.
- explicit operator approval is present and bound (Section 10).

Write eligibility is a gate result only. It does not perform a write.

## 5. Required citation fields
A citation is complete only if all required fields are present and non-empty:
- source_url (https)
- source_title
- source_date
- publisher_host
- source_confidence
- confidence_score
- citation_fingerprint
- extracted_winner

Recommended (not strictly required for initial gate decision):
- method
- round_time
- identity_matches_selected_row

Missing any required citation field blocks write eligibility.

## 6. Source-confidence thresholds
The gate uses the existing confidence mapping:
- tier_a0: 0.85
- tier_a1: 0.72
- tier_b: 0.55
- conflict/none: 0.0

Threshold policy for write eligibility:
- confidence_score >= 0.70 required for any write-eligible state.
- confidence_score < 0.70 is not write-eligible.

Tier policy:
- Tier A0 can be write-eligible only when citation is complete and identity match passes.
- Tier A1 can be write-eligible only when citation is complete and no conflict exists.
- Tier B alone is never write-eligible; manual-review only.

## 7. Accepted / manual-review / rejected states
Accepted (write-eligible gate outcome):
- Tier A0 or Tier A1
- Complete citation
- Identity match pass
- No conflict
- No stale date
- Confidence >= 0.70
- Approval binding valid

Manual-review required:
- Tier B without corroborating A-tier evidence
- Any conflict condition
- Any ambiguity in extracted winner identity
- Any stale date or borderline quality condition requiring operator judgment

Rejected (not eligible, no write path):
- Disallowed source URL or host
- Citation incomplete
- Identity conflict
- Publisher host mismatch
- Confidence below threshold
- Explicit deny reason from preview/provider validation

## 8. Deny reasons
Minimum deterministic deny/manual-review reason codes to support in the gate design:
- selected_key_not_found
- source_url_not_allowed
- publisher_host_mismatch
- citation_incomplete
- identity_conflict
- stale_source_date
- source_conflict_same_tier
- source_conflict
- tier_b_without_corroboration
- confidence_below_threshold
- candidate_urls_empty
- candidate_urls_exceeds_limit
- approval_binding_mismatch
- approval_expired
- approval_missing
- preview_only_boundary_violation

## 9. Operator approval requirements
Future write path must require explicit operator approval and all of:
- approval_granted=true on write request only
- operator identity/actor recorded in audit
- human confirmation timestamp recorded
- approval scoped to one selected_key only
- approval cannot be inferred from preview success

Preview alone can never authorize write.

## 10. Token/fingerprint binding requirements
Approval must be cryptographically bound to:
- selected_key
- citation_fingerprint
- source_url
- extracted_winner
- source_date

Binding rules:
- Any change in bound fields invalidates approval.
- Approval TTL maximum: 300 seconds.
- Expired approval is denied.
- Replay of consumed or stale approval token is denied.
- Binding mismatch returns approval_binding_mismatch.

## 11. Exact no-mutation preview boundary
Preview boundary is strict:
- mutation_performed must remain false.
- bulk_lookup_performed must remain false.
- scoring_semantics_changed must remain false.
- no file writes to any actual_results JSON artifacts.
- no queue mutation, no scoring recalculation side effects.

A gate decision computed during preview is advisory and non-mutating.

## 12. Future approved-write boundary
Future write endpoint boundary (not implemented in this slice):
- Requires explicit apply intent.
- Requires approval_granted=true.
- Requires valid selected_key + citation_fingerprint binding.
- Requires fresh re-validation that gate criteria still pass.
- Single-record only; batch disallowed.
- Must preserve scoring semantics unchanged.

If any condition fails, write is blocked and a deterministic deny reason is returned.

## 13. Audit fields required before write
Before any future write attempt, audit envelope must include:
- correlation_id
- selected_key
- record_fight_id
- phase
- approval_required
- approval_granted
- operator_id (or equivalent actor field)
- provider_attempted
- attempted_sources
- source_url
- source_title
- source_date
- publisher_host
- source_confidence
- confidence_score
- citation_fingerprint
- reason_code
- write_performed
- mutation_performed
- scoring_semantics_changed
- created_at_utc

Missing required audit fields blocks write.

## 14. Test requirements before implementation
Before enabling any write behavior, implementation must include tests for:
- Contract validation
  - reject missing/invalid selected_key
  - reject invalid mode/intent transitions
  - reject write without approval
- Gate correctness
  - A0 and A1 eligibility success paths
  - Tier B manual-review-only path
  - conflict/stale/identity/citation failures
  - confidence threshold boundary behavior
- Binding integrity
  - selected_key + citation_fingerprint binding enforcement
  - token expiry and replay rejection
  - field-change invalidation after preview
- Safety boundaries
  - no write from preview-only endpoint
  - no batch behavior
  - no page-load lookup trigger
  - scoring_semantics_changed remains false
- Mutation safety
  - no mutation of actual_results files in preview phase
  - rollback on failed write attempt in future write slice

## 15. Failure and rollback requirements
Failure handling requirements for future write slice:
- Any gate failure returns deterministic reason_code and write_performed=false.
- Partial write attempts must roll back to pre-write state.
- Rollback outcome must be auditable (reason_code and rollback status).
- On internal errors, default to safe denial (no mutation).
- No silent fallback to weaker sources.

## 16. Future implementation slices
Recommended safe sequence after this design lock:
1. Contract-only acceptance-gate evaluator (read-only; no write).
2. Approval binding service (token TTL + anti-replay), still no write.
3. Apply endpoint guard integration for single-record only.
4. Transaction-safe single-record write with rollback guarantees.
5. Audit/observability hardening for gate outcomes and denials.
6. UI exposure of gate decision state (read-only indicators), no auto-run.

---

Design status: ready for review.
Implementation status: intentionally not started.
