# official-source-approved-apply-global-ledger-implementation-design-v1

Status: DRAFT (docs-only)
Date: 2026-04-30
Owner: AI-RISA operator-dashboard governance
Predecessor lock: official-source-approved-apply-global-ledger-design-review-v1 (b82c9b8)

## 1) Implementation Scope
This document defines a future implementation planning boundary for global result ledger integration on top of the locked local one-record approved apply flow.

This is an implementation design artifact only. No implementation is authorized by this document.

## 2) Source Artifacts Reviewed
1. docs/official_source_approved_apply_global_ledger_design_v1.md
2. docs/official_source_approved_apply_global_ledger_design_review_v1.md

## 3) Locked Baseline Summary
1. Local one-record approved apply proof complete.
2. Approved apply temp write visible through /api/accuracy/comparison-summary.
3. Guard-deny keeps row waiting.
4. Guard-deny records operation_id audit row.
5. Read-side accuracy helpers honor local accuracy-dir override.
6. No token digest drift.
7. No token consume drift.
8. operation_id remains separate from internal mutation UUID.
9. No global result ledger behavior currently implemented.

## 4) Proposed Implementation Touchpoints
1. Approved apply endpoint.
2. Local audit helper.
3. Future global ledger helper.
4. Write sequencing boundary.
5. Duplicate/conflict lookup boundary.
6. Test surfaces.

## 5) Proposed Global Ledger Storage Model
1. Append-only JSONL or equivalent local file-backed ledger for the first implementation.
2. Deterministic serialization.
3. Stable field ordering.
4. No silent overwrite.
5. Isolated temp paths in tests.

## 6) Proposed Global Ledger Record Schema
1. global_ledger_record_id
2. local_result_key
3. event_id
4. bout_id
5. fighter_ids
6. fighter_names
7. official_source_reference
8. approved_actual_result
9. operation_id
10. internal_mutation_uuid
11. approval_token_status
12. guard_outcome
13. apply_or_write_outcome
14. token_consume_outcome
15. local_audit_reference
16. timestamp_utc
17. deterministic_status

## 7) Write Sequencing Plan
1. Validate request.
2. Validate approval token.
3. Run guard checks.
4. Perform local write.
5. Append local audit row.
6. Append global ledger row only after local success.
7. Consume token using internal mutation UUID path.
8. Return deterministic response.

## 8) Idempotency And Duplicate Rules
1. Global ledger must not replace local write path.
2. Global ledger must not become token identity.
3. Global ledger must not replace operation_id.
4. Global ledger must not replace internal mutation UUID.
5. Duplicate global record detection must be deterministic.
6. Conflicting duplicate must return explicit conflict state.

## 9) Failure Handling
The implementation plan must account for:
1. Local write succeeds but global ledger write fails.
2. Global ledger duplicate conflict.
3. Malformed operation_id.
4. Missing official source reference.
5. Guard deny.
6. Token consume failure.
7. Partial audit state.

Failure handling requirements:
1. Preserve local state integrity.
2. Preserve deterministic response classification.
3. Preserve append-only audit explainability.
4. Avoid silent corruption or overwrite.

## 10) Future Implementation Test Plan
1. One local success mirrored to global ledger.
2. Guard deny not mirrored as approved result but audited.
3. Duplicate global record conflict.
4. Retry after success deterministic.
5. Global ledger write failure does not corrupt local state.
6. Token digest unchanged.
7. Token consume unchanged.
8. Final git clean proof.

## 11) Explicit Non-Goals
1. No implementation in this slice.
2. No batch backfill.
3. No frontend expansion.
4. No external database integration.
5. No scoring rewrite.
6. No prediction model change.
7. No intake behavior change.
8. No report-generation behavior change.

## 12) Implementation Readiness Verdict
The global ledger implementation design is approved only as a planning artifact.

Actual global ledger implementation remains blocked until a separate implementation slice is explicitly opened and test-gated.
