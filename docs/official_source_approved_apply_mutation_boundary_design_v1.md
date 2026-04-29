# official-source-approved-apply-mutation-boundary-design-v1

## 1. Purpose
Define a docs-only mutation boundary for a future one-record approved-apply write path after the proven non-mutating guard decision flow.

This slice does not implement any runtime behavior.

## 2. Non-goals
- No endpoint implementation changes.
- No backend source code changes.
- No UI/runtime wiring.
- No token consume persistence implementation.
- No write/apply implementation.
- No actual-results file mutation.
- No batch behavior.
- No page-load apply behavior.
- No auto-apply behavior.
- No scoring formula or scoring semantics changes.
- No external lookup execution.

## 3. Current proven non-mutating state
Current locked state (contract-hardening + valid-contract smoke):
- The approved-apply endpoint accepts valid one-record contract payloads.
- Guard can return guard_allowed=true with reason_code=accepted_preview_write_eligible.
- Endpoint responses are normalized and include token/guard/binding status fields.
- All outcomes remain non-mutating:
  - mutation_performed=false
  - write_performed=false
  - bulk_lookup_performed=false
  - scoring_semantics_changed=false
  - external_lookup_performed=false
- No actual-results artifacts were modified in smoke/regression validation.

## 4. Exact mutation boundary
Mutation is allowed only inside a future explicit write segment that starts after all of the following pass in the same request lifecycle:
1. schema request_valid=true
2. token_valid=true
3. approval_binding_valid=true
4. guard_allowed=true
5. acceptance_gate.state=write_eligible and write_eligible=true

Mutation boundary rules:
- Exactly one selected record per request.
- Exactly one allowed write target.
- No fallback write targets.
- No write activity before all preconditions are true.
- No write activity after any post-precondition failure without rollback.

## 5. Preconditions before mutation
Required preconditions:
- mode=official_source_approved_apply
- lookup_intent=apply_write
- selected_key present and one-record only
- approval_granted=true
- approval_token present and valid
- approval binding fields present and matching preview snapshot
- preview snapshot matches authoritative server-side revalidation
- acceptance gate remains write_eligible at apply time
- no token replay/expired/consumed state
- no manual-review or rejected gate state

Any failed precondition must deny with no mutation.

## 6. Required guard_allowed=true checks
Before crossing into mutation boundary, all must be true in the endpoint decision envelope:
- request_valid=true
- token_valid=true
- guard_allowed=true
- approval_binding_valid=true
- reason_code=accepted_preview_write_eligible
- manual_review_required=false
- acceptance_gate.state=write_eligible
- acceptance_gate.write_eligible=true

If any is false, mutation remains blocked.

## 7. Token consume persistence requirements
Token consume persistence is defined here but not implemented in this slice.

Required future behavior:
- Token consume must occur only after successful atomic write completion.
- Replay/expired/consumed tokens must block write.
- Consume operation must be idempotent and auditable.
- Consume state must not be committed on pre-write denial.
- Consume state and write success must be transactionally coherent (no ambiguous partial state).

This slice authorizes no token persistence implementation.

## 8. Write target
Allowed target only:
- ops/accuracy/actual_results_manual.json

Disallowed targets:
- ops/accuracy/actual_results.json
- ops/accuracy/actual_results_unresolved.json
- queue files
- any alternative output path

## 9. Exact write schema
Future write record must include at minimum:
- fight_id
- fight_name
- actual_winner
- source
- source_url
- source_title
- source_date
- publisher_host
- source_confidence
- confidence_score
- citation_fingerprint
- selected_key
- write_mode
- approval_type
- operator_id
- approved_at_utc

Optional fields:
- method
- round_time
- event_name
- event_date
- notes

Schema invariants:
- source=official_source_manual_approved
- write_mode=official_source_approved_apply
- approval_type=explicit_operator_approval
- actual_winner must match bound extracted_winner
- source_date must match bound source_date

## 10. Atomic write strategy
Future atomic write strategy:
1. Read current bytes from ops/accuracy/actual_results_manual.json.
2. Compute and store pre_write_file_sha256.
3. Build deterministic candidate output with exactly one record insert/update effect.
4. Write candidate output to a temporary file in the same filesystem boundary.
5. Atomic replace target with temporary file.
6. Verify replace success and compute post_write_file_sha256.
7. Only after step 6, proceed to token consume persistence.

Atomicity requirement:
- No partial bytes or torn writes may survive.

## 11. Rollback strategy
Rollback must restore exact prior bytes if any failure occurs after write start.

Future rollback flow:
1. Capture pre-write bytes and hash before mutation.
2. On any post-start failure, restore pre-write bytes to target.
3. Verify restored hash equals pre_write_file_sha256.
4. Emit rollback metadata in response/audit envelope.

Failure must fail closed:
- write_performed=false in final response if rollback restores pre-write state.

## 12. Rollback proof metadata
Required rollback proof fields:
- pre_write_file_sha256
- post_write_file_sha256 (on success)
- rollback_attempted
- rollback_succeeded
- post_rollback_file_sha256
- rollback_reason_code
- rollback_error_detail (if any)

