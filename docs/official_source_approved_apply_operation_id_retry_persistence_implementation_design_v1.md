# official-source-approved-apply-operation-id-retry-persistence-implementation-design-v1

Status: DRAFT (docs-only)
Date: 2026-04-30
Owner: operator-dashboard
Predecessor locks:
- official-source-approved-apply-operation-id-retry-persistence-design-v1 (4f86d87)
- official-source-approved-apply-operation-id-retry-persistence-design-review-v1 (94aa956)

## 1) Implementation Scope
This document defines a future implementation plan for operation_id retry and persistence behavior in the official-source approved-apply flow.

This is an implementation-design artifact only.

In scope for planning:
1. Identify expected code touchpoints for a future slice.
2. Define persistence fields and retry-state classification.
3. Define future idempotency, audit, and failure-handling boundaries.
4. Define future test touchpoints and required validation gates.

Out of scope:
1. No code changes.
2. No retry or persistence implementation.
3. No endpoint behavior changes.
4. No token digest semantic changes.
5. No token consume semantic changes.
6. No mutation behavior changes.
7. No UI, dashboard, scoring, batch, ledger runtime, prediction, intake, report, or global database behavior changes.
8. No runtime file creation.
9. No test execution.

## 2) Source Artifacts Reviewed
1. docs/official_source_approved_apply_operation_id_retry_persistence_design_v1.md
2. docs/official_source_approved_apply_operation_id_retry_persistence_design_review_v1.md

## 3) Current Locked Baseline Summary
The future implementation plan must preserve the currently locked baseline:
1. operation_id is optional.
2. Request omission remains backward compatible.
3. Surfaced request operation_id remains separate from the internal mutation UUID.
4. Token digest semantics remain unchanged.
5. Token consume semantics remain unchanged.

These baseline rules are locked and are not negotiable in the future implementation slice unless separately re-approved.

## 4) Proposed Code Touchpoints
### 4.1 Endpoint handler touchpoint
Expected future touchpoint:
- official-source approved-apply endpoint handler where parsed request operation_id is already surfaced.

Planned responsibility:
- consult future retry/persistence helper only after request parsing and schema normalization are complete.
- do not bypass existing authorization or guard flow.

### 4.2 Response envelope touchpoint
Expected future touchpoint:
- approved-apply normalized response envelope.

Planned responsibility:
- surface retry/persistence classification additively where authorized by a future slice.
- preserve existing operation_id response field and deterministic ordering.

### 4.3 Append-only audit/ledger touchpoint
Expected future touchpoint:
- append-only audit or ledger write helper dedicated to approved-apply retry/persistence records.

Planned responsibility:
- record terminal attempt outcomes without in-place mutation of prior records.
- persist operation_id and internal mutation UUID as separate fields.

### 4.4 Duplicate/retry lookup touchpoint
Expected future touchpoint:
- helper or lookup layer that classifies prior operation_id state from append-only records.

Planned responsibility:
- determine whether the operation_id is unseen, already-applied, previously denied, conflicting, or otherwise non-retryable.

### 4.5 Test touchpoints
Expected future touchpoints:
1. focused backend tests for approved-apply endpoint behavior
2. persistence-helper unit tests
3. append-only audit/ledger tests
4. targeted regression tests for token and consume invariants

## 5) Proposed Persistence Fields
A future append-only record should include at minimum:
1. operation_id
2. internal_mutation_operation_id
3. write_attempt_id
4. request_parse_status
5. guard_or_authorization_outcome
6. apply_or_write_outcome
7. token_consume_outcome
8. timestamp_utc
9. deterministic_status

Additional stable fields may include:
1. token_id
2. selected_key
3. terminal_reason_code
4. contract_version
5. endpoint_version

Field constraints:
1. request operation_id and internal mutation UUID must remain separate.
2. deterministic_status must be stable and explicit.
3. no persistence field may redefine token identity.

## 6) Retry Behavior Matrix
### 6.1 No operation_id
Expected future behavior:
- remain backward compatible.
- no forced persistence lookup requirement.
- existing endpoint behavior remains primary.

### 6.2 First operation_id use
Expected future behavior:
- treat as first-seen request if no prior append-only record exists.
- allow normal schema, authorization, guard, mutation, and consume flow to proceed.
- record the resulting terminal state append-only.

