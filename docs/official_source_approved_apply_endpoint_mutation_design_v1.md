# official-source-approved-apply-endpoint-mutation-design-v1

## 1. Purpose

Define a docs-only design for a future endpoint slice that connects the already locked
`official_source_approved_apply_mutation_adapter` to the existing approved-apply endpoint.

This design exists after three facts are already proven and locked:

- the request contract and non-mutating guard path are locked
- the guard response can surface `token_id`
- the mutation adapter can perform adapter-local atomic write, exact-byte rollback, and
  rollback-failed-terminal escalation without endpoint wiring

This slice is design only. It introduces no endpoint code, no adapter changes, no token consume
persistence, and no runtime behavior change.

---

## 2. Non-goals

- No implementation changes to `operator_dashboard/app.py`.
- No implementation changes to `operator_dashboard/official_source_approved_apply_mutation_adapter.py`.
- No token consume persistence implementation.
- No endpoint runtime wiring.
- No UI changes.
- No batch behavior.
- No scoring changes.
- No mutation of `ops/accuracy/actual_results*.json` in this slice.
- No new persistence backend.
- No page-load, background-job, or auto-apply behavior.

---

## 3. Current locked starting point

Current locked endpoint behavior:

- Route already exists: `POST /api/operator/actual-result-lookup/official-source-approved-apply`
- Endpoint is decision-only and non-mutating.
- Response envelope already normalizes:
  - `request_valid`
  - `token_valid`
  - `guard_allowed`
  - `manual_review_required`
  - `approval_binding_valid`
  - `token_status`
  - `reason_code`
  - `acceptance_gate`
  - `binding_digest_expected`
  - `binding_digest_actual`
- Endpoint currently synthesizes `authoritative_preview_result` from `preview_snapshot` and returns
  a non-mutating skeleton message.

Current locked adapter behavior:

- Adapter is standalone and not wired into runtime.
- Adapter requires `guard_result.token_id` and `guard_allowed=true` preconditions.
- Adapter writes only to `ops/accuracy/actual_results_manual.json`.
- Adapter owns:
  - same-filesystem temp-file write
  - `os.replace` atomic swap
  - exact-byte rollback
  - `rollback_failed_terminal` escalation
  - file-scoped lock behavior
- Adapter does not mutate token-consume state.

---

## 4. Endpoint mutation boundary

Future endpoint mutation begins only after all of the following are true in the same request:

1. request body is valid JSON object
2. schema validation returns `request_valid=true`
3. guard returns `guard_allowed=true`
4. guard returns `token_valid=true`
5. guard returns `approval_binding_valid=true`
6. guard returns `manual_review_required=false`
7. guard returns `reason_code="accepted_preview_write_eligible"`
8. guard returns `token_id` present and non-empty
9. `acceptance_gate.state == "write_eligible"`
10. `acceptance_gate.write_eligible == true`

If any one of these fails, the endpoint must remain non-mutating and must not call the adapter.

---

## 5. Future endpoint call sequence

The future wired endpoint sequence is:

1. Parse request JSON.
2. Run `validate_official_source_approved_apply_request(data)`.
3. Build authoritative preview result from trusted server-side state.
4. Run `evaluate_official_source_approved_apply_guard(...)`.
5. If guard denies, return deny/manual-review envelope unchanged.
6. If guard allows, prepare endpoint-scoped mutation call context:
   - `accuracy_dir`
   - `operation_id`
   - `write_attempt_id`
   - `contract_version`
   - `endpoint_version`
   - `consumed_token_ids` read-only view
7. Call `apply_official_source_approved_apply_mutation(...)`.
8. If adapter write succeeds, endpoint may proceed to post-write token-consume handling in a later
   approved slice.
9. If adapter write fails, endpoint returns adapter envelope merged into normalized response.

This design does not authorize step 8 implementation. It only defines the future boundary.

---

## 6. Endpoint-to-adapter input contract

Future endpoint wiring must call:

```python
apply_official_source_approved_apply_mutation(
    guard_result=guard_result,
    preview_snapshot=authoritative_preview_result,
    accuracy_dir=accuracy_dir,
    consumed_token_ids=consumed_token_ids,
    lock_timeout_seconds=10,
    operation_id=operation_id,
    write_attempt_id=write_attempt_id,
    contract_version="official_source_approved_apply_contract_v1",
    endpoint_version="official_source_approved_apply_endpoint_mutation_v1",
)
```