Proof requirement:
- post_rollback_file_sha256 must equal pre_write_file_sha256 when rollback_succeeded=true.

## 13. Audit response fields
Future mutation-capable envelope must include current decision fields plus write/rollback audit fields:
- correlation_id
- phase
- selected_key
- approval_required
- approval_granted
- approval_binding_valid
- token_status
- approval_token_status
- approval_token_id
- approval_token_issued_at_utc
- approval_token_expires_at_utc
- approval_token_consumed
- acceptance_gate.state
- acceptance_gate.write_eligible
- acceptance_gate.reason_code
- binding_digest_expected
- binding_digest_actual
- write_target
- write_performed
- mutation_performed
- scoring_semantics_changed
- pre_write_file_sha256
- post_write_file_sha256
- rollback_attempted
- rollback_succeeded
- post_rollback_file_sha256
- reason_code
- errors

## 14. Failure states
Failure states requiring fail-closed handling:
- pre-write file read error
- candidate serialization error
- temporary file write error
- atomic replace error
- post-write verification hash mismatch
- token consume persistence error after write success
- rollback restore failure

Failure state outcomes:
- deterministic reason_code
- no scoring changes
- no batch side effects
- explicit rollback metadata fields

## 15. Deny states
Deny states remain non-mutating and include (not exhaustive):
- invalid_apply_mode
- invalid_lookup_intent
- selected_key_type_invalid / selected_key_required / single_record_required
- approval_granted_required_true
- approval_token_missing
- approval_expired
- approval_replayed
- approval_token_consumed
- approval_binding_mismatch
- selected_key_binding_mismatch
- citation_binding_mismatch
- source_url_binding_mismatch
- source_date_binding_mismatch
- extracted_winner_binding_mismatch
- record_identity_binding_mismatch
- preview_snapshot_mismatch
- acceptance_gate_not_write_eligible

Deny outcome invariants:
- guard_allowed=false
- write_performed=false
- mutation_performed=false

## 16. Manual-review states
Manual-review states remain non-mutating and include:
- acceptance_gate.state=manual_review
- confidence_below_threshold
- tier_b_without_corroboration
- stale_source_date
- source_conflict

Manual-review outcome invariants:
- guard_allowed=false
- manual_review_required=true
- write_performed=false
- mutation_performed=false

## 17. No-batch / no-page-load / no-auto-apply rules
Must remain true in all future mutation slices:
- Batch apply remains impossible.
- selected_keys/targets/batch_size/execution_token/apply_all/queue_wide/queue_scope remain disallowed.
- Page-load apply remains impossible.
- Automatic apply remains impossible.
- Only explicit one-record operator action may initiate apply.

## 18. Scoring semantics protection
Scoring semantics protection is mandatory:
- scoring_semantics_changed must remain false.
- No scoring formula updates in apply flow.
- No prediction logic modifications in apply flow.
- Apply write affects only approved actual result record state in manual target file.

## 19. Test requirements before implementation
Before any write implementation, tests must prove:
- All preconditions gate mutation boundary correctly.
- guard_allowed=true with valid binding and token can enter write boundary path.
- Any deny/manual-review/token invalid state blocks write.
- Replay/expired/consumed tokens block write.
- One-record-only enforcement.
- Write target enforcement to ops/accuracy/actual_results_manual.json only.
- Atomic replace success path is deterministic.
- Rollback restores exact previous bytes on forced failures.
- rollback proof metadata correctness.
- No batch, no page-load apply, no auto-apply behavior.
- scoring_semantics_changed remains false in all outcomes.

## 20. Future implementation micro-slices
1. Mutation boundary fixture lock (tests/docs only)
- Lock request/response fixtures for success, deny, manual-review, rollback.

2. Write planner helper (non-writing dry planner)
- Build proposed_write and candidate record update plan only.

3. Atomic write adapter implementation
- Implement temp-write + atomic replace with verification.

4. Rollback adapter implementation
- Implement restore path and rollback proof fields.

5. Token consume persistence integration
- Implement consume-after-commit semantics and replay safety.

6. Endpoint mutation branch integration
- Wire guarded mutation branch after guard_allowed=true only.

7. End-to-end safety tests and freeze review
- Run full contract, rollback, and no-batch/no-scoring regression.

---

Mandatory policy closure:
- Mutation can only occur after guard_allowed=true.
- Mutation can only write one selected record.
- Mutation can only write to ops/accuracy/actual_results_manual.json.
- Mutation must be atomic.
- Mutation must snapshot manual actual-results bytes before write.
- If write fails, rollback must restore exact previous bytes.
- Token consume persistence is defined but not implemented in this slice.
- Replayed/expired/consumed tokens must block write.
- Batch apply remains impossible.
- Page-load apply remains impossible.
- Automatic apply remains impossible.
- Scoring semantics do not change.

Design status: ready for review.
Implementation status: intentionally not started.