### 6.3 Same operation_id retry after success
Expected future behavior:
- classify deterministically as already applied or replay-equivalent.
- do not silently perform duplicate mutation.
- surface stable outcome metadata without changing locked token/consume semantics.

### 6.4 Same operation_id retry after deny
Expected future behavior:
- classify deterministically as prior deny or retry-not-eligible according to future policy.
- do not bypass current authorization or guard semantics.

### 6.5 Duplicate operation_id with different payload
Expected future behavior:
- classify as explicit conflict.
- do not mutate data.
- do not overwrite prior records.

### 6.6 Malformed operation_id
Expected future behavior:
- remain governed by schema failure.
- persistence lookup and append-only write must not run.

### 6.7 Unparsed payload
Expected future behavior:
- no retry/persistence interaction.
- preserve current non-JSON or invalid-request handling.

## 7) Idempotency Rules
1. operation_id must not replace token identity.
2. operation_id must not replace internal mutation UUID.
3. operation_id must not bypass authorization.
4. operation_id must not bypass guard checks.
5. operation_id must not alter token digest material.
6. operation_id must not alter token consume state transitions.

Additional planning rule:
- a future implementation must treat operation_id as a caller-supplied retry correlation key only, not as the primary authoritative mutation key.

## 8) Audit/Ledger Write Rules
1. All retry/persistence recording must be append-only.
2. Field ordering in serialized records must be deterministic.
3. No silent overwrite of existing records is allowed.
4. Duplicate detection must be stable and reproducible.
5. Outcome status must be explicit.

Recommended deterministic_status examples for future policy discussion:
1. parse_rejected
2. schema_invalid
3. guard_denied
4. write_applied
5. write_failed
6. consume_failed_after_write
7. duplicate_conflict
8. already_applied_replay

These labels are planning examples only and are not implementation authorization.

## 9) Failure Handling
### 9.1 Parse failure
- preserve current endpoint behavior.
- do not run persistence lookup.
- do not append retry record unless a future slice explicitly approves parse-failure audit recording.

### 9.2 Schema failure
- preserve current schema-driven response.
- do not append success-like records.
- future audit recording, if added, must distinguish schema_invalid clearly.

### 9.3 Guard deny
- preserve current deny behavior.
- future retry record may capture deny terminal state append-only.

### 9.4 Duplicate conflict
- return explicit conflict classification in a future slice.
- do not mutate existing records or perform mutation side effects.

### 9.5 Already-applied retry
- return deterministic replay-style result in a future slice.
- do not perform duplicate write.

### 9.6 Write failure
- preserve mutation failure semantics.
- record failure append-only only if a future slice explicitly authorizes it.

### 9.7 Consume failure
- preserve current token consume failure semantics.
- future persistence may record consume_failed_after_write as an append-only terminal state without changing consume transitions.

## 10) Future Implementation Test Plan
A future implementation slice must include tests proving:
1. no operation_id compatibility remains intact
2. first success records operation_id deterministically
3. retry after success is deterministic
4. retry after deny is deterministic
5. duplicate operation_id conflict is handled explicitly
6. malformed operation_id does not corrupt state
7. operation_id is excluded from token digest
8. token consume still uses internal mutation UUID
9. audit or ledger remains append-only
10. final git state remains clean after validation

Additional recommended checks:
1. conflicting duplicate payloads do not rewrite prior records
2. stable record ordering is preserved
3. internal mutation UUID remains separately surfaced and audited

## 11) Non-Goals
1. No implementation in this slice.
2. No code edits.
3. No test edits.
4. No endpoint behavior changes.
5. No retry policy activation.
6. No persistence activation.
7. No token digest changes.
8. No token consume changes.
9. No mutation behavior changes.
10. No runtime artifacts.
11. No broad system behavior changes outside approved-apply retry/persistence planning.

## 12) Implementation Readiness Verdict
The implementation design is approved only as a planning artifact.

Actual retry/persistence code remains blocked until a separate implementation slice is explicitly opened, narrowly scoped, and test-gated.

## 13) Recommended Next Safe Slice
Recommended next slice:
- official-source-approved-apply-operation-id-retry-persistence-implementation-design-review-v1

That next slice should remain docs-only and review whether the proposed implementation plan preserves locked endpoint-binding behavior, append-only persistence expectations, and unchanged token digest/consume semantics.