Input rules:

- `preview_snapshot` must be the authoritative server-side preview result, not the raw client body.
- `guard_result` must be the exact guard output returned by the locked guard helper.
- `consumed_token_ids` is passed for interface stability only; the adapter must not mutate it.
- `operation_id` is stable per request lifecycle.
- `write_attempt_id` is unique per mutation attempt.

---

## 7. Authoritative preview rule

The endpoint must not pass the client-submitted `preview_snapshot` directly into the adapter.

Required policy:

- The endpoint must continue reconstituting or revalidating an authoritative preview result first.
- The guard must compare request payload against that authoritative preview.
- The adapter must receive the authoritative preview result, not the raw user payload copy.

Reason:

- this preserves the already locked binding-verification model
- this avoids client-controlled mutation input after guard approval
- this keeps `source_citation` and `acceptance_gate` values authoritative at write time

---

## 8. Response normalization plan

The existing endpoint `_normalized_response(...)` helper will need additive fields in a future
implementation slice.

Required additive fields:

- `token_id`
- `fight_id`
- `proposed_write`
- `write_target`
- `before_row_count`
- `after_row_count`
- `pre_write_file_sha256`
- `post_write_file_sha256`
- `rollback_attempted`
- `rollback_succeeded`
- `post_rollback_file_sha256`
- `rollback_reason_code`
- `rollback_error_detail`
- `rollback_started_at_utc`
- `rollback_finished_at_utc`
- `rollback_terminal_state`
- `escalation_required`
- `operator_escalation_action`
- `approval_token_id`
- `token_consume_performed`
- `operation_id`
- `write_attempt_id`
- `contract_version`
- `endpoint_version`

Existing fields that must remain:

- `mode`
- `phase`
- `request_valid`
- `token_valid`
- `guard_allowed`
- `manual_review_required`
- `approval_required`
- `approval_granted`
- `approval_binding_valid`
- `token_status`
- `approval_token_status`
- `mutation_performed`
- `write_performed`
- `bulk_lookup_performed`
- `scoring_semantics_changed`
- `external_lookup_performed`
- `reason_code`
- `errors`
- `selected_key`
- `acceptance_gate`
- `binding_digest_expected`
- `binding_digest_actual`

No existing field should be removed when endpoint mutation wiring is eventually implemented.

---

## 9. HTTP outcome model

This design defines envelope semantics first and leaves final status-code mapping to a later,
smaller hardening slice. Still, the expected response classes are:

### Class A — schema / malformed request

- adapter not called
- `guard_allowed=false`
- `write_performed=false`
- `mutation_performed=false`

### Class B — token / binding / preview mismatch denial

- adapter not called
- `guard_allowed=false`
- `write_performed=false`
- `mutation_performed=false`

### Class C — manual-review / rejected gate state

- adapter not called
- `guard_allowed=false`
- `write_performed=false`
- `mutation_performed=false`

### Class D — adapter success

- adapter called once
- `guard_allowed=true`
- `write_performed=true`
- `mutation_performed=true`
- `token_consume_performed=false` at endpoint-mutation slice unless token-consume work is separately approved

### Class E — adapter fail-closed

- adapter called once
- `guard_allowed=true`
- `write_performed=false`
- `mutation_performed=false`
- exact failure reason comes from adapter

### Class F — rollback failed terminal

- adapter called once
- `rollback_terminal_state="rollback_failed_terminal"`
- `escalation_required=true`
- `operator_escalation_action="manual_file_recovery_required"`

---

## 10. Token consume boundary at endpoint layer

The adapter slice already locked the rule that token consume does not happen inside the adapter.
The future endpoint slice must preserve that separation.

Required future ordering:

1. Guard validates token using current consumed-token state.
2. Endpoint calls adapter only after guard allow.
3. Adapter returns write result.
4. Only if adapter returns `write_performed=true` may endpoint enter token-consume stage.

This design explicitly defers all implementation of step 4.

Therefore, the future endpoint-mutation implementation slice must still return:

- `token_consume_performed=false`

