# official-source-approved-apply-mutation-adapter-design-v1

## Purpose

Define a corrected docs-only design for a future `official_source_approved_apply_mutation_adapter`
module. This design replaces the prior informal adapter sketch that was rejected for conflicting
with the locked mutation-boundary rules.

This slice creates no runtime code, no endpoint changes, no test files, and no actual-results
mutation. It exists solely to resolve the five blockers identified during design review and to
establish a pre-implementation contract that is fully consistent with:

- `official_source_approved_apply_mutation_boundary_design_v1`
- `official_source_approved_apply_mutation_boundary_final_review_v1`
- `official_source_approved_apply_fixture_test_design_v1`
- `official_source_approved_apply_contract_v1`

---

## Non-goals

- No implementation of `official_source_approved_apply_mutation_adapter.py`.
- No changes to `operator_dashboard/app.py`.
- No changes to `operator_dashboard/official_source_approved_apply_guard.py`.
- No changes to any test file.
- No changes to any template.
- No token consume persistence implementation.
- No mutation lock implementation.
- No write-path activation of any kind.
- No actual-results file mutation.
- No batch behavior.
- No UI behavior.
- No scoring changes.
- No external lookup execution.

---

## Blocker corrections (vs. rejected informal design)

### Blocker 1 — "Existing upsert is enough" assumption: CORRECTED

The informal design proposed calling `_upsert_single_manual_actual_result` directly as if it were
atomic-safe. The existing helper has no pre-write snapshot, no SHA256 verification, no temp-file
strategy, and no rollback capability. It is write-capable but not mutation-safe for this path.

**Correction:** The adapter must implement its own atomic write wrapper that satisfies the boundary
design atomic write strategy (§10 of mutation boundary design) before delegating any bytes to disk.
Calling `_upsert_single_manual_actual_result` directly is not permitted from the adapter layer.
The adapter must call a new internal write helper (`_atomic_write_single_record`) that:

1. Takes a pre-write byte snapshot.
2. Computes `pre_write_file_sha256`.
3. Writes to a same-filesystem temp file.
4. Atomically replaces the target.
5. Verifies `post_write_file_sha256`.
6. Handles rollback on any step failure.

### Blocker 2 — No pre-write snapshot or SHA256: CORRECTED

The adapter must capture the exact byte content of `ops/accuracy/actual_results_manual.json`
before any mutation attempt begins. SHA256 of those bytes becomes `pre_write_file_sha256` and is
included in the audit envelope regardless of outcome.

If the file cannot be read, the adapter returns `reason_code="pre_write_read_error"` with
`write_performed=False` and no mutation.

### Blocker 3 — No same-filesystem temp file / atomic replace: CORRECTED

The write helper must write the candidate bytes to a temporary file created in the same directory
as the target (`ops/accuracy/`) using `tempfile.NamedTemporaryFile(dir=target_dir, delete=False)`.
It must then call `os.replace(tmp_path, target_path)` to perform an atomic rename within the same
filesystem. Cross-filesystem writes are a hard error (`reason_code="cross_filesystem_write_error"`).

The temp file must be cleaned up on any failure that leaves it behind.

### Blocker 4 — No rollback: CORRECTED

If any step fails after the pre-write snapshot is captured, the adapter must attempt to restore the
exact original bytes to the target file. Rollback verification requires computing
`post_rollback_file_sha256` and asserting it equals `pre_write_file_sha256`. If they differ, the
outcome is classified as `rollback_failed_terminal`.

### Blocker 5 — No mutation lock / contention handling: CORRECTED

The adapter must attempt to acquire a named exclusive mutation lock scoped to
`actual_results_manual.json` before reading the pre-write snapshot. Lock acquisition failure
returns `reason_code="mutation_lock_acquire_failed"`. Contention timeout returns
`reason_code="contention_timeout"`. The lock must be released in a `finally` block regardless of
write outcome. Lock backend choice remains implementation-time; the design requires deterministic
timeout behavior and reason codes only.

### Blocker 6 — No token_id surfacing from guard: CORRECTED

