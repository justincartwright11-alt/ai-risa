# official-source-approved-apply-operation-id-retry-design-v1

## 1. Purpose

Define a docs-only design for externally supplied `operation_id` so approved-apply supports true cross-request idempotent retry semantics without introducing duplicate writes.

This design focuses on retry identity and conflict determinism across repeated requests that represent the same operator-intended action.

## 2. Non-goals

- No code changes.
- No endpoint implementation changes in this slice.
- No mutation adapter changes.
- No token consume helper changes.
- No schema runtime implementation in this slice.
- No UI/runtime wiring changes.
- No batch behavior.
- No scoring semantics changes.
- No mutation of any actual-results files.

## 3. Current limitation

Current endpoint behavior generates `operation_id` server-side per request lifecycle. That blocks external callers from supplying a stable operation identity across retried requests.

Resulting limitation:

- Cross-request idempotent retry is not externally expressible yet.
- Retry after write-success + consume-failure can be correlated internally, but not reliably re-issued by clients using the same externally controlled operation identity.

## 4. Proposed request schema addition

Future request schema (after implementation authorization) adds one field:

```json
{
  "operation_id": "string"
}
```

Placement:

- top-level request field in approved-apply request body

Behavioral contract:

- required for write-capable approved-apply requests once feature is enabled
- optional/ignored only before rollout gate is enabled
- not valid for batch paths (batch remains out of scope)

## 5. operation_id format rules

`operation_id` must be a non-empty string that satisfies strict format rules:

- length: 16..128 characters
- allowed characters: `A-Z`, `a-z`, `0-9`, `_`, `-`, `.`
- must not contain spaces
- must not contain path separators (`/`, `\\`)
- must not be purely punctuation

Validation failures:

- empty/missing: `operation_id_required`
- invalid type: `malformed_field_type`
- invalid format: `operation_id_format_invalid`

## 6. operation_id binding rules

`operation_id` must bind to the following immutable binding tuple:

- `selected_key`
- `token_id`
- `citation_fingerprint`
- `source_url`
- `source_date`
- `extracted_winner`

Binding source of truth:

- guard-validated request fields plus authoritative preview revalidation

Binding invariants:

- same `operation_id` is valid only when full tuple is identical
- any mismatch in bound fields is deterministic conflict

## 7. Idempotency identity

Idempotency identity key:

- primary: `operation_id`
- secondary verification: full binding tuple listed above

Idempotent success condition:

- same `operation_id` + same binding tuple + already committed write and/or consumed token state

Idempotent response contract:

- return stable success envelope
- mark idempotent replay explicitly (`token_consume_idempotent=true` and/or `operation_id_idempotent=true` in a future additive field)
- no second write mutation attempt

## 8. Retry behavior by prior outcome

### Retry after token consume success

- return idempotent success
- no adapter write
- no additional token consume mutation beyond idempotent acknowledgement
- reason code: `operation_id_idempotent_replay`

### Retry after token consume failure after write success

- consume-only retry path
- must not invoke adapter write again
- if consume now succeeds, return success with idempotent consume linkage
- if consume still fails, return deterministic consume failure code

### Retry after adapter write failure

- write may be re-attempted only if previous outcome confirmed `write_performed=false` and no terminal rollback failure
- operation_id identity remains same
- response must preserve deterministic reason classification

### Retry after rollback success

- prior attempt ended with `write_performed=false` after rollback
- retriable with same `operation_id` and same binding tuple
- adapter may attempt write again

### Retry after rollback_failed_terminal

- fail closed
- no automatic retry write
- require operator escalation action
- deterministic reason code: `rollback_failed_terminal`

## 9. Conflict behavior

All conflicts below return deterministic conflict with no write:

### same operation_id, different token_id

- reason code: `operation_id_binding_conflict_token_id`

### same operation_id, different selected_key

- reason code: `operation_id_binding_conflict_selected_key`

### same operation_id, different citation_fingerprint

- reason code: `operation_id_binding_conflict_citation_fingerprint`

### same operation_id, different source_url/source_date/extracted_winner

- reason codes:
  - `operation_id_binding_conflict_source_url`
  - `operation_id_binding_conflict_source_date`
  - `operation_id_binding_conflict_extracted_winner`

General conflict envelope policy:

- `mutation_performed=false`
- `write_performed=false`
- `token_consume_performed=false`
- include prior binding summary in audit-safe redacted form when available

## 10. Response fields

Future additive response fields for operation-id retry semantics:

- `operation_id`
- `operation_id_supplied`
- `operation_id_valid`
- `operation_id_binding_valid`
- `operation_id_conflict`
- `operation_id_conflict_field`
- `operation_id_first_seen_at_utc`
- `operation_id_last_seen_at_utc`
- `operation_id_idempotent_replay`
- `operation_id_retry_mode` (`none|consume_only|write_retry_disallowed|write_retry_allowed`)

Existing write/consume/rollback fields remain unchanged and additive.

## 11. Audit fields

Future additive audit fields:

- `operation_id`
- `operation_id_binding_digest`
- `operation_id_binding_selected_key`
- `operation_id_binding_token_id`
- `operation_id_binding_citation_fingerprint`
- `operation_id_binding_source_url`
- `operation_id_binding_source_date`
- `operation_id_binding_extracted_winner`
- `operation_id_conflict`
- `operation_id_conflict_field`
- `operation_id_idempotent_replay`
- `operation_id_retry_attempt_count`

Audit policy:

- preserve deterministic traceability without widening batch/UI scope
- never alter scoring semantics

## 12. Test requirements

Before implementation is accepted, tests must prove:

1. missing/invalid `operation_id` fails deterministically
2. valid `operation_id` accepted only with strict format rules
3. same `operation_id` + same binding returns idempotent success without rewrite
4. same `operation_id` + different `token_id` returns deterministic conflict
5. same `operation_id` + different `selected_key` returns deterministic conflict
6. same `operation_id` + different `citation_fingerprint` returns deterministic conflict
7. same `operation_id` + different source tuple (`source_url`, `source_date`, `extracted_winner`) returns deterministic conflict
8. retry after write success + consume failure is consume-only (no rewrite)
9. retry after rollback_failed_terminal fails closed and requires escalation
10. no batch/UI/scoring side effects are introduced

## 13. Future implementation micro-slices

1. `official-source-approved-apply-operation-id-retry-design-v1`
- this docs-only design slice

2. `official-source-approved-apply-operation-id-retry-design-review-v1`
- docs-only review and closure of conflict/retry semantics

3. `official-source-approved-apply-operation-id-schema-implementation-v1`
- schema validation for externally supplied operation_id format and requiredness gates

4. `official-source-approved-apply-operation-id-endpoint-binding-implementation-v1`
- endpoint binding checks and deterministic conflict mapping

5. `official-source-approved-apply-operation-id-consume-retry-implementation-v1`
- consume-only retry path with no rewrite guarantee after write success

6. `official-source-approved-apply-operation-id-hardening-v1`
- status mapping, audit completion, and release-readiness hardening

---

## Mandatory policy confirmation

- operation_id must be client/operator supplied only after the design is implemented.
- operation_id must be non-empty string with strict length/character rules.
- operation_id must bind to selected_key + token_id + citation_fingerprint + source_url + source_date + extracted_winner.
- Same operation_id + same binding may return idempotent success without re-writing.
- Same operation_id + different binding must return deterministic conflict.
- Retry after write success + consume failure must be consume-only, no rewrite.
- Retry after rollback_failed_terminal must fail closed and require operator escalation.
- No batch behavior.
- No UI changes.
- No scoring changes.