unless a separate, later token-consume slice is also approved and wired.

---

## 11. No direct use of legacy upsert helper

The future endpoint must not call `_upsert_single_manual_actual_result` directly.

Required policy:

- endpoint mutation path calls adapter only
- adapter owns all file mutation mechanics
- legacy helper remains unrelated to this endpoint path

Reason:

- preserves the locked atomic-write and rollback proof
- prevents accidental bypass of same-filesystem temp-file and exact-byte rollback rules

---

## 12. Audit and correlation fields

The future endpoint layer must generate and preserve:

- `operation_id`
- `write_attempt_id`
- `contract_version`
- `endpoint_version`

Generation policy:

- `operation_id` generated once per request
- `write_attempt_id` generated once per adapter call
- both fields returned to client and passed into adapter

These fields must remain stable across:

- guard evaluation
- adapter call
- adapter rollback path
- future token-consume retry linkage

---

## 13. Failure-handling boundary

Future endpoint code must not reinterpret adapter failure into a different semantic class.

Required rule:

- adapter reason codes pass through unchanged for mutation-phase failures

This includes:

- `critical_field_missing`
- `pre_write_read_error`
- `pre_write_parse_error`
- `candidate_serialization_error`
- `cross_filesystem_write_error`
- `temp_write_error`
- `atomic_replace_error`
- `post_write_hash_mismatch`
- `mutation_lock_acquire_failed`
- `contention_timeout`
- `rollback_failed_terminal`

The endpoint may map these to HTTP statuses later, but must not rename them.

---

## 14. Runtime invariants for the future endpoint slice

When adapter is not called:

- `write_performed=false`
- `mutation_performed=false`
- `token_consume_performed=false`

When adapter is called and succeeds:

- `write_performed=true`
- `mutation_performed=true`
- `bulk_lookup_performed=false`
- `scoring_semantics_changed=false`
- `external_lookup_performed=false`

When adapter is called and fails:

- `write_performed=false`
- `mutation_performed=false`
- `bulk_lookup_performed=false`
- `scoring_semantics_changed=false`

At no point may this endpoint:

- enter batch behavior
- mutate `actual_results.json`
- mutate `actual_results_unresolved.json`
- change scoring semantics
- trigger UI-side auto-apply behavior

---

## 15. Test plan for the future endpoint implementation slice

Before runtime wiring is considered complete, tests must prove:

1. Endpoint still rejects invalid non-JSON and non-object JSON bodies.
2. Endpoint still rejects schema-invalid requests without calling adapter.
3. Endpoint still rejects token-invalid and binding-invalid requests without calling adapter.
4. Endpoint still rejects preview mismatch requests without calling adapter.
5. Endpoint still rejects manual-review and rejected gate states without calling adapter.
6. Endpoint calls adapter exactly once on `guard_allowed=true` path.
7. Endpoint passes authoritative preview result, not raw request snapshot, into adapter.
8. Endpoint returns adapter success fields when adapter succeeds.
9. Endpoint returns adapter failure fields unchanged when adapter fails.
10. Endpoint surfaces `rollback_failed_terminal` escalation metadata unchanged.
11. Endpoint does not mutate token-consume state in the endpoint-mutation slice.
12. Endpoint does not call `_upsert_single_manual_actual_result` in the approved-apply path.
13. Endpoint continues to keep `bulk_lookup_performed=false` and `scoring_semantics_changed=false`.
14. Endpoint does not touch `actual_results.json` or `actual_results_unresolved.json`.
15. Endpoint does not enable batch semantics.

---

## 16. Future micro-slices after this design

1. `official-source-approved-apply-endpoint-mutation-review-v1`
- docs-only review of this design

2. `official-source-approved-apply-endpoint-mutation-implementation-v1`
- wire adapter into endpoint
- no token consume persistence

3. `official-source-approved-apply-endpoint-mutation-hardening-v1`
- lock status mapping and final response shape

4. `official-source-approved-apply-token-consume-design-v1`
- docs-only token-consume persistence design

5. `official-source-approved-apply-token-consume-implementation-v1`
- add idempotent consume registration after confirmed write success

---

## 17. Slice status

Design status: ready for review.

Implementation status: intentionally not started.

No runtime mutation behavior is authorized by this design note.