Token consume can only happen after write success. The guard result must surface `token_id` as an
additive field for the endpoint to extract. This requires one additive change to
`official_source_approved_apply_guard.py` (`_build_guard_response` adds `"token_id": token_id`).
That change is scoped to the guard-amendment slice (separate from this adapter slice). The adapter
design requires `token_id` to be present in the guard result envelope — it is a required input.

### Blocker 7 — UNKNOWN fallback for critical fields: CORRECTED

The informal design allowed `"UNKNOWN"` fallbacks for fields that must be deterministic and
source-verified. This design prohibits `"UNKNOWN"` for all critical fields. A missing or empty
critical field is a hard precondition failure with `reason_code="critical_field_missing"` — see
Critical-field denial rules below.

---

## Preconditions

All preconditions are evaluated before any file I/O or lock acquisition. A precondition failure
returns immediately with `mutation_performed=False`, `write_performed=False`, and a deterministic
`reason_code`. No temp file is created. No lock is acquired.

| # | Precondition | Deny reason code |
|---|---|---|
| 1 | `guard_result["guard_allowed"] is True` | `precondition_guard_not_allowed` |
| 2 | `guard_result["reason_code"] == "accepted_preview_write_eligible"` | `precondition_wrong_reason_code` |
| 3 | `guard_result["token_valid"] is True` | `precondition_token_not_valid` |
| 4 | `guard_result["approval_binding_valid"] is True` | `precondition_binding_not_valid` |
| 5 | `guard_result["manual_review_required"] is False` | `precondition_manual_review_required` |
| 6 | `isinstance(guard_result.get("token_id"), str) and guard_result["token_id"]` | `precondition_token_id_missing` |
| 7 | `isinstance(preview_snapshot, dict)` | `precondition_preview_snapshot_invalid` |
| 8 | `acceptance_gate["state"] == "write_eligible"` (from guard result) | `precondition_gate_not_write_eligible` |
| 9 | `accuracy_dir.is_dir()` | `precondition_accuracy_dir_missing` |
| 10 | Target file `actual_results_manual.json` is readable | `pre_write_read_error` |
| 11 | All critical fields present and non-empty (see below) | `critical_field_missing` |

---

## Inputs

```
apply_official_source_approved_apply_mutation(
    *,
    guard_result: dict,
    preview_snapshot: dict,
    accuracy_dir: Path,
    consumed_token_ids: set,        # caller-managed; checked but not mutated by adapter
    lock_timeout_seconds: int = 10,
    operation_id: str,              # stable UUID for this request lifecycle
    write_attempt_id: str,          # unique UUID per mutation attempt (including retries)
    contract_version: str,          # e.g. "official_source_approved_apply_contract_v1"
    endpoint_version: str,          # e.g. "approved_apply_v1"
) -> dict
```

The adapter does **not** write to `consumed_token_ids`. That is exclusively the caller's
responsibility (the endpoint), and only after the adapter returns with `write_performed=True`.

---

## Proposed write schema

The write record persisted to `ops/accuracy/actual_results_manual.json` must include all of the
following fields. No field may be `None`, empty string, or `"UNKNOWN"`.

