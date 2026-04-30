# official-source-approved-apply-operation-id-retry-persistence-design-v1

Status: DRAFT (docs-only)
Date: 2026-04-30
Owner: operator-dashboard
Predecessor lock: official-source-approved-apply-operation-id-endpoint-binding-implementation-v1 (aefde15)

## 1) Purpose
This design defines the future boundary for operation_id retry and persistence behavior for the official-source approved-apply flow.

The goal is to specify how a caller-supplied top-level operation_id may be recorded and interpreted across retries without changing any currently locked authorization, token, mutation, or consume semantics.

This document is design-only and does not authorize implementation.

## 2) Current Locked Behavior
Current locked behavior at commit aefde15:
1. operation_id is an optional top-level request field.
2. Requests that omit operation_id remain backward compatible.
3. The surfaced response operation_id is the parsed request value and remains separate from the internal mutation UUID.
4. Token digest semantics are unchanged.
5. Token consume semantics are unchanged.
6. Existing authorization, guard, deny, and mutation semantics remain unchanged.

These behaviors are locked and must remain stable unless a later explicitly approved implementation slice says otherwise.

## 3) Proposed Persistence Model
### 3.1 Persistence objective
A future implementation slice may persist operation_id to support deterministic retry interpretation and auditability.

### 3.2 Recommended recording location
Preferred future recording model:
1. Record operation_id in an append-only approved-apply audit ledger entry.
2. Record the associated internal mutation UUID in the same audit entry as a separate field.
3. Optionally mirror operation_id into an endpoint response audit field when a write or deny event is recorded.

### 3.3 Persistence shape
A future append-only persistence record should include deterministic fields such as:
1. operation_id
2. internal_mutation_operation_id
3. write_attempt_id
4. token_id
5. selected_key
6. request_parse_state
7. guard_decision
8. terminal_reason_code
9. timestamp_utc
10. contract_version
11. endpoint_version

### 3.4 Non-membership in token digest material
operation_id must not be added to approval token digest material.
operation_id must not alter existing binding digest construction.
operation_id must not become part of token identity or token consume identity.

## 4) Retry Semantics
### 4.1 Same operation_id retry
If a future implementation receives the same valid operation_id again, the system may consult append-only audit records to determine whether the prior attempt:
1. succeeded with a committed write
2. was denied before write
3. failed after parse but before commit
4. failed after commit but before downstream acknowledgment

### 4.2 Duplicate operation_id handling
Duplicate operation_id behavior must be deterministic and explicitly classified.
Recommended future classification:
1. Same operation_id, same already-committed write: return idempotent replay-style response without rewriting data.
2. Same operation_id, prior deny: return stable deny result or explicit retry-not-eligible result depending on future policy.
3. Same operation_id, conflicting request shape or token context: return conflict/error response without mutating data.

### 4.3 Already-applied operation_id handling
If a future append-only ledger shows operation_id already reached committed write state, future retries must not silently reapply mutation.
The response may surface the prior terminal state, prior internal mutation UUID, and stable reason metadata.

### 4.4 Denied operation_id handling
If a prior attempt with the same operation_id was denied, future behavior must not bypass current authorization or guard checks.
Any future shortcut behavior must still preserve the same deny semantics and audit trail.

### 4.5 Malformed operation_id handling
Malformed operation_id handling remains schema-level behavior.
If the payload is malformed such that operation_id is unparsed or invalid, future persistence logic must not run.

## 5) Idempotency Boundary
1. operation_id must not become token identity.
2. operation_id must not replace the internal mutation UUID.
3. operation_id must not bypass authorization checks.
4. operation_id must not bypass guard checks.
5. operation_id must not independently authorize mutation or token consume.
6. Internal mutation UUID remains the write/consume correlation identifier for mutation internals.

## 6) Error and Deny Behavior
### 6.1 Parsed operation_id behavior
When operation_id is parsed and accepted by schema, future error/deny responses should continue to surface it additively in the response envelope.

### 6.2 Unparsed or malformed payload behavior
If the payload is non-JSON, non-object, or otherwise unparsed before schema can normalize operation_id, the response should remain unchanged and operation_id should be absent or null.

If the payload reaches schema and operation_id is malformed, the existing schema invalid response should continue to surface normalized-or-null operation_id exactly as defined by the locked schema behavior.

### 6.3 Persistence boundary for deny/error events
A future implementation may choose to record deny/error events in append-only audit form, but only if:
1. ordering is deterministic
2. no prior records are mutated in place
3. a deny record cannot be mistaken for a successful apply

## 7) Audit and Observability Requirements
1. Persistence must be append-only.
2. Field ordering in serialized audit output must remain stable where practical.
3. No silent overwrite of prior operation_id records is allowed.
4. Ledger/audit writes must be deterministic for the same terminal event shape.
5. Success, deny, and conflict outcomes must be distinguishable by explicit state fields.
6. operation_id and internal mutation UUID must remain separately observable.
7. Observability must support reconstruction of:
   1. request identity
   2. authorization/guard outcome
   3. mutation terminal state
   4. consume terminal state without redefining consume semantics

## 8) Security and Governance Guardrails
1. No replay bypass via operation_id.
2. No consume-state drift caused by operation_id reuse.
3. No digest drift caused by operation_id adoption.
4. No mutation semantic drift.
5. No downgrade of existing guard-first validation.
6. No collapsing request identity and mutation identity into the same field.
7. No persistence model that allows destructive in-place rewriting of prior audit history.

## 9) Future Implementation Test Plan
Any future retry/persistence implementation slice must include tests proving:
1. Retry with same operation_id after success is deterministic and non-rewriting.
2. Duplicate operation_id after success does not trigger duplicate mutation.
3. Duplicate operation_id after deny remains deterministic and policy-consistent.
4. Requests without operation_id remain backward compatible.
5. Token digest behavior remains unchanged.
6. Token consume behavior remains unchanged.
7. Internal mutation UUID remains separate from surfaced request operation_id.
8. Ledger or audit persistence is deterministic and append-only.
9. Conflicting duplicate operation_id inputs produce explicit non-silent conflict handling.
10. Malformed operation_id never reaches persistence path.

## 10) Explicit Non-Goals
1. No code changes.
2. No retry implementation.
3. No persistence implementation.
4. No endpoint behavior changes.
5. No token digest semantic changes.
6. No token consume semantic changes.
7. No mutation behavior changes.
8. No UI, dashboard, scoring, batch, ledger runtime, prediction, intake, or report changes.
9. No runtime file creation.
10. No test execution in this slice.

## 11) Final Design Verdict
The retry/persistence design is approved only as a future design boundary.

Implementation remains blocked until a separate implementation slice is explicitly opened, narrowly scoped, and test-gated.

## 12) Recommended Next Safe Slice
Recommended next slice:
- official-source-approved-apply-operation-id-retry-persistence-design-review-v1

That review slice should remain docs-only and should verify that any future implementation stays additive, deterministic, append-only where applicable, and does not alter locked token, consume, authorization, or mutation semantics.
