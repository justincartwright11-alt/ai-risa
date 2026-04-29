# official-source-approved-apply-fixture-test-design-v1

## 1. Purpose
Define docs-only fixtures and tests required before any write adapter or mutation implementation exists for approved apply.

This slice does not change runtime code, endpoint behavior, or test files.

## 2. Scope and non-goals
In scope:
- Fixture catalog design for approved-apply request/response envelopes.
- Deterministic expected-outcome matrix for deny, manual-review, and write-eligible paths.
- Pre-implementation test plan for boundary, rollback, contention, and partial-failure semantics.

Out of scope:
- No runtime code.
- No endpoint changes.
- No mutation implementation.
- No UI/template changes.
- No batch behavior.
- No scoring changes.

## 3. Fixture package structure (design)
Proposed fixture tree for a future non-mutating fixture/test slice:

```text
tests/fixtures/approved_apply/
  requests/
    valid/
      apply_write_write_eligible.json
    deny/
      invalid_apply_mode.json
      invalid_lookup_intent.json
      selected_key_required.json
      single_record_required.json
      approval_granted_required_true.json
      approval_token_missing.json
      approval_expired.json
      approval_replayed.json
      approval_token_consumed.json
      approval_binding_mismatch.json
      selected_key_binding_mismatch.json
      citation_binding_mismatch.json
      source_url_binding_mismatch.json
      source_date_binding_mismatch.json
      extracted_winner_binding_mismatch.json
      record_identity_binding_mismatch.json
      preview_snapshot_mismatch.json
      acceptance_gate_not_write_eligible.json
    manual_review/
      confidence_below_threshold.json
      tier_b_without_corroboration.json
      stale_source_date.json
      source_conflict.json
  expected/
    valid/
      apply_write_write_eligible.expected.json
    deny/
      *.expected.json
    manual_review/
      *.expected.json
  scenarios/
    ordering/
      token_consume_post_write_failed.design.json
    contention/
      mutation_lock_acquire_failed.design.json
      contention_timeout.design.json
    interruption/
      crash_interruption_recovery_required.design.json
    rollback/
      rollback_failed_terminal.design.json
```

Design intent:
- requests/ contains canonical request payload fixtures.
- expected/ contains canonical envelope assertions used by tests.
- scenarios/ contains fault-injection design fixtures for future adapter-level simulation.

## 4. Canonical baseline fixture requirements
Baseline valid fixture must include:
- mode=official_source_approved_apply
- lookup_intent=apply_write
- one selected_key
- approval_granted=true
- valid approval_token
- fully bound approval_binding
- preview_snapshot with acceptance_gate.state=write_eligible

Baseline expected envelope must assert:
- request_valid=true
- token_valid=true
- approval_binding_valid=true
- guard_allowed=true
- reason_code=accepted_preview_write_eligible
- manual_review_required=false
- mutation_performed=false (pre-implementation)
- write_performed=false (pre-implementation)
- write_target=ops/accuracy/actual_results_manual.json
- scoring_semantics_changed=false

## 5. Deny fixture taxonomy
Each deny fixture must map to one deterministic reason code and non-mutating invariants.

Deny invariants for all deny fixtures:
- guard_allowed=false
- write_performed=false
- mutation_performed=false
- bulk_lookup_performed=false
- scoring_semantics_changed=false

Required deny reason-code coverage:
- invalid_apply_mode
- invalid_lookup_intent
- selected_key_required
- single_record_required
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

## 6. Manual-review fixture taxonomy
Manual-review fixtures must prove reviewable states remain non-mutating and not guard-allowed.

Required manual-review coverage:
- confidence_below_threshold
- tier_b_without_corroboration
- stale_source_date
- source_conflict

Manual-review invariants for all fixtures:
- guard_allowed=false
- manual_review_required=true
- write_performed=false
- mutation_performed=false
- scoring_semantics_changed=false