```json
{
  "fight_id": "<from preview_snapshot.audit.record_fight_id>",
  "fight_name": "<from preview_snapshot.audit.fight_name or selected_row.fight_name>",
  "actual_winner": "<from preview_snapshot.source_citation.extracted_winner>",
  "actual_method": "<from preview_snapshot.source_citation.extracted_method>",
  "actual_round": "<from preview_snapshot.source_citation.extracted_round>",
  "event_date": "<from preview_snapshot.source_citation.source_date>",
  "event_name": "<from preview_snapshot.source_citation.source_title or audit.event_name>",
  "source": "official_source_manual_approved",
  "source_url": "<from preview_snapshot.source_citation.source_url>",
  "source_title": "<from preview_snapshot.source_citation.source_title>",
  "source_date": "<from preview_snapshot.source_citation.source_date>",
  "publisher_host": "<from preview_snapshot.source_citation.publisher_host>",
  "source_confidence": "<from preview_snapshot.source_citation.source_confidence>",
  "confidence_score": "<from preview_snapshot.source_citation.confidence_score>",
  "citation_fingerprint": "<from preview_snapshot.source_citation.citation_fingerprint>",
  "selected_key": "<from guard_result.selected_key>",
  "write_mode": "official_source_approved_apply",
  "approval_type": "explicit_operator_approval",
  "approval_token_id": "<from guard_result.token_id>",
  "operation_id": "<operation_id param>",
  "write_attempt_id": "<write_attempt_id param>",
  "contract_version": "<contract_version param>",
  "endpoint_version": "<endpoint_version param>",
  "approved_at_utc": "<ISO-8601 UTC timestamp of write attempt>",
  "binding_digest": "<from guard_result.binding_digest_expected>"
}
```

Field invariants:
- `source` is always the literal constant `"official_source_manual_approved"`.
- `write_mode` is always the literal constant `"official_source_approved_apply"`.
- `approval_type` is always the literal constant `"explicit_operator_approval"`.
- `actual_winner` must exactly equal `approval_binding.extracted_winner` (verified by guard before
  adapter is called — adapter asserts via `preview_snapshot.source_citation.extracted_winner` ==
  `guard_result.acceptance_gate.citation_fingerprint`-binding chain, not re-derived independently).

---

## Critical-field denial rules

The following fields are **required, non-empty, non-UNKNOWN**. If any is missing, null, blank, or
the literal string `"UNKNOWN"` after stripping, the adapter returns
`reason_code="critical_field_missing"` with `errors` listing each violating field name.
`write_performed=False`. No lock acquired. No temp file created.

Critical fields:
- `fight_id` (from `preview_snapshot["audit"]["record_fight_id"]`)
- `actual_winner` (from `preview_snapshot["source_citation"]["extracted_winner"]`)
- `citation_fingerprint` (from `preview_snapshot["source_citation"]["citation_fingerprint"]`)
- `source_url` (from `preview_snapshot["source_citation"]["source_url"]`)
- `source_date` (from `preview_snapshot["source_citation"]["source_date"]`)
- `selected_key` (from `guard_result["selected_key"]`)
- `approval_token_id` (from `guard_result["token_id"]`)

Non-critical fields (UNKNOWN allowed as final fallback):
- `actual_method`
- `actual_round`
- `event_name`

---

## Atomic write strategy

Step-by-step sequence inside `_atomic_write_single_record`:

```
1.  Acquire named exclusive mutation lock for ops/accuracy/actual_results_manual.json
    (timeout = lock_timeout_seconds).
    → failure: reason_code="mutation_lock_acquire_failed", no further I/O.
    → timeout: reason_code="contention_timeout", no further I/O.

2.  Read current file bytes from ops/accuracy/actual_results_manual.json.
    → failure: reason_code="pre_write_read_error", release lock, no further I/O.

3.  Compute pre_write_file_sha256 = SHA256(current_bytes).

4.  Parse current JSON list; locate existing record by fight_id (upsert logic).
    → parse failure: reason_code="pre_write_parse_error", release lock, no further I/O.

5.  Build candidate record list (exactly one insert or one update effect).
    Serialize to UTF-8 JSON bytes with indent=2, trailing newline.
    → serialization failure: reason_code="candidate_serialization_error", release lock.

6.  Create temp file: tempfile.NamedTemporaryFile(
        dir=target_dir, suffix=".tmp", delete=False, mode="wb"
    )
    Verify temp file is on same filesystem as target
    (os.stat(tmp_path).st_dev == os.stat(target_dir).st_dev).
    → cross-filesystem: reason_code="cross_filesystem_write_error", delete tmp, release lock.

7.  Write candidate bytes to temp file. Flush. fsync(tmp_file.fileno()).
    → write failure: reason_code="temp_write_error", delete tmp, release lock.

8.  Close temp file.

9.  os.replace(tmp_path, target_path).
    → replace failure: reason_code="atomic_replace_error", attempt rollback (step 11).

10. Read back target bytes. Compute post_write_file_sha256.
    If post_write_file_sha256 != SHA256(candidate_bytes):
    → reason_code="post_write_hash_mismatch", attempt rollback (step 11).

11. Release mutation lock.

12. Return success envelope with pre_write_file_sha256, post_write_file_sha256.
```

