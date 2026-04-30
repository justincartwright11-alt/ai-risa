# official-source-approved-apply-local-one-record-flow-design-v1

Status: DRAFT (docs-only)
Date: 2026-04-30
Owner: operator-dashboard
Predecessor lock: official-source-approved-apply-operation-id-retry-persistence-final-review-v1 (56f086a)

## 1) Purpose
Define the next design boundary for proving the local one-record approved official-source result write path end-to-end.

This design is intentionally limited to a single local approved-result write path that bridges the locked official-source approved-apply endpoint behavior to the downstream local accuracy and report-scoring workflow.

This is a design-only slice.

## 2) Locked Baseline
The following behavior is already locked and must be preserved:
1. operation_id remains optional.
2. No-operation_id requests remain backward compatible.
3. operation_id remains separate from the internal mutation UUID.
4. Retry/persistence uses append-only audit rows.
5. Retry after success is deterministic.
6. Retry after deny is deterministic.
7. Duplicate conflicting operation_id is handled deterministically.
8. Malformed operation_id does not corrupt persistence state.
9. Token digest semantics remain unchanged.
10. Token consume remains tied to the internal mutation UUID.

## 3) Local One-Record Workflow
The intended local one-record workflow is:
1. Operator identifies one unresolved prediction or result row.
2. Official-source lookup confirms the actual result for that one row.
3. Approval token is generated and later validated against the locked binding semantics.
4. The approved-apply endpoint is called for that one record.
5. operation_id may be supplied for audit and retry tracking.
6. Local mutation or write occurs only after guard approval.
7. Append-only audit row is recorded for operation_id when present and parsed.
8. Token consume remains internal-mutation-UUID based.
9. The final local state is available to the existing accuracy or report-scoring workflow.

## 4) Required Local Evidence
The local one-record flow must make available or preserve the following evidence items:
1. selected prediction or result key
2. official source reference
3. approval token status
4. operation_id
5. internal mutation UUID
6. guard outcome
7. apply or write outcome
8. token consume outcome
9. deterministic final status

This evidence should be sufficient to explain why a one-record local write did or did not occur.

## 5) Boundaries
This design explicitly does not expand into:
1. global database behavior
2. global result ledger integration
3. cross-event automation
4. batch backfill
5. UI expansion
6. scoring rewrite
7. prediction model change

The local one-record flow must remain a narrow endpoint-to-local-write path only.

## 6) Success Criteria
The local one-record approved-result write path is successful only if:
1. one record can be safely approved
2. one record can be written locally
3. one record can be audited
4. retry behavior is deterministic
5. failed or denied attempt is auditable
6. token digest semantics remain unchanged
7. token consume semantics remain unchanged

## 7) Failure Handling
The design must account for the following local failure modes:
1. unresolved official source
2. mismatched fighter or result key
3. invalid approval token
4. guard deny
5. duplicate operation_id conflict
6. write failure
7. consume failure

For each failure class, the local one-record path must preserve deterministic status reporting and avoid silent state corruption.

## 8) Relationship To Accuracy And Report-Scoring Workflow
This local flow is intended to provide a reliable, auditable source of one approved actual-result write that downstream local accuracy and report-scoring workflows can consume without redefining those workflows.

This means:
1. the approved local write becomes the input state for existing accuracy handling
2. report-scoring consumes the local written result through existing workflow boundaries
3. no scoring semantics are changed by this design slice
4. no report-generation logic is changed by this design slice

## 9) Future Implementation Test Plan
A future implementation slice should include tests proving:
1. one clean success path
2. one deny path
3. one retry-after-success path
4. one duplicate conflict path
5. one malformed operation_id path
6. one final clean git state proof

These tests should remain narrowly scoped to the local one-record approved-result write path.

## 10) Explicit Non-Goals
1. No code changes.
2. No endpoint behavior changes.
3. No token digest changes.
4. No token consume changes.
5. No mutation semantic changes.
6. No global result ledger work.
7. No global database work.
8. No UI or dashboard expansion.
9. No scoring rewrite.
10. No prediction model changes.
11. No batch or automation expansion.
12. No runtime file creation.
13. No test execution in this slice.

## 11) Final Design Verdict
The local one-record approved result write path is approved as the next design boundary.

Implementation remains blocked until a separate implementation slice is explicitly opened and test-gated.

## 12) Recommended Next Safe Slice
Recommended next slice:
- official-source-approved-apply-local-one-record-flow-design-review-v1

That next slice should remain docs-only and verify that the local one-record flow stays narrow, deterministic, auditable, and compatible with the already locked approved-apply operation_id behavior.
