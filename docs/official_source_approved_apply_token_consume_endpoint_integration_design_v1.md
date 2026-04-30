# official-source-approved-apply-token-consume-endpoint-integration-design-v1

## 1. Purpose

Define a docs-only design for integrating token consume behavior into the existing approved-apply endpoint flow after adapter-confirmed write success.

This slice does not change runtime behavior and does not authorize endpoint wiring or write-path implementation.

## 2. Non-goals

- No endpoint code changes.
- No source-code changes of any kind.
- No mutation adapter wiring changes.
- No token consume endpoint wiring implementation.
- No write/apply implementation changes.
- No mutation of `ops/accuracy/actual_results.json`.
- No mutation of `ops/accuracy/actual_results_manual.json`.
- No mutation of `ops/accuracy/actual_results_unresolved.json`.
- No UI/runtime/template changes.
- No batch behavior.
- No page-load apply behavior.
- No scoring semantics changes.

## 3. Current locked helper state

Locked checkpoint:

- `official-source-approved-apply-token-consume-helper-v1`
- commit `c69ff0f`
- post-freeze smoke passed

Current helper contract (already implemented and tested in isolation):

- `lookup(token_id)`
- `register_consume(...)`
- `lookup_by_operation(operation_id)`

Current deterministic helper outcomes:

- first consume success
- idempotent same-operation retry success
- conflict on mismatched operation/token linkage
- malformed field deny
- absent record state
- store unavailable state

## 4. Endpoint integration point

Target endpoint context is:

- `POST /api/operator/actual-result-lookup/official-source-approved-apply`

Integration point is post-guard and post-adapter in the future endpoint flow:

1. schema + guard validation
2. authoritative preview revalidation
3. adapter mutation attempt
4. if and only if adapter confirms successful write, invoke token consume registration

No endpoint wiring is performed in this slice.

## 5. Token consume call timing

Hard timing policy:

- Token consume must happen only after confirmed successful adapter write.
- Token consume must never occur before file mutation success.
- Any path with `write_performed=false` must not attempt token consume.

Minimum consume call preconditions for future implementation:

- `guard_allowed=true`
- `token_valid=true`
- `approval_binding_valid=true`
- adapter result `write_performed=true`
- `token_id` present
- `operation_id` present
- `write_attempt_id` present

## 6. Token consume success behavior

On successful post-write consume registration:

- keep `write_performed=true`
- return `token_consume_performed=true`
- return `token_consume_reason_code=consumed`
- include consume audit linkage fields (`token_id`, `operation_id`, `write_attempt_id`)
- do not alter scoring semantics
- do not trigger any batch behavior

## 7. Token consume failure behavior

If consume registration fails after a confirmed write:

- `write_performed` remains `true`
- `token_consume_performed=false`
- map deterministic reason code from consume stage
- include actionable error details for recovery
- do not retry write in-line as part of consume failure handling

Representative consume failure reason codes:

- `token_consume_post_write_failed`
- `token_consume_store_unavailable`
- `token_consume_conflict`
- `malformed_field_type`

## 8. Write-success / consume-failure recovery

Recovery policy for `write_performed=true` and `token_consume_performed=false`:

- write remains committed
- recovery path performs consume reconciliation only
- recovery must use `operation_id + token_id` correlation
- recovery must never perform a second record write
- recovery must not mutate other actual-results files

Terminal-recovery objective:

- eventual consumed state for the same write event, or deterministic terminal escalation with explicit reason code

## 9. Idempotent retry behavior

Retry model for consume reconciliation:

- retrying consume for the same `token_id` and same `operation_id` is idempotent success
- retrying consume for same `token_id` but different `operation_id` is deterministic conflict
- retrying consume for same `operation_id` but different `token_id` is deterministic conflict

Critical no-rewrite guarantee:

- retry must consume the same token idempotently without re-writing

## 10. operation_id and write_attempt_id binding

Binding requirements:

- `operation_id` identifies the request lifecycle and consume reconciliation identity
- `write_attempt_id` identifies the specific write attempt audit event
- consume registration must persist both values
- response/audit envelope must return both values for traceability

Integrity requirement:

- any mismatch in persisted consume linkage must produce deterministic conflict/failure classification

## 11. token_id audit binding

Token binding requirements:

- endpoint must use guard-surfaced `token_id`
- consume registration must persist the exact token id used for approval
- audit response must include `token_id` and consume result
- post-write consume reconciliation must be keyed by same `token_id` + `operation_id`

## 12. No-consume-before-write rule

Hard policy:

- no consume attempt is allowed before adapter-confirmed write success

Enforcement expectations for future implementation:

- deny/manual-review/precondition fail paths never call consume helper
- adapter fail-closed paths with `write_performed=false` never call consume helper

## 13. No-rewrite-on-consume-retry rule

Hard policy:

- consume retry flow must never trigger another adapter write

Enforcement expectations for future implementation:

- consume retry route/function (if added later) must be consume-only
- existing write result is treated as immutable for retry handling

## 14. Failure reason codes

Consume-stage reason code set for endpoint integration design:

- success: `consumed`
- post-write generic failure: `token_consume_post_write_failed`
- store unavailable: `token_consume_store_unavailable`
- idempotent conflict: `token_consume_conflict`
- malformed consume payload field: `malformed_field_type`

Existing guard-time token reason codes remain unchanged and outside consume-stage reclassification.

## 15. Audit response fields

Future endpoint response/audit envelope should include consume-stage fields:

- `token_id`
- `token_consume_performed`
- `token_consume_reason_code`
- `token_consume_attempted_at_utc`
- `token_consume_completed_at_utc`
- `token_consume_retry_count`
- `operation_id`
- `write_attempt_id`
- `contract_version`
- `endpoint_version`
- `binding_digest_expected`
- `selected_key`

Write-stage fields remain additive and unchanged by this docs-only slice.

## 16. Test requirements before implementation

Before any endpoint consume integration implementation is accepted, tests must prove:

1. consume is not attempted when `write_performed=false`
2. consume is attempted exactly once after `write_performed=true`
3. consume success sets `token_consume_performed=true` with `consumed`
4. consume failure preserves `write_performed=true`
5. consume failure returns deterministic reason code and audit linkage fields
6. idempotent retry with same `token_id` + `operation_id` succeeds without rewrite
7. conflict retry with mismatched token/operation returns deterministic conflict
8. no path re-writes file during consume retry or consume recovery
9. no mutation of `actual_results.json` or `actual_results_unresolved.json` from consume flow
10. no batch/UI/scoring side effects are introduced

## 17. Future micro-slices

1. `official-source-approved-apply-token-consume-endpoint-integration-design-v1`
- this docs-only slice

2. `official-source-approved-apply-token-consume-endpoint-integration-review-v1`
- docs review and amendment gate for endpoint consume sequencing

3. `official-source-approved-apply-token-consume-endpoint-integration-implementation-v1`
- endpoint consume wiring after adapter success only, no new write semantics

4. `official-source-approved-apply-token-consume-recovery-hardening-v1`
- explicit recovery/retry endpoint mechanics and status mapping hardening

---

## Mandatory policy confirmation

- Token consume must happen only after confirmed successful adapter write.
- Token consume must never occur before file mutation success.
- If write succeeds and token consume fails, the write remains committed.
- Retry must consume the same token idempotently without re-writing.
- No endpoint mutation wiring in this slice.
- No actual_results_manual.json mutation in this slice.
- No batch behavior.
- No UI.
- No scoring change.