Rollback is triggered in step 9 or 10 failure cases — see rollback strategy below.

---

## Rollback strategy

Rollback executes only after a write has been attempted (step 9 or step 10 failure). Pre-write
failures (steps 2–8) are fail-closed without needing rollback because no partial state has reached
the target file.

Rollback sequence:

```
R1. Set rollback_started_at_utc = now.
R2. Attempt to write pre_write_bytes back to target path using os.replace
    (same temp-file mechanism — write to new temp file, then replace).
R3. Compute post_rollback_file_sha256 = SHA256(read back target).
R4. If post_rollback_file_sha256 == pre_write_file_sha256:
    → rollback_succeeded=True.
    → write_performed=False in return envelope.
R5. If post_rollback_file_sha256 != pre_write_file_sha256 or R2 threw an exception:
    → rollback_succeeded=False.
    → rollback_terminal_state="rollback_failed_terminal".
    → reason_code="rollback_failed_terminal".
    → escalation_required=True.
    → operator_escalation_action="manual_file_recovery_required".
R6. Set rollback_finished_at_utc = now.
R7. Release mutation lock (if still held).
```

Rollback-failed-terminal invariant: token consume persistence must not proceed if
`rollback_terminal_state="rollback_failed_terminal"`.

---

## Token consume boundary

Ordering contract (enforced by the endpoint caller, not the adapter):

```
1. Guard validates token using consumed_token_ids set (token_id absent → valid).
2. Guard succeeds (guard_allowed=True).
3. Endpoint calls adapter.
4. Adapter acquires lock, writes, verifies, releases lock.
5. Adapter returns write_performed=True.
6. [Only now] Endpoint adds token_id to consumed_token_ids.
7. If step 6 fails (token_consume_post_write_failed):
   - Do NOT re-run the write.
   - Log with operation_id and write_attempt_id for idempotent retry.
   - Return reason_code="token_consume_post_write_failed" in envelope.
   - write_performed remains True in envelope (the write succeeded).
```

The adapter never mutates `consumed_token_ids`. It receives it as a read-only input for
pre-condition checking only (the guard has already checked it; the adapter does not re-check).

Token consume failure recovery:
- A retry of token consume using `operation_id` + `write_attempt_id` as idempotency key must not
  produce a second write.
- `token_consume_post_write_failed` is a non-fatal outcome from the operator's perspective — the
  result is committed but consume registration failed.

---

## Contention / lock policy

| Scenario | Reason code | write_performed |
|---|---|---|
| Lock unavailable immediately | `mutation_lock_acquire_failed` | False |
| Lock wait exceeds timeout | `contention_timeout` | False |
| Process crash while lock held | Recovery at next request; lock must be re-acquirable (not held forever) | — |
| Crash after write, before lock release | `crash_interruption_recovery_required`; operator manual review | — |

Lock backend implementation requirements (deferred to implementation slice):
- Must be deterministic on timeout.
- Must not starve requests indefinitely.
- Must be releasable from a `finally` block on exception.
- Must be scoped to target file path, not global.

---

## Audit fields

The adapter return envelope must include all of the following fields. The endpoint merges these
into the normalized response.

