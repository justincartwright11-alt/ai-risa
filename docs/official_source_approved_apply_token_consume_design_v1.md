# official-source-approved-apply-token-consume-design-v1

## 1. Purpose

Define a docs-only token-consume persistence design for approved-apply mutation flow.

This slice exists to close the sequencing requirement that no routable write-capable endpoint
implementation is allowed until token-consume design is locked.

This design introduces no runtime behavior changes and no persistence implementation.

---

## 2. Non-goals

- No implementation changes.
- No endpoint code changes.
- No mutation adapter code changes.
- No token consume persistence implementation in this slice.
- No UI/runtime wiring changes.
- No batch behavior.
- No scoring changes.
- No write/apply behavior changes.

---

## 3. Current locked starting point

Current locked boundaries:

- Endpoint mutation design is final-reviewed and pass-locked (docs-only).
- Adapter is already write-capable and does not mutate token-consume state.
- Guard surfaces `token_id` from token validation.
- Endpoint mutation implementation is not yet started.

Known current ordering contract:

1. guard validates token and produces `token_id`
2. adapter may write if guard-allow preconditions pass
3. token consume is endpoint responsibility after confirmed write success

What remains undefined before this slice:

- persistent consumed-token store contract
- idempotent consume registration protocol
- consume failure classification and recovery model

---

## 4. Sequencing gate (hard policy)

Routable write-capable endpoint implementation is forbidden until this token-consume design is
locked.

Allowed before token-consume implementation is complete:

- dark/non-routable internal-test endpoint integration only

Disallowed before token-consume implementation is complete:

- publicly routable endpoint that can perform write-capable approved apply

---

## 5. Token consume scope and invariants

Token consume applies only to approval token replay protection for approved-apply writes.

Consume invariants:

- Consume occurs only after confirmed successful write commit.
- Consume never occurs on deny/manual-review paths.
- Consume never occurs on pre-write failure.
- Consume never occurs on rollback-success failure paths where final `write_performed=false`.
- Consume is idempotent for the same `token_id` and `operation_id`.
- Consume is auditable via correlation fields.

Required envelope invariants:

- `token_consume_performed=true` only when consume registration succeeded.
- `token_consume_performed=false` for all other outcomes.
- `write_performed=true` may coexist with `token_consume_performed=false` only in
  `token_consume_post_write_failed` outcome.

---

## 6. Persistence model (design contract)

The consumed-token store must support these operations:

1. `lookup(token_id) -> state`
2. `register_consume(token_id, metadata) -> result`
3. `lookup_by_operation(operation_id) -> consume_status`

Required store fields per consumed token:

- `token_id`
- `consumed_at_utc`
- `operation_id`
- `write_attempt_id`
- `selected_key`
- `reason_code_at_consume` (expected: `official_source_write_applied`)
- `binding_digest_expected`
- `contract_version`
- `endpoint_version`

State model:

- `not_consumed`
- `consumed`
- `consume_register_failed` (transient operational state, not token validity state)

Store guarantees:

- uniqueness on `token_id`
- deterministic idempotent behavior on repeated register attempts for same token_id
- read-after-write consistency for consume registration responses

---

## 7. Endpoint consume protocol (future implementation contract)

Future endpoint protocol after adapter call:

1. If adapter result has `write_performed=false`, skip consume.
2. If adapter result has `write_performed=true`, attempt consume registration with:
   - `token_id`
   - `operation_id`
   - `write_attempt_id`
   - selected audit fields
3. If consume registration succeeds:
   - return `token_consume_performed=true`
4. If consume registration fails:
   - return `reason_code=token_consume_post_write_failed`
   - return `write_performed=true`
   - return `token_consume_performed=false`
   - do not re-run write

This preserves write-first semantics while making consume failure explicit and recoverable.

---

## 8. Idempotency and replay model

### Replay validation

Guard/token validation should reject replay/consumed token states before write path entry.

### Idempotent consume registration

If consume is retried for same `token_id`:

- if prior consume is already registered with matching `operation_id`, return success idempotently
- if prior consume exists with different operation_id, return deterministic conflict

Suggested deterministic consume conflict classification:

- `approval_token_consumed` for guard-time validation
- `token_consume_conflict` for post-write consume-registration conflict path

---

## 9. Failure classifications

Token consume design must include deterministic reason codes for post-write stage:

- `token_consume_post_write_failed`
- `token_consume_conflict`
- `token_consume_store_unavailable`

Existing guard-time token reason codes remain unchanged:

- `approval_replayed`
- `approval_token_consumed`
- `approval_expired`
- `approval_binding_mismatch`

Failure handling contract:

- Consume failures after successful write must never trigger write retry.
- Consume failures must be recoverable via idempotent consume retry by `operation_id` + `token_id`.

---

## 10. Recovery model

Recovery objective:

- resolve `write_performed=true` and `token_consume_performed=false` into eventual consumed state
  without changing write outcome.

Required recovery inputs:

- `operation_id`
- `write_attempt_id`
- `token_id`
- `write_target`
- `post_write_file_sha256`

Recovery requirements:

- no second write attempt
- no mutation of non-target files
- no batch behavior
- deterministic completion or deterministic terminal escalation reason

---

## 11. Audit fields for token consume stage

Future endpoint response/audit should include consume-stage fields:

- `token_id`
- `token_consume_performed`
- `token_consume_reason_code`
- `token_consume_attempted_at_utc`
- `token_consume_completed_at_utc`
- `token_consume_retry_count`
- `operation_id`
- `write_attempt_id`

Carry-forward linkage fields:

- `contract_version`
- `endpoint_version`
- `binding_digest_expected`
- `selected_key`

---

## 12. Security and boundary constraints

Token consume stage must preserve existing boundaries:

- one-record only
- no batch consume flow
- no page-load behavior
- no UI auto-apply behavior
- no scoring changes
- no alternate write targets

Token consume must not expand accepted request surface.

---

## 13. Required tests (future implementation slice)

Before token-consume implementation is considered complete, tests must prove:

1. Consume is not attempted when `write_performed=false`.
2. Consume is attempted once when `write_performed=true`.
3. Successful consume sets `token_consume_performed=true`.
4. Consume store unavailable yields `token_consume_post_write_failed` with `write_performed=true`.
5. Consume retry with same `operation_id` is idempotent success.
6. Consume retry with different `operation_id` yields deterministic conflict.
7. No path retries or replays write during consume recovery.
8. Guard continues rejecting consumed token at pre-write stage.
9. Recovery path uses `operation_id` + `token_id` linkage and preserves audit integrity.
10. No batch/UI/scoring side effects are introduced.

---

## 14. Interaction with endpoint-mutation implementation slice

This design authorizes planning of endpoint-mutation implementation with the following gating:

- routable write-capable mode must remain blocked until token-consume implementation is also
  approved and locked
- dark/non-routable internal-test mode may be used to validate endpoint-to-adapter integration
  before consume implementation

Once token-consume implementation locks, routable activation can be evaluated in a later hardening
or release-readiness slice.

---

## 15. Future micro-slices

1. `official-source-approved-apply-token-consume-design-v1`
- this slice (docs-only)

2. `official-source-approved-apply-endpoint-mutation-implementation-v1`
- endpoint-to-adapter wiring (dark/non-routable allowed before consume implementation lock)

3. `official-source-approved-apply-token-consume-implementation-v1`
- persistent consume registration + idempotent retry path

4. `official-source-approved-apply-endpoint-mutation-hardening-v1`
- status mapping and final envelope hardening with consume fields

---

## 16. Slice status

Design status: ready for review.

Implementation status: intentionally not started.

No runtime behavior is changed by this design note.