## 7. Audit and envelope fixture assertions
Expected fixtures should assert presence and format of key fields, even before mutation implementation:
- correlation_id
- phase
- selected_key
- approval_token_status
- acceptance_gate.state
- acceptance_gate.write_eligible
- acceptance_gate.reason_code
- binding_digest_expected
- binding_digest_actual
- write_target
- reason_code
- errors

Future mutation-capable fixture design placeholders must reserve fields:
- operation_id
- write_attempt_id
- contract_version
- endpoint_version
- pre_write_file_sha256
- post_write_file_sha256
- rollback_attempted
- rollback_succeeded
- post_rollback_file_sha256
- rollback_reason_code
- rollback_terminal_state

## 8. Pre-implementation test plan
Test groups to create before mutation code:

1. Contract and schema gate tests
- Validate valid fixture acceptance to write-eligible non-mutating envelope.
- Validate each deny fixture reason code and invariant set.

2. Binding integrity tests
- selected_key, citation_fingerprint, source_url, source_date, extracted_winner, and record identity mismatch cases.
- Ensure no fallback acceptance on partial binding agreement.

3. Manual-review classification tests
- Verify manual_review_required=true and guard_allowed=false for all manual-review fixtures.

4. One-record and anti-batch tests
- Reject multi-key payloads.
- Reject batch-like fields/flags.

5. Write-target protection tests
- Assert write_target always resolves to ops/accuracy/actual_results_manual.json.
- Assert disallowed targets cannot be selected.

6. Ordering and partial-failure design tests (non-mutating harness)
- Model token_consume_post_write_failed expected classification semantics.
- Assert no duplicate write-plan execution on consume-retry design path.

7. Contention and lock behavior design tests
- Model mutation_lock_acquire_failed deterministic deny/fail-closed outcome.
- Model contention_timeout deterministic fail-closed outcome.

8. Interruption and rollback proof design tests
- Model crash_interruption_recovery_required expected classification.
- Model rollback_failed_terminal with escalation_required=true and operator_escalation_action=manual_file_recovery_required.

9. Scoring and side-effect protection tests
- Assert scoring_semantics_changed=false in all fixtures.
- Assert no batch, no external lookup, no page-load apply behavior.

## 9. Deterministic idempotency fixture rules
Fixtures must encode identity precedence exactly as:
1. selected_key
2. citation_fingerprint
3. record_fight_id (when present)

Idempotency design assertions:
- Repeated requests with same identity tuple resolve to same logical target identity.
- Duplicate tuple does not imply duplicate record creation intent.
- Divergent tuple component must produce deterministic binding/identity mismatch deny.

## 10. Fault-injection fixture contracts (design only)
Fault-injection scenario fixtures define expected classifications and required metadata, not implementation.

Required scenario contracts:
- token_consume_post_write_failed
  - reason_code deterministic
  - write phase considered committed in model
  - consume retry modeled as idempotent
- rollback_failed_terminal
  - escalation_required=true
  - operator_escalation_action=manual_file_recovery_required
  - token consume blocked
- mutation_lock_acquire_failed
  - fail-closed classification
  - no mutation side effects
- contention_timeout
  - fail-closed classification
  - retry policy documented at test expectation layer
- crash_interruption_recovery_required
  - recovery classification deterministic
  - rollback proof fields required when recovery path engages

## 11. Entry/exit criteria for this design stage
Entry criteria:
- mutation-boundary final review locked.
- no mutation implementation in progress.

Exit criteria for fixture/test design completeness:
- Full fixture matrix for valid/deny/manual-review is documented.
- Deterministic reason-code expectations are documented.
- Contention/interruption/partial-failure scenario expectations are documented.
- Audit field and placeholder mutation-proof fields are documented.
- Non-mutating and no-scoring invariants are documented for all categories.

## 12. Next slice after this document
Next safe slice after this docs design:
- non-mutating mutation fixture lock (tests/docs only)

Not allowed next:
- write adapter code
- rollback adapter code
- token consume persistence code
- endpoint mutation branch activation

Design status: ready for docs review.
Implementation status: intentionally not started.