```json
{
  "ok": true | false,
  "mutation_performed": true | false,
  "write_performed": true | false,
  "bulk_lookup_performed": false,
  "scoring_semantics_changed": false,
  "reason_code": "...",
  "errors": [],
  "selected_key": "...",
  "fight_id": "..." | null,
  "proposed_write": { ... } | null,
  "write_target": "ops/accuracy/actual_results_manual.json" | null,
  "before_row_count": 12 | null,
  "after_row_count": 13 | null,
  "pre_write_file_sha256": "..." | null,
  "post_write_file_sha256": "..." | null,
  "rollback_attempted": false | true,
  "rollback_succeeded": false | true | null,
  "post_rollback_file_sha256": "..." | null,
  "rollback_reason_code": null | "...",
  "rollback_error_detail": null | "...",
  "rollback_started_at_utc": null | "...",
  "rollback_finished_at_utc": null | "...",
  "rollback_terminal_state": null | "rollback_failed_terminal",
  "escalation_required": false | true,
  "operator_escalation_action": null | "manual_file_recovery_required",
  "approval_token_id": "..." | null,
  "token_consume_performed": false,
  "operation_id": "...",
  "write_attempt_id": "...",
  "contract_version": "...",
  "endpoint_version": "..."
}
```

Invariants that must always hold in the envelope:
- `bulk_lookup_performed` is always `False`.
- `scoring_semantics_changed` is always `False`.
- `token_consume_performed` is always `False` from the adapter (token consume is the caller's act).
- `mutation_performed` is `True` if and only if `write_performed` is `True`.
- `rollback_attempted` is `False` for all precondition-failure paths (no I/O reached target file).
- `escalation_required` is `True` if and only if
  `rollback_terminal_state == "rollback_failed_terminal"`.

---

## Failure states

| State | Reason code | write_performed | rollback_attempted | escalation_required |
|---|---|---|---|---|
| Guard not allowed | `precondition_guard_not_allowed` | False | False | False |
| Wrong reason code | `precondition_wrong_reason_code` | False | False | False |
| Token not valid | `precondition_token_not_valid` | False | False | False |
| Binding not valid | `precondition_binding_not_valid` | False | False | False |
| Manual review required | `precondition_manual_review_required` | False | False | False |
| Token ID missing | `precondition_token_id_missing` | False | False | False |
| Preview snapshot invalid | `precondition_preview_snapshot_invalid` | False | False | False |
| Gate not write_eligible | `precondition_gate_not_write_eligible` | False | False | False |
| Accuracy dir missing | `precondition_accuracy_dir_missing` | False | False | False |
| Critical field missing | `critical_field_missing` | False | False | False |
| Lock acquire failed | `mutation_lock_acquire_failed` | False | False | False |
| Contention timeout | `contention_timeout` | False | False | False |
| Pre-write read error | `pre_write_read_error` | False | False | False |
| Pre-write parse error | `pre_write_parse_error` | False | False | False |
| Candidate serialization error | `candidate_serialization_error` | False | False | False |
| Cross-filesystem error | `cross_filesystem_write_error` | False | False | False |
| Temp write error | `temp_write_error` | False | False | False |
| Atomic replace error | `atomic_replace_error` | False | True | False (if rollback ok) |
| Post-write hash mismatch | `post_write_hash_mismatch` | False | True | False (if rollback ok) |
| Rollback failed terminal | `rollback_failed_terminal` | False | True | **True** |
| Write success | `official_source_write_applied` | **True** | False | False |
| Token consume post-write failure | `token_consume_post_write_failed` | **True** | False | False |
| Crash / unknown exception | `internal_apply_error` | False | True (attempted) | Depends |

---

## Test plan

The implementation slice will create
`operator_dashboard/test_official_source_approved_apply_mutation_adapter.py`.

All tests use `unittest.mock.patch` for `_atomic_write_single_record`, os-level file calls, and
the mutation lock. No real file I/O in tests. No calls to
`_upsert_single_manual_actual_result` (the adapter does not call that function).

| Test class | Scenarios | Est. count |
|---|---|---|
| `PreconditionDenialTest` | Each of the 10 preconditions fails individually; assert `write_performed=False`, correct `reason_code`, no lock acquired, no file I/O | 10 |
| `CriticalFieldDenialTest` | Each of the 7 critical fields is missing/empty/UNKNOWN one at a time; assert `critical_field_missing`, all fields listed in `errors` | 7 |
| `LockDenialTest` | `mutation_lock_acquire_failed`; `contention_timeout` | 2 |
| `PreWriteErrorTest` | `pre_write_read_error`; `pre_write_parse_error`; `candidate_serialization_error`; `cross_filesystem_write_error`; `temp_write_error` | 5 |
| `AtomicReplaceFailureTest` | `atomic_replace_error` → rollback succeeds; `atomic_replace_error` → rollback fails → `rollback_failed_terminal` | 2 |
| `PostWriteHashMismatchTest` | Hash mismatch → rollback succeeds; hash mismatch → rollback fails → `rollback_failed_terminal` | 2 |
| `WriteSuccessTest` | Upsert (insert); upsert (update); SHA256 proof fields populated; `mutation_performed=True`; `token_consume_performed=False` | 3 |
| `ProposedWriteSchemaTest` | All write fields map correctly; literal constants correct; no UNKNOWN in critical fields; `source` constant; `write_mode` constant | 5 |
| `InvariantTest` | `bulk_lookup_performed` always False; `scoring_semantics_changed` always False; `mutation_performed` iff `write_performed`; `escalation_required` iff `rollback_failed_terminal` | 4 |
| `TokenConsumeOrderingTest` | Adapter never mutates `consumed_token_ids`; caller protocol: token_id surfaced, add after write | 2 |
| `RollbackProofTest` | `post_rollback_file_sha256` equals `pre_write_file_sha256` when rollback succeeds; mismatch triggers escalation | 2 |
| `OperationIdTest` | `operation_id` and `write_attempt_id` appear in envelope and proposed_write record | 2 |

Estimated total: **~46 tests**.

---

## Future micro-slices

The following slices follow this design in strict sequence. No slice may begin before the
previous is locked and tagged.

| Sequence | Slice name | Scope |
|---|---|---|
| 1 | `official-source-approved-apply-mutation-adapter-design-v1` | **This doc** — design only |
| 2 | `official-source-approved-apply-guard-token-id-surface-v1` | Add additive `token_id` field to guard response; guard tests updated; no adapter code |
| 3 | `official-source-approved-apply-mutation-adapter-implementation-v1` | Implement adapter module + unit tests (~46 tests); no `app.py` changes; no write activation |
| 4 | `official-source-approved-apply-endpoint-wiring-v1` | Wire adapter into `app.py` endpoint; endpoint tests; first live write path |
| 5 | `official-source-approved-apply-token-consume-persistence-v1` | Persistent consumed-token-ids store; idempotent retry by `operation_id`; recovery tests |
| 6 | `official-source-approved-apply-mutation-lock-implementation-v1` | Implement deterministic mutation lock backend; contention tests |
| 7 | `official-source-approved-apply-interruption-simulation-v1` | Fault-injection tests for crash/rollback/partial-state scenarios |
| 8 | `official-source-approved-apply-audit-log-v1` | Structured audit log for mutation attempts; no endpoint behavior change |

Each slice:
- Must validate all prior 266+ tests still pass before committing.
- Must not touch `ops/accuracy/actual_results*.json` except slice 4+ under test-only mock.
- Must not change scoring semantics.
- Must not activate batch behavior.

---

## Write target (confirmed)

One allowed write target, exactly:

```
ops/accuracy/actual_results_manual.json
```

Prohibited targets (write to any of these is a hard error at design and implementation level):
- `ops/accuracy/actual_results.json`
- `ops/accuracy/actual_results_unresolved.json`
- Any queue file
- Any alternate path

---

## Source_citation and acceptance_gate binding verification

The adapter relies entirely on the guard having already verified that `preview_snapshot` matches
`authoritative_preview_result` and that `approval_binding` fields match `source_citation` fields.
The adapter does **not** re-derive or re-validate binding. It asserts that guard preconditions
passed (preconditions 1–5) and then extracts source fields directly from `preview_snapshot`.

This means `source_citation` and `acceptance_gate` values used to build `proposed_write` are
already binding-verified by the time the adapter runs. The adapter is not a second validation
layer — it is a write executor that operates only after the guard has cleared